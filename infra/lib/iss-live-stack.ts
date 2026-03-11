import * as path from 'path';
import { Duration, Stack, StackProps, CfnOutput, RemovalPolicy } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { RestApi, LambdaIntegration, Cors } from 'aws-cdk-lib/aws-apigateway';
import { Runtime } from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as iam from 'aws-cdk-lib/aws-iam';

const GITHUB_REPO = 'Hiru5han/iss-live';
const DOMAIN_NAME = 'iss-tracker.hirushan.dev';
const HOSTED_ZONE_ID = 'Z035374199CJOMN0YV2N';
const CERTIFICATE_ARN =
  'arn:aws:acm:us-east-1:549363909845:certificate/7731e719-3d48-48af-84ee-f7b23660e53b';

export class IssLiveStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // ── Backend (Lambda + API Gateway) ──────────────────────────────

    const issNowFunction = new PythonFunction(this, 'IssNowFunction', {
      entry: path.join(__dirname, '..', '..', 'backend'),
      index: 'app/serverless_handler.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_12,
      timeout: Duration.seconds(10),
      memorySize: 512,
      environment: {
        CACHE_TTL: '8',
        UPSTREAM_URL: 'https://api.wheretheiss.at/v1/satellites/25544'
      }
    });

    const api = new RestApi(this, 'IssLiveApi', {
      restApiName: 'IssLiveApi',
      description: 'Serverless mirror of the local ISS /iss/now endpoint',
      defaultCorsPreflightOptions: {
        allowOrigins: Cors.ALL_ORIGINS,
        allowMethods: ['GET', 'OPTIONS']
      }
    });

    const iss = api.root.addResource('iss');
    const now = iss.addResource('now');

    now.addMethod('GET', new LambdaIntegration(issNowFunction, { proxy: true }));

    // ── Frontend (S3 + CloudFront) ──────────────────────────────────

    const siteBucket = new s3.Bucket(this, 'SiteBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const certificate = acm.Certificate.fromCertificateArn(
      this, 'SiteCertificate', CERTIFICATE_ARN
    );

    const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
      comment: 'iss-tracker frontend',
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: new cloudfront.CachePolicy(this, 'SiteCachePolicy', {
          defaultTtl: Duration.seconds(300),
          maxTtl: Duration.seconds(1200),
          minTtl: Duration.seconds(0),
          queryStringBehavior: cloudfront.CacheQueryStringBehavior.all(),
        }),
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: Duration.seconds(300),
        },
      ],
      domainNames: [DOMAIN_NAME],
      certificate,
      httpVersion: cloudfront.HttpVersion.HTTP2,
    });

    new s3deploy.BucketDeployment(this, 'DeploySite', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '..', '..', 'frontend', 'dist'))],
      destinationBucket: siteBucket,
      distribution,
      distributionPaths: ['/*'],
    });

    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(this, 'Zone', {
      hostedZoneId: HOSTED_ZONE_ID,
      zoneName: 'hirushan.dev',
    });

    new route53.ARecord(this, 'SiteAlias', {
      zone: hostedZone,
      recordName: DOMAIN_NAME,
      target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
    });

    // ── GitHub Actions OIDC ───────────────────────────────────────────

    const ghProvider = new iam.OpenIdConnectProvider(this, 'GitHubOidc', {
      url: 'https://token.actions.githubusercontent.com',
      clientIds: ['sts.amazonaws.com'],
    });

    const deployRole = new iam.Role(this, 'GitHubActionsDeployRole', {
      roleName: 'iss-live-github-deploy',
      assumedBy: new iam.WebIdentityPrincipal(ghProvider.openIdConnectProviderArn, {
        StringEquals: {
          'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
        },
        StringLike: {
          'token.actions.githubusercontent.com:sub': `repo:${GITHUB_REPO}:ref:refs/heads/main`,
        },
      }),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess'),
      ],
    });

    // ── Outputs ─────────────────────────────────────────────────────

    new CfnOutput(this, 'IssApiUrl', {
      value: `${api.url}iss/now`,
      description: 'Invoke URL for the ISS state endpoint'
    });

    new CfnOutput(this, 'SiteUrl', {
      value: `https://${DOMAIN_NAME}`,
      description: 'Frontend URL'
    });

    new CfnOutput(this, 'DistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront distribution ID'
    });

    new CfnOutput(this, 'DeployRoleArn', {
      value: deployRole.roleArn,
      description: 'GitHub Actions deploy role ARN'
    });
  }
}

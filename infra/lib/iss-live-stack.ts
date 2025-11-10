import * as path from 'path';
import { Duration, Stack, StackProps, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { RestApi, LambdaIntegration, Cors } from 'aws-cdk-lib/aws-apigateway';
import { Runtime } from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

export class IssLiveStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

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

    new CfnOutput(this, 'IssApiUrl', {
      value: `${api.url}iss/now`,
      description: 'Invoke URL for the ISS state endpoint'
    });
  }
}

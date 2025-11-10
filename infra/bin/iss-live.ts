#!/usr/bin/env node
import 'source-map-support/register';
import { App } from 'aws-cdk-lib';
import { IssLiveStack } from '../lib/iss-live-stack';

const app = new App();

new IssLiveStack(app, 'IssLiveStack', {
  description: 'Serverless skeleton for ISS Live backend (API Gateway + Lambda)'
});

#!/usr/bin/env node

// Commented code will attempt to also deploy pipeline stack
import 'source-map-support/register';
import cdk = require('@aws-cdk/core');
import { MarbleWebKioskExportStack } from '../lib/deploy-stack';

const stage = process.env.STAGE || 'dev'

const app = new cdk.App();
new MarbleWebKioskExportStack(app, 'marble-web-kiosk-export' + `${stage === 'prod' ? '' : '-' + stage}`);

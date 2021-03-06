import cdk = require('@aws-cdk/core');
import lambda = require("@aws-cdk/aws-lambda");
import iam = require('@aws-cdk/aws-iam');
//import ssm = require('@aws-cdk/aws-ssm');
//import kms = require('@aws-cdk/aws-kms');
import events = require('@aws-cdk/aws-events');
import targets = require('@aws-cdk/aws-events-targets');


export class MarbleWebKioskExportStack extends cdk.Stack {

  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
      const stackName = id + '-stack'
    super(scope, stackName, props);

    const stage = process.env.STAGE || 'dev'

    // Create a role for this Lambda
    const embarkLambdaRole = new iam.Role(this, 'LambdaTrustRole', {
        assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        roleName:  id + '-role',
    });


    const embarkLambdaPolicy = new iam.Policy(this, 'EmbarkLambdaPolicy', {
        policyName: id + '-policy',
        roles: [embarkLambdaRole]
    });

    // Grant access to access Cloud Watch logs
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        resources: [cdk.Fn.sub('arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*')],
        actions: ['logs:CreateLogGroup',
          'logs:CreateLogStream',
          'logs:PutLogEvents'],
    }));

    // Grant access to read and set Parameter Store parameters
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        resources:[cdk.Fn.sub('arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/all/marble-data-processing/*')],
        actions: ["ssm:GetParameterHistory",
            "ssm:GetParametersByPath",
            "ssm:GetParameters",
            "ssm:GetParameter",
            "ssm:DescribeParameters"
        ],
    }));

    // Grant access to encrypt and decrypt Parameter Store secure strings
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        resources:[cdk.Fn.sub('arn:aws:kms:${AWS::Region}:${AWS::AccountId}:key/CMK')],
        actions: ["kms:Decrypt",
                "kms:Encrypt"]
    }));

    // Grant access to send email
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        resources: [cdk.Fn.sub('arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/nd.edu')],
        actions: ["ses:SendEmail"]
    }));


      // Define Lambda itself
      const embarkLambda = new lambda.Function(this, 'EmbarkLambda', {
          code: lambda.Code.fromAsset("../../src"),
          handler: 'handler.run',
          runtime: lambda.Runtime.PYTHON_3_7,
          functionName: id, // 'marble-web-kiosk-export',
          description: 'This function retrieves Embark Web Kiosk metadata from a web call, breaks it apart by object described, and saves each resulting metadata xml file to a google team drive.',
          // layers: [
          //     lambda.LayerVersion.fromLayerVersionArn(
          //       this,
          //       'sentry', cdk.Fn.importValue('sentry-sdk-python-layer:LayerArn')),
          //     lambda.LayerVersion.fromLayerVersionArn(
          //         this,
          //         'google', cdk.Fn.importValue('google-api-python-layer:LayerArn'))
          // ],
          environment: {
              SSM_KEY_BASE: `/all/marble-data-processing/${stage === 'prod' ? 'prod' : 'test'}`,
              WEB_KIOSK_EXPORT_MODE: `${stage === 'prod' ? 'incremental' : 'full'}`
          },
          role: embarkLambdaRole,
          timeout: cdk.Duration.seconds(900),
          memorySize: 256  // Because of the size of the xml, 128 isn't reliably big enough
      });


      // Set this up to run as a scheduled event
      // Run every day at 7AM UTC
      // See https://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-expressions.html
      const rule = new events.Rule(this, 'Rule', {
        schedule: events.Schedule.expression('cron(0 7 * * ? *)'),
        ruleName: id + '-rule'
      });

      rule.addTarget(new targets.LambdaFunction(embarkLambda));

  }
}

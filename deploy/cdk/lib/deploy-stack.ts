import cdk = require('@aws-cdk/core');
import lambda = require("@aws-cdk/aws-lambda");
import iam = require('@aws-cdk/aws-iam');
//import ssm = require('@aws-cdk/aws-ssm');
//import kms = require('@aws-cdk/aws-kms');
import events = require('@aws-cdk/aws-events');
import targets = require('@aws-cdk/aws-events-targets');


export class MarbleWebKioskExportStack extends cdk.Stack {
    public readonly lambdaCode: lambda.CfnParametersCode; // Expose this so pipeline can later write to it to pass in code for Lambda

  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
      const stackName = id + '-stack'
    super(scope, stackName, props);

    const stage = process.env.STAGE || 'dev'

    this.lambdaCode = lambda.Code.cfnParameters()

    // Create a role for this Lambda
    const embarkLambdaRole = new iam.Role(this, 'LambdaTrustRole', {
        assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        roleName:  id + '-role',
        // inlinePolicies: [embarkLambdaPolicy]
    });


    const embarkLambdaPolicy = new iam.Policy(this, 'EmbarkLambdaPolicy', {
        policyName: id + '-policy',
        roles: [embarkLambdaRole]
    });

    // Grant access to access Cloud Watch logs
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        // resources:['*'],
        resources: [cdk.Fn.sub('arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*')],
        actions: ['logs:CreateLogGroup',
          'logs:CreateLogStream',
          'logs:PutLogEvents'],
    }));

    // Grant access to read and set Parameter Store parameters
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        resources:[cdk.Fn.sub('arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/all/marble-embark-loader/*')],
        actions: ["ssm:GetParameterHistory",
            "ssm:GetParametersByPath",
            "ssm:GetParameters",
            "ssm:GetParameter",
        ],
    }));

    // Grant access to Describe  Parameter Store parameters
    embarkLambdaPolicy.addStatements(new iam.PolicyStatement({
        resources:['*'],
        actions: ['ssm:DescribeParameters',
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
          //code: this.lambdaCode,
          // Note replace below with above to use code inserted from pipeline instead of local src/ code.
          // code: lambda.Code.asset("../src"),
          code: lambda.Code.asset("../../src/function.zip"),
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
              SSM_KEY_BASE: `/all/marble-embark-loader/${stage === 'prod' ? 'prod' : 'test'}`,
              WEB_KIOSK_EXPORT_MODE: 'incremental'
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

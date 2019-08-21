import { MarbleWebKioskExportStack } from '../../lib/deploy-stack';
import cdk = require('../../node_modules/@aws-cdk/core');
import assert = require('../../node_modules/@aws-cdk/assert');
//import { expect, haveResource } from '../../node_modules/@aws-cdk/assert';
import 'mocha';

const stack = new cdk.App();
const MyStack = new MarbleWebKioskExportStack(stack,"marble-web-kiosk-export",{
});

describe('Test Marble Web Kiosk Export Stack', () => {

    it('Should have a Trust Role defined named \'marble-web-kiosk-export-role\'.', () => {
      assert.expect(MyStack).to(assert.haveResource("AWS::IAM::Role",{
          RoleName: 'marble-web-kiosk-export-role'
    }
    ))
    });

    it('Should have a Policy defined named \'marble-web-kiosk-export-policy\'.', () => {
        assert.expect(MyStack).to(assert.haveResource("AWS::IAM::Policy",{
            PolicyName: 'marble-web-kiosk-export-policy'
    }
    ))
    });


    it('Should have a Policy Statement granting access to logs, ssm, and ses.', () => {
        assert.expect(MyStack).to(assert.haveResource("AWS::IAM::Policy",{
            PolicyDocument: {
                "Statement": [
                  {
                    "Action": [
                      "logs:CreateLogGroup",
                      "logs:CreateLogStream",
                      "logs:PutLogEvents"
                    ],
                    "Effect": "Allow",
                    "Resource": {
                      "Fn::Sub": "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*"
                    }
                  },
                  {
                    "Action": [
                      "ssm:GetParameterHistory",
                      "ssm:GetParametersByPath",
                      "ssm:GetParameters",
                      "ssm:GetParameter"
                    ],
                    "Effect": "Allow",
                    "Resource": {
                      "Fn::Sub": "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/all/marble-embark-loader/*"
                    }
                  },
                  {
                    "Action": "ssm:DescribeParameters",
                    "Effect": "Allow",
                    "Resource": "*"
                  },
                  {
                    "Action": [
                      "kms:Decrypt",
                      "kms:Encrypt"
                    ],
                    "Effect": "Allow",
                    "Resource": {
                      "Fn::Sub": "arn:aws:kms:${AWS::Region}:${AWS::AccountId}:key/CMK"
                    }
                  },
                  {
                    "Action": "ses:SendEmail",
                    "Effect": "Allow",
                    "Resource": {
                      "Fn::Sub": "arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/nd.edu"
                    }
                  }
                ],
                "Version": "2012-10-17"
              },
            //   "Statement": [
            //     {
            //       "Action": [
            //         "ssm:DescribeParameters",
            //         "logs:CreateLogGroup",
            //         "logs:CreateLogStream",
            //         "logs:PutLogEvents"
            //       ],
            //       "Effect": "Allow",
            //       "Resource": "*"
            //     },
            //     {
            //       "Action": [
            //         "ssm:GetParameterHistory",
            //         "ssm:GetParametersByPath",
            //         "ssm:GetParameters",
            //         "ssm:GetParameter",
            //       ],
            //       "Effect": "Allow",
            //       "Resource": {
            //         "Fn::Sub": "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/all/*"
            //       }
            //     },
            //     {
            //       "Action": [
            //         "kms:Decrypt",
            //         "kms:Encrypt"
            //       ],
            //       "Effect": "Allow",
            //       "Resource": {
            //         "Fn::Sub": "arn:aws:kms:${AWS::Region}:${AWS::AccountId}:key/CMK"
            //       }
            //     },
            //     {
            //       "Action": "ses:SendEmail",
            //       "Effect": "Allow",
            //       "Resource": {
            //         "Fn::Sub": "arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/nd.edu"
            //       }
            //     }
            //   ],
            //  "Version": "2012-10-17"
            // }
        }
    ))
    });

    // it('Should have a Lambda defined named \'marble-web-kiosk-export\'.', () => {
    //     assert.expect(MyStack).to(assert.haveResource("AWS::Lambda::Function",{
    //         FunctionName: 'marble-web-kiosk-export'
    // }
    // ))
    // });
    //
    // it('Should have Layers defined named \'sentry-sdk-python-layer:LayerArn\' and \'google-api-python-layer:LayerArn\'.', () => {
    //   assert.expect(MyStack).to(assert.haveResource("AWS::Lambda::Function",{
    //       Layers: [
    //           {
    //             "Fn::ImportValue": "sentry-sdk-python-layer:LayerArn"
    //           },
    //           {
    //             "Fn::ImportValue": "google-api-python-layer:LayerArn"
    //           }
    //     ]
    // }
    // ))
    // });
    //

});

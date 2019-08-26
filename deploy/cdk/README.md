# Useful commands

To deploy, run the following:
 * 'npm run build'   compile typescript to js
 * 'npm test'        runs unit testing on the stack created by the cdk
 * 'cdk synth'       emits the synthesized CloudFormation template
 * 'cdk deploy'      deploy this stack to your default AWS account/region

    Note:  To deploy, first establish an aws session using AWS vault.
      (e.g.  aws-vault exec testlibnd-superAdmin --session-ttl=1h --assume-role-ttl=1h --)

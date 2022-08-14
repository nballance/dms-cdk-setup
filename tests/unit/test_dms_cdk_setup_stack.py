import aws_cdk as core
import aws_cdk.assertions as assertions

from dms_cdk_setup.dms_cdk_setup_stack import DmsCdkSetupStack

# example tests. To run these tests, uncomment this file along with the example
# resource in dms_cdk_setup/dms_cdk_setup_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DmsCdkSetupStack(app, "dms-cdk-setup")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

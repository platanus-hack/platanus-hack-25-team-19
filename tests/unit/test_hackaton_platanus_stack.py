import aws_cdk as core
import aws_cdk.assertions as assertions

from hackaton_platanus.hackaton_platanus_stack import HackatonPlatanusStack


# example tests. To run these tests, uncomment this file along with the example
# resource in hackaton_platanus/hackaton_platanus_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = HackatonPlatanusStack(app, "hackaton-platanus")
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

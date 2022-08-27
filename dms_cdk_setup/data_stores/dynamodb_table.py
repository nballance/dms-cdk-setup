from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
def create_dynamodb_table(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    table = dynamodb.Table(self, "Table",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    # sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
    )
    table.apply_removal_policy(RemovalPolicy.DESTROY)
    return table
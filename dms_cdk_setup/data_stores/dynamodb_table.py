from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_dms as dms,
    aws_rds as rds,
    aws_iam as iam,
    RemovalPolicy,
)
def create_dynamodb_table(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    table = dynamodb.Table(self, "Table",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    # sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
    )
    table.apply_removal_policy(RemovalPolicy.DESTROY)
    return table


# TODO: Add support for DynamoDB endpoint
# DynamoDB uses a "service access role"
def create_dynamodb_endpoint(self, isSource, data_store, set_username):
    # set_engine_name=data_store.engine.engine_type
    # set_port=data_store.instance_endpoint.port
    # set_server_name=data_store.instance_endpoint.hostname
    # set_password=data_store.secret.secret_value_from_json('password').unsafe_unwrap()
    
    resource_endpoint_name="CDKTargetEndpoint"
    set_endpoint_type="target"
    set_endpoint_identifier="cdk-target-endpoint"

    ddb_role = iam.Role(
    self,
    "dms_ddb_role",
    assumed_by=iam.ServicePrincipal("dms.amazonaws.com"),
    managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
    ],
    )
    ddb_role_arn=ddb_role.role_arn

    ddb_instance_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
        endpoint_type=set_endpoint_type, #EndpointType
        engine_name="dynamodb", #engineName is hardcoded with dynamodb
        
        dynamo_db_settings=dms.CfnEndpoint.DynamoDbSettingsProperty(
            service_access_role_arn=ddb_role_arn
        ),
        # database_name=set_database_name, 
        # password=set_password, #need to retrieve from secrets manager
        # username=set_username, #need to retrieve from secrets manager
        # server_name=set_server_name,
        # port=set_port,
        endpoint_identifier=set_endpoint_identifier
    )
    return ddb_instance_endpoint
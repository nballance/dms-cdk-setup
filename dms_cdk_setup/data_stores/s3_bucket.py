from aws_cdk import (
    aws_s3 as s3,
    aws_dms as dms,
    aws_iam as iam,

    RemovalPolicy,
)
import json


# TODO: Add s3 as source/target, trying 'get_cdk_identifier' instead of IF/ELSE check...
def create_s3_bucket(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    bucket = s3.Bucket(self, "Bucket") # Change bucket to stack_name if successful
    bucket.apply_removal_policy(RemovalPolicy.DESTROY)
    return bucket



# TODO: The IAM role only allows access on "s3:*", will this include subdirectories/folders?
# TODO: Currently have random 'external_table_definition', this is used with S3 source.
def create_s3_endpoint(self, isSource, data_store, username):

    if(isSource):
        resource_endpoint_name="CDKSourceEndpoint"
        set_endpoint_type="source"
        set_endpoint_identifier="cdk-source-endpoint"
    else:
        resource_endpoint_name="CDKTargetEndpoint"
        set_endpoint_type="target"
        set_endpoint_identifier="cdk-target-endpoint"

    s3_role = iam.Role(
    self,
    "dms_s3_role",
    assumed_by=iam.ServicePrincipal("dms.amazonaws.com"),
    managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
    ],
    )
    s3_role_arn=s3_role.role_arn

    s3_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
        endpoint_type=set_endpoint_type, #EndpointType
        engine_name="s3", #engineName is hardcoded with dynamodb
        s3_settings=dms.CfnEndpoint.S3SettingsProperty(
            add_column_name=False,
            # bucket_folder="bucketFolder",
            bucket_name=data_store.bucket_name,
            external_table_definition=json.dumps({"TableCount":"1","Tables":[{"TableName":"employee","TablePath":"hr/employee/","TableOwner":"hr","TableColumns":[{"ColumnName":"Id","ColumnType":"INT8","ColumnNullable":"false","ColumnIsPk":"true"},{"ColumnName":"LastName","ColumnType":"STRING","ColumnLength":"20"},{"ColumnName":"FirstName","ColumnType":"STRING","ColumnLength":"30"},{"ColumnName":"HireDate","ColumnType":"DATETIME"},{"ColumnName":"OfficeLocation","ColumnType":"STRING","ColumnLength":"20"}],"TableColumnsTotal":"5"}]}),
            service_access_role_arn=s3_role_arn
        ),
        # database_name=set_database_name, 
        # password=set_password, #need to retrieve from secrets manager
        # username=set_username, #need to retrieve from secrets manager
        # server_name=set_server_name,
        # port=set_port,
        endpoint_identifier=set_endpoint_identifier
    )
    return s3_endpoint

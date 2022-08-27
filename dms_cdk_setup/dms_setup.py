from aws_cdk import (
    aws_dms as dms,
    aws_rds as rds,
    aws_iam as iam,

)
import json


# Full list of settings for CFN endpoints - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dms/CfnEndpoint.html#aws_cdk.aws_dms.CfnEndpoint.S3SettingsProperty


def create_subnet_group(self, vpc):
    tmp = []
    for sub in vpc.private_subnets:
        tmp.append(sub.subnet_id)

    replication_subnet = dms.CfnReplicationSubnetGroup(self, "CDKReplicationSubnetGroup",
        replication_subnet_group_description="CDK replication subnet group",
        replication_subnet_group_identifier="cdk-replication-subnet-group",
        subnet_ids=tmp
    )
    return replication_subnet

def create_DMS_replication_instance(self, replication_subnet, self_referencing_security_group):
        replication_instance = dms.CfnReplicationInstance(self, "CDKReplicationInstance",
            replication_instance_class="dms.t3.small",
            replication_subnet_group_identifier=replication_subnet.ref,
            publicly_accessible=False,
            vpc_security_group_ids=[self_referencing_security_group.security_group_id], # Add rule
            replication_instance_identifier="cdk-replication-instance", 
        )
        return replication_instance

# TODO: Migrate from 'dms_cdk_setup_stack.py'
def create_DMS_replication_task(self, replication_instance, source_endpoint, target_endpoint):
    set_source_endpoint_arn = source_endpoint.ref
    set_target_endpoint_arn = target_endpoint.ref
    set_replication_instance_arn = replication_instance.ref

    replication_task = dms.CfnReplicationTask(self, "CDKReplicationTask",
        migration_type="full-load", # full-load | cdc | full-load-and-cdc
        replication_instance_arn=set_replication_instance_arn, # replication_instance
        source_endpoint_arn=set_source_endpoint_arn, # source endpoint
        target_endpoint_arn=set_target_endpoint_arn, # target endpoint
        table_mappings= json.dumps({"rules":[{"rule-type":"selection","rule-id":"1","rule-name":"1","object-locator":{"schema-name":"%","table-name":"%"},"rule-action":"include"}]}),
        resource_identifier="cdk-replication-task-ri",
        replication_task_identifier="cdk-replication-task-i",
        # the properties below are optional
        # cdc_start_position="cdcStartPosition",
        # cdc_start_time=123,
        # cdc_stop_position="cdcStopPosition",
        # replication_task_identifier="replicationTaskIdentifier",
        # replication_task_settings="replicationTaskSettings",
        # tags=[CfnTag(
        #     key="key",
        #     value="value"
        # )],
        # task_data="taskData"
    )
    add_DMS_replication_task_dependencies(self, replication_task, replication_instance, source_endpoint, target_endpoint)


def add_DMS_replication_task_dependencies(self, replication_task, replication_instance, source_endpoint, target_endpoint):
    replication_task.add_depends_on(replication_instance)
    replication_task.add_depends_on(source_endpoint)
    replication_task.add_depends_on(target_endpoint)


def create_aurora_endpoint(self, isSource, data_store, set_username):
    if(type(data_store) == rds.DatabaseCluster):
        set_database_name=''
        print('default engine name')
        set_engine_name=''
        if(data_store.engine.engine_type == 'aurora-mysql' or data_store.engine.engine_type=='aurora'):
            print('aurora-mysql/aurora engine name')
            set_database_name=''
            set_engine_name='aurora'
        elif(data_store.engine.engine_type == 'aurora-postgresql'):
            print('aurora-postgresql engine name')
            set_database_name='postgres'
            set_engine_name=data_store.engine.engine_type
        else:
            print(data_store.engine.engine_type)
            print('INVALID ENGINE NAME')

        set_password=data_store.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

        # Returns the writer instance host name for DB cluster (e.g. Aurora PostgreSQL), the writer instance host name for a DB instance (e.g. Oracle RDS)
        set_host_name_object=find_host_name_object(self, data_store)
        set_server_name=data_store.cluster_endpoint.hostname
        set_port=data_store.cluster_endpoint.port
    if(isSource):
        resource_endpoint_name="CDKSourceEndpoint"
        set_endpoint_type="source"
        set_endpoint_identifier="cdk-source-endpoint"
    else:
        resource_endpoint_name="CDKTargetEndpoint"
        set_endpoint_type="target"
        set_endpoint_identifier="cdk-target-endpoint"

    if(data_store.engine == 'aurora-mysql'): # MySQL does not have a database_name
        aurora_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )
    else: #(data_store.engine == 'aurora-postgresql'):
        aurora_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name=set_database_name, 
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )

    aurora_endpoint.add_depends_on(set_host_name_object) # need to wait on host name to resolve
    return aurora_endpoint

# TODO: Pass in the set values. Set the values in the data_store_setup file
def create_database_instance_endpoint(self, isSource, data_store, set_username):
    set_engine_name=data_store.engine.engine_type
    set_port=data_store.instance_endpoint.port
    set_server_name=data_store.instance_endpoint.hostname
    set_password=data_store.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

    set_host_name_object=find_host_name_object(self, data_store)

    # TODO: Make a function to get database_name and call it. Determine all database_name attributes, for now mysql and postgres
    set_database_name=''
    if(data_store.engine.engine_type=='postgres'):
        set_database_name=data_store.engine.engine_type
    elif(data_store.engine.engine_type=='mysql'):
        print('database instance endpoint engine is mysql')
    elif(data_store.engine.engine_type=='mariadb'):
        print('database instance endpoint engine is mariadb')
    elif(data_store.engine.engine_type=='sqlserver-web'):
        print('database instance endpoint engine is sqlserver-web')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
        # TODO: Test Endpoint failed: Application-Status: 1020912, Application-Message: Cannot connect to SQL Server Authentication failed, Application-Detailed-Message: RetCode: SQL_ERROR SqlState: 28000 NativeError: 18456 Message: [unixODBC][Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Login failed for user 'syscdk'.
    elif(data_store.engine.engine_type=='sqlserver-ex'):
        print('database instance endpoint engine is sqlserver-ex')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
    elif(data_store.engine.engine_type=='sqlserver-se'):
        print('database instance endpoint engine is sqlserver-se')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
    elif(data_store.engine.engine_type=='sqlserver-ee'):
        print('database instance endpoint engine is sqlserver-ee')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
    else:
        print('Current database instance endpoint engine is not supported')

    if(isSource):
        resource_endpoint_name="CDKSourceEndpoint"
        set_endpoint_type="source"
        set_endpoint_identifier="cdk-source-endpoint"
    else:
        resource_endpoint_name="CDKTargetEndpoint"
        set_endpoint_type="target"
        set_endpoint_identifier="cdk-target-endpoint"

    if(data_store.engine == 'mysql' or data_store.engine == 'mariadb'): # MySQL does not have a database_name
        database_instance_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )
    else: #TODO: (data_store.engine == 'postgres'): Need to check for other engines the default 'database_name' e.g. oracle, sql server, mariadb, etc
        database_instance_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name=set_database_name, 
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )

    # TODO: test if this is needed since this function is only called after the start of the instance
    database_instance_endpoint.add_depends_on(set_host_name_object) # need to wait on host name to resolve
    return database_instance_endpoint


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


# Function to find the main host name. For DB instance this is the DB instance. For Aurora this is the writer. Depends on the type
def find_host_name_object(self, data_store):
    if(type(data_store) == rds.DatabaseCluster):
        for child in data_store.node.children:
            if(type(child) == rds.CfnDBInstance):  # For now we filter by type DB Instance, since we deploy one instance this should be the writer.
                host_name_object=child
                return host_name_object
    elif(type(data_store) == rds.DatabaseInstance):
        for child in data_store.node.children:
            if(type(child) == rds.CfnDBInstance):  # For now we filter by type DB Instance, since we deploy one instance this should be the writer.
                host_name_object=child
                return host_name_object
    else:
        print('find_host_name_object type not defined')
        return ''

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

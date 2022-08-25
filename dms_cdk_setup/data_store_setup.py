from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy,
    aws_dynamodb as dynamodb
)
from .dms_setup import *

# TODO Would it be better to have an, isvalidsource/isvalidtarget function rather than this if(isSource) block?
# TODO: Decide whether to have a is_valid_data_store() function instead of in this create function
# TODO: Create the data store for either source or target from engine input, username, and security group to apply
def create_data_store(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    # TODO: Check if this is a valid source
    if(isSource):
        if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_aurora_endpoint(self, isSource, data_store, username)

        # TODO: make a list of possible RDS DB instances and check if in list
        elif (engine == 'postgres' or engine == 'mariadb' or engine == 'mysql' or engine == 'oracle-ee' or engine == 'oracle-se2' or engine == 'oracle-se1' or engine == 'oracle-se' or engine == 'postgres' or engine == 'sqlserver-ee' or engine == 'sqlserver-se' or engine == 'sqlserver-ex' or engine == 'sqlserver-web'):
            data_store=create_database_instance(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_database_instance_endpoint(self, isSource, data_store, username)





        # TODO: DocumentDB Cluster - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_docdb/README.html
        # elif(source_engine == 'documentdb'): 
        # RDS INSTANCE: postgres, mysql, ... ,  - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/CfnDBInstance.html
        # TODO: support all valid RDS instance options
        # mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
        # if(source_engine == 'postgres' or source_engine == 'mysql'):
        #     if(source_engine == 'postgres'):
        #         set_target_engine=rds.DatabaseInstanceEngine.POSTGRES # Default PostgreSQL engine version
        #     elif(source_engine == 'mysql'):
        #         set_target_engine=rds.DatabaseInstanceEngine.MYSQL # Default MySQL engine version
            
        #     source_instance = rds.DatabaseInstance(self, "Instance",
        #         engine=set_target_engine
        #     )
        #     source=source_instance
        # S3 BUCKET
        # elif(source_engine == 's3'):
        #     source_bucket = s3.Bucket(self, "dms-cdk-setup")
        #     source_bucket.apply_removal_policy(RemovalPolicy.DESTROY)
        #     source=source_bucket
        else:
            print('create_data_store Source is undocumented')
        return data_store_endpoint
    
    # TODO: Check if this is a valid target
    else:
        if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_aurora_endpoint(self, isSource, data_store, username)
        elif (engine == 'postgres' or engine == 'mariadb' or engine == 'mysql' or engine == 'oracle-ee' or engine == 'oracle-se2' or engine == 'oracle-se1' or engine == 'oracle-se' or engine == 'postgres' or engine == 'sqlserver-ee' or engine == 'sqlserver-se' or engine == 'sqlserver-ex' or engine == 'sqlserver-web'):
            data_store=create_database_instance(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_database_instance_endpoint(self, isSource, data_store, username)

        elif (engine == 'dynamodb'):
            data_store=create_ddb_table(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_ddb_endpoint(self, isSource, data_store, username)

        # TODO: Need to input all possible valid targets
        # TODO: DocumentDB
        # elif(target_engine == 'documentdb'):
        #     target='documentdb'

        # TODO: support all valid RDS instance options
        # mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
        # elif(target_engine == 'postgres'):
        #     target='postgres'

        # TODO: S3
        # TODO: Redshift
        # TODO: DynamoDB
        # TODO: Kafka
        # TODO: Kinesis
        # TODO: DynamoDB
        # TODO: Neptune
        # TODO: Redis
        # TODO: OpenSearch
        # TODO: Babelfish
        else:
            print('create_data_store Target is undocumented')
        return data_store_endpoint


# TODO: Create functions to create each data store
def create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    if(engine == 'aurora-postgresql'):
        print('aurora-postgresql')
        set_engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_12_11) # Default Aurora PostgreSQL engine version is 12.11
        cluster_parameter_group_aurora={
            "rds.logical_replication": "1"
        }
    else: #(engine == 'aurora-mysql'):
        print('aurora-mysql')
        set_engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0) # Default Aurora MySQL engine version is 3.01.0
        cluster_parameter_group_aurora={
            "binlog_format": "ROW"
        }

    if(isSource):
        identifier="cdk-source"
    else:
        identifier="cdk-target"


    cluster = rds.DatabaseCluster(self, stack_name,
        engine=set_engine,  # Aurora MySQL: engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
        credentials=rds.Credentials.from_generated_secret(username),  # Optional - will default to 'admin' username and generated password
        instances=1, #TODO: comment out if no instances deployed, need to find out how to deploy only writer
        cluster_identifier=identifier,
        # parameters=add_parameter()
        instance_props=rds.InstanceProps(
            # TODO: Make this publicly accessible and launch in public subnet
            # instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
            security_groups=[self_referencing_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            vpc=vpc,   
        ),
        parameters=cluster_parameter_group_aurora
    )
    cluster.apply_removal_policy(RemovalPolicy.DESTROY)

    return cluster

# TODO: Create valid RDS instance types: mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
# TODO: Test Endpoint failed: Application-Status: 1020912, Application-Message: Failed to connect Network error has occurred, Application-Detailed-Message: RetCode: SQL_ERROR SqlState: 08001 NativeError: 101 Message: [unixODBC]timeout expired
# retrying fails...need to check networking
def create_database_instance(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    if(isSource):
        identifier="cdk-source"
    else:
        identifier="cdk-target"

    if(engine == 'mariadb'): 
        print('mariadb')
        set_engine=rds.DatabaseInstanceEngine.MARIADB
    elif(engine == 'mysql'): 
        print('mysql')
        set_engine=rds.DatabaseInstanceEngine.MYSQL

    elif(engine == 'postgres'):
        print('postgres')
        set_engine=rds.DatabaseInstanceEngine.POSTGRES
    elif(engine == 'sqlserver-ee'): 
        print('sqlserver-ee')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_EE
    elif(engine == 'sqlserver-se'): 
        print('sqlserver-se')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_SE  
    elif(engine == 'sqlserver-ex'): 
        print('sqlserver-ex')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_EX
    elif(engine == 'sqlserver-web'): 
        print('sqlserver-web')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_WEB
    '''
    elif(engine == 'oracle-ee'): # Cannot test/deploy Oracle in personal account
        print('oracle-ee')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1)   
    elif(engine == 'oracle-se2'): # Cannot test/deploy Oracle in personal account
        print('oracle se2')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1) 
    elif(engine == 'oracle-se1'): # Cannot test/deploy Oracle in personal account
        print('oracle-se1')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1)    
    elif(engine == 'oracle-se'): # Cannot test/deploy Oracle in personal account
        print('oracle-se')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1) 
    '''
    
    instance = rds.DatabaseInstance(self, "Instance",
        engine=set_engine,
        instance_identifier=identifier,
        # optional, defaults to m5.large
        instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
        credentials=rds.Credentials.from_generated_secret(username),  # Optional - will default to 'admin' username and generated password
        vpc=vpc,
        vpc_subnets=ec2.SubnetSelection( # Double check same networking subnets, no new subnets created
            subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
        ),
        security_groups=[self_referencing_security_group],
    )
    instance.apply_removal_policy(RemovalPolicy.DESTROY)

    return instance

def create_ddb_table(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    table = dynamodb.Table(self, "Table",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    # sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
    )
    table.apply_removal_policy(RemovalPolicy.DESTROY)
    return table
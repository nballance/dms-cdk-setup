from dms_cdk_setup.data_stores.dynamodb_table import create_dynamodb_endpoint, create_dynamodb_table
from dms_cdk_setup.data_stores.s3_bucket import create_s3_bucket, create_s3_endpoint
from dms_cdk_setup.data_stores.rds_database_instance import create_database_instance, create_database_instance_endpoint
from dms_cdk_setup.data_stores.rds_database_cluster import create_aurora, create_aurora_endpoint

from .dms_setup import *

# TODO Would it be better to have an, isvalidsource/isvalidtarget function rather than this if(isSource) block?
# TODO: Decide whether to have a is_valid_data_store() function instead of in this create function
# TODO: Create the data store for either source or target from engine input, username, and security group to apply
def create_data_store(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    # TODO: Check if this is a valid source
    aurora_engines=['aurora-postgresql', 'aurora-mysql']
    rds_instance_engines=['mariadb', 'mysql', 'oracle-ee', 'oracle-se2', 'oracle-se1', 'oracle-se', 'postgres', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web']


    if(isSource):
        # if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
        if(engine in aurora_engines):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_aurora_endpoint(self, isSource, data_store, username)

        # TODO: make a list of possible RDS DB instances and check if in list
        # elif (engine == 'postgres' or engine == 'mariadb' or engine == 'mysql' or engine == 'oracle-ee' or engine == 'oracle-se2' or engine == 'oracle-se1' or engine == 'oracle-se' or engine == 'postgres' or engine == 'sqlserver-ee' or engine == 'sqlserver-se' or engine == 'sqlserver-ex' or engine == 'sqlserver-web'):
        elif (engine in rds_instance_engines):
            data_store=create_database_instance(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_database_instance_endpoint(self, isSource, data_store, username)

        elif (engine == 's3'):
            data_store=create_s3_bucket(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_s3_endpoint(self, isSource, data_store, username)
        



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
        if(engine in aurora_engines):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_aurora_endpoint(self, isSource, data_store, username)
        elif (engine in rds_instance_engines):
            data_store=create_database_instance(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_database_instance_endpoint(self, isSource, data_store, username)

        elif (engine == 'dynamodb'):
            data_store=create_dynamodb_table(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_dynamodb_endpoint(self, isSource, data_store, username)

        elif (engine == 's3'):
            data_store=create_s3_bucket(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
            data_store_endpoint=create_s3_endpoint(self, isSource, data_store, username)

        # TODO: Need to input all possible valid targets
        # TODO: DocumentDB
        # elif(target_engine == 'documentdb'):
        #     target='documentdb'

        # TODO: support all valid RDS instance options
        # mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
        # elif(target_engine == 'postgres'):
        #     target='postgres'

        # TODO: Redshift
        # TODO: Kafka
        # TODO: Kinesis
        # TODO: Neptune
        # TODO: Redis
        # TODO: OpenSearch
        # TODO: Babelfish
        else:
            print('create_data_store Target is not implemented')
        return data_store_endpoint

# Simple function to map the isSource value to the CDK identifier value -- possibly use this in the dms_setup file
def get_cdk_identifier(isSource):
    if(isSource):
        identifier="cdk-source"
    else:
        identifier="cdk-target"
    return identifier

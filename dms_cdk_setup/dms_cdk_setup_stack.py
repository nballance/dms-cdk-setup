from distutils import core
from aws_cdk import (
    # Duration,
    Stack,
    aws_dms as dms,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    RemovalPolicy,
)
import json

from constructs import Construct

from .vpc_setup import *
from .dms_setup import *
from .data_store_setup import *


class DmsCdkSetupStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: Create a README with format similar to - https://github.com/aws-samples/dms-cdk


        ######################################################
        # Set the source engine, e.g.                        #
        # source_engine = 'aurora-postgresql'                #
        #                                                    #
        # Set the target engine, e.g.                        #
        # target_engine = 'kafka'                            #
        ######################################################
        source_engine='aurora-postgresql'
        # source_password='replaceme123' #TODO: It is not best practice to have password in CDK, can manually retrieve from secrets manager
        source_username='syscdk'
        target_engine = 'aurora-postgresql'
        target_username=source_username

        """
        Phase #1: Create VPC and Security Groups
        Phase #2: Provision source
        Phase #3: Provision target
        Phase #4: Create source and target endpoint
        Phase #5: Create DMS replication instance and DMS task
        """
       
        """
        Phase #1: Create VPC and Security Groups
        Create with best practices in mind for public and private subnets
        """
        vpc=create_VPC(self)
        self_referencing_security_group=create_self_referencing_security_group(self, vpc)


        """
        Phase #2: Provision source - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.html
        This will be the bulk of the code. Need to provision infrastructure based on inputs. Will make check if it is valid source EP here.
        """

        # TODO: Call source=create_data_store(self, source_engine, source_username, self_referencing_security_group, vpc)
        # TODO: Need to set the correct resource for the wait dependency. With aurora this is the writer instance, with normal DB this is the instance itself
        # if(source_engine == 'aurora-postgresql' or source_engine == 'aurora-mysql'):
        isSource=True
        source=create_data_store(self, isSource, source_engine, source_username, self_referencing_security_group, vpc, "CDKDataStoreSource")
        
        # TODO: Create dependency function: different for aurora cluster vs RDS DB instance
        for child in source.node.children:
            if(type(child) == rds.CfnDBInstance):  # For nwo we filter by type DB Instance, since we deploy one instance this should be the writer.
                source_writer=child

            source_password=source.secret.secret_value_from_json('password').unsafe_unwrap() # Configure password with best practice
        # source_host_name_object=find_host_name_object(self, source) ---- returns the source_writer for aurora

        # TODO: DocumentDB Cluster - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_docdb/README.html
        # elif(source_engine == 'documentdb'): 


        # RDS INSTANCE: postgres, mysql, ... ,  - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/CfnDBInstance.html
        # TODO: support all valid RDS instance options
        # mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
        if(source_engine == 'postgres' or source_engine == 'mysql'):
            if(source_engine == 'postgres'):
                set_target_engine=rds.DatabaseInstanceEngine.POSTGRES # Default PostgreSQL engine version
            elif(source_engine == 'mysql'):
                set_target_engine=rds.DatabaseInstanceEngine.MYSQL # Default MySQL engine version
            
            source_instance = rds.DatabaseInstance(self, "Instance",
                engine=set_target_engine
            )
            source=source_instance


        # S3 BUCKET
        elif(source_engine == 's3'):
            source_bucket = s3.Bucket(self, "dms-cdk-setup")
            source_bucket.apply_removal_policy(RemovalPolicy.DESTROY)
            source=source_bucket
        
        """
        Phase #3: Provision target - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.html
        This will be the bulk of the code. Need to provision infrastructure based on inputs. Will make check if it is valid target EP here.
        """

        isSource=False
        target=create_data_store(self, isSource, target_engine, target_username, self_referencing_security_group, vpc, "CDKDataStoreTarget")

        # TODO: Create dependency function: different for aurora cluster vs RDS DB instance
        for child in target.node.children:
            if(type(child) == rds.CfnDBInstance):  # For nwo we filter by type DB Instance, since we deploy one instance this should be the writer.
                target_writer=child

            target_password=target.secret.secret_value_from_json('password').unsafe_unwrap() # Configure password with best practice

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

        """
        Phase #4: Create source and target endpoint
        https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_dms/CfnEndpoint.html
        """
        # Supported Sources for data migration - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Introduction.Sources.html
        # Supported Targets for data migration - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Introduction.Targets.html

        # TODO: source endpoint
        # Checks if cluster type
        if(type(source) == rds.DatabaseCluster):
            set_source_engine_name=source.engine.engine_type
            # set_source_server_name=source_cluster.cluster_endpoint.hostname
            # set_source_port=source_cluster.cluster_endpoint.port
            
            set_source_server_name=source.cluster_endpoint.hostname
            set_source_port=source.cluster_endpoint.port
        # if(type(source) == rds.Database)
        # if(type(source) == docdb.DatabaseCluster)

        # Currently using cluster, will need to use generic object.
        source_endpoint = dms.CfnEndpoint(source, "CDKSourceEndpoint",
            endpoint_type="source", #EndpointType
            engine_name=set_source_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name="postgres", 
            password=source_password, #need to retrieve from secrets manager
            username=source_username, #need to retrieve from secrets manager
            server_name=set_source_server_name,
            port=set_source_port,
            endpoint_identifier="cdk-source-endpoint"
        )
        source_endpoint.add_depends_on(source_writer) # need to wait on writer instance host name to resolve

        # TODO: Target endpoint 
        # Checks if cluster type
        if(type(target) == rds.DatabaseCluster):
            print('target is Aurora')
            # TODO: add target info
            set_target_engine_name=target.engine.engine_type
            set_target_server_name=target.cluster_endpoint.hostname
            set_target_port=target.cluster_endpoint.port
        
        # Currently using cluster, will need to use generic object.
        target_endpoint = dms.CfnEndpoint(target, "CDKTargetEndpoint",  
            endpoint_type="target", #EndpointType
            engine_name=set_target_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name="postgres", 
            password=target_password, #need to retrieve from secrets manager
            username=target_username, #need to retrieve from secrets manager
            server_name=set_target_server_name,
            port=set_target_port,
            endpoint_identifier="cdk-target-endpoint"
        )
        target_endpoint.add_depends_on(target_writer)        

        """
        Phase #5: Create DMS replication instance and DMS task
        
        """

        rep_sub=create_subnet_group(self, vpc)

        replication_instance=create_DMS_replication_instance(self, rep_sub, self_referencing_security_group)

        create_DMS_replication_task(self, replication_instance, source_endpoint, target_endpoint)
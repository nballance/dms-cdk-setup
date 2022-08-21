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
        """
        isSource=True
        source=create_data_store(self, isSource, source_engine, source_username, self_referencing_security_group, vpc, "CDKDataStoreSource")
        
        source_password=source.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

        # Returns the writer instance host name for DB cluster (e.g. Aurora PostgreSQL), the writer instance host name for a DB instance (e.g. Oracle RDS)
        source_host_name_object=find_host_name_object(self, source)
                

        """
        Phase #3: Provision target - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.html
        This will be the bulk of the code. Need to provision infrastructure based on inputs. Will make check if it is valid target EP here.
        """
        isSource=False
        target=create_data_store(self, isSource, target_engine, target_username, self_referencing_security_group, vpc, "CDKDataStoreTarget")

        target_password=target.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

        # Returns the writer instance host name for DB cluster (e.g. Aurora PostgreSQL), the writer instance host name for a DB instance (e.g. Oracle RDS)
        target_host_name_object=find_host_name_object(self, target)


        """
        Phase #4: Create source and target endpoint
        https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_dms/CfnEndpoint.html
        """
        # TODO: Separate logic for endpoints to separate file
        # This should be handled in Phase #2 with a function
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
        source_endpoint.add_depends_on(source_host_name_object) # need to wait on host name to resolve

        # TODO: Separate logic for endpoints to separate file
        # This should be handled in Phase #3 with a function
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
        target_endpoint.add_depends_on(target_host_name_object)        

        """
        Phase #5: Create DMS replication instance and DMS task
        """
        rep_sub=create_subnet_group(self, vpc)
        replication_instance=create_DMS_replication_instance(self, rep_sub, self_referencing_security_group)
        create_DMS_replication_task(self, replication_instance, source_endpoint, target_endpoint)
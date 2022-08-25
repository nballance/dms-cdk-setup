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
        source_engine='postgres'
        # source_password='replaceme123' #TODO: It is not best practice to have password in CDK, can manually retrieve from secrets manager
        source_username='syscdk'
        target_engine = 'dynamodb'
        target_username=source_username

        # Create VPC and Security Group
        vpc=create_VPC(self)
        self_referencing_security_group=create_self_referencing_security_group(self, vpc)

        # Create source data store and endpoint https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.html
        isSource=True
        source_endpoint=create_data_store(self, isSource, source_engine, source_username, self_referencing_security_group, vpc, "CDKDataStoreSource")

        # Create target data store and endpoint https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.html
        isSource=False
        target_endpoint=create_data_store(self, isSource, target_engine, target_username, self_referencing_security_group, vpc, "CDKDataStoreTarget")

        # Create DMS replication instance and DMS task
        replication_subnet=create_subnet_group(self, vpc)
        replication_instance=create_DMS_replication_instance(self, replication_subnet, self_referencing_security_group)
        create_DMS_replication_task(self, replication_instance, source_endpoint, target_endpoint)
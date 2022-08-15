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

from constructs import Construct

class DmsCdkSetupStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # source_endpoint = 'aurora-postgresql'
        # target_endpoint = 'kafka'

        """
        Phase #1: Create VPC and Security Groups
        Phase #2: Provision source and target resources
        Phase #3: Create source and target endpoint
        Phase #4: Create DMS replication instance and DMS task
        """




        
        """
        Phase #1: Create VPC and Security Groups
        Create with best practices in mind for public and private subnets
        """
        vpc = ec2.Vpc(self, 'DMSVPC', 
            cidr="10.0.0.0/16",
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='public1',
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='private1',
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                )
            ]  
        )

        # vpc = ec2.Vpc(self, "DMSVPC",
        #     cidr="10.0.0.0/16"
        # )     
        #    

        """
        Phase #2: Provision source and target resources
        This will be the bulk of the code. Need to provision infrastructure based on inputs. Will make check if it is valid source/target EP here.
        """
        # RDS CLUSTER: Aurora PostgreSQL/MySQL 
        # Valid for: Source and Target

        # if(source_endpoint = 'aurora-postgresql')
        cluster = rds.DatabaseCluster(self, "Database",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_12_11),  # Aurora MySQL: engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
            credentials=rds.Credentials.from_generated_secret("username"),  # Optional - will default to 'admin' username and generated password
            instance_props=rds.InstanceProps(
                # optional , defaults to t3.medium
                # instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                ),
                vpc=vpc
            )
        )



        # S3 BUCKET
        # Valid for: Source and Target
        bucket = s3.Bucket(self, "dms-cdk-setup")
        bucket.apply_removal_policy(RemovalPolicy.DESTROY)


        """
        Phase #3: Create source and target endpoint
        https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_dms/CfnEndpoint.html
        """
        # Supported Sources for data migration - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Introduction.Sources.html
        # Supported Targets for data migration - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Introduction.Targets.html


        source_endpoint = dms.CfnEndpoint(self, "CDKSourceEndpoint",
        endpoint_type="source", #EndpointType
        engine_name="aurora-postgresql", #engineName; engine_name = source_endpoint
        database_name="postgres", #databaseName
        password="password", #need to retrieve from secrets manager
        username="username", #need to retrieve from secrets manager
        server_name="serverName",
        port=5432,
        )

        """
        Phase #4: Create DMS replication instance and DMS task
        
        """
        tmp = []
        for sub in vpc.private_subnets:
            tmp.append(sub.subnet_id)

        rep_sub = dms.CfnReplicationSubnetGroup(self, "rep_sub",
            replication_subnet_group_description="desc rep_sub",
            subnet_ids=tmp
        )

        replication_instance = dms.CfnReplicationInstance(self, "rep-instance",
            replication_instance_class="dms.t3.small",
            replication_subnet_group_identifier=rep_sub.ref,
            publicly_accessible=False
        )

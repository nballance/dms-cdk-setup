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
        Phase #2: Provision source - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.html
        This will be the bulk of the code. Need to provision infrastructure based on inputs. Will make check if it is valid source EP here.
        """

        # RDS CLUSTER: aurora-postgresql and aurora-mysql - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/CfnDBCluster.html
        # Valid for: Source and Target
        # TODO: get rid of Secrets Manager and manually use password+username, may need to create DatabaseInstance - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html
        # TODO: setup custom parameter groups for CDC replication
        if(source_engine == 'aurora-postgresql' or source_engine == 'aurora-mysql'):
            if(source_engine == 'aurora-postgresql'):
                set_source_engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_12_11) # Default Aurora PostgreSQL engine version is 12.11
            if(source_engine == 'aurora-mysql'):
                set_source_engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0) # Default Aurora MySQL engine version is 3.01.0
        
            source_cluster = rds.DatabaseCluster(self, "Source Cluster",
                engine=set_source_engine,  # Aurora MySQL: engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
                credentials=rds.Credentials.from_generated_secret(source_username),  # Optional - will default to 'admin' username and generated password
                instances=1, #TODO: comment out if no instances deployed, need to find out how to deploy only writer
                # credentials=rds.Credentials.from_password(source_username, source_password), #TODO: It is not recommended to expose password in CDK, manual process to view secrets manager created and use auto-generated value
                instance_props=rds.InstanceProps(
                    # optional , defaults to t3.medium
                    # instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
                    vpc_subnets=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                    ),
                    vpc=vpc
                )
            )
            # TODO: Print secret password value for easy access
            # Set the source object details
            source = source_cluster
        
        # TODO: DocumentDB Cluster - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_docdb/README.html
        # elif(source_engine == 'documentdb'): 


        # RDS INSTANCE: postgres, mysql, ... ,  - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/CfnDBInstance.html
        # TODO: support all valid RDS instance options
        # mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
        elif(source_engine == 'postgres' or source_engine == 'mysql'):
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
        # TODO: aurora-postgresql or aurora-mysql
        if(target_engine == 'aurora-postgresql' or target_engine == 'aurora-mysql'):
            if(target_engine == 'aurora-postgresql'):
                set_target_engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_12_11) # Default Aurora PostgreSQL engine version is 12.11
            if(target_engine == 'aurora-mysql'):
                set_target_engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0) # Default Aurora MySQL engine version is 3.01.0
            
            target_cluster = rds.DatabaseCluster(self, "Target Cluster",
                engine=set_target_engine,  # Aurora MySQL: engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
                credentials=rds.Credentials.from_generated_secret(target_username),  # Optional - will default to 'admin' username and generated password
                instances=1, #TODO: comment out if no instances deployed, need to find out how to deploy only writer
                # credentials=rds.Credentials.from_password(source_username, source_password), #TODO: It is not recommended to expose password in CDK, manual process to view secrets manager created and use auto-generated value
                instance_props=rds.InstanceProps(
                    # optional , defaults to t3.medium
                    # instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
                    vpc_subnets=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                    ),
                    vpc=vpc
                )
            )
            target = target_cluster


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
            set_engine_name=source.engine.engine_type
            set_server_name=source_cluster.cluster_endpoint.hostname
            set_port=source_cluster.cluster_endpoint.port
        # if(type(source) == rds.Database)
        # if(type(source) == docdb.DatabaseCluster)

        # Currently using cluster, will need to use generic object.
        source_endpoint = dms.CfnEndpoint(source, "CDKSourceEndpoint",
            endpoint_type="source", #EndpointType
            engine_name=source.engine.engine_type, #engineName; engine_name = source_endpoint # cluster.engine
            database_name="postgres", 
            password="password", #need to retrieve from secrets manager
            username=source_username, #need to retrieve from secrets manager
            # TODO: Currently server_name is for Aurora cluster only
            # server_name=cluster.cluster_endpoint.hostname,
            server_name=set_server_name,
            port=set_port,
        )
        set_source_endpoint_arn = source_endpoint.ref
        # TODO: Need to TestConnection - https://stackoverflow.com/questions/50512065/unable-to-test-aws-dms-end-points-in-cloud-fromation-template
        # Option is to deploy a lambda and execute code to test connection

        # TODO: Target endpoint 
        # Checks if cluster type
        if(type(target) == rds.DatabaseCluster):
            print('target is Aurora')
            # TODO: add target info
            set_engine_name=target.engine.engine_type
            set_server_name=target_cluster.cluster_endpoint.hostname
            set_port=target_cluster.cluster_endpoint.port
        # if(type(source) == rds.Database)
        # if(type(source) == docdb.DatabaseCluster)
        
        # Currently using cluster, will need to use generic object.
        target_endpoint = dms.CfnEndpoint(source, "CDKTargetEndpoint",
            endpoint_type="target", #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name="postgres", 
            password="password", #need to retrieve from secrets manager
            username=target_username, #need to retrieve from secrets manager
            # TODO: Currently server_name is for Aurora cluster only
            # server_name=cluster.cluster_endpoint.hostname,
            server_name=set_server_name,
            port=set_port,
        )
        set_target_endpoint_arn = target_endpoint.ref
        

        """
        Phase #5: Create DMS replication instance and DMS task
        
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
        set_replication_instance_arn = replication_instance.ref


            


        # TODO: Create Replication Task - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dms/CfnReplicationTask.html
        # Need to wait on source, target, replication instance, test endpoints.
        replication_task = dms.CfnReplicationTask(self, "MyCfnReplicationTask",
            migration_type="full-load", # full-load | cdc | full-load-and-cdc
            replication_instance_arn=set_replication_instance_arn, # replication_instance
            source_endpoint_arn=set_source_endpoint_arn, # source endpoint
            target_endpoint_arn=set_target_endpoint_arn, # target endpoint
            table_mappings= json.dumps({"rules":[{"rule-type":"selection","rule-id":"1","rule-name":"1","object-locator":{"schema-name":"%","table-name":"%"},"rule-action":"include"}]}),


            # the properties below are optional
            # cdc_start_position="cdcStartPosition",
            # cdc_start_time=123,
            # cdc_stop_position="cdcStopPosition",
            # replication_task_identifier="replicationTaskIdentifier",
            # replication_task_settings="replicationTaskSettings",
            resource_identifier="CDKDMSTask",
            # tags=[CfnTag(
            #     key="key",
            #     value="value"
            # )],
            # task_data="taskData"
        )
        replication_task.add_depends_on(replication_instance)
        replication_task.add_depends_on(source_endpoint)
        replication_task.add_depends_on(target_endpoint)
        

from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy,

)

# TODO: Decide whether to have a is_valid_data_store() function instead of in this create function
# TODO: Create the data store for either source or target from engine input, username, and security group to apply
def create_data_store(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):

    # TODO: Check if this is a valid source
    if(isSource):
        if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
        # TODO: Need to input all possible valid sources
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
        return data_store
    
    # TODO: Check if this is a valid target
    else:
        if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
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
        return data_store


# TODO: Create functions to create each data store
def create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    if(engine == 'aurora-postgresql'):
            set_engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_12_11) # Default Aurora PostgreSQL engine version is 12.11
    else: #(engine == 'aurora-mysql'):
        set_engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0) # Default Aurora MySQL engine version is 3.01.0

    if(isSource):
        identifier="cdk-source"
    else:
        identifier="cdk-target"

    cluster = rds.DatabaseCluster(self, stack_name,
        engine=set_engine,  # Aurora MySQL: engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
        credentials=rds.Credentials.from_generated_secret(username),  # Optional - will default to 'admin' username and generated password
        instances=1, #TODO: comment out if no instances deployed, need to find out how to deploy only writer
        cluster_identifier=identifier,
        instance_props=rds.InstanceProps(
            # TODO: Make this publicly accessible and launch in public subnet
            # optional , defaults to t3.medium
            # instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
            security_groups=[self_referencing_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            vpc=vpc
        )
        # TODO: RDS INSTANCE SECURITY GROUP DOES NOT ALLOW ANY INBOUND RULES
    )
    cluster.apply_removal_policy(RemovalPolicy.DESTROY)

    # TODO: Print secret password value for easy access
    # Set the source object details
    return cluster


# Function to find the main host name. For DB instance this is the DB instance. For Aurora this is the writer. Depends on the type
def find_host_name_object(self, data_store):
    if(type(data_store) == rds.DatabaseCluster):
        for child in data_store.node.children:
            if(type(child) == rds.CfnDBInstance):  # For now we filter by type DB Instance, since we deploy one instance this should be the writer.
                host_name_object=child
                return host_name_object

    else:
        print('find_host_name_object type not defined')
        return ''
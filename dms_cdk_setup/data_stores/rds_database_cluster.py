from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy,
)

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
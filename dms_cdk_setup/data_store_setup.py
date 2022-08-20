from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy,

)


# TODO: Create the data store for either source or target from engine input, username, and security group to apply
def create_data_store(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):

    # TODO: Check if this is a valid source
    if(isSource):
        if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
        
        return data_store
    
    # TODO: Check if this is a valid target
    else:
        if(engine == 'aurora-postgresql' or engine == 'aurora-mysql'):
            data_store=create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name)
        return data_store

# TODO: Create functions to create each data store
def create_aurora(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    if(engine == 'aurora-postgresql'):
            set_engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_12_11) # Default Aurora PostgreSQL engine version is 12.11
    if(engine == 'aurora-mysql'):
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
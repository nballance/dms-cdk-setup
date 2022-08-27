from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_dms as dms,

    RemovalPolicy,
)

from dms_cdk_setup.dms_setup import find_host_name_object

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



def create_aurora_endpoint(self, isSource, data_store, set_username):
    if(type(data_store) == rds.DatabaseCluster):
        set_database_name=''
        print('default engine name')
        set_engine_name=''
        if(data_store.engine.engine_type == 'aurora-mysql' or data_store.engine.engine_type=='aurora'):
            print('aurora-mysql/aurora engine name')
            set_database_name=''
            set_engine_name='aurora'
        elif(data_store.engine.engine_type == 'aurora-postgresql'):
            print('aurora-postgresql engine name')
            set_database_name='postgres'
            set_engine_name=data_store.engine.engine_type
        else:
            print(data_store.engine.engine_type)
            print('INVALID ENGINE NAME')

        set_password=data_store.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

        # Returns the writer instance host name for DB cluster (e.g. Aurora PostgreSQL), the writer instance host name for a DB instance (e.g. Oracle RDS)
        set_host_name_object=find_host_name_object(self, data_store)
        set_server_name=data_store.cluster_endpoint.hostname
        set_port=data_store.cluster_endpoint.port
    if(isSource):
        resource_endpoint_name="CDKSourceEndpoint"
        set_endpoint_type="source"
        set_endpoint_identifier="cdk-source-endpoint"
    else:
        resource_endpoint_name="CDKTargetEndpoint"
        set_endpoint_type="target"
        set_endpoint_identifier="cdk-target-endpoint"

    if(data_store.engine == 'aurora-mysql'): # MySQL does not have a database_name
        aurora_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )
    else: #(data_store.engine == 'aurora-postgresql'):
        aurora_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name=set_database_name, 
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )

    aurora_endpoint.add_depends_on(set_host_name_object) # need to wait on host name to resolve
    return aurora_endpoint
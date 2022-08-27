from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_dms as dms,

    RemovalPolicy,
)

from dms_cdk_setup.dms_setup import find_host_name_object

# TODO: Create valid RDS instance types: mariadb mysql oracle-ee oracle-se2 oracle-se1 oracle-se postgres sqlserver-ee sqlserver-se sqlserver-ex sqlserver-web
# TODO: Test Endpoint failed: Application-Status: 1020912, Application-Message: Failed to connect Network error has occurred, Application-Detailed-Message: RetCode: SQL_ERROR SqlState: 08001 NativeError: 101 Message: [unixODBC]timeout expired
# retrying fails...need to check networking
def create_database_instance(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    if(isSource):
        identifier="cdk-source"
    else:
        identifier="cdk-target"

    if(engine == 'mariadb'): 
        print('mariadb')
        set_engine=rds.DatabaseInstanceEngine.MARIADB
    elif(engine == 'mysql'): 
        print('mysql')
        set_engine=rds.DatabaseInstanceEngine.MYSQL

    elif(engine == 'postgres'):
        print('postgres')
        set_engine=rds.DatabaseInstanceEngine.POSTGRES
    elif(engine == 'sqlserver-ee'): 
        print('sqlserver-ee')
        print('    license included')
        set_license_model=rds.LicenseModel.LICENSE_INCLUDED,
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_EE
    elif(engine == 'sqlserver-se'): 
        print('sqlserver-se')
        set_license_model=rds.LicenseModel.LICENSE_INCLUDED,
        print('    license included')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_SE  
    elif(engine == 'sqlserver-ex'): 
        print('sqlserver-ex')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_EX
    elif(engine == 'sqlserver-web'): 
        print('sqlserver-web')
        set_engine=rds.DatabaseInstanceEngine.SQL_SERVER_WEB
    '''
    elif(engine == 'oracle-ee'): # Cannot test/deploy Oracle in personal account
        print('oracle-ee')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1)   
    elif(engine == 'oracle-se2'): # Cannot test/deploy Oracle in personal account
        print('oracle se2')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1) 
    elif(engine == 'oracle-se1'): # Cannot test/deploy Oracle in personal account
        print('oracle-se1')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1)    
    elif(engine == 'oracle-se'): # Cannot test/deploy Oracle in personal account
        print('oracle-se')
        set_engine=rds.DatabaseInstanceEngine.oracle_se2(version=rds.OracleEngineVersion.VER_19_0_0_0_2020_04_R1) 
    '''
    if(engine == 'sqlserver-ee' or engine == 'sqlserver-se'):  # If this is a license-included engine
        instance = rds.DatabaseInstance(self, stack_name,
            engine=set_engine,
            instance_identifier=identifier,
            # license_model=set_license_model,
            license_model=rds.LicenseModel.LICENSE_INCLUDED,
            # optional, defaults to m5.large
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.XLARGE), # SQL Server Instance Class support - https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html#SQLServer.Concepts.General.InstanceClasses
            credentials=rds.Credentials.from_generated_secret(username),  # Optional - will default to 'admin' username and generated password
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection( # Double check same networking subnets, no new subnets created
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            security_groups=[self_referencing_security_group],
        )
    else:
        instance = rds.DatabaseInstance(self, stack_name,
            engine=set_engine,
            instance_identifier=identifier,
            # optional, defaults to m5.large
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            credentials=rds.Credentials.from_generated_secret(username),  # Optional - will default to 'admin' username and generated password
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection( # Double check same networking subnets, no new subnets created
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            security_groups=[self_referencing_security_group],
        )
    instance.apply_removal_policy(RemovalPolicy.DESTROY)

    return instance




# TODO: Pass in the set values. Set the values in the data_store_setup file
def create_database_instance_endpoint(self, isSource, data_store, set_username):
    set_engine_name=data_store.engine.engine_type
    set_port=data_store.instance_endpoint.port
    set_server_name=data_store.instance_endpoint.hostname
    set_password=data_store.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

    set_host_name_object=find_host_name_object(self, data_store) # Pretty sure we don't need this function...


    # TODO: Make a function to get database_name and call it. Determine all database_name attributes, for now mysql and postgres
    set_database_name=''
    if(data_store.engine.engine_type=='postgres'):
        set_database_name=data_store.engine.engine_type
    elif(data_store.engine.engine_type=='mysql'):
        print('database instance endpoint engine is mysql')
    elif(data_store.engine.engine_type=='mariadb'):
        print('database instance endpoint engine is mariadb')
    elif(data_store.engine.engine_type=='sqlserver-web'):
        print('database instance endpoint engine is sqlserver-web')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
        # TODO: Test Endpoint failed: Application-Status: 1020912, Application-Message: Cannot connect to SQL Server Authentication failed, Application-Detailed-Message: RetCode: SQL_ERROR SqlState: 28000 NativeError: 18456 Message: [unixODBC][Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Login failed for user 'syscdk'.
    elif(data_store.engine.engine_type=='sqlserver-ex'):
        print('database instance endpoint engine is sqlserver-ex')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
    elif(data_store.engine.engine_type=='sqlserver-se'):
        print('database instance endpoint engine is sqlserver-se')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
    elif(data_store.engine.engine_type=='sqlserver-ee'):
        print('database instance endpoint engine is sqlserver-ee')
        set_engine_name='sqlserver'
        set_database_name='rdsadmin'
    else:
        print('Current database instance endpoint engine is not supported')

    if(isSource):
        resource_endpoint_name="CDKSourceEndpoint"
        set_endpoint_type="source"
        set_endpoint_identifier="cdk-source-endpoint"
    else:
        resource_endpoint_name="CDKTargetEndpoint"
        set_endpoint_type="target"
        set_endpoint_identifier="cdk-target-endpoint"

    if(data_store.engine == 'mysql' or data_store.engine == 'mariadb'): # MySQL does not have a database_name
        database_instance_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )
    else: #TODO: (data_store.engine == 'postgres'): Need to check for other engines the default 'database_name' e.g. oracle, sql server, mariadb, etc
        database_instance_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
            endpoint_type=set_endpoint_type, #EndpointType
            engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
            database_name=set_database_name, 
            password=set_password, #need to retrieve from secrets manager
            username=set_username, #need to retrieve from secrets manager
            server_name=set_server_name,
            port=set_port,
            endpoint_identifier=set_endpoint_identifier
        )

    # TODO: test if this is needed since this function is only called after the start of the instance
    database_instance_endpoint.add_depends_on(set_host_name_object) # need to wait on host name to resolve
    return database_instance_endpoint

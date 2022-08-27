from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy,
)

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
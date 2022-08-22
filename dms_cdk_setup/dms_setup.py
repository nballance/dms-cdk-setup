from aws_cdk import (
    aws_dms as dms,
    aws_rds as rds,

)
import json




def create_subnet_group(self, vpc):
    tmp = []
    for sub in vpc.private_subnets:
        tmp.append(sub.subnet_id)

    replication_subnet = dms.CfnReplicationSubnetGroup(self, "CDKReplicationSubnetGroup",
        replication_subnet_group_description="CDK replication subnet group",
        replication_subnet_group_identifier="cdk-replication-subnet-group",
        subnet_ids=tmp
    )
    return replication_subnet

def create_DMS_replication_instance(self, replication_subnet, self_referencing_security_group):
        replication_instance = dms.CfnReplicationInstance(self, "CDKReplicationInstance",
            replication_instance_class="dms.t3.small",
            replication_subnet_group_identifier=replication_subnet.ref,
            publicly_accessible=False,
            vpc_security_group_ids=[self_referencing_security_group.security_group_id], # Add rule
            replication_instance_identifier="cdk-replication-instance", 
        )
        return replication_instance

# TODO: Migrate from 'dms_cdk_setup_stack.py'
def create_DMS_replication_task(self, replication_instance, source_endpoint, target_endpoint):
    set_source_endpoint_arn = source_endpoint.ref
    set_target_endpoint_arn = target_endpoint.ref
    set_replication_instance_arn = replication_instance.ref

    replication_task = dms.CfnReplicationTask(self, "CDKReplicationTask",
        migration_type="full-load", # full-load | cdc | full-load-and-cdc
        replication_instance_arn=set_replication_instance_arn, # replication_instance
        source_endpoint_arn=set_source_endpoint_arn, # source endpoint
        target_endpoint_arn=set_target_endpoint_arn, # target endpoint
        table_mappings= json.dumps({"rules":[{"rule-type":"selection","rule-id":"1","rule-name":"1","object-locator":{"schema-name":"%","table-name":"%"},"rule-action":"include"}]}),
        resource_identifier="cdk-replication-task",
        replication_task_identifier="cdk-replication-task",
        # the properties below are optional
        # cdc_start_position="cdcStartPosition",
        # cdc_start_time=123,
        # cdc_stop_position="cdcStopPosition",
        # replication_task_identifier="replicationTaskIdentifier",
        # replication_task_settings="replicationTaskSettings",
        # tags=[CfnTag(
        #     key="key",
        #     value="value"
        # )],
        # task_data="taskData"
    )
    add_DMS_replication_task_dependencies(self, replication_task, replication_instance, source_endpoint, target_endpoint)


def add_DMS_replication_task_dependencies(self, replication_task, replication_instance, source_endpoint, target_endpoint):
    replication_task.add_depends_on(replication_instance)
    replication_task.add_depends_on(source_endpoint)
    replication_task.add_depends_on(target_endpoint)


def create_aurora_endpoint(self, isSource, data_store, set_username):
    if(type(data_store) == rds.DatabaseCluster):
                
        set_password=data_store.secret.secret_value_from_json('password').unsafe_unwrap() # Retrieve source password for Aurora cluster

        # Returns the writer instance host name for DB cluster (e.g. Aurora PostgreSQL), the writer instance host name for a DB instance (e.g. Oracle RDS)
        set_host_name_object=find_host_name_object(self, data_store)
        set_engine_name=data_store.engine.engine_type
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

    # Currently using cluster, will need to use generic object.
    aurora_endpoint = dms.CfnEndpoint(data_store, resource_endpoint_name,
        endpoint_type=set_endpoint_type, #EndpointType
        engine_name=set_engine_name, #engineName; engine_name = source_endpoint # cluster.engine
        database_name="postgres", 
        password=set_password, #need to retrieve from secrets manager
        username=set_username, #need to retrieve from secrets manager
        server_name=set_server_name,
        port=set_port,
        endpoint_identifier=set_endpoint_identifier
    )
    aurora_endpoint.add_depends_on(set_host_name_object) # need to wait on host name to resolve
    return aurora_endpoint



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
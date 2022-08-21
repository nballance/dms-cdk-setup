from aws_cdk import (
    aws_dms as dms,
)
import json


def create_subnet_group(self, vpc):
    tmp = []
    for sub in vpc.private_subnets:
        tmp.append(sub.subnet_id)

    rep_sub = dms.CfnReplicationSubnetGroup(self, "CDKReplicationSubnetGroup",
        replication_subnet_group_description="CDK replication subnet group",
        replication_subnet_group_identifier="cdk-replication-subnet-group",
        subnet_ids=tmp
    )
    return rep_sub

def create_DMS_replication_instance(self, rep_sub, self_referencing_security_group):
        replication_instance = dms.CfnReplicationInstance(self, "CDKReplicationInstance",
            replication_instance_class="dms.t3.small",
            replication_subnet_group_identifier=rep_sub.ref,
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
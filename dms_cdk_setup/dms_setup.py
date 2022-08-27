from aws_cdk import (
    aws_dms as dms,
    aws_rds as rds,
    aws_iam as iam,

)
import json


# Full list of settings for CFN endpoints - https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dms/CfnEndpoint.html#aws_cdk.aws_dms.CfnEndpoint.S3SettingsProperty


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

    custom_replication_task_settings=set_replication_task_settings()


    set_source_endpoint_arn = source_endpoint.ref
    set_target_endpoint_arn = target_endpoint.ref
    set_replication_instance_arn = replication_instance.ref

    replication_task = dms.CfnReplicationTask(self, "CDKReplicationTask",
        migration_type="full-load", # full-load | cdc | full-load-and-cdc
        replication_instance_arn=set_replication_instance_arn, # replication_instance
        source_endpoint_arn=set_source_endpoint_arn, # source endpoint
        target_endpoint_arn=set_target_endpoint_arn, # target endpoint
        table_mappings= json.dumps({"rules":[{"rule-type":"selection","rule-id":"1","rule-name":"1","object-locator":{"schema-name":"%","table-name":"%"},"rule-action":"include"}]}),
        resource_identifier="cdk-replication-task-ri",
        replication_task_identifier="cdk-replication-task-i",
        # the properties below are optional
        # cdc_start_position="cdcStartPosition",
        # cdc_start_time=123,
        # cdc_stop_position="cdcStopPosition",
        # replication_task_identifier="replicationTaskIdentifier",
        replication_task_settings=custom_replication_task_settings,


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


def set_replication_task_settings():
    my_json = {
    "TargetMetadata": {
        "TargetSchema": "",
        "SupportLobs": True,
        "FullLobMode": False,
        "LobChunkSize": 64,
        "LimitedSizeLobMode": True,
        "LobMaxSize": 32,
        "InlineLobMaxSize": 0,
        "LoadMaxFileSize": 0,
        "ParallelLoadThreads": 0,
        "ParallelLoadBufferSize":0,
        "ParallelLoadQueuesPerThread": 1,
        "ParallelApplyThreads": 0,
        "ParallelApplyBufferSize": 100,
        "ParallelApplyQueuesPerThread": 1,    
        "BatchApplyEnabled": False,
        "TaskRecoveryTableEnabled": False
    },
    "FullLoadSettings": {
        "TargetTablePrepMode": "DO_NOTHING",
        "CreatePkAfterFullLoad": False,
        "StopTaskCachedChangesApplied": False,
        "StopTaskCachedChangesNotApplied": False,
        "MaxFullLoadSubTasks": 8,
        "TransactionConsistencyTimeout": 600,
        "CommitRate": 10000
    },
    #     "TTSettings" : {
    #     "EnableTT" : True,
    #     "TTS3Settings": {
    #         "EncryptionMode": "SSE_KMS",
    #         "ServerSideEncryptionKmsKeyId": "arn:aws:kms:us-west-2:112233445566:key/myKMSKey",
    #         "ServiceAccessRoleArn": "arn:aws:iam::112233445566:role/dms-tt-s3-access-role",
    #         "BucketName": "myttbucket",
    #         "BucketFolder": "myttfolder",
    #         "EnableDeletingFromS3OnTaskDelete": False
    #     },
    #     "TTRecordSettings": {
    #         "EnableRawData" : True,
    #         "OperationsToLog": "DELETE,UPDATE",
    #         "MaxRecordSize": 64
    #     }
    # },
    "Logging": {
        "EnableLogging": False
    },
    "ControlTablesSettings": {
        "ControlSchema":"",
        "HistoryTimeslotInMinutes":5,
        "HistoryTableEnabled": False,
        "SuspendedTablesTableEnabled": False,
        "StatusTableEnabled": False
    },
    "StreamBufferSettings": {
        "StreamBufferCount": 3,
        "StreamBufferSizeInMB": 8
    },
    "ChangeProcessingTuning": { 
        "BatchApplyPreserveTransaction": True, 
        "BatchApplyTimeoutMin": 1, 
        "BatchApplyTimeoutMax": 30, 
        "BatchApplyMemoryLimit": 500, 
        "BatchSplitSize": 0, 
        "MinTransactionSize": 1000, 
        "CommitTimeout": 1, 
        "MemoryLimitTotal": 1024, 
        "MemoryKeepTime": 60, 
        "StatementCacheSize": 50 
    },
    # "ChangeProcessingDdlHandlingPolicy": {
    #     "HandleSourceTableDropped": True,
    #     "HandleSourceTableTruncated": True,
    #     "HandleSourceTableAltered": True
    # },
    # "LoopbackPreventionSettings": {
    #     "EnableLoopbackPrevention": True,
    #     "SourceSchema": "LOOP-DATA",
    #     "TargetSchema": "loop-data"
    # },

    # "CharacterSetSettings": {
    #     "CharacterReplacements": [ {
    #         "SourceCharacterCodePoint": 35,
    #         "TargetCharacterCodePoint": 52
    #     }, {
    #         "SourceCharacterCodePoint": 37,
    #         "TargetCharacterCodePoint": 103
    #     }
    #     ],
    #     "CharacterSetSupport": {
    #     "CharacterSet": "UTF16_PlatformEndian",
    #     "ReplaceWithCharacterCodePoint": 0
    #     }
    # },
    # "BeforeImageSettings": {
    #     "EnableBeforeImage": False,
    #     "FieldName": "",  
    #     "ColumnFilter": "pk-only"
    # },
    "ErrorBehavior": {
        "DataErrorPolicy": "LOG_ERROR",
        "DataTruncationErrorPolicy":"LOG_ERROR",
        "DataErrorEscalationPolicy":"SUSPEND_TABLE",
        "DataErrorEscalationCount": 50,
        "TableErrorPolicy":"SUSPEND_TABLE",
        "TableErrorEscalationPolicy":"STOP_TASK",
        "TableErrorEscalationCount": 50,
        "RecoverableErrorCount": 0,
        "RecoverableErrorInterval": 5,
        "RecoverableErrorThrottling": True,
        "RecoverableErrorThrottlingMax": 1800,
        "ApplyErrorDeletePolicy":"IGNORE_RECORD",
        "ApplyErrorInsertPolicy":"LOG_ERROR",
        "ApplyErrorUpdatePolicy":"LOG_ERROR",
        "ApplyErrorEscalationPolicy":"LOG_ERROR",
        "ApplyErrorEscalationCount": 0,
        "FullLoadIgnoreConflicts": True
    },
    "ValidationSettings": {
        "EnableValidation": False,
        "ValidationMode": "ROW_LEVEL",
        "ThreadCount": 5,
        "PartitionSize": 10000,
        "FailureMaxCount": 1000,
        "RecordFailureDelayInMinutes": 5,
        "RecordSuspendDelayInMinutes": 30,
        "MaxKeyColumnSize": 8096,
        "TableFailureMaxCount": 10000,
        "ValidationOnly": False,
        "HandleCollationDiff": False,
        "RecordFailureDelayLimitInMinutes": 1,
        "SkipLobColumns": False,
        "ValidationPartialLobSize": 0,
        "ValidationQueryCdcDelaySeconds": 0
    }
    }
    return (json.dumps(my_json))


# Function to find the main host name. For DB instance this is the DB instance. For Aurora this is the writer. Depends on the type
def find_host_name_object(self, data_store):
    if(type(data_store) == rds.DatabaseCluster):
        for child in data_store.node.children:
            if(type(child) == rds.CfnDBInstance):  # For now we filter by type DB Instance, since we deploy one instance this should be the writer.
                host_name_object=child
                return host_name_object
    elif(type(data_store) == rds.DatabaseInstance):
        for child in data_store.node.children:
            if(type(child) == rds.CfnDBInstance):  # For now we filter by type DB Instance, since we deploy one instance this should be the writer.
                host_name_object=child
                return host_name_object
    else:
        print('find_host_name_object type not defined')
        return ''
from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy,
)
# TODO: Add s3 as source/target, trying 'get_cdk_identifier' instead of IF/ELSE check...
def create_s3_bucket(self, isSource, engine, username, self_referencing_security_group, vpc, stack_name):
    bucket = s3.Bucket(self, "Bucket") # Change bucket to stack_name if successful
    bucket.apply_removal_policy(RemovalPolicy.DESTROY)
    return bucket
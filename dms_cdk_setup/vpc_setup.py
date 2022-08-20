from aws_cdk import (
        Stack,
        aws_ec2 as ec2,
        aws_rds as rds,

)

def createVPC(self):
    vpc=ec2.Vpc(self, 'CDKDMSVPC', 
    cidr="10.0.0.0/16",
    max_azs=3,
    subnet_configuration=[
        ec2.SubnetConfiguration(
            cidr_mask=24,
            name='public1',
            subnet_type=ec2.SubnetType.PUBLIC
        ),
        ec2.SubnetConfiguration(
            cidr_mask=24,
            name='private1',
            subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
        )
    ]  
    )
    return vpc

# def createSelfReferencingSecurityGroup(self, vpc):
#     self_referencing_security_group=ec2.SecurityGroup(self, 'CDKSelfReferencingRule',
#                 vpc=vpc,
#                 description='Self-referencing security group',
#                 allow_all_outbound=True
#             )
    # return se

# class VPCDefault(Construct):
#     def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
#         super().__init__(scope, construct_id, **kwargs)

#         ec2.Vpc(self, 'CDKDMSVPC', 
#             cidr="10.0.0.0/16",
#             max_azs=3,
#             subnet_configuration=[
#                 ec2.SubnetConfiguration(
#                     cidr_mask=24,
#                     name='public1',
#                     subnet_type=ec2.SubnetType.PUBLIC
#                 ),
#                 ec2.SubnetConfiguration(
#                     cidr_mask=24,
#                     name='private1',
#                     subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
#                 )
#             ]  
#         )
#         print(VPCDefault)

        # self_referencing_security_group = ec2.SecurityGroup(self, 'CDKSelfReferencingRule',
        #     vpc=vpc,
        #     description='Self-referencing security group',
        #     allow_all_outbound=True
        # )
        # self_referencing_security_group.add_ingress_rule(self_referencing_security_group, ec2.Port.all_tcp(), "Self-referencing rule")
        # self_referencing_security_group.security_group_id
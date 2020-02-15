#!/usr/bin/env python3
from modules import *

def attach_sg_list(ec2_client, sg_list, instance_id):
    attach_sg_response = ec2_client.modify_instance_attribute(
        InstanceId=instance_id,
        Groups=[
            sg_list,
        ]
    )
    
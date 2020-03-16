#!/usr/bin/env python3
from modules import *

def attach_sg_list(ec2_client, sg_list, instance_id):
    sg_list = [x.strip(' ') for x in sg_list]
    try:
        attach_sg_response = ec2_client.modify_instance_attribute(InstanceId=instance_id,Groups=sg_list)
    except Exception as e:
        print(f"An error has occurred: {e}")
    time.sleep(5)
    
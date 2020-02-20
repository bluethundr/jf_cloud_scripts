#!/usr/bin/env python3
from modules import *

def attach_sg_list(ec2_client, sg_list, instance_id):
    #message = Fore.GREEN + f"Adding the security group list to instance: {instance_id}" + Fore.RESET
    #banner(message)
    sg_list = [x.strip(' ') for x in sg_list]
    #sg_list = str(sg_list).replace(' ', '').replace('[','').replace(']','')
    #sg_list = sg_list.lstrip('\'')
    #sg_list = sg_list.rstrip('\'')
    print(f"SG List: {sg_list}")
    time.sleep(30)
    try:
        attach_sg_response = ec2_client.modify_instance_attribute(InstanceId=instance_id,Groups=sg_list)
        #print(f"Attach SG Response: {attach_sg_response}")
    except Exception as e:
        print(f"An error has occurred: {e}")
    time.sleep(5)
    
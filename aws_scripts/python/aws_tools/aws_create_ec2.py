#!/usr/bin/env python3
from modules import *

def create_instances(image_id, max_count, key_name, instance_type, aws_account, region, ec2_client, ec2_resource, subnet_id, name_tags, sg_id, public_ip, private_ip, private_ip_list, tenancy, monitoring_enabled, user_data):
    print(Fore.CYAN)
    # create a new EC2 instance
    if private_ip_list is not None:
            instances = ec2_resource.create_instances(
                ImageId=image_id,
                InstanceType=instance_type,
                KeyName=key_name,
                MinCount=1,
                MaxCount=1,
                DryRun=False,
                DisableApiTermination=True,
                EbsOptimized=False,
                UserData=user_data,
                Placement={
                    'Tenancy': tenancy,
                },
                Monitoring={
                    'Enabled': monitoring_enabled
                },
                InstanceInitiatedShutdownBehavior='stop',
                NetworkInterfaces=[
                    {
                        'AssociatePublicIpAddress': public_ip,
                        'DeleteOnTermination': True,
                        'DeviceIndex': 0,
                        'PrivateIpAddress': private_ip,
                        'SubnetId': subnet_id,
                        'Groups': [
                            sg_id
                        ]
                    }
                ]
                )
    else:
        private_ip = None
        instances = ec2_resource.create_instances(
        ImageId=image_id,
        InstanceType=instance_type,
        KeyName=key_name,
        MinCount=1,
        MaxCount=max_count,
        DisableApiTermination=True,
        EbsOptimized=False,
        UserData=user_data,
        Placement={
            'Tenancy': tenancy,
        },
        Monitoring={
            'Enabled': monitoring_enabled
        },
        InstanceInitiatedShutdownBehavior='stop',
        NetworkInterfaces=[
            {
                'AssociatePublicIpAddress': public_ip,
                'DeleteOnTermination': True,
                'DeviceIndex': 0,
                'SubnetId': subnet_id,
                'Groups': [
                    sg_id
                ]
            }
        ]
        )
    instance_list, root_volumes_list = list_new_instances(ec2_client, instances)
    return instance_list, root_volumes_list


def main():
    welcomebanner()
    private_ip_list = []
    tag_instances_list = []
    tag_volumes_list = []
    aws_account, region, max_count, image_id, key_name, instance_type, vpc_id, subnet_id, sg_id, sg_list, subnet_ids, public_ip, private_ip_list, tenancy, monitoring_enabled, user_data, name_tags = user_input()
    today, aws_env_list, ec2_client, ec2_resource = initialize(aws_account, region)
    print(Fore.CYAN)
    banner("Creating the instance(s)", "*")
    if private_ip_list is not None:
        for private_ip in private_ip_list:
            instance_list, root_volumes_list = create_instances(image_id, max_count, key_name, instance_type, aws_account, region, ec2_client, ec2_resource, subnet_id, name_tags, sg_id, public_ip, private_ip, private_ip_list, tenancy, monitoring_enabled, user_data)
            tag_instances_list.append(instance_list)
            tag_volumes_list.append(root_volumes_list)
    else:
        private_ip = None
        instance_list, root_volumes_list = create_instances(image_id, max_count, key_name, instance_type, aws_account, region, ec2_client, ec2_resource, subnet_id, name_tags, sg_id, public_ip, private_ip, private_ip_list, tenancy, monitoring_enabled, user_data)
        tag_instances_list.append(instance_list)
        tag_volumes_list.append(root_volumes_list)
    tagged_instance_id_list = tag_instances(tag_instances_list, name_tags, ec2_client)
    tagged_root_volume_list = tag_root_volumes(tag_instances_list, name_tags, ec2_client, tag_volumes_list)
    # Print the instasnce list
    if instance_list and root_volumes_list:
        for instance_id, volume_id in zip(tagged_instance_id_list, tagged_root_volume_list):
            print(f"Instance ID: {instance_id} has been created with volume: {volume_id}")
    else:
        print("Instances have not been created.")
    '''
    print("Adding the security group list")
    if instance_list:
        for instance_id in tagged_instance_list:
            attach_sg_list(ec2_client, sg_list, instance_id)
    else:
        pass
    '''
    endbanner()
    
if __name__ == "__main__":
    main()
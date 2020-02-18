from modules import *

def list_new_instances(ec2_client, instances, private_ip_list):
    instance_list = []
    root_volumes_list = []
    # If assigning private IPs you have to drill down an extra level
    if private_ip_list is not None:
        for instance_info in instances:
            for item in instance_info:
                instance_id = item.instance_id
                instance_list.append(instance_id)
                time.sleep(2)
                root_volume_id = (ec2_client.describe_instance_attribute(InstanceId=instance_id, Attribute='blockDeviceMapping')['BlockDeviceMappings'][0]['Ebs']['VolumeId'])
                root_volumes_list.append(root_volume_id)
    else:
        for instance in instances:
            instance_id = instance.instance_id
            instance_list.append(instance_id)
            time.sleep(2)
            root_volume_id = (ec2_client.describe_instance_attribute(InstanceId=instance_id, Attribute='blockDeviceMapping')['BlockDeviceMappings'][0]['Ebs']['VolumeId'])
            root_volumes_list.append(root_volume_id)
    return instance_list, root_volumes_list
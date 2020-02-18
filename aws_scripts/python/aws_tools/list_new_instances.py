from modules import *

def list_new_instances(ec2_client, instances):
    print(f"Instances from list_new_instances: {instances}")
    instance_list = []
    root_volumes_list = []
    if instances:
        for instance in instances:
            instance_id = instance.instance_id
            instance_list.append(instance_id)
            time.sleep(2)
            root_volume_id = (ec2_client.describe_instance_attribute(InstanceId=instance_id, Attribute='blockDeviceMapping')['BlockDeviceMappings'][0]['Ebs']['VolumeId'])
            root_volumes_list.append(root_volume_id)
    else:
        print("New instance(s) have not been created.")
    return instance_list, root_volumes_list
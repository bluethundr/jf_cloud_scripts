import boto3

tagged_instance_id_list = []
tagged_root_volume_list = []
def tag_instances(tag_instances_list, name_tags, ec2_client, private_ip_list):
    for instance_id, name_tag in zip(tag_instances_list, name_tags): 
        instance_id = str(instance_id).strip('[]').strip('\'')
        tagged_instance_id_list.append(instance_id)
        response = ec2_client.create_tags(
            Resources=[
                instance_id,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name_tag,
                },
                {
                    'Key': 'project',
                    'Value':'JF 2020',
                },
                {
                    'Key': 'Environment',
                    'Value': 'QA',
                },
            ],
        )

def tag_root_volumes(tag_instances_list, name_tags, ec2_client, tag_volumes_list, private_ip_list):
    for instance_id, name_tag, root_volume_id in zip(tag_instances_list, name_tags, tag_volumes_list):
        instance_id = str(instance_id).strip('[]').strip('\'')
        root_volume_id = str(root_volume_id).strip('[]').strip('\'')
        volume_tag = name_tag + ' root volume'
        tagged_root_volume_list.append(root_volume_id)
        response = ec2_client.create_tags(
            Resources=[
                root_volume_id,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': volume_tag,
                },
                {
                    'Key': 'project',
                    'Value':'JF 2020',
                },
                {
                    'Key': 'Environment',
                    'Value': 'QA',
                },
            ],
        )


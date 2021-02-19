#!/usr/bin/env python3
from modules import *

def arguments():
    parser = argparse.ArgumentParser(description='This is a program that creates the servers in EC2')
    parser.add_argument(
    "-a",
    "--ami_id",
    type = str,
    default = None,
    nargs = '?',
    help = "Specify the AMI ID")

    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the AWS account you'll be working in")

    parser.add_argument(
    "-m",
    "--max_count",
    type = str,
    help = "The number of ec2 instances you will create")

    parser.add_argument(
    "-k",
    "--key_name",
    type = str,
    help = "The name of the key you want to use")

    parser.add_argument(
    "-i",
    "--run_again",
    type = str,
    help = "Run again")

    parser.add_argument(
    "-v",
    "--verbose",
    type = str,
    help = "Write the EC2 instances to the screen")  

    options = parser.parse_args()
    return options

def init_create_ec2(aws_account, region):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_confluence_page.csv')
    # Create the session
    if 'gov' in aws_account and not 'admin' in aws_account:
        try:
            session = boto3.Session(profile_name=aws_account, region_name=region)
        except botocore.exceptions.ProfileNotFound as e:
            profile_missing_message = f"An exception has occurred: {e}. Please try again!"
            banner(profile_missing_message)
            ec2_client = None
            ec2_resource = None
            
    else:
        try:
            session = boto3.Session(profile_name=aws_account, region_name=region)
            account_found = 'yes'
        except botocore.exceptions.ProfileNotFound as e:
            profile_missing_message = f"An exception has occurred: {e}. Please try again!"
            banner(profile_missing_message)


    try:
        ec2_client = session.client("ec2")
        ec2_resource = session.resource("ec2")
    except Exception as e:
        print(f"An exception has occurred: {e}")
        ec2_client = None
        ec2_resource = None
    return today, aws_env_list, ec2_client, ec2_resource

def create_instances(aws_account, ec2_client, ec2_resource, region, max_count, image_id, key_name, instance_type, vpc_id, subnet_id, sg_id, sg_list, subnet_ids, public_ip, private_ip_list, tenancy, monitoring_enabled, user_data, name_tags):
    print(Fore.CYAN)
    message = "Creating the instance(s)"
    banner(message, "*")
    instances_list = []
    # create new EC2 instance(s)
    if private_ip_list is not None:
        for private_ip in private_ip_list:
            try:
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
                instances_list.append(instances)
            except Exception as e:
                message = Fore.YELLOW + f"An error has occurred: {e} Instance(s) have not been created." + Fore.RESET
                print(message)
                main()
    else:
        try:
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
        except Exception as e:
            message = Fore.YELLOW + f"An error has occurred: {e} Instance(s) have not been created." + Fore.RESET
            print(message)
            main()

    if private_ip_list is not None:
        instance_list, root_volumes_list = list_new_instances(ec2_client, instances_list, private_ip_list)
    else:
        instance_list, root_volumes_list = list_new_instances(ec2_client, instances, private_ip_list)

    return instance_list, root_volumes_list


def main():
    options = arguments()
    welcomebanner()
    # Return the user input
    aws_account, region, max_count, image_id, key_name, instance_type, vpc_id, subnet_id, sg_id, sg_list, subnet_ids, public_ip, private_ip_list, tenancy, monitoring_enabled, user_data, name_tags = user_input()
    # Get important variables from init
    today, aws_env_list, ec2_client, ec2_resource = init_create_ec2(aws_account, region)
    # Create the instances
    instance_list, root_volumes_list = create_instances(aws_account, ec2_client, ec2_resource, region, max_count, image_id, key_name, instance_type, vpc_id, subnet_id, sg_id, sg_list, subnet_ids, public_ip, private_ip_list, tenancy, monitoring_enabled, user_data, name_tags)
    # Tag the instances
    tag_instances(instance_list, name_tags, ec2_client, private_ip_list)
    # Tag the root volumes
    tag_root_volumes(instance_list, name_tags, ec2_client, root_volumes_list, private_ip_list)
    # Add security groups
    if instance_list:
        for instance_id in instance_list:
            attach_sg_list(ec2_client, sg_list, instance_id)


    # Print the instance list
    print(Fore.CYAN)
    if instance_list and root_volumes_list:
        for instance_id, volume_id in zip(instance_list, root_volumes_list):
            print(f"Instance ID: {instance_id} has been created with volume: {volume_id}")

    endbanner()

if __name__ == "__main__":
    main()
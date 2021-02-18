#!/usr/bin/env python3
import os
import argparse
import boto3
import time
import objectpath
from datetime import datetime
from colorama import init, deinit, Fore
from find_vpcs import *

# Initialize the color ouput with colorama
init()

### Utility Functions
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             Create AWS EC2 Instances                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* Create AWS Instance Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

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
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')
    if 'gov' in aws_account and not 'admin' in aws_account:
        session = boto3.Session(profile_name=aws_account,region_name='us-gov-west-1')
        ec2_client = session.client('ec2')
        ec2_resource = session.resource('ec2')
    else:
        session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
        ec2_client = session.client('ec2')
        ec2_resource = session.resource('ec2')
    return today, aws_env_list, ec2_client, ec2_resource

def user_input():
    name_tags = []
    print(Fore.GREEN)
    banner('AWS Account')
    print(Fore.YELLOW)
    aws_account = input("Enter the account name: ")
    #aws_account = 'jf-master-acct-pd'
    message = f"Ok. Working in AWS account: {aws_account}" + Fore.RESET
    banner(message)
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("AWS Region")
    print(Fore.YELLOW)
    region = input("Enter the region to create EC2 in: ")
    #region = 'us-east-1'
    message = f"Using region: {region}" + Fore.RESET
    banner(message)
    today, aws_env_list, ec2_client, ec2_resource = init_create_ec2(aws_account, region)
    print(Fore.RESET)
    time.sleep(5)
    if ec2_client is None:
        init_create_ec2(aws_account, region)

    print(Fore.GREEN)
    banner("Instance Count")
    print(Fore.YELLOW)
    max_count = None
    while max_count is None:
        try:
            max_count = int(input("Enter how many EC2 Servers: "))
            print(f"Ok. Max count set to: {max_count}")
        except Exception:
            continue
    print(Fore.CYAN)
    for count in range(max_count):
        name_tag = input(f"Please enter the name of server: {count + 1}: ")
        name_tags.append(name_tag)
    name_tag_list = str(list(name_tags)).replace('[','').replace(']','').replace('\'','')
    print(f"The name tags set are: {name_tag_list}")
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("AMI ID")
    print(Fore.YELLOW)
    image_id = input("Enter an AMI ID: ")
    print(f"The AMI ID is set to: {image_id}")
    #image_id = 'ami-00e6eeb9644429ec6'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Key Pair")
    print(Fore.YELLOW)
    key_name = input("Enter the key name to use: ")
    print(f"Using key name: {key_name}")
    print(Fore.RESET)

    print(Fore.GREEN)   
    banner("Instance Type")
    print(Fore.YELLOW)
    instance_type = input("Enter the instance type: ")
    print(f"Using instance type: {instance_type}")
    #instance_type = 't2.small'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("VPC Selection")
    print(Fore.YELLOW)
    vpc_id = find_vpcs(ec2_client)
    #vpc_id = 'vpc-68b1ff12'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Security Groups")
    print(Fore.YELLOW)
    sg_list = ec2_client.describe_security_groups()
    tree = objectpath.Tree(sg_list)
    sg_id_list = set(tree.execute('$..SecurityGroups[\'GroupId\']'))
    sg_id_list = list(sg_id_list)
    sg_id_list = str(list(sg_id_list)).replace('[','').replace(']','').replace('\'','')
    print(Fore.CYAN)
    message = f"Available Security Groups: {sg_id_list}"
    banner(message)
    print(Fore.YELLOW)
    #sg_list = input("Enter a comma separated list of security groups to add: ")
    sg_list_input = str(input("Enter a comma separated list of security groups to add: "))
    sg_list_input = [sg_list_input.strip(' ') for sd in sg_list_input]
    sg_list_input = str.split(",")
    print(f"SG List Input Value: {sg_list_input}\nSG List Input Type: {type(sg_list_input)}\nLength of list: {len(sg_list_input)}")
    sg_list = []
    for sg in sg_list_input:
	    sg_list.append(str(sg))
    print(f"SG List Value: {sg_list}\nSG List Type: {type(sg_list)}\nLength of list: {len(sg_list)}")
    time.sleep(5)
    #sg_list = list(sg_list)
    #sg_list = sg_list.split(',')
    sg_id = sg_list.pop(0)
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("VPC Subnets")
    print(Fore.YELLOW)
    subnet_ids = []
    for vpc in ec2_resource.vpcs.all():
        # here you can choose which subnet based on the id
        if vpc.id == vpc_id:
            for subnet in vpc.subnets.all():
                subnet_ids.append(subnet.id)
    subnet_list = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    tree = objectpath.Tree(subnet_list)
    subnet_list = set(tree.execute('$..Subnets[\'SubnetId\']'))
    subnet_list = list(subnet_list)
    subnet_list = str(subnet_list).replace('[','').replace(']','').replace('\'','')
    print(Fore.CYAN)
    message = f"Available Subnet IDs in {vpc_id}:\n{subnet_list}"
    banner(message)
    print(Fore.YELLOW)
    subnet_id = input("Enter the subnet id: ")
    #subnet_id = 'subnet-63ad5a6d'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Public IP")
    print(Fore.YELLOW)
    public_ip_answer = input("Associate a public IP (y/n): ")
    #public_ip_answer = 'yes'
    if public_ip_answer.lower() == 'yes' or public_ip_answer == 'yes':
        public_ip = True
    else:
        public_ip = False
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Private IP")
    print(Fore.YELLOW)
    private_ip_answer = input("Specify private ip address(es) (y/n): ")
    #private_ip_answer = 'no'
    if private_ip_answer.lower() == 'y' or private_ip_answer.lower() == 'yes':
        private_ip_list = input("Enter private IP addresses separated by commas: ")
        private_ip_list = private_ip_list.split(",")
    else:
        private_ip_list = None

    print(Fore.GREEN)
    banner("Host Tenancy")
    print(Fore.YELLOW)
    print("Tenancy choices are: default|dedicated|host")
    tenancy = input("Enter the type of tenancy you want: ")
    #tenancy = 'default'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Instance Monitoring")
    print(Fore.YELLOW)
    monitoring_enabled = input("Add monitoring (y/n): ")
    #monitoring_enabled = 'no'
    if monitoring_enabled.lower() == 'y' or monitoring_enabled.lower() == 'yes':
        monitoring_enabled = True
    else:
        monitoring_enabled = False

    print(Fore.GREEN)
    banner("User Data")
    print(Fore.YELLOW)
    user_data_question = input("Enter user data (y/n): ")
    #user_data_question = 'no'
    if user_data_question.lower() == 'y' or user_data_question.lower() == 'yes':
        user_data = input("Enter user data: ")
    else:
        user_data = ''
    print(Fore.RESET)
    print("\n")
    return  aws_account, region, max_count, image_id, key_name, instance_type, vpc_id, subnet_id, sg_id, sg_list, subnet_ids, public_ip, private_ip_list, tenancy, monitoring_enabled, user_data, name_tags

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
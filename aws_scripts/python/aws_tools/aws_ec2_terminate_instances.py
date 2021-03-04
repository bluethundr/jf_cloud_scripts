#!/usr/bin/env python
import boto3
import botocore
import objectpath
import time
from collections import defaultdict
from colorama import init, deinit, Fore

init()

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             Terminate AWS EC2 Instances                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* Terminate AWS Instance Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)


def terminate_instances():
    private_ips_list = None
    public_ips_list = None
    # Select the account
    print(Fore.YELLOW)
    aws_account = input("Enter the name of the AWS account you'll be working in: ")
    message = Fore.YELLOW + f"Okay. Working in AWS account: {aws_account}"
    banner(message)
    # Select the region
    aws_region = input("Enter the name of the AWS region you'll be working in: ")
    message = Fore.YELLOW + f"Okay. Working in AWS region: {aws_region}"
    banner(message)
    # Set the account and region
    try:
        session = boto3.Session(profile_name=aws_account,region_name=aws_region)
        ec2_client = session.client("ec2")
    except Exception as e:
        print(f"An exception has occurred: {e}")

    print(Fore.YELLOW)
    instance_id_list = input("Enter instance IDs separated by commas: ")
    instance_ids = instance_id_list.split(",")
    instance_ids = [instance_id.strip(' ') for instance_id in instance_ids]
    check_state = input("Check the server state (y/n): ")
    print("\n")
    print(Fore.RESET + "-------------------------------------")
    print(Fore.GREEN + "Deleting the following instances: \n")
    for instance_id in instance_ids:
        print(Fore.CYAN + instance_id)
    print(Fore.RESET + "-------------------------------------\n")
    for instance_id in instance_ids:
        message = Fore.CYAN + f"Terminating Instance ID: {instance_id}" + Fore.RESET
        banner(message)
        instance = ec2_client.describe_instances(
            InstanceIds=[instance_id]
            )['Reservations'][0]['Instances'][0]
        ec2info = defaultdict()
        launch_time = instance['LaunchTime']
        launch_time_friendly = launch_time.strftime("%B %d %Y")
        tree = objectpath.Tree(instance)
        volume_ids = set(tree.execute('$..BlockDeviceMappings[\'Ebs\'][\'VolumeId\']'))
        volume_ids = list(volume_ids)
        private_ips =  set(tree.execute('$..PrivateIpAddress'))
        if len(private_ips) == 0:
            private_ips = None
            if private_ips:
                private_ips_list = list(private_ips)
                private_ips_list = str(private_ips_list).replace('[','').replace(']','').replace('\'','')
            else:
                private_ips_list = None
        public_ips =  set(tree.execute('$..PublicIp'))
        if len(public_ips) == 0:
            public_ips = None
        if public_ips:
            public_ips_list = list(public_ips)
            public_ips_list = str(public_ips_list).replace('[','').replace(']','').replace('\'','')
        else:
            public_ips_list = None
        ec2info[instance['InstanceId']] = {
            'Instance ID': instance['InstanceId'],
            'Type': instance['InstanceType'],
            'State': instance['State']['Name'],
            'Private IP':private_ips_list,
            'Public IP': public_ips_list,
            'Launch Time' : launch_time_friendly
         }
        attributes = ['Instance ID', 'Type',
                'State', 'Private IP', 'Public IP', 'Launch Time' ]
        for instance_id, instance in ec2info.items():
            for key in attributes:
                print(Fore.GREEN + "{0}: {1}".format(key, instance[key]))
        message = Fore.YELLOW + "Modifying and deleting the instance." + Fore.RESET
        banner(message)
        try:
            ec2_client.modify_instance_attribute(InstanceId=instance_id, DisableApiTermination={'Value':False})
            ec2_client.terminate_instances(InstanceIds=[instance_id], DryRun=False)
            pause = 1
        except Exception as e:
            print(Fore.GREEN + f"The instance id: {instance_id} has already been terminated.")
            pause = 0
        ## Check the current state
        if pause == 1 or ('y' or 'yes') in check_state.lower():
            message = Fore.GREEN + "Pausing 60 seconds for termination." + Fore.RESET
            banner(message)
            time.sleep(60)
        else:
            print(Fore.GREEN)
            message = "NOT Pausing 60 seconds for termination."
            banner(message)
        message = Fore.YELLOW + "Deleting Volumes" + Fore.RESET
        banner(message)
        for volume_id in volume_ids:
                print(Fore.GREEN + f"Deleting volume: {volume_id}")
                try:
                    delete_response = (ec2_client.delete_volume(VolumeId=volume_id)['ResponseMetadata']['HTTPStatusCode'])
                    if delete_response == 200:
                        print(Fore.GREEN + "Volume ID: %s has been deleted." % volume_id)
                except Exception as error:
                    print(f"Volume ID: {volume_id} has been deleted.")

        try:
            instance = ec2_client.describe_instances(
            InstanceIds=[instance_id]
            )['Reservations'][0]['Instances'][0]
        except Exception as e:
            print("An exception has occurred: {e}")
        instance_state = instance['State']['Name']
        message = Fore.YELLOW + f"Current Instance State: {instance_state}" + Fore.RESET
        banner(message)
        print("\n")
                        
def main():
    welcomebanner()
    terminate_instances()
    endbanner()
    deinit()
    
if __name__ == "__main__":
    main()

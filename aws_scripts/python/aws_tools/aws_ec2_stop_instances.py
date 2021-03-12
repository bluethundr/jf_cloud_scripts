#!/usr/bin/env python
from modules import *

init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = f"*             Stop EC2 Instances                      *"
    banner(message,"*")

def endbanner():
    print(Fore.CYAN)
    message = f"* Stop EC2 Instances Operations Are Complete   *"
    banner(message,"*")


def stop_instances():
    # Select the account
    print(Fore.YELLOW)
    aws_account = input("Enter the name of the AWS account you'll be working in: ")
    message = Fore.YELLOW + "Okay. Working in AWS account: " + aws_account
    banner(message)
    # Select the region
    aws_region = input("Enter the name of the AWS region you'll be working in: ")
    message = Fore.YELLOW + "Okay. Working in AWS region: " + aws_region
    banner(message)
    # Set the account and region
    try:
        session = boto3.Session(profile_name=aws_account,region_name=aws_region)
    except Exception as e:
        print(f"An error has occurred: {e}")

    try:
        ec2_client = session.client("ec2")
    except Exception as e:
        print(f"An error has occurred: {e}")

    print(Fore.YELLOW)
    instance_id_list = input("Enter instance IDs separated by commas: ")
    instance_ids = instance_id_list.split(",")
    instance_ids = [instance_id.strip(' ') for instance_id in instance_ids]
    check_state = input("Check the server state (y/n): ")
    print("\n")
    print(Fore.RESET + "-------------------------------------")
    print(Fore.GREEN + "Stopping the following instances: \n")
    for instance_id in instance_ids:
        print(Fore.CYAN + instance_id)
    print(Fore.RESET + "-------------------------------------\n")
    
    for instance_id in instance_ids:
        print(Fore.GREEN)
        message = f"Stopping Instance ID: {instance_id}"
        banner(message)
        instance = ec2_client.describe_instances(
            InstanceIds=[instance_id]
            )['Reservations'][0]['Instances'][0]
        instance_state = instance['State']['Name']
        ec2info = defaultdict()
        launch_time = instance['LaunchTime']
        launch_time_friendly = launch_time.strftime("%B %d %Y")
        try:
            public_ip = instance['PublicIpAddress']
        except:
            ec2info[instance['InstanceId']] = {
                'Instance ID': instance['InstanceId'],
                'Type': instance['InstanceType'],
                'State': instance['State']['Name'],
                'Private IP': instance['PrivateIpAddress'],
                'Launch Time' : launch_time_friendly
            }
            attributes = ['Instance ID', 'Type',
                    'State', 'Private IP', 'Launch Time' ]
            for instance_id, instance in ec2info.items():
                for key in attributes:
                    print(Fore.CYAN + "{0}: {1}".format(key, instance[key]))
        else:
            ec2info[instance['InstanceId']] = {
                'Instance ID': instance['InstanceId'],
                'Type': instance['InstanceType'],
                'State': instance['State']['Name'],
                'Private IP': instance['PrivateIpAddress'],
                'Public IP': public_ip,
                'Launch Time' : launch_time_friendly
        }
            attributes = ['Instance ID', 'Type',
                    'State', 'Private IP', 'Public IP', 'Launch Time' ]
            for instance_id, instance in ec2info.items():
                for key in attributes:
                    print(Fore.GREEN + "{0}: {1}".format(key, instance[key]))
        if instance_state == 'running':
            message = Fore.YELLOW + "Stopping the instance."
            banner(message)
            try:
                ec2_client.stop_instances(InstanceIds=[instance_id], DryRun=False)
            except Exception as e:
                print(f"An error has occurred: {e}.")
            if ('y' or 'yes') in check_state.lower():
                ## Check the current state
                message = Fore.GREEN + "Pausing for 60 seconds for the instance to stop." + Fore.RESET
                banner(message)
                time.sleep(60) 
                instance = ec2_client.describe_instances(
                    InstanceIds=[instance_id]
                    )['Reservations'][0]['Instances'][0]
                instance_state = instance['State']['Name']
                message = Fore.YELLOW + f"Current Instance State: {instance_state}"
                banner(message)
        else:
            message = Fore.YELLOW + f"Instance: {instance_id} has already been stopped."
            print(message)
                

def main():
    welcomebanner()
    stop_instances()
    endbanner()

if __name__ == "__main__":
    main()
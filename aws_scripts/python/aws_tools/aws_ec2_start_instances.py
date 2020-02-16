#!/usr/bin/env python

import boto3

from modules import *

init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = f"*             Start AWS Instances                       *"
    banner(message,"*")

def endbanner():
    print(Fore.CYAN)
    message = f"* Start AWS Instances Operations Are Complete   *"
    banner(message,"*")


def arguments():
    parser = argparse.ArgumentParser(description='This is a program that starts servers in EC2')


    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the AWS account you'll be working in")

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

def start_instances():
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
        print(f"An error has occurred: {e}.")
    try:
        ec2_client = session.client("ec2")
    except Exception as e:
        print(f"An error has occurred: {e}.")

    print(Fore.YELLOW)
    instance_id_list = input("Enter instance IDs separated by commas: ")
    instance_ids = instance_id_list.split(",")
    check_state = input("Check the server state (y/n): ")
    print("\n")
    print(Fore.RESET + "-------------------------------------")
    print(Fore.GREEN + "Starting the following instances: \n")
    for instance_id in instance_ids:
        print(Fore.CYAN + instance_id)
    print(Fore.RESET + "-------------------------------------\n")
    for instance_id in instance_ids:
        print(Fore.GREEN)
        message = f"Starting Instance ID: {instance_id}"
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
        if instance_state == 'stopped':
            message = Fore.YELLOW + "Starting the instance."
            banner(message)
            try:
                ec2_client.start_instances(InstanceIds=[instance_id], DryRun=False)
            except Exception as e:
                print(f"An error has occurred: {e}.")
            if check_state.lower() == 'Y' or check_state.lower() == 'Yes':
                ## Check the current state
                message = Fore.GREEN + "Pausing for 60 seconds for the instance to start."
                banner(message)
                time.sleep(60) 
                instance = ec2_client.describe_instances(
                    InstanceIds=[instance_id]
                    )['Reservations'][0]['Instances'][0]
                instance_state = instance['State']['Name']
                message = Fore.YELLOW + f"Current Instance State: {instance_state}"
                banner(message)
        else:
            message = Fore.YELLOW + f"The instance: {instance_id} has already been started."
            banner(message)

                     
def main():
    options = arguments()
    welcomebanner()
    start_instances()
    endbanner()

    if options.run_again:
        list_again = options.run_again
    else:
        list_again = input("List EC2 instances again (y/n): ")
    if list_again.lower() == 'y' or list_again.lower() == 'yes':
        main()
    else:
        exit_program()

if __name__ == "__main__":
    main()
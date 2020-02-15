#!/usr/bin/env python

import boto3
import collections
from collections import defaultdict
import time
from datetime import datetime
from colorama import init, deinit, Fore, Back, Style
from termcolor import colored
init()

print(Fore.CYAN)
print('******************************************************')
print('             Stop AWS Instances                  ')
print('******************************************************\n')

# Select the account
print(Fore.YELLOW)
aws_account = input("Enter the name of the AWS account you'll be working in: ")
print(Fore.YELLOW + "Okay. Working in AWS account: ", aws_account, "\n")
# Select the region
aws_region = input("Enter the name of the AWS region you'll be working in: ")
print(Fore.YELLOW + "Okay. Working in AWS region: ", aws_region, "\n")
# Set the account and region
session = boto3.Session(profile_name=aws_account,region_name=aws_region)
ec2 = session.client("ec2")

print(Fore.YELLOW)
instance_id_list = input("Enter instance IDs separated by commas: ")
instance_ids = instance_id_list.split(",")
print("\n")
print(Fore.RESET + "-------------------------------------")
print(Fore.GREEN + "Stopping the following instances: \n")
for instance_id in instance_ids:
    print(Fore.CYAN + instance_id)
print(Fore.RESET + "-------------------------------------\n")
time.sleep(5)
for instance_id in instance_ids:
    print(Fore.RESET + "----------------------------------------------")
    print(Fore.CYAN + "Stopping Instance ID: ", instance_id)
    print(Fore.RESET + "----------------------------------------------")
    instance = ec2.describe_instances(
        InstanceIds=[instance_id]
        )['Reservations'][0]['Instances'][0]
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
    time.sleep(5)
    print(Fore.RESET + "-------------------------------------")
    print(Fore.YELLOW + "Stopping the instance.")
    print(Fore.RESET + "-------------------------------------")
    ec2_connection.stop_instances(InstanceIds=[instance_id], DryRun=False)
    ## Check the current state
    print(Fore.RESET + "---------------------------------------")
    print(Fore.GREEN + "Pausing for 60 seconds for termination.")
    print(Fore.RESET + "---------------------------------------")
    time.sleep(60) 
    instance = ec2.describe_instances(
        InstanceIds=[instance_id]
        )['Reservations'][0]['Instances'][0]
    instance_state = instance['State']['Name']
    print(Fore.RESET + "----------------------------------------")
    print(Fore.YELLOW + "Current Instance State: ", instance_state)
    print(Fore.RESET + "----------------------------------------\n")
                       
time.sleep(5)
print(Fore.CYAN + "******************************************************")
print("* Terminate Instance Operations in AWS Are Complete  *")
print("******************************************************")
deinit()

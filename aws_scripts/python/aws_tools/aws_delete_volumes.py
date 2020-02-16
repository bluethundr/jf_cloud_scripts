#!/usr/bin/env python3

import os
import boto3
import botocore
import time
import datetime
import dateutil
import json
import csv
import objectpath
from colorama import init, Fore
from datetime import date, datetime, timedelta
from botocore.exceptions import ClientError, ProfileNotFound
from choose_accounts import choose_accounts

init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = f"*             Delete EBS Volumes                       *"
    banner(message,"*")

def endbanner():
    print(Fore.CYAN)
    message = f"* Delete EBS Volumes Operations Are Complete   *"
    banner(message,"*")


def write_header():
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize()
    try:
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()
    except Exception as e:
        print(Fore.GREEN, f"The file could not be opened: {output_file_name}.")

def initialize():
    print(Fore.RESET)
    # Set the date
    today = datetime.now()
    today = today.strftime("%Y-%m-%d")
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')
        
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_delete_volumes', 'csv')
    output_file = output_dir + "\\" + 'aws-delete-volumes-' + today + '.csv'
    output_file_name = 'aws-delete-volumes-' + today + '.csv'

    fieldnames = [ 'AWS Account', 'Account Number', 'Volume ID', 'Deleted At']

    return today, aws_env_list, output_file, output_file_name, fieldnames


def delete_volumes(aws_account,aws_account_number, output_file, ec2_client):
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize()
    volumes = ec2_client.describe_volumes()
    tree = objectpath.Tree(volumes)
    volumes = set(tree.execute('$..Volumes[\'VolumeId\']'))
    volumes = list(volumes)
    print(Fore.GREEN)
    if volumes:
        for volume in volumes:
            try:
                delete_volume_response = (ec2_client.delete_volume(VolumeId=volume)['ResponseMetadata']['HTTPStatusCode'])
            except Exception as e:
                print(f"An exception has occurred: {e}.")
            if delete_volume_response == 200:
                deleted_at = datetime.now()
                deleted_at = deleted_at.strftime("%Y%m%d-%H:%M:%S")
                print(f"Volume ID: {volume} has been deleted at {deleted_at}.")
                try:
                    with open(output_file,'a') as csv_file:
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                        writer.writerow({'AWS Account': aws_account, 'Account Number': aws_account_number, 'Volume ID': volume, 'Deleted At': deleted_at})
                except Exception as e:
                            print(Fore.GREEN, f"The file could not be opened: {output_file_name}.")
    else:
        print(f"No volumes to delete in AWS Account: {aws_account} ({aws_account_number}).")

    try:
        with open(output_file,'a') as csv_file:
            csv_file.close()
    except Exception as e:
        print(Fore.GREEN, f"The file could not be opened: {output_file_name}.")
    return output_file

def loop_accounts():
    print(Fore.CYAN)
    message = f"*             Loop Accounts                          *"
    banner(message, "*")
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize()
    print(Fore.RESET)
    account_names, account_numbers = choose_accounts(aws_env_list)
    for (aws_account, aws_account_number) in zip(account_names, account_numbers):
        try:
            aws_account = aws_account.split()[0]
        except Exception as e:
            message = f"An exception has occurred: {e}"
            banner(message)
        else:
            print("\n")
            message = Fore.GREEN + f"Working in AWS Account: {aws_account} ({aws_account_number})"
            banner(message)
        if 'gov' in aws_account and not 'admin' in aws_account:
            try:
                session = boto3.Session(profile_name=aws_account,region_name='us-gov-west-1')
                account_found = 'yes'
            except botocore.exceptions.ProfileNotFound as e:
                message = f"An exception has occurred: {e}"
                account_found = 'no'
                banner(message)
                
                pass
            try:
                ec2_client = session.client('ec2')
            except Exception as e:
                pass
            if account_found == 'yes':
                message = "This is a gov account."
                banner(message)
                delete_volumes(aws_account,aws_account_number, output_file, ec2_client)
        else:
            try:
                session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
                account_found = 'yes'
            except botocore.exceptions.ProfileNotFound as e:
                message = f"An exception has occurred: {e}"
                banner(message)
                account_found = 'no'
                
                pass
            try:
                ec2_client = session.client('ec2')
            except Exception as e:
                pass
            message = "This is a commercial account."
            banner(message)
            delete_volumes(aws_account,aws_account_number, output_file, ec2_client)

def main():
    welcomebanner()
    print(Fore.RESET)
    write_header()
    loop_accounts()
    endbanner()

if __name__ == "__main__":
    main()

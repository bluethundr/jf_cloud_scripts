#!/usr/bin/env python3

import os
import boto3
import botocore
import time
import datetime
import dateutil
import itertools
import json
import csv
import objectpath
from colorama import init, Fore
from datetime import date, datetime, timedelta
from botocore.exceptions import ClientError, ProfileNotFound

init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = f"*             Delete AWS MFA                       *"
    banner(message,"*")

def endbanner():
    print(Fore.CYAN)
    message = f"* Delete AWS MFA Operations Are Complete   *"
    banner(message,"*")


def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def initialize():
    print(Fore.RESET)
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%m-%d-%Y')
    test_account_answer = input("Use test account (y/n): ")
    if test_account_answer.lower() == 'y' or test_account_answer.lower() == 'yes':
        src = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_jokefire_page-' + yesterday + '.csv')
        dst = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_jokefire_page-' + today + '.csv')
        time.sleep(5)
        if not os.path.exists(dst):
            try:
                os.rename(src, dst)
            except Exception as e:
                print("An exception has occurred: {e}")
        aws_env_list = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_jokefire_page-' + today + '.csv')
    else:
        aws_env_list = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_confluence_page-' + today + '.csv')
        
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_delete_role', 'csv')
    output_file = output_dir + 'aws-delete-role-' + today +'.csv'
    output_file_name = 'aws-delete-role-' + today +'.csv'    
    return today, aws_env_list, output_file, output_file_name

def read_account_info(aws_env_list):
    account_names = []
    account_numbers = []
    with open(aws_env_list) as csv_file:
    	csv_reader = csv.reader(csv_file, delimiter=',')
    	next(csv_reader)
    	for row in csv_reader:
            account_name = str(row[0])
            account_number = str(row[5])
            account_names.append(account_name)
            account_numbers.append(account_number)
    return account_names, account_numbers


def choose_accounts(aws_env_list):
    account_names = []
    account_numbers = []
    my_account_name = ''
    my_account_number = ''
    all_accounts_question = input("Loop through all accounts (one/some/all): ")
    if all_accounts_question.lower() == 'one':
        my_account_name = input("Enter the name of the AWS account you'll be working in: ")
        account_names, account_numbers = read_account_info(aws_env_list)
        for (aws_account, aws_account_number) in zip(account_names, account_numbers):
            if my_account_name == aws_account:
                my_account_number = aws_account_number
                time.sleep(5)
        account_names = []
        account_numbers = []
        account_names.append(my_account_name)
        account_numbers.append(my_account_number)
        time.sleep(15)
    elif all_accounts_question == 'some':
        my_account_names = input("Enter AWS account names separated by commas: ")
        my_account_names = my_account_names.split(",")
        my_account_numbers = []
        account_names, account_numbers = read_account_info(aws_env_list)
        for (aws_account, aws_account_number, my_account_name) in zip(account_names, account_numbers, my_account_names):
            if my_account_name == aws_account:
                my_account_number = aws_account_number
                my_account_numbers.append(my_account_number)
        account_names = my_account_names
        aws_account_numbers = my_account_numbers
    elif all_accounts_question == 'all':   
        account_names, account_numbers = read_account_info(aws_env_list)
    else:
        print("That is not a valid choice.")
    time.sleep(5)
    return account_names, account_numbers


def delete_mfa(aws_account,aws_account_number, user_name, output_file, iam_client):
    fieldnames = [ 'AWS Account', 'Account Number', 'User Name', 'MFA Exists', 'MFA Deleted']
    count_bucket_entries = 0
    mfa_info = ''
    # Determine if the user exists in this account
    user_list = iam_client.list_users()['Users']
    if user_list:
        tree = objectpath.Tree(user_list)
        user_names = set(tree.execute('$..UserName]'))
        user_names = list(user_names)
        user_names = str(user_names).replace('[','').replace(']','').replace('\'','').replace(',', '')
        time.sleep(5)
        for name in user_names.split():
            if name == user_name:
                user_exists = 'yes'
                print(f"Name: {user_name} is a match for {name}.")
                break
            else:
                user_exists = 'no'
    else:
        message = f"No IAM users exist in AWS Account: {aws_account}."
        banner(message)
    if user_list:
        if user_exists == 'yes':
            # Delete the MFA
            message = f"Removing MFA from user: {user_name}."
            banner(message)
            try:
                mfa_info = (iam_client.list_mfa_devices(UserName=user_name)['MFADevices'])
            except Exception as e:
                print(f"An exception has occurred: {e}")
            if mfa_info:
                list_mfa_devices = (iam_client.list_mfa_devices(UserName=user_name))
                mfa_serial = list_mfa_devices['MFADevices'][0]['SerialNumber']
                message = f"User: {user_name} has the following MFA attached: "
                banner(message)
                print(mfa_serial)
                mfa_exists = True
                try:
                    deactivate_mfa_device_status = iam_client.deactivate_mfa_device(UserName=user_name,SerialNumber=mfa_serial)
                    message = "MFA deactivated."
                    banner(message)
                except Exception as e:
                    message = f"Exception: {e}"
                    banner(message)
                try:
                    delete_mfa_device_status = iam_client.delete_virtual_mfa_device(SerialNumber=mfa_serial)
                    message = "MFA deleted."
                    banner(message)
                    mfa_deleted = 'yes'
                    time.sleep(5)
                except Exception as e:
                    message = f"Exception: {e}"
                    banner(message)
                    mfa_deleted = 'no'
            else:
                message = f"User: {user_name} has no MFA devices."
                banner(message)
                mfa_exists = False
                mfa_deleted = 'no'
            time.sleep(5)
            with open(output_file,'a') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                writer.writerow({'AWS Account': aws_account, 'Account Number': aws_account_number, 'User Name': user_name, 'MFA Exists': mfa_exists, 'MFA Deleted': mfa_deleted})
        elif user_exists == 'no':
            message = f"User name: {user_name} does not exist in account: {aws_account}."
            banner(message)

    with open(output_file,'a') as csv_file:
        csv_file.close()
    return output_file

def loop_accounts(user_name):
    print(Fore.CYAN)
    message = f"*             Loop Accounts                          *"
    banner(message, "*")
    today, aws_env_list, output_file, output_file_name = initialize()
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
            message = f"Working in AWS Account: {aws_account} ({aws_account_number})"
            banner(message)
        if 'gov' in aws_account and not 'admin' in aws_account:
            try:
                session = boto3.Session(profile_name=aws_account,region_name='us-gov-west-1')
                account_found = 'yes'
            except botocore.exceptions.ProfileNotFound as e:
                message = f"An exception has occurred: {e}"
                account_found = 'no'
                banner(message)
                time.sleep(5)
                pass
            try:
                iam_client = session.client('iam')
            except Exception as e:
                pass
            if account_found == 'yes':
                message = "This is a gov account."
                banner(message)
                delete_mfa(aws_account,aws_account_number, user_name, output_file, iam_client)
        else:
            try:
                session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
                account_found = 'yes'
            except botocore.exceptions.ProfileNotFound as e:
                message = f"An exception has occurred: {e}"
                banner(message)
                account_found = 'no'
                time.sleep(5)
                pass
            try:
                iam_client = session.client('iam')
            except Exception as e:
                pass
            if account_found == 'yes' and aws_account != 'company-lighthouse':
                if aws_account == 'company-lighthouse':
                    print("Skipping Lighthouse account.")
                message = "This is a commercial account."
                banner(message)
                delete_mfa(aws_account,aws_account_number, user_name, output_file, iam_client)

def main():
    welcomebanner()
    print(Fore.RESET)
    user_name = input("Enter the user name: ")
    loop_accounts(user_name)
    endbanner()


if __name__ == "__main__":
    main()

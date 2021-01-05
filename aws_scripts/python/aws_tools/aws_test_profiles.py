#!/usr/bin/env python3

import os
import boto3
import botocore
import datetime
import csv
from colorama import init, Fore
from datetime import datetime

init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = f"*   Test AWS Access   *"
    banner(message,"*")

def endbanner():
    print(Fore.CYAN)
    message = "*   Test AWS Access Operations Are Complete   *"
    banner(message, "*")

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
    test_account_answer = input("Use test account (y/n): ")
    if test_account_answer.lower() == 'y' or test_account_answer.lower() == 'yes':
        aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_jokefire_page.csv')
    else:
        aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')

    return today, aws_env_list

def read_account_info(aws_env_list):
    account_names = []
    account_numbers = []
    with open(aws_env_list) as csv_file:
    	csv_reader = csv.reader(csv_file, delimiter=',')
    	next(csv_reader)
    	for row in csv_reader:
            account_name = str(row[0])
            account_number = str(row[1])
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
                print(f"My Account Name: {my_account_name}\nMy Account Number: {my_account_number}")
        account_names = []
        account_numbers = []
        account_names.append(my_account_name)
        account_numbers.append(my_account_number)
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

    return account_names, account_numbers

def loop_accounts():
    print(Fore.CYAN)
    message = '*   Loop Accounts   *'
    banner(message,"*")
    _, aws_env_list = initialize()
    account_names, account_numbers = choose_accounts(aws_env_list)
    print(Fore.RESET)
    for (aws_account, aws_account_number) in zip(account_names, account_numbers):
        try:
            aws_account = aws_account.split()[0]
        except Exception as e:
            message = f"An exception has occurred: {e}"
            banner(message)
        else:
            print("\n")
            message = f"Working in AWS Account: {aws_account} - ({aws_account_number})"
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
                test_profiles(ec2_client, aws_account, aws_account_number)
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
            if account_found == 'yes':
                message = "This is a commercial account."
                banner(message)
                test_profiles(ec2_client, aws_account, aws_account_number)

def test_profiles(ec2_client, aws_account, aws_account_number):
    print(Fore.RESET)
    policy_doc = ''
    policy_arn = ''
    try:
        desc_network_interfaces_response = (ec2_client.describe_network_interfaces()['ResponseMetadata']['HTTPStatusCode'])
        # Verify that console login was created
        if desc_network_interfaces_response == 200:
            print(Fore.GREEN + f"Access is working.")
        else:
            print(Fore.YELLOW + f"Access is not working.")
    except Exception as e:
        print(f"An exception has occurred: {e}")
    print(Fore.RESET)

def main():
    welcomebanner()
    print(Fore.RESET)
    loop_accounts()
    endbanner()

if __name__ == "__main__":
    main()
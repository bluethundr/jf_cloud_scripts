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
        aws_env_list = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_jokefire_page-' + today + '.csv')
    else:
        aws_env_list = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_confluence_page-' + today + '.csv')
        
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_create_role', 'csv')
    output_file = output_dir + 'aws-create-role-' + today +'.csv'
    output_file_name = 'aws-create-role-' + today +'.csv'    
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
    today, aws_env_list, output_file, output_file_name = initialize()
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

def send_email(aws_accounts_question,aws_account,aws_account_number): 
    # Get the variables from intitialize
    today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
    ## Get the address to send to
    print(Fore.YELLOW)
    first_name = str(input("Enter the recipient's first name: "))
    to_addr = input("Enter the recipient's email address: ")
    from_addr = 'cloudops@noreply.company.com'
    subject = "AWS Profile Test Results " + today
    if aws_accounts_question == 'one':
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of instances in all AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>Cloud Ops</font>"
    else:
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of instances in all company AWS accounts.<br><br>Regards,<br>Cloud Ops</font>"    
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = MIMEText(content, 'html')
    msg.attach(body)

    filename = output_file
    with open(filename, 'r') as f:
        part = MIMEApplication(f.read(), Name=basename(filename))
        part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(filename))
        msg.attach(part)
    server = smtplib.SMTP('smtpout.us.cworld.company.com', 25)
    try:
        server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
        print("Email was sent to: %s" % to_addr)
    except Exception as error:
        print("Exception:", error)
        print("Email was not sent.")

def main():
    welcomebanner()
    print(Fore.RESET)
    loop_accounts()
    endbanner()

if __name__ == "__main__":
    main()
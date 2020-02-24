#!/usr/bin/env python3

import os
import io
import boto3
import time
import json
import datetime
import dateutil
import smtplib
import contextlib
import objectpath
import subprocess
import sys
import random
import string
import csv
import urllib3
import certifi
import requests
from pysecret import AWSSecret
from os.path import basename
from time import gmtime
from datetime import date, datetime, timedelta
from dateutil import parser
from colorama import init, Fore
from botocore.exceptions import ClientError, ProfileNotFound
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

## Standard utility functions
# Initialize the color ouput with colorama
init()
BASE_URL = "https://confluence.synchronoss.net:8443/rest/api/content"
VIEW_URL = "https://confluence.synchronoss.net:8443/pages/viewpage.action?pageId="

## Provide session info to the functions based on AWS account
def initialize():
    ## One or many accounts
    print(Fore.YELLOW)
    aws_accounts_question = input("Work in one or all accounts: ")
    if aws_accounts_question != 'all':
        while True:
            try:
                print(Fore.YELLOW)
                aws_account = input("Enter the name of the AWS account you'll be working in: ")
                if 'gov' in aws_account and 'admin' not in aws_account:
                    print("This is an AWS gov account.")
                    gov_account = True
                else:
                    print("This is an AWS commercial account.")
                    gov_account = False
                if aws_account.lower() == 'all' or aws_account.lower() == 'many':
                    aws_account = 'all-accounts'
                session = boto3.Session(profile_name=aws_account)
                iam_resource = session.resource('iam')
                iam_client = session.client('iam', use_ssl=True, verify=None)
                kms_client = session.client('kms')
                secrets_client = session.client('secretsmanager')
                org_client = session.client('organizations')
                ce_client = session.client('ce')
                break
            except ProfileNotFound:
                print('AWS account does not exist. Try again!')
    else:
        aws_account = 'all'
        gov_account = ''
        session = '' 
        iam_resource =  ''
        iam_client =  ''
        kms_client = ''  
        secrets_client = ''
        org_client = ''

    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    aws_account_number = aws_accounts_to_account_numbers(aws_account)
    print(Fore.GREEN, "\n")
    message = f"*          Okay. Working in AWS account: {aws_account}         *"
    banner(message,"*")
    return aws_accounts_question, aws_account, aws_account_number, gov_account, iam_client, kms_client, secrets_client, org_client, iam_resource, today

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = '*             AWS IAM Operations                     *'
    banner(message,"*")

def endbanner():
    print(Fore.CYAN)
    message = "*          AWS IAM Operations Are Complete               *"
    banner(message,"*")

def aws_account_iterator(aws_accounts_question, aws_account, aws_account_number, gov_account, iam_client, kms_client, secrets_client, org_client, iam_resource, today, choice):
    aws_env_list="../../source_files/aws_environments/aws_environments_all.txt"
    print
    password = set_password()
    print(f"Password: {password}")
    #aws_env_list="source_files/aws_environments/aws_environments_jf.txt"
    interactive = 0
    ## account iteration preamble
    # Create user
    if choice == '10':
        user_name = get_user_name()
    elif choice == '15':
        user_name = get_user_name()
        
    with open(aws_env_list, 'r') as aws_envs:
                for aws_account in aws_envs.readlines():
                    aws_account = aws_account.strip()
                    aws_account_number = aws_accounts_to_account_numbers(aws_account)
                    session = boto3.Session(profile_name=aws_account)
                    iam_resource = session.resource('iam')
                    iam_client = session.client('iam', use_ssl=True, verify=None)
                    kms_client = session.client('kms')
                    secrets_client = session.client('secretsmanager')
                    org_client = session.client('organizations')
                    # 1 List keys
                    if choice == "1":        
                        list_keys(iam_client, iam_resource, aws_account, aws_account_number, today, interactive)
                    # 2 Create keys
                    elif choice == "2":
                        secrets_aws_account = aws_account
                        user_name = get_user_name()
                        access_key, secret_key = create_access_key(iam_client, aws_account, user_name, interactive)
                        kms_key_id = create_kms_key(aws_account, user_name, kms_clien)
                        create_iam_policy(aws_account, kms_key_id, user_name, iam_client)
                        store_secret(aws_account, user_name, secrets_aws_account, secrets_client, access_key, secret_key, kms_key_id)
                    # 3 Delete keys
                    elif choice == "3":
                        delete_access_key(iam_client, interactive)
                    # 4 Deactivate Keys
                    elif choice == "4":
                        deactivate_access_key(iam_client, interactive)
                    # 5 Activate Keys
                    elif choice == "5":
                        activate_access_key(iam_client, interactive)
                    # 6 Rotate Keys
                    elif choice == "6":
                        rotate_access_keys(aws_account, iam_client, kms_client, secrets_client, interactive)
                    # 7 Create Standard Groups
                    elif choice == "7":
                        aws_account_number = aws_accounts_to_account_numbers(aws_account)
                        create_standard_groups(aws_account, aws_account_number, gov_account, iam_client)
                    # 8 Create Lake Nona Groups
                    elif choice == "8":
                        aws_account_number = aws_accounts_to_account_numbers(aws_account)
                        create_lake_nona_groups(aws_account, aws_account_number, gov_account, iam_client)
                    # 9 List Roles
                    elif choice == '9':
                        aws_account_number = aws_accounts_to_account_numbers(aws_account)
                        list_roles(aws_account, aws_account_number, iam_client)
                        main()
                    # 10 Create Roles
                    elif choice == "10":
                        create_roles(iam_client, aws_account)
                    # 11 Create Roles
                    elif choice == "11":
                        delete_roles(iam_client, aws_account)
                    # 12 Update Roles
                    elif choice == "12":
                        delete_roles(iam_client, aws_account)
                    # 13 Create User
                    elif choice == "13":
                        print(f"Welcome to choice 10. This is the user name: {user_name}.")
                        user_name, access_key, secret_key, user_group_list, user_secrets_list, aws_account, aws_account_number, aws_signin_url, mail_body, subject = create_user(password, iam_client, aws_account, secrets_client, interactive, user_name) 
                    # 14 Create Login Profile
                    elif choice == "14":
                        create_console_access(password, iam_client, interactive, user_name=None)
                    # 15 Delete user
                    elif choice == "15":
                        delete_user(iam_client, interactive, user_name = None)
                    # 16 List Users
                    elif choice == "16":
                        list_users(iam_client, aws_account, interactive)
                    # 17 Change User Name
                    elif choice == "17":
                        change_user_name(iam_clien, aws_account)
                    # 18 Create / Update Secret
                    elif choice == "18":
                        key_choice = input("Create new access key (y/n): ")
                        secrets_aws_account = ''
                        if key_choice.lower() == 'y' or key_choice.lower() == 'yes':
                            create_access_key(iam_client, aws_account, user_name)
                        else:
                            secrets_aws_account = input("Enter the account name for the keys: ")
                            access_key = input("Enter access key: ")
                            secret_key = input("Enter secret key: ")
                        kms_key_id = create_kms_key(aws_account, user_name, kms_client)
                        store_secret(aws_account, user_name, secrets_aws_account, secrets_client, access_key, secret_key, kms_key_id)
                    # 19 Create AWS Account
                    elif choice == "19":
                        kms_key_id = create_kms_key(aws_account, user_name, kms_client)
                    elif choice == "19":
                        print("No iteration option available for create AWS account.")
    if choice == '1':
        outfile = os.path.join('output_files', 'aws_access_keys', 'aws-access-keys-list-all-accounts.csv')
        first_name = ''
        subject = 'AWS Access Keys List ' + today
        mail_body='<font size=2 face=Verdana color=black>Hello ' +  first_name + ', <br><br>Here is a list of AWS access keys in all Synchronoss AWS accounts.<br><br>See attached!<br><br>Regards,<br>Cloud Ops</font>'
        attachment = outfile
        send_email(subject, mail_body, attachment)
    elif choice == '9':
        send_email(user_name, password, access_key, secret_key, user_group_list, user_secrets_list, aws_account, aws_account_number, aws_signin_url, mail_body, subject, attachment)

    main()
                

def set_password(stringLength=24):
    characters = string.ascii_uppercase + string.digits + string.ascii_lowercase + string.punctuation
    password = ''.join(random.sample(characters,stringLength))
    return password

# Function 12
def exit_program():
    endbanner()
    exit()

def choose_action():
    print(Fore.GREEN)
    print("*********************************************")
    print("*         Choose an Action                  *")
    print("*********************************************")
    print(Fore.YELLOW)
    print("These are the actions possible in AWS: ")
    print("1. List AWS Keys")
    print("2. Create an AWS Access Key")
    print("3. Delete an AWS Key")
    print("4. Deactivate an AWS Key")
    print("5. Activate an AWS Key")
    print("6. Rotate AWS Keys")
    print("7. Create Standard Groups")
    print("8. Create Lake Nona Groups")
    print("9. List Roles")
    print("10. Create Roles")
    print("11. Delete Roles")
    print("12. Update Roles")
    print("13. List Users")
    print("14. Create User")
    print("15. Create Console Access")
    print("16. Delete User")
    print("17. Change User Name")
    print("18. Create/Update Secret")
    print("19. Create KMS Key")
    print("20. Create AWS Account")
    print("21. Exit Program")

    choice=input("Enter an action: ")
    return choice

def get_user_name():
    print(Fore.YELLOW)
    user_name = input("Enter the user name: ")
    print('\n')
    return user_name

def create_work_dir(work_dir):
    access_rights = 0o755
    try:  
        os.mkdir(work_dir)
    except OSError:  
        print ("The directory %s already exists" % work_dir + '\n')
    else:  
        print ("Successfully created the directory %s " % work_dir + '\n')

def aws_accounts_to_account_numbers(aws_account):
    switcher = {
        'Synchronoss-lab': '486469900423',
        'Synchronoss-bill': '188087670762',
        'Synchronoss-stage': '051170381115',
        'Synchronoss-dlab': '287093337099',
        'Synchronoss-nonprod': '832839043616',
        'Synchronoss-prod': '560044853747',
        'Synchronoss-ksr-a': '764210188035',
        'Synchronoss-ksr-b': '991163571593',
        'Synchronoss-dsg-logging-admin': '962923862227',
        'Synchronoss-dsg-logging-gov': '900653850120',
        'Synchronoss-dsg-security-admin': '219577256432',
        'Synchronoss-dsg-security-gov': '902541738353',
        'Synchronoss-master': '419585237664',
        'Synchronoss-main-hub1': '303779310401',
        'Synchronoss-transit-hub3': '154101686306',
        'Synchronoss-transit-hub4': '664008221807',
        'Synchronoss-security': '193256904289',
        'Synchronoss-shared-services': '300944922012',
        'Synchronoss-logging': '826254699822',
        'Synchronoss-spoke-acct1': '103440952267',
        'Synchronoss-spoke-acct2': '288378600023',
        'Synchronoss-spoke-acct3': '872950281716',
        'Synchronoss-spoke-acct4': '167031866369',
        'Synchronoss-spoke-acct6': '067621579922',
        'Synchronoss-spoke-acct7': '580036671366',
        'Synchronoss-spoke-acct9': '806534465904',
        'Synchronoss-spoke-acct10': '421544879922',
        'Synchronoss-spoke-acct11': '795959353786',
        'Synchronoss-spoke-acct12': '353390891816',
        'Synchronoss-ab-nonprod': '151528745488',
        'Synchronoss-ab-prod': '155775729998',
        'Synchronoss-govcloud-ab-admin-nonprod': '675966588449',
        'Synchronoss-govcloud-ab-nonprod': '654077510425',
        'Synchronoss-govcloud-ab-admin-prod': '863351155240',
        'Synchronoss-govcloud-ab-prod': '654360223973',
        'Synchronoss-govcloud-ab-mc-admin-nonprod': '818951881696',
        'Synchronoss-govcloud-ab-mc-nonprod': '026715570499',
        'Synchronoss-govcloud-ab-mc-admin-prod': '609094545271',
        'Synchronoss-govcloud-ab-mc-prod': '028074947530',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-nonprod': '913530316654',
        'Synchronoss-govcloud-ab-dsg-logmon-nonprod': '042821237378',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-prod': '849740718434',
        'Synchronoss-govcloud-ab-dsg-logmon-prod': '042489471961',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-nonprod2': '142490000192',
        'Synchronoss-govcloud-ab-dsg-logmon-nonprod2': '155207289643',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-prod2': '260416396087',
        'Synchronoss-govcloud-ab-dsg-logmon-prod2': '155216231062',
        'Synchronoss-dsg-security-lab': '059345717693',
        'Synchronoss-us-aws-adv-ab-sandbox': '788139706897',
        'Synchronoss-govcloud-ab-hippa-admin-np': '061929239435',
        'Synchronoss-govcloud-ab-hippa-np': '242658374974',
        'Synchronoss-govcloud-ab-hippa-admin-pd': '231667950558',
        'Synchronoss-govcloud-ab-hippa-pd': '22433837123',
        'jf-python-dev': '369812892824',
        'jf-python-dev-gov': '894300395449',
        'jf-master-acct': '993905884429',
        'jf-spoke-acct5': '222761149296',
        'jf-security': '424743200470'
    }
    return switcher.get(aws_account, "nothing")

def aws_accounts_to_url(aws_account):
    switcher = {
        'Synchronoss-lab': 'https://Synchronoss-lab.signin.aws.amazon.com/console',
        'Synchronoss-bill': 'https://Synchronoss-bill.signin.aws.amazon.com/console',
        'Synchronoss-stage': 'https://Synchronoss-us-aws-ktech-nonprod-slab.signin.aws.amazon.com/console',
        'Synchronoss-dlab': 'https://Synchronoss-us-aws-ktech-nonprod-dlab.signin.aws.amazon.com/console',
        'Synchronoss-nonprod': 'https://Synchronoss-us-aws-ktech-nonprod.signin.aws.amazon.com/console',
        'Synchronoss-prod': 'https://Synchronoss-us-aws-ktech-prod.signin.aws.amazon.com/console',
        'Synchronoss-ksr-a': 'https://Synchronoss-us-aws-ktech-ksr-a.signin.aws.amazon.com/console',
        'Synchronoss-ksr-b': 'https://Synchronoss-us-aws-ktech-ksr-b.signin.aws.amazon.com/console',
        'Synchronoss-dsg-logging-admin': 'https://dsg-security-admin.signin.aws.amazon.com/console',
        'Synchronoss-dsg-logging-gov': 'https://dsg-logging-gov.signin.amazonaws-us-gov.com/console',
        'Synchronoss-dsg-security-admin': 'https://dsg-security-admin.signin.aws.amazon.com/console',
        'Synchronoss-dsg-security-gov': 'https://dsg-security-admin.signin.aws.amazon.com/console',
        'Synchronoss-master': 'https://us-ktech-aws-master-acct.signin.aws.amazon.com/console',
        'Synchronoss-transit-hub1': 'https://303779310401.signin.aws.amazon.com/console',
        'Synchronoss-transit-hub3': 'https://transithub3-lab.signin.aws.amazon.com/console',
        'Synchronoss-transit-hub4': 'https://Synchronoss-transit-hub4-prod.signin.aws.amazon.com/console',
        'Synchronoss-security': 'https://193256904289.signin.aws.amazon.com/console',
        'Synchronoss-shared-services': 'https://300944922012.signin.aws.amazon.com/console',
        'Synchronoss-logging': 'https://826254699822.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct1': 'https://block-chain.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct2': 'https://lakenonadev.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct3': 'https://lakehouseqa.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct4': 'https://cloud-hsm.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct6': 'https://lakenona-load-test.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct7': 'https://us-ktawsspk7acct.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct9': 'https://cloud-hsm-prod.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct10': 'https://lakehouseuat.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct11': 'https://cloud-hsm.signin.aws.amazon.com/console',
        'Synchronoss-spoke-acct12': 'https://lakehouseint.signin.aws.amazon.com/console',
        'Synchronoss-ab-nonprod': 'https://Synchronoss-ab-nonprod.signin.aws.amazon.com/console/',
        'Synchronoss-ab-prod': 'https://Synchronoss-ab-prod.signin.aws.amazon.com/console/',
        'Synchronoss-govcloud-ab-admin-nonprod': 'https://Synchronoss-govcloud-ab-admin-nonprod.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-nonprod': 'https://Synchronoss-govcloud-ab-nonprod.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-ab-admin-prod': 'https://Synchronoss-govcloud-ab-admin-prod.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-prod': 'https://Synchronoss-govcloud-ab-prod.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-ab-mc-admin-nonprod': 'https://Synchronoss-us-aws-adv-ab-mc-govcloud-admin-nonprod.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-mc-nonprod': 'https://Synchronoss-us-aws-adv-ab-mc-govcloud-nonprod.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-ab-mc-admin-prod': 'https://Synchronoss-us-aws-adv-ab-mc-govcloud-admin-prod.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-mc-prod': 'https://Synchronoss-us-aws-adv-ab-mc-govcloud-prod.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-nonprod': 'https://Synchronoss-us-aws-adv-ab-dsg-govcloud-admin-nonprod.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-dsg-logmon-nonprod': 'https://Synchronoss-us-aws-adv-ab-dsg-govcloud-nonprod.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-prod': 'https://Synchronoss-us-aws-adv-ab-dsg-govcloud-admin-prod.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-dsg-logmon-prod': 'https://Synchronoss-govcloud-ab-dsg-logmon-prod.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-nonprod2': 'https://Synchronoss-us-aws-adv-ab-dsg-govcloud-admin-nonprod2.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-dsg-logmon-nonprod2': 'https://Synchronoss-govcloud-ab-dsg-logmon-nonprod2.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-admin-ab-dsg-logmon-prod2': 'https://Synchronoss-govcloud-admin-ab-dsg-logmon-prod2.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-dsg-logmon-prod2': 'https://Synchronoss-govcloud-ab-dsg-logmon-prod2.signin.amazonaws-us-gov.com/console',
        'Synchronoss-dsg-security-admin': 'https://dsg-security-admin.signin.aws.amazon.com/console',
        'Synchronoss-us-aws-adv-ab-sandbox': 'https://Synchronoss-ab-sandbox.signin.aws.amazon.com/console',
        'jf-python-dev': 'https://jf-python-dev.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-hippa-admin-np': 'https://Synchronoss-us-aws-adv-ab-hippa-govcloud-admin-np.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-hippa-np': 'https://Synchronoss-us-aws-adv-ab-hippa-govcloud-np.signin.amazonaws-us-gov.com/console',
        'Synchronoss-govcloud-ab-hippa-admin-pd': 'https://Synchronoss-us-aws-adv-ab-hippa-govcloud-admin-pd.signin.aws.amazon.com/console',
        'Synchronoss-govcloud-ab-hippa-pd': 'https://Synchronoss-us-aws-adv-ab-hippa-govcloud-pd.signin.amazonaws-us-gov.com/console',
        'jf-python-dev-gov': 'https://jf-python-dev-gov.signin.amazonaws-us-gov.com/console',
        'jf-master-acct': 'https://us-jokefire-aws-master-acct.signin.aws.amazon.com/console',
        'jf-spoke-acct5': 'https://us-jokefire=spoke5-acct.signin.aws.amazon.com/console',
        'jf-security': 'https://jf-security.signin.aws.amazon.com/console'
        
    }
    return switcher.get(aws_account, "nothing")

# Attach IAM policy
def attach_admin_policy(group_name, gov_account, iam_client):
    policy_name = 'AdministratorAccess'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    if gov_account == True:
        policy_arn = 'arn:aws-us-gov:iam::aws:policy/AdministratorAccess' 
    else:
        policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach %s to %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)
    

# Attach IAM policy
def attach_read_only_policy(group_name, gov_account, iam_client):
    policy_name = 'ReadOnlyAccess'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    if gov_account == True:
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess' 
    else:
        policy_arn = 'arn:aws-us-gov:iam::aws:policy/ReadOnlyAccess'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach %s to %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)

# Attach IAM policy
def attach_aws_cloud9_environment_member_policy(group_name, iam_client):
    policy_name = 'AWSCloud9EnvironmentMember'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    policy_name = 'AWSCloud9EnvironmentMember'
    policy_arn = 'arn:aws:iam::aws:policy/AWSCloud9EnvironmentMember' 

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)

# Attach IAM policy
def attach_aws_cloud9_admin_policy(group_name, iam_client):
    policy_name = 'AWSCloud9Administrator'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    policy_arn = 'arn:aws:iam::aws:policy/AWSCloud9Administrator'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)
    
# Attach IAM policy
def attach_aws_cloud9_user_policy(group_name, iam_client):
    policy_name = 'AWSCloud9User'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    policy_arn = 'arn:aws:iam::aws:policy/AWSCloud9User'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)
    
# Attach IAM policy
def attach_aws_code_commit_power_user_policy(group_name, gov_account, iam_client):
    policy_name = 'AWSCodeCommitPowerUser'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")

    if gov_account == False:
        policy_arn = 'arn:aws:iam::aws:policy/AWSCodeCommitPowerUser'
    else:
        policy_arn = 'arn:aws-us-gov:iam::aws:policy/AWSCodeCommitPowerUser'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)

# Attach IAM policy
def attach_aws_code_commit_full_access_policy(group_name, gov_account, iam_client):
    policy_name = 'AWSCodeCommitFullAccess'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    if gov_account == False:
        policy_arn = 'arn:aws:iam::aws:policy/AWSCodeCommitFullAccess'
    else:
        policy_arn = 'arn:aws-us-gov:iam::aws:policy/AWSCodeCommitFullAccess'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)


# Attach IAM policy
def attach_aws_code_deploy_role_for_lambda_policy(group_name, gov_account, iam_client):
    policy_name = 'AWSCodeDeployRoleForLambda'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    if gov_account == False:
        policy_arn = 'arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda'
    else:
        policy_arn = 'arn:aws-us-gov:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)

# Attach IAM policy
def attach_aws_code_pipeline_full_access_policy(group_name, iam_client):
    policy_name = 'AWSCodePipelineFullAccess'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    policy_arn = 'arn:aws:iam::aws:policy/AWSCodePipelineFullAccess'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach policy: %s to group: %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)


# Attach S3 Read Only Policy
def attach_s3_read_only_policy(group_name, gov_account, iam_client):
    policy_name = 'AdministratorAccess'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    if gov_account == True:               
        policy_arn = 'arn:aws-us-gov:iam::aws:policy/AmazonS3ReadOnlyAccess' 
    else:
        policy_arn = 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'

    # Attach the policy to the user
    policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
    print("Attach %s to %s" % (policy_arn, group_name))
    if policy_attach_status == 200:
        print("%s policy attached to: %s" % (policy_name,group_name))
    else:
        print("%s policy not attached." % policy_name)
    time.sleep(5)

# Create secrets manager IAM policy and attach it to the user
def create_iam_policy(aws_account, kms_key_id, user_name, iam_client):
    print(Fore.CYAN)
    message = f"*   Create IAM policy for user: {user_name} in AWS account: {aws_account}   *"
    banner(message,"*")
    print(Fore.YELLOW)
    # Set the policy document
    if 'gov' in aws_account and not 'admin' in aws_account:
        policy_doc = {"Version": "2012-10-17","Statement": [{"Effect": "Allow","Action": ["secretsmanager:ListSecrets","secretsmanager:GetRandomPassword"],"Resource": "*"},{"Effect": "Allow","Action": ["kms:Decrypt"],"Resource": "arn:aws-us-gov:kms:us-east-1:832839043616:key/" + kms_key_id},{"Effect": "Allow","Action": ["kms:List*"],"Resource": "*"},{"Effect": "Allow","Action": ["secretsmanager:GetResourcePolicy","secretsmanager:GetSecretValue","secretsmanager:DescribeSecret","secretsmanager:ListSecretVersionIds"],"Resource": "*","Condition": {"ForAnyValue:StringEquals": {"secretsmanager:ResourceTag/Name": user_name}}}]}
    else:
         policy_doc = {"Version": "2012-10-17","Statement": [{"Effect": "Allow","Action": ["secretsmanager:ListSecrets","secretsmanager:GetRandomPassword"],"Resource": "*"},{"Effect": "Allow","Action": ["kms:Decrypt"],"Resource": "arn:aws:kms:us-east-1:832839043616:key/" + kms_key_id},{"Effect": "Allow","Action": ["kms:List*"],"Resource": "*"},{"Effect": "Allow","Action": ["secretsmanager:GetResourcePolicy","secretsmanager:GetSecretValue","secretsmanager:DescribeSecret","secretsmanager:ListSecretVersionIds"],"Resource": "*","Condition": {"ForAnyValue:StringEquals": {"secretsmanager:ResourceTag/Name": user_name}}}]}
    

    # See if policy by that name already exists
    policy_list = (iam_client.list_policies(Scope='Local',OnlyAttached=False))
    tree = objectpath.Tree(policy_list)
    policy_arns =  set(tree.execute('$..Arn'))
    policy_arn_list = list(policy_arns)
    policy_exists = False
    for policy_arn in policy_arn_list:
        if ('pol-aws-secrets-manager-' + user_name) in str(policy_arn):
            policy_exists = True
            policy_attached_list = (iam_client.list_attached_user_policies(UserName=user_name)['AttachedPolicies'])
            # If no policies are attached yet
            if len(policy_attached_list) == 0:
                try:
                    policy_attach_status = (iam_client.attach_user_policy(UserName=user_name,PolicyArn=policy_arn))
                    message = f"User: {user_name} has no policies attached\nPolicy exists: {policy_arn}\nSecrets manager policy has been attached to: {user_name}."
                    banner(message)
                except ValueError:
                    message = "Policy was not attached."
                    banner(message)
            # If policies are attached
            else:
                for policy in policy_attached_list:
                    policy_name = policy['PolicyName']
                    if policy_name.endswith(user_name):
                        message = f"Secrets manager policy is already attached to: {user_name}."
                        break
                    else:
                        print("Policy was not yet attached. Trying now.")
                        try:
                            policy_attach_status = (iam_client.attach_user_policy(UserName=user_name,PolicyArn=policy_arn))
                            message = f"Policy attach status: {policy_attach_status}."
                        except ValueError:
                            message = "An error occured: Policy was not attached."
                            banner(message)
  
    if policy_exists == False:
        # Create the IAM policy
        policy_arn = (iam_client.create_policy(PolicyName='pol-aws-secrets-manager-' + user_name,PolicyDocument=json.dumps(policy_doc))['Policy']['Arn'])
        print("Policy Arn:", policy_arn)
        # Attach the policy to the user
        print("Attach %s to %s" % (policy_arn, user_name))
        policy_attach_status = (iam_client.attach_user_policy(UserName=user_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
        if policy_attach_status == 200:
            print("Secrets manager policy attached to:", user_name)
        else:
            print("Secrets manager policy not attached.")
    else:
        pass
    time.sleep(5)


# Create secrets manager IAM policy and attach it to the user
def create_pol_cloud_admins_group(group_name, aws_account, aws_account_number, gov_account, iam_client):
    policy_name = 'pol-grp-cloud-admins'
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Attach IAM policy: %s to group: %s                     " % (policy_name,group_name))
    print("****************************************************************")
    if gov_account == True:
        # Set the policy document
        policy_doc = {"Version": "2012-10-17","Statement": [{"Effect": "Allow","Action": "*","Resource": "*"}]}
    else:
        policy_doc = {"Version": "2012-10-17","Statement": [{"Sid": "AllowAccessToAllServicesOtherThanSecretsManager","Effect": "Allow","NotAction": "secretsmanager:*","Resource": "*"}]}
        
    # See if policy by that name already exists
    policy_list = (iam_client.list_policies(Scope='Local',OnlyAttached=False))
    tree = objectpath.Tree(policy_list)
    policy_arns =  set(tree.execute('$..Arn'))
    policy_arn_list = list(policy_arns)
    policy_exists = False
    for policy_arn in policy_arn_list:
        if policy_name in str(policy_arn):
            policy_exists = True

    if policy_exists == False:
        # Create the IAM policy
        new_policy = (iam_client.create_policy(PolicyName=policy_name,PolicyDocument=json.dumps(policy_doc)))
        create_policy_status = (new_policy['ResponseMetadata']['HTTPStatusCode'])
        policy_arn = (new_policy['Policy']['Arn'])
        # Attach the policy to the user
        policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
        print("Creating the policy: %s in AWS account: %s" % (policy_name, aws_account))
        if create_policy_status == 200:
            print("The policy: %s has been successfully created." % policy_name)
            print("Policy Arn:", policy_arn)
        else:
            print(policy_name + " has not been created.")
        print("Attach %s to %s" % (policy_arn, group_name))
        if policy_attach_status == 200:
            print("%s policy attached to: %s" % (policy_name,group_name))
        else:
            print("%s  policy not attached." % policy_name)
    else:
        print("Policy already exists.")
    time.sleep(5)

# Create secrets manager IAM policy and attach it to the user
def create_pol_grpedit_restriction(group_name, aws_account, aws_account_number, gov_account, iam_client):
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Create IAM policy for %s                                   " % group_name)
    print("****************************************************************")
    policy_name = 'pol-grpedit-restriction'
    if gov_account == True:
        cloud_type = 'aws-us-gov'
    else:
        cloud_type = 'aws'
        
    # Set the policy document
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "LimitGroupModificationPermissions",
                "Effect": "Deny",
                "Action": "*",
                "Resource": [
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-grpedit-restriction",
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-ip-restriction",
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-region-restriction",
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-mfa-enforce"
                ]
            },
            {
                "Sid": "NoBoundaryPolicyEdit",
                "Effect": "Deny",
                "Action": [
                    "iam:CreatePolicyVersion",
                    "iam:DeletePolicy",
                    "iam:DeletePolicyVersion",
                    "iam:SetDefaultPolicyVersion"
                ],
                "Resource": [
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":policy/pol-grpedit-restriction"
                ]
            },
            {
                "Sid": "NoBoundaryUserDelete",
                "Effect": "Deny",
                "Action": "iam:DeleteUserPermissionsBoundary",
                "Resource": "*"
            },
            {
                "Sid": "NoPolicyChangeandDelete",
                "Effect": "Deny",
                "Action": [
                    "iam:CreatePolicyVersion",
                    "iam:DeletePolicy"
                ],
                "Resource": [
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-grpedit-restriction",
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-ip-restriction",
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-region-restriction",
                    "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-mfa-enforce"
                ]
            },
            {
                "Sid": "DenyAttachDetach",
                "Effect": "Deny",
                "Action": [
                    "iam:Attach*",
                    "iam:Detach*"
                ],
                "Resource": "*",
                "Condition": {
                    "ArnEquals": {
                        "iam:PolicyARN": [
                            "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-grpedit-restriction",
                            "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-ip-restriction",
                            "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-region-restriction",
                            "arn:" + cloud_type + ":iam::" + aws_account_number + ":group/grp-mfa-enforce"
                        ]
                    }
                }
            },
            {
                "Sid": "CreateOrChangeOnlyWithBoundary",
                "Effect": "Deny",
                "Action": [
                    "iam:CreateUser",
                    "iam:DeleteUserPolicy",
                    "iam:AttachUserPolicy",
                    "iam:DetachUserPolicy",
                    "iam:PutUserPermissionsBoundary"
                ],
                "Resource": "*",
                "Condition": {
                    "StringNotEquals": {
                        "iam:PermissionsBoundary": "arn:" + cloud_type + ":iam::" + aws_account_number + ":policy/pol-grpedit-restriction"
                    }
                }
            }
        ]
    }
    
    
    # See if policy by that name already exists
    policy_list = (iam_client.list_policies(Scope='Local',OnlyAttached=False))
    tree = objectpath.Tree(policy_list)
    policy_arns =  set(tree.execute('$..Arn'))
    policy_arn_list = list(policy_arns)
    policy_exists = False
    for policy_arn in policy_arn_list:
        if policy_name in str(policy_arn):
            policy_exists = True

    if policy_exists == False:
        # Create the IAM policy
        new_policy = (iam_client.create_policy(PolicyName=policy_name,PolicyDocument=json.dumps(policy_doc)))
        create_policy_status = (new_policy['ResponseMetadata']['HTTPStatusCode'])
        policy_arn = (new_policy['Policy']['Arn'])
        # Attach the policy to the user
        policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
        print("Creating the policy: %s in AWS account: %s" % (policy_name, aws_account))
        if create_policy_status == 200:
            print("The policy: %s has been successfuly created." % policy_name)
            print("Policy Arn:", policy_arn)
        else:
            print(policy_name + " has not been created.")
        print("Attach %s to %s" % (policy_arn, group_name))
        if policy_attach_status == 200:
            print("%s policy attached to: %s" % (policy_name,group_name))
        else:
            print("%s policy not attached." % policy_name)
    else:
        print("Policy already exists.")
    time.sleep(5)


# Create secrets manager IAM policy and attach it to the user
def create_pol_ip_restriction(group_name, aws_account, aws_account_number, iam_client):
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Create IAM policy for %s                                   " % group_name)
    print("****************************************************************")
    policy_name = 'pol-ip-restriction'
    # Set the policy document
    policy_doc = {"Version": "2012-10-17","Statement": {"Effect": "Deny","Action": "*","Resource": "*","Condition": {"NotIpAddress": {"aws:SourceIp": ["10.0.0.0/8","199.206.0.0/15"]}}}}
    
    # See if policy by that name already exists
    policy_list = (iam_client.list_policies(Scope='Local',OnlyAttached=False))
    tree = objectpath.Tree(policy_list)
    policy_arns =  set(tree.execute('$..Arn'))
    policy_arn_list = list(policy_arns)
    policy_exists = False
    for policy_arn in policy_arn_list:
        if policy_name in str(policy_arn):
            policy_exists = True

    if policy_exists == False:
        # Create the IAM policy
        new_policy = (iam_client.create_policy(PolicyName=policy_name,PolicyDocument=json.dumps(policy_doc)))
        create_policy_status = (new_policy['ResponseMetadata']['HTTPStatusCode'])
        policy_arn = (new_policy['Policy']['Arn'])
        # Attach the policy to the user
        policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
        print("Creating the policy: %s in AWS account: %s" % (policy_name, aws_account))
        if create_policy_status == 200:
            print("The policy: %s has been successfuly created." % policy_name)
            print("Policy Arn:", policy_arn)
        else:
            print(policy_name + " has not been created.")
        print("Attach %s to %s" % (policy_arn, group_name))
        if policy_attach_status == 200:
            print("%s policy attached to: %s" % (policy_name,group_name))
        else:
            print("%s policy not attached." % policy_name)
    else:
        print("Policy already exists.")
    time.sleep(5)

# Create secrets manager IAM policy and attach it to the user
def create_pol_mfa_enforce(group_name, aws_account, aws_account_number, gov_account, iam_client):
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Create IAM policy for %s                                   " % group_name)
    print("****************************************************************")
    policy_name = 'pol-mfa-enforce'
    if gov_account == True:
        cloud_type = 'aws-us-gov'
    else:
        cloud_type = 'aws'
    # Set the policy document
    policy_doc = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowListActions",
      "Effect": "Allow",
      "Action": [
        "iam:ListUsers",
        "iam:ListVirtualMFADevices"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowIndividualUserToListOnlyTheirOwnMFA",
      "Effect": "Allow",
      "Action": [
        "iam:ListMFADevices"
      ],
      "Resource": [
        "arn:" + cloud_type + ":iam::*:mfa/*",
        "arn:" + cloud_type + ":iam::*:user/${aws:username}"
      ]
    },
    {
      "Sid": "AllowIndividualUserToManageTheirOwnMFA",
      "Effect": "Allow",
      "Action": [
        "iam:CreateVirtualMFADevice",
        "iam:DeleteVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:ResyncMFADevice"
      ],
      "Resource": [
        "arn:" + cloud_type + ":iam::*:mfa/${aws:username}",
        "arn:" + cloud_type + ":iam::*:user/${aws:username}"
      ]
    },
    {
      "Sid": "DenyManageOtherMFAIfNotUsingMFA",
      "Effect": "Deny",
      "Action": [
        "iam:CreateVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:ListMFADevices",
        "iam:ResyncMFADevice"
      ],
      "NotResource": [
        "arn:" + cloud_type + ":iam::*:mfa/${aws:username}",
        "arn:" + cloud_type + ":iam::*:user/${aws:username}"
      ],
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    },
    {
      "Sid": "DenyStopAndStartWhenMFAIsNotPresent",
      "Effect": "Deny",
      "Action": [
        "workspaces:*",
        "ec2:*",
        "s3:*",
        "a4b:*",
        "acm:*",
        "apigateway:",
        "application-autoscaling:*",
        "autoscaling-plans:D*",
        "appstream:*",
        "appsync:*",
        "athena:*",
        "autoscaling:*",
        "batch:*",
        "cloud9:*",
        "clouddirectory:*",
        "cloudformation:*",
        "cloudfront:*",
        "cloudhsm:*",
        "cloudsearch:*",
        "cloudtrail:*",
        "cloudwatch:*",
        "codebuild:*",
        "codecommit:*",
        "codedeploy:*",
        "codepipeline:*",
        "codestar:List*",
        "codestar:Describe*",
        "codestar:Get*",
        "codestar:Verify*",
        "cognito-identity:Describe*",
        "cognito-identity:Get*",
        "cognito-identity:List*",
        "cognito-identity:Lookup*",
        "cognito-sync:List*",
        "cognito-sync:Describe*",
        "cognito-sync:Get*",
        "cognito-sync:QueryRecords",
        "cognito-idp:AdminGet*",
        "cognito-idp:AdminList*",
        "cognito-idp:List*",
        "cognito-idp:Describe*",
        "cognito-idp:Get*",
        "config:Deliver*",
        "config:Describe*",
        "config:Get*",
        "config:List*",
        "connect:List*",
        "connect:Describe*",
        "connect:GetFederationToken",
        "datasync:Describe*",
        "datasync:List*",
        "datapipeline:Describe*",
        "datapipeline:EvaluateExpression",
        "datapipeline:Get*",
        "datapipeline:List*",
        "datapipeline:QueryObjects",
        "datapipeline:Validate*",
        "dax:BatchGetItem",
        "dax:Describe*",
        "dax:GetItem",
        "dax:ListTags",
        "dax:Query",
        "dax:Scan",
        "directconnect:Describe*",
        "devicefarm:List*",
        "devicefarm:Get*",
        "discovery:Describe*",
        "discovery:List*",
        "discovery:Get*",
        "dlm:Get*",
        "dms:Describe*",
        "dms:List*",
        "dms:Test*",
        "ds:Check*",
        "ds:Describe*",
        "ds:Get*",
        "ds:List*",
        "ds:Verify*",
        "dynamodb:*",
        "ecr:*",
        "ecs:*",
        "eks:",
        "elasticache:*",
        "elasticbeanstalk:*",
        "elasticfilesystem:*",
        "elasticloadbalancing:*",
        "elasticmapreduce:*",
        "elastictranscoder:*",
        "es:*",
        "events:*",
        "firehose:*",
        "fsx:*",
        "gamelift:*",
        "glacier:*",
        "greengrass:*",
        "guardduty:*",
        "health:*",
        "iam:AddRoleToInstanceProfile",
        "iam:AddUserToGroup",
        "iam:AddUserToGroup",
        "iam:AttachGroupPolicy",
        "iam:AttachRolePolicy",
        "iam:AttachUserPolicy",
        "iam:CreateAccessKey",
        "iam:CreateAccountAlias",
        "iam:CreateGroup",
        "iam:CreateInstanceProfile",
        "iam:CreateLoginProfile",
        "iam:CreateOpenIDConnectProvider",
        "iam:CreatePolicy",
        "iam:CreatePolicyVersion",
        "iam:CreateRole",
        "iam:CreateSAMLProvider",
        "iam:CreateUser",
        "iam:DeactivateMFADevice",
        "iam:DeleteAccessKey",
        "iam:DeleteAccountAlias",
        "iam:DeleteAccountPasswordPolicy",
        "iam:DeleteGroup",
        "iam:DeleteGroupPolicy",
        "iam:DeleteInstanceProfile",
        "iam:DeleteLoginProfile",
        "iam:DeleteOpenIDConnectProvider",
        "iam:DeletePolicy",
        "iam:DeletePolicyVersion",
        "iam:DeleteRole",
        "iam:DeleteRolePolicy",
        "iam:DeleteSAMLProvider",
        "iam:DeleteSSHPublicKey",
        "iam:DeleteServerCertificate",
        "iam:DeleteSigningCertificate",
        "iam:DeleteUser",
        "iam:DeleteUserPolicy",
        "iam:DetachRolePolicy",
        "iam:DetachGroupPolicy",
        "iam:GenerateCredentialReport",
        "iam:GetAccessKeyLastUsed",
        "iam:GetAccountAuthorizationDetails",
        "iam:GetAccountPasswordPolicy",
        "iam:GetAccountSummary",
        "iam:GetContextKeysForCustomPolicy",
        "iam:GetContextKeysForPrincipalPolicy",
        "iam:GetCredentialReport",
        "iam:GetGroup",
        "iam:GetGroupPolicy",
        "iam:GetInstanceProfile",
        "iam:GetLoginProfile",
        "iam:GetOpenIDConnectProvider",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:GetRole",
        "iam:GetRolePolicy",
        "iam:GetSAMLProvider",
        "iam:GetSSHPublicKey",
        "iam:GetServerCertificate",
        "iam:GetServiceLastAccessedDetailsWithEntities",
        "iam:GetUser",
        "iam:GetUserPolicy",
        "iam:PutRolePolicy",
        "iam:PutUserPolicy",
        "iam:RemoveClientIDFromOpenIDConnectProvider",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:RemoveUserFromGroup",
        "iam:SetDefaultPolicyVersion",
        "iam:SimulateCustomPolicy",
        "iam:SimulatePrincipalPolicy",
        "iam:UpdateAccessKey",
        "iam:UpdateAccountPasswordPolicy",
        "iam:UpdateAssumeRolePolicy",
        "iam:UpdateGroup",
        "iam:UpdateLoginProfile",
        "iam:UpdateOpenIDConnectProviderThumbprint",
        "iam:UpdateSAMLProvider",
        "iam:UpdateSSHPublicKey",
        "iam:UpdateServerCertificate",
        "iam:UpdateSigningCertificate",
        "iam:UpdateUser",
        "iam:UploadSSHPublicKey",
        "iam:UploadServerCertificate",
        "iam:GenerateServiceLastAccessedDetails",
        "iam:GetServiceLastAccessedDetails",
        "iam:PassRole",
        "iam:CreateServiceLinkedRole",
        "iam:CreateServiceSpecificCredential",
        "iam:DeleteServiceLinkedRole",
        "iam:DeleteServiceSpecificCredential",
        "iam:GetServiceLinkedRoleDeletionStatus",
        "iam:ResetServiceSpecificCredential",
        "iam:UpdateRoleDescription",
        "iam:UpdateServiceSpecificCredential",
        "importexport:*",
        "inspector:*",
        "iot:*",
        "iotanalytics:*",
        "kinesisanalytics:*",
        "kinesisvideo:*",
        "kinesis:*",
        "kms:*",
        "lambda:*",
        "lex:*",
        "lightsail:*",
        "logs:*",
        "machinelearning:*",
        "mobileanalytics:*",
        "mobilehub:*",
        "mobiletargeting:*",
        "mq:*",
        "opsworks:*",
        "organizations:*",
        "pi:",
        "polly:*",
        "rekognition:",
        "rds:*",
        "redshift:*",
        "resource-groups:*",
        "route53:*",
        "route53domains:*",
        "sagemaker:*",
        "sdb:*",
        "secretsmanager:*",
        "serverlessrepo:*",
        "servicecatalog:*",
        "servicediscovery:*",
        "ses:*",
        "shield:*",
        "snowball:*",
        "sns:*",
        "sqs:*",
        "ssm:*",
        "states:*",
        "storagegateway:*",
        "sts:*",
        "swf:*",
        "tag:*",
        "transcribe:*",
        "trustedadvisor:*",
        "waf:*",
        "waf-regional:*",
        "workdocs:*",
        "workmail:*",
        "xray:*"
      ],
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
    
    # See if policy by that name already exists
    policy_list = (iam_client.list_policies(Scope='Local',OnlyAttached=False))
    tree = objectpath.Tree(policy_list)
    policy_arns =  set(tree.execute('$..Arn'))
    policy_arn_list = list(policy_arns)
    policy_exists = False
    for policy_arn in policy_arn_list:
        if policy_name in str(policy_arn):
            policy_exists = True

    if policy_exists == False:
        # Create the IAM policy
        new_policy = (iam_client.create_policy(PolicyName=policy_name,PolicyDocument=json.dumps(policy_doc)))
        create_policy_status = (new_policy['ResponseMetadata']['HTTPStatusCode'])
        policy_arn = (new_policy['Policy']['Arn'])
        # Attach the policy to the user
        policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
        print("Creating the policy: %s in AWS account: %s" % (policy_name, aws_account))
        if create_policy_status == 200:
            print("Policy Arn:", policy_arn)
        else:
            print(policy_name + " has not been created.")
        print("Attach %s to %s" % (policy_arn, group_name))
        if policy_attach_status == 200:
            print("%s policy attached to: %s" % (policy_name,group_name))
        else:
            print("%s policy not attached." % policy_name)
    else:
        print("Policy already exists.")
    time.sleep(5)

# Create secrets manager IAM policy and attach it to the user
def create_pol_region_restriction(group_name, aws_account, aws_account_number, gov_account, iam_client):
    print(Fore.CYAN)
    print("****************************************************************")
    print("         Create IAM policy for %s                                   " % group_name)
    print("****************************************************************")
    policy_name = 'pol-region-restriction'
    if gov_account == True:
        region_type = 'us-gov-west-1'
    else:
        region_type = 'us-east-1'
    # Set the policy document
    policy_doc = {"Version": "2012-10-17","Statement": [{"Sid": "DenyAllRegionsExceptUsEast1","Effect": "Deny","Action": "*","Resource": "*","Condition": {"ForAnyValue:StringNotEquals": {"aws:RequestedRegion": region_type}}}]}
    
    # See if policy by that name already exists
    policy_list = (iam_client.list_policies(Scope='Local',OnlyAttached=False))
    tree = objectpath.Tree(policy_list)
    policy_arns =  set(tree.execute('$..Arn'))
    policy_arn_list = list(policy_arns)
    policy_exists = False
    for policy_arn in policy_arn_list:
        if policy_name in str(policy_arn):
            policy_exists = True

    if policy_exists == False:
        # Create the IAM policy
        new_policy = (iam_client.create_policy(PolicyName=policy_name,PolicyDocument=json.dumps(policy_doc)))
        create_policy_status = (new_policy['ResponseMetadata']['HTTPStatusCode'])
        policy_arn = (new_policy['Policy']['Arn'])
        # Attach the policy to the user
        policy_attach_status = (iam_client.attach_group_policy(GroupName=group_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
        print("Creating the policy: %s in AWS account: %s" % (policy_name, aws_account))
        if create_policy_status == 200:
            print("The policy: %s has been successfuly created." % policy_name)
            print("Policy Arn:", policy_arn)
        else:
            print(policy_name + " has not been created.")
            print("Attach %s to %s" % (policy_arn, group_name))
        if policy_attach_status == 200:
            print("%s policy attached to: %s" % (policy_name,group_name))
        else:
            print("%s policy not attached." % policy_name)
    else:
        print("Policy already exists.")
    time.sleep(5)

def create_pol_rl_Synchronoss_admin():
    policy_doc = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::832839043616:user/efrainjimenez1",
          "arn:aws:iam::832839043616:role/rl-lambda-execution-iam-ro",
          "arn:aws:iam::832839043616:user/bkolodny",
          "arn:aws:iam::832839043616:user/michaelmartinez1",
          "arn:aws:iam::419585237664:user/efrainjimenez1",
          "arn:aws:iam::419585237664:user/tdunphy",
          "arn:aws:iam::832839043616:user/tdunphy",
          "arn:aws:iam::832839043616:user/us-svc-cloudops-aws"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
    policy_doc = json.dumps(policy_doc)
    return policy_doc

def create_pol_rl_netops():
    policy_doc = json.dumps({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::832839043616:user/tstroebele",
          "arn:aws:iam::832839043616:user/jrobbins",
          "arn:aws:iam::832839043616:user/mfranqueira"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
})
    return policy_doc


def create_pol_rl_Synchronoss_read_only():
    policy_doc = json.dumps({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::832839043616:user/tafaritaylor1",
          "arn:aws:iam::832839043616:user/robertwong",
          "arn:aws:iam::832839043616:user/mohammadbilal",
          "arn:aws:iam::832839043616:user/stephenwhite",
          "arn:aws:iam::832839043616:user/tdunphy",
          "arn:aws:iam::832839043616:user/chengwu"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
})
    return policy_doc

def create_kms_key(aws_account, user_name, kms_client):
    print(Fore.CYAN)
    message = f"*   Create KMS Key for user: {user_name} in AWS account: {aws_account}   *"
    banner(message, "*")
    print(Fore.YELLOW)
    alias_list = (kms_client.list_aliases())
    alias_name_exists = False
    kms_key_alias_response = ''
    for alias in alias_list['Aliases']:
        my_alias  = alias['AliasName']
        if 'TargetKeyId' in alias:
            if user_name in my_alias:
                kms_key_id = alias['TargetKeyId']
                message = f"User: {user_name} already has a key assigned.\nAlias Name: {my_alias} belongs to KMS Key ID: {kms_key_id}."
                banner(message)
                alias_name_exists = True
                break
            else:
                alias_name_exists = False
    
    if alias_name_exists == False:
        alias_name = 'alias/Synchronoss-kms-key-' + user_name
        try:
            kms_key_id = (kms_client.create_key()['KeyMetadata']['KeyId'])
            if kms_key_id:
                message = f"Creating new kms key for: {user_name}\nKMS Key ID: {kms_key_id}\nKMS Key Alias: {alias_name}."
            else:
                print(f"ELSE: {kms_key_alias_response}")
                message = "KMS Key has not been created."
                banner(message)
        except Exception as e:
            print(f"An exception occurred: {e}")
        try:       
            kms_key_alias_response = (kms_client.create_alias(AliasName=alias_name,TargetKeyId=kms_key_id)['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            print(f"An exception has occurred: {e}.")
        banner(message)
    time.sleep(5)
    return kms_key_id

def send_email(subject, mail_body, attachment= None):
    print(Fore.CYAN)
    print('******************************************************')
    print('*             Send Email                             *')
    print('******************************************************\n')
    print(Fore.YELLOW)
    ## Get the user's first name
    #first_name = input("Enter the recipient's first name: ")
    to_addr = input("Enter the recipient's email address: ")
    from_addr = 'cloudops@noreply.Synchronoss.com'
    cc = ['tdunphy@Synchronoss.com']
    bcc = ['bluethundr@gmail.com']
    to_addrs = [to_addr] + cc + bcc
    content = mail_body
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = MIMEText(content, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtpout.us.kworld.Synchronoss.com', 25)
    if attachment is None:
        try:
            server.send_message(msg, from_addr=from_addr, to_addrs=to_addrs)
            print(f"Email was sent to: {to_addr}.")
            time.sleep(5)
        except Exception as e:
            print(f"Exception: {e}")
            print("Email was not sent.")
            time.sleep(5)
    else:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read(), Name=basename(attachment))
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(attachment))
            msg.attach(part)
            try:
                server.send_message(msg, from_addr=from_addr, to_addrs=to_addrs)
                print(f"Email was sent to: {to_addrs}")
                time.sleep(5)
            except Exception as e:
                print(f"Exception: {e}")
                print("Email was not sent.")
                time.sleep(5)


### End utility functions

## Function 1
def list_keys(iam_client, iam_resource, aws_account, aws_account_number, today, interactive):
    print(Fore.RESET)
    print('******************************************************************************')
    print('             List AWS Access Keys in account: %s' % aws_account)
    print('******************************************************************************\n')
    print(Fore.GREEN)
    output_dir = os.path.join('output_files', 'aws_access_keys')
    with contextlib.redirect_stdout(io.StringIO()):
        create_work_dir(output_dir)
    if interactive == 1:
        outfile = os.path.join(output_dir, 'aws-access-keys-list-' + aws_account + '.csv')
    else:
        outfile = os.path.join(output_dir, 'aws-access-keys-list-all-accounts.csv')
    max_days = 0
    key_list = []
    fieldnames = ''
    timeLimit=datetime.now() - timedelta(days=max_days)
    if interactive == 1:
        try:
            with open(outfile, mode='w+') as csv_file:
                title_writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
                title_writer.writerow(["AWS Access Key List " + today])
                fieldnames = ['User Name', 'Access Key', 'Access Key Date', 'Last Used', 'Days Active', 'AWS Account', 'AWS Account Number']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                writer.writeheader()
        except Exception as error:
            print("Exception: ", error)
    print("User Name                                  Access Key                                  Access Key Creation Date                   Last Used                            Days Active                  AWS Account                  AWS Account Number")
    print("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    for user in iam_resource.users.all():
        meta_data = iam_client.list_access_keys(UserName=user.user_name)
        if meta_data['AccessKeyMetadata']:
            for key in user.access_keys.all():
                    access_id = key.access_key_id 
                    last_used = (iam_client.get_access_key_last_used(AccessKeyId=access_id)['AccessKeyLastUsed'])
                    if 'LastUsedDate' in last_used:
                        last_used = (iam_client.get_access_key_last_used(AccessKeyId=access_id)['AccessKeyLastUsed']['LastUsedDate'].strftime("%Y-%m-%d, %H:%M:%S"))
                    else:
                        last_used = 'Never'
                    access_key_date = meta_data['AccessKeyMetadata'][0]['CreateDate']
                    my_access_key_date = meta_data['AccessKeyMetadata'][0]['CreateDate'].date()
                    current_date = date.today()
                    active_days = current_date - my_access_key_date
                    active_days = str(active_days)
                    active_days = (active_days.strip(', 0:00:00')) 
                    if access_key_date.date() <= timeLimit.date():
                        access_key_date = access_key_date.strftime("%Y-%m-%d, %H:%M:%S")
                        access_key_date = str(access_key_date)
                        last_user = str(last_used)
                        active_days = str(active_days)
                        print("User: ", user.user_name.ljust(35, ' '), "Access Key: ", access_id.ljust(30, ' '), "Access Key Date:", access_key_date.ljust(25, ' '), "Last Used:", last_used.ljust(25, ' '), "Days Active:", active_days.ljust(15, ' '), "AWS Account:", aws_account.ljust(15, ' '), "AWS Account Number:", aws_account_number)
                        with open(outfile,'a') as csv_file:
                            fieldnames = ['User Name', 'Access Key', 'Access Key Creation Date', 'Last Used', 'Days Active', 'AWS Account', 'AWS Account Number']
                            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                            writer.writerow({'User Name': user.user_name, 'Access Key': access_id, 'Access Key Creation Date': access_key_date, 'Last Used': last_used, 'Days Active': active_days, 'AWS Account': aws_account, 'AWS Account Number': aws_account_number})
                        key_list.append(access_id)

    if len(key_list) == 0:
        print("NO access keys older than ", max_days, " days in:", aws_account)
    if interactive == 1:
        aws_account_number = aws_accounts_to_account_numbers(aws_account)
        first_name = input("Enter the user's first name: ")
        subject = 'AWS Access Keys List ' + today
        mail_body='<font size=2 face=Verdana color=black>Hello ' +  first_name + ', <br><br>Here is a list of AWS access keys in: ' + aws_account + ' (' + aws_account_number + ')' + '<br><br>See attached!<br><br>Regards,<br>Cloud Ops</font>'
        attachment = outfile
        send_email(subject, mail_body, attachment)
        time.sleep(10)
    elif interactive == 0:
        pass

# Function 2
def create_access_key(iam_client, aws_account, user_name):
    print(Fore.CYAN)
    message = f"*  Create AWS Access Keys for user: {user_name} in AWS account: {aws_account}   *"
    banner(message,"*")
    print(Fore.YELLOW)
    iam_users_list = iam_client.list_users()
    tree = objectpath.Tree(iam_users_list)
    user_names = set(tree.execute('$..Users[\'UserName\']'))
    if user_name in user_names:
        # Loop through the keys
        paginator = iam_client.get_paginator('list_access_keys')
        for response in paginator.paginate(UserName=user_name):
            ## See if key 1 exists
            if len(response['AccessKeyMetadata']) and 'AccessKeyId' in response['AccessKeyMetadata'][0].keys():
                key1 =  response['AccessKeyMetadata'][0]['AccessKeyId']
            else:
                key1 = None

            ## See if key 2 exists
            if len(response['AccessKeyMetadata']) > 1 and 'AccessKeyId' in response['AccessKeyMetadata'][1].keys():
                key2 =  response['AccessKeyMetadata'][1]['AccessKeyId']
            else:
                key2 = None
            
            # End function if key 2 exists
            if key2:
                print("Sorry. The user %s already has the maximum number of access keys." % user_name)
                time.sleep(5)
                main()
            else:
                new_keys = iam_client.create_access_key(UserName=user_name)
                access_key = new_keys['AccessKey']['AccessKeyId']
                secret_key = new_keys['AccessKey']['SecretAccessKey']
                message = f"New access key created: {access_key}"
                banner(message)
            time.sleep(5)
    else:
        message = f"User name: {user_name} does not exist in {aws_account}."
        banner(message)
        time.sleep(5)
        main()
    return access_key, secret_key
            
# Function 3
def delete_access_key(iam_client, interactive):
    print(Fore.CYAN)
    print('******************************************************')
    print('*             Delete AWS Access Keys                 *')
    print('******************************************************\n')
    # Ask for a user name
    user_name = input("Enter a user name: ")
    # Loop through the keys
    paginator = iam_client.get_paginator('list_access_keys')
    for response in paginator.paginate(UserName=user_name):
        #print("Raw response: ", response) 
        if len(response['AccessKeyMetadata']) and 'AccessKeyId' in response['AccessKeyMetadata'][0].keys():
            key1 =  response['AccessKeyMetadata'][0]['AccessKeyId']
        else:
            key2 = None
        if len(response['AccessKeyMetadata']) > 1 and 'AccessKeyId' in response['AccessKeyMetadata'][1].keys():
            key2 =  response['AccessKeyMetadata'][1]['AccessKeyId']
        else:
            key2 = None
    if key1:
        print("Key 1:", key1)
    if key2:
        print("Key 2:", key2)
    key_id = str(input("Enter an access key: "))
    # Ask for the key to delete
    if key_id:
        delete_response = iam_client.delete_access_key(UserName=user_name, AccessKeyId=key_id)
        delete_status = delete_response['ResponseMetadata']['HTTPStatusCode']
    # Verify that the key was deleted
    if delete_status == 200:
        print("Access Key deleted")
    else:
        print("Access Key not deleted")
    time.sleep(5)

# Function 5
def deactivate_access_key(iam_client):
    print(Fore.CYAN)
    print('******************************************************')
    print('*             Deactivate AWS Access Keys             *')
    print('******************************************************\n')
    key1 = ''
    key2 = ''
    # Ask for a user name
    user_name = input("Enter a user name: ")
    # Loop through the keys
    paginator = iam_client.get_paginator('list_access_keys')
    for response in paginator.paginate(UserName=user_name):
        #print("Raw response: ", response) 
        if len(response['AccessKeyMetadata']) and 'AccessKeyId' in response['AccessKeyMetadata'][0].keys():
            key1 =  response['AccessKeyMetadata'][0]['AccessKeyId']
        else:
            key2 = None
        if len(response['AccessKeyMetadata']) > 1 and 'AccessKeyId' in response['AccessKeyMetadata'][1].keys():
            key2 =  response['AccessKeyMetadata'][1]['AccessKeyId']
        else:
            key2 = None
    if key1:
        print("Key 1: ", key1)
    if key2:
        print("Key 2: ", key2)
    key_id = input("Enter an access key: ")
    # Ask for the key to delete
    if key_id:
        deactivate_response = iam_client.update_access_key(AccessKeyId=key_id,Status='Inactive',UserName=user_name)
        deactivate_status = deactivate_response['ResponseMetadata']['HTTPStatusCode']
    time.sleep(5)
    # Verify that the key was deleted
    if deactivate_status == 200:
        print("Access Key deactivated")
    else:
        print("Access Key not deactivated")
    time.sleep(5)

# Function 5
def activate_access_key(iam_client):
    print(Fore.CYAN)
    print('******************************************************')
    print('*             Activate AWS Access Keys               *')
    print('******************************************************\n')
    # Ask for a user name
    user_name = input("Enter a user name: ")
    # Loop through the keys
    paginator = iam_client.get_paginator('list_access_keys')
    for response in paginator.paginate(UserName=user_name):
        #print("Raw response: ", response) 
        if len(response['AccessKeyMetadata']) and 'AccessKeyId' in response['AccessKeyMetadata'][0].keys():
            key1 =  response['AccessKeyMetadata'][0]['AccessKeyId']
        else:
            key2 = None
        if len(response['AccessKeyMetadata']) > 1 and 'AccessKeyId' in response['AccessKeyMetadata'][1].keys():
            key2 =  response['AccessKeyMetadata'][1]['AccessKeyId']
        else:
            key2 = None
    if key1:
        print("Key 1: ", key1)
    if key2:
        print("Key 2: ", key2)
    key_id = input("Enter an access key: ")
    # Ask for the key to delete
    if key_id:
        deactivate_response = iam_client.update_access_key(AccessKeyId=key_id,Status='Active',UserName=user_name)
        deactivate_status = deactivate_response['ResponseMetadata']['HTTPStatusCode']
    # Verify that the key was deleted
    if deactivate_status == 200:
        print("Access Key activated")
    else:
        print("Access Key not activated")
    time.sleep(5)

# Function 6
def rotate_access_keys(aws_account, iam_client, kms_client, secrets_client):
    print(Fore.CYAN)
    print('******************************************************')
    print('*             Rotate AWS Access Keys                 *')
    print('******************************************************\n')
    print("AWS Account from Secrets:", aws_account)
    access_key = ''
    secret_key = ''
    key1 = None
    key2 = None
    print("Secrets AWS Account:", secrets_aws_account)
    # Ask for a user name
    print(Fore.YELLOW)
    user_name = input("Enter a user name: ")
    # Loop through the keys
    paginator = iam_client.get_paginator('list_access_keys')
    for response in paginator.paginate(UserName=user_name):
        if len(response['AccessKeyMetadata']) and 'AccessKeyId' in response['AccessKeyMetadata'][0].keys():
            key1 = response['AccessKeyMetadata'][0]['AccessKeyId']
        else:
            key2 = None
        if len(response['AccessKeyMetadata']) > 1 and 'AccessKeyId' in response['AccessKeyMetadata'][1].keys():
            key2 =  response['AccessKeyMetadata'][1]['AccessKeyId']
        else:
            key2 = None
        # Print the keys
        if key1:
            print("\nAccess Key 1: ", key1)
        else:
            print("The user does not have any keys.")
            time.sleep(5)
            main()

        if key2:
            print("Access Key 2: ", key2)
        key_id = input("\nEnter an access key: ")
            # Ask for the key to delete
        if key_id:
            delete_response = iam_client.delete_access_key(UserName=user_name, AccessKeyId=key_id)
            delete_status = delete_response['ResponseMetadata']['HTTPStatusCode']
        # Verify that the key was deleted
        if delete_status == 200:
            print("Access Key deleted")
        else:
            print("Access Key not deleted")
            time.sleep(5)
        # Create an access key
        response = iam_client.create_access_key(UserName=user_name)
        create_status = response['ResponseMetadata']['HTTPStatusCode']
        # Verify that the key was created
        if create_status == 200:
            print("\nAccess Key created")
        else:
            print("\nAccess Key not created")
        #print(response)
        access_key = response['AccessKey']['AccessKeyId']
        secret_key = response['AccessKey']['SecretAccessKey']
        print("New Access Key:", access_key)
        time.sleep(5)
        kms_key_id = create_kms_key(aws_account, user_name, kms_client)
        create_iam_policy(aws_account, kms_key_id, user_name, iam_client)
        user_secrets_list = store_secret(aws_account, account_name, secrets_aws_account, user_name, secrets_client, access_key, secret_key, kms_key_id)

    return user_name, access_key, secret_key, user_secrets_list

# Function 7
def create_standard_groups(aws_account, aws_account_number, gov_account, iam_client):
    print(Fore.CYAN)
    print('******************************************************')
    print('*            Create Standard Groups                  *')
    print('******************************************************\n')
    #################################
    # List the groups in the account
    group_list = iam_client.list_groups()

    ####################
    # Set the group name
    group_name = 'grp-cloud-admins'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')

    # Create the group if it doesn't exist
    group_exists = False
    create_group_status = ''
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False

    if group_exists == True:
        print("Group name %s already exists in %s." % (group_name, aws_account))
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group: %s has been successfully created." % group_name)
            time.sleep(5)
        else:
            print("The group: %s has not been created." % group_name)
            time.sleep(5)
        create_pol_cloud_admins_group(group_name, aws_account, aws_account_number, gov_account, iam_client)
    
    ###################
    # Set the group name
    group_name = 'grp-grpedit-restriction'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')

    # Create the group if it doesn't exist
    group_exists = False
    create_group_status = ''
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False
 
    if group_exists == True:
        print("Group name %s already exists in %s." % (group_name, aws_account))
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group: %s has been successfully created." % group_name)
            time.sleep(5)
        else:
            print("The group: %s has not been created." % group_name)
            time.sleep(5)
        create_pol_grpedit_restriction(group_name, aws_account, aws_account_number, gov_account, iam_client)

    ####################   
    # Set the group name
    group_name = 'grp-ip-restriction'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')
    
    # Create the group if it doesn't exist
    group_exists = False
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False
             
    if group_exists == True:
        print("Group name already exists in %s." % aws_account)
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group: %s has been successfully created." % group_name)
            time.sleep(5)
        else:
            print("The group: %s has not been created." % group_name)
            time.sleep(5)
        create_pol_ip_restriction(group_name, aws_account, aws_account_number, iam_client)

    ####################    
    # Set the group name
    group_name = 'grp-mfa-enforce'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')
    
    # Create the group if it doesn't exist
    group_exists = False
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False

    if group_exists == True:
        print("Group name already exists in %s." % aws_account)
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group %s has been successfully created." % group_name)
        else:
            print("The group %s has not been created." % group_name)
        create_pol_mfa_enforce(group_name, aws_account, aws_account_number, gov_account, iam_client)

    ####################
    # Set the group name
    group_name = 'grp-region-restriction'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')
    
    # Create the group if it doesn't exist
    group_exists = False
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False

    if group_exists == True:
        print("Group name already exists in %s." % aws_account)
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group %s has been successfully created." % group_name)
            time.sleep(5)
        else:
            print("The group %s has not been created." % group_name)
            time.sleep(5)
        create_pol_region_restriction(group_name, aws_account, aws_account_number, gov_account, iam_client)

    ####################
    # Set the group name
    group_name = 'grp-s3-readonly'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')
    
    # Create the group if it doesn't exist
    group_exists = False
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False

    if group_exists == True:
        print("Group name already exists in %s." % aws_account)
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group %s has been successfully created." % group_name)
            time.sleep(5)
        else:
            print("The group %s has not been created." % group_name)
            time.sleep(5)
        create_pol_region_restriction(group_name, aws_account, aws_account_number, gov_account, iam_client)

# Function 8
def create_lake_nona_groups(aws_account, aws_account_number, gov_account, iam_client):
    print(Fore.CYAN)
    print('******************************************************')
    print('*            Create Standard Groups                  *')
    print('******************************************************\n')
    #################################
    # List the groups in the account
    group_list = iam_client.list_groups()

    ####################
    # Set the group name
    group_name = 'LakeNonaAdmins'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')

    # Create the group if it doesn't exist
    group_exists = False
    create_group_status = ''
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False

    if group_exists == True:
        print("Group name %s already exists in %s." % (group_name, aws_account))
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group: %s has been successfully created." % group_name)
            attach_admin_policy(group_name, gov_account, iam_client)
            attach_aws_cloud9_environment_member_policy(group_name, iam_client)
            attach_aws_cloud9_admin_policy(group_name, iam_client)
            
            time.sleep(5)
        else:
            print("The group: %s has not been created (it already exists)." % group_name)
            time.sleep(5)

    ####################
    # Set the group name
    group_name = 'codecommit-group'
    print(Fore.GREEN)
    print('******************************************************')
    print('             Creating: %s' % group_name)
    print('******************************************************\n')
    # Create the group if it doesn't exist
    group_exists = False
    create_group_status = ''
    for group in group_list['Groups']:
        my_group_name = group['GroupName']
        if my_group_name == group_name:
            group_exists = True
            break
        else:
            group_exists = False

    if group_exists == True:
        print("Group name %s already exists in %s." % (group_name, aws_account))
    else:
        print("Creating the group: %s in AWS account: %s" % (group_name, aws_account))
        create_group_status = (iam_client.create_group(GroupName=group_name)['ResponseMetadata']['HTTPStatusCode'])
        if create_group_status == 200:
            print("The group: %s has been successfully created." % group_name)
            attach_aws_code_commit_power_user_policy(group_name, gov_account, iam_client)
            attach_aws_code_commit_full_access_policy(group_name, gov_account, iam_client)
            attach_aws_code_deploy_role_for_lambda_policy(group_name, gov_account, iam_client)
            attach_aws_code_pipeline_full_access_policy(group_name, iam_client)
            time.sleep(5)
        else:
            print("The group: %s has not been created." % group_name)
            time.sleep(5)
            
def list_roles(aws_account, aws_account_number, iam_client):
    print('******************************************************')
    print(f'             List AWS Roles in {aws_account}: {aws_account_number}   ')
    print('******************************************************\n')
    list_roles_response = iam_client.list_roles()
    tree = objectpath.Tree(list_roles_response)
    roles_list = set(tree.execute('$..Roles[\'RoleName\']'))
    for role_name in roles_list:
        print(Fore.CYAN + f"Role Name: {role_name}")
    time.sleep(10)

# Function 9
def create_roles(iam_client, aws_account):
    print(Fore.CYAN)
    print('******************************************************')
    print(f'             Create New AWS Role in {aws_account}    ')
    print('******************************************************\n')
    role_name = input("Enter the role name: ")
    if role_name == 'rl-Synchronoss-admin':
        policy_doc = create_pol_rl_Synchronoss_admin()
        role_description = 'rl-Synchronoss-admin gives users admin access to the account.'
        policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'
    elif role_name == 'rl-netops':
        policy_doc = create_pol_rl_netops()
        role_description = 'rl-netops gives users read only access to the account.'
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    elif role_name == 'rl-Synchronoss-read-only':
        policy_doc = create_pol_rl_Synchronoss_read_only()
        role_description = 'rl-Synchronoss-read-only gives users read only access to the account.'
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    try:    
        create_role_response = (iam_client.create_role(RoleName=role_name,AssumeRolePolicyDocument=policy_doc, Description=role_description)['ResponseMetadata']['HTTPStatusCode'])
        # Verify that console login was created
        if create_role_response == 200:
            print(Fore.GREEN + f"Role: {role_name} created.")
            time.sleep(10)
        else:
            print(Fore.RED + f"Role: {role_name} not created.")
            time.sleep(10)
    except Exception as e:
        print(f"An exception has occurred: {e}")



    try:
        attach_policy_response = (iam_client.attach_role_policy(PolicyArn=policy_arn,RoleName=role_name)['ResponseMetadata']['HTTPStatusCode'])
            # Verify that console login was created
        if attach_policy_response == 200:
            print(Fore.GREEN + f"Policy arn: {policy_arn} attached to: {role_name}.")
            time.sleep(10)
        else:
            print(Fore.RED + f"Policy Arn: {policy_arn} attached to: {role_name}.")
            time.sleep(10)
    except Exception as e:
        print(f"An exceltion has occurred: {e}")
    


# Function 10
def delete_roles(iam_client, aws_account):
    print(Fore.CYAN)
    print('******************************************************')
    print(f'             Delete AWS Role in {aws_account}        ')
    print('******************************************************\n')
    detach_role_response = ''
    role_name = input("Enter the role name: ")
    if role_name == 'rl-Synchronoss-admin':
        policy_doc = create_pol_rl_Synchronoss_admin()
        policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'
    elif role_name == 'rl-netops':
        policy_doc = create_pol_rl_netops()
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    elif role_name == 'rl-Synchronoss-read-only':
        policy_doc = create_pol_rl_Synchronoss_read_only()
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    try:    
        detach_role_response = ((iam_client.detach_role_policy(PolicyArn=policy_arn,RoleName=role_name)['ResponseMetadata']['HTTPStatusCode']))
        # Verify that console login was deleted
        if detach_role_response == 200:
            print(Fore.GREEN + f"Policy arn: {policy_arn} detached from: {role_name}.")
            time.sleep(5)
        else:
            print(Fore.GREEN + f"Policy Arn: {policy_arn} detached from: {role_name}.")
            time.sleep(5)
    except Exception as e:
        print(f"An exception has occurred: {e}")

    try:    
        delete_role_response = ((iam_client.delete_role(RoleName=role_name)['ResponseMetadata']['HTTPStatusCode']))
        # Verify that console login was deleted
        if delete_role_response == 200:
            print(Fore.GREEN + f"Role: {role_name} was deleted.")
            time.sleep(5)
        else:
            print(Fore.GREEN + f"Role: {role_name} was not deleted.")
            time.sleep(5)
    except Exception as e:
        print(f"An exception has occurred: {e}")


# Function 9
def update_roles(iam_client, aws_account):
    print(Fore.CYAN)
    print('******************************************************')
    print(f'             Update AWS Role in {aws_account}    ')
    print('******************************************************\n')
    role_name = input("Enter the role name: ")
    if role_name == 'rl-Synchronoss-admin':
        policy_doc = create_pol_rl_Synchronoss_admin()
        role_description = 'rl-Synchronoss-admin gives users admin access to the account.'
        policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'
    elif role_name == 'rl-netops':
        policy_doc = create_pol_rl_netops()
        role_description = 'rl-netops gives users read only access to the account.'
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    elif role_name == 'rl-Synchronoss-read-only':
        policy_doc = create_pol_rl_Synchronoss_read_only()
        role_description = 'rl-Synchronoss-read-only gives users read only access to the account.'
        policy_arn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    
    try:    
        detach_role_policy_response = ((iam_client.detach_role_policy(PolicyArn=policy_arn,RoleName=role_name)['ResponseMetadata']['HTTPStatusCode']))
        # Verify that console login was deleted
        if detach_role_policy_response == 200:
            print(Fore.GREEN + f"Policy arn: {policy_arn} detached from: {role_name}.")
            time.sleep(5)
        else:
            print(Fore.GREEN + f"Policy Arn: {policy_arn} detached from: {role_name}.")
            time.sleep(5)
    except Exception as e:
        print(f"An exception has occurred: {e}")

    try:    
        delete_role_response = ((iam_client.delete_role(RoleName=role_name)['ResponseMetadata']['HTTPStatusCode']))
        # Verify that console login was deleted
        if delete_role_response == 200:
            print(Fore.GREEN + f"Role: {role_name} was deleted.")
            time.sleep(10)
        else:
            print(Fore.GREEN + f"Role: {role_name} was not deleted.")
            time.sleep(10)
    except Exception as e:
        print(f"An exception has occurred: {e}")

    try:    
        create_role_response = (iam_client.create_role(RoleName=role_name,AssumeRolePolicyDocument=policy_doc, Description=role_description)['ResponseMetadata']['HTTPStatusCode'])
        # Verify that console login was created
        if create_role_response == 200:
            print(Fore.GREEN + f"Role: {role_name} created.")
            time.sleep(10)
        else:
            print(Fore.RED + f"Role: {role_name} not created.")
            time.sleep(10)

    except Exception as e:
        print(f"An exception has occurred: {e}")


    try:
        attach_policy_response = (iam_client.attach_role_policy(PolicyArn=policy_arn,RoleName=role_name)['ResponseMetadata']['HTTPStatusCode'])
        # Verify that console login was created
        if attach_policy_response == 200:
            print(Fore.GREEN + f"Policy arn: {policy_arn} attached to: {role_name}.")
            time.sleep(10)
        else:
            print(Fore.RED + f"Policy Arn: {policy_arn} attached to: {role_name}.")
            time.sleep(10)
    except Exception as e:
        print(f"An exceltion has occurred: {e}")
    

    
# Function 11
def create_user(password, iam_client, kms_client, secrets_client, aws_account, interactive, user_name=None):
    print(Fore.CYAN)
    message = f'*   Create New AWS User in {aws_account}   *'
    banner(message,"*")
    if user_name:
        message = f"User: {user_name} has been passed to this function."
        banner(message)
    iam_users_list = iam_client.list_users()
    if user_name not in iam_users_list:
        print(Fore.YELLOW)
        user_secrets_list = ''
        first_name = ''
        access_key = ''
        secret_key = ''
        attachment = None
        orig_aws_account = aws_account
        if interactive == 1:
            user_name = get_user_name()
        user_list =  iam_client.list_users()
        user_exists = False
        for user in user_list['Users']:
            my_user_name = user['UserName']
            if my_user_name == user_name:
                user_exists = True
            else:
                user_exists = False
        
        if user_exists == False:
            try:
                new_user = iam_client.create_user(UserName=user_name)
            except:
                message = f"User: {user_name} wasn't created."
                banner(message)
                time.sleep(5)
                main()
        else:
            message = f"User name: {user_name} already exists."
            banner(message)
            time.sleep(5)
            main()

        ## List the groups in the account
        message = f"List the groups in AWS account: {aws_account}"
        banner(message)
        group_list = iam_client.list_groups()
        all_groups = []
        user_group_list = []
        for group in group_list['Groups']:
            group_name = group['GroupName']
            all_groups.append(group_name)
        
        for group_name in all_groups:
            print(group_name)

        ## Add user to groups
        message = f"Add user: {user_name} to groups in AWS account: {aws_account}."
        banner(message)
        message = f"Type quit to stop adding groups."
        banner(message)
        add_group_name = ''
        while add_group_name.strip() != 'quit':
            add_group_name = input("Enter the group name to add to user %s: " % user_name)
            if add_group_name.strip() == 'quit':
                message = f"OK. Done adding groups to: {user_name}."
                banner(message)
                time.sleep(5)
                break
            else:
                iam_client.add_user_to_group(GroupName=add_group_name,UserName=user_name)
                user_group_list.append(add_group_name)

        # Get AWS account number
        aws_account_number = aws_accounts_to_account_numbers(aws_account)
        # Get the sign in url
        aws_signin_url = aws_accounts_to_url(aws_account)

        message = f"The user has the following information\nUser Name: {user_name}\nAWS Account: {aws_account}\nAWS Account Number: {aws_account_number}\nAWS Sign In URL: {aws_signin_url}"
        banner(message)

        # Prepare the email
        # Prepare the group list for email
        sep = ', '
        sep = sep.join(user_group_list)
        user_group_list = sep
        message = f'Group list: {user_group_list}'
        banner(message)

        #Provide console access
        console_access = input("\nGive the user console access (y/n): ")
        if console_access.lower() == 'yes' or console_access.lower() == 'y':
            create_console_access(password, iam_client, user_name)
        
        # Provide key access
        print(Fore.YELLOW)
        key_access = input("Give the user an access key (y/n): ")
        if key_access.lower() == 'yes' or key_access.lower() == 'y':
            access_key, secret_key = create_access_key(iam_client, aws_account, user_name)
            secrets_aws_account = aws_account
            kms_key_id = create_kms_key(aws_account, user_name, kms_client)
            create_iam_policy(aws_account, kms_key_id, user_name, iam_client)
            user_secrets_list = store_secret(aws_account, user_name, secrets_aws_account, secrets_client, access_key, secret_key, kms_key_id)
            aws_account = orig_aws_account
        else:
            user_secrets_list = ''
        print(Fore.RESET)


        # Prepare the secrets list for the email
        if user_secrets_list:
            sep = sep.join(user_secrets_list)
            user_secrets_list = sep
            print(Fore.YELLOW + 'Secrets list:', user_secrets_list)

        # Mail for console access and access key access
        if (console_access.lower() == "yes" or console_access.lower() == "y") and (key_access.lower() == "yes" or key_access.lower() == "y"):
            access_type = 'console_key_access'  
        elif console_access.lower() == "yes" or console_access.lower() == "y":
            access_type = 'console_access'
        # Mail for access key access
        elif key_access.lower() == "yes" or key_access.lower() == "y":
            access_type = 'key_access'
        kiki_mfa_url = '<a href="https://kiki.us.kworld.Synchronoss.com/display/6TO/Enable+MFA+in+AWS">Enable MFA in AWS</a>'
        ## Get the user's first name
        if interactive == 1:
            first_name = input("Enter the recipient's first name: ")
            subject = 'Welcome To AWS Account: ' + aws_account + ' (' + aws_account_number + ')'
            # Mail for console access and access key access
            if access_type == 'console_key_access':
                mail_body="<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>You have been given access to this AWS account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>You can get started by using the sign-in information provided below.<br><br>-------------------------------------------------<br><br>Sign-in URL: " + aws_signin_url + "<br>User name: " + user_name + "<br>Password: "  + password + "<br><br>-------------------------------------------------<br><br>When you sign in for the first time, you must change your password.<br><br>The user name " +  user_name + " belongs to these groups: <br><br>" + user_group_list + "<br><br>You have been issued new AWS access keys for this account. You will find them in the secrets manager of the same AWS account.<br><br>Please refer to the following secret for access to your keys:<br><br> " + user_secrets_list +  "<br><br>Please note: YOU MUST ENABLE MFA BEFORE USING THESE RESOURCES.<br><br>Refer to this url for MFA instructions: " + kiki_mfa_url + "<br><br>Regards,<br>Cloud Ops</font>"
            # Mail for console access
            elif access_type == 'console_access':
                mail_body="<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>You have been given access to this AWS account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>You can get started by using the sign-in information provided below.<br><br>-------------------------------------------------<br><br>Sign-in URL: " + aws_signin_url + "<br>User name: " + user_name + "<br>Password: "  + password + "<br><br>-------------------------------------------------<br><br>When you sign in for the first time, you must change your password.<br><br>The user name " +  user_name + " belongs to these groups: <br><br>" + user_group_list + "<br><br>Please note: YOU MUST ENABLE MFA BEFORE USING THESE RESOURCES.<br><br>Refer to this url for MFA instructions: " + kiki_mfa_url + "<br><br>Regards,<br>Cloud Ops</font>"
            # Mail for access key access
            elif access_type == 'key_access':
                mail_body="<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>You have been given access to this AWS account: " + aws_account + " (" + aws_account_number + ")" + "<br><br>The user name " +  user_name + " belongs to these groups: <br><br>" + user_group_list + ".<br><br>You have been issued new AWS access keys for this account. You will find them in the secrets manager of the same AWS Account.<br><br>Please refer to the following secret for access to your keys:<br><br> " + user_secrets_list + "<br><br>Please note: YOU MUST ENABLE MFA BEFORE USING THESE RESOURCES.<br><br>Refer to this url for MFA instructions: " + kiki_mfa_url + "<br><br>Regards,<br>Cloud Ops</font>"
        else:
            #aws_account = aws_account.append(aws_account)
            mail_body = 'tbd'
            attachment = ''
    else:
        message = f"User: {user_name} already exists in AWS Account: {aws_account}."
        banner(message)
    #print(f"Types for variables:\n User Name:{type(user_name)}\nAccess Key: {type(access_key)}\nSecret Key: {type(secret_key)}\nUser Group List: {type(user_group_list)}\nUser Secrets List: {type(user_secrets_list)}\nAWS Account: {type(aws_account)}\nAWS Account Number: {type(aws_account_number)}\nAWS Sign In URL: {type(aws_signin_url)}\nAccess Type: {type(access_type)}\nMail Body: {type(mail_body)}\nSubject: {type(subject)}\nAttachment: {type(attachment)}")
    return user_name, access_key, secret_key, user_group_list, user_secrets_list, aws_account, aws_account_number, aws_signin_url, access_type, mail_body, subject, attachment

# Function 12      
def create_console_access(password, iam_client, interactive, user_name=None):
    #print(user_name)
    print(Fore.CYAN)
    message = '*            Create Console Access                   *'
    banner(message,"*")
    if not user_name:
        user_name = get_user_name()
    new_login_profile_status = ''
    # Create the console access
    try:
        new_login_profile_status = (iam_client.create_login_profile(UserName=user_name,Password=password,PasswordResetRequired=True)['ResponseMetadata']['HTTPStatusCode'])
    except Exception as e:
        print("Exception: ", e)

    # Verify that console login was created
    if new_login_profile_status == 200:
        print(Fore.YELLOW + "Console login created.")
    else:
        print(Fore.RED + "Console login not created.")
    time.sleep(5)
    print(Fore.RESET)

# Function 13
def delete_user(iam_client, interactive, user_name = None):
    print(Fore.CYAN)
    message = '*            Delete AWS User                         *'
    banner(message,"*")
    key1 = ''
    key2 = ''
    login_profile = ''
    paginator = ''
    delete_profile_status = ''
    mfa_serial = ''
    if user_name == None:
        user_name = get_user_name()

    # Remove user from groups
    message = f"Removing user: {user_name} from groups"
    banner(message)

    user_group_list = iam_client.list_groups_for_user(UserName=user_name)

    if (len(user_group_list['Groups'])) > 0:
        print("The user belongs to these groups:")
        for group in user_group_list['Groups']:
            group_name = group['GroupName']
            print("Group Name:", group_name)
        for group in user_group_list['Groups']:
            group_name = group['GroupName']
            remove_from_group_status = (iam_client.remove_user_from_group(GroupName=group_name,UserName=user_name)['ResponseMetadata']['HTTPStatusCode'])   
            if remove_from_group_status == 200:
                message = f"User: {user_name} has been removed from group: {group_name}"
                banner(message)
            else:
                message = f"User: {user_name} has NOT been removed from group: {group_name}"
                banner(message)
        time.sleep(5)
    else:
        print("User: %s does not belong to any groups." % user_name)
    time.sleep(5)

    # Remove directly attached managed policies from user
    message = f"Removing managed policies directly attached to user: {user_name}"
    banner(message)
    managed_user_policies = (iam_client.list_attached_user_policies(UserName=user_name))
    tree = objectpath.Tree(managed_user_policies)
    managed_policies_list = set(tree.execute('$..AttachedPolicies[\'PolicyArn\']'))
    managed_policy_names = set(tree.execute('$..AttachedPolicies[\'PolicyName\']'))
    if managed_policies_list:
        for policy_arn, policy_name in zip(managed_policies_list, managed_policy_names):
            message = f"Removing: {policy_name} from User: {user_name}."
            banner(message)
            detach_user_policy_response = (iam_client.detach_user_policy(UserName=user_name,PolicyArn=policy_arn)['ResponseMetadata']['HTTPStatusCode'])
            if detach_user_policy_response == 200:
                message = f"Policy: {policy_name} has been removed from user: {user_name}"
                banner(message)
            else:
                message = f"Policy: {policy_name} has NOT been removed from user: {user_name}"
                banner(message)
    else:
        message = f"User: {user_name} has no managed policies directly attached."
        banner(message)

    # Remove inline policies for the user
    message = f"Removing inline policies directly attached to user: {user_name}"
    banner(message)
    inline_user_policies = (iam_client.list_user_policies(UserName=user_name))
    tree = objectpath.Tree(inline_user_policies)
    inline_policies_list = list(tree.execute('$..PolicyNames'))
    if inline_user_policies['PolicyNames']:
        for policy_name in inline_policies_list:
            print(f"Deleting inline policy: {policy_name} for user: {user_name}.")
            delete_inline_policy_response = (iam_client.delete_user_policy(UserName=user_name,PolicyName=policy_name)['ResponseMetadata']['HTTPStatusCode'])
        if delete_inline_policy_response == 200:
            message = f"Policy: {policy_name} has been removed from user: {user_name}."
            banner(message)
        else:
            message = f"Policy: {policy_name} has NOT been removed from user: {user_name}."
            banner(message)
    else:
        message = f"User: {user_name} has no inline policies directly attached."
        banner(message)
        
    # Delete access keys
    message = f"Removing access keys from user: {user_name}."
    banner(message)
    paginator = iam_client.get_paginator('list_access_keys')
    for response in paginator.paginate(UserName=user_name):
        if response['AccessKeyMetadata']:
            if len(response['AccessKeyMetadata']) and 'AccessKeyId' in response['AccessKeyMetadata'][0].keys():
                key1 =  response['AccessKeyMetadata'][0]['AccessKeyId']
            else:
                key2 = None
            if len(response['AccessKeyMetadata']) > 1 and 'AccessKeyId' in response['AccessKeyMetadata'][1].keys():
                key2 =  response['AccessKeyMetadata'][1]['AccessKeyId']
            else:
                key2 = None

            if key1:
                print("\nDeleting Key 1:", key1)
                delete_response = iam_client.delete_access_key(UserName=user_name, AccessKeyId=key1)
                delete_status = (delete_response['ResponseMetadata']['HTTPStatusCode'])
                # Verify that the key was deleted
                if delete_status == 200:
                    print(f"Access Key 1 deleted.")
                else:
                    print("Access Key 1 not deleted.")
                time.sleep(5)
            if key2:
                print("Deleting Key 2:", key2)
                delete_response = iam_client.delete_access_key(UserName=user_name, AccessKeyId=key2)
                delete_status = (delete_response['ResponseMetadata']['HTTPStatusCode'])
                # Verify that the key was deleted
                if delete_status == 200:
                    print("Access Key 2 deleted.")
                else:
                    print("Access Key 2 not deleted.")
                time.sleep(5)
        else:
            message = f"User: {user_name} does not have any access keys."
            banner(message)
    time.sleep(5)
    
    # Delete login profile
    message = f"Removing Login Profile from user: {user_name}"
    banner(message)
    try:
        login_profile = (iam_client.get_login_profile(UserName=user_name)['LoginProfile']['UserName'])
    except iam_client.exceptions.NoSuchEntityException:
        message = f"User: {user_name} Login Profile does not exist."
        banner(message)

    if login_profile == user_name:
        try:
            delete_login_profile_status = (iam_client.delete_login_profile(UserName=user_name)['ResponseMetadata']['HTTPStatusCode'])
            message = f"User: {user_name} login profile deleted."
            banner(message)
        except Exception as e:
            print("Exception was: ", e)
            delete_profile_status = False
    else:
        pass
    time.sleep(5)

    # Delete the MFA
    message = f"Removing MFA from user: {user_name}."
    banner(message)
    mfa_exists = (iam_client.list_mfa_devices(UserName=user_name)['MFADevices'])
    if mfa_exists:
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
        except Exception as e:
            message = f"Exception: {e}"
            banner(message)
    else:
        message = f"User: {user_name} has no MFA devices."
        banner(message)
        mfa_exists = False
    time.sleep(5)

    # Delete signing certificates
    message = f"Removing Signing Certificates from user: {user_name}."
    banner(message)
    signing_certificate_list = (iam_client.list_signing_certificates(UserName=user_name)['Certificates'])
    if len(signing_certificate_list) == 0:
        message = f"User: {user_name} has no signing certificates."
        banner(message)
    else:
        message = "Listing Signing Cert IDs."
        banner(message)
        cert_ids = []
        for certificate in signing_certificate_list:
             cert_ids.append(certificate['CertificateId'])
        for cert_id in cert_ids:
            message = f"Certificate ID: {cert_id}."
            banner(message)

        message = "Deleting Signing Certificates."
        banner(message)
        for cert_id in cert_ids:
            try:
                delete_signing_certificate = iam_client.delete_signing_certificate(UserName=user_name,CertificateId=cert_id)
                message = f"Signing Certificate: cert_id deleted."
                banner(message)

            except Exception as e:
                message = "Exception: {e}"
                banner(message)
    time.sleep(5)
    
    # Delete ssh keys
    message = f"Removing SSH Keys from user: {user_name}."
    banner(message)
    ssh_keys_list = (iam_client.list_ssh_public_keys(UserName=user_name)['SSHPublicKeys'])
    if len(ssh_keys_list) == 0:
        message = "The user has no ssh keys."
        banner(message)
    else:
        message = "Listing SSH keys."
        banner(message)
        ssh_key_ids = []
        for ssh_key in ssh_keys_list:
            ssh_key_id = ssh_key['SSHPublicKeyId']
            message = f"SSH KEY: {ssh_key_id}"
            banner(message)
        
        message = f"Deleting SSH Keys."
        banner(message)
        for ssh_key in ssh_keys_list:
            ssh_key_id = ssh_key['SSHPublicKeyId']
            try:
                delete_ssh_key_result = (iam_client.delete_ssh_public_key(UserName=user_name,SSHPublicKeyId=ssh_key_id))
                message = f"SSH Key: {ssh_key_id} deleted"
                banner(message)
            except Exception as e:
                message = f"SSH key not deleted: {e}"
                banner(message)  

    # Delete the user
    message  = f"Deleting the User: {user_name}"
    banner(message)
    try:
        delete_user_status = (iam_client.delete_user(UserName=user_name)['ResponseMetadata']['HTTPStatusCode'])
        if delete_user_status == 200:
            print(Fore.GREEN + "\nUser: %s has been deleted" % user_name)
    except Exception as e:
        message = "Exception: {e}"
        banner(message)
    time.sleep(5)

# 14 List Users
def list_users(iam_client, aws_account, interactive):
    print(Fore.CYAN)
    message = f"*    List AWS Users in AWS Account: {aws_account}     *"
    banner(message,"*")
    print("User Name                                User ID                       User ARN                                                          Create Date           Password Last Used           Access Key 1               Access Key 2  ")
    print("-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    user_list = iam_client.list_users()
    access_key1 = ' '
    access_key2 = ' '
    for user in user_list['Users']:
        user_name = user['UserName']
        user_id = user['UserId']
        user_arn = user['Arn']
        create_date = user['CreateDate']
        time_format = "%Y-%m-%d %H:%M:%S"
        create_date = str(create_date.strftime(time_format))
        access_key_list = (iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata'])
        try:
            access_key1 = access_key_list[0]['AccessKeyId']
        except Exception as e:
            access_key1 = ' '
            #print("Exception: ", e)
        try:
            access_key2 = access_key_list[1]['AccessKeyId']
        except Exception as e:
            access_key2 = ' '
            #print("Exception: ", e)
        try:
            pass_last_used = str(user['PasswordLastUsed'].strftime(time_format))
        except Exception as e:
            pass_last_used = ' '
            #print("Exception: ", e)
        print_string = ''
        # No Access Key 1, Access Key 2, Pass Last Used
        if access_key1 == ' ' and access_key2 == ' ' and pass_last_used != ' ':
            print_string = user_name.ljust(30, ' ') + '           ' + user_id + '         ' + user_arn.ljust(60, ' ') + '      ' + create_date.ljust(21, ' ')  + ' ' + pass_last_used + ' ' + access_key2
        # No Access Key 1 and Pass Last Used 
        elif access_key1 == ' ' and pass_last_used == ' ':
            print_string = user_name.ljust(30, ' ') + '           ' + user_id + '         ' + user_arn.ljust(60, ' ') + '      ' + create_date + '   ' + ' ' + access_key1.ljust(25, ' ') + pass_last_used + ' ' + access_key2
        # No Pass Last Used
        elif pass_last_used == ' ':
            print_string = user_name.ljust(30, ' ') + '           ' + user_id + '         ' + user_arn.ljust(60, ' ') + '      ' + create_date.ljust(47, ' ') + '   ' + ' ' + access_key1.ljust(25, ' ') + pass_last_used + ' ' + access_key2
        # Access key 1 exists, access key 2 exists and pass last used exists
        else:
            print_string = user_name.ljust(30, ' ') + '           ' + user_id + '         ' + user_arn.ljust(60, ' ') + '      ' + create_date.ljust(22, ' ') + pass_last_used.ljust(28, ' ')  + ' ' +  access_key1.ljust(27, ' ') + ' ' + access_key2
        print(print_string)
    time.sleep(15)

# 15 Change User Name:
def change_user_name(iam_client, aws_account):
    print(Fore.CYAN)
    message = f"*   Change User name in AWS account: {aws_account}   *"
    banner(message,"*")
    user_name = get_user_name()
    new_user_name = input("Enter the new user name: ")
    change_user_name_response = (iam_client.update_user(UserName=user_name,NewUserName=new_user_name)['ResponseMetadata']['HTTPStatusCode'])
    if change_user_name_response == 200:
        print(Fore.GREEN + f"User name: {user_name} has been changed to: {new_user_name} in AWS account: {aws_account}.")
        time.sleep(15)
    else:
        print(Fore.CYAN + f"User name: {user_name} has not been been changed.")
        time.sleep(15)

    
# 16 Create / Update Secret
def store_secret(aws_account, user_name, secrets_aws_account, secrets_client, access_key, secret_key, kms_key_id):
    print(Fore.CYAN)
    message = f"*   Store Secret for user: {user_name} in AWS account: {aws_account}   *"
    banner(message,"*")
    key_info = []
    user_secrets_list = []

    ## Set the info for the new secret
    secrets_list = secrets_client.list_secrets()
    secret_exists = False
    secret_name = secrets_aws_account + '-keys' + '-' + user_name
    secret_description = user_name + "'s " + secrets_aws_account + " Access keys."
    #key_info = str([{"Access Key":access_key},{"Secret Key":secret_key}])
    #key_info = str({
	#user_name: {
	#	"access_key": access_key,
     #	"secret_key": secret_key
	 # }
    #})
    key_info = json.dumps({
	user_name: {
		"access_key": access_key,
		"secret_key": secret_key
	  }
    })
    # Find the user's secret
    print(Fore.YELLOW)
    for secret in secrets_list['SecretList']:
        my_secret_name = secret['Name']
        if my_secret_name == secret_name:
            message = f"Find the user's secret.\nUser {user_name} already a secret: {my_secret_name}."
            banner(message)
            secret_exists = True
            break
        else:
            secret_exists = False


    # Take action based on whether or not the user already has a secret        
    if secret_exists == True:
        message = f"Updating user secret: {secret_name}."
        banner(message)
        aws_secret = secrets_client.update_secret(SecretId=secret_name,Description=secret_description,KmsKeyId=kms_key_id,SecretString=key_info)
        user_secrets_list.append(aws_secret['Name'])
    else:
        message = f"Find the user's secret.\nSecret does not exist yet.\nCreate this secret name: {secret_name}."
        banner(message)
        try:
            aws_secret = secrets_client.create_secret(Name=secret_name,Description=secret_description,KmsKeyId=kms_key_id,SecretString=key_info,Tags=[{'Key': 'Name','Value': user_name}])
            #aws_secret = aws.deploy_secret(name=secret_name, secret_data=key_info)
            user_secrets_list.append(aws_secret['Name'])
        except Exception as error:
            print(f"An error occured: {error}")
    time.sleep(5)
    return user_secrets_list

# 17 Create AWS Account
def create_account(org_client):
    print(Fore.YELLOW)
    email_address = input("Enter an email address: ")
    time.sleep(5)
    account_type = input("Create a commercial acccount or a gov account: ")
    time.sleep(5)
    account_name = input("Enter an AWS account name: ")
    time.sleep(5)
    account_name = account_name.strip()
    account_create = ''
    create_account_response = ''
    role_name = input("Enter a role name: ")
    billing_permission = input("Allow IAM access to billing (Y/N): ")
    time.sleep(5)
    if billing_permission.lower() == 'y' or billing_permission.lower() == 'yes':
        allow_billing = 'ALLOW'
    else:
        allow_billing = 'DENY'

    if account_type == 'commercial':
        try:
            create_account_response = (org_client.create_account(Email=email_address,AccountName=account_name,RoleName=role_name,IamUserAccessToBilling=allow_billing)['ResponseMetadata']['HTTPStatusCode'])
        except Exception as error:
            print("An error occured creating your account: ", error)
            time.sleep(5)
        if create_account_response == 200:
            account_created = True
        else:
            account_created = False
        time.sleep(5)
    elif account_type == 'gov':
        print("Entered gov")
        try:
            create_account_response = (org_client.create_gov_cloud_account(Email=email_address,AccountName=account_name,RoleName=role_name,IamUserAccessToBilling=allow_billing)['ResponseMetadata']['HTTPStatusCode'])
            print(f"Create account response: {create_account_response}")
        except Exception as error:
            print(f"An error occured creating your account: {error}")
        if create_account_response == 200:
            account_created = True
        else:
            account_created = False
    else:
        print("That is not a valid account type.")

    # Check to see if the account was created
    if account_created == True:
        print(Fore.CYAN + f"AWS account was created: {account_name}")
        time.sleep(5)
    else:
        print("AWS account was not created.")


## Main function
def main():
    welcomebanner()
    password = set_password()
    choice = choose_action()
    if choice == '21':
        exit_program()
    else:
        aws_accounts_question, aws_account, aws_account_number, gov_account, iam_client, kms_client, secrets_client, org_client, iam_resource, today = initialize()
    if aws_accounts_question.lower() == "one":
        interactive = 1  
        # 1 List keys
        if choice == '1':            
            list_keys(iam_client, iam_resource, aws_account, aws_account_number, today, interactive)
            main()
        # 2 Create keys
        elif choice == '2':
            secrets_aws_account = aws_account
            user_name = get_user_name()
            access_key, secret_key = create_access_key(iam_client, aws_account, user_name)
            kms_key_id = create_kms_key(aws_account, user_name, kms_client)
            create_iam_policy(aws_account, kms_key_id, user_name, iam_client)
            store_secret(aws_account, user_name, secrets_aws_account, secrets_client, access_key, secret_key, kms_key_id)
            time.sleep(5)
            main()
        # 3 Delete keys
        elif choice == '3':
            delete_access_key(iam_client, interactive)
            main()
        # 4 Deactivate Keys
        elif choice == '4':
            deactivate_access_key(iam_client, interactive)
            main()
        # 5 Activate Keys
        elif choice == '5':
            activate_access_key(iam_client, interactive)
            main()
        # 6 Rotate Keys
        elif choice == '6':
            rotate_access_keys(aws_account, iam_client, kms_client, secrets_client, interactive)
            main()
        # 7 Create Standard Groups
        elif choice == '7':
            aws_account_number = aws_accounts_to_account_numbers(aws_account)
            create_standard_groups(aws_account, aws_account_number, gov_account, iam_client)
            main()
        # 8 Create Lake Nona Groups
        elif choice == '8':
            aws_account_number = aws_accounts_to_account_numbers(aws_account)
            create_lake_nona_groups(aws_account, aws_account_number, gov_account, iam_client)
            main()
        # 9 List Roles
        elif choice == '9':
            aws_account_number = aws_accounts_to_account_numbers(aws_account)
            list_roles(aws_account, aws_account_number, iam_client)
            main()
        # 10 Create Roles
        elif choice == '10':
            create_roles(iam_client, aws_account)
            main()
        # 11 Delete Roles
        elif choice == '11':
            delete_roles(iam_client, aws_account)
            main()
        # 12 Update Roles
        elif choice == '12':
            update_roles(iam_client, aws_account)
            main()
        # 13 List Users
        elif choice == '13':
            list_users(iam_client, aws_account, interactive)
            main()
        # 14 Crete User
        elif choice == '14':
            user_name, access_key, secret_key, user_group_list, user_secrets_list, aws_account, aws_account_number, aws_signin_url, access_type, mail_body, subject, attachment = create_user(password, iam_client, kms_client, secrets_client, aws_account, interactive)
            send_email(subject, mail_body, attachment)
            main()
        # 15 Create Login Profile
        elif choice == '15':

            create_console_access(password, iam_client, interactive)
            main()
        # 16 Delete user
        elif choice == '16':
            user_name = get_user_name()
            delete_user(iam_client, interactive, user_name)
            main()
        # 17 Change user name
        elif choice == '17':
            change_user_name(iam_client, aws_account)
            main()
        # 18 Create / Update Secret
        elif choice == '18':
            user_name = get_user_name()
            key_choice = input("Create new access key (y/n): ")
            secrets_aws_account = ''
            if key_choice.lower() == 'y' or key_choice.lower() == 'yes':
                create_access_key(iam_client, aws_account, user_name)
            else:
                secrets_aws_account = input("Enter the account name for the keys: ")
                access_key = input("Enter access key: ")
                secret_key = input("Enter secret key: ")
            kms_key_id = create_kms_key(aws_account, user_name, kms_client)
            store_secret(aws_account, user_name, secrets_aws_account, secrets_client, access_key, secret_key, kms_key_id)
            main()
       # 19 Create KMS Key
        elif choice == '19':
            user_name = input("Enter the user name: ")
            kms_key_id = create_kms_key(aws_account, user_name, kms_client)
            print(f"Your KMS Key ID: {kms_key_id}")
        # 20 Create AWS Account
        elif choice == '20':
            create_account(org_client)
            main()
    elif aws_accounts_question.lower() == "many" or aws_accounts_question.lower() == "all":
        aws_account_iterator(aws_accounts_question, aws_account, aws_account_number, gov_account, iam_client, kms_client, secrets_client, org_client, iam_resource, today, choice)
    else:
        print("That is not a valid choice.")
        main()
        
if __name__ == "__main__":
    main()
#!/usr/bin/env python3

# Import modules
import boto3
import botocore
import time
import objectpath
import csv
import smtplib
import os
import argparse
import getpass
import json
import keyring
import requests
from html import escape
from botocore.exceptions import ValidationError
from requests.auth import HTTPBasicAuth
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from ec2_mongo import insert_doc,set_db,mongo_export_to_file

# Initialize the color ouput with colorama
init()

BASE_URL = "https://confluence.company.net:8443/rest/api/content"
VIEW_URL = "https://confluence.company.net:8443/pages/viewpage.action?pageId="

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             List AWS EC2 Instances                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* List AWS Instance Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def authenticate():
    auth = get_login()
    return auth

def initialize(interactive, aws_account):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set the fieldnames for the CSV and for the confluence page
    fieldnames = [ 'AWS Account', 'Account Number', 'Name', 'Instance ID', 'AMI ID', 'Volumes', 'Private IP', 'Public IP', 'Private DNS', 'Region', 'Availability Zone', 'VPC ID', 'Type', 'Key Pair Name', 'State', 'Launch Date']
    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'csv', '')
    ### Interactive == 1  - user specifies an account
    if interactive == 1:
        output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.csv')
        output_file_name = 'aws-instance-list-' + aws_account + '-' + today + '.csv'
    else:
        output_file = os.path.join(output_dir, 'aws-instance-master-list-' + today +'.csv')
        output_file_name = 'aws-instance-master-list-' + today +'.csv'
    return today, aws_env_list, output_file, output_file_name, fieldnames

def exit_program():
    endbanner()
    exit()

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

def report_instance_stats(instance_count, aws_account, account_found):
    if account_found == 'yes':
        if instance_count == 0:
            message = f"There are no EC2 instances in AWS Account: {aws_account}."
            banner(message)
        elif instance_count == 1:
            message = f"There is: {instance_count} EC2 instance in AWS Account: {aws_account}."
            banner(message)
        else:
            message = f"There are: {instance_count} EC2 instances in AWS Account: {aws_account}."
            banner(message)

def report_gov_or_comm(aws_account, account_found):
    if 'gov' in aws_account and not 'admin' in aws_account:
        message = "This is a Govcloud account."
        banner(message)
    else:
        message = "This is a commercial account."
        banner(message)


def set_regions(aws_account):
    print(Fore.GREEN)
    message = f"Getting the regions in {aws_account} "
    banner(message, "*")
    print(Fore.RESET)
    regions = []
    if 'gov' in aws_account and not 'admin' in aws_account:
        session = boto3.Session(profile_name=aws_account,region_name='us-gov-west-1')
        ec2_client = session.client('ec2')
        regions = [reg['RegionName'] for reg in ec2_client.describe_regions()['Regions']]
    else:
        session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
        ec2_client = session.client('ec2')
        regions = [reg['RegionName'] for reg in ec2_client.describe_regions()['Regions']]
    return regions


def list_instances(aws_account,aws_account_number, interactive, regions, fieldnames, show_details):
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
    options = arguments()
    instance_list = ''
    session = ''
    ec2 = ''
    account_found = ''
    PrivateDNS = None
    block_device_list = None
    instance_count = 0
    account_type_message = ''
    profile_missing_message = ''
    region = ''
    # Set the ec2 dictionary
    ec2info = {}
    print(Fore.CYAN)
    report_gov_or_comm(aws_account, account_found)
    print(Fore.RESET)
    account_found = 'yes'
    for region in regions:
        if 'gov' in aws_account and not 'admin' in aws_account:
            try:
                session = boto3.Session(profile_name=aws_account, region_name=region)
            except botocore.exceptions.ProfileNotFound as e:
                profile_missing_message = f"An exception has occurred: {e}"
                account_found = 'no'
                pass
        else:
            try:
                session = boto3.Session(profile_name=aws_account, region_name=region)
                account_found = 'yes'
            except botocore.exceptions.ProfileNotFound as e:
                profile_missing_message = f"An exception has occurred: {e}"
                pass
        try:
            ec2 = session.client("ec2")
        except Exception as e:
            print(f"An exception has occurred: {e}")
        print(Fore.GREEN)
        message = f"* Region: {region} in {aws_account}: ({aws_account_number}) *"
        banner(message, "*")

        print(Fore.RESET)
        # Loop through the instances
        try:
            instance_list = ec2.describe_instances()
        except Exception as e:
            print(f"An exception has occurred: {e}")
        try:
            for reservation in instance_list["Reservations"]:
                for instance in reservation.get("Instances", []):
                    instance_count = instance_count + 1
                    launch_time = instance["LaunchTime"]
                    launch_time_friendly = launch_time.strftime("%B %d %Y")
                    tree = objectpath.Tree(instance)
                    block_devices = set(tree.execute('$..BlockDeviceMappings[\'Ebs\'][\'VolumeId\']'))
                    if block_devices:
                        block_devices = list(block_devices)
                        block_devices = str(block_devices).replace('[','').replace(']','').replace('\'','')
                    else:
                        block_devices = None
                    private_ips =  set(tree.execute('$..PrivateIpAddress'))
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
                    name = None
                    if 'Tags' in instance:
                        try:
                            tags = instance['Tags']
                            name = None
                            for tag in tags:
                                if tag["Key"] == "Name":
                                    name = tag["Value"]
                                if tag["Key"] == "Engagement" or tag["Key"] == "Engagement Code":
                                    engagement = tag["Value"]
                        except ValueError:
                            pass
                    key_name = instance['KeyName'] if instance['KeyName'] else None
                    vpc_id = instance.get('VpcId') if instance.get('VpcId') else None
                    private_dns = instance['PrivateDnsName'] if instance['PrivateDnsName'] else None
                    ec2info[instance['InstanceId']] = {
                        'AWS Account': aws_account,
                        'Account Number': aws_account_number,
                        'Name': name,
                        'Instance ID': instance['InstanceId'],
                        'AMI ID': instance['ImageId'],
                        'Volumes': block_devices,
                        'Private IP': private_ips_list,
                        'Public IP': public_ips_list,
                        'Private DNS': private_dns,
                        'Availability Zone': instance['Placement']['AvailabilityZone'],
                        'VPC ID': vpc_id,
                        'Type': instance['InstanceType'],
                        'Key Pair Name': key_name,
                        'State': instance['State']['Name'],
                        'Launch Date': launch_time_friendly
                    }
                    instance_dict = {'AWS Account': aws_account, "Account Number": aws_account_number, 'Name': name, 'Instance ID': instance["InstanceId"], 'AMI ID': instance['ImageId'], 'Volumes': block_devices,  'Private IP': private_ips_list, 'Public IP': public_ips_list, 'Private DNS': private_dns, 'Availability Zone': instance['Placement']['AvailabilityZone'], 'VPC ID': vpc_id, 'Type': instance["InstanceType"], 'Key Pair Name': key_name, 'State': instance["State"]["Name"], 'Launch Date': launch_time_friendly}
                    mongo_instance_dict = {'_id': '', 'AWS Account': aws_account, "Account Number": aws_account_number, 'Name': name, 'Instance ID': instance["InstanceId"], 'AMI ID': instance['ImageId'], 'Volumes': block_devices,  'Private IP': private_ips_list, 'Public IP': public_ips_list, 'Private DNS': private_dns, 'Availability Zone': instance['Placement']['AvailabilityZone'], 'VPC ID': vpc_id, 'Type': instance["InstanceType"], 'Key Pair Name': key_name, 'State': instance["State"]["Name"], 'Launch Date': launch_time_friendly}
                    insert_doc(mongo_instance_dict)
                    ec2_info_items = ec2info.items
                    if show_details == 'y' or show_details == 'yes':
                        for instance_id, instance in ec2_info_items():
                            if account_found == 'yes':
                                print(Fore.RESET + "-------------------------------------")
                                for key in [
                                    'AWS Account',
                                    'Account Number',
                                    'Name',
                                    'Instance ID',
                                    'AMI ID',
                                    'Volumes',
                                    'Private IP',
                                    'Public IP',
                                    'Private DNS',
                                    'Availability Zone',
                                    'VPC ID',
                                    'Type',
                                    'Key Pair Name',
                                    'State',
                                    'Launch Date'
                                ]:
                                    print(Fore.GREEN + f"{key}: {instance.get(key)}")
                                print(Fore.RESET + "-------------------------------------")
                        else:
                            pass
                    reservation = {}
                    instance = {}
                    ec2_info_items = {}
                    ec2info = {}
        except Exception as e:
            print(f"An exception has occurred: {e}")
    if profile_missing_message == '*':
        banner(profile_missing_message)
    print(Fore.GREEN)
    report_instance_stats(instance_count, aws_account, account_found)
    print(Fore.RESET + '\n')
    return output_file

def convert_csv_to_html_table(output_file, today, interactive, aws_account):
    output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'html')
    ### Interactive == 1  - user specifies an account
    if interactive == 1:
        htmlfile = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.html')
        htmlfile_name = 'aws-instance-list-' + aws_account + '-' + today + '.html'
    else:
        htmlfile = os.path.join(output_dir, 'aws-instance-master-list-' + today + '.html')
        htmlfile_name = 'aws-instance-master-list-' + today +'.html'
    remove_htmlfile = htmlfile
    count = 0
    html = ''
    with open(output_file,'r') as CSVFILE:
        reader = csv.reader(CSVFILE)
        html += "<table><tbody>"
        for row in reader:
            html += "<tr>"
            # Process the headers
            if count == 0:
                for column in row:
                    html += "<th>%s</th>" % escape(column)
            else:
                # Process the data
                for column in row:
                    html += "<td>%s</td>" % escape(column)
            html += "</tr>"
            count += 1
        html += "</tbody></table>"
    with open(htmlfile,'w+') as HTMLFILE:
        HTMLFILE.write(html)
    return htmlfile, htmlfile_name, remove_htmlfile


def get_page_ancestors(auth, pageid):
    # Get basic page information plus the ancestors property
    url = '{base}/{pageid}?expand=ancestors'.format(
        base = BASE_URL,
        pageid = pageid)
    r = requests.get(url, auth = auth)
    r.raise_for_status()
    return r.json()['ancestors']


def get_page_info(auth, pageid):
    url = '{base}/{pageid}'.format(
        base = BASE_URL,
        pageid = pageid)
    r = requests.get(url, auth = auth)
    r.raise_for_status()
    return r.json()

def write_data_to_confluence(auth, html, pageid, title = None):
    info = get_page_info(auth, pageid)
    ver = int(info['version']['number']) + 1
    ancestors = get_page_ancestors(auth, pageid)
    anc = ancestors[-1]
    del anc['_links']
    del anc['_expandable']
    del anc['extensions']
    if title is not None:
        info['title'] = title
    data = {
        'id' : str(pageid),
        'type' : 'page',
        'title' : info['title'],
        'version' : {'number' : ver},
        'ancestors' : [anc],
        'body'  : {
            'storage' :
            {
                'representation' : 'storage',
                'value' : str(html)
            }
        }
    }
    data = json.dumps(data)
    url = '{base}/{pageid}'.format(base = BASE_URL, pageid = pageid)
    try:
        r = requests.put(
            url,
            data = data,
            auth = auth,
            headers = { 'Content-Type' : 'application/json' }
        )
    except Exception as e:
        print(f"An exception has occurred: {e}")
    if r.status_code >= 400:
        print(f"HTTP Status Code: {r.status_code}")
        raise RuntimeError(r.content)
    else:
        message = f"Wrote {info['title']} version {ver}\nURL: {VIEW_URL}{pageid}"
        print(Fore.CYAN)
        banner(message, '*')
        print(Fore.RESET)

def get_login(username = None):
    if username is None:
        username = getpass.getuser()
    passwd = None
    if passwd is None:
        passwd = getpass.getpass()
        keyring.set_password('confluence_script', username, passwd)
    return (username, passwd)

def send_email(aws_accounts_answer,aws_account,aws_account_number, interactive):
    options = arguments()
    to_addr = ''
    # Get the variables from intitialize
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
    if options.first_name:
        ## Get the address to send to
        print(Fore.YELLOW)
        first_name = options.first_name
        print(Fore.RESET)
    else:
        first_name = str(input("Enter the recipient's first name: "))

    if options.email_recipient:
        to_addr = options.email_recipient
    else:
        to_addr = input("Enter the recipient's email address: ")

    from_addr = 'jkfr.noreply@gmail.com'
    if aws_accounts_answer == 'one':
        subject = "JF AWS Instance List: " + aws_account + " (" + aws_account_number + ") " + today
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of instances in AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>The SD Team</font>"
    else:
        subject = "JF AWS Instance Master List " + today
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of instances in all company AWS accounts.<br><br>Regards,<br>The SD Team</font>"    
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
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        gmail_user = 'jkfr.noreply@gmail.com'
        gmail_password = 'ehhloWorld12345'
        server.login(gmail_user, gmail_password)
        server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
        message = f"Email was sent to: {to_addr}"
        banner(message)
    except Exception as error:
        message = f"Exception: {error}\nEmail was not sent."
        banner(message)
    print(Fore.RESET)


def remove_file(output_file, output_file_name):
    print(Fore.GREEN)
    message = f"Removing the output file: {output_file_name}"
    banner(message)
    try:
        os.remove(output_file)
    except Exception as error:
        print("Error: ", error)
        remove_stat = 1
    else:
        remove_stat = 0
    if remove_stat == 0:
        message = "File removed!"
        banner(message)
    else:
        message = "File not removed."
        banner(message)
    print(Fore.RESET)

def arguments():
    parser = argparse.ArgumentParser(description='This is a program that lists the servers in EC2')

    parser.add_argument(
    "-u",
    "--user",
    default = getpass.getuser(),
    help = "Specify the username to log into Confluence")

    parser.add_argument(
    "-d",
    "--password",
    help = "Specify the user's password")

    parser.add_argument(
    "-t",
    "--title",
    default = None,
    type = str,
    help = "Specify a new title")

    parser.add_argument(
    "-f",
    "--file",
    default = None,
    type = str,
    help = "Write the contents of FILE to the confluence page")

    parser.add_argument(
    "--html",
    type = str,
    default = None,
    nargs = '?',
    help = "Write the immediate html string to confluence page")

    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the AWS account you'll be working in")

    parser.add_argument(
    "-c",
    "--all_accounts",
    type = str,
    default = None,
    nargs = '?',
    help = "Process one or all accounts")

    parser.add_argument(
    "-p",
    "--pageid",
    type = int,
    help = "Specify the Conflunce page id to overwrite")

    parser.add_argument(
    "-e",
    "--send_email",
    type = str,
    help = "Send an email")

    parser.add_argument(
    "-r",
    "--email_recipient",
    type = str,
    help = "Who will receive the email")

    parser.add_argument(
    "-g",
    "--first_name",
    type = str,
    help = "First (given) name of the person receving the email")

    parser.add_argument(
    "-w",
    "--write_confluence",
    type = str,
    help = "Write to confluence")

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

    parser.add_argument(
    "-o",
    "--reports",
    type = str,
    help = "Run reports")

    options = parser.parse_args()
    return options

def main():
    options = arguments()

    # Display the welcome banner
    welcomebanner()

    if options.html:
        html = options.html

    if options.reports:
        reports_answer = options.reports
    else:
        print(Fore.YELLOW)
        reports_answer = input("Print reports (y/n): ")
        print(Fore.RESET )

    if options.all_accounts:
        aws_accounts_answer = options.all_accounts
    else:
        ## Select one or many accounts
        print(Fore.YELLOW)
        aws_accounts_answer = input("List instances in one or all accounts: ")
        print(Fore.RESET)

    # Set interacive variable to indicate one or many accounts
    if aws_accounts_answer.lower() == "one" or aws_accounts_answer.lower() == "1":
        interactive = 1
    else:
        interactive = 0

    if options.pageid:
        pageid = options.pageid
    else:
        pageid = 222389323 # AWS EC2 Instances - CCMI page

    if options.title:
        title = options.title
    else:
        title = 'AWS EC2 Instances - CCMI'

    aws_account_number = ''
    ### Interactive == 1  - user specifies an account
    if interactive == 1:
        ## Select the account
        if options.account_name:
            aws_account = options.account_name
        else:
            print(Fore.YELLOW)
            aws_account = input("Enter the name of the AWS account you'll be working in: ")
            print(Fore.RESET)

        if options.verbose:
            show_details = options.verbose
        else:
            print(Fore.YELLOW)
            show_details = input("Show server details (y/n): ")
            print(Fore.RESET)

        # Grab variables from initialize
        today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)

        # Read account info from the accounts list file
        account_names, account_numbers = read_account_info(aws_env_list)
        print(Fore.YELLOW)
        message = "Work in one or all accounts"
        banner(message)
        if aws_accounts_answer.lower() == 'one':
            message = f"Working in {aws_accounts_answer} account."
        else:
            message = f"Working in {aws_accounts_answer} accounts."
        banner(message)
        message = f"Working in AWS account: {aws_account}."
        banner(message)
        print(Fore.RESET)
        # Find the account's account number
        for (my_aws_account, my_aws_account_number) in zip(account_names, account_numbers):
            if my_aws_account == aws_account:
                aws_account_number = my_aws_account_number

        # Set the regions and run the program
        regions = set_regions(aws_account)
        output_file = list_instances(aws_account,aws_account_number, interactive, regions, fieldnames, show_details)
        if reports_answer.lower() == 'yes' or reports_answer.lower() == 'y':
            mongo_export_to_file(interactive, aws_account)
            htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file, today, interactive, aws_account)
            print(Fore.YELLOW)
            message = "Send an Email"
            banner(message)
            if options.send_email:
                email_answer = options.send_email
            else:
                print(Fore.YELLOW)
                email_answer = input("Send an email (y/n): ")

            if email_answer.lower() == 'y' or email_answer == 'yes':
                send_email(aws_accounts_answer,aws_account,aws_account_number, interactive)
            else:
                message = "Okay. Not sending an email."
                print(Fore.YELLOW)
                banner(message)
            print(Fore.RESET)

            with open(htmlfile, 'r') as htmlfile:
                html = htmlfile.read()

            message = "* Write to Confluence *"
            print(Fore.CYAN)
            banner(message, "*")
            print(Fore.RESET)
            if options.write_confluence:
                confluence_answer = options.write_confluence
            else:
                print(Fore.CYAN)
                confluence_answer = input("Write the list to confluence (y/n): ")
                print(Fore.RESET)

            if options.user and options.password:
                user = options.user
                password = options.password
                auth = (user, password)
                write_data_to_confluence(auth, html, pageid, title)
            elif confluence_answer.lower() == 'yes' or confluence_answer.lower() == 'y':
                auth = authenticate()
                write_data_to_confluence(auth, html, pageid, title)
            else:
                message = "Okay. Not writing to confluence."
                print(Fore.CYAN)
                banner(message)
                print(Fore.RESET)
    ### Interactive = 0 - cycling through all acounts.
    else:
        if options.verbose:
            show_details = options.verbose
        else:
            print(Fore.YELLOW)
            show_details = input("Show server details (y/n): ")
            print(Fore.RESET)
        aws_account = 'all'
        today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
        account_names, account_numbers = read_account_info(aws_env_list)
        for (aws_account, aws_account_number) in zip(account_names, account_numbers):
            try:
                aws_account = aws_account.split()[0]
            except Exception as e:
                message = f"An exception has occurred: {e}"
                banner(message)
            else:
                message = f"Working in AWS Account: {aws_account}."
                print(Fore.YELLOW)
                banner(message)
                print(Fore.RESET)
                # Set the regions
                regions = set_regions(aws_account)
                output_file = list_instances(aws_account,aws_account_number, interactive, regions, fieldnames, show_details)
                htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file,today, interactive, aws_account)
                mongo_export_to_file(interactive, aws_account)
        if reports_answer.lower() == 'yes' or reports_answer.lower() == 'y':
            message = " Send an Email "
            print(Fore.YELLOW)
            banner(message, "*")
            print(Fore.RESET)
            if options.send_email:
                email_answer = options.send_email
            else:
                print(Fore.YELLOW)
                email_answer = input("Send an email (y/n): ")

            if email_answer.lower() == 'y' or email_answer.lower() == 'yes':
                send_email(aws_accounts_answer,aws_account,aws_account_number, interactive)
            else:
                message = "Okay. Not sending an email."
                print(Fore.YELLOW)
                banner(message)

            with open(htmlfile, 'r') as htmlfile:
                html = htmlfile.read()

            print(Fore.CYAN)
            message = "* Write to Confluence *"
            banner(message, "*")
            if options.write_confluence:
                confluence_answer = options.write_confluence
            else:
                confluence_answer = input("Write the list to confluence (y/n): ")

            if options.user and options.password:
                user = options.user
                password = options.password
                auth = (user, password)
                try:
                    write_data_to_confluence(auth, html, pageid, title)
                except Exception as e:
                    print(f"An exception has occurred: {e}")
            else:
                if confluence_answer.lower() == 'yes' or confluence_answer.lower() == 'y':
                    if options.user:
                        username = options.user
                    else:
                        username = input("Enter a user name:")
                    auth = authenticate()
                    write_data_to_confluence(auth, html, pageid, title)
                else:
                    message = "Okay. Not writing to confluence."
                    banner(message)
                print(Fore.RESET)

    print(Fore.GREEN)
    if options.run_again:
        list_again = options.run_again
    else:
        list_again = input("List EC2 instances again (y/n): ")
    if list_again.lower() == 'y' or list_again.lower() == 'yes':
        main()
    else:
        exit_program()
    print(Fore.RESET)

if __name__ == "__main__":
    main()
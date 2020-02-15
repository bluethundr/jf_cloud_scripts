#!/usr/bin/env python3

# Import modules
import boto3
import botocore
import time
import objectpath
import pprint
import csv
import smtplib
import os
import argparse
import getpass
import sys
import json
import keyring
import requests
import itertools
import codecs
import pandas
from requests_kerberos import HTTPKerberosAuth
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from subprocess import check_output,CalledProcessError,PIPE
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


# Initialize the color ouput with colorama
init()

BASE_URL = "https://kiki.us.kworld.company.com/rest/api/content"
VIEW_URL = "https://kiki.us.kworld.company.com/pages/viewpage.action?pageId="

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    print('******************************************************')
    print('*             List AWS Instances                     *')
    print('******************************************************\n')

def endbanner():
    print(Fore.CYAN + "***********************************************")
    print("* List AWS Instance Operations Are Complete   *")
    print("***********************************************")

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def authenticate():
    auth = get_login()
    auth = str(auth).replace('(','').replace('\'','').replace(',',':').replace(')','').replace(' ','')
    kerberos_auth = HTTPKerberosAuth(mutual_authentication="DISABLED",principal=auth)
    auth = kerberos_auth
    return auth

def initialize(interactive, aws_account):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    aws_env_list = os.path.join('..', '..', 'output_files', 'aws_accounts_list', 'aws_kiki_page-' + today + '.csv')
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'csv')
    if interactive == 1:
        output_file = output_dir + 'aws-instance-master-list-' + aws_account + '-' + today +'.csv'
        output_file_name = 'aws-instance-master-list-' + aws_account + '-' + today +'.csv'
    else:
        output_file = output_dir + 'aws-instance-master-list-' + today +'.csv'
        output_file_name = 'aws-instance-master-list-' + today +'.csv'    
    return today, aws_env_list, output_file, output_file_name

def read_account_info(aws_env_list):
    account_names = []
    account_numbers = []
    account_urls = []
    engagements = []
    with open(aws_env_list) as csv_file:
    	csv_reader = csv.reader(csv_file, delimiter=',')
    	next(csv_reader)
    	for row in csv_reader:
            account_name = str(row[0])
            account_number = str(row[5])
            account_url = str(row[9])
            engagement_code = str(row[11])
            account_names.append(account_name)
            account_numbers.append(account_number)
            account_urls.append(account_url)
            engagements.append(engagement_code)
    return account_names, account_numbers, account_urls, engagements

def exit_program():
    endbanner()
    exit()
  
def list_instances(aws_account,aws_account_number, interactive):
    today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
    instance_list = ''
    session = ''
    ec2 = ''
    instance_count = 0
    fieldnames = [ 'AWS Account', 'Account Number', 'Name', 'Instance ID', 'VPC ID', 'Type', 'Platform', 'State', 'Key Pair Name', 'Private IP', 'Public IP', 'Private DNS', 'Volumes', 'Availability Zone', 'Launch Date']
    # Set the ec2 dictionary
    ec2info = {}
    # Write the file headers
    if interactive == 1:
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()
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
            ec2 = session.client("ec2")
        except Exception as e:
            pass
        if account_found == 'yes':
          message = "This is a gov account."
          banner(message)
    else:
        try:
            session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
            account_found = 'yes'
        except botocore.exceptions.ProfileNotFound as e:
            message = f"An exception has occurred: {e}"
            account_found = 'no'
            banner(message)
            time.sleep(5)
            pass
        try:
            ec2 = session.client("ec2")
        except Exception as e:
            pass
        if account_found == 'yes':
            message = "This is a commercial account."
            banner(message)

    # Loop through the instances
    try:
        instance_list = ec2.describe_instances()
    except Exception as e:
            pass
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
                type(private_ips_list)
                public_ips =  set(tree.execute('$..PublicIp'))
                if len(public_ips) == 0:
                    public_ips = None
                if public_ips:
                    public_ips_list = list(public_ips)
                    public_ips_list = str(public_ips_list).replace('[','').replace(']','').replace('\'','')
                else:
                    public_ips_list = None
                if 'KeyName' in instance:
                    key_name = instance['KeyName']
                else:
                    key_name = None
                name = None
                if 'Tags' in instance:
                    try:
                        tags = instance['Tags']
                        name = None
                        for tag in tags:
                            if tag["Key"] == "Name":
                                name = tag["Value"]
                    except ValueError:
                        print("Instance: %s has no tags" % instance_id)
                if 'VpcId' in instance:
                    vpc_id = instance['VpcId']
                else:
                    vpc_id = None
                if 'PrivateDnsName' in instance:
                    private_dns = instance['PrivateDnsName']
                else:
                    private_dns = None
                if 'Platform' in instance:
                    platform = instance['Platform']
                else:
                    platform = None
                ec2info[instance['InstanceId']] = {
                    'AWS Account': aws_account,
                    'Account Number': aws_account_number,
                    'Name': name,
                    'Instance ID': instance['InstanceId'],
                    'VPC ID': vpc_id,
                    'Type': instance['InstanceType'],
                    'Platform': platform,
                    'State': instance['State']['Name'],
                    'Key Pair Name': key_name,
                    'Private IP': private_ips_list,
                    'Public IP': public_ips_list,
                    'Private DNS': private_dns,
                    'Volumes': block_devices,
                    'Availability Zone': instance['Placement']['AvailabilityZone'],
                    'Launch Date': launch_time_friendly
                }
                with open(output_file,'a') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                    writer.writerow({'AWS Account': aws_account, "Account Number": aws_account_number,'Name': name, 'Instance ID': instance["InstanceId"], 'VPC ID': vpc_id, 'Type': instance["InstanceType"], 'Platform': platform, 'State': instance["State"]["Name"], 'Key Pair Name': key_name,  'Private IP': private_ips_list, 'Public IP': public_ips_list, 'Private DNS': private_dns, 'Volumes': block_devices, 'Availability Zone': instance['Placement']['AvailabilityZone'], 'Launch Date': launch_time_friendly})
    except Exception as e:
        pass
    for instance_id, instance in ec2info.items():
        if account_found == 'yes':
            print(Fore.RESET + "-------------------------------------")
        for key in [
            'AWS Account',
            'Account Number',
            'Name',
            'Instance ID',
            'VPC ID',
            'Type',
            'Platform',
            'Key Pair Name',
            'State',
            'Private IP',
            'Public IP',
            'Private DNS',
            'Volumes',
            'Availability Zone',
            'Launch Date'
        ]:
            print(Fore.GREEN + "{0}: {1}".format(key, instance.get(key)))          
        time.sleep(2)
    if account_found == 'yes':
        print(Fore.RESET + "-------------------------------------")
    with open(output_file,'a') as csv_file:
        csv_file.close()
    if account_found == 'yes':
        if instance_count == 0:
            message = f"There are no EC2 instances in AWS Account: {aws_account}"
            banner(message)
        elif instance_count == 1:
            message = f"There is: {instance_count} EC2 instance in AWS Account: {aws_account}"
            banner(message)
        else:
            message = f"There are: {instance_count} EC2 instances in AWS Account: {aws_account}"
            banner(message)
    return output_file


def convert_csv_to_html_table(output_file, today, interactive, aws_account):
    output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'html')
    if interactive == 1:
        htmlfile = os.path.join(output_dir, 'aws-instance-master-list-' + aws_account + '-' + today +'.html')
        htmlfile_name = 'aws-instance-master-list-' + aws_account + '-' + today +'.html'
    else:
        htmlfile = os.path.join(output_dir, 'aws-instance-master-list-' + today +'.html')
        htmlfile_name = 'aws-instance-master-list-' + today +'.html'
    remove_htmlfile = htmlfile
    count = 0
    html = ''
    with open(output_file,'r') as CSVFILE:
        reader = csv.reader(CSVFILE)
        with open(output_file,'r') as CSVFILE:
            reader = csv.reader(CSVFILE)
            html += "<table><tbody>"
            for row in reader:
                html += "<tr>"
                # Process the headers
                if count == 0:
                    for column in row:
                        html += "<th>%s</th>" % column
                else:
                    # Process the data
                    for column in row:
                        html += "<td>%s</td>" % column
                html += "</tr>"
                count += 1
            html += "</tbody></table>"
    with open(htmlfile,'w+') as HTMLFILE:
        HTMLFILE.write(html)
    return htmlfile, htmlfile_name, remove_htmlfile

def pprint(data):
    '''
    Pretty prints json data.
    '''
    json.dumps(
    data,
    sort_keys = True,
    indent = 4,
    separators = (', ', ' : '))

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
    r = requests.put(
        url,
        data = data,
        auth = auth,
        headers = { 'Content-Type' : 'application/json' }
    )
    r.raise_for_status()
    print("Wrote '%s' version %d" % (info['title'], ver))
    print("URL: %s%d" % (VIEW_URL, pageid))
 
def get_login(username = None):
    if username is None:
        username = getpass.getuser()
    passwd = None
    if passwd is None:
        passwd = getpass.getpass()
        keyring.set_password('confluence_script', username, passwd)
    return (username, passwd)

def send_email(aws_accounts_question,aws_account,aws_account_number, interactive): 
    # Get the variables from intitialize
    today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
    ## Get the address to send to
    print(Fore.YELLOW)
    first_name = str(input("Enter the recipient's first name: "))
    to_addr = input("Enter the recipient's email address: ")
    from_addr = 'cloudops@noreply.company.com'
    subject = "company AWS Instance Master List " + today
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
    server = smtplib.SMTP('smtpout.us.kworld.company.com', 25)
    try:
        server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
        print("Email was sent to: %s" % to_addr)
    except Exception as error:
        print("Exception:", error)
        print("Email was not sent.")


def remove_file(output_file, output_file_name):
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

def main():
    # Display the welcome banner
    welcomebanner()
    ## One or many accounts
    print(Fore.YELLOW)
    aws_accounts_question = input("List instances in one or all accounts: ")
    if aws_accounts_question.lower() == "one":
        interactive = 1
    else:
        interactive = 0
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--user",
        help = "Specify the username to log into Confluence")
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

    options = parser.parse_args()
    pageid = 138317098
    title = 'AWS EC2 Instance List'
    aws_account_number = ''
    if interactive == 1:
        ## Select the account
        print(Fore.YELLOW)
        aws_account = input("Enter the name of the AWS account you'll be working in: ")
        # Grab variables from initialize
        today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
        account_names, account_numbers, account_urls, engagements = read_account_info(aws_env_list)
        message = f"Okay. Working in AWS account: {aws_account}"
        banner(message)
        for (my_aws_account, my_aws_account_number, my_account_url) in zip(account_names, account_numbers,account_urls):
            if my_aws_account == aws_account:
                aws_account_number = my_aws_account_number
        output_file = list_instances(aws_account,aws_account_number, interactive)
        htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file, today, interactive, aws_account)
        email_answer = input("Send an email (y/n): ")
        if email_answer.lower() == 'y' or email_answer == 'yes':
            send_email(aws_accounts_question,aws_account,aws_account_number, interactive)
        else:
            message = "Okay. Not sending an email."
            banner(message)
        with open(htmlfile, 'r', encoding='utf-8') as htmlfile:
            html = htmlfile.read()
        confluence_answer = input("Write the list to confluence (y/n): ")
        if confluence_answer.lower() == 'yes' or confluence_answer.lower() == 'y':
            auth = authenticate()
            write_data_to_confluence(auth, html, pageid, title)
        else:
            message = "Okay. Not writing to confluence."
            banner(message)
    else:
        aws_account = 'all'
        today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
        fieldnames = [ 'AWS Account', 'Account Number', 'Name', 'Instance ID', 'VPC ID', 'Type', 'Platform', 'State', 'Key Pair Name', 'Private IP', 'Public IP', 'Private DNS', 'Volumes', 'Availability Zone', 'Launch Date']
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()
        account_names, account_numbers, account_urls, engagements = read_account_info(aws_env_list)
        for (aws_account, aws_account_number, account_url) in zip(account_names, account_numbers,account_urls):
            print(f"AWS account before split: {aws_account}")
            try:
                aws_account = aws_account.split()[0]
                print(f"AWS account after split: {aws_account}")
            except Exception as e:
                message = f"An exception has occurred: {e}"
                banner(message)
            else:
                print("\n")
                message = f"Working in AWS Account: {aws_account}"
                banner(message)
                output_file = list_instances(aws_account,aws_account_number, interactive)
                htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file,today, interactive, aws_account)
        email_answer = input("Send an email (y/n): ")
        if email_answer.lower() == 'y' or email_answer.lower() == 'yes':
                send_email(aws_accounts_question,aws_account,aws_account_number, interactive)
        else:
            print("Okay. Not sending an email.")
        with open(htmlfile, 'r', encoding='utf-8') as htmlfile:
            html = htmlfile.read()
        confluence_answer = input("Write the list to confluence (y/n): ")
        if confluence_answer.lower() == 'yes' or confluence_answer.lower() == 'y':
            auth = get_login()
            auth = str(auth).replace('(','').replace('\'','').replace(',',':').replace(')','').replace(' ','')
            kerberos_auth = HTTPKerberosAuth(mutual_authentication="DISABLED",principal=auth)
            auth = kerberos_auth
            write_data_to_confluence(auth, html, pageid, title)
        else:
            message = "Okay. Not writing to confluence."
            banner(message)
    remove_file(output_file, output_file_name)
    remove_file(remove_htmlfile, htmlfile_name)
    list_again = input("List EC2 instances again (y/n): ")
    if list_again.lower() == 'y' or list_again.lower() == 'yes':
        main()
    else:
        time.sleep(5)
        exit_program()
     
if __name__ == "__main__":
    main()
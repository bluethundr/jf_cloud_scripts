#!/usr/bin/env python3

# Import modules
import boto3
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
VIEW_URL = "https://kiki.us.kworld.company.com/pages/viewinfo.action?pageId="

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

def initialize(interactive, aws_account):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set source files
    aws_env_list = os.path.join('..', 'source_files', 'aws_environments', 'aws_environments_all_with_LH.txt')
    if interactive == 1:
        # Set the output file
        output_dir = os.path.join('..', 'output_files', 'aws_public_ips_list', 'csv')
        print(output_dir)
        time.sleep(10)
        output_file = os.path.join('..', output_dir, 'aws-public-ips-list-' + aws_account + '.csv')
        print(f"Output File: {output_file}")
        time.sleep(10)
        #output_file = output_dir + 'aws-public-ips-list-' + aws_account + '-' + today +'.csv'
        output_file_name = os.path.join('aws-public-ips-list' + aws_account + '.csv')
        #output_file_name = 'aws-public-ips-list-' + aws_account + '-' + today +'.csv'
    else:
        # Set the output file
        output_dir = os.path.join('..', 'output_files', 'aws_public_ips_list', 'csv')
        output_file = os.path.join('output_dir', 'aws-public-ips-list' + today + '.csv')
        #output_file = output_dir + 'aws-public-ips-list-' + today +'.csv'
        output_file_name = os.path.join('aws-public-ips-list' + today + '.csv')
        #output_file_name = 'aws-public-ips-list-' + today +'.csv'    
    return today, aws_env_list, output_file, output_file_name

def choose_action():
    print(Fore.GREEN)
    print("*********************************************")
    print("*         Choose an Action                  *")
    print("*********************************************")
    print(Fore.YELLOW)
    print("These are the actions possible in AWS List Instances: ")
    print("1. List AWS Instances")
    print("2. Read the price list")
    print("3. Exit Program")

    choice=input("Enter an action: ")
    return choice

def exit_program():
    endbanner()
    exit()

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def aws_accounts_to_account_numbers(aws_account):
    switcher = {
        'company-lab': '486469900423',
        'company-bill': '188087670762',
        'company-stage': '051170381115',
        'company-dlab': '287093337099',
        'company-nonprod': '832839043616',
        'company-prod': '560044853747',
        'company-ksr-a': '764210188035',
        'company-ksr-b': '991163571593',
        'company-dsg-logging-admin': '962923862227',
        'company-dsg-logging-gov': '900653850120',
        'company-dsg-security-admin': '219577256432',
        'company-dsg-security-gov': '902541738353',
        'company-dsg-security-lab': '059345717693',
        'company-master': '419585237664',
        'company-transit-hub1': '303779310401',
        'company-transit-hub3': '154101686306',
        'company-transit-hub4': '664008221807',
        'company-security': '193256904289',
        'company-shared-services': '300944922012',
        'company-logging': '826254699822',
        'company-spoke-acct1': '103440952267',
        'company-spoke-acct2': '288378600023',
        'company-spoke-acct3': '872950281716',
        'company-spoke-acct4': '167031866369',
        'company-spoke-acct6': '067621579922',
        'company-spoke-acct7': '580036671366',
        'company-spoke-acct9': '806534465904',
        'company-spoke-acct10': '421544879922',
        'company-spoke-acct11': '795959353786',
        'company-spoke-acct12': '353390891816',
        'company-lighthouse': '056680040343',
        'company-ab-nonprod': '151528745488',
        'company-ab-prod': '155775729998',
        'company-govcloud-ab-admin-nonprod': '675966588449',
        'company-govcloud-ab-nonprod': '654077510425',
        'company-govcloud-ab-admin-prod': '863351155240',
        'company-govcloud-ab-prod': '654360223973',
        'company-govcloud-ab-mc-admin-nonprod': '818951881696',
        'company-govcloud-ab-mc-nonprod': '026715570499',
        'company-govcloud-ab-mc-admin-prod': '609094545271',
        'company-govcloud-ab-mc-prod': '028074947530',
        'company-govcloud-ab-core-qa-admin': '941596672588',
        'company-govcloud-ab-core-qa': '003639698863',
        'company-govcloud-ab-core-stage-admin': '445128552952',
        'company-govcloud-ab-core-stage': '009247348608',
        'company-govcloud-ab-mc-qa-admin': '201370688988',
        'company-govcloud-ab-mc-qa': '005350604950',
        'company-govcloud-ab-mc-stage-admin': '635681562415',
        'company-govcloud-ab-mc-stage': '007107066053',
        'company-govcloud-admin-ab-dsg-logmon-nonprod': '913530316654',
        'company-govcloud-ab-dsg-logmon-nonprod': '042821237378',
        'company-govcloud-admin-ab-dsg-logmon-prod': '849740718434',
        'company-govcloud-ab-dsg-logmon-prod': '042489471961',
        'company-govcloud-admin-ab-dsg-logmon-nonprod2': '142490000192',
        'company-govcloud-ab-dsg-logmon-nonprod2': '155207289643',
        'company-govcloud-admin-ab-dsg-logmon-prod2': '260416396087',
        'company-govcloud-ab-dsg-logmon-prod2': '155216231062',
    }
    return switcher.get(aws_account, "nothing")

def get_public_ips(aws_account,aws_account_number, interactive):
    today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
    # Set the account
    session = boto3.Session(profile_name=aws_account)
    ec2_client = session.client("ec2")
    fieldnames = [ 'AWS Account', 'Account Number', 'Region', 'Instance ID', 'Public IP' ]
    count_public_ip_entries = 0
    public_ip = ''
    # Set the ec2 dictionary
    ec2info = {}
    # Write the file headers
    if interactive == 1:
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()
    if 'gov' in aws_account and not 'admin' in aws_account:
        print("This is a gov account.")
        print(Fore.RESET + "-----------------------------------------------")
        session = boto3.Session(profile_name=aws_account,region_name='us-gov-west-1')
        my_region = session.region_name
    else:
        print("This is a commercial account.")
        print(Fore.RESET + "-----------------------------------------------")
        session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
        my_region = session.region_name

    ec2_client = session.client("ec2")
    # Loop through the instances
    instance_list = ec2_client.describe_instances()
    for reservation in instance_list["Reservations"]:
        for instance in reservation.get("Instances", []):
            instance_id = instance['InstanceId']
            tree = objectpath.Tree(instance)
            public_ips =  set(tree.execute('$..PublicIp'))
            if len(public_ips) == 0:
                public_ips = None
            if public_ips:
                public_ips_list = list(public_ips)
                public_ips_list = str(public_ips_list).replace('[','').replace(']','').replace('\'','')
            else:
                public_ips_list = None
            if public_ips_list is not None:
                ec2info[instance['InstanceId']] = {
                    'AWS Account': aws_account,
                    'Account Number': aws_account_number,
                    'Region': my_region,
                    'Instance ID': instance_id,
                    'Public IP': public_ips_list,
                }
                count_public_ip_entries = count_public_ip_entries + 1
                print(Fore.CYAN + f"Public IP: {public_ips_list}")
                for pubic_ip in public_ips_list:
                    print(f"Public IP: {public_ip}")
                with open(output_file,'a') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                    writer.writerow({'AWS Account': aws_account, 'Account Number': aws_account_number, 'Region': my_region, 'Instance ID': instance_id, 'Public IP': public_ips_list})

    with open(output_file,'a') as csv_file:
        csv_file.close()
    if count_public_ip_entries == 0:
        print("No public IPs in this account.")
    return output_file


def convert_csv_to_html_table(output_file, today, interactive, aws_account):
    output_dir = os.path.join('..', 'output_files', 'aws_public_ips_list', 'html')
    if interactive == 1:
        htmlfile = output_dir + 'aws-public-ips-list-' + aws_account + '-' + today +'.html'
        htmlfile_name = 'aws-public-ips-list-' + aws_account + '-' + today +'.html'
    else:
        htmlfile = output_dir + 'aws-public-ips-list-' + today +'.html'
        htmlfile_name = 'aws-public-ips-list-' + today +'.html'

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
    subject = "company AWS Public IP List " + today
    if aws_accounts_question == 'one':
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of Public IPs in all AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>Cloud Ops</font>"
    else:
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of Public IPs in all company AWS accounts.<br><br>Regards,<br>Cloud Ops</font>"    
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
    print("Removing the output file:", output_file_name)
    try:
        os.remove(output_file)
    except Exception as error:
        print("Error: ", error)
        remove_stat = 1
    else:
        remove_stat = 0
    if remove_stat == 0:
        print("File removed!")
    else:
        print("File not removed.")

def main():
    # Display the welcome banner
    welcomebanner()
    ## One or many accounts
    print(Fore.YELLOW)
    aws_accounts_question = input("List public IPs in one or all accounts: ")
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
    pageid = 147849365
    title = 'AWS Public IP List - Commercial and Gov'
    if interactive == 1:
        ## Select the account
        print(Fore.YELLOW)
        aws_account = input("Enter the name of the AWS account you'll be working in: ")
        aws_account_number = aws_accounts_to_account_numbers(aws_account)
        # Grab variables from initialize
        today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
        print(Fore.RESET + "-----------------------------------------------")
        print(Fore.YELLOW + "Okay. Working in AWS account: ", aws_account)
        print(Fore.RESET + "-----------------------------------------------")
        output_file = get_public_ips(aws_account,aws_account_number, interactive)
        print(Fore.RESET + "-----------------------------------------------")
        htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file, today, interactive, aws_account)
        print(Fore.RESET)
        email_answer = input("Send an email (y/n): ")
        if email_answer.lower() == 'y' or email_answer == 'yes':
            send_email(aws_accounts_question,aws_account,aws_account_number, interactive)
        else:
            print("Okay. Not sending an email.")
        with open(htmlfile, 'r', encoding='utf-8') as htmlfile:
            html = htmlfile.read()
        confluence_answer = input("Write the list to confluence (y/n): ")
        if confluence_answer.lower() == 'yes' or confluence_answer.lower() == 'y':
            auth = get_login()
            auth = str(auth).replace('(','').replace('\'','').replace(',',':').replace(')','').replace(' ','')
            time.sleep(5)
            kerberos_auth = HTTPKerberosAuth(mutual_authentication="DISABLED",principal=auth)
            auth = kerberos_auth
            write_data_to_confluence(auth, html, pageid, title)
        else:
            print("Okay. Not writing to confluence.")
    else:
        aws_account = 'all'
        today, aws_env_list, output_file, output_file_name = initialize(interactive, aws_account)
        fieldnames = [ 'AWS Account', 'Account Number', 'Region', 'Instance ID', 'Public IP' ]
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()           
        print(Fore.RESET + "-----------------------------------------")
        with open(aws_env_list, 'r') as aws_envs:
                for aws_account in aws_envs.readlines():
                    aws_account = aws_account.strip()
                    aws_account_number = aws_accounts_to_account_numbers(aws_account)
                    print("\n")
                    print("Working in AWS Account: ", aws_account)
                    print(Fore.RESET + "-----------------------------------------------")
                    output_file = get_public_ips(aws_account,aws_account_number, interactive)
                    htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file,today, interactive, aws_account)
                    print(Fore.RESET + "-----------------------------------------------")
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
    endbanner()

if __name__ == "__main__":
    main()
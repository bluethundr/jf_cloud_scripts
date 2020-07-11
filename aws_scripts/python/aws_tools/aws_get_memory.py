#!/usr/bin/env python3

# Import modules
import boto3
import botocore
import time
import objectpath
import csv
import os
import argparse
import sys
import json
import codecs
import pandas as pd
import paramiko
import psutil as pu
import fileinput
import platform
import smtplib
from os import listdir
from os.path import isfile, join
from botocore.exceptions import ValidationError
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from subprocess import check_output,CalledProcessError,PIPE
from shutil import copyfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Initialize the color ouput with colorama
init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             Get AWS Memory Stats                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* Get AWS Memory Stats Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def initialize(aws_account):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set the fieldnames for the CSV
    fieldnames = [ 'Name', 'PrivateIP']

    # Set private key
    key_file = "/home/tdun0002/.ssh/id_rsa"

    # Set output files
    text_path = "/home/tdun0002/stash/cloud_scripts/aws_scripts/output_files/memory_stats/text/"
    csv_path = "/home/tdun0002/stash/cloud_scripts/aws_scripts/output_files/memory_stats/csv/"

    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')

    # Set the hosts list directory
    hosts_dir = os.path.join('..', '..', 'source_files', 'aws_hosts_list')

    # Set the output files
    output_dir = os.path.join('..', '..', 'output_files', 'aws_hostname_list', 'csv', '')
    output_file = os.path.join(output_dir, 'aws-hostname-list-' + today + '.csv')
    output_file_name = 'aws-hostname-list-' + today +'.csv'
    memory_stats_textdir = os.path.join('..', '..', 'output_files', 'memory_stats', 'text', '')
    memory_stats_csvdir = os.path.join('..', '..', 'output_files', 'memory_stats', 'csv', '')
    return today, aws_env_list, output_dir, output_file, output_file_name, hosts_dir, memory_stats_textdir, memory_stats_csvdir, key_file, fieldnames, csv_path, text_path

def create_csvoutputdir(output_dir):
    if not os.path.exists(output_dir):
         os.makedirs(output_dir)

def create_hosts_sourcedir(hosts_dir):
    if not os.path.exists(hosts_dir):
         os.makedirs(hosts_dir)

def create_memory_stats_textdir(memory_stats_textdir):
    if not os.path.exists(memory_stats_textdir):
         os.makedirs(memory_stats_textdir)

def create_memory_stats_csvdir(memory_stats_csvdir):
    if not os.path.exists(memory_stats_csvdir):
         os.makedirs(memory_stats_csvdir)

def copy_outputfile(output_file, aws_account):
    src = output_file
    dst = os.path.join('..', '..', 'source_files', 'aws_hosts_list', 'aws_hosts_list.csv')
    copyfile(src, dst)
    hosts_list = dst
    return hosts_list

def get_memory(hosts_list, aws_account,key_file, csv_path, text_path):
    print(Fore.GREEN)
    fields = ['Name']
    df = pd.read_csv(hosts_list, skipinitialspace=True, usecols=fields)
    list_names = df['Name'].tolist()
    message = f"Connecting to hosts in AWS Account: {aws_account}"
    banner(message)
    k = paramiko.RSAKey.from_private_key_file(key_file)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    local_path = text_path # Read the current directory
    remote_path = "/home/tdun0002/"
    for server_name in list_names:
        print(f"Connecting to: {server_name}")
        try:
            file_name = server_name + "-memory.txt"
            local_name = os.path.join(local_path, file_name)
            remote_name = os.path.join(remote_path, file_name)
            c.connect( hostname = server_name, username = "tdun0002", pkey = k )
            print("connected")
            cmd1 = "grep MemTotal /proc/meminfo  | sed 's/MemTotal://g;s/kB//g;s/^[ \t]*//g;s/[\t]*$//g' > " + file_name
            cmd2 = "rm -fv " + remote_name
            cmd3 = "ls -ltrh"
            print(f"Copying: {remote_name} to: {local_name}")
            stdin, stdout, stderr = c.exec_command(cmd1)
            ftp_client=c.open_sftp()
            ftp_client.get(remote_name,local_name) 
            ftp_client.close()
            stdin, stdout, stderr = c.exec_command(cmd2)
            outlines=stdout.readlines()
            resp=''.join(outlines)
            print(f"{resp}") # Output
            stdin, stdout, stderr = c.exec_command(cmd3)
            outlines=stdout.readlines()
            resp=''.join(outlines)
            print(resp) # Output
            c.close()
        except Exception as e:
            print(Fore.YELLOW + f"ERROR: {e} on {server_name}" + Fore.GREEN + '\n')

def convert_to_csv(csv_path,text_path,hosts_list, aws_account, aws_account_number, today):
    csv_output = csv_path + 'sncr_memory_report-' + aws_account + '-' + today + '.csv'
    filelist = os.listdir(text_path)
    pd.options.display.max_rows

    # Read the servers into the DF
    fields = ["Name", "PrivateIP"]
    hosts_df = pd.read_csv(hosts_list, skipinitialspace=True, usecols=fields)

    # Create the memory dataframe
    column_names = ["Memory"]
    memory_df = pd.DataFrame(columns=column_names)
    memory_list = []
    print(f"Reading text files into the Memory DF")
    for filename in filelist:
        print(f"Adding filename: {filename}")
        filename = text_path + filename
        temp_df = pd.read_csv(filename, delim_whitespace=True, names=column_names)
        memory_df = memory_df.append(temp_df)
    print("\n")

    # Set the memory type for the memory DF
    memory_df.Memory = memory_df.Memory.astype("int32")

    # Create the final frame
    final_df = pd.concat([hosts_df, memory_df.reset_index(drop=True)], axis=1)

    try:
        final_df.to_csv(csv_output, index=False)
    except Exception as e:
        print(f"An error has occurred: {e}")
    return csv_output


def send_email(aws_account,aws_account_number, memory_report, today):
    options = arguments()
    to_addr = ''
    # Get the variables from intitialize
    today, aws_env_list, output_dir, output_file, output_file_name, hosts_dir, memory_stats_textdir, memory_stats_csvdir, key_file, fieldnames, csv_path, text_path = initialize(aws_account)
    print(Fore.YELLOW)
    message = "Sending the email"
    banner(message)
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

    from_addr = 'cloudops@noreply.sncr.com'
    subject = "SNCR AWS Instance Memory Report " + today
    content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find the AWS Instance Memory Report for AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>The SD Team</font>"
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = MIMEText(content, 'html')
    msg.attach(body)

    with open(memory_report, 'r') as f:
        part = MIMEApplication(f.read(), Name=basename(memory_report))
        part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(memory_report))
        msg.attach(part) 
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        gmail_user = 'sncr.noreply@gmail.com'
        gmail_password = 'ehhloWorld12345'
        server.login(gmail_user, gmail_password)
        server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
        message = f"Email was sent to:{to_addr}"
        banner(message)
    except Exception as error:
        message = f"Exception: {error}\nEmail was not sent."
        banner(message)
    print(Fore.RESET)


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


def list_instances(aws_account,aws_account_number, fieldnames):
    today, aws_env_list, output_dir, output_file, output_file_name, hosts_dir, memory_stats_textdir, memory_stats_csvdir, key_file, fieldnames, csv_path, text_path = initialize(aws_account)
    options = arguments()
    instance_list = ''
    session = ''
    ec2 = ''
    account_found = ''
    instance_count = 0
    account_type_message = ''
    profile_missing_message = ''
    region = ''
    # Set the ec2 dictionary
    ec2info = {}
    # Write the file headers

    with open(output_file, mode='w+') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
        writer.writeheader()
    print(Fore.CYAN)
    account_found = 'yes'
    try:
         session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
    except Exception as e:
        print(f"An exception has occurred: {e}")
    try:
        ec2 = session.client("ec2")
    except Exception as e:
        print(f"An exception has occurred: {e}")
    print(Fore.GREEN)
    # Loop through the instances
    try:
        instance_list = ec2.describe_instances()
    except Exception as e:
        print(f"An exception has occurred: {e}")
    try:
        for reservation in instance_list["Reservations"]:
            for instance in reservation.get("Instances", []):
                instance_count = instance_count + 1
                tree = objectpath.Tree(instance)
                private_ips =  set(tree.execute('$..PrivateIpAddress'))
                if private_ips:
                    private_ips_list = list(private_ips)
                    private_ips_list = str(private_ips_list).replace('[','').replace(']','').replace('\'','')
                else:
                    private_ips_list = None
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
                        # print("Instance: %s has no tags" % instance_id)
                        pass
                ec2info[instance['InstanceId']] = {
                    'Name': name,
                    'PrivateIP': private_ips_list,
                }
                with open(output_file,'a') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
                    writer.writerow({'Name': name, 'PrivateIP': private_ips_list})
                ec2_info_items = ec2info.items
                reservation = {}
                instance = {}
                ec2_info_items = {}
                ec2info = {}
                with open(output_file,'a') as csv_file:
                    csv_file.close()
    except Exception as e:
        print(f"An exception has occurred: {e}")
    if profile_missing_message == '*':
        banner(profile_missing_message)
    print(Fore.GREEN)
    report_instance_stats(instance_count, aws_account, account_found)
    print(Fore.RESET + '\n')
    return output_file


def arguments():
    parser = argparse.ArgumentParser(description='This is a program that lists the servers in EC2')

    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the AWS account you'll be working in.")

    parser.add_argument(
    "-c",
    "--all_accounts",
    type = str,
    default = None,
    nargs = '?',
    help = "Process one or all accounts.")

    parser.add_argument(
    "-i",
    "--run_again",
    type = str,
    help = "Run again.")

    parser.add_argument(
    "-v",
    "--verbose",
    type = str,
    help = "Write the EC2 instances to the screen.")

    parser.add_argument(
    "-f",
    "--first_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the person to send the email to.")

    parser.add_argument(
    "-e",
    "--email_recipient",
    type = str,
    default = None,
    nargs = '?',
    help = "Email address of the person to send to.")

    options = parser.parse_args()
    return options

def main():
    options = arguments()
    # Display the welcome banner
    welcomebanner()
    aws_account = input("Enter the AWS Account to use: ")
    aws_account_number = ''

    # Grab variables from initialize
    today, aws_env_list, output_dir, output_file, output_file_name, hosts_dir, memory_stats_textdir, memory_stats_csvdir, key_file, fieldnames, csv_path, text_path = initialize(aws_account)

    # Create CSV Output Directory
    create_csvoutputdir(output_dir)

    # Create Hosts Source Directory
    create_hosts_sourcedir(hosts_dir)

    # Create Memory Stats Text Directory
    create_memory_stats_textdir(memory_stats_textdir)

    # Create Memory Stats CSV Directory
    create_memory_stats_csvdir(memory_stats_csvdir)

    # Get the list of the accounts
    account_names, account_numbers = read_account_info(aws_env_list)
    print(Fore.GREEN)
    message = f"Working in AWS account: {aws_account}"
    banner(message)
    # Find the account's account number
    for (my_aws_account, my_aws_account_number) in zip(account_names, account_numbers):
        if my_aws_account == aws_account:
            aws_account_number = my_aws_account_number
        if not aws_account_number:
            aws_account_number = 'Null'

    output_file = list_instances(aws_account,aws_account_number, fieldnames)
    hosts_list = copy_outputfile(output_file, aws_account)
    get_memory(hosts_list, aws_account, key_file, csv_path, text_path)
    memory_report = convert_to_csv(csv_path,text_path,hosts_list, aws_account, aws_account_number, today)
    send_email(aws_account,aws_account_number, memory_report, today)

    print(Fore.GREEN)
    if options.run_again:
        list_again = options.run_again
    else:
        list_again = input("Get Memory Report Again (y/n): ")
    if list_again.lower() == 'y' or list_again.lower() == 'yes':
        main()
    else:
        exit_program()
    print(Fore.RESET)

if __name__ == "__main__":
    main()

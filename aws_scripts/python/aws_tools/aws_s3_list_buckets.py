import boto3
import objectpath
import os
import csv
import smtplib
import argparse
import getpass
import keyring
import time
import requests
import json
import time
from web_scraper import web_scraper
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from subprocess import check_output,CalledProcessError,PIPE
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

init()
BASE_URL = "https://confluence.company.net:8443/rest/api/content"
VIEW_URL = "https://confluence.company.net:8443/pages/viewpage.action?pageId="

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = '*             List AWS S3 Buckets                    *'
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* List AWS S3 Bucket Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def authenticate():
    auth = get_login()
    return auth

def initialize(interactive, aws_account):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")

    # Set the field names in the output
    fieldnames = [ 'AWS Account', 'Account Number', 'Bucket Name' ]
    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_confluence_page.csv')
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_s3_buckets_list', 'csv')
    if interactive == 1:
        output_file = output_dir + 'aws-s3-buckets-list-' + aws_account + '-' + today +'.csv'
        output_file_name = 'aws-s3-buckets-list-' + aws_account + '-' + today +'.csv'  
    else:
        output_file = output_dir + 'aws-s3-buckets-list-' + today +'.csv'
        output_file_name = 'aws-s3-buckets-list-' + today +'.csv'    
    return today, aws_env_list, output_file, output_file_name, fieldnames

def choose_action():
    print(Fore.GREEN)
    print("*********************************************")
    print("*         Choose an Action                  *")
    print("*********************************************")
    print(Fore.YELLOW)
    print("These are the actions possible in AWS List S3 Buckets: ")
    print("1. List AWS S3 Buckets")
    print("2. Find a bucket in accounts")
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

def remove_file(output_file, output_file_name):
    print(Fore.GREEN)
    print("Removing the output file:", output_file_name)
    try:
        os.remove(output_file)
    except Exception as error:
        print("Error: ", error)
        remove_stat = 1
    else:
        remove_stat = 0
    if remove_stat == 0:
        print("File removed!", Fore.RESET)
    else:
        print("File not removed.", Fore.RESET)

def aws_accounts_to_account_numbers(aws_account):
    switcher = {
        'ccmi-mx-prod': '889220455594',
        'ccmi-mx-stg': '697814175949',
        'ccmi-mx-c2c': '400723089300',
        'ccmi-att-lab': '253251734662',
        'ccmi-pac-lab': '742215071658',
        'ccmi-sprint-lab': '771501756991',
        'ccmi-tmo-lab': '691848290388',
        'core-mx-lab': '311600198949',
        'france-cloud-lab':  '696722235731',
        'mmp-kube-dev': '424546976472',
        'ncs-maap-lab2': '915850090302',
        'ncs-maap-lab': '630333306496',
        'scv-sandbox': '062541756289',
        'tmo-mx-dev': '794081766429',
        'tmo-mx-prod': '629890620112',
        'tmo-mx-stg': '004103171578',
    }
    return switcher.get(aws_account, "nothing")

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
        print(f"An error has occurred: {e}")

    try:     
        r.raise_for_status()
    except Exception as e:
        print(f"An error has occurred: {e}")
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

def convert_csv_to_html_table(output_file, today, interactive, aws_account):
    output_dir = os.path.join('..', '..', 'output_files', 'aws_s3_buckets_list', 'html')
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

def send_email(aws_accounts_question,aws_account,aws_account_number, interactive):
    # Get the variables from intitialize
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
    ## Get the address to send to
    print(Fore.YELLOW)
    first_name = str(input("Enter the recipient's first name: "))
    to_addr = input("Enter the recipient's email address: ")
    from_addr = 'cloudops@noreply.company.com'
    subject = "company AWS S3 Bucket List " + today
    if aws_accounts_question == 'one':
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of S3 Buckets in AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>Cloud Ops</font>"
    else:
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find a list of S3 Buckets in all company AWS accounts.<br><br>Regards,<br>Cloud Ops</font>"    
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
        message = f"Email was sent to: {to_addr}"
        banner(message)
    except Exception as error:
        message = "Exception: {error}\nEmail was not sent."
        banner(message)


def list_s3_buckets(aws_account,aws_account_number, interactive, show_details, search_bucket = None):
    today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
    # Set the account
    session = boto3.Session(profile_name=aws_account)
    s3_client = session.client('s3')
    count_bucket_entries = 0
    if interactive == 1:
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()
    print(Fore.GREEN)
    if 'gov' in aws_account and not 'admin' in aws_account:
        message = "This is a gov account."
        banner(message)
        session = boto3.Session(profile_name=aws_account,region_name='us-gov-west-1')
    else:
        message = "This is a commercial account."
        banner(message)
        session = boto3.Session(profile_name=aws_account,region_name='us-east-1')
    print(Fore.RESET)

    # Loop through the S3 Buckets
    print(Fore.GREEN)
    s3_response = s3_client.list_buckets()
    for bucket in s3_response['Buckets']:
        bucket_name = bucket['Name']
        count_bucket_entries = count_bucket_entries + 1
        if show_details.lower() == 'yes' or show_details.lower() == 'y':
             print(f"Bucket Name: {bucket_name}")
        if search_bucket == bucket_name.strip():
            print(f"***Bucket: {search_bucket} was found in AWS Account: {aws_account} ({aws_account_number})***")
            time.sleep(30)
        with open(output_file,'a') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writerow({'AWS Account': aws_account, 'Account Number': aws_account_number, 'Bucket Name': bucket_name})

    with open(output_file,'a') as csv_file:
        csv_file.close()
    if count_bucket_entries == 0:
        message = "No S3 Buckets in this account."
        banner(message)
    print(Fore.RESET)
    return output_file

def arguments():
    parser = argparse.ArgumentParser(description='This is a program that lists buckets in S3')

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
    "-a",
    "--accountlist",
    type = str,
    default = None,
    nargs = '?',
    help = "Update the account list")

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
    help = "Process all accounts")

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
    help = "First name of the person receving the email")

    parser.add_argument(
    "-i",
    "--run_again",
    type = str,
    help = "First name of the person receving the email")

    parser.add_argument(
    "-s",
    "--search",
    type = str,
    help = "Search for an S3 bucket")

    parser.add_argument(
    "-m",
    "--bucket_name",
    type = str,
    help = "Bucket Name")

    parser.add_argument(
    "-v",
    "--verbose",
    type = str,
    help = "Write the S3 Buckets to the screen")    

    options = parser.parse_args()
    return options

def main():
    # Get the arguments and reference them as options
    options = arguments()
    # Display the welcome banner
    welcomebanner()
    find_bucket = ''
    html = ''

    if options.html:
        html = options.html

    if options.accountlist:
        update_account_list = options.accountlist
    else:
        ## One or many accounts
        print(Fore.YELLOW)
        update_account_list = input("Update the account list (y/n): ")
        print(Fore.RESET)

    if update_account_list.lower() == 'y' or update_account_list.lower() == 'yes':
        web_scraper(options)

    if options.all_accounts:
            aws_accounts_question = options.all_accounts
    else:
        ## Select one or many accounts
        print(Fore.YELLOW)
        aws_accounts_question = input("List S3 buckets in one or all accounts: ")
        print(Fore.RESET)

    if aws_accounts_question.lower() == "one":
        interactive = 1
    else:
        interactive = 0

    if options.pageid:
        pageid = options.pageid
    else:
        pageid=223215673 # Main S3 Buckets Page
   
    if options.title:
        title = options.title
    else:
        title = 'AWS List Buckets - Test'

    if options.verbose:
        show_details = options.verbose
    else:
        print(Fore.YELLOW)
        show_details = input("Display bucket names (y/n): ")
        print(Fore.RESET)

    if options.send_email:
        email_answer = options.send_email
    else:
        print(Fore.YELLOW)
        email_answer = input("Send an email (y/n): ")
        print(Fore.RESET)

    if options.write_confluence:
        confluence_answer = options.write_confluence
    else:
        print(Fore.CYAN)
        confluence_answer = input("Write the list to confluence (y/n): ")
        print(Fore.RESET)


    # If to select one or many accounts based on the interactive variable
    if interactive == 1:
        # Set the account name
        if options.account_name:
            aws_account = options.account_name
        else:
            print(Fore.YELLOW)
            aws_account = input("Enter the name of the AWS account you'll be working in: ")
            print(Fore.RESET)

        # Find an S3 bucket
        if options.search:
            search_bucket = options.search
        else:
            search_bucket = input("Search for a bucket (y/n): ")

        ## Set the account number
        aws_account_number = aws_accounts_to_account_numbers(aws_account)
       
        # Grab variables from initialize
        today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
        print(Fore.CYAN)
        message = f"Working in AWS account: {aws_account}"
        output_file = list_s3_buckets(aws_account,aws_account_number, interactive, show_details, search_bucket)
        htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file, today, interactive, aws_account)
        print(Fore.YELLOW)

        message = " Send an Email "
        print(Fore.YELLOW)
        banner(message, "*")
        print(Fore.RESET)  
        # Send the email
        if email_answer.lower() == 'y' or email_answer == 'yes':
            send_email(aws_accounts_question,aws_account,aws_account_number, interactive)
        else:
            message = "Not sending an email."
            print(Fore.YELLOW)
            banner(message)
            print(Fore.RESET)
       
        with open(htmlfile, 'r', encoding='utf-8') as htmlfile:
            html = htmlfile.read()

        message = "* Write to Confluence *"
        print(Fore.CYAN)
        banner(message, "*")
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

    else:
        aws_account = 'all'
        today, aws_env_list, output_file, output_file_name, fieldnames = initialize(interactive, aws_account)
       
        # Find an S3 bucket
        if options.search:
            search_bucket = options.search
        else:
            search_bucket = input("Search for a bucket (y/n): ")

        if search_bucket.lower() == 'yes' or search_bucket.lower() == 'y':
            if options.bucket_name:
                find_bucket = options.bucket_name
            else:
                message = "Enter 'none' if you don't want to search for a bucket."
                banner(message)
                find_bucket = input("Enter a bucket name to find in the accounts: ")
       
        if find_bucket.lower() != 'none':
            search_bucket = find_bucket.lower()
        else:
            search_bucket = None

        if search_bucket is None:
            print("OK. Not searching for a bucket name")
           
        with open(output_file, mode='w+') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
            writer.writeheader()          
        with open(aws_env_list, 'r') as aws_envs:
                csv_reader = csv.reader(aws_envs, delimiter=',')
                next(csv_reader)
                for aws_accounts in csv_reader:
                    aws_account = str(aws_accounts[0])
                    aws_account_number = str(aws_accounts[1])
                    print("\n")
                    print("Working in AWS Account: ", aws_account)
                    print(Fore.RESET + "-----------------------------------------------")
                    output_file = list_s3_buckets(aws_account,aws_account_number, interactive, search_bucket)
                    htmlfile, htmlfile_name, remove_htmlfile = convert_csv_to_html_table(output_file,today, interactive, aws_account)
                    print(Fore.RESET + "-----------------------------------------------")
       
        message = " Send an Email "
        print(Fore.YELLOW)
        banner(message, "*")
        print(Fore.RESET)  
        # Send the email
        if email_answer.lower() == 'y' or email_answer == 'yes':
            send_email(aws_accounts_question,aws_account,aws_account_number, interactive)
        else:
            message = "Not sending an email."
            print(Fore.YELLOW)
            banner(message)
            print

        message = "* Write to Confluence *"
        print(Fore.CYAN)
        banner(message, "*")
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
    #remove_file(output_file, output_file_name)
    #remove_file(remove_htmlfile, htmlfile_name)
    endbanner()

if __name__ == "__main__":
    main()

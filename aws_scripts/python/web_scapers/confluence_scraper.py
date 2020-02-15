import csv
import os
import io
import requests
import getpass
import contextlib
import time
import argparse
from os import path
from requests_kerberos import HTTPKerberosAuth
from datetime import date, datetime, timedelta
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from colorama import init, Fore
init()

def welcome_banner():
    print(Fore.CYAN)
    message = "*             AWS Accounts Confluence Page Scraper        *"
    banner(message, '*')
    print(Fore.RESET)

def end_banner():
    print(Fore.CYAN)
    message = "*  AWS Accounts Confluence Page Scraper Operations Complete      *"
    banner(message, '*')
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def get_today():
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    return today

def get_user_name():
    print(Fore.YELLOW)
    user_name = input("Enter the user name: ")
    print('\n')
    return user_name

def get_login(username = None):
    if username is None:
        username = getpass.getuser()
    passwd = None
    if passwd is None:
        passwd = getpass.getpass()
    return (username, passwd)

def create_work_dir(work_dir):
    access_rights = 0o755
    try:  
        os.mkdir(work_dir)
    except OSError:  
        print (f"The directory %s already exists: {work_dir}")
    else:  
        print (f"Successfully created the directory: {work_dir}")

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

def arguments():
    parser = argparse.ArgumentParser(description='This program scrapes the kiki page to build a list of AWS accounts referenced in other modules.')

    parser.add_argument(
    "-u",
    "--user",
    default = getpass.getuser(),
    help = "Specify the username to log into Confluence")

    parser.add_argument(
    "-d",
    "--password",
    help = "Specify the user's password")

    options = parser.parse_args()
    return options

def web_scraper(options):
    today = get_today()
    output_dir = os.path.join( '..', '..', 'output_files', 'aws_accounts_list')
    with contextlib.redirect_stdout(io.StringIO()):
        create_work_dir(output_dir)
    filename = 'aws_kiki_page-' + today
    destination = os.path.join(output_dir, filename + '.csv' )
    url = 'https://kiki.us.kworld.company.com/display/6TO/AWS+Accounts'
    message = "Log into the kiki"
    print(Fore.CYAN)
    banner(message)
    print(Fore.RESET)

    if options.user and options.password:
        user = options.user
        password = options.password
        auth = (user, password)
        auth = str(auth).replace('(','').replace('\'','').replace(',',':').replace(')','').replace(' ','')
        kerberos_auth = HTTPKerberosAuth(mutual_authentication="DISABLED",principal=auth)
        page = requests.get(url, auth=kerberos_auth)
    else:
        auth = get_login()
        auth = str(auth).replace('(','').replace('\'','').replace(',',':').replace(')','').replace(' ','')
        kerberos_auth = HTTPKerberosAuth(mutual_authentication="DISABLED",principal=auth)
   
    page = requests.get(url, auth=kerberos_auth)
    headers = ['companyAccountName', 'AWSAccountName', 'AccountEmailID', 'Description', 'Application', 'LOB', 'AWSAccountNumber', 'CIDRBlock', 'QualysKeys', 'ConnectedtoMontvaleDC', 'PeninsulaorIsland', 'URL', 'Owner', 'Business/TechnicalContact', 'EngagementCode', 'CloudOpsAccessType']
    soup = BeautifulSoup(page.text, features="html.parser")
    table = soup.find('div',{'id':'content'})

    rows = []
    for table_row in table.find_all('tr'):
        columns = table_row.find_all('td')
        output_row = []
        for column in columns:
            output_row.append(column.text.strip().replace('(', ' ('))
        #print(output_row)    
        rows.append(output_row)
       
    with open(destination, 'w+', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for row in rows:
            if any(row):
                writer.writerow(row)
    if destination:
        message = f"Accounts list has been written to: {filename}."
    else:
        message = "Accounts list was not created."
    print(Fore.CYAN)
    banner(message)
    print(Fore.RESET)

def main():
    options = arguments()
    welcome_banner()
    time.sleep(10)
    web_scraper(options)
    time.sleep(10)
    end_banner()

if __name__ == "__main__":
    main()

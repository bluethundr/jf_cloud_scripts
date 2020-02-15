import csv
import os
import io
import requests
import time
import argparse
import contextlib
import getpass
from os import path
from datetime import date, datetime, timedelta
from requests import get
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from colorama import init, Fore
init()

def welcome_banner():
    print(Fore.CYAN)
    message = "*   Monster Page Scraper   *"
    banner(message, '*')
    print(Fore.RESET)

def end_banner():
    print(Fore.CYAN)
    message = "*   Monster Page Scraper Operations Complete   *"
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
    parser = argparse.ArgumentParser(description='This program scrapes the monster site looking for python jobs.')

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
    output_dir = os.path.join( '..', '..', 'output_files', 'monster')
    with contextlib.redirect_stdout(io.StringIO()):
        create_work_dir(output_dir)
    filename = 'monster_page-' + today
    destination = os.path.join(output_dir, filename + '.csv' )
    region = input("Where do you want to work: ")
    url = 'https://www.monster.com/jobs/search/?q=Software-Developer&where=' + region
    message = "Scrape the monster page and look for python jobs"
    print(Fore.CYAN)
    banner(message)
    print(Fore.RESET)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, features="html.parser")
    results = soup.find(id='ResultsContainer')
    job_elems = results.find_all('section', class_='card-content')
    python_jobs = results.find_all('h2',
                            string=lambda text: "python" in text.lower())
    count = 0
    for p_job in python_jobs:
        link = p_job.find('a')['href']
        print(p_job.text.strip())
        print(f"Apply here: {link}\n")
        count = count + 1


    if len(python_jobs) == 0:
        print(f"Sorry. No python developer jobs in {region}.")
    elif len(python_jobs) == 1:
        print(f"There is 1 python job in {region}.")
    else:
        print(f"There are {count} python jobs in {region}.")

def main():
    options = arguments()
    welcome_banner()
    time.sleep(10)
    web_scraper(options)
    time.sleep(10)
    end_banner()

if __name__ == "__main__":
    main()
 
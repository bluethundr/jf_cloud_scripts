import os
import sys
import logging
import boto3
import threading
from botocore.exceptions import ClientError
from colorama import init, Fore

## Standard functions
def exit_program():
    endbanner()
    exit()
    
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    print('******************************************************')
    print('*             AWS Billing Operations                 *')
    print('******************************************************\n')
    time.sleep(5)

def endbanner():
    print(Fore.CYAN)
    print("*****************************************************")
    print("* AWS Billing Operations Are Complete               *")
    print("*****************************************************")

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def initialize():
    print(Fore.YELLOW)
    aws_account = input("Enter the name of the AWS account you'll be working in: ")
    print(Fore.GREEN, "\n")
    message = f"*            Okay. Working in AWS account: {aws_account}                *"
    banner(message, "*")
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
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
        s3_client = session.client("s3")
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
            s3_client = session.client("s3")
        except Exception as e:
            pass
        if account_found == 'yes':
            message = "This is a commercial account."
            banner(message)
    return aws_account, aws_account_number, s3_client, today


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


class ProgressPercentage(object):
    
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()


def main():
    welcomebanner()
    initialize()
    upload_file(filename, bucket, object_name=None)

if __name__ == "__main__":
    main()
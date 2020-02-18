from modules import *
from datetime import datetime
from banners import *

def init_create_ec2(aws_account, region):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_confluence_page.csv')
    # Create the session
    if 'gov' in aws_account and not 'admin' in aws_account:
        try:
            session = boto3.Session(profile_name=aws_account, region_name=region)
        except botocore.exceptions.ProfileNotFound as e:
            profile_missing_message = f"An exception has occurred: {e}"
            banner(profile_missing_message)
    else:
        try:
            session = boto3.Session(profile_name=aws_account, region_name=region)
            account_found = 'yes'
        except botocore.exceptions.ProfileNotFound as e:
            profile_missing_message = f"An exception has occurred: {e}"
            banner(profile_missing_message)
    try:
        ec2_client = session.client("ec2")
        ec2_resource = session.resource("ec2")
    except Exception as e:
        print(f"An exception has occurred: {e}")
    return today, aws_env_list, ec2_client, ec2_resource
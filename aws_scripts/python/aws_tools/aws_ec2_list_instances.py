#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Import modules
import boto3, botocore, objectpath, csv, smtplib, os, argparse, getpass, json, keyring, requests, time, signal, re, difflib
import dns.resolver
from html import escape
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from banners import banner
from aws_partition import get_partition, is_gov
from ec2_mongo import insert_coll, mongo_export_to_file, delete_from_collection
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ProfileNotFound,
    NoCredentialsError,
    UnauthorizedSSOTokenError,
    SSOTokenLoadError,
    TokenRetrievalError,
    SSLError,
    EndpointConnectionError
)

# Initialize the color output with colorama
init()

# Handles ctl+c anywhere
def _handle_sigint(sig, frame):
    print(Fore.YELLOW)
    banner("Interrupted (Ctrl+C). Exiting cleanly.")
    print(Fore.RESET)
    raise SystemExit(130)

# Define Config
config = Config(
    retries={"max_attempts": 8, "mode": "standard"},
    connect_timeout=5,
    read_timeout=30,
)

# Call the sigint function
signal.signal(signal.SIGINT, _handle_sigint)

### Cli arguments
def arguments():
    parser = argparse.ArgumentParser(description='This is a program that lists the servers in EC2')

    parser.add_argument(
        "-n",
        "--account_name",
        type=str,
        default=None,
        nargs='?',
        help="Name of the AWS account you'll be working in")

    parser.add_argument(
        "-c",
        "--all_accounts",
        type=str,
        default=None,
        nargs='?',
        help="Process one or all accounts")

    parser.add_argument(
        "-e",
        "--send_email",
        type=str,
        help="Send an email")

    parser.add_argument(
        "-r",
        "--email_recipient",
        type=str,
        help="Who will receive the email")

    parser.add_argument(
        "-g",
        "--first_name",
        type=str,
        help="First (given) name of the person receving the email")

    parser.add_argument(
        "-i",
        "--run_again",
        type=str,
        help="Run again")

    parser.add_argument(
        "-v",
        "--verbose",
        type=str,
        help="Write the EC2 instances to the screen")

    parser.add_argument(
        "-o",
        "--reports",
        type=str,
        help="Run reports")

    options = parser.parse_args()
    return options

## Define regions
DEFAULT_REGIONS_COMMERCIAL = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
]

OPTIONAL_REGIONS_COMMERCIAL = [
    "af-south-1",
    "ap-east-1",
    "ap-south-2",
    "ap-southeast-3",
    "ap-southeast-4",
    "eu-central-2",
    "eu-south-1",
    "eu-south-2",
    "il-central-1",
    "me-central-1",
    "me-south-1",
    "mx-central-1",
]

DEFAULT_REGIONS_GOV = [
    "us-gov-west-1",
    "us-gov-east-1",
]

EXCLUDED_COMMERCIAL_REGIONS = {
    "me-south-1",
}

## Check email domains regex
EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def is_valid_email_syntax(email_addr: str) -> bool:
    return bool(EMAIL_RE.match(email_addr.strip()))

### Utility Functions
#Banners
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*                     List AWS EC2 Instances                     *"
    banner(message)
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "*   List AWS Instance Operations Are Complete   *"
    banner(message)
    print(Fore.RESET)

# Fail gracefully on import errors
def fatal(msg: str, code: int = 1) -> None:
    print(Fore.RED)
    banner(msg)
    print(Fore.RESET)
    raise SystemExit(code)

# Check all logins before the loop
def preflight_all_sso_or_fail(profiles: list[str]) -> None:
    """
    Validate that all profiles can resolve creds (SSO) BEFORE scanning.
    If any profile fails due to expired/missing SSO, exit with one banner.
    """
    bad: list[tuple[str, str]] = []

    for profile in profiles:
        p = profile.strip()
        if not p:
            continue

        try:
            s = boto3.Session(profile_name=p)
        except ProfileNotFound as e:
            # This is NOT SSO expiry; still useful to stop early if you want.
            bad.append((p, f"Profile not found: {e}"))
            continue

        try:
            s.client("sts").get_caller_identity()
        except Exception as e:
            # Keep only auth/SSO style failures (or keep all failures—your choice)
            bad.append((p, friendly_aws_auth_error(e, p)))

    if bad:
        lines = ["SSO / credential preflight failed. Log into AWS SSO and re-run.", ""]
        # Provide a clear command + list which profiles failed
        lines.append("Fix (run these):")
        for prof, _ in bad:
            lines.append(f"  aws sso login --profile {prof}")

        lines.append("")
        lines.append("Details:")
        for prof, msg in bad:
            lines.append(f"- {prof}: {msg}")

        fatal("\n".join(lines))


def friendly_aws_auth_error(e: Exception, profile: str) -> str:
    """
    Convert common boto/botocore auth problems (especially SSO expiry) into a human message.
    """
    # SSO token / login problems
    if isinstance(e, (UnauthorizedSSOTokenError, SSOTokenLoadError, TokenRetrievalError)):
        return (
            f"AWS SSO credentials are missing/expired for profile '{profile}'.\n"
            f"Fix: run `aws sso login --profile {profile}` and re-run the script."
        )

    # No credentials found at all
    if isinstance(e, NoCredentialsError):
        return (
            f"No AWS credentials found for profile '{profile}'.\n"
            f"If this is SSO, run `aws sso login --profile {profile}`."
        )

    # STS/SDK says “no auth / expired”
    if isinstance(e, ClientError):
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        if code in {"ExpiredToken", "InvalidClientTokenId", "UnrecognizedClientException"}:
            return (
                f"AWS credentials are expired/invalid for profile '{profile}'. ({code})\n"
                f"Fix: run `aws sso login --profile {profile}`.\n"
                f"Details: {msg}"
            )
        if code in {"AccessDenied", "AccessDeniedException"}:
            return (
                f"Access denied for profile '{profile}'. ({code})\n"
                f"Details: {msg}"
            )

    # Fallback
    return f"AWS error for profile '{profile}': {e}"


def make_session_or_fail(profile: str) -> boto3.Session:
    """
    (a) Handles misspelled profile (ProfileNotFound)
    (b) Handles expired SSO / creds by probing STS once
    """
    try:
        s = boto3.Session(profile_name=profile)
    except ProfileNotFound as e:
        fatal(
            f"Profile '{profile}' was not found (misspelled account name / missing AWS config).\n"
            f"Fix: check your aws_accounts_list.csv and `aws configure list-profiles`.\n"
            f"Details: {e}"
        )

    # Probe STS to force credential resolution now (instead of failing later in random places)
    try:
        s.client("sts").get_caller_identity()
    except Exception as e:
        fatal(friendly_aws_auth_error(e, profile))

    return s


def make_session_or_skip(profile: str) -> boto3.Session | None:
    """
    Same as above, but returns None so caller can skip this account (useful for 'all accounts' mode).
    """
    try:
        s = boto3.Session(profile_name=profile)
    except ProfileNotFound as e:
        banner(
            f"Skipping '{profile}': profile not found (misspelled / missing config).\n"
            f"Details: {e}"
        )
        return None

    try:
        s.client("sts").get_caller_identity()
    except Exception as e:
        banner(f"Skipping '{profile}': {friendly_aws_auth_error(e, profile)}")
        return None

    return s

# Initialize the main body of the script
def initialize(interactive, aws_account):
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')
    # Set the output file
    output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'csv', '')
    ### Interactive == 1  - user specifies an account
    if interactive == 1:
        output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today + '.csv')
        output_file_name = 'aws-instance-list-' + aws_account + '-' + today + '.csv'
    else:
        output_file = os.path.join(output_dir, 'aws-instance-master-list-' + today + '.csv')
        output_file_name = 'aws-instance-master-list-' + today + '.csv'
    return today, aws_env_list, output_file, output_file_name

# Exit the program
def exit_program():
    endbanner()
    exit()

# Read acccount info
def read_account_info(aws_env_list):
    account_names = []
    account_numbers = []
    with open(aws_env_list) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            account_name = str(row[0]).strip()
            account_number = str(row[1]).strip()
            account_names.append(account_name)
            account_numbers.append(account_number)
    return account_names, account_numbers

# Distinguish between gov and commercial accounts
def report_gov_or_comm(aws_account):
    if is_gov(aws_account):
        message = "Verified: This is a GovCloud account."
        banner(message)
    else:
        message = "Verified: This is a commercial account."
        banner(message)

# Report number of instances in an account
def report_instance_stats(instance_count: int, aws_account: str, account_found: bool) -> None:
    if not account_found:
        return
    noun = "instance" if instance_count == 1 else "instances"
    verb = "is" if instance_count == 1 else "are"
    none = "no" if instance_count == 0 else str(instance_count)
    banner(f"There {verb} {none} EC2 {noun} in AWS Account: {aws_account}.")

# Set the regions
def set_regions(active_session_object):
    sts_info = active_session_object.client('sts').get_caller_identity()
    partition = sts_info['Arn'].split(':')[1]

    print(Fore.GREEN)
    banner("Getting the regions...")
    print(Fore.RESET)

    home = 'us-gov-west-1' if partition == 'aws-us-gov' else 'us-east-1'

    ec2_discovery = active_session_object.client('ec2', region_name=home, config=config)
    active_regions = [r['RegionName'] for r in ec2_discovery.describe_regions(AllRegions=False)['Regions']]

    if partition != 'aws-us-gov':
        active_regions = [r for r in active_regions if r not in EXCLUDED_COMMERCIAL_REGIONS]

    return active_regions

def make_session_or_skip(profile: str) -> boto3.Session | None:
    """
    Same as above, but returns None so caller can skip this account.
    """
    try:
        s = boto3.Session(profile_name=profile)
    except ProfileNotFound as e:
        banner(
            f"Skipping '{profile}': profile not found (misspelled / missing config).\n"
            f"Details: {e}"
        )
        return None

    try:
        s.client("sts").get_caller_identity()
    except Exception as e:
        banner(f"Skipping '{profile}': {friendly_aws_auth_error(e, profile)}")
        return None

    return s

COMMON_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "comcast.net",
    "verizon.net",
}

COMMON_EMAIL_DOMAIN_FIXES = {
    "gmail.om": "gmail.com",
    "gmal.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmail.con": "gmail.com",
    "gmaisl.om": "gmail.com",
    "yahoo.con": "yahoo.com",
    "outlook.con": "outlook.com",
    "hotmail.con": "hotmail.com",
}

EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

def is_valid_email_syntax(email_addr: str) -> bool:
    return bool(EMAIL_RE.match(email_addr.strip()))


def suggest_email_domain(domain: str) -> str | None:
    matches = difflib.get_close_matches(
        domain.lower().strip(),
        COMMON_EMAIL_DOMAINS,
        n=1,
        cutoff=0.72
    )

    if matches:
        return matches[0]

    return None


def domain_has_mx_record(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False
def yellow_input(prompt: str) -> str:
    print(Fore.YELLOW + prompt, end="")
    answer = input()
    print(Fore.RESET, end="")
    return answer

def validate_email_recipient(email_addr: str, interactive_confirm: bool = True) -> str | None:
    email_addr = email_addr.strip()

    if not is_valid_email_syntax(email_addr):
        print(Fore.RED + f"Invalid email address format: {email_addr}" + Fore.RESET)
        return None

    local_part, domain = email_addr.rsplit("@", 1)
    domain = domain.lower()

    suggested_domain = suggest_email_domain(domain)

    if suggested_domain and suggested_domain != domain:
        suggested_email = f"{local_part}@{suggested_domain}"

        if interactive_confirm:
            answer = yellow_input(
                f"Suspicious email domain '{domain}'. Did you mean {suggested_email}? (y/n): "
            ).strip().lower()
            if answer in {"y", "yes"}:
                email_addr = suggested_email
                domain = suggested_domain
            else:
                return None
        else:
            banner(f"Suspicious email domain '{domain}'. Did you mean {suggested_email}?")
            return None

    if not domain_has_mx_record(domain):
        print(
            Fore.RED +
            f"The domain '{domain}' does not appear to accept email." +
            Fore.RESET
        )
        return None

    if interactive_confirm:
        confirm = yellow_input(
            f"Final recipient will be: {email_addr}. Send to this address? (y/n): "
        ).strip().lower()
        if confirm not in {"y", "yes"}:
            return None

    return email_addr


def prompt_for_valid_email(prompt="Enter the recipient's email address: ") -> str:
    while True:
        email_addr = input(prompt)
        validated_email = validate_email_recipient(email_addr, interactive_confirm=True)

        if validated_email:
            return validated_email

        print(Fore.YELLOW + "Please enter the recipient email address again." + Fore.RESET)

### Email function
def send_email(aws_accounts_answer, aws_account, aws_account_number, interactive):
    ## Get gmail username and pass from environment variables
    gmail_user = os.environ.get('gmail_user')
    gmail_password = os.environ.get('gmail_password')
    options = arguments()
    to_addr = ''
    # Get the variables from intitialize
    today, _, output_file, _ = initialize(interactive, aws_account)
    if options.first_name:
        ## Get the address to send to
        print(Fore.YELLOW)
        first_name = options.first_name
        print(Fore.RESET)
    else:
        first_name = input("Enter the recipient's first name: ")

    if options.email_recipient:
        to_addr = validate_email_recipient(
            options.email_recipient,
            interactive_confirm=True
        )

        if not to_addr:
            banner("Invalid, suspicious, or unconfirmed email recipient. Email was not sent.")
            return
    else:
        to_addr = prompt_for_valid_email()

    from_addr = 'jokefire.noreply@gmail.com'
    if aws_accounts_answer == 'one':
        subject = "AWS Instance List: " + aws_account + " (" + aws_account_number + ") " + today
        content = "<font size=2 face=Verdana color=black>Hello " + first_name + ", <br><br>Enclosed, please find a list of instances in JF AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>The Jokefire Systems Team</font>"
    else:
        subject = "AWS Instance Master List " + today
        content = "<font size=2 face=Verdana color=black>Hello " + first_name + ", <br><br>Enclosed, please find a list of instances in all JF AWS accounts.<br><br>Regards,<br>The Jokefire Systems Team</font>"
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = MIMEText(content, 'html')
    msg.attach(body)
    filename = output_file
    try:
        with open(filename, 'rb') as f:
            file_data = f.read()
    except Exception as e:
        print(f"Failed to read file: {e}")
        return

    fname = basename(filename) if filename else "attachment.csv"

    part = MIMEApplication(file_data, Name=basename(filename))
    part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(filename))
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
        message = f"Email was sent to: {to_addr}"
        print(Fore.YELLOW)
        banner(message)
        print(Fore.RESET)
    except Exception as error:
        message = f"Exception: {error}\nEmail was not sent."
        banner(message)
    print(Fore.RESET)


# Convert CSV to HTML
def convert_csv_to_html_table(output_file, today, interactive, aws_account):
    output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'html')
    try:
        if interactive == 1:
            htmlfile = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today + '.html')
            htmlfile_name = 'aws-instance-list-' + aws_account + '-' + today + '.html'
        else:
            htmlfile = os.path.join(output_dir, 'aws-instance-master-list-' + today + '.html')
            htmlfile_name = 'aws-instance-master-list-' + today + '.html'

        count = 0
        html = ''
        with open(output_file, 'r') as CSVFILE:
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

        with open(htmlfile, 'w+') as HTMLFILE:
            HTMLFILE.write(html)
    except Exception as e:
        print(f"A convert_csv_to_html_table exception has occurred: {e}")
        return None, None  # Return None to indicate failure

    return htmlfile, htmlfile_name


### AWS List Instances
def list_instances(session_obj, aws_account, aws_account_number, interactive, regions, show_details):
    _, _, output_file, _ = initialize(interactive, aws_account)
    delete_from_collection(aws_account_number)

    instance_count = 0
    account_found = False
    ec2info = {}

    print(Fore.CYAN)
    report_gov_or_comm(aws_account)
    print(Fore.RESET)
    for region in regions:
        response = None

        for attempt in range(1, 4):
            try:
                ec2 = session_obj.client("ec2", region_name=region, config=config)
                response = ec2.describe_instances()
                break
            except SSLError as e:
                if attempt == 3:
                    print(f"SSL/TLS failed in {aws_account}/{region}: {e}")
                else:
                    time.sleep(2 ** attempt)
            except EndpointConnectionError as e:
                print(f"Endpoint connection failed in {aws_account}/{region}: {e}")
                break
            except ClientError as e:
                print(f"AWS client error in {aws_account}/{region}: {e}")
                break

        if response is None:
            continue

        # Process instances (don’t hide errors; fail with banner)
        try:
            for reservation in response.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instance_count += 1

                    instance_state = inst.get("State", {}).get("Name")
                    instance_type = inst.get("InstanceType")
                    instance_id = inst.get("InstanceId")
                    ami_id = inst.get("ImageId")

                    launch_time = inst.get("LaunchTime")
                    launch_time_friendly = launch_time.strftime("%B %d %Y") if launch_time else None

                    tree = objectpath.Tree(inst)

                    block_devices = set(tree.execute('$..BlockDeviceMappings[\'Ebs\'][\'VolumeId\']'))
                    volumes = (
                        str(list(block_devices)).replace("[", "").replace("]", "").replace("'", "")
                        if block_devices else None
                    )

                    private_ips = set(tree.execute("$..PrivateIpAddress"))
                    private_ips_list = (
                        str(list(private_ips)).replace("[", "").replace("]", "").replace("'", "")
                        if private_ips else None
                    )

                    public_ips = set(tree.execute("$..PublicIp"))
                    public_ips_list = (
                        str(list(public_ips)).replace("[", "").replace("]", "").replace("'", "")
                        if public_ips else None
                    )

                    instance_name = None
                    engagement = None
                    for tag in inst.get("Tags", []) or []:
                        if tag.get("Key") == "Name":
                            instance_name = tag.get("Value")
                        if tag.get("Key") in {"Engagement", "Engagement Code"}:
                            engagement = tag.get("Value")

                    key_name = inst.get("KeyName")  # safe
                    vpc_id = inst.get("VpcId")
                    private_dns = inst.get("PrivateDnsName")
                    availability_zone = inst.get("Placement", {}).get("AvailabilityZone")

                    row = {
                        "AWS Account": aws_account,
                        "Account Number": aws_account_number,
                        "Instance Name": instance_name,
                        "Instance ID": instance_id,
                        "AMI ID": ami_id,
                        "Volumes": volumes,
                        "Private IP": private_ips_list,
                        "Public IP": public_ips_list,
                        "Private DNS": private_dns,
                        "Availability Zone": availability_zone,
                        "VPC ID": vpc_id,
                        "Instance Type": instance_type,
                        "Key Pair Name": key_name,
                        "Instance State": instance_state,
                        "Launch Date": launch_time_friendly,
                    }

                    ec2info[instance_id] = row
                    insert_coll({"_id": "", **row})

        except Exception as e:
            fatal(f"Error processing instances in {aws_account}/{region}: {e}")

        # Optional verbose printing (fixes your key mismatches)
        if show_details in {"y", "yes"}:
            for _, instrow in ec2info.items():
                print(Fore.RESET + "-------------------------------------")
                for key in [
                    "AWS Account",
                    "Account Number",
                    "Instance Name",
                    "Instance ID",
                    "AMI ID",
                    "Volumes",
                    "Private IP",
                    "Public IP",
                    "Private DNS",
                    "Availability Zone",
                    "VPC ID",
                    "Instance Type",
                    "Key Pair Name",
                    "Instance State",
                    "Launch Date",
                ]:
                    print(Fore.GREEN + f"{key}: {instrow.get(key)}")
                print(Fore.RESET + "-------------------------------------")

        ec2info.clear()

    print(Fore.CYAN)
    noun = "instance" if instance_count == 1 else "instances"
    verb = "is" if instance_count == 1 else "are"
    none = "no" if instance_count == 0 else str(instance_count)
    banner(f"There {verb} {none} EC2 {noun} in AWS Account: {aws_account}.")
    print(Fore.RESET + "\n")

    return output_file


### Main Function
def main():
    # Get command line arguments
    options = arguments()

    # Display the welcome banner
    welcomebanner()
    if options.reports:
        reports_answer = options.reports
    else:
        print(Fore.YELLOW)
        reports_answer = input("Print reports (y/n): ")
        print(Fore.RESET)

    if options.all_accounts:
        aws_accounts_answer = options.all_accounts
    else:
        ## Select one or many accounts
        print(Fore.YELLOW)
        aws_accounts_answer = input("List instances in one or all accounts: ")
        print(Fore.RESET)

    # Set interacive variable to indicate one or many accounts
    if '1' in aws_accounts_answer.lower() or 'one' in aws_accounts_answer.lower():
        interactive = 1
    else:
        interactive = 0

    aws_account_number = None
    ### Interactive == 1  - user specifies an account
    if interactive == 1:
        ## Select the account
        if options.account_name:
            aws_account = options.account_name
        else:
            print(Fore.YELLOW)
            aws_account = input("Enter the name of the AWS account you'll be working in: ")
            print(Fore.RESET)

        # Set variables
        today, aws_env_list, output_file, _ = initialize(interactive, aws_account)

        if options.verbose:
            show_details = options.verbose
        else:
            print(Fore.YELLOW)
            show_details = input("Show server details (y/n): ")
            print(Fore.RESET)


        # Read account info from the accounts list file
        account_names, account_numbers = read_account_info(aws_env_list)
        print(Fore.YELLOW)
        message = "Work in one or all accounts"
        banner(message)
        if 'one' in aws_accounts_answer.lower():
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
        # Fail gracefully on misspelled profile
        if not aws_account_number:
            banner(f"Account '{aws_account}' not found in aws_accounts_list.csv. Check spelling.")
            exit_program()

        # Set the regions and run the program
        session_obj = make_session_or_fail(aws_account)  # validates profile + STS auth once
        regions = set_regions(session_obj)
        output_file = list_instances(session_obj, aws_account, aws_account_number, interactive, regions, show_details)
        if reports_answer.lower() == 'yes' or reports_answer.lower() == 'y':
            try:
                mongo_export_to_file(interactive, aws_account, aws_account_number)
            except Exception as e:
                print(f"A mongo exception has occurred: {e}")
            htmlfile, _ = convert_csv_to_html_table(output_file, today, interactive, aws_account)
            print(Fore.YELLOW)
            message = "Send an Email"
            banner(message)
            if options.send_email:
                email_answer = options.send_email
            else:
                print(Fore.YELLOW)
                email_answer = input("Send an email (y/n): ")

            if 'yes' in email_answer or 'y' in email_answer:
                send_email(aws_accounts_answer, aws_account, aws_account_number, interactive)
            else:
                message = "Okay. Not sending an email."
                print(Fore.YELLOW)
                banner(message)
            print(Fore.RESET)

            try:
                with open(htmlfile, 'r') as htmlfile:
                    html = htmlfile.read()
            except Exception as e:
                print(f"Open file exception: {e}")

    ### Interactive == 0 - cycling through all acounts.
    else:
        if options.verbose:
            show_details = options.verbose
        else:
            print(Fore.YELLOW)
            show_details = input("Show server details (y/n): ")
            print(Fore.RESET)
        aws_account = 'all'
        # Grab variables from initialize
        today, aws_env_list, output_file, _ = initialize(interactive, aws_account)
        account_names, account_numbers = read_account_info(aws_env_list)
        # Preflight before doing any scanning
        preflight_all_sso_or_fail(account_names)
        for (aws_account, aws_account_number) in zip(account_names, account_numbers):
            message = f"Working in AWS Account: {aws_account}."
            print(Fore.YELLOW)
            banner(message)
            print(Fore.RESET)
            # Set the regions
            session_obj = make_session_or_skip(aws_account)
            if not session_obj:
                continue
            try:
                regions = set_regions(session_obj)
            except Exception as e:
                banner(f"Skipping {aws_account}: unable to list regions:\n{friendly_aws_auth_error(e, aws_account)}")
                continue
            output_file = list_instances(session_obj, aws_account, aws_account_number, interactive, regions, show_details)
        if reports_answer.lower() == 'yes' or reports_answer.lower() == 'y':
            mongo_export_to_file(interactive, "all", None)
            htmlfile, _ = convert_csv_to_html_table(output_file, today, interactive, "all")
            print(Fore.YELLOW)
            message = "Send an Email"
            banner(message)
            if options.send_email:
                email_answer = options.send_email
            else:
                print(Fore.YELLOW)
                email_answer = input("Send an email (y/n): ")

            if email_answer.lower() == 'y' or email_answer == 'yes':
                send_email(aws_accounts_answer, aws_account, aws_account_number, interactive)
            else:
                message = "Okay. Not sending an email."
                print(Fore.YELLOW)
                banner(message)
            print(Fore.RESET)

            with open(htmlfile, 'r') as htmlfile:
                html = htmlfile.read()

    print(Fore.GREEN)
    if options.run_again:
        list_again = options.run_again
    else:
        print(Fore.GREEN)
        list_again = input("List EC2 instances again (y/n): ")
        print(Fore.RESET)
    if list_again.lower() == 'y' or list_again.lower() == 'yes':
        main()
    else:
        exit_program()
    print(Fore.RESET)


### Run locally
if __name__ == "__main__":
    main()
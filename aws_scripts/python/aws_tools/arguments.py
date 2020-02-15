import argparse

def arguments():
    parser = argparse.ArgumentParser(description='This is a program that creates the servers in EC2')

    parser.add_argument(
    "-a",
    "--ami_id",
    type = str,
    default = None,
    nargs = '?',
    help = "Specify the AMI ID")

    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the AWS account you'll be working in")

    parser.add_argument(
    "-m",
    "--max_count",
    type = str,
    help = "The number of ec2 instances you will create")

    parser.add_argument(
    "-k",
    "--key_name",
    type = str,
    help = "The name of the key you want to use")

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

    options = parser.parse_args()
    return options
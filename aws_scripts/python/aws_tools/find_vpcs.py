import re
from banners import *

def find_vpcs(ec2_client):
    vpc = ''
    vpc_list = ec2_client.describe_vpcs()
    print(Fore.CYAN)
    message = f"Available VPCS:"
    banner(message)
    for vpc in vpc_list["Vpcs"]:
        print(vpc['VpcId'])
    print(Fore.YELLOW)
    vpc_id = input("Enter the vpc to use: ")
    #pattern = re.compile('vpc-\w{21}$')
    #match = pattern.match(vpc_id)
    #while not match:
    #    vpc_id = input('vpc id:')
    #    match = pattern.match(vpc_id)
    #return vpc_id
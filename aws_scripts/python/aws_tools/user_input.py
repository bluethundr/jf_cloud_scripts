import objectpath
from init import initialize
from find_vpcs import find_vpcs
from arguments import arguments
from colorama import init, Fore
from banners import *

# Initialize the color ouput with colorama
init()

  
def user_input():
    options = arguments()

    name_tags = []
    print(Fore.GREEN)
    banner('AWS Account')
    print(Fore.YELLOW)
    aws_account = input("Enter the account name: ")
    #aws_account = 'jf-master-acct-pd'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("AWS Region")
    print(Fore.YELLOW)
    region = input("Enter the region to create EC2 in: ")
    #region = 'us-east-1'
    today, aws_env_list, ec2_client, ec2_resource = initialize(aws_account, region)
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Instance Count")
    print(Fore.YELLOW)
    max_count = None
    while max_count is None:
        try:
            max_count = int(input("Enter how many EC2 Servers: "))
        except Exception:
            continue
    print(Fore.CYAN)
    for count in range(max_count):
        name_tag = input(f"Please enter the name of server: {count + 1}: ")
        name_tags.append(name_tag)
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("AMI ID")
    print(Fore.YELLOW)
    image_id = input("Enter an AMI ID: ")
    #image_id = 'ami-00e6eeb9644429ec6'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Key Pair")
    print(Fore.YELLOW)
    key_name = input("Enter the key name to use: ")
    #key_name = 'sncr-timd'
    print(Fore.RESET)

    print(Fore.GREEN)   
    banner("Instance Type")
    print(Fore.YELLOW)
    instance_type = input("Enter the instance type: ")
    #instance_type = 't2.small'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("VPC Selection")
    print(Fore.YELLOW)
    vpc_id = find_vpcs(ec2_client)
    #vpc_id = 'vpc-68b1ff12'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Security Groups")
    print(Fore.YELLOW)
    sg_list = ec2_client.describe_security_groups()
    tree = objectpath.Tree(sg_list)
    sg_id_list = set(tree.execute('$..SecurityGroups[\'GroupId\']'))
    sg_id_list = list(sg_id_list)
    sg_id_list = str(list(sg_id_list)).replace('[','').replace(']','').replace('\'','')
    print(Fore.CYAN)
    message = f"Available Security Groups: {sg_id_list}"
    banner(message)
    print(Fore.YELLOW)
    sg_list = input("Enter a comma separated list of security groups to add: ")
    #sg_list = 'sg-0afa867f9029bb468, sg-031ac185d029cd5fd, sg-0e4b5fc1d40185fc3, sg-05ef09508245e56bc, sg-2cad407c, sg-0d0ddf3117d23cadb'
    sg_list = sg_list.split(',')
    sg_id = sg_list.pop(0)
    #sg_list = str(sg_list)
    #sg_list = sg_list.replace('[','').replace(']','').replace('\'','').replace('\'','').replace(' ','')
    #print(f"SG ID: {sg_id}\nSG List: {sg_list}")
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("VPC Subnets")
    print(Fore.YELLOW)
    subnet_ids = []
    for vpc in ec2_resource.vpcs.all():
        # here you can choose which subnet based on the id
        if vpc.id == vpc_id:
            for subnet in vpc.subnets.all():
                subnet_ids.append(subnet.id)
    subnet_list = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    tree = objectpath.Tree(subnet_list)
    subnet_list = set(tree.execute('$..Subnets[\'SubnetId\']'))
    subnet_list = list(subnet_list)
    subnet_list = str(subnet_list).replace('[','').replace(']','').replace('\'','')
    print(Fore.CYAN)
    message = f"Available Subnet IDs in {vpc_id}:\n{subnet_list}"
    banner(message)
    print(Fore.YELLOW)
    subnet_id = input("Enter the subnet id: ")
    #subnet_id = 'subnet-63ad5a6d'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Public IP")
    print(Fore.YELLOW)
    public_ip_answer = input("Associate a public IP (y/n): ")
    #public_ip_answer = 'yes'
    if public_ip_answer.lower() == 'yes' or public_ip_answer == 'yes':
        public_ip = True
    else:
        public_ip = False
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Private IP")
    print(Fore.YELLOW)
    private_ip_answer = input("Specify private ip address(es) (y/n): ")
    #private_ip_answer = 'no'
    if private_ip_answer.lower() == 'y' or private_ip_answer.lower() == 'yes':
        private_ip_list = input("Enter private IP addresses separated by commas: ")
        private_ip_list = private_ip_list.split(",")
    else:
        private_ip_list = None

    print(Fore.GREEN)
    banner("Host Tenancy")
    print(Fore.YELLOW)
    print("Tenancy choices are: default|dedicated|host")
    tenancy = input("Enter the type of tenancy you want: ")
    #tenancy = 'default'
    print(Fore.RESET)

    print(Fore.GREEN)
    banner("Instance Monitoring")
    print(Fore.YELLOW)
    monitoring_enabled = input("Add monitoring (y/n): ")
    #monitoring_enabled = 'no'
    if monitoring_enabled.lower() == 'y' or monitoring_enabled.lower() == 'yes':
        monitoring_enabled = True
    else:
        monitoring_enabled = False

    print(Fore.GREEN)
    banner("User Data")
    print(Fore.YELLOW)
    user_data_question = input("Enter user data (y/n): ")
    #user_data_question = 'no'
    if user_data_question.lower() == 'y' or user_data_question.lower() == 'yes':
        user_data = input("Enter user data: ")
    else:
        user_data = ''
    print(Fore.RESET)
    print("\n")

    return aws_account, region, max_count, image_id, key_name, instance_type, vpc_id, subnet_id, sg_id, sg_list, subnet_ids, public_ip, private_ip_list, tenancy, monitoring_enabled, user_data, name_tags

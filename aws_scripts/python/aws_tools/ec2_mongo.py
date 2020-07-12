# Import modules
import pymongo
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from datetime import datetime
from colorama import init, Fore
from pprint import pprint
init()

def set_db():
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient['aws_ec2_list']
    instance_col_date = 'aws_ec2_list-' + today
    instance_col = mydb[instance_col_date]
    #database_names = mydb.list_database_names()
    return myclient, mydb, instance_col

def set_test_dict():
    mydict = { "AWS Account": "ccmi-verizon-lab", "Account Number": "046480487130", "Name": "bastion001",
"Instance ID": "i-07aaef3b7167d592a", "AMI ID": "ami-07fd81f1ecf6cf387", "Volumes": "vol-09d6d898db4af132a",
"Private IP": "10.238.3.165", "Public IP": "3.227.224.221", "Private DNS": "ip-10-238-3-165.ec2.internal",
"Availability Zone": "us-east-1a", "VPC ID": "vpc-00de11103235ec567", "Type": "t3.small", "Key Pair Name": "ccmi-vzn-int01", "Instance State": "running", "Launch Date": "September 10 2019"}
    return mydict

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             EC2 MongoDB                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* EC2 MongoDB Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def exit_program():
    endbanner()
    exit()

def insert_doc(instance_col,mydict):
    message = f"* Insert MongoDB Document *"
    print(Fore.GREEN)
    banner(message, border='*')
    print("This command inserts a test document.\n")
    mydict['_id'] = ObjectId()
    x = instance_col.insert_one(mydict)
    print(f"MongoDB record inserted: {x.inserted_id}")
    return x

def print_db(instance_col):
    message = f"* Print DB Documents *"
    print(Fore.GREEN)
    banner(message, border='*')
    print('\n')
    x = instance_col.find()
    for data in x:
        print(data)

def clear_db(instance_col):
    message = f"* Clear the DB *"
    print(Fore.GREEN)
    banner(message, border='*')
    print(f"This command empties the database.\n")
    try:
        x = instance_col.delete_many({})
    except Exception as e:
        print(f"An error has occurred: {e}")
    print(x.deleted_count, " documents deleted.")

def print_collections(my_db,instance_col):
    message = f"* Print DB Collections *"
    print(Fore.GREEN)
    banner(message, border='*')
    print(f"This command prints the database collection names: \n")
    col_list = my_db.list_collection_names()
    for col_name in col_list:
        print(col_name)

def menu():
    print(Fore.GREEN)
    print("1. Do a test insert to the DB")
    print("2. Clear the DB")
    print("3. Print the DB")
    print("4. Print collections")
    print("5. Exit ec2 mongo")


def main():
    welcomebanner()
    myclient, mydb, instance_col = set_db()
    mydict = set_test_dict()
    menu()
    print(Fore.GREEN)
    option = input("Enter the option: ")
    print(f"Option is: {option}")
    if option  == '1':
        x = insert_doc(instance_col,mydict)
        main()
    elif option == '2':
        clear_db(instance_col)
        main()
    elif option == '3':
        print_db(instance_col)
        main()
    elif option == '4':
       print_collections(mydb,instance_col)
       main()
    elif option == '5':
        exit_program()

    else:
        print("That is not a valid option.")
        main()

if __name__ == "__main__":
    main()
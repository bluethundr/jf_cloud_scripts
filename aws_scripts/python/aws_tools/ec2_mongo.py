#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# Import modules
import io, os, time, pandas, argparse, csv, pathlib
from socket import TCP_NODELAY
from pathlib import Path
from pandas import ExcelWriter
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from datetime import datetime
from colorama import init, Fore


## Initialize Colorama
init()

## Get MongoDB username and pass from environment variables
user_name = os.environ.get('MONGO_USER_NAME')
user_pass = os.environ.get('MONGO_USER_PASS')

### DB Functions
def connect_db():
    try:
        myclient = MongoClient(
                host = f"mongodb://{user_name}:{user_pass}@localhost:27017/admin",
                serverSelectionTimeoutMS = 3000 # 3 second timeout
            )
    except errors.ServerSelectionTimeoutError as e:
        # set the client instance to 'None' if exception
        myclient = None
        # catch pymongo.errors.ServerSelectionTimeoutError
        print ("pymongo ERROR:", e)
    return myclient

def set_db():
    myclient = connect_db()
    today = datetime.today()
    today = today.strftime("%m%d%Y")
    if myclient != None:
        mydb = myclient["aws_inventories"]
        mydb_name = "aws_inventories"
        insert_coll = "ec2_list_" + today
        insert_coll = mydb[insert_coll]
    return mydb, mydb_name, insert_coll

def choose_db():
    myclient = connect_db()
    today = datetime.today()
    today = today.strftime("%m%d%Y")
    if __name__ == "__main__":
        message = "* Choose a MongoDB Database *"
        print(Fore.CYAN)
        banner(message, "*")
        print(Fore.RESET)
    print(Fore.CYAN + "Available MongoDB Databases:")
    if myclient != None:
		# the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter  = 1
        for db in database_names:
            message = str(counter) + ". " + db
            print(message)
    print(f"There are {len(database_names)} databases.\n")
    print(f"Please select a database. Enter a number 1 through {len(database_names)}.")
    choice = input("Enter a number: ")
    if is_digit(choice) == True:
        if int(choice) > counter:
            print("Wrong selction.")
            choose_db()
        choice = int(choice)
        choice = choice - 1
        if myclient != None:
            mydb = myclient[database_names[choice]]
            mydb_name = database_names[choice]
            insert_coll = "ec2_list_" + today
            insert_coll = mydb[insert_coll]
            print(f"You've selected: {database_names[choice]}\n")
        else:
            print("Must enter a digit. Try again.\n")
    return mydb, mydb_name, insert_coll

### Utility Functions
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             EC2 MongoDB                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* EC2 MongoDB Operations Are Complete *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border="-"):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def menu():
    message = "Main Menu"
    banner(message)
    print(Fore.CYAN + "Your available actions: ")
    print("1. Create new MongoDB Database")
    print("2. Drop MongoDB Database")
    print("3. Do a test insert to the DB")
    print("4. Clear the DB")
    print("5. Remove accounts from the DB.")
    print("6. Print the DB")
    print("7. Print DB Names")
    print("8. Print collections")
    print("9. Export MongoDB to file")
    print("10. Print Reports")
    print("11. Exit ec2 mongo")
    print("\n")

def is_digit(check_input):
    if check_input.isdigit():
        return True
    return False

def initialize():
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # Set the input file
    aws_env_list = os.path.join('..', '..', 'source_files', 'aws_accounts_list', 'aws_accounts_list.csv')
    return today, aws_env_list

def read_account_info(aws_env_list):
    account_names = []
    account_numbers = []
    with open(aws_env_list) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
                account_name = str(row[0])
                account_number = str(row[1])
                account_names.append(account_name)
                account_numbers.append(account_number)
    return account_names, account_numbers

def select_account(options, aws_env_list):
    ## Select the account
    if options.account_name:
        aws_account = options.account_name
    else:
        print(Fore.YELLOW)
        aws_account = input("Enter the name of the AWS account you'll be working in: ")
        print(Fore.RESET)
    aws_account_number = find_account_number(aws_account, aws_env_list)
    return aws_account, aws_account_number

def find_account_number(aws_account,aws_env_list):
    account_names, account_numbers = read_account_info(aws_env_list)
    for (my_aws_account, my_aws_account_number) in zip(account_names, account_numbers):
        if my_aws_account == aws_account:
            aws_account_number = my_aws_account_number
        else:
            aws_account_number = None
    if aws_account ==  "all":
        aws_account_number = '1234567891011'
    return aws_account_number

def create_directories():
    ## Set source and output file directories
    source_files_path = Path('..', '..', 'source_files', 'aws_accounts_list')
    output_files_path = Path('..', '..', 'output_files', 'aws_instance_list')

    os.makedirs(source_files_path, exist_ok=True)
    os.makedirs(output_files_path, exist_ok=True)

    # Create output subdirectories
    folders = ['csv','excel','html', 'json']
    for folder in folders:
        full_path = os.path.join(output_files_path,folder)
        os.makedirs(full_path, exist_ok=True)

def set_test_dict():
    mydict = { "AWS Account": "company-lab", "Account Number": "12345678910", "Name": "bastion001",
"Instance ID": "i-07aaef3b7167d592a", "AMI ID": "ami-07fd81f1ecf6cf387", "Volumes": "vol-09d6d898db4af132a",
"Private IP": "10.238.3.165", "Public IP": "xx.xx.xx.xx", "Private DNS": "ip-10-238-3-165.ec2.internal",
"Availability Zone": "us-east-1a", "VPC ID": "vpc-00de11103235ec567", "Type": "t3.small", "Key Pair Name": "ccmi-vzn-int01", "Instance State": "running", "Launch Date": "September 10 2019"}
    return mydict

## Used by ec2_list_instances only. Not in a menu.
def delete_from_collection(aws_account_number):
    _, _, insert_coll = set_db()
    if __name__ == "__main__":
        message = f"* Clear old entries *"
        banner(message, border="*")
        print(f"This command clears old entries the database.\n")
        aws_account_number = input("Enter an AWS account number: ")
    try:
        #insert_coll.remove({"Account Number": aws_account_number});
        insert_coll.delete_many({"Account Number": aws_account_number})
    except Exception as e:
        print(f"An error has occurred: {e}")

# CLI Arguments
def arguments():
    parser = argparse.ArgumentParser(description="This is a program that provides a text interface to MongoDB.")

    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = "?",
    help = "Name of the AWS account you'll be working in")

    options = parser.parse_args()
    return options

# 1. Create new MongoDB Database
def create_mongodb(mydict):
    myclient = connect_db()
    message = f"* Create new MongoDB *"
    banner(message, border="*")
    print("\n")
    newdb = input("Enter the name of a new mongo database: ")
    dblist = myclient.list_database_names()
    if newdb in dblist:
        print("The database exists.")
        main()
    else:
        try:
            if myclient != None:
                mydb = myclient[newdb]
                mycol = mydb["testColumn"]
                mycol.insert_one(mydict)
                message = f"Succeeded in creating: {newdb}"
                banner(message)
        except Exception as e:
            print(f"MongoDB Database creation failed with: {e}")

# 2. Drop MongoDB Database
def drop_mongodb():
    message = "* Drop MongoDB *"
    banner(message, "*")
    myclient = connect_db()
    today = datetime.today()
    today = today.strftime("%m%d%Y")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter = 1
        for db in database_names:
            message = str(counter) + ". " + db
            print(message)
            counter = counter + 1
        print ("There are", len(database_names), "databases.\n")
        db_names_before_drop = myclient.list_database_names()
        print ("db count BEFORE drop:", len(db_names_before_drop))
        print(f"Please select a database. Enter a number 1 through {len(database_names)}.")
        choice = input("Enter a number: ")
        if is_digit(choice) == True:
            if int(choice) > counter:
                print("Wrong selection.")
                set_db()
            choice = int(choice)
            choice = choice - 1
            dropdb = myclient[database_names[choice]]
            insert_coll = "ec2_list_" + today
            insert_coll = dropdb[insert_coll]
            print(f"You've selected: {database_names[choice]}\n")
        else:
            print("Must enter a digit. Try again.\n")
        # check if a collection exists
        col_exists = insert_coll in dropdb.list_collection_names()
        print ("Some Collection exists:", col_exists) # will print True or False
        # call MongoDB client object"s drop_database() method to delete a db
        myclient.drop_database(dropdb) # pass db name as string
        time.sleep(5)
        # get all of the database names
        db_names_after_drop = myclient.list_database_names()
        print ("db count AFTER drop:", len(db_names_before_drop))
        diff = len(db_names_before_drop) - len(db_names_after_drop)
        print ("difference:", diff)

# 3. Insert MongoDB Collection
def insert_coll(mydict):
    _, _, insert_coll = set_db()
    instance_doc = ''
    try:
        mydict["_id"] = ObjectId()
        instance_doc = insert_coll.insert_one(mydict)
    except Exception as e:
        print(f"An error occurred: {e}")
    if __name__ == "__main__":
        message = "* MongoDB Insert Document *"
        banner(message, "*")
        message = f"MongoDB record inserted: {instance_doc.inserted_id}"
        banner(message)
    return instance_doc

# 4. Clear the DB
def clear_db():
    _, _, insert_coll = set_db()
    message = f"* Clear the DB *"
    banner(message, border="*")
    print(f"This command empties the database.\n")
    try:
        x = insert_coll.delete_many({})
    except Exception as e:
        print(f"An error has occurred: {e}")
    print(x.deleted_count, "documents deleted.")

# 5. Remove accounts from DB
def print_db_names():
    myclient = connect_db()
    message = f"* Print DB Names *"
    banner(message, border="*")
    print("The database names are:")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter = 1
        for db in database_names:
            message = str(counter) + ". " + db
            print(message)
            counter = counter + 1
        print ("There are", len(database_names), "databases.")

# 6. MongoDB Select All
def mongo_select_all():
    _, mydb_name, insert_coll = set_db()
    instance_list = list(insert_coll.find())
    if __name__ == "__main__":
        message = f"* Print DB Documents in {mydb_name} *"
        banner(message, border="*")
        print("\n")
        if not instance_list:
            message = f"The database: {mydb_name} has no entries."
            banner(message)
        else:
            message = f"The databse: {mydb_name} has {len(instance_list)} entries."
            for data in instance_list:
                print(data)
    print("\n")
    return instance_list

# 7. Print DB Names
def print_db_names():
    myclient = connect_db()
    message = f"* Print DB Names *"
    banner(message, border="*")
    print("The database names are:")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter = 1
        for db in database_names:
            message = str(counter) + ". " + db
            print(message)
            counter = counter + 1
        print ("There are", len(database_names), "databases.")

# 8 Print Collections
def print_collections():
    myclient = connect_db()
    print(myclient)
    time.sleep(10)
    message = f"* Print DB Collections *"
    banner(message, border="*")
    print(f"This command prints the database collection names.\n")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        print ("There are", len(database_names), "databases.")
        for db_num, db in enumerate(database_names):
            print ("\nGetting collections for database:", db, "--", db_num)
            collection_names = myclient[db].list_collection_names()
            print ("The MongoDB database returned", len(collection_names), "collections.")
            # iterate over the list of collection names
            for coll_num, coll in enumerate(collection_names):
                print (coll, "--", coll_num)

# 9. Export Mongo DB to File
def mongo_export_to_file(interactive, aws_account, aws_account_number,insert_coll=None,date=None):
    print(Fore.CYAN)
    if __name__ == "__main__":
        message = "* Export MongoDB to File *"
        banner(message, "*")
    create_directories()
    if date == None:
        format= "%m-%d-%Y"
        today = datetime.today()
        today = today.strftime(format)
        date = today
    else:
        format= "%m-%d-%Y"
        date = datetime.strptime(date,"%m%d%Y")
        date = date.strftime(format)
    if not insert_coll:
        _, _, insert_coll = set_db()
    # make an API call to the MongoDB server
    if interactive == 0:
        mongo_docs = insert_coll.find({})
    else:
        mongo_docs = insert_coll.find({"Account Number": aws_account_number})
    # Convert the mongo docs to a DataFrame
    docs = pandas.DataFrame(mongo_docs)
    # Discard the Mongo ID for the documents
    try:
        docs.pop("_id")
    except Exception as e:
        pass
    if __name__ == "__main__":
        print("Choose a file format")
        print("1. CSV")
        print("2. JSON")
        print("3. HTML")
        print("4. Excel")
        choice = input("Enter a number 1-4: ")
        choice = int(choice)
    else:
        choice = 1
    if choice == 1:
        # Set the CSV output directory
        output_dir = os.path.join("..", "..", "output_files", "aws_instance_list", "csv", "")
        if interactive == 1:
            output_file = os.path.join(output_dir, "aws-instance-list-" + aws_account + "-" + date +".csv")
            output_file_name = "aws-instance-list-" + aws_account + "-" + date +".csv"
        else:
            output_file = os.path.join(output_dir, "aws-instance-master-list-" + date +".csv")
        # export MongoDB documents to a CSV file, leaving out the row "labels" (row numbers)
        try:
            docs.to_csv(output_file, sep=",", index=False) # CSV delimited by commas
        except Exception as e:
            print(f"An exception has occurred: {e}.\nClose the file and try again!")
            mongo_export_to_file(interactive, aws_account, aws_account_number,insert_coll=None,date=None)
        path = pathlib.Path(output_file)
        if path.exists():
            if interactive == 1:
                output_file_name = "aws-instance-list-" + aws_account + "-" + date +".csv"
            else:
                output_file_name = "aws-instance-master-list-" + date +".csv"
            message = f"A CSV file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The CSV file has not been created.")
    elif choice == 2:
        # Set the JSON output directory
        output_dir = os.path.join("..", "..", "output_files", "aws_instance_list", "json", "")
        if interactive == 1:
            output_file = os.path.join(output_dir, "aws-instance-list-" + aws_account + "-" + date +".json")
        else:
            output_file = os.path.join(output_dir, "aws-instance-master-list-" + date +".json")
        # export MongoDB documents to a CSV file, leaving out the row "labels" (row numbers)
        try:
            docs.to_json(output_file)
        except Exception as e:
            print(f"An exception has occurred: {e}.\nClose the file and try again!")
            mongo_export_to_file(interactive, aws_account, aws_account_number,insert_coll=None,date=None)
        path = pathlib.Path(output_file)
        if path.exists():
            if interactive == 1:
                output_file_name = "aws-instance-list-" + aws_account + "-" + date +".json"
            else:
                output_file_name = "aws-instance-master-list-" + date +".json"
            message = f"A JSON file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The JSON file has not been created.")
    elif choice == 3:
        html_str = io.StringIO()
        # export as HTML
        docs.to_html(
        buf=html_str,
        classes="table table-striped"
        )
        # Set the HTML output directory
        output_dir = os.path.join("..", "..", "output_files", "aws_instance_list", "html", "")
        if interactive == 1:
            output_file = os.path.join(output_dir, "aws-instance-list-" + aws_account + "-" + date +".html")
        else:
            output_file = os.path.join(output_dir, "aws-instance-master-list-" + date + ".html")
        # save the MongoDB documents as an HTML table
        try:
            docs.to_html(output_file)
        except Exception as e:
            print(f"An exception has occurred: {e}.\nClose the file and try again!")
            mongo_export_to_file(interactive, aws_account, aws_account_number,insert_coll=None,date=None)
        path = pathlib.Path(output_file)
        if path.exists():
            if interactive == 1:
                output_file_name = "aws-instance-list-" + aws_account + "-" + date +".html"
            else:
                output_file_name = "aws-instance-master-list-" + date +".html"
            message = f"An HTML file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The HTML file has not been created.")
    elif choice == 4:
        # Set the Excel output directory
        output_dir = os.path.join("..", "..", "output_files", "aws_instance_list", "excel", "")
        time.sleep(5)
        if interactive == 1:
            output_file = os.path.join(output_dir, "aws-instance-list-" + aws_account + "-" + date + ".xlsx")
        else:
            output_file = os.path.join(output_dir, "aws-instance-master-list-" + date + ".xlsx")
        # export MongoDB documents to a Excel file, leaving out the row "labels" (row numbers)
        try:
            writer = ExcelWriter(output_file)
            docs.to_excel(writer,"EC2 List",index=False)
            writer.save()
            writer.close()
        except Exception as e:
            print(f"An exception has occurred: {e}.\nClose the file and try again!")
            mongo_export_to_file(interactive, aws_account, aws_account_number,insert_coll=None,date=None)
        path = pathlib.Path(output_file)
        if path.exists():
            if interactive == 1:
                output_file_name = "aws-instance-list-" + aws_account + "-" + date +".xlsx"
            else:
                output_file_name = "aws-instance-master-list-" + date +".xlsx"
            message = f"An Excel file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The Excel file has not been created.")
    if __name__ == "__main__":
        exit = input("Exit program (y/n): ")
        if exit.lower() == "y" or exit.lower() == "yes":
            exit_program()
        else:
            main()

# 10. Print Reports
def print_reports(interactive,aws_account,aws_account_number):
    print(Fore.CYAN)
    if __name__ == "__main__":
        message = "* Print Reports *"
        banner(message, "*")

    inputDate = input("Enter the date in format 'dd/mm/yyyy': ")
    month,day,year = inputDate.split('/')
    isValidDate = True
    try:
        datetime(int(year),int(month),int(day))
    except ValueError :
        isValidDate = False
        print("Invalid date. Try")
        print_reports(interactive,aws_account,aws_account_number)

    if(isValidDate) :
        print(f"Input date is valid: {inputDate}")
        format= "%m%d%Y"
        inputDate = datetime.strptime(inputDate,"%m/%d/%Y")
        inputDate = inputDate.strftime(format)
    else:
        print(f"Input date is not valid: {inputDate}")
        print_reports(interactive,aws_account,aws_account_number)
    myclient = connect_db()
    if myclient != None:
        mydb = myclient["aws_inventories"]
        try:
            insert_coll = "ec2_list_" + inputDate
            collection_names = mydb.list_collection_names()
            if insert_coll not in collection_names:
                print(f"Collection name: {insert_coll} does not exist in DB. Try again!")
                print_reports(interactive,aws_account,aws_account_number)
            else:
                insert_coll = mydb[insert_coll]
        except Exception as e:
            print(f"An error has occurred: {e}")
    mongo_export_to_file(interactive, aws_account, aws_account_number,insert_coll,inputDate)

# Choice 11. Exit ec2 Mongo
def exit_program():
    endbanner()
    exit()

### Main Function
def main():
    options = arguments()
    welcomebanner()
    mydict = set_test_dict()
    if __name__ == "__main__":
        print(Fore.YELLOW)
        aws_accounts_answer = input("Work in one or all accounts: ")
        print(Fore.RESET)
        # Set interacive variable to indicate one or many accounts
        if aws_accounts_answer.lower() == "one" or aws_accounts_answer.lower() == "1":
            interactive = 1
        else:
            interactive = 0
        aws_account = ''
        _, aws_env_list = initialize()
        menu()
        option = input("Enter the option: ")
        option = int(option)
        # 1. Create a MongoDB database
        if option == 1:
            create_mongodb(mydict)
            main()
        # 2. Drop a MongoDB Database
        elif option == 2:
            drop_mongodb()
            main()
        # 3. Do a test insert to the DB
        elif option  == 3:
            insert_coll(mydict)
            main()
        # 4. Clear the DB"
        elif option == 4:
            clear_db()
            main()
        # 5. Remove accounts from the DB.
        elif option == 5:
            _, aws_account_number = select_account(options, aws_env_list)
            delete_from_collection(aws_account_number)
            main()
        # 6. Print the DB
        elif option == 6:
            mongo_select_all()
            main()
        # 7. Print DB Names
        elif option == 7:
            print_db_names()
            main()
        # 8. Print collections
        elif option == 8:
            print_collections()
            main()
        # 9. Export MongoDB to file
        elif option == 9:
            if aws_accounts_answer == "all":
                aws_account = "all"
                aws_account_number = "123456789101"
            else:
                aws_account, aws_account_number = select_account(options, aws_env_list)
            mongo_export_to_file(interactive, aws_account, aws_account_number)
            main()
        # 10 Print Reports
        elif option == 10:
            if aws_accounts_answer == "all":
                aws_account = "all"
                aws_account_number = "123456789101"
                print_reports(interactive,aws_account,aws_account_number)
            else:
                pass
                aws_account, aws_account_number = select_account(options, aws_env_list)
                print_reports(interactive,aws_account,aws_account_number)
        # 11. Exit ec2 mongo
        elif option == 11:
            exit_program()
        # Invalid Input
        else:
            message = "That is not a valid option."
            banner(message)
            main()

### Run locally
if __name__ == "__main__":
    main()
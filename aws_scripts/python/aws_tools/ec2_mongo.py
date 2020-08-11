#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# Import module
import io
import os
import time
import pymongo
import pandas
import argparse
import numpy as np
from pandas import ExcelWriter, ExcelFile
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from datetime import datetime
from colorama import init, Fore
from collections import OrderedDict
init()

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

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

def exit_program():
    endbanner()
    exit()

def is_digit(check_input):
    if check_input.isdigit():
        return True
    return False

def arguments():
    parser = argparse.ArgumentParser(description='This is a program that provides a text interface to MongoDB.')

    parser.add_argument(
    "-n",
    "--account_name",
    type = str,
    default = None,
    nargs = '?',
    help = "Name of the AWS account you'll be working in")

    options = parser.parse_args()
    return options

def set_test_dict():
    mydict = { "AWS Account": "company-lab", "Account Number": "12345678910", "Name": "bastion001",
"Instance ID": "i-07aaef3b7167d592a", "AMI ID": "ami-07fd81f1ecf6cf387", "Volumes": "vol-09d6d898db4af132a",
"Private IP": "10.238.3.165", "Public IP": "xx.xx.xx.xx", "Private DNS": "ip-10-238-3-165.ec2.internal",
"Availability Zone": "us-east-1a", "VPC ID": "vpc-00de11103235ec567", "Type": "t3.small", "Key Pair Name": "ccmi-vzn-int01", "Instance State": "running", "Launch Date": "September 10 2019"}
    return mydict

def connect_db():
    try:
        myclient = MongoClient(
                host = "mongodb://localhost:27017/",
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
    today = today.strftime("%m-%d-%Y")
    if __name__ == '__main__':
        message = "Select Database"
        banner(message)
        print(Fore.CYAN + "Available MongoDB Databases:")
        if myclient != None:
            # the list_database_names() method returns a list of strings
            database_names = myclient.list_database_names()
            counter = 1
            for db in database_names:
                message = str(counter) + '. ' + db
                print(message)
                counter = counter + 1
        print ("There are", len(database_names), "databases.\n")
        print(f"Please select a database. Enter a number 1 through {len(database_names)}.")
        choice = input("Enter a number: ")
        if is_digit(choice) == True:
            if int(choice) > counter:
                print("Wrong selection.")
                set_db()
            choice = int(choice)
            choice = choice - 1
            mydb = myclient[database_names[choice]]
            mydb_name = database_names[choice]
            instance_col = 'ec2_list-' + today
            instance_col = mydb[instance_col]
            print(f"You've selected: {database_names[choice]}\n")
        else:
            print("Must enter a digit. Try again.\n")
    else:
        mydb = myclient["aws_inventories"]
        mydb_name = 'aws_inventories'
        instance_col = 'ec2_list-' + today
        instance_col = mydb[instance_col]
    return mydb, mydb_name, instance_col

def create_mongodb(mydict):
    myclient = connect_db()
    if __name__ == '__main__':
        message = f"* Create new MongoDB *"
        banner(message, border='*')
        print('\n')
    newdb = input("Enter the name of a new mongo database: ")
    dblist = myclient.list_database_names()
    if newdb in dblist:
        print("The database exists.")
        main()
    else:
        try:
            mydb = myclient[newdb]
            mycol = mydb["testColumn"]
            x = mycol.insert_one(mydict)
            message = f"Succeeded in creating: {newdb}"
            banner(message)
        except Exception as e:
            print(f"MongoDB Database creation failed with: {e}")

def drop_mongodb():
    myclient = connect_db()
    today = datetime.today()
    today = today.strftime("%m%d%Y")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter = 1
        for db in database_names:
            message = str(counter) + '. ' + db
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
        print(dropdb)
        dropdb_name = database_names[choice]
        instance_col = 'ec2List-' + today
        instance_col = dropdb[instance_col]
        print(f"You've selected: {database_names[choice]}\n")
    else:
        print("Must enter a digit. Try again.\n")
    # check if a collection exists
    col_exists = instance_col in dropdb.list_collection_names()
    print ("Some Collection exists:", col_exists) # will print True or False
    # call MongoDB client object's drop_database() method to delete a db
    myclient.drop_database(dropdb) # pass db name as string
    # get all of the database names
    db_names_after_drop = myclient.list_database_names()
    print ("db count AFTER drop:", len(db_names_before_drop))
    diff = len(db_names_before_drop) - len(db_names_after_drop)
    print ("difference:", diff)

def insert_doc(mydict):
    mydb, mydb_name, instance_col = set_db()
    mydict['_id'] = ObjectId()
    instance_doc = instance_col.insert_one(mydict)
    if __name__ == '__main__':
        message = "* MongoDB Insert Document *"
        banner(message, "*")
        message = f"MongoDB record inserted: {instance_doc.inserted_id}"
        banner(message)
    return instance_doc

def mongo_select_all():
    mydb, mydb_name, instance_col = set_db()
    instance_list = list(instance_col.find())
    if __name__ == '__main__':
        message = f"* Print DB Documents in {mydb_name} *"
        banner(message, border='*')
        print('\n')
        if not instance_list:
            message = f"The database: {mydb_name} has no entries."
            banner(message)
        else:
            message = f"The databse: {mydb_name} has {len(instance_list)} entries."
            for data in instance_list:
                print(data)
    print("\n")
    return instance_list

def mongo_export_to_file(interactive, aws_account):
    time.sleep(5)
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    _, _, instance_col = set_db()
    # make an API call to the MongoDB server
    mongo_docs = instance_col.find()

    # Convert the mongo docs to a DataFrame
    docs = pandas.DataFrame(mongo_docs)
    # Discard the Mongo ID for the documents
    docs.pop("_id")
    if __name__ == '__main__':
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
        if __name__ == '__main__':
            # export MongoDB documents to CSV
            csv_export = docs.to_csv(sep=",") # CSV delimited by commas
            print ("\nCSV data:", csv_export)
        # Set the CSV output directory
        output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'csv', '')
        if interactive == 1:
            output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.csv')
        else:
            output_file = os.path.join(output_dir, 'aws-instance-master-list' + today +'.csv')

        # export MongoDB documents to a CSV file, leaving out the row "labels" (row numbers)
        docs.to_csv(output_file, ",", index=False) # CSV delimited by commas
    elif choice == 2:
        if __name__ == '__main__':
            json_export = docs.to_json() # return JSON data
            print ("\nJSON data:", json_export)
        # Set the JSON output directory
        output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'json', '')
        if interactive == 1:
            output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.json')
        else:
            output_file = os.path.join(output_dir, 'aws-instance-master-list' + today +'.json')
        # export MongoDB documents to a CSV file, leaving out the row "labels" (row numbers)
        docs.to_json(output_file)
    elif choice == 3:
        html_str = io.StringIO()
        # export as HTML
        docs.to_html(
        buf=html_str,
        classes='table table-striped'
        )
        if __name__ == '__main__':
            # print out the HTML table
            print (html_str.getvalue())
        # Set the HTML output directory
        output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'html', '')
        if interactive == 1:
            output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.html')
        else:
            output_file = os.path.join(output_dir, 'aws-instance-master-list' + today + '.html')
        # save the MongoDB documents as an HTML table
        docs.to_html(output_file)
    elif choice == 4:
        # Set the Excel output directory
        output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'excel', '')
        time.sleep(5)
        if interactive == 1:
            output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today + '.xlsx')
        else:
            output_file = os.path.join(output_dir, 'aws-instance-master-list' + today + '.xlsx')
        # export MongoDB documents to a Excel file, leaving out the row "labels" (row numbers)
        writer = ExcelWriter(output_file)
        docs.to_excel(writer,'EC2 List',index=False)
        writer.save()

def clear_db():
    mydb, mydb_name, instance_col = set_db()
    message = f"* Clear the DB *"
    banner(message, border='*')
    print(f"This command empties the database.\n")
    try:
        x = instance_col.delete_many({})
    except Exception as e:
        print(f"An error has occurred: {e}")
    print(x.deleted_count, "documents deleted.")

def print_db_names():
    myclient = connect_db()
    message = f"* Print DB Names *"
    banner(message, border='*')
    print("The database names are:")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter = 1
        for db in database_names:
            message = str(counter) + '. ' + db
            print(message)
            counter = counter + 1
        print ("There are", len(database_names), "databases.")

def print_collections():
    myclient = connect_db()
    message = f"* Print DB Collections *"
    banner(message, border='*')
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
            for col_num, col in enumerate(collection_names):
                print (col, "--", col_num)

def menu():
    message = "Main Menu"
    banner(message)
    print(Fore.CYAN + "Your available actions: ")
    print("1. Create new MongoDB Database")
    print("2. Drop MongoDB Database")
    print("3. Do a test insert to the DB")
    print("4. Clear the DB")
    print("5. Print the DB")
    print("6. Print DB Names")
    print("7. Print collections")
    print("8. Export MongoDB to file")
    print("9. Exit ec2 mongo")
    print("\n")


def main():
    options = arguments()
    welcomebanner()
    mydict = set_test_dict()
    if __name__ == '__main__':
        interactive = 1
    ### Interactive == 1  - user specifies an account
    if interactive == 1:
        ## Select the account
        if options.account_name:
            aws_account = options.account_name
        else:
            print(Fore.YELLOW)
            aws_account = input("Enter the name of the AWS account you'll be working in: ")
            print(Fore.RESET)
    menu()
    option = input("Enter the option: ")
    print(f"Option is: {option}\n")
    # 1. Create a MongoDB database
    if option == '1':
        create_mongodb(mydict)
        main()
    # 2. Drop a MongoDB Database
    elif option == '2':
        drop_mongodb()
        main()
    # 3. Do a test insert to the DB
    elif option  == '3':
        x = insert_doc(mydict)
        main()
    # 4. Clear the DB"
    elif option == '4':
        clear_db()
        main()
    # 5. Print the DB
    elif option == '5':
        mongo_select_all()
        main()
    # 6. Print DB Names
    elif option == '6':
       print_db_names()
       main()
    # 7. Print collections
    elif option == '7':
       print_collections()
       main()
    # 8. Export MongoDB to file
    elif option == '8':
        mongo_export_to_file(interactive, aws_account)
        main()
    # 9. Exit ec2 mongo
    elif option == '9':
        exit_program()
    # Invalid Input
    else:
        message = "That is not a valid option."
        banner(message)
        main()

if __name__ == "__main__":
    main()
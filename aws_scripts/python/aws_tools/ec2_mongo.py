#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# Import modules
import time
import pymongo
import pandas
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from datetime import datetime
from colorama import init, Fore
from pprint import pprint
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

def set_test_dict():
    mydict = { "AWS Account": "ccmi-verizon-lab", "Account Number": "046480487130", "Name": "bastion001",
"Instance ID": "i-07aaef3b7167d592a", "AMI ID": "ami-07fd81f1ecf6cf387", "Volumes": "vol-09d6d898db4af132a",
"Private IP": "10.238.3.165", "Public IP": "3.227.224.221", "Private DNS": "ip-10-238-3-165.ec2.internal",
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
    message = "* Create MongoDB Database *"
    banner(message, "*")
    newdb = input("Enter a new database name: ")
    if myclient != None:
        dblist = myclient.list_database_names()
        if newdb in dblist:
            print("The database exists.")
        else:
            try:
                mydb = myclient[newdb]
                collection = mydb['test-collection']
                x = collection.insert_one(mydict)
            except Exception as e:
                print(Fore.RED + f"Database not created: {newdb} due to: {e}")
                main()

    print("The current list of database names is:")
    if myclient != None:
        # the list_database_names() method returns a list of strings
        database_names = myclient.list_database_names()
        counter = 1
        for db in database_names:
            message = str(counter) + '. ' + db
            print(message)
            counter = counter + 1
        print ("There are", len(database_names), "databases.")

def drop_mongodb():
    myclient = connect_db()
    message = "* Drop MongoDB Database *"
    banner(message, "*")
    # get all of the database names
    db_names_before_drop = myclient.list_database_names()
    print ("db count BEFORE drop:", len(db_names_before_drop))
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
        dropdb = myclient[database_names[choice]]
        dropdb_name = database_names[choice]
        print(f"You've selected: {database_names[choice]}\n")
    else:
        print("Must enter a digit. Try again.\n")
    try:
        db = myclient.newdb
    except Exception as e:
        print(f"A pymongo error has occurred: {e}")

    # check the collection names on the database
    col_list = db.list_collection_names()
    print ("collections on the unwanted db:", col_list)

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
    print("8. Exit ec2 mongo")
    print("\n")


def main():
    welcomebanner()
    mydict = set_test_dict()
    menu()
    option = input("Enter the option: ")
    print(f"Option is: {option}\n")
    if option == '1':
        create_mongodb(mydict)
        main()
    elif option == '2':
        drop_mongodb()
        main()
    # 1. Do a test insert to the DB
    elif option  == '3':
        x = insert_doc(mydict)
        main()
    # 2. Clear the DB"
    elif option == '4':
        clear_db()
        main()
    # 3. Print the DB
    elif option == '5':
        mongo_select_all()
        main()
    # 4. Print DB Names
    elif option == '6':
       print_db_names()
       main()
    # 5. Print collections
    elif option == '7':
       print_collections()
       main()
    # 6. Exit ec2 mongo
    elif option == '8':
        exit_program()
    else:
        message = "That is not a valid option."
        banner(message)
        main()

if __name__ == "__main__":
    main()
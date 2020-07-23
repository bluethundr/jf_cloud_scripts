#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# Import modules
import os
import time
import pymongo
import pandas
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
            mycol = mydb["test_column"]
            x = mycol.insert_one(mydict)
            message = f"Succeeded in creating: {newdb}"
            banner(message)
        except Exception as e:
            print(f"MongoDB Database creation failed with: {e}")

def drop_mongodb():
    myclient = connect_db()
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
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
        instance_col = 'ec2_list-' + today
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
    if __name__ == '__main__':
        print("Available formats:")
        print("1. JSON")
        print("2. CSV")
        print("3. HTML")
        choice = input("Please select a number 1-3: ")
    else:
        choice = '2'
    if is_digit(choice) == True:
        if int(choice) > 3:
            print("Wrong selection.")
            #mongo_export_to_file(interactive, aws_account)
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    #mydb, mydb_name, instance_col = set_db()
    _, _, instance_col = set_db()
    if __name__ == '__main__':
            message = f"* Export MongoDB to File *"
            banner(message, border='*')
    # start time of script
    start_time = time.time()

    # make an API call to the MongoDB server
    #cursor = instance_col.find()
    # extract the list of documents from cursor obj
    #mongo_docs = list(cursor)
    mongo_docs = instance_col.find()

    if __name__ == '__main__':
        print ("total docs:", len(list(mongo_docs)))



    # iterate over the list of MongoDB dict documents
    for num, doc in enumerate(mongo_docs):
        # Keep the original order
        # convert ObjectId() to str

        # create an empty DataFrame for storing documents
        #docs = pandas.DataFrame(columns=[])
        docs = pandas.DataFrame(mongo_docs)

        # Discard the Mongo ID for the documents
        docs.pop("_id")

        '''
        EXPORT THE MONGODB DOCUMENTS
        TO DIFFERENT FILE FORMATS
        '''
        if __name__ == '__main__':
            print ("\nexporting Pandas objects to different file types.")
            print ("DataFrame len:", len(docs))

        if choice == '1':
            # Output to JSON
            if interactive == 1:
                output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'json', '')
                output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.json')
                output_file_name = 'aws-instance-list-' + aws_account + '-' + today + '.json'
            else:
                output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'json', '')
                output_file = os.path.join(output_dir, 'aws-instance-master-list-' + today +'.json')

            # export the MongoDB documents as a JSON file
            docs.to_json(output_file)

            # have Pandas return a JSON string of the documents
            json_export = docs.to_json() # return JSON data
            if __name__ == '__main__':
                print ("\nJSON data:", json_export)

        elif choice == '2':
        # Export to CSV
            if interactive == 1:
                output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'csv', '')
                output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.csv')
                output_file_name = 'aws-instance-list-' + aws_account + '-' + today + '.csv'
            else:
                # Set the output file
                output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'csv', '')
                output_file = os.path.join(output_dir, 'aws-instance-master-list-' + today +'.csv')

            # export MongoDB documents to a CSV file
            docs.to_csv(output_file, ",", index=False)

            # export MongoDB documents to CSV
            csv_export = docs.to_csv(sep=",") # CSV delimited by commas
            if __name__ == '__main__':
                print ("\nCSV data:", csv_export)

        elif choice == '3':
            # create IO HTML string
            import io
            html_str = io.StringIO()

            # export as HTML
            docs.to_html(
            buf=html_str,
            classes='table table-striped'
            )

            if __name__ == '__main__':
                # print out the HTML table
                print (html_str.getvalue())

            # Output to HTML
            if interactive == 1:
                output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'html', '')
                output_file = os.path.join(output_dir, 'aws-instance-list-' + aws_account + '-' + today +'.html')
                output_file_name = 'aws-instance-list-' + aws_account + '-' + today + '.html'
            else:
                output_dir = os.path.join('..', '..', 'output_files', 'aws_instance_list', 'html', '')
                output_file = os.path.join(output_dir, 'aws-instance-master-list-' + today +'.html')

            # save the MongoDB documents as an HTML table
            docs.to_html(output_file)
            if __name__ == '__main__':
                print ("\n\ntime elapsed:", time.time()-start_time)
        else:
            Print("That is not a valid choice.")
            #mongo_export_to_file(interactive, aws_account)

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
    welcomebanner()
    mydict = set_test_dict()
    menu()
    interactive = 1
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
        if __name__ == '__main__':
            aws_account = 'jf-master-pd'
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

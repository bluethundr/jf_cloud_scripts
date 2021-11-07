#-------------------------------------------------------------------------------------------------------------------
# Import Block                                                                                                     #
#-------------------------------------------------------------------------------------------------------------------
import io,os,pandas,pathlib
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from pathlib import Path
from pandas import ExcelWriter
user_name = os.environ.get('MONGO_USER_NAME')
user_pass = os.environ.get('MONGO_USER_PASS')
#-------------------------------------------------------------------------------------------------------------------
# End Import Block                                                                                                 #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#  Utility Functions                                                                                              #
#-------------------------------------------------------------------------------------------------------------------    
def create_directories():
    ## Set source and output file directories
    source_files_path = Path('..', '..', 'source_files', 'gcp_accounts_list')
    output_files_path = Path('..', '..', 'output_files', 'gcp_instance_list')

    os.makedirs(source_files_path, exist_ok=True)
    os.makedirs(output_files_path, exist_ok=True)

    # Create output subdirectories
    folders = ['csv','excel','html','json']
    for folder in folders:
        full_path = os.path.join(output_files_path,folder)
        os.makedirs(full_path, exist_ok=True)

def exit_program():
    endbanner()
    exit()
#-------------------------------------------------------------------------------------------------------------------
#  End  Utility Functions                                                                                          #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#  Banner Functions                                                                                                #
#-------------------------------------------------------------------------------------------------------------------
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*  GCP MongoDB Functions  *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    # Print the end banner
    print(Fore.CYAN)
    message = "*  GCP MongoDB Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    # Generic banner function
    line = border * len(message)
    print(line)
    print(message)
    print(line)
#-------------------------------------------------------------------------------------------------------------------
#  End Banner                                                                                                      #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# MongoDB Functions                                                                                                #
#-------------------------------------------------------------------------------------------------------------------
def connect_db():
    try:
        myclient = MongoClient(
                host = f"mongodb://{user_name}:{user_pass}@localhost:27017/admin",
                serverSelectionTimeoutMS = 3000 # 3 second timeout
            )
    except errors.ServerSelectionTimeoutError as e:
        myclient = None
        attempts = 4
        for attempt in attempts:
            print(f"Attempt {attempt + 1} connecting to MongoDB.")
            connect_db()
        print(f"Cannot conect to MongoDB in 5 attempts")
    return myclient

def set_db(date):
    myclient = connect_db()
    if myclient != None:
        mydb = myclient["gcp_inventories"]
        insert_coll = "gcp_compute_list_" + date
        insert_coll = mydb[insert_coll]
    return mydb,insert_coll

def insert_coll(mydict,date):
    _, insert_coll = set_db(date)
    mydict["_id"] = ObjectId()
    instance_doc = insert_coll.insert_one(mydict)
    return instance_doc

def delete_from_collection(date):
    _, insert_coll = set_db(date)
    try:
        insert_coll.delete_many({})
    except Exception as e:
        pass
#-------------------------------------------------------------------------------------------------------------------
# End MongoDB Functions                                                                                            #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# Write Output Files                                                                                               #
#-------------------------------------------------------------------------------------------------------------------
def mongo_export_to_file(choice,insert_coll,date,today):
    # make an API call to the MongoDB server
    mongo_docs = insert_coll.find({})
    # Convert the mongo docs to a DataFrame
    docs = pandas.DataFrame(mongo_docs)
    # Create today string
    today = str(today).strip(' 00:00:00')
    # Discard the Mongo ID for the documents
    try:
        docs.pop("_id")
    except Exception as e:
        pass
    if choice == 1:
        # Set the CSV output directory
        output_dir = os.path.join("..", "..", "output_files", "gcp_instance_list", "csv", "")
        output_file = os.path.join(output_dir, "gcp-instance-master-list-" + today +".csv")
        # export MongoDB documents to a CSV file, leaving out the row "labels" (row numbers)
        try:
            docs.to_csv(output_file, ",", index=False)
        except Exception as e:
            mongo_export_to_file(choice,insert_coll,date,today)
        path = pathlib.Path(output_file)
        if path.exists():
            output_file_name = "gcp-instance-master-list-" + today +".csv"
            message = f"A CSV file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The CSV file has not been created.")
    elif choice == 2:
        # Set the JSON output directory
        output_dir = os.path.join("..", "..", "output_files", "gcp_instance_list", "json", "")
        output_file = os.path.join(output_dir, "gcp-instance-master-list-" + today + ".json")
        # export MongoDB documents to a JSON file, leaving out the row "labels" (row numbers)
        try:
            docs.to_json(output_file)
        except Exception as e:
            pass
        path = pathlib.Path(output_file)
        if path.exists():
            output_file_name = "gcp-instance-master-list-" + today + ".json"
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
        output_dir = os.path.join("..", "..", "output_files", "gcp_instance_list", "html", "")

        output_file = os.path.join(output_dir,"gcp-instance-master-list-" + today + ".html")
        output_file_name = 'gcp-instance-master-list-' + today + '.html'
        # save the MongoDB documents as an HTML table
        try:
            docs.to_html(output_file,index=False)
        except Exception as e:
            mongo_export_to_file(insert_coll,date,today)
        path = pathlib.Path(output_file)
        if path.exists():
            message = f"An HTML file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The HTML file has not been created.")
        return output_file
    elif choice == 4:
        # Set the Excel output directory
        output_dir = os.path.join("..", "..", "output_files", "gcp_instance_list", "excel", "")
        output_file = os.path.join(output_dir, "gcp-instance-master-list-" + today + ".xlsx")
        # export MongoDB documents to a Excel file, leaving out the row "labels" (row numbers)
        try:
            writer = ExcelWriter(output_file)
            docs.to_excel(writer,"GCP Instance List",index=False)
            writer.save()
            writer.close()
        except Exception as e:
            pass
        path = pathlib.Path(output_file)
        if path.exists():
            output_file_name = "gcp-instance-master-list-" + today +".xlsx"
            message = f"An Excel file has been created as: {output_file_name}"
            banner(message)
        else:
            print("The Excel file has not been created.")
#-------------------------------------------------------------------------------------------------------------------
# End Write Output Files                                                                                           #
#-------------------------------------------------------------------------------------------------------------------
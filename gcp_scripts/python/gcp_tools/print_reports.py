#-------------------------------------------------------------------------------------------------------------------
# Import Block                                                                                                     #
#-------------------------------------------------------------------------------------------------------------------
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from datetime import datetime
from dateutil.parser import parse
from colorama import init, Fore
from gcp_mongo import connect_db,mongo_export_to_file
from gcp_list_instances import initialize
#-------------------------------------------------------------------------------------------------------------------
# End Import Block                                                                                                 #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# Initialize the output with Colorama                                                                              #
#-------------------------------------------------------------------------------------------------------------------
init()
#-------------------------------------------------------------------------------------------------------------------
#  Banner Functions                                                                                                #
#-------------------------------------------------------------------------------------------------------------------
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*  Print Reports  *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    # Print the end banner
    print(Fore.CYAN)
    message = "*  Print Reports Operations Are Complete   *"
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
# Print Reports Function                                                                                           #
#-------------------------------------------------------------------------------------------------------------------
def print_reports():
    print(Fore.CYAN)
    if __name__ == "__main__":
        message = "* Print Reports *"
        banner(message, "*")
    choice = 4 # <-- Output to Excel
    inputDate = input("Enter the date in format 'mm/dd/yyyy': ")
    today = datetime.strptime(inputDate, "%m/%d/%Y")
    month,day,year = inputDate.split('/')
    isValidDate = True
    try:
        datetime(int(year),int(month),int(day))
    except ValueError :
        isValidDate = False
        print("Invalid date. Try again.")
        print_reports()

    if(isValidDate):
        print(f"Input date is valid: {inputDate}")
        format= "%m%d%Y"
        inputDate = datetime.strptime(inputDate,"%m/%d/%Y")
        inputDate = inputDate.strftime(format)
    else:
        print(f"Input date is not valid: {inputDate}")
        print_reports()
    myclient = connect_db()
    mydb = myclient["gcp_inventories"]
    insert_coll = "gcp_compute_list_" + inputDate
    collection_names = mydb.list_collection_names()
    if insert_coll not in collection_names:
        print(f"Collection name: {insert_coll} does not exist in the DB. Try again!")
        print_reports()
    else:
        insert_coll = mydb[insert_coll]
        mongo_export_to_file(choice,insert_coll,inputDate,today)
#-------------------------------------------------------------------------------------------------------------------
# End Print Reports Function                                                                                       #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# Main Funcion                                                                                                     #
#-------------------------------------------------------------------------------------------------------------------
def main():
    print_reports()

if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------------------------------------------
# End Main Funcion                                                                                                 #
#-------------------------------------------------------------------------------------------------------------------
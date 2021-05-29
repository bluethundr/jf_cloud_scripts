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

write confluence

#-------------------------------------------------------------------------------------------------------------------
# Import Block                                                                                                     #
#-------------------------------------------------------------------------------------------------------------------
import json,requests,keyring,getpass
from html import escape
from requests.auth import HTTPBasicAuth
from colorama import init, Fore
#-------------------------------------------------------------------------------------------------------------------
# End Import Block                                                                                                 #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# Set base URL and View URL variables                                                                              #
#-------------------------------------------------------------------------------------------------------------------
BASE_URL = "https://confluence.company.com/rest/api/content"
VIEW_URL = "https://confluence.company.com/pages/viewpage.action?pageId="
#-------------------------------------------------------------------------------------------------------------------
# END base URL and View URL variables                                                                              #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#  Banner Functions                                                                                                #
#-------------------------------------------------------------------------------------------------------------------
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
# Confluence Functions                                                                                             #
#-------------------------------------------------------------------------------------------------------------------
def get_login(username = None):
    if username is None:
        username = getpass.getuser()
    passwd = None
    if passwd is None:
        passwd = getpass.getpass()
        keyring.set_password('confluence_script', username, passwd)
    return (username, passwd)

def authenticate():
    auth = get_login()
    return auth

def get_page_ancestors(auth, pageid):
    # Get basic page information plus the ancestors property
    url = '{base}/{pageid}?expand=ancestors'.format(
        base = BASE_URL,
        pageid = pageid)
    r = requests.get(url, auth = auth)
    r.raise_for_status()
    return r.json()['ancestors']

def get_page_info(auth, pageid):
    url = '{base}/{pageid}'.format(
        base = BASE_URL,
        pageid = pageid)
    r = requests.get(url, auth = auth)
    r.raise_for_status()
    return r.json()

def write_data_to_confluence(auth, pageid,output_file,title = None):
    info = get_page_info(auth, pageid)
    with open(output_file, 'r') as htmlfile:
        html = htmlfile.read()
    ver = int(info['version']['number']) + 1
    ancestors = get_page_ancestors(auth, pageid)
    anc = ancestors[-1]
    del anc['_links']
    del anc['_expandable']
    del anc['extensions']
    if title is not None:
        info['title'] = title
    data = {
        'id' : str(pageid),
        'type' : 'page',
        'title' : info['title'],
        'version' : {'number' : ver},
        'ancestors' : [anc],
        'body'  : {
            'storage' :
            {
                'representation' : 'storage',
                'value' : str(html)
            }
        }
    }
    data = json.dumps(data)
    url = '{base}/{pageid}'.format(base = BASE_URL, pageid = pageid)
    try:
        r = requests.put(
            url,
            data = data,
            auth = auth,
            headers = { 'Content-Type' : 'application/json' }
        )
    except Exception as e:
        pass
    if r.status_code >= 400:
        print(f"HTTP Status Code: {r.status_code}")
        raise RuntimeError(r.content)
    else:
        message = f"Wrote {info['title']} version {ver}\nURL: {VIEW_URL}{pageid}"
        print(Fore.CYAN)
        banner(message, '*')
        print(Fore.RESET)
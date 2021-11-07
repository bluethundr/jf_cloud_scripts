#-------------------------------------------------------------------------------------------------------------------
# Import Block                                                                                                     #
#-------------------------------------------------------------------------------------------------------------------
import os,time,datetime,csv,googleapiclient.discovery
from datetime import datetime
from colorama import init, Fore
from os.path import basename
from pathlib import Path
from gcp_mongo import create_directories,set_db,insert_coll,delete_from_collection,mongo_export_to_file
#from write_confluence import authenticate,write_data_to_confluence
#-------------------------------------------------------------------------------------------------------------------
# End Import Block                                                                                                 #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# Initialize the output with Colorama                                                                              #
#-------------------------------------------------------------------------------------------------------------------
init()
#-------------------------------------------------------------------------------------------------------------------
#  Utility Functions                                                                                              #
#-------------------------------------------------------------------------------------------------------------------
def initialize():
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y") # <- Human friendly time for naming files
    date = datetime.today()
    date = date.strftime("%m%d%Y")  # <- Computer friendly time for use with MongoDB
    # Set the input file
    gcp_env_list = os.path.join('..', '..', 'source_files', 'gcp_projects_list.csv')
    # Set the zones list
    gcp_zones_list = os.path.join('..', '..', 'source_files', 'gcp_zones_list.txt')
    return today,date,gcp_env_list,gcp_zones_list
 
def delete_file(output_file):
    try:
        os.remove(output_file)
    except OSError:
        pass

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
    message = "*     List GCP Compute Instances     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    # Print the end banner
    print(Fore.CYAN)
    message = "*  List GCP Compute Instances Operations Are Complete  *"
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
#  Read Project Info                                                                                               #
#-------------------------------------------------------------------------------------------------------------------
def read_project_info(gcp_env_list):
    project_ids = []
    with open(gcp_env_list) as csv_file:
        try:
            csv_reader = csv.reader(csv_file)
        except Exception as e:
            print(f"A CSV error has occurred:")
        next(csv_reader)
        for row in csv_reader:
            project_id = str(row[0])
            project_ids.append(project_id)
    return project_ids
#-------------------------------------------------------------------------------------------------------------------
#  End Read Project Info                                                                                           #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#  Read Zone Info                                                                                                  #
#-------------------------------------------------------------------------------------------------------------------
def read_zone_info(gcp_zones_list):
    gcp_zones = []
    try:
        with open(gcp_zones_list) as text_file:
            zones = text_file.readlines()
            for zone in zones:
                gcp_zones.append(zone.strip())
    except Exception as e:
        print(f"A CSV error has occurred: {e} ")
    return gcp_zones
#-------------------------------------------------------------------------------------------------------------------
#  End Read Zone Info                                                                                              #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# List Instances Function                                                                                          #
#-------------------------------------------------------------------------------------------------------------------
def list_instances(compute,project_ids,gcp_zones,date):
    delete_from_collection(date)
    for project_id in project_ids:
        print(f"Project ID: {project_id}")
        for zone in gcp_zones:
            print(f"ZONE: {zone}")
            result = compute.instances().list(project=project_id, zone=zone, filter='status=running').execute()
            instance = result.get('items')
            #data = json.load(instance)
            #print(f"Data: {data}")
            if instance:
                try:
                    for item in instance:
                        instance_id = item['id']
                        name = item['name']
                        timestamp = item['creationTimestamp']
                        pretty_dt = timestamp
                        private_ip = item['networkInterfaces'][0]['networkIP']
                        machine_type = item['machineType']
                        machine_type = machine_type.split("/")[-1]
                        status = item['status']
                        zone = item['zone']
                        zone = zone.split("/")[-1]
                        subnetwork = item['networkInterfaces'][0]['subnetwork']
                        subnetwork = subnetwork.split("/")[-1]
                        instance_dict = {'Project ID': project_id, 'Instance ID': instance_id, 'Name': name,'Private IP': private_ip, 'Zone': zone, 'Subnet': subnetwork, 'Machine Type': machine_type, 'Status': status, 'Date Launched': pretty_dt,}
                        insert_coll(instance_dict,date)
                except Exception:
                    pass 
#-------------------------------------------------------------------------------------------------------------------
# End List Instances Function                                                                                      #
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
# Main Function                                                                                                    #
#-------------------------------------------------------------------------------------------------------------------
def main():
    welcomebanner()
    ### Begin variables
    #auth = authenticate()
    project_ids = ''
    compute = googleapiclient.discovery.build('compute', 'v1')
    choice = 3 # <- File format HTML
    today,date,gcp_env_list,gcp_zones_list = initialize()
    _, insert_coll = set_db(date)
    try:
        project_ids = read_project_info(gcp_env_list)
    except Exception as e:
        print(f"A CSV error has occurred: {e}")
    gcp_zones = read_zone_info(gcp_zones_list)
    pageid = 1164580700 # <-- Main page
    #pageid = 1166025346 # <-- Test page
    title = 'GCP Compute Instance Inventory'
    #title = 'GCP Compute Instance Inventory - Test'
    ### End variables
    ### Begin Functions
    create_directories()
    list_instances(compute,project_ids,gcp_zones,date)
    output_file = mongo_export_to_file(choice,insert_coll,date,today)
    #write_data_to_confluence(auth,pageid,output_file,title)
    time.sleep(5) # <-- Time delay is necessary or the file is deleted before it's written to confluence
    delete_file(output_file)
    endbanner()
    ### End Functions

if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------------------------------------------
# End Main Function                                                                                                #
#-------------------------------------------------------------------------------------------------------------------
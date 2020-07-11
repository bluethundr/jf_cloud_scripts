import pymongo

def set_db():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["aws_ec2_list"]
    mycol = mydb["ec2_instances"]
    return myclient, mydb, mycol

def set_dict():
    mydict = { "AWS Account": "ccmi-verizon-lab", "Account Number": "046480487130", "Name": "bastion001",
"Instance ID": "i-07aaef3b7167d592a", "AMI ID": "ami-07fd81f1ecf6cf387", "Volumes": "vol-09d6d898db4af132a", 
"Private IP": "10.238.3.165", "Public IP": "3.227.224.221", "Private DNS": "ip-10-238-3-165.ec2.internal", 
"Availability Zone": "us-east-1a", "VPC ID": "vpc-00de11103235ec567", "Type": "t3.small", "Key Pair Name": "ccmi-vzn-int01", "Instance State": "running", "Launch Date": "September 10 2019"}
    return mydict

def insert_col(mycol,mydict):
    x = mycol.insert_one(mydict)
    print(f"MongoDB record inserted: {x.inserted_id}")
    return x

def print_db(mycol):
    x = mycol.find()
    for data in x:
        print(data)

def delete_db(mycol):
    try:
        x = mycol.delete_many({})
    except Exception as e:
        print(f"An error has occurred: {e}")
    print(x.deleted_count, " documents deleted.")

def menu():
    print("1. Insert to the DB")
    print("2. Delete from the DB")
    print("3. Print the DB")

def main():
    myclient, mydb, mycol = set_db()
    mydict = set_dict()
    menu()
    option = input("Enter the option: ")
    print(f"Option is: {option}")
    if option  == '1':
        x = insert_col(mycol,mydict)
    elif option == '2':
        delete_db(mycol)
    elif option == '3':
        print_db(mycol)

if __name__ == "__main__":
    main()
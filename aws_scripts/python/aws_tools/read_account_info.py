from modules import *

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
from modules import *

def choose_accounts(aws_env_list):
    account_names = []
    account_numbers = []
    my_account_name = ''
    my_account_number = ''
    print(Fore.YELLOW)
    all_accounts_question = input("Loop through all accounts (one/some/all): ")
    if all_accounts_question.lower() == 'one':
        my_account_name = input("Enter the name of the AWS account you'll be working in: ")
        account_names, account_numbers = read_account_info(aws_env_list)
        for (aws_account, aws_account_number) in zip(account_names, account_numbers):
            if my_account_name == aws_account:
                my_account_number = aws_account_number
        account_names = []
        account_numbers = []
        account_names.append(my_account_name)
        account_numbers.append(my_account_number)
    elif all_accounts_question == 'some':
        my_account_names = input("Enter AWS account names separated by commas: ")
        my_account_names = my_account_names.split(",")
        my_account_numbers = []
        account_names, account_numbers = read_account_info(aws_env_list)
        for (aws_account, aws_account_number, my_account_name) in zip(account_names, account_numbers, my_account_names):
            if my_account_name == aws_account:
                my_account_number = aws_account_number
                my_account_numbers.append(my_account_number)
        account_names = my_account_names
        aws_account_numbers = my_account_numbers
    elif all_accounts_question == 'all':   
        account_names, account_numbers = read_account_info(aws_env_list)
    else:
        print("That is not a valid choice.")
    print(Fore.YELLOW)
    
    return account_names, account_numbers
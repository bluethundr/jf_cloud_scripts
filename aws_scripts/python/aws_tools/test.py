import datetime
def print_reports(interactive,aws_account,aws_account_number):
     #set_db(instance_col=None)
    inputDate = input("Enter the date in format 'mm/dd/yyyy': ")
    month,day,year = inputDate.split('/')
    isValidDate = True
    try:
        datetime(int(year), int(month), int(day))
    except ValueError :
        isValidDate = False
        print("Date is not valid.")
        time.sleep(10)
        print_reports(interactive,aws_account,aws_account_number)###

    if(isValidDate) :
        print(f"Input date is valid: {inputDate}")
        format= "%m%d%Y"
        inputDate = datetime.strptime(inputDate,"%m/%d/%Y")
        inputDate = inputDate.strftime(format)
        print("SUCCESS!!!")
    else:
        print(f"Input date is not valid: {inputDate}")
        print("FAILURE!!!")
        time.sleep(5)
        print_reports(interactive,aws_account,aws_account_number)
    #myclient = connect_db()
    #mydb = myclient["aws_inventories"]
    #instance_col = "ec2_list_" + inputDate
    #instance_col = mydb[instance_col]
    print_reports(interactive,aws_account,aws_account_number)
    #mongo_export_to_file(interactive, aws_account, aws_account_number,instance_col,date=inputDate)

interactive=1
aws_account='new'
aws_account_number='1234567789'
print_reports(interactive,aws_account,aws_account_number)
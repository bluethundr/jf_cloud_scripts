#!/usr/bin/env python3

import os
import mysql.connector
import csv
import time
import smtplib
import pandas as pd
import gzip
import contextlib
import io
from io import StringIO
from time import strftime
from contextlib import contextmanager
from mysql.connector import Error
from mysql.connector import errorcode
from dateutil.relativedelta import *
from datetime import datetime
from os.path import basename
from colorama import init, Fore
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

## Begin Utility Functions
# Initialize Colorama formatting
init()

def connect_to_db():
    mydb = mysql.connector.connect(user='admin', password='********',
                            host='127.0.0.1',
                            database='aws_bill')
    cursor = mydb.cursor()
    return cursor, mydb

## Provide session info to the functions based on AWS account
def initialize():
    print(Fore.YELLOW)
    print("Selecting company-bill or company-master will produce a report for all accounts.")
    aws_account = input("Enter the name of the AWS account you'll be working in: ")
    if aws_account.lower() == 'all':
        aws_account_number = ''
    else:
        aws_account_number = aws_accounts_to_account_numbers(aws_account)
    print(Fore.GREEN, "\n")
    print("**************************************************************")
    print("          Okay. Working in AWS account: %s                    " % aws_account)
    print("**************************************************************")
    # Set the date
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    return aws_account, aws_account_number, today

## Standard functions
def exit_program():
    endbanner()
    exit()
    
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    print('******************************************************')
    print('*             AWS Billing Operations                 *')
    print('******************************************************\n')
    time.sleep(5)

def endbanner():
    print(Fore.CYAN)
    print("*****************************************************")
    print("* AWS Billing Operations Are Complete               *")
    print("*****************************************************")


def choose_action():
    print(Fore.GREEN)
    print("*********************************************")
    print("*         Choose an Action                  *")
    print("*********************************************")
    print(Fore.YELLOW)
    print("These are the actions possible in AWS: ")
    print("1. Run the Report")
    print("2. Read AWS Bill")
    print("3. Read the CUR File")
    print("4. Write AWS Bill")
    print("5. Send Email")
    print("6. Recreate Table")
    print("7. Recreate CUR Table")
    print("8. Update Database To NULL")
    print("9. Set Default Engagement")
    print("10. Replace Bad Engagement")
    print("11. Replace Old Engagement")
    print("12. Exit Program")
    choice=input("Enter an action: ")
    return choice

def create_work_dir(work_dir):
    access_rights = 0o755
    try:  
        os.mkdir(work_dir)
    except OSError:  
        print ("The directory %s already exists" % work_dir + '\n')
    else:  
        print ("Successfully created the directory %s " % work_dir + '\n')

def table_name():
    table_type = input("Use a CUR file (y/n): ")
    if table_type.lower() == 'y' or table_type.lower() == 'yes':
        table_name = 'billing_info_cur'
        print('OK. Using the CUR table.')
    else:
        table_name = 'billing_info_dbr'
        print('OK. Using the DBR table.')
    

    test_table = input("Use a test table (Y/N): ")
    if test_table.lower() == 'y' or test_table.lower() == 'yes':
        table_name = table_name + '_test'
        print('OK. Using the test table.')
    print(f"Table name: {table_name}")
    return table_name

def aws_accounts_to_account_numbers(aws_account):
    switcher = {
        'company-lab': '123456789101',
        'company-bill': '123456789102',
        'company-stage': '123456789103',
        'company-dlab': '123456789104',
        'company-nonprod': '123456789105',
        'company-prod': '123456789106',
        'company-ksr-a': '123456789107',
        'company-ksr-b': '123456789108',
        'company-dsg-logging-admin': '123456789109',
        'company-dsg-logging-gov': '123456789110',
        'company-dsg-security-admin': '123456789111',
        'company-dsg-security-gov': '123456789112',
        'company-master': '12345678913',
        'company-transit-hub1': '123456789114',
        'company-transit-hub3': '123456789115',
        'company-security': '123456789116',
        'company-shared-services': '123456789117',
        'company-logging': '123456789118',
        'company-spoke-acct1': '123456789119',
        'company-spoke-acct2': '123456789120',
        'company-spoke-acct3': '123456789121',
        'company-spoke-acct4': '123456789122',
        'company-spoke-acct6': '123456789123',
        'company-ab-nonprod': '1234567891024',
        'company-ab-prod': '123456789125',
        'company-govcloud-ab-admin-nonprod': '123456789126',
        'company-govcloud-ab-nonprod': '123456789127',
        'company-govcloud-ab-admin-prod': '123456789128',
        'company-govcloud-ab-prod': '123456789129',
        'company-govcloud-ab-mc-admin-nonprod': '123456789130',
        'company-govcloud-ab-mc-nonprod': '123456789131',
        'company-govcloud-ab-mc-admin-prod': '123456789132',
        'company-govcloud-ab-mc-prod': '123456789133',
        'company-govcloud-admin-ab-dsg-logmon-nonprod': '123456789134',
        'company-govcloud-ab-dsg-logmon-nonprod': '123456789135',
        'company-govcloud-admin-ab-dsg-logmon-prod': '123456789136',
        'company-govcloud-ab-dsg-logmon-prod': '123456789137',
        'company-dsg-security-lab': '123456789138',
        'jf-python-dev': '123456789139',
        'jf-python-dev-gov': '123456789140',
        'jf-master-acct': '123456789141'
    }
    return switcher.get(aws_account, "nothing")

def get_today():
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    return today

## End Utility Functions

## 2. Read AWS Billing
def read_csv_to_sql(aws_account, aws_account_number):
    print(Fore.CYAN)
    print("*****************************************************")
    print("*             Read the AWS Bill                     *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    source_file = input('Enter the name of the source file: ')
    source = os.path.join('source_files', 'aws_bills', source_file + '.csv')
    if aws_account.lower() == 'company-bill':
        insert_sql = """ INSERT INTO """ + my_table_name + """ (InvoiceId, PayerAccountId, LinkedAccountId, RecordType, RecordId, ProductName, RateId, SubscriptionId, PricingPlanId, UsageType, Operation, AvailabilityZone, ReservedInstance, ItemDescription, UsageStartDate, UsageEndDate, UsageQuantity, BlendedRate, BlendedCost, UnBlendedRate, UnBlendedCost, ResourceId, Engagement, Name, Owner, Parent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ;"""
    elif aws_account.lower() == 'company-master':
        insert_sql = """ INSERT INTO """ + my_table_name + """ (InvoiceId, PayerAccountId, LinkedAccountId, RecordType, RecordId, ProductName, RateId, SubscriptionId, PricingPlanId, UsageType, Operation, AvailabilityZone, ReservedInstance, ItemDescription, UsageStartDate, UsageEndDate, UsageQuantity, BlendedRate, BlendedCost, UnBlendedRate, UnBlendedCost, ResourceId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ;""" 
    try:
        with open(source) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            rows = []
            row_count = 0
            for row in csv_reader:
                row_count += 1
                rows.append(row)
                if row_count == 5000:
                    try:
                        cursor.executemany(insert_sql,rows)
                        print(cursor.rowcount, 'rows inserted with LinkedAccountId', row[2], 'at', datetime.now().isoformat())
                        rows = []
                        row_count = 0
                    except mysql.connector.Error as error:
                        print("Failed inserting" + str(cursor.rowcount) + " records into the billing_info table: {}".format(error))
                        print("Failed inserting UnBlendedCost: ")
                        print(row[20])
                        print("Under AWS Account Number: ", row[2])
            if rows:
                try:
                    cursor.executemany(insert_sql,rows)
                    print(cursor.rowcount, 'rows inserted with LinkedAccountId', row[2], 'at', datetime.now().isoformat())
                except mysql.connector.Error as error:
                    print("Failed inserting" + cursor.rowcount  +" records into the billing_info table: {}".format(error))
                    time.sleep(5)
            # Commit changes to the database.
            try:
                print("Committing the DB.")
                mydb.commit()
            except mysql.connector.Error as error:
                print(f"Failed committing changes to the billing_info table: {error}.")
                time.sleep(5)
            finally:    
                print("Done importing data.")
                time.sleep(5)

    except mysql.connector.Error as error:
        print(f"Failed inserting record into billing_info table: {error}.")
        time.sleep(5)
        mydb.rollback()
    finally:
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

## 3. Read AWS CUR Billing
def read_cur_to_sql(aws_account, aws_account_number):
    print(Fore.CYAN)
    print("*****************************************************")
    print("*             Read the AWS Bill                     *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    source_file = input('Enter the name of the source file: ')
    source = os.path.join('source_files', 'aws_bills', source_file + '.csv')
    insert_sql = """ INSERT INTO """ + my_table_name + """ (identity_LineItemId, identity_TimeInterval, bill_InvoiceId, bill_BillingEntity, bill_BillType, bill_PayerAccountId, bill_BillingPeriodStartDate, bill_BillingPeriodEndDate, LinkedAccountId, lineItem_LineItemType, lineItem_UsageStartDate, lineItem_UsageEndDate, lineItem_ProductCode, lineItem_UsageType, lineItem_Operation, lineItem_AvailabilityZone, lineItem_ResourceId, lineItem_UsageAmount, lineItem_NormalizationFactor, lineItem_NormalizedUsageAmount, lineItem_CurrencyCode, lineItem_UnblendedRate, UnblendedCost, lineItem_BlendedRate, lineItem_BlendedCost, lineItem_LineItemDescription, lineItem_TaxType, lineItem_LegalEntity, product_ProductName, product_accountAssistance, product_alarmType, product_architecturalReview, product_architectureSupport, product_availability, product_bestPractices, product_brokerEngine, product_bundle, product_capacitystatus, product_caseSeverityresponseTimes, product_category, product_clockSpeed, product_computeFamily, product_computeType, product_contentType, product_currentGeneration, product_customerServiceAndCommunities, product_databaseEdition, product_databaseEngine, product_dedicatedEbsThroughput, product_deploymentOption, product_description, product_directorySize, product_directoryType, product_directoryTypeDescription, product_durability, product_ecu, product_edition, product_endpointType, product_engineCode, product_enhancedNetworkingSupport, product_enhancedNetworkingSupported, product_executionFrequency, product_executionLocation, product_feeCode, product_feeDescription, product_freeQueryTypes, product_freeTier, product_freeTrial, product_frequencyMode, product_fromLocation, product_fromLocationType, product_gpu, product_group, product_groupDescription, product_includedServices, product_instanceFamily, product_instanceType, product_instanceTypeFamily, product_io, product_launchSupport, product_license, product_licenseModel, product_location, product_locationType, product_mailboxStorage, product_maxIopsBurstPerformance, product_maxIopsvolume, product_maxThroughputvolume, product_maxVolumeSize, product_maximumExtendedStorage, product_maximumStorageVolume, product_memory, product_memoryGib, product_messageDeliveryFrequency, product_messageDeliveryOrder, product_minVolumeSize, product_minimumStorageVolume, product_networkPerformance, product_normalizationSizeFactor, product_operatingSystem, product_operation, product_operationsSupport, product_origin, product_physicalProcessor, product_planType, product_preInstalledSw, product_proactiveGuidance, product_processorArchitecture, product_processorFeatures, product_productFamily, product_programmaticCaseManagement, product_provisioned, product_queueType, product_recipient, product_region, product_requestDescription, product_requestType, product_resourceEndpoint, product_resourceType, product_rootvolume, product_routingTarget, product_routingType, product_runningMode, product_servicecode, product_servicename, product_sku, product_softwareIncluded, product_standardStorageRetentionIncluded, product_storage, product_storageClass, product_storageMedia, product_storageType, product_subscriptionType, product_technicalSupport, product_tenancy, product_thirdpartySoftwareSupport, product_toLocation, product_toLocationType, product_training, product_transferType, product_usageFamily, product_usagetype, product_uservolume, product_vcpu, product_version, product_volumeType, product_whoCanOpenCases, pricing_LeaseContractLength, pricing_OfferingClass, pricing_PurchaseOption, pricing_RateId, pricing_publicOnDemandCost, pricing_publicOnDemandRate, pricing_term, pricing_unit, reservation_AmortizedUpfrontCostForUsage, reservation_AmortizedUpfrontFeeForBillingPeriod, reservation_AvailabilityZone, reservation_EffectiveCost, reservation_EndTime, reservation_ModificationStatus, reservation_NormalizedUnitsPerReservation, reservation_NumberOfReservations, reservation_RecurringFeeForUsage, reservation_ReservationARN, reservation_StartTime, reservation_SubscriptionId, reservation_TotalReservedNormalizedUnits, reservation_TotalReservedUnits, reservation_UnitsPerReservation, reservation_UnusedAmortizedUpfrontFeeForBillingPeriod, reservation_UnusedNormalizedUnitQuantity, reservation_UnusedQuantity, reservation_UnusedRecurringFee, reservation_UpfrontValue, Engagement, Name, Owner, Parent) VALUES   (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ;"""
    try:
        with open(source) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            rows = []
            row_count = 0
            for row in csv_reader:
                row_count += 1
                rows.append(row)
                if row_count == 5000:
                    try:
                        cursor.executemany(insert_sql,rows)
                        print(cursor.rowcount, 'rows inserted with LinkedAccountId', row[2], 'at', datetime.now().isoformat())
                        rows = []
                        row_count = 0
                    except mysql.connector.Error as error:
                        print("Failed inserting" + str(cursor.rowcount) + " records into the CUR table: {}".format(error))
                        print("Under AWS Account Number: ", row[2])
            if rows:
                try:
                    cursor.executemany(insert_sql,rows)
                    print(cursor.rowcount, 'rows inserted with LinkedAccountId', row[2], 'at', datetime.now().isoformat())
                except mysql.connector.Error as error:
                    print("Failed inserting" + cursor.rowcount  +" records into the CUR table: {}".format(error))
                    time.sleep(5)
            # Commit changes to the database.
            try:
                print("Committing the DB.")
                mydb.commit()
            except mysql.connector.Error as error:
                print(f"Failed committing changes to the  CUR table: {error}.")
                time.sleep(5)
            finally:    
                print("Done importing data.")
                time.sleep(5)

    except mysql.connector.Error as error:
        print(f"Failed inserting record into CUR table: {error}.")
        time.sleep(5)
        mydb.rollback()
    finally:
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

## 3. Write AWS Bill
def write_to_csv(aws_account, aws_account_number, table_name):
    print(Fore.CYAN)
    print("*****************************************************")
    print("*             Write the AWS Bill                    *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    table_name = table_name()
    one_month_ago = datetime.now() - relativedelta(months=1)
    previous_month = one_month_ago.strftime("%Y%m").lower()
    if table_name == 'billing_info_cur':
        source = 'Cost Allocation - CUR  - ' + previous_month
    else:
        source = 'Cost Allocation - DBR - ' + previous_month
    output_dir = os.path.join('output_files', 'aws_bills')
    with contextlib.redirect_stdout(None):
        create_work_dir(output_dir)
    destination = os.path.join(output_dir, source + '.csv')
    if table_name == 'billing_info_dbr':
        if aws_account.strip() == 'company-bill' or aws_account.strip == 'company-master' or aws_account.strip == 'all':
            read_sql = """ SELECT LinkedAccountId,RecordType,Engagement,UnBlendedCost FROM """ + table_name + """ WHERE UnBlendedCost != 0 ;"""
        else:
            read_sql = """ SELECT LinkedAccountId,RecordType,Engagement,UnBlendedCost FROM """ + table_name + """ where LinkedAccountId= """ + aws_account_number + """ AND UnBlendedCost != 0;"""
    else:
        if aws_account.strip() == 'company-bill' or aws_account.strip == 'company-master' or aws_account.strip == 'all':
            read_sql = """ SELECT LinkedAccountId,UnBlendedCost,Engagement FROM """ + table_name + """ WHERE UnBlendedCost != 0 ;"""
        else:
            read_sql = """ SELECT LinkedAccountId,UnBlendedCost,Engagement FROM """ + table_name + """ where LinkedAccountId= """ + aws_account_number + """ AND UnBlendedCost != 0;"""
        

    print(f"Writing the file: {source}.")

    with open(destination, mode='w+') as csv_file:
        if table_name == 'billing_info_dbr':
            fieldnames = ['Account Number', 'Record Type','Engagement', 'Unblended Cost']
        else:
            fieldnames = ['Account Number', 'Unblended Cost', 'Engagement']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
        writer.writeheader()
    # Open the file
    with open(destination, mode='a') as csv_file:
        cursor.execute(read_sql)
        while True:
            try:
                # Read the data
                df = pd.DataFrame(cursor.fetchmany(5000))
                # We are done if there are no data
                if len(df) == 0:
                    break
                # Let's write to the file
                else:
                    df.to_csv(csv_file, header=None, index=False, line_terminator='\n')
            except Exception as e:
                print(f"An error has occurred: {error}.")
                time.sleep(5)
            except mysql.connector.Error as error:
                print(f"Failed committing changes to the billing_info table: {error}.")
                time.sleep(5)
            finally:
                if(mydb.is_connected()):
                    cursor.close()
                    mydb.close()
                    print("MySQL connection is closed.")
                    time.sleep(5)
    print("Finished writing the file.")
    time.sleep

## 4. Send Email
def send_email(aws_account, aws_account_number):
    print(Fore.CYAN)
    print("*****************************************************")
    print("*              Send Email                           *")
    print("*****************************************************")
    today = get_today()
    # Get the variables from intitialize
    ## One or many accounts
    print(Fore.YELLOW)
    ## Get the user's first name
    first_name = input("Enter the recipient's first name: ")
    ## Get the address to send to
    to_addr = input("Enter the recipient's email address: ")
    destination = input("Enter the name of the report: ")
    output_dir = os.path.join('output_files', 'aws_bills')
    destination = os.path.join(output_dir, destination)
    aws_accounts_question = input("Get billing info for one or all accounts: ")
    from_addr = 'cloudops@noreply.company.com'
    subject = "company AWS Billing Info " + today
    if aws_accounts_question == 'one':
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find billing info for AWS Account: " + aws_account + " (" + aws_account_number + ")" + ".<br><br>Regards,<br>Cloud Ops</font>"
    else:
        content = "<font size=2 face=Verdana color=black>Hello " +  first_name + ", <br><br>Enclosed, please find billing info for all company AWS accounts.<br><br>Regards,<br>Cloud Ops</font>"
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = MIMEText(content, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtpout.us.cworld.company.com', 25)
    filename = destination
    try:
        with open(filename, 'r', errors='ignore') as f:
            part = MIMEApplication(f.read(), Name=basename(filename))
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(filename))
            msg.attach(part)
            server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
        print("Email was sent to: %s" %  to_addr)
    except Exception as e:
        print(f"Exception: {e}.")
        print("Email was not sent.")

## 5. Recreate Table
def recreate_sql_table():
    print(Fore.CYAN)
    print("*************************************************************")
    print("*             Recreate the Billing Table                    *")
    print("*************************************************************")
    print(Fore.RESET)   
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    drop_table_sql = """ DROP TABLE IF EXISTS """ + my_table_name + """; """
    create_table_sql = """ CREATE TABLE IF NOT EXISTS """ + my_table_name + """ (
	`ID` INT  AUTO_INCREMENT,
    `InvoiceId` CHAR(9),
    `PayerAccountId` BIGINT NOT NULL,
    `LinkedAccountId` CHAR(12),
    `RecordType` CHAR(25) NOT NULL,
    `RecordId` CHAR(27),
    `ProductName` VARCHAR(50),
	`RateId` VARCHAR(9),
	`SubscriptionId` CHAR(15),
	`PricingPlanId` VARCHAR(8),
	`UsageType` VARCHAR(50),
	`Operation` VARCHAR(50),
	`AvailabilityZone` VARCHAR(15),
	`ReservedInstance` CHAR(1),
	`ItemDescription` VARCHAR(300) NOT NULL,
	`UsageStartDate` CHAR(20),
	`UsageEndDate` CHAR(20),
	`UsageQuantity` VARCHAR(50),
	`BlendedRate` CHAR(50),
	`BlendedCost` CHAR(50) NOT NULL,
	`UnBlendedRate` CHAR(50),
	`UnBlendedCost` CHAR(50) NOT NULL,
	`ResourceId` VARCHAR(150),
	`Engagement` VARCHAR(15),
	`Name` VARCHAR(150),
	`Owner` VARCHAR(30),
	`Parent` VARCHAR(30),
	PRIMARY KEY (ID)
    ); """
    # Drop the table
    try:
         print("Dropping the Billing Info table.")
         time.sleep(5)
         drop_table  = cursor.execute(drop_table_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Done dropping the table.")
        time.sleep(5)
    # Create the table
    try:
         print("Creating the Billing Info table.")
         time.sleep(5)
         create_table  = cursor.execute(create_table_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Done creating the table.")
        time.sleep(5)
    try:
        print("Committing the DB.")
        mydb.commit()
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Done making changes to the DB.")
        time.sleep(5)
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

## 6. Recreate Table
def recreate_cur_table():
    print(Fore.CYAN)
    print("*************************************************************")
    print("*             Recreate the Billing Table                    *")
    print("*************************************************************")
    print(Fore.RESET)   
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    drop_table_sql = """ DROP TABLE IF EXISTS """ + my_table_name + """; """
    create_table_sql = """ CREATE TABLE IF NOT EXISTS """ + my_table_name + """ (
	`ID` INT AUTO_INCREMENT,
    identity_LineItemId TEXT(300),
    identity_TimeInterval TEXT(300),
    bill_InvoiceId TEXT(300),
    bill_BillingEntity TEXT(300),
    bill_BillType TEXT(300),
    bill_PayerAccountId TEXT(300),
    bill_BillingPeriodStartDate TEXT(300),
    bill_BillingPeriodEndDate TEXT(300),
    LinkedAccountId TEXT(300),
    lineItem_LineItemType TEXT(300),
    lineItem_UsageStartDate TEXT(300),
    lineItem_UsageEndDate TEXT(300),
    lineItem_ProductCode TEXT(300),
    lineItem_UsageType TEXT(300),
    lineItem_Operation TEXT(300),
    lineItem_AvailabilityZone TEXT(300),
    lineItem_ResourceId TEXT(300),
    lineItem_UsageAmount TEXT(300),
    lineItem_NormalizationFactor TEXT(300),
    lineItem_NormalizedUsageAmount TEXT(300),
    lineItem_CurrencyCode TEXT(300),
    lineItem_UnblendedRate TEXT(300),
    UnblendedCost TEXT(300),
    lineItem_BlendedRate TEXT(300),
    lineItem_BlendedCost TEXT(300),
    lineItem_LineItemDescription TEXT(300),
    lineItem_TaxType TEXT(300),
    lineItem_LegalEntity TEXT(300),
    product_ProductName TEXT(300),
    product_accountAssistance TEXT(300),
    product_alarmType TEXT(300),
    product_architecturalReview TEXT(300),
    product_architectureSupport TEXT(300),
    product_availability TEXT(300),
    product_bestPractices TEXT(300),
    product_brokerEngine TEXT(300),
    product_bundle TEXT(300),
    product_capacitystatus TEXT(300),
    product_caseSeverityresponseTimes TEXT(300),
    product_category TEXT(300),
    product_clockSpeed TEXT(300),
    product_computeFamily TEXT(300),
    product_computeType TEXT(300),
    product_contentType TEXT(300),
    product_currentGeneration TEXT(300),
    product_customerServiceAndCommunities TEXT(300),
    product_databaseEdition TEXT(300),
    product_databaseEngine TEXT(300),
    product_dedicatedEbsThroughput TEXT(300),
    product_deploymentOption TEXT(300),
    product_description TEXT(300),
    product_directorySize TEXT(300),
    product_directoryType TEXT(300),
    product_directoryTypeDescription TEXT(300),
    product_durability TEXT(300),
    product_ecu TEXT(300),
    product_edition TEXT(300),
    product_endpointType TEXT(300),
    product_engineCode TEXT(300),
    product_enhancedNetworkingSupport TEXT(300),
    product_enhancedNetworkingSupported TEXT(300),
    product_executionFrequency TEXT(300),
    product_executionLocation TEXT(300),
    product_feeCode TEXT(300),
    product_feeDescription TEXT(300),
    product_freeQueryTypes TEXT(300),
    product_freeTier TEXT(300),
    product_freeTrial TEXT(300),
    product_frequencyMode TEXT(300),
    product_fromLocation TEXT(300),
    product_fromLocationType TEXT(300),
    product_gpu TEXT(300),
    product_group TEXT(300),
    product_groupDescription TEXT(300),
    product_includedServices TEXT(300),
    product_instanceFamily TEXT(300),
    product_instanceType TEXT(300),
    product_instanceTypeFamily TEXT(300),
    product_io TEXT(300),
    product_launchSupport TEXT(300),
    product_license TEXT(300),
    product_licenseModel TEXT(300),
    product_location TEXT(300),
    product_locationType TEXT(300),
    product_mailboxStorage TEXT(300),
    product_maxIopsBurstPerformance TEXT(300),
    product_maxIopsvolume TEXT(300),
    product_maxThroughputvolume TEXT(300),
    product_maxVolumeSize TEXT(300),
    product_maximumExtendedStorage TEXT(300),
    product_maximumStorageVolume TEXT(300),
    product_memory TEXT(300),
    product_memoryGib TEXT(300),
    product_messageDeliveryFrequency TEXT(300),
    product_messageDeliveryOrder TEXT(300),
    product_minVolumeSize TEXT(300),
    product_minimumStorageVolume TEXT(300),
    product_networkPerformance TEXT(300),
    product_normalizationSizeFactor TEXT(300),
    product_operatingSystem TEXT(300),
    product_operation TEXT(300),
    product_operationsSupport TEXT(300),
    product_origin TEXT(300),
    product_physicalProcessor TEXT(300),
    product_planType TEXT(300),
    product_preInstalledSw TEXT(300),
    product_proactiveGuidance TEXT(300),
    product_processorArchitecture TEXT(300),
    product_processorFeatures TEXT(300),
    product_productFamily TEXT(300),
    product_programmaticCaseManagement TEXT(300),
    product_provisioned TEXT(300),
    product_queueType TEXT(300),
    product_recipient TEXT(300),
    product_region TEXT(300),
    product_requestDescription TEXT(300),
    product_requestType TEXT(300),
    product_resourceEndpoint TEXT(300),
    product_resourceType TEXT(300),
    product_rootvolume TEXT(300),
    product_routingTarget TEXT(300),
    product_routingType TEXT(300),
    product_runningMode TEXT(300),
    product_servicecode TEXT(300),
    product_servicename TEXT(300),
    product_sku TEXT(300),
    product_softwareIncluded TEXT(300),
    product_standardStorageRetentionIncluded TEXT(300),
    product_storage TEXT(300),
    product_storageClass TEXT(300),
    product_storageMedia TEXT(300),
    product_storageType TEXT(300),
    product_subscriptionType TEXT(300),
    product_technicalSupport TEXT(300),
    product_tenancy TEXT(300),
    product_thirdpartySoftwareSupport TEXT(300),
    product_toLocation TEXT(300),
    product_toLocationType TEXT(300),
    product_training TEXT(300),
    product_transferType TEXT(300),
    product_usageFamily TEXT(300),
    product_usagetype TEXT(300),
    product_uservolume TEXT(300),
    product_vcpu TEXT(300),
    product_version TEXT(300),
    product_volumeType TEXT(300),
    product_whoCanOpenCases TEXT(300),
    pricing_LeaseContractLength TEXT(300),
    pricing_OfferingClass TEXT(300),
    pricing_PurchaseOption TEXT(300),
    pricing_RateId TEXT(300),
    pricing_publicOnDemandCost TEXT(300),
    pricing_publicOnDemandRate TEXT(300),
    pricing_term TEXT(300),
    pricing_unit TEXT(300),
    reservation_AmortizedUpfrontCostForUsage TEXT(300),
    reservation_AmortizedUpfrontFeeForBillingPeriod TEXT(300),
    reservation_AvailabilityZone TEXT(300),
    reservation_EffectiveCost TEXT(300),
    reservation_EndTime TEXT(300),
    reservation_ModificationStatus TEXT(300),
    reservation_NormalizedUnitsPerReservation TEXT(300),
    reservation_NumberOfReservations TEXT(300),
    reservation_RecurringFeeForUsage TEXT(300),
    reservation_ReservationARN TEXT(300),
    reservation_StartTime TEXT(300),
    reservation_SubscriptionId TEXT(300),
    reservation_TotalReservedNormalizedUnits TEXT(300),
    reservation_TotalReservedUnits TEXT(300),
    reservation_UnitsPerReservation TEXT(300),
    reservation_UnusedAmortizedUpfrontFeeForBillingPeriod TEXT(300),
    reservation_UnusedNormalizedUnitQuantity TEXT(300),
    reservation_UnusedQuantity TEXT(300),
    reservation_UnusedRecurringFee TEXT(300),
    reservation_UpfrontValue TEXT(300),
    Engagement TEXT(300),
    Name TEXT(300),
    Owner TEXT(300),
    Parent TEXT(300),
	PRIMARY KEY (ID)
    ); """
    # Drop the table
    try:
         print("Dropping the CUR table.")
         time.sleep(5)
         drop_table  = cursor.execute(drop_table_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the CUR table: {error}.")
        time.sleep(5)
    finally:    
        print("Done dropping the CUR table.")
        time.sleep(5)
    # Create the table
    try:
         print("Creating the CUR table.")
         time.sleep(5)
         create_table  = cursor.execute(create_table_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the CUR table: {error}.")
        time.sleep(5)
    finally:    
        print("Done creating CUR the table.")
        time.sleep(5)
    try:
        print("Committing the DB.")
        mydb.commit()
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the CUR table: {error}.")
        time.sleep(5)
    finally:    
        print("Done making changes to the DB.")
        time.sleep(5)
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)



## 6. Update Database To NULL
def update_database(aws_account, table_name):
    print(Fore.CYAN)
    print("*****************************************************")
    print("*      Update Emtpy Cells to NULL                   *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    print(f"My Table name: {my_table_name}")
    print("Updating all empty values to NULL.")
    time.sleep(10)
    if my_table_name == 'billing_info_dbr':
        # Set all empty values to NULL
        if aws_account.lower() == 'company-bill':   
            update_sql = """ UPDATE """ + my_table_name + """
                SET InvoiceId=NULLIF(InvoiceId, ''),
                LinkedAccountId=NULLIF(LinkedAccountId, ''),
                RecordId=NULLIF(RecordId, ''),
                ProductName=NULLIF(ProductName, ''),
                RateId=NULLIF(RateId, ''),
                SubscriptionId=NULLIF(SubscriptionId, ''),
                PricingPlanId=NULLIF(PricingPlanId, ''),
                UsageType=NULLIF(UsageTYpe, ''),
                Operation=NULLIF(Operation, ''),
                AvailabilityZone=NULLIF(AvailabilityZone, ''),
                ReservedInstance=NULLIF(ReservedInstance, ''),
                UsageStartDate=NULLIF(UsageStartDate, ''),
                UsageEndDate=NULLIF(UsageEndDate, ''),
                UsageQuantity=NULLIF(UsageQuantity, ''),
                BlendedRate=NULLIF(BlendedRate, ''),
                UnBlendedRate=NULLIF(UnBlendedRate, ''),
                ResourceId=NULLIF(ResourceId, ''),
                Engagement=NULLIF(Engagement, ''),
                Name=NULLIF(Name, ''),
                Owner=NULLIF(Owner, ''),
                Parent=NULLIF(Parent, '') ; """

    elif my_table_name == 'billing_info_cur':
        update_sql = """ UPDATE """ + my_table_name + """
        SET identity_LineItemId=NULLIF(identity_LineItemId, ''),
            identity_TimeInterval=NULLIF(identity_TimeInterval, ''),
            bill_InvoiceId=NULLIF(bill_InvoiceId, ''),
            bill_BillingEntity=NULLIF(bill_BillingEntity, ''),
            bill_BillType=NULLIF(bill_BillType, ''),
            bill_PayerAccountId=NULLIF(bill_PayerAccountId, ''),
            bill_BillingPeriodStartDate=NULLIF(bill_BillingPeriodStartDate, ''),
            bill_BillingPeriodEndDate=NULLIF(bill_BillingPeriodEndDate, ''),
            LinkedAccountId=NULLIF(LinkedAccountId, ''),
            lineItem_LineItemType=NULLIF(lineItem_LineItemType, ''),
            lineItem_UsageStartDate=NULLIF(lineItem_UsageStartDate, ''),
            lineItem_UsageEndDate=NULLIF(lineItem_UsageEndDate, ''),
            lineItem_ProductCode=NULLIF(lineItem_ProductCode, ''),
            lineItem_UsageType=NULLIF(lineItem_UsageType, ''),
            lineItem_Operation=NULLIF(lineItem_Operation, ''),
            lineItem_AvailabilityZone=NULLIF(lineItem_AvailabilityZone, ''),
            lineItem_ResourceId=NULLIF(lineItem_ResourceId, ''),
            lineItem_UsageAmount=NULLIF(lineItem_UsageAmount, ''),
            lineItem_NormalizationFactor=NULLIF(lineItem_NormalizationFactor, ''),
            lineItem_NormalizedUsageAmount=NULLIF(lineItem_NormalizedUsageAmount, ''),
            lineItem_CurrencyCode=NULLIF(lineItem_CurrencyCode, ''),
            lineItem_UnblendedRate=NULLIF(lineItem_UnblendedRate, ''),
            UnblendedCost=NULLIF(UnblendedCost, ''),
            lineItem_BlendedRate=NULLIF(lineItem_BlendedRate, ''),
            lineItem_BlendedCost=NULLIF(lineItem_BlendedCost, ''),
            lineItem_LineItemDescription=NULLIF(lineItem_LineItemDescription, ''),
            lineItem_TaxType=NULLIF(lineItem_TaxType, ''),
            lineItem_LegalEntity=NULLIF(lineItem_LegalEntity, ''),
            product_ProductName=NULLIF(product_ProductName, ''),
            product_accountAssistance=NULLIF(product_accountAssistance, ''),
            product_alarmType=NULLIF(product_alarmType, ''),
            product_architecturalReview=NULLIF(product_architecturalReview, ''),
            product_architectureSupport=NULLIF(product_architectureSupport, ''),
            product_availability=NULLIF(product_availability, ''),
            product_bestPractices=NULLIF(product_bestPractices, ''),
            product_brokerEngine=NULLIF(product_brokerEngine, ''),
            product_bundle=NULLIF(product_bundle, ''),
            product_capacitystatus=NULLIF(product_capacitystatus, ''),
            product_caseSeverityresponseTimes=NULLIF(product_caseSeverityresponseTimes, ''),
            product_category=NULLIF(product_category, ''),
            product_clockSpeed=NULLIF(product_clockSpeed, ''),
            product_computeFamily=NULLIF(product_computeFamily, ''),
            product_computeType=NULLIF(product_computeType, ''),
            product_contentType=NULLIF(product_contentType, ''),
            product_currentGeneration=NULLIF(product_currentGeneration, ''),
            product_customerServiceAndCommunities=NULLIF(product_customerServiceAndCommunities, ''),
            product_databaseEdition=NULLIF(product_databaseEdition, ''),
            product_databaseEngine=NULLIF(product_databaseEngine, ''),
            product_dedicatedEbsThroughput=NULLIF(product_dedicatedEbsThroughput, ''),
            product_deploymentOption=NULLIF(product_deploymentOption, ''),
            product_description=NULLIF(product_description, ''),
            product_directorySize=NULLIF(product_directorySize, ''),
            product_directoryType=NULLIF(product_directoryType, ''),
            product_directoryTypeDescription=NULLIF(product_directoryTypeDescription, ''),
            product_durability=NULLIF(product_durability, ''),
            product_ecu=NULLIF(product_ecu, ''),
            product_edition=NULLIF(product_edition, ''),
            product_endpointType=NULLIF(product_endpointType, ''),
            product_engineCode=NULLIF(product_engineCode, ''),
            product_enhancedNetworkingSupport=NULLIF(product_enhancedNetworkingSupport, ''),
            product_enhancedNetworkingSupported=NULLIF(product_enhancedNetworkingSupported, ''),
            product_executionFrequency=NULLIF(product_executionFrequency, ''),
            product_executionLocation=NULLIF(product_executionLocation, ''),
            product_feeCode=NULLIF(product_feeCode, ''),
            product_feeDescription=NULLIF(product_feeDescription, ''),
            product_freeQueryTypes=NULLIF(product_freeQueryTypes, ''),
            product_freeTier=NULLIF(product_freeTier, ''),
            product_freeTrial=NULLIF(product_freeTrial, ''),
            product_frequencyMode=NULLIF(product_frequencyMode, ''),
            product_fromLocation=NULLIF(product_fromLocation, ''),
            product_fromLocationType=NULLIF(product_fromLocationType, ''),
            product_gpu=NULLIF(product_gpu, ''),
            product_group=NULLIF(product_group, ''),
            product_groupDescription=NULLIF(product_groupDescription, ''),
            product_includedServices=NULLIF(product_includedServices, ''),
            product_instanceFamily=NULLIF(product_instanceFamily, ''),
            product_instanceType=NULLIF(product_instanceType, ''),
            product_instanceTypeFamily=NULLIF(product_instanceTypeFamily, ''),
            product_io=NULLIF(product_io, ''),
            product_launchSupport=NULLIF(product_launchSupport, ''),
            product_license=NULLIF(product_license, ''),
            product_licenseModel=NULLIF(product_licenseModel, ''),
            product_location=NULLIF(product_location, ''),
            product_locationType=NULLIF(product_locationType, ''),
            product_mailboxStorage=NULLIF(product_mailboxStorage, ''),
            product_maxIopsBurstPerformance=NULLIF(product_maxIopsBurstPerformance, ''),
            product_maxIopsvolume=NULLIF(product_maxIopsvolume, ''),
            product_maxThroughputvolume=NULLIF(product_maxThroughputvolume, ''),
            product_maxVolumeSize=NULLIF(product_maxVolumeSize, ''),
            product_maximumExtendedStorage=NULLIF(product_maximumExtendedStorage, ''),
            product_maximumStorageVolume=NULLIF(product_maximumStorageVolume, ''),
            product_memory=NULLIF(product_memory, ''),
            product_memoryGib=NULLIF(product_memoryGib, ''),
            product_messageDeliveryFrequency=NULLIF(product_messageDeliveryFrequency, ''),
            product_messageDeliveryOrder=NULLIF(product_messageDeliveryOrder, ''),
            product_minVolumeSize=NULLIF(product_minVolumeSize, ''),
            product_minimumStorageVolume=NULLIF(product_minimumStorageVolume, ''),
            product_networkPerformance=NULLIF(product_networkPerformance, ''),
            product_normalizationSizeFactor=NULLIF(product_normalizationSizeFactor, ''),
            product_operatingSystem=NULLIF(product_operatingSystem, ''),
            product_operation=NULLIF(product_operation, ''),
            product_operationsSupport=NULLIF(product_operationsSupport, ''),
            product_origin=NULLIF(product_origin, ''),
            product_physicalProcessor=NULLIF(product_physicalProcessor, ''),
            product_planType=NULLIF(product_planType, ''),
            product_preInstalledSw=NULLIF(product_preInstalledSw, ''),
            product_proactiveGuidance=NULLIF(product_proactiveGuidance, ''),
            product_processorArchitecture=NULLIF(product_processorArchitecture, ''),
            product_processorFeatures=NULLIF(product_processorFeatures, ''),
            product_productFamily=NULLIF(product_productFamily, ''),
            product_programmaticCaseManagement=NULLIF(product_programmaticCaseManagement, ''),
            product_provisioned=NULLIF(product_provisioned, ''),
            product_queueType=NULLIF(product_queueType, ''),
            product_recipient=NULLIF(product_recipient, ''),
            product_region=NULLIF(product_region, ''),
            product_requestDescription=NULLIF(product_requestDescription, ''),
            product_requestType=NULLIF(product_requestType, ''),
            product_resourceEndpoint=NULLIF(product_resourceEndpoint, ''),
            product_resourceType=NULLIF(product_resourceType, ''),
            product_rootvolume=NULLIF(product_rootvolume, ''),
            product_routingTarget=NULLIF(product_routingTarget, ''),
            product_routingType=NULLIF(product_routingType, ''),
            product_runningMode=NULLIF(product_runningMode, ''),
            product_servicecode=NULLIF(product_servicecode, ''),
            product_servicename=NULLIF(product_servicename, ''),
            product_sku=NULLIF(product_sku, ''),
            product_softwareIncluded=NULLIF(product_softwareIncluded, ''),
            product_standardStorageRetentionIncluded=NULLIF(product_standardStorageRetentionIncluded, ''),
            product_storage=NULLIF(product_storage, ''),
            product_storageClass=NULLIF(product_storageClass, ''),
            product_storageMedia=NULLIF(product_storageMedia, ''),
            product_storageType=NULLIF(product_storageType, ''),
            product_subscriptionType=NULLIF(product_subscriptionType, ''),
            product_technicalSupport=NULLIF(product_technicalSupport, ''),
            product_tenancy=NULLIF(product_tenancy, ''),
            product_thirdpartySoftwareSupport=NULLIF(product_thirdpartySoftwareSupport, ''),
            product_toLocation=NULLIF(product_toLocation, ''),
            product_toLocationType=NULLIF(product_toLocationType, ''),
            product_training=NULLIF(product_training, ''),
            product_transferType=NULLIF(product_transferType, ''),
            product_usageFamily=NULLIF(product_usageFamily, ''),
            product_usagetype=NULLIF(product_usagetype, ''),
            product_uservolume=NULLIF(product_uservolume, ''),
            product_vcpu=NULLIF(product_vcpu, ''),
            product_version=NULLIF(product_version, ''),
            product_volumeType=NULLIF(product_volumeType, ''),
            product_whoCanOpenCases=NULLIF(product_whoCanOpenCases, ''),
            pricing_LeaseContractLength=NULLIF(pricing_LeaseContractLength, ''),
            pricing_OfferingClass=NULLIF(pricing_OfferingClass, ''),
            pricing_PurchaseOption=NULLIF(pricing_PurchaseOption, ''),
            pricing_RateId=NULLIF(pricing_RateId, ''),
            pricing_publicOnDemandCost=NULLIF(pricing_publicOnDemandCost, ''),
            pricing_publicOnDemandRate=NULLIF(pricing_publicOnDemandRate, ''),
            pricing_term=NULLIF(pricing_term, ''),
            pricing_unit=NULLIF(pricing_unit, ''),
            reservation_AmortizedUpfrontCostForUsage=NULLIF(reservation_AmortizedUpfrontCostForUsage, ''),
            reservation_AmortizedUpfrontFeeForBillingPeriod=NULLIF(reservation_AmortizedUpfrontFeeForBillingPeriod, ''),
            reservation_AvailabilityZone=NULLIF(reservation_AvailabilityZone, ''),
            reservation_EffectiveCost=NULLIF(reservation_EffectiveCost, ''),
            reservation_EndTime=NULLIF(reservation_EndTime, ''),
            reservation_ModificationStatus=NULLIF(reservation_ModificationStatus, ''),
            reservation_NormalizedUnitsPerReservation=NULLIF(reservation_NormalizedUnitsPerReservation, ''),
            reservation_NumberOfReservations=NULLIF(reservation_NumberOfReservations, ''),
            reservation_RecurringFeeForUsage=NULLIF(reservation_RecurringFeeForUsage, ''),
            reservation_ReservationARN=NULLIF(reservation_ReservationARN, ''),
            reservation_StartTime=NULLIF(reservation_StartTime, ''),
            reservation_SubscriptionId=NULLIF(reservation_SubscriptionId, ''),
            reservation_TotalReservedNormalizedUnits=NULLIF(reservation_TotalReservedNormalizedUnits, ''),
            reservation_TotalReservedUnits=NULLIF(reservation_TotalReservedUnits, ''),
            reservation_UnitsPerReservation=NULLIF(reservation_UnitsPerReservation, ''),
            reservation_UnusedAmortizedUpfrontFeeForBillingPeriod=NULLIF(reservation_UnusedAmortizedUpfrontFeeForBillingPeriod, ''),
            reservation_UnusedNormalizedUnitQuantity=NULLIF(reservation_UnusedNormalizedUnitQuantity, ''),
            reservation_UnusedQuantity=NULLIF(reservation_UnusedQuantity, ''),
            reservation_UnusedRecurringFee=NULLIF(reservation_UnusedRecurringFee, ''),
            reservation_UpfrontValue=NULLIF(reservation_UpfrontValue, ''),
            Engagement=NULLIF(Engagement, ''),
            Name=NULLIF(Name, ''),
            Owner=NULLIF(Owner, ''),
            Parent=NULLIF(Parent, '') ; """
    try:
        cursor.execute(update_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    # Commit changes to the database.
    try:
        print("Committing the DB.")
        mydb.commit()
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Finished updating the data.")
        time.sleep(5)
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

## 7. Set Default Engagement
def set_default_engagement():
    print(Fore.CYAN)
    print("*****************************************************")
    print("*         Set Default Engagement Codes              *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    print("Updating all blank engagement codes.")
    time.sleep(5)
    # Set all empty values to NULL  
    set_engagement_sql = """ UPDATE """ + my_table_name + """ SET 
                    Engagement = CASE 
                        WHEN LinkedAccountId = '103440952267' THEN '800000046406'
                        WHEN LinkedAccountId = '412164052405' THEN '803000006453'
                        WHEN LinkedAccountId IN ('167031866369', '806534465904') THEN '800000043270'
                        WHEN LinkedAccountId IN ('764210188035', '991163571593') THEN '400000008426'
                        WHEN LinkedAccountId IN ('151528745488', '155775729998') THEN '807000000401'
                        WHEN LinkedAccountId IN ('913530316654', '042821237378', '849740718434', '042489471961') THEN '808000000298'
                        WHEN LinkedAccountId IN ('962923862227', '900653850120', '219577256432', '902541738353') THEN '800000047650'
                        WHEN LinkedAccountId IN ('419585237664', '303779310401', '193256904289','300944922012', '826254699822','288378600023', '872950281716', '067621579922', '421544879922', '795959353786') THEN '800000039768'
                        WHEN LinkedAccountId IN ('675966588449', '654077510425', '863351155240', '654360223973', '818951881696', '026715570499', '609094545271', '028074947530', '201370688988', '005350604950',  '635681562415', '007107066053') THEN '400000008692'
                        WHEN LinkedAccountId IN ('580036671366', '664008221807', '486469900423', '188087670762',  '051170381115', '287093337099', '832839043616', '560044853747', '615531451610',  '396689707712', '193327972326', '396993371780', '120022335547', '363046072563') THEN '400000008378' 
                        ELSE '800000039768'
                    END
                    WHERE Engagement IS NULL OR Engagement RLIKE '^[a-zA-Z]'; """
    try:
        cursor.execute(set_engagement_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    # Commit changes to the database.
    try:
        print("Committing the DB.")
        mydb.commit()
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Finished updating the data.")
        time.sleep(5)
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

## 8. Replace Bad Engagement Code
def replace_bad_enagement():
    print(Fore.CYAN)
    print("*****************************************************")
    print("*         Replace Bad Engagement                    *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    print("Replacing bad engagement codes.")
    # Set all empty values to NULL  
    replace_bad_engagement_sql = """ UPDATE """ + my_table_name + """ SET Engagement='400000008378' WHERE LinkedAccountId = '051170381115' AND Engagement = '123456789012' ; """
    try:
        cursor.execute(replace_bad_engagement_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    # Commit changes to the database.
    try:
        print("Committing the DB.")
        mydb.commit()
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Finished updating the data.")
        time.sleep(5)
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

## 9. Replace Bad Engagement Code
def replace_old_enagements():
    print(Fore.CYAN)
    print("*****************************************************")
    print("*         Replace Old Engagement                    *")
    print("*****************************************************")
    print(Fore.RESET)
    cursor, mydb = connect_to_db()
    my_table_name = table_name()
    print("Replacing old engagement codes.")
    # Set all empty values to NULL  
    replace_old_engagements_sql = """ UPDATE """ + my_table_name + """
                                SET Engagement = CASE Engagement
                                                    WHEN '800000026680' THEN '800000032764'
                                                    WHEN '807000000041' THEN '808000000000'
                                                    WHEN '870000012569' THEN '807000000412'
                                                    WHEN '807000000279' THEN '808000000223'
                                                    WHEN '807000000282' THEN '808000000223'
                                                    WHEN '870000000403' THEN '808000000223'
                                                END
                                WHERE LinkedAccountId in ('151528745488','155775729998') AND Engagement IN ('800000026680', '807000000041', '870000012569', '807000000279', '807000000282', '870000000403'); """
    try:
        cursor.execute(replace_old_engagements_sql)
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    # Commit changes to the database.
    try:
        print("Committing the DB.")
        mydb.commit()
    except mysql.connector.Error as error:
        print(f"Failed committing changes to the billing_info table: {error}.")
        time.sleep(5)
    finally:    
        print("Finished updating the data.")
        time.sleep(5)
        if(mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL connection is closed.")
            time.sleep(5)

def main():
    welcomebanner()
    choice = choose_action()
    my_table_name = table_name()
    # Exit the program
    if choice == "12":
        exit_program()
    # 1 Run the report
    elif choice == "1":
        aws_account, aws_account_number, today = initialize()
        recreate_sql_table(my_table_name)
        read_csv_to_sql(aws_account, aws_account_number, my_table_name)
        update_database(aws_account, table_name)
        set_default_engagement(my_table_name)
        replace_bad_enagement(my_table_name)
        replace_old_enagements(my_table_name)
        write_to_csv(aws_account, aws_account_number,my_table_name)
        main()
    # 2 Read the file
    elif choice == "2":
        aws_account, aws_account_number, today = initialize()
        read_csv_to_sql(aws_account, aws_account_number, my_table_name)
        main()
    # 3 Read the CUR file
    elif choice == "3":
        aws_account, aws_account_number, today = initialize()
        read_cur_to_sql(aws_account, aws_account_number,my_table_name)
        main()
    # 4 Write the file
    elif choice == "4":
        aws_account, aws_account_number, today = initialize()
        write_to_csv(aws_account, aws_account_number, my_table_name)
        main()
    # 5 Send email
    elif choice == "5":
        aws_account, aws_account_number, today = initialize()
        send_email(aws_account, aws_account_number, my_table_name)
        main()
    # 6 Recreate the table
    elif choice == "6":
        recreate_sql_table(my_table_name)
        main()
    # 7 Recreate the table
    elif choice == "7":
        recreate_cur_table(my_table_name)
        main()
    # 8 Update the database to NULL
    elif choice == "8":
        aws_account, aws_account_number, today = initialize()
        update_database(aws_account, my_table_name)
        main()
    # 9 Set Default Engagement
    elif choice == "9":
        set_default_engagement(my_table_name)
        main()
    # 10 Replace Bad Engagement
    elif choice == "10":
        replace_bad_enagement(my_table_name)
        main()
    # 11 Replace Old Engagement Code
    elif choice == "11":
        replace_old_enagements(my_table_name)
        main()

if __name__ == "__main__":
    main()

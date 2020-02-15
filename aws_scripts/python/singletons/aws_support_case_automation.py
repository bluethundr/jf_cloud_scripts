import json
import boto3
session = boto3.Session(profile_name='company-master')
support_client = session.client('support')

def my_handler(event, context):
    time.sleep(15)
    case_subject="Enable Enterprise Support for account " + newAccountID
    case_severity_code='normal'
    case_communication_body = "Hi AWS! Please enable Enterprise Support on new account ID " + newAccountID + "; the same support plan as this Payer account. This is an automated case - please resolve it when done."
    cc_email_address = 'us-dbcloudopsallist@company.com'
    new_aws_support_case = client.create_case(
        subject=case_subject,
        severityCode=case_severity_code,
        categoryCode='string',
        communicationBody=case_communication_body,
        ccEmailAddresses= cc_email_address,
        language='en',
        issueType='customer-service'
    )
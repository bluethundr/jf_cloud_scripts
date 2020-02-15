import json
import boto3

def lambda_function(event, context):
    time.sleep(15)
    case_subject="Enable Enterprise Support for account " + newAccountID
    case_severity_code='normal'
    case_communication_body = "Hi AWS! Please enable Enterprise Support on new account ID " + newAccountID + "; the same support plan as this payer account. This is an automated case - please resolve it when done."
    add_to_invoicing_body = "Please add " + newAccountID + " to invoicing on this payer account. Plese refer to the following billing information:\n* Company Name: company LLP\n* Contact Name for Invoice: Timothy Dunphy\n* Contact Phone for Invoice:201-505-6218\n* Contact Email for Invoice: tdunphy@company.com\n* Address: 75 Chestnut Ridge Road\n* City: Montvale\n* State: NJ\n* Zip: 07645\n* Country: USA"
    case_communication_body = case_communication_body + add_to_invoicing_body
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
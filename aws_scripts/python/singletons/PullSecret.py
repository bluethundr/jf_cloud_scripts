#Author: AWS and Kevin Scott (DSG)

import boto3
import base64
import sys
from botocore.exceptions import ClientError

def get_secret(profileName,secretName, region):
    secret_name = secretName
    region_name = region

    # Create a Secrets Manager client
    session = boto3.session.Session(profile_name=profileName)
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            print(secret)
            #return secret
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            print(decoded_binary_secret)
            #return decoded_binary_secret

    # If you want to pull and use the api key dynamically, insert your code below here using the variables secret or
    # decoded_binary_secret...dependent on the type of secret.  Otherwise this function will just print to stdout
    # Or you can import this function into your script and uncomment the return lines on line 45/49 to get the secret
    # returned for use

#usage: get_secret(profileName, secretName, region)
get_secret(sys.argv[1], sys.argv[2], sys.argv[3])
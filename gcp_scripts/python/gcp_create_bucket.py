#!/usr/bin/env python

# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from colorama import init, Fore

# Initialize the color ouput with colorama
init()


### Utility Functions
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             Create GCP Buckets                    *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "*  Create GCP Buckets Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

# [START storage_create_bucket_class_location]
from google.cloud import storage


def create_bucket_class_location(bucket_name):
    """Create a new bucket in specific location with storage class"""
    if not bucket_name:
        bucket_name = input("Enter a bucket name: ")
    # bucket_name = "your-new-bucket-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = "COLDLINE"
    new_bucket = storage_client.create_bucket(bucket, location="us")

    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return new_bucket


# [END storage_create_bucket_class_location]

if __name__ == "__main__":
    welcomebanner()
    create_bucket_class_location(bucket_name=None)
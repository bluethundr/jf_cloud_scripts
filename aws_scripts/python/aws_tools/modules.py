#!/usr/bin/env python3
# Import modules
import boto3
import botocore
import argparse
import objectpath
import time
import pprint
import os
import csv
import re
from init import *
import collections
from collections import defaultdict
from aws_tag_resources import tag_instances, tag_root_volumes
from user_input import *
from banners import welcomebanner,endbanner,banner
from datetime import datetime
from colorama import init, deinit, Fore
from list_new_instances import list_new_instances
from read_account_info import read_account_info
from find_vpcs import find_vpcs
from aws_add_sg_list import attach_sg_list
from choose_accounts import choose_accounts

# Initialize the color ouput with colorama
init()
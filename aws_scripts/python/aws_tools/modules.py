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
from init import initialize
from aws_tag_resources import tag_instances, tag_root_volumes
from arguments import *
from user_input import *
from banners import *
from datetime import datetime
from colorama import init, Fore
from list_new_instances import list_new_instances


# Initialize the color ouput with colorama
init()
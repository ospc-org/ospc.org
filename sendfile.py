# python manage.py dumpdata flatblocks --output flatblocks_heroku.json

import boto
from boto.s3.connection import S3Connection
import os

AWS_KEY_ID = os.environ['AWS_KEY_ID']
AWS_SECRET_ID = os.environ['AWS_SECRET_ID']

aws_connection = S3Connection(AWS_KEY_ID, AWS_SECRET_ID)
bucket = aws_connection.get_bucket('pufbucket')

from boto.s3.key import Key
k = Key(bucket)
k.key = 'flatblocks_heroku'

flatblocks_info = open("flatblocks_heroku.json").read()
k.set_contents_from_string(flatblocks_info)

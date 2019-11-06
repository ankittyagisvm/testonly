import sys
from pip._internal import main

main(['install', '-I', '-q', 'boto3', '--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0,'/tmp/')

import boto3
from botocore.exceptions import ClientError

######### upper code is to replace only 'import boto3'
from datetime import date
import datetime
from dateutil.tz import tzutc
from datetime import datetime, timedelta
import os
import smtplib

def send_mail(host, port, username, password, subject, body, mail_to, mail_from = None, reply_to = None):
    if mail_from is None: mail_from = username
    if reply_to is None: reply_to = mail_to
    
    message = """From: %s\nTo: %s\nReply-To:%s\nSubject: %s\n\n%s""" % (mail_from, mail_to, reply_to, subject, body)
    print(message)
    try:
        server = smtplib.SMTP(host, port)
        server.ehlo()
        server.starttls()
        server.login(username, password)
        server.sendmail(mail_from, mail_to.split(','), message)
        server.close()
        return True
    except Exception as ex:
        print(ex)
        return False
        
resource = boto3.resource('iam')
client = boto3.client("iam")

def lambda_handler(event, context):
    for user in resource.users.all():
        Metadata = client.list_access_keys(UserName=user.user_name)
        if Metadata['AccessKeyMetadata'] :
            for key in user.access_keys.all():
                #print(key.user_name, key.id, key.status)
                if key.status == "Active":
                    res = client.list_access_keys(UserName=key.user_name)
                    accesskeydate = res['AccessKeyMetadata'][0]['CreateDate'].date()
                    currentdate = date.today()
                    active_days = currentdate - accesskeydate
                    print (active_days.days)
                    age = str(active_days.days)
                    if active_days.days > 85 and active_days.days < 91:
                        print(key.user_name,"user age is ", active_days.days , " days")
                        Name = key.user_name
                        username = os.environ['USERNAME']
                        password = os.environ['PASSWORD']
                        host = os.environ['SMTPHOST']
                        port = os.environ['SMTPPORT']
                        mail_from = os.environ['MAIL_FROM']
                        #mail_to = os.environ['MAIL_TO']
                        MAIL_id = 'antyagi291@gmail.com'
                        recpt = MAIL_id +',itsmesushil.kumar@gmail.com'
                        mail_to = recpt
                        print(mail_to)
                        #reply_to = os.environ['MAIL_TO']
                        reply_to = 'itsmesushil.kumar@gmail.com'
                        subject = "Access keys deactivation detail of " + Name
                        body = "Dear "+ Name + ",\n\n Your IAM access key age is "+ age +" days.\n Please go to your AWS console for more details.\n\nRegards,\nAnkit Tyagi" 
                            
                        send_mail(host, port, username, password, subject, body, mail_to, mail_from, reply_to)
                            

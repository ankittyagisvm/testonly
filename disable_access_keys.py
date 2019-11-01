import sys
from pip._internal import main

main(['install', '-I', '-q', 'boto3', '--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0,'/tmp/')

import boto3
from botocore.exceptions import ClientError

######### upper code is to replace only 'import boto3'

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
                    for i in range(len(client.list_user_tags(UserName=key.user_name)['Tags'])):
                        if client.list_user_tags(UserName=key.user_name)['Tags'][i]['Key']=='Owner':
                            MAIL_id=client.list_user_tags(UserName=key.user_name)['Tags'][i]['Value']
                    response = client.get_access_key_last_used(
                        AccessKeyId=key.id
                    )
                    if 'LastUsedDate' in response['AccessKeyLastUsed']:
                        #print(response['AccessKeyLastUsed']['LastUsedDate'])
                        User_last_acess=response['AccessKeyLastUsed']['LastUsedDate'].date() # this is when last time key get accessed
                        todays=datetime.now()  #   - timedelta(days=100)  
                        date_only=todays.date()  # todays date
                        use_polcy_diff = (date_only - User_last_acess).days
                        if use_polcy_diff > 90:
                            response = client.update_access_key(
                                UserName = key.user_name,
                                AccessKeyId = key.id,
                                Status='Inactive'
                            )
                            print(key.user_name,"not using his access keys from last", use_polcy_diff, " days")
                            Name = key.user_name
                            username = os.environ['USERNAME']
                            password = os.environ['PASSWORD']
                            host = os.environ['SMTPHOST']
                            port = os.environ['SMTPPORT']
                            mail_from = os.environ['MAIL_FROM']
                            #mail_to = os.environ['MAIL_TO']
                            recpt = MAIL_id +',comscoresupport@3pillarglobal.com'
                            mail_to = recpt
                            print(mail_to)
                            #reply_to = os.environ['MAIL_TO']
                            reply_to = 'comscoresupport@3pillarglobal.com'
                            subject = "Access keys deactivation detail of " + Name
                            body = "Dear "+ Name + ",\n\n You have not used your access keys in last 3 months. As per the policy your keys has been deactived.\n Please go to your AWS console for more details.\n\nRegards,\nAnkit Tyagi" 
                            
                            send_mail(host, port, username, password, subject, body, mail_to, mail_from, reply_to)
                            

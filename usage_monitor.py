""""
Monitor CPU usage per user
"""

#======= PARAMETERS
# maximum CPU threshold allowed 100 correspond to one full core used
MAX_CPU_THRESHOLD = 2000.

# Notification using Gmail account
EMAIL_NOTIFICATION_ENABLED = False
GMAIL_USER = 'aaa@gmail.com'
GMAIL_PASS = 'password'
CONN_TIMEOUT = 30 # timeout to close connection in seconds, raises an exception
#=======



# Imports
import os
import subprocess
import pandas as pd
import smtplib
from email.message import EmailMessage





class Emailer:
    gmail_user = GMAIL_USER
    gmail_password = GMAIL_PASS

    def sendMsg(self, contentTxt, to, subject='Alert' ):
        # Open the plain text file whose name is in textfile for reading.
        msg = EmailMessage()
        msg.set_content(contentTxt)

        # me == the sender's email address
        # you == the recipient's email address
        msg['Subject'] = subject
        msg['From'] = 'LHC server'
        msg['To'] = to

        # Send the message via SMTP server.
        s = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=CONN_TIMEOUT)
        s.ehlo()
        s.login(self.gmail_user, self.gmail_password)

        s.send_message(msg)
        s.quit()



def getUsers():
    """
    List all users including root
    """
    usrLst = os.listdir('/home')
    usrLst.append('root')
    return usrLst


def getCpuUsage(usersIn):
    res =  subprocess.run( ['(lscpu | grep "^CPU(s):" | awk \'{print $2}\')'], check=True, shell=True, stdout=subprocess.PIPE )
    cpuNum = int(res.stdout)


    usageDic = {'user':[],'totCpuUsage':[], 'CpuUsageRatio':[]}

    for userTmp in usersIn:
        # userTmp = 'lgiancardo'
        cmd = "(top -b -n 1 -u \"{0:}\" | awk -v user=\"{0:}\" -v CPUS={1:} 'NR>7 {{ sum += $9; }} END {{ if (sum > 0.0) print user, sum, sum/CPUS; }}')".format(userTmp,cpuNum)
        res =  subprocess.run( [cmd], check=True, shell=True, stdout=subprocess.PIPE )
        tok = res.stdout.decode("utf-8").strip().split(' ')
        if len(tok)==3: # user found
            usageDic['user'].append(tok[0])
            usageDic['totCpuUsage'].append(float(tok[1]))
            usageDic['CpuUsageRatio'].append(float(tok[2]))

    return pd.DataFrame(usageDic)


# find users based on home directory
userLst = getUsers()

#  emails for notification
emailsFr = pd.read_csv('email_lst.csv')

# get current CPU usage
usageFr = getCpuUsage( userLst )

# merge
usageFr = usageFr.merge(emailsFr, on='user', how='left')


# check exceeded usage and notify
overusageFr = usageFr[usageFr['totCpuUsage'] > MAX_CPU_THRESHOLD]

#list users above threshold and notify them
em = Emailer()
for r in range(len(overusageFr)):
    usr=overusageFr.iloc[r]
    msg = 'user {:} is at {:}% CPU usage for this machine'.format(usr['user'], usr['totCpuUsage']) 

    print(msg)
    if EMAIL_NOTIFICATION_ENABLED:
        em.sendMsg(msg,usr['email'])
    else:
        print('notification email not sent')

    
#!/usr/bin/env python

import subprocess
import os

'''
thin wrapper for sending an email from orchestra or ec2 or laptop using the
'mail' command.
'''

def sendmail(fromAddr, toAddrs, subject, message, method=None):
    '''
    fromAddr: email string of who is the mail coming from.  
    toAddrs: list of email addresses
    subject: string
    message: string
    method: determines how the fromAddr is set.
      if None, does not attempt to set the fromAddr of the email.
      if 'qmail', uses mail command, setting qmail env vars to set mail sender
      and host.  this works from orchestra nodes (balcony, trumpet, compute
      nodes, etc.)
      if 'sendmail', uses mail command with -r option to set sender email
      address.  this works from ec2 basic linux instance.
    raises: exception if sending mail returns a non-zero return code.
    '''
    env = {}
    env.update(os.environ)
    fromArgs = []
    if method == 'qmail':
        # -r option does not work, but these env vars can be used to set the sender/from address.
        mailUser, mailHost = fromAddr.split('@')
        env['MAILUSER'] = str(mailUser)
        env['MAILHOST'] = str(mailHost)
        env['QMAILINJECT'] = 'f'
    if method == 'sendmail':
        # the env vars do not work, but -r does.  go figure.
        fromArgs = ['-r', fromAddr]

    # command contains subject and who the mail goes to
    args = ['mail', '-s', subject] + fromArgs + toAddrs
    p = subprocess.Popen(args, env=env, stdin=subprocess.PIPE)

    # stdin contains the body of the mail.
    p.communicate(str(message)+'\n')
    if p.returncode != 0:
        raise Exception('Non-zero return code when sending mail', p.returncode, fromAddr, toAddrs, subject, message, method)
    


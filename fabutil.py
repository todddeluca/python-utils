
'''
FABRIC UTILITY FUNCTIONS
'''

import os
import subprocess


import fabric.api
from fabric.api import env
import fabric.contrib.files

# http://stackoverflow.com/questions/6725244/running-fabric-script-locally
def setremote():
    env.run = fabric.api.run
    env.cd = fabric.api.cd
    env.rsync = rsync
    env.exists = fabric.contrib.files.exists
    return env

def setlocal():
    env.run = fabric.api.local
    env.cd = fabric.api.lcd
    env.rsync = lrsync
    env.exists = os.path.exists
    return env


def file_format(infile, outfile, args=None, keywords=None):
    '''
    Read the contents of infile as a string, format the string using args and keywords,
    and write the formatted string to outfile
    This is useful if infile is a "template" and args and keywords contain the concrete
    values for the template.
    '''
    if args is None:
        args = []
    if keywords is None:
        keywords is {}
    with open(infile) as fh:
        text = fh.read()
    new_text = text.format(*args, **keywords)
    with open(outfile, 'w') as fh2:
        fh2.write(new_text)
    

def lrsync(options, src, dest, cwd=None, **kwds):
    '''
    options: list of rsync options, e.g. ['--delete', '-avz']
    src: source directory (or files).  Note: rsync behavior varies depending on whether or not src dir ends in '/'.
    dest: destination directory.
    cwd: change (using subprocess) to cwd before running rsync.
    This is a helper function for using rsync to sync files to localhost.
    It uses subprocess.  Note: shell=False.
    Use rsync() to sync files to a remote host.
    '''
    args = ['rsync'] + options + [src, dest]
    print args
    subprocess.check_call(args, cwd=cwd)
    
    
def rsync(options, src, dest, user=None, host=None, cwd=None):
    '''
    options: list of rsync options, e.g. ['--delete', '-avz']
    src: source directory (or files).  Note: rsync behavior varies depending on whether or not src dir ends in '/'.
    dest: destination directory.
    cwd: change (using subprocess) to cwd before running rsync.
    This is a helper function for running rsync locally, via subprocess.  Note: shell=False.
    '''
    # if remote user and host specified, copy there instead of locally.
    if user and host:
        destStr = '{}@{}:{}'.format(user, host, dest)
    else:
        destStr = dest

    args = ['rsync'] + options + [src, destStr]
    print args
    subprocess.check_call(args, cwd=cwd)
    


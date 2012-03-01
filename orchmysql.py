'''
The module contains functionality to get mysql credentials and mysql connection objects on the orchestra system.
FromAnywhere means first checking in the environment and then looking in a credentials file.
An application using this module will typically do some of the following to get credentials:
  set up some credentials in a configuration file (e.g. host) an application specific and deployment environment specific manner;
  get some creds from the environment, like creds set up by a web server;
  get some creds from a DEFAULT_CREDS_FILE, especially when the application is not used via the web server.
Once credentials are obtained, an application will typically use them to get a connection to the mysql database.
'''

import contextlib
import MySQLdb
import os

DEFAULT_CREDS_FILE = '.my.cnf' # in HOME dir.  

######################
# DATABASE CREDENTIALS
######################


def getCredsFromAnywhere(hostKey, dbKey, userKey, passwordKey, credsFile=None, environ=os.environ):
    host = getHostFromAnywhere(hostKey, credsFile, environ=environ)
    db = getDbFromAnywhere(dbKey, credsFile, environ=environ)
    user = getUserFromAnywhere(userKey, credsFile, environ=environ)
    password = getPasswordFromAnywhere(passwordKey, credsFile, environ=environ)
    return {'host': host, 'db': db, 'user': user, 'password': password}
    

def getHostFromAnywhere(key, credsFile=None, environ=os.environ):
    if environ.has_key(key):
        return environ[key]
    return getCnf(credsFile)['host']


def getDbFromAnywhere(key, credsFile=None, environ=os.environ):
    if environ.has_key(key):
        return environ[key]
    return getCnf(credsFile)['database']    


def getUserFromAnywhere(key, credsFile=None, environ=os.environ):
    if environ.has_key(key):
        return environ[key]
    if environ.has_key('USER'):
        return environ['USER']
    if environ.has_key('LOGNAME'):
        return environ['LOGNAME']
    else:
        raise Exception('Missing USER and LOGNAME env vars. ')


def getPasswordFromAnywhere(key, credsFile=None, environ=os.environ):
    if environ.has_key(key):
        return environ[key]
    return getCnf(credsFile)['password']

# cache cnf creds b/c reading file is expensive.  premature optimization?
CNF_CACHE = []
def getCnf(credsFile=None):
    if not CNF_CACHE:
        if credsFile is None:
            credsFile = os.path.join(os.environ['HOME'], DEFAULT_CREDS_FILE)
        cnf = parseCnfFile(credsFile)
        CNF_CACHE.append(cnf)
    return CNF_CACHE[0]


def parseCnfFile(path):
    # read cnf config file into a dict
    cnf = {}
    if os.path.isfile(path):
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                continue
            if '=' in line:
                key, value = [piece.strip() for piece in line.split('=', 1)]
                cnf[key] = value
    return cnf    


######################
# DATABASE CONNECTIONS
######################


@contextlib.contextmanager
def connCM(host, db, user, password):
    try:
        conn = openConn(host, db, user, password)
        yield conn
    finally:
        conn.close()
        

def openConn(host, db, user, password):
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)


# last line

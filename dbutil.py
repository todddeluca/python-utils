#!/usr/bin/env python

'''
Code to work with python DB API v2.0 Connection and Cursor objects. (http://www.python.org/dev/peps/pep-0249/)
No RDBMS specific code should be in here.
No Orchestra specific code.
No application (rodeo, roundup, genotator, etc.) specific code.

Things this module does not do:
  Get connections, since that is specific to the database server being used (MySQL, Oracle, etc.)
  Generate SQL, since that can be database-specific too. (some exceptions might apply.)
'''

import contextlib
import logging


class Reuser(object):
    '''
    An instance is a callable object that returns an open connection.  Multiple
    calls will return the same connection, if the connection is still "live".
    It will open a new connection if no connection is open yet or the existing
    connection is closed (or otherwise fails to be pinged.)
    This object is meant to handle two common scenarios with one API.
    * Opening and closing a connection very rapidly can cause a database to
      balk.  Reuser allows a process to open one connection and reuse it.
    * A connection kept open a long time can be closed by the database. 
      Reuser will open a new connection when the existing connection can
      not be reused.

    '''
    def __init__(self, open_conn):
        '''
        open_conn: function that returns an open connection
        '''
        self.open_conn = open_conn
        self.conn = None

    def __call__(self):
        '''
        returns: an open db connection, opening one if necessary.
        '''
        if not self._ping():
            self.conn = self.open_conn()
        return self.conn

    def _ping(self):
        '''
        returns: True if there is an active connection.  False otherwise.
        '''
        if self.conn:
            try:
                selectSQL(self.conn, 'SELECT 1')
                return True
            except Exception as e: 
                # OperationalError 2006 happens when the db connection times
                # out.
                if not e.args or e.args[0] != 2006:
                    # only log non-2006 execptions
                    logging.exception('Exception encountered when pinging connection in Reuser._ping.')
                return False
        else:
            return False


@contextlib.contextmanager
def doTransaction(conn, start=True, startSQL='START TRANSACTION'):
    '''
    wrap a connection in a transaction.  starts a transaction, yields the conn, and then if an exception occurs, calls rollback().  otherwise calls commit().
    start: if True, executes 'START TRANSACTION' sql before yielding conn.  Useful for connections that are autocommit by default.
    startSQL: override if 'START TRANSACTION' does not work for your db server.
    '''
    try:
        if start:
            executeSQL(conn, startSQL)
        yield conn
    except:
        conn.rollback()
        raise
    else:
        conn.commit()


@contextlib.contextmanager
def doCursor(conn):
    '''
    create and yield a cursor, closing it when done.
    '''
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
    

def selectSQL(conn, sql, args=None):
    '''
    sql: a select statement
    args: if sql has parameters defined with either %s or %(key)s then args should be a either list or dict of parameter
    values respectively.
    returns a tuple of rows, each of which is a tuple.
    '''
    with doCursor(conn) as cursor:
        cursor.execute(sql, args)
        results = cursor.fetchall()
        return results


def insertSQL(conn, sql, args=None):
    '''
    args: if sql has parameters defined with either %s or %(key)s then args should be a either list or dict of parameter
    values respectively.
    returns the insert id
    '''
    with doCursor(conn) as cursor:
        cursor.execute(sql, args)
        id = conn.insert_id()
        return id


def updateSQL(conn, sql, args=None):
    '''
    args: if sql has parameters defined with either %s or %(key)s then args should be a either list or dict of parameter
    values respectively.
    returns the number of rows affected by the sql statement
    '''
    with doCursor(conn) as cursor:
        numRowsAffected = cursor.execute(sql, args)
        return numRowsAffected


def executeSQL(conn, sql, args=None):
    '''
    args: if sql has parameters defined with either %s or %(key)s then args should be a either list or dict of parameter
    values respectively.
    executes sql statement.  useful for executing statements like CREATE TABLE or RENAME TABLE,
    which do not have an result like insert id or a rowset.
    returns: the number of rows affected by the sql statement if any.
    '''
    with doCursor(conn) as cursor:
        numRowsAffected = cursor.execute(sql, args)
        return numRowsAffected
    

def executeManySQL(conn, sql, args=None):
    '''
    args: list of groups of arguments.  if sql has parameters defined with either %s or %(key)s then groups should be a either lists or dicts of parameter
    values respectively.
    returns: not sure.  perhaps number of rows affected.
    '''
    with doCursor(conn) as cursor:
        retval = cursor.executemany(sql, args)
        return retval



# last line

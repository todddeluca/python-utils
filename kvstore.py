'''
Simple homebrewed key-value store.  Use a real KV store, not this one.

Features:
    Can use a RDBMS like MySQL to implement the ULTIMATE in distributed,
    persistent, atomic and concurrent experiences. :-)
    Keys are strings.
    Values are serialized as json, which supports lists, dicts, strings,
    numbers, None, and booleans.  http://www.json.org/

Design Goals:
    no dependency on a specific RDBMS.  
    atomic, process-level concurrency-safe, though that depends on your RDMBS.
    For example SQLite is not concurrency safe when files reside on NFS.  See
    http://sqlite.org/faq.html#q5 for more details.

Warnings: 
    No thread-safety guarantees.

Usage:
Wrap a connection or a factory function in a context manager like util.NoopCM
or util.ClosingFactoryCM.

The following code illustrates creating a queue which gets a new connection for each operation by using the ClosingFactoryCM context manager.
It demonstrates putting, getting, removing, and checking for the existence of keys and values.
Here config.openDbConn is a function that returns a python db api v2 connection.
python -c'
import kvstore, util, config;
kv = kvstore.KVStore(util.ClosingFactoryCM(config.openDbConn), drop=True, create=True)
kv.put("hi", "test")
print kv.get("bye")
print kv.get("hi")
print kv.exists("hi")
print kv.exists("bye")
print kv.remove("hi")
print kv.exists("hi")
print kv.get("hi", "missing")
print kv.remove("bye")
'
'''

import json

import dbutil


def testKVStore():
    import kvstore, util, config;
    kv = kvstore.KVStore(util.ClosingFactoryCM(config.openDbConn)).drop().create()
    kv.put("hi", "test")
    print kv.get("bye")
    print kv.get("hi")
    print kv.exists("hi")
    print kv.exists("bye")
    print kv.remove("hi")
    print kv.exists("hi")
    print kv.get("hi", "missing")
    print kv.remove("bye")
    kv.drop()
    

class KVStore(object):
    '''
    A key-value store backed by a relational database. e.g. mysql.
    Upon first using a namespace, call create() to initialize the table.
    When done using a namespace, call drop() to drop the table.
    '''
    def __init__(self, manager, ns=None):
        '''
        manager: context manager yielding a Connection.
          Typical managers are cmutil.Noop(conn) to reuse a connection or cmutil.ClosingFactory(getConnFunc) to use a new connection each time.
        ns: the "namespace" of the keys.  should be a valid mysql table name.  defaults to 'key_value_store'.
        '''
        self.manager = manager
        self.table = ns if ns is not None else 'key_value_store'


    def create(self):
        sql = '''CREATE TABLE IF NOT EXISTS ''' + self.table + ''' ( 
                 id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                 name VARCHAR(255) NOT NULL UNIQUE KEY,
                 value blob,
                 create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 INDEX key_index (name) 
                 ) ENGINE = InnoDB '''
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                dbutil.executeSQL(conn, sql)
        return self
    
        
    def drop(self):
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                dbutil.executeSQL(conn, 'DROP TABLE IF EXISTS ' + self.table)
        return self


    def reset(self):
        return self.drop().create()
    

    def get(self, key, default=None):
        encodedKey = json.dumps(key)
        with self.manager as conn:
            sql = 'SELECT value FROM ' + self.table + ' WHERE name = %s'
            results = dbutil.selectSQL(conn, sql, args=[encodedKey])
            if results:
                value = json.loads(results[0][0])
            else:
                value = default
            return value


    def put(self, key, value):
        encodedKey = json.dumps(key)
        encodedValue = json.dumps(value)
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                sql = 'INSERT INTO ' + self.table + ' (name, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s'
                return dbutil.insertSQL(conn, sql, args=[encodedKey, encodedValue, encodedValue])


    def exists(self, key):
        encodedKey = json.dumps(key)
        with self.manager as conn:
            sql = 'SELECT id FROM ' + self.table + ' WHERE name = %s'
            results = dbutil.selectSQL(conn, sql, args=[encodedKey])
            return bool(results) # True if there are any results, False otherwise.


    def remove(self, key):
        encodedKey = json.dumps(key)
        sql = 'DELETE FROM ' + self.table + ' WHERE name = %s'
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                return dbutil.executeSQL(conn, sql, args=[encodedKey])
            

def testKStore():
    import util
    import config
    completes = KStore(manager=util.ClosingFactoryCM(config.openDbConn), ns='kstore_test')
    try:
        print completes.exists('test')
    except Exception:
        print 'exists fails b/c table is missing'
    completes.create()
    completes.create()
    print completes.exists('test')
    print completes.add('test')
    print completes.add('test')
    print completes.exists('test')
    print completes.exists('test')
    print completes.remove('test')
    print completes.remove('test')
    print completes.exists('test')
    print completes.add('test')
    print completes.exists('test')
    print completes.reset()
    print completes.exists('test')
    print completes.drop()
    try:
        print completes.exists('test')
    except Exception:
        print 'exists fails b/c table is missing'

    
class KStore(object):
    '''
    Key-value store too complicated?  This class implements a key store.
    It uses KVStore to manage a set of keys within a namespace.
    '''

    def __init__(self, manager, ns=None):
        '''
        manager: context manager yielding a Connection.
          Typical managers are cmutil.Noop(conn) to reuse a connection or cmutil.ClosingFactory(getConnFunc) to use a new connection each time.
        ns: the "namespace" of the keys.  should be a valid mysql table name.  defaults to 'key_store'.
        '''
        self.manager = manager
        self.ns = ns if ns is not None else 'key_store'
        self.kv = KVStore(self.manager, ns=self.ns)

    def exists(self, key):
        '''
        returns: True if the key is in the namespace.  False otherwise.
        '''
        return self.kv.exists(key)

    def add(self, key):
        '''
        add key to the namespace.  it is fine to add a key multiple times.
        '''
        self.kv.put(key, True)

    def remove(self, key):
        '''
        remove key from the namespace.  it is fine to remove a key multiple times.
        '''
        self.kv.remove(key)

    def create(self):
        '''
        readies the namespace for new marks
        '''
        # self.kv = KVStore(self.manager, ns=self.ns).create()
        self.kv.create()
        return self

    def reset(self):
        '''
        clears all marks from the namespace and readies it for new marks
        '''
        # self.kv = KVStore(self.manager, ns=self.ns).drop().create()
        self.kv.reset()
        return self

    def drop(self):
        '''
        clears all marks from the namespace and cleans it up.
        '''
        # self.kv = KVStore(self.manager, ns=self.ns).drop()
        self.kv.drop()
        return self


# last line




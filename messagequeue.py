'''
A persistent message queuing module that can be used by concurrent, distributed processes.
Uses RDBMS (e.g. MySQL) to implement the distributed, persistent, atomic and
concurrent experience. ;-)
This queue is inspired by Amazon Simple Queue Service (SQS), where any number of actors can send messages to a queue or read messages from a queue.
Fault-tolerance is implemented by locking messages read by an actor.  If an actor successfully processes a message it should delete it.
If an actor dies mysteriously, the read lock will timeout eventually and another actor will be able to read the message.

Design Goals:
    no dependency on a specific RDBMS.  
    atomic, process-level concurrency-safe.

Warning: 
    no thread-safety guarantees.
Inspiration: 
    Amazon SQS.

Usage:
Wrap a connection or a factory function in a context manager like util.NoopCM or
util.ClosingFactoryCM.
Create a MessageQueue instance or create and cache it in the module using setQueue().
Put messages on the queue.  Pop them off, either one at a time or with the generator function popGen().

The following code illustrates creating a queue which gets a new connection for each operation by using the ClosingFactory context manager.
It illustrates the prescribed idioms for reading messages, either in a for loop or with statement.
This way the state of the message queue is gracefully managed in the face of success or exceptions.

python -c'
import messagequeue, util, config;
q = messagequeue.MessageQueue("test", util.ClosingFactoryCM(config.openDbConn))
[q.send(i*i) for i in range(10)]
for m in q.readAll():
    print repr(m)
with q.read(default="empty") as m:
    print repr(m)
q.send(None)
with q.read() as m:
    print repr(m)
with q.read() as m:
    print repr(m)
'
'''


import contextlib

import dbutil


DEFAULT_LOCK_TIMEOUT = 24 * 60 * 60 # 1 day


class EmptyQueueError(Exception):
    '''
    Exception used to indicate that a queue currently has no messages.
    '''
    pass


class MessageQueue(object):
    def __init__(self, queue, manager, timeout=DEFAULT_LOCK_TIMEOUT, drop=False, create=False):
        '''
        queue: name of queue from which to send and read messages
        manager: context manager yielding a Connection.
          Typical managers are util.NoopCM(conn) to reuse a connection or
          util.ClosingFactoryCM(getConnFunc) to use a new connection each time.
        timeout: It is important that timeout be longer than it takes a
          consumer to process a message and delete it or else the message might
          be read and processed twice.
          Used to recover a message when a consumer dies while processing a
          message and before deleting it.
        '''
        self.manager = manager
        self.queue = queue
        self.timeout = timeout
        if drop:
            self._drop()
        if create:
            self._create()

    def _create(self):
        sql = '''CREATE TABLE IF NOT EXISTS message_queue ( 
                 id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                 queue varchar(200) NOT NULL, 
                 message blob,
                 create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 read_time TIMESTAMP,
                 lock_time TIMESTAMP,
                 timeout INT NOT NULL,
                 locked BOOLEAN NOT NULL DEFAULT FALSE,
                 INDEX queue_index (queue) 
                 ) ENGINE = InnoDB '''
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                dbutil.executeSQL(conn, sql)

    def _drop(self):
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                dbutil.executeSQL(conn, 'drop table if exists message_queue')

    def send(self, message, timeout=None):
        '''
        timeout: if None, the default read lock timeout is used.  if not None, this is the number of seconds before the read lock on this message expires.
        '''
        if timeout is None:
            timeout = self.timeout
        sql = 'INSERT INTO message_queue (queue, message, timeout) VALUES (%s, %s, %s)'
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                return dbutil.insertSQL(conn, sql, args=[self.queue, message, timeout])

    @contextlib.contextmanager
    def read(self, **keywords):
        '''
        Context Manager for use in with statement.  Yields a message from queue.  Message is automatically deleted from queue when with block exits.
        If an exception occurs, the message read-lock timeout is set to 0. (i.e. message is instantly available for reading.)
        default: keyword only argument.  if no messages on queue, default returned instead of EmptyQueueError exception being raised.
        '''
        try:
            i, m = self._readUnhandled()
        except EmptyQueueError:
            if keywords.has_key('default'):
                yield keywords['default']
            else:
                raise
        else:
            with self._handled(i, m) as m:
                yield m

    def readAll(self):
        '''
        Generator for use in for statement.  Yields messages from queue.  Messages are automagically deleted from queue when the yield returns.
        If an exception occurs, the last message read-lock timeout is set to 0. (i.e. message is instantly available for reading.)
        '''
        for i, m in self._readAllUnhandled():
            with self._handled(i, m) as m:
                yield m

    @contextlib.contextmanager
    def _handled(self, id, message):
        try:
            yield message
        except:
            print 'here'
            self.changeTimeout(id, 0)
            raise
        else:
            self.delete(id)
    
    def _readUnhandled(self):
        '''
        Reads the next message from the queue.
        Returns: message_id, message.
        Use message_id to delete() the message when done or to changeTimeout() of the message if necessary.
        '''
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                # read first available message (pending or lock timeout)
                sql = 'SELECT id, message FROM message_queue WHERE queue = %s AND (NOT locked OR  lock_time < CURRENT_TIMESTAMP)'
                sql += ' ORDER BY id ASC LIMIT 1 FOR UPDATE '
                results = dbutil.selectSQL(conn, sql, args=[self.queue])
                if results:
                    id, message = results[0]
                    # mark message unavailable for reading for timeout seconds.
                    sql = 'UPDATE message_queue SET locked = TRUE, read_time = CURRENT_TIMESTAMP, lock_time = ADDTIME(CURRENT_TIMESTAMP, SEC_TO_TIME(timeout)) WHERE id = %s'
                    dbutil.executeSQL(conn, sql, args=[id])
                    return id, message
                else:
                    raise EmptyQueueError(str(self.queue))

    def _readAllUnhandled(self):
        while 1:
            try:
                yield self._readUnhandled()
            except EmptyQueueError:
                break

    def delete(self, id):
        sql = 'DELETE FROM message_queue WHERE id = %s '
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                return dbutil.executeSQL(conn, sql, args=[id])

    def changeTimeout(self, id, timeout):
        ''' changes read lock to <timeout> seconds from now. '''
        sql = 'UPDATE message_queue SET lock_time = ADDTIME(CURRENT_TIMESTAMP, SEC_TO_TIME(%s)) WHERE id = %s'
        with self.manager as conn:
            with dbutil.doTransaction(conn):
                return dbutil.executeSQL(conn, sql, args=[timeout, id])


# last line




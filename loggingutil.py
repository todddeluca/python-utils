'''
Utilities for using the logging module.
'''


import email.mime.text
import email.utils
import logging
import os
import smtplib


class MailHandler(logging.Handler):
    def __init__(self, fromaddr, toaddrs, subject, sendmail, mail_options=None,
            rcpt_options=None):
        ''' 
        fromaddr: an RFC 822 address string
        toaddrs: a list of RFC 822 address strings
        subject: text of the subject line
        sendmail: a callable with the same signature as smtplib.SMTP.sendmail
          sendmail(from_addr, to_addrs, msg[, mail_options, rcpt_options])

        Looking at smtplib and real-world practice, there are such a
        diversity of ways to connect to SMTP servers -- with or without a 
        keyfile or a keyfile and certfile, with or without starttls or
        immediately with ssl, with or without authentication, once for each
        email sent or once for a batch of emails, through a command line client
        or an HTTP API (e.g. MailChimp, Amazon SES), etc.
        Using sendmail as a proxy keeps this complexity out of this class.

        mail_options: a list of options passed to smtplib.SMTP.sendmail()
        rcpt_options: a list of options passed to smtplib.SMTP.sendmail()
        '''
        logging.Handler.__init__(self)
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject
        self.sendmail = sendmail
        self.mail_options = mail_options if mail_options is not None else []
        self.rcpt_options = rcpt_options if rcpt_options is not None else []

    def emit(self, record):
        body = self.format(record)
        msg = email.mime.text.MIMEText(body)
        msg['Date'] = email.utils.formatdate()
        msg['From'] = self.fromaddr
        msg['To'] = ','.join(self.toaddrs)
        msg['Subject'] = self.subject
        msg = msg.as_string()

        self.sendmail(self.fromaddr, self.toaddrs, msg,
                self.mail_options, self.rcpt_options)


class ConcurrentFileHandler(logging.Handler):
    """
    A handler class which writes logging records to a file.  Every time it
    writes it opens, writes, flushes, and closes the file.
    So do not use in a tight loop.  This is an attempt to overcome concurrent
    write issues that the standard logging FileHandler has
    when multiple processes on the cluster try to log messages.
    """
    def __init__(self, filename, mode="a"):
        """
        Open the specified file and use it as the stream for logging.
        """
        logging.Handler.__init__(self)
        # keep the absolute path, otherwise derived classes which use this
        # may come a cropper when the current directory changes
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode

    def openWriteClose(self, msg):
        f = open(self.baseFilename, self.mode)
        f.write(msg)
        f.flush() # improves consistency of writes in a concurrent environment (Orchestra cluster)
        f.close()

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline
        [N.B. this may be removed depending on feedback]. If exception
        information is present, it is formatted using
        traceback.print_exception and appended to the stream.
        """
        try:
            msg = self.format(record)
            fs = "%s\n"
            self.openWriteClose(fs % msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class ClusterMailHandler(logging.Handler):
    '''
    Deprecated.  Use MailHandler, passing it the appropriate server object.
    Email log messages using sendmail module, which can mail from EC2 and
    Orchestra nodes.
    '''

    def __init__(self, fromAddr, toAddrs, subject, method):
        import sendmail
        logging.Handler.__init__(self)
        self.fromAddr = fromAddr
        self.toAddrs = toAddrs
        self.subject = subject
        self.method = method

    def emit(self, record):
        """
        Emit a record.
        
        Format the record and send it to the specified addressees.
        """
        try:
            msg = self.format(record)
            sendmail.sendmail(self.fromAddr, self.toAddrs, self.subject, message=msg, method=self.method)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)






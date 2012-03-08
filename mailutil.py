
'''
Helper functions and classes for sending a text email via an SMTP server.

Standard SMTP ports
  http://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol#Ports
  25 - for unencrypted SMTP, or SMTP+TLS.  sometimes blocked by ISPs
  587 - alternative for port 25
  465 - used for SMTP over SSL.

Enhancements
  Sending multiple emails per connection.
  Sending multipart mime emails or other non-plaintext emails.

Notes
  fromAddr is handled differently by different SMTP servers.  
  Some servers, e.g. smtp.gmail.com, replace the from address with the address 
  of the authenticated user.
  Some servers, e.g. from AWS SES, only allow a verified address.
  Some servers, e.g. from AWS SES, append a 'via ...' to the from address.

Usage Example
import smtputil
s = smtputil.SMTP("smtp.example.com")
s.send("testing@example.com", ["anyone@example.com"], "testing", 
       "hi from orchestra")

Useful links
http://docs.python.org/library/smtplib.html
http://hg.python.org/cpython/file/2.7/Lib/smtplib.py
http://mynthon.net/howto/-/python/python%20-%20logging.SMTPHandler-how-to-use-gmail-smtp-server.txt
http://docs.python.org/library/logging.handlers.html#smtphandler
http://hg.python.org/cpython/file/2.7/Lib/logging/handlers.py

'''

import email.mime.text
import email.utils
import smtplib


def make_sendtextmail(sendmail):
    '''
    sendmail: a callable with the smtplib.SMTP.sendmail signature, which will
    send a single email message.

    returns: A function that takes a from address, a list of to addresses, a
    text subject and body, an optional list of cc addresses, an optional list
    of mail options, and an optional list of rcpt options. The function then
    formats and email message and sends it with sendmail.
    '''
    def sendtextmail(from_addr, to_addrs, subject, body, cc_addrs=None,
            mail_options=None, rcpt_options=None):
        '''
        from_addr: an RFC 822 from-address string
        to_addrs: a list of RFC 822 to-address strings
        subject: text of the subject line
        body: text of the message body
        cc_addrs: a list of RFC 822 address strings.
        Boilerplate for composing and sending a single plaintext message.
        http://stackoverflow.com/questions/1546367/python-how-to-send-mail-with-to-cc-and-bcc
        '''
        from_addr, to_addrs, msg = formattextmail(from_addr, to_addrs,
                subject, body, cc_addrs)
        return sendmail(from_addr, to_addrs, msg, mail_options, rcpt_options)
    return sendtextmail


def formattextmail(from_addr, to_addrs, subject, body, cc_addrs=None):
    '''
    from_addr: an RFC 822 from-address string
    to_addrs: a list of RFC 822 to-address strings
    subject: text of the subject line
    body: text of the message body
    cc_addrs: a list of RFC 822 address strings.
    Format a simple text message as an email.  
    Returns: tuple of from_addr, the new to_addrs list (which includes any
    cc_addrs), and the formatted email message as a string.
    '''
    
    cc_addrs = cc_addrs if cc_addrs is not None else []
    msg = email.mime.text.MIMEText(str(body))
    msg['Date'] = email.utils.formatdate()
    msg['From'] = str(from_addr)
    msg['To'] = ','.join((str(addr) for addr in to_addrs))
    if cc_addrs:
        msg['CC'] = ','.join(cc_addrs)
    msg['Subject'] = str(subject)
    return (from_addr, to_addrs + cc_addrs, msg.as_string())


class SMTP(object):
    '''
    Send a text email via SMTP.
    '''
    def __init__(self, host=None, port=None, local_hostname=None, timeout=None,
            username=None, password=None):
        '''
        username and password: if both are not None, will attempt to login to
        SMTP server after connecting.
        Note: does not open the connection.
        '''
        self.host = host
        self.port = port
        self.local_hostname = local_hostname
        self.timeout = timeout
        self.username = username
        self.password = password
        self.isopen = False
        self.server = None

    def init_server(self):
        '''
        create smtplib server object if it does not already exist.
        '''
        if not self.server:
            # send None as host so smtplib does not connect to host immediately.
            args = [None]
            args += [arg for arg in [self.port, self.local_hostname,
                self.timeout] if arg]
            self.server = smtplib.SMTP(*args)

    def connect(self):
        '''
        open a connection to the SMTP server, if it is not already open.
        '''
        self.init_server()
        if not self.isopen:
            self.server.connect(self.host, self.port)
            self.isopen = True

    def login(self):
        '''
        authenticate with server, if self has a username and password 
        '''
        if self.username and self.password:
            self.server.login(self.username, self.password)

    def sendmail(self, from_addr, to_addrs, msg, mail_options=None, rcpt_options=None):
        '''
        Send an email via the open smtp server connection.  
        You must open the connection first.
        from_addr: an RFC 822 from-address string
        to_addrs: a list of RFC 822 to-address strings
        msg: a string reprentation of an email message.
        mail_options : List of ESMTP options (such as 8bitmime) for the mail
        command.
        rcpt_options : List of ESMTP options (such as DSN commands) for all the
        rcpt commands.
        '''
        args = [from_addr, to_addrs, msg]
        if mail_options:
            args.append(mail_options)
        if rcpt_options:
            args.append(rcpt_options)
        return self.server.sendmail(*args)

    def quit(self):
        '''
        close the connection to the SMTP server, if it is not already closed.
        '''
        if self.isopen:
            self.server.quit()
            self.isopen = False

    def sendone(self, from_addr, to_addrs, msg, mail_options=None,
            rcpt_options=None):
        '''
        Connect to server, send an email, and disconnect.
        '''
        try:
            self.connect()
            self.login()
            self.sendmail(from_addr, to_addrs, msg, mail_options, rcpt_options)
        finally:
            self.quit()


class SMTPSSL(SMTP):
    '''
    Send a text email via SMTP+SSL.
    '''
    def __init__(self, host=None, port=None, local_hostname=None, keyfile=None,
            certfile=None, timeout=None, username=None, password=None):
        SMTP.__init__(self, host, port, local_hostname, timeout, username,
                password)
        self.keyfile = keyfile
        self.certfile = certfile

    def init_server(self):
        '''
        create smtplib server object if it does not already exist.
        '''
        if not self.server:
            # send None as host so smtplib does not connect to host immediately.
            args = [None]
            args += [arg for arg in [self.port, self.local_hostname,
                self.keyfile, self.certfile, self.timeout] if arg]
            self.server = smtplib.SMTP_SSL(*args)


class SMTPTLS(SMTP):
    '''
    For servers that want an encrypted session (TLS) started after the initial
    connection.
    '''
    def __init__(self, host=None, port=None, local_hostname=None, keyfile=None,
            certfile=None, timeout=None, username=None, password=None):
        SMTP.__init__(self, host, port, local_hostname, timeout, username,
                password)
        self.keyfile = keyfile
        self.certfile = certfile

    def connect(self):
        '''
        Connect to SMTP server and then start a TLS session.
        '''
        SMTP.connect(self)
        args = [arg for arg in [self.keyfile, self.certfile] if arg]
        self.server.starttls(*args)




def main():
    import sys
    import getpass
    print 'test sending via SMTP[SSL,TLS]. include the following arguments:'
    print 'method, host, port, from_addr, to_addr, subject, body[, username]'
    method, host, port, from_addr, to_addr, subject, body = sys.argv[1:8]
    if method == 'SMTP':
        s = SMTP(host, port)
    elif method == 'SMTPSSL':
        username = sys.argv[8]
        password = getpass.getpass('password:')
        s = SMTPSSL(host, port, username=username, password=password)
    elif method == 'SMTPTLS':
        username = sys.argv[8]
        password = getpass.getpass('password:')
        s = SMTPTLS(host, port, username=username, password=password)
    
    sendmail = make_sendtextmail(s.sendone)
    print 'Sending mail and printing which recipients were refused by the SMTP server?'
    print sendmail(from_addr, [to_addr], subject, body)


if __name__ == '__main__':
    main()




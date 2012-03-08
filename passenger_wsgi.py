'''
Use Phusion Passenger to run a Python WSGI application.
'''
import datetime
import os
import sys
import traceback

# substitute a python executable for the default one used by passenger/apache.
PYTHON_EXE = '/usr/bin/python2.7'
if sys.executable != PYTHON_EXE:
    os.execl(PYTHON_EXE, PYTHON_EXE, *sys.argv)


def exceptionLoggingMiddleware(application, logfile):
    '''
    very basic exception logging middleware application which could be useful
    if you are able to get this module to run, but your app can not respond to
    requests for some reason and it is not able to log why.
    '''
    def logApp(environ, start_response):
        try:
            return application(environ, start_response)
        except:
            fh = open(logfile, 'a')
            fh.write(datetime.datetime.now().isoformat()+'\n'+traceback.format_exc())
            fh.close()
            raise
    return logApp
            

def moveEnvVarsWSGIMiddleware(application, keys):
    '''
    application: wsgi application that needs some env vars transferred.  
    keys: a list of environment variable names.
    wsgi middleware application that transfers environment variables from the
    wsgi environment to the os environment before calling application.
    '''
    def app(environ, start_response):
        for key in keys:
            if environ.has_key(key):
                os.environ[key] = environ[key]
        return application(environ, start_response)
    return app


# add to sys.path the location of user-defined modules
# assume user-defined modules (e.g. index.py) are located with passenger_wsgi.py, this file.
sys.path.append(os.path.dirname(__file__))


# RUNNING A WSGI-APP USING PASSENGER requires setting 'application' to a wsgi-app

# DJANGO
# run a django wsgi-application using phusion passenger: https://github.com/kwe/passenger-django-wsgi-example/tree/django
# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# import django.core.handlers.wsgi
# application = django.core.handlers.wsgi.WSGIHandler()

# FLASK EXAMPLE
# import hello
# application = hello.app

# USING MIDDLEWARE
# move database credentials from the webserver to the process environment
# application = moveEnvVarsWSGIMiddleware(
#         application, ('HOST', 'DB', 'USER', 'PASSWORD'))
# log errors
# application = exceptionLoggingMiddleware(application, os.path.expanduser('~/passenger_wsgi.log'))

# # SIMPLE WSGI APPS FOR TESTING
# def application(environ, start_response):
#     status = '200 OK'
#     headers = [('Content-type', 'text/html')]
#     start_response(status, headers)
#     parts = ['<html><head></head><body><img src="/wsgi-snake.jpg"/><pre>'] # image tests serving static content
#     parts += ['%s: %s\n' % (key, value) for key, value in environ.iteritems()]
#     parts += ['</pre></body></html>']
#     return parts
# def application(environ, start_response):
#     start_response('200 OK', [('Content-type', 'text/plain')])
#     return ["Hello, world!"]





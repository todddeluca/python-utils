



import subprocess
import os


PID_FILE = os.path.abspath('test_daemon.pid')
LOG_FILE = os.path.abspath('test_daemon.log')

def test_cli():
    '''
    Test start, status, restart, and stop using the daemoncmd.py command
    line interface.  The "test" is that the subprocess calls do not return a
    non-zero return code.
    '''
    kws = {'pid': PID_FILE, 'out': LOG_FILE, 'err': LOG_FILE}

    try:
        # check the process is not running yet.
        cmd = 'python daemoncmd.py status --pidfile {pid}'
        output = subprocess.check_output(cmd.format(**kws), shell=True)
        print 'hi', output
        print output.find('stopped')
        assert output.find('stopped') != -1

        # start process
        cmd = ('python daemoncmd.py start --pidfile {pid} --stdout {out} ' +
              '--stderr {err} sleep 10')
        output = subprocess.check_output(cmd.format(**kws), shell=True)

        # check that process is running
        cmd = 'python daemoncmd.py status --pidfile {pid}'
        output = subprocess.check_output(cmd.format(**kws), shell=True)
        print 'hi', output
        print output.find('running')
        assert output.find('running') != -1

        # restart process
        cmd = ('python daemoncmd.py restart --pidfile {pid} --stdout {out} ' +
              '--stderr {err} sleep 10')
        output = subprocess.check_output(cmd.format(**kws), shell=True)

        # check that process is running
        cmd = 'python daemoncmd.py status --pidfile {pid}'
        output = subprocess.check_output(cmd.format(**kws), shell=True)
        print 'hi', output
        print output.find('running')
        assert output.find('running') != -1

        # stop process
        cmd = 'python daemoncmd.py stop --pidfile {pid}'
        output = subprocess.check_output(cmd.format(**kws), shell=True)

        # check that process is stopped
        cmd = 'python daemoncmd.py status --pidfile {pid}'
        output = subprocess.check_output(cmd.format(**kws), shell=True)
        print 'hi', output
        print output.find('stopped')
        assert output.find('stopped') != -1
    finally:
        for path in (PID_FILE, LOG_FILE):
            if os.path.exists(path):
                os.remove(path)




from __future__ import division, print_function
import os
import subprocess

WINDOWS = os.name == 'nt'

if WINDOWS:
    import win32job
    import pywintypes

class RunProcess(subprocess.Popen):

    def __init__(self, args, cwd):

        if WINDOWS:
            preexec_fn = None
        else:
            preexec_fn = os.setpgrp

        super(RunProcess, self).__init__(args=args, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=preexec_fn
        )


    def kill_job(self):
        ''' kill_job is for windows only'''
        if not WINDOWS:
            return
        print("Kill Windows JobObject handle: {0}".format(self.job))

        try:
            win32job.TerminateJobObject(self.job, 1)
        except pywintypes.error as err:
            print("Could not terminate job object")
            print(err)
            return err

    def kill_pg(self):
        '''kill_pg is for posix only '''
        if WINDOWS:
            return

        try:
            pgid = os.getpgid(self.pid)
        except OSError as err:
            print("Could not get process group for pid %s", self.pid, exc_info=err)
            return err

        print("Kill posix process group pgid: {0}".format(pgid))

        try:
            os.killpg(pgid, signal.SIGTERM)
        except OSError as err:
            print("Could not kill process group for pid {}".format(self.pid), exc_info=err)
            return err

    def kill(self):
        '''Kill all processes and child processes'''

        try:
            print("Kill Tree parent pid: {0}".format(self.pid))
            parent = psutil.Process(self.pid)
            children = parent.children(recursive=True)
        except psutil.NoSuchProcess:
            print("Parent pid {0} is already dead".format(self.pid))
            # Already dead
            parent = None
            children = []
        if WINDOWS:
            err = self.kill_job()
            msg = 'job'
        else:
            err = self.kill_pg()
            msg = 'process group'
        if parent and parent.is_running():
            print("RunProcess.kill: parent pid {} is being killed".format(parent.pid))
            super(RunProcess, self).kill()

        for child in children:
            if child.is_running():
                print("RunProcess.kill: child pid {} is being killed".format(child.pid))
                child.kill()

from __future__ import print_function, unicode_literals, division

from functools import partial
import io
import os
import subprocess as sp
import time
from threading import Thread, Event

from taxbrain_server.utils import set_env

celery = 'taxbrain-celery-worker'
flask = 'taxbrain-flask-worker'
redis = 'redis-server'

EVENT = Event()
bad_ret = None

def kill_all():
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'scripts',
                     'ensure_procs_killed.sh')
    sp.Popen(['pkill', 'redis-server']).wait()
    sp.check_output(['bash', f, 'flask'])
    sp.check_output(['bash', f, 'celery'])
    sp.check_output(['bash', f, 'redis-server'])

def printer(name, line, end=''):
    print(name, line.replace('\n', '\n {}: '.format(name)), end=end)

def flush(proc):
    pass#for s in (proc.stdout, proc.stderr):
        #s.flush()


def get_default_env():
    x = sp.Popen(['conda', 'env', 'list'], stdout=sp.PIPE, stderr=sp.PIPE).stdout.read()
    return [xi.split()[0] for xi in x.split('\n') if '*' in xi][0]

def readline(name, stdout):
    line = stdout.readline().decode().strip()
    if line:
        printer(name, line, end='\n')

def main():
    try:
        kill_all()
        env = dict(os.environ)
        env.update({str(k): (str(v) if not isinstance(v, bool) else str(int(v)))
                    for k, v in set_env().items()})
        env.pop('MOCK_CELERY', None)
        env['CONDA_DEFAULT_ENV'] = get_default_env()
        def get_proc(a, name):

            proc = sp.Popen(a, stdout=sp.PIPE,
                            stderr=sp.STDOUT,
                            env=env,
                            shell=False)
            proc._name = name
            return proc
        f1 = get_proc([redis], 'redis')
        f2 = get_proc([flask], 'flask')
        procs = [f1, f2,]
        print('Started threads')
        do_kill = False
        while all(p.poll() in (None, 0) for p in procs):
            for p in procs:
                if p._name == 'celery':
                    t = Thread(target=partial(sp.check_output, [celery]))
                    t.start()
                    t.join(0.2)
        for p in procs:
            print(p._name, 'kill')
            kill_all()
            print(p._name, 'wait')
            p.wait()
            print(p._name, 'read')
            print(p.stdout.read())
    except:
        kill_all()
        raise
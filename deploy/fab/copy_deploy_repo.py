from __future__ import print_function
import os
import shutil
import subprocess as sp
import tempfile

d = os.path.dirname
DEPLOY_LOCAL_DIR = d(d(os.path.abspath(__file__)))
WEBAPP_REPO = d(DEPLOY_LOCAL_DIR)
REMOTE_DEPLOY = '/home/ubuntu/deploy'

def check_unmodified():
    args = 'git ls-files -m'.split()
    proc = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE, cwd=WEBAPP_REPO, env=os.environ)
    if proc.wait() != 0:
        raise ValueError("Failed subproc {} - {} {}".format(args, proc.stdout.read(), proc.stderr.read()))
    lines = proc.stdout.read().splitlines()
    for line in lines:
        if line.strip():
            raise ValueError('There are modified files not checked in:\n {}'.format(lines))


def copy_deploy_repo(sudo_func, put_func, run_func):
    '''Copy the current deploy directory after ensuring all files
    are committed and that only files within "git ls-files" are
    copied over. Moves a zip and then unizps it to be /home/ubuntu/deploy
    '''
    tmp = os.path.join(tempfile.mkdtemp(), 'deploy')
    try:
        args = 'git ls-files'.split()
        proc = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE, cwd=WEBAPP_REPO, env=os.environ)
        if proc.wait() != 0:
            raise ValueError("Failed subproc {} - {} {}".format(args, proc.stdout.read(), proc.stderr.read()))
        lines = proc.stdout.read().splitlines()
        for line in lines:
            fname_rel = line.strip()
            if not fname_rel.startswith('deploy'):
                continue
            src = os.path.join(WEBAPP_REPO, fname_rel)
            dst = os.path.join(tmp, fname_rel)
            dirr = os.path.dirname(dst)
            if not os.path.exists(dirr):
                os.makedirs(dirr)
            if os.path.exists(src):
                shutil.copy(src, dst)
            else:
                print('WARNING:', src, '(deploy repo) is in git ls-files but not found.  Not copying...')
        deploy_zip = os.path.join(os.path.dirname(tmp), 'deploy.zip')
        args = 'zip -r {} ./*'.format(deploy_zip)
        print(args, '(from {})'.format(tmp), os.listdir(tmp))
        proc = sp.Popen(args, cwd=tmp, shell=True)
        if proc.wait() or not os.path.exists(deploy_zip):
            raise ValueError('Failed on zipping in {}'.format(tmp))
        print('COPY DEPLOY REPO')
        if sudo_func:
            sudo_func('apt-get install -y unzip')
        run_func('rm -rf {}'.format(REMOTE_DEPLOY))
        run_func('mkdir {}'.format(REMOTE_DEPLOY))
        put_func(deploy_zip, os.path.join(REMOTE_DEPLOY, 'deploy.zip'))
        run_func('cd {} && unzip deploy.zip'.format(REMOTE_DEPLOY)) # TODO && rm deploy.zip?
        remote_reset_server = os.path.join(os.path.dirname(REMOTE_DEPLOY), 'reset_server.sh')
        run_func('cd {} && cp reset_server.sh {}'.format(os.path.join(REMOTE_DEPLOY, 'fab'), remote_reset_server))
    finally:
        shutil.rmtree(os.path.dirname(tmp))


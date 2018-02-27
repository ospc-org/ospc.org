from __future__ import print_function
import argparse
import json
import datetime
import os
import subprocess as sp

from copy_deploy_repo import copy_deploy_repo, check_unmodified


def next_log_file(args):
    now = datetime.datetime.utcnow(
            ).isoformat().replace(':', '_').replace(' ', '_')
    kw = dict(vars(args))
    kw['now'] = now
    fname = 'dropq_log_{ip_address}_{now}.txt'.format(**kw)
    with open(fname, 'a') as f:
        f.write('Redeploy with {}'.format(json.dumps(kw)))
    return fname


def pem_string(pem):
    return "-i {}".format(pem)


def cli(ip_address=None):

    parser = argparse.ArgumentParser(description='Re-deploy the deploy app from laptop to EC2 box that already has deploy on it')
    if not ip_address:
        parser.add_argument('ip_address', help='IP address that already has been deployed (has reset_server.sh in home dir)')
    parser.add_argument('--keypath', default="", help='Full local path to the PEM file for EC2 box access, typically something like /path/to/latest.pem')
    parser.add_argument('--user', default='ubuntu', help='Login user, typically (default): %(default)s')
    parser.add_argument('--allow-uncommited',
                        action='store_true',
                        help='Allow uncommited changes in deploy to be '
                             're-deployed.  By default there is an exception '
                             'if attempting to re-deploy the deploy repo '
                             'with uncommited changes')
    args = parser.parse_args()
    if ip_address:
        args.ip_address = ip_address
    return args


def proc_mgr(cmd, fname):
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT,
                    shell=True, cwd=os.path.abspath(os.curdir),
                    env=os.environ)
    with open(fname, 'a') as f:
        while proc.poll() is None:
            content = proc.stdout.read(4)
            f.write(content)
            print(content, end='')
        ret = proc.poll()
        if ret:
            raise ValueError('Failed with {}'.format(ret))
        content = proc.stdout.read()
        f.write(content)
        print(content)


def put(pem, ip, fname, local, rmt):
    proc_mgr('scp {} {} ubuntu@{}:{}'.format(pem, os.path.abspath(local), ip, rmt), fname)


def run(pem, ip, fname, cmd):
    proc_mgr('ssh {} ubuntu@{} "{}"'.format(pem, ip, cmd), fname)


def main(args=None):
    args = args or cli()
    # env_str = []
    # for k in dir(args):
    #     if 'install_method' in k or 'version' in k or 'install_label' in k:
    #         os.environ[k.upper()] = getattr(args, k)
    #         env_str.append('{}="{}"'.format(k.upper(), getattr(args, k)))
    fname = next_log_file(args)
    if args.keypath:
        assert os.path.exists(args.keypath), ('PEM file {} does not exist'.format(args.keypath))
        pem = pem_string(args.keypath)
    else:
        pem = ""
    ip_address = args.ip_address
    user = args.user
    if not args.allow_uncommited:
        check_unmodified()
    cmd = 'ssh {} {}@{} "sudo apt-get install -y unzip"'.format(pem, user, ip_address)
    proc_mgr(cmd, fname=fname)
    put_func = lambda x, y: put(pem, ip_address, fname, x, y)
    run_func = lambda cmd: run(pem, ip_address, fname, cmd)
    copy_deploy_repo(None, put_func, run_func)
    template = 'ssh {} {}@{} \'bash reset_server.sh\''
    cmd = template.format(pem, user, ip_address)
    proc_mgr(cmd, fname)


if __name__ == '__main__':
    main()

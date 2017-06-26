#!/usr/bin/env python
from __future__ import print_function
from functools import partial
import os
import sys
import boto.exception
import boto.ec2
import datetime
import time
import subprocess

from fabric.api import (
    env,
    settings,
    sudo,
    prefix,
    put,
    cd,
    run,
)

from fabric.tasks import execute

from fabric.contrib.files import (
    comment,
    uncomment,
    exists,
    append,
    sed
)

import logging
from copy_deploy_repo import copy_deploy_repo, check_unmodified
from redeploy import cli as deploy_versions_cli, main as reset_server_main

DEPLOYMENT_VERSIONS_ARGS = deploy_versions_cli(ip_address='skip')
if not 'OSPC_ANACONDA_TOKEN' in os.environ:
    raise ValueError('OSPC_ANACONDA_TOKEN must be defined in env vars')
check_unmodified()
#based on https://github.com/ContinuumIO/wakari-deploy/blob/master/ami_creation/fabfile.py
ssh_transport = logging.getLogger("ssh.transport")
ssh_transport.disabled = True
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)

# log.addHandler(handler)
log.addHandler(console)

# ami-65ce000e
# ami-849e0c84
# ami-1998e77c
# ami-af5591eb
# ami-9f92edfa
# ami-1d4b1f78
#AMI_ID = 'ami-1d4b1f78' #SSD in us-east-1
#AMI_ID = 'ami-dfcab0b5' #SSD in us-east-1
#AMI_ID = 'ami-dfcab0b5' #SSD in us-east-1
AMI_ID = 'ami-6c276206' #SSD in us-east-1

use_latest_key = 'True' == os.environ.get('USE_LATEST_KEY', False)

if 'xxx' == os.environ.get('AWS_ID', 'xxx').lower():
    print("you must pass a value for the environment variable AWS_ID")
    quit()
if 'xxx' == os.environ.get('AWS_SECRET', 'xxx').lower():
    print("you must pass a value for the environment variable AWS_SECRET")
    quit()
if 'xxx' == os.environ.get('PUF_FILE_PATH', 'xxx').lower():
    print("you must pass a value for the environment variable PUF_FILE_PATH")
    quit()
if 'xxx' == os.environ.get('SERVER_FILE_PATH', 'xxx').lower():
    print("you must pass a value for the environment variable SERVER_FILE_PATH")
    quit()

else:
    SERVER_FILE_PATH = os.path.abspath(os.path.expanduser(os.environ.get('SERVER_FILE_PATH')))

ec2 = boto.ec2.connect_to_region('us-east-1', #N. Virginia
        aws_access_key_id = os.environ.get('AWS_ID'),
        aws_secret_access_key = os.environ.get('AWS_SECRET'))
env.use_ssh_config = True
env.disable_known_hosts = True
env.connection_attempts = True
env.timeout = 50

KEYNAME = "{}-aei-dropq-{}".format(AMI_ID,os.environ.get('USER', 'ospc'))
#KEYNAME = "keypair-ospc"
#SECURITY_GROUP = 'launch-wizard-26'
#SECURITY_GROUP = 'dropq-security-group'
SECURITY_GROUP = 'dropq-iam-group'
NODE_COUNT = 1

def create_box():
    old_ids = set(i.id for i in ec2.get_only_instances())
    machine = ec2.run_instances(AMI_ID, key_name=KEYNAME, min_count=NODE_COUNT, max_count=NODE_COUNT,
        security_groups=[SECURITY_GROUP,], instance_type=os.environ.get('EC2_INSTANCE_TYPE', 'm3.medium'))
    new_instances = [i for i in ec2.get_only_instances() if i.id not in old_ids]
    for new_instance in new_instances:
        print("new instance:", new_instance.id)
        ec2.create_tags([new_instance.id], {"billingProject": "aei"})


    is_running = [False] * len(new_instances)
    while not all(is_running):
        for count, newinstance in enumerate(new_instances):
            is_running[count] = new_instance.state == u'running'
        time.sleep(3)
        for new_instance in new_instances:
            new_instance.update()


    is_reachable = [False] * len(new_instances)
    while not all(is_reachable):
        instance_ids=[new_instance.id for new_instance in new_instances]
        inst_statuses = ec2.get_all_instance_status(instance_ids=instance_ids)
        is_reachable = [inst_status.system_status.details['reachability'] != 'passed' for inst_status in inst_statuses]
        time.sleep(3)

    time.sleep(1)
    for new_instance in new_instances:
        assert new_instance.public_dns_name
        print("public dns name:", new_instance.public_dns_name)

    return new_instances


def create_keypair(source=KEYNAME):

    try:
        kp = ec2.delete_key_pair(source)
    except (boto.exception.EC2ResponseError):
        pass

    kp = ec2.create_key_pair(source)
    filename = os.environ.get('EC2_KEY_PATH', './keys/ec2-{}.pem'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M')))
    latest_filename = os.environ.get('EC2_KEY_PATH', './latest.pem')
    kfile = open(filename, 'wb')
    latest_kfile = open(latest_filename, 'wb')
    def file_mode(user, group, other):
        return user*(8**2) + group*(8**1) + other*(8**0)
    kfile.write(kp.material)
    latest_kfile.write(kp.material)
    kfile.close()
    latest_kfile.close()
    os.chmod(filename, file_mode(7,0,0))
    os.chmod(latest_filename, file_mode(7,0,0))
    return filename

def test_all_ssh(instances, key_file):
    # needed to convert from unicode to ascii?
    key_file = str(key_file)
    ips = [str(instance.public_dns_name) for instance in instances]
    #env.host = 'ubuntu@e' + ip
    #env.host_string = ip
    #env.hosts = ['ubuntu@e' + ip for ip in ips]
    env.hosts = [ip for ip in ips]
    env.user = 'ubuntu'
    env.password = ''
    env.key_file = key_file
    env.key_filename = key_file

    print(env.hosts)

    # forward ssh agent -- equivalent of ssh -A
    env.forward_agent = True

    log.info('Key file: %s' % (key_file))
    log.debug('Trying to connect...')
    import pdb;pdb.set_trace()
    for h in env.hosts:
        env.host_string = h
        run('pwd')

def test_ssh2():
    '''log.info('Key file: %s' % (key_file))
    log.debug('Trying to connect...')
    for ip in ips:
        env.host = 'ubuntu@' + ip
        env.password = ''
        '''
    run('pwd')

def test_ssh(instance, key_file):
    # needed to convert from unicode to ascii?
    key_file = str(key_file)
    ip = str(instance.public_dns_name)
    env.host = 'ubuntu@e' + ip
    env.password = ''
    env.host_string = ip
    env.hosts = [env.host]
    env.user = 'ubuntu'
    env.key_file = key_file
    env.key_filename = key_file

    # forward ssh agent -- equivalent of ssh -A
    env.forward_agent = True

    log.info('Key file: %s' % (key_file))
    log.debug('Trying to connect...')
    run('pwd')

def connect_to_existing_machine(ip, key_file_path):
    env.user = 'ubuntu'
    env.password = ''
    env.hosts = ['{}@{}'.format(env.user, ip)]
    env.host = '{}@{}'.format(env.user, ip)
    env.host_string = '{}@{}'.format(env.user, ip)
    env.key_file = key_file_path
    env.key_filename = key_file_path
    env.forward_agent = True
    log.info('Key file: %s' % (key_file_path))
    log.debug('Trying to connect...')
    run('pwd')

def fix_sshd_config():
    '''root needs an actual shell, so fix the sshd_config.'''
    config_file = '/etc/ssh/sshd_config'
    uncomment(config_file, r'^.*PermitRootLogin yes', use_sudo=True)
    comment(config_file, r'^PermitRootLogin forced-commands-only', use_sudo=True)

def apt_installs():
    log.info("installing packages with apt-get")
    sudo("add-apt-repository -y ppa:saltstack/salt")
    sudo("apt-get update -y")
    packages = ['salt-master', 'salt-minion', 'salt-syndic', 'git', 'tig',
                'silversearcher-ag', 'python-qt4']
    sudo("apt-get install -y {}".format(' '.join(packages)))


def install_deploy_repo():
    sudo('rm -rf ~/deploy')
    run('mkdir ~/deploy')
    copy_deploy_repo(sudo, put, run)


def install_ogusa_repo():
    url = 'https://github.com/open-source-economics/OG-USA'
    sudo('rm -rf ~/OG-USA')
    if os.environ.get('OGUSA_GIT_BRANCH'):
        run("git clone {} --branch {}".format(url, os.environ.get('OGUSA_GIT_BRANCH')))
    else:
        run("git clone {}".format(url))


def write_ospc_anaconda_token():
    token = os.environ['OSPC_ANACONDA_TOKEN']
    run('echo {token} &> /home/ubuntu/.ospc_anaconda_token'.format(token=token))


def convenience_aliases():
    run('echo "alias supervisorctl=\'supervisorctl -c /home/ubuntu/deploy/fab/supervisord.conf\'" >> ~/.bashrc')
    run('echo "alias ss=\'sudo /usr/bin/salt-call state.highstate --retcode-passthrough --log-level=debug --config-dir=/home/ubuntu/deploy/fab/salt\'" >> ~/.bashrc')


def run_salt():
    run("ln -s ~/deploy/fab/salt ~/salt")
    sudo('sudo /usr/bin/salt-call state.highstate --retcode-passthrough --log-level=debug --config-dir="$HOME/deploy/fab/salt"')


def _env_str(args):
    s = []
    for k in dir(args):
        val = getattr(args, k)
        if any(tok in k.lower() for tok in ('install', 'method' 'version')):
            s.append('{}="{}"'.format(k, val))
    return " ".join(s)

def reset_server():
    e = _env_str(DEPLOYMENT_VERSIONS_ARGS)
    command = "{} source /home/ubuntu/reset_server.sh".format(e)
    print('Running', command)
    run(command)


def wait_for_login_prompt(instance, retry_count=20):
    import time
    import re

    for i in range(retry_count):
        print("checking for login prompt on", instance, "at", time.ctime())
        console = instance.get_console_output()
        try:
            mo = re.search("login:", console.output)
            if mo is not None:
                #We got the login console for this machine, so we are done.
                print("Got login console for", instance)
                break

        except TypeError:
            #We'll get a TypeError if the console output is None
            pass
        time.sleep(30)

    if i == retry_count:
        #If we retried our maximum number of times, indicate failure
        raise RuntimeError("Instance was not up after trying for {} retries".format(retry_count))

if os.environ.get('DROPQ_IP_ADDR'):
    ip_address = os.environ.get('DROPQ_IP_ADDR')
    key_filename = os.path.abspath('./keys/ec2-{}.pem'.format(ip_address))
    if not os.path.exists(key_filename):
        key_filename = os.path.abspath('latest.pem')
    public_dns_name = 'ec2-{}.compute-1.amazonaws.com'.format(ip_address.replace('.','-'))
    connect_to_existing_machine(ip_address, key_filename)
else:
    if not use_latest_key:
        raise ValueError()
        key_filename = create_keypair()

    else:
        key_filename = "./latest.pem"

    instances = create_box()
    public_dns_names = []
    ip_addresses = []
    for instance in instances:
        print("trying this instance :", instance)
        subprocess.check_output(['cp', key_filename,
                                os.path.join(os.path.dirname(key_filename), 'ec2-{}.pem'.format(instance.ip_address))])
        public_dns_names.append(instance.public_dns_name)
        ip_addresses.append(instance.ip_address)

if 'quitafterec2spinup' in sys.argv:
    quit()

#import pdb;pdb.set_trace()
#test_all_ssh(instances, key_filename)

key_file = str(key_filename)
fqdns = [str(instance.public_dns_name) for instance in instances]
env.hosts = [fqdn for fqdn in fqdns]
env.user = 'ubuntu'
env.password = ''
env.key_file = key_file
env.key_filename = key_file
# forward ssh agent -- equivalent of ssh -A
env.forward_agent = True

print("hosts:", env.hosts)
print("ips:", fqdns)

#Wait for the machines to actually come up:

for instance in instances[:]:
    try:
        wait_for_login_prompt(instance)
    except RuntimeError:
        #This host isn't ready, so terminate it and cleanup
        env.hosts.remove(str(instance.public_dns_name))
        instances.remove(instance)
        print("Terminating", instance)
        instance.terminate()


execute(test_ssh2)
execute(apt_installs)
execute(install_deploy_repo)
execute(install_ogusa_repo)
execute(convenience_aliases)
execute(write_ospc_anaconda_token)
execute(run_salt)
execute(reset_server)

for instance in instances:
    ssh_command = 'ssh -i {key} ubuntu@{ip} "'.format(ip=instance.ip_address, key=key_filename)
    with open("log_{}.log".format(instance.ip_address), 'w') as f:
        f.write(ssh_command)
    print(ssh_command)


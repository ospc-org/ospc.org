#!/usr/bin/env python
from __future__ import print_function
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

from copy_deploy_repo import copy_deploy_repo
#based on https://github.com/ContinuumIO/wakari-deploy/blob/master/ami_creation/fabfile.py

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
    PUF_FILE_PATH = os.path.abspath(os.path.expanduser(os.environ.get('PUF_FILE_PATH')))
    SERVER_FILE_PATH = os.path.abspath(os.path.expanduser(os.environ.get('SERVER_FILE_PATH')))
    if not os.path.exists(PUF_FILE_PATH):
        print("{} does not exist".format(PUF_FILE_PATH))
        quit()

env.use_ssh_config = True
env.disable_known_hosts = True
env.connection_attempts = True
env.timeout = 300

KEYNAME = "{}-aei-dropq-{}".format(AMI_ID,os.environ.get('USER', 'ospc'))
#KEYNAME = "keypair-ospc"
#SECURITY_GROUP = 'launch-wizard-26'
#SECURITY_GROUP = 'dropq-security-group'
SECURITY_GROUP = 'dropq-iam-group'

def create_box():
    old_ids = set(i.id for i in ec2.get_only_instances())
    machine = ec2.run_instances(AMI_ID, key_name=KEYNAME, min_count=2, max_count=2,
        security_groups=[SECURITY_GROUP,], instance_type=os.environ.get('EC2_INSTANCE_TYPE', 'm3.medium'))
    new_instances = [i for i in ec2.get_only_instances() if i.id not in old_ids]
    for new_instance in new_instances:
        print(new_instance.id)
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
        print(new_instance.public_dns_name)

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
    env.key_file = key_file
    env.key_filename = key_file

    print(env.hosts)

    # forward ssh agent -- equivalent of ssh -A
    env.forward_agent = True

    log.info('Key file: %s' % (key_file))
    log.debug('Trying to connect...')
    for h in env.hosts:
        env.host_string = h
        run('pwd')

def test_ssh2():
    run('pwd')

def test_ssh(instance, key_file):
    # needed to convert from unicode to ascii?
    key_file = str(key_file)
    ip = str(instance.public_dns_name)
    env.host = 'ubuntu@e' + ip
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


def install_ogusa_repo():
    if 'XXX' not in os.environ.get('GITHUB_PRIVATE_KEY_PATH'):
        with settings(warn_only = True):
            run('ssh -T git@github.com -o StrictHostKeyChecking=no')
        url = 'git@github.com:open-source-economics/OG-USA'
    else:
      url = 'https://{USERNAME}@github.com/open-source-economics/OG-USA'.format(
          USERNAME = os.environ.get('GITHUB_USERNAME'))

    sudo('rm -rf ~/OG-USA')
    if os.environ.get('GIT_BRANCH'):
        run("git clone {} --branch {}".format(url, os.environ.get('OGUSA_GIT_BRANCH')))
    else:
        run("git clone {}".format(url))



def copy_puf_file():
    put(PUF_FILE_PATH, "/home/ubuntu/deploy/puf.csv.gz")
    put(SERVER_FILE_PATH, "/home/ubuntu/reset_server.sh")

def extract_puf_file():
    run("cd /home/ubuntu/deploy/; gunzip -k puf.csv.gz")

def convenience_aliases():
    run('echo "alias supervisorctl=\'supervisorctl -c /home/ubuntu/deploy/fab/supervisord.conf\'" >> ~/.bashrc')
    run('echo "alias ss=\'sudo /usr/bin/salt-call state.highstate --retcode-passthrough --log-level=debug --config-dir=/home/ubuntu/deploy/fab/salt\'" >> ~/.bashrc')


def run_salt():
    run("ln -s ~/deploy/salt ~/salt")
    sudo('sudo /usr/bin/salt-call state.highstate --retcode-passthrough --log-level=debug --config-dir="$HOME/deploy/salt"')

def reset_server():
    run("source /home/ubuntu/reset_server.sh")


key_filename = './latest.pem'
#instances = ['ip1', 'ip2']
key_file = str(key_filename)
ips = instances
env.hosts = [ip for ip in ips]
env.user = 'ubuntu'
env.key_file = key_file
env.key_filename = key_file
# forward ssh agent -- equivalent of ssh -A
env.forward_agent = True

print(env.hosts)
print(ips)
#execute(test_ssh2)
#execute(apt_installs)
#execute(install_ogusa_repo)
#execute(convenience_aliases)
#execute(copy_puf_file)
#execute(extract_puf_file)
execute(run_salt)
execute(reset_server)

for instance in instances:
    ssh_command = 'ssh -i {key} ubuntu@{ip} "'.format(ip=instance, key=key_filename)
    with open("log_{}.log".format(instance), 'w') as f:
        f.write(ssh_command)
    print(ssh_command)

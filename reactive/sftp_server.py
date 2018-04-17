import subprocess

from charms.reactive import when, when_any  # set_state
from charmshelpers.core import host

from libsftp import SftpHelper

sh = SftpHelper

# @when_not('sftp-server.installed')
# def install_sftp_server():
#     set_state('sftp-server.installed')


@when('config.changed.sftp-config')
def process_config():
    sh.setup_chroot()
    sh.write_fstab()
    users = []
    for entry in sh.charm_config['sftp-config'].split(';'):
        user = entry.split(',')[0]
        users.append(user)
        host.adduser(user, password=host.pwgen, shell='/dev/null')
    subprocess.check_call(['umount', '-a'])
    subprocess.check_call(['mount', '-a'])


@when_any('config.changed.sftp-password-auth',
          'config.changed.sftp-config')
def write_sshd_config():
    sh.write_sshd_config()
    host.service_restart('sshd')

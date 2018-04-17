import subprocess

from charms.reactive import when, when_any  # set_state
from charmhelpers.core import host

from libsftp import SftpHelper

sh = SftpHelper()

# @when_not('sftp-server.installed')
# def install_sftp_server():
#     set_state('sftp-server.installed')


@when('config.changed.sftp-config')
def process_config():
    users = []
    for entry in sh.charm_config['sftp-config'].split(';'):
        user = entry.split(',')[0]
        users.append(user)
        host.adduser(user, password=host.pwgen(), shell='/dev/null')
    sh.setup_chroot()
    sh.write_fstab()
    subprocess.call(['umount', '-a', '-O', 'bind'])
    subprocess.check_call(['mount', '-a'])


@when_any('config.changed.sftp-password-auth',
          'config.changed.sftp-config')
def write_sshd_config():
    sh.write_sshd_config()
    host.service_restart('sshd')

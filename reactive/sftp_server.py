from charms.reactive import when, when_any  # set_state
from charmhelpers.core import host

from libsftp import SftpHelper

sh = SftpHelper()

# @when_not('sftp-server.installed')
# def install_sftp_server():
#     set_state('sftp-server.installed')


@when('config.changed.sftp-config')
def process_config():
    for entry in sh.parse_config():
        host.adduser(entry['user'], password=host.pwgen(), shell='/dev/null')
    sh.setup_chroot()
    sh.write_fstab()


@when_any('config.changed.sftp-password-auth',
          'config.changed.sftp-config')
def write_sshd_config():
    sh.write_sshd_config()
    host.service_restart('sshd')

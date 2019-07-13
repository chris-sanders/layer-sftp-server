from charms.reactive import when, when_any, when_not, set_state
from charmhelpers.core import host, hookenv
from charmhelpers import fetch

from libsftp import SftpHelper
from libserviceaccount import ServiceAccountHelper

sh = SftpHelper()
sa = ServiceAccountHelper()


@when("layer-service-account.installed")
@when_not("sftp-server.installed")
def install_sftp_server():
    fetch.apt_install("whois")
    hookenv.status_set("active", "Sftp-server is ready")
    set_state("sftp-server.installed")


@when("config.changed.sftp-config")
@when("sftp-server.installed")
def process_config():
    for entry in sh.parse_config():
        host.adduser(entry["user"], password=host.pwgen(), shell="/dev/null")
        sa.add_group_member('sftp', entry["user"])
    sh.setup_chroot()
    sh.write_fstab()


@when_any("config.changed.sftp-password-auth", "config.changed.sftp-config")
def write_sshd_config():
    sh.write_sshd_config()
    host.service_restart("sshd")

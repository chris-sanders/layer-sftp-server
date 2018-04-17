import os
import shutil
import fileinput

from charmhelpers.core import (
    hookenv,
    templating,
)


class SftpHelper:
    def __init__(self):
        self.charm_config = hookenv.config()
        self.sftp_dir = '/var/sftp'
        self.sshd_file = '/etc/ssh/sshd_config'
        self.sshd_sftp_file = '/etc/ssh/sshd_sftp_config'
        self.fstab_file = '/etc/fstab'

    def _get_config(self):
        results = []
        for entry in self.charm_config['sftp-config'].split(';'):
            user = entry.split(',')[0]
            paths = entry.split(',')[1::]
            for path in paths:
                src = path.split(':')[0]
                try:
                    name = path.split(':')[1]
                except IndexError:
                    name = src.split('/')[-1]
                results.append({'user': user,
                                'src': src,
                                'name': name})
        return results

    def setup_chroot(self):
        config = self._get_config()
        for entry in config:
            os.makedirs('{}/{}/{}'.format(self.sftp_dir,
                                          entry['user'],
                                          entry['name']))
            shutil.chown('{}/{}/{}'.format(self.sftp_dir,
                                           entry['user'],
                                           entry['name']),
                         user=entry['user'],
                         group=entry['user'])

    def write_fstab(self):
        with fileinput.input(self.fstab_file, inplace=True) as fstab:
            for line in fstab:
                if self.sftp_dir in line:
                    continue
                print(line, end='')
        with open(self.fstab_file, 'a') as fstab:
            for entry in self._get_config():
                line = ('{}\t'
                        '{}/{}/{}\t'
                        'none bind,_netdev,x-systemd.requires={} 0 0\n'.format(
                            entry['src'],
                            self.sftp_dir,
                            entry['user'],
                            entry['name'],
                            self.sftp_dir)
                        )
                fstab.write(line)

    def write_sshd_config(self):
        # Write the sftp config
        users = []
        for entry in self._get_config():
            if entry['user'] not in users:
                users.append(entry['user'])
        if self.charm_config['sftp-password-auth']:
            auth = 'yes'
        else:
            auth = 'no'
        context = {'sftp_dir': self.sftp_dir,
                   'users': ','.join(users),
                   'password_auth': auth}
        templating.render('sshd_sftp_config', self.sshd_sftp_file, context, perms=0o664)

        # Add an include statement
        with fileinput.input(self.sshd_file, inplace=True) as sshd:
            for line in sshd:
                if self.sshd_sftp_file in line:
                    continue
                print(line, end='')
        with open(self.sshd_file, 'a') as sshd:
            line = 'Include {}'.format(self.sshd_sftp_file)
            sshd.write(line)

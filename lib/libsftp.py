import os
import shutil
import fileinput

from charmhelpers.core import (
    hookenv,
    templating,
    host,
)


class SftpHelper:
    def __init__(self):
        self.charm_config = hookenv.config()
        self.sftp_dir = '/var/sftp'
        self.sshd_file = '/etc/ssh/sshd_config'
        self.sshd_sftp_file = '/etc/ssh/sshd_sftp_config'
        self.fstab_file = '/etc/fstab'
        self.sshd_comment_line = "# Below this line managed by sftp-server charm do not edit\n"

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
            try:
                os.makedirs('{}/{}/{}'.format(self.sftp_dir,
                                              entry['user'],
                                              entry['name']))
            except FileExistsError:
                pass  # Don't error if directory already exists

    def write_fstab(self):
        for (mnt, dev) in host.mounts():
            if self.sftp_dir in mnt:
                host.umount(mnt, persist=True)
        for entry in self._get_config():
            host.mount(entry['src'],
                       '{}/{}/{}'.format(self.sftp_dir,
                                         entry['user'],
                                         entry['name']),
                       'bind,_netdev,x-systemd.requires={}'.format(self.sftp_dir),
                       persist=True,
                       filesystem="none")
            if self.charm_config['sftp-chown-mnt']:
                shutil.chown('{}/{}/{}'.format(self.sftp_dir,
                                               entry['user'],
                                               entry['name']),
                             user=entry['user'],
                             group=entry['user'])

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
        user_block = templating.render('sshd_sftp_config', None, context)
        user_block = self.sshd_comment_line + user_block
        # templating.render('sshd_sftp_config', self.sshd_sftp_file, context, perms=0o664)

        # Add an include statement
        with fileinput.input(self.sshd_file, inplace=True) as sshd:
            for line in sshd:
                if self.sshd_comment_line in line:
                    break
                print(line, end='')
        with open(self.sshd_file, 'a') as sshd:
            sshd.write(user_block)
            # line = 'Include {}'.format(self.sshd_sftp_file)
            # sshd.write(line)

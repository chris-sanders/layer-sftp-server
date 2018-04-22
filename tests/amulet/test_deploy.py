#!/usr/bin/python3

import pytest
import amulet
import time


@pytest.fixture(scope="module")
def deploy():
    deploy = amulet.Deployment(series='xenial')
    deploy.add('sftp-server')
    deploy.expose('sftp-server')
    deploy.configure('sftp-server', {'sftp-config': ('user1,/tmp:system-tmp;'
                                                     ' user2,/opt')})
    deploy.setup(timeout=1000)
    return deploy


@pytest.fixture(scope="module")
def sftp(deploy):
    return deploy.sentry['sftp-server'][0]


class TestSftp():

    def test_deploy(self, deploy):
        try:
            deploy.sentry.wait(timeout=1500)
        except amulet.TimeoutError:
            raise

    def test_fstab(self, deploy, sftp):
        # Check mounts were added
        fstab = sftp.file_contents('/etc/fstab')
        print(fstab)
        assert '/tmp /var/sftp/user1/system-tmp' in fstab
        assert '/opt /var/sftp/user2/opt' in fstab

        # Check mounts are removed
        deploy.configure('sftp-server', {'sftp-config': ('user1,/tmp:system-tmp;')})
        fstab = sftp.file_contents('/etc/fstab')
        print(fstab)
        assert '/tmp /var/sftp/user1/system-tmp' in fstab
        assert '/opt /var/sftp/user2/opt' not in fstab

        # Re-add for other tests
        deploy.configure('sftp-server', {'sftp-config': ('user1,/tmp:system-tmp;'
                                                         'user2,/opt')})

    def test_chroot_folders(self, deploy, sftp):
        # Create folderes with chown
        system_tmp = sftp.directory_stat('/var/sftp/user1/system-tmp')
        opt = sftp.directory_stat('/var/sftp/user2/opt')
        with pytest.raises(IOError):
            sftp.directory_stat('/var/sftp/user1/fake')

        print(system_tmp)
        print(opt)
        assert system_tmp['uid'] == 1001
        assert system_tmp['gid'] == 1001
        assert opt['uid'] == 1002
        assert opt['gid'] == 1002

        # Create folderes without chown
        deploy.configure('sftp-server', {'sftp-config': ('user1,/tmp:system-tmp;'
                                                         'user2,/opt;'
                                                         'user3,/mnt'),
                                         'sftp-chown-mnt': False})

        time.sleep(5)
        mnt = sftp.directory_stat('/var/sftp/user3/mnt')
        print(mnt)
        assert mnt['uid'] == 0
        assert mnt['gid'] == 0

    def test_ssh_config(self, deploy, sftp):
        config = sftp.file_contents('/etc/ssh/sshd_config')
        print(config)
        assert 'Match User user1,user2,user3' in config
        deploy.configure('sftp-server', {'sftp-config': ('user1,/tmp:system-tmp;'
                                                         'user2,/opt')})
        time.sleep(5)
        config = sftp.file_contents('/etc/ssh/sshd_config')
        print(config)
        assert 'Match User user1,user2,user3' not in config
        assert 'Match User user1,user2' in config

    def test_actions(self, deploy, sftp):
        uuid = sftp.action_do('set-password', {'user': 'user1', 'password': 'amulet'})
        result = deploy.action_fetch(uuid, full_output=True)
        print(result)
        assert result['status'] == 'completed'

        uuid = sftp.action_do('set-key', {'user': 'user1', 'key': 'test_key'})
        result = deploy.action_fetch(uuid, full_output=True)
        print(result)
        assert result['status'] == 'completed'

        uuid = sftp.action_do('add-key', {'user': 'user1', 'key': 'test_key2'})
        result = deploy.action_fetch(uuid, full_output=True)
        print(result)
        assert result['status'] == 'completed'

    #     # test we can access over http
    #     # page = requests.get('http://{}'.format(self.unit.info['public-address']))
    #     # self.assertEqual(page.status_code, 200)
    #     # Now you can use self.d.sentry[SERVICE][UNIT] to address each of the units and perform
    #     # more in-depth steps. Each self.d.sentry[SERVICE][UNIT] has the following methods:
    #     # - .info - An array of the information of that unit from Juju
    #     # - .file(PATH) - Get the details of a file on that unit
    #     # - .file_contents(PATH) - Get plain text output of PATH file from that unit
    #     # - .directory(PATH) - Get details of directory
    #     # - .directory_contents(PATH) - List files and folders in PATH on that unit
    #     # - .relation(relation, service:rel) - Get relation data from return service

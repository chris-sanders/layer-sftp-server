#!/usr/bin/python3
import os
import mock


class TestLibSftp():

    def test_pytest(self):
        assert True

    def test_sh(self, sh):
        ''' See if the sh fixture works to load charm configs '''
        assert isinstance(sh.charm_config, dict)

    def test_setup_chroot(self, sh, monkeypatch):
        sh.charm_config['sftp-config'] = ('test-user,/mnt/test1:name1,/mnt/test2;'
                                          ' test-user2,/mnt/test3,/mnt/test4:name4;')
        mock_chown = mock.Mock()
        monkeypatch.setattr('libsftp.shutil.chown', mock_chown)
        sh.setup_chroot()
        assert os.path.isdir('{}/{}/{}'.format(sh.sftp_dir,
                                               'test-user',
                                               'name1'))
        assert os.path.isdir('{}/{}/{}'.format(sh.sftp_dir,
                                               'test-user',
                                               'test2'))
        assert os.path.isdir('{}/{}/{}'.format(sh.sftp_dir,
                                               'test-user2',
                                               'test3'))
        assert os.path.isdir('{}/{}/{}'.format(sh.sftp_dir,
                                               'test-user2',
                                               'name4'))

    def test_write_sshd_config(self, sh, mock_fchown):
        sh.charm_config['sftp-config'] = ('test-user,/mnt/test1:name1,/mnt/test2;'
                                          ' test-user3,/mnt/test3;')
        sh.write_sshd_config()

        # Check the template was written
        with open(sh.sshd_file, 'r') as sftp:
            contents = sftp.read()
            assert 'Match User test-user,test-user3' in contents
            assert 'ForceCommand internal-sftp' in contents
            assert 'PasswordAuthentication yes' in contents
            assert 'ChrootDirectory {}/%u'.format(sh.sftp_dir) in contents
            assert 'PermitTunnel no' in contents
            assert 'AllowAgentForwarding no' in contents
            assert 'AllowTcpForwarding no' in contents
            assert 'X11Forwarding no' in contents

        sh.charm_config['sftp-config'] = 'test-user,/mnt/test1:name1,/mnt/test2;'
        sh.charm_config['sftp-password-auth'] = False
        sh.write_sshd_config()
        with open(sh.sshd_file, 'r') as sftp:
            contents = sftp.read()
            assert 'Match User test-user' in contents
            assert 'PasswordAuthentication no' in contents


#!/usr/bin/python3
import pytest
import mock

import sys
import shutil


@pytest.fixture
def mock_layers():
    sys.modules["charms.layer"] = mock.Mock()
    sys.modules["reactive"] = mock.Mock()


@pytest.fixture
def mock_fchown(monkeypatch):
    mock_fchown = mock.Mock()
    monkeypatch.setattr("libsftp.os.fchown", mock_fchown)
    return mock_fchown


# @pytest.fixture
# def mock_check_call(monkeypatch):
#     mock_call = mock.Mock()
#     monkeypatch.setattr('libsftp.subprocess.check_call', mock_call)
#     return mock_call


@pytest.fixture
def mock_hookenv_action_get(monkeypatch):
    monkeypatch.setattr("libsftp.hookenv.action_get", mock.Mock())


@pytest.fixture
def mock_hookenv_config(monkeypatch):
    import yaml

    def mock_config():
        cfg = {}
        yml = yaml.safe_load(open("./config.yaml"))

        # Load all defaults
        for key, value in yml["options"].items():
            cfg[key] = value["default"]

        return cfg

    monkeypatch.setattr("libsftp.hookenv.config", mock_config)


@pytest.fixture
def sh(tmpdir, mock_layers, mock_hookenv_config, monkeypatch, mock_hookenv_action_get):
    from libsftp import SftpHelper

    sh = SftpHelper()

    # Set correct charm_dir
    monkeypatch.setattr("libsftp.hookenv.charm_dir", lambda: ".")

    # sftp_dir
    sftp_dir = tmpdir.join(sh.sftp_dir)
    sh.sftp_dir = sftp_dir.strpath

    # sshd_file
    sshd_config = tmpdir.join("sshd_config")
    sh.sshd_file = sshd_config.strpath
    shutil.copyfile("./tests/unit/sshd_config", sh.sshd_file)

    # sshd_sftp_file
    sshd_sftp_file = tmpdir.join("sshd_sftp_config")
    sh.sshd_sftp_file = sshd_sftp_file.strpath

    # fstab
    fstab_file = tmpdir.join("fstab")
    sh.fstab_file = fstab_file.strpath
    shutil.copyfile("./tests/unit/fstab", sh.fstab_file)

    # Any other functions that load DH will get this version
    monkeypatch.setattr("libsftp.SftpHelper", lambda: sh)

    return sh

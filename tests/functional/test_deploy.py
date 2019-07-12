import os
import pytest
import subprocess

# import stat

# Treat all tests as coroutines
pytestmark = pytest.mark.asyncio

juju_repository = os.getenv("JUJU_REPOSITORY", ".").rstrip("/")
series = [
    "xenial",
    pytest.param("bionic", marks=pytest.mark.xfail(reason="canary")),
    # pytest.param('cosmic', marks=pytest.mark.xfail(reason='canary')),
]
sources = [
    ("local", "{}/builds/sftp-server".format(juju_repository)),
    # ('jujucharms', 'cs:...'),
]


# Custom fixtures
@pytest.fixture(params=series)
def series(request):
    return request.param


@pytest.fixture(params=sources, ids=[s[0] for s in sources])
def source(request):
    return request.param


@pytest.fixture
async def app(model, series, source):
    app_name = "sftp-server-{}-{}".format(series, source[0])
    return await model._wait_for_new("application", app_name)


async def test_sftpserver_deploy(model, series, source, request):
    # Starts a deploy for each series
    # Using subprocess b/c libjuju fails with JAAS
    # https://github.com/juju/python-libjuju/issues/221
    application_name = "sftp-server-{}-{}".format(series, source[0])
    cmd = [
        "juju",
        "deploy",
        source[1],
        "-m",
        model.info.name,
        "--series",
        series,
        application_name,
    ]
    if request.node.get_closest_marker("xfail"):
        # If series is 'xfail' force install to allow testing against versions not in
        # metadata.yaml
        cmd.append("--force")
    subprocess.check_call(cmd)


async def test_charm_upgrade(model, app):
    if app.name.endswith("local"):
        pytest.skip("No need to upgrade the local deploy")
    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == "idle")
    subprocess.check_call(
        [
            "juju",
            "upgrade-charm",
            "--switch={}".format(sources[0][1]),
            "-m",
            model.info.name,
            app.name,
        ]
    )
    await model.block_until(lambda: unit.agent_status == "executing")


# Tests
async def test_sftpserver_status(model, app):
    # Verifies status for all deployed series of the charm
    await model.block_until(lambda: app.status == "active")
    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == "idle")


async def test_fstab(app, jujutools):
    # Check mounts are added
    await app.set_config({"sftp-config": ("user1,/tmp:system-tmp;user2,/opt")})
    config = await app.get_config()
    assert config["sftp-config"]["value"] == "user1,/tmp:system-tmp;user2,/opt"

    fstab = await jujutools.file_contents("/etc/fstab", app.units[0])
    print(fstab)
    assert "/tmp /var/sftp/user1/system-tmp" in fstab
    assert "/opt /var/sftp/user2/opt" in fstab

    # Check mounts are removed
    await app.set_config({"sftp-config": ("user1,/tmp:system-tmp;")})
    config = await app.get_config()
    assert config["sftp-config"]["value"] == "user1,/tmp:system-tmp;"
    fstab = await jujutools.file_contents("/etc/fstab", app.units[0])
    print(fstab)
    assert "/tmp /var/sftp/user1/system-tmp" in fstab
    assert "/opt /var/sftp/user2/opt" not in fstab

    # Re-add 2nd mount for other tests
    await app.set_config({"sftp-config": ("user1,/tmp:system-tmp;user2,/opt")})
    config = await app.get_config()
    assert config["sftp-config"]["value"] == "user1,/tmp:system-tmp;user2,/opt"


async def test_chroot_folders(app, jujutools):
    # Create folderes with chown
    system_tmp = await jujutools.file_stat("/var/sftp/user1/system-tmp", app.units[0])
    opt = await jujutools.file_stat("/var/sftp/user2/opt", app.units[0])
    with pytest.raises(EOFError):
        fail = await jujutools.file_stat("/var/sftp/user1/fake", app.units[0])
        print(fail)

    assert system_tmp.st_uid == 1001
    assert system_tmp.st_gid == 1001
    assert opt.st_uid == 1002
    assert opt.st_gid == 1002

    # Create folderes without chown
    await app.set_config(
        {
            "sftp-config": ("user1,/tmp:system-tmp;user2,/opt;user3,/mnt"),
            "sftp-chown-mnt": "False",
        }
    )
    config = await app.get_config()
    assert (
        config["sftp-config"]["value"] == "user1,/tmp:system-tmp;user2,/opt;user3,/mnt"
    )
    assert config["sftp-chown-mnt"]["value"] is False

    # time.sleep(5)
    mnt = await jujutools.file_stat("/var/sftp/user3/mnt", app.units[0])
    print(mnt)
    assert mnt.st_uid == 0
    assert mnt.st_gid == 0


async def test_ssh_config(app, jujutools):
    # Check all three users from previous tests are present
    config = await jujutools.file_contents("/etc/ssh/sshd_config", app.units[0])
    print(config)
    assert "Match User user1,user2,user3" in config

    # Check removal of user 3
    await app.set_config({"sftp-config": ("user1,/tmp:system-tmp;user2,/opt;")})
    config = await app.get_config()
    assert config["sftp-config"]["value"] == "user1,/tmp:system-tmp;user2,/opt;"
    config = await jujutools.file_contents("/etc/ssh/sshd_config", app.units[0])
    print(config)
    assert "Match User user1,user2,user3" not in config
    assert "Match User user1,user2" in config


async def test_actions(app, jujutools):
    # run set-password
    action = await app.units[0].run_action(
        "set-password", user="user1", password="test"
    )
    action = await action.wait()
    print(action.status)
    assert action.status == "completed"

    # run set-key
    action = await app.units[0].run_action("set-key", user="user1", key="test_key")
    action = await action.wait()
    print(action.status)
    assert action.status == "completed"

    # run add-key
    action = await app.units[0].run_action("add-key", user="user1", key="test_key2")
    action = await action.wait()
    print(action.status)
    assert action.status == "completed"

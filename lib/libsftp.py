import os
import shutil
import fileinput
import subprocess

from charmhelpers.core import hookenv, templating, host


class SftpHelper:
    def __init__(self):
        self.charm_config = hookenv.config()
        self.sftp_dir = "/var/sftp"
        self.sshd_file = "/etc/ssh/sshd_config"
        self.sshd_sftp_file = "/etc/ssh/sshd_sftp_config"
        self.fstab_file = "/etc/fstab"
        self.sshd_comment_line = (
            "# Below this line managed by sftp-server charm do not edit\n"
        )

    def parse_config(self):
        results = []
        for entry in self.charm_config["sftp-config"].rstrip("; ").split(";"):
            user = entry.split(",")[0].lstrip(" ")
            paths = entry.split(",")[1::]
            for path in paths:
                src = path.split(":")[0]
                try:
                    name = path.split(":")[1]
                except IndexError:
                    name = src.split("/")[-1]
                results.append({"user": user, "src": src, "name": name})
        return results

    def setup_chroot(self):
        config = self.parse_config()
        for entry in config:
            try:
                os.makedirs(
                    "{}/{}/{}".format(self.sftp_dir, entry["user"], entry["name"])
                )
            except FileExistsError:
                pass  # Don't error if directory already exists

    def write_fstab(self):
        for (mnt, dev) in host.mounts():
            if self.sftp_dir in mnt:
                host.umount(mnt, persist=True)
        for entry in self.parse_config():
            host.mount(
                entry["src"],
                "{}/{}/{}".format(self.sftp_dir, entry["user"], entry["name"]),
                "bind,_netdev,x-systemd.requires={}".format(self.sftp_dir),
                persist=True,
                filesystem="none",
            )
            if self.charm_config["sftp-chown-mnt"]:
                try:
                    shutil.chown(
                        "{}/{}/{}".format(self.sftp_dir, entry["user"], entry["name"]),
                        user=entry["user"],
                        group=entry["user"],
                    )
                except Exception as e:
                    hookenv.log("Chown failed: {}".format(e), level=hookenv.WARNING)
            else:
                try:
                    shutil.chown(
                        "{}/{}/{}".format(self.sftp_dir, entry["user"], entry["name"]),
                        user="sftp",
                        group="sftp",
                    )
                except Exception as e:
                    hookenv.log("Chown failed: {}".format(e), level=hookenv.WARNING)

    def write_sshd_config(self):
        # Write the sftp config
        users = []
        for entry in self.parse_config():
            if entry["user"] not in users:
                users.append(entry["user"])
        if self.charm_config["sftp-password-auth"]:
            auth = "yes"
        else:
            auth = "no"
        context = {
            "sftp_dir": self.sftp_dir,
            "users": ",".join(users),
            "password_auth": auth,
        }
        user_block = templating.render("sshd_sftp_config", None, context)
        user_block = self.sshd_comment_line + user_block

        # Add an include statement
        with fileinput.input(self.sshd_file, inplace=True) as sshd:
            for line in sshd:
                if self.sshd_comment_line in line:
                    break
                print(line, end="")
        with open(self.sshd_file, "a") as sshd:
            sshd.write(user_block)

    def set_password(self, user, password):
        p = subprocess.Popen(
            ("mkpasswd", "-m", "sha-512", password), stdout=subprocess.PIPE
        )
        shadow_password = p.communicate()[0].strip()
        subprocess.check_call(("usermod", "-p", shadow_password, user))

    def add_key(self, user, key):
        try:
            os.makedirs("/home/{}/.ssh/".format(user))
        except FileExistsError:
            pass  # Don't error if directory already exists

        with open("/home/{}/.ssh/authorized_keys".format(user), "a") as keys:
            keys.write(key + "\n")

    def set_key(self, user, key):
        try:
            os.makedirs("/home/{}/.ssh/".format(user))
        except FileExistsError:
            pass  # Don't error if directory already exists

        with open("/home/{}/.ssh/authorized_keys".format(user), "w") as keys:
            keys.write(key)

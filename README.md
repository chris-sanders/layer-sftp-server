# Overview

This charm provides a simple sftp server via openssh. The users are restricted
to sftp (no shell) access and a chroot is setup. Configured directories are then
mounted into the chroot for the user so their access is limited to only the
specified folders.

# Usage

This charm doesn't currently have any interfaces and deployment is fairly
straight forward.

```bash
juju deploy sftp-server
```

After deployment configure the server for users and mounts.

## Scale out Usage

No current allowance for scale out usage, if you want to run this behind HAProxy
for tcp load balancing, that's probably fairly easy to add contact the charm
author to discuss use cases.

## Known Limitations and Issues

The mount points are only allowed to be used one time each in fstab, meaning a
source location can not be mounted into multiple chroot environments. This is
actually a limitation of the charmhelpers library but if you have a use case for it,
fixing in charmhelpers would remove the limitation.

# Configuration

The sftp-config option follows the following format

<user>,<src path>:<optional mnt name>,<more paths>;

After the ';' you repeat the pattern for additional users.

# Contact Information

## Upstream Project Name

  - Code: https://github.com/chris-sanders/layer-sftp-server 
  - Bug tracking: https://github.com/chris-sanders/layer-sftp-server/issues
  - Contact information: sanders.chris@gmail.com


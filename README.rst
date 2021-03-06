.. image:: https://travis-ci.org/sneben/backuptool.svg?branch=master
    :target: https://travis-ci.org/sneben/backuptool

.. image:: https://coveralls.io/repos/sneben/backuptool/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/sneben/backuptool?branch=master

==========
backuptool
==========

Overview
========
Simple backuptool for FILE, MySQL and LDAP backups. It could be used for
servers which operates such a service on low load.

How the script operates?
========================
It create backups from the sources:

* File
* MySQL
* LDAP

And aggregate the result to an ``tar.gz``, which could be optionally
encrypted with **gpg**. The target to place the backup to could be:

* Local filesystem
* FTP
* SFTP
* S3

The resulting filenames are like **backup-<name>-<timestamp>.tar.gz[.gpg]**
Following commands are available:

.. code-block:: text

    Usage:
      backuptool [options] create [<name>]
      backuptool [options] restore [<name>]
      backuptool [options] delete <name>
      backuptool [options] rotate
      backuptool [options] list

    All necessary settings will be read from the config dir.

    Options:
      -h --help               Show this
      -d --debug              Don't remove the working directory automatically
      -c --config CONFIG_DIR  Path to config directory. [default: /etc/backuptool/]

Listing
-------
To just list the available backups for the current machine:

.. code-block:: console

   $ backuptool list
   Available backups for this instance
   ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
   mybackup_name (SFTP):
   ├─ backup-mybackup_name-20170607062837.tar.gz.gpg      2.04MB     2017-06-08T18:29:02
   └─ backup-mybackup_name-20170608062901.tar.gz.gpg      2.04MB     2017-06-07T06:25:01

   mybackup_name_1 (S3):
   ├─ backup-mybackup_name_1-20170608182903.tar.gz.gpg    840.50MB   2017-06-08T18:29:03
   ├─ backup-mybackup_name_1-20170608062505.tar.gz.gpg    840.50MB   2017-06-08T06:25:05
   └─ backup-mybackup_name_1-20170607062505.tar.gz.gpg    840.50MB   2017-06-07T06:25:05

Installation
============
To build the project follow these steps:

.. code-block:: console

   $ virtualenv venv
   $ source venv/bin/activate
   $ pip install pybuilder
   $ pyb install_dependencies
   $ pyb -v

The generated install source can be found in ``target/dist/backuptool-0.1/``.
Do what ever you want with the ``setup.py``.

Configuration
=============
General
-------
Configuration files have to be placed into ``/etc/backuptool``. The format is
**yaml** and has to be start with an ``backup:`` section. Then you can choose
a name for your backup like ``mybackup:``. The different
configuration possibilities are explained below.

With this logic it is possible to define several backups with several sources
and targets.

Backup sources
--------------
There are several variants for the target where the backup should be placed to.

File
~~~~
The file target backups a single file or a whole directory tree. On the restore
process eventually existing files/directories get wiped.

.. code-block:: yaml

    files:
        - /path/to/backup

MySQL
~~~~~
Do a simple ``sqldump`` of defined mysql databases. During the restore process
this dump(s) is/are simply played back using ``mysql``.

.. code-block:: yaml

    mysql_databases:
        - mydatabase
    mysql_user: backupuser
    mysql_password: password123

LDAP
~~~~
Generate an ldif of an entire ldap database. When the backup is restored the
whole database directory get wiped and is restored using the ldif from backup.
The default ldap data directory is ``/var/lib/ldap/``, but can be changed with
the option ``datadir``. To set the correct ownership of the ``datadir``, you
can define the ``system_user`` and the ``system_group`` option. Default is
``openldap``. ``slapd`` is *stopped* and *started* prior and after the
restore process.

.. code-block:: yaml

    ldap_backup:
        datadir: /var/lib/ldap
        system_user: openldap
        system_group: openldap

Backup targets
--------------

File
~~~~
Will copy the resulting ``tar.gz`` to another point
in the filesystem. The needed configuration paramters are:

.. code-block:: yaml

    target: file://path/to/put/backup

SFTP
~~~~
Uploads the resulting ``tar.gz`` to an sftp space.
The needed configuration paramters are:

.. code-block:: yaml

    sftp_user: username
    sftp_password: password123
    target: sftp://backup.example.com

FTP
~~~
Uploads the resulting ``tar.gz`` to an ftp space.
The needed configuration paramters are:

.. code-block:: yaml

    ftp_user: username
    ftp_password: password123
    target: ftp://backup.example.com

S3
~~
Uploads the resulting ``tar.gz`` to an S3 bucket.
The needed configuration paramters are:

.. code-block:: yaml

    aws-region: eu-west-1
    aws-access-key-id: AKIAIOSFODNN7EXAMPLE
    aws-secret-access-key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY
    target: s3://my-backup-bucket

User
----
The script can be configured to only run under a certain user. If the calling
user is a different one, the script will refuse to work (Default is 'root').

.. code-block:: yaml

    user: user1

Rotation
--------
The backup filenames have a timestamp in the name (see section
*How the script operates*). If e.g. the five freshest backups should be
kept, set the ``rotate`` option to ``5`` (default is ``3``).
All older backups get deleted on rotation.

.. code-block:: yaml

    rotate: 5

Encryption
----------
Optionally it is possible to encrypt the generated backup ``tar.gz`` with
pgp. You have to put your wished key to the gpg keyring and put its id
into the configuration:

.. code-block:: yaml

    encrypt: True
    gpg_key_id: 1A2B3C4D

Pre & post scripts
------------------
You can define scripts/commands which should be executed before backup
processes. E.g. for mounting things before **create** a backup:

.. code-block:: yaml

    pre-create: docker-machine mount docker.domain.com:/path/to/mount /mnt/mybackup

A multiline script could be given by using the yaml literal syntax. If a script
should be run after e.g. the backup **create** process is finished, use this:

.. code-block:: yaml

    post-create: |
        docker-machine mount -u docker.domain.com:/path/to/mount /mnt/mybackup
        touch /tmp/backup_indicator

The naming is  pretty self-explanatory, so to do the same for the **restore**
process, use **restore** instead of **create** on the section name.

Further there is a more general variant called **pre-script** and
**post-script**, which is executed on both actions, create or restore. Where
**pre-script** always run first and **post-script** always run last, if you
define other pre or post scripting options.

Example configuration
---------------------
Example configuration with all available features:

.. code-block:: yaml

    mybackup_name:
        user: user1
        rotate: 3
        encrypt: True
        gpg_key_id: 1A2B3C4D
        target: s3://my-backup-bucket
        aws-access-key-id: AKIAIOSFODNN7EXAMPLE
        aws-secret-access-key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY
        ldap_backup: True
        files:
            - /path/to/backup
        mysql_databases:
            - mydatabase
        mysql_user: backupuser
        mysql_password: password123
        pre-create: docker-machine mount docker.domain.com:/path/to/mount /mnt/mybackup
        post-create: |
            docker-machine mount -u docker.domain.com:/path/to/mount /mnt/mybackup
            touch /tmp/backup_indicator

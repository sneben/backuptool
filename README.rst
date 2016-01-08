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
* S3

The resulting filenames are like **backup-<name>-<timestamp>.tar.gz[.gpg]**
Following commands are available:

.. code-block:: text

    Usage:
      backuptool [options] create
      backuptool [options] restore
      backuptool [options] rotate
      backuptool [options] delete <name>
      backuptool [options] list

    All necessary settings will be read from the config dir.

    Options:
      -h --help               Show this
      -c --config CONFIG_DIR  Path to config directory. [default: /etc/backuptool/]

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
Do what ever you want with the ``setup.py``

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
whole database directory get wiped (e.g. ``/var/lib/ldap/``) and is restored
using the ldif from backup. ``slapd`` is *stopped* and *started* prior and
after the restore process.

.. code-block:: yaml

    ldap_backup: True

Backup targets
--------------

File
~~~~
Will copy the resulting ``tar.gz`` to another point
in the filesystem. The needed configuration paramters are:

.. code-block:: yaml

    target: file://path/to/put/backup

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
*How the script operates*). If e.g. the three freshest backups should be
kept, set the ``rotate`` option to 3. All older backups get deleted on upload.

.. code-block:: yaml

    rotate: 3

Encryption
----------
Optionally it is possible to encrypt the generated backup ``tar.gz`` with
pgp. You have to put your wished key to the gpg keyring and put its id
into the configuration:

.. code-block:: yaml

    encrypt: True
    gpg_key_id: 1A2B3C4D

Puppet
------
After the backup is restored, a local puppet manifest could be executed:

.. code-block:: yaml

    puppet-manifest: /etc/puppet/manifests/mymanifests

Example configuration
---------------------
Example configuration with all available features:

.. code-block:: yaml

    backup:
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
            puppet-manifest: /etc/puppet/manifests/mymanifests

License
=======
Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

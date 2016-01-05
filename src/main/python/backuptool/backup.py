#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import time
import gnupg
import errno
import shutil
import getpass
import tarfile
import subprocess
import distutils.dir_util

from glob import glob
from functools import wraps
from datetime import datetime
from contextlib import closing


class CallingUserError(Exception):
    """Exception class for throwing CallingUserError exceptions"""
    pass


class Backup(object):
    """Parent class for backup operations"""

    def __init__(self, *args, **kwargs):
        self.name = args[0]
        self.config = kwargs.get('config', {})
        self.workdir = kwargs.get('workdir')
        self.encrypt = None
        self.files = None
        self.filename = None
        self.filename_abs = None
        self.mysql_databases = None
        self.ldap_backup = None
        self.filename_prefix = 'backup-{0}'.format(self.name)
        self.rotation_num = self.config['rotate']
        if 'encrypt' in self.config:
            self.encrypt = self.config['encrypt']
            if self.encrypt:
                self.gpg = gnupg.GPG()
            self.gpg_key_id = self.config['gpg_key_id']
        if 'files' in self.config:
            self.files = self.config['files']
        if 'mysql_databases' in self.config:
            self.mysql_databases = self.config['mysql_databases']
            self.mysql_user = self.config['mysql_user']
            self.mysql_password = self.config['mysql_password']
        if 'ldap_backup' in self.config:
            self.ldap_backup = self.config['ldap_backup']

    def _needs_root_user(original_function):
        """Decorator method to ensure sieve connectivity"""
        @wraps(original_function)
        def new_function(self, *args, **kwargs):
            if getpass.getuser() != 'root':
                message = 'Root user is needed to perform this action'
                raise CallingUserError(message)
            return original_function(self, *args, **kwargs)
        return new_function

    def download(self):
        """Dummy method, will be overwritten by child classes"""
        raise NotImplementedError  # pragma: no cover

    def upload(self):
        """Will be overwritten by child class method"""
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def create_directory(directory):
        """Create the given directory, if not exist, else do nothing"""
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def rmfile(filename):
        """Delete the given file"""
        try:
            for file_to_remove in glob(filename):
                os.remove(file_to_remove)
        except OSError as error:
            if error.errno != errno.ENOENT:
                raise

    def copy_files(self):
        """Copy the entries from file list to its temporary target"""
        if not self.files:
            return
        for entry in self.files:
            dst = '{0}/files/{1}'.format(self.workdir, os.path.dirname(entry))
            for member in glob(entry):
                if os.path.isfile(member):
                    if not os.path.exists(dst):
                        self.create_directory(dst)
                    shutil.copy(member, dst)
                elif os.path.isdir(member):
                    move_dst = '{0}/{1}'.format(dst, os.path.basename(member))
                    distutils.dir_util.copy_tree(member, move_dst)

    @_needs_root_user
    def create(self):
        """Collect data, encrypt it and upload the result"""
        self.copy_files()
        self.dump_database()
        self.dump_ldap()
        self.tar_workdir()
        self.encrypt_archive()
        self.upload()

    def decrypt(self):
        """Decrypt the gpg file"""
        if not self.encrypt:
            return
        with open('{0}.gpg'.format(self.filename_abs), 'rb') as gpg_file:
            self.gpg.decrypt_file(gpg_file, self.gpg_key_id,
                                  output=self.filename_abs)

    def dump_database(self):
        """Create a sql dump of given mysql databases"""
        if self.mysql_databases is not None:
            self.create_directory('{0}/mysql'.format(self.workdir))
            cmd = 'mysqldump -u {0} -p{1} {2} > {3}/mysql/{4}.sql'
            for database in self.mysql_databases:
                formatted_cmd = cmd.format(self.mysql_user,
                                           self.mysql_password,
                                           database,
                                           self.workdir,
                                           database)
                subprocess.check_call(formatted_cmd, shell=True)

    def dump_ldap(self):
        """Create a complete ldap dump"""
        if self.ldap_backup is not None and bool(self.ldap_backup):
            self.create_directory('{0}/ldap'.format(self.workdir))
            cmd = 'slapcat -n1 -l {0}/ldap/dump.ldif'
            subprocess.check_call(cmd.format(self.workdir), shell=True)

    def encrypt_archive(self):
        """Encrypt the created tarball with gpg"""
        if not self.encrypt:
            return
        gpg_target_file = "{0}.gpg".format(self.filename_abs)
        with open(self.filename_abs, 'rb') as tared_file:
            crypt = self.gpg.encrypt_file(tared_file,
                                          self.gpg_key_id,
                                          always_trust=True,
                                          output=gpg_target_file)
            if not crypt.ok:
                raise NameError('GPG encryption was not successfull!')

    @_needs_root_user
    def restore(self):
        """Call all necessary methods to do an backup restore"""
        if self.download():
            print('Restoring backup: {0}'.format(self.name))
            self.decrypt()
            self.untar_backup_file()
            self.restore_files()
            self.restore_database()
            self.restore_ldap()

    def restore_database(self):
        """Import the given sql dumps into local mysql"""
        backup_path = '{0}/mysql'.format(self.workdir)
        if os.path.isdir(backup_path):
            cmd = 'mysql -u {0} -p{1} {2} < {3}/mysql/{4}'
            for dump_file in os.listdir(backup_path):
                formatted_cmd = cmd.format(self.mysql_user,
                                           self.mysql_password,
                                           '.'.join(dump_file.split('.')[:-1]),
                                           self.workdir,
                                           dump_file)
                subprocess.check_call(formatted_cmd, shell=True)

    def restore_ldap(self):
        """Wipe ldap and import the dump from backup"""
        if os.path.isdir("{0}/ldap".format(self.workdir)):
            subprocess.check_call('service slapd stop', shell=True)
            self.rmfile('/var/lib/ldap/*')
            cmds = [
                'slapadd -l {0}/ldap/dump.ldif'.format(self.workdir),
                'echo "set_flags DB_LOG_AUTOREMOVE" >> /var/lib/ldap/DB_CONFIG',
                'chown -R openldap:openldap /var/lib/ldap'
            ]
            for cmd in cmds:
                subprocess.check_call(cmd, shell=True)
            subprocess.check_call('service slapd start', shell=True)

    def restore_files(self):
        """Copy the file tree from temporary space to the system"""
        if os.path.isdir('{0}/files'.format(self.workdir)):
            cmd = 'rsync -a {0}/files/ /'.format(self.workdir)
            subprocess.check_call(cmd, shell=True)

    def tar_workdir(self):
        """Tar the prepared working directory"""
        timestamp = time.time()
        formatted_timestamp = datetime.fromtimestamp(timestamp)
        formatted_timestamp = formatted_timestamp.strftime('%Y%m%d%H%M%S')
        filename = '{0}-{1}.tar.gz'
        self.filename = filename.format(self.filename_prefix,
                                        formatted_timestamp)
        self.filename_abs = '{0}/{1}'.format(self.workdir, self.filename)
        # Python 2.6 has no support for the context manager protocol
        with closing(tarfile.open(self.filename_abs, 'w:gz')) as tar:
            tar.add(self.workdir, arcname='.')

    def untar_backup_file(self):
        """Extract the backup tarball"""
        # Python 2.6 has no support for the context manager protocol
        with closing(tarfile.open(self.filename_abs)) as tar:
            tar.extractall(path=self.workdir)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import time
import shutil

from .backup import Backup


class FileBackup(Backup):
    """Class for creating backups on file targets"""

    def __init__(self, *args, **kwargs):
        super(FileBackup, self).__init__(*args, **kwargs)
        self.backup_dir = '/{0}'.format(self.config['target'].split('//')[1])
        self.existing_backup_files = []
        self.set_existing_backups()

    def set_existing_backups(self):
        """Set a list of all existing backups entries"""
        if not os.path.isdir(self.backup_dir):
            raise NameError('configured backup directory does not exist')
        self.existing_backup_files = os.listdir(self.backup_dir)
        self.existing_backup_files.sort()

    def upload(self):
        """Copy the created backup file to the configured target"""
        if self.encrypt:
            filename_abs = '{0}.gpg'.format(self.filename_abs)
        else:
            filename_abs = self.filename_abs
        shutil.copy(filename_abs, '/{0}/'.format(self.backup_dir))

    def list(self):
        """List all available file backups"""
        print('{0} (FILE):'.format(self.name))
        if not self.existing_backup_files:
            print('  <no backups>\n')
            return
        for entry, more_items in self._lookahead(self.existing_backup_files):
            file_path = '{0}/{1}'.format(self.backup_dir, entry)
            date = time.ctime(os.path.getctime(file_path))
            size_value = float(os.path.getsize(file_path)) / 1024 / 1024
            size = '{0:.2f}MB'.format(size_value)
            name = entry
            if more_items:
                tree_prefix = '├─ '
            else:
                tree_prefix = '└─ '
            print('{0}{1:<53}{2:<10}{3}'.format(tree_prefix, name, size, date))
        print('')

    def rotate(self):
        """Only keep the given amount of backup files and delete the rest"""
        files = self.existing_backup_files
        files.reverse()
        files_to_be_deleted = files[self.rotation_num:]
        for backup_file in files_to_be_deleted:
            self.rmfile('{0}/{1}'.format(self.backup_dir, backup_file))

    def delete(self, name):
        """Delete the given backup file"""
        self.rmfile('{0}/{1}'.format(self.backup_dir, name))

    def download(self):
        """Copy the newest backup to the temporary directory"""
        if not self.existing_backup_files:
            return False
        newest_backup = self.existing_backup_files[-1]
        file_target = '{0}/{1}'.format(self.workdir, newest_backup)
        file_source = '{0}/{1}'.format(self.backup_dir, newest_backup)
        shutil.copy(file_source, file_target)
        self.check_encryption_by_name(newest_backup)
        return True

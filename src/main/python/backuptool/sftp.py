#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import paramiko

from datetime import datetime

from .backup import Backup


class SFTPBackup(Backup):
    """Class for creating backups on sftp space"""

    def __init__(self, *args, **kwargs):
        super(SFTPBackup, self).__init__(*args, **kwargs)
        self.existing_backup_listings = []
        self.transport = None
        self.sftp = None
        self.connect()
        self.set_existing_backups()

    def __del__(self):
        self.sftp.close()
        self.transport.close()

    def connect(self):
        """Connect against the configured ftp server"""
        match = re.search(r'sftp://([^:/]+):*([^/]*)', self.config['target'])
        host = match.group(1)
        port = 22
        if match.group(2):
            port = int(match.group(2))
        self.transport = paramiko.Transport((host, port))
        self.transport.connect(username=self.config['sftp_user'],
                               password=self.config['sftp_password'])
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def set_existing_backups(self):
        """Set a list of all existing backups entries found on ftp server"""
        for entry in self.sftp.listdir():
            stats = self.sftp.stat(entry)
            date_format = '%b %d %H:%M'
            date = datetime.fromtimestamp(stats.st_mtime).strftime(date_format)
            self.existing_backup_files.append(
                {
                    'name': entry,
                    'size': stats.st_size / 1024 / 1024,
                    'date': date
                }
            )

    def upload(self):
        """Upload the composed (and encrypted) backup file"""
        if self.encrypt:
            filename = '{0}.gpg'.format(self.filename)
            filename_abs = '{0}.gpg'.format(self.filename_abs)
        else:
            filename = self.filename
            filename_abs = self.filename_abs
        self.sftp.put(filename_abs, filename)

    def list(self):
        """List all available backups on ftp server"""
        print('{0} (SFTP):'.format(self.name))
        for entry in self.existing_backup_listings:
            print('  {0:<53}{1:<10}{2}'.format(entry['name'],
                                               entry['size'],
                                               entry['date']))
        print('')

    def rotate(self):
        """Only keep the given amount of backup files and delete the rest"""
        files = self.existing_backup_files
        files.reverse()
        files_to_be_deleted = files[self.rotation_num:]
        for backup_file in files_to_be_deleted:
            self.sftp.remove(backup_file['name'])

    def delete(self, name):
        """Delete the given backup file from ftp server"""
        self.sftp.remove(name)

    def download(self):
        """Download the newest backup from ftp server"""
        if not self.existing_backup_files:
            return False
        newest_backup_file = self.existing_backup_files[-1]['name']
        file_target = '{0}/{1}'.format(self.workdir, newest_backup_file)
        self.sftp.get(newest_backup_file, file_target)
        if newest_backup_file.split('.')[-1] == 'gpg':
            self.encrypt = True
            self.filename = '.'.join(newest_backup_file.split('.')[:-1])
        else:
            self.encrypt = False
            self.filename = newest_backup_file
        self.filename_abs = '{0}/{1}'.format(self.workdir, self.filename)
        return True
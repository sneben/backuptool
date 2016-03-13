#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import ftplib  # nosec

from .backup import Backup


class FTPBackup(Backup):
    """Class for creating backups on ftp space"""

    def __init__(self, *args, **kwargs):
        super(FTPBackup, self).__init__(*args, **kwargs)
        self.ftp = None
        self.existing_backup_listings = []
        self.existing_backup_files = []
        self.connect()
        self.set_existing_backups()

    def __del__(self):
        if self.ftp:
            self.ftp.quit()

    def connect(self):
        """Connect against the configured ftp server"""
        match = re.search(r'ftp://([^:/]+):*([^/]*)', self.config['target'])
        host = match.group(1)
        port = 21
        if match.group(2):
            port = match.group(2)
        self.ftp = ftplib.FTP()  # nosec
        self.ftp.connect(host, port)
        self.ftp.login(self.config['ftp_user'], self.config['ftp_password'])

        self.ftp = ftplib.FTP(self.config['target'].split('//')[1])  # nosec
        self.ftp.login(self.config['ftp_user'], self.config['ftp_password'])

    def set_existing_backups(self):
        """Set a list of all existing backups entries found on ftp server"""
        self.ftp.dir(self.existing_backup_listings.append)
        self.existing_backup_files = []
        for entry in self.existing_backup_listings:
            pattern = r'^{0}-\d+.tar.gz(?:.gpg)?$'
            pattern = pattern.format(self.filename_prefix)
            if re.match(pattern, entry.split()[8]):
                self.existing_backup_files.append(entry.split()[8])

    def upload(self):
        """Upload the composed (and encrypted) backup file"""
        if self.encrypt:
            filename = '{0}.gpg'.format(self.filename)
            filename_abs = '{0}.gpg'.format(self.filename_abs)
        else:
            filename = self.filename
            filename_abs = self.filename_abs
        self.ftp.storbinary("STOR " + filename, open(filename_abs, 'rb'), 1024)

    def list(self):
        """List all available backups on ftp server"""
        print('{0} (FTP):'.format(self.name))
        if not self.existing_backup_files:
            print('  <no backups>')
            return
        for entry in self.existing_backup_listings:
            date = ' '.join(entry.split()[5:8])
            size = '{0:.2f}MB'.format(float(entry.split()[4]) / 1024 / 1024)
            name = entry.split()[8]
            print('  {0:<53}{1:<10}{2}'.format(name, size, date))
        print('')

    def rotate(self):
        """Only keep the given amount of backup files and delete the rest"""
        files = self.existing_backup_files
        files.reverse()
        files_to_be_deleted = files[self.rotation_num:]
        for backup_file in files_to_be_deleted:
            self.ftp.delete(backup_file)

    def delete(self, name):
        """Delete the given backup file from ftp server"""
        self.ftp.delete(name)

    def download(self):
        """Download the newest backup from ftp server"""
        if not self.existing_backup_files:
            return False
        newest_backup = self.existing_backup_files[-1]
        file_target = '{0}/{1}'.format(self.workdir, newest_backup)
        with open(file_target, 'wb') as target:
            def callback(data):
                target.write(data)
            self.ftp.retrbinary("RETR " + newest_backup, callback)
        self.check_encryption_by_name(newest_backup)
        return True

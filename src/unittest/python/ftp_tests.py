#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Test suite for testing the ftp target functionality of backuptool"""

import os
import shutil
import tempfile

from mock import patch
from unittest2 import TestCase
from backuptool.ftp import FTPBackup


class FTPBackupTests(TestCase):
    @patch('ftplib.FTP', autospec=True)
    def setUp(self, mock_ftp):
        """Preparations to be done before every test"""
        self.workdir = tempfile.mkdtemp(prefix='backuptool-ftp-tests-')
        self.file_source_dir = '{0}/file_source'.format(self.workdir)
        self.backup_test_workdir = '{0}/workdir'.format(self.workdir)
        os.makedirs(self.file_source_dir)
        os.makedirs(self.backup_test_workdir)
        open('{0}/file_1'.format(self.file_source_dir), 'w').close()
        self.file_patterns = [
            '{0}/file_*'.format(self.file_source_dir)
        ]
        self.ftp_based_config = {
            'ftp_user': 'testuser',
            'ftp_password': 'testpassword',
            'target': 'ftp://testftp.example.com',
            'rotate': 3,
            'files': self.file_patterns
        }
        self.backup = FTPBackup('test_backup',
                                config=self.ftp_based_config,
                                workdir=self.backup_test_workdir)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_ftp_backup(self):
        self.backup.copy_files()
        self.backup.tar_workdir()
        self.backup.upload()

    def test_should_rotate_backup_files(self):
        self.backup.rotate()

    @patch("__builtin__.print")
    def test_should_list_backup_files(self, mock_print):
        entry = ('-rw-r--r--   1 user   group   826948694 Jul 25 04:27 ' +
                 'backup-listtest-20150725062606.tar.gz')
        self.backup.existing_backup_listings = [entry]
        self.backup.list()

    def test_should_download_backup_files(self):
        entry = 'backup-listtest-20150725062606.tar.gz'
        self.backup.existing_backup_files = [entry]
        self.backup.download()

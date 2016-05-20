#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Test suite for testing the ftp target functionality of backuptool"""

import os
import shutil
import tempfile

from mock import patch
from unittest2 import TestCase
from backuptool.sftp import SFTPBackup


class SFTPBackupTests(TestCase):
    @patch('paramiko.SFTPClient', autospec=True)
    @patch('paramiko.Transport', autospec=True)
    def setUp(self, mock_transport, mock_sftp_client):
        """Preparations to be done before every test"""
        self.workdir = tempfile.mkdtemp(prefix='backuptool-sftp-tests-')
        self.file_source_dir = '{0}/file_source'.format(self.workdir)
        self.backup_test_workdir = '{0}/workdir'.format(self.workdir)
        os.makedirs(self.file_source_dir)
        os.makedirs(self.backup_test_workdir)
        open('{0}/file_1'.format(self.file_source_dir), 'w').close()
        self.file_patterns = [
            '{0}/file_*'.format(self.file_source_dir)
        ]
        self.sftp_based_config = {
            'sftp_user': 'testuser',
            'sftp_password': 'testpassword',
            'target': 'sftp://testftp.example.com',
            'rotate': 3,
            'files': self.file_patterns
        }
        existing_backups = ({
            'name': 'backup-listtest-20150725062606.tar.gz',
            'size': '826948694',
            'date': 'Jul 25 04:27 '
        })
        self.backup = SFTPBackup('test_backup',
                                 config=self.sftp_based_config,
                                 workdir=self.backup_test_workdir)
        self.backup.existing_backup_files = [existing_backups]

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
        self.backup.list()

    def test_should_download_backup_files(self):
        self.backup.download()

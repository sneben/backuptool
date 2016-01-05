#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Test suite for testing the file target functionality of backuptool"""

import os
import shutil
import tempfile

from mock import patch
from unittest2 import TestCase
from backuptool import FileBackup


class FileBackupTests(TestCase):
    def setUp(self):
        """Preparations to be done before every test"""
        self.workdir = tempfile.mkdtemp(prefix='backuptool-file-tests-')
        self.file_source_dir = '{0}/file_source'.format(self.workdir)
        self.backup_target_dir = '{0}/target'.format(self.workdir)
        self.backup_test_workdir = '{0}/workdir'.format(self.workdir)
        os.makedirs(self.file_source_dir)
        os.makedirs(self.backup_target_dir)
        os.makedirs(self.backup_test_workdir)
        open('{0}/file_1'.format(self.file_source_dir), 'w').close()
        self.file_patterns = [
            '{0}/file_*'.format(self.file_source_dir),
            '{0}/dir_1'.format(self.file_source_dir)
        ]
        os.makedirs('{0}/dir_1'.format(self.file_source_dir))
        backup_file = '{0}/existing_backup.tar.gz'
        backup_file = backup_file.format(self.backup_target_dir)
        open(backup_file, 'w').close()
        file_based_config = {
            'target': 'file://{0}'.format(self.backup_target_dir),
            'rotate': 3,
            'files': self.file_patterns
        }
        self.backup = FileBackup('test_backup',
                                 config=file_based_config,
                                 workdir=self.backup_test_workdir)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_copy_function(self):
        self.backup.copy_files()
        expected_file = '{0}/files/{1}/file_1'.format(self.backup_test_workdir,
                                                      self.file_source_dir)
        expected_dir = '{0}/files/{1}/dir_1'.format(self.backup_test_workdir,
                                                    self.file_source_dir)
        self.assertTrue(os.path.isfile(expected_file))
        self.assertTrue(os.path.isdir(expected_dir))

    def test_copy_from_backup_source(self):
        self.assertTrue(self.backup.download())

    def test_should_remove_file(self):
        file_to_remove = '{0}/file_to_remove'.format(self.backup_test_workdir)
        open(file_to_remove, 'w').close()
        self.backup.rmfile(file_to_remove)
        self.assertFalse(os.path.isfile(file_to_remove))

    def test_should_rotate_backup_files(self):
        self.backup.rotate()

    @patch('__builtin__.print')
    def test_should_list_backup_files(self, mock_print):
        self.backup.list()

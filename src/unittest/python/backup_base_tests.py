# -*- coding: utf-8 -*-

"""Test suite for testing the basic functionality of backuptool"""

import os
import shutil
import tempfile

from mock import patch
from unittest2 import TestCase
from backuptool.backup import Backup


class BackupBaseTests(TestCase):
    def setUp(self):
        """Preparations to be done before every test"""
        self.workdir = tempfile.mkdtemp(prefix='backuptool-base-tests-')
        self.backup_test_workdir = '{0}/workdir'.format(self.workdir)
        os.makedirs(self.backup_test_workdir)
        base_config = {
            'mysql_databases': ['test_db_1', 'test_db_2'],
            'mysql_user': 'testuser',
            'mysql_password': 'testpassword',
            'ldap_backup': {
                'datadir': '/tmp/ldap',
                'system_user': 'ldap',
                'system_group': 'ldap'
            },
            'rotate': 3
        }
        self.backup = Backup('test_backup',
                             config=base_config,
                             workdir=self.backup_test_workdir)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    @patch('subprocess.check_call')
    def test_restore_commands(self, mock_check_call):
        os.makedirs('{0}/ldap'.format(self.backup_test_workdir))
        os.makedirs('{0}/mysql'.format(self.backup_test_workdir))
        self.backup.restore_database()
        self.backup.restore_ldap()
        self.backup.restore_files()

    @patch('subprocess.check_call')
    def test_dump_commands(self, mock_check_call):
        self.backup.dump_database()
        self.backup.dump_ldap()

##!/usr/bin/python
## -*- coding: utf-8 -*-
#
#import os
#import boto
#import shutil
#import tempfile
#
#from boto.s3.key import Key
#from mock import patch
#from moto import mock_s3
#from unittest2 import TestCase
#from backuptool.s3 import S3Backup
#
#
#class S3BackupTests(TestCase):
#    def setUp(self):
#        self.workdir = tempfile.mkdtemp(prefix='backuptool-s3-tests-')
#        self.file_source_dir = '{0}/file_source'.format(self.workdir)
#        self.backup_test_workdir = '{0}/workdir'.format(self.workdir)
#        os.makedirs(self.file_source_dir)
#        os.makedirs(self.backup_test_workdir)
#        open('{0}/file_1'.format(self.file_source_dir), 'w').close()
#        self.file_patterns = [
#            '{0}/file_1'.format(self.file_source_dir)
#        ]
#        self.s3_based_config = {
#            'aws-access-key-id': 'AKIAIOSFODNN7EXAMPLE',
#            'aws-secret-access-key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY',
#            'target': 's3://backup-test-bucket',
#            'rotate': 3,
#            'files': self.file_patterns
#        }
#
#    def tearDown(self):
#        shutil.rmtree(self.workdir)
#
#    @mock_s3
#    def test_s3_backup(self):
#        connection = boto.connect_s3()
#        connection.create_bucket('backup-test-bucket')
#        backup = S3Backup('test_backup',
#                          config=self.s3_based_config,
#                          workdir=self.backup_test_workdir)
#        backup.copy_files()
#        backup.tar_workdir()
#        backup.upload()
#
#    @mock_s3
#    def test_should_rotate_backup_files(self):
#        connection = boto.connect_s3()
#        connection.create_bucket('backup-test-bucket')
#        backup = S3Backup('test_backup',
#                          config=self.s3_based_config,
#                          workdir=self.backup_test_workdir)
#        backup.rotate()
#
#    @mock_s3
#    @patch('__builtin__.print')
#    def test_should_list_backup_files(self, mock_print):
#        connection = boto.connect_s3()
#        bucket = connection.create_bucket('backup-test-bucket')
#        k = Key(bucket, name='backup-listtest-20150725062606.tar.gz')
#        k.size = '1234567890'
#        backup = S3Backup('test_backup',
#                          config=self.s3_based_config,
#                          workdir=self.backup_test_workdir)
#        backup.s3_keys = [k]
#        backup.list()
#
#    @mock_s3
#    def test_should_download_backup_files(self):
#        connection = boto.connect_s3()
#        connection.create_bucket('backup-test-bucket')
#        backup = S3Backup('test_backup',
#                          config=self.s3_based_config,
#                          workdir=self.backup_test_workdir)
#        backup.download()
#

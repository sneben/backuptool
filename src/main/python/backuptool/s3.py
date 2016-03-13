#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from boto import s3
from .backup import Backup
from boto.s3.key import Key
from datetime import datetime


class S3Backup(Backup):
    """Class for creating backups on aws s3"""

    def __init__(self, *args, **kwargs):
        super(S3Backup, self).__init__(*args, **kwargs)
        self.region = self.config.get('aws-region', 'eu-central-1')
        self.connection = None
        self.bucket = None
        self.s3_keys = None
        self.bucket_name = self.config['target'].split('://')[1]
        self.connect()
        self.set_s3_keys()

    def connect(self):
        """Connect against aws services"""
        key_id = self.config['aws-access-key-id']
        secret_key = self.config['aws-secret-access-key']
        self.connection = s3.connect_to_region(self.region,
                                               aws_access_key_id=key_id,
                                               aws_secret_access_key=secret_key)
        self.bucket = self.connection.get_bucket(self.bucket_name)

    def set_s3_keys(self):
        """Set a list of all existing key entries in the defined bucket"""
        self.s3_keys = self.bucket.get_all_keys(prefix=self.filename_prefix)
        self.s3_keys.reverse()

    def upload(self):
        """Upload the composed (and encrypted) backup file"""
        k = Key(self.bucket)
        if self.encrypt:
            k.key = '{0}.gpg'.format(self.filename)
            k.set_contents_from_filename('{0}.gpg'.format(self.filename_abs))
        else:
            k.key = self.filename
            k.set_contents_from_filename(self.filename_abs)

    def download(self):
        """Download the newest backup from s3"""
        if not self.s3_keys:
            return False
        newest_backup = self.s3_keys[0]
        file_target = '{0}/{1}'.format(self.workdir, newest_backup.name)
        newest_backup.get_contents_to_filename(file_target)
        self.check_encryption_by_name(newest_backup.name)
        return True

    def rotate(self):
        """Only keep the given amount of bucket keys and delete the rest"""
        keys_to_be_deleted = self.s3_keys[self.rotation_num:]
        for key in keys_to_be_deleted:
            key.delete()

    def list(self):
        """List all available backups for this type"""
        print('{0} (S3):'.format(self.name))
        if not self.s3_keys:
            print('  <no backups>')
            return
        for key in self.s3_keys:
            key_timestamp = '-'.join(key.name.split('-')[-1:]).split('.')[0]
            parsed_date = datetime.strptime(key_timestamp, '%Y%m%d%H%M%S')
            date = parsed_date.strftime('%Y-%m-%dT%H:%M:%S')
            size = '{0:.2f}MB'.format(float(key.size) / 1024 / 1024)
            print('  {0:<53}{1:<10}{2}'.format(key.name, size, date))
        print('')

    def delete(self, name):
        """Delete the given backup from s3 bucket"""
        for key in self.s3_keys:
            if key.name == name:
                key.delete()

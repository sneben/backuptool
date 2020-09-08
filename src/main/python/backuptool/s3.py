# -*- coding: utf-8 -*-

import boto3

from .backup import Backup
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
        self._connect()
        self.set_s3_keys()

    def _connect(self):
        """Connect against aws services"""
        key_id = self.config['aws-access-key-id']
        secret_key = self.config['aws-secret-access-key']
        self.connection = boto3.client('s3',
                                       aws_access_key_id=key_id,
                                       aws_secret_access_key=secret_key)

    def set_s3_keys(self):
        """Set a list of all existing key entries in the defined bucket"""
        objects = self.connection.list_objects(Bucket=self.bucket_name)
        contents = objects['Contents']
        self.s3_keys = \
            [d for d in contents if d['Key'].startswith('backup-auth')]
        self.s3_keys.reverse()

    def upload(self):
        """Upload the composed (and encrypted) backup file"""
        if self.encrypt:
            abs_path = '{0}.gpg'.format(self.filename_abs)
            filename = '{0}.gpg'.format(self.filename)
        else:
            abs_path = self.filename_abs
            filename = self.filename
        self.connection.upload_file(abs_path, self.bucket_name, filename)

    def download(self):
        """Download the newest backup from s3"""
        if not self.s3_keys:
            return False
        newest_backup = self.s3_keys[0]
        file_target = '{0}/{1}'.format(self.workdir, newest_backup['Key'])
        self.connection.download_file(self.bucket_name,
                                      newest_backup['Key'],
                                      file_target)
        self.check_encryption_by_name(newest_backup['Key'])
        return True

    def rotate(self):
        """Only keep the given amount of bucket keys and delete the rest"""
        keys_to_be_deleted = self.s3_keys[self.rotation_num:]
        for key in keys_to_be_deleted:
            self.delete(key['Key'])

    def list(self):
        """List all available backups for this type"""
        print('{0} (S3):'.format(self.name))
        if not self.s3_keys:
            print('  <no backups>\n')
            return
        for key, more_items in self._lookahead(self.s3_keys):
            key_timestamp = '-'.join(key['Key'].split('-')[-1:]).split('.')[0]
            parsed_date = datetime.strptime(key_timestamp, '%Y%m%d%H%M%S')
            date = parsed_date.strftime('%Y-%m-%dT%H:%M:%S')
            size = '{0:.2f}MB'.format(float(key['Size']) / 1024 / 1024)
            if more_items:
                tree_prefix = '├─ '
            else:
                tree_prefix = '└─ '
            print('{0}{1:<53}{2:<10}{3}'.format(tree_prefix,
                                                key['Key'],
                                                size,
                                                date))
        print('')

    def delete(self, name):
        """Delete the given backup object from s3 bucket"""
        self.connection.delete_object(Bucket=self.bucket_name, Key=name)

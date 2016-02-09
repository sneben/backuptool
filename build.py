from pybuilder.core import use_plugin, init, task, depends, Author

use_plugin('python.core')
use_plugin('python.unittest')
use_plugin('python.install_dependencies')
use_plugin('python.flake8')
use_plugin('python.coverage')
use_plugin('python.distutils')

name = 'backuptool'
summary = 'Create simple backups and store them on Filesystem, FTP or S3'
description = """Create backups of different source types
(file, mysql, ldap), optionally encrypt it with pgp and store the
result on s3, ftp or on the local filesystem"""
license = 'Apache License 2.0'
authors = [Author('Stefan Neben', "stefan.neben@mailfoo.net")]
url = 'https://github.com/sneben/backuptool'
version = '0.1'
default_task = ['clean', 'analyze', 'package']


@init
def set_properties(project):
    project.depends_on('boto')
    project.depends_on('gnupg')
    project.depends_on('docopt')
    project.depends_on('yamlreader')
    project.build_depends_on('mock')
    project.build_depends_on('moto')
    project.build_depends_on('unittest2')


@task
@depends('prepare')
def build_directory(project):
    print project.expand_path("$dir_dist")

#!/usr/local/bin/python3.6 -u

# Installer for gavin-dpv software

import os.path
from os import unlink

# File locations
file_map = {}
file_map['top level dir'] = '/opt/gavin'
file_map['config_dir'] = '/opt/gavin/etc'
file_map['bin_dir'] = '/opt/gavin/bin'

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys, urllib2, re
from ConfigParser import SafeConfigParser

DEFAULT_PATH = os.path.join(os.path.expanduser("~"), "")
CONFIG_FILE = os.path.join(DEFAULT_PATH, '.xPhotOrganizer.cfg')
url = 'https://maps.googleapis.com/maps/api/place/search/json?radius=500&sensor=false&language=es&key=AIzaSyAIUxeFm3wCYMZGCJGFNi5zX2BjsXqCtCw&location='


def write_config(config):
    if config:
        with open(CONFIG_FILE, 'w') as cfg:
            config.write(cfg)

        return True
    else:
        return False

def get_config():
    """
    """
    DEFAULTS = { 'main': {
                    "source_dir": os.path.join(DEFAULT_PATH, ""),
                    "dest_dir": os.path.join(DEFAULT_PATH, "Pictures"),
                    },
                }
    config = SafeConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print "There is no config file. Creating default %s" % CONFIG_FILE
        for section, options in DEFAULTS.items():
            for section, options in DEFAULTS.items():
                if not config.has_section(section):
                    config.add_section(section)
                for option, value in options.items():
                    config.set(section, option, value)

        write_config(config)
    else:
        with open(CONFIG_FILE, 'r') as cfg:
            config.readfp(cfg)

    return config

def get_locations(lat,lon):
    base_url = url+str(lat)+','+str(lon)
    data = json.load(urllib2.urlopen(base_url))
    return data

def convert_pos(g, m, s):
    pos = g + (m / 60.0) + (s / 3600)
    return pos

def count_files(directory):
    qty = 0
    for filename in os.listdir(directory):
        if re.match(r'.*\.jpg$', filename, re.I):
            qty += 1
    return qty

def file_size(directory):
    size = 0
    for filename in os.listdir(directory):
        print directory, filename
        if re.match(r'.*\.jpg$', filename, re.I):
                    size += os.path.getsize(os.path.join(directory,filename))
    return size

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
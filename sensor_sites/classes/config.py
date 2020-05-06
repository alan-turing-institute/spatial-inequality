#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
| System-wide configuration
|
| Assumes the existence of the file 'settings.ini' for accessing the NISMOD DB++ API.  This should reside in
| the same directory ('classes') as this file, and contain the following lines:
|     
| [API_CREDENTIALS]
| username = <api_username>
| password = <api_password>
|
| Note that no extra quotation marks are required around the credentials.
|
| Created on Fri Jan 10 2020 16:15
|
| @author: ndh114
"""

import logging
import configparser
from os.path import dirname, join


class Config:

    # Project top-level directory
    __project_root = dirname(dirname(__file__))

    # Read API credentials from the (non-Git managed) api_credentials.ini file
    __ini_parser = configparser.ConfigParser()
    __ini_parser.read("{}/settings.ini".format(dirname(__file__)))

    __conf = {
        # NISMOD-DB++ API
        "NISMOD_DB_API_USERNAME": __ini_parser["API_CREDENTIALS"]["username"],
        "NISMOD_DB_API_PASSWORD": __ini_parser["API_CREDENTIALS"]["password"],
        "NISMOD_DB_API_URL": "https://www.nismod.ac.uk/api/data",
        # NISMOD-DB++ database credentials (on VM)
        "NISMOD_DB_HOST": __ini_parser["DB_CREDENTIALS"]["host"],
        "NISMOD_DB_USERNAME": __ini_parser["DB_CREDENTIALS"]["username"],
        "NISMOD_DB_PASSWORD": __ini_parser["DB_CREDENTIALS"]["password"],
        # Logging
        "LOG_LEVEL": logging.INFO,
        "LOG_FILE": join(__project_root, "logs", "dst-wps.log"),
        "LOG_FORMAT": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        "LOG_DATE_FORMAT": "%d-%m %H:%M",
        # Default data directory
        "DATA_DIRECTORY": join(__project_root, "test_data"),
        # British National Grid projection
        "BRITISH_NATIONAL_GRID": "epsg:27700",
        # Snap tolerance for relaxing points onto segments of road network, in metres
        "SNAP_TOLERANCE": 100,
    }

    __setters = ["LOG_LEVEL"]

    @staticmethod
    def get(name):
        return Config.__conf[name]

    @staticmethod
    def set(name, value):
        if name in Config.__setters:
            Config.__conf[name] = value
        else:
            raise NameError("Name not accepted in set() method")

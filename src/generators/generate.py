"""Script for coordinating multiple types of file generation"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__created__ = "2017-03-09"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
import utils.log

# Possible types of files to generate
TYPES = [
    "base",
    "detector",
    "plugin",
    "test"
]

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    # Set up terminal printer
    # Verbosity
    if commandline_args.verbose:
        terminal_log_level = 10
    else:
        terminal_log_level = 50

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=True)

    # Print out commandline arguments
    tprint(arg="\nCommandline arguments:", level=10)
    for pair in commandline_args._get_kwargs():
        tprint(arg="  arg:%-20s  val:%s" % (pair[0], pair[1]), level=10)

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate RAPD files"
    parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    parser.add_argument("-v", "--verbise",
                        action="store_true",
                        dest="verbose",
                        help="Control verbosity")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="type",
                        nargs=1,
                        default="base",
                        choices=TYPES,
                        help="Type of file to be generated")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        parser.print_help()
        parser.exit()

    return parser.parse_args()

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)
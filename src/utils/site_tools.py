"""
This file is part of RAPD

Copyright (C) 2016 Cornell University
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

__created__ = "2016-01-27"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import functools
import os
import sys

def get_site_files():
    """Returns a list of site files

    Uses the PYTHONPATH to find the sites directory for this rapd install and then
    walks it to find all files that have names that match "*.py" and do not start with
    "_" or have the word "secret"
    """
    # print "get_site_files"

    # Looking for the rapd src directory
    sites_dir = False
    for path in sys.path:
        if "rapd" in path and path.endswith("src"):
            sites_dir = os.path.join(path, "sites")

    if sites_dir:
        # print "Looking for site definition files in %s" % sites_dir
        site_files = []
        for (path, directory, files) in os.walk(sites_dir):
            for filename in files:
                # No secret-containing files
                if "secret" in filename:
                    continue
                # No files that start with _
                if filename.startswith("_"):
                    continue
                # Filename must end with .py
                if filename.endswith(".py"):
                    site_files.append(os.path.join(path, filename))
    else:
        raise Exception("Cannot find sites directory on PYTHONPATH")

    if len(site_files) == 0:
        raise Exception("No site files found")
    else:
        return site_files

def check_site_against_known(site_str):
    """Check a site string against known sites in the sites directory

    Keyword arguments:
    site_str -- user-specified site string
    """
    pass

def determine_site(site_arg=None):
    """Determine the site for a run instance

    Keyword arguments:
    site_arg -- user-specified site arguments (default None)
    """
    terminal_print("determine_site", level=1)
    # Get site files
    site_files = get_site_files()

    # Transform site files to a more palatable form
    safe_sites = {}
    for site_file in site_files:
        safe_site = os.path.basename(site_file).split(".")[0].lower()
        safe_sites[safe_site] = site_file

    # No site_arg, look to the path for the site
    safe_site_args = []
    if site_arg == None:
        cwd = os.getcwd()
        path_elems = cwd.split(os.path.sep)
        for path_elem in reversed(path_elems):
            safe_path_elem = path_elem.lower()
            if len(safe_path_elem) > 0:
                safe_site_args.append(safe_path_elem)
    else:
        # Transform the input site_arg to lowercase string
        safe_site_args.append(str(site_arg).lower())

    # Now search safe_sites for safe_site_args
    for safe_site_arg in safe_site_args:
        if safe_site_arg in safe_sites:
            print "Have one! %s %s" % (safe_site_arg, safe_sites[safe_site_arg])

def verbose_print(arg, level, verbosity=1):
    if level <= verbosity:
        print arg

if __name__ == "__main__":

    print "site_tools.py"
    print "============="

    terminal_print = functools.partial(verbose_print, verbosity=2)
    determine_site()
    determine_site("necat_C")

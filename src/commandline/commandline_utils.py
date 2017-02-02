"""
Utilities for commandline running
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

__created__ = "2016-11-28"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import glob
import multiprocessing
import os
import pprint

# RAPD imports
import detectors.detector_utils as detector_utils
# import utils.log
# import utils.lock
import utils.site
# import utils.text as text

# The data processing parser - to be used by commandline RAPD processes
dp_parser = argparse.ArgumentParser(add_help=False)

# Verbosity
dp_parser.add_argument("-v", "--verbose",
                       action="store_true",
                       dest="verbose",
                       help="Enable verbose feedback")

# Test mode?
dp_parser.add_argument("-t", "--test",
                       action="store_true",
                       dest="test",
                       help="Run in test mode")

# The site
dp_parser.add_argument("-s", "--site",
                       action="store",
                       dest="site",
                       help="Define the site (ex. NECAT_C)")

# List possible sites
dp_parser.add_argument("-ls", "--listsites",
                       action="store_true",
                       dest="listsites",
                       help="List the available sites")

# The detector
dp_parser.add_argument("-d", "--detector",
                       action="store",
                       dest="detector",
                       help="Define the detector (ex. adsc_q315)")

# List possible detectors
dp_parser.add_argument("-ld", "--listdetectors",
                       action="store_true",
                       dest="listdetectors",
                       help="List the available detectors")

# Beam center
dp_parser.add_argument("-b", "--beamcenter",
                       action="store",
                       dest="beamcenter",
                       default=[False, False],
                       nargs=2,
                       type=float,
                       help="Define the beam center x,y")

# Spacegroup
dp_parser.add_argument("-sg", "--spacegroup",
                       action="store",
                       dest="spacegroup",
                       default=False,
                       help="Input a spacegroup")

# Sample type
dp_parser.add_argument("--sample_type",
                       action="store",
                       dest="sample_type",
                       default="protein",
                       choices=["protein", "dna", "rna", "peptide"],
                       help="The type of sample")

# Solvent fraction
dp_parser.add_argument("--solvent",
                       action="store",
                       dest="solvent",
                       type=float,
                       help="Solvent fraction 0.0-1.0")

# Resolution low
dp_parser.add_argument("--lowres",
                       action="store",
                       dest="lowres",
                       type=float,
                       help="Low resolution limit")

# Resolution hi
dp_parser.add_argument("--hires",
                       action="store",
                       dest="hires",
                       default=0.0,
                       type=float,
                       help="High resolution limit")

# Working directory
dp_parser.add_argument("--work_dir",
                       action="store",
                       dest="work_dir",
                       default=False,
                       help="Working directory")

# Number of processors to use
dp_parser.add_argument("--nproc",
                       action="store",
                       dest="nproc",
                       type=int,
                       default=multiprocessing.cpu_count(),
                       help="Number of processors to use. Defaults to the number of processors available")

# The rapd file generating parser - to be used by commandline RAPD processes
gf_parser = argparse.ArgumentParser(add_help=False)

# Verbosity
gf_parser.add_argument("-v", "--verbose",
                       action="store_true",
                       dest="verbose",
                       help="Enable verbose feedback")

# Test mode?
gf_parser.add_argument("-t", "--test",
                       action="store_true",
                       dest="test",
                       help="Run in test mode")

# Test mode?
gf_parser.add_argument("-f", "--force",
                       action="store_true",
                       dest="force",
                       help="Allow overwriting of files")

# Maintainer
gf_parser.add_argument("-m", "--maintainer",
                       action="store",
                       dest="maintainer",
                       default="Your name",
                       help="Maintainer's name")

# Maintainer's email
gf_parser.add_argument("-e", "--email",
                       action="store",
                       dest="email",
                       default="Your email",
                       help="Maintainer's email")

# Directory or files
gf_parser.add_argument(action="store",
                       dest="file",
                       nargs="?",
                       default=False,
                       help="Name of file to be generated")

def print_sites(left_buffer=""):
    """
    Print out all the sites
    """
    sites = utils.site.get_site_files()

    for site in sites:
        print left_buffer + os.path.basename(site)

def print_detectors(left_buffer="", show_py=False):
    """
    Print out all the detectors
    """
    detectors = detector_utils.get_detector_files()

    for detector in detectors:
        if not show_py:
            detector_name = os.path.basename(detector).replace(".py", "")
        else:
            detector_name = os.path.basename(detector)

        print left_buffer + detector_name

def analyze_data_sources(sources, mode="index"):
    """
    Return information on files or directory from input
    """
    # print "analyze_data_sources", sources

    return_data = {}

    if mode == "index":

        for source in sources:
            source_abspath = os.path.abspath(source)

            # Does file/dir exist?
            if os.path.exists(source_abspath):
                if os.path.isdir(source_abspath):
                    pass
                elif os.path.isfile(source_abspath):
                    if mode == "index":
                        # 1st file of 1 or 2
                        if not "files" in return_data:
                            return_data["files"] = [source_abspath]
                        # 3rd file - error
                        elif len(return_data["files"]) > 1:
                            raise Exception("Up to two images can be submitted for indexing")
                        # 2nd file - presumably a pair
                        else:
                            # Same file twice
                            if source_abspath == return_data["files"][0]:
                                raise Exception("The same image has been submitted twice for indexing")
                            else:
                                return_data["files"].append(source_abspath)
                                break
            else:
                raise Exception("%s does not exist" % source_abspath)

    elif mode == "integrate":

        template = sources

        # Establish the abspath
        full_path_template = os.path.abspath(template)

        # Grab a list of files
        # "#" as numbers that increment
        return_data = glob.glob(full_path_template.replace("#", "[0-9]"))
        # "?" as numbers that increment
        return_data = glob.glob(full_path_template.replace("?", "[0-9]"))
        return_data.sort()
        pprint.pprint(return_data)

        if len(return_data) == 0:
            raise Exception("No files for %s found" % template)

    return return_data


if __name__ == "__main__":

    print "commandline_utils.py"

    parser = argparse.ArgumentParser(parents=[dp_parser],
                                     description="Testing")
    returned_args = parser.parse_args()
    print "\nVariables:"
    print "%20s  %-10s" % ("var", "val")
    print "%20s  %-10s" % ("=======", "=======")
    for pair in returned_args._get_kwargs():
        print "%20s  %-10s" % pair


    print "\nSites:"
    print_sites(left_buffer="  ")

"""HDF5 utilities for RAPD"""

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

__created__ = "2017-02-08"
_maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
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
# import sys
# import time

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

def convert_hdf5_cbf(inp,
                     odir=False,
                     prefix=False,
                     imgn=False,
                     zfill=5,
                     logger=False):
    """
    Run eiger2cbf on HDF5 dataset. Returns path of new CBF files.
    Not sure I need multiprocessing.Pool, but used as saftety.
    odir is output directory
    prefix is new image prefix
    imgn is the image number for the output frame.
    zfill is the number digits for snap image numbers
    returns header
    """
    import multiprocessing, time, sys
    from rapd_pilatus import pilatus_read_header as readHeader

    if logger:
        logger.debug('Utilities::convert_hdf5_cbf')

    try:
        #command0 = '/gpfs6/users/necat/Jon/Programs/CCTBX_x64/base_tmp/eiger2cbf/trunk/eiger2cbf %s'%inp
        command0 = "eiger2cbf %s" % inp

        if odir:
            out = odir
        else:
            out = '/gpfs6/users/necat/Jon/RAPD_test/Output/Temp'
        if prefix == False:
            prefix = 'conv_1_'

        # check if folder exists, if not make it and change to it.
        #folders2(self,out)
        if os.path.exists(out) == False:
            os.makedirs(out)
        os.chdir(out)

        if inp.count("master"):

            # Not really needed, unless someone collected a huge dataset.
            ncpu = multiprocessing.cpu_count()
            pool = multiprocessing.Pool(processes=ncpu)

            # Check how many frames are in dataset
            nimages = pool.apply_async(processLocal, ((command0, os.path.join(out, "test.log")),))
            nimages.wait()
            total = int(open('test.log','r').readlines()[-1])
            if BLspec.checkCluster():
                # Half the number of nodes in the queue.
                split = int(round(total/8))
                cluster = True
            else:
                # Least amount of splitting without running out of memory.
                split = 360
                cluster = False
            st = 1
            end = split
            stop = False
            # For Autoindexing. Differentiate pairs from separate runs.
            if total == 1:
                # Set the image number defaut to 1.
                if imgn == False: imgn = 1
                img = '%s%s.cbf'%(os.path.join(out,prefix),str(imgn).zfill(zfill))
                command = '%s 1 %s'%(command0, img)
            else:
                command = '%s %s:%s %s'%(command0,st, end, os.path.join(out,prefix))
            while 1:
                if cluster:
                    # No self required
                    pool.apply_async(BLspec.processCluster_NEW, ((command,os.path.join(out,'eiger2cbf.log')),))
                else:
                    pool.apply_async(processLocal, ((command,os.path.join(out,'eiger2cbf.log')),))
                time.sleep(0.1)
                if stop:
                    break
                st += split
                end += split
                # Check to see if next round will be out of range
                if st >= total:
                    break
                if st + split >= total:
                    end = total
                    stop = True
                if end > total:
                    end = total
            pool.close()
            pool.join()

            # Get the detector description from the h5 file
            with open('eiger2cbf.log','r') as f:
                for line in f:
                    if line.count('description'):
                        det = line[line.find('=')+2:].strip()
                        break

            # Read header from first image and pass it back.
            header = readHeader(img)

            # change the detector
            header['detector'] = det
            return(header)
        else:
            return('Not master file!!!')

    except:
        if logger:
            logger.exception('**ERROR in Utils.convert_hdf5_cbf**')
        return("FAILED")


def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    # parser.add_argument("-c", "--commandline",
    #                     action="store_true",
    #                     dest="commandline",
    #                     help="Generate commandline argument parsing")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)

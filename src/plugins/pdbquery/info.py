"""This is a docstring for this container file"""

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

__created__ = "2017-04-20"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
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
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

# Dict with PDB codes for common contaminants.
CONTAMINANTS = {
    "1E1O": {"Name": "LYSYL-TRNA SYNTHETASE, HEAT INDUCIBLE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/e1/1e1o.cif"},
    "1ESO": {"Name": "CU, ZN SUPEROXIDE DISMUTASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/es/1eso.cif"},
    "1G6N": {"Name": "CATABOLITE GENE ACTIVATOR PROTEIN",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/g6/1g6n.cif"},
    "1GGE": {"Name": "PROTEIN (CATALASE HPII)",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/gg/1gge.cif"},
    "1I6P": {"Name": "CARBONIC ANHYDRASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/i6/1i6p.cif"},
    "1OEE": {"Name": "HYPOTHETICAL PROTEIN YODA",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/oe/1oee.cif"},
    "1OEL": {"Name": "GROEL (HSP60 CLASS)",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/oe/1oel.cif"},
    "1PKY": {"Name": "PYRUVATE KINASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/pk/1pky.cif"},
    "1X8F": {"Name": "2-dehydro-3-deoxyphosphooctonate aldolase",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/x8/1x8f.cif"},
    "1Z7E": {"Name": "protein ArnA",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/z7/1z7e.cif"},
    "2JGD": {"Name": "2-OXOGLUTARATE DEHYDROGENASE E1 COMPONENT",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/jg/2jgd.cif"},
    "2QZS": {"Name": "glycogen synthase",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/qz/2qzs.cif"},
    "2VF4": {"Name": "GLUCOSAMINE--FRUCTOSE-6-PHOSPHATE AMINOTRANSFERASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/vf/2vf4.cif"},
    "2Y90": {"Name": "PROTEIN HFQ",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/y9/2y90.cif"},
    "3CLA": {"Name": "TYPE III CHLORAMPHENICOL ACETYLTRANSFERASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/cl/3cla.cif"},
    "4UEJ": {"Name": "GALACTITOL-1-PHOSPHATE 5-DEHYDROGENASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/ue/4uej.cif"},
    "4QEQ": {"Name": "Lysozyme C",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/qe/4qeq.cif"},
    "2I6W": {"Name": "AcrB",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/i6/2i6w.cif"},
    "1NEK": {"Name": "Succinate dehydrogenase flavoprotein subunit",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/ne/1nek.cif"},
    "1TRE": {"Name": "TRIOSEPHOSPHATE ISOMERASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/tr/1tre.cif"},
    "1I40": {"Name": "INORGANIC PYROPHOSPHATASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/i4/1i40.cif"},
    "2P9H": {"Name": "Lactose operon repressor",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/p9/2p9h.cif"},
    "1PHO": {"Name": "PHOSPHOPORIN",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/ph/1pho.cif"},
    "1BTL": {"Name": "BETA-LACTAMASE",
             "path": "/gpfs5/users/necat/rapd/pdbq/pdb/bt/1btl.cif"},
}

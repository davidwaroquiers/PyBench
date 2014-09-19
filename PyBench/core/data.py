from __future__ import print_function, division

__author__ = 'setten'
__version__ = "0.1"
__maintainer__ = "Michiel van Setten"
__email__ = "mjvansetten@gmail.com"
__date__ = "Sept 2014"

import copy
import os
import pymongo
import gridfs
from abc import ABCMeta, abstractmethod
from PyBench.core.descriptions import BaseDescription, get_description
from pymatgen.io.vaspio.vasp_output import Vasprun
from pymatgen.io.vaspio.vasp_output import Outcar
from xml.etree.cElementTree import ParseError
from pymongo.errors import OperationFailure
from pymongo import Connection

def get_collection(server="marilyn.pcpm.ucl.ac.be", db_name="Bencmark_results", collection="vasp", with_gfs=False):
    """
    Add the actual pymongo collection object as self.col

    :param server:
    name of the server

    :param db_name:
    name of the data_base

    :param collection:
    name of the collection

    :return:
    """
    local_serv = Connection(server)
    try:
        user = os.environ['MAR_USER']
    except KeyError:
        user = input('DataBase user name: ')
    try:
        pwd = os.environ['MAR_PAS']
    except KeyError:
        pwd = input('DataBase pwd: ')
    db = local_serv[db_name]
    db.authenticate(user, pwd)
    if with_gfs:
        return db[collection], gridfs.GridFS(db)
    else:
        return db[collection]


class BaseDataSet(object):
    """
    object to handle the data from benchmark calculations
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        """
        description will contain the description of the cluster and code version and compilation
        data will contain the actual data
        """
        self.description = BaseDescription
        self.data = {}
        try:
            self.col = get_collection()
        except pymongo.errors.OperationFailure:
            print("pymongo operation failure, no DB support")
        self.ncpus = []

    @abstractmethod
    def gather_data(self):
        """
        read the data from path
        """
        # read the calculation results

    def insert_in_db(self):
        entry = copy.deepcopy(self.description)
        entry.update(self.data)
        self.col.save(entry)

    def set_parameter_lists(self):
        print("NCPUS:\n%s\n" % self.ncpus)

    def print_parameter_lists(self):
        for entry in self.data:
            if entry["ncpus"] not in self.ncpus:
                self.ncpus.append(entry["ncpus"])
        self.ncpus.sort()

class VaspData(BaseDataSet):
    """
    object for vasp benchmark data
    """
    def __init__(self):
        self.code = 'vasp'
        super(VaspData, self).__init__()
        self.description = get_description(self.code)
        self.data = {}

    def add_data_entry(self, path):
        try:
            xml = Vasprun(os.path.join(path, "vasprun.xml"))
            out = Outcar(os.path.join(path, "OUTCAR"))
            if xml.converged:
                entry = {
                    "NPAR": xml.parameters.get('NPAR'),
                    'ncpus': out.run_stats['cores'],
                    "final_energy": xml.final_energy,
                    "vasp_version": xml.vasp_version,
                    "generator": xml.generator,
                    "generator_hash": hash(frozenset(xml.generator)),
                    "total_wall_time": out.run_stats}
                entry_hash = hash((entry['ncpus'], entry['NPAR'], entry['generator_hash']))
                print(entry)
                self.data.update({entry_hash: entry})
        except (ParseError, ValueError):
            pass

    def gather_data(self):
        tree = os.walk(".")
        for dirs in tree:
            data_file = os.path.join(dirs[0], 'vasprun.xml')
            if os.path.isfile(data_file):
                print(data_file)
                self.add_data_entry(dirs[0])


def get_data_set(code):
    """
    factory function
    :param code:
    :return:
    """
    data_sets = {'vasp': VaspData()}
    return data_sets[code]
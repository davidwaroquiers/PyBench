from __future__ import print_function, division

__author__ = 'setten'
__version__ = "0.1"
__maintainer__ = "Michiel van Setten"
__email__ = "mjvansetten@gmail.com"
__date__ = "Sept 2014"

import copy
import os
from abc import ABCMeta, abstractmethod
from PyBench.core.descriptions import BaseDescription, get_description
from pymatgen.io.vaspio.vasp_output import Vasprun
from pymatgen.io.vaspio.vasp_output import Outcar
from xml.etree.cElementTree import ParseError


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

    @abstractmethod
    def gather_data(self):
        """
        read the data from path
        """
        # read the calculation results

    def insert_in_db(self):
        entry = copy.deepcopy(self.description)
        entry.update(self.data)


class VaspData(BaseDataSet):
    """
    object for vasp benchmark data
    """
    def __init__(self):
        self.code = 'vasp'
        super(BaseDataSet, self).__init__()
        self.description = get_description(self.code)
        self.data = {}

    def add_data_entry(self, path):
        try:
            xml = Vasprun(os.path.join(path, "vasprun.xml"))
            out = Outcar(os.path.join(path, "OUTCAR"))
            if xml.converged:
                entry = {
                    "NPAR": xml.parameters.get('NPAR'),
                    'ncpus': None,
                    "final_energy": xml.final_energy,
                    "vasp_version": xml.vasp_version,
                    "generator": xml.generator,
                    "generator_hash": hash(frozenset(xml.generator)),
                    "total_wall_time": out.run_stats}
                entry_hash = hash((entry['ncpus'], entry['NPAR'], entry['generator_hash']))
                print(entry)
                self.data.update({entry_hash: entry})
        except ParseError:
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
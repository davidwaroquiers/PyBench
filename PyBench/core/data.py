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

    def add_data_entry(self, path):
        data = Vasprun(path)
        entry = {}
        if data.converged:
            entry = {
                "NPAR": data.parameters.get('NPAR'),
                "final_energy": data.final_energy,
                "vasp_version": data.vasp_version}
        print(entry)

    def gather_data(self):
        tree = os.walk(".")
        for dirs in tree:
            data_file = os.path.join(dirs[0], 'vasprun.xml')
            if os.path.isfile(data_file):
                self.add_data_entry(data_file)


def get_data_set(code):
    """
    factory function
    :param code:
    :return:
    """
    data_sets = {'vasp': VaspData()}
    return data_sets[code]
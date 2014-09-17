__author__ = 'setten'

import copy
from abc import ABCMeta, abstractmethod
from PyBench.core.descriptions import BaseDescription, get_description


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
    def get_data(self, path):
        """
        read the data from path
        """
        # read the calculation info file
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

    def get_data(self, path):
        pass
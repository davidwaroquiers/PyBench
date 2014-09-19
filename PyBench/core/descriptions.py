from __future__ import print_function, division

__author__ = 'setten'
__version__ = "0.1"
__maintainer__ = "Michiel van Setten"
__email__ = "mjvansetten@gmail.com"
__date__ = "Sept 2014"

import os
import ast
import copy
from abc import ABCMeta, abstractmethod


class BaseDescription(object):
    """
    object to handle descriptions
    concrete implementation are made for specific codes
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self._base_template = {'cluster'    : 'name of the cluster',
                               'compiler'   : 'fortran compiler',
                               'fft_lib'    : 'fft lib used',
                               'blas_lib'   : 'blas lib used',
                               'user_name'  : 'name of the person who compiled and ran the benchmark',
                               'user_email' : 'user_name email',
                               'version'    : 'version of the code',
                               'code'       : 'name of the code',
                               'remarks'    : 'additional remarks'}
        self.fn = 'description'
        self.template = {}
        self.description = {}
        self.complete_template()

    def __hash__(self):
        return hash(frozenset(self.description))

    @abstractmethod
    def complete_template(self):
        """
        method to complete the template for a specific code
        """

    def print_template(self):
        """
        print the description template to file for the user to fill
        """
        f = open(self.fn, 'w')
        f.write(str(self.template))
        f.close()

    def print_to_file(self):
        """
        print the description to file
        """
        f = open(self.fn, 'w')
        f.write(str(self.description))
        f.close()

    def read_from_file(self, file_name=None):
        """
        read the description from file
        :returns True on succes
        """
        if file_name is None:
            file_name = self.fn

        if os.path.isfile(file_name):
            f = open(file_name, 'r')
            self.description = ast.literal_eval(f.read())
            return True
        else:
            return False

    def create_interactively_from_template(self):
        """
        interactively create the description from the template
        :returns True on succes
        """
        return False

    def make(self, file_name='description'):
        """
        main entry point
        make the description
        """
        if self.read_from_file(file_name):
            return True
        elif self.create_interactively_from_template():
            self.print_to_file()
            return True
        else:
            return False


class VaspDescription(BaseDescription):
    """
    descrition for vasp
    """
    def complete_template(self):
        self.template = copy.deepcopy(self._base_template)
        self.template['code'] = 'vasp'
        return True


def get_description(code):
    """
    factory function
    :param code:
    :return:
    """
    desc = {'vasp': VaspDescription()}
    return desc[code]
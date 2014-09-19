from __future__ import print_function, division

__author__ = 'setten'
__version__ = "0.1"
__maintainer__ = "Michiel van Setten"
__email__ = "mjvansetten@gmail.com"
__date__ = "Sept 2014"


"""
Script to setup a set of benchmark calculations
"""


from PyBench.core.descriptions import get_description
from PyBench.core.data import get_data_set

if __name__ == "__main__":
    code = 'vasp'
    desc = get_description(code=code)
    data_set = get_data_set(code=code)
    data_set.gather_data()
    data_set.set_parameter_lists()
    data_set.print_parameter_lists()
    #data_set.insert_in_db()

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
import numpy as np
from abc import ABCMeta, abstractmethod, abstractproperty
from PyBench.core.descriptions import get_description
from pymatgen.io.vaspio.vasp_output import Vasprun
from pymatgen.io.vaspio.vasp_output import Outcar, Incar
from xml.etree.cElementTree import ParseError
from pymongo.errors import OperationFailure
from pymongo import Connection
import pprint
import matplotlib.pyplot as plt

symbol = [' ', 'o', '^', 's', '1']
text = "Description:\n"



def log(a):
    pass


def get_collection(server="marilyn.pcpm.ucl.ac.be", db_name="benchmarks", collection="vasp-5.2", with_gfs=False):
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

    def __init__(self, new=False):
        """
        description will contain the description of the cluster and code version and compilation
        data will contain the actual data
        """
        self.description = get_description(self.code)
        if new:
            if not self.description.read_from_file():
                print('desctipion found, create it from template please:')
                if not self.description.create_interactively_from_template():
                    raise RuntimeError
        try:
            self.col = get_collection(collection=self.code+"-"+self.version)
        except pymongo.errors.OperationFailure:
            print("pymongo operation failure, no DB support")
        self.data = {}
        self.ncpus = []
        self.gh = []
        self.systems = []
        self.data = {}

    @abstractproperty
    def code(self):
        """
        the code for the concrete data set
        """

    @abstractproperty
    def version(self):
        """
        the version of the code
        """

    @abstractmethod
    def gather_data(self):
        """
        read the data from path
        """
        # read the calculation results

    def insert_in_db(self):
        entry = copy.deepcopy(self.description.description)
        entry['desc_hash'] = hash(self.description)
        entry['data'] = self.data
        pprint.pprint(entry)
        for x in self.col.find():
            print('in db:    ', x['desc_hash'])
        #    print(x['fft_lib'])
        #print(self.description)
        #print(self.description.description)
        #print(hash(frozenset(self.description.description)))
        print('this one: ', hash(self.description))
        count = self.col.find({'desc_hash': hash(self.description)}).count()
        if count == 0:
            print('new')
            self.col.insert(entry)
        elif count == 1:
            new_entry = self.col.find_one({'desc_hash': hash(self.description)})
            new_entry.update(entry)
            self.col.save(new_entry)
            print('already there')
        else:
            raise RuntimeError

    def get_from_db(self, dh=None):
        if dh == None:
            """
            no description hash specified: create a list of all gh available and let the user pick one
            """
            data_sets = self.col.find()
            i = 0
            hash_list = []
            for data_set in data_sets:
                print("set %s:" % i)
                hash_list.append(data_set['desc_hash'])
                desc = get_description(self.code)
                desc.from_db_entry(data_set)
                print(desc)
                i += 1
            dh = hash_list[int(raw_input('Which set should be imported?\n'))]
        print(dh)
        entry = self.col.find({'desc_hash': dh})[0]
        #pprint.pprint(entry)
        self.data = entry['data']
        self.description.from_db_entry(entry)
        print(self.description)

    def set_parameter_lists(self):
        for entry in self.data.values():
            if entry["ncpus"] not in self.ncpus:
                self.ncpus.append(entry["ncpus"])
            if entry["generator_hash"] not in self.gh:
                self.gh.append(entry["generator_hash"])
            if entry["system"] not in self.systems:
                self.systems.append(entry["system"])
        self.ncpus.sort()

    def print_parameter_lists(self):
        print(self.ncpus)
        print(self.gh)
        print(self.systems)

    def plot_data(self, mode='speedup'):
        """
        plot the time v.s. ncpu for the current data,
        this method should be used on a single generators data
        """
        plot = plt
        l1 = []
        l2 = []
        timing = '\n\nAbsolute timing / nbands @ ncpus=1:'
        mx, my = 0, 0
        t1 = {}
        y_data = {}
        npars = {}
        for system in self.systems:
            y_data[system] = []
            npars[system] = [0, 0.5, 1]
        for entry in self.data.values():
            s = entry['system']
            if entry['NPAR'] == entry['ncpus']:
                pnp = 1
            elif entry['NPAR'] == 1:
                pnp = 0
            else:
                pnp = 0.5
            t = entry['run_stats']['Total CPU time used (sec)']/entry['nband']
            e = entry['final_energy']
            y_data[s].append((pnp, entry['ncpus'], t, e, ))
            #npars[s].append(entry['NPAR'])
            if entry['ncpus'] == 1:
                t1[entry['system']] = t
        print('t1:', t1)
        for system in sorted(self.systems):
            #npars[system] = sorted(set(npars[system]))
            y_data[system].sort()
            for npar in npars[system]:
                x, y, en = [], [], []
                for d in y_data[system]:
                    if d[0] == npar:
                        x.append(d[1])
                        if mode == 'speedup':
                            y.append(t1[system]/d[2])
                        elif mode == 'abstiming':
                            y.append(d[2])
                        elif mode == 'energies':
                            y.append(d[3] / (float(system[-1]))**3)
                        elif mode == 'efficiency':
                            y.append((t1[system]/d[2])/d[1])
                        en.append(d[3])
                w = "%s@NPAR%s" % (system, npar)
                l1.append(w)
                l2.append(plot.plot(x, y, symbol[int(system[-1])]+'-')[0])
                my = max(my, max(y))
                mx = max(mx, max(x))
            plot.gca().set_color_cycle(None)
            timing += "\n  %s: %s s" % (system, t1[system])
            #energies += "\n  %s: %s s" % (system, t1[system])
        if mode == 'speedup':
            plot.plot([0, my], [0, my], '-')
            plot.ylabel('speedup')
        if mode == 'efficiency':
            plot.ylabel('efficiency')
        elif mode == 'energies':
            plot.ylabel('Total energy (eV)')
        elif mode == 'abstiming':
            plot.ylabel('Total cpu time (s)')

        plot.xlabel('n cpus')

        plot.text(mx+20, 0, text + str(self.description) + timing, fontsize=10)
        plot.subplots_adjust(right=0.60)
        plot.legend(l2, l1,  bbox_to_anchor=(1.7, 1), fontsize=10)

        plot.show()


class VaspData(BaseDataSet):
    """
    object for vasp benchmark data
    """
    @property
    def code(self):
        return 'vasp'

    @property
    def version(self):
        return "5.2"

    def add_data_entry(self, path):
        """
        parse the data found in path and add it to data
        """
        try:
            xml = Vasprun(os.path.join(path, "vasprun.xml"))
            out = Outcar(os.path.join(path, "OUTCAR"))
            if xml.converged or True:
                entry = {
                    'system': path.split('/')[1].split('_par')[0],
                    "NPAR": xml.parameters.get('NPAR'),
                    'nband': xml.parameters.get('NBANDS'),
                    'ncpus': int(out.run_stats['cores']),
                    "final_energy": xml.final_energy,
                    "vasp_version": xml.vasp_version,
                    "generator": xml.generator,
                    "generator_hash": hash(frozenset(xml.generator)),
                    "run_stats": out.run_stats}
                entry_hash = hash((entry['ncpus'], entry['NPAR'], entry['generator_hash'], entry['system']))
                #print(entry)
                self.data.update({str(entry_hash): entry})
                print(entry['ncpus'], entry['NPAR'], entry['generator_hash'], entry['system'])
        except (ParseError, ValueError, IOError):
            try:
                out = Outcar(os.path.join(path, "OUTCAR"))
                inc = Incar(os.path.join(path, "INCAR"))
                entry = {
                    "NPAR": inc.as_dict()['NPAR'],
                    "nband": inc.as_dict()['nband'],
                    'ncpus': int(out.run_stats['cores']),
                    "final_energy": -1,
                    "vasp_version": 'v',
                    "generator": {},
                    "generator_hash": hash(' '),
                    "run_stats": out.run_stats}
                entry_hash = hash((entry['ncpus'], entry['NPAR'], entry['generator_hash'], entry['system']))
                log(entry)
                self.data.update({str(entry_hash): entry})
                print(entry['ncpus'], entry['NPAR'], entry['generator_hash'], entry['system'])
            except (ParseError, ValueError, IOError):
                print('parsing error')
            pass

    def gather_data(self):
        tree = os.walk(".")
        for dirs in tree:
            data_file = os.path.join(dirs[0], 'vasprun.xml')
            if os.path.isfile(data_file):
                print(data_file)
                self.add_data_entry(dirs[0])


def get_data_set(code, new=False):
    """
    factory function
    :param code:
    :return:
    """
    data_sets = {'vasp': VaspData}
    return data_sets[code](new=new)
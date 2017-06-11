#!/usr/bin/env python
# -- coding: utf-8 --

from jsonextended.parsers.base import BasicParser

class CrystalDFTParser(BasicParser):
    """ a class for parsing Crystal DFT Simulation Data

    format:

        meta
        initial
        scf
           step
               <number>        
        optimisation
           step
               <number>
        optimised
    
    Examples
    --------
    
    >>> from jsonextended import utils, parsers
    >>> datapath = utils.get_data_path('crystal_test.data',parsers)
    >>> parser = CrystalDFTParser()
    >>> parser.read_file(datapath)
    >>> sorted(parser.data.keys())
    ['initial', 'meta', 'optimisation', 'optimised', 'scf']

    """
    def _eval_meta_data(self):
        if self._has_sig('date:'):
            self.add_data('start date',' '.join(self._get_fields_after(1)),['meta'])
            return True
        if self._has_sig('input:'):
            self.add_data('input file',' '.join(self._get_fields_after(1)),['meta'])
            return True
        if self._has_sig('resources_used.ncpus ='):
            self.add_data('processors',self._get_fields(3),['meta'],dtype=int) 
            return True           
        if self._has_sig('Job output begins below'):
            self._exit_file_section(1)            

    def _get_geom_data(self):

        if self._has_sig({1:'PRIMITIVE',2:'CELL',7:'VOLUME=',10:'DENSITY'}):
            self.add_data(['volume','density'],self._get_fields([8,11]),
                                 init_keys=self._get_section()+['primitive'],
                                 dtype=float)
            self._skip_lines()
            assert self._has_sig('A B C ALPHA BETA GAMMA')
            self._skip_lines()
            self.add_data(['a','b','c','alpha','beta','gamma'],
                                self._get_fields([1,2,3,4,5,6]),
                                init_keys=self._get_section()+['primitive','lattice_parameters'],
                                dtype=float)
            return True

        if self._has_sig('ATOMS IN THE ASYMMETRIC UNIT'):
            self._skip_lines(3)
            cdict = self._table_todict(['id','assym','atomic_number','label','x/a','y/b','z/c'],
                                [int,self._str_map({'T':True,'F':False}),int,str,float,float,float])
            self.add_data('geometry',cdict,merge=True,
                                init_keys=self._get_section()+['primitive'])
            return True

        if self._has_sig('CRYSTALLOGRAPHIC CELL (VOLUME='):
            self.add_data('volume',self._get_fields(4)[0:-1],
                                 init_keys=self._get_section()+['crystallographic'],
                                 dtype=float)
            self._skip_lines()
            assert self._has_sig('A B C ALPHA BETA GAMMA')
            self._skip_lines()
            self.add_data(['a','b','c','alpha','beta','gamma'],
                                self._get_fields([1,2,3,4,5,6]),
                                 init_keys=self._get_section()+['crystallographic','lattice_parameters'],
                                 dtype=float)
            return True

        if self._has_sig('COORDINATES IN THE CRYSTALLOGRAPHIC CELL'):
            self._skip_lines(3)
            cdict = self._table_todict(['id','assym','atomic_number','label','x/a','y/b','z/c'],
                                [int,self._str_map({'T':True,'F':False}),int,str,float,float,float])
            self.add_data('geometry',cdict,merge=True,
                                 init_keys=self._get_section()+['crystallographic'])
            return True

        if self._has_sig('DIRECT LATTICE VECTORS CARTESIAN COMPONENTS'):
            self._skip_lines(2)
            self.add_data('a',[float(v) for v in self._get_fields([1,2,3])],
                                init_keys=self._get_section()+['crystallographic','lattice_vectors'])
            self._skip_lines(1)
            self.add_data('b',[float(v) for v in self._get_fields([1,2,3])],
                                init_keys=self._get_section()+['crystallographic','lattice_vectors'])
            self._skip_lines(1)
            self.add_data('c',[float(v) for v in self._get_fields([1,2,3])],
                                init_keys=self._get_section()+['crystallographic','lattice_vectors'])
            return True

        if self._has_sig('CARTESIAN COORDINATES - PRIMITIVE CELL'):
            self._skip_lines(4)
            cdict = self._table_todict(['id','atomic_number','label','x','y','z'],
                                    [int,int,str,float,float,float])
            self.add_data('geometry',cdict,merge=True,
                                 init_keys=self._get_section()+['primitive'])
            return True

    def _eval_initial_data(self):

        if self._has_sig('* CRYSTAL14 *'):
            self._enter_file_section('initial',level=1)
            return True

        if not self._in_section('initial'):
            return        
        
        return self._get_geom_data()

    def _eval_scf(self):
        
        if self._has_sig('CRYSTAL - SCF - TYPE OF CALCULATION'):
            self._enter_file_section('scf',level=1)
            ctyp = self._get_fields_after(8,join=True)
            self.add_data('calculation type',ctyp,init_keys=['scf'])
            self._enter_file_section('step',level=2)            
            self._enter_file_section(0,level=3)            
            return True
        if self._has_sig('== SCF ENDED -'):
            self._exit_file_section(1)
            return True
        
        if not self._in_section('scf'):
            return

        if self._has_sig('CHARGE NORMALIZATION FACTOR'):
            step = self._get_section(3)
            self._exit_file_section(3)
            self._enter_file_section(step+1,level=3)
            self.add_data('charge normalisation',self._get_fields(4),
                        init_keys=self._get_section(),dtype=float)
            return True
            
        if self._has_sig('TOTAL ATOMIC CHARGES:'):
            self._skip_lines(1)
            charges = []
            while True:
                data = self._line.split()
                if not data:
                    break
                try: 
                    charges += [float(d) for d in data]
                    self._skip_lines(1)
                except:
                    break
            self.add_data('charge',charges,
                          init_keys=self._get_section())
            return True

        if self._has_sig('SUMMED SPIN DENSITY'):
            self.add_data('spin density',self._get_fields(4),
                        init_keys=self._get_section(),dtype=float)
            return True

        if self._has_sig('TOTAL ATOMIC SPINS'):
            self._skip_lines(1)
            spins = []
            while True:
                data = self._line.split()
                if not data:
                    break
                try: 
                    spins += [float(d) for d in data]
                    self._skip_lines(1)
                except:
                    break
            self.add_data('spin',spins,
                          init_keys=self._get_section())
            return True

        for dname in ['MOQGAD','SHELLX2','MONMO3','NUMDFT','FDIK','PDIG']:
            if self._has_sig(' TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT {} TELAPSE'.format(dname)):
                self.add_data(dname,{'TELAPSE':float(self._get_fields(4)),
                                        'TCPU':float(self._get_fields(6))},
                              init_keys=self._get_section())
                return True

        if self._has_sig({1:'CYC',5:'DETOT'}):
            self.add_data('energy',self._get_fields(4),
                        init_keys=self._get_section(),dtype=float)
            return True
                       
    def _eval_optimisation_data(self):

        if self._has_sig('STARTING GEOMETRY OPTIMIZATION'):
            self._exit_file_section(1)
            self._enter_file_section('optimisation',level=1)
            self._enter_file_section('steps',level=2)
            return True

        if self._has_sig('* OPT END -'):
            self._exit_file_section(1)
            if self._get_fields(5) == 'CONVERGED':
                self.add_data('converged',True,['meta'])
            else:
                self.add_data('converged',False,['meta'])
            self.add_data('energy',self._get_fields(8),
                          ['optimised'],dtype=float)
            return True
        
        if not self._in_section('optimisation'):
            return

        if self._has_sig('COORDINATE AND CELL OPTIMIZATION - POINT'):
            config_number = self._get_fields(7)
            self._enter_file_section(config_number, level=3)
            self.add_data('step',config_number,
                          init_keys=self._get_section(),
                          dtype=int)
            return True
        
        return self._get_geom_data()

        if self._has_sig('TOTAL ENERGY(DFT)(AU)('):
            self._line = self._line.replace('TOTAL ENERGY(DFT)(AU)(','') # ) touches energy value
            self.add_data('energy',self._get_fields(2),
                          init_keys=self._get_section(),
                          dtype=float)
            return True

    def _eval_optimised_data(self):

        if self._has_sig('FINAL OPTIMIZED GEOMETRY'):
            self._enter_file_section('optimised',level=1)
            return True

        if not self._in_section('optimised'):
            return
            
        return self._get_geom_data()
        

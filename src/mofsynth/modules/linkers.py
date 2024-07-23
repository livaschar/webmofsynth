
from dataclasses import dataclass
import os
import re
from . other import copy
from . mof import MOF


@dataclass
class Linkers:
    r"""
    Class for managing linker molecules and their optimization.

    Attributes
    ----------
    job_sh : str
        Default job script file name.
    run_str : str
        Default run string for optimization.
    opt_cycles : int
        Default number of optimization cycles.
    run_str_sp : str
        Default run string for single-point energy calculation.
    job_sh_path : str
        Default path for job script.
    settings_path : str
        Default path for settings file.
    instances : list
        List to store instances of the Linkers class.
    converged : list
        List to store converged linker instances.
    not_converged : list
        List to store not converged linker instances.
    best_opt_energy_dict : dictionary
        Dictionary containing the smile_codes as a key and value is a list of the opt_energy and the opt_path

    Methods
    -------
    change_smiles(smiles)
        Change the SMILES code of a linker instance.

    opt_settings(run_str, opt_cycles, job_sh=None)
        Set optimization settings for all linker instances.

    optimize(rerun=False)
        Optimize the linker structure.

    check_optimization_status(linkers_list)
        Check the optimization status of linker instances.

    read_linker_opt_energies()
        Read the optimization energy for a converged linker instance.

    define_the_best_opt_energies()
        Define the best optimization energy for each SMILES code.
    """
    
    # Initial parameters that can be changed
    job_sh = 'job.sh'
    run_str = 'sbatch job.sh'
    opt_cycles = 1000
    
    run_str_sp =  "bash -l -c 'module load turbomole/7.02; x2t linker.xyz > coord; uff; t2x -c > final.xyz'"
    
    # job_sh_path = os.path.join('/'.join(__file__.split('/')[:-2]),'input_data')
    # settings_path = os.path.join('/'.join(__file__.split('/')[:-2]),'input_data/settings.txt')
    settings_path = os.path.join(os.getcwd(),'input_data/settings.txt')
    job_sh_path = os.path.join(os.getcwd(),'input_data')
    
    
    run_str = ''
    opt_cycles = ''
    job_sh = ''

    instances = []
    converged = []
    not_converged = []
    best_opt_energy_dict = {}

    def __init__(self, smiles_code, mof_name):
        r"""
        Initialize a Linkers instance.

        Parameters
        ----------
        smiles_code : str
            SMILES code of the linker molecule.
        mof_name : str
            Name of the associated MOF.
        """
        Linkers.instances.append(self)

        self.smiles_code = smiles_code
        self.mof_name = mof_name
        self.opt_path = os.path.join(MOF.path_to_linkers_directory, self.smiles_code, self.mof_name)
        self.opt_energy = 0
        self.opt_status = 'not_converged'

        try:
            os.makedirs(self.opt_path, exist_ok = True)
        except:
            return None
    
    # def change_smiles(self, smiles):
    #     """
    #     Change the SMILES code of the linker instance.

    #     Parameters
    #     ----------
    #     smiles : str
    #         New SMILES code.
    #     """        
    #     self.smiles_code = smiles
    #     #self.simple_smile = re.sub(re.compile('[^a-zA-Z0-9]'), '', self.smiles_code)
    #     self.opt_path = os.path.join(MOF.linkers_path, self.simple_smile, self.mof_name)

    @classmethod
    def opt_settings(cls, run_str, opt_cycles, job_sh = None):
        r"""
        Set optimization settings for all linker instances.

        Parameters
        ----------
        run_str : str
            New run string for optimization.
        opt_cycles : int
            New number of optimization cycles.
        job_sh : str, optional
            New job script file name.
        """
        cls.run_str = run_str
        cls.opt_cycles = opt_cycles
        if job_sh != None:
            cls.job_sh = job_sh

    def optimize(self, rerun = False):
        r"""
        Optimize the linker structure.

        Parameters
        ----------
        rerun : bool, optional
            Whether this optimization has runned again.

        Notes
        -----
        This function updates the optimization settings, runs the optimization, and modifies necessary files.
        """
        
        # if os.path.exists(os.path.join(self.opt_path, 'uffconverged')):
        #     return
        
        # Must be before os.chdir(self.opt_path)
        if rerun == False:
            copy(Linkers.job_sh_path, self.opt_path, Linkers.job_sh)
        
        os.chdir(self.opt_path)

        if rerun == False:
            try:
                os.system(Linkers.run_str_sp)
            except Exception as e:
                print(f"An error occurred while running the command for turbomole: {str(e)}")
        
        # MIGHT DELETE
        if rerun == True:
            os.rename(f'linker.xyz', 'linker_original.xyz')
            os.rename(f'final.xyz', 'linker.xyz')

        with open("control", 'r') as f:
            lines = f.readlines()
        words = lines[2].split()
        words[0] = str(self.opt_cycles)
        lines[2] = ' '.join(words) +'\n'
        with open("control",'w') as f:
            f.writelines(lines)

        try:
            os.system(Linkers.run_str)
        except Exception as e:
            print(f"An error occurred while running the command for turbomole: {str(e)}")
        
        os.chdir(MOF.src_dir)

    @classmethod
    def check_optimization_status(cls, linkers_list):
        r"""
        Check the optimization status of linker instances.

        Parameters
        ----------
        linkers_list : list
            List of linker instances.

        Returns
        -------
        Tuple
            A tuple containing lists of converged and not converged linker instances.
        """

        for linker in linkers_list:
            
            if os.path.exists(os.path.join(linker.opt_path, 'uffconverged')):
                cls.converged.append(linker)
                linker.opt_status = 'converged'
        
            elif os.path.exists(os.path.join(linker.opt_path, 'not.uffconverged')):
                cls.not_converged.append(linker)
            
        return cls.converged, cls.not_converged
    
    def read_linker_opt_energies(self):   
        r"""
        Read the optimization energy for a converged linker instance.
        """        
        with open(os.path.join(self.opt_path, 'uffenergy')) as f:
            lines = f.readlines()
        
        self.opt_energy = lines[1].split()[-1]

        return self.opt_energy

    
    @classmethod
    def define_best_opt_energy(cls):

        for instance in Linkers.converged:
            if instance.smiles_code in cls.best_opt_energy_dict:
                if float(instance.opt_energy) < float(cls.best_opt_energy_dict[instance.smiles_code][0]):
                    cls.best_opt_energy_dict[instance.smiles_code] = [instance.opt_energy, instance.opt_path]
            else:
                cls.best_opt_energy_dict[instance.smiles_code] = [instance.opt_energy, instance.opt_path]

        return cls.best_opt_energy_dict


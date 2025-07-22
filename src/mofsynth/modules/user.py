import os

class USER:
    def __init__(self, unique_user):

        self.src_dir = ''
        self.job_sh_path = ''
        self.job_sh_sp = 'job_sp.sh'
        self.job_sh_opt = 'job_opt.sh'
        self.opt_cycles = 1000
        self.synth_path = ''
        
        self.instances = []
        self.fault_supercell = []
        self.fault_fragment = []
        self.path_to_linkers_directory = os.path.join(self.synth_path, '_Linkers_')

        self.new_instances = []
        self.fault_smiles = []
        self.linker_instances = []

        self.converged = []
        self.not_converged = []
        self.output_file_name = 'synth_results'
        self.results_csv_path = os.path.join(self.synth_path, f'{self.output_file_name}.csv')
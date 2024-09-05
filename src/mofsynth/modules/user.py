import os

class USER:
    def __init__(self, unique_user):
        
        self.src_dir = ''
        self.settings_path = ''
        self.job_sh_path = ''
        self.synth_path = './Synth_folder'
        self.path_to_linkers_directory = os.path.join(self.synth_path, '_Linkers_')
        self.output_file_name = 'synth_results'
        self.instances = []
        self.fault_smiles = []
        self.new_instances = []
        self.smiles_id_dict = {}
        self.results_csv_path = os.path.join(self.synth_path, f'{self.output_file_name}.csv')
        
        self.linker_instances = []
        self.converged = []
        self.not_converged = []

        self.job_sh = 'job.sh'
        self.run_str = 'sbatch job.sh'
        self.opt_cycles = 1000

        # MOF CLASS
        self.src_dir = ''
        self.settings_path = ''
        self.job_sh_path = ''

        self.path_to_linkers_directory = os.path.join(self.synth_path, '_Linkers_')
        self.results_txt_path = os.path.join(self.synth_path, f'{self.output_file_name}.txt')
        self.results_xlsx_path = os.path.join(self.synth_path, f'{self.output_file_name}.xlsx')
        self.results_csv_path = os.path.join(self.synth_path, f'{self.output_file_name}.csv')
        self.run_str_sp = "bash -l -c 'module load turbomole/7.02; x2t linker.xyz > coord; uff; t2x -c > final.xyz'"
        
        self.instances = []
        self.fault_supercell = []
        self.fault_fragment = []
        self.fault_smiles = []
        self.smiles_id_dict = {}
        self.new_instances = []
        self.already_runned = []

        # LINKER CLASS
        self.job_sh = 'job.sh'
        self.run_str = 'sbatch job.sh'
        self.opt_cycles = 1000
        self.run_str_sp =  "bash -l -c 'module load turbomole/7.02; x2t linker.xyz > coord; uff; t2x -c > final.xyz'"
        self.settings_path = os.path.join(os.getcwd(),'input_data/settings.txt')
        self.run_str = ''
        self.opt_cycles = ''
        self.job_sh = ''
        self.instances = []
        self.converged = []
        self.not_converged = []
        self.best_opt_energy_dict = {}
# This file is part of MOF-Synth.
# Copyright (C) 2023 Charalampos G. Livas

# MOF-Synth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import pickle
from . modules.mof import MOF
from . modules.linkers import Linkers
from . modules.other import (copy, settings_from_file,
                             user_settings, load_objects,
                             write_txt_results, write_xlsx_results, write_csv_results,print_energy_ranking)

def main(directory, function, supercell_limit):
    r"""
    Acts as a dispatcher, directing the program to execute the specified function.

    Parameters
    ----------
    directory : str
        The path to the directory containing CIF files.
    function : str
        Name of the function to run. Supported values: 'main_run', 'check_opt', 'export_results'.
    supercell_limit: int
        The maximum length for each edge of the unit cell in Angstroms.

    Raises
    ------
    ValueError
        If an unsupported function name is provided.


    Supported Functions:
    - 'main_run': Executes the main_run function reading files from the given directory
    and the supercell limit
    - 'check_opt': Executes the check_opt function that checks
    which optimization runs are converged.
    - 'export_results': Executes the export_results function and
    creates files with the results.
    """
    if function == 'main_run':
        main_run(directory, supercell_limit)
    elif function == 'check_opt':
        check_opt()
    elif function == 'export_results':
        export_results()
    else:
        print('Wrong function. Aborting...')
        sys.exit()


def main_run(directory, supercell_limit, EXECUTION_FOLDER):
    r"""
    Perform the synthesizability evaluation for MOFs in the specified directory.

    Parameters
    ----------
    directory : str
        The directory containing CIF files for synthesizability evaluation.

    Returns
    -------
    Tuple
        A tuple containing instances of MOF and Linkers classes, and lists of MOFs with
        faults in supercell creation and fragmentation procedures.
    """

    # Create the working directory
    os.makedirs("Synth_folder", exist_ok=True)

    # If settings file exists, read settings from there else ask for user input
    Linkers.settings_path = os.path.join(EXECUTION_FOLDER, 'input_data/settings.txt')
    Linkers.job_sh_path = os.path.join(EXECUTION_FOLDER, 'input_data')
    MOF.src_dir = EXECUTION_FOLDER

    if os.path.exists(Linkers.settings_path):
        run_str, job_sh, opt_cycles = settings_from_file(Linkers.settings_path)
    else:
        run_str, job_sh, opt_cycles = user_settings()

    Linkers.opt_settings(run_str, opt_cycles, job_sh)

    
    print(f'  \033[1;32m\nSTART OF SYNTHESIZABILITY EVALUATION\033[m')

    # A list of cifs from the user soecified directory
    user_dir = os.path.join(f"./{directory}")
    cifs = [item for item in os.listdir(user_dir) if item.endswith(".cif")]

    if cifs == []:
        print(f"\nWARNING: No cif was found in: {user_dir}. Please check run.py\n")
        return 2

    # Start procedure for each cif
    for _, cif in enumerate(cifs):

        print(f'\n - \033[1;34mMOF under study: {cif[:-4]}\033[m -')

        # Initialize the mof name as an object of MOF class
        mof = MOF(cif[:-4])

        # Check if its already initialized a MOF object. Sometimes the code may break in the middle of a run.
        # This serves as a quick way to ignore already analyzed instances.
        if os.path.exists(os.path.join(mof.sp_path, "final.xyz")):
            supercell_check = True
        else:
            # Copy .cif and job.sh in the mof directory
            copy(user_dir, mof.init_path, f"{mof.name}.cif")
            copy(Linkers.job_sh_path, mof.sp_path, job_sh)

            # Create supercell, do the fragmentation, extract one linker,
            # calculate single point energy
            supercell_check, _ = mof.create_supercell(supercell_limit)        
            mof.fragmentation()
            mof.obabel()
            mof.single_point()

        # Check if supercell procedure runned correctly
        if supercell_check is False:
            MOF.fault_supercell.append(mof.name)
            MOF.instances.pop()

        # Check if fragmentation procedure found indeed a linker
        fragm_check = mof.check_fragmentation()
        if fragm_check is False:
            MOF.fault_fragment.append(mof.name)
            MOF.instances.pop()

    # Find the unique linkers from the whole set of MOFs
    smiles_id_dict = MOF.find_unique_linkers(EXECUTION_FOLDER)
    
    # Proceed to the optimization procedure of every linker
    for linker in Linkers.instances:
        print(f'\n - \033[1;34mLinker under optimization study: {linker.smiles_code}, of {linker.mof_name}\033[m -')
        linker.optimize(rerun = False)
    
    # Right instances of MOF class
    with open('cifs.pkl', 'wb') as file:
        pickle.dump(MOF.instances, file)
    
    # Right instances of Linkers class
    with open('linkers.pkl', 'wb') as file:
        pickle.dump(Linkers.instances, file)
    
    if MOF.fault_fragment != []:
        with open('fault_fragmentation.txt', 'w') as file:
            for mof_name in MOF.fault_fragment:
                file.write(f'{mof_name}\n')
    
    if MOF.fault_smiles != []:
        with open('fault_smiles.txt', 'w') as file:
            for mof_name in MOF.fault_smiles:
                file.write(f'{mof_name}\n')
    
    with open('smiles_id_dictionary.txt', 'w') as file:
        for key, value in smiles_id_dict.items():
            file.write(f'{key} : {value}\n')

    return 1
    return MOF.instances, Linkers.instances, MOF.fault_fragment, MOF.fault_smiles

def check_opt(EXECUTION_FOLDER, len_files):
    r"""
    Check the optimization status of linker molecules.

    Returns
    -------
    Tuple
        A tuple containing lists of converged and not converged linker instances.
    """
    Linkers.settings_path = os.path.join(EXECUTION_FOLDER, 'input_data/settings.txt')
    Linkers.job_sh_path = os.path.join(EXECUTION_FOLDER, 'input_data')
    MOF.src_dir = EXECUTION_FOLDER
    

    os.chdir(EXECUTION_FOLDER)
    
    _, linkers, _= load_objects(EXECUTION_FOLDER)

    converged, not_converged = Linkers.check_optimization_status(linkers)
    
    # with open('converged.txt', 'w') as f:
    #     for instance in converged:
    #         f.write(f"{instance.smiles_code} {instance.mof_name}\n")
        
    # with open('not_converged.txt', 'w') as f:
    #     for instance in not_converged:
    #         f.write(f"{instance.smiles_code} {instance.mof_name}\n")
    
    if len(converged) + len(not_converged) == len_files:
        return converged, True
    else:
        return [], False
   
def export_results(EXECUTION_FOLDER, compare = False):
    from . modules.other import load_objects
    import pandas as pd
    
    Linkers.settings_path = os.path.join(EXECUTION_FOLDER, 'input_data/settings.txt')
    Linkers.job_sh_path = os.path.join(EXECUTION_FOLDER, 'input_data')
    MOF.src_dir = EXECUTION_FOLDER

    os.chdir(EXECUTION_FOLDER)
    
    cifs, linkers, id_smiles_dict = load_objects(EXECUTION_FOLDER)
   
    Linkers.check_optimization_status(linkers)

    for linker in Linkers.converged:
        linker.read_linker_opt_energies()

    # Best opt for each smiles code. {smile code as keys and value [opt energy, opt_path]}
    best_opt_energy_dict = Linkers.define_best_opt_energy()
    
    file_path = os.path.join(EXECUTION_FOLDER, 'input_data/databases.xlsx')
    df = pd.read_excel(file_path)

    results_list = MOF.analyse(cifs, linkers, best_opt_energy_dict, id_smiles_dict, df)

    write_csv_results(results_list, os.path.join(EXECUTION_FOLDER, MOF.results_csv_path))
    
    return 1

def compare_to_others(EXECUTION_FOLDER, cifs):
    print('YEAH')
    import pandas as pd
    from scipy.stats import percentileofscore
    
    # Load the Excel file
    file_path = os.path.join(EXECUTION_FOLDER, 'input_data/databases.xlsx')
    df = pd.read_excel(file_path)
    
    for mof in cifs:
        # Create a new DataFrame row
        example_row = pd.DataFrame({
           'NAME': [mof.name],
           'ENERGY_(OPT-SP)_[kcal/mol]': [mof.de*627.51],
           'RMSD_[A]': [mof.rmsd]
           })
        df = pd.concat([df, example_row], ignore_index=True)
    
        # Sort by ENERGY_(OPT-SP)_[kcal/mol]
        df_sorted_energy = df.sort_values(by='ENERGY_(OPT-SP)_[kcal/mol]', ascending=True).reset_index(drop=True)
        df_sorted_energy['Energy_Rank'] = df_sorted_energy.index + 1
        
        # Sort by RMSD_[A]
        df_sorted_rmsd = df.sort_values(by='RMSD_[A]', ascending=True).reset_index(drop=True)
        df_sorted_rmsd['RMSD_Rank'] = df_sorted_rmsd.index + 1
        
        # Find the rank of the example
        example_energy_rank = df_sorted_energy[df_sorted_energy['NAME'] == cifs[0].name]['Energy_Rank'].values[0]
        example_rmsd_rank = df_sorted_rmsd[df_sorted_rmsd['NAME'] == cifs[0].name]['RMSD_Rank'].values[0]
        
        # Calculate percentile for energy
        energy_scores = df['ENERGY_(OPT-SP)_[kcal/mol]']
        example_energy_percentile = percentileofscore(energy_scores, cifs[0].de*627.51, kind='weak')
        
        # Calculate percentile for RMSD
        rmsd_scores = df['RMSD_[A]']
        example_rmsd_percentile = percentileofscore(rmsd_scores, cifs[0].rmsd, kind='weak')
        
        print(f'\nIt belongs to top {example_energy_percentile} %')
        print('Rank rmsd:', example_rmsd_percentile)

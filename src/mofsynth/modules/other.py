import shutil
import pickle
import os
import openpyxl
import numpy as np
import csv


def load_objects(path):
    
    id_smiles_dict = {}
    cifs_pkl = os.path.join(path, 'cifs.pkl')
    linkers_pkl = os.path.join(path, 'linkers.pkl')
    smiles_id_dictionary = os.path.join(path, 'smiles_id_dictionary.txt')

    with open(cifs_pkl, 'rb') as file:
        cifs = pickle.load(file)
    with open(linkers_pkl, 'rb') as file:
        linkers = pickle.load(file)
    
    with open(smiles_id_dictionary, 'r') as file:
        lines = file.readlines()
        for line in lines:
            id_smiles_dict[line.split()[-1]] = line.split()[0]
    
    return cifs, linkers, id_smiles_dict


def copy(path1, path2, file_1, file_2 = None):
    
    if file_2 is None:
        file_2 = file_1
    
    shutil.copy(os.path.join(path1, file_1), os.path.join(path2, file_2))

    return

def settings_from_file(filepath):
        
    with open(filepath) as f:
        lines = f.readlines()
    
    run_str = ' '.join([i for i in lines[1].split()])
    try:
        job_sh = lines[3].split()[0]
    except:
        pass
    cycles = lines[5].split()[0]

    return run_str, job_sh, cycles

def user_settings():
    run_str = input("\nProvide the string with which the optimization program runs: ")

    question = input("\nIs there a file in MOFSynth/Files folder that is necessary to run your optimization programm? [y/n]: ")
    if question == 'y':
        job_sh = input("\nSpecify the file name: ")
    else:
        job_sh = None
    
    cycles = input("\nPlease specify the number of optimization cycles (default = 1000): ")
    try:
        cycles = int(cycles)
    except:
        print("Not a valid value provided. Default value will be used")
        cycles = '1000'
    
    return run_str, job_sh, cycles

def write_txt_results(results_list, results_txt_path):

    with open(results_txt_path, "w") as f:
        f.write('{:<50} {:<37} {:<37} {:<30} {:<10} {:<60} {:<30} {:<30} {:<10} \n'.format("NAME", "ENERGY_(OPT-SP)_[au]", "ENERGY_(OPT-SP)_[kcal/mol]", "RMSD_[A]", "LINKER_(CODE)", "LINKER_(SMILES)", "Linker_SinglePointEnergy_[au]", "Linker_OptEnergy_[au]", 'Opt_status'))
        for i in results_list:
            # if np.isnan(j for j in i):
            #     f.write(f"{i[0]:<50} {i[1]:<37} {i[2]:<37} {i[3]:<30} {i[4]:<10} {i[5]:<60} {i[6]:<30} {i[7]:<30} {i[8]:<10}\n") 
            # else:
            f.write(f"{i[0]:<50} {i[1]:<37.3f} {i[2]:<37.3f} {i[3]:<30.3f} {i[4]:<10} {i[5]:<60} {i[6]:<30.3f} {i[7]:<30.3f} {i[8]:<10}\n")

def write_xlsx_results(results_list, results_xlsx_path):
    
    # Create a new workbook and select the active sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    # Write headers
    # headers = ["NAME", "ENERGY_(OPT-SP)_[au]", "ENERGY_(OPT-SP)_[kcal/mol]", "RMSD_[A]", "LINKER_(CODE)", "LINKER_(SMILES)", "Linker_SinglePointEnergy_[au]", "Linker_OptEnergy_[au]", "Opt_status"]
    headers = ["NAME", "ENERGY_(OPT-SP)_[kcal/mol]", "RMSD_[A]", "LINKER_(SMILES)", "Linker_SinglePointEnergy_[au]", "Linker_OptEnergy_[au]", "Opt_status"]
    sheet.append(headers)

    # Write results
    for result_row in results_list:
        row_data = [result_row[0], result_row[2], result_row[3], result_row[5], result_row[6], result_row[7], result_row[8]]
        sheet.append(row_data)
        # sheet.append(result_row)

    # Save the workbook to the specified Excel file
    workbook.save(results_xlsx_path)

def write_csv_results(results_list, results_csv_path):
    
    headers = ["Ranking", "Filename", "Energy Percentile Rank (%)", "RMSD Percentile Rank (%)", "Energy (kcal/mol)", "RMSD (A)", "Smiles", "Single Point Energy (au)", "Optimized Energy (au)", "Status"]    
    
    sorted_results = sorted(results_list, key=lambda x: -float(x[2]))
    
    # Open the CSV file for writing
    with open(results_csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write headers
        writer.writerow(headers)
        
        # Write results
        for index, result_row in enumerate(sorted_results):
            row_data = [index+1, result_row[0], result_row[1], result_row[2], result_row[4], result_row[5], result_row[7], result_row[8], result_row[9], result_row[10]]
            writer.writerow(row_data)
            # writer.writerow(result_row)

def print_energy_ranking(results_list):
    # Sort results_list based on the energy value (result_row[2])
    sorted_results = sorted(results_list, key=lambda x: float(x[2]))  # Assuming result_row[2] is the energy value

    # Print or process the sorted results
    for rank, result_row in enumerate(sorted_results, start=1):
        print(f"Rank {rank}: {result_row[0]} - Energy: {result_row[2]} kcal/mol")


def delete_files_except(folder_path, exceptions):
    """
    Delete all files in the folder except those in the exceptions list.
    
    Parameters:
    - folder_path (str): The path to the folder.
    - exceptions (list): List of filenames to be excluded from deletion.
    """
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and filename not in exceptions:
                os.remove(file_path)
                print(f"Deleted: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


def move_and_delete_contents(source_path, destination_path):
    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    # Get a list of all files in the source directory
    files = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))]

    # Move each file to the destination directory
    for file in files:
        source_file = os.path.join(source_path, file)
        destination_file = os.path.join(destination_path, file)
        shutil.move(source_file, destination_file)

    # Now, delete the original contents of folder1
    shutil.rmtree(source_path)
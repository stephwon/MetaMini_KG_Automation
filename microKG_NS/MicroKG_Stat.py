# Install required packages
import os
import argparse
import pandas as pd
import sys 
import csv

# Argument parser setup
parser = argparse.ArgumentParser(description="Process microbiome data files.")
parser.add_argument('--input', required=True, help="Path to the input TSV file.")
parser.add_argument('--stat_dir', required=False, default="syn_stat", help="Directory to save statistic files.")
parser.add_argument('--result_file', required=False, default="data_syn/Microbiome_KG_nodes_syn_v0.2.1.tsv", help="Path to the result file.")
args = parser.parse_args()

# Input and output file paths
input_file = os.path.abspath(args.input)
stat_dir_path = os.path.abspath(args.stat_dir)
result_file_path = os.path.abspath(args.result_file)


# Ensure stat_dir exists
os.makedirs(stat_dir_path, exist_ok=True)


# Function to count rows in a CSV file
def row_count(file_path):
    try:
        df = pd.read_csv(file_path)
        return df.shape[0]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

# Detailed Lookup Statistics
def analyze_lookup_performance(data, stat_dir):
    total_rows = len(data)

    failed_curies_path = os.path.join(stat_dir, 'failed_curies.csv')
    failed_both_path = os.path.join(stat_dir, 'failed_both.csv')
    
    # Load failure files and count rows
    if os.path.exists(failed_curies_path):
        id_lookup_fails = row_count(failed_curies_path)
    else:
        print(f"Warning: {failed_curies_path} not found. Assuming 0 ID lookup failures.")
        id_lookup_fails = 0

    if os.path.exists(failed_both_path):
        final_fails = row_count(failed_both_path)
    else:
        print(f"Warning: {failed_both_path} not found. Assuming 0 final failures.")
        final_fails = 0
    
    # Calculation
    id_lookup_success = total_rows - id_lookup_fails
    name_lookup_success = id_lookup_fails - final_fails

    # Prepare the performance analysis summary
    analysis = (
        "Node Synonymization Performance Analysis:\n"
        f"1. Total Rows: {total_rows}\n"
        "\n2. Step 1 (ID Lookup):\n"
        f"   * Successful: {id_lookup_success} ({id_lookup_success/total_rows*100:.2f}%)\n"
        f"   * Failed: {id_lookup_fails} ({id_lookup_fails/total_rows*100:.2f}%)\n"
        "\n3. Step 2 (Name Lookup for Step 1 Fails):\n"
        f"   * Total attempted lookups: {id_lookup_fails}\n"
        f"   * Successful: {name_lookup_success}\n"
        f"   * Failed: {final_fails} ({final_fails/total_rows*100:.2f}%)\n"
        "\nSummary:\n"
        f"* ID Lookup Success: {id_lookup_success}\n"
        f"* Name Lookup Success: {name_lookup_success}\n"
        f"* Total Success: {id_lookup_success + name_lookup_success} ({(id_lookup_success + name_lookup_success)/total_rows*100:.2f}%)\n"
        f"* Final Failures: {final_fails} ({final_fails/total_rows*100:.2f}%)\n"
    )

    # Print the analysis to the console
    print(analysis)

    # Save the analysis to a text file
    analysis_file_path = os.path.join(stat_dir, "NS_performance_summary.txt")
    with open(analysis_file_path, "w") as file:
        file.write(analysis)
    
    print(f"Performance summary saved to: {analysis_file_path}")

### NS Result Statistic ###

def process_microbiome_data(input_file, result_file):
    try:
        data = pd.read_csv(input_file, sep='\t')
    except FileNotFoundError:
        print(f"Input file not found: {input_file}")
        return

    # Analyze lookup performance
    analyze_lookup_performance(data, stat_dir_path)
    
    try:
        result_data = pd.read_csv(result_file, sep='\t')
    except FileNotFoundError:
        print(f"Result file not found: {result_file}")
        return
    
    # Identify erroneous or missing names
    wrong_name = result_data[result_data['name'].str.isnumeric()]
    no_name = result_data[result_data['name'] == '\\']

    # Save wrong_name and no_name to CSV files in the stat_dir
    wrong_name_path = os.path.join(stat_dir_path, 'wrong_name.csv')
    no_name_path = os.path.join(stat_dir_path, 'no_name.csv')

    wrong_name.to_csv(wrong_name_path, index=False)
    no_name.to_csv(no_name_path, index=False)

    print()
    print()
    print(f"Saved wrong_name to: {wrong_name_path}")
    print(f"Saved no_name to: {no_name_path}")

    # Find entries where MicroKG `name`  and `id` do not map via NS. 
    # We approach this by filtering rows where 'id' does not match 'c_id'
    filtered_curie = result_data[result_data['id'] != result_data['c_id']] # Curie means ID
    filtered_name = result_data[result_data['name'] != result_data['c_name']]


    # Save filtered_curie (ID) and filtered_name to CSV files in the stat_dir
    filtered_curie_path = os.path.join(stat_dir_path, 'curie_not_mapping.csv')
    filtered_name_path = os.path.join(stat_dir_path, 'name_not_mapping.csv')

    filtered_curie.to_csv(filtered_curie_path, index=False)
    filtered_name.to_csv(filtered_name_path, index=False)

    print()
    print()
    print(f"Filtered curie mismatches saved to: {filtered_curie_path}")
    print(f"Filtered name mismatches saved to: {filtered_name_path}")

# Execute the main function
if __name__ == "__main__":
    process_microbiome_data(input_file, result_file_path)


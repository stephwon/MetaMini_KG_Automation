import os
import sys
import argparse
import pandas as pd
import logging
from node_synonymizer import NodeSynonymizer

def setup_logger():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process failed synonyms using RTX Node Synonymizer.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input TSV file")
    parser.add_argument("--output", type=str, required=True, help="Directory to save the output files")
    parser.add_argument("--syn_db", type=str, required=True, help="Path to RTX Node Synonymizer SQLite database")
    return parser.parse_args()

def load_data(file_path):
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        sys.exit(1)
    return pd.read_csv(file_path, sep='\t')

def initialize_synonymizer(db_path):
    return NodeSynonymizer(sqlite_file_name=db_path)

def process_synonyms(data, synonymizer):
    data['c_id'] = None
    data['c_name'] = None
    
    failed_curie, failed_both, total_success, errors = [], [], [], []
    
    for index, row in data.iterrows():
        try:
            curie, name = row['ID'], row['Name']
            curie_output = synonymizer.get_canonical_curies(curies=[curie]).get(curie, None)
            
            if curie_output:
                data.at[index, 'c_id'] = curie_output.get('preferred_curie', curie)
                data.at[index, 'c_name'] = curie_output.get('preferred_name', name)
                total_success.append({'id': curie, 'name': name, 'category': row.get('category', 'unknown')})
            else:
                failed_curie.append({'id': curie, 'category': row.get('category', 'unknown')})
                name_output = synonymizer.get_canonical_curies(names=[name]).get(name, None)
                
                if name_output:
                    data.at[index, 'c_id'] = name_output.get('preferred_curie', curie)
                    data.at[index, 'c_name'] = name_output.get('preferred_name', name)
                    total_success.append({'id': curie, 'name': name, 'category': row.get('category', 'unknown')})
                else:
                    failed_both.append({'id': curie, 'name': name, 'category': row.get('category', 'unknown')})
        except Exception as e:
            errors.append({'index': index, 'id': curie, 'name': name, 'error': str(e)})
            data.at[index, 'c_id'], data.at[index, 'c_name'] = curie, name
    
    return data, failed_curie, failed_both, total_success, errors

def save_results(output_dir, base_name, data, failed_curie, failed_both, total_success):
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"{base_name}_processed.tsv")
    data.to_csv(output_file, sep='\t', index=False)
    logging.info(f"Processed data saved at: {output_file}")
    
    failure_dir = os.path.join(output_dir, "failure_logs")
    os.makedirs(failure_dir, exist_ok=True)
    
    if failed_curie:
        pd.DataFrame(failed_curie).to_csv(os.path.join(failure_dir, 'failed_curies2.csv'), index=False)
    if failed_both:
        pd.DataFrame(failed_both).to_csv(os.path.join(failure_dir, 'failed_both2.csv'), index=False)
    if total_success:
        pd.DataFrame(total_success).to_csv(os.path.join(failure_dir, 'total_success2.csv'), index=False)

def main():
    setup_logger()
    args = parse_arguments()
    
    logging.info("Loading input data...")
    data = load_data(args.input)
    
    logging.info("Initializing Node Synonymizer...")
    synonymizer = initialize_synonymizer(args.syn_db)
    
    logging.info("Processing synonyms...")
    data, failed_curie, failed_both, total_success, errors = process_synonyms(data, synonymizer)
    
    logging.info("Saving results...")
    save_results(args.output, "failed_both_syn", data, failed_curie, failed_both, total_success)
    
    if errors:
        logging.warning(f"Errors encountered in {len(errors)} records. Check logs for details.")
    logging.info("Processing complete.")

if __name__ == "__main__":
    main()

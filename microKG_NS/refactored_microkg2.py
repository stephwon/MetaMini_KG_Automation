import os
import pandas as pd
import sys
import logging
import argparse
from node_synonymizer import NodeSynonymizer

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_data(file_path):
    """Loads the microbiome knowledge graph data."""
    try:
        return pd.read_csv(file_path, sep='\t')
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        sys.exit(1)

def initialize_synonymizer(sql_path):
    """Initializes the NodeSynonymizer."""
    return NodeSynonymizer(sqlite_file_name=sql_path)

def synonymize_nodes(data, synonymizer):
    """Processes each row and updates `c_id` (canonical ID) and `c_name` (canonical name) columns."""
    data['c_id'], data['c_name'] = pd.NA, pd.NA
    
    failed_curie, failed_both, errors, passed_lookups = [], [], [], []
    
    for index, row in data.iterrows():
        try:
            curie, name = row['id'], row['name']
            category = row.get('category', 'unknown')  # Default to 'unknown' if missing
            
            # First try CURIE lookup
            result = synonymizer.get_canonical_curies(curies=[curie])
            if result and curie in result:
                curie_output = result[curie]
                
                data.at[index, 'c_id'] = curie_output.get('preferred_curie', curie)
                data.at[index, 'c_name'] = curie_output.get('preferred_name', name)
        
                # It logs MicroKG informations that passed mapping
                passed_lookups.append({'id': curie, 'name': name, 'category': category})
                continue # Move to the next row if found
            
            failed_curie.append({'id': curie, 'name': name, 'category': category})
                
            # Try looking up by name if CURIE lookup failed
            result = synonymizer.get_canonical_curies(names=[name])
            if result and name in result:
                name_output = result[name]
                
                data.at[index, 'c_id'] = name_output.get('preferred_curie', curie)
                data.at[index, 'c_name'] = name_output.get('preferred_name', name)
                
                passed_lookups.append({'id': curie, 'name': name, 'category': category})
            else:
                failed_both.append({'id': curie, 'name': name, 'category': category})
                
        except Exception as e:
            errors.append({'index': index, 'id': curie, 'name': name, 'category': category})
            logging.error(f"Error processing row {index}: {e}")
            # Fall back to input values
            data.at[index, 'c_id'] = curie
            data.at[index, 'c_name'] = name
            
    return data, failed_curie, failed_both, errors, passed_lookups

def save_results(syn_stat_dir, failed_curie, failed_both, passed_lookups):
    """Saves processed results to CSV files."""
    pd.DataFrame(failed_curie).to_csv(os.path.join(syn_stat_dir, "failed_curies.csv"), index=False)
    pd.DataFrame(failed_both).to_csv(os.path.join(syn_stat_dir, "failed_both.csv"), index=False)
    pd.DataFrame(passed_lookups).to_csv(os.path.join(syn_stat_dir, "total_success.csv"), index=False)

def main():
    parser = argparse.ArgumentParser(description="Microbiome Knowledge Graph Synonymizer")
    parser.add_argument("--input", required=True, help="Path to input TSV file")
    parser.add_argument("--syn_db", required=True, help="Path to SQLite synonym database")
    parser.add_argument("--output", required=True, help="Path to save output TSV file")
    parser.add_argument("--syn_stat_dir", required=True, help="Path to save syn_stat files")
    
    args = parser.parse_args()
    
    logging.info("Loading input data...")
    data = load_data(args.input)
    
    logging.info("Initializing synonymizer...")
    synonymizer = initialize_synonymizer(args.syn_db)
    
    logging.info("Processing synonyms...")
    updated_data, failed_curie, failed_both, passed_lookups = synonymize_nodes(data, synonymizer)
    
    logging.info("Saving output data...")
    updated_data.to_csv(args.output, sep='\t', index=False)
    
    logging.info("Saving syn_stat results...")
    save_results(args.syn_stat_dir, failed_curie, failed_both, passed_lookups)
    
    logging.info("Processing complete!")
    
if __name__ == "__main__":
    main()
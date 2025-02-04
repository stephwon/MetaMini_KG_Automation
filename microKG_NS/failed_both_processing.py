import os
import time
import pandas as pd
import requests
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def parse_args():
    """
    Parse command-line arguments for input and output file paths.
    """
    parser = argparse.ArgumentParser(
        description="Process gene file with annotations using NCBI's E-utilities."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="syn_stat/failed_both.csv",
        help="Path to the input CSV file (default: syn_stat/failed_both.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="syn_stat/processed_failed_both.tsv",
        help="Path to the output TSV file (default: syn_stat/processed_failed_both.tsv)"
    )
    return parser.parse_args()


def find_file(filename, search_dir="."):
    for root, dirs, files in os.walk(search_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None


def process_dataframe(df):
    # Step 1: Create a new column, `ID`, to store processed MicroKG `id`
    data['ID'] = data['id'].apply(
        lambda x: x.replace('EC:', 'KEGG.ENZYME:') if isinstance(x, str) and x.startswith('EC:') else x
    )

    # Step 2 & 3: Create a new column for the modified `name`
    def modify_name(row):
        if isinstance(row['id'], str) and row['id'].startswith('NCBITaxon:'):
            if isinstance(row['name'], str):
                if 'CAG:' in row['name']:
                    return row['name'].split('CAG:')[0].strip()
                words = row['name'].split()
                if len(words) < 3 and 'sp.' in words:
                    return ' '.join(words[:words.index('sp.') + 1])
                elif len(words) >= 3 and ('bacterium' in words or 'sp.' in words):
                    for keyword in ['bacterium', 'sp.']:
                        if keyword in words:
                            return ' '.join(words[:words.index(keyword) + 1])
        return row['name']

    df['Name'] = df.apply(modify_name, axis=1) # This is where modified name will be stored
    return df


def fetch_gene_description_json(gene_id):
    """
    Retrieve the gene description from NCBI using the esummary endpoint.
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "gene", "id": gene_id, "retmode": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "result" in data and gene_id in data["result"]:
            return data["result"][gene_id].get("description", "No description available")
        else:
            return "Gene ID not found in response."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching description for gene ID {gene_id}: {e}")
        logging.error(f"Request URL: {response.url if 'response' in locals() else f'{url}?{params}'}")
        if 'response' in locals():
            logging.error(f"Response content: {response.content.decode()}")
        return None


def update_gene_descriptions(df):
    """
    Update the 'Name' column in the dataframe with correct gene descriptions for rows where 'id'

    """
    for index, row in df.iterrows():
        if isinstance(row['id'], str) and row['id'].startswith('NCBIGene:'):
            gene_id = row['id'].split(':')[-1]
            description = fetch_gene_description_json(gene_id)
            if description:
                df.at[index, 'Name'] = description
            time.sleep(0.5)  # Delay to respect API rate limits
    return df


def main():
    args = parse_args()
    input_path = args.input
    output_path = args.output

    # Check if the input file exists and is not empty
    if not os.path.exists(input_path):
        logging.error(f"Input file '{input_path}' does not exist.")
        return

    if os.path.getsize(input_path) == 0:
        logging.error(f"Input file '{input_path}' is empty.")
        return

    logging.info(f"Input file found and not empty: {input_path}")

    # Load and process the data
    try:
        df = pd.read_csv(input_path, sep=',')
    except Exception as e:
        logging.error(f"Failed to read '{input_path}': {e}")
        return

    processed_data = process_dataframe(df)
    processed_data = update_gene_descriptions(processed_data)

    # Ensure the output directory exists and save the processed file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    processed_data.to_csv(output_path, index=False, sep='\t')
    logging.info(f"Cleaned data saved to {output_path}")


if __name__ == "__main__":
    main()

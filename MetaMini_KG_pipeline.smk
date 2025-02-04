# Snake Make
## Import Config Files
configfile: "./config.yml"

## Import Python libraries
import os, sys
import subprocess

## Define Global Variables
ROOT_PATH = os.getcwd() # /scratch1/sjw6257; base working directory
DATA_PATH = os.path.join(ROOT_PATH, 'data')
MICRO_DATA_PATH = os.path.join(DATA_PATH, 'microbiomeKG_data') # microbiomeKG_data/Microbiome_KG_nodes_v0.2.1.tsv; directory where MicroKG is located

SCRIPT_PATH = os.path.join(ROOT_PATH, 'microKG_NS') # microKG_NS is where all the scripts are located
STAT_PATH = os.path.join(ROOT_PATH, 'syn_stat') # This is where stats are located (round 1 and 2)
DATA_SYN_DIR = os.path.join(ROOT_PATH, "data_syn") # This is where synonymized data are located

MICROBIOME_KG_VERSION = config['KG_VARIABLES']['MICROBIOME_KG_VERSION'] # modify config file to latest version
FILENAME = f"Microbiome_KG_nodes_{MICROBIOME_KG_VERSION}.tsv"
NODE_FILE_PATH = os.path.join(MICRO_DATA_PATH, FILENAME) # Full path to the node file

MICROBIOME_KG_DOWNLOAD_URL = "https://db.systemsbiology.net/gestalt/KG/"
NODE_SYN_DB = config['KG_VARIABLES']['NODE_SYN_DIR']

FAILED_BOTH_INPUT = os.path.join(STAT_PATH, "failed_both.csv")
FAILED_BOTH_OUTPUT = os.path.join(STAT_PATH, "processed_failed_both.tsv")
FAILED_BOTH_SCRIPT = os.path.join(SCRIPT_PATH, "failed_both_processing.py")


## Create Required Folders
for folder in [
    os.path.join(ROOT_PATH, "data_syn"),
    os.path.join(ROOT_PATH, "syn_stat"),
    os.path.join(STAT_PATH, "syn_stat_failed_both")
]:
    os.makedirs(folder, exist_ok=True)

# Download MicrobiomeKG Node data
if not os.path.exists(NODE_FILE_PATH):
    print(f"{FILENAME} does not exist. Attempting to download...")
    result = subprocess.run(
        ["wget", "-O", NODE_FILE_PATH, MICROBIOME_KG_DOWNLOAD_URL + FILENAME],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode == 0:
        print(f"File {NODE_FILE_PATH} downloaded successfully!")
    else:
        print(f"Error downloading file {NODE_FILE_PATH}.")
else:
    print(f"File {NODE_FILE_PATH} already exists, skipping download.")

## Build Rules
rule targets:
    input:
        os.path.join(ROOT_PATH, "data_syn", f"Microbiome_KG_nodes_syn_{MICROBIOME_KG_VERSION}.tsv"),
        os.path.join(ROOT_PATH, "syn_stat", "failed_curies.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "failed_both.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "total_success.csv"),
        os.path.join(STAT_PATH, "syn_stat_failed_both", "failed_curies2.csv"),
        os.path.join(STAT_PATH, "syn_stat_failed_both", "failed_both2.csv"),
        os.path.join(STAT_PATH, "syn_stat_failed_both", "total_success2.csv")

# Node synonymize MicroKG nodes (round 1)
rule run_nodesyn_microkg:
    input:
        file = NODE_FILE_PATH,
        script = os.path.join(SCRIPT_PATH, 'node_syn_microkg.py'),
        syn_db = NODE_SYN_DB
    output:
        os.path.join(ROOT_PATH, "data_syn", f"Microbiome_KG_nodes_syn_{MICROBIOME_KG_VERSION}.tsv"),
        os.path.join(ROOT_PATH, "syn_stat", "failed_curies.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "failed_both.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "total_success.csv")
    params:
        data_syn_dir = directory(os.path.join(ROOT_PATH, "data_syn")),  
        syn_stat_dir = directory(os.path.join(ROOT_PATH, "syn_stat"))
    run:
        """
        python {input.script} --input {input.file} --syn_db {input.syn_db} --output {params.data_syn_dir} --syn_stat_dir {params.syn_stat_dir}
        """
rule stat_node_syn:
    input:
        file = NODE_FILE_PATH,
        script = os.path.join(SCRIPT_PATH, 'MicroKG_Stat.py')
    output:
        os.path.join(ROOT_PATH, "syn_stat", "NS_performance_summary.txt"),
        os.path.join(ROOT_PATH, "syn_stat", "wrong_name.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "no_name.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "curie_not_mapping.csv"),
        os.path.join(ROOT_PATH, "syn_stat", "name_not_mapping.csv")
    params:
        node_syn_result = os.path.join(ROOT_PATH, "data_syn", f"Microbiome_KG_nodes_syn_{MICROBIOME_KG_VERSION}.tsv")
    run:
        """
        python {input.script} --input {input.file} --stat_dir syn_stat --result_file {params.node_syn_result}
        """
rule failed_both_processing:
    input:
        file = FAILED_BOTH_INPUT
        script=FAILED_BOTH_SCRIPT
    output:
        result = FAILED_BOTH_OUTPUT
    shell:
        """
        python {input.script} --input {input.file} --output {output.result}
        """
rule node_syn_failed_both:
    input:
        file = FAILED_BOTH_OUTPUT
        syn_db = NODE_SYN_DB
        script = os.path.join(SCRIPT_PATH, 'NodeSyn_failed_both.py')
    output:
        os.path.join(ROOT_PATH, "data_syn", "failed_both_syn_v0.2.1.tsv"),
        os.path.join(STAT_PATH, "syn_stat_failed_both", "failed_curies2.csv"),
        os.path.join(STAT_PATH, "syn_stat_failed_both", "failed_both2.csv"),
        os.path.join(STAT_PATH, "syn_stat_failed_both", "total_success2.csv")
    shell:
        """
        python {input.script} --input {input.file} --syn_db {input.syn_db} --output {output}
        """


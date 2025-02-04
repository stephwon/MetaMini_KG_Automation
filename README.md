# MetaMini_KG_Automation
This is an automation pipeline that cleans and produces basic output performance statistics of node synonymization mapping.

**Note**: This pipeline is decommissioned due to change in project direction and change in data schema.
The input Microbiome knowledge-graph (`MicrobiomeKG`) was provided by Glusman Lab at Institute for Systems Biology (ISB).


## Modify `config.yaml` File If Needed 
Before executing the pipelline one should modify some global variables in the `config.yml` file. We listed some required variables below:
```
  MICROBIOME_KG_VERSION: 'v0.2.1' # change to correct version of MicrobiomeKG data
  MICROBIOME_KG_DOWNLOAD_URL: 'https://db.systemsbiology.net/gestalt/KG/' # if web address is changed, input correct link
  NODE_SYN_DIR:  # input correct RTX Node Synonymizer path (git repo clone)
```


## Schematic
The basic schematic of the snakemake pipeline is as followed:


### Step 1: Node Synonymization (Round 1)
This is the first round of node synonymization. Nodes ID and/or name are passed through [ARAX Node Synonymization](https://github.com/RTXteam/RTX/blob/master/code/ARAX/NodeSynonymizer/node_synonymizer.py) (version 2.10.1). To obtian the ARAX Node Synonymization, clone the repository and follow the git instruction.
The node ID is used first in Node Synonymizer to get the mapping result, however if the result is not produced then the node `Name` will be used to yield mapping result. If both ID and Name do not provide result, the node will be logged as `failed_both`.
If either ID or Name produces successfully synonymized nodes mapping results it will store the canonical ID and Name in TSV file. 

### Step 2: Performance Statistics
This will give basic performance statistics on previous mapping results as summary (`NS_performance_summary.txt`) and CSV files of breakdown of failure results for later detailed analysis (`wrong_name`,`no_name`,`curie_no_mapping`,`name_no_mapping`).

### Step 3: Post Processing Step
We realized that there were prefixes that needed to be modified and gene names were not correct in the `failed_both` nodes that were contributing to the failure rate in node mapping. Therefore, we employed additional data cleaning step (correcting gene name, prefixes, removing strains etc.) to maximize mapping hit rate.

### Step 4: Failed Both NS 
This is Round 2(-ish) of Node Synonymization. After cleaning the `failed_both` nodes, we ran these `failed_both` nodes through node synonymization again to obtain mapping result.


To execute this pipeline use the following command below:
```bash
  snakemake --cores 16 -s MetaMini_KG_pipeline.smk targets
```

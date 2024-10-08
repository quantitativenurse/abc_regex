# we used a singlularity container for our environment on our supercomputer cluster
# below are the arguments we used when running the code


# run script/arguments for extract function
singularity exec /path/to/container/singularity_container.sif \
    python abc_regex.py \
        --extract y \
        --in_file /path/to/input_file.txt \
        --out_file /path/to/output \
        --chunk_size 10000000

# run script/arguments for aggregate and score function
singularity exec /data/g_jeffery_lab/substance_use_disorders/containers/images/python_container.sif \
    python abc_regex.py \
        --aggregate_score y \
        --results_path /path/to/results/

# this is the format we used for each row in our tab separated input file
# due to it being real notes with punctuation, we used special delimiters that are unlikely
# to be found as a false delimiter in the text to be processed
person_identifier      !^!     note_identifier    !^!     note_text

# Automation of the Addiction Behaviors Checklist with regular expressions  

## Data Pre-Processing  
Since we're using real notes with punctuation, we used special delimiters that are unlikely to be found as a false delimiter in the text to be processed.

This is the format we used for each row in our tab separated input file:
```
person_identifier&nbsp;&nbsp;      !^!&nbsp;&nbsp;     note_identifier&nbsp;&nbsp;    !^!&nbsp;&nbsp;     note_text
```

## Running Scripts  
Runscript/arguments for extract function to find all matches for each pattern:
```
singularity exec /path/to/container/singularity_container.sif \
    python abc_regex.py \
        --extract y \
        --in_file /path/to/input_file.txt \
        --out_file /path/to/output \
        --chunk_size 10000000
```

Runscript/arguments for aggregate and score function to generate a score for an individual patient across all notes:
```
singularity exec /path/to/container/singularity_container.sif \
    python abc_regex.py \
        --aggregate_score y \
        --results_path /path/to/results/
```






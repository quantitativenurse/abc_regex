# Automation of the Addiction Behaviors Checklist with regular expressions  

## Update: now a Python package (sudregex)
After the published work, this code was developed into a Python package, **sudregex**: https://github.com/quantitativenurse/sud-regex (`pip install sudregex`). The scripts here are unchanged from the published work, and sudregex's output won't match them exactly. Use this repo to reproduce the published results, and sudregex for new work.

## Data Pre-Processing  
Since we're using real notes with punctuation, we used special delimiters that are unlikely to be found as a false delimiter in the text to be processed.

This is the format we used for each row in our tab separated input file:
```
person_identifier      !^!     note_identifier    !^!     note_text
```

## Running Scripts  
Runscript/arguments for extract function to find all matches for each pattern:
```
    python abc_regex.py \
        --extract y \
        --in_file /path/to/input_file.txt \
        --out_file /path/to/output \
        --chunk_size 10000000
```

Runscript/arguments for aggregate and score function to generate a score for an individual patient across all notes:
```
    python abc_regex.py \
        --aggregate_score y \
        --results_path /path/to/results/
```






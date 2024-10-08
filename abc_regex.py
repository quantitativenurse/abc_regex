#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import re
import time
import glob
import os
import sys
import argparse

import importlib
import abc_regex_checklist
import abc_regex_helper as hlp
importlib.reload(hlp)

# mute setting with copy warning
pd.options.mode.chained_assignment = None  # default='warn'

# read in command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--extract",
                    help="Whether to perform regular expression extraction")
parser.add_argument("--aggregate_score",
                    help="Whether to aggreagte & score results")
parser.add_argument("--in_file",
                    help="Path to text file for searching")
parser.add_argument("--out_file",
                    help="Path to where results should be exported")
parser.add_argument("--results_path",
                    help="Directory containing the results files to aggregate and score")
parser.add_argument("--nrows",
                    help="Number of text file rows to read in; defaults to all if empty")
parser.add_argument("--chunk_size",
                    help="Number of rows to analyze at 1 time; defaults to 1M if empty")
parser.add_argument("--run_tests",
                    help="Indicate whether we are testing the code by running a test set")
args = parser.parse_args()

in_file = args.in_file
out_file = args.out_file
results_path = args.results_path
run_tests = args.run_tests

# for de-bugging
# total_memory, used_memory, free_memory = map(int, os.popen('free -t -m') \
#                                            .readlines()[-1].split()[1:])
# print("RAM memory % used:", round((used_memory/total_memory) * 100, 2))

# Regular expression extraction
if args.extract:
    from pandarallel import pandarallel
    pandarallel.initialize(progress_bar=False)

    # default is to read all rows in
    NROWS = None
    if args.nrows:
        NROWS = int(args.nrows)

    # default is 1 million rows
    CHUNK_SIZE = 1e6
    if args.chunk_size:
        CHUNK_SIZE = int(args.chunk_size)

    # create dataframes for storing results
    results = pd.DataFrame()
    col_names = ["grid", "note_id", "note_text"]

    time0 = time.time()

    # keep a running counter for printing & exporting
    counter = 0

    for chunk in pd.read_csv(in_file, sep = '\t\!\^\!\t', engine='python', header=None, 
                            nrows=NROWS, chunksize=CHUNK_SIZE):
        chunk.rename(columns={0:"grid", 1:"note_id", 2:"note_text"}, inplace=True)

        print('Starting chunk ' + str(counter))

        # Some SD note_text is an empty string, which defaults to "NaN" & cannot
        #  be treated as a string. So, we're removing all empty notes. We can do 
        #  a simple dropna() since there are only 3 columns & all should have values. 
        chunk.dropna(inplace=True)

        # keep a copy of the grid/note_id cross-walk before dropping the grid
        crosswalk = chunk[['grid', 'note_id']]

        # Some of the SD note_id's are duplicated, perhaps due to multi-part notes. 
        # This causes memory problems due to the note_id being the key on which to merge
        #  dataframes. The following code concatenates (space-separated) the note_text
        #  from all rows that share a note_id. 
        chunk = chunk.groupby(['note_id'])['note_text'].apply(' '.join).reset_index()
        EXPECTED_ROW_COUNT = chunk.shape[0]

        regex_counts = chunk['note_id']
        regex_counts = regex_counts.to_frame()

        # check if partial results already exist
        fname = out_file + '_part_' + str(counter) + '.csv'
        if os.path.isfile(fname):
            print('Chunk ' + str(counter) + ' already processed & available at ' + fname)
        else:
            result = hlp.regex_extract(checklist = abc_regex_checklist.checklist,
                                    df_to_analyze = chunk,
                                    metadata = regex_counts,
                                    preview_count = 0,
                                    expected_row_count = EXPECTED_ROW_COUNT)

            # merge GRID back onto result df
            result = result.merge(crosswalk, how='left', on='note_id')

            # export
            result.to_csv(fname)
            print('Results saved to ' + fname)

        # iterate count
        counter +=1 

    print('Elapsed time: ' + str(round(time.time() - time0, 2)) + ' seconds.')


# Aggregate to patient level and calculate score
if args.aggregate_score:

    # read in & concatenate results
    results = pd.DataFrame()

    # check if results_path is file or directory
    if os.path.isdir(results_path):
        all_files = glob.glob(os.path.join(results_path, "results*.csv"))
    elif os.path.isfile(results_path):
        all_files = [results_path]
    else:
        print('Results path not found: ' + results_path)
        exit
    
    for f in all_files:
        print('Starting ' + f)
        # read in 1M rows at a time & drop note_text each time to help with memory management
        for chunk in pd.read_csv(f, chunksize=1e6):
            chunk.drop(columns=['Unnamed: 0', 'note_text'], inplace=True)
            results = pd.concat([results, chunk], ignore_index=True)
            #total_memory, used_memory, free_memory = map(int, os.popen('free -t -m') \
            #                                .readlines()[-1].split()[1:])
            #print("RAM memory % used:", round((used_memory/total_memory) * 100, 2))

    # aggregate & temporarily store the note counts before aggregating other columns
    note_counts_by_grid = results[['grid', 'note_id']]
    note_counts_by_grid = note_counts_by_grid.groupby('grid')['note_id'].nunique().reset_index()
    note_counts_by_grid.rename(columns={'note_id': 'note_counts'}, inplace=True)

    # specify column names to keep 
    column_list = ['grid',
                   'illicit_drugs_OPIOID_MATCHED_NEG', # 1a
                   'problem_drinking_NEG', # 1b
                   'dui_NEG', # 1c
                   'hoarding_OPIOID_MATCHED_NEG', # 2
                   'more_narcotic_OPIOID_MATCHED_NEG', # 3
                   'ran_out_early_OPIOID_MATCHED_NEG', # 4
                   'increased_op_OPIOID_MATCHED_NEG', # 5a
                   'escalation_op_OPIOID_MATCHED_NEG', # 5b
                   'prn_OPIOID_MATCHED', # 6
                   'multiple_sources_x_OPIOID_MATCHED_NEG', # 7a
                   'multiple_sources_y_OPIOID_MATCHED_NEG', # 7b
                   'bought_on_street_OPIOID_MATCHED_NEG', # 8
                   'sedated_OPIOID_MATCHED_NEG', # 9
                   'worries_about_addiction_NEG', # 10
                   'strong_preference_OPIOID_MATCHED_NEG', # 11a
                   'strong_preference_IV', # 11b
                   'future_availability_1_OPIOID_MATCHED_NEG', # 12a
                   'future_availability_2_OPIOID_MATCHED_NEG', # 12b
                   'worsened_relationships_OPIOID_MATCHED_NEG', # 13
                   'misrep_use_OPIOID_MATCHED', # 14
                   'needs_must_have_OPIOID_MATCHED', # 15
                   'opioid_tag_OPIOID_MATCHED_NEG', # 16
                   'lack_interest_rehab_OPIOID_MATCHED', # 17
                   'minimal_relief_x_OPIOID_MATCHED', # 18a
                   'tolerance_OPIOID_MATCHED_NEG', # 18b
                   'med_agreement', # 19
                   'SO_concern_OPIOID_MATCHED_NEG' # 20
                   ]
    results = results[column_list]

    # column collapsing/aggregation
    # 1
    cols = ['illicit_drugs_OPIOID_MATCHED_NEG', 'problem_drinking_NEG', 'dui_NEG']
    results['drugs_alc'] = results[cols].sum(axis=1)
    results.drop(columns=cols, inplace=True)

    # 5
    cols = ['increased_op_OPIOID_MATCHED_NEG', 'escalation_op_OPIOID_MATCHED_NEG']
    results['increase_use'] = results[cols].sum(axis=1)
    results.drop(columns=cols, inplace=True)

    # 7
    cols = ['multiple_sources_x_OPIOID_MATCHED_NEG','multiple_sources_y_OPIOID_MATCHED_NEG']
    results['multiple_sources'] = results[cols].sum(axis=1)
    results.drop(columns=cols, inplace=True)

    # 11
    cols = ['strong_preference_OPIOID_MATCHED_NEG', 'strong_preference_IV']
    results['strong_preference'] = results[cols].sum(axis=1)
    results.drop(columns=cols, inplace=True)

    # 12
    cols = ['future_availability_1_OPIOID_MATCHED_NEG','future_availability_2_OPIOID_MATCHED_NEG']
    results['future_availability'] = results[cols].sum(axis=1)
    results.drop(columns=cols, inplace=True)

    # 18
    cols = ['minimal_relief_x_OPIOID_MATCHED', 'tolerance_OPIOID_MATCHED_NEG']
    results['minimal_relief'] = results[cols].sum(axis=1)
    results.drop(columns=cols, inplace=True)

    # sum items by patient/grid
    aggregated = results.groupby(by='grid').sum()

    #convert regex counts per rule to binary 1/0 based on a threshold of matches
    abc_col_list = results.columns.values.tolist()
    abc_col_list.remove('grid')
    THRESHOLD = 0
    for col in abc_col_list:
        aggregated[col] = aggregated[col].apply(lambda x: 1 if x > THRESHOLD else 0)

    # sum together into a total score
    aggregated['regex_score'] = aggregated[abc_col_list].sum(axis=1)

    # add note counts to results
    aggregated = aggregated.merge(note_counts_by_grid, on='grid', how='left')

    # export
    aggregated.to_csv(results_path + '_final_scores.csv')
    print('Aggregated and scored file saved as: ' + results_path + '_final_scores.csv')

    # run tests if desired
    if run_tests:
        aggregated = aggregated.reset_index()
        cases = aggregated[aggregated['grid'] == 1]
        if int(cases['regex_score']) < 20:
            print("It appears some items might not be captured with your current set-up.")
        
        controls = aggregated[aggregated['grid'] == 0].reset_index()
        if int(controls['regex_score']) > 0:
            print("It appears you have some false positives with your current set-up.")


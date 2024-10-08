"""
Helper file so that functions are stored separately from main execution file. 
"""

import pandas as pd
import numpy as np
import re
import time
import glob
import os
import sys

PRINT = False

# global variables
#opioid vocabulary
TERMS_OPIOID = ['pain med','opioid','opiod',' narc','analges','suboxone','Avinza','codeine', 'dilaudid',
             'fentanyl', 'hydrocodone', 'morphine', 'opana', 'opiate','oxycodone','oxycontin','oxymorphone','percocet',
             'roxicodone','sufentanyl','vicodin', 'lortab', 'hydromorphone','abstral','actiq','alfentanil','arymo','ascomp',
             'astramorph','avinza','belbuca','brompheniramine','bunavail','buprenex','buprenorphine','butalbital','butorphanol',
             'butrans','capcof','carisoprodol','cheratussin','coditussin','conzip','demerol','dexbrompheniramine','dihydrocodeine','diskets',
             'dolophine','durmorph','embeda','endacof','endocet','exalgo','fentora','fioricet','flowtuss','guaifenesin','histex',
             'hycet','hycofenix','hydrocodone','hydromorphone','hysingla','ibudone','infumorph','iophen','iorinal','kadian','lazanda',
             'levorphanol','lorcet','lotruss','meperidine','methadone','methadose','morphabond','morphine','ms contin',
             'nalbuphine','nalocet','ninjacof','nucynta','obredon','opana','opium','orco','oxaydo','oxecta','oxycodone','panlor',
             'paregoric','pentazocine','percocet','phenylhistine','primlev',
             'pro-clear','probuphine','promethazine','psuedoephedrine',
             'relcof','remifentanil','reprexain','rezira','robafen','roxicodone','rydex','suboxone','subsys','sufentanil','synalgos',
             'talwin','tapentado','tramadol','trezix','triplidine','trymine','tusnel','tussicpas','ultiva','ultracet','ultram',
             'verdrocet','vicodin','vicoprofen','virtussin','xartemix','xodol','xtampza','zamicet','zodryl','zubsolv','zutripro',
             'zylon']
if PRINT:
    print('The opioid-related terms used for searching include: ' + str(TERMS_OPIOID))

# Memory usage
total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])

#note filters, for removing symbols etc.
remove_line_break = lambda x : str(x).replace("$+$"," ")

def previews_batch(checklist, df_summarized, n_notes=2, span=300):
    """
    The following function previews the notes and writes them to a text file. 
    
    INPUTS: checklist for previews, df of summarized data WITH NOTE TEXT, number of notes you would like to
    preview per item, and the span of the match preview
    
    OUTPUTS: previews as a text printout, saved to a .txt file
    """
    
    #definte the normal readout to be the system redoubt so you have a default for when you change it later
    original_stdout = sys.stdout

    #safe open file
    with open('note_previews.txt', 'w') as f:

        #set the outputs of the subsequent print function calls to print TO THE FILE
        sys.stdout = f

        #create a list of column names to preview from the df input and remove the note_id and note_text columns
        #from the list
        columns = list(results_saved)
        columns.remove('note_id')
        columns.remove('note_text')

        for i in checklist:
            col_name = checklist[i]['col_name']

            #if the col name is in the columns list, generate the related names for opioid and negation checks
            if col_name in columns:

                lab = checklist[i]['lab']
                print("\n", lab, "\n")

                pat = checklist[i]['pat']
                print("Pattern:", pat, "\n")

                #generate column names
                col_name = checklist[i]['col_name']

                if checklist[i]['opioid']:
                    col_name_opioid = col_name + '_OPIOID_MATCHED'
                    if checklist[i]['negation']: 
                        col_name_negated = col_name_opioid + '_NEG'
                elif checklist[i]['negation']: 
                    col_name_negated = col_name + '_NEG'

                #create list of column names to preview
                if checklist[i]['opioid']:
                    col_name_list = [col_name_opioid]
                    if checklist[i]['negation']: 
                        col_name_list = [col_name_negated]
                elif checklist[i]['negation']: 
                    col_name_list = [col_name_negated]
                else:
                    col_name_list = [col_name]
                print("Columns related to this checklist item:", col_name_list, "\n")

            else:
                continue

            #actual preview portion
            for col_name in col_name_list:
                print("Column Name:", col_name, "\n")
                if n_notes > len(results_saved[results_saved[col_name] > 0]):
                    n_notes = len(results_saved[results_saved[col_name] > 0])
                #sample ten random matches
                matches = results_saved[results_saved[col_name] > 0]
                matches.sample(n_notes, random_state=123)

                if n_notes > len(matches.index):
                    n_notes=len(matches.index)

                #for every match in matches in the range of the number of rows, print the string
                for i in range(matches.shape[0]):
                    print('~~~ ' + str(matches['note_id'].iloc[i]) + ' ~~~')

                    # create iterator of all possible matches
                    for m in re.finditer(pat, matches['note_text'].iloc[i], flags=re.IGNORECASE|re.MULTILINE):

                        print(m, "\n")

                        # store each span as start & stop
                        #start, stop = next(m).span()
                        start, stop = m.span()

                        # don't go before beginning of note or after the end
                        start = max(0, start - span)
                        stop = max(stop, stop + span)

                        text_print = matches['note_text'].iloc[i][start:stop]

                        """
                        #this inserts highlighting around the main match- for some reason this often results in the whole
                        #note being highlighted when you use start, stop locations so I just have it highlight the first
                        #eight characters right no
                        text_print = matches['note_text'].iloc[i][start:stop]

                        text_print = (text_print[0:(span)] + '\x1b[0;39;43m' + text_print[(span):(span+8)] + 
                                        '\x1b[0m' + text_print[(span+8):-1])

                        #highlight opioid and negation related vocabularies
                        for term in TERMS_OPIOID:
                                x = re.search(term, text_print, flags=re.IGNORECASE|re.MULTILINE)
                                if x:
                                    start, stop = x.span()
                                    text_print = (text_print[0:start] + '\x1b[0;39;43m' + text_print[start:stop] + 
                                        '\x1b[0m' + text_print[stop:-1])

                        neg = ['no ', 'not ', 'denies', 'denial', 'doubt', 'never', 'negative for']

                        for term in neg:
                                x = re.search(term, text_print, flags=re.IGNORECASE|re.MULTILINE)
                                if x:
                                    start, stop = x.span()
                                    text_print = (text_print[0:start] + '\x1b[0;39;43m' + text_print[start:stop] + 
                                        '\x1b[0m' + text_print[stop:-1])
                        """

                        print(text_print)
                        print('\n')

                #explicitly clear matches just to make sure to save memory
                del matches

        #change the readout back to the default system readout
        sys.stdout = original_stdout


def regex_extract(checklist, df_to_analyze, metadata, preview_count, expected_row_count):
    """
    The following function accessess the dictionary of checklist items and applies the regex search functions to each 
    one iteratively. 

    Inputs: checklist of items, df with notes to analyze, note metadata to create a summarized df, and
    if you are previeiwing, a number of notes to preview.

    Outputs: a results df which contains the summarized number of matches per NOTE
    """

    for i in checklist:
        assert df_to_analyze.shape[0] == expected_row_count,'Row counts do not match - double-check merges'
        print('Checklist item #: ' + str(i))

        pat = checklist[i]['pat']

        # generate appropriate column names for this checklist item
        col_name = checklist[i]['col_name']
        if checklist[i]['opioid']:
            col_name_opioid = col_name + '_OPIOID_MATCHED'
            if checklist[i]['negation']: 
                col_name_negated = col_name_opioid + '_NEG'
        elif checklist[i]['negation']: 
            col_name_negated = col_name + '_NEG'

        # perform initial search for pattern
        df_searched = regex_search_file(pat, col_name, df_to_analyze, metadata, preview=True)

        # perform next searches for opioid-detection and/or negation detection
        if checklist[i]['opioid']:
            # if there are matches for the original pattern, start additional searches...
            if df_searched[col_name].sum() > 0:
                df_searched = check_for_opioid(pat, col_name, col_name_opioid, df_searched)

                if checklist[i]['negation']:
                    if df_searched[col_name_opioid].sum() > 0: 
                        df_searched = check_negation(pat, col_name_opioid, col_name_negated, df_searched, 
                                                     t=[], neg=True, span=65)

                        # discharge
                        df_searched = discharge_instructions(pat, df_searched, col_name_negated, span=250)
                        # fp
                        try:
                            common_fp = checklist[i]['common_fp']
                            df_searched = check_common_false_positives(pat, df_searched, col_name_negated, common_fp, span=65)
                        except:
                            pass

                    # if no original pattern matches, simply set the column's value to 0
                    else:
                        df_searched[col_name_negated] = 0

            else:
                # if no original pattern matches, simply set the column's value to 0
                df_searched[col_name_opioid] = 0
                df_searched[col_name_negated] = 0

                # discharge
                df_searched = discharge_instructions(pat, df_searched, col_name_opioid, span=250)
                # fp
                try:
                    common_fp = checklist[i]['common_fp']
                    df_searched = check_common_false_positives(pat, df_searched, col_name_opioid, common_fp, span=65)
                except:
                    pass

        elif checklist[i]['negation']: 
            # if there are matches, continue checking...
            if df_searched[col_name].sum() > 0:
                df_searched = check_negation(pat, col_name, col_name_negated, df_searched, t=[], neg=True, span=65)

                # discharge
                df_searched = discharge_instructions(pat, df_searched, col_name_negated, span=250)
                # fp
                try:
                    common_fp = checklist[i]['common_fp']
                    df_searched = check_common_false_positives(pat, df_searched, col_name_negated, common_fp, span=65)
                except:
                    pass

            # if no original pattern matches, simply set the column's value to 0
            else:
                df_searched[col_name_negated] = 0

        else:
            # if there are matches, continue checking...
            if df_searched[col_name].sum() > 0:
                # discharge
                df_searched = discharge_instructions(pat, df_searched, col_name, span=250)
                # fp
                try:
                    common_fp = checklist[i]['common_fp']
                    df_searched = check_common_false_positives(pat, df_searched, col_name, common_fp, span=65)
                except:
                    pass

        if checklist[i]['preview']:
            preview_string_matches(pat, col_name, df_searched, n_notes=preview_count, span=100)

        if checklist[i]['opioid']:
            if checklist[i]['negation']:
                metadata = metadata.merge(df_searched[['note_id', col_name, col_name_opioid, col_name_negated]], 
                                  on='note_id', how='left')

            else:
                metadata = metadata.merge(df_searched[['note_id', col_name, col_name_opioid]], 
                                  on='note_id', how='left')

        elif checklist[i]['negation']:
            metadata = metadata.merge(df_searched[['note_id', col_name, col_name_negated]], 
                                  on='note_id', how='left')

        else:
            metadata = metadata.merge(df_searched[['note_id', col_name]], 
                                  on='note_id', how='left')

    metadata = metadata.merge(df_to_analyze[['note_id', 'note_text']], on ='note_id', how='left')
    print("RAM memory % used:", round((used_memory/total_memory) * 100, 2))

    return metadata


def regex_search_file(pat, new_col_name, df_to_search, metadata, preview=True):
    """
    This function searches the note text in each of the rows of the file and returns the number of matches for the regex.
    It concatenates the matches to a summarized df for each note_id

    INPUTS: the pattern from the checklist, the name of the column for the summarized df from the checklist,
    the df to search for matches w/ notes, and preview argument.

    OUTPUTS: df that has been searched for matches with note_text and matches 
    """

    #print("Regex Search File: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    # create empty dataframe for storing counts
    #new_col_name: is col_name taken in new_column_and_search and specified in each ABC checklist
    #item
    counts = pd.DataFrame(columns = ['note_id', 'note_text', new_col_name])

    #search for pattern
    #findall: Return all non-overlapping matches of pattern in string,
    #as a list of strings or tuples. The string is scanned left-to-right, 
    #and matches are returned in the order found. Empty matches are included in the result.
    
    #returns the number of matches in the note_text with ignoring case and the multiline flag
    pat_search = lambda x: len(re.findall(pat, str(x), flags=re.IGNORECASE|re.MULTILINE))
    
    #apply the search to every note text
    #use parallel apply to process multiple notes at the same time
    #for df in dfs:
    df_to_search['note_text'] = df_to_search['note_text'].parallel_apply(remove_line_break)
    df_to_search[new_col_name] = df_to_search['note_text'].parallel_apply(pat_search)
#     df['note_text'] = df['note_text'].apply(remove_line_break)
#     df[new_col_name] = df['note_text'].apply(pat_search)
    
    # add resulting counts to the temporary dataframe
    #outer join of counts to input df that also sorts the df
    counts = pd.concat([counts, df_to_search], sort=True)

    #columns to keep for the final df
    keep_cols = ['note_id', new_col_name]
    #optional preview of note text
    if preview:
        keep_cols.append('note_text')
    
    #merge w/ left join to creat df on note id with the counts
    df_searched = metadata.merge(counts[keep_cols], how='left', on='note_id')

    # create dataframe of matches for providing descriptive statistics
    for_counts = df_searched[df_searched[new_col_name] > 0]
    #print('Original pattern search yielded ' 
          #+ str(for_counts[new_col_name].sum()) + ' total matches within ' 
          #+ str(len(np.unique(for_counts['note_id']))) + ' notes.')

    #print("Regex Search File: RAM memory % used:", round((used_memory/total_memory) * 100, 2))

    return df_searched


def check_for_opioid(pat, col_name, col_name_opioid, df_searched, span=100):
    """
    Searches if opioid tag around match. creates new column with results. 

    Inputs: pattern to search, new column name, df searched for initial matches, and span argument that determines 
    scope of search.

    Outputs: searched df with additional opioid matches
    """

    yes_or_no = []

    matches = df_searched[df_searched[col_name] > 0]
    for i in range(matches.shape[0]):        
        match = False
        for m in re.finditer(pat, matches['note_text'].iloc[i], flags=re.IGNORECASE|re.MULTILINE):
            # store each span as start & stop
            #start, stop = next(m).span()
            #m.span is the location of the beginning and end of the match as a tuple, which are 
            #respectively assigned to start and stop
            start, stop = m.span()

            # don't go before beginning of note or after the end
            #the start of the opioid search is either position 0 or 200 before the span
            start = max(0, start - span)
            #the end is either then end of the match location or 200 after the span
            stop = max(stop, stop + span)
            match_str = matches['note_text'].iloc[i][start:stop]
            
            #search for every opioid vocabulary, if it matches, match = true
            for term in TERMS_OPIOID:
                x = re.search(term, match_str, flags=re.IGNORECASE|re.MULTILINE)
                if x:
                    match = True
        if match:
            yes_or_no.append(1)
        
        elif not match:
            yes_or_no.append(0)

    # add the new matches with the opioid check to the counts file by making a new data frame
    #and using an index of note_id, then rename back to the col_name_opioid, aka the title of the abc
    #checklist item

    matches[col_name_opioid] = yes_or_no
    add_this= pd.DataFrame(data=yes_or_no, index=matches['note_id'])

    add_this.rename(columns = {0: col_name_opioid}, inplace = True)

    df_opioid_searched = df_searched.merge(add_this, how='left', on='note_id')

   # print("df opioid searched:", df_opioid_searched)

    #dfn.fillna(value = 0, inplace = True)
    #assert sum(dfn[col_name_opioid].isnull()) == 0

    # create dataframe of matches for providing descriptive statistics
    for_counts = df_opioid_searched[df_opioid_searched[col_name_opioid] > 0]
    #print('Restricting to opioid matches yielded ' 
          #+ str(for_counts[col_name_opioid].sum()) + ' total matches within ' 
          #+ str(len(np.unique(for_counts['note_id']))) + ' notes. ')
    counts_sum = for_counts[col_name_opioid].sum()

    return df_opioid_searched


def check_negation(pat, col_name, col_name_negated, df_searched, t=[], neg=True, span=65):
    
    """
    Searches for negation vocabulary around match. creates new column with results. 

    Inputs: pattern to search, new column name, df searched for initial matches, and span argument that determines 
    scope of search.

    Outputs: searched df with additional negation matches
    """

    matches = df_searched[df_searched[col_name] > 0]
    
    if neg:
        neg = ['no ', 'not ', 'denie', 'denial', 'doubt', 'never', 'negative', 'without', 'neg',
               "didn't"] # 3/22/24: Alvin adding "didn't" to the list
        neg.extend(t)
    else:
        neg = t
    
    yes_or_no = []

    for i in range(matches.shape[0]):
        match = False
        for m in re.finditer(pat, matches['note_text'].iloc[i], flags=re.IGNORECASE|re.MULTILINE):
            start, stop = m.span()

            # don't go before beginning of note or after the end
            start = max(0, start - span)
            match_str = matches['note_text'].iloc[i][start:stop]
            
            for term in neg:
                x = re.search(term, match_str, flags=re.IGNORECASE|re.MULTILINE)
                if x:
                    match = True
        # difference here is that if it matches we append 0, 1 for not.
        if match:
            yes_or_no.append(0)
        elif not match:
            yes_or_no.append(1)
        
    matches[col_name_negated] = yes_or_no
  
    add_this= pd.DataFrame(data=yes_or_no, index=matches['note_id'])
    add_this.rename(columns = {0: col_name_negated}, inplace = True)
    
    df_negation_searched = df_searched.merge(add_this, how='left', on='note_id')
    
    #print("dataframe negation searched", df_negation_searched)
    
    #dfn.fillna(value = 0, inplace = True)
    #assert sum(df[col_name].isnull()) == 0
    
    # create dataframe of matches for providing descriptive statistics
    for_counts = df_negation_searched[df_negation_searched[col_name_negated] > 0]
    #print('Removing negated matches yielded ' 
         # + str(for_counts[col_name_negated].sum()) + ' total matches within ' 
         # + str(len(np.unique(for_counts['note_id']))) + ' notes. \n' )
    
   # print("Negation Search: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    return df_negation_searched


def check_common_false_positives(pat, df_searched, col_name_fp, common_fp, span=20):

    """
    There are common false positives associated with many of the items. This will access common false positives associated
    with each item and remove those matches. 

    Inputs: pattern to search, new column name, df searched for initial matches, and span argument that determines 
    scope of search.

    Outputs: searched df with additional negation matches
    """
    
    # print("FP Search: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    matches = df_searched[df_searched[col_name_fp] > 0]

    #family_history = ['family history', 'family medical history']

    yes_or_no = []

    for i in range(matches.shape[0]):        
        match = False
        for m in re.finditer(pat, matches['note_text'].iloc[i], flags=re.IGNORECASE|re.MULTILINE):
            start, stop = m.span()

            # don't go before beginning of note or after the end
            start = max(0, start - span)
            stop = max(stop, stop + span)
            match_str = matches['note_text'].iloc[i][start:stop]
            
            for term in common_fp:
                x = re.search(term, match_str, flags=re.IGNORECASE|re.MULTILINE)
                if x:
                    match = True
        # difference here is that if it matches we append 0, 1 for not.
        if match:
            yes_or_no.append(0)
        elif not match:
            yes_or_no.append(1)
        
    matches[col_name_fp] = yes_or_no
  
    add_this= pd.DataFrame(data=yes_or_no, index=matches['note_id'], columns = ['false_positive'])
    df_searched = df_searched.merge(add_this, how='left', on='note_id')
    df_searched = df_searched.drop(labels = col_name_fp, axis = 1)
    df_searched.rename(columns = {'false_positive': col_name_fp}, inplace = True)
    
    #df_searched[col_name_fp] = add_this[col_name_fp]
    
    #print("dataframe fp searched", df_searched)
    
    #dfn.fillna(value = 0, inplace = True)
    #assert sum(df[col_name].isnull()) == 0
    
    # create dataframe of matches for providing descriptive statistics
    for_counts = df_searched[df_searched[col_name_fp] > 0]
    #print('Removing false positive matches yielded ' 
         # + str(for_counts[col_name_fp].sum()) + ' total matches within ' 
         # + str(len(np.unique(for_counts['note_id']))) + ' notes. \n' )
    
    #print("Negation Search: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    return df_searched


def discharge_instructions(pat, df_searched, col_name_discharge, span=350):
    
    """
    Removes matches that are associated with discharge instructions
    
    Inputs: data frame with matchdata and note text
    Oupts: data frame with matches removed that are in discharge instructions
    """
    
    #print("Negation Search: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    matches = df_searched[df_searched[col_name_discharge] > 0]
    
    discharge = ['discharge instructions', 'no results for']
   
    yes_or_no = []

    for i in range(matches.shape[0]):
        match = False
        for m in re.finditer(pat, matches['note_text'].iloc[i], flags=re.IGNORECASE|re.MULTILINE):
            start, stop = m.span()

            # don't go before beginning of note 
            start = max(0, start - span)
            match_str = matches['note_text'].iloc[i][start:stop]
            
            for term in discharge:
                x = re.search(term, match_str, flags=re.IGNORECASE|re.MULTILINE)
                if x:
                    match = True
        # difference here is that if it matches we append 0, 1 for not.
        if match:
            yes_or_no.append(0)
        elif not match:
            yes_or_no.append(1)
        
    matches[col_name_discharge] = yes_or_no
  
    add_this= pd.DataFrame(data=yes_or_no, index=matches['note_id'], columns = ['discharge'])
    df_searched = df_searched.merge(add_this, how='left', on='note_id')
    df_searched = df_searched.drop(labels = col_name_discharge, axis = 1)
    df_searched.rename(columns = {'discharge': col_name_discharge}, inplace = True)
    
    #print("discharge matches in df_searched: " + str(df_searched[col_name_discharge].sum()))
    
    #print("dataframe discharge searched", df_searched)
    
    #dfn.fillna(value = 0, inplace = True)
    #assert sum(df[col_name].isnull()) == 0
    
    # create dataframe of matches for providing descriptive statistics
    for_counts = df_searched[df_searched[col_name_discharge] > 0]
    #print('Removing discarge instruction matches yielded ' 
         # + str(for_counts[col_name_discharge].sum()) + ' total matches within ' 
         # + str(len(np.unique(for_counts['note_id']))) + ' notes. \n' )
    
    #print("Discarge Search: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    return df_searched
    


def preview_string_matches(pat, col_name, df_searched, col_check=False, n_notes=10, span=100):
    
    """
    INPUTS: data frame with match data and note text
    OUTPUT: a preview of the string where the match occurs in the note printed out
    """
    
    #check memory usage
    # print("Previews: RAM memory % used:", round((used_memory/total_memory) * 100, 2))
    
    if n_notes > len(df_searched[df_searched[col_name] > 0]):
        n_notes = len(df_searched[df_searched[col_name] > 0])
    
    #sample ten random matches
    matches = df_searched[df_searched[col_name] > 0].sample(n_notes, random_state=123)
    
    if n_notes > len(matches.index):
        n_notes=len(matches.index)
    
    #for every match in matches in the range of the number of rows, print the string
    for i in range(matches.shape[0]):
        print('~~~ ' + str(matches['note_id'].iloc[i]) + ' ~~~')
        
        # create iterator of all possible matches
        for m in re.finditer(pat, matches['note_text'].iloc[i], flags=re.IGNORECASE|re.MULTILINE):
            
            # store each span as start & stop
            #start, stop = next(m).span()
            start, stop = m.span()
            
            
            # don't go before beginning of note or after the end
            start = max(0, start - span)
            stop = max(stop, stop + span)
            
            #this inserts highlighting around the main match- for some reason this often results in the whole
            #note being highlighted when you use start, stop locations so I just have it highlight the first
            #eight characters right now
            text_print = matches['note_text'].iloc[i][start:stop]
            text_print = (text_print[0:(span)] + '\x1b[0;39;43m' + text_print[(span):(span+8)] + 
                            '\x1b[0m' + text_print[(span+8):-1])
            
            #highlight opioid and negation related vocabularies
            for term in TERMS_OPIOID:
                    x = re.search(term, text_print, flags=re.IGNORECASE|re.MULTILINE)
                    if x:
                        start, stop = x.span()
                        text_print = (text_print[0:start] + '\x1b[0;39;43m' + text_print[start:stop] + 
                            '\x1b[0m' + text_print[stop:-1])

            neg = ['no ', 'not ', 'denies', 'denial', 'doubt', 'never', 'negative for']

            for term in neg:
                    x = re.search(term, text_print, flags=re.IGNORECASE|re.MULTILINE)
                    if x:
                        start, stop = x.span()
                        text_print = (text_print[0:start] + '\x1b[0;39;43m' + text_print[start:stop] + 
                            '\x1b[0m' + text_print[stop:-1])
            
            print(text_print)
            
            print('\n')
            
    # print("Previews: RAM memory % used:", round((used_memory/total_memory) * 100, 2))


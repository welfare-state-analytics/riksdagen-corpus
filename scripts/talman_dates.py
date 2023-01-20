"""
Algorithmically provide dates for the (vice) talmän dataset.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def main():
    ### Load and format talman data
    talman = pd.read_csv('corpus/talman.csv')
    talman["start"] = talman["start"].fillna('9999')
    talman["end"] = talman["end"].fillna('9999')
    talman["start_manual"] = pd.Series(dtype=bool)
    talman["end_manual"] = pd.Series(dtype=bool)

    for i in range(len(talman)):
        start,end = talman.loc[i, ["start", "end"]]
    
        if len(start) > 4:
            talman.loc[i, "start_manual"] = True
        if len(end) > 4:
            talman.loc[i, "end_manual"] = True

    ### Load and format riksdagen_dates data
    rd_dates = pd.read_csv('corpus/riksdagen_dates.csv')

    # Remove missing starting dates 
    rd_dates = rd_dates[rd_dates["start"].apply(lambda x: len(x) > 4)]

    # Remove urtima files to avoid duplicate year-chamber pairs
    rd_dates = rd_dates[~rd_dates["file"].str.contains("urtima")]

    # Create year and chamber columns for matching
    years = rd_dates["start"].str.split('-')
    rd_dates["year"] = [year[0] for year in years]

    rd_dates["chamber"] = pd.Series(dtype=str)

    # Have duplicates but should be fine when taking chambers into account
    #rd_dates = rd_dates.drop_duplicates(subset='start')

    # Create new vars
    rd_dates = rd_dates.reset_index()
    rd_dates["end"] = pd.Series(dtype=str)

    for i in range(len(rd_dates)):
        if 'fk' in rd_dates.loc[i,"file"]:
            rd_dates.loc[i,"chamber"] = 'Första kammaren'

        elif 'ak' in rd_dates.loc[i,"file"]:
            rd_dates.loc[i,"chamber"] = 'Andra kammaren'

        else:
            rd_dates.loc[i,"chamber"] = 'Enkammarriksdagen'

    # Make periods end 1 day before another begins
    for i in range(len(rd_dates)):
        date = rd_dates.loc[i,"start"]
        
        # Convert datetime in order to back a day
        date = datetime.strptime(date, '%Y-%m-%d')
        date = str(date - timedelta(days = 1)).split(' ')[0]

        rd_dates.loc[i,"end"] = date

    ## Find non-overlapping stard-end years
    start_no_overlap = list(set(talman["start"]) - set(talman["end"]))
    end_no_overlap = list(set(talman["end"]) - set(talman["start"]))

    # Filter away manually added dates
    start_no_overlap = [date for date in start_no_overlap if len(date) <= 4]
    end_no_overlap = [date for date in end_no_overlap if len(date) <= 4]

    # Add dates algorithmically
    for i in range(len(talman)):
        talman_start, talman_end, chamber = talman.loc[i, ["start", "end", "chamber"]]

        # Ignore manually added dates
        if len(talman_start) <= 4:

            # If no one ends when someone starts, make starting date 'YYYY-01-01'
            if talman_start in start_no_overlap:
                talman.loc[i, "start"] = '-'.join([talman_start, '01', '01'])
                talman.loc[i, "start_manual"] = False

            # Else make date day of starting the riksdagen year
            else:
                id_start = np.where((rd_dates["year"] == talman_start) & (rd_dates["chamber"] == chamber))[0]

                # Skip non-matches
                if len(id_start) != 0:
                    talman.loc[i,"start"] = rd_dates.loc[id_start[0],"start"]
                    talman.loc[i, "start_manual"] = False

        if len(talman_end) <= 4:
            # If no one starts when someone ends, make starting date day 'YYYY-12-31'
            if talman_end in end_no_overlap:
                talman.loc[i, "end"] = '-'.join([talman_end, '12', '31'])
                talman.loc[i, "end_manual"] = False

            # Else make date day BEFORE of ending the riksdagen year
            else:
                id_end = np.where((rd_dates["year"] == talman_end) & (rd_dates["chamber"] == chamber))[0]

                # Skip non-matches
                if len(id_end) != 0:
                    talman.loc[i,"end"] = rd_dates.loc[id_end[0],"end"]
                    talman.loc[i, "end_manual"] = False

    # Cleanup and save
    talman.loc[talman["start"] == '9999', "start"] = np.nan
    talman.loc[talman["end"] == '9999', "end"] = np.nan
    talman.to_csv('corpus/talman.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    main()


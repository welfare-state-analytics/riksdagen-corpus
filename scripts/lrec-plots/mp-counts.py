#!/usr/bin/env python3
import pandas as pd

def main():

    mp = pd.read_csv("corpus/metadata/member_of_parliament.csv")
    person = pd.read_csv("corpus/metadata/person.csv")
    party = pd.read_csv("corpus/metadata/party_affiliation.csv")
    name = pd.read_csv("corpus/metadata/name.csv")
    iort = pd.read_csv("corpus/metadata/location_specifier.csv")
    twitter = pd.read_csv("corpus/metadata/twitter.csv")
    print("people:", len(person['wiki_id'].unique()))
    print("names:", len(name))
    print("iort:", len(iort), len(iort['wiki_id'].unique()))
    party.drop_duplicates(subset=['wiki_id', 'party_id'], keep='first', inplace=True)
    print("party:", len(party), len(party['wiki_id'].unique()))
    mp2 = mp.loc[pd.notnull(mp['start']) | pd.notnull(mp['end'])]
    print('start/end:', len(mp2), len(mp2['wiki_id'].unique()))
    print('twitter:', len(twitter), len(twitter['wiki_id'].unique()))

if __name__ == '__main__':
    main()

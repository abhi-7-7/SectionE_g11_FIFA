"""
etl_pipeline.py — Standalone ETL Pipeline
Project: FIFA World Cup Analytics | SectionE_g11

Runs the full extraction → cleaning → merge → export pipeline
without requiring Jupyter. Execute with: python scripts/etl_pipeline.py
"""

import pandas as pd
import numpy as np
import re
import os
import sys

RAW_PATH       = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
PROCESSED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
os.makedirs(PROCESSED_PATH, exist_ok=True)


def log(msg):
    print(f'[ETL] {msg}')


# ─── EXTRACT ──────────────────────────────────────────────────────────────────

def extract():
    log('Loading raw data...')
    cups    = pd.read_csv(os.path.join(RAW_PATH, 'WorldCups.csv'))
    matches = pd.read_csv(os.path.join(RAW_PATH, 'WorldCupMatches.csv'))
    players = pd.read_csv(os.path.join(RAW_PATH, 'WorldCupPlayers.csv'))
    log(f'WorldCups    : {cups.shape}')
    log(f'WorldCupMatches: {matches.shape}')
    log(f'WorldCupPlayers: {players.shape}')
    return cups, matches, players


# ─── CLEAN CUPS ───────────────────────────────────────────────────────────────

def clean_cups(cups_raw):
    log('Cleaning WorldCups...')
    cups = cups_raw.copy()

    def fix_attendance(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        if val.count('.') > 1:
            val = val.replace('.', '')
        return float(val)

    cups['Attendance'] = cups['Attendance'].apply(fix_attendance)

    name_map = {'Germany FR': 'West Germany', 'Korea Republic': 'South Korea'}
    for col in ['Winner', 'Runners-Up', 'Third', 'Fourth', 'Country']:
        cups[col] = cups[col].replace(name_map)

    cups.rename(columns={
        'GoalsScored':    'Total_Goals',
        'QualifiedTeams': 'Qualified_Teams',
        'MatchesPlayed':  'Matches_Played'
    }, inplace=True)

    log(f'  WorldCups cleaned: {cups.shape}')
    return cups


# ─── CLEAN MATCHES ────────────────────────────────────────────────────────────

def clean_matches(matches_raw):
    log('Cleaning WorldCupMatches...')
    matches = matches_raw.copy()

    str_cols = matches.select_dtypes(include='object').columns
    matches[str_cols] = matches[str_cols].apply(lambda c: c.str.strip())

    before = len(matches)
    matches.drop_duplicates(subset='MatchID', keep='first', inplace=True)
    log(f'  Duplicates removed: {before - len(matches)}')

    matches['Attendance'] = pd.to_numeric(matches['Attendance'], errors='coerce')
    matches['Attendance'] = matches.groupby('Year')['Attendance'].transform(
        lambda x: x.fillna(x.median())
    )

    matches['Half-time Home Goals'] = matches['Half-time Home Goals'].fillna(0).astype(int)
    matches['Half-time Away Goals'] = matches['Half-time Away Goals'].fillna(0).astype(int)

    def normalize_win_condition(val):
        if pd.isna(val) or str(val).strip() == '':
            return 'Normal'
        val = str(val).strip().lower()
        if 'penalty' in val or 'penalties' in val:
            return 'Penalties'
        if 'extra time' in val or 'aet' in val:
            return 'AET'
        return 'Normal'

    matches['Win_Conditions'] = matches['Win conditions'].apply(normalize_win_condition)
    matches.drop(columns=['Win conditions'], inplace=True)

    name_map = {'Germany FR': 'West Germany', 'Korea Republic': 'South Korea'}
    for col in ['Home Team Name', 'Away Team Name']:
        matches[col] = matches[col].replace(name_map)

    def get_result(row):
        if row['Home Team Goals'] > row['Away Team Goals']:
            return 'Home Win'
        elif row['Home Team Goals'] < row['Away Team Goals']:
            return 'Away Win'
        return 'Draw'

    matches['Match_Result']             = matches.apply(get_result, axis=1)
    matches['Total_Goals']              = matches['Home Team Goals'] + matches['Away Team Goals']
    matches['Second_Half_Home_Goals']   = matches['Home Team Goals'] - matches['Half-time Home Goals']
    matches['Second_Half_Away_Goals']   = matches['Away Team Goals'] - matches['Half-time Away Goals']

    stage_map = {
        'Group 1': 'Group Stage', 'Group 2': 'Group Stage', 'Group 3': 'Group Stage',
        'Group 4': 'Group Stage', 'Group 5': 'Group Stage', 'Group 6': 'Group Stage',
        'Group A': 'Group Stage', 'Group B': 'Group Stage', 'Group C': 'Group Stage',
        'Group D': 'Group Stage', 'Group E': 'Group Stage', 'Group F': 'Group Stage',
        'Group G': 'Group Stage', 'Group H': 'Group Stage',
        'First round': 'Group Stage', 'Preliminary round': 'Group Stage',
        'Quarter-finals': 'Quarter-Final', 'Semi-finals': 'Semi-Final',
        'Third place': 'Third Place', 'Final': 'Final',
        'Round of 16': 'Round of 16', 'Second round': 'Round of 16',
        'Play-off for third place': 'Third Place'
    }
    matches['Stage_Std'] = matches['Stage'].map(stage_map).fillna(matches['Stage'])

    matches.rename(columns={
        'Home Team Name':       'Home_Team',
        'Away Team Name':       'Away_Team',
        'Home Team Goals':      'Home_Goals',
        'Away Team Goals':      'Away_Goals',
        'Half-time Home Goals': 'HT_Home_Goals',
        'Half-time Away Goals': 'HT_Away_Goals',
        'Home Team Initials':   'Home_Initials',
        'Away Team Initials':   'Away_Initials',
    }, inplace=True)

    log(f'  WorldCupMatches cleaned: {matches.shape}')
    return matches


# ─── CLEAN PLAYERS ────────────────────────────────────────────────────────────

def parse_events(event_str):
    if pd.isna(event_str) or str(event_str).strip() == '':
        return 0, 0, 0, 0, 0
    goals   = len(re.findall(r'(?<!S)G\d+', event_str))
    yellows = len(re.findall(r'Y\d+', event_str))
    reds    = len(re.findall(r'R\d+|SY\d+', event_str))
    sub_in  = len(re.findall(r'I\d+', event_str))
    sub_out = len(re.findall(r'O\d+', event_str))
    return goals, yellows, reds, sub_in, sub_out


def clean_players(players_raw):
    log('Cleaning WorldCupPlayers...')
    players = players_raw.copy()

    str_cols = players.select_dtypes(include='object').columns
    players[str_cols] = players[str_cols].apply(lambda c: c.str.strip())

    players['Shirt Number'] = players['Shirt Number'].replace(0, np.nan)
    players['Is_Captain']   = (players['Position'] == 'C').astype(int)
    players['Position']     = players['Position'].replace({'C': np.nan})

    events_parsed = players['Event'].apply(parse_events)
    players[['Goals_Scored', 'Yellow_Cards', 'Red_Cards', 'Sub_In', 'Sub_Out']] = \
        pd.DataFrame(events_parsed.tolist(), index=players.index)

    players['Is_Substitute'] = (players['Line-up'] == 'N').astype(int)

    players.rename(columns={
        'Team Initials': 'Team_Initials',
        'Coach Name':    'Coach_Name',
        'Line-up':       'Lineup',
        'Shirt Number':  'Shirt_Number',
        'Player Name':   'Player_Name',
    }, inplace=True)

    log(f'  WorldCupPlayers cleaned: {players.shape}')
    return players


# ─── MERGE ────────────────────────────────────────────────────────────────────

def merge_datasets(cups, matches, players):
    log('Merging datasets...')
    master = players.merge(
        matches[['MatchID', 'Year', 'Stage', 'Stage_Std', 'Home_Team', 'Away_Team',
                 'Home_Goals', 'Away_Goals', 'Total_Goals', 'Attendance',
                 'HT_Home_Goals', 'HT_Away_Goals', 'Stadium', 'City',
                 'Win_Conditions', 'Match_Result', 'Home_Initials', 'Away_Initials',
                 'Second_Half_Home_Goals', 'Second_Half_Away_Goals']],
        on='MatchID', how='left'
    )
    master = master.merge(
        cups[['Year', 'Country', 'Winner', 'Total_Goals', 'Qualified_Teams', 'Matches_Played']].rename(
            columns={'Country': 'Host_Nation', 'Winner': 'Tournament_Winner',
                     'Total_Goals': 'Tournament_Goals'}
        ),
        on='Year', how='left'
    )
    log(f'  Master dataset: {master.shape}')
    return master


# ─── EXPORT ───────────────────────────────────────────────────────────────────

def export(cups, matches, master):
    log('Exporting processed files...')
    master.to_csv(os.path.join(PROCESSED_PATH, 'wc_master.csv'), index=False)
    matches.to_csv(os.path.join(PROCESSED_PATH, 'wc_matches_clean.csv'), index=False)
    cups.to_csv(os.path.join(PROCESSED_PATH, 'wc_cups_clean.csv'), index=False)
    for f in os.listdir(PROCESSED_PATH):
        if f.endswith('.csv'):
            rows = len(pd.read_csv(os.path.join(PROCESSED_PATH, f)))
            log(f'  {f}: {rows:,} rows')


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log('=== FIFA World Cup ETL Pipeline — SectionE_g11 ===')
    cups_raw, matches_raw, players_raw = extract()
    cups    = clean_cups(cups_raw)
    matches = clean_matches(matches_raw)
    players = clean_players(players_raw)
    master  = merge_datasets(cups, matches, players)
    export(cups, matches, master)
    log('Pipeline complete.')


if __name__ == '__main__':
    main()

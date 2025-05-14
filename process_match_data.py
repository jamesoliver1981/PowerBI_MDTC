import pandas as pd
import os
import argparse

def process_match_data(file_path, match_id, match_date_str,
                       core_stats_path='core_stats.csv',
                       match_info_path='match_info.csv'):

    # Read the raw CSV
    df = pd.read_csv(file_path)

    # Extract match-level slicer metadata (assume last 4 rows)
    metadata_rows = df.tail(4).copy()
    df = df.iloc[:-4]  # Remove those rows from main data

    # Create match_info from those slicers
    metadata = metadata_rows.set_index(df.columns[0])[df.columns[1]].to_dict()
    match_info = {
        'match_id': match_id,
        'match_date': pd.to_datetime(match_date_str),
        'match_surface': metadata.get('matchSurface'),
        'match_level': metadata.get('matchLevel'),
        'match_type': metadata.get('matchType'),
        'match_result': metadata.get('matchResult')
    }
    match_info['match_month'] = match_info['match_date'].month
    match_info['match_year'] = match_info['match_date'].year
    match_info_df = pd.DataFrame([match_info])

    # Melt data to long format
    df_long = pd.melt(df, id_vars=[df.columns[0], df.columns[1]],
                      var_name='MetricType', value_name='MetricValue')
    df_long.columns = ['MetricCategory', 'MetricSubcategory', 'MetricType', 'MetricValue']

    # ✅ Force MetricValue to be numeric
    df_long['MetricValue'] = pd.to_numeric(df_long['MetricValue'], errors='coerce')

    # Add concatenated label and match_id
    df_long['MetricLabel'] = df_long['MetricCategory'] + ' | ' + df_long['MetricSubcategory']
    df_long['match_id'] = match_id

    # Paths to backup folder
    backup_dir = 'backup'
    os.makedirs(backup_dir, exist_ok=True)

    # Append or create core_stats
    if os.path.exists(core_stats_path):
        # BACKUP before modifying
        core_stats_backup_path = os.path.join(backup_dir, 'core_stats_backup.csv')
        pd.read_csv(core_stats_path).to_csv(core_stats_backup_path, index=False)

        core_stats = pd.read_csv(core_stats_path)
        assert match_id not in core_stats['match_id'].unique(), f"match_id '{match_id}' already exists in core_stats!"
        core_stats = pd.concat([core_stats, df_long], ignore_index=True)
    else:
        core_stats = df_long

    # Append or create match_info
    if os.path.exists(match_info_path):
        match_info_backup_path = os.path.join(backup_dir, 'match_info_backup.csv')
        pd.read_csv(match_info_path).to_csv(match_info_backup_path, index=False)

        match_info_all = pd.read_csv(match_info_path, parse_dates=['match_date'])
        assert match_id not in match_info_all['match_id'].unique(), f"match_id '{match_id}' already exists in match_info!"
        match_info_all = pd.concat([match_info_all, match_info_df], ignore_index=True)
    else:
        match_info_all = match_info_df

    # ✅ Save with float formatting for consistency
    core_stats.to_csv(core_stats_path, index=False, float_format='%.2f')
    match_info_all.to_csv(match_info_path, index=False)

    print(f"[✓] Processed match '{match_id}' and updated datasets.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and append tennis match data.')
    parser.add_argument('--file', required=True, help='Path to input CSV file')
    parser.add_argument('--match_id', required=True, help='Unique match ID')
    parser.add_argument('--date', required=True, help='Match date in YYYY-MM-DD format')

    args = parser.parse_args()

    process_match_data(args.file, args.match_id, args.date)

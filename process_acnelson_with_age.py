"""
process_acnelson_with_age.py

Reads all Excel files in ./ACNelsonViewingRate, normalizes them and preserves age-group data.
Writes `ACNelson_normalized_with_age.csv` with both main rating and all age demographics.

Behavior & assumptions:
- Uses '4歲以上' as the main Rating column (total audience).
- Preserves all age-group columns for demographic analysis.
- Cleans program names by removing episode markers like '#12', '(...)', trailing
  punctuation and returns a cleaned series name in `Cleaned_Series_Name`.
- Uses existing time slot format from the data.
- Produces Chinese weekday labels: 一,二,三,四,五,六,日.
- Sorts results by date chronologically.

Output columns:
Date,Weekday,Time,Program,Program_Sheet,Time_Slot,Rating,Cleaned_Series_Name,[Age_Groups...]

Usage:
  python process_acnelson_with_age.py

This script uses pandas and openpyxl. Install via:
  pip install -r requirements.txt

"""
import re
from pathlib import Path
from datetime import datetime, timedelta
import sys
import warnings

import pandas as pd

ROOT = Path(__file__).resolve().parent
AC_DIR = ROOT / "ACNelsonViewingRate"
OUT_PATH = ROOT / "ACNelson_normalized_with_age.csv"

WEEKDAY_CN = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}

# Age group columns to preserve (based on the file structure we saw)
AGE_COLUMNS = [
    '4歲以上', '15-44歲', '4歲以上最高', '4歲以上女性', '4歲以上男性',
    '15-24歲', '15-24歲女性', '15-24歲男性', 
    '25-34歲', '25-34歲女性', '25-34歲男性',
    '35-44歲', '35-44歲女性', '35-44歲男性',
    '45-54歲', '45-54歲女性', '45-54歲男性',
    '55歲以上', '55歲以上女性', '55歲以上男性'
]


def cleaned_series_name(prog):
    if pd.isna(prog):
        return ""
    s = str(prog).strip()
    # remove episode markers like #12 or #12(完) or ##12
    s = re.sub(r"[#＃]{1,2}\s*\d+.*$", "", s)
    # remove parenthetical completion markers like (完)
    s = re.sub(r"（.*?）|\(.*?\)", "", s)
    # remove (第 X 集) patterns
    s = re.sub(r"\(第.*?集\)", "", s)
    # remove 首播 and (普) markers
    s = re.sub(r"首播|（普）|\(普\)", "", s)
    # trim trailing separators
    s = re.sub(r"[\-–—:：\s]+$", "", s)
    return s.strip()


def weekday_cn_from_date(d):
    if pd.isna(d):
        return ""
    if isinstance(d, str):
        # try parse common formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                dt = datetime.strptime(d.strip(), fmt)
                return WEEKDAY_CN[dt.weekday()]
            except Exception:
                continue
        try:
            dt = pd.to_datetime(d)
            return WEEKDAY_CN[dt.weekday()]
        except Exception:
            return ""
    if isinstance(d, (pd.Timestamp, datetime)):
        return WEEKDAY_CN[d.weekday()]
    return ""


def parse_time_from_slot(time_slot):
    """Extract start time from time slot like '00:00~01:00'"""
    if pd.isna(time_slot):
        return ""
    slot_str = str(time_slot).strip()
    # Extract the start time (before ~)
    if '~' in slot_str:
        start_time = slot_str.split('~')[0].strip()
        # Ensure it's in HH:MM:SS format
        if ':' in start_time and len(start_time.split(':')) == 2:
            start_time += ':00'
        return start_time
    return slot_str


def normalize_file(path: Path):
    out_rows = []
    try:
        xls = pd.read_excel(path, sheet_name=None, engine='openpyxl')
    except Exception as e:
        print(f"Failed to open {path.name}: {e}")
        return out_rows

    for sheet_name, df in xls.items():
        if df.empty:
            continue
        
        # Skip if this doesn't look like the main data sheet
        if '尼爾森各節目年齡層收視率' not in sheet_name:
            continue
            
        # drop completely empty columns
        df = df.loc[:, df.notna().any(axis=0)]

        # Column mapping based on the structure we saw
        date_col = '日期'
        time_col = '播出時間'  # This contains the time slot
        prog_col = '節目名稱'
        main_rating_col = '4歲以上'  # Use this as the main rating

        if date_col not in df.columns or prog_col not in df.columns:
            print(f"  Warning: Required columns not found in {sheet_name}")
            continue

        for idx, row in df.iterrows():
            date_val = row[date_col] if date_col in row.index else None
            time_slot_val = row[time_col] if time_col in row.index else None
            prog_val = row[prog_col] if prog_col in row.index else None

            # Skip rows with missing essential data
            if pd.isna(date_val) or pd.isna(prog_val):
                continue

            # Parse time from time slot
            time_val = parse_time_from_slot(time_slot_val)
            
            # Main rating (4歲以上)
            rating = row[main_rating_col] if main_rating_col in row.index else None

            # Clean program name
            cleaned = cleaned_series_name(prog_val)

            # Get weekday
            weekday_cn = weekday_cn_from_date(date_val)

            # Build base row
            row_data = {
                'Date': pd.to_datetime(date_val).date() if not pd.isna(date_val) else '',
                'Weekday': weekday_cn,
                'Time': time_val,
                'Program': prog_val if prog_val is not None else '',
                'Program_Sheet': f"{path.name}:{sheet_name}",
                'Time_Slot': time_slot_val if time_slot_val is not None else '',
                'Rating': float(rating) if pd.notna(rating) else 0.0,
                'Cleaned_Series_Name': cleaned,
            }
            
            # Add all age group columns
            for age_col in AGE_COLUMNS:
                if age_col in row.index:
                    age_val = row[age_col]
                    row_data[age_col] = float(age_val) if pd.notna(age_val) else 0.0
                else:
                    row_data[age_col] = 0.0

            out_rows.append(row_data)

    return out_rows


def main():
    files = sorted(AC_DIR.glob("*.xls*"))
    if not files:
        print("No ACNelson files found in:", AC_DIR)
        return

    all_rows = []
    for f in files:
        print(f"Processing {f.name}...")
        rows = normalize_file(f)
        print(f"  -> extracted {len(rows)} rows")
        all_rows.extend(rows)

    if not all_rows:
        print("No rows extracted.")
        return

    out_df = pd.DataFrame(all_rows)
    
    # Remove any rows with empty dates or programs
    out_df = out_df[out_df['Date'] != '']
    out_df = out_df[out_df['Program'] != '']

    # Convert Date column to datetime for proper sorting
    out_df['Date_for_sort'] = pd.to_datetime(out_df['Date'], errors='coerce')
    
    # Sort by date and time
    out_df = out_df.sort_values(['Date_for_sort', 'Time'], na_position='last')
    
    # Drop the temporary sorting column
    out_df = out_df.drop('Date_for_sort', axis=1)
    
    # Define column order
    base_cols = ['Date', 'Weekday', 'Time', 'Program', 'Program_Sheet', 'Time_Slot', 'Rating', 'Cleaned_Series_Name']
    all_cols = base_cols + AGE_COLUMNS
    
    # Ensure all columns exist
    for c in all_cols:
        if c not in out_df.columns:
            out_df[c] = ''

    out_df = out_df[all_cols]

    out_df.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
    print(f"Wrote normalized output with age data to: {OUT_PATH}")
    print(f"Total rows: {len(out_df)}")
    
    # Show date range
    dates = pd.to_datetime(out_df['Date'], errors='coerce').dropna()
    if len(dates) > 0:
        print(f"Date range: {dates.min().date()} to {dates.max().date()}")
    
    # print small preview
    print("\nFirst 5 rows:")
    print(out_df.head(5)[base_cols].to_string(index=False))
    
    # Show age column summary
    print(f"\nAge columns included: {', '.join(AGE_COLUMNS)}")


if __name__ == '__main__':
    main()

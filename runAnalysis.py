import pandas as pd
import datetime

def excel_to_date(excel_date):
    """處理 Excel 日期格式，並將 2023 年的日期調整為 2024 年"""
    try:
        date_result = None
        
        # 如果已經是 datetime 物件，直接返回日期部分
        if isinstance(excel_date, datetime.datetime):
            date_result = excel_date.date()
        # 如果是字串，嘗試解析
        elif isinstance(excel_date, str):
            if excel_date == '日期' or excel_date.strip() == '':
                return None
            date_result = pd.to_datetime(excel_date).date()
        # 如果是數字（Excel 序號），進行轉換
        elif isinstance(excel_date, (int, float)):
            converted = pd.to_datetime('1899-12-30') + pd.to_timedelta(int(excel_date), 'D')
            date_result = converted.date()
        else:
            return None
            
        # 如果是 2023 年的日期，自動調整為 2024 年
        if date_result and date_result.year == 2023:
            date_result = date_result.replace(year=2024)
            
        return date_result
    except:
        return None

def extract_program_schedule(excel_file_path):
    # 讀取 Excel 檔案的所有工作表
    xls = pd.ExcelFile(excel_file_path)
    all_data = []

    for sheet_name in xls.sheet_names:
        # 讀取單個工作表
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        # 提取日期行（row2）和星期行（row3）
        date_row = df.iloc[1]  # 日期
        weekday_row = df.iloc[2]  # 星期

        # 找到時間列（第一列）
        time_col = df.iloc[3:, 0].str.strip()  # 從 row4 開始，提取時間

        # 遍歷每一列（代表一天）
        for col_idx in range(1, df.shape[1]):
            # 檢查是否有日期
            date_value = date_row[col_idx]
            if pd.isna(date_value) or date_value == '日期':
                continue

            # 提取日期和星期
            date = excel_to_date(date_value)
            if date is None:  # 如果日期轉換失敗，跳過這一列
                continue
            weekday = weekday_row[col_idx] if pd.notna(weekday_row[col_idx]) else None

            # 提取該列的節目數據
            programs = df.iloc[3:, col_idx].str.strip()  # 從 row4 開始，提取節目名稱

            # 將時間和節目配對
            for time, program in zip(time_col, programs):
                if pd.notna(program):  # 只保留有節目名稱的記錄
                    all_data.append({
                        'Date': date,
                        'Weekday': weekday,
                        'Time': time,
                        'Program': program,
                        'Sheet': sheet_name
                    })

    # 轉換為 DataFrame
    result_df = pd.DataFrame(all_data)

    # 清理時間格式（確保一致性）
    result_df['Time'] = result_df['Time'].str.replace(r'\s+', '', regex=True)  # 移除多餘空格
    result_df['Time'] = pd.to_datetime(result_df['Time'], format='%H:%M', errors='coerce').dt.time

    # 按日期、時間排序
    result_df = result_df.sort_values(by=['Date', 'Time']).reset_index(drop=True)
    
    return result_df

# 使用範例
excel_file_path = '【愛爾達綜合台】2024年1~12月節目表.xlsx'
schedule_df = extract_program_schedule(excel_file_path)

# 儲存結果到 CSV（可選）
schedule_df.to_csv('program_schedule_extracted.csv', index=False, encoding='utf-8-sig')

# 顯示數據摘要
print("=== 節目表數據摘要 ===")
print(f"總記錄數: {len(schedule_df):,}")
print(f"日期範圍: {schedule_df['Date'].min()} 到 {schedule_df['Date'].max()}")

# 統計各年份的記錄數
schedule_df_copy = schedule_df.copy()
schedule_df_copy['Year'] = pd.to_datetime(schedule_df_copy['Date']).dt.year
year_counts = schedule_df_copy['Year'].value_counts().sort_index()
print("\n各年份的記錄數:")
for year, count in year_counts.items():
    print(f"  {year}年: {count:,} 筆")

# 顯示 2024 年的前 10 筆數據
print("\n=== 2024年節目表前10筆 ===")
df_2024 = schedule_df[pd.to_datetime(schedule_df['Date']).dt.year == 2024]
if len(df_2024) > 0:
    print(df_2024.head(10))
else:
    print("未找到2024年的數據")

# 顯示整體前10筆（包含所有年份）
print("\n=== 所有數據前10筆（按日期排序）===")
print(schedule_df.head(10))
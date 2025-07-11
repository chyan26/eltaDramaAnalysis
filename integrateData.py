import pandas as pd
import datetime
from datetime import time

def excel_to_date(excel_date):
    """處理 Excel 日期格式，並將非2024年的日期調整為2024年"""
    try:
        date_result = None
        
        if isinstance(excel_date, datetime.datetime):
            date_result = excel_date.date()
        elif isinstance(excel_date, str):
            if excel_date == '日期' or excel_date.strip() == '':
                return None
            date_result = pd.to_datetime(excel_date).date()
        elif isinstance(excel_date, (int, float)):
            converted = pd.to_datetime('1899-12-30') + pd.to_timedelta(int(excel_date), 'D')
            date_result = converted.date()
        else:
            return None
            
        # 將所有非2024年和2025年的日期調整為2024年（保持月日不變）
        if date_result and date_result.year not in [2024, 2025]:
            date_result = date_result.replace(year=2024)
            
        return date_result
    except:
        return None

def extract_ratings_data(ratings_file_path):
    """提取收視率資料"""
    xls = pd.ExcelFile(ratings_file_path)
    all_ratings = []
    
    for sheet_name in xls.sheet_names:
        if sheet_name == '月平均收視率':  # 跳過摘要表
            continue
            
        print(f"處理收視率工作表: {sheet_name}")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # 提取日期行（第1行）
        date_row = df.iloc[1, 1:]  # 跳過第一列
        
        # 提取時段列（從第5行開始）
        time_slots = df.iloc[5:, 0]  # 從付費用戶數後開始的時段
        
        # 遍歷每一列（代表一天）
        for col_idx in range(1, df.shape[1]):
            date_value = date_row.iloc[col_idx-1] if col_idx-1 < len(date_row) else None
            
            if pd.isna(date_value):
                continue
                
            date = excel_to_date(date_value)
            if date is None:
                continue
            
            # 提取該列的收視率數據（從第5行開始）
            ratings_col = df.iloc[5:, col_idx]
            
            # 將時段和收視率配對
            for time_slot, rating in zip(time_slots, ratings_col):
                if pd.notna(time_slot) and pd.notna(rating) and str(time_slot).startswith(('0', '1', '2')):
                    # 解析時段格式 "00:00~00:15" -> 開始時間 "00:00"
                    try:
                        start_time_str = str(time_slot).split('~')[0]
                        start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
                        
                        all_ratings.append({
                            'Date': date,
                            'Time_Slot': time_slot,
                            'Start_Time': start_time,
                            'Rating': float(rating),
                            'Sheet': sheet_name
                        })
                    except:
                        continue
    
    return pd.DataFrame(all_ratings)

def convert_program_time_to_slot(program_time):
    """將節目時間轉換為對應的15分鐘時段"""
    if pd.isna(program_time) or program_time is None:
        return None
        
    try:
        if isinstance(program_time, str):
            program_time = datetime.datetime.strptime(program_time, '%H:%M:%S').time()
        elif isinstance(program_time, datetime.time):
            pass
        else:
            return None
            
        # 將時間轉換為15分鐘時段的開始時間
        hour = program_time.hour
        minute = program_time.minute
        
        # 計算15分鐘時段
        slot_minute = (minute // 15) * 15
        slot_time = time(hour, slot_minute)
        
        return slot_time
    except:
        return None

def integrate_program_and_ratings(program_file, ratings_file):
    """整合節目表和收視率資料"""
    
    # 讀取節目表資料
    print("讀取節目表資料...")
    if program_file.endswith('.csv'):
        program_df = pd.read_csv(program_file)
        program_df['Date'] = pd.to_datetime(program_df['Date']).dt.date
        program_df['Time'] = pd.to_datetime(program_df['Time'], format='%H:%M:%S').dt.time
    else:
        # 從Excel重新提取節目表（使用之前的函數）
        print("從Excel重新提取節目表...")
        # 這裡可以調用之前的extract_program_schedule函數
        pass
    
    # 提取收視率資料
    print("提取收視率資料...")
    ratings_df = extract_ratings_data(ratings_file)
    
    # 為節目資料添加時段對應
    print("計算節目對應的收視時段...")
    program_df['Time_Slot_Start'] = program_df['Time'].apply(convert_program_time_to_slot)
    
    # 合併資料
    print("合併節目表和收視率資料...")
    merged_df = program_df.merge(
        ratings_df,
        left_on=['Date', 'Time_Slot_Start'],
        right_on=['Date', 'Start_Time'],
        how='left'
    )
    
    # 清理欄位
    merged_df = merged_df.drop(['Time_Slot_Start', 'Start_Time', 'Sheet_y'], axis=1, errors='ignore')
    merged_df = merged_df.rename(columns={'Sheet_x': 'Program_Sheet'})
    
    return merged_df

# 主程式
if __name__ == "__main__":
    program_file = 'program_schedule_extracted.csv'
    ratings_file = '2024年綜合台中華電信會員V1分時收視資料.xlsx'
    
    # 整合資料
    integrated_df = integrate_program_and_ratings(program_file, ratings_file)
    
    # 儲存結果
    integrated_df.to_csv('integrated_program_ratings.csv', index=False, encoding='utf-8-sig')
    
    # 顯示結果摘要
    print("\n=== 整合結果摘要 ===")
    print(f"總記錄數: {len(integrated_df):,}")
    print(f"有收視率資料的記錄: {integrated_df['Rating'].notna().sum():,}")
    print(f"缺失收視率資料的記錄: {integrated_df['Rating'].isna().sum():,}")
    
    # 顯示範例
    print("\n=== 整合資料範例（前10筆有收視率的記錄）===")
    sample_with_ratings = integrated_df[integrated_df['Rating'].notna()].head(10)
    print(sample_with_ratings[['Date', 'Time', 'Program', 'Rating', 'Time_Slot']])
    
    # 統計分析
    print("\n=== 收視率統計 ===")
    if integrated_df['Rating'].notna().sum() > 0:
        print(f"平均收視率: {integrated_df['Rating'].mean():.4f}")
        print(f"最高收視率: {integrated_df['Rating'].max():.4f}")
        print(f"最低收視率: {integrated_df['Rating'].min():.4f}")
        
        # 找出收視率最高的節目
        max_rating_idx = integrated_df['Rating'].idxmax()
        top_program = integrated_df.loc[max_rating_idx]
        print(f"\n收視率最高的節目:")
        print(f"  節目: {top_program['Program']}")
        print(f"  日期: {top_program['Date']}")
        print(f"  時間: {top_program['Time']}")
        print(f"  收視率: {top_program['Rating']:.4f}")

import pandas as pd
import re

def clean_program_names():
    """清理節目名稱，合併重複的系列"""
    
    # 讀取整合資料
    df = pd.read_csv('integrated_program_ratings.csv')
    
    def extract_and_clean_series_name(program_name):
        """提取並清理劇集名稱"""
        if pd.isna(program_name):
            return None
        
        # 去除集數 (#數字)
        series_name = re.sub(r'#\d+.*$', '', str(program_name))
        # 去除特殊符號
        series_name = re.sub(r'[()（）].*$', '', series_name)
        # 去除結尾的 # 符號
        series_name = re.sub(r'#$', '', series_name)
        series_name = series_name.strip()
        
        # 統一相同節目的不同命名格式
        if '蠟筆小新' in series_name:
            series_name = '蠟筆小新'
        
        # 可以在這裡添加更多的清理規則
        # 例如：
        # if '甄嬛傳' in series_name:
        #     series_name = '後宮甄嬛傳'
        
        return series_name
    
    # 應用清理函數
    df['Cleaned_Series_Name'] = df['Program'].apply(extract_and_clean_series_name)
    
    # 統計清理後的結果
    print("=== 節目名稱清理結果 ===")
    
    # 清理前的統計
    original_series = df['Program'].apply(lambda x: re.sub(r'#\d+.*$', '', str(x)).strip()).value_counts()
    print(f"清理前系列數量: {len(original_series)}")
    
    # 清理後的統計
    cleaned_series = df['Cleaned_Series_Name'].value_counts()
    print(f"清理後系列數量: {len(cleaned_series)}")
    
    print(f"合併了 {len(original_series) - len(cleaned_series)} 個重複系列")
    
    # 顯示主要系列的統計
    print("\n清理後的主要系列 (集數>=20):")
    major_series = cleaned_series[cleaned_series >= 20].head(10)
    for series, count in major_series.items():
        avg_rating = df[df['Cleaned_Series_Name'] == series]['Rating'].mean()
        print(f"{series:<20} 集數:{count:4d} 平均收視率:{avg_rating:.4f}")
    
    # 保存清理後的資料
    df.to_csv('integrated_program_ratings_cleaned.csv', index=False, encoding='utf-8-sig')
    print("\n清理後的資料已保存為 'integrated_program_ratings_cleaned.csv'")
    
    return df

if __name__ == "__main__":
    clean_df = clean_program_names()

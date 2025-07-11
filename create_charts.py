
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re

# 設定中文字體和圖表風格
plt.rcParams['font.sans-serif'] = ['Heiti TC']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

def create_visualizations():
    """創建收視率分析視覺化圖表"""
    
    # 讀取清理後的資料
    df = pd.read_csv('integrated_program_ratings_cleaned.csv')
    df = df[df['Rating'].notna()]
    df['Date'] = pd.to_datetime(df['Date'])
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    
    # 創建圖表
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('愛爾達綜合台收視率分析', fontsize=16, fontweight='bold')
    
    # 1. 時段收視率分析
    hourly_ratings = df.groupby('Hour')['Rating'].mean()
    axes[0, 0].bar(hourly_ratings.index, hourly_ratings.values, color='skyblue', alpha=0.8)
    axes[0, 0].set_title('各時段平均收視率')
    axes[0, 0].set_xlabel('時段')
    axes[0, 0].set_ylabel('平均收視率')
    axes[0, 0].set_xticks(range(0, 24, 2))
    
    # 2. 月份收視率趨勢
    monthly_ratings = df.groupby(df['Date'].dt.month)['Rating'].mean()
    axes[0, 1].plot(monthly_ratings.index, monthly_ratings.values, marker='o', linewidth=2, markersize=6)
    axes[0, 1].set_title('月份收視率趨勢')
    axes[0, 1].set_xlabel('月份')
    axes[0, 1].set_ylabel('平均收視率')
    axes[0, 1].set_xticks(range(1, 13))
    
    # 3. 主要劇集收視率比較
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 30].head(8)
    series_ratings = []
    series_names = []
    
    for series in major_series.index:
        avg_rating = df[df['Cleaned_Series_Name'] == series]['Rating'].mean()
        series_ratings.append(avg_rating)
        series_names.append(series[:10] + '...' if len(series) > 10 else series)
    
    axes[1, 0].barh(series_names, series_ratings, color='lightcoral', alpha=0.8)
    axes[1, 0].set_title('主要劇集平均收視率')
    axes[1, 0].set_xlabel('平均收視率')
    
    # 4. 收視率分布
    axes[1, 1].hist(df['Rating'], bins=30, color='lightgreen', alpha=0.7, edgecolor='black')
    axes[1, 1].set_title('收視率分布')
    axes[1, 1].set_xlabel('收視率')
    axes[1, 1].set_ylabel('節目數量')
    
    plt.tight_layout()
    plt.savefig('ratings_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("視覺化圖表已保存為 'ratings_analysis.png'")

if __name__ == "__main__":
    create_visualizations()

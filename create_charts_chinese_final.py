import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.font_manager as fm

def setup_chinese_font():
    """設定中文字體，使用黑體"""
    # 設定中文字體為黑體
    plt.rcParams['font.sans-serif'] = ['Heiti TC']
    plt.rcParams['axes.unicode_minus'] = False
    print("✓ 使用黑體字型")
    return True

def create_visualizations_chinese():
    """創建中文版收視率分析圖表"""
    
    # 設定字體
    chinese_font_ok = setup_chinese_font()
    sns.set_style("whitegrid")
    
    print("正在讀取資料...")
    # 讀取清理後的資料
    df = pd.read_csv('integrated_program_ratings_cleaned.csv')
    df = df[df['Rating'].notna()]
    df['Date'] = pd.to_datetime(df['Date'])
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    
    print("正在創建圖表...")
    # 創建圖表 - 增大尺寸以便更好顯示中文
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    
    # 設定主標題
    if chinese_font_ok:
        fig.suptitle('愛爾達綜合台收視率分析儀表板', fontsize=20, fontweight='bold', y=0.98)
    else:
        fig.suptitle('Elta TV Rating Analysis Dashboard', fontsize=20, fontweight='bold', y=0.98)
    
    # 1. 時段收視率分析
    print("  生成時段分析圖...")
    hourly_ratings = df.groupby('Hour')['Rating'].mean()
    bars = axes[0, 0].bar(hourly_ratings.index, hourly_ratings.values, 
                         color='skyblue', alpha=0.8, edgecolor='navy', linewidth=0.8)
    
    if chinese_font_ok:
        axes[0, 0].set_title('各時段平均收視率', fontsize=16, pad=20)
        axes[0, 0].set_xlabel('時段 (小時)', fontsize=14)
        axes[0, 0].set_ylabel('平均收視率', fontsize=14)
    else:
        axes[0, 0].set_title('Average Rating by Hour', fontsize=16, pad=20)
        axes[0, 0].set_xlabel('Hour of Day', fontsize=14)
        axes[0, 0].set_ylabel('Average Rating', fontsize=14)
    
    axes[0, 0].set_xticks(range(0, 24, 2))
    axes[0, 0].grid(True, alpha=0.3)
    
    # 添加數值標籤
    for bar in bars:
        height = bar.get_height()
        if height > 0.15:
            axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + 0.005,
                           f'{height:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 2. 月份收視率趨勢
    print("  生成月份趨勢圖...")
    monthly_ratings = df.groupby(df['Date'].dt.month)['Rating'].mean()
    line = axes[0, 1].plot(monthly_ratings.index, monthly_ratings.values, 
                          marker='o', linewidth=3, markersize=10, color='darkgreen')
    
    if chinese_font_ok:
        axes[0, 1].set_title('月份收視率趨勢', fontsize=16, pad=20)
        axes[0, 1].set_xlabel('月份', fontsize=14)
        axes[0, 1].set_ylabel('平均收視率', fontsize=14)
    else:
        axes[0, 1].set_title('Monthly Rating Trends', fontsize=16, pad=20)
        axes[0, 1].set_xlabel('Month', fontsize=14)
        axes[0, 1].set_ylabel('Average Rating', fontsize=14)
    
    axes[0, 1].set_xticks(range(1, 13))
    axes[0, 1].grid(True, alpha=0.3)
    
    # 添加數值標籤
    for i, v in enumerate(monthly_ratings.values):
        axes[0, 1].text(i+1, v + 0.002, f'{v:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 3. 主要劇集收視率比較
    print("  生成劇集比較圖...")
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 100].head(6)  # 調整為100集以上，顯示前6名
    series_ratings = []
    series_names = []
    
    for series in major_series.index:
        avg_rating = df[df['Cleaned_Series_Name'] == series]['Rating'].mean()
        series_ratings.append(avg_rating)
        # 縮短名稱以便顯示
        short_name = series if len(series) <= 6 else series[:6] + '..'
        series_names.append(short_name)
    
    bars = axes[1, 0].barh(series_names, series_ratings, 
                          color='lightcoral', alpha=0.8, edgecolor='darkred', linewidth=0.8)
    
    if chinese_font_ok:
        axes[1, 0].set_title('主要劇集平均收視率', fontsize=16, pad=20)
        axes[1, 0].set_xlabel('平均收視率', fontsize=14)
    else:
        axes[1, 0].set_title('Top Series Average Ratings', fontsize=16, pad=20)
        axes[1, 0].set_xlabel('Average Rating', fontsize=14)
    
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # 添加數值標籤
    for i, bar in enumerate(bars):
        width = bar.get_width()
        axes[1, 0].text(width + 0.005, bar.get_y() + bar.get_height()/2,
                       f'{width:.3f}', ha='left', va='center', fontsize=11)
    
    # 4. 收視率分布
    print("  生成收視率分布圖...")
    n, bins, patches = axes[1, 1].hist(df['Rating'], bins=30, color='lightgreen', 
                                      alpha=0.7, edgecolor='darkgreen', linewidth=0.8)
    
    if chinese_font_ok:
        axes[1, 1].set_title('收視率分布', fontsize=16, pad=20)
        axes[1, 1].set_xlabel('收視率', fontsize=14)
        axes[1, 1].set_ylabel('節目數量', fontsize=14)
    else:
        axes[1, 1].set_title('Rating Distribution', fontsize=16, pad=20)
        axes[1, 1].set_xlabel('Rating', fontsize=14)
        axes[1, 1].set_ylabel('Number of Programs', fontsize=14)
    
    axes[1, 1].grid(True, alpha=0.3)
    
    # 添加統計資訊
    mean_rating = df['Rating'].mean()
    max_rating = df['Rating'].max()
    axes[1, 1].axvline(mean_rating, color='red', linestyle='--', alpha=0.8, linewidth=2)
    
    if chinese_font_ok:
        stats_text = f'平均值: {mean_rating:.3f}\\n最大值: {max_rating:.3f}'
    else:
        stats_text = f'Mean: {mean_rating:.3f}\\nMax: {max_rating:.3f}'
    
    axes[1, 1].text(0.7, 0.9, stats_text, transform=axes[1, 1].transAxes, 
                   fontsize=12, bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # 調整佈局
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    
    # 保存圖表
    print("正在保存圖表...")
    filename = 'ratings_analysis_chinese_final.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # 顯示圖表
    plt.show()
    
    print(f"✓ 視覺化圖表已保存為 '{filename}'")
    
    # 輸出統計資訊
    print("\\n圖表統計資訊:")
    print(f"- 總節目數: {len(df):,}")
    print(f"- 平均收視率: {df['Rating'].mean():.4f}")
    print(f"- 最高收視率: {df['Rating'].max():.4f}")
    print(f"- 主要劇集數: {len(major_series)}")
    print(f"- 黃金時段(20-22點)平均收視率: {df[df['Hour'].between(20, 22)]['Rating'].mean():.4f}")
    
    # 輸出主要劇集資訊
    print(f"\\n主要劇集收視率排名:")
    for i, (series, rating) in enumerate(zip(series_names, series_ratings), 1):
        print(f"  {i}. {series}: {rating:.4f}")

if __name__ == "__main__":
    create_visualizations_chinese()

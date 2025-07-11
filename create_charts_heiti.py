import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.font_manager as fm

# 明確設定字體 - 使用多個黑體備選
def setup_font():
    """設定字體，確保中文顯示正常"""
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Heiti TC', 'STHeiti', 'SimHei', 'Microsoft JhengHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 清除字體快取
    plt.rcParams.update(plt.rcParamsDefault)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Heiti TC', 'STHeiti', 'SimHei', 'Microsoft JhengHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    print("✓ 字體設定完成：黑體系列")

def create_charts():
    """創建收視率分析圖表"""
    
    # 設定字體
    setup_font()
    sns.set_style("whitegrid")
    
    print("正在讀取資料...")
    # 讀取清理後的資料
    df = pd.read_csv('integrated_program_ratings_cleaned.csv')
    df = df[df['Rating'].notna()]
    df['Date'] = pd.to_datetime(df['Date'])
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    
    print("正在創建圖表...")
    # 創建圖表
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 設定主標題 - 直接指定字體
    fig.suptitle('愛爾達綜合台收視率分析儀表板', 
                fontsize=18, fontweight='bold', y=0.98,
                fontproperties='Heiti TC')
    
    # 1. 時段收視率分析
    print("  生成時段分析圖...")
    hourly_ratings = df.groupby('Hour')['Rating'].mean()
    bars = axes[0, 0].bar(hourly_ratings.index, hourly_ratings.values, 
                         color='skyblue', alpha=0.8, edgecolor='navy', linewidth=0.8)
    
    axes[0, 0].set_title('各時段平均收視率', fontsize=14, fontweight='bold', 
                        fontproperties='Heiti TC')
    axes[0, 0].set_xlabel('時間(小時)', fontproperties='Heiti TC')
    axes[0, 0].set_ylabel('平均收視率', fontproperties='Heiti TC')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 標註最高收視率時段
    max_hour = hourly_ratings.idxmax()
    max_rating = hourly_ratings.max()
    axes[0, 0].annotate(f'最高: {max_rating:.3f}\n({max_hour}:00)', 
                       xy=(max_hour, max_rating), xytext=(max_hour+2, max_rating+0.02),
                       arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                       fontsize=10, ha='center', color='red',
                       fontproperties='Heiti TC')
    
    # 2. 月份趨勢分析
    print("  生成月份趨勢圖...")
    df['Month'] = df['Date'].dt.month
    monthly_ratings = df.groupby('Month')['Rating'].agg(['mean', 'std']).reset_index()
    
    line = axes[0, 1].plot(monthly_ratings['Month'], monthly_ratings['mean'], 
                          marker='o', linewidth=2.5, markersize=8, color='forestgreen')
    axes[0, 1].fill_between(monthly_ratings['Month'], 
                           monthly_ratings['mean'] - monthly_ratings['std'],
                           monthly_ratings['mean'] + monthly_ratings['std'],
                           alpha=0.2, color='forestgreen')
    
    axes[0, 1].set_title('月份收視率趨勢', fontsize=14, fontweight='bold',
                        fontproperties='Heiti TC')
    axes[0, 1].set_xlabel('月份', fontproperties='Heiti TC')
    axes[0, 1].set_ylabel('平均收視率', fontproperties='Heiti TC')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xticks(range(1, 13))
    
    # 3. 主要劇集比較
    print("  生成劇集比較圖...")
    series_ratings = df.groupby('Cleaned_Series_Name')['Rating'].agg(['mean', 'count']).reset_index()
    series_ratings = series_ratings[series_ratings['count'] >= 50].sort_values('mean', ascending=True)
    
    if len(series_ratings) > 8:
        series_ratings = series_ratings.tail(8)
    
    bars = axes[1, 0].barh(range(len(series_ratings)), series_ratings['mean'], 
                          color=plt.cm.viridis(np.linspace(0, 1, len(series_ratings))),
                          alpha=0.8, edgecolor='black', linewidth=0.5)
    
    axes[1, 0].set_yticks(range(len(series_ratings)))
    axes[1, 0].set_yticklabels(series_ratings['Cleaned_Series_Name'], 
                              fontproperties='Heiti TC')
    axes[1, 0].set_title('主要劇集平均收視率比較', fontsize=14, fontweight='bold',
                        fontproperties='Heiti TC')
    axes[1, 0].set_xlabel('平均收視率', fontproperties='Heiti TC')
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # 添加數值標籤
    for i, (idx, row) in enumerate(series_ratings.iterrows()):
        axes[1, 0].text(row['mean'] + 0.005, i, f'{row["mean"]:.3f}', 
                       va='center', fontsize=9, fontproperties='Heiti TC')
    
    # 4. 收視率分布
    print("  生成收視率分布圖...")
    axes[1, 1].hist(df['Rating'], bins=50, alpha=0.7, color='coral', 
                   edgecolor='darkred', linewidth=0.8, density=True)
    
    # 添加統計線
    mean_rating = df['Rating'].mean()
    median_rating = df['Rating'].median()
    
    axes[1, 1].axvline(mean_rating, color='blue', linestyle='--', linewidth=2, 
                      label=f'平均值: {mean_rating:.3f}')
    axes[1, 1].axvline(median_rating, color='green', linestyle='--', linewidth=2, 
                      label=f'中位數: {median_rating:.3f}')
    
    axes[1, 1].set_title('收視率分布', fontsize=14, fontweight='bold',
                        fontproperties='Heiti TC')
    axes[1, 1].set_xlabel('收視率', fontproperties='Heiti TC')
    axes[1, 1].set_ylabel('密度', fontproperties='Heiti TC')
    axes[1, 1].legend(prop=fm.FontProperties(fname=None, family=['Heiti TC']))
    axes[1, 1].grid(True, alpha=0.3)
    
    # 調整布局
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    
    # 保存圖表
    filename = 'ratings_analysis_heiti.png'
    print("正在保存圖表...")
    plt.savefig(filename, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    
    print(f"✓ 圖表已保存為 '{filename}'")
    
    # 顯示圖表
    plt.show()
    
    # 統計資訊
    print(f"\n圖表統計資訊:")
    print(f"- 總節目數: {len(df):,}")
    print(f"- 平均收視率: {df['Rating'].mean():.4f}")
    print(f"- 最高收視率: {df['Rating'].max():.4f}")
    print(f"- 主要劇集數: {len(series_ratings)}")
    
    # 黃金時段統計
    golden_time = df[df['Hour'].between(20, 22)]
    print(f"- 黃金時段(20-22點)平均收視率: {golden_time['Rating'].mean():.4f}")
    
    # 劇集排名
    print(f"\n主要劇集收視率排名:")
    for i, (idx, row) in enumerate(series_ratings.sort_values('mean', ascending=False).iterrows(), 1):
        series_name = row['Cleaned_Series_Name']
        if len(series_name) > 8:
            series_name = series_name[:8] + ".."
        print(f"  {i}. {series_name}: {row['mean']:.4f}")

if __name__ == "__main__":
    create_charts()

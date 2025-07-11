import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import re

# 設定中文字體 - 使用黑體
plt.rcParams['font.sans-serif'] = ['Heiti TC']
plt.rcParams['axes.unicode_minus'] = False

def analyze_drama_ratings():
    """分析整部劇的收視率變化和主要收視時段"""
    
    # 讀取清理後的整合資料
    df = pd.read_csv('integrated_program_ratings_cleaned.csv')
    df = df[df['Rating'].notna()]  # 只取有收視率的資料
    df['Date'] = pd.to_datetime(df['Date'])
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    
    print("=== 整部劇收視率變化分析 (使用清理後資料) ===\n")
    
    # 2. 找出主要劇集（集數較多的）
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 20].head(10)  # 至少20集的前10部劇
    
    print("1. 主要劇集統計 (集數>=20)")
    print("=" * 50)
    for series, count in major_series.items():
        avg_rating = df[df['Cleaned_Series_Name'] == series]['Rating'].mean()
        max_rating = df[df['Cleaned_Series_Name'] == series]['Rating'].max()
        print(f"{series:<20} 集數:{count:3d} 平均:{avg_rating:.4f} 最高:{max_rating:.4f}")
    
    # 3. 分析每部主要劇集的收視率變化
    print("\n2. 主要劇集收視率趨勢分析")
    print("=" * 50)
    
    for series_name in major_series.head(5).index:  # 分析前5部劇
        series_data = df[df['Cleaned_Series_Name'] == series_name].copy()
        
        # 提取集數
        def extract_episode_number(program_name):
            match = re.search(r'#(\d+)', str(program_name))
            return int(match.group(1)) if match else None
        
        series_data['Episode'] = series_data['Program'].apply(extract_episode_number)
        series_data = series_data[series_data['Episode'].notna()]
        
        if len(series_data) > 0:
            # 按集數分組計算平均收視率
            episode_ratings = series_data.groupby('Episode')['Rating'].mean().sort_index()
            
            print(f"\n{series_name}:")
            print(f"  總集數: {len(episode_ratings)}")
            print(f"  首集收視率: {episode_ratings.iloc[0]:.4f}")
            print(f"  最終集收視率: {episode_ratings.iloc[-1]:.4f}")
            print(f"  平均收視率: {episode_ratings.mean():.4f}")
            print(f"  收視率標準差: {episode_ratings.std():.4f}")
            
            # 找出收視率最高和最低的集數
            max_ep = episode_ratings.idxmax()
            min_ep = episode_ratings.idxmin()
            print(f"  收視率最高: 第{max_ep}集 ({episode_ratings.max():.4f})")
            print(f"  收視率最低: 第{min_ep}集 ({episode_ratings.min():.4f})")
            
            # 計算趨勢
            if len(episode_ratings) >= 5:
                correlation = np.corrcoef(episode_ratings.index, episode_ratings.values)[0, 1]
                trend = "上升" if correlation > 0.1 else "下降" if correlation < -0.1 else "平穩"
                print(f"  整體趨勢: {trend} (相關係數: {correlation:.3f})")
    
    # 4. 主要收視時段分析
    print("\n3. 主要收視時段分析")
    print("=" * 50)
    
    # 按小時統計收視率
    hourly_stats = df.groupby('Hour')['Rating'].agg(['mean', 'count', 'std', 'max']).round(4)
    hourly_stats = hourly_stats.sort_values('mean', ascending=False)
    
    print("時段  平均收視率  節目數量  標準差    最高收視率")
    print("-" * 50)
    for hour, row in hourly_stats.head(15).iterrows():
        print(f"{hour:2d}時  {row['mean']:8.4f}  {row['count']:6.0f}  {row['std']:6.4f}  {row['max']:8.4f}")
    
    # 5. 黃金時段詳細分析
    print("\n4. 黃金時段詳細分析 (18-22點)")
    print("=" * 50)
    
    prime_time = df[df['Hour'].between(18, 22)]
    prime_hourly = prime_time.groupby('Hour')['Rating'].agg(['mean', 'count']).round(4)
    
    for hour, row in prime_hourly.iterrows():
        top_programs = prime_time[prime_time['Hour'] == hour].nlargest(3, 'Rating')
        print(f"\n{hour}點 (平均收視率: {row['mean']:.4f}, 節目數: {row['count']:.0f})")
        print("  收視率前3名:")
        for idx, (_, program) in enumerate(top_programs.iterrows(), 1):
            print(f"    {idx}. {program['Program']:<25} {program['Rating']:.4f} ({program['Date'].strftime('%m/%d')})")
    
    # 6. 週末 vs 平日收視率比較
    print("\n5. 週末 vs 平日收視率比較")
    print("=" * 50)
    
    df['Is_Weekend'] = df['Date'].dt.dayofweek.isin([5, 6])  # 週六、週日
    
    weekend_stats = df[df['Is_Weekend']]['Rating'].describe()
    weekday_stats = df[~df['Is_Weekend']]['Rating'].describe()
    
    print("統計項目     週末      平日      差異")
    print("-" * 40)
    print(f"平均值    {weekend_stats['mean']:.4f}  {weekday_stats['mean']:.4f}  {weekend_stats['mean']-weekday_stats['mean']:+.4f}")
    print(f"最大值    {weekend_stats['max']:.4f}  {weekday_stats['max']:.4f}  {weekend_stats['max']-weekday_stats['max']:+.4f}")
    print(f"標準差    {weekend_stats['std']:.4f}  {weekday_stats['std']:.4f}  {weekend_stats['std']-weekday_stats['std']:+.4f}")
    
    # 7. 月份趨勢分析
    print("\n6. 月份收視率趨勢")
    print("=" * 50)
    
    monthly_ratings = df.groupby(df['Date'].dt.month)['Rating'].agg(['mean', 'count', 'max']).round(4)
    
    print("月份  平均收視率  節目數量  最高收視率")
    print("-" * 40)
    for month, row in monthly_ratings.iterrows():
        print(f"{month:2d}月  {row['mean']:8.4f}  {row['count']:6.0f}  {row['max']:8.4f}")
    
    # 8. 收視率分布區間分析
    print("\n7. 收視率分布區間分析")
    print("=" * 50)
    
    bins = [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0]
    labels = ['<0.05', '0.05-0.1', '0.1-0.15', '0.15-0.2', '0.2-0.3', '0.3-0.5', '≥0.5']
    df['Rating_Range'] = pd.cut(df['Rating'], bins=bins, labels=labels, include_lowest=True)
    
    rating_dist = df['Rating_Range'].value_counts().sort_index()
    
    print("收視率區間    節目數量    百分比")
    print("-" * 35)
    for range_label, count in rating_dist.items():
        percentage = count / len(df) * 100
        print(f"{range_label:<12}  {count:6d}    {percentage:5.1f}%")
    
    # 9. 特殊發現和建議
    print("\n8. 特殊發現和建議")
    print("=" * 50)
    
    # 找出收視率突破0.5的節目
    high_rating_programs = df[df['Rating'] >= 0.5]
    if len(high_rating_programs) > 0:
        print(f"✓ 收視率突破0.5的節目共 {len(high_rating_programs)} 筆")
        top_series = high_rating_programs['Cleaned_Series_Name'].value_counts().head(3)
        print("  表現最好的劇集:")
        for series, count in top_series.items():
            avg_rating = high_rating_programs[high_rating_programs['Cleaned_Series_Name'] == series]['Rating'].mean()
            print(f"    {series}: {count}集突破0.5 (平均{avg_rating:.4f})")
    
    # 最佳播出時段
    best_hour = hourly_stats.index[0]
    best_rating = hourly_stats.iloc[0]['mean']
    print(f"\n✓ 最佳播出時段: {best_hour}點 (平均收視率 {best_rating:.4f})")
    
    # 收視率增長最快的劇集
    growth_analysis = {}
    for series_name in major_series.head(5).index:
        series_data = df[df['Cleaned_Series_Name'] == series_name].copy()
        series_data['Episode'] = series_data['Program'].apply(lambda x: re.search(r'#(\d+)', str(x)).group(1) if re.search(r'#(\d+)', str(x)) else None)
        series_data = series_data[series_data['Episode'].notna()]
        
        if len(series_data) >= 10:  # 至少10集
            episode_ratings = series_data.groupby('Episode')['Rating'].mean().sort_index()
            first_half = episode_ratings.iloc[:len(episode_ratings)//2].mean()
            second_half = episode_ratings.iloc[len(episode_ratings)//2:].mean()
            growth = (second_half - first_half) / first_half * 100
            growth_analysis[series_name] = growth
    
    if growth_analysis:
        best_growth = max(growth_analysis, key=growth_analysis.get)
        print(f"\n✓ 收視率增長最佳劇集: {best_growth} (增長 {growth_analysis[best_growth]:+.1f}%)")
    
    return df

def create_visualization_script():
    """創建視覺化腳本"""
    script_content = '''
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
'''
    
    with open('create_charts.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("\n視覺化腳本已創建為 'create_charts.py'")
    print("執行 'python create_charts.py' 來生成圖表")

if __name__ == "__main__":
    df = analyze_drama_ratings()
    create_visualization_script()

"""
drama_age_analysis.py

基於ACNelson年齡分層收視資料進行深度人口統計分析。
分析不同年齡群組對各劇集的收視偏好、時段分布和趨勢變化。

功能包含：
1. 各年齡層收視率統計分析
2. 劇集的年齡群組偏好分析
3. 不同時段的年齡分布
4. 性別差異分析
5. 年齡層收視趨勢分析
6. 生成視覺化圖表

使用方法：
  python drama_age_analysis.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.font_manager as fm
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

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
    plt.rcParams['font.size'] = 10
    
    print("✓ 字體設定完成：黑體系列")

sns.set_style("whitegrid")

# 定義年齡分組
AGE_GROUPS = {
    '總體': ['4歲以上'],
    '核心觀眾': ['15-44歲'],
    '年輕族群': ['15-24歲'],
    '青壯年': ['25-34歲'],
    '中年': ['35-44歲'],
    '熟齡': ['45-54歲'],
    '銀髮族': ['55歲以上']
}

GENDER_GROUPS = {
    '總體男性': '4歲以上男性',
    '總體女性': '4歲以上女性',
    '年輕男性': '15-24歲男性',
    '年輕女性': '15-24歲女性',
    '青壯年男性': '25-34歲男性',
    '青壯年女性': '25-34歲女性',
    '中年男性': '35-44歲男性',
    '中年女性': '35-44歲女性',
    '熟齡男性': '45-54歲男性',
    '熟齡女性': '45-54歲女性',
    '銀髮男性': '55歲以上男性',
    '銀髮女性': '55歲以上女性'
}

def load_and_prepare_data():
    """載入並準備分析資料"""
    print("正在載入ACNelson年齡分層收視資料...")
    
    df = pd.read_csv('ACNelson_normalized_with_age.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    df['Month'] = df['Date'].dt.month
    df['Weekday_Num'] = df['Date'].dt.dayofweek
    df['Is_Weekend'] = df['Weekday_Num'].isin([5, 6])
    
    # 過濾掉無效資料
    df = df[df['Rating'] > 0]
    
    print(f"✓ 載入完成: {len(df):,} 筆有效資料")
    print(f"  時間範圍: {df['Date'].min().date()} 至 {df['Date'].max().date()}")
    print(f"  包含劇集: {df['Cleaned_Series_Name'].nunique()} 部")
    
    return df

def analyze_age_group_preferences():
    """分析各年齡層收視偏好"""
    print("\n" + "="*60)
    print("1. 各年齡層收視偏好分析")
    print("="*60)
    
    df = load_and_prepare_data()
    
    # 計算各年齡層的平均收視率
    age_stats = {}
    for group_name, columns in AGE_GROUPS.items():
        if columns[0] in df.columns:
            age_stats[group_name] = df[columns[0]].mean()
    
    print("\n各年齡層整體平均收視率:")
    print("-" * 40)
    for group, rating in sorted(age_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{group:<10} {rating:.4f}")
    
    # 分析主要劇集的年齡偏好
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 50].head(10)
    
    print(f"\n主要劇集年齡層偏好分析 (>=50集的前10部劇):")
    print("=" * 80)
    
    age_preference_data = []
    
    for series_name in major_series.index:
        series_data = df[df['Cleaned_Series_Name'] == series_name]
        
        print(f"\n{series_name} (共{len(series_data)}集):")
        print("-" * 50)
        
        # 計算各年齡層收視率
        series_age_stats = {}
        for group_name, columns in AGE_GROUPS.items():
            if columns[0] in series_data.columns:
                avg_rating = series_data[columns[0]].mean()
                series_age_stats[group_name] = avg_rating
                print(f"  {group_name:<10} {avg_rating:.4f}")
        
        # 找出主要觀眾群
        if series_age_stats:
            max_group = max(series_age_stats, key=series_age_stats.get)
            max_rating = series_age_stats[max_group]
            print(f"  → 主要觀眾群: {max_group} ({max_rating:.4f})")
            
            # 儲存資料供視覺化使用
            for group, rating in series_age_stats.items():
                age_preference_data.append({
                    'Series': series_name[:10] + '...' if len(series_name) > 10 else series_name,
                    'Age_Group': group,
                    'Rating': rating
                })
    
    return pd.DataFrame(age_preference_data)

def analyze_time_slot_demographics():
    """分析不同時段的年齡分布"""
    print("\n" + "="*60)
    print("2. 時段年齡分布分析")
    print("="*60)
    
    df = load_and_prepare_data()
    
    # 定義時段
    time_slots = {
        '凌晨': (0, 5),
        '早晨': (6, 11),
        '午間': (12, 17),
        '黃金': (18, 22),
        '深夜': (23, 23)
    }
    
    print("\n各時段年齡層收視率分析:")
    print("=" * 80)
    
    time_age_data = []
    
    for slot_name, (start_hour, end_hour) in time_slots.items():
        slot_data = df[df['Hour'].between(start_hour, end_hour)]
        
        if len(slot_data) > 0:
            print(f"\n{slot_name}時段 ({start_hour}-{end_hour}點, {len(slot_data):,}筆資料):")
            print("-" * 40)
            
            # 計算各年齡層收視率
            for group_name, columns in AGE_GROUPS.items():
                if columns[0] in slot_data.columns:
                    avg_rating = slot_data[columns[0]].mean()
                    print(f"  {group_name:<10} {avg_rating:.4f}")
                    
                    time_age_data.append({
                        'Time_Slot': slot_name,
                        'Age_Group': group_name,
                        'Rating': avg_rating
                    })
    
    # 找出各年齡層最佳時段
    print("\n各年齡層最佳收視時段:")
    print("-" * 40)
    
    time_age_df = pd.DataFrame(time_age_data)
    for group in AGE_GROUPS.keys():
        group_data = time_age_df[time_age_df['Age_Group'] == group]
        if len(group_data) > 0:
            best_slot = group_data.loc[group_data['Rating'].idxmax()]
            print(f"{group:<10} → {best_slot['Time_Slot']}時段 ({best_slot['Rating']:.4f})")
    
    return time_age_df

def analyze_gender_differences():
    """分析性別收視差異"""
    print("\n" + "="*60)
    print("3. 性別收視差異分析")
    print("="*60)
    
    df = load_and_prepare_data()
    
    # 整體性別差異
    print("\n整體性別收視率比較:")
    print("-" * 30)
    
    overall_male = df['4歲以上男性'].mean()
    overall_female = df['4歲以上女性'].mean()
    
    print(f"男性觀眾: {overall_male:.4f}")
    print(f"女性觀眾: {overall_female:.4f}")
    print(f"差異: {abs(overall_male - overall_female):.4f} ({'女性較高' if overall_female > overall_male else '男性較高'})")
    
    # 各年齡層性別差異
    print("\n各年齡層性別差異:")
    print("-" * 50)
    print("年齡層      男性    女性    差異    偏向")
    print("-" * 50)
    
    gender_analysis_data = []
    
    age_gender_pairs = [
        ('15-24歲', '15-24歲男性', '15-24歲女性'),
        ('25-34歲', '25-34歲男性', '25-34歲女性'),
        ('35-44歲', '35-44歲男性', '35-44歲女性'),
        ('45-54歲', '45-54歲男性', '45-54歲女性'),
        ('55歲以上', '55歲以上男性', '55歲以上女性')
    ]
    
    for age_group, male_col, female_col in age_gender_pairs:
        if male_col in df.columns and female_col in df.columns:
            male_avg = df[male_col].mean()
            female_avg = df[female_col].mean()
            diff = abs(male_avg - female_avg)
            bias = '女性' if female_avg > male_avg else '男性'
            
            print(f"{age_group:<10} {male_avg:.4f}  {female_avg:.4f}  {diff:.4f}   {bias}")
            
            gender_analysis_data.extend([
                {'Age_Group': age_group, 'Gender': '男性', 'Rating': male_avg},
                {'Age_Group': age_group, 'Gender': '女性', 'Rating': female_avg}
            ])
    
    # 主要劇集的性別偏好
    print("\n主要劇集性別偏好分析:")
    print("=" * 50)
    
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 50].head(8)
    
    series_gender_data = []
    
    for series_name in major_series.index:
        series_data = df[df['Cleaned_Series_Name'] == series_name]
        
        male_rating = series_data['4歲以上男性'].mean()
        female_rating = series_data['4歲以上女性'].mean()
        
        bias = '女性向' if female_rating > male_rating else '男性向'
        diff = abs(male_rating - female_rating)
        
        print(f"{series_name[:15]:<15} 男:{male_rating:.4f} 女:{female_rating:.4f} → {bias} (差異:{diff:.4f})")
        
        series_gender_data.extend([
            {'Series': series_name[:12] + '...' if len(series_name) > 12 else series_name, 
             'Gender': '男性', 'Rating': male_rating},
            {'Series': series_name[:12] + '...' if len(series_name) > 12 else series_name, 
             'Gender': '女性', 'Rating': female_rating}
        ])
    
    return pd.DataFrame(gender_analysis_data), pd.DataFrame(series_gender_data)

def analyze_monthly_age_trends():
    """分析月份年齡趨勢"""
    print("\n" + "="*60)
    print("4. 月份年齡趨勢分析")
    print("="*60)
    
    df = load_and_prepare_data()
    
    print("\n各月份年齡層收視率變化:")
    print("=" * 70)
    
    monthly_age_data = []
    
    for month in range(1, 13):
        month_data = df[df['Month'] == month]
        
        if len(month_data) > 0:
            print(f"\n{month}月 ({len(month_data):,}筆資料):")
            print("-" * 30)
            
            for group_name, columns in AGE_GROUPS.items():
                if columns[0] in month_data.columns:
                    avg_rating = month_data[columns[0]].mean()
                    print(f"  {group_name:<10} {avg_rating:.4f}")
                    
                    monthly_age_data.append({
                        'Month': month,
                        'Age_Group': group_name,
                        'Rating': avg_rating
                    })
    
    # 找出各年齡層最佳月份
    print("\n各年齡層最佳收視月份:")
    print("-" * 40)
    
    monthly_age_df = pd.DataFrame(monthly_age_data)
    for group in AGE_GROUPS.keys():
        group_data = monthly_age_df[monthly_age_df['Age_Group'] == group]
        if len(group_data) > 0:
            best_month = group_data.loc[group_data['Rating'].idxmax()]
            worst_month = group_data.loc[group_data['Rating'].idxmin()]
            print(f"{group:<10} 最佳:{best_month['Month']:2.0f}月({best_month['Rating']:.4f}) " + 
                  f"最差:{worst_month['Month']:2.0f}月({worst_month['Rating']:.4f})")
    
    return monthly_age_df

def create_age_analysis_visualizations():
    """創建年齡分析視覺化圖表"""
    print("\n" + "="*60)
    print("5. 生成視覺化圖表")
    print("="*60)
    
    # 設定字體
    setup_font()
    
    # 執行各項分析並獲取資料
    age_pref_data = analyze_age_group_preferences()
    time_age_data = analyze_time_slot_demographics()
    gender_data, series_gender_data = analyze_gender_differences()
    monthly_data = analyze_monthly_age_trends()
    
    # 創建綜合圖表
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('愛爾達綜合台年齡分層收視分析', fontsize=16, fontweight='bold', y=0.98,
                fontproperties='Heiti TC')
    
    # 1. 主要劇集年齡偏好熱力圖
    if not age_pref_data.empty:
        pivot_data = age_pref_data.pivot(index='Series', columns='Age_Group', values='Rating')
        sns.heatmap(pivot_data, annot=True, fmt='.3f', cmap='YlOrRd', 
                   ax=axes[0, 0], cbar_kws={'label': '收視率'})
        axes[0, 0].set_title('主要劇集年齡偏好分析', fontsize=12, fontproperties='Heiti TC')
        axes[0, 0].set_xlabel('年齡群組', fontsize=10, fontproperties='Heiti TC')
        axes[0, 0].set_ylabel('劇集', fontsize=10, fontproperties='Heiti TC')
    
    # 2. 時段年齡分布
    if not time_age_data.empty:
        pivot_time = time_age_data.pivot(index='Time_Slot', columns='Age_Group', values='Rating')
        pivot_time.plot(kind='bar', ax=axes[0, 1], width=0.8)
        axes[0, 1].set_title('不同時段年齡分布', fontsize=12, fontproperties='Heiti TC')
        axes[0, 1].set_xlabel('時段', fontsize=10, fontproperties='Heiti TC')
        axes[0, 1].set_ylabel('平均收視率', fontsize=10, fontproperties='Heiti TC')
        axes[0, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, prop={'family': 'Heiti TC'})
        axes[0, 1].tick_params(axis='x', rotation=0, labelsize=9)
    
    # 3. 性別差異比較
    if not gender_data.empty:
        pivot_gender = gender_data.pivot(index='Age_Group', columns='Gender', values='Rating')
        pivot_gender.plot(kind='bar', ax=axes[0, 2], color=['lightblue', 'lightcoral'])
        axes[0, 2].set_title('各年齡層性別差異', fontsize=12, fontproperties='Heiti TC')
        axes[0, 2].set_xlabel('年齡群組', fontsize=10, fontproperties='Heiti TC')
        axes[0, 2].set_ylabel('平均收視率', fontsize=10, fontproperties='Heiti TC')
        axes[0, 2].legend(['男性', '女性'], fontsize=9, prop={'family': 'Heiti TC'})
        axes[0, 2].tick_params(axis='x', rotation=45, labelsize=9)
    
    # 4. 月份趨勢（選取主要年齡層）
    if not monthly_data.empty:
        main_groups = ['總體', '核心觀眾', '年輕族群', '銀髮族']
        for group in main_groups:
            group_data = monthly_data[monthly_data['Age_Group'] == group]
            if not group_data.empty:
                axes[1, 0].plot(group_data['Month'], group_data['Rating'], 
                               marker='o', label=group, linewidth=2)
        axes[1, 0].set_title('月份年齡趨勢', fontsize=12, fontproperties='Heiti TC')
        axes[1, 0].set_xlabel('月份', fontsize=10, fontproperties='Heiti TC')
        axes[1, 0].set_ylabel('平均收視率', fontsize=10, fontproperties='Heiti TC')
        axes[1, 0].legend(fontsize=9, prop={'family': 'Heiti TC'})
        axes[1, 0].set_xticks(range(1, 13))
        axes[1, 0].tick_params(labelsize=9)
    
    # 5. 劇集性別偏好
    if not series_gender_data.empty:
        pivot_series_gender = series_gender_data.pivot(index='Series', columns='Gender', values='Rating')
        pivot_series_gender.plot(kind='barh', ax=axes[1, 1], color=['lightblue', 'lightcoral'])
        axes[1, 1].set_title('主要劇集性別偏好', fontsize=12, fontproperties='Heiti TC')
        axes[1, 1].set_xlabel('平均收視率', fontsize=10, fontproperties='Heiti TC')
        axes[1, 1].set_ylabel('劇集', fontsize=10, fontproperties='Heiti TC')
        axes[1, 1].legend(['男性', '女性'], fontsize=9, prop={'family': 'Heiti TC'})
        axes[1, 1].tick_params(labelsize=9)
    
    # 6. 整體年齡分布餅圖
    df = load_and_prepare_data()
    age_totals = {}
    for group_name, columns in AGE_GROUPS.items():
        if group_name != '總體' and columns[0] in df.columns:
            age_totals[group_name] = df[columns[0]].sum()
    
    if age_totals:
        axes[1, 2].pie(age_totals.values(), labels=age_totals.keys(), autopct='%1.1f%%', 
                      startangle=90, colors=plt.cm.Set3.colors, 
                      textprops={'fontsize': 9, 'family': 'Heiti TC'})
        axes[1, 2].set_title('整體年齡分布占比', fontsize=12, fontproperties='Heiti TC')
    
    plt.tight_layout()
    plt.savefig('drama_age_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ 視覺化圖表已保存為 'drama_age_analysis.png'")

def generate_summary_report():
    """生成分析摘要報告"""
    print("\n" + "="*60)
    print("6. 分析摘要報告")
    print("="*60)
    
    df = load_and_prepare_data()
    
    # 關鍵發現
    print("\n📊 關鍵發現:")
    print("-" * 30)
    
    # 1. 主要觀眾群
    age_ratings = {}
    for group_name, columns in AGE_GROUPS.items():
        if columns[0] in df.columns:
            age_ratings[group_name] = df[columns[0]].mean()
    
    main_audience = max(age_ratings, key=age_ratings.get)
    main_rating = age_ratings[main_audience]
    print(f"1. 主要觀眾群: {main_audience} (平均收視率 {main_rating:.4f})")
    
    # 2. 性別差異
    male_avg = df['4歲以上男性'].mean()
    female_avg = df['4歲以上女性'].mean()
    gender_bias = '女性' if female_avg > male_avg else '男性'
    print(f"2. 性別偏向: {gender_bias}觀眾較多 (差異 {abs(male_avg - female_avg):.4f})")
    
    # 3. 最佳時段
    hourly_ratings = df.groupby('Hour')['4歲以上'].mean()
    best_hour = hourly_ratings.idxmax()
    best_rating = hourly_ratings.max()
    print(f"3. 最佳收視時段: {best_hour}點 (平均收視率 {best_rating:.4f})")
    
    # 4. 季節性趨勢
    monthly_ratings = df.groupby('Month')['4歲以上'].mean()
    best_month = monthly_ratings.idxmax()
    worst_month = monthly_ratings.idxmin()
    print(f"4. 最佳收視月份: {best_month}月 ({monthly_ratings[best_month]:.4f})")
    print(f"   最差收視月份: {worst_month}月 ({monthly_ratings[worst_month]:.4f})")
    
    # 5. 劇集建議
    print("\n📈 節目策略建議:")
    print("-" * 30)
    
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 50].head(5)
    
    for series_name in major_series.index:
        series_data = df[df['Cleaned_Series_Name'] == series_name]
        
        # 找出該劇的主要觀眾群
        series_age_ratings = {}
        for group_name, columns in AGE_GROUPS.items():
            if columns[0] in series_data.columns:
                series_age_ratings[group_name] = series_data[columns[0]].mean()
        
        main_audience_series = max(series_age_ratings, key=series_age_ratings.get)
        print(f"• {series_name[:20]:<20} → 主攻 {main_audience_series}")
    
    print(f"\n✅ 分析完成! 共分析 {len(df):,} 筆收視資料")
    print(f"   涵蓋 {df['Cleaned_Series_Name'].nunique()} 部劇集")
    print(f"   時間跨度 {df['Date'].min().date()} 至 {df['Date'].max().date()}")

def main():
    """主要執行函式"""
    print("🎬 愛爾達綜合台劇集年齡分層收視分析")
    print("=" * 60)
    
    try:
        # 執行完整分析流程
        age_pref_data = analyze_age_group_preferences()
        time_age_data = analyze_time_slot_demographics()
        gender_data, series_gender_data = analyze_gender_differences()
        monthly_data = analyze_monthly_age_trends()
        
        # 生成視覺化圖表
        create_age_analysis_visualizations()
        
        # 生成摘要報告
        generate_summary_report()
        
    except FileNotFoundError:
        print("❌ 錯誤: 找不到 'ACNelson_normalized_with_age.csv' 檔案")
        print("   請先執行 'process_acnelson_with_age.py' 生成年齡分層資料")
    except Exception as e:
        print(f"❌ 分析過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()

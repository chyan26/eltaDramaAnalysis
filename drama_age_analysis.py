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
    
    print("\n各時段年齡&性別層收視率分析:")
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
            
            # 加入性別層的資料
            for gender_group_name, col_name in GENDER_GROUPS.items():
                if col_name in slot_data.columns:
                    gender_avg_rating = slot_data[col_name].mean()
                    print(f"  {gender_group_name:<10} {gender_avg_rating:.4f}")

                    time_age_data.append({
                        'Time_Slot': slot_name,
                        'Age_Group': gender_group_name,
                        'Rating': gender_avg_rating
                    })
    
    # 找出各年齡層最佳時段
    print("\n各年齡&性別層最佳收視時段:")
    print("-" * 40)
    
    time_age_df = pd.DataFrame(time_age_data)
    for group in AGE_GROUPS.keys():
        group_data = time_age_df[time_age_df['Age_Group'] == group]
        if len(group_data) > 0:
            best_slot = group_data.loc[group_data['Rating'].idxmax()]
            print(f"{group:<10} → {best_slot['Time_Slot']}時段 ({best_slot['Rating']:.4f})")
    
    for gender_group in GENDER_GROUPS.keys():
        gender_group_data = time_age_df[time_age_df['Age_Group'] == gender_group]
        if len(gender_group_data) > 0:
            best_gender_slot = gender_group_data.loc[gender_group_data['Rating'].idxmax()]
            print(f"{gender_group:<10} → {best_gender_slot['Time_Slot']}時段 ({best_gender_slot['Rating']:.4f})")
    
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

def create_gender_landscape_chart():
    """創建專用的橫向性別年齡分布圖表"""
    
    # 載入資料
    df = load_and_prepare_data()
    
    # 建立橫向圖表 (16x10 inch landscape)
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # 定義要顯示的性別年齡組合
    gender_age_groups = [
        '年輕男性', '年輕女性', '中年男性', '中年女性', 
        '熟齡男性', '熟齡女性', '銀髮男性', '銀髮女性'
    ]
    
    # 對應到資料中的實際欄位名稱
    column_mapping = {
        '年輕男性': '15-24歲男性',
        '年輕女性': '15-24歲女性',
        '中年男性': '35-44歲男性',
        '中年女性': '35-44歲女性',
        '熟齡男性': '45-54歲男性',
        '熟齡女性': '45-54歲女性',
        '銀髮男性': '55歲以上男性',
        '銀髮女性': '55歲以上女性'
    }
    
    # 時段名稱映射（從原始名稱到完整名稱）
    time_slot_display_mapping = {
        '凌晨': '凌晨時段',
        '早晨': '早晨時段', 
        '午間': '午間時段',
        '黃金': '黃金時段',
        '深夜': '深夜時段'
    }
    
    # 定義時段（與analyze_time_slot_demographics()一致）
    time_slots = {
        '凌晨': (0, 5),
        '早晨': (6, 11), 
        '午間': (12, 17),
        '黃金': (18, 22),
        '深夜': (23, 23)
    }
    
    # 建立時段性別年齡資料
    time_gender_data = []
    for slot_name, (start_hour, end_hour) in time_slots.items():
        slot_data = df[df['Hour'].between(start_hour, end_hour)]
        # 將原始時段名稱轉換為完整顯示名稱
        display_time_slot = time_slot_display_mapping.get(slot_name, slot_name)
        
        for display_name, column_name in column_mapping.items():
            if column_name in df.columns:
                avg_rating = slot_data[column_name].mean()
                time_gender_data.append({
                    'Time_Slot': display_time_slot,
                    'Age_Gender_Group': display_name,
                    'Rating': avg_rating
                })
    
    if time_gender_data:
        time_gender_df = pd.DataFrame(time_gender_data)
        pivot_time = time_gender_df.pivot(index='Time_Slot', columns='Age_Gender_Group', values='Rating')
        
        # 確保欄位順序
        ordered_groups = [group for group in gender_age_groups if group in pivot_time.columns]
        pivot_time = pivot_time.reindex(columns=ordered_groups, fill_value=0)
        
        # 專業性別年齡配色方案
        colors = {
            '年輕男性': '#1f77b4',    # 深藍（男性）
            '年輕女性': '#87CEEB',    # 淺藍（女性）
            '中年男性': '#2ca02c',    # 深綠（男性）  
            '中年女性': '#90EE90',    # 淺綠（女性）
            '熟齡男性': '#d62728',    # 深紅（男性）
            '熟齡女性': '#FFB6C1',    # 淺紅（女性）
            '銀髮男性': '#9467bd',    # 深紫（男性）
            '銀髮女性': '#DDA0DD'     # 淺紫（女性）
        }
        chart_colors = [colors.get(col, '#777777') for col in pivot_time.columns]
        
        # 創建條形圖
        bars = pivot_time.plot(kind='bar', ax=ax, width=0.8, 
                              color=chart_colors, alpha=0.85, 
                              edgecolor='white', linewidth=1.0)
        
        # 設定圖表屬性
        ax.set_title('不同時段年齡與性別收視分布', fontsize=20, fontweight='bold',
                    fontproperties='Heiti TC', pad=30)
        ax.set_xlabel('時段', fontsize=16, fontproperties='Heiti TC')
        ax.set_ylabel('平均收視率', fontsize=16, fontproperties='Heiti TC')
        
        # 優化圖例 - 橫向佈局
        ax.legend(bbox_to_anchor=(0.5, -0.08), loc='upper center', fontsize=13,
                 prop={'family': 'Heiti TC'}, frameon=True, fancybox=True,
                 title='年齡群組與性別', title_fontsize=15, shadow=True,
                 ncol=4)  # 4列橫向顯示
        
        # 軸標籤和刻度
        ax.tick_params(axis='x', rotation=0, labelsize=14)
        ax.tick_params(axis='y', labelsize=14)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # 添加數值標籤 - 所有類別
        for container in bars.containers:
            ax.bar_label(container, fmt='%.3f', fontsize=11, rotation=0, 
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9))
    
    # 調整布局和保存
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)  # 為圖例留出空間
    plt.savefig('gender_age_analysis_landscape.png', dpi=300, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    plt.show()

def create_age_analysis_visualizations():
    """創建年齡分析視覺化圖表 - 優化版"""
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
    
    # 創建主要分析圖表
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1], width_ratios=[1, 1], 
                         hspace=0.5, wspace=0.3)
    
    # 設定全局字體大小
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 11
    })
    
    fig.suptitle('愛爾達綜合台年齡分層收視分析', fontsize=20, fontweight='bold', 
                y=0.98, fontproperties='Heiti TC')
    
    # 0. 整體年齡層收視率概覽
    ax0 = fig.add_subplot(gs[0, 0])
    if not age_pref_data.empty:
        # 計算各年齡層平均收視率
        age_avg = age_pref_data.groupby('Age_Group')['Rating'].mean().sort_values(ascending=False)
        bars = age_avg.plot(kind='bar', ax=ax0, color='#2E8B57', width=0.7, alpha=0.8)
        ax0.set_title('各年齡層整體平均收視率', fontsize=14, fontweight='bold',
                     fontproperties='Heiti TC', pad=20)
        ax0.set_xlabel('年齡群組', fontsize=12, fontproperties='Heiti TC')
        ax0.set_ylabel('平均收視率', fontsize=12, fontproperties='Heiti TC')
        ax0.tick_params(axis='x', rotation=45, labelsize=10)
        ax0.tick_params(axis='y', labelsize=10)
        ax0.grid(True, alpha=0.3, linestyle='--')
        
        # 添加數值標籤
        for container in bars.containers:
            ax0.bar_label(container, fmt='%.3f', fontsize=9, rotation=0,
                         bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.8))

    # 1. 主要劇集年齡偏好熱力圖 - 增強版
    ax1 = fig.add_subplot(gs[0, 1])
    if not age_pref_data.empty:
        pivot_data = age_pref_data.pivot(index='Series', columns='Age_Group', values='Rating')
        sns.heatmap(pivot_data, annot=True, fmt='.3f', cmap='RdYlBu_r', 
                   ax=ax1, cbar_kws={'label': '收視率', 'shrink': 0.8},
                   annot_kws={'size': 10})
        ax1.set_title('主要劇集年齡偏好分析', fontsize=14, fontweight='bold',
                     fontproperties='Heiti TC', pad=20)
        ax1.set_xlabel('年齡群組', fontsize=12, fontproperties='Heiti TC')
        ax1.set_ylabel('劇集', fontsize=12, fontproperties='Heiti TC')
        ax1.tick_params(axis='x', rotation=45, labelsize=10)
        ax1.tick_params(axis='y', rotation=0, labelsize=10)
    
    # # 2. 時段年齡分布 (簡化版，性別分布移至獨立頁面)
    # ax2 = fig.add_subplot(gs[0, 1])
    # if not time_age_data.empty:
    #     # 使用基本年齡群組
    #     basic_groups = ['核心觀眾', '年輕族群', '中年', '熟齡', '銀髮族']
    #     filtered_data = time_age_data[time_age_data['Age_Group'].isin(basic_groups)]
        
    #     if not filtered_data.empty:
    #         pivot_time = filtered_data.pivot(index='Time_Slot', columns='Age_Group', values='Rating')
    #         pivot_time = pivot_time.reindex(columns=basic_groups, fill_value=0)
            
    #         colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    #         bars = pivot_time.plot(kind='bar', ax=ax2, width=0.7, color=colors, alpha=0.8)
            
    #         ax2.set_title('時段收視分布（基本年齡層）', fontsize=14, fontweight='bold',
    #                      fontproperties='Heiti TC', pad=20)
    #         ax2.set_xlabel('時段', fontsize=12, fontproperties='Heiti TC')
    #         ax2.set_ylabel('平均收視率', fontsize=12, fontproperties='Heiti TC')
    #         ax2.legend(fontsize=10, prop={'family': 'Heiti TC'}, loc='upper left')
    #         ax2.tick_params(axis='x', rotation=45, labelsize=10)
    #         ax2.tick_params(axis='y', labelsize=10)
    #         ax2.grid(True, alpha=0.3, linestyle='--')
    
    # 3. 性別差異比較 - 優化版
    ax3 = fig.add_subplot(gs[1, 0])
    if not gender_data.empty:
        pivot_gender = gender_data.pivot(index='Age_Group', columns='Gender', values='Rating')
        pivot_gender.plot(kind='bar', ax=ax3, color=['#4A90E2', '#E24A72'], width=0.7)
        ax3.set_title('各年齡層性別差異', fontsize=14, fontweight='bold',
                     fontproperties='Heiti TC', pad=20)
        ax3.set_xlabel('年齡群組', fontsize=12, fontproperties='Heiti TC')
        ax3.set_ylabel('平均收視率', fontsize=12, fontproperties='Heiti TC')
        ax3.legend(['男性', '女性'], fontsize=11, prop={'family': 'Heiti TC'}, 
                  frameon=True, fancybox=True)
        ax3.tick_params(axis='x', rotation=45, labelsize=10)
        ax3.grid(True, alpha=0.3)
    
    # 4. 月份趨勢 - 改進版
    ax4 = fig.add_subplot(gs[1, 1])
    if not monthly_data.empty:
        main_groups = ['總體', '核心觀眾', '年輕族群', '銀髮族']
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#8E5572']
        
        for i, group in enumerate(main_groups):
            group_data = monthly_data[monthly_data['Age_Group'] == group]
            if not group_data.empty:
                ax4.plot(group_data['Month'], group_data['Rating'], 
                        marker='o', label=group, linewidth=2.5, 
                        color=colors[i], markersize=6)
        
        ax4.set_title('月份年齡趨勢', fontsize=14, fontweight='bold',
                     fontproperties='Heiti TC', pad=20)
        ax4.set_xlabel('月份', fontsize=12, fontproperties='Heiti TC')
        ax4.set_ylabel('平均收視率', fontsize=12, fontproperties='Heiti TC')
        ax4.legend(fontsize=11, prop={'family': 'Heiti TC'}, 
                  frameon=True, fancybox=True)
        ax4.set_xticks(range(1, 13))
        ax4.tick_params(labelsize=10)
        ax4.grid(True, alpha=0.3)
    
    # 5. 劇集性別偏好 - 優化版
    ax5 = fig.add_subplot(gs[2, 0])
    if not series_gender_data.empty:
        pivot_series_gender = series_gender_data.pivot(index='Series', columns='Gender', values='Rating')
        pivot_series_gender.plot(kind='barh', ax=ax5, 
                               color=['#4A90E2', '#E24A72'], width=0.7)
        ax5.set_title('主要劇集性別偏好', fontsize=14, fontweight='bold',
                     fontproperties='Heiti TC', pad=20)
        ax5.set_xlabel('平均收視率', fontsize=12, fontproperties='Heiti TC')
        ax5.set_ylabel('劇集', fontsize=12, fontproperties='Heiti TC')
        ax5.legend(['男性', '女性'], fontsize=11, prop={'family': 'Heiti TC'}, 
                  frameon=True, fancybox=True)
        ax5.tick_params(labelsize=10)
        ax5.grid(True, alpha=0.3)
    
    # 6. 整體年齡分布餅圖 - 優化版
    ax6 = fig.add_subplot(gs[2, 1])
    df = load_and_prepare_data()
    age_totals = {}
    for group_name, columns in AGE_GROUPS.items():
        if group_name != '總體' and columns[0] in df.columns:
            age_totals[group_name] = df[columns[0]].sum()
    
    if age_totals:
        # 使用更好的顏色方案和更大的字體
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF']
        wedges, texts, autotexts = ax6.pie(age_totals.values(), labels=age_totals.keys(), 
                                          autopct='%1.1f%%', startangle=90, 
                                          colors=colors[:len(age_totals)],
                                          textprops={'fontsize': 11, 'family': 'Heiti TC'})
        
        # 調整百分比文字樣式
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        ax6.set_title('整體年齡分布占比', fontsize=14, fontweight='bold',
                     fontproperties='Heiti TC', pad=20)
    
    # 調整布局並保存主要圖表
    plt.tight_layout()
    plt.savefig('drama_age_analysis.png', dpi=300, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    plt.show()
    
    # 創建獨立的橫向性別年齡分布圖表
    create_gender_landscape_chart()
    
    print("✓ 視覺化圖表已保存為 'drama_age_analysis.png'")
    print("  - 圖表尺寸: 20x16 英吋")
    print("  - 解析度: 300 DPI")
    print("  - 字體大小: 顯著增大以提升可讀性")
    print("  - 布局: 優化間距避免重疊")
    print("✓ 性別年齡分布圖表已保存為 'gender_age_analysis_landscape.png'")
    print("  - 圖表尺寸: 16x10 英吋 (橫向)")
    print("  - 專為8個性別年齡類別優化的可讀性")

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

"""
Demo Script for Reports and Charts Viewer
演示報告和圖表查看功能的測試腳本
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_demo_chart():
    """創建演示用的分析圖表"""
    
    # 生成模擬的年齡分層收視數據
    np.random.seed(42)
    
    # 年齡組別
    age_groups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    time_slots = ['08:00', '12:00', '16:00', '20:00', '22:00']
    
    # 生成收視率數據
    data = []
    for age in age_groups:
        for time in time_slots:
            base_rating = np.random.uniform(0.5, 3.5)
            # 晚間時段收視率較高
            if time in ['20:00', '22:00']:
                base_rating *= 1.5
            # 年輕人晚間收視率更高
            if age in ['18-24', '25-34'] and time == '22:00':
                base_rating *= 1.3
            # 老年人白天收視率較高
            if age in ['55-64', '65+'] and time in ['12:00', '16:00']:
                base_rating *= 1.2
                
            data.append({
                'age_group': age,
                'time_slot': time,
                'rating': base_rating,
                'share': base_rating * np.random.uniform(2, 4)
            })
    
    df = pd.DataFrame(data)
    
    # 創建圖表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('愛爾達綜合台年齡分層收視分析', fontsize=16, fontweight='bold')
    
    # 1. 年齡組別平均收視率
    age_avg = df.groupby('age_group')['rating'].mean()
    ax1.bar(age_avg.index, age_avg.values, color='skyblue', edgecolor='navy')
    ax1.set_title('各年齡組別平均收視率', fontweight='bold')
    ax1.set_xlabel('年齡組別')
    ax1.set_ylabel('收視率 (%)')
    ax1.grid(True, alpha=0.3)
    
    # 2. 時段分布熱力圖
    pivot_data = df.pivot(index='age_group', columns='time_slot', values='rating')
    sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax2)
    ax2.set_title('年齡組別 × 時段收視率熱力圖', fontweight='bold')
    ax2.set_xlabel('時段')
    ax2.set_ylabel('年齡組別')
    
    # 3. 時段收視趨勢
    time_avg = df.groupby('time_slot')['rating'].mean()
    ax3.plot(time_avg.index, time_avg.values, marker='o', linewidth=2, markersize=8)
    ax3.fill_between(time_avg.index, time_avg.values, alpha=0.3)
    ax3.set_title('各時段平均收視率趨勢', fontweight='bold')
    ax3.set_xlabel('時段')
    ax3.set_ylabel('收視率 (%)')
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. 收視率分布箱線圖
    df_plot = []
    for age in age_groups:
        age_data = df[df['age_group'] == age]['rating'].values
        df_plot.extend([(age, rating) for rating in age_data])
    
    plot_df = pd.DataFrame(df_plot, columns=['age_group', 'rating'])
    sns.boxplot(data=plot_df, x='age_group', y='rating', ax=ax4)
    ax4.set_title('各年齡組別收視率分布', fontweight='bold')
    ax4.set_xlabel('年齡組別')
    ax4.set_ylabel('收視率 (%)')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # 保存圖表
    plt.savefig('drama_age_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 年齡分析圖表已生成: drama_age_analysis.png")
    
    plt.close()

def create_demo_ratings_chart():
    """創建收視率分析圖表"""
    
    # 生成模擬劇集收視數據
    np.random.seed(123)
    
    dramas = [
        '都市愛情劇A', '古裝劇B', '懸疑劇C', '家庭劇D', '偶像劇E',
        '職場劇F', '歷史劇G', '科幻劇H', '喜劇I', '動作劇J'
    ]
    
    # 生成30天的收視數據
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    data = []
    for drama in dramas:
        base_rating = np.random.uniform(1.0, 4.0)
        for i, date in enumerate(dates):
            # 添加趨勢和隨機變動
            trend = 0.02 * i if np.random.random() > 0.5 else -0.01 * i
            noise = np.random.normal(0, 0.3)
            rating = max(0.1, base_rating + trend + noise)
            
            data.append({
                'drama': drama,
                'date': date,
                'rating': rating,
                'share': rating * np.random.uniform(2.5, 4.5)
            })
    
    df = pd.DataFrame(data)
    
    # 創建圖表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('愛爾達綜合台劇集收視率分析', fontsize=16, fontweight='bold')
    
    # 1. 劇集平均收視率排行
    drama_avg = df.groupby('drama')['rating'].mean().sort_values(ascending=True)
    ax1.barh(drama_avg.index, drama_avg.values, color='lightcoral')
    ax1.set_title('劇集平均收視率排行', fontweight='bold')
    ax1.set_xlabel('收視率 (%)')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # 2. Top 5 劇集收視趨勢
    top5_dramas = drama_avg.tail(5).index
    for drama in top5_dramas:
        drama_data = df[df['drama'] == drama].sort_values('date')
        ax2.plot(drama_data['date'], drama_data['rating'], 
                marker='o', label=drama, linewidth=2, markersize=4)
    
    ax2.set_title('Top 5 劇集收視率趨勢', fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('收視率 (%)')
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. 收視率分布直方圖
    ax3.hist(df['rating'], bins=20, color='lightblue', edgecolor='navy', alpha=0.7)
    ax3.axvline(df['rating'].mean(), color='red', linestyle='--', 
                label=f'平均: {df["rating"].mean():.2f}%')
    ax3.set_title('收視率分布直方圖', fontweight='bold')
    ax3.set_xlabel('收視率 (%)')
    ax3.set_ylabel('頻次')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 每週收視率變化
    df['weekday'] = df['date'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_avg = df.groupby('weekday')['rating'].mean().reindex(weekday_order)
    
    ax4.bar(range(len(weekday_avg)), weekday_avg.values, color='lightgreen')
    ax4.set_title('星期別平均收視率', fontweight='bold')
    ax4.set_xlabel('星期')
    ax4.set_ylabel('收視率 (%)')
    ax4.set_xticks(range(len(weekday_avg)))
    ax4.set_xticklabels(['週一', '週二', '週三', '週四', '週五', '週六', '週日'])
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # 保存圖表
    plt.savefig('ratings_analysis_heiti.png', dpi=300, bbox_inches='tight')
    print("✅ 收視率分析圖表已生成: ratings_analysis_heiti.png")
    
    plt.close()

def create_demo_pdf_content():
    """創建演示PDF報告內容"""
    
    report_content = f"""
# 愛爾達綜合台年齡分層收視分析報告

## 報告摘要
生成時間：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
分析期間：2024年1月 - 2024年12月
資料來源：Nielsen收視率調查

## 主要發現

### 1. 年齡分層特徵
- 25-34歲年齡層為主要收視群體，平均收視率2.8%
- 55歲以上觀眾在日間時段表現活躍
- 18-24歲年輕觀眾偏好晚間22:00時段

### 2. 時段偏好分析
- 黃金時段(20:00-22:00)收視率最高
- 午間時段(12:00-16:00)中老年觀眾比例較高
- 深夜時段年輕觀眾活躍度明顯提升

### 3. 劇集類型偏好
- 都市愛情劇在25-44歲女性觀眾中表現突出
- 古裝劇在45歲以上觀眾中受歡迎
- 懸疑劇獲得跨年齡層觀眾喜愛

## 策略建議

### 節目編排優化
1. 加強黃金時段優質內容投入
2. 針對不同年齡層定制節目內容
3. 強化週末時段節目吸引力

### 目標觀眾拓展
1. 深耕25-44歲核心觀眾群
2. 開發青少年觀眾市場
3. 維護中老年忠實觀眾

---
*本報告由愛爾達劇集分析系統自動生成*
"""
    
    # 將內容寫入文本文件（模擬PDF）
    with open('demo_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("✅ 演示分析報告已生成: demo_analysis_report.txt")

if __name__ == "__main__":
    print("🎨 開始生成演示圖表和報告...")
    print("=" * 50)
    
    try:
        # 生成年齡分析圖表
        create_demo_chart()
        
        # 生成收視率分析圖表
        create_demo_ratings_chart()
        
        # 生成演示報告
        create_demo_pdf_content()
        
        print("\n" + "=" * 50)
        print("🎉 所有演示內容生成完成！")
        print("\n📊 生成的檔案:")
        print("  📈 drama_age_analysis.png - 年齡分層收視分析圖")
        print("  📈 ratings_analysis_heiti.png - 收視率分析圖表")
        print("  📋 demo_analysis_report.txt - 演示分析報告")
        print("\n💡 現在您可以在Streamlit應用中的「📊 報告與圖表」功能查看這些內容！")
        
    except Exception as e:
        print(f"❌ 生成過程中發生錯誤: {e}")
        print("🔧 請確保安裝了matplotlib和seaborn套件")

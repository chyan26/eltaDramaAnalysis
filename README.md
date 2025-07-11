# ELTA Drama Analysis Project / 愛爾達綜合台收視率分析專案

## Overview / 專案概述

This project successfully integrates ELTA's program schedule with viewership ratings data and conducts in-depth viewership analysis.

本專案成功整合了愛爾達綜合台的節目表與收視率資料，並進行了深入的收視率分析。

## Features / 主要功能

- **Data Integration**: Merge program schedules with rating data
- **Data Cleaning**: Standardize drama names and handle inconsistencies  
- **Comprehensive Analysis**: Multi-dimensional rating analysis
- **Visualization**: Generate publication-ready charts with Chinese font support
- **Time Series Analysis**: Track drama performance over time

## Installation / 安裝

1. Clone the repository:
```bash
git clone https://github.com/yourusername/eltaDramaAnalysis.git
cd eltaDramaAnalysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start / 快速開始

### Option 1: Use cleaned data directly / 直接使用清理後的資料
```python
import pandas as pd
df = pd.read_csv('integrated_program_ratings_cleaned.csv')
# Start your analysis...
```

### Option 2: Run complete analysis pipeline / 執行完整分析流程
```bash
# 1. Data integration (if reprocessing raw data)
python integrateData.py

# 2. Data cleaning (if re-cleaning is needed)
python clean_data.py

# 3. Run analysis
python drama_analysis.py

# 4. Generate charts (recommended version with Chinese font support)
python create_charts_heiti.py
```

## 完成的主要工作

### 1. 資料處理與整合
- **檔案**: `integrateData.py`
- **功能**: 
  - 解析節目表 Excel，修正日期欄位讀取問題
  - 將非2024/2025年資料自動調整為2024年
  - 解析收視率 Excel，正確提取各時段收視率
  - 整合節目表與收視率資料，產生 `integrated_program_ratings.csv`

### 2. 資料清理
- **檔案**: `clean_data.py` 
- **功能**:
  - 統一劇集名稱，解決命名不一致問題
  - 合併重複系列（如「蠟筆小新」與「蠟筆小新#」）
  - 產生清理後的資料檔案 `integrated_program_ratings_cleaned.csv`

### 3. 深度分析
- **檔案**: `drama_analysis.py`
- **功能**:
  - 主要劇集統計與排名
  - 收視率趨勢分析
  - 黃金時段分析（18-22點）
  - 週末 vs 平日比較
  - 月份趨勢分析
  - 收視率分布區間分析

### 4. 視覺化圖表
- **檔案**: `create_charts.py`
- **功能**:
  - 各時段平均收視率長條圖
  - 月份收視率趨勢線圖
  - 主要劇集收視率比較圖
  - 收視率分布直方圖
  - 產生高解析度圖表 `ratings_analysis.png`

## 關鍵發現

### 主要劇集表現
1. **蠟筆小新**: 2,534集，平均收視率0.1650，呈上升趨勢
2. **延禧攻略**: 320集，平均收視率0.2718，表現優異
3. **後宮甄嬛傳**: 284集，平均收視率0.1928，穩定成長
4. **墨雨雲間**: 240集，平均收視率0.2731，收視率最高

### 收視時段分析
- **最佳時段**: 20點（平均收視率0.3847）
- **黃金時段**: 18-22點表現最佳
- **收視高峰**: 《墨雨雲間》完結集達0.8989

### 收視率分布
- 69%的節目收視率低於0.2
- 僅0.6%的節目收視率突破0.5
- 高收視率節目主要集中在特定劇集

## Chart Generation Options / 圖表生成選項

### Recommended / 推薦使用
**`create_charts_heiti.py`** - Font issues completely resolved! / 字體問題已完全解決！
- ✅ No font warnings / 無字體警告
- ✅ Proper Chinese display / 中文顯示正常  
- ✅ Uses Heiti font family / 使用黑體系列字體
- ✅ Generates: `ratings_analysis_heiti.png`

### Alternative Versions / 其他可用版本
1. **`create_charts_english.py`** - English version (no font issues)
2. **`create_charts_chinese_final.py`** - Chinese alternative
3. **`create_charts.py`** - Generic version

## Technical Features / 技術特色

### Data Quality Control / 資料品質控制
- Automatic date correction / 自動修正日期年份錯誤
- Handle different Excel date formats / 處理Excel不同日期格式
- Clean inconsistent drama names / 清理劇集名稱命名不一致
- Complete NA value analysis / 完整的NA值分析與處理

### Analysis Depth / 分析深度
- Multi-dimensional rating analysis / 多維度收視率分析
- Statistical trend analysis / 趨勢統計分析
- Time slot and program type correlation / 時段與節目類型關聯分析
- Comprehensive statistical descriptions / 完整的統計描述

### Visualization / 可視化效果
- Multi-subplot comprehensive display / 多子圖綜合展示
- High-resolution chart output / 高解析度圖表輸出
- Chinese label support / 中文標籤支援

## Dependencies / 依賴套件

- pandas >= 1.3.0
- matplotlib >= 3.3.0
- seaborn >= 0.11.0
- numpy >= 1.20.0
- openpyxl >= 3.0.0

## Contributing / 貢獻

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License / 授權

This project is open source. Please ensure you have the right to use any data files included.

## Contact / 聯絡

For questions about this project, please open an issue on GitHub.

---

## Notes / 注意事項
- All scripts updated to use cleaned data / 所有腳本已更新為使用清理後的資料
- Drama names standardized to avoid duplicate counting / 劇集名稱已統一，避免重複計算
- Chinese font display supported (may require Chinese font installation) / 支援中文字體顯示（可能需要安裝中文字體）
- Charts output in high-resolution PNG format / 圖表輸出為高解析度PNG格式

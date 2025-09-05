# 愛爾達收視率分析 - 快速參考指南

## 🚀 快速執行命令

### 基礎分析
```bash
# 基本收視率分析
python drama_analysis.py

# 生成推薦圖表（無字體問題）
python create_charts_heiti.py
```

### 進階分析
```bash
# 年齡層分析
python drama_age_analysis.py

# 生成專業PDF報告
python generate_pdf_report.py

# 生成AI投影片
xelatex ai_python_presentation.tex
```

### 完整流程
```bash
# 從頭開始完整分析
python integrateData.py && python clean_data.py && python drama_analysis.py && python create_charts_heiti.py && python drama_age_analysis.py
```

## 📊 主要輸出檔案

| 檔案名稱 | 類型 | 說明 |
|---------|------|------|
| `integrated_program_ratings_cleaned.csv` | 資料 | 清理後的完整收視率資料 |
| `ratings_analysis_heiti.png` | 圖表 | 主要收視率分析圖表（推薦） |
| `drama_age_analysis.png` | 圖表 | 年齡層分析圖表 |
| `drama_age_analysis_report.pdf` | 報告 | 專業分析報告 |
| `ai_python_presentation.pdf` | 投影片 | AI與Python應用展示 |

## 🎯 關鍵發現摘要

### 頂級劇集
1. **墨雨雲間** - 收視率: 0.2731
2. **延禧攻略** - 收視率: 0.2718
3. **後宮甄嬛傳** - 收視率: 0.1928

### 最佳時段
- **20:00** - 黃金時段，平均收視率: 0.3847
- **19:00** - 次黃金時段，平均收視率: 0.2891

### 收視高峰
- **墨雨雲間完結集** - 收視率: 0.8989
- **延禧攻略完結集** - 收視率: 0.8142

## 🔧 程式檔案功能

| 程式檔案 | 主要功能 |
|---------|----------|
| `integrateData.py` | 整合節目表與收視率資料 |
| `clean_data.py` | 清理資料，統一劇集名稱 |
| `drama_analysis.py` | 基礎收視率分析 |
| `drama_age_analysis.py` | 年齡層分析 |
| `create_charts_heiti.py` | 生成中文圖表（推薦） |
| `generate_pdf_report.py` | 生成專業PDF報告 |

## ⚡ 一鍵分析
```bash
# 最推薦的快速分析
python create_charts_heiti.py && python drama_analysis.py && python drama_age_analysis.py
```

## 📋 系統需求
- Python 3.7+
- pandas, matplotlib, seaborn, numpy
- LaTeX（用於PDF報告）
- 中文字體支援

## 🆘 常見問題
- **字體問題**: 使用 `create_charts_heiti.py`
- **PDF生成失敗**: 確認已安裝LaTeX
- **資料載入錯誤**: 確認CSV檔案存在
- **記憶體不足**: 大資料集需要4GB+記憶體
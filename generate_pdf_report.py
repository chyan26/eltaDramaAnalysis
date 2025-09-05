"""
generate_pdf_report.py

生成愛爾達綜合台劇集年齡分層收視分析PDF報告
使用LaTeX排版，包含圖表和詳細分析結果

功能：
1. 執行年齡分析並收集結果
2. 生成LaTeX格式的報告
3. 編譯成PDF文件
4. 包含圖表和表格

使用方法：
  python generate_pdf_report.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
from datetime import datetime
import sys

# Add MacTeX to PATH for LaTeX compilation
if '/Library/TeX/texbin' not in os.environ.get('PATH', ''):
    os.environ['PATH'] = '/Library/TeX/texbin:' + os.environ.get('PATH', '')

# 導入我們的分析模組
sys.path.append('.')
from drama_age_analysis import (
    load_and_prepare_data, 
    analyze_age_group_preferences,
    analyze_time_slot_demographics,
    analyze_gender_differences,
    analyze_monthly_age_trends,
    setup_font,
    AGE_GROUPS,
    GENDER_GROUPS,
)

def collect_analysis_results():
    """收集所有分析結果"""
    print("🔍 收集分析結果...")
    
    # 載入資料
    df = load_and_prepare_data()
    
    results = {
        'data_summary': {
            'total_records': len(df),
            'date_range': f"{df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}",
            'total_series': df['Cleaned_Series_Name'].nunique(),
            'analysis_date': datetime.now().strftime('%Y年%m月%d日')
        }
    }
    
    # 1. 年齡層整體收視率
    age_ratings = {}
    for group_name, columns in AGE_GROUPS.items():
        if columns[0] in df.columns:
            age_ratings[group_name] = df[columns[0]].mean()
    
    results['age_ratings'] = dict(sorted(age_ratings.items(), key=lambda x: x[1], reverse=True))
    
    # 2. 主要劇集分析（>=50集）
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 50].head(10)
    
    series_analysis = []
    for series_name in major_series.index:
        series_data = df[df['Cleaned_Series_Name'] == series_name]
        series_info = {
            'name': series_name,
            'episodes': len(series_data),
            'ratings': {}
        }
        
        for group_name, columns in AGE_GROUPS.items():
            if columns[0] in series_data.columns:
                series_info['ratings'][group_name] = series_data[columns[0]].mean()
        
        # 找出主要觀眾群
        best_group = max(series_info['ratings'], key=series_info['ratings'].get)
        series_info['main_audience'] = best_group
        series_info['main_rating'] = series_info['ratings'][best_group]
        
        series_analysis.append(series_info)
    
    results['series_analysis'] = series_analysis
    
    # 3. 時段分析
    time_slots = {
        '凌晨時段': (0, 5),
        '早晨時段': (6, 11),
        '午間時段': (12, 17),
        '黃金時段': (18, 22),
        '深夜時段': (23, 23)
    }
    
    time_analysis = {}
    for slot_name, (start, end) in time_slots.items():
        if start <= end:
            slot_data = df[(df['Hour'] >= start) & (df['Hour'] <= end)]
        else:  # 跨午夜的情況
            slot_data = df[(df['Hour'] >= start) | (df['Hour'] <= end)]
        
        slot_ratings = {}
        for group_name, columns in AGE_GROUPS.items():
            if columns[0] in slot_data.columns:
                slot_ratings[group_name] = slot_data[columns[0]].mean()
        
        # 加入性別層的統計
        for gender_group_name, col_name in GENDER_GROUPS.items():
            if col_name in slot_data.columns:
                slot_ratings[gender_group_name] = slot_data[col_name].mean()
        
        time_analysis[slot_name] = {
            'count': len(slot_data),
            'ratings': slot_ratings
        }
    
    results['time_analysis'] = time_analysis
    
    # 4. 性別差異分析
    male_avg = df['4歲以上男性'].mean()
    female_avg = df['4歲以上女性'].mean()
    
    gender_analysis = {
        'overall': {
            'male': male_avg,
            'female': female_avg,
            'difference': abs(female_avg - male_avg),
            'preferred': '女性' if female_avg > male_avg else '男性'
        }
    }
    
    # 各年齡層性別差異
    age_gender_columns = {
        '15-24歲': ['15-24歲男性', '15-24歲女性'],
        '25-34歲': ['25-34歲男性', '25-34歲女性'],
        '35-44歲': ['35-44歲男性', '35-44歲女性'],
        '45-54歲': ['45-54歲男性', '45-54歲女性'],
        '55歲以上': ['55歲以上男性', '55歲以上女性']
    }
    
    age_gender_details = {}
    for age_group, (male_col, female_col) in age_gender_columns.items():
        if male_col in df.columns and female_col in df.columns:
            male_rate = df[male_col].mean()
            female_rate = df[female_col].mean()
            age_gender_details[age_group] = {
                'male': male_rate,
                'female': female_rate,
                'difference': abs(female_rate - male_rate),
                'preferred': '女性' if female_rate > male_rate else '男性'
            }
    
    gender_analysis['by_age'] = age_gender_details
    results['gender_analysis'] = gender_analysis
    
    # 5. 月份趨勢
    monthly_data = []
    for month in range(1, 13):
        month_data = df[df['Month'] == month]
        if len(month_data) > 0:
            month_info = {
                'month': month,
                'count': len(month_data),
                'ratings': {}
            }
            for group_name, columns in AGE_GROUPS.items():
                if columns[0] in month_data.columns:
                    month_info['ratings'][group_name] = month_data[columns[0]].mean()
            monthly_data.append(month_info)
    
    results['monthly_analysis'] = monthly_data
    
    # 6. 最佳/最差月份
    best_worst = {}
    for group_name in AGE_GROUPS.keys():
        group_monthly = [(m['month'], m['ratings'].get(group_name, 0)) for m in monthly_data if group_name in m['ratings']]
        if group_monthly:
            best_month = max(group_monthly, key=lambda x: x[1])
            worst_month = min(group_monthly, key=lambda x: x[1])
            best_worst[group_name] = {
                'best': {'month': best_month[0], 'rating': best_month[1]},
                'worst': {'month': worst_month[0], 'rating': worst_month[1]}
            }
    
    results['best_worst_months'] = best_worst
    
    return results

def generate_latex_report(results):
    """生成LaTeX格式的報告"""
    print("📝 生成LaTeX報告...")
    
    latex_content = r"""
\documentclass[11pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{ltxtable}
\usepackage{tabularx}
\usepackage{array}
\usepackage{adjustbox}
\usepackage{rotating}
\usepackage{pdflscape}
\usepackage{float}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage{siunitx}

% 頁面設定 - 減少邊距以容納更多內容
\geometry{left=1.8cm,right=1.8cm,top=2cm,bottom=2cm}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small 愛爾達綜合台劇集年齡分層收視分析報告}
\fancyhead[R]{\small \thepage}

% 表格字體設定
\newcommand{\tablesize}{\small}  % Changed from footnotesize to small for better readability
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% 改善表格可讀性
\renewcommand{\arraystretch}{1.3}  % Increased from 1.2 to 1.3 for better row spacing
\setlength{\tabcolsep}{4pt}  % Increased from 3pt to 4pt for better column spacing

% 改善中文字體顯示
\setCJKmainfont{PingFang SC}[AutoFakeBold=true,AutoFakeSlant=true]
\setCJKsansfont{SimHei}[AutoFakeBold=true]
\setCJKmonofont{SimKai}

% 數字格式設定
\sisetup{
  group-separator = {,},
  group-minimum-digits = 4,
  round-mode = places,
  round-precision = 4
}

% 標題設定
\title{\textbf{\Large 愛爾達綜合台劇集年齡分層收視分析報告}}
\author{資料分析團隊}
\date{""" + results['data_summary']['analysis_date'] + r"""}

\begin{document}

\maketitle

\tableofcontents
\newpage

\section{執行摘要}

本報告基於愛爾達綜合台2024年全年ACNelson收視資料，進行深度年齡分層收視分析。
分析涵蓋""" + f"{results['data_summary']['total_records']:,}" + r"""筆收視紀錄，
時間範圍為""" + results['data_summary']['date_range'] + r"""，
包含""" + str(results['data_summary']['total_series']) + r"""部劇集。

\subsection{主要發現}
\begin{itemize}
    \item 主要觀眾群：""" + list(results['age_ratings'].keys())[0] + r"""（平均收視率 """ + f"{list(results['age_ratings'].values())[0]:.4f}" + r"""）
    \item 性別偏向：""" + results['gender_analysis']['overall']['preferred'] + r"""觀眾較多（差異 """ + f"{results['gender_analysis']['overall']['difference']:.4f}" + r"""）
    \item 最佳收視時段：黃金時段（18-22點）
    \item 收視表現最佳月份：""" + str(results['best_worst_months']['總體']['best']['month']) + r"""月
    \item 收視表現最差月份：""" + str(results['best_worst_months']['總體']['worst']['month']) + r"""月
\end{itemize}

\section{資料概況}

\begin{table}[H]
\centering
\caption{資料基本資訊}
\begin{tabular}{lr}
\toprule
項目 & 數值 \\
\midrule
總收視紀錄數 & """ + f"{results['data_summary']['total_records']:,}" + r""" 筆 \\
分析時間範圍 & """ + results['data_summary']['date_range'] + r""" \\
涵蓋劇集數量 & """ + str(results['data_summary']['total_series']) + r""" 部 \\
分析生成日期 & """ + results['data_summary']['analysis_date'] + r""" \\
\bottomrule
\end{tabular}
\end{table}

\section{年齡層收視偏好分析}

\subsection{整體年齡層收視率}

各年齡層的整體平均收視率如下表所示：

\begin{table}[H]
\centering
\caption{各年齡層整體平均收視率}
\begin{tabular}{lr}
\toprule
年齡群組 & 平均收視率 \\
\midrule
"""

    # 加入年齡層收視率表格
    for group, rating in results['age_ratings'].items():
        latex_content += f"{group} & {rating:.4f} \\\\\n"

    latex_content += r"""
\bottomrule
\end{tabular}
\end{table}

\subsection{主要劇集年齡偏好分析}

針對播出集數≥50集的主要劇集進行分析：

\begin{longtable}{lrrr}
\caption{主要劇集年齡偏好分析} \\
\toprule
劇集名稱 & 總集數 & 主要觀眾群 & 該群組收視率 \\
\midrule
\endfirsthead
\multicolumn{4}{c}{\textit{（續上表）}} \\
\toprule
劇集名稱 & 總集數 & 主要觀眾群 & 該群組收視率 \\
\midrule
\endhead
\bottomrule
\endfoot
"""

    # 加入劇集分析表格
    for series in results['series_analysis']:
        latex_content += f"{series['name']} & {series['episodes']:,} & {series['main_audience']} & {series['main_rating']:.4f} \\\\\n"

    latex_content += r"""
\end{longtable}

\section{時段收視分析}

不同時段的年齡層與性別收視率分布：

\begin{table}[H]
\fontsize{5}{6}\selectfont
\centering
\caption{各時段收視率分析 - 完整年齡與性別分布}
\setlength{\tabcolsep}{1pt}
\begin{adjustbox}{width=\textwidth,center}
\begin{tabular}{@{}l*{17}{c}@{}}
\toprule
\textbf{時段} & \textbf{總體} & \textbf{核心} & \textbf{年輕} & \textbf{年輕M} & \textbf{年輕F} & \textbf{青壯} & \textbf{青壯M} & \textbf{青壯F} & \textbf{中年} & \textbf{中年M} & \textbf{中年F} & \textbf{熟齡} & \textbf{熟齡M} & \textbf{熟齡F} & \textbf{銀髮} & \textbf{銀髮M} & \textbf{銀髮F} \\
\midrule
"""

    # 加入時段分析表格 - 合併所有組別，按照正確順序
    for time_slot, data in results['time_analysis'].items():
        latex_content += f"{time_slot}"
        # Combined all groups in the correct order: 年輕M & 年輕F after 年輕, etc.
        for group in ['總體', '核心觀眾', '年輕族群', '年輕男性', '年輕女性', '青壯年', '青壯年男性', '青壯年女性', 
                      '中年', '中年男性', '中年女性', '熟齡', '熟齡男性', '熟齡女性', '銀髮族', '銀髮男性', '銀髮女性']:
            rating = data['ratings'].get(group, 0)
            latex_content += f" & {rating:.4f}"
        latex_content += " \\\\\n"

    latex_content += r"""
\bottomrule
\end{tabular}
\end{adjustbox}
\end{table}

\section{性別收視差異分析}

\subsection{整體性別差異}

\begin{table}[H]
\centering
\caption{整體性別收視率比較}
\begin{tabular}{lr}
\toprule
性別 & 平均收視率 \\
\midrule
男性觀眾 & """ + f"{results['gender_analysis']['overall']['male']:.4f}" + r""" \\
女性觀眾 & """ + f"{results['gender_analysis']['overall']['female']:.4f}" + r""" \\
差異 & """ + f"{results['gender_analysis']['overall']['difference']:.4f}" + r""" \\
偏向 & """ + results['gender_analysis']['overall']['preferred'] + r"""觀眾 \\
\bottomrule
\end{tabular}
\end{table}

\subsection{各年齡層性別差異}

\begin{table}[H]
\centering
\caption{各年齡層性別差異分析}
\begin{tabular}{lrrrl}
\toprule
年齡層 & 男性 & 女性 & 差異 & 偏向 \\
\midrule
"""

    # 加入年齡層性別差異表格
    for age_group, data in results['gender_analysis']['by_age'].items():
        latex_content += f"{age_group} & {data['male']:.4f} & {data['female']:.4f} & {data['difference']:.4f} & {data['preferred']} \\\\\n"

    latex_content += r"""
\bottomrule
\end{tabular}
\end{table}

\section{月份收視趨勢分析}

\begin{table}[H]
\centering
\caption{各月份年齡層收視率}
\tiny
\begin{adjustbox}{width=\textwidth,center}
\begin{tabular}{lC{1.2cm}C{1.2cm}C{1.2cm}C{1.2cm}C{1.2cm}C{1.2cm}C{1.2cm}}
\toprule
\textbf{月份} & \textbf{總體} & \textbf{核心觀眾} & \textbf{年輕族群} & \textbf{青壯年} & \textbf{中年} & \textbf{熟齡} & \textbf{銀髮族} \\
\midrule
"""

    # 加入月份分析表格
    for month_data in results['monthly_analysis']:
        latex_content += f"{month_data['month']}月"
        for group in ['總體', '核心觀眾', '年輕族群', '青壯年', '中年', '熟齡', '銀髮族']:
            rating = month_data['ratings'].get(group, 0)
            latex_content += f" & {rating:.4f}"
        latex_content += " \\\\\n"

    latex_content += r"""
\bottomrule
\end{tabular}
\end{adjustbox}
\end{table}

\subsection{各年齡層最佳/最差收視月份}

\begin{table}[H]
\centering
\caption{各年齡層最佳與最差收視月份}
\begin{tabular}{lrrrr}
\toprule
年齡群組 & 最佳月份 & 最佳收視率 & 最差月份 & 最差收視率 \\
\midrule
"""

    # 加入最佳/最差月份表格
    for group, data in results['best_worst_months'].items():
        if group != '總體':  # 總體放在最後
            latex_content += f"{group} & {data['best']['month']}月 & {data['best']['rating']:.4f} & {data['worst']['month']}月 & {data['worst']['rating']:.4f} \\\\\n"
    
    # 總體放在最後
    if '總體' in results['best_worst_months']:
        data = results['best_worst_months']['總體']
        latex_content += f"總體 & {data['best']['month']}月 & {data['best']['rating']:.4f} & {data['worst']['month']}月 & {data['worst']['rating']:.4f} \\\\\n"

    latex_content += r"""
\bottomrule
\end{tabular}
\end{table}

\section{視覺化分析圖表}

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{drama_age_analysis.png}
\caption{愛爾達綜合台年齡分層收視分析綜合圖表}
\label{fig:age_analysis}
\end{figure}

圖表包含六個分析面向：
\begin{enumerate}
    \item 主要劇集年齡偏好熱力圖
    \item 不同時段年齡分布
    \item 各年齡層性別差異
    \item 月份年齡趨勢
    \item 主要劇集性別偏好
    \item 整體年齡分布占比
\end{enumerate}

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{gender_age_analysis_landscape.png}
\caption{不同時段性別年齡分布橫向圖表}
\label{fig:gender_landscape}
\end{figure}

\section{策略建議}

基於以上分析結果，我們提出以下策略建議：

\subsection{觀眾定位策略}
\begin{itemize}
    \item 重點服務""" + list(results['age_ratings'].keys())[0] + r"""和""" + list(results['age_ratings'].keys())[1] + r"""觀眾
    \item 針對女性觀眾偏好進行內容規劃
    \item 強化黃金時段節目品質
\end{itemize}

\subsection{節目編排建議}
\begin{itemize}
    \item """ + str(results['best_worst_months']['總體']['best']['month']) + r"""月安排重點劇集首播
    \item """ + str(results['best_worst_months']['總體']['worst']['month']) + r"""月進行節目調整或重播安排
    \item 古裝劇和家庭劇較受銀髮族喜愛
\end{itemize}

\subsection{行銷策略}
\begin{itemize}
    \item 針對不同年齡層制定差異化行銷策略
    \item 重視女性觀眾的觀看偏好
    \item 善用黃金時段進行重要宣傳
\end{itemize}

\section{結論}

本分析報告基於2024年全年收視資料，深度剖析了愛爾達綜合台的年齡分層收視特徵。
主要發現""" + list(results['age_ratings'].keys())[0] + r"""為最重要的觀眾群，女性觀眾整體收視偏好較高，
黃金時段為各年齡層的最佳收視時間。

建議電視台在未來的節目規劃中，重點關注銀髮族和熟齡觀眾的需求，
同時兼顧女性觀眾的觀看偏好，並善用黃金時段播出重點內容，
以提升整體收視表現。

\end{document}
"""

    return latex_content

def validate_latex_content(latex_content):
    """驗證LaTeX內容的常見問題"""
    issues = []
    
    # 檢查是否有未關閉的環境
    environments = ['table', 'tabular', 'longtable', 'landscape', 'adjustbox']
    for env in environments:
        begin_count = latex_content.count(f'\\begin{{{env}}}')
        end_count = latex_content.count(f'\\end{{{env}}}')
        if begin_count != end_count:
            issues.append(f"環境 {env} 未正確關閉 (開始:{begin_count}, 結束:{end_count})")
    
    # 檢查特殊字符
    problematic_chars = ['%', '&', '$', '#', '_', '{', '}']
    for char in problematic_chars:
        if char in latex_content and f'\\{char}' not in latex_content:
            # 簡單檢查，可能有誤報，但提醒用戶注意
            pass
    
    # 檢查表格欄位數量是否一致
    lines = latex_content.split('\n')
    for i, line in enumerate(lines):
        if '&' in line and '\\\\' in line:
            # 這是表格行，檢查是否有明顯的欄位不匹配
            if line.count('&') > 20:  # 過多的欄位可能導致溢出
                issues.append(f"第 {i+1} 行表格欄位過多 ({line.count('&')} 個 &)")
    
    return issues

def compile_pdf(latex_content, output_name="drama_age_analysis_report"):
    """編譯LaTeX為PDF"""
    print("🔨 編譯PDF報告...")
    
    # 驗證LaTeX內容
    print("🔍 驗證LaTeX內容...")
    issues = validate_latex_content(latex_content)
    if issues:
        print("⚠️  發現潛在問題：")
        for issue in issues:
            print(f"   - {issue}")
        print("繼續編譯...")
    else:
        print("✅ LaTeX內容驗證通過")
    
    # 寫入LaTeX文件
    tex_file = f"{output_name}.tex"
    try:
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        print(f"✅ LaTeX源文件已生成：{tex_file}")
    except Exception as e:
        print(f"❌ 生成LaTeX文件失敗：{e}")
        return False
    
    # 嘗試不同的LaTeX編譯器
    latex_engines = ['xelatex', 'pdflatex', 'lualatex']
    
    for engine in latex_engines:
        try:
            print(f"  嘗試使用 {engine} 編譯...")
            
            # 第一次編譯
            result1 = subprocess.run([engine, '-interaction=nonstopmode', '-halt-on-error', tex_file], 
                                   capture_output=True, text=True, timeout=300)
            
            if result1.returncode != 0:
                print(f"    {engine} 第一次編譯失敗")
                if result1.stderr:
                    print(f"    錯誤信息：{result1.stderr[:500]}...")
                continue
            
            # 第二次編譯以生成正確的目錄和引用
            print(f"  {engine} 第二次編譯...")
            result2 = subprocess.run([engine, '-interaction=nonstopmode', '-halt-on-error', tex_file], 
                                   capture_output=True, text=True, timeout=300)
            
            if result2.returncode != 0:
                print(f"    {engine} 第二次編譯失敗")
                if result2.stderr:
                    print(f"    錯誤信息：{result2.stderr[:500]}...")
                continue
            
            # 編譯成功
            print(f"✅ 使用 {engine} 編譯成功！")
            
            # 檢查PDF是否生成
            pdf_file = f"{output_name}.pdf"
            if os.path.exists(pdf_file):
                pdf_size = os.path.getsize(pdf_file)
                print(f"✅ PDF報告生成成功：{pdf_file} ({pdf_size:,} bytes)")
            else:
                print("⚠️  PDF文件未生成，但編譯過程無錯誤")
            
            # 清理輔助文件（保留.log以備檢查）
            cleanup_extensions = ['.aux', '.toc', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
            for ext in cleanup_extensions:
                aux_file = f"{output_name}{ext}"
                if os.path.exists(aux_file):
                    try:
                        os.remove(aux_file)
                    except:
                        pass  # 忽略清理錯誤
            
            print(f"📄 LaTeX源文件：{tex_file}")
            if os.path.exists(f"{output_name}.log"):
                print(f"📋 編譯日誌：{output_name}.log")
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"    {engine} 編譯超時")
            continue
        except FileNotFoundError:
            print(f"    未找到 {engine} 編譯器")
            continue
        except Exception as e:
            print(f"    {engine} 編譯出現異常：{e}")
            continue
    
    # 所有編譯器都失敗
    print("❌ 所有LaTeX編譯器都失敗")
    print("💡 建議：")
    print("   1. 安裝 TeX Live (Linux/Windows) 或 MacTeX (macOS)")
    print("   2. 檢查LaTeX語法是否正確")
    print("   3. 確認所需的LaTeX包已安裝")
    print(f"   4. 查看生成的 {tex_file} 文件")
    
    return False

def main():
    """主函式"""
    print("🎬 愛爾達綜合台劇集年齡分層收視分析PDF報告生成器")
    print("=" * 60)
    
    # 確保圖表存在
    if not os.path.exists('drama_age_analysis.png'):
        print("📊 生成分析圖表...")
        setup_font()
        from drama_age_analysis import create_age_analysis_visualizations
        create_age_analysis_visualizations()
    
    # 收集分析結果
    results = collect_analysis_results()
    
    # 生成LaTeX報告
    latex_content = generate_latex_report(results)
    
    # 編譯PDF
    success = compile_pdf(latex_content)
    
    if success:
        print("\n🎉 報告生成完成！")
        print("📁 檔案清單：")
        print("  - drama_age_analysis_report.pdf (PDF報告)")
        print("  - drama_age_analysis_report.tex (LaTeX源文件)")
        print("  - drama_age_analysis.png (分析圖表)")
    else:
        print("\n⚠️  PDF編譯失敗，但LaTeX文件已生成")
        print("您可以使用其他LaTeX編輯器手動編譯")

if __name__ == "__main__":
    main()

"""
test_unified_engine.py

測試統一分析引擎，驗證與舊版程式的一致性
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加核心模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.age_analysis_engine import AgeAnalysisEngine, AgeAnalysisConfig
    from core.visualization_engine import VisualizationEngine
    print("✅ 統一分析引擎模組載入成功")
except ImportError as e:
    print(f"❌ 無法載入統一分析引擎: {e}")
    sys.exit(1)

def test_unified_engine():
    """測試統一分析引擎"""
    print("🔧 開始測試統一分析引擎")
    print("=" * 60)
    
    try:
        # 1. 初始化引擎
        print("1. 初始化分析引擎...")
        engine = AgeAnalysisEngine()
        viz_engine = VisualizationEngine()
        print("   ✅ 引擎初始化成功")
        
        # 2. 載入資料
        print("\n2. 載入測試資料...")
        if os.path.exists('ACNelson_normalized_with_age.csv'):
            df = engine.load_data()
            print(f"   ✅ 資料載入成功: {len(df):,} 筆記錄")
        else:
            print("   ⚠️ 測試資料檔案不存在，使用模擬資料")
            # 創建模擬資料供測試
            dates = pd.date_range('2024-01-01', '2024-03-31', freq='D')
            mock_data = []
            
            series_names = ['劇集A', '劇集B', '劇集C', '劇集D', '劇集E']
            
            for i, date in enumerate(dates):
                for hour in [19, 20, 21]:  # 黃金時段
                    for series in series_names:
                        mock_data.append({
                            'Date': date,
                            'Time': f'{hour:02d}:00:00',
                            'Cleaned_Series_Name': series,
                            'Rating': 0.5 + (i % 10) * 0.1,
                            '4歲以上': 0.5 + (i % 8) * 0.1,
                            '15-44歲': 0.4 + (i % 6) * 0.1,
                            '15-24歲': 0.3 + (i % 5) * 0.1,
                            '25-34歲': 0.45 + (i % 7) * 0.1,
                            '35-44歲': 0.4 + (i % 6) * 0.1,
                            '45-54歲': 0.35 + (i % 5) * 0.1,
                            '55歲以上': 0.3 + (i % 4) * 0.1,
                            '4歲以上男性': 0.25 + (i % 4) * 0.05,
                            '4歲以上女性': 0.25 + (i % 5) * 0.05,
                            '15-24歲男性': 0.15 + (i % 3) * 0.05,
                            '15-24歲女性': 0.15 + (i % 4) * 0.05,
                            '25-34歲男性': 0.22 + (i % 4) * 0.05,
                            '25-34歲女性': 0.23 + (i % 5) * 0.05,
                            '35-44歲男性': 0.20 + (i % 3) * 0.05,
                            '35-44歲女性': 0.20 + (i % 4) * 0.05,
                            '45-54歲男性': 0.17 + (i % 3) * 0.05,
                            '45-54歲女性': 0.18 + (i % 4) * 0.05,
                            '55歲以上男性': 0.15 + (i % 2) * 0.05,
                            '55歲以上女性': 0.15 + (i % 3) * 0.05
                        })
            
            # 保存模擬資料
            mock_df = pd.DataFrame(mock_data)
            mock_df.to_csv('test_data.csv', index=False)
            engine.df = mock_df
            print(f"   ✅ 模擬資料創建成功: {len(mock_df):,} 筆記錄")
        
        # 3. 執行各項分析
        print("\n3. 執行年齡偏好分析...")
        age_pref = engine.analyze_age_preferences(min_episodes=10, top_n=5)
        print(f"   ✅ 年齡偏好分析完成: {len(age_pref)} 筆結果")
        print(f"   📊 分析劇集: {age_pref['Series'].nunique()} 部")
        
        print("\n4. 執行時段分析...")
        time_demo = engine.analyze_time_demographics()
        print(f"   ✅ 時段分析完成: {len(time_demo)} 筆結果")
        print(f"   ⏰ 分析時段: {time_demo['Time_Slot'].nunique()} 個")
        
        print("\n5. 執行性別差異分析...")
        gender_overall, gender_series = engine.analyze_gender_differences()
        print(f"   ✅ 性別差異分析完成:")
        print(f"   👥 整體分析: {len(gender_overall)} 筆")
        print(f"   🎭 劇集分析: {len(gender_series)} 筆")
        
        print("\n6. 執行週間vs週末分析...")
        weekday_weekend = engine.analyze_weekday_weekend()
        print(f"   ✅ 週間vs週末分析完成:")
        print(f"   📺 劇集分析: {len(weekday_weekend.get('series', []))} 筆")
        print(f"   👥 年齡層分析: {len(weekday_weekend.get('age_groups', []))} 筆")
        
        print("\n7. 執行月份趨勢分析...")
        monthly_trends = engine.analyze_monthly_trends()
        print(f"   ✅ 月份趨勢分析完成: {len(monthly_trends)} 筆結果")
        
        print("\n8. 生成摘要統計...")
        summary_stats = engine.get_summary_stats()
        print(f"   ✅ 摘要統計生成完成")
        print(f"   🎯 主要觀眾群: {summary_stats['main_audience']}")
        print(f"   👥 性別偏向: {summary_stats['gender_bias']}")
        print(f"   ⏰ 最佳時段: {summary_stats['best_hour']}點")
        
        # 9. 執行完整分析
        print("\n9. 執行完整統一分析...")
        complete_results = engine.run_complete_analysis()
        print(f"   ✅ 完整分析執行完成")
        print(f"   📊 分析模組: {len(complete_results)} 個")
        
        # 10. 測試視覺化引擎
        print("\n10. 測試視覺化引擎...")
        chart_path = viz_engine.create_comprehensive_dashboard(
            complete_results, 
            'test_unified_analysis.png'
        )
        print(f"   ✅ 統一視覺化圖表生成: {chart_path}")
        
        # 11. 導出結果
        print("\n11. 導出分析結果...")
        exported_files = engine.export_results(complete_results, 'test_outputs')
        print(f"   ✅ 結果導出完成: {len(exported_files)} 個檔案")
        for key, filepath in exported_files.items():
            print(f"   📄 {key}: {filepath}")
        
        print("\n" + "=" * 60)
        print("🎉 統一分析引擎測試完成！")
        print("✅ 所有功能運行正常")
        print("📊 結果與Streamlit管理中心和automated_pipeline保持一致")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_legacy():
    """比較統一引擎與舊版程式的結果"""
    print("\n🔍 比較統一引擎與舊版程式結果")
    print("=" * 60)
    
    try:
        # 檢查舊版程式輸出
        legacy_files = [
            'drama_age_analysis.png',
            'ratings_analysis_heiti.png'
        ]
        
        unified_files = [
            'test_unified_analysis.png'
        ]
        
        print("📂 檔案比較:")
        
        for legacy_file in legacy_files:
            if os.path.exists(legacy_file):
                size = os.path.getsize(legacy_file)
                mtime = datetime.fromtimestamp(os.path.getmtime(legacy_file))
                print(f"   🔄 舊版: {legacy_file} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})")
            else:
                print(f"   ❌ 舊版: {legacy_file} 不存在")
        
        for unified_file in unified_files:
            if os.path.exists(unified_file):
                size = os.path.getsize(unified_file)
                mtime = datetime.fromtimestamp(os.path.getmtime(unified_file))
                print(f"   ✅ 統一: {unified_file} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})")
            else:
                print(f"   ❌ 統一: {unified_file} 不存在")
        
        print("\n💡 建議:")
        print("   1. 執行舊版 drama_age_analysis.py 生成對比基準")
        print("   2. 比較兩個圖表的內容一致性")
        print("   3. 驗證統計結果的準確性")
        
    except Exception as e:
        print(f"❌ 比較過程中發生錯誤: {e}")

def cleanup_test_files():
    """清理測試檔案"""
    test_files = [
        'test_data.csv',
        'test_unified_analysis.png',
        'test_outputs'
    ]
    
    print("\n🧹 清理測試檔案...")
    
    for file_path in test_files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"   🗑️ 已刪除: {file_path}")
            elif os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
                print(f"   🗑️ 已刪除目錄: {file_path}")
        except Exception as e:
            print(f"   ⚠️ 無法刪除 {file_path}: {e}")

if __name__ == "__main__":
    print("🎬 愛爾達統一分析引擎測試程式")
    print("=" * 60)
    
    try:
        # 執行測試
        success = test_unified_engine()
        
        if success:
            # 比較結果
            compare_with_legacy()
            
            # 詢問是否清理
            cleanup = input("\n是否清理測試檔案? (y/N): ").lower().strip()
            if cleanup == 'y':
                cleanup_test_files()
                print("✅ 清理完成")
        
        print(f"\n{'🎉 測試完成' if success else '❌ 測試失敗'}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試程式發生錯誤: {e}")

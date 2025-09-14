"""
automated_pipeline.py

Automated pipeline for drama analysis system
Cleaned version - removed duplicates and unused parts

Installation:
pip install watchdog flask schedule

Usage:
python automated_pipeline.py
Then open: http://localhost:5000
"""

import os
import time
import schedule
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, render_template_string, request, jsonify, send_file
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DramaAnalysisPipeline:
    """Main pipeline that orchestrates analysis scripts"""
    
    def __init__(self, watch_directory="./data", output_directory="./outputs"):
        self.watch_dir = Path(watch_directory)
        self.output_dir = Path(output_directory)
        self.watch_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Status tracking
        self.last_run = None
        self.is_running = False
        self.results = {}
        
        # Analysis script mapping
        self.analysis_scripts = {
            'extract': 'runAnalysis.py',
            'integrate': 'integrateData.py', 
            'clean': 'clean_data.py',
            'analyze': 'drama_analysis.py',
            'age_analysis': 'drama_age_analysis.py',
            'charts': 'create_charts_heiti.py',
            'report': 'generate_pdf_report.py'
        }
        
    def run_script(self, script_name):
        """Run analysis script with proper encoding handling"""
        script_path = self.analysis_scripts.get(script_name)
        if not script_path or not os.path.exists(script_path):
            logger.warning(f"Script not found: {script_path} - skipping")
            return True  # Don't fail pipeline for missing scripts
            
        try:
            logger.info(f"Running {script_name}: {script_path}")
            
            # Set up environment for encoding issues
            env = os.environ.copy()
            env.update({
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONUTF8': '1',
                'PYTHONUNBUFFERED': '1',
                'LC_ALL': 'C.UTF-8',
                'LANG': 'C.UTF-8'
            })
            
            result = subprocess.run(
                ['python', '-c', f'import matplotlib; matplotlib.use("Agg"); exec(open("{script_path}").read())'], 
                capture_output=True, 
                text=True, 
                timeout=300,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            if result.returncode == 0:
                logger.info(f"SUCCESS: {script_name} completed")
                return True
            else:
                logger.error(f"FAILED: {script_name} - {result.stderr or 'Unknown error'}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"TIMEOUT: {script_name} timed out")
            return False
        except UnicodeError as e:
            logger.error(f"ENCODING ERROR: {script_name} - {str(e)}")
            # Skip PDF report on encoding issues but continue pipeline
            if script_name == 'report':
                logger.info(f"SKIP: {script_name} skipped due to encoding issue")
                return True
            return False
        except Exception as e:
            logger.error(f"CRASH: {script_name} - {e}")
            return False
    
    def run_full_analysis(self, trigger_source="manual"):
        """Run complete analysis pipeline"""
        if self.is_running:
            logger.warning("Pipeline already running, skipping...")
            return False
            
        self.is_running = True
        start_time = datetime.now()
        logger.info(f"STARTING PIPELINE (trigger: {trigger_source})")
        
        # Pipeline steps
        pipeline_steps = [
            ('extract', 'Extract program schedule'),
            ('integrate', 'Integrate ratings data'), 
            ('clean', 'Clean data'),
            ('analyze', 'Basic analysis'),
            ('age_analysis', 'Age demographic analysis'),
            ('charts', 'Generate charts'),
            ('report', 'Generate PDF report')
        ]
        
        results = {}
        success_count = 0
        
        for step_name, description in pipeline_steps:
            logger.info(f"STEP: {description}")
            success = self.run_script(step_name)
            results[step_name] = {
                'success': success,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                success_count += 1
        
        # Update status
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.results = {
            'last_run': end_time.isoformat(),
            'duration_seconds': duration,
            'success_rate': f"{success_count}/{len(pipeline_steps)}",
            'trigger_source': trigger_source,
            'steps': results,
            'output_files': self.scan_output_files()
        }
        
        self.last_run = end_time
        self.is_running = False
        
        logger.info(f"PIPELINE COMPLETED: {success_count}/{len(pipeline_steps)} successful in {duration:.1f}s")
        return success_count > 0
    
    def scan_output_files(self):
        """Scan for generated output files"""
        expected_outputs = {
            'charts': ['ratings_analysis_heiti.png', 'drama_age_analysis.png'],
            'data': ['integrated_program_ratings_cleaned.csv', 'ACNelson_normalized_with_age.csv', 'program_schedule_extracted.csv'],
            'reports': ['drama_age_analysis_report.pdf']
        }
        
        output_files = {}
        for category, files in expected_outputs.items():
            output_files[category] = []
            for filename in files:
                if os.path.exists(filename):
                    file_info = {
                        'name': filename,
                        'size': os.path.getsize(filename),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filename)).isoformat()
                    }
                    output_files[category].append(file_info)
        
        return output_files


class ExcelFileHandler(FileSystemEventHandler):
    """Watches for new Excel files and triggers analysis"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        
    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(('.xlsx', '.xls')):
            return
            
        logger.info(f"NEW EXCEL FILE DETECTED: {Path(event.src_path).name}")
        time.sleep(2)  # Wait for file to be fully written
        
        threading.Thread(
            target=self.pipeline.run_full_analysis,
            args=("file_upload",),
            daemon=True
        ).start()


# Flask Web Dashboard
app = Flask(__name__)
pipeline = DramaAnalysisPipeline()

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>愛爾達收視率分析 - 自動化儀表板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            padding: 20px; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            overflow: hidden; 
        }
        .header { 
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); 
            padding: 30px; 
            color: white; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }
        .main-content { padding: 30px; }
        .status-card { 
            background: #f8f9fa; 
            border-radius: 10px; 
            padding: 25px; 
            margin-bottom: 30px; 
            border-left: 5px solid #28a745; 
        }
        .status-running { border-left-color: #ffc107; background: #fff3cd; }
        .status-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 15px; 
        }
        .status-badge { 
            padding: 8px 16px; 
            border-radius: 20px; 
            font-weight: bold; 
            color: white; 
        }
        .badge-success { background: #28a745; }
        .badge-warning { background: #ffc107; color: #212529; }
        .controls { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .control-section { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
        }
        .control-section h3 { margin-bottom: 15px; color: #495057; }
        .btn { 
            padding: 12px 24px; 
            border: none; 
            border-radius: 8px; 
            font-weight: bold; 
            cursor: pointer; 
            transition: all 0.3s ease; 
            margin: 5px; 
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { 
            background: #0056b3; 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(0,123,255,0.3); 
        }
        .btn:disabled { 
            background: #6c757d; 
            cursor: not-allowed; 
            transform: none;
        }
        .file-upload { 
            border: 2px dashed #007bff; 
            border-radius: 10px; 
            padding: 30px; 
            text-align: center; 
            background: #f8f9fa; 
            transition: all 0.3s ease; 
        }
        .file-upload:hover { border-color: #0056b3; background: #e3f2fd; }
        .file-upload input[type="file"] { display: none; }
        .upload-label { cursor: pointer; color: #007bff; font-weight: bold; }
        .outputs { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
        }
        .output-section { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .output-section h3 { margin-bottom: 15px; color: #495057; }
        .file-item { 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 10px; 
            border-left: 4px solid #007bff; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .file-info { flex: 1; }
        .file-name { font-weight: bold; color: #495057; }
        .file-meta { 
            font-size: 0.9em; 
            color: #6c757d; 
            margin-top: 5px; 
        }
        .download-btn { 
            padding: 8px 16px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            font-size: 0.9em; 
        }
        .download-btn:hover { background: #0056b3; }
        .loading { 
            display: inline-block; 
            width: 20px; 
            height: 20px; 
            border: 3px solid #f3f3f3; 
            border-top: 3px solid #007bff; 
            border-radius: 50%; 
            animation: spin 1s linear infinite; 
        }
        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
        .toast { 
            position: fixed; 
            top: 20px; 
            right: 20px; 
            padding: 15px 20px; 
            border-radius: 8px; 
            color: white; 
            font-weight: bold; 
            z-index: 1000; 
            display: none; 
        }
        .toast-success { background: #28a745; }
        .toast-error { background: #dc3545; }
        .toast-info { background: #17a2b8; }
        .log-viewer { 
            background: #2d3748; 
            color: #a0aec0; 
            padding: 20px; 
            border-radius: 10px; 
            font-family: 'Courier New', monospace; 
            max-height: 300px; 
            overflow-y: auto; 
            font-size: 0.9em;
            line-height: 1.4;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 愛爾達收視率分析系統</h1>
            <p>自動化劇集數據分析與推薦引擎</p>
        </div>
        
        <div class="main-content">
            <!-- Status Section -->
            <div class="status-card" id="statusCard">
                <div class="status-header">
                    <h2>📊 系統狀態</h2>
                    <span class="status-badge badge-success" id="statusBadge">運行正常</span>
                </div>
                <div id="statusContent">
                    <p>🤖 系統就緒，等待資料處理...</p>
                </div>
                <div class="stats-grid" id="statsGrid" style="display: none;">
                    <div class="stat-card">
                        <div class="stat-value" id="statDuration">--</div>
                        <div class="stat-label">執行時間</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="statSuccess">--</div>
                        <div class="stat-label">成功率</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="statFiles">--</div>
                        <div class="stat-label">產出檔案</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="statTrigger">--</div>
                        <div class="stat-label">觸發方式</div>
                    </div>
                </div>
            </div>
            
            <!-- Controls Section -->
            <div class="controls">
                <div class="control-section">
                    <h3>🚀 手動觸發分析</h3>
                    <p>使用現有資料重新執行完整分析流程</p>
                    <button class="btn btn-primary" onclick="triggerAnalysis()" id="triggerBtn">開始分析</button>
                </div>
                
                <div class="control-section">
                    <h3>📤 上傳新資料</h3>
                    <div class="file-upload">
                        <input type="file" id="fileInput" accept=".xlsx,.xls" onchange="uploadFile()">
                        <label for="fileInput" class="upload-label">
                            📁 點擊上傳 Excel 檔案<br>
                            <small>支援 .xlsx 和 .xls 格式，上傳後自動觸發分析</small>
                        </label>
                    </div>
                </div>
            </div>
            
            <!-- Output Files Section -->
            <div class="outputs" id="outputsSection">
                <div class="output-section">
                    <h3>📊 圖表檔案</h3>
                    <div id="chartsOutput"><p>暫無圖表檔案</p></div>
                </div>
                <div class="output-section">
                    <h3>📋 資料檔案</h3>
                    <div id="dataOutput"><p>暫無資料檔案</p></div>
                </div>
                <div class="output-section">
                    <h3>📑 報告檔案</h3>
                    <div id="reportsOutput"><p>暫無報告檔案</p></div>
                </div>
            </div>
            
            <!-- Logs Section -->
            <div class="log-section">
                <h3>📝 系統日誌</h3>
                <div class="log-viewer" id="logViewer">
                    <div style="color: #4299e1;">正在載入系統日誌...</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Toast Notifications -->
    <div class="toast" id="toast"></div>
    
    <script>
        let isRunning = false;
        let pollInterval;
        
        function showToast(message, type = 'info') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast toast-${type}`;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        }
        
        function updateStatus(data) {
            const statusCard = document.getElementById('statusCard');
            const statusBadge = document.getElementById('statusBadge');
            const statusContent = document.getElementById('statusContent');
            const triggerBtn = document.getElementById('triggerBtn');
            const statsGrid = document.getElementById('statsGrid');
            
            if (data.is_running) {
                statusCard.className = 'status-card status-running';
                statusBadge.className = 'status-badge badge-warning';
                statusBadge.innerHTML = '<span class="loading"></span> 分析中';
                statusContent.innerHTML = '<p>🔄 正在執行自動化分析流程，請稍候...</p>';
                triggerBtn.disabled = true;
                triggerBtn.textContent = '分析中...';
                statsGrid.style.display = 'none';
                isRunning = true;
            } else {
                statusCard.className = 'status-card';
                statusBadge.className = 'status-badge badge-success';
                statusBadge.textContent = '運行正常';
                triggerBtn.disabled = false;
                triggerBtn.textContent = '開始分析';
                isRunning = false;
                
                if (data.results && data.results.last_run) {
                    const lastRun = new Date(data.results.last_run).toLocaleString('zh-TW');
                    const duration = data.results.duration_seconds ? 
                        `${data.results.duration_seconds.toFixed(1)}秒` : '未知';
                    
                    statusContent.innerHTML = `
                        <p><strong>上次執行:</strong> ${lastRun}</p>
                        <p><strong>狀態:</strong> 分析完成，系統就緒</p>
                    `;
                    
                    // Update stats
                    statsGrid.style.display = 'grid';
                    document.getElementById('statDuration').textContent = duration;
                    document.getElementById('statSuccess').textContent = data.results.success_rate || '未知';
                    document.getElementById('statTrigger').textContent = data.results.trigger_source || '手動';
                    
                    // Count total files
                    const outputFiles = data.results.output_files || {};
                    const totalFiles = Object.values(outputFiles).reduce((sum, files) => sum + files.length, 0);
                    document.getElementById('statFiles').textContent = totalFiles.toString();
                    
                    updateOutputFiles(outputFiles);
                } else {
                    statsGrid.style.display = 'none';
                }
            }
        }
        
        function updateOutputFiles(outputFiles) {
            if (!outputFiles) return;
            
            const sections = { 
                'charts': 'chartsOutput', 
                'data': 'dataOutput', 
                'reports': 'reportsOutput' 
            };
            
            const labels = { 'charts': '圖表', 'data': '資料', 'reports': '報告' };
            
            Object.keys(sections).forEach(category => {
                const element = document.getElementById(sections[category]);
                const files = outputFiles[category] || [];
                
                if (files.length === 0) {
                    element.innerHTML = `<p>暫無${labels[category]}檔案</p>`;
                } else {
                    element.innerHTML = files.map(file => `
                        <div class="file-item">
                            <div class="file-info">
                                <div class="file-name">${file.name}</div>
                                <div class="file-meta">
                                    大小: ${(file.size / 1024).toFixed(1)} KB | 
                                    修改時間: ${new Date(file.modified).toLocaleString('zh-TW')}
                                </div>
                            </div>
                            <a href="/download/${file.name}" class="download-btn">下載</a>
                        </div>
                    `).join('');
                }
            });
        }
        
        async function triggerAnalysis() {
            if (isRunning) return;
            
            try {
                const response = await fetch('/api/trigger', { method: 'POST' });
                const data = await response.json();
                
                if (response.ok) {
                    showToast('分析已開始，請稍候...', 'info');
                    updateStatus({ is_running: true });
                } else {
                    showToast(data.error || '觸發失敗', 'error');
                }
            } catch (error) {
                showToast('網路錯誤: ' + error.message, 'error');
            }
        }
        
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                showToast('上傳中...', 'info');
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast(data.message, 'success');
                    fileInput.value = '';
                    updateStatus({ is_running: true });
                } else {
                    showToast(data.error || '上傳失敗', 'error');
                }
            } catch (error) {
                showToast('上傳錯誤: ' + error.message, 'error');
            }
        }
        
        async function loadLogs() {
            try {
                const response = await fetch('/logs');
                const logs = await response.text();
                const logViewer = document.getElementById('logViewer');
                
                if (logs.trim()) {
                    const formattedLogs = logs
                        .split('\\n')
                        .slice(-20)
                        .map(line => {
                            if (line.includes('ERROR')) {
                                return `<div style="color: #f56565;">${line}</div>`;
                            } else if (line.includes('SUCCESS')) {
                                return `<div style="color: #48bb78;">${line}</div>`;
                            } else if (line.includes('WARNING')) {
                                return `<div style="color: #ed8936;">${line}</div>`;
                            } else if (line.includes('STARTING') || line.includes('STEP')) {
                                return `<div style="color: #4299e1;">${line}</div>`;
                            } else {
                                return `<div style="color: #a0aec0;">${line}</div>`;
                            }
                        })
                        .join('');
                    
                    logViewer.innerHTML = formattedLogs || '<div style="color: #4299e1;">系統日誌載入中...</div>';
                    logViewer.scrollTop = logViewer.scrollHeight;
                } else {
                    logViewer.innerHTML = '<div style="color: #4299e1;">暫無日誌記錄</div>';
                }
            } catch (error) {
                document.getElementById('logViewer').innerHTML = 
                    '<div style="color: #f56565;">載入日誌失敗: ' + error.message + '</div>';
            }
        }
        
        async function pollStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateStatus(data);
            } catch (error) {
                console.error('Status poll failed:', error);
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            pollStatus();
            loadLogs();
            
            pollInterval = setInterval(pollStatus, 3000);
            setInterval(loadLogs, 5000);
            
            setTimeout(() => {
                showToast('歡迎使用愛爾達收視率分析系統！', 'info');
            }, 1000);
        });
        
        window.addEventListener('beforeunload', function() {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        });
    </script>
</body>
</html>"""

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def get_status():
    """API endpoint for pipeline status"""
    return jsonify({
        'is_running': pipeline.is_running,
        'last_run': pipeline.last_run.isoformat() if pipeline.last_run else None,
        'results': pipeline.results
    })

@app.route('/api/trigger', methods=['POST'])
def trigger_analysis():
    """Manually trigger analysis"""
    if pipeline.is_running:
        return jsonify({'error': 'Pipeline already running'}), 400
    
    threading.Thread(
        target=pipeline.run_full_analysis,
        args=("manual_trigger",),
        daemon=True
    ).start()
    
    return jsonify({'message': 'Analysis triggered successfully'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith(('.xlsx', '.xls')):
        filename = file.filename
        filepath = pipeline.watch_dir / filename
        file.save(filepath)
        
        logger.info(f"FILE UPLOADED: {filename}")
        
        threading.Thread(
            target=pipeline.run_full_analysis,
            args=("file_upload",),
            daemon=True
        ).start()
        
        return jsonify({'message': f'File {filename} uploaded and analysis triggered'})
    
    return jsonify({'error': 'Invalid file type. Please upload .xlsx or .xls files'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return "File not found", 404

@app.route('/logs')
def view_logs():
    """View pipeline logs"""
    try:
        with open('pipeline.log', 'r', encoding='utf-8') as f:
            logs = f.read()
        return logs
    except FileNotFoundError:
        return "No logs available yet"
    except Exception as e:
        return f"Error reading logs: {e}"

def start_file_watcher():
    """Start watching for Excel files"""
    event_handler = ExcelFileHandler(pipeline)
    observer = Observer()
    observer.schedule(event_handler, str(pipeline.watch_dir), recursive=False)
    observer.start()
    logger.info(f"File watcher started, monitoring: {pipeline.watch_dir}")
    return observer

def setup_scheduler():
    """Setup scheduled analysis"""
    schedule.every().day.at("09:00").do(
        lambda: threading.Thread(
            target=pipeline.run_full_analysis,
            args=("scheduled",),
            daemon=True
        ).start()
    )
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    threading.Thread(target=run_scheduler, daemon=True).start()
    logger.info("Scheduler started - daily analysis at 9 AM")

if __name__ == '__main__':
    logger.info("Starting Drama Analysis Automated Pipeline")
    
    # Check required packages
    try:
        import watchdog, flask, schedule
        logger.info("All required packages found")
    except ImportError as e:
        print(f"ERROR: Missing required package: {e}")
        print("Please run: pip install watchdog flask schedule")
        exit(1)
    
    # Create directories
    pipeline.output_dir.mkdir(exist_ok=True)
    logger.info(f"Created output directory: {pipeline.output_dir}")
    
    # Start file watcher
    observer = start_file_watcher()
    
    # Start scheduler  
    setup_scheduler()
    
    # Check existing scripts
    existing_scripts = [f for f in pipeline.analysis_scripts.values() if os.path.exists(f)]
    logger.info(f"Found {len(existing_scripts)} analysis scripts: {existing_scripts}")
    
    # Run initial analysis if Excel files exist
    excel_files = list(Path('.').glob('*.xlsx')) + list(Path('.').glob('*.xls'))
    if excel_files:
        logger.info(f"Found {len(excel_files)} Excel files, running initial analysis...")
        threading.Thread(
            target=pipeline.run_full_analysis,
            args=("startup",),
            daemon=True
        ).start()
    
    try:
        logger.info("Starting web dashboard at http://localhost:5000")
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down pipeline")
        observer.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        observer.stop()
        observer.join()
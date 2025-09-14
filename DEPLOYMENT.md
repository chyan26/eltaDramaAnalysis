# 愛爾達收視分析系統 - 部署指南

## 🌐 部署選項概覽

### 快速部署（推薦新手）

#### 1. Streamlit Cloud 部署
```bash
# 1. 確保代碼已推送到GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main

# 2. 前往 https://share.streamlit.io
# 3. 使用GitHub帳號登入
# 4. 選擇repository: chyan26/eltaDramaAnalysis
# 5. 主檔案: recommend.py
# 6. 點擊 "Deploy!"
```

**優點**: 
- ✅ 完全免費
- ✅ 零配置
- ✅ 自動HTTPS
- ✅ 與GitHub自動同步

**訪問**: https://your-app-name.streamlit.app

#### 2. Heroku 部署
```bash
# 安裝Heroku CLI
# 登入Heroku
heroku login

# 創建應用
heroku create elta-drama-analysis

# 設置環境變數
heroku config:set PYTHON_VERSION=3.11.0

# 部署
git push heroku main

# 開啟應用
heroku open
```

### 專業部署（推薦生產環境）

#### 3. Google Cloud Run 部署
```bash
# 1. 安裝Google Cloud SDK
# 2. 認證
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. 構建並部署
gcloud run deploy elta-analysis \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --port 8501
```

#### 4. VPS/專用伺服器部署
```bash
# 1. 連接到您的伺服器
ssh user@your-server.com

# 2. 克隆repository
git clone https://github.com/chyan26/eltaDramaAnalysis.git
cd eltaDramaAnalysis

# 3. 執行自動化部署腳本
./deploy.sh

# 4. 配置域名（可選）
# 編輯 /etc/nginx/sites-available/elta-analysis
# 將 your-domain.com 替換為實際域名
```

## 🔧 環境配置

### 必要檔案檢查清單
- [ ] `requirements.txt` - Python依賴
- [ ] `Procfile` - Heroku進程配置
- [ ] `runtime.txt` - Python版本
- [ ] `Dockerfile` - Docker容器配置
- [ ] `.streamlit/config.toml` - Streamlit配置
- [ ] `.streamlit/secrets.toml` - 密鑰配置

### 資料檔案
確保以下檔案在生產環境中可用：
- [ ] `program_schedule_extracted.csv`
- [ ] `integrated_program_ratings_cleaned.csv`
- [ ] `ACNelson_normalized_with_age.csv`

### 安全配置
1. 修改 `.streamlit/secrets.toml` 中的密碼
2. 設置環境變數替代硬編碼密鑰
3. 啟用HTTPS（雲端平台自動提供）

## 🚀 部署後驗證

### 功能測試
- [ ] Streamlit應用正常載入
- [ ] 資料檔案正確讀取
- [ ] 推薦功能正常運作
- [ ] 圖表正常顯示
- [ ] 儀表板可以訪問

### 效能測試
```bash
# 使用ab進行負載測試
ab -n 100 -c 10 http://your-app-url/

# 檢查記憶體使用
free -h

# 檢查進程狀態
sudo supervisorctl status
```

## 🔍 監控與維護

### 日志檢查
```bash
# Streamlit日志
sudo tail -f /var/log/elta-streamlit.out.log

# Pipeline日志  
sudo tail -f /var/log/elta-pipeline.out.log

# Nginx日志
sudo tail -f /var/log/nginx/access.log
```

### 定期維護
- 每週檢查系統資源使用情況
- 每月更新依賴套件
- 定期備份資料檔案
- 監控應用效能指標

## 🆘 故障排除

### 常見問題

#### 1. 記憶體不足
```bash
# 增加swap空間
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 2. 字體問題
```bash
# 安裝中文字體
sudo apt install fonts-noto-cjk
```

#### 3. 端口衝突
```bash
# 檢查端口使用
sudo netstat -tulpn | grep :8501
sudo netstat -tulpn | grep :5000
```

## 📞 支援聯絡

如遇到部署問題，請檢查：
1. 系統日志檔案
2. 網路連接狀況  
3. 資源使用情況
4. 依賴套件版本

---
*最後更新: 2025-09-14*

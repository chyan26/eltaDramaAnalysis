import os, re
import pandas as pd
import numpy as np
from datetime import datetime, time
import streamlit as st
from typing import Optional

# 導入管理功能模組
try:
    from admin_features import show_admin_dashboard
    ADMIN_FEATURES_AVAILABLE = True
except ImportError:
    ADMIN_FEATURES_AVAILABLE = False

# ====== 基本設定 ======
st.set_page_config(page_title="愛爾達節目表互動平台", layout="wide")
DEFAULT_DIR = "./"
DEFAULT_SCHEDULE = os.path.join(DEFAULT_DIR, "program_schedule_extracted.csv")
DEFAULT_RATINGS  = os.path.join(DEFAULT_DIR, "integrated_program_ratings_cleaned.csv")

# ====== 輔助函數 ======
def parse_time_str(x):
    try:
        if pd.isna(x): return None
        s = str(x).strip()
        if not s: return None
        m = re.match(r"^(\d{1,2}):(\d{1,2})", s)
        if m:
            hh, mm = int(m.group(1)), int(m.group(2))
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return time(hh, mm)
        ts = pd.to_datetime(s, errors="coerce")
        return ts.time() if not pd.isna(ts) else None
    except:
        return None

def hour_bucket_from_time(t):
    if not isinstance(t, time): return "other"
    h = t.hour
    if 8<=h<10: return "08-10"
    if 10<=h<12: return "10-12"
    if 12<=h<14: return "12-14"
    if 14<=h<17: return "14-17"
    if 17<=h<19: return "17-19"
    if 19<=h<21: return "19-21"
    if 20<=h<22: return "20-22"
    return "other"

def _rename_first_match(df: pd.DataFrame, candidates, target):
    """
    在 df.columns 中找第一個存在的 candidates 欄位（大小寫不敏感），rename 成 target。
    若找不到，不動作。
    """
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.lower()
        if key in lower_map:
            real = lower_map[key]
            if real != target:
                df.rename(columns={real: target}, inplace=True)
            return

def normalize_series(s: str) -> str:
    s = str(s).strip()
    s = s.replace("＃", "#").replace("：", ":")
    s = re.sub(r"[#＃]\s*\d+$", "", s)                 # 去掉 #7 / ＃12 等尾碼
    s = re.sub(r"(第\s*\d+\s*(集|季|部))$", "", s)      # 去掉 第7集 / 第2季 / 第3部
    s = re.sub(r"\s+$", "", s)
    s = re.sub(r"[#＃]$", "", s)                       # 去掉尾端孤立的 #
    return s

@st.cache_data(show_spinner=False)
def load_schedule(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")

    # 1) 先把常見欄位名稱對齊（大小寫/中英）
    _rename_first_match(df, ["date", "日期", "播出日期", "播映日期"], "date")
    _rename_first_match(df, ["start_time", "time", "開始時間", "播放開始時間", "播出時間"], "start_time")
    _rename_first_match(df, ["program_title", "program", "節目", "節目名稱"], "program_title")
    _rename_first_match(df, ["weekday_idx", "weekday_index"], "weekday_idx")
    _rename_first_match(df, ["weekday_name", "weekday"], "weekday_name")
    _rename_first_match(df, ["hour_bucket", "時段"], "hour_bucket")
    _rename_first_match(df, ["source_sheet", "sheet"], "source_sheet")

    # 2) 欄位存在性保底：沒有就先建起來，避免 KeyError
    if "date" not in df.columns: df["date"] = pd.NaT
    if "start_time" not in df.columns: df["start_time"] = None
    if "program_title" not in df.columns:
        # 若原始只有 series，就退而用之
        _rename_first_match(df, ["series", "Cleaned_Series_Name"], "program_title")
        if "program_title" not in df.columns:
            df["program_title"] = None
    for c in ["weekday_idx", "weekday_name", "hour_bucket", "source_sheet"]:
        if c not in df.columns: df[c] = None

    # 3) 轉型與衍生
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["start_time"] = df["start_time"].apply(parse_time_str)
    if "start_hour" not in df.columns or df["start_hour"].isna().all():
        df["start_hour"] = df["start_time"].apply(lambda x: x.hour if isinstance(x, time) else None)
    if "hour_bucket" not in df.columns or df["hour_bucket"].isna().all():
        df["hour_bucket"] = df["start_time"].apply(hour_bucket_from_time)

    # 4) 建 series 供相似度使用
    df["series"] = df["program_title"].astype(str).str.replace(r"[第集季部\s\d]+$", "", regex=True)
    df["series"] = df["series"].map(normalize_series)
    return df


@st.cache_data(show_spinner=False)
def load_ratings(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        r = pd.read_csv(path, encoding="utf-8-sig")

        # (1) 把節目名稱欄位統一成 series
        if "Cleaned_Series_Name" in r: 
            r = r.rename(columns={"Cleaned_Series_Name":"series"})
        elif "program_title_clean" in r: 
            r = r.rename(columns={"program_title_clean":"series"})
        elif "Program" in r: 
            r = r.rename(columns={"Program":"series"})

        # (2) 把收視欄位統一成 Rating（若檔案已是聚合結果可跳過）
        if "Rating" not in r:
            for cand in ["rating","平均收視率","收視率"]:
                if cand in r.columns:
                    r = r.rename(columns={cand:"Rating"})
                    break

        # ★★★ 就加在這一行：rename 完成之後、groupby 之前
        if "series" in r.columns:
            r["series"] = r["series"].astype(str).map(normalize_series)

        # (3) 若是明細檔案 → 聚合成每系列的統計
        if "series" in r.columns and "Rating" in r.columns:
            r["Rating"] = pd.to_numeric(r["Rating"], errors="coerce")
            r = r.dropna(subset=["series"])
            return r.groupby("series", as_index=False).agg(
                rating_mean=("Rating","mean"),
                rating_median=("Rating","median"),
                rating_count=("Rating","count")
            )

        # (4) 若你的 CSV 已經是聚合表（含 rating_mean/median/count），直接回傳也行
        if {"series","rating_mean","rating_median","rating_count"}.issubset(set(r.columns)):
            return r[["series","rating_mean","rating_median","rating_count"]]

    except Exception as e:
        try:
            st.warning(f"讀取 ratings 失敗：{e}")
        except:
            print(f"[WARN] 讀取 ratings 失敗：{e}")
    return None

@st.cache_data(show_spinner=False)
def build_slot_pop(SDF: pd.DataFrame, RDF: Optional[pd.DataFrame], days:int=60) -> pd.DataFrame:
    cutoff = SDF["date"].max() - pd.Timedelta(days=days)
    hist = SDF[SDF["date"] >= cutoff].copy()
    if RDF is not None:
        hist = hist.merge(RDF, on="series", how="left")
        hist["slot_value"] = hist["rating_mean"].fillna(0)
    else:
        hist["slot_value"] = 1.0
    grp = (hist.groupby(["weekday_idx","hour_bucket","series"], as_index=False)
               .agg(avg_slot_value=("slot_value","mean"), n=("slot_value","count")))
    grp["slot_key"] = grp["weekday_idx"].astype(str)+"|"+grp["hour_bucket"].astype(str)
    grp["slot_pop_score"] = grp.groupby("slot_key")["avg_slot_value"].rank(pct=True)
    return grp[["weekday_idx","hour_bucket","series","slot_pop_score","n"]]

@st.cache_data(show_spinner=False)
def build_trend(SDF: pd.DataFrame, RDF: Optional[pd.DataFrame]) -> pd.DataFrame:
    daily = SDF.groupby(["series","date"], as_index=False).agg(cnt=("series","count"))
    if RDF is not None:
        rr = SDF.merge(RDF, on="series", how="left")
        daily_r = rr.groupby(["series","date"], as_index=False).agg(daily_value=("rating_mean","mean"))
    else:
        daily_r = daily.rename(columns={"cnt":"daily_value"})
    daily_r = daily_r.sort_values(["series","date"])
    daily_r["ma7"]  = daily_r.groupby("series")["daily_value"].transform(lambda s: s.rolling(7, min_periods=3).mean())
    daily_r["ma30"] = daily_r.groupby("series")["daily_value"].transform(lambda s: s.rolling(30, min_periods=5).mean())
    daily_r["trend"] = daily_r["ma7"] - daily_r["ma30"]
    last = daily_r.groupby("series", as_index=False).agg(trend=("trend","last"))
    last["trend_z"] = (last["trend"] - last["trend"].mean()) / (last["trend"].std() + 1e-6)
    return last[["series","trend_z"]]

# === bucket 相鄰表（用於 Fallback L1）===
BUCKET_NEIGHBORS = {
    "08-10": ["10-12"],
    "10-12": ["08-10", "12-14"],
    "12-14": ["10-12", "14-17"],
    "14-17": ["12-14", "17-19"],
    "17-19": ["14-17", "19-21"],
    "19-21": ["17-19", "20-22"],
    "20-22": ["19-21"],
    "other": []  # other 不指定相鄰桶
}

def get_slot_candidates(SLOT_POP: pd.DataFrame, wkd: int, hb: str) -> pd.DataFrame:
    """
    依照 Fallback 階梯回傳 slot-pop 候選：
    L0: 同 weekday + 同 bucket
    L1: 同 weekday + 相鄰 bucket（依 BUCKET_NEIGHBORS）
    L2: 同 weekday + 全桶
    L3: 全 weekday + 同 bucket
    L4: 全域（所有資料）
    """
    base_cols = ["series", "slot_pop_score"]
    take = lambda mask: SLOT_POP.loc[mask, base_cols]

    # L0: 同 weekday + 同 bucket
    c = take((SLOT_POP["weekday_idx"] == wkd) & (SLOT_POP["hour_bucket"] == hb))
    if not c.empty:
        return c

    # L1: 同 weekday + 相鄰 bucket
    for nb in BUCKET_NEIGHBORS.get(hb, []):
        c = take((SLOT_POP["weekday_idx"] == wkd) & (SLOT_POP["hour_bucket"] == nb))
        if not c.empty:
            return c

    # L2: 同 weekday + 全桶
    c = take(SLOT_POP["weekday_idx"] == wkd)
    if not c.empty:
        return c

    # L3: 全 weekday + 同 bucket
    c = take(SLOT_POP["hour_bucket"] == hb)
    if not c.empty:
        return c

    # L4: 全域熱門
    return SLOT_POP[base_cols]

# 內容相似（優先 jieba，失敗改 char ngram）
def build_sim_index(SDF: pd.DataFrame):
    try:
        import jieba
        from sklearn.feature_extraction.text import TfidfVectorizer
        def tok(t): return list(jieba.cut(t))
        vec = TfidfVectorizer(tokenizer=tok, max_features=5000)
    except Exception:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(analyzer="char", ngram_range=(2,3), max_features=8000)
    catalog = SDF.groupby("series", as_index=False).agg(n=("series","count"))
    X = vec.fit_transform(catalog["series"].fillna(""))
    return vec, X, catalog

def similar_series(seed, vec, X, catalog, topk=20):
    from sklearn.metrics.pairwise import cosine_similarity
    ser = catalog["series"].tolist()
    idx = {s:i for i,s in enumerate(ser)}
    if seed not in idx: return []
    i = idx[seed]
    sims = cosine_similarity(X[i], X).ravel()
    ords = sims.argsort()[::-1]
    out = []
    for j in ords[:topk+1]:
        s = ser[j]
        if s == seed: continue
        out.append((s, float(sims[j])))
        if len(out) >= topk: break
    return out

def hour_bucket_by_hour(h):
    if 8<=h<10: return "08-10"
    if 10<=h<12: return "10-12"
    if 12<=h<14: return "12-14"
    if 14<=h<17: return "14-17"
    if 17<=h<19: return "17-19"
    if 19<=h<21: return "19-21"
    if 20<=h<22: return "20-22"
    return "other"

# ================== 機器學習：就地學出權重（在當前候選上） ==================
def _safe_target_from_cand(cand: pd.DataFrame) -> pd.Series:
    """優先用 rating_mean 作為學習目標；沒有就用 freq 正規化。"""
    if "rating_mean" in cand.columns and cand["rating_mean"].notna().any():
        y = cand["rating_mean"].copy()
        # 避免尺度問題，做 0~1 normalize
        y = (y - y.min()) / (y.max() - y.min() + 1e-9)
        return y
    # fallback：用頻次代表受歡迎程度
    if "freq" in cand.columns:
        y = cand["freq"].copy()
        y = (y - y.min()) / (y.max() - y.min() + 1e-9)
        return y
    # 再不行就全 0.5（等同不學）
    return pd.Series([0.5] * len(cand), index=cand.index)

def learn_weights_from_candidates(cand: pd.DataFrame):
    """
    在目前候選 cand（含 slot_pop_score/content_sim/trend_z）上，
    以 rating_mean（或 freq）為目標，學出線性權重。
    回傳 (weights_dict, fitted_score_series)
    """
    feats = ["slot_pop_score", "content_sim", "trend_z"]
    df = cand.copy()
    for f in feats:
        if f not in df.columns:
            df[f] = 0.0
    X = df[feats].fillna(0.0).values
    y = _safe_target_from_cand(df).values

    # 盡量用 sklearn，沒有就走 numpy 最小二乘
    try:
        from sklearn.linear_model import LinearRegression
        m = LinearRegression()
        m.fit(X, y)
        w = m.coef_
    except Exception:
        # 最小二乘 w = (X^T X)^-1 X^T y
        XtX = X.T.dot(X) + 1e-9*np.eye(X.shape[1])
        w = np.linalg.solve(XtX, X.T.dot(y))

    # 權重非負 & 正規化到加總=1（易於解讀與對比）
    w = np.clip(w, 0, None)
    if w.sum() == 0:
        w = np.array([1/3, 1/3, 1/3])
    else:
        w = w / w.sum()

    weights = dict(zip(feats, [float(x) for x in w]))
    fitted = X.dot(w)
    return weights, pd.Series(fitted, index=df.index, name="ml_score")


# ================== AI 模擬用：生成卡片內容（純本地，不呼叫 API） ==================
_RAND_CAST = ["趙露思","吳磊","任嘉倫","迪麗熱巴","肖戰","王一博","楊紫","楊冪","胡歌","劉詩詩","孫儷","陳曉","羅云熙","譚松韻","白鹿","張晚意"]
def _mock_brief(name: str, bucket: str) -> str:
    tmpl = [
        f"《{name}》近期在【{bucket}】時段表現穩定，網路討論以角色人設與情節節奏為主，口碑聚焦於服化道與配樂。",
        f"各大社群對《{name}》的評價多為正面，觀眾關注關係線推進與轉折點，適合黃金時段回放與帶檔。",
        f"《{name}》的粉絲圖譜偏向女性 18–44，追劇黏著度高；在相同檔期具替代或互補價值。"
    ]
    return " ".join(tmpl)

def _mock_similar_list(series_name: str, sim_candidates: list, topk=3, seed=42):
    """
    從你現有的相似函式結果（或 series catalog）挑幾個，給個 6.8~9.2 的模擬評分。
    """
    rng = np.random.default_rng(abs(hash(series_name)) % (2**32) + seed)
    if not sim_candidates:
        # 沒相似候選就造幾個相近風格字串
        pool = [series_name + s for s in ["·前傳","·特別篇","·番外","·新編"]]
    else:
        pool = [s for s,_ in sim_candidates]
    rng.shuffle(pool)
    pool = pool[:topk]
    ratings = [round(float(r), 1) for r in list(rng.uniform(6.8, 9.2, size=len(pool)))]
    return list(zip(pool, ratings))

def _mock_shared_cast(topk=3, seed=99):
    rng = np.random.default_rng(seed)
    picks = rng.choice(_RAND_CAST, size=topk, replace=False)
    return [str(x) for x in picks]

def recommend(dt_str, seed_series, SLOT_POP, TREND, SDF, RDF, vec, X, catalog,
              topk=10, w_slot=0.5, w_sim=0.3, w_trend=0.2):
    t = pd.to_datetime(dt_str)
    wkd = t.weekday()
    hb  = hour_bucket_by_hour(t.hour)
    c1 = get_slot_candidates(SLOT_POP, wkd=wkd, hb=hb)
    c2 = pd.DataFrame(similar_series(seed_series, vec, X, catalog, topk=60), columns=["series","content_sim"]) if seed_series else pd.DataFrame(columns=["series","content_sim"])
    c3 = TREND.copy()
    cand = c1.merge(c2, on="series", how="outer").merge(c3, on="series", how="left").fillna(0.0)
    meta = SDF.groupby("series", as_index=False).agg(freq=("series","count"))
    if RDF is not None: meta = meta.merge(RDF, on="series", how="left")
    cand = cand.merge(meta, on="series", how="left")
    cand["score"] = w_slot*cand["slot_pop_score"] + w_sim*cand["content_sim"] + w_trend*cand["trend_z"]
    show = ["series","score","slot_pop_score","content_sim","trend_z","freq"]
    if RDF is not None: show += ["rating_mean","rating_median","rating_count"]
    return cand.sort_values("score", ascending=False).head(topk)[show].reset_index(drop=True)

# ====== Sidebar：應用模式選擇 ======
st.sidebar.title("🎯 愛爾達分析平台")
app_mode = st.sidebar.selectbox(
    "選擇功能模式:",
    ["📺 劇集推薦系統", "🔧 系統管理中心"],
    index=0
)

st.sidebar.markdown("---")

# 如果選擇管理模式，顯示管理儀表板
if app_mode == "🔧 系統管理中心":
    if ADMIN_FEATURES_AVAILABLE:
        show_admin_dashboard()
        st.stop()  # 停止執行後續的推薦系統代碼
    else:
        st.error("❌ 管理功能模組不可用")
        st.info("請確保 admin_features.py 檔案存在且可正常導入")
        st.stop()

# ====== Sidebar：資料來源 ======
st.sidebar.header("資料來源")
use_upload = st.sidebar.checkbox("改用上傳檔案", value=False)
if use_upload:
    up1 = st.sidebar.file_uploader("上傳節目表 CSV（program_schedule_extracted.csv）", type=["csv"])
    up2 = st.sidebar.file_uploader("（可選）上傳收視 CSV（integrated_program_ratings_cleaned.csv）", type=["csv"])
    if up1:
        SDF = load_schedule(up1)
    else:
        st.stop()
    RDF = load_ratings(up2) if up2 else None
else:
    SDF = load_schedule(DEFAULT_SCHEDULE)
    RDF = load_ratings(DEFAULT_RATINGS)

# 🔧（你先前已加）補齊欄位
SDF["weekday_idx"] = pd.to_datetime(SDF["date"], errors="coerce").dt.weekday
SDF["hour_bucket"] = SDF["hour_bucket"].fillna(SDF["start_time"].apply(hour_bucket_from_time))

# 🔎👉 在這裡貼上以下 debug 區塊
import os
st.write("DEBUG | CWD:", os.getcwd())
st.write("DEBUG | DEFAULT_RATINGS:", DEFAULT_RATINGS, " | exists:", os.path.exists(DEFAULT_RATINGS))

if RDF is None:
    st.error("RDF is None：沒有成功讀到收視率檔案或欄位無法對齊")
else:
    st.success("RDF 已讀到")
    st.write("DEBUG | RDF.columns:", list(RDF.columns))
    st.write("DEBUG | RDF.head():", RDF.head())

    # 檢查鍵值是否對得上（series 交集有多少）
    series_sdf = set(SDF["series"].dropna().astype(str).str.strip().unique())
    series_rdf = set(RDF["series"].dropna().astype(str).str.strip().unique()) if "series" in RDF.columns else set()
    st.write("DEBUG | series 交集筆數：", len(series_sdf & series_rdf))
    # 顯示前 10 個交集樣本
    st.write("DEBUG | series 交集樣本：", list((series_sdf & series_rdf))[:10])

# ====== 建索引（快取） ======
SLOT_POP = build_slot_pop(SDF, RDF, days=60)
TREND    = build_trend(SDF, RDF)
vec, X, catalog = build_sim_index(SDF)

# ====== 主頁內容 ======
st.title("愛爾達節目表互動平台（Streamlit）")

# 摘要
col1, col2, col3 = st.columns([1,1,1])
with col1:
    st.subheader("摘要總覽")
    total = len(SDF)
    date_min = str(SDF["date"].min().date()) if SDF["date"].notna().any() else ""
    date_max = str(SDF["date"].max().date()) if SDF["date"].notna().any() else ""
    st.metric("總筆數", f"{total:,}")
    st.caption(f"日期範圍：{date_min} ~ {date_max}")
with col2:
    yy = SDF.copy()
    yy["year"] = pd.to_datetime(yy["date"], errors="coerce").dt.year
    st.subheader("年份計數")
    st.dataframe(yy["year"].value_counts().sort_index().rename_axis("year").reset_index(name="count"))
with col3:
    st.subheader("時段分布")
    st.dataframe(SDF["hour_bucket"].value_counts().sort_index().rename_axis("bucket").reset_index(name="count"))

st.divider()

# 篩選
st.subheader("節目清單檢索")
c1, c2, c3, c4 = st.columns([1,1,1,2])
min_d, max_d = SDF["date"].min(), SDF["date"].max()
with c1:
    d_from = st.date_input("日期（起）", value=min_d.date() if pd.notna(min_d) else None)
with c2:
    d_to   = st.date_input("日期（迄）", value=max_d.date() if pd.notna(max_d) else None)
with c3:
    bucket = st.selectbox("時段", ["(全部)","08-10","10-12","12-14","14-17","17-19","19-21","20-22","other"], index=0)
with c4:
    q = st.text_input("關鍵字（節目）", "")

df = SDF.copy()
if d_from: df = df[df["date"] >= pd.to_datetime(d_from)]
if d_to:   df = df[df["date"] <= pd.to_datetime(d_to)]
if bucket and bucket != "(全部)": df = df[df["hour_bucket"] == bucket]
if q: df = df[df["program_title"].astype(str).str.contains(re.escape(q), case=False, na=False)]
df = df.sort_values(["date","start_time"])
st.dataframe(df[["date","weekday_name","start_time","hour_bucket","program_title","source_sheet"]], use_container_width=True)

st.divider()

# 推薦
st.subheader("簡易推薦（Slot + 相似 + 趨勢）")
rc1, rc2, rc3 = st.columns([1.2,1,1])
with rc1:
    dt_str = st.text_input("目標時間", value=f"{str(SDF['date'].max().date())} 20:00")
with rc2:
    seed = st.text_input("種子節目（可空）", "")
with rc3:
    topk = st.number_input("Top-K", min_value=3, max_value=30, value=10, step=1)

if st.button("產生推薦"):
    rec = recommend(dt_str, seed if seed else None, SLOT_POP, TREND, SDF, RDF, vec, X, catalog, topk=topk)
    st.session_state['rec'] = rec  # ⭐️ 存起來，給 ML/AI 區塊用
    st.dataframe(rec, use_container_width=True)
    st.caption("總分 = 0.5*Slot + 0.3*Sim + 0.2*Trend（可於程式內調整）")

st.divider()
st.header("🧪 深入計算")

if 'rec' not in st.session_state:
    st.info("請先在上方產生一次推薦（取得候選清單），再來這裡用 ML 學權重。")
else:
    cand = st.session_state['rec'].copy()  # 取剛剛那次候選
    st.caption("說明：在【當前候選】上，以 rating_mean（或 freq）作為學習目標，學出 Slot/Sim/Trend 的最佳加權。")

    if st.button("用機器學習自動學權重"):
        w, ml_score = learn_weights_from_candidates(cand)
        cand["ml_score"] = ml_score
        cand2 = cand.sort_values("ml_score", ascending=False).reset_index(drop=True)

        colA, colB = st.columns(2)
        with colA:
            st.subheader("學出的權重 (歸一化到總和=1)")
            st.json({
                "slot_pop_score": round(w.get("slot_pop_score",0), 3),
                "content_sim":    round(w.get("content_sim",0), 3),
                "trend_z":        round(w.get("trend_z",0), 3),
            })
        with colB:
            st.subheader("與原本權重的對照（原：0.5/0.3/0.2）")
            st.json({"original": {"slot":0.5,"sim":0.3,"trend":0.2}})

        st.subheader("ML 重新排序結果")
        st.dataframe(cand2, use_container_width=True)
        st.caption("提示：學習僅於當前候選上進行，建議先載入 ratings 讓目標更貼近真實表現。")

        # 保存供 AI 模擬區塊使用
        st.session_state['rec_ml'] = cand2

st.divider()
st.header("🤖 AI 功能模擬區塊")

if 'rec' not in st.session_state and 'rec_ml' not in st.session_state:
    st.info("請先在上方產生推薦，或在【機器學習區塊】重新排序後再來模擬。")
else:
    base = st.session_state.get('rec_ml', st.session_state.get('rec')).copy()
    N = st.slider("要生成幾個 AI 推薦卡片", min_value=3, max_value=15, value=6, step=1)
    bucket_hint = st.selectbox("情境（僅文字，用於摘要模擬）", 
                               ["19-21 黃金帶", "20-22 黃金帶", "10-12 上午帶", "其他時段"], index=0)
    if st.button("生成 AI 模擬卡片"):
        # 嘗試拿相似節目（若你有 vec/X/catalog）
        sim_index = {}
        try:
            for s in base["series"].head(N):
                sim_index[s] = similar_series(s, vec, X, catalog, topk=10)
        except Exception:
            pass

        for i, row in base.head(N).iterrows():
            series = str(row["series"])
            # 模擬內容
            brief = _mock_brief(series, bucket_hint)
            sim_list = _mock_similar_list(series, sim_index.get(series, []), topk=3, seed=2025+i)
            cast = _mock_shared_cast(topk=3, seed=1000+i)

            with st.expander(f"《{series}》｜AI 模擬資訊卡"):
                c1, c2 = st.columns([2,1])
                with c1:
                    st.markdown(f"**網路摘要（模擬）**：{brief}")
                    st.markdown("**類似影視劇＋評分（模擬）**：")
                    st.write(pd.DataFrame(sim_list, columns=["title", "mock_score"]))
                with c2:
                    st.metric("Slot", f"{row.get('slot_pop_score',0):.3f}")
                    st.metric("Sim",  f"{row.get('content_sim',0):.3f}")
                    st.metric("Trend",f"{row.get('trend_z',0):.3f}")
                    if 'rating_mean' in row:
                        st.metric("Rating(均值)", f"{row.get('rating_mean',float('nan')):.3f}" if pd.notna(row.get('rating_mean')) else "-")
                    st.caption(f"可能共同主角（模擬）：{', '.join(cast)}")
        st.success("已生成 AI 模擬卡片（純本地隨機/規則，無外部呼叫）。")
# =========================
# 🤖 AI 推薦後續體驗（模擬版）
# 推薦理由 + 類似劇卡片（黑鏡/三體/竊聽風雲） + 觀眾評論摘要
# 依賴：st.session_state['rec_ml'] 或 ['rec'] 作為來源候選
# 圖片請放在專案根目錄：黑鏡.webp、三體.jpg、竊聽風雲.webp
# =========================
st.divider()
st.header("🤖 AI 推薦後續體驗")

# 取用上一段推薦結果
_base_rec = st.session_state.get('rec_ml', st.session_state.get('rec'))
if _base_rec is None or len(_base_rec) == 0:
    st.info("請先在上方產生一次推薦，或使用『機器學習區塊』重新排序後再回來。")
else:
    # 讓使用者挑一筆推薦作為「主推薦對象」
    options = _base_rec["series"].astype(str).tolist()
    sel = st.selectbox("選擇一個主推薦節目（作為理由與延伸資訊的核心）", options, index=0)

    # 找到該列（取分數供理由生成）
    row = _base_rec[_base_rec["series"].astype(str) == sel].head(1)
    slot_v  = float(row["slot_pop_score"].iloc[0]) if "slot_pop_score" in row and not row["slot_pop_score"].isna().iloc[0] else 0.0
    sim_v   = float(row["content_sim"].iloc[0])   if "content_sim" in row and not row["content_sim"].isna().iloc[0]   else 0.0
    trend_v = float(row["trend_z"].iloc[0])       if "trend_z" in row and not row["trend_z"].isna().iloc[0]           else 0.0
    rating_mean = row["rating_mean"].iloc[0] if "rating_mean" in row else None

    # —— 模擬推薦理由（依你的三分項生成自然語句）——
    reason_bits = []
    # Slot
    if slot_v >= 0.75:
        reason_bits.append("在近 60 天的相同時段中表現屬於前 25%")
    elif slot_v >= 0.5:
        reason_bits.append("在同時段表現穩定，位於中上區間")
    else:
        reason_bits.append("近 60 天同時段曝光逐步增加")
    # Sim
    if sim_v > 0:
        reason_bits.append("與你的種子偏好高度相似")
    # Trend
    if trend_v > 0.3:
        reason_bits.append("近期討論度/熱度明顯上升")
    elif trend_v > 0:
        reason_bits.append("近期熱度略有增長")
    else:
        reason_bits.append("熱度平穩可作為檔期穩定選項")
    # rating
    if rating_mean is not None and pd.notna(rating_mean):
        try:
            reason_bits.append(f"平均收視約 {float(rating_mean):.2f}")
        except:
            pass

    st.subheader("推薦理由")
    st.markdown(f"**為什麼推薦《{sel}》？** " + "；".join(reason_bits) + "。")

    # —— 類似劇卡片（固定三張）＋ 評分（模擬）＋ 圖片 —— 
    st.subheader("類似影視劇")
    DEFAULT_IMG_DIR = DEFAULT_DIR  # 你專案一開始就定義的 DEFAULT_DIR
    cards = [
        {"title": "黑鏡", "file": "黑鏡.webp", "desc": "英國科幻選集，聚焦科技與人性的黑暗面，單元劇形式，每集獨立。"},
        {"title": "三體", "file": "三體.jpg", "desc": "硬科幻敘事，圍繞文明存亡與宇宙秩序的宏大命題，理性派受眾偏好。"},
        {"title": "竊聽風雲", "file": "竊聽風雲.webp", "desc": "香港犯罪類型片，情報博弈與商戰元素強，情報小組視角推進。"},
    ]
    # 給個模擬評分（固定/輕隨機皆可；這裡給固定區間）
    mock_scores = {"黑鏡": 8.8, "三體": 8.3, "竊聽風雲": 7.9}

    c1, c2, c3 = st.columns(3)
    for c, item in zip([c1, c2, c3], cards):
        with c:
            img_path = os.path.join(DEFAULT_IMG_DIR, item["file"])
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.caption(f"（找不到圖片檔：{item['file']}，請放在專案根目錄）")
            st.markdown(f"**{item['title']}**")
            st.caption(item["desc"])
            st.metric("模擬評分", f"{mock_scores.get(item['title'], 8.0):.1f} / 10")

    # —— 觀眾評論摘要（模擬）——
    st.subheader("觀眾評論摘要（模擬）")
    # 可依當下主推薦、或所選時段情境拼接不同的語句
    demo_comments = [
        f"《{sel}》的節奏在中後段明顯加快，角色關係線更緊密，討論多集中在關鍵轉折與結局鋪陳。",
        "服化道與場景質感獲得普遍好評；少數觀眾對部分支線篇幅有分歧。",
        "如果喜歡世界觀與議題思辨，類似的《黑鏡》《三體》能提供更強的概念密度；想要偏類型快感可選《竊聽風雲》。",
    ]
    st.write("- " + "\n- ".join(demo_comments))

    st.caption("以上為介面示意（不呼叫外部 API）。未來要接真資料：只要把『理由句』與『卡片資訊/評分』從 API/資料庫填入即可。")
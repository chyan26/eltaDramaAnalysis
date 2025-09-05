import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import os

def get_cast_for_program(program_name, manual_cast):
    if program_name in manual_cast:
        return manual_cast[program_name]
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    search_url = f"https://zh.wikipedia.org/wiki/{program_name}"
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
    except Exception:
        return "N/A"
    if response.status_code != 200:
        search_api = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={program_name}&format=json"
        try:
            resp = requests.get(search_api, headers=headers, timeout=10)
        except Exception:
            return "N/A"
        if resp.status_code == 200:
            data = resp.json()
            if data["query"]["search"]:
                title = data["query"]["search"][0]["title"]
                search_url = f"https://zh.wikipedia.org/wiki/{title}"
                try:
                    response = requests.get(search_url, headers=headers, timeout=10)
                except Exception:
                    return "N/A"
            else:
                return "N/A"
        else:
            return "N/A"
    soup = BeautifulSoup(response.text, "html.parser")
    infobox = soup.find("table", {"class": "infobox"})
    if infobox:
        for tr in infobox.find_all("tr"):
            if tr.th and any(key in tr.th.text for key in ["主演", "演員", "配音", "主持人", "主要演員"]):
                cast = tr.td.text.strip().replace('\n', '、').replace(' ', '')
                manual_cast[program_name] = cast
                return cast
    manual_cast[program_name] = "N/A"
    return "N/A"

def main():
    src_file = "integrated_program_ratings_cleaned.csv"
    out_file = "integrated_program_ratings_cleaned_with_cast.csv"
    manual_cast = {
        "神鵰俠侶": "陳曉、陳妍希",
        "一剪芳華": "何晟銘、姜梓新",
        # 可自行補充
    }

    df = pd.read_csv(src_file)
    # 若已存在結果檔，則讀取已查詢進度
    if os.path.exists(out_file):
        df_out = pd.read_csv(out_file)
        if 'Cast' in df_out.columns:
            df['Cast'] = df_out['Cast']
        else:
            df['Cast'] = ""
    else:
        df['Cast'] = ""

    print("開始爬取卡司資料...")
    start_idx = 0
    if df['Cast'].notna().sum() > 0:
        # 找到第一個未查詢的位置
        start_idx = df[df['Cast'].isna() | (df['Cast'] == "")].index[0]

    for i in tqdm(range(start_idx, len(df)), desc="查詢卡司"):
        series_name = df.loc[i, 'Cleaned_Series_Name']
        if pd.isna(df.loc[i, 'Cast']) or df.loc[i, 'Cast'] == "":
            cast = get_cast_for_program(series_name, manual_cast)
            df.loc[i, 'Cast'] = cast
            tqdm.write(f"Series: {series_name}, Cast: {cast}")
            time.sleep(1)
        # 每180筆儲存一次
        if (i + 1) % 180 == 0:
            df.to_csv(out_file, index=False)
            tqdm.write(f"已儲存至 {out_file}，進度：{i+1}/{len(df)}")
    # 最後一次儲存
    df.to_csv(out_file, index=False)
    print("全部完成，已新增 Cast 欄位並儲存新檔案。")

if __name__ == "__main__":
    main()
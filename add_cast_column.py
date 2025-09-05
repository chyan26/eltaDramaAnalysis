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
                td = tr.find('td')
                if td:
                    cast = td.text.strip().replace('\n', '、').replace(' ', '')
                else:
                    cast = ""
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
    # 取得所有唯一劇集名稱
    unique_series = df['Cleaned_Series_Name'].dropna().unique()
    print(f"共 {len(unique_series)} 種劇集，開始爬取卡司...")

    # 先建立劇集名稱到卡司的 dict
    cast_dict = {}
    for series_name in tqdm(unique_series, desc="劇集卡司查詢"):
        cast = get_cast_for_program(series_name, manual_cast)
        cast_dict[series_name] = cast
        tqdm.write(f"{series_name}: {cast}")
        time.sleep(1)

    # 將卡司合併回原始資料
    df['Cast'] = df['Cleaned_Series_Name'].map(cast_dict)
    df.to_csv(out_file, index=False)
    print(f"全部完成，已新增 Cast 欄位並儲存新檔案：{out_file}")

if __name__ == "__main__":
    main()
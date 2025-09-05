import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm

def get_cast_for_program(program_name):
    """
    根據節目名稱爬取卡司（以 Wikipedia 為例，請根據實際情況修改）
    """
    search_url = f"https://zh.wikipedia.org/wiki/{program_name}"
    try:
        response = requests.get(search_url)
        if response.status_code != 200:
            return "N/A"
        soup = BeautifulSoup(response.text, "html.parser")
        # 假設卡司在 infobox 的 "主演" 欄位
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            for tr in infobox.find_all("tr"):
                if tr.th and ("主演" in tr.th.text or "主持人" in tr.th.text):
                    print(f"Found cast for {program_name}: {tr.td.text.strip()}")
                    return tr.td.text.strip()
        return "N/A"
    except Exception as e:
        print(f"Error fetching {program_name}: {e}")
        return "N/A"

def main():
    # 讀取原始 CSV
    df = pd.read_csv("integrated_program_ratings_cleaned.csv")
    
    # 新增 Cast 欄位
    cast_list = []
    print("開始爬取卡司資料...")
    for program in tqdm(df['Program']):  # 修正這一行
        cast = get_cast_for_program(program)
        cast_list.append(cast)
        time.sleep(1)  # 避免爬蟲過快被封鎖
    
    df['Cast'] = cast_list
    
    # 儲存回 CSV
    df.to_csv("integrated_program_ratings_cleaned_with_cast.csv", index=False)
    print("已新增 Cast 欄位並儲存新檔案。")

if __name__ == "__main__":
    main()
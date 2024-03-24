import openai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re
import json
import os

# OpenAI APIキー設定
openai.api_key = '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'

# Chromeのヘッドレスモードを設定
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # ヘッドレスモードを有効にする

# WebDriverのセットアップ
chrome_driver_path = r"C:\Users\kanai\Downloads\chromedriver-win32\chromedriver-win32\chromedriver.exe"
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# 絶対パスを指定
file_path = 'C:/Users/kanai/west2/sonota.json'  # 直接絶対パスを指定

# JSONファイルの読み込み
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
except json.decoder.JSONDecodeError as e:
    print(f"JSONファイルの読み込み中にエラーが発生しました: {e}")
    exit()

# 読み込んだデータから路線名、原因、方向を取得する部分（修正が必要）
routes = data['routes']
causes = data['causes']
directions = data['directions']
zyokyo = data['zyokyo']


# 指定されたURLにアクセス
url = "https://trafficinfo.westjr.co.jp/kinki.html"
driver.get(url)

soup = BeautifulSoup(driver.page_source, 'html.parser')
jisyo_containers = soup.find_all('div', class_='jisyo')

info_list = []
for jisyo in jisyo_containers:
    title = jisyo.find('h2', class_='jisyo_title').get_text(strip=True)
    target_line = title.split('】')[1].split('　')[0]
    jisyo_contents = jisyo.find('div', class_='jisyo_contents')
    summary = jisyo_contents.find('p', class_='gaiyo').get_text(strip=True)
    info_list.append(f"{target_line}\n{summary}")
    lines = jisyo_contents.find_all('span', class_='line')
    stations = jisyo_contents.find_all('span', class_='station')
    for line, station in zip(lines, stations):
        line_text = line.get_text(strip=True)
        station_text = station.get_text(strip=True)
        info_list.append(f"{line_text}: {station_text}")

driver.quit()

scraped_info_str = "\n\n".join(info_list)

print(scraped_info_str)

if scraped_info_str:
    # JSONデータから路線名、原因、方向を参照するための指示を追加
    prompt = f"""
    以下の情報を基にして、次のカテゴリーに適切に情報を分類してください。路線名、原因、方向については、添付のJSONファイルの中から選択してください。それ以外の情報は、提供されたテキストから直接引き出してください。

    カテゴリー:
    - 原因発生路線 (JSONファイルから選択)
    - 原因発生始点駅
    - 原因発生終点駅
    - 発生or見込み時間
    - 影響路線 (JSONファイルから選択)
    - 影響始点駅
    - 影響終点駅
    - 影響方向 (JSONファイルから選択)
    - 原因 (JSONファイルから選択)
    - 状況(JSONファイルから選択)

    提供された情報:
    {scraped_info_str}

    JSONファイルのデータに基づく選択肢:
    - 路線名: {', '.join(data['routes'])}
    - 原因: {', '.join(data['causes'])}
    - 方向: {', '.join(data['directions'])}
    - 状況: {', '.join(data['zyokyo'])}

    分類作業を開始してください。
    """

# GPT-3.5ターボモデルによる問い合わせの実行
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "ユーザーから提供された情報と、指定されたJSONファイルのデータを基に、情報を正確にカテゴリー分けしてください。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

# 分類結果の表示
    response_text = response.choices[0].message['content']

    
# レスポンステキストを解析して情報を辞書に格納
    info_dict = {}
    for line in response_text.strip().split("\n"):
        if ": " in line:  # Check if the line contains the separator before splitting
            key, value = line.split(": ", 1)
            info_dict[key.strip()] = value.strip()
        else:
        # Handle lines without separator or take no action
        # For example, you could log these lines or simply pass
            print(f"Skipping line without expected format: '{line}'")
# 辞書から情報を変数に格納
    # 必要な変数を初期化
    影響路線 = ""
    原因発生始点駅 = ""
    原因発生終点駅 = ""
    発生or見込み時間 = ""
    影響方向 = ""
    影響始点駅 = ""
    影響終点駅 = ""
    原因 = ""
    状況 = ""

# レスポンステキストを解析
    lines = response_text.split("\n")
    for line in lines:
        if "原因発生路線" in line:
            _, 影響路線 = line.split(":", 1)
        elif "原因発生始点駅" in line:
            _, 原因発生始点駅 = line.split(":", 1)
        elif "原因発生終点駅" in line:
            _, 原因発生終点駅 = line.split(":", 1)
        elif "発生or見込み時間" in line:
            _, 発生or見込み時間 = line.split(":", 1)
        elif "影響路線" in line:
            _, 影響路線 = line.split(":", 1)
        elif "影響始点駅" in line:
            _, 影響始点駅 = line.split(":", 1)
        elif "影響終点駅" in line:
            _, 影響終点駅 = line.split(":", 1)
        elif "影響方向" in line:
            _, 影響方向 = line.split(":", 1)
        elif "原因" in line:
            _, 原因 = line.split(":", 1)
        elif "状況" in line:
            _, 状況 = line.split(":", 1)

# 各変数のトリミング（不要な空白の削除）
    影響路線 = 影響路線.strip()
    原因発生始点駅 = 原因発生始点駅.strip()
    原因発生終点駅 = 原因発生終点駅.strip()
    発生or見込み時間 = 発生or見込み時間.strip()
    影響方向 = 影響方向.strip()
    影響始点駅 = 影響始点駅.strip()
    影響終点駅 = 影響終点駅.strip()
    原因 = 原因.strip()
    状況 = 状況.strip()

# 結果の出力
    print(f"影響路線: {影響路線}")
    print(f"原因発生始点駅: {原因発生始点駅}")
    print(f"原因発生終点駅: {原因発生終点駅}")
    print(f"発生or見込み時間: {発生or見込み時間}")
    print(f"影響方向: {影響方向}")
    print(f"影響始点駅: {影響始点駅}")
    print(f"影響終点駅: {影響終点駅}")
    print(f"原因: {原因}")
    print(f"状況: {状況}")

else:
    print("運行情報はありません。")
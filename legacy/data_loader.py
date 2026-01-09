# src/data_loader.py

import json
import os

def load_companies():
    # このファイル（data_loader.py）から見て ../data/companies.json を指す
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "companies.json")
    data_path = os.path.abspath(data_path)

    if not os.path.exists(data_path):
        # ここではまだ Streamlit を import していないので、
        # 呼び出し側（main.py 側）で「企業データがありません」と表示する前提で、
        # ひとまず空リストを返して安全に処理を続行する
        return []

    with open(data_path, "r", encoding="utf-8") as f:
        companies = json.load(f)

    return companies

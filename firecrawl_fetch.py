# firecrawl_fetch.py

import os
import json
from firecrawl import FirecrawlApp  # pip install firecrawl-py

G7_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025Gauss7Contest.html"
G8_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025Gauss8Contest.html"
SOL_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025GaussSolution.html"

# 환경변수 또는 코드에 직접 키 설정
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "YOUR_API_KEY_HERE")


def fetch_firecrawl_page(url: str) -> dict:
    app = FirecrawlApp(FIRECRAWL_API_KEY)

    # extract: 한 페이지를 구조화해서 가져오는 모드
    res = app.extract(
        {
            "url": url,
            "format": "json",       # "markdown"도 가능
            "params": {
                # 필요시 깊이/필터 등 옵션 조정 가능
            },
        }
    )
    return res


def main():
    # 1) Grade 7 contest
    g7_json = fetch_firecrawl_page(G7_URL)
    with open("firecrawl_gauss7_2025_contest.json", "w", encoding="utf-8") as f:
        json.dump(g7_json, f, ensure_ascii=False, indent=2)

    # 2) Grade 8 contest
    g8_json = fetch_firecrawl_page(G8_URL)
    with open("firecrawl_gauss8_2025_contest.json", "w", encoding="utf-8") as f:
        json.dump(g8_json, f, ensure_ascii=False, indent=2)

    # 3) solutions
    sol_json = fetch_firecrawl_page(SOL_URL)
    with open("firecrawl_gauss_2025_solution.json", "w", encoding="utf-8") as f:
        json.dump(sol_json, f, ensure_ascii=False, indent=2)

    print("Saved Firecrawl JSON files.")


if __name__ == "__main__":
    main()
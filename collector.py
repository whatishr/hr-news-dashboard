# collector.py (초기 대량 구축용)
from daily_collector import process_article_with_gpt, clean_text, is_trusted_source, is_noise_article, SEARCH_KEYWORDS, CLIENT_ID, CLIENT_SECRET, CSV_FILE_PATH
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import urllib.parse, requests, pandas as pd

def rebuild_initial_dataset(days=3, limit_total=30):
    """며칠간의 데이터를 대량 수집하여 초기 hr_news.csv를 완전 새로 생성"""
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(days=days) # 3일 전 기사까지 수집

    print(f"🚀 초기 데이터 구축 시작 (최근 {days}일치 수집)...")
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    raw_articles = []

    for kw in SEARCH_KEYWORDS:
        url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(kw)}&display=100&sort=date"
        res = requests.get(url, headers=headers, verify=False)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                try:
                    pub_dt = parsedate_to_datetime(item.get("pubDate", ""))
                    if pub_dt.tzinfo is None: pub_dt = pub_dt.replace(tzinfo=kst)
                    if pub_dt < cutoff_date: continue
                except: continue

                link = item.get("originallink") or item.get("link", "")
                if not is_trusted_source(link): continue

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))
                if is_noise_article(title, raw_desc): continue

                raw_articles.append({"title": title, "raw_desc": raw_desc, "link": link, "pubDate": item["pubDate"], "pub_dt": pub_dt})

    raw_articles.sort(key=lambda x: x["pub_dt"], reverse=True)

    articles = []
    for art in raw_articles:
        date_prefix = f"[{art['pub_dt'].strftime('%m/%d')}]"
        ai_res = process_article_with_gpt(art["title"], art["raw_desc"], date_prefix)
        if not ai_res.get("is_hr_related", False): continue

        articles.append({
            "category": ai_res["category"],
            "title": ai_res["brief_title"],
            "description": ai_res["description"],
            "link": art["link"],
            "pubDate": art["pubDate"],
            "pub_dt_iso": art["pub_dt"].isoformat(),
            "collected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        })
        if len(articles) >= limit_total: break

    df = pd.DataFrame(articles).drop_duplicates(subset=["link"], keep="first")
    df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8-sig")
    print(f"🎉 초기 데이터베이스 구축 완료! (총 {len(df)}건 저장)")

if __name__ == "__main__":
    rebuild_initial_dataset(days=3, limit_total=20)
import os
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("NAVER_CLIENT_ID") or "n_sOcFCgRFVkTTGUN9W7"
CLIENT_SECRET = os.getenv("CLIENT_SECRET") or os.getenv("NAVER_CLIENT_SECRET") or "56vRPwOw1b"

TRUSTED_SOURCES = [
    "hankyung.com", "mk.co.kr", "sedaily.com", "chosun.com", "joongang.co.kr", 
    "donga.com", "etnews.com", "worklaw.co.kr", "laborplus.co.kr", "hani.co.kr", 
    "khan.co.kr", "yna.co.kr", "newsis.com", "thisisgame.com", "gamemeca.com"
]

CATEGORY_KEYWORDS = {
    "오늘의 스마일게이트": ["스마일게이트"],
    "HR 트렌드 섹션 (ai등HR/인사 트렌드)": ["HR 테크 AI 인사", "인사 트렌드 2026", "HR Analytics 피플"],
    "고용노동부/노동법/판례": ["고용노동부 근로감독", "근로기준법 대법원 판결", "중대재해처벌법 판례"],
    "노사/ 노동 / 노조/보상/평가/성과급": ["기업 노사 파업 노조", "인사평가 성과급 보상", "연봉 인상 임단협"],
    "채용/조직문화": ["채용 트렌드 경력직", "기업 조직문화 근무제도", "하이브리드 워크 복지"]
}

CSV_FILE_PATH = "hr_news.csv"

# 💡 제목 내 모든 말줄임표 및 언론사 라벨 완벽 제거
def clean_title(title):
    if not title: return ""
    text = re.sub("<.*?>", "", title).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
    # [단독], [포토], [기획] 등 수식어 제거
    text = re.sub(r"\[(단독|포토|기획|속보|인사|부음)\]", "", text).strip()
    # 제목 중간이나 끝에 붙은 네이버 특유의 말줄임표(..., …) 제거
    text = re.sub(r"\.{2,}", " ", text)
    text = re.sub(r"…", " ", text)
    # 연속된 공백 하나로 정리
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_free_summary(link, raw_desc):
    try:
        res = requests.get(link, timeout=2.5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            valid_texts = []
            for p in paragraphs:
                t = p.get_text().strip()
                if len(t) > 30 and not any(x in t for x in ["기자", "저작권", "무단전재", "구독"]):
                    valid_texts.append(t)
                if len(valid_texts) >= 2:
                    break
            if valid_texts:
                summary = " ".join(valid_texts)
                return summary[:180] + "..." if len(summary) > 180 else summary
    except:
        pass
    
    clean_desc = re.sub("<.*?>", "", raw_desc).replace("&quot;", '"').replace("&amp;", "&").strip()
    return clean_desc

def is_trusted_source(link):
    return any(domain in link for domain in TRUSTED_SOURCES) if link else False

def is_noise_article(title, raw_desc=""):
    full_text = f"{title} {raw_desc}"
    if "이혼" in full_text or "재산분할" in full_text or "위자료" in full_text: return True
    domain_noise = ["금융감독원", "가계대출", "대출난민", "소상공인", "보건소", "부동산", "아파트", "청약", "코스피", "주가"]
    if any(k in full_text for k in domain_noise): return True
    spec_noise = ["인사발령", "부음", "동정", "부고", "전보", "명예퇴직"]
    if any(bad in title for bad in spec_noise) or re.search(r"\[인사\]|\[부음\]|\[동정\]", title): return True
    return False

def run_collection():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(days=14)

    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    final_articles = []

    print("📡 맞춤 뉴스 수집 및 정제 시작...")

    for category_name, keywords in CATEGORY_KEYWORDS.items():
        cat_articles = []
        seen_titles = set()

        for kw in keywords:
            url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(kw)}&display=30&sort=date"
            res = requests.get(url, headers=headers, verify=False)
            if res.status_code == 200:
                for item in res.json().get("items", []):
                    try:
                        pub_dt = parsedate_to_datetime(item.get("pubDate", ""))
                        if pub_dt.tzinfo is None: pub_dt = pub_dt.replace(tzinfo=kst)
                        if pub_dt < cutoff_date: continue
                    except: continue

                    link = item.get("originallink") or item.get("link", "")
                    if category_name != "오늘의 스마일게이트" and not is_trusted_source(link): continue

                    title = clean_title(item["title"])
                    raw_desc = item.get("description", "")
                    
                    if is_noise_article(title, raw_desc): continue
                    if title in seen_titles: continue
                    seen_titles.add(title)

                    date_str = pub_dt.strftime("[%m/%d]")
                    summary_desc = fetch_free_summary(link, raw_desc)

                    cat_articles.append({
                        "category": category_name,
                        "date_str": date_str,
                        "title": title,
                        "description": summary_desc,
                        "link": link,
                        "pubDate": item["pubDate"],
                        "pub_dt": pub_dt
                    })

        cat_articles.sort(key=lambda x: x["pub_dt"], reverse=True)
        limit = 5 if category_name == "오늘의 스마일게이트" else 8
        selected = cat_articles[:limit]
        final_articles.extend(selected)
        print(f"  - [{category_name}]: {len(selected)}개 수집 완료")

    new_df = pd.DataFrame(final_articles)

    if not new_df.empty:
        if "pub_dt" in new_df.columns:
            new_df = new_df.drop(columns=["pub_dt"])
        new_df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8-sig")
        print(f"\n🎉 총 {len(new_df)}개 기사가 '{CSV_FILE_PATH}'에 저장되었습니다.")

if __name__ == "__main__":
    run_collection()
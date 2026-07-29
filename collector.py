import os
import re
import json
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
    "khan.co.kr", "yna.co.kr", "newsis.com", "inven.co.kr", "thisisgame.com", "gamemeca.com"
]

CATEGORY_KEYWORDS = {
    "오늘의 스마일게이트": ["스마일게이트"],
    "HR 트렌드 섹션 (ai등HR/인사 트렌드)": ["HR 테크 AI 인사", "인사 트렌드 2026", "HR Analytics 피플"],
    "고용노동부/노동법/판례": ["고용노동부 근로감독", "근로기준법 대법원 판결", "중대재해처벌법 판례"],
    "노사/ 노동 / 노조/보상/평가/성과급": ["기업 노사 파업 노조", "인사평가 성과급 보상", "연봉 인상 임단협"],
    "채용/조직문화": ["채용 트렌드 경력직", "기업 조직문화 근무제도", "하이브리드 워크 복지"]
}

CSV_FILE_PATH = "hr_news.csv"

def clean_title(title):
    if not title: return ""
    text = re.sub("<.*?>", "", title).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
    text = re.sub(r"\[(단독|포토|기획|속보|인사|부음)\]", "", text).strip()
    text = re.sub(r"\.{2,}", " ", text)
    text = re.sub(r"…", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# 💡 무료로 [핵심 요약 / 실무 임팩트 / 실무 체크포인트] 생성 함수
def generate_free_hr_insight(link, title, raw_desc):
    body_text = ""
    try:
        res = requests.get(link, timeout=2.5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            valid = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30 and not any(x in p.get_text() for x in ["기자", "저작권", "무단전재"])]
            if valid:
                body_text = " ".join(valid)
    except:
        pass

    if not body_text:
        body_text = re.sub("<.*?>", "", raw_desc).replace("&quot;", '"').replace("&amp;", "&").strip()

    # 1. 핵심 요약
    summary = body_text[:220] + "..." if len(body_text) > 220 else body_text

    # 2. 실무 임팩트 (주요 키워드 기반 자동 구성)
    impact = f"본 기사는 '{title[:25]}...' 관련 주요 동향을 다루고 있으며, 관련된 법적 규제 및 인사 관리 방침에 직접적인 영향을 미칠 수 있습니다."

    # 3. 실무 체크포인트 (규칙 기반 자동 추출)
    checkpoints = [
        "관련 제도 변화 및 산업군 내 적용 사례를 지속 모니터링해야 합니다.",
        "현재 내부 인사/노무 관련 규정 및 운영 실태와의 일치 여부를 사전 점검할 필요가 있습니다."
    ]

    return {
        "summary": summary,
        "impact": impact,
        "checkpoints": checkpoints
    }

def is_trusted_source(link):
    return any(domain in link for domain in TRUSTED_SOURCES) if link else False

def is_noise_article(title, raw_desc=""):
    full_text = f"{title} {raw_desc}"
    if any(k in full_text for k in ["이혼", "재산분할", "위자료", "가계대출", "소상공인", "부동산", "청약", "코스피"]): return True
    if any(bad in title for bad in ["인사발령", "부음", "동정", "부고", "전보"]): return True
    return False

def run_collection():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(days=14)

    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    final_articles = []

    print("📡 리포팅 스타일 뉴스 수집 및 3단계 인사이트 생성 시작...")

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
                    
                    # 💡 3단계 인사이트 생성
                    insight = generate_free_hr_insight(link, title, raw_desc)

                    cat_articles.append({
                        "category": category_name,
                        "date_str": date_str,
                        "title": title,
                        "summary": insight["summary"],
                        "impact": insight["impact"],
                        "checkpoints": json.dumps(insight["checkpoints"], ensure_ascii=False),
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
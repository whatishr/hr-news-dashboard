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

def clean_text(text):
    if not text: return ""
    t = re.sub("<.*?>", "", text).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
    t = re.sub(r"\[(단독|포토|기획|속보|인사|부음)\]", "", t).strip()
    t = re.sub(r"\.{2,}", " ", t)
    t = re.sub(r"…", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def extract_quality_summary_and_checkpoints(category_name, link, title, raw_desc):
    body_paragraphs = []
    try:
        res = requests.get(link, timeout=2.5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for p in soup.find_all("p"):
                txt = p.get_text().strip()
                if len(txt) > 30 and not any(x in txt for x in ["기자", "저작권", "무단전재", "구독", "무단 전재"]):
                    body_paragraphs.append(clean_text(txt))
    except:
        pass

    clean_desc = clean_text(raw_desc)
    
    # 💡 요약문 정제 (완성형 문장 2~3개 결합)
    if body_paragraphs:
        summary_sentences = body_paragraphs[:3]
        summary = " ".join(summary_sentences)
        if len(summary) > 230:
            summary = summary[:230] + "..."
    elif clean_desc:
        summary = clean_desc if len(clean_desc) <= 230 else clean_desc[:230] + "..."
    else:
        summary = f"{title} 관련 주요 경과 및 업계 동향에 대한 상세 내용입니다."

    # 💡 스마일게이트 카테고리는 체크포인트 불필요
    if category_name == "오늘의 스마일게이트":
        return {"summary": summary, "checkpoints": []}

    # 💡 실제 기사 본문 및 제목 기반의 정밀 체크포인트 생성
    full_content = f"{title} {summary}"
    checkpoints = []

    if any(k in full_content for k in ["임금피크", "동의", "취업규칙", "무효", "대법원", "판결", "통상임금"]):
        if "동의" in full_content or "전산망" in full_content:
            checkpoints.append("사내 전산망/온라인 동의 방식이 법상 근로자 집단적 동의 요건을 만족하는지 서면 절차 검토")
        if "임금피크" in full_content:
            checkpoints.append("도입 시 업무량 감축 및 대상조치(보상) 수준이 대법원 정당성 판정 기준에 부합하는지 재점검")
        else:
            checkpoints.append("판결 취지가 당사 인사규정 및 취업규칙 개정 절차에 미치는 리스크 검토")

    elif any(k in full_content for k in ["근로시간", "유연근무", "연장근로", "근로감독", "노동부"]):
        checkpoints.append("부서별 근로시간 운영 현황 및 주 52시간 한도 준수 여부 사전 모니터링")
        checkpoints.append("유연근무제 운영 시 근로자대표 서면합의서 체결 및 규정 개정 필요성 점검")

    elif any(k in full_content for k in ["성과급", "노조", "임단협", "임금", "보상", "파업"]):
        checkpoints.append("동종업계 성과급 지급 체계 및 임금 인상률 동향 비교 분석")
        checkpoints.append("성과급의 임금성(근로 대가성) 인정 여부에 따른 퇴직금/통상임금 영향 사전 검토")

    elif any(k in full_content for k in ["AI", "채용", "조직문화", "평가"]):
        checkpoints.append("AI 도입 시 개인정보 처리 동의 및 채용 절차의 공정성/투명성 점검")
        checkpoints.append("내부 평가 및 채용 프로세스 가이드라인 최신화 검토")

    if not checkpoints:
        checkpoints.append(f"기사 주요 이슈('{title[:18]}...') 관련 사내 규정 및 노무 영향도 검토")
        checkpoints.append("제도 변경 시 근로자 사전 의견 수렴 및 노사 협의 절차 이행")

    return {
        "summary": summary,
        "checkpoints": checkpoints[:2]
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

    print("📡 고품질 뉴스 수집 및 정제 작업 시작...")

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

                    title = clean_text(item["title"])
                    raw_desc = item.get("description", "")
                    
                    if is_noise_article(title, raw_desc): continue
                    if title in seen_titles: continue
                    seen_titles.add(title)

                    date_str = pub_dt.strftime("[%m/%d]")
                    insight = extract_quality_summary_and_checkpoints(category_name, link, title, raw_desc)

                    cat_articles.append({
                        "category": category_name,
                        "date_str": date_str,
                        "title": title,
                        "summary": insight["summary"],
                        "checkpoints": json.dumps(insight["checkpoints"], ensure_ascii=False),
                        "link": link,
                        "pubDate": item["pubDate"],
                        "pub_dt": pub_dt
                    })

        cat_articles.sort(key=lambda x: x["pub_dt"], reverse=True)
        limit = 5 if category_name == "오늘의 스마일게이트" else 8
        selected = cat_articles[:limit]
        final_articles.extend(selected)
        print(f"  - [{category_name}]: {len(selected)}개 완료")

    new_df = pd.DataFrame(final_articles)

    if not new_df.empty:
        if "pub_dt" in new_df.columns:
            new_df = new_df.drop(columns=["pub_dt"])
        new_df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8-sig")
        print(f"\n🎉 데이터 저장 완료!")

if __name__ == "__main__":
    run_collection()
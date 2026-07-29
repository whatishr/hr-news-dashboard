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

def clean_title(title):
    if not title: return ""
    text = re.sub("<.*?>", "", title).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
    text = re.sub(r"\[(단독|포토|기획|속보|인사|부음)\]", "", text).strip()
    text = re.sub(r"\.{2,}", " ", text)
    text = re.sub(r"…", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# 💡 실제 기사 본문 및 제목 기반의 정밀 인사이트 추출 로직
def generate_free_hr_insight(link, title, raw_desc):
    body_text = ""
    try:
        res = requests.get(link, timeout=2.5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            valid = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30 and not any(x in p.get_text() for x in ["기자", "저작권", "무단전재", "무단 전재"])]
            if valid:
                body_text = " ".join(valid)
    except:
        pass

    clean_desc = re.sub("<.*?>", "", raw_desc).replace("&quot;", '"').replace("&amp;", "&").strip()
    full_text = f"{title} {body_text} {clean_desc}"

    # 1. 핵심 요약 (기사 본문 핵심 문장 가공)
    if body_text and len(body_text) >= 100:
        summary = body_text[:240].strip() + "..."
    elif clean_desc:
        summary = clean_desc[:240].strip() + "..." if len(clean_desc) > 240 else clean_desc
    else:
        summary = f"본 기사는 '{title}'에 관한 상세 소식으로, 관련 노무 및 인사 관리 현황을 다루고 있습니다."

    # 2. 실무 체크포인트 (기사 키워드 맥락 분석 기반 생성)
    checkpoints = []

    # Case A: 취업규칙 / 동의 절차 / 임금피크제 / 판결 관련
    if any(k in full_text for k in ["임금피크", "동의", "취업규칙", "무효", "대법원", "판결", "통상임금"]):
        if "동의" in full_text or "전산망" in full_text:
            checkpoints.append("사내 전산망/온라인 동의 방식이 근로기준법상 '집단적 동의 요건' 또는 서면 동의 절차를 충족하는지 법적 검토 필요")
        if "임금피크" in full_text:
            checkpoints.append("현행 임금피크제 도입 시 업무량 감축, 대상조치(보상) 수준이 대법원 정당성 인정 기준에 부합하는지 재점검")
        else:
            checkpoints.append("관련 대법원 판결 요지가 당사 인사규정 및 취업규칙 불이익 변경 절차에 미칠 법적 리스크 점검")

    # Case B: 근로시간 / R&D / 유연근무 / 고용노동부 근로감독
    elif any(k in full_text for k in ["근로시간", "유연근무", "연장근로", "근로감독", "노동부", "중대재해"]):
        checkpoints.append("부서별/직무별 근로시간 운영 실태 및 연장근로 한도(주 52시간) 준수 여부 사전 데이터 점검")
        checkpoints.append("유연근무제 도입 시 근로자대표와의 서면 합의서 체결 및 취업규칙 개정 필요성 검토")

    # Case C: 노사 / 성과급 / 임단협 / 파업 / 보상
    elif any(k in full_text for k in ["성과급", "노조", "임단협", "임금", "보상", "파업"]):
        checkpoints.append("경쟁사/동종업계 성과급 지급 체계 및 임금 인상률 동향 비교 분석")
        checkpoints.append("성과급의 '근로 대가성(임금성)' 인정 여부에 따른 퇴직금 및 통상임금 산정 리스크 점검")

    # Case D: AI / HR 테크 / 채용 / 조직문화
    elif any(k in full_text for k in ["AI", "채용", "조직문화", "평가", "경력직"]):
        checkpoints.append("AI 도구 도입 시 개인정보보호법 준수 및 채용 절차의 공정성/투명성 확보 절차 마련")
        checkpoints.append("내부 직무 역량 평가 기준 정비 및 신규 채용 프로세스 개선안 검토")

    # Default Case (기타 HR 트렌드)
    if not checkpoints:
        checkpoints.append(f"기사 내 언급된 주요 이슈('{title[:20]}...')와 관련한 사내 규정 유관 부서 수시 모니터링")
        checkpoints.append("관련 제도 도입 또는 개정 시 근로자 사전 의견 수렴 및 노사 협의 절차 마련")

    return {
        "summary": summary,
        "checkpoints": checkpoints[:2] # 최대 2개로 깔끔하게 제한
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

    print("📡 고품질 실무 중심 HR 뉴스 수집 및 추출 시작...")

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
                    insight = generate_free_hr_insight(link, title, raw_desc)

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
        print(f"\n🎉 총 {len(new_df)}개 실무 인사이트 데이터 저장 완료!")

if __name__ == "__main__":
    run_collection()
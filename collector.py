import os
import re
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. 환경 변수 및 설정
# ==========================================
CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("NAVER_CLIENT_ID") or "n_sOcFCgRFVkTTGUN9W7"
CLIENT_SECRET = os.getenv("CLIENT_SECRET") or os.getenv("NAVER_CLIENT_SECRET") or "56vRPwOw1b"

TRUSTED_SOURCES = [
    "hankyung.com", "mk.co.kr", "sedaily.com", "chosun.com", "joongang.co.kr", 
    "donga.com", "etnews.com", "worklaw.co.kr", "laborplus.co.kr", "hani.co.kr", 
    "khan.co.kr", "yna.co.kr", "newsis.com"
]

# 💡 '노동부' 행정 기사 대신 실무 '노동' 키워드로 강화
SEARCH_KEYWORDS = [
    "노동 근로감독 주52시간", "근로기준법 통상임금 판결", "중대재해처벌법 처벌",
    "노사 임단협 파업 협상", "기업 성과급 연봉 인상", "기업 조직문화 주4일제",
    "채용 트렌드 경력직", "HR 테크 AI 인사관리"
]

CSV_FILE_PATH = "hr_news.csv"

# ==========================================
# 2. 텍스트 정제 및 노이즈 필터링
# ==========================================
def clean_text(text):
    if not text: return ""
    return re.sub("<.*?>", "", text).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()

def is_trusted_source(link):
    return any(domain in link for domain in TRUSTED_SOURCES) if link else False

def is_noise_article(title, raw_desc=""):
    full_text = f"{title} {raw_desc}"
    
    # ❌ 1. HR 실무와 상관없는 분야 (금융, 지역행사, 정치, 소상공인 등)
    domain_noise = [
        "금융감독원", "가계대출", "대출난민", "사모펀드", "소상공인", "자영업자",
        "지자체", "군청", "시청", "구청", "도청", "의회", "보건소", "교육청",
        "초등학교", "중학교", "고등학교", "대학생", "공무원 수당", "농업", "어업",
        "부동산", "아파트", "청약", "주택공급", "코스피", "주가", "증권"
    ]
    if any(k in full_text for k in domain_noise):
        return True

    # ❌ 2. 단순 단신 / 인사동정 / 사건사고
    spec_noise = [
        "인사발령", "부음", "동정", "부고", "승진", "전보", "명예퇴직", "체포", "구속", "사기"
    ]
    if any(bad in title for bad in spec_noise) or re.search(r"\[인사\]|\[부음\]|\[동정\]", title):
        return True

    # ✅ 3. HR 필수 포함 키워드 체크 ('노동' 포함)
    hr_core_keywords = [
        "근로", "노동", "임금", "연봉", "성과급", "채용", "노사", "파업",
        "중대재해", "주52시간", "퇴직금", "복지", "조직문화", "HR", "인사",
        "구직", "이직", "근무", "재택", "포괄임금", "육아휴직"
    ]
    if not any(core in full_text for core in hr_core_keywords):
        return True

    return False

# 백업용 규칙 기반 분류기
def fallback_classify(title, desc):
    text = f"{title} {desc}"
    if any(k in text for k in ["노무", "근로", "고용", "중대재해", "파업", "노조", "임단협", "근로감독", "노동법", "노동", "통상임금", "포괄임금"]):
        return "노무 · 근로기준법 · 노동 이슈"
    elif any(k in text for k in ["채용", "연봉", "성과급", "구직", "인재", "리크루팅", "스카우트", "이직"]):
        return "채용 트렌드 및 이슈"
    elif any(k in text for k in ["조직문화", "근무", "복지", "재택", "주52시간", "워라밸", "주4일제"]):
        return "조직문화 & 근무제도"
    else:
        return "HR 트렌드 & HR Tech"

# ==========================================
# 3. 메인 수집 실행 함수
# ==========================================
def run_collection():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(hours=48)

    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    raw_articles = []

    print("📡 인사 실무 맞춤형 뉴스 수집 시작...")
    for kw in SEARCH_KEYWORDS:
        url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(kw)}&display=50&sort=date"
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
                
                # 노이즈 기사 필터링
                if is_noise_article(title, raw_desc): continue

                raw_articles.append({"title": title, "raw_desc": raw_desc, "link": link, "pubDate": item["pubDate"], "pub_dt": pub_dt})

    raw_articles.sort(key=lambda x: x["pub_dt"], reverse=True)
    
    # 중복 제거 (제목 기준)
    seen_titles = set()
    unique_articles = []
    for art in raw_articles:
        if art["title"] not in seen_titles:
            seen_titles.add(art["title"])
            unique_articles.append(art)

    new_articles = []
    print(f"🤖 총 {len(unique_articles)}개 필터링 통과 기사 정제 중...")
    
    for art in unique_articles:
        date_prefix = f"[{art['pub_dt'].strftime('%m/%d')}]"
        category = fallback_classify(art["title"], art["raw_desc"])

        domain = art["link"].split("/")[2].replace("www.", "") if "http" in art["link"] else "네이버뉴스"
        press_map = {
            "hankyung.com": "한국경제", "mk.co.kr": "매일경제", "sedaily.com": "서울경제", 
            "chosun.com": "조선일보", "joongang.co.kr": "중앙일보", "donga.com": "동아일보", 
            "etnews.com": "전자신문", "worklaw.co.kr": "월간노동법률", "laborplus.co.kr": "참여와혁신", 
            "hani.co.kr": "한겨레", "khan.co.kr": "경향신문", "yna.co.kr": "연합뉴스", "newsis.com": "뉴시스"
        }
        press_name = press_map.get(domain, "주요언론")

        new_articles.append({
            "category": category,
            "title": f"{date_prefix} {art['title']}",
            "description": art["raw_desc"],
            "link": art["link"],
            "press": press_name,
            "pubDate": art["pubDate"],
            "pub_dt_iso": art["pub_dt"].isoformat(),
            "collected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        })
        if len(new_articles) >= 16: break

    new_df = pd.DataFrame(new_articles)

    if not new_df.empty:
        new_df = new_df.sort_values(by="pub_dt_iso", ascending=False)
        new_df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8-sig")
        print(f"\n🎉 정제 완료! HR 실무 관심 기사 {len(new_df)}개가 '{CSV_FILE_PATH}'에 저장되었습니다.")
    else:
        print("\n⚠️ 필터링 조건을 만족하는 기사가 없습니다.")

if __name__ == "__main__":
    run_collection()
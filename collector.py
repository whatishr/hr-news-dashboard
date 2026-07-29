from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import os
import re
import urllib.parse
import json
import pandas as pd
import requests
import urllib3
from openai import OpenAI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. API 키 및 기본 환경 설정
# ==========================================
CLIENT_ID = (
    os.getenv("CLIENT_ID")
    or os.getenv("NAVER_CLIENT_ID")
    or "n_sOcFCgRFVkTTGUN9W7"
)
CLIENT_SECRET = (
    os.getenv("CLIENT_SECRET")
    or os.getenv("NAVER_CLIENT_SECRET")
    or "56vRPwOw1b"
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# 신뢰 언론사 도메인 리스트
TRUSTED_SOURCES = [
    "hankyung.com",   # 한국경제
    "mk.co.kr",        # 매일경제
    "sedaily.com",     # 서울경제
    "chosun.com",      # 조선일보
    "joongang.co.kr",  # 중앙일보
    "donga.com",       # 동아일보
    "etnews.com",      # 전자신문
    "worklaw.co.kr",   # 월간노동법률
    "laborplus.co.kr", # 레이버플러스
    "hani.co.kr",      # 한겨레
    "khan.co.kr",      # 경향신문
    "yna.co.kr",       # 연합뉴스
    "newsis.com"       # 뉴시스
]

SEARCH_KEYWORDS = [
    "고용노동부 근로감독",
    "근로기준법 판결 중대재해",
    "노사 임단협 파업",
    "기업 성과급 연봉 채용",
    "기업 조직문화 근무제도",
    "HR 테크 AI 인사"
]


# ==========================================
# 2. 텍스트 정제 및 노이즈 필터링
# ==========================================
def clean_text(text):
    if not text:
        return ""
    return (
        re.sub("<.*?>", "", text)
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .strip()
    )


def is_trusted_source(link):
    if not link:
        return False
    return any(domain in link for domain in TRUSTED_SOURCES)


def is_noise_article(title, raw_desc=""):
    full_text = f"{title} {raw_desc}"

    # 지자체, 보건소, 학교, 단순 자원봉사, 에세이 등 노이즈 차단
    noise_patterns = [
        "지자체", "군청", "시청", "구청", "도청", "의회", "지방의회", "경남도", "전남도", "충북도",
        "보건소", "교육청", "교육원", "특수교육원", "진로교육원", "학교", "학생", "교사", 
        "공무원", "주민센터", "면사무소", "읍사무소", "도지사", "시장", "군수", "구청장",
        "연수", "교과목", "대학", "캠퍼스", "서평", "에세이"
    ]
    if any(keyword in full_text for keyword in noise_patterns):
        return True

    # 단순 인사발령 차단
    spec_keywords = ["인사발령", "부음", "동정", "부고", "승진", "전보", "전입", "전출", "명예퇴직"]
    if any(bad in title for bad in spec_keywords) or re.search(r"\[인사\]|\[부음\]|\[동정\]", title):
        return True

    return False


# ==========================================
# 3. GPT 정밀 카테고리 매칭 로직 (엄격한 규칙 적용)
# ==========================================
def process_article_with_gpt(title, raw_description):
    """
    명확한 카테고리 정의와 기준에 따라 기사를 정확하게 분류
    """
    default_res = {
        "is_hr_related": False,
        "category": "노무 · 근로기준법 · 고용부 이슈",
        "brief_title": f"[국내] {title}",
        "description": raw_description
    }

    if not client or not OPENAI_API_KEY:
        return default_res

    try:
        prompt = f"""
당신은 기업 HR/인사 전문 에디터입니다.
아래 뉴스 기사를 읽고, **가장 정확한 카테고리 1개**를 엄격한 기준에 따라 분류해 주세요.

[카테고리 분류 상세 기준 - 매우 중요!]
1. "노무 · 근로기준법 · 고용부 이슈"
   - 사망 사고, 중대재해, 특별근로감독, 산재, 노조, 파업, 임단협, 근로기준법, 대법원 판결, 부당해고, 고용노동부 정책/지침 등 **모든 법률/노사/노동 이슈**는 무조건 이 카테고리입니다.
2. "채용 · 보상 · 조직문화"
   - 기업의 채용 소식, 성과급/연봉/임금 인상, 조직문화 개선, 유연근무제/재택근무 등 **기업 내부 인사/보상/근무제도** 관련 기사.
3. "HR 테크 · AI · 디지털"
   - AI 기반 HR 솔루션, HR Tech 소프트웨어, 학습/교육 디지털 플랫폼(SaaS), HR 데이터 분석 등 **IT/기술 접목 HR** 기사.
4. "글로벌 HR & 경영 트렌드"
   - 해외 기업 HR 사례, 글로벌 노동 트렌드, 기타 인사관련 일반 경영 트렌드.

[제외(is_hr_related: false) 기준]
- 단순 자산운용사/연금 투자의 '기금 운용 평가자' 관련 금융 기사, 장애인공단 등 일반 공공기관 내부 사건사고, 일반 지역 봉사 활동 등 HR 실무와 관련 없는 기사는 false 처리하세요.

[기사 정보]
- 제목: {title}
- 본문 개요: {raw_description}

[응답 형식]
JSON 형식으로만 답하세요:
{{
  "is_hr_related": true 또는 false,
  "category": "위 4개 카테고리명 중 정확히 하나",
  "brief_title": "[국내] 실무자 관점의 한 줄 요약 제목 (예: [국내] HD현대중공업 노동자 사망 사고... 노조 특별근로감독 촉구)",
  "description": "인사 실무 관점 1~2줄 핵심 요약"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 기사 내용을 정확하게 분석하여 오분류 없이 HR 카테고리에 매칭하는 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,  # 일관성을 위해 0.0으로 설정
            max_tokens=250,
            response_format={"type": "json_object"}
        )
        
        result_content = response.choices[0].message.content.strip()
        data = json.loads(result_content)
        return {
            "is_hr_related": data.get("is_hr_related", False),
            "category": data.get("category", "노무 · 근로기준법 · 고용부 이슈"),
            "brief_title": data.get("brief_title", f"[국내] {title}"),
            "description": data.get("description", raw_description)
        }
    except Exception as e:
        print(f"⚠️ GPT 처리 실패 ({title[:15]}...): {e}")
        return default_res


def is_similar(title1, title2):
    words1 = set(re.findall(r"\w+", title1))
    words2 = set(re.findall(r"\w+", title2))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    return (len(intersection) / min(len(words1), len(words2))) > 0.5


# ==========================================
# 4. 메인 수집 로직
# ==========================================
def fetch_top_hr_news(limit_total=12):
    raw_articles = []
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(days=2)

    print(f"🔎 정밀 카테고리 분류 기반 HR 뉴스 수집 시작... (기준: {cutoff_date.strftime('%Y-%m-%d %H:%M')} 이후)")
    
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }

    for kw in SEARCH_KEYWORDS:
        encoded_query = urllib.parse.quote(kw)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=50&sort=date"

        res = requests.get(url, headers=headers, verify=False)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                pub_date_str = item.get("pubDate", "")
                
                try:
                    pub_dt = parsedate_to_datetime(pub_date_str)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=kst)
                    
                    if pub_dt < cutoff_date:
                        continue
                except Exception:
                    continue

                link = item.get("originallink") or item.get("link", "")
                
                if not is_trusted_source(link):
                    continue

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                if is_noise_article(title, raw_desc):
                    continue

                raw_articles.append({
                    "title": title,
                    "raw_desc": raw_desc,
                    "link": link,
                    "pubDate": item["pubDate"],
                    "pub_dt": pub_dt
                })

    raw_articles.sort(key=lambda x: x["pub_dt"], reverse=True)

    unique_articles = []
    for art in raw_articles:
        duplicate = False
        for saved in unique_articles:
            if is_similar(art["title"], saved["title"]):
                duplicate = True
                break
        if not duplicate:
            unique_articles.append(art)

    print(f"📋 {len(unique_articles)}건 대상 GPT 정밀 매칭 진행 중...")
    final_articles = []
    
    for art in unique_articles:
        ai_res = process_article_with_gpt(art["title"], art["raw_desc"])
        
        if not ai_res.get("is_hr_related", False):
            continue

        final_articles.append({
            "category": ai_res["category"],
            "title": ai_res["brief_title"],
            "description": ai_res["description"],
            "link": art["link"],
            "pubDate": art["pubDate"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        if len(final_articles) >= limit_total:
            break

    df = pd.DataFrame(final_articles)
    if not df.empty:
        df.to_csv("hr_news.csv", index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 정밀 카테고리 매칭 뉴스 {len(df)}건 저장 완료!")
    else:
        print("⚠️ 조건에 맞는 최신 뉴스 결과가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=12)
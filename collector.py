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

# HR 카테고리별 정밀 검색어
SEARCH_KEYWORDS = [
    "고용노동부 지침",
    "근로기준법 판결",
    "노사 임단협",
    "기업 성과급 연봉",
    "기업 채용 조직문화",
    "HR 테크 AI"
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

    # 지자체, 보건소, 교육청, 학교, 에세이, 소상공인 정책 차단
    noise_patterns = [
        "지자체", "군청", "시청", "구청", "도청", "의회", "지방의회", "경남도", "전남도", "충북도",
        "보건소", "교육청", "교육원", "특수교육원", "진로교육원", "학교", "학생", "교사", 
        "공무원", "주민센터", "면사무소", "읍사무소", "도지사", "시장", "군수", "구청장",
        "연수", "교과목", "대학", "캠퍼스", "서평", "에세이", "동행론"
    ]
    if any(keyword in full_text for keyword in noise_patterns):
        return True

    # 인사발령, 부고 등 단순 인사동정 차단
    spec_keywords = ["인사발령", "부음", "동정", "부고", "승진", "전보", "전입", "전출", "명예퇴직"]
    if any(bad in title for bad in spec_keywords) or re.search(r"\[인사\]|\[부음\]|\[동정\]", title):
        return True

    return False


# ==========================================
# 3. GPT 정밀 카테고리 분류(4개 고정) 및 한줄 브리핑 생성
# ==========================================
def process_article_with_gpt(title, raw_description):
    """
    4개 지정 카테고리 중 하나로 분류하고 [국내] 머리말을 붙인 한 줄 브리핑 제목 생성
    """
    default_res = {
        "is_hr_related": False,
        "category": "노무 · 근로기준법 · 고용부",
        "brief_title": f"[국내] {title}",
        "description": raw_description
    }

    if not client or not OPENAI_API_KEY:
        return default_res

    try:
        prompt = f"""
당신은 민간기업 HR 인사실무자를 위한 핵심 이슈 브리핑 에디터입니다.
다음 뉴스 기사를 검토하여 민간기업 HR/노무 실무와 연관이 없으면 제외하고, 연관이 있다면 아래 4개 카테고리 중 단 하나를 선택해 분류하세요.

[제외(false) 기준]
- 지자체, 보건소, 학교/교육청, 공무원, 서평, 소상공인 지원 정책, 단발성 봉사 기사는 무조건 "is_hr_related": false 처리.

[4개 고정 카테고리 중 선택]
1. 노무 · 근로기준법 · 고용부 (고용부 정책/지침, 근로기준법, 법원 판례, 부당해고, 근로시간 등)
2. 노사관계 · 노동계 (노조, 파업, 임단협, 노사 협상/갈등 등)
3. 채용 · 보상 · 조직문화 (기업 채용, 성과급/연봉, 평가제도, 근무제도, 조직문화)
4. HR 테크 · AI · 글로벌 (HR Tech 솔루션, AI 인사, 글로벌 HR 트렌드)

[기사 정보]
- 제목: {title}
- 본문 개요: {raw_description}

[응답 형식]
JSON 형식으로만 답하세요:
{{
  "is_hr_related": true 또는 false,
  "category": "선택한 4개 카테고리명 중 정확히 하나",
  "brief_title": "[국내] 실무자 관점의 한 줄 핵심 요약 제목 (예: [국내] 대법원, 경영상 해고 시 서면 통지 의무 명확화)",
  "description": "상세 설명 1~2줄 요약"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 HR 인사실무자 전용 뉴스 브리핑을 작성하는 에디터입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=250,
            response_format={"type": "json_object"}
        )
        
        result_content = response.choices[0].message.content.strip()
        data = json.loads(result_content)
        return {
            "is_hr_related": data.get("is_hr_related", False),
            "category": data.get("category", "노무 · 근로기준법 · 고용부"),
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

    print(f"🔎 4대 카테고리 맞춤 HR 최신 뉴스 수집 시작... (기준: {cutoff_date.strftime('%Y-%m-%d %H:%M')} 이후)")
    
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

    print(f"📋 {len(unique_articles)}건 대상 GPT 4대 카테고리 정제 중...")
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
        print(f"🎉 [성공] 4개 카테고리 정제 뉴스 {len(df)}건 저장 완료!")
    else:
        print("⚠️ 조건에 맞는 최신 뉴스 결과가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=12)
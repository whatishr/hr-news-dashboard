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

# ★ [검증된 주요 언론사 도메인 리스트] - 이 출처가 아니면 무조건 제외
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

# HR / 인사관리 / 노무 / 노사 / 노동법 중심 검색어
SEARCH_KEYWORDS = [
    "HR 인사관리", 
    "근로기준법 개정", 
    "고용노동부 지침", 
    "노사 관계", 
    "노동법", 
    "인사제도 개편", 
    "조직문화 근무제도"
]


# ==========================================
# 2. 텍스트 정제 및 유틸리티 함수
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
    """
    기사 링크가 신뢰할 수 있는 매체 도메인을 포함하는지 확인 (하드 필터)
    """
    if not link:
        return False
    return any(domain in link for domain in TRUSTED_SOURCES)


def is_noise_article(title):
    """
    단순 승진/전보/부고/지자체 발령 명단 기사 차단
    """
    noise_keywords = [
        "인사발령", "부음", "동정", "부고", "승진", "특가", "부동산",
        "전보", "전입", "전출", "명예퇴직", "정기인사", "신규임용", "발령"
    ]
    if any(bad in title for bad in noise_keywords):
        return True

    if re.search(r"\[인사\]|\[부음\]|\[동정\]", title):
        return True

    return False


def classify_and_summarize_with_gpt(title, raw_description):
    """
    GPT를 이용하여 기사가 기업 인사/노무/HR 담당자에게 직접적인 유용한 정보인지 정밀 검증
    """
    default_res = {
        "category": "HR 트렌드 & HR Tech",
        "description": raw_description,
        "is_hr_related": True
    }

    if not client or not OPENAI_API_KEY:
        return default_res

    try:
        prompt = f"""
당신은 게임/플랫폼 기업의 HR 전문위원입니다.
다음 뉴스 기사가 기업의 **HR, 인사관리, 노무, 노사관계, 노동법, 조직문화**와 직접적인 관련이 있고 인사담당자에게 가치가 있는지 정밀 평가해 주세요.

[판단 기준]
- 단순 기업의 일반 채용 소식, 단발성 사건사고, 지자체 홍보 등은 'False'로 처리.
- 인사제도 변경, 노동법 개정, 고용부 지침, 노사 이슈, HR Tech 트렌드, 조직문화 변화 등 실무와 직결되면 'True'.

[선택할 카테고리 목록 (관련이 있을 경우)]
1. HR 트렌드 & HR Tech
2. 노무 · 근로기준법 · 고용노동부
3. 채용 트렌드 및 이슈
4. 조직문화 & 근무제도

[기사 정보]
- 제목: {title}
- 본문 개요: {raw_description}

[응답 형식]
JSON 형식으로만 출력하세요:
{{"is_hr_related": true 또는 false, "category": "선택한 카테고리명", "description": "인사 실무 관점 1~2줄 핵심 요약"}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 깐깐한 HR 전문 기사 검수자입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=250,
            response_format={"type": "json_object"}
        )
        
        result_content = response.choices[0].message.content.strip()
        data = json.loads(result_content)
        return {
            "is_hr_related": data.get("is_hr_related", True),
            "category": data.get("category", "HR 트렌드 & HR Tech"),
            "description": data.get("description", raw_description)
        }
    except Exception as e:
        print(f"⚠️ GPT 검증 실패 ({title[:15]}...): {e}")
        return default_res


def is_similar(title1, title2):
    words1 = set(re.findall(r"\w+", title1))
    words2 = set(re.findall(r"\w+", title2))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    return (len(intersection) / min(len(words1), len(words2))) > 0.5


# ==========================================
# 3. 뉴스 수집 및 메인 로직 함수
# ==========================================
def fetch_top_hr_news(limit_total=10):
    raw_articles = []
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(days=2)  # 최근 2일 이내 기준

    print(f"🔎 신뢰 언론사 대상 최근 2일 이내 HR/인사 전문 뉴스 수집 시작... (기준: {cutoff_date.strftime('%Y-%m-%d %H:%M')} 이후)")
    
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
                
                # ★ [필수 조건 1] 신뢰 언론사가 아니면 수집에서 즉시 제외
                if not is_trusted_source(link):
                    continue

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                # 단순 발령/승진/부음 차단
                if is_noise_article(title):
                    continue

                raw_articles.append({
                    "title": title,
                    "raw_desc": raw_desc,
                    "link": link,
                    "pubDate": item["pubDate"],
                    "pub_dt": pub_dt
                })

    # 최신 순 정렬
    raw_articles.sort(key=lambda x: x["pub_dt"], reverse=True)

    # 중복 기사 제거
    unique_articles = []
    for art in raw_articles:
        duplicate = False
        for saved in unique_articles:
            if is_similar(art["title"], saved["title"]):
                duplicate = True
                break
        if not duplicate:
            unique_articles.append(art)

    print(f"📋 1차 언론사 필터를 통과한 {len(unique_articles)}건 대상 GPT 정밀 HR 관련성 검증 시작...")
    final_articles = []
    
    for art in unique_articles:
        # ★ [필수 조건 2] GPT가 읽고 순수 HR/인사/노무 관련 기사인지 최종 판별
        ai_res = classify_and_summarize_with_gpt(art["title"], art["raw_desc"])
        
        if not ai_res.get("is_hr_related", True):
            continue

        final_articles.append({
            "category": ai_res["category"],
            "title": art["title"],
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
        print(f"🎉 [성공] 검증된 메이저 언론사의 HR 전문 뉴스 {len(df)}건을 저장했습니다!")
    else:
        print("⚠️ 최근 2일 이내 조건에 맞는 신뢰 언론사의 HR 전문 뉴스가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)
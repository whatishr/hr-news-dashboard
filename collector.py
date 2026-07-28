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

TRUSTED_SOURCES = [
    "hankyung.com", "mk.co.kr", "sedaily.com", "chosun.com", "joongang.co.kr",
    "donga.com", "etnews.com", "e27.co.kr", "worklaw.co.kr", "laborplus.co.kr",
    "hani.co.kr", "khan.co.kr"
]

# ★ HR / 인사관리 / 노무 / 노사 / 노동법 본질에 집중된 키워드 세트
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


def is_noise_article(title):
    """
    1차 키워드 단어 검사 (승진, 부고, 지자체 단순 인사발령 등)
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
    GPT를 이용하여 기사가 순수 HR/인사/노무 관련인지 검증하고 카테고리 분류 및 요약 진행
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
다음 뉴스 기사가 기업의 **HR/인사/노무/노사/근로제도**와 직접적인 관련이 있는지 평가하고, 적절한 카테고리를 선택해 주세요.

[판단 기준]
- 단순 기업의 일반 채용 공고, 단순 사건사고, 지자체 소식 등은 HR/인사 관련성 'False'로 판단할 것.
- 인사제도, 노동법, 노사관계, 조직문화, HR Tech, 근무제도 등 인사담당자가 숙지해야 할 내용이면 'True'.

[선택할 카테고리 목록 (관련이 있을 경우)]
1. HR 트렌드 & HR Tech (AI, HR테크, 디지털 인사, 인사시스템 등)
2. 노무 · 근로기준법 · 고용노동부 (근로기준법, 고용부 지침, 임금, 휴일, 노사관계, 노동법 등)
3. 채용 트렌드 및 이슈 (채용 시장 트렌드, 이직, 비정규직, 고용동향 등)
4. 조직문화 & 근무제도 (재택/유연근무, 기업문화, HRD/교육, 리더십 등)

[기사 정보]
- 제목: {title}
- 본문 개요: {raw_description}

[응답 형식]
JSON 형식으로만 출력하세요:
{{"is_hr_related": true 또는 false, "category": "선택한 카테고리명", "description": "실무 관점 1~2줄 요약문"}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 깐깐한 HR 전문 기사 검수자입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
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
        print(f"⚠️ GPT 분류/요약 실패 ({title[:15]}...): {e}")
        return default_res


def calculate_score(item):
    score = 0
    link = item.get("originallink", "") or item.get("link", "")
    if any(domain in link for domain in TRUSTED_SOURCES):
        score += 50
    if item.get("originallink"):
        score += 20
    return score


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

    print(f"🔎 순수 HR/인사/노무 관련 최신 뉴스 검색 중... (기준: {cutoff_date.strftime('%Y-%m-%d %H:%M')} 이후)")
    
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }

    for kw in SEARCH_KEYWORDS:
        encoded_query = urllib.parse.quote(kw)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=30&sort=date"

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

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                # 단순 발령/승진/부음 노이즈 1차 차단
                if is_noise_article(title):
                    continue

                score = calculate_score(item)
                raw_articles.append({
                    "title": title,
                    "raw_desc": raw_desc,
                    "link": item.get("originallink") or item["link"],
                    "pubDate": item["pubDate"],
                    "pub_dt": pub_dt,
                    "score": score,
                })

    # 정렬 및 유사 중복 제거
    raw_articles.sort(key=lambda x: (x["pub_dt"], x["score"]), reverse=True)

    unique_articles = []
    for art in raw_articles:
        duplicate = False
        for saved in unique_articles:
            if is_similar(art["title"], saved["title"]):
                duplicate = True
                break
        if not duplicate:
            unique_articles.append(art)

    print(f"\n🤖 {len(unique_articles)}건 대상 GPT 2차 정밀 HR 관련성 검증 및 분류 진행 중...")
    final_articles = []
    
    for art in unique_articles:
        ai_res = classify_and_summarize_with_gpt(art["title"], art["raw_desc"])
        
        # GPT 판단 결과 HR/인사/노무와 무관한 기사는 버림
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
        print(f"🎉 [성공] 정밀 검증된 HR/인사/노무 최신 뉴스 {len(df)}건을 저장했습니다!")
    else:
        print("⚠️ 최근 2일 이내 조건에 맞는 HR 전문 뉴스가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)
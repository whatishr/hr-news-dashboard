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

# ★ [개별 키워드 리스트] 네이버 API 안정성을 위해 개별 검색 진행
SEARCH_KEYWORDS = ["HR", "인사관리", "근로기준법", "채용", "조직문화", "고용노동부"]


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


def classify_and_summarize_with_gpt(title, raw_description):
    """
    GPT를 이용하여 기사의 최적 카테고리를 자동 분류하고 1~2줄 요약문을 생성합니다.
    """
    default_res = {
        "category": "HR 트렌드 & HR Tech",
        "description": raw_description
    }

    if not client or not OPENAI_API_KEY:
        return default_res

    try:
        prompt = f"""
다음 뉴스 기사의 내용에 가장 부합하는 카테고리를 아래 4개 중 '하나만' 선택하고, 게임/플랫폼 기업 인사담당자 관점에서 1~2문장(80~120자 내외)의 실무 요약문을 작성해 주세요.

[선택할 카테고리 목록]
1. HR 트렌드 & HR Tech (AI, HR테크, 디지털 인사, 신규 인사 시스템 등)
2. 노무 · 근로기준법 · 고용노동부 (근로기준법, 고용부 지침, 임금, 휴일 개정, 노사관계 등)
3. 채용 트렌드 및 이슈 (채용, 이직, 비정규직, 실업률, 고용동향 등)
4. 조직문화 & 근무제도 (재택/유연근무, 기업문화, HRD/교육, 리더십 등)

[기사 정보]
- 제목: {title}
- 본문 개요: {raw_description}

[응답 형식]
반드시 아래 JSON 형식으로만 출력해 주세요:
{{"category": "선택한 카테고리명", "description": "실무 요약문"}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 HR 기사를 분류하고 요약하는 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=250,
            response_format={"type": "json_object"}
        )
        
        result_content = response.choices[0].message.content.strip()
        data = json.loads(result_content)
        return {
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
    cutoff_date = now - timedelta(days=2)  # 최근 2일(48시간) 이내 기준

    print(f"🔎 최근 2일 이내의 모든 HR/인사 뉴스 검색 시작... (기준: {cutoff_date.strftime('%Y-%m-%d %H:%M')} 이후)")
    
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }

    # 키워드별 개별 검색 수행
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
                    
                    # 2일 초과 기사 필터링
                    if pub_dt < cutoff_date:
                        continue
                except Exception:
                    continue

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                # 단순 부고/승진/인사발령 노이즈 제외
                if any(bad in title for bad in ["인사발령", "부음", "동정", "부고", "승진", "특가"]):
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

    print(f"📋 총 {len(raw_articles)}건의 최근 2일 기사 1차 수집 완료 (정렬 및 중복 제거 진행 중...)")

    # 최신 날짜순 > 출처 점수순 정렬
    raw_articles.sort(key=lambda x: (x["pub_dt"], x["score"]), reverse=True)

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

        if len(unique_articles) >= limit_total:
            break

    print(f"\n🤖 최종 선별된 {len(unique_articles)}건 기사 GPT AI 자동 분류 및 요약 시작...")
    final_articles = []
    for art in unique_articles:
        ai_res = classify_and_summarize_with_gpt(art["title"], art["raw_desc"])
        
        final_articles.append({
            "category": ai_res["category"],
            "title": art["title"],
            "description": ai_res["description"],
            "link": art["link"],
            "pubDate": art["pubDate"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(final_articles)
    if not df.empty:
        df.to_csv("hr_news.csv", index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 최신 뉴스 {len(df)}건을 AI 분류 완료하여 hr_news.csv에 저장했습니다!")
    else:
        print("⚠️ 최근 2일 이내 조건에 맞는 최신 뉴스가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)
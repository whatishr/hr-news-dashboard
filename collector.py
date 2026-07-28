from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import os
import re
import urllib.parse
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

# OpenAI 클라이언트 생성
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# 주요 언론사 가산점 목록
TRUSTED_SOURCES = [
    "hankyung.com", "mk.co.kr", "sedaily.com", "chosun.com", "joongang.co.kr",
    "donga.com", "etnews.com", "e27.co.kr", "worklaw.co.kr", "laborplus.co.kr",
    "hani.co.kr", "khan.co.kr"
]

# 카테고리별 네이버 뉴스 검색어 설정
HR_SEARCH_TARGETS = {
    "노동법/법률이슈": '"근로기준법 개정" | "노동법 개정" | "최저임금 개정" | "노사관계 판결"',
    "HR/인사 트렌드": "(HR | 인사관리) + (트렌드 | 리포트 | 전략 | 제도)",
    "채용 트렌드": "(채용 | 이직 | 경력직) + (트렌드 | 시장 | 채용문화)",
    "조직문화/근무제도": "(조직문화 | 근무제도) + (주4일제 | 원격근무 | 유연근무 | 직원경험)",
}


# ==========================================
# 2. 텍스트 정제 및 유틸리티 함수
# ==========================================
def clean_text(text):
    """HTML 태그 및 특수문자 제거"""
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


def summarize_with_gpt(title, raw_description):
    """GPT 기반 인사담당자용 1~2줄 요약문 생성"""
    if not client or not OPENAI_API_KEY:
        print("⚠️ OpenAI API Key가 없어 원본 description을 사용합니다.")
        return raw_description

    try:
        prompt = f"""
다음은 최근 HR/노무 뉴스 기사의 제목과 원문 요약입니다.
이 뉴스를 읽고, 게임/플랫폼 기업의 **HR 인사담당자가 꼭 알아야 할 핵심 메시지 및 영향**을 중심으로 1~2문장(80~120자 내외)의 깔끔한 요약문으로 재작성해 주세요.

- 기사 제목: {title}
- 원문 개요: {raw_description}

[주의사항]
1. 단순 제목 반복이나 헤드라인 나열을 금지합니다.
2. '~함에 따라 대비가 필요함', '~가 확대되는 추세임' 등 인사 실무 관점의 명확한 서술어로 작성해 주세요.
3. 오직 요약문 결과만 출력하세요.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 게임/플랫폼 업계 전문 HR 아날리스트입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ GPT 요약 실패 ({title[:15]}...): {e}")
        return raw_description


def calculate_score(item):
    """언론사 신뢰도 점수 부여"""
    score = 0
    link = item.get("originallink", "") or item.get("link", "")
    if any(domain in link for domain in TRUSTED_SOURCES):
        score += 50
    if item.get("originallink"):
        score += 20
    return score


def is_similar(title1, title2):
    """기사 제목 유사도 판별 (중복 제거용)"""
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
    
    # KST (한국 시각) 기준 48시간(2일)전 계산
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    two_days_ago = now - timedelta(days=2)

    print("🔎 네이버 API 최신 HR 뉴스 검색 시작...")
    for category, query in HR_SEARCH_TARGETS.items():
        encoded_query = urllib.parse.quote(query)
        # sort=date (최신순)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=30&sort=date"
        headers = {
            "X-Naver-Client-Id": CLIENT_ID,
            "X-Naver-Client-Secret": CLIENT_SECRET,
        }

        res = requests.get(url, headers=headers, verify=False)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                pub_date_str = item.get("pubDate", "")
                
                # ★ [날짜 필터 및 검증]
                try:
                    pub_dt = parsedate_to_datetime(pub_date_str)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=kst)
                    
                    if pub_dt < two_days_ago:
                        continue  # 2일 초과된 옛날 기사는 필터링
                except Exception:
                    continue  # 날짜 파싱 오류 기사는 제외

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                # 불필요한 단순 인사/부고성 기사 제외
                if any(bad in title for bad in ["인사발령", "부음", "동정", "부고", "승진", "특가"]):
                    continue

                score = calculate_score(item)
                raw_articles.append({
                    "category": category,
                    "title": title,
                    "raw_desc": raw_desc,
                    "link": item.get("originallink") or item["link"],
                    "pubDate": item["pubDate"],
                    "pub_dt": pub_dt,  # 정렬용 날짜 객체
                    "score": score,
                })

    # ★ [핵심 정렬] 1순위: 발행 시각(최신순), 2순위: 출처 점수(신뢰도)
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

    print(f"\n🤖 최근 2일 내 수집된 검증 기사 {len(unique_articles)}건 GPT 요약 진행 중...")
    final_articles = []
    for art in unique_articles:
        gpt_summary = summarize_with_gpt(art["title"], art["raw_desc"])
        final_articles.append({
            "category": art["category"],
            "title": art["title"],
            "description": gpt_summary,
            "link": art["link"],
            "pubDate": art["pubDate"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    # CSV 파일 저장
    df = pd.DataFrame(final_articles)
    if not df.empty:
        df.to_csv("hr_news.csv", index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 최근 2일 이내의 최신 뉴스 {len(df)}건을 hr_news.csv에 저장했습니다!")
    else:
        print("⚠️ 최근 2일 이내 조건에 맞는 신규 뉴스가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)
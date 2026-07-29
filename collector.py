from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import os, re, urllib.parse, json
import pandas as pd
import requests, urllib3
from openai import OpenAI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("NAVER_CLIENT_ID") or "n_sOcFCgRFVkTTGUN9W7"
CLIENT_SECRET = os.getenv("CLIENT_SECRET") or os.getenv("NAVER_CLIENT_SECRET") or "56vRPwOw1b"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

TRUSTED_SOURCES = [
    "hankyung.com", "mk.co.kr", "sedaily.com", "chosun.com", "joongang.co.kr", 
    "donga.com", "etnews.com", "worklaw.co.kr", "laborplus.co.kr", "hani.co.kr", 
    "khan.co.kr", "yna.co.kr", "newsis.com"
]

SEARCH_KEYWORDS = [
    "고용노동부 근로감독", "근로기준법 판결 중대재해", "노사 임단협 파업",
    "기업 성과급 연봉 채용", "기업 조직문화 근무제도", "HR 테크 AI 인사"
]

CSV_FILE_PATH = "hr_news.csv"

def clean_text(text):
    if not text: return ""
    return re.sub("<.*?>", "", text).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()

def is_trusted_source(link):
    return any(domain in link for domain in TRUSTED_SOURCES) if link else False

def is_noise_article(title, raw_desc=""):
    full_text = f"{title} {raw_desc}"
    noise = ["지자체", "군청", "시청", "구청", "도청", "의회", "보건소", "교육청", "학교", "학생", "공무원", "대학"]
    if any(k in full_text for k in noise): return True
    spec = ["인사발령", "부음", "동정", "부고", "승진", "전보", "명예퇴직"]
    if any(bad in title for bad in spec) or re.search(r"\[인사\]|\[부음\]|\[동정\]", title): return True
    return False

def process_article_with_gpt(title, raw_description, date_prefix):
    default_res = {"is_hr_related": False, "category": "HR 트렌드 & HR Tech", "brief_title": f"{date_prefix} {title}", "description": raw_description}
    if not client or not OPENAI_API_KEY: return default_res

    try:
        prompt = f"""
당신은 기업 HR 인사 전문 에디터입니다.
아래 기사를 읽고 다음 4가지 카테고리 중 가장 정확한 **하나**를 엄격히 선택하세요.

[카테고리 목록 - 반환 문자열 일치 필수]
- "노무 · 근로기준법 · 고용부 이슈" (근로감독, 법원판결, 중대재해, 파업, 노사관계 등)
- "채용 트렌드 및 이슈" (신입/경력 채용, 연봉, 성과급, 구직, 인재확보 등)
- "조직문화 & 근무제도" (주52시간, 재택근무, 복지, 조직문화, 근무형태 등)
- "HR 트렌드 & HR Tech" (AI 인사, HR 솔루션, HR Tech, 인적자원개발 등)

[기사 정보]
제목: {title}
내용: {raw_description}

JSON 형식 응답:
{{
  "is_hr_related": true,
  "category": "선택한 카테고리명",
  "brief_title": "{date_prefix} [국내] 실무자 관점의 한 줄 요약 제목",
  "description": "인사 실무 관점의 1~2줄 요약 설명"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content.strip())
        return {
            "is_hr_related": data.get("is_hr_related", True),
            "category": data.get("category", "HR 트렌드 & HR Tech"),
            "brief_title": data.get("brief_title", f"{date_prefix} [국내] {title}"),
            "description": data.get("description", raw_description)
        }
    except Exception:
        return default_res

def run_collection():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(hours=48)

    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    raw_articles = []

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
                if is_noise_article(title, raw_desc): continue

                raw_articles.append({"title": title, "raw_desc": raw_desc, "link": link, "pubDate": item["pubDate"], "pub_dt": pub_dt})

    raw_articles.sort(key=lambda x: x["pub_dt"], reverse=True)
    
    new_articles = []
    for art in raw_articles:
        date_prefix = f"[{art['pub_dt'].strftime('%m/%d')}]"
        ai_res = process_article_with_gpt(art["title"], art["raw_desc"], date_prefix)
        if not ai_res.get("is_hr_related", False): continue

        # 언론사 명 추출
        domain = art["link"].split("/")[2].replace("www.", "") if "http" in art["link"] else "네이버뉴스"
        press_map = {"hankyung.com": "한국경제", "mk.co.kr": "매일경제", "sedaily.com": "서울경제", "chosun.com": "조선일보", "joongang.co.kr": "중앙일보", "donga.com": "동아일보", "etnews.com": "전자신문", "worklaw.co.kr": "월간노동법률", "laborplus.co.kr": "참여와혁신", "hani.co.kr": "한겨레", "khan.co.kr": "경향신문", "yna.co.kr": "연합뉴스", "newsis.com": "뉴시스"}
        press_name = press_map.get(domain, "주요언론")

        new_articles.append({
            "category": ai_res["category"],
            "title": ai_res["brief_title"],
            "description": ai_res["description"],
            "link": art["link"],
            "press": press_name,
            "pubDate": art["pubDate"],
            "pub_dt_iso": art["pub_dt"].isoformat(),
            "collected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        })
        if len(new_articles) >= 16: break

    new_df = pd.DataFrame(new_articles)

    if os.path.exists(CSV_FILE_PATH):
        try:
            existing_df = pd.read_csv(CSV_FILE_PATH)
            combined_df = pd.concat([new_df, existing_df], ignore_index=True).drop_duplicates(subset=["link"], keep="first")
        except: combined_df = new_df
    else:
        combined_df = new_df

    if not combined_df.empty:
        if "pub_dt_iso" in combined_df.columns:
            combined_df = combined_df.sort_values(by="pub_dt_iso", ascending=False)
        combined_df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8-sig")
        print(f"🎉 수집 완료! 총 {len(combined_df)}건 저장")

if __name__ == "__main__":
    run_collection()
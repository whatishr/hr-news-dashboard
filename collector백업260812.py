from __future__ import annotations

import datetime
import html
import json
import os
import re
import time
import urllib.parse
from collections import defaultdict
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# ============================================================
# 경로 및 환경설정
# ============================================================

BASE_DIR = Path(
    r"D:\Local developing\HR-news dashboard"
)

ENV_FILE_PATH = BASE_DIR / ".env"
CSV_FILE_PATH = BASE_DIR / "hr_news.csv"
STATUS_FILE_PATH = BASE_DIR / "collector_status.json"

load_dotenv(ENV_FILE_PATH)

NAVER_CLIENT_ID = (
    os.getenv("NAVER_CLIENT_ID")
    or os.getenv("CLIENT_ID")
    or ""
).strip()

NAVER_CLIENT_SECRET = (
    os.getenv("NAVER_CLIENT_SECRET")
    or os.getenv("CLIENT_SECRET")
    or ""
).strip()

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or ""
).strip()

GEMINI_MODEL_NAME = "gemini-3.1-flash-lite"


# ============================================================
# 기본 설정
# ============================================================

NAVER_DISPLAY_COUNT = 20
COLLECTION_DAYS = 2

# 검색어별 최대 네이버 결과 페이지
MAX_SEARCH_PAGES = 2

# Gemini 분류 요청 한 번에 넣을 기사 수
CLASSIFICATION_BATCH_SIZE = 40

# Gemini 분류 전 최대 후보 수
MAX_RAW_CANDIDATES = 300
MAX_CANDIDATES_PER_CATEGORY = 50

SMILEGATE_ARTICLE_LIMIT = 5
NORMAL_CATEGORY_ARTICLE_LIMIT = 4

KST = datetime.timezone(
    datetime.timedelta(hours=9)
)

CSV_COLUMNS = [
    "category",
    "date_str",
    "title",
    "summary",
    "checkpoints",
    "link",
    "pubDate",
    "collected_at"
]


# ============================================================
# 기존 카테고리명 유지
# ============================================================

CATEGORY_SMILEGATE = "오늘의 스마일게이트"
CATEGORY_HR_TREND = "HR 트렌드 섹션 (ai등HR/인사 트렌드)"
CATEGORY_LAW = "고용노동부/노동법/판례"
CATEGORY_LABOR = "노사/ 노동 / 노조/보상/평가/성과급"
CATEGORY_RECRUIT = "채용/조직문화"

CATEGORY_ORDER = [
    CATEGORY_SMILEGATE,
    CATEGORY_HR_TREND,
    CATEGORY_LAW,
    CATEGORY_LABOR,
    CATEGORY_RECRUIT
]


# ============================================================
# 후보 수집용 검색어
#
# 이 검색어는 최종 분류용이 아닙니다.
# 후보를 넓게 모으기 위한 용도로만 사용합니다.
# 최종 카테고리는 Gemini가 판단합니다.
# ============================================================

SEARCH_GROUPS = {
    CATEGORY_SMILEGATE: [
        "스마일게이트",
        "스마일게이트 게임",
        "스마일게이트 신작",
        "스마일게이트 서비스",
        "스마일게이트 사업",
        "스마일게이트 투자",
        "스마일게이트 글로벌",
        "스마일게이트 AI 기술",
        "스마일게이트 채용 조직",
        "스마일게이트 ESG 사회공헌",
        "스마일게이트 경영",
        "스마일게이트 대표 인터뷰"
    ],

    CATEGORY_HR_TREND: [
        "기업 인사제도 개편",
        "기업 평가체계 개편",
        "기업 성과평가 변경",
        "기업 성과관리 개편",
        "기업 보상체계 개편",
        "기업 연봉제 개편",
        "기업 직급체계 개편",
        "기업 승진제도 개편",
        "기업 인재관리 전략",
        "기업 피플애널리틱스",
        "기업 AI 인사관리",
        "기업 AI 평가",
        "기업 AI 성과관리",
        "기업 조직 운영 개편",
        ],

    CATEGORY_LAW: [
        "고용노동부 기업",
        "기업 근로기준법",
        "기업 노동법 개정",
        "기업 노동 판례",
        "기업 통상임금 판결",
        "기업 근로자성 판결",
        "기업 부당해고 판결",
        "기업 직장 내 괴롭힘 판례",
        "기업 근로시간 법 개정",
        "기업 육아휴직 법 개정",
        "기업 산업안전보건법"
    ],

    CATEGORY_LABOR: [
        "기업 노사관계",
        "기업 노동조합",
        "기업 임금협상",
        "기업 임단협",
        "기업 파업",
        "기업 성과급 갈등",
        "기업 인사평가 갈등",
        "기업 희망퇴직",
        "기업 구조조정",
        "기업 복리후생",
        "기업 스톡옵션"
    ],

    CATEGORY_RECRUIT: [
        "기업 채용 확대",
        "기업 채용 축소",
        "기업 신입 공채",
        "기업 경력 채용",
        "기업 수시채용",
        "기업 채용 방식 변경",
        "기업 인재 확보 경쟁",
        "기업 핵심인재 영입",
        "기업 온보딩 제도",
        "기업 퇴사율",
        "기업 이직률",
        "기업 리텐션",
        "기업 근무제도 개편",
        "기업 재택근무 축소",
        "기업 출근제 변경",
        "기업 주4일제",
        "기업 유연근무",
        "기업 조직문화 개편",
    ]
}


# ============================================================
# 코드에서 즉시 제외할 명백한 잡음
#
# 카테고리 판단은 Gemini가 담당하지만,
# 아래처럼 명백한 잡음은 API 호출 전에 제거합니다.
# ============================================================

HARD_EXCLUDE_KEYWORDS = [
    "재산분할",
    "이혼",
    "연예인",
    "방송 출연",
    "드라마",
    "프로야구",
    "프로축구",
    "스포츠 선수",
    "경마",
    "개인택시",
    "농업인",
    "학생 대상",
    "학교 수업",
    "교사 연수",
    "청소년 교육",
    "인공지능교육센터",
    "공무원 인사발령",
    "공무원 인사 발령",
    "공무원 전보",
    "공무원 승진자",
    "적극행정 우수사례",
    "우수행정",
    "공무원 포상"
        # 대학/학교
    "대학교",
    "대학",
    "캠퍼스",

    # 공기업/공공기관
    "개발공사",
    "공기업",
    "공사",

    # 카지노/리조트
    "카지노",
    "리조트",

    # 지자체
    "개발공사",
    "Who Is",
]


# ============================================================
# HTTP 세션
# ============================================================

def create_http_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ],
        allowed_methods=["GET"],
        raise_on_status=False
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session = requests.Session()

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/150.0 Safari/537.36"
        )
    })

    return session


HTTP_SESSION = create_http_session()


# ============================================================
# 상태 파일
# ============================================================

def write_status(
    success: bool,
    message: str,
    article_count: int = 0
) -> None:
    status = {
        "success": success,
        "message": message,
        "article_count": article_count,
        "updated_at": (
            datetime.datetime
            .now(KST)
            .isoformat()
        )
    }

    try:
        STATUS_FILE_PATH.write_text(
            json.dumps(
                status,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
    except OSError:
        pass


# ============================================================
# 문자열 처리
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = html.unescape(
        str(value)
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    text = re.sub(
        (
            r"\[(단독|포토|기획|속보|인사|부음|국내|해외|"
            r"종합|영상|인터뷰|현장)\]"
        ),
        "",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def normalize_title(
    title: str
) -> str:
    text = clean_text(
        title
    ).lower()

    text = re.sub(
        r"\[[^\]]+\]",
        " ",
        text
    )

    for word in [
        "단독",
        "속보",
        "종합",
        "포토",
        "영상",
        "기획",
        "인터뷰",
        "현장"
    ]:
        text = text.replace(
            word,
            " "
        )

    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        text
    )


def normalize_url(
    url: str
) -> str:
    if not url:
        return ""

    try:
        parts = urlsplit(
            url.strip()
        )

        query = [
            (key, value)
            for key, value in parse_qsl(
                parts.query,
                keep_blank_values=True
            )
            if not (
                key.lower().startswith("utm_")
                or key.lower() in {
                    "ref",
                    "source",
                    "campaign",
                    "fbclid",
                    "gclid"
                }
            )
        ]

        path = re.sub(
            r"/+$",
            "",
            parts.path
        )

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(query),
            ""
        ))

    except ValueError:
        return url.strip()


def contains_hard_exclude(
    title: str,
    description: str
) -> bool:
    target = (
        f"{title} {description}"
    ).lower()

    return any(
        keyword.lower() in target
        for keyword in HARD_EXCLUDE_KEYWORDS
    )


# ============================================================
# 날짜 처리
# ============================================================

def parse_pub_date(
    value: str
) -> Optional[datetime.datetime]:
    try:
        parsed = parsedate_to_datetime(
            value
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=KST
            )

        return parsed.astimezone(
            KST
        )

    except (
        TypeError,
        ValueError,
        OverflowError
    ):
        return None


# ============================================================
# 네이버 뉴스 검색
# ============================================================

def search_naver_news(
    keyword: str,
    headers: Dict[str, str],
    start: int
) -> Tuple[bool, List[Dict[str, Any]]]:
    query = urllib.parse.quote(
        keyword
    )

    url = (
        "https://openapi.naver.com/"
        "v1/search/news.json"
        f"?query={query}"
        f"&display={NAVER_DISPLAY_COUNT}"
        f"&start={start}"
        "&sort=date"
    )

    try:
        response = HTTP_SESSION.get(
            url,
            headers=headers,
            timeout=(5, 15),
            verify=False
        )

    except requests.RequestException as error:
        print(
            f"  ❌ 네이버 API 연결 실패: {error}"
        )
        return False, []

    if response.status_code != 200:
        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text[:300]

        print(
            "  ❌ 네이버 API 오류 "
            f"HTTP {response.status_code}: "
            f"{error_body}"
        )

        return False, []

    try:
        payload = response.json()
    except ValueError as error:
        print(
            f"  ❌ 네이버 API JSON 분석 실패: {error}"
        )
        return False, []

    items = payload.get(
        "items",
        []
    )

    if not isinstance(
        items,
        list
    ):
        return True, []

    return True, items


# ============================================================
# 원문 제목 및 본문
# ============================================================

@lru_cache(maxsize=256)
def fetch_article_page(
    url: str
) -> Tuple[str, str]:
    if not url:
        return "", ""

    try:
        response = HTTP_SESSION.get(
            url,
            timeout=(5, 12),
            verify=False,
            allow_redirects=True
        )

        if response.status_code != 200:
            return "", ""

        response.encoding = (
            response.apparent_encoding
            or response.encoding
        )

        page_html = response.text

        soup = BeautifulSoup(
            page_html,
            "html.parser"
        )

        original_title = ""

        for selector in [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]'
        ]:
            tag = soup.select_one(
                selector
            )

            if not tag:
                continue

            original_title = clean_text(
                tag.get(
                    "content",
                    ""
                )
            )

            if original_title:
                break

        if (
            not original_title
            and soup.title
            and soup.title.string
        ):
            original_title = clean_text(
                soup.title.string
            )

        body = ""

        if trafilatura is not None:
            try:
                body = (
                    trafilatura.extract(
                        page_html,
                        include_comments=False,
                        include_tables=False
                    )
                    or ""
                ).strip()

            except Exception:
                body = ""

        if len(body) < 100:
            selectors = [
                "article",
                ".article_body",
                "#articleBody",
                "#articeBody",
                "#newsCollapse",
                ".news_body",
                ".article-view-content-div",
                ".article_view",
                ".newsct_article"
            ]

            for selector in selectors:
                target = soup.select_one(
                    selector
                )

                if target is None:
                    continue

                candidate = clean_text(
                    target.get_text(
                        " ",
                        strip=True
                    )
                )

                if len(candidate) >= 100:
                    body = candidate
                    break

        return (
            original_title,
            body
        )

    except Exception as error:
        print(
            f"   └ 원문 접속 실패: {error}"
        )
        return "", ""


# ============================================================
# 1차 후보 수집
# ============================================================

def collect_raw_candidates(
    headers: Dict[str, str],
    cutoff_date: datetime.datetime
) -> Tuple[List[Dict[str, Any]], int]:
    candidates: List[
        Dict[str, Any]
    ] = []

    seen_urls: Set[str] = set()
    seen_titles: Set[str] = set()

    successful_api_calls = 0
    next_id = 1

    for suggested_category, keywords in (
        SEARCH_GROUPS.items()
    ):
        category_candidate_count = 0

        print(
            f"\n📂 후보 수집: [{suggested_category}]"
        )

        for keyword in keywords:
            print(
                f"  🔍 검색어: {keyword}"
            )

            accepted_count = 0

            for page_index in range(
                MAX_SEARCH_PAGES
            ):
                start = (
                    page_index
                    * NAVER_DISPLAY_COUNT
                    + 1
                )

                success, items = search_naver_news(
                    keyword,
                    headers,
                    start
                )

                if success:
                    successful_api_calls += 1

                if not items:
                    break

                for item in items:
                    pub_date_raw = str(
                        item.get(
                            "pubDate",
                            ""
                        )
                    )

                    pub_dt = parse_pub_date(
                        pub_date_raw
                    )

                    if (
                        pub_dt is None
                        or pub_dt < cutoff_date
                    ):
                        continue

                    title = clean_text(
                        item.get(
                            "title",
                            ""
                        )
                    )

                    description = clean_text(
                        item.get(
                            "description",
                            ""
                        )
                    )

                    link = (
                        item.get("originallink")
                        or item.get("link")
                        or ""
                    ).strip()

                    if not title:
                        continue

                    if contains_hard_exclude(
                        title,
                        description
                    ):
                        continue

                    normalized_url = normalize_url(
                        link
                    )

                    normalized_title = normalize_title(
                        title
                    )

                    # 확실한 URL 중복
                    if (
                        normalized_url
                        and normalized_url in seen_urls
                    ):
                        continue

                    # 완전히 같은 제목
                    if (
                        normalized_title
                        and normalized_title in seen_titles
                    ):
                        continue

                    candidate = {
                        "id": next_id,
                        "suggested_category": (
                            suggested_category
                        ),
                        "search_keyword": keyword,
                        "title": title,
                        "description": description,
                        "link": link,
                        "normalized_url": normalized_url,
                        "normalized_title": normalized_title,
                        "pubDate": pub_date_raw,
                        "pub_dt": pub_dt
                    }

                    candidates.append(
                        candidate
                    )
                    category_candidate_count += 1

                    if normalized_url:
                        seen_urls.add(
                            normalized_url
                        )

                    if normalized_title:
                        seen_titles.add(
                            normalized_title
                        )

                    next_id += 1
                    accepted_count += 1

                    if (
                        len(candidates)
                        >= MAX_RAW_CANDIDATES
                    ):
                        break

                if (
                    len(candidates)
                    >= MAX_RAW_CANDIDATES
                ):
                    break

                # 첫 페이지에서 어느 정도 확보됐으면
                # 불필요한 다음 페이지 호출을 생략합니다.
                if accepted_count >= 6:
                    break

            print(
                f"    └ 신규 후보 {accepted_count}건"
            )

            if (
                category_candidate_count
                >= MAX_CANDIDATES_PER_CATEGORY
            ):
                break

        if (
            len(candidates)
            >= MAX_RAW_CANDIDATES
        ):
            break

    candidates.sort(
        key=lambda article: (
            article["pub_dt"]
        ),
        reverse=True
    )

    return (
        candidates,
        successful_api_calls
    )


# ============================================================
# Gemini 공통 호출
# ============================================================

def extract_gemini_text(
    response: Any
) -> str:
    text_parts: List[str] = []

    candidates = (
        getattr(
            response,
            "candidates",
            None
        )
        or []
    )

    for candidate in candidates:
        content = getattr(
            candidate,
            "content",
            None
        )

        if content is None:
            continue

        parts = (
            getattr(
                content,
                "parts",
                None
            )
            or []
        )

        for part in parts:
            part_text = getattr(
                part,
                "text",
                None
            )

            if part_text:
                text_parts.append(
                    str(part_text)
                )

    if text_parts:
        return "\n".join(
            text_parts
        )

    try:
        return (
            getattr(
                response,
                "text",
                ""
            )
            or ""
        )
    except Exception:
        return ""


def parse_gemini_json(
    response_text: str
) -> Dict[str, Any]:
    text = response_text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    start = text.find(
        "{"
    )

    if start == -1:
        raise ValueError(
            "Gemini 응답에서 JSON 시작을 찾지 못했습니다."
        )

    decoder = json.JSONDecoder()

    try:
        data, _ = decoder.raw_decode(
            text[start:]
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini JSON 분석 실패: {error}"
        ) from error

    if not isinstance(
        data,
        dict
    ):
        raise ValueError(
            "Gemini 응답이 JSON 객체가 아닙니다."
        )

    return data


def call_gemini_json(
    prompt: str,
    temperature: float = 0.1
) -> Optional[Dict[str, Any]]:
    if (
        not GEMINI_API_KEY
        or genai is None
        or types is None
    ):
        return None

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception as error:
        print(
            f"   └ Gemini 클라이언트 생성 실패: {error}"
        )
        return None

    max_attempts = 4

    for attempt in range(
        max_attempts
    ):
        attempt_number = (
            attempt + 1
        )

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type=(
                        "application/json"
                    ),
                    temperature=temperature
                )
            )

            response_text = extract_gemini_text(
                response
            )

            if not response_text.strip():
                raise ValueError(
                    "Gemini 응답 내용이 비어 있습니다."
                )

            return parse_gemini_json(
                response_text
            )

        except Exception as error:
            error_message = str(
                error
            )

            print(
                "   └ Gemini 호출 실패 "
                f"({attempt_number}/{max_attempts}): "
                f"{error_message}"
            )

            is_last_attempt = (
                attempt_number >= max_attempts
            )

            if is_last_attempt:
                break

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "high demand"
                in error_message.lower()
            ):
                wait_seconds = (
                    5 * (2 ** attempt)
                )

            elif (
                "429" in error_message
                or "RESOURCE_EXHAUSTED"
                in error_message
                or "quota"
                in error_message.lower()
            ):
                wait_seconds = (
                    10 * (2 ** attempt)
                )

            elif (
                "404" in error_message
                or "NOT_FOUND"
                in error_message
            ):
                break

            else:
                wait_seconds = 3

            print(
                f"   ⏳ {wait_seconds}초 후 재시도합니다."
            )

            time.sleep(
                wait_seconds
            )

    return None


# ============================================================
# Gemini 일괄 분류
# ============================================================

def build_classification_prompt(
    batch: List[Dict[str, Any]]
) -> str:
    article_payload = []

    for article in batch:
        article_payload.append({
            "id": article["id"],
            "title": article["title"],
            "description": article["description"],
            "search_keyword": article["search_keyword"],
            "suggested_category": (
                article["suggested_category"]
            ),
            "date": article["pub_dt"].strftime(
                "%Y-%m-%d %H:%M"
            )
        })

    allowed_categories = CATEGORY_ORDER

    return f"""
당신은 대한민국 민간기업의 HR·인사·노무 담당자를 위한
뉴스 편집자입니다.

아래 기사 목록을 검토하여
각 기사에 대해 다음 순서로 판단하세요.

아래 기사 목록을 다음 순서로 판단하세요.

1. 먼저 기사의 핵심 주체가 스마일게이트인지 판단합니다.

- 스마일게이트가 기사의 핵심 주체라면
  HR 관련 기사인지 여부와 관계없이
  "오늘의 스마일게이트" 후보로 판단합니다.

- 게임, 신작, 서비스, 사업, 투자, 글로벌,
  AI·기술, 채용·조직, 경영, ESG·사회공헌 등
  스마일게이트 자체의 주요 소식을 포함합니다.

2. 스마일게이트가 핵심 주체가 아닌 기사만
   HR 카테고리 분류를 진행합니다.

이 경우 다음을 판단합니다.

- 사람, 조직, 고용, 노동, 보상, 평가, 채용,
  근무방식, 조직운영 또는 HR 관련 법·제도와
  직접 관련된 사건인가?

- 민간기업 HR 담당자가 이 기사를 읽음으로써
  제도 운영, 정책 대응, 타사 사례 파악,
  인력운영 판단에 실질적인 참고를 얻을 수 있는가?

위 조건을 만족하는 경우에만
HR 관련 카테고리로 분류합니다.

[허용 카테고리]
{json.dumps(allowed_categories, ensure_ascii=False)}

[핵심 판단 원칙]

기사 제목에 반드시 "HR", "인사", "채용" 등의 단어가
직접 포함될 필요는 없습니다.

대신 제목만 읽었을 때
"기업의 사람·조직·고용 관련 중요한 변화나 사건"이라는 점이
명확하게 드러나야 합니다.

예:

포함 가능
- "A사, 전 직원 주 3일 출근제로 전환"
- "B사, 저성과자 관리 제도 강화"
- "C사, 성과급 지급 기준 변경"
- "D사, 희망퇴직 실시"
- "E사 노조, 임금협상 결렬로 파업 예고"
- "대법원, 통상임금 판단 기준 변경"
- "고용노동부, 육아휴직 제도 개편 발표"

위 사례는 제목에 'HR'이라는 단어가 없어도
기업 HR 담당자의 업무와 직접 관련되므로 포함할 수 있습니다.

반면 다음은 제외합니다.

- 단순 기업 실적
- 주가 및 투자 뉴스
- 제품 및 서비스 출시
- 홍보성 인터뷰
- 일반 산업 동향
- 일반 AI 기술 뉴스
- 개인 취업 성공 사례
- 단순 채용 공고
- 행사·협약·수상
- HR 담당자의 의사결정에 참고하기 어려운 기사
- Who Is 시리즈
- CEO·대표이사·임원의 프로필 소개 기사
- 인물 소개 및 경력 중심 기사
- Great Place to Work 선정 기사
- 일하기 좋은 기업 선정 기사
- 기업문화 인증 기사
- ESG·브랜드 평판 중심 기사
- 수상 및 인증 기사

[include 판단]

다음 질문 중 하나 이상에 명확하게 YES이면 후보가 될 수 있습니다.

- 다른 기업의 HR 제도 변화 또는 운영 사례인가?
- 인력 규모, 구조, 채용, 퇴직 등 workforce 변화인가?
- 평가·보상·승진·성과관리 방식의 변화인가?
- 근무방식이나 조직운영 방식의 변화인가?
- 노조·임금·성과급·구조조정 등 노사 이슈인가?
- HR 업무에 영향을 주는 정부 정책·법령·판례인가?
- AI가 실제 기업의
  채용, 평가, 보상, 인력운영, 업무방식 변화에
  적용되는 사례인가?

  모두 NO라면 include=false입니다.

단, AI 제품 출시, AI 서비스 출시,
AI 교육, AI 솔루션 홍보,
Copilot·ERP·SaaS 기능 소개는
include=false입니다.

가장 중요한 최종 판단 기준은 다음 질문입니다.

"민간기업 HR 담당자가 이 기사를 읽고
'우리 회사에도 적용하거나 참고해볼 수 있겠다'
라고 생각할 가능성이 있는가?"

YES이면 include=true를 검토할 수 있습니다.
NO이면
HR 관련 키워드가 포함되어 있더라도
include=false입니다.

기사의 핵심이
HR 제도 운영이 아니라

- 제품 판매
- 서비스 홍보
- 교육 홍보
- 컨설팅 홍보
- 기업 홍보
- CEO 또는 임원 개인
- 오너 일가
- 경영권 및 승계

라면 반드시 include=false입니다.
[practical_value 판단]

practical_value는
"HR 담당자가 실제 업무에 활용할 가치"를 평가합니다.

90~100
법·판례, 정부 정책,
평가·보상 제도 변경,
대기업 HR 제도 변화 등
즉시 참고해야 하는 기사.

70~89
타사의 채용, 조직문화,
노사관계,
성과관리 사례 등
실무 참고 가치가 높은 기사.

50~69
HR 관련은 있지만 실무 활용성이 제한적이다.
실무 활용 가치가 낮더라도
HR 관련 키워드만 포함되어 있다는 이유만으로
include=true를 선택해서는 안 됩니다.

0~49
실무 활용 가치가 거의 없다.

원칙적으로 practical_value가 60 미만이면 include=false로 판단하세요.


[hr_relevance 판단]

hr_relevance는
"이 기사가 민간기업 HR 담당자의 업무와 얼마나 직접적으로 관련되는지"를 평가합니다.

90~100
HR, 인사, 노무, 채용, 평가, 보상, 조직문화, 근무제도,
노동법, 노사관계가 기사의 핵심 주제이다.

70~89
기업의 사람·조직 운영과 밀접하게 관련되어 있으며
HR 담당자가 업무상 참고할 가치가 높다.

50~69
HR와 간접적인 관련은 있으나
경영, 산업, AI 등의 일반 기사 성격이 더 강하다.

0~49
HR와 직접적인 관련이 거의 없다.

[카테고리 분류]

1. 오늘의 스마일게이트
[오늘의 스마일게이트 추가 기준]

- 스마일게이트가 기사의 핵심 주체여야 합니다.
제공된 제목과 description을 기준으로
스마일게이트가 기사의 명백한 핵심 주체인지 판단합니다.

여러 게임사·기업을 함께 다루며
스마일게이트가 여러 사례 중 하나로 보이는 경우 제외합니다.

스마일게이트가 기사의 중심 주체로 명확히 판단되는 경우에만
"오늘의 스마일게이트"로 분류합니다.
- 제목에 스마일게이트가 있더라도 본문의 절반 이상이 다른 기업, 산업 일반, 타사 사례에 관한 내용이면 제외합니다.
- 반대로 제목과 본문의 핵심 사건이 스마일게이트의 사업, 게임, 서비스, 기술, HR, 경영, ESG 등이라면 포함합니다.

2. HR 트렌드 섹션 (AI 등 HR/인사 트렌드)

기업 내부 HR 제도 또는 운영 방식의 실제 변화가
기사의 핵심인 경우만 분류합니다.

예)
- 인사제도 개편
- 평가·성과관리 변경
- 보상체계 변경
- 직급·승진제도 개편
- 인재관리 전략 변화
- 조직 운영 방식 변화
- HR AI 실제 도입 사례
- 피플 애널리틱스 활용 사례

다음은 HR 트렌드가 아닙니다.

- 기업 내부 제도 변화가 아닌 기사
- 제품·서비스·교육·컨설팅 홍보
- CEO·오너·경영권·지배구조 기사
- 기업 실적·투자·브랜드 홍보
- 일반 AI 기술 또는 제품 소개

채용이나 근무제도가 핵심이면
'채용/조직문화'를 우선합니다.

3. 고용노동부/노동법/판례
- 법령 개정
- 정부 정책
- 고용노동부 지침
- 법원 판결
- 노동위원회 판단
- 근로자성
- 통상임금
- 부당해고
- 근로시간 등

기업 사례가 등장하더라도
기사의 핵심이 법적 판단이면 이 카테고리를 우선합니다.

4. 노사/ 노동 / 노조/보상/평가/성과급

- 노조
- 파업
- 임단협
- 임금협상
- 성과급 갈등
- 평가 갈등
- 희망퇴직
- 구조조정
- 노사분쟁

기업의 실제 갈등 또는 노사관계 사건이 핵심인 경우 분류합니다.

5. 채용/조직문화
- 채용 확대·축소
- 인재 확보
- 신입·경력 채용 전략
- 온보딩
- 리텐션
- 조직문화
- 재택근무
- 출근제
- 유연근무
- 주4일제 등 근무방식 변화

기업이 실제 채용하는 기사만 포함합니다.

채용 플랫폼,
채용 솔루션,
채용 교육,
채용 컨설팅은 포함하지 않습니다.

[카테고리 충돌 시 우선순위]

스마일게이트가 기사의 핵심 주체
→ 오늘의 스마일게이트

스마일게이트 기사에서는
채용, 조직문화, AI, 경영, 기술 등의 내용이더라도
다른 HR 카테고리보다 "오늘의 스마일게이트"를 우선합니다.

그 다음에만 아래 우선순위를 적용합니다.

1. 법령 개정, 정부 시행, 판결, 법적 해석이 핵심이면
   반드시 "고용노동부/노동법/판례"

2. 회사와 노조의 실제 협상·파업·임금·성과급 갈등이면
   "노사/ 노동 / 노조/보상/평가/성과급"

3. 채용 규모·채용 방식·인재 확보·조직문화·근무방식이면
   "채용/조직문화"

4. 그 외 기업 내부 HR 제도의 도입·개편 사례만
   "HR 트렌드"

   육아휴직, 출산휴가, 근로시간, 연차, 통상임금 등
법령이나 정부 제도 변경이 핵심인 기사는
근무제도나 조직문화처럼 보여도
"고용노동부/노동법/판례"를 우선합니다.

[제외 원칙]

다음은 원칙적으로 제외합니다.

- 공무원 인사발령
- 지자체 인사
- 학교 학생 대상 프로그램
- 일반 교육 행사
- 스포츠·연예
- 개인 사건
- 단순 제품 출시
- 단순 솔루션 출시
- MOU
- 업무협약
- 단순 행사
- 수상
- 단순 대표 선임·임원 승진
- 단순 채용 공고
다음은 원칙적으로 include=false입니다.

- AI 솔루션 출시
- SaaS 출시
- HR 솔루션 출시
- Copilot, ERP, 그룹웨어 등 제품 홍보 기사
- 컨설팅 서비스 출시 또는 정부지원 사업 홍보
- 교육 과정 개설
- 세미나, 웨비나, 포럼 개최
- 교육기관·컨설팅사의 홍보 기사
- "일하기 좋은 기업", GPTW 등 인증·수상 기사
- CEO 인터뷰
- 오너 일가
- 경영권 승계
- 지배구조
- 대표이사 프로필
- 임원 개인 소개

단, 기사 주체가 학교·공기업·병원·협회·리조트라는 이유만으로
자동 제외하지 마세요.

해당 조직의 사례가
민간기업 HR 담당자가 참고할 만한
노동법, 노사관계, 평가·보상, 근무제도 사례라면
포함할 수 있습니다.


[출력 규칙]

각 기사에 대해 다음 필드를 출력하세요.

- article_id
- include
- category
- practical_value
- topic
- reason

reason은 반드시
"왜 민간기업 HR 담당자가 읽을 가치가 있는지"
또는
"왜 HR 브리핑에서 제외해야 하는지"
구체적으로 한 문장으로 작성합니다.

- article ID를 절대 변경하지 마세요.
- category는 허용 카테고리 중 하나 또는 null
- include는 true 또는 false
- hr_relevance는 0~100
- practical_value는 0~100
- topic은 짧은 한국어 또는 지정 Topic
- why_hr는 include=true인 경우 왜 민간기업 HR 담당자가 읽어야 하는지 한 문장으로 작성
- reason은 포함 또는 제외한 이유를 한 문장으로 작성
- JSON만 출력

[기사 목록]
{json.dumps(article_payload, ensure_ascii=False)}

[JSON 형식]
{{
  "articles": [
    {{
      "id": 1,
      "include": true,
      "category": "채용/조직문화",
      "topic": "기업 온보딩",
      "hr_relevance": 91,
      "practical_value": 82,
      "why_hr": "타사의 온보딩 운영 사례를 참고하여 자사 제도 개선에 활용할 수 있다.",
      "reason": "기업의 온보딩 제도 운영 사례가 기사의 핵심이다."
    }}
  ]
}}
""".strip()


def fallback_classification(
    batch: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Gemini 분류가 실패했을 때는
    검색 출처 카테고리를 임시 사용합니다.

    이 경우 정확도는 낮아질 수 있지만,
    전체 수집이 중단되지는 않습니다.
    """

    results = []

    for article in batch:
        results.append({
            "id": article["id"],
            "include": True,
            "category": article["suggested_category"],
            "topic": article["search_keyword"],
            "duplicate_group": f"fallback_{article['id']}",
            "hr_relevance": 50,
            "practical_value": 50,
            "why_hr": "Gemini 분류 실패로 검색 카테고리를 임시 적용한 기사입니다.",
            "reason": "Gemini 분류 실패로 검색 카테고리 사용"
        })

    return results


def classify_candidates_with_gemini(
    candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    article_by_id = {
        article["id"]: article
        for article in candidates
    }

    classified = []

    for batch_start in range(
        0,
        len(candidates),
        CLASSIFICATION_BATCH_SIZE
    ):
        batch = candidates[
            batch_start:
            batch_start + CLASSIFICATION_BATCH_SIZE
        ]

        print(
            "\n🤖 Gemini 기사 일괄 분류 "
            f"{batch_start + 1}~"
            f"{batch_start + len(batch)}"
        )

        prompt = build_classification_prompt(
            batch
        )

        data = call_gemini_json(
            prompt,
            temperature=0.1
        )

        if data is None:
            result_items = fallback_classification(
                batch
            )
        else:
            result_items = data.get(
                "articles",
                []
            )

            if not isinstance(
                result_items,
                list
            ):
                result_items = fallback_classification(
                    batch
                )

        result_by_id = {}

        for result in result_items:
            if not isinstance(
                result,
                dict
            ):
                continue

            try:
                article_id = int(
                    result.get(
                        "id"
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                continue

            result_by_id[
                article_id
            ] = result

        for article in batch:
            result = result_by_id.get(
                article["id"]
            )

            if result is None:
                continue

            include = result.get(
                "include",
                False
            )

            # 문자열 "false"를 True로 읽지 않도록 처리
            if isinstance(
                include,
                str
            ):
                include = (
                    include.strip().lower()
                    == "true"
                )

            if not include:
                continue

            why_hr = str(
                result.get(
                    "why_hr",
                    ""
                )
            ).strip()

            if not why_hr:
                continue

            category = result.get(
                "category"
            )

            if category not in CATEGORY_ORDER:
                continue

            enriched = dict(
                article
            )

            enriched["category"] = category

            enriched["topic"] = str(
                result.get(
                    "topic",
                    ""
                )
            ).strip()

            enriched["duplicate_group"] = (
                f"article_{article['id']}"
            )

            try:
                enriched["hr_relevance"] = int(
                    result.get(
                        "hr_relevance",
                        0
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                enriched["hr_relevance"] = 0

            try:
                enriched["practical_value"] = int(
                    result.get(
                        "practical_value",
                        50
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                enriched["practical_value"] = 50

            enriched["classification_reason"] = str(
                result.get(
                    "reason",
                    ""
                )
            ).strip()

            enriched["why_hr"] = why_hr

            classified.append(
                enriched
            )

        time.sleep(1)

    return classified


# ============================================================
# Gemini 결과 기준 중복 정리
# ============================================================
def review_duplicates_with_gemini(
    articles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    1차 분류를 통과한 기사들을 카테고리별로 비교하여
    동일 사건에 같은 duplicate_group을 부여합니다.
    """

    reviewed_articles = []

    for category in CATEGORY_ORDER:
        category_articles = [
            article
            for article in articles
            if article.get("category") == category
        ]

        if not category_articles:
            continue

        # 1건뿐이면 중복 비교 불필요
        if len(category_articles) == 1:
            article = dict(
                category_articles[0]
            )

            article["duplicate_group"] = (
                f"article_{article['id']}"
            )

            reviewed_articles.append(
                article
            )

            continue

        article_payload = []

        for article in category_articles:
            article_payload.append({
                "id": article["id"],
                "title": article["title"],
                "description": article.get(
                    "description",
                    ""
                ),
                "date": article["pub_dt"].strftime(
                    "%Y-%m-%d %H:%M"
                )
            })

        prompt = f"""
당신은 뉴스 중복 검수자입니다.

아래 기사들은 이미 동일한 카테고리로 분류된 기사입니다.

기사 제목과 description을 서로 비교하여
실질적으로 동일한 사건을 다루는 기사끼리
같은 duplicate_group을 부여하세요.

[카테고리]
{category}

[중복으로 판단]

- 동일 기업의 동일 제도 변경
- 동일 채용 발표
- 동일 노사협상 또는 파업
- 동일 성과급·보상 사건
- 동일 법령 개정 또는 정부 발표
- 동일 판결
- 동일 보도자료를 여러 언론사가 재작성
- 표현은 다르지만 핵심 사건, 주체, 시점이 같은 경우

[중복이 아님]

- 같은 기업의 서로 다른 사건
- 같은 주제지만 다른 기업 사례
- 같은 법률 주제라도 서로 다른 판결이나 사건
- 기존 사건 이후 새로운 결정이나 결과가 나온 후속 기사

중요:
단순히 키워드가 비슷하다는 이유로 중복 처리하지 마세요.

중복이 없는 기사도 고유한 duplicate_group을 부여하세요.

기사 ID는 절대 변경하지 마세요.

JSON만 출력하세요.

[기사 목록]
{json.dumps(article_payload, ensure_ascii=False)}

[JSON 형식]
{{
  "articles": [
    {{
      "id": 1,
      "duplicate_group": "dup_001"
    }},
    {{
      "id": 2,
      "duplicate_group": "dup_001"
    }},
    {{
      "id": 3,
      "duplicate_group": "dup_002"
    }}
  ]
}}
""".strip()

        data = call_gemini_json(
            prompt,
            temperature=0.0
        )

        if data is None:
            for article in category_articles:
                fallback_article = dict(
                    article
                )

                fallback_article[
                    "duplicate_group"
                ] = (
                    f"article_{article['id']}"
                )

                reviewed_articles.append(
                    fallback_article
                )

            continue

        result_items = data.get(
            "articles",
            []
        )

        group_by_id = {}

        if isinstance(
            result_items,
            list
        ):
            for result in result_items:
                if not isinstance(
                    result,
                    dict
                ):
                    continue

                try:
                    article_id = int(
                        result.get("id")
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    continue

                duplicate_group = str(
                    result.get(
                        "duplicate_group",
                        f"article_{article_id}"
                    )
                ).strip()

                group_by_id[
                    article_id
                ] = duplicate_group

        for article in category_articles:
            reviewed_article = dict(
                article
            )

            reviewed_article[
                "duplicate_group"
            ] = group_by_id.get(
                article["id"],
                f"article_{article['id']}"
            )

            reviewed_articles.append(
                reviewed_article
            )

        time.sleep(1)

    return reviewed_articles


def deduplicate_classified_articles(
    articles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    같은 duplicate_group에서는
    실무 가치 점수가 가장 높은 기사 하나만 남깁니다.

    점수가 같으면 최신 기사를 우선합니다.
    """

    groups: Dict[
        str,
        List[Dict[str, Any]]
    ] = defaultdict(list)

    for article in articles:
        duplicate_group = article.get(
            "duplicate_group",
            f"article_{article['id']}"
        )

        groups[
            duplicate_group
        ].append(article)

    deduplicated = []

    for group_articles in groups.values():
        group_articles.sort(
            key=lambda article: (
                article.get(
                    "practical_value",
                    0
                ),
                article["pub_dt"]
            ),
            reverse=True
        )

        deduplicated.append(
            group_articles[0]
        )

    # 혹시 Gemini가 중복 그룹을 놓쳤더라도
    # URL과 완전 동일 제목은 다시 제거합니다.
    final_articles = []
    seen_urls: Set[str] = set()
    seen_titles: Set[str] = set()

    for article in sorted(
        deduplicated,
        key=lambda item: (
            item.get(
                "practical_value",
                0
            ),
            item["pub_dt"]
        ),
        reverse=True
    ):
        normalized_url = article.get(
            "normalized_url",
            ""
        )

        normalized_title = article.get(
            "normalized_title",
            ""
        )

        if (
            normalized_url
            and normalized_url in seen_urls
        ):
            continue

        if (
            normalized_title
            and normalized_title in seen_titles
        ):
            continue

        final_articles.append(
            article
        )

        if normalized_url:
            seen_urls.add(
                normalized_url
            )

        if normalized_title:
            seen_titles.add(
                normalized_title
            )

    return final_articles


# ============================================================
# 카테고리별 다양성 선정
# ============================================================

def select_category_candidates(
    articles: List[Dict[str, Any]],
    category: str,
    limit: int
) -> List[Dict[str, Any]]:
    category_articles = [
        article
        for article in articles
        if article.get(
            "category"
        ) == category
    ]

    category_articles.sort(
        key=lambda article: (
            article.get(
                "practical_value",
                0
            ),
            article["pub_dt"]
        ),
        reverse=True
    )

    selected = []
    used_topics: Set[str] = set()

    # 1차: Topic당 한 건
    for article in category_articles:
        if len(selected) >= limit:
            break

        topic = article.get(
            "topic",
            ""
        ).strip()

        topic_key = (
            topic.lower()
            if topic
            else f"article_{article['id']}"
        )

        if topic_key in used_topics:
            continue

        selected.append(
            article
        )

        used_topics.add(
            topic_key
        )

    # 2차: Topic이 부족하면 남은 고득점 기사로 보충
    for article in category_articles:
        if len(selected) >= limit:
            break

        if article in selected:
            continue

        selected.append(
            article
        )

    selected.sort(
        key=lambda article: (
            article["pub_dt"]
        ),
        reverse=True
    )

    return selected


# ============================================================
# 기본 요약
# ============================================================

def make_fallback_summary(
    title: str,
    content: str
) -> Tuple[str, List[str]]:
    normalized = re.sub(
        r"\s+",
        " ",
        content
    ).strip()

    if not normalized:
        normalized = title

    sentences = [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?。])\s+",
            normalized
        )
        if sentence.strip()
    ]

    first = (
        sentences[0][:180]
        if sentences
        else title[:180]
    )

    second = (
        sentences[1][:180]
        if len(sentences) >= 2
        else "기사 원문에서 세부 내용과 적용 영향을 확인해야 합니다."
    )

    return (
        f"• {first}\n• {second}",
        [
            "원문 기사 내용 확인",
            "사내 제도 및 업무 관련성 검토"
        ]
    )


# ============================================================
# 최종 기사 요약
# ============================================================

def generate_article_summary(
    category: str,
    title: str,
    full_content: str
) -> Tuple[str, List[str]]:
    fallback_summary, fallback_checkpoints = (
        make_fallback_summary(
            title,
            full_content
        )
    )

    if category == CATEGORY_SMILEGATE:
        role = (
            "스마일게이트 외부 뉴스 브리핑 담당자"
        )

        checkpoint_instruction = (
            "스마일게이트 관점에서 확인할 "
            "사업·게임·대외 동향 두 가지"
        )

    else:
        role = (
            "대한민국 기업 HR·인사·노무 실무자"
        )

        checkpoint_instruction = (
            "기업 HR 담당자가 확인할 실무 사항 두 가지"
        )

    prompt = f"""
당신은 {role}입니다.

[카테고리]
{category}

[기사 제목]
{title}

[기사 내용]
{full_content[:4500]}

[작성 기준]
1. 기사에 실제로 있는 내용만 사용합니다.
2. 핵심 내용을 두 개의 불릿으로 요약합니다.
3. 추정이나 과장은 하지 않습니다.
4. checkpoints는 {checkpoint_instruction}를 작성합니다.
5. JSON만 출력합니다.

[JSON 형식]
{{
  "summary": "• 핵심 내용 1\\n• 핵심 내용 2",
  "checkpoints": [
    "확인사항 1",
    "확인사항 2"
  ]
}}
""".strip()

    data = call_gemini_json(
        prompt,
        temperature=0.2
    )

    if data is None:
        return (
            fallback_summary,
            fallback_checkpoints
        )

    summary = str(
        data.get(
            "summary",
            ""
        )
    ).strip()

    checkpoints = data.get(
        "checkpoints",
        []
    )

    if not isinstance(
        checkpoints,
        list
    ):
        checkpoints = []

    checkpoints = [
        str(item).strip()
        for item in checkpoints
        if str(item).strip()
    ][:2]

    if not summary:
        summary = fallback_summary

    if not checkpoints:
        checkpoints = fallback_checkpoints

    return (
        summary,
        checkpoints
    )


# ============================================================
# CSV 저장
# ============================================================

def load_previous_data() -> pd.DataFrame:
    if not CSV_FILE_PATH.exists():
        return pd.DataFrame(
            columns=CSV_COLUMNS
        )

    try:
        return pd.read_csv(
            CSV_FILE_PATH,
            encoding="utf-8-sig"
        )
    except Exception:
        return pd.DataFrame(
            columns=CSV_COLUMNS
        )


def save_articles(
    articles: List[Dict[str, Any]]
) -> None:
    data_frame = pd.DataFrame(
        articles
    )

    for column in CSV_COLUMNS:
        if column not in data_frame.columns:
            data_frame[column] = ""

    data_frame = data_frame[
        CSV_COLUMNS
    ]

    temp_path = CSV_FILE_PATH.with_suffix(
        ".tmp.csv"
    )

    data_frame.to_csv(
        temp_path,
        index=False,
        encoding="utf-8-sig"
    )

    temp_path.replace(
        CSV_FILE_PATH
    )


# ============================================================
# 전체 실행
# ============================================================

def run_collection() -> bool:
    if (
        not NAVER_CLIENT_ID
        or not NAVER_CLIENT_SECRET
    ):
        message = (
            "네이버 API 인증정보가 없습니다. "
            ".env 파일의 NAVER_CLIENT_ID와 "
            "NAVER_CLIENT_SECRET을 확인하세요."
        )

        print(
            f"❌ {message}"
        )

        write_status(
            False,
            message
        )

        return False

    if (
        not GEMINI_API_KEY
        or genai is None
        or types is None
    ):
        print(
            "⚠️ Gemini를 사용할 수 없습니다. "
            "검색어 기준 임시 분류로 실행됩니다."
        )

    now = datetime.datetime.now(
        KST
    )

    cutoff_date = (
        now
        - datetime.timedelta(
            days=COLLECTION_DAYS
        )
    )

    headers = {
        "X-Naver-Client-Id": (
            NAVER_CLIENT_ID
        ),
        "X-Naver-Client-Secret": (
            NAVER_CLIENT_SECRET
        )
    }

    print("=" * 72)
    print("🌐 HR 뉴스 수집 시작")
    print(
        f"📁 저장 위치: {CSV_FILE_PATH}"
    )
    print(
        f"🤖 Gemini 모델: {GEMINI_MODEL_NAME}"
    )
    print(
        f"🕒 기준 시간: "
        f"{now:%Y-%m-%d %H:%M:%S}"
    )
    print("=" * 72)

    # --------------------------------------------------------
    # 1. 후보 수집
    # --------------------------------------------------------

    raw_candidates, api_success_count = (
        collect_raw_candidates(
            headers,
            cutoff_date
        )
    )

    print(
        f"\n📋 전체 원시 후보: "
        f"{len(raw_candidates)}건"
    )

    # --------------------------------------------------------
    # 2. Gemini 일괄 분류
    # --------------------------------------------------------

    classified = classify_candidates_with_gemini(
        raw_candidates
    )

    print(
        f"🤖 Gemini 포함 판정: "
        f"{len(classified)}건"
    )

# --------------------------------------------------------
# 3. Gemini 2차 중복 검토
# --------------------------------------------------------

    duplicate_reviewed = (
        review_duplicates_with_gemini(
            classified
        )
    )

# --------------------------------------------------------
# 4. 동일 사건 및 재배포 제거
# --------------------------------------------------------


    deduplicated = (
        deduplicate_classified_articles(
            classified
        )
    )

    print(
        f"🔄 중복 제거 후: "
        f"{len(deduplicated)}건"
    )

    # --------------------------------------------------------
    # 4. 카테고리별 후보 선정
    # --------------------------------------------------------

    selected_by_category: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    for category in CATEGORY_ORDER:
        limit = (
            SMILEGATE_ARTICLE_LIMIT
            if category == CATEGORY_SMILEGATE
            else NORMAL_CATEGORY_ARTICLE_LIMIT
        )

        preselect_limit = limit * 2

        selected = select_category_candidates(
            deduplicated,
            category,
            preselect_limit
        )

        selected_by_category[
            category
        ] = selected

        print(
            f"🎯 [{category}] "
            f"{len(selected)}건 선정"
        )

    # --------------------------------------------------------
    # 5. 선택 기사 원문 추출 및 요약
    # --------------------------------------------------------

    final_articles = []

    for category in CATEGORY_ORDER:
        selected = selected_by_category.get(
            category,
            []
        )

        print(
            f"\n🧾 [{category}] 최종 처리"
        )

        for index, candidate in enumerate(
            selected,
            start=1
        ):
            title = candidate[
                "title"
            ]

            link = candidate[
                "link"
            ]

            description = candidate[
                "description"
            ]

            print(
                f"  📖 [{index}/{len(selected)}] "
                f"{title[:70]}"
            )

            original_title, full_content = (
                fetch_article_page(
                    link
                )
            )

            if (
                original_title
                and (
                    title.endswith("...")
                    or title.endswith("…")
                    or "..." in title[-8:]
                    or "…" in title[-8:]
                )
            ):
                title = original_title

            if len(full_content.strip()) < 80:
                full_content = (
                    description
                    or title
                )

            summary, checkpoints = (
                generate_article_summary(
                    category,
                    title,
                    full_content
                )
            )

            pub_dt = candidate[
                "pub_dt"
            ]

            final_articles.append({
                "category": category,
                "date_str": pub_dt.strftime(
                    "[%m/%d]"
                ),
                "title": title,
                "summary": summary,
                "checkpoints": json.dumps(
                    checkpoints,
                    ensure_ascii=False
                ),
                "link": link,
                "pubDate": candidate[
                    "pubDate"
                ],
                "collected_at": (
                    now.isoformat()
                )
            })

            print(
                "     ✅ 요약 완료"
            )

            if GEMINI_API_KEY:
                time.sleep(1)

    # --------------------------------------------------------
    # 6. 저장
    # --------------------------------------------------------

    if final_articles:
        save_articles(
            final_articles
        )

        message = (
            "뉴스 수집 완료: "
            f"총 {len(final_articles)}건 저장"
        )

        write_status(
            True,
            message,
            len(final_articles)
        )

        print(
            f"\n🎉 {message}"
        )

        return True

    if api_success_count == 0:
        previous_data = (
            load_previous_data()
        )

        message = (
            "네이버 API 호출이 모두 실패했습니다. "
            "기존 CSV는 보존했습니다."
        )

        write_status(
            False,
            message,
            len(previous_data)
        )

        print(
            f"\n❌ {message}"
        )

        return False

    save_articles([])

    message = (
        "API 호출은 성공했지만 "
        "Gemini 선별 기준에 맞는 기사가 없습니다."
    )

    write_status(
        True,
        message,
        0
    )

    print(
        f"\nℹ️ {message}"
    )

    return True


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    try:
        success = run_collection()

        raise SystemExit(
            0 if success else 1
        )

    except KeyboardInterrupt:
        message = (
            "사용자가 뉴스 수집을 중단했습니다."
        )

        write_status(
            False,
            message
        )

        print(
            f"\n⚠️ {message}"
        )

        raise SystemExit(130)

    except Exception as error:
        message = (
            "예상하지 못한 오류: "
            f"{error}"
        )

        write_status(
            False,
            message
        )

        print(
            f"\n❌ {message}"
        )

        raise
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
MAX_SEARCH_PAGES = 2
COLLECTION_DAYS = 2

SMILEGATE_ARTICLE_LIMIT = 5
NORMAL_CATEGORY_ARTICLE_LIMIT = 4

# Gemini 검증 전에 확보할 후보 수
SMILEGATE_PRESELECT_LIMIT = 12
NORMAL_PRESELECT_LIMIT = 10

# 제목·주제 중복 기준
TITLE_DUPLICATE_THRESHOLD = 0.58
SMILEGATE_TITLE_DUPLICATE_THRESHOLD = 0.48

TOPIC_DUPLICATE_THRESHOLD = 0.50
SMILEGATE_TOPIC_DUPLICATE_THRESHOLD = 0.45

# 본문 일부 중복 기준
CONTENT_DUPLICATE_THRESHOLD = 0.68

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
# 카테고리명
# 기존 기획 명칭 그대로 유지
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
# 검색어
# ============================================================

CATEGORY_KEYWORDS = {
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
        "기업 HR 전략",
        "기업 인사 전략",
        "기업 평가제도",
        "기업 성과관리",
        "기업 보상제도",
        "기업 HR 데이터",
        "기업 피플 애널리틱스",
        "기업 생성형AI HR",
        "기업 인재관리",
        "기업 리더십 조직개발",
        "기업 직원경험",
        "기업 HR 트렌드"
    ],

    CATEGORY_LAW: [
        "고용노동부 기업 정책",
        "기업 근로기준법 개정",
        "기업 노동법 개정",
        "기업 노동 판례",
        "기업 통상임금 판결",
        "기업 근로자성 판결",
        "기업 부당해고 판결",
        "기업 직장 내 괴롭힘 판례",
        "기업 근로시간 법 개정",
        "기업 육아휴직 법 개정",
        "기업 산업안전보건법",
        "기업 취업규칙 노동법"
    ],

    CATEGORY_LABOR: [
        "기업 노사관계",
        "기업 노동조합",
        "기업 임금협상",
        "기업 임단협",
        "기업 파업",
        "기업 성과급 갈등",
        "기업 보상제도 사례",
        "기업 인사평가 갈등",
        "기업 희망퇴직",
        "기업 구조조정",
        "기업 복리후생",
        "기업 스톡옵션 임직원"
    ],

    CATEGORY_RECRUIT: [
        "기업 채용전략",
        "기업 인재확보",
        "기업 신입 채용",
        "기업 경력직 채용",
        "기업 수시채용",
        "기업 공채",
        "기업 조직문화",
        "기업 온보딩",
        "기업 리텐션",
        "기업 유연근무제",
        "기업 재택근무",
        "기업 직원경험 조직문화"
    ]
}


# ============================================================
# 카테고리 핵심 키워드
# ============================================================

CATEGORY_CORE_KEYWORDS = {
    CATEGORY_HR_TREND: [
        "hr",
        "인사",
        "인사관리",
        "인사전략",
        "인적자원",
        "인재관리",
        "성과관리",
        "성과평가",
        "평가제도",
        "보상제도",
        "피플 애널리틱스",
        "인사 데이터",
        "조직개발",
        "직원경험",
        "직원 경험",
        "리더십",
        "인사담당자",
        "생성형 ai",
        "생성형ai"
    ],

    CATEGORY_LAW: [
        "고용노동부",
        "근로기준법",
        "노동법",
        "법 개정",
        "법률 개정",
        "시행령",
        "시행규칙",
        "판례",
        "판결",
        "대법원",
        "법원",
        "노동위원회",
        "중앙노동위원회",
        "행정해석",
        "근로감독",
        "통상임금",
        "근로자성",
        "부당해고",
        "최저임금",
        "임금체불",
        "산업안전보건법",
        "직장 내 괴롭힘",
        "직장내괴롭힘",
        "취업규칙",
        "근로시간"
    ],

    CATEGORY_LABOR: [
        "노사",
        "노조",
        "노동조합",
        "파업",
        "쟁의",
        "임단협",
        "임금협상",
        "단체협약",
        "노사협의",
        "성과급",
        "인센티브",
        "보상제도",
        "인사평가",
        "평가제도",
        "연봉협상",
        "임금 인상",
        "희망퇴직",
        "구조조정",
        "정리해고",
        "복리후생",
        "스톡옵션",
        "우리사주"
    ],

    CATEGORY_RECRUIT: [
        "채용",
        "공채",
        "수시채용",
        "경력직",
        "신입사원",
        "신입 채용",
        "인재확보",
        "인재 확보",
        "채용전략",
        "조직문화",
        "온보딩",
        "리텐션",
        "유연근무",
        "재택근무",
        "근무제도",
        "직원경험",
        "직원 경험",
        "퇴사율",
        "몰입도"
    ]
}


# ============================================================
# 기업 실무 맥락
# ============================================================

CORPORATE_CONTEXT_KEYWORDS = [
    "기업",
    "회사",
    "사업장",
    "법인",
    "사용자",
    "사측",
    "고용주",
    "경영진",
    "임직원",
    "직원",
    "근로자",
    "인사담당자",
    "인사팀",
    "hr담당자",
    "직장",
    "채용",
    "취업규칙",
    "인사제도",
    "평가제도",
    "보상제도",
    "성과관리",
    "근무제도",
    "노사협의",
    "임금협상",
    "임단협",
    "단체협약",
    "노동조합",
    "노조",
    "성과급",
    "복리후생",
    "희망퇴직",
    "구조조정"
]


# ============================================================
# 제외 키워드
# ============================================================

GENERAL_EXCLUDE_KEYWORDS = [
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
    "주민 대상",
    "군민 대상",
    "학생 대상",
    "청소년 교육",
    "학교 수업",
    "교사 연수",
    "창업 지원",
    "창업지원",
    "인공지능교육센터"
]

PUBLIC_ADMIN_EXCLUDE_KEYWORDS = [
    "인사발령",
    "인사 발령",
    "전보",
    "보직",
    "승진자",
    "공무원",
    "지방자치단체",
    "지자체",
    "도청",
    "시청",
    "군청",
    "구청",
    "교육청",
    "도의회",
    "시의회",
    "군의회",
    "구의회",
    "시장",
    "군수",
    "도지사",
    "교육감",
    "적극행정",
    "우수행정",
    "행정 우수사례",
    "공무원 포상",
    "여성재단",
    "문화재단",
    "복지재단"
]

LOCAL_GOVERNMENT_NAMES = [
    "서울시",
    "부산시",
    "대구시",
    "인천시",
    "광주시",
    "대전시",
    "울산시",
    "세종시",
    "경기도",
    "강원도",
    "충청북도",
    "충청남도",
    "전라북도",
    "전북특별자치도",
    "전라남도",
    "경상북도",
    "경상남도",
    "제주도",
    "제주특별자치도"
]

PUBLIC_ADMIN_TITLE_PATTERNS = [
    re.compile(r"(?:^|\s)[가-힣]{2,10}(시|군|구|도)\s"),
    re.compile(r"[가-힣]{2,10}(시장|군수|도지사|교육감)"),
    re.compile(r"(공무원|공직자).*(승진|전보|인사|발령)")
]


# ============================================================
# 홍보성 기사 필터
# ============================================================

VENDOR_PROMOTION_KEYWORDS = [
    "출시",
    "선보여",
    "론칭",
    "서비스 오픈",
    "솔루션 출시",
    "플랫폼 출시",
    "신제품",
    "무료 체험",
    "도입 문의",
    "고객사 모집",
    "프로모션",
    "기능 업데이트",
    "업무협약 체결",
    "mou 체결"
]

MAJOR_INNOVATION_KEYWORDS = [
    "세계 최초",
    "국내 최초",
    "업계 최초",
    "대규모 도입",
    "전사 도입",
    "산업 전반",
    "글로벌 표준",
    "패러다임 전환",
    "채용 전 과정 자동화",
    "인사 의사결정 자동화",
    "인사 운영 혁신",
    "생성형 ai 기반 인사",
    "생성형ai 기반 인사"
]

RECRUITMENT_EXCLUDE_KEYWORDS = [
    "상무 승진",
    "전무 승진",
    "부사장 승진",
    "회장 승진",
    "대표이사 선임",
    "상무 선임",
    "전무 선임",
    "정기 임원인사",
    "임원 인사",
    "인사 발령"
]


# ============================================================
# 법·노사 구분 키워드
# ============================================================

LEGAL_AUTHORITY_KEYWORDS = [
    "고용노동부",
    "근로기준법",
    "노동법",
    "법 개정",
    "법률 개정",
    "시행령",
    "시행규칙",
    "판결",
    "판례",
    "대법원",
    "법원",
    "노동위원회",
    "중앙노동위원회",
    "행정해석",
    "근로감독"
]

LABOR_CASE_KEYWORDS = [
    "노조",
    "노동조합",
    "사측",
    "파업",
    "쟁의",
    "임단협",
    "임금협상",
    "단체협약",
    "성과급 갈등",
    "인사평가 갈등",
    "희망퇴직",
    "구조조정",
    "복리후생",
    "스톡옵션"
]


# ============================================================
# 스마일게이트 Topic
# ============================================================

SMILEGATE_TOPIC_RULES = {
    "Game": [
        "게임",
        "로스트아크",
        "에픽세븐",
        "크로스파이어",
        "로드나인",
        "스토브",
        "e스포츠",
        "이스포츠",
        "업데이트",
        "시즌",
        "이벤트",
        "캐릭터",
        "콜라보"
    ],

    "Release": [
        "신작",
        "출시",
        "론칭",
        "사전예약",
        "공개",
        "얼리 액세스",
        "신규 타이틀"
    ],

    "Business": [
        "사업",
        "투자",
        "인수",
        "협업",
        "파트너십",
        "계약",
        "실적",
        "매출",
        "퍼블리싱",
        "지분"
    ],

    "Global": [
        "글로벌",
        "해외",
        "북미",
        "유럽",
        "일본",
        "중국",
        "대만",
        "동남아",
        "수출"
    ],

    "Technology": [
        "ai",
        "인공지능",
        "기술",
        "개발",
        "엔진",
        "플랫폼",
        "클라우드",
        "데이터",
        "연구개발",
        "r&d"
    ],

    "HR": [
        "채용",
        "인재",
        "직원",
        "임직원",
        "조직문화",
        "복지",
        "근무제도",
        "인사"
    ],

    "Management": [
        "경영",
        "대표",
        "인터뷰",
        "조직개편",
        "전략",
        "비전",
        "브랜드",
        "수상"
    ],

    "ESG_Social": [
        "esg",
        "사회공헌",
        "퓨처랩",
        "재단",
        "기부",
        "봉사",
        "청소년",
        "교육",
        "상생"
    ]
}


# ============================================================
# HTTP
# ============================================================

def create_http_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
        )
    })

    return session


HTTP_SESSION = create_http_session()


# ============================================================
# 공통 유틸리티
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
        "updated_at": datetime.datetime.now(KST).isoformat()
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


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", "", text)

    text = re.sub(
        (
            r"\[(단독|포토|기획|속보|인사|부음|국내|해외|"
            r"종합|영상|인터뷰|현장)\]"
        ),
        "",
        text
    )

    return re.sub(r"\s+", " ", text).strip()


def contains_any(
    target: str,
    keywords: List[str]
) -> bool:
    lowered = target.lower()

    return any(
        keyword.lower() in lowered
        for keyword in keywords
    )


def count_matches(
    target: str,
    keywords: List[str]
) -> int:
    lowered = target.lower()

    return sum(
        1
        for keyword in keywords
        if keyword.lower() in lowered
    )


def parse_pub_date(
    value: str
) -> Optional[datetime.datetime]:
    try:
        parsed = parsedate_to_datetime(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=KST)

        return parsed.astimezone(KST)

    except (
        TypeError,
        ValueError,
        OverflowError
    ):
        return None


def normalize_url(url: str) -> str:
    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())

        filtered_query = [
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

        clean_path = re.sub(
            r"/+$",
            "",
            parts.path
        )

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            clean_path,
            urlencode(filtered_query),
            ""
        ))

    except ValueError:
        return url.strip()


def normalize_title(title: str) -> str:
    text = clean_text(title).lower()
    text = re.sub(r"\[[^\]]+\]", " ", text)

    for word in [
        "단독",
        "속보",
        "종합",
        "포토",
        "영상",
        "기획",
        "인터뷰",
        "현장",
        "이슈",
        "분석"
    ]:
        text = text.replace(word, " ")

    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        text
    )


def normalize_topic_text(
    title: str,
    description: str
) -> str:
    text = f"{title} {description}".lower()

    for pattern in [
        r"\[.*?\]",
        r"\(.*?\)",
        r"단독",
        r"속보",
        r"종합",
        r"포토",
        r"영상",
        r"운영",
        r"실시",
        r"진행",
        r"개최",
        r"업무협약",
        r"협약 체결",
        r"mou",
        r"밝혔다",
        r"전했다"
    ]:
        text = re.sub(
            pattern,
            " ",
            text
        )

    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        text
    )


def make_ngrams(
    value: str,
    n: int
) -> Set[str]:
    if not value:
        return set()

    if len(value) < n:
        return {value}

    return {
        value[index:index + n]
        for index in range(
            len(value) - n + 1
        )
    }


def jaccard_similarity(
    value1: str,
    value2: str,
    n: int
) -> float:
    set1 = make_ngrams(value1, n)
    set2 = make_ngrams(value2, n)

    if not set1 or not set2:
        return 0.0

    return len(set1 & set2) / len(set1 | set2)


def title_similarity(
    title1: str,
    title2: str
) -> float:
    return jaccard_similarity(
        normalize_title(title1),
        normalize_title(title2),
        2
    )


def topic_similarity(
    article1: Dict[str, Any],
    article2: Dict[str, Any]
) -> float:
    text1 = normalize_topic_text(
        article1.get("title", ""),
        article1.get("description", "")
    )

    text2 = normalize_topic_text(
        article2.get("title", ""),
        article2.get("description", "")
    )

    return jaccard_similarity(
        text1,
        text2,
        3
    )


def content_similarity(
    content1: str,
    content2: str
) -> float:
    normalized1 = re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        content1.lower()
    )[:1600]

    normalized2 = re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        content2.lower()
    )[:1600]

    return jaccard_similarity(
        normalized1,
        normalized2,
        5
    )


# ============================================================
# 원문 제목·본문
# ============================================================

@lru_cache(maxsize=256)
def fetch_article_page(
    url: str
) -> Tuple[str, str]:
    """
    원문 제목과 본문을 한 번의 접속으로 가져옵니다.
    """

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

        title = ""

        for selector in [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]'
        ]:
            tag = soup.select_one(selector)

            if tag:
                title = clean_text(
                    tag.get("content", "")
                )

                if title:
                    break

        if (
            not title
            and soup.title
            and soup.title.string
        ):
            title = clean_text(
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
            for selector in [
                "article",
                ".article_body",
                "#articleBody",
                "#articeBody",
                "#newsCollapse",
                ".news_body",
                ".article-view-content-div",
                ".article_view",
                ".newsct_article"
            ]:
                target = soup.select_one(selector)

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

        return title, body

    except Exception:
        return "", ""


# ============================================================
# 스마일게이트 분류
# ============================================================

def calculate_smilegate_relevance(
    title: str,
    description: str
) -> int:
    title_lower = title.lower()
    description_lower = description.lower()
    target = f"{title_lower} {description_lower}"

    score = 0

    if "스마일게이트" in title_lower:
        score += 14

    title_position = title_lower.find(
        "스마일게이트"
    )

    if 0 <= title_position <= 15:
        score += 5

    score += min(
        description_lower.count(
            "스마일게이트"
        ) * 2,
        6
    )

    for rules in SMILEGATE_TOPIC_RULES.values():
        score += min(
            count_matches(target, rules),
            3
        )

    for pattern in [
        "스마일게이트 등",
        "스마일게이트 비롯",
        "넥슨·스마일게이트",
        "넥슨과 스마일게이트",
        "엔씨·스마일게이트",
        "넷마블·스마일게이트",
        "게임사들",
        "게임업계",
        "국내 게임사",
        "주요 게임사",
        "대형 게임사",
        "게임 3사",
        "게임 빅3"
    ]:
        if pattern in title_lower:
            score -= 8

    if (
        "스마일게이트" not in title_lower
        and description_lower.count(
            "스마일게이트"
        ) <= 1
    ):
        score -= 8

    return score


def classify_smilegate_topic(
    title: str,
    description: str
) -> str:
    target = f"{title} {description}".lower()

    scores = {
        topic: count_matches(
            target,
            keywords
        )
        for topic, keywords
        in SMILEGATE_TOPIC_RULES.items()
    }

    best_topic = max(
        scores,
        key=scores.get
    )

    if scores[best_topic] == 0:
        return "Management"

    return best_topic


def extract_game_identity(
    title: str,
    description: str
) -> str:
    target = f"{title} {description}".lower()

    known_games = [
        "로스트아크",
        "에픽세븐",
        "크로스파이어",
        "로드나인",
        "스토브",
        "카오스 제로 나이트메어"
    ]

    matched = [
        game
        for game in known_games
        if game in target
    ]

    return "|".join(
        matched
    )


# ============================================================
# 정부·홍보·카테고리 필터
# ============================================================

def is_public_admin_article(
    title: str,
    description: str
) -> bool:
    target = f"{title} {description}".lower()

    if contains_any(
        target,
        PUBLIC_ADMIN_EXCLUDE_KEYWORDS
    ):
        return True

    if contains_any(
        target,
        LOCAL_GOVERNMENT_NAMES
    ):
        return True

    return any(
        pattern.search(title)
        for pattern in PUBLIC_ADMIN_TITLE_PATTERNS
    )


def has_corporate_context(
    target: str
) -> bool:
    return contains_any(
        target,
        CORPORATE_CONTEXT_KEYWORDS
    )


def is_vendor_promotion(
    target: str
) -> bool:
    promotion = contains_any(
        target,
        VENDOR_PROMOTION_KEYWORDS
    )

    major_innovation = contains_any(
        target,
        MAJOR_INNOVATION_KEYWORDS
    )

    return (
        promotion
        and not major_innovation
    )


def category_score(
    category: str,
    title: str,
    description: str
) -> int:
    target = f"{title} {description}".lower()

    if contains_any(
        target,
        GENERAL_EXCLUDE_KEYWORDS
    ):
        return -100

    if category == CATEGORY_SMILEGATE:
        if "스마일게이트" not in target:
            return -100

        return calculate_smilegate_relevance(
            title,
            description
        )

    # 고용노동부의 법·정책 기사는 허용하되
    # 지자체 행정·인사발령은 차단합니다.
    if is_public_admin_article(
        title,
        description
    ):
        return -100

    if not has_corporate_context(target):
        return -100

    core_keywords = CATEGORY_CORE_KEYWORDS.get(
        category,
        []
    )

    core_count = count_matches(
        target,
        core_keywords
    )

    if core_count == 0:
        return -100

    score = core_count * 3

    if category == CATEGORY_HR_TREND:
        if is_vendor_promotion(target):
            return -100

        score += count_matches(
            target,
            [
                "인사담당자",
                "인사제도",
                "성과관리",
                "평가제도",
                "보상제도",
                "인재관리",
                "직원경험",
                "조직개발"
            ]
        ) * 2

    elif category == CATEGORY_LAW:
        legal_count = count_matches(
            target,
            LEGAL_AUTHORITY_KEYWORDS
        )

        if legal_count == 0:
            return -100

        score += legal_count * 4

        # 단순 기업 갈등 기사보다 법적 판단 기사를 우선
        if contains_any(
            target,
            [
                "판결",
                "판례",
                "대법원",
                "법 개정",
                "시행령",
                "행정해석"
            ]
        ):
            score += 5

    elif category == CATEGORY_LABOR:
        labor_count = count_matches(
            target,
            LABOR_CASE_KEYWORDS
        )

        if labor_count == 0:
            return -100

        score += labor_count * 4

        # 법 해설뿐이고 기업 사례가 없는 기사는 제외
        if (
            contains_any(
                target,
                LEGAL_AUTHORITY_KEYWORDS
            )
            and not contains_any(
                target,
                [
                    "회사",
                    "기업",
                    "사측",
                    "노조",
                    "노동조합",
                    "임직원"
                ]
            )
        ):
            return -100

    elif category == CATEGORY_RECRUIT:
        if contains_any(
            target,
            RECRUITMENT_EXCLUDE_KEYWORDS
        ):
            return -100

        if (
            "승진" in target
            and not contains_any(
                target,
                [
                    "승진제도",
                    "승진 제도",
                    "평가제도",
                    "인사제도"
                ]
            )
        ):
            return -100

        if (
            "선임" in target
            and not contains_any(
                target,
                [
                    "채용",
                    "조직개편",
                    "인사제도"
                ]
            )
        ):
            return -100

        score += count_matches(
            target,
            [
                "채용전략",
                "인재확보",
                "온보딩",
                "리텐션",
                "유연근무",
                "조직문화",
                "직원경험"
            ]
        ) * 3

    return score


# ============================================================
# 네이버 뉴스 검색
# ============================================================

def search_naver_news(
    keyword: str,
    headers: Dict[str, str],
    start: int
) -> Tuple[bool, List[Dict[str, Any]]]:
    query = urllib.parse.quote(keyword)

    url = (
        "https://openapi.naver.com/v1/search/news.json"
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

    return (
        True,
        items if isinstance(items, list) else []
    )


# ============================================================
# 후보 중복 검사
# ============================================================

def find_duplicate(
    candidate: Dict[str, Any],
    existing: List[Dict[str, Any]],
    title_threshold: float,
    topic_threshold: float,
    check_content: bool = False
) -> Optional[Dict[str, Any]]:
    candidate_url = candidate.get(
        "normalized_url",
        ""
    )

    candidate_title = candidate.get(
        "normalized_title",
        ""
    )

    for other in existing:
        if (
            candidate_url
            and candidate_url
            == other.get("normalized_url", "")
        ):
            return other

        if (
            candidate_title
            and candidate_title
            == other.get("normalized_title", "")
        ):
            return other

        if title_similarity(
            candidate.get("title", ""),
            other.get("title", "")
        ) >= title_threshold:
            return other

        if topic_similarity(
            candidate,
            other
        ) >= topic_threshold:
            return other

        if check_content:
            content1 = candidate.get(
                "content_preview",
                ""
            )

            content2 = other.get(
                "content_preview",
                ""
            )

            if (
                content1
                and content2
                and content_similarity(
                    content1,
                    content2
                ) >= CONTENT_DUPLICATE_THRESHOLD
            ):
                return other

    return None


# ============================================================
# 카테고리 후보 수집
# ============================================================

def collect_category_candidates(
    category: str,
    keywords: List[str],
    headers: Dict[str, str],
    cutoff_date: datetime.datetime
) -> Tuple[List[Dict[str, Any]], int]:
    candidates: List[Dict[str, Any]] = []
    successful_api_calls = 0

    for query_index, keyword in enumerate(keywords):
        print(
            f"  🔍 검색어: {keyword}"
        )

        accepted_for_query = 0

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
                    item.get("pubDate", "")
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
                    item.get("title", "")
                )

                description = clean_text(
                    item.get("description", "")
                )

                link = (
                    item.get("originallink")
                    or item.get("link")
                    or ""
                ).strip()

                if not title:
                    continue

                # 잘린 제목만 원문에서 보완
                if (
                    title.endswith("...")
                    or title.endswith("…")
                    or "..." in title[-8:]
                    or "…" in title[-8:]
                ):
                    original_title, _ = fetch_article_page(
                        link
                    )

                    if original_title:
                        title = original_title

                score = category_score(
                    category,
                    title,
                    description
                )

                if score < 0:
                    continue

                candidate = {
                    "category": category,
                    "keyword": keyword,
                    "query_index": query_index,
                    "title": title,
                    "description": description,
                    "link": link,
                    "normalized_url": normalize_url(link),
                    "normalized_title": normalize_title(title),
                    "pubDate": pub_date_raw,
                    "pub_dt": pub_dt,
                    "category_score": score,
                    "topic_group": "",
                    "game_identity": "",
                    "content_preview": ""
                }

                if category == CATEGORY_SMILEGATE:
                    candidate["topic_group"] = (
                        classify_smilegate_topic(
                            title,
                            description
                        )
                    )

                    candidate["game_identity"] = (
                        extract_game_identity(
                            title,
                            description
                        )
                    )

                    title_threshold = (
                        SMILEGATE_TITLE_DUPLICATE_THRESHOLD
                    )

                    topic_threshold = (
                        SMILEGATE_TOPIC_DUPLICATE_THRESHOLD
                    )

                else:
                    candidate["topic_group"] = keyword
                    title_threshold = TITLE_DUPLICATE_THRESHOLD
                    topic_threshold = TOPIC_DUPLICATE_THRESHOLD

                duplicate = find_duplicate(
                    candidate,
                    candidates,
                    title_threshold,
                    topic_threshold
                )

                if duplicate:
                    # 같은 기사가 더 적합한 검색어에서 발견된 경우 교체
                    if (
                        candidate["category_score"]
                        > duplicate["category_score"]
                    ):
                        candidates.remove(
                            duplicate
                        )
                        candidates.append(
                            candidate
                        )
                    continue

                candidates.append(candidate)
                accepted_for_query += 1

            # 첫 페이지에서 충분한 후보가 확보되면
            # 불필요한 추가 페이지 호출을 하지 않습니다.
            if accepted_for_query >= 4:
                break

        print(
            f"    └ 후보 {accepted_for_query}건 확보"
        )

    candidates.sort(
        key=lambda article: (
            article["category_score"],
            article["pub_dt"]
        ),
        reverse=True
    )

    preselect_limit = (
        SMILEGATE_PRESELECT_LIMIT
        if category == CATEGORY_SMILEGATE
        else NORMAL_PRESELECT_LIMIT
    )

    # 원문을 너무 많이 접속하지 않도록
    # 상위 후보에만 본문 일부를 추가합니다.
    enriched = []

    for candidate in candidates[
        :preselect_limit
    ]:
        original_title, body = fetch_article_page(
            candidate["link"]
        )

        if (
            original_title
            and (
                candidate["title"].endswith("...")
                or candidate["title"].endswith("…")
            )
        ):
            candidate["title"] = original_title
            candidate["normalized_title"] = (
                normalize_title(original_title)
            )

        candidate["content_preview"] = (
            body[:1800]
            if body
            else candidate["description"][:1800]
        )

        duplicate = find_duplicate(
            candidate,
            enriched,
            (
                SMILEGATE_TITLE_DUPLICATE_THRESHOLD
                if category == CATEGORY_SMILEGATE
                else TITLE_DUPLICATE_THRESHOLD
            ),
            (
                SMILEGATE_TOPIC_DUPLICATE_THRESHOLD
                if category == CATEGORY_SMILEGATE
                else TOPIC_DUPLICATE_THRESHOLD
            ),
            check_content=True
        )

        if duplicate:
            continue

        enriched.append(candidate)

    return enriched, successful_api_calls


# ============================================================
# 카테고리 간 중복 제거
# ============================================================

def resolve_cross_category_duplicates(
    category_candidates: Dict[
        str,
        List[Dict[str, Any]]
    ]
) -> Dict[str, List[Dict[str, Any]]]:
    all_candidates: List[
        Dict[str, Any]
    ] = []

    for category in CATEGORY_ORDER:
        all_candidates.extend(
            category_candidates.get(
                category,
                []
            )
        )

    all_candidates.sort(
        key=lambda article: (
            article["category_score"],
            article["pub_dt"]
        ),
        reverse=True
    )

    accepted: List[
        Dict[str, Any]
    ] = []

    for candidate in all_candidates:
        duplicate = find_duplicate(
            candidate,
            accepted,
            TITLE_DUPLICATE_THRESHOLD,
            TOPIC_DUPLICATE_THRESHOLD,
            check_content=True
        )

        if duplicate:
            # 동일 기사가 두 카테고리에 들어갔다면
            # 점수가 높은 카테고리만 유지합니다.
            if (
                candidate["category_score"]
                > duplicate["category_score"]
            ):
                accepted.remove(duplicate)
                accepted.append(candidate)

            continue

        accepted.append(candidate)

    result = {
        category: []
        for category in CATEGORY_ORDER
    }

    for candidate in accepted:
        result[
            candidate["category"]
        ].append(candidate)

    for category in CATEGORY_ORDER:
        result[category].sort(
            key=lambda article: (
                article["category_score"],
                article["pub_dt"]
            ),
            reverse=True
        )

    return result


# ============================================================
# 다양성 기반 후보 순서
# ============================================================

def order_smilegate_candidates(
    candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    selected: List[
        Dict[str, Any]
    ] = []

    used_topics: Set[str] = set()
    used_games: Set[str] = set()

    # 1차: Topic당 1건
    for candidate in candidates:
        topic = candidate.get(
            "topic_group",
            "Management"
        )

        game = candidate.get(
            "game_identity",
            ""
        )

        if topic in used_topics:
            continue

        if (
            game
            and game in used_games
        ):
            continue

        selected.append(candidate)
        used_topics.add(topic)

        if game:
            used_games.add(game)

    # 2차: Topic이 부족해도 동일 게임·동일 사건은 제외
    for candidate in candidates:
        if candidate in selected:
            continue

        game = candidate.get(
            "game_identity",
            ""
        )

        if (
            game
            and game in used_games
        ):
            continue

        if find_duplicate(
            candidate,
            selected,
            SMILEGATE_TITLE_DUPLICATE_THRESHOLD,
            SMILEGATE_TOPIC_DUPLICATE_THRESHOLD,
            check_content=True
        ):
            continue

        selected.append(candidate)

        if game:
            used_games.add(game)

    return selected


def order_normal_candidates(
    candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    selected: List[
        Dict[str, Any]
    ] = []

    used_queries: Set[str] = set()

    # 검색어별 대표 기사 우선
    for candidate in candidates:
        keyword = candidate["keyword"]

        if keyword in used_queries:
            continue

        if find_duplicate(
            candidate,
            selected,
            TITLE_DUPLICATE_THRESHOLD,
            TOPIC_DUPLICATE_THRESHOLD,
            check_content=True
        ):
            continue

        selected.append(candidate)
        used_queries.add(keyword)

    # 부족하면 남은 고품질 후보로 보충
    for candidate in candidates:
        if candidate in selected:
            continue

        if find_duplicate(
            candidate,
            selected,
            TITLE_DUPLICATE_THRESHOLD,
            TOPIC_DUPLICATE_THRESHOLD,
            check_content=True
        ):
            continue

        selected.append(candidate)

    return selected


# ============================================================
# Gemini
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
        else "기사 원문에서 세부 적용 대상과 영향을 확인해야 합니다."
    )

    return (
        f"• {first}\n• {second}",
        [
            "원문 기사 내용 확인",
            "사내 제도 및 업무 관련성 검토"
        ]
    )


def extract_gemini_text(
    response: Any
) -> str:
    text_parts: List[str] = []

    for candidate in (
        getattr(
            response,
            "candidates",
            None
        )
        or []
    ):
        content = getattr(
            candidate,
            "content",
            None
        )

        if content is None:
            continue

        for part in (
            getattr(
                content,
                "parts",
                None
            )
            or []
        ):
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
        return "\n".join(text_parts)

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

    start = text.find("{")

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

    if not isinstance(data, dict):
        raise ValueError(
            "Gemini 응답이 JSON 객체가 아닙니다."
        )

    return data


def generate_llm_insights(
    category: str,
    title: str,
    full_content: str
) -> Tuple[bool, str, List[str], str]:
    fallback_summary, fallback_checkpoints = (
        make_fallback_summary(
            title,
            full_content
        )
    )

    # Gemini를 사용할 수 없으면 기존 규칙 필터 결과를 신뢰하고 저장
    if (
        not GEMINI_API_KEY
        or genai is None
        or types is None
    ):
        return (
            True,
            fallback_summary,
            fallback_checkpoints,
            "Gemini 미사용"
        )

    if category == CATEGORY_SMILEGATE:
        relevance_instruction = (
            "이 기사가 스마일게이트 자체의 게임, 서비스, 사업, "
            "투자, 글로벌, 기술, 인사, 경영 또는 사회공헌 소식인지 판단하세요. "
            "타 회사나 게임업계 전체 기사에서 스마일게이트가 단순 언급된 경우 false입니다."
        )

        checkpoint_instruction = (
            "스마일게이트 관점에서 확인할 대외 동향 또는 업무 확인사항 두 가지"
        )

    else:
        relevance_instruction = (
            "이 기사가 대한민국 기업의 HR·인사·노무 담당자가 "
            "실무적으로 참고할 가치가 있는지 판단하세요. "
            "학교 교육, 지자체 행정, 공무원 인사발령, 일반 제품 홍보, "
            "단순 임원 승진, 개인 사건이면 false입니다."
        )

        checkpoint_instruction = (
            "기업 HR·인사·노무 담당자가 실무에서 확인할 사항 두 가지"
        )

    prompt = f"""
당신은 대한민국 기업의 HR·인사·노무 뉴스 편집자입니다.

[검증 기준]
{relevance_instruction}

[카테고리]
{category}

[기사 제목]
{title}

[기사 내용]
{full_content[:4500]}

[작성 지침]
1. practical_relevance는 위 검증 기준에 따라 true 또는 false로 작성합니다.
2. practical_relevance가 false이면 summary와 checkpoints는 비워도 됩니다.
3. true이면 기사 내용만 근거로 핵심 내용을 불릿 두 개로 요약합니다.
4. 기사에 없는 사실을 추정하지 않습니다.
5. checkpoints는 {checkpoint_instruction}를 작성합니다.
6. 응답은 JSON 객체만 출력합니다.

[JSON 형식]
{{
  "practical_relevance": true,
  "reason": "판단 이유",
  "summary": "• 핵심 내용 1\\n• 핵심 내용 2",
  "checkpoints": [
    "확인사항 1",
    "확인사항 2"
  ]
}}
""".strip()

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception as error:
        print(
            f"   └ Gemini 클라이언트 생성 실패: {error}"
        )

        return (
            True,
            fallback_summary,
            fallback_checkpoints,
            "클라이언트 생성 실패"
        )

    max_attempts = 4

    for attempt in range(max_attempts):
        attempt_number = attempt + 1

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type=(
                        "application/json"
                    ),
                    temperature=0.1
                )
            )

            response_text = extract_gemini_text(
                response
            )

            if not response_text.strip():
                raise ValueError(
                    "Gemini 응답 내용이 비어 있습니다."
                )

            data = parse_gemini_json(
                response_text
            )

            relevant = bool(
                data.get(
                    "practical_relevance",
                    True
                )
            )

            reason = str(
                data.get(
                    "reason",
                    ""
                )
            ).strip()

            if not relevant:
                return (
                    False,
                    "",
                    [],
                    reason
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
                checkpoints = (
                    fallback_checkpoints
                )

            return (
                True,
                summary,
                checkpoints,
                reason
            )

        except Exception as error:
            error_message = str(error)

            print(
                "   └ Gemini 호출 실패 "
                f"({attempt_number}/{max_attempts}): "
                f"{error_message}"
            )

            is_last_attempt = (
                attempt_number >= max_attempts
            )

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "high demand"
                in error_message.lower()
            ):
                if is_last_attempt:
                    break

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
                if is_last_attempt:
                    break

                wait_seconds = (
                    10 * (2 ** attempt)
                )

            elif (
                "404" in error_message
                or "NOT_FOUND" in error_message
            ):
                break

            else:
                if is_last_attempt:
                    break

                wait_seconds = 3

            print(
                f"   ⏳ {wait_seconds}초 후 재시도합니다."
            )

            time.sleep(wait_seconds)

    # Gemini 장애가 기사를 전부 없애지 않도록
    # 규칙 필터를 통과한 기사는 기본 요약으로 유지합니다.
    return (
        True,
        fallback_summary,
        fallback_checkpoints,
        "Gemini 최종 실패"
    )


# ============================================================
# CSV
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
    data_frame = pd.DataFrame(articles)

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
# 최종 처리
# ============================================================

def process_category(
    category: str,
    ordered_candidates: List[Dict[str, Any]],
    limit: int,
    now: datetime.datetime,
    globally_accepted: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    completed: List[
        Dict[str, Any]
    ] = []

    for candidate in ordered_candidates:
        if len(completed) >= limit:
            break

        # 최종 단계에서 카테고리 간 중복을 다시 검사
        if find_duplicate(
            candidate,
            globally_accepted,
            TITLE_DUPLICATE_THRESHOLD,
            TOPIC_DUPLICATE_THRESHOLD,
            check_content=True
        ):
            continue

        title = candidate["title"]
        description = candidate["description"]
        link = candidate["link"]

        print(
            f"\n  📖 기사 분석: {title[:70]}"
        )

        if category == CATEGORY_SMILEGATE:
            print(
                "     Topic: "
                f"{candidate.get('topic_group', 'Management')}"
            )

        full_content = candidate.get(
            "content_preview",
            ""
        )

        if len(full_content) < 100:
            _, fetched_body = fetch_article_page(
                link
            )

            full_content = (
                fetched_body
                or description
                or title
            )

        relevant, summary, checkpoints, reason = (
            generate_llm_insights(
                category,
                title,
                full_content
            )
        )

        if not relevant:
            print(
                "     🚫 Gemini 실무 가치 검증 제외: "
                f"{reason}"
            )
            continue

        pub_dt = candidate["pub_dt"]

        article = {
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
            "pubDate": candidate["pubDate"],
            "collected_at": now.isoformat()
        }

        completed.append(article)
        globally_accepted.append(candidate)

        print(
            "     ✅ 최종 선정"
        )

        if GEMINI_API_KEY:
            time.sleep(1)

    return completed


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

    now = datetime.datetime.now(KST)

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
    print(f"📁 저장 위치: {CSV_FILE_PATH}")
    print(f"🤖 Gemini 모델: {GEMINI_MODEL_NAME}")
    print(
        f"🕒 기준 시간: "
        f"{now:%Y-%m-%d %H:%M:%S}"
    )
    print("=" * 72)

    category_candidates: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    api_success_count = 0

    # 1. 모든 카테고리 후보를 먼저 수집
    for category in CATEGORY_ORDER:
        print(
            f"\n📂 [{category}]"
        )

        candidates, success_count = (
            collect_category_candidates(
                category,
                CATEGORY_KEYWORDS[category],
                headers,
                cutoff_date
            )
        )

        category_candidates[
            category
        ] = candidates

        api_success_count += success_count

        print(
            f"  📋 1차 후보 {len(candidates)}건"
        )

    # 2. 카테고리 간 중복 제거
    category_candidates = (
        resolve_cross_category_duplicates(
            category_candidates
        )
    )

    # 3. 다양성 기준 후보 순서 구성
    ordered_candidates: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    for category in CATEGORY_ORDER:
        candidates = category_candidates.get(
            category,
            []
        )

        if category == CATEGORY_SMILEGATE:
            ordered = order_smilegate_candidates(
                candidates
            )
        else:
            ordered = order_normal_candidates(
                candidates
            )

        ordered_candidates[
            category
        ] = ordered

        print(
            f"  🎯 [{category}] "
            f"중복·다양성 처리 후 {len(ordered)}건"
        )

    # 4. Gemini 검증 및 최종 선정
    final_articles: List[
        Dict[str, Any]
    ] = []

    globally_accepted: List[
        Dict[str, Any]
    ] = []

    for category in CATEGORY_ORDER:
        limit = (
            SMILEGATE_ARTICLE_LIMIT
            if category == CATEGORY_SMILEGATE
            else NORMAL_CATEGORY_ARTICLE_LIMIT
        )

        print(
            f"\n🧾 [{category}] 최종 처리"
        )

        completed = process_category(
            category,
            ordered_candidates.get(
                category,
                []
            ),
            limit,
            now,
            globally_accepted
        )

        final_articles.extend(
            completed
        )

        print(
            f"  ✅ 최종 {len(completed)}건 완료"
        )

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
        previous_data = load_previous_data()

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
        "API 호출은 성공했지만 최근 "
        f"{COLLECTION_DAYS}일 내 조건에 맞는 "
        "기사가 없습니다."
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
            f"예상하지 못한 오류: {error}"
        )

        write_status(
            False,
            message
        )

        print(
            f"\n❌ {message}"
        )

        raise
from __future__ import annotations
import re
import unicodedata
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("＋", "+").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text

DISEASES = [
    {
        "canonical": "NSCLC", "code": "C34-NSCLC", "demo_supported": True,
        "aliases": [
            "非小细胞肺癌", "非小细胞性肺癌", "肺腺癌", "肺鳞癌",
            "nsclc", "non-small cell lung cancer", "non small cell lung cancer",
            "lung adenocarcinoma", "lung squamous cell carcinoma",
        ],
    },
    {
        "canonical": "SCLC", "code": "C34-SCLC", "demo_supported": False,
        "aliases": ["小细胞肺癌", "sclc", "small cell lung cancer"],
    },
    {
        "canonical": "BREAST_CANCER", "code": "C50-BREAST", "demo_supported": True,
        "aliases": [
            "乳腺癌", "乳癌", "breast cancer", "breast carcinoma",
            "mammary carcinoma",
        ],
    },
    {
        "canonical": "COLORECTAL_CANCER", "code": "C18-CRC", "demo_supported": True,
        "aliases": [
            "结直肠癌", "结肠癌", "直肠癌", "大肠癌",
            "crc", "colorectal cancer", "colon cancer", "rectal cancer",
        ],
    },
    {
        "canonical": "T2DM", "code": "E11-T2DM", "demo_supported": True,
        "aliases": [
            "2型糖尿病", "二型糖尿病", "成人糖尿病", "糖尿病",
            "t2dm", "type 2 diabetes", "type ii diabetes",
            "type 2 diabetes mellitus",
        ],
    },
    {
        "canonical": "HYPERTENSION", "code": "I10-HTN", "demo_supported": True,
        "aliases": [
            "高血压", "原发性高血压", "高血压病",
            "hypertension", "essential hypertension", "high blood pressure",
        ],
    },
    {
        "canonical": "GASTRIC_CANCER", "code": "C16-GC", "demo_supported": False,
        "aliases": ["胃癌", "胃腺癌", "gastric cancer", "stomach cancer", "gastric adenocarcinoma"],
    },
    {
        "canonical": "HCC", "code": "C22-HCC", "demo_supported": False,
        "aliases": ["肝癌", "肝细胞癌", "hcc", "hepatocellular carcinoma", "liver cancer"],
    },
    {
        "canonical": "PANCREATIC_CANCER", "code": "C25-PC", "demo_supported": False,
        "aliases": ["胰腺癌", "pancreatic cancer", "pancreatic carcinoma"],
    },
    {
        "canonical": "PROSTATE_CANCER", "code": "C61-PCa", "demo_supported": False,
        "aliases": ["前列腺癌", "prostate cancer", "prostatic carcinoma"],
    },
    {
        "canonical": "OVARIAN_CANCER", "code": "C56-OC", "demo_supported": False,
        "aliases": ["卵巢癌", "ovarian cancer", "ovarian carcinoma"],
    },
    {
        "canonical": "CERVICAL_CANCER", "code": "C53-CC", "demo_supported": False,
        "aliases": ["宫颈癌", "子宫颈癌", "cervical cancer"],
    },
    {
        "canonical": "CKD", "code": "N18-CKD", "demo_supported": False,
        "aliases": ["慢性肾病", "慢性肾脏病", "ckd", "chronic kidney disease"],
    },
    {
        "canonical": "CAD", "code": "I25-CAD", "demo_supported": False,
        "aliases": ["冠心病", "冠状动脉粥样硬化性心脏病", "cad", "coronary artery disease"],
    },
    {
        "canonical": "HEART_FAILURE", "code": "I50-HF", "demo_supported": False,
        "aliases": ["心力衰竭", "心衰", "heart failure", "hf"],
    },
    {
        "canonical": "COPD", "code": "J44-COPD", "demo_supported": False,
        "aliases": ["慢阻肺", "慢性阻塞性肺疾病", "copd", "chronic obstructive pulmonary disease"],
    },
]

MOLECULAR = [
    {
        "concept": "EGFR_MUT", "gene": "EGFR", "result": "MUT",
        "aliases": [
            "egfr突变", "egfr阳性", "egfr+", "egfr mutant", "egfr-mutant",
            "egfr mutation", "egfr mutations", "egfr positive",
            "egfr-mutated",
        ],
    },
    {
        "concept": "HER2_POS", "gene": "HER2", "result": "POS",
        "aliases": [
            "her2阳性", "her2+", "her2 positive", "her2-positive",
            "her2 overexpression", "her2过表达",
        ],
    },
    {
        "concept": "KRAS_MUT", "gene": "KRAS", "result": "MUT",
        "aliases": [
            "kras突变", "kras+", "kras mutant", "kras-mutant",
            "kras mutation", "kras mutations", "kras positive",
        ],
    },
    {
        "concept": "ALK_POS", "gene": "ALK", "result": "POS",
        "aliases": ["alk阳性", "alk融合", "alk+", "alk positive", "alk rearrangement", "alk fusion"],
    },
    {
        "concept": "PDL1_POS", "gene": "PD-L1", "result": "POS",
        "aliases": ["pd-l1阳性", "pdl1阳性", "pd-l1 positive", "pdl1 positive", "pd-l1+"],
    },
    {
        "concept": "BRAF_MUT", "gene": "BRAF", "result": "MUT",
        "aliases": ["braf突变", "braf mutation", "braf mutant", "braf-mutant"],
    },
]

def _contains_alias(text: str, alias: str) -> bool:
    t = normalize_text(text)
    a = normalize_text(alias)
    if not a:
        return False
    return a in t

def _best_fuzzy_match(text: str, items: list[dict], threshold: float = 0.87):
    """
    Lightweight fallback for small typos / spacing differences.
    Exact alias containment always takes priority.
    """
    t = normalize_text(text)
    words = re.findall(r"[a-z0-9+\-]+|[\u4e00-\u9fff]+", t)
    candidates = [t] + words

    best = None
    best_score = 0.0
    for item in items:
        for alias in item.get("aliases", []):
            a = normalize_text(alias)
            for cand in candidates:
                score = SequenceMatcher(None, cand, a).ratio()
                if score > best_score:
                    best_score = score
                    best = item
    return best if best_score >= threshold else None

def resolve_disease(text: str):
    for item in DISEASES:
        for alias in item["aliases"]:
            if _contains_alias(text, alias):
                return item
    return _best_fuzzy_match(text, DISEASES)

def resolve_molecular(text: str):
    for item in MOLECULAR:
        for alias in item["aliases"]:
            if _contains_alias(text, alias):
                return item
    return _best_fuzzy_match(text, MOLECULAR, threshold=0.90)

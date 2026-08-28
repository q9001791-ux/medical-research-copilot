DISEASES = [
    {"canonical":"NSCLC","code":"C34-NSCLC","synonyms":["非小细胞肺癌","NSCLC","non-small cell lung cancer","non small cell lung cancer"]},
    {"canonical":"BREAST_CANCER","code":"C50-BREAST","synonyms":["乳腺癌","breast cancer"]},
    {"canonical":"COLORECTAL_CANCER","code":"C18-CRC","synonyms":["结直肠癌","结肠癌","colorectal cancer","colon cancer"]},
    {"canonical":"T2DM","code":"E11-T2DM","synonyms":["2型糖尿病","二型糖尿病","T2DM","type 2 diabetes","type 2 diabetes mellitus"]},
    {"canonical":"HYPERTENSION","code":"I10-HTN","synonyms":["高血压","hypertension"]},
]
MOLECULAR = [
    {"gene":"EGFR","result":"MUT","synonyms":["EGFR突变","EGFR mutation","EGFR mutations","EGFR-mutant","EGFR+"]},
    {"gene":"HER2","result":"POS","synonyms":["HER2阳性","HER2 positive","HER2-positive","HER2+"]},
    {"gene":"KRAS","result":"MUT","synonyms":["KRAS突变","KRAS mutation","KRAS mutations","KRAS-mutant","KRAS+"]},
]

def _match(text, items):
    low = text.lower()
    for item in items:
        if any(s.lower() in low for s in item["synonyms"]):
            return item
    return None

def resolve_disease(text):
    return _match(text, DISEASES)

def resolve_molecular(text):
    return _match(text, MOLECULAR)

from __future__ import annotations

import base64
import html
import io
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm
from sqlalchemy import text
from db import get_engine


METHODS = {
    "auto": {"zh": "自动选择", "en": "Auto select"},
    "descriptive": {"zh": "描述性统计", "en": "Descriptive statistics"},
    "t_test": {"zh": "独立样本 t 检验", "en": "Independent t-test"},
    "paired_t": {"zh": "配对 t 检验", "en": "Paired t-test"},
    "mann_whitney": {"zh": "Mann–Whitney U 检验", "en": "Mann–Whitney U"},
    "wilcoxon": {"zh": "Wilcoxon 配对秩和检验", "en": "Wilcoxon signed-rank"},
    "anova": {"zh": "单因素方差分析 ANOVA", "en": "One-way ANOVA"},
    "kruskal": {"zh": "Kruskal–Wallis 检验", "en": "Kruskal–Wallis"},
    "chi_square": {"zh": "卡方检验", "en": "Chi-square test"},
    "fisher": {"zh": "Fisher 精确检验", "en": "Fisher's exact test"},
    "pearson": {"zh": "Pearson 相关分析", "en": "Pearson correlation"},
    "spearman": {"zh": "Spearman 相关分析", "en": "Spearman correlation"},
    "linear_regression": {"zh": "线性回归", "en": "Linear regression"},
    "logistic_regression": {"zh": "Logistic 回归", "en": "Logistic regression"},
    "survival": {"zh": "Kaplan–Meier + Log-rank", "en": "Kaplan–Meier + Log-rank"},
    "cox": {"zh": "Cox 比例风险回归", "en": "Cox proportional hazards"},
}


def method_label(method: str, lang: str = "zh") -> str:
    return METHODS.get(method, {"zh": method, "en": method}).get(lang, method)


def _image(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _read_csv_bytes(data: bytes) -> pd.DataFrame:
    last_error = None
    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"CSV读取失败 / Failed to read CSV: {last_error}")


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cols = []
    seen = {}
    for raw in out.columns:
        name = str(raw).strip()
        if not name:
            name = "unnamed"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        cols.append(name)
    out.columns = cols
    out = out.replace(r"^\s*$", np.nan, regex=True)
    return out


def _coerce_numeric_like(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            continue
        s = out[col]
        non_null = s.dropna()
        if non_null.empty:
            continue
        converted = pd.to_numeric(
            non_null.astype(str).str.replace("%", "", regex=False),
            errors="coerce",
        )
        if converted.notna().mean() >= 0.92:
            full = pd.to_numeric(
                s.astype(str).str.replace("%", "", regex=False),
                errors="coerce",
            )
            out[col] = full
    return out


def _extract_delimited_block(text: str) -> str | None:
    """
    Find an embedded CSV/TSV-style table in a free-form research question.
    Supports fenced blocks first, then consecutive delimited lines.
    """
    if not text:
        return None

    fenced = re.findall(r"```(?:csv|tsv|text)?\s*(.*?)```", text, flags=re.I | re.S)
    for block in fenced:
        lines = [x for x in block.strip().splitlines() if x.strip()]
        if len(lines) >= 2 and any(d in lines[0] for d in [",", "\t", ";"]):
            return "\n".join(lines)

    lines = [x.rstrip() for x in text.splitlines()]
    runs = []
    current = []
    for line in lines:
        if line.strip() and any(d in line for d in [",", "\t", ";"]):
            current.append(line)
        else:
            if len(current) >= 2:
                runs.append(current)
            current = []
    if len(current) >= 2:
        runs.append(current)

    if not runs:
        return None
    return "\n".join(max(runs, key=len))


def _parse_delimited_text(text: str) -> pd.DataFrame:
    raw = text.strip()
    if not raw:
        raise ValueError("没有可解析的数据 / No pasted data found.")

    first = raw.splitlines()[0]
    if "\t" in first:
        sep = "\t"
    elif "," in first:
        sep = ","
    elif ";" in first:
        sep = ";"
    else:
        raise ValueError("请使用 CSV/TSV 格式粘贴数据。")

    return pd.read_csv(io.StringIO(raw), sep=sep)


def _numeric_cols(df):
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _categorical_cols(df):
    result = []
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            result.append(c)
        else:
            n = df[c].nunique(dropna=True)
            if 1 < n <= 10:
                result.append(c)
    return result


def _match_columns_in_question(question: str, columns: list[str]) -> list[str]:
    q = (question or "").lower()
    matches = []
    for col in sorted(columns, key=len, reverse=True):
        if str(col).lower() in q:
            matches.append(col)
    return matches


def _km_curve(times, events):
    times = np.asarray(times, dtype=float)
    events = np.asarray(events, dtype=int)
    order = np.argsort(times)
    times = times[order]
    events = events[order]

    event_times = np.sort(np.unique(times[events == 1]))
    xs, ys = [0.0], [1.0]
    surv = 1.0
    for t in event_times:
        at_risk = np.sum(times >= t)
        deaths = np.sum((times == t) & (events == 1))
        if at_risk > 0:
            surv *= 1 - deaths / at_risk
        xs.extend([float(t), float(t)])
        ys.extend([ys[-1], float(surv)])
    end = float(np.max(times)) if len(times) else 0
    if xs[-1] < end:
        xs.append(end)
        ys.append(ys[-1])
    median = None
    for x, y in zip(xs, ys):
        if y <= 0.5:
            median = x
            break
    return np.array(xs), np.array(ys), median


def _multigroup_logrank(times, events, groups):
    times = np.asarray(times, dtype=float)
    events = np.asarray(events, dtype=int)
    groups = np.asarray(groups)
    labels = np.array(sorted(pd.unique(groups)))
    k = len(labels)
    if k < 2:
        return 0.0, 1.0

    observed = np.zeros(k)
    expected = np.zeros(k)
    cov = np.zeros((k, k))

    for t in np.sort(np.unique(times[events == 1])):
        risk = times >= t
        death_mask = (times == t) & (events == 1)
        n = risk.sum()
        d = death_mask.sum()
        if n <= 1 or d == 0:
            continue
        n_g = np.array([np.sum(risk & (groups == g)) for g in labels], dtype=float)
        d_g = np.array([np.sum(death_mask & (groups == g)) for g in labels], dtype=float)
        p = n_g / n
        observed += d_g
        expected += d * p
        factor = d * (n - d) / (n - 1)
        cov += factor * (np.diag(p) - np.outer(p, p))

    diff = observed - expected
    v = cov[:-1, :-1]
    z = diff[:-1]
    try:
        chi2 = float(z.T @ np.linalg.pinv(v) @ z)
        pvalue = float(stats.chi2.sf(chi2, k - 1))
    except Exception:
        chi2, pvalue = 0.0, 1.0
    return chi2, pvalue



PLATFORM_DATASETS = {
    "none": {
        "zh": "暂不选择平台数据",
        "en": "No platform dataset",
        "description_zh": "可以改为上传文件、粘贴数据，或在分析指令中直接附带表格。",
        "description_en": "You may instead upload a file, paste data, or embed a table in the analysis instruction.",
        "fields": [],
    },
    "nsclc": {
        "zh": "肺癌科研数据集 · NSCLC",
        "en": "Lung cancer dataset · NSCLC",
        "description_zh": "人口学、EGFR状态、治疗方案、随访事件和总生存时间。",
        "description_en": "Demographics, EGFR status, treatment, follow-up event and overall survival.",
        "fields": ["sex", "age", "molecular_status", "treatment", "os_months", "event"],
    },
    "breast": {
        "zh": "乳腺癌科研数据集",
        "en": "Breast cancer dataset",
        "description_zh": "人口学、HER2状态、治疗方案、随访事件和总生存时间。",
        "description_en": "Demographics, HER2 status, treatment, follow-up event and overall survival.",
        "fields": ["sex", "age", "molecular_status", "treatment", "os_months", "event"],
    },
    "crc": {
        "zh": "结直肠癌科研数据集",
        "en": "Colorectal cancer dataset",
        "description_zh": "人口学、KRAS状态、治疗方案、随访事件和总生存时间。",
        "description_en": "Demographics, KRAS status, treatment, follow-up event and overall survival.",
        "fields": ["sex", "age", "molecular_status", "treatment", "os_months", "event"],
    },
    "t2dm": {
        "zh": "2型糖尿病科研数据集",
        "en": "Type 2 diabetes dataset",
        "description_zh": "人口学、治疗方案、基线/随访HbA1c与HbA1c变化量。",
        "description_en": "Demographics, treatment, baseline/follow-up HbA1c and HbA1c change.",
        "fields": ["sex", "age", "treatment", "baseline_hba1c", "followup_hba1c", "hba1c_change"],
    },
    "hypertension": {
        "zh": "高血压科研数据集",
        "en": "Hypertension dataset",
        "description_zh": "人口学、治疗方案、基线/随访血压、血压变化量和控制结局。",
        "description_en": "Demographics, treatment, baseline/follow-up BP, BP changes and control outcome.",
        "fields": ["sex", "age", "treatment", "baseline_sbp", "followup_sbp", "bp_controlled", "sbp_change"],
    },
}

@dataclass
class DataProfile:
    rows: int
    columns: int
    numeric_columns: list[str]
    categorical_columns: list[str]
    missing_cells: int
    missing_rate: float


class CustomDataEngine:
    MAX_ROWS = 100_000
    MAX_COLUMNS = 250

    def platform_dataset_options(self, lang="zh"):
        key = "zh" if lang == "zh" else "en"
        return [(code, meta[key]) for code, meta in PLATFORM_DATASETS.items()]

    def platform_dataset_description(self, code, lang="zh"):
        meta = PLATFORM_DATASETS.get(code, PLATFORM_DATASETS["none"])
        return meta["description_zh" if lang == "zh" else "description_en"]

    def platform_dataset_fields(self, code):
        return list(PLATFORM_DATASETS.get(code, {}).get("fields", []))

    def load_platform_dataset(self, code: str) -> pd.DataFrame | None:
        if code == "none":
            return None

        db_engine = get_engine()

        if code in {"nsclc", "breast", "crc"}:
            code_map = {
                "nsclc": ("C34-NSCLC", "EGFR"),
                "breast": ("C50-BREAST", "HER2"),
                "crc": ("C18-CRC", "KRAS"),
            }
            diagnosis_code, gene = code_map[code]
            sql = """
            WITH dx AS (
                SELECT patient_id, MIN(diagnosis_date) AS diagnosis_date
                FROM diagnoses
                WHERE diagnosis_code=:diagnosis_code
                GROUP BY patient_id
            ),
            mol AS (
                SELECT patient_id,
                       MAX(CASE WHEN gene=:gene THEN result END) AS molecular_status
                FROM molecular_tests
                GROUP BY patient_id
            ),
            tx AS (
                SELECT t.patient_id,
                       t.regimen,
                       MIN(t.start_date) AS treatment_start
                FROM treatments t
                JOIN dx ON dx.patient_id=t.patient_id
                WHERE date(t.start_date)>=date(dx.diagnosis_date)
                GROUP BY t.patient_id
            ),
            fu AS (
                SELECT patient_id,
                       MAX(followup_date) AS last_followup,
                       MAX(CASE WHEN status='DEAD' THEN 1 ELSE 0 END) AS event
                FROM followups
                GROUP BY patient_id
            ),
            death AS (
                SELECT patient_id, MIN(followup_date) AS death_date
                FROM followups
                WHERE status='DEAD'
                GROUP BY patient_id
            )
            SELECT
                p.patient_id,
                p.sex,
                ROUND((julianday(dx.diagnosis_date)-julianday(p.birth_date))/365.25,1) AS age,
                dx.diagnosis_date,
                mol.molecular_status,
                tx.regimen AS treatment,
                tx.treatment_start,
                fu.last_followup,
                fu.event,
                ROUND(
                    (julianday(COALESCE(death.death_date,fu.last_followup))
                     - julianday(tx.treatment_start))/30.4375,
                    2
                ) AS os_months
            FROM patients p
            JOIN dx ON dx.patient_id=p.patient_id
            LEFT JOIN mol ON mol.patient_id=p.patient_id
            JOIN tx ON tx.patient_id=p.patient_id
            JOIN fu ON fu.patient_id=p.patient_id
            LEFT JOIN death ON death.patient_id=p.patient_id
            """
            with db_engine.connect() as conn:
                df = pd.read_sql(
                    text(sql),
                    conn,
                    params={"diagnosis_code": diagnosis_code, "gene": gene},
                )
            return self.prepare(df)

        if code == "t2dm":
            sql = """
            WITH dx AS (
                SELECT patient_id, MIN(diagnosis_date) AS diagnosis_date
                FROM diagnoses
                WHERE diagnosis_code='E11-T2DM'
                GROUP BY patient_id
            ),
            tx AS (
                SELECT t.patient_id,
                       t.regimen,
                       MIN(t.start_date) AS treatment_start
                FROM treatments t
                JOIN dx ON dx.patient_id=t.patient_id
                WHERE date(t.start_date)>=date(dx.diagnosis_date)
                GROUP BY t.patient_id
            ),
            base_lab AS (
                SELECT l.patient_id,
                       l.value AS baseline_hba1c,
                       ROW_NUMBER() OVER (
                         PARTITION BY l.patient_id
                         ORDER BY ABS(julianday(l.test_date)-julianday(tx.treatment_start))
                       ) AS rn
                FROM lab_results l
                JOIN tx ON tx.patient_id=l.patient_id
                WHERE l.test_code='HBA1C'
                  AND date(l.test_date)<=date(tx.treatment_start,'+30 day')
            ),
            follow_lab AS (
                SELECT l.patient_id,
                       l.value AS followup_hba1c,
                       ROW_NUMBER() OVER (
                         PARTITION BY l.patient_id
                         ORDER BY date(l.test_date) DESC
                       ) AS rn
                FROM lab_results l
                JOIN tx ON tx.patient_id=l.patient_id
                WHERE l.test_code='HBA1C'
                  AND date(l.test_date)>=date(tx.treatment_start,'+90 day')
                  AND date(l.test_date)<=date(tx.treatment_start,'+365 day')
            )
            SELECT
                p.patient_id,
                p.sex,
                ROUND((julianday(dx.diagnosis_date)-julianday(p.birth_date))/365.25,1) AS age,
                dx.diagnosis_date,
                tx.regimen AS treatment,
                b.baseline_hba1c,
                f.followup_hba1c,
                ROUND(f.followup_hba1c-b.baseline_hba1c,2) AS hba1c_change
            FROM patients p
            JOIN dx ON dx.patient_id=p.patient_id
            JOIN tx ON tx.patient_id=p.patient_id
            LEFT JOIN base_lab b ON b.patient_id=p.patient_id AND b.rn=1
            LEFT JOIN follow_lab f ON f.patient_id=p.patient_id AND f.rn=1
            """
            with db_engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
            return self.prepare(df)

        if code == "hypertension":
            sql = """
            WITH dx AS (
                SELECT patient_id, MIN(diagnosis_date) AS diagnosis_date
                FROM diagnoses
                WHERE diagnosis_code='I10-HTN'
                GROUP BY patient_id
            ),
            tx AS (
                SELECT t.patient_id,
                       t.regimen,
                       MIN(t.start_date) AS treatment_start
                FROM treatments t
                JOIN dx ON dx.patient_id=t.patient_id
                WHERE date(t.start_date)>=date(dx.diagnosis_date)
                GROUP BY t.patient_id
            ),
            before_bp AS (
                SELECT b.patient_id,b.sbp AS baseline_sbp,b.dbp AS baseline_dbp,
                       ROW_NUMBER() OVER(
                         PARTITION BY b.patient_id
                         ORDER BY ABS(julianday(b.observation_date)-julianday(tx.treatment_start))
                       ) AS rn
                FROM blood_pressure b
                JOIN tx ON tx.patient_id=b.patient_id
                WHERE date(b.observation_date)<=date(tx.treatment_start,'+30 day')
            ),
            after_bp AS (
                SELECT b.patient_id,b.sbp AS followup_sbp,b.dbp AS followup_dbp,
                       ROW_NUMBER() OVER(
                         PARTITION BY b.patient_id
                         ORDER BY date(b.observation_date) DESC
                       ) AS rn
                FROM blood_pressure b
                JOIN tx ON tx.patient_id=b.patient_id
                WHERE date(b.observation_date)>=date(tx.treatment_start,'+30 day')
                  AND date(b.observation_date)<=date(tx.treatment_start,'+365 day')
            )
            SELECT
                p.patient_id,
                p.sex,
                ROUND((julianday(dx.diagnosis_date)-julianday(p.birth_date))/365.25,1) AS age,
                dx.diagnosis_date,
                tx.regimen AS treatment,
                b.baseline_sbp,
                b.baseline_dbp,
                a.followup_sbp,
                a.followup_dbp,
                CASE
                  WHEN a.followup_sbp<140 AND a.followup_dbp<90 THEN 1
                  ELSE 0
                END AS bp_controlled,
                (a.followup_sbp-b.baseline_sbp) AS sbp_change,
                (a.followup_dbp-b.baseline_dbp) AS dbp_change
            FROM patients p
            JOIN dx ON dx.patient_id=p.patient_id
            JOIN tx ON tx.patient_id=p.patient_id
            LEFT JOIN before_bp b ON b.patient_id=p.patient_id AND b.rn=1
            LEFT JOIN after_bp a ON a.patient_id=p.patient_id AND a.rn=1
            """
            with db_engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
            return self.prepare(df)

        raise ValueError(f"Unknown platform dataset: {code}")

    def load_uploaded(self, uploaded_file) -> pd.DataFrame:
        name = uploaded_file.name.lower()
        data = uploaded_file.getvalue()

        if name.endswith(".csv"):
            df = _read_csv_bytes(data)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(data), engine="openpyxl")
        elif name.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(data), engine="xlrd")
        else:
            raise ValueError("仅支持 CSV / XLS / XLSX。")

        return self.prepare(df)

    def load_pasted(self, text: str) -> pd.DataFrame:
        return self.prepare(_parse_delimited_text(text))

    def extract_from_question(self, question: str) -> pd.DataFrame | None:
        block = _extract_delimited_block(question)
        if not block:
            return None
        return self.load_pasted(block)

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            raise ValueError("数据为空 / Dataset is empty.")
        if len(df) > self.MAX_ROWS:
            raise ValueError(f"当前演示版最多支持 {self.MAX_ROWS:,} 行。")
        if len(df.columns) > self.MAX_COLUMNS:
            raise ValueError(f"当前演示版最多支持 {self.MAX_COLUMNS} 个变量。")
        df = _clean_columns(df)
        df = _coerce_numeric_like(df)
        return df

    def profile(self, df: pd.DataFrame) -> DataProfile:
        missing = int(df.isna().sum().sum())
        total = max(int(df.shape[0] * df.shape[1]), 1)
        return DataProfile(
            rows=int(len(df)),
            columns=int(len(df.columns)),
            numeric_columns=_numeric_cols(df),
            categorical_columns=_categorical_cols(df),
            missing_cells=missing,
            missing_rate=missing / total,
        )

    def infer_intent(self, question: str, df: pd.DataFrame) -> dict:
        q = (question or "").lower()
        cols = list(df.columns)
        mentioned = _match_columns_in_question(q, cols)
        nums = _numeric_cols(df)
        cats = _categorical_cols(df)

        explicit = None
        keyword_map = [
            ("paired_t", ["配对t", "paired t", "paired-t"]),
            ("t_test", ["t检验", "t 检验", "t-test", "t test", "independent t"]),
            ("wilcoxon", ["wilcoxon", "配对秩和"]),
            ("mann_whitney", ["mann", "mann-whitney", "秩和检验", "rank sum"]),
            ("anova", ["anova", "方差分析"]),
            ("kruskal", ["kruskal"]),
            ("fisher", ["fisher"]),
            ("chi_square", ["卡方", "chi-square", "chi square"]),
            ("spearman", ["spearman"]),
            ("pearson", ["pearson"]),
            ("logistic_regression", ["logistic", "逻辑回归", "logit"]),
            ("linear_regression", ["线性回归", "linear regression", "ols"]),
            ("cox", ["cox"]),
            ("survival", ["kaplan", "log-rank", "logrank", "生存曲线", "生存分析"]),
            ("descriptive", ["描述统计", "描述性统计", "descriptive"]),
        ]
        for method, words in keyword_map:
            if any(w in q for w in words):
                explicit = method
                break

        group_guess = next(
            (c for c in mentioned if c in cats),
            next((c for c in cats if re.search(r"group|arm|treat|regimen|组|方案|治疗", c, re.I)), None),
        )
        time_guess = next(
            (c for c in cols if re.search(r"(^|_)(time|duration|months?|days?|os|pfs)($|_)|时间|时长|生存期|随访", c, re.I)),
            None,
        )
        event_guess = next(
            (c for c in cols if re.search(r"event|death|status|censor|死亡|事件|结局状态", c, re.I)),
            None,
        )

        numeric_mentioned = [c for c in mentioned if c in nums]
        categorical_mentioned = [c for c in mentioned if c in cats]

        outcome_guess = numeric_mentioned[0] if numeric_mentioned else (
            next((c for c in nums if re.search(r"outcome|value|score|hba1c|result|指标|结局|数值|评分", c, re.I)), None)
        )

        x_guess = numeric_mentioned[0] if numeric_mentioned else (nums[0] if nums else None)
        y_guess = numeric_mentioned[1] if len(numeric_mentioned) > 1 else (nums[1] if len(nums) > 1 else None)

        if explicit:
            method = explicit
        elif any(w in q for w in ["生存", "survival", "死亡", "mortality"]) and time_guess and event_guess:
            method = "survival"
        elif any(w in q for w in ["相关", "correlation", "关联"]) and len(nums) >= 2:
            method = "spearman"
        elif group_guess and outcome_guess:
            levels = df[group_guess].nunique(dropna=True)
            method = "t_test" if levels == 2 else "anova"
        elif len(categorical_mentioned) >= 2:
            method = "chi_square"
        else:
            method = "descriptive"

        return {
            "method": method,
            "mentioned_columns": mentioned,
            "group": group_guess,
            "outcome": outcome_guess,
            "x": x_guess,
            "y": y_guess,
            "time": time_guess,
            "event": event_guess,
            "predictors": numeric_mentioned[1:] if len(numeric_mentioned) > 1 else [],
        }

    def _result(self, method, p, summary, image_b64, conclusion, details=None):
        return {
            "method": method,
            "p": p,
            "summary": summary,
            "image": image_b64,
            "conclusion": conclusion,
            "details": details or [],
        }

    def analyze(self, df: pd.DataFrame, config: dict, lang="zh") -> dict:
        method = config["method"]
        if method == "descriptive":
            return self._descriptive(df, config, lang)
        if method in {"t_test", "mann_whitney", "anova", "kruskal"}:
            return self._group_numeric(df, config, lang)
        if method in {"paired_t", "wilcoxon"}:
            return self._paired(df, config, lang)
        if method in {"chi_square", "fisher"}:
            return self._categorical(df, config, lang)
        if method in {"pearson", "spearman"}:
            return self._correlation(df, config, lang)
        if method == "linear_regression":
            return self._linear_regression(df, config, lang)
        if method == "logistic_regression":
            return self._logistic_regression(df, config, lang)
        if method in {"survival", "cox"}:
            return self._survival(df, config, lang)
        raise ValueError(f"暂不支持方法：{method}")

    def _descriptive(self, df, config, lang):
        rows = []
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                s = pd.to_numeric(df[c], errors="coerce").dropna()
                rows.append({
                    "variable": c,
                    "type": "numeric",
                    "n": int(len(s)),
                    "mean": round(float(s.mean()), 4) if len(s) else None,
                    "sd": round(float(s.std(ddof=1)), 4) if len(s) > 1 else None,
                    "median": round(float(s.median()), 4) if len(s) else None,
                    "missing": int(df[c].isna().sum()),
                })
            else:
                s = df[c].dropna().astype(str)
                top = s.value_counts().index[0] if len(s) else None
                rows.append({
                    "variable": c,
                    "type": "categorical",
                    "n": int(len(s)),
                    "mean": None,
                    "sd": None,
                    "median": None,
                    "missing": int(df[c].isna().sum()),
                    "top": top,
                })

        fig, ax = plt.subplots(figsize=(8.2, 4.8))
        nums = _numeric_cols(df)
        if nums:
            vals = pd.to_numeric(df[nums[0]], errors="coerce").dropna()
            ax.hist(vals, bins=min(20, max(5, int(np.sqrt(max(len(vals), 1))))))
            ax.set_title(f"Distribution: {nums[0]}")
            ax.set_xlabel(nums[0])
            ax.set_ylabel("Count")
        else:
            first = df.columns[0]
            vc = df[first].astype(str).value_counts().head(12)
            ax.bar(vc.index.astype(str), vc.values)
            ax.set_title(f"Frequency: {first}")
            ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()

        conclusion = (
            "已完成数据集描述性统计。该结果用于概览样本分布，不进行显著性推断。"
            if lang == "zh"
            else "Descriptive statistics are complete. This summarizes the dataset without inferential significance testing."
        )
        return self._result("Descriptive statistics", None, rows, _image(fig), conclusion)

    def _group_numeric(self, df, config, lang):
        group = config.get("group")
        outcome = config.get("outcome")
        if not group or not outcome:
            raise ValueError("该方法需要选择分组变量和连续结局变量。")

        d = df[[group, outcome]].copy()
        d[outcome] = pd.to_numeric(d[outcome], errors="coerce")
        d = d.dropna()
        groups = list(pd.unique(d[group]))
        arrays = [d.loc[d[group] == g, outcome].values.astype(float) for g in groups]
        if len(groups) < 2:
            raise ValueError("分组变量至少需要两个有效组别。")

        method = config["method"]
        if method == "t_test":
            if len(groups) != 2:
                raise ValueError("独立样本 t 检验需要恰好两个组。")
            res = stats.ttest_ind(arrays[0], arrays[1], equal_var=False, nan_policy="omit")
            p = float(res.pvalue)
            stat_name = "Welch t-test"
            pooled = np.sqrt(((len(arrays[0])-1)*np.var(arrays[0], ddof=1) + (len(arrays[1])-1)*np.var(arrays[1], ddof=1)) / max(len(arrays[0])+len(arrays[1])-2, 1))
            effect = (np.mean(arrays[0])-np.mean(arrays[1])) / pooled if pooled > 0 else np.nan
            details = [{"metric": "Cohen_d", "value": float(effect) if np.isfinite(effect) else None}]
        elif method == "mann_whitney":
            if len(groups) != 2:
                raise ValueError("Mann–Whitney U 检验需要恰好两个组。")
            res = stats.mannwhitneyu(arrays[0], arrays[1], alternative="two-sided")
            p = float(res.pvalue)
            stat_name = "Mann–Whitney U"
            details = [{"metric": "U", "value": float(res.statistic)}]
        elif method == "anova":
            res = stats.f_oneway(*arrays)
            p = float(res.pvalue)
            stat_name = "One-way ANOVA"
            details = [{"metric": "F", "value": float(res.statistic)}]
        else:
            res = stats.kruskal(*arrays)
            p = float(res.pvalue)
            stat_name = "Kruskal–Wallis"
            details = [{"metric": "H", "value": float(res.statistic)}]

        summary = []
        for g, arr in zip(groups, arrays):
            summary.append({
                "group": str(g),
                "n": int(len(arr)),
                "mean": round(float(np.mean(arr)), 4),
                "sd": round(float(np.std(arr, ddof=1)), 4) if len(arr) > 1 else None,
                "median": round(float(np.median(arr)), 4),
            })

        fig, ax = plt.subplots(figsize=(8.3, 5))
        ax.boxplot(arrays, tick_labels=[str(g) for g in groups], showmeans=True)
        ax.set_title(f"{outcome} by {group}")
        ax.set_ylabel(outcome)
        ax.tick_params(axis="x", rotation=15)
        fig.tight_layout()

        if lang == "zh":
            conclusion = (
                f"{stat_name} 显示不同组的 {outcome} 存在统计学显著差异（P={p:.4g}）。"
                if p < .05 else
                f"{stat_name} 未发现不同组的 {outcome} 存在统计学显著差异（P={p:.4g}）。"
            )
        else:
            conclusion = (
                f"{stat_name} detected a statistically significant difference in {outcome} across groups (P={p:.4g})."
                if p < .05 else
                f"{stat_name} did not detect a statistically significant difference in {outcome} across groups (P={p:.4g})."
            )
        return self._result(stat_name, p, summary, _image(fig), conclusion, details)

    def _paired(self, df, config, lang):
        before = config.get("x")
        after = config.get("y")
        if not before or not after:
            raise ValueError("配对分析需要选择两个连续变量，例如治疗前和治疗后。")
        d = df[[before, after]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(d) < 2:
            raise ValueError("有效配对样本不足。")
        diff = d[after] - d[before]

        if config["method"] == "paired_t":
            res = stats.ttest_rel(d[before], d[after])
            name = "Paired t-test"
        else:
            res = stats.wilcoxon(d[before], d[after])
            name = "Wilcoxon signed-rank"
        p = float(res.pvalue)

        summary = [{
            "n": int(len(d)),
            f"{before}_mean": round(float(d[before].mean()), 4),
            f"{after}_mean": round(float(d[after].mean()), 4),
            "mean_change": round(float(diff.mean()), 4),
            "median_change": round(float(diff.median()), 4),
        }]

        fig, ax = plt.subplots(figsize=(7.8, 4.8))
        ax.boxplot([d[before].values, d[after].values], tick_labels=[before, after], showmeans=True)
        ax.set_title(f"Paired comparison: {before} vs {after}")
        fig.tight_layout()

        conclusion = (
            f"{name} {'显示两次测量存在统计学显著差异' if p < .05 else '未显示两次测量存在统计学显著差异'}（P={p:.4g}）。"
            if lang == "zh" else
            f"{name} {'detected' if p < .05 else 'did not detect'} a statistically significant paired difference (P={p:.4g})."
        )
        return self._result(name, p, summary, _image(fig), conclusion)

    def _categorical(self, df, config, lang):
        group = config.get("group")
        outcome = config.get("outcome")
        if not group or not outcome:
            raise ValueError("分类变量检验需要选择两个分类变量。")
        d = df[[group, outcome]].dropna()
        table = pd.crosstab(d[group], d[outcome])
        if table.shape[0] < 2 or table.shape[1] < 2:
            raise ValueError("两个变量都至少需要两个有效类别。")

        use_fisher = config["method"] == "fisher"
        if use_fisher:
            if table.shape != (2, 2):
                raise ValueError("Fisher 精确检验当前仅支持 2×2 列联表。")
            stat, p = stats.fisher_exact(table.values)
            name = "Fisher's exact test"
            details = [{"metric": "odds_ratio", "value": float(stat)}]
        else:
            stat, p, dof, expected = stats.chi2_contingency(table)
            name = "Chi-square test"
            details = [{"metric": "chi2", "value": float(stat)}, {"metric": "dof", "value": int(dof)}]

        p = float(p)
        summary = table.reset_index().to_dict("records")

        pct = table.div(table.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(8.3, 5))
        bottom = np.zeros(len(pct))
        for col in pct.columns:
            vals = pct[col].values
            ax.bar(pct.index.astype(str), vals, bottom=bottom, label=str(col))
            bottom += vals
        ax.set_ylabel("Percent (%)")
        ax.set_title(f"{outcome} by {group}")
        ax.legend(title=outcome, fontsize=8)
        ax.tick_params(axis="x", rotation=15)
        fig.tight_layout()

        conclusion = (
            f"{name} {'显示两个分类变量存在统计学显著关联' if p < .05 else '未显示两个分类变量存在统计学显著关联'}（P={p:.4g}）。"
            if lang == "zh" else
            f"{name} {'detected' if p < .05 else 'did not detect'} a statistically significant association (P={p:.4g})."
        )
        return self._result(name, p, summary, _image(fig), conclusion, details)

    def _correlation(self, df, config, lang):
        x, y = config.get("x"), config.get("y")
        if not x or not y:
            raise ValueError("相关分析需要选择两个连续变量。")
        d = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(d) < 3:
            raise ValueError("有效样本不足。")

        if config["method"] == "pearson":
            r, p = stats.pearsonr(d[x], d[y])
            name = "Pearson correlation"
        else:
            r, p = stats.spearmanr(d[x], d[y])
            name = "Spearman correlation"
        r, p = float(r), float(p)

        fig, ax = plt.subplots(figsize=(7.8, 5))
        ax.scatter(d[x], d[y], alpha=.65)
        if len(d) >= 2:
            coef = np.polyfit(d[x], d[y], 1)
            xs = np.linspace(d[x].min(), d[x].max(), 100)
            ax.plot(xs, coef[0] * xs + coef[1])
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(f"{name}: r={r:.3f}")
        fig.tight_layout()

        summary = [{"n": int(len(d)), "correlation": round(r, 4), "p": p}]
        conclusion = (
            f"{name}：{x} 与 {y} 的相关系数为 {r:.3f}，{'相关具有统计学意义' if p < .05 else '相关未达到统计学显著'}（P={p:.4g}）。"
            if lang == "zh" else
            f"{name}: correlation between {x} and {y} was r={r:.3f}; it {'was' if p < .05 else 'was not'} statistically significant (P={p:.4g})."
        )
        return self._result(name, p, summary, _image(fig), conclusion)

    def _design_matrix(self, df, predictors):
        X = df[predictors].copy()
        X = pd.get_dummies(X, drop_first=True, dtype=float)
        for c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")
        return X

    def _linear_regression(self, df, config, lang):
        outcome = config.get("outcome")
        predictors = config.get("predictors") or []
        if not outcome or not predictors:
            raise ValueError("线性回归需要选择一个连续结局变量和至少一个自变量。")

        y = pd.to_numeric(df[outcome], errors="coerce")
        X = self._design_matrix(df, predictors)
        d = pd.concat([y.rename("__y__"), X], axis=1).dropna()
        if len(d) <= len(X.columns) + 2:
            raise ValueError("有效样本量不足以拟合该回归模型。")

        y2 = d.pop("__y__")
        X2 = sm.add_constant(d, has_constant="add")
        model = sm.OLS(y2, X2).fit()

        summary = []
        for var in model.params.index:
            summary.append({
                "variable": var,
                "coef": round(float(model.params[var]), 5),
                "CI95_low": round(float(model.conf_int().loc[var, 0]), 5),
                "CI95_high": round(float(model.conf_int().loc[var, 1]), 5),
                "p": float(model.pvalues[var]),
            })

        fig, ax = plt.subplots(figsize=(8, max(4, .45 * len(summary) + 1)))
        coefs = [x["coef"] for x in summary if x["variable"] != "const"]
        names = [x["variable"] for x in summary if x["variable"] != "const"]
        ax.barh(names, coefs)
        ax.axvline(0, linewidth=1)
        ax.set_title("Linear regression coefficients")
        fig.tight_layout()

        p_model = float(model.f_pvalue) if np.isfinite(model.f_pvalue) else None
        conclusion = (
            f"线性回归模型已拟合，R²={model.rsquared:.3f}"
            + (f"，整体模型 P={p_model:.4g}。" if p_model is not None else "。")
            if lang == "zh" else
            f"Linear regression fitted with R²={model.rsquared:.3f}"
            + (f" and overall model P={p_model:.4g}." if p_model is not None else ".")
        )
        return self._result("Linear regression", p_model, summary, _image(fig), conclusion)

    def _binary_encode(self, s):
        vals = list(pd.unique(s.dropna()))
        if len(vals) != 2:
            raise ValueError("Logistic 回归的结局变量必须恰好有两个类别。")
        mapping = {vals[0]: 0, vals[1]: 1}
        return s.map(mapping), mapping

    def _logistic_regression(self, df, config, lang):
        outcome = config.get("outcome")
        predictors = config.get("predictors") or []
        if not outcome or not predictors:
            raise ValueError("Logistic 回归需要选择一个二分类结局变量和至少一个自变量。")

        y, mapping = self._binary_encode(df[outcome])
        X = self._design_matrix(df, predictors)
        d = pd.concat([y.rename("__y__"), X], axis=1).dropna()
        if len(d) <= len(X.columns) + 4:
            raise ValueError("有效样本量不足以拟合 Logistic 回归。")

        y2 = d.pop("__y__").astype(float)
        X2 = sm.add_constant(d, has_constant="add")
        model = sm.Logit(y2, X2).fit(disp=False, maxiter=200)

        ci = model.conf_int()
        summary = []
        for var in model.params.index:
            summary.append({
                "variable": var,
                "OR": round(float(np.exp(model.params[var])), 5),
                "CI95_low": round(float(np.exp(ci.loc[var, 0])), 5),
                "CI95_high": round(float(np.exp(ci.loc[var, 1])), 5),
                "p": float(model.pvalues[var]),
            })

        plot_rows = [x for x in summary if x["variable"] != "const"]
        fig, ax = plt.subplots(figsize=(8, max(4, .48 * len(plot_rows) + 1)))
        ors = [x["OR"] for x in plot_rows]
        names = [x["variable"] for x in plot_rows]
        ax.barh(names, ors)
        ax.axvline(1, linewidth=1)
        ax.set_title("Logistic regression odds ratios")
        fig.tight_layout()

        p_model = float(model.llr_pvalue)
        conclusion = (
            f"Logistic 回归已完成，整体模型似然比检验 P={p_model:.4g}。结局编码：{mapping}。"
            if lang == "zh" else
            f"Logistic regression completed; likelihood-ratio model P={p_model:.4g}. Outcome mapping: {mapping}."
        )
        return self._result("Logistic regression", p_model, summary, _image(fig), conclusion)

    def _survival(self, df, config, lang):
        time_col = config.get("time")
        event_col = config.get("event")
        group = config.get("group")
        if not time_col or not event_col:
            raise ValueError("生存分析必须选择时间变量和事件变量。")

        cols = [time_col, event_col] + ([group] if group else [])
        d = df[cols].copy()
        d[time_col] = pd.to_numeric(d[time_col], errors="coerce")
        d[event_col] = pd.to_numeric(d[event_col], errors="coerce")
        d = d.dropna(subset=[time_col, event_col])
        d = d[d[time_col] >= 0]
        d[event_col] = (d[event_col] != 0).astype(int)
        if d.empty:
            raise ValueError("没有有效的生存分析数据。")

        if group:
            groups = list(pd.unique(d[group].dropna()))
        else:
            d["__all__"] = "All"
            group = "__all__"
            groups = ["All"]

        fig, ax = plt.subplots(figsize=(8.4, 5.2))
        summary = []
        for g in groups:
            sub = d[d[group] == g]
            xs, ys, median = _km_curve(sub[time_col], sub[event_col])
            ax.step(xs, ys, where="post", label=str(g))
            summary.append({
                "group": str(g),
                "n": int(len(sub)),
                "events": int(sub[event_col].sum()),
                "median_time": None if median is None else round(float(median), 4),
            })

        ax.set_xlabel(time_col)
        ax.set_ylabel("Survival probability")
        ax.set_ylim(0, 1.03)
        ax.set_title("Kaplan–Meier survival")
        if len(groups) > 1:
            ax.legend()
        ax.grid(alpha=.2)
        fig.tight_layout()

        if len(groups) > 1:
            stat, p = _multigroup_logrank(d[time_col], d[event_col], d[group])
            p = float(p)
            conclusion = (
                f"Kaplan–Meier / Log-rank 分析{'显示组间生存曲线存在统计学显著差异' if p < .05 else '未显示组间生存曲线存在统计学显著差异'}（P={p:.4g}）。"
                if lang == "zh" else
                f"Kaplan–Meier / Log-rank {'detected' if p < .05 else 'did not detect'} a statistically significant difference between survival curves (P={p:.4g})."
            )
            details = [{"metric": "logrank_statistic", "value": float(stat)}]
        else:
            p = None
            conclusion = (
                "已完成单队列 Kaplan–Meier 生存估计；未提供分组变量，因此不进行组间 Log-rank 检验。"
                if lang == "zh" else
                "Single-cohort Kaplan–Meier estimation completed; no group variable was supplied, so no between-group Log-rank test was performed."
            )
            details = []

        # Cox if explicitly selected.
        if config["method"] == "cox":
            predictors = config.get("predictors") or []
            if not predictors:
                raise ValueError("Cox 回归需要至少一个协变量/自变量。")
            X = self._design_matrix(df, predictors)
            survival_df = pd.concat([
                pd.to_numeric(df[time_col], errors="coerce").rename("__time__"),
                pd.to_numeric(df[event_col], errors="coerce").rename("__event__"),
                X,
            ], axis=1).dropna()
            survival_df["__event__"] = (survival_df["__event__"] != 0).astype(int)

            from statsmodels.duration.hazard_regression import PHReg
            exog = survival_df.drop(columns=["__time__", "__event__"])
            model = PHReg(
                survival_df["__time__"],
                exog,
                status=survival_df["__event__"],
            ).fit(disp=False)
            ci = model.conf_int()
            cox_rows = []
            for i, name in enumerate(exog.columns):
                cox_rows.append({
                    "variable": name,
                    "HR": round(float(np.exp(model.params[i])), 5),
                    "CI95_low": round(float(np.exp(ci[i, 0])), 5),
                    "CI95_high": round(float(np.exp(ci[i, 1])), 5),
                    "p": float(model.pvalues[i]),
                })
            summary = cox_rows
            conclusion = (
                "Cox 比例风险模型已完成。HR>1 表示较高瞬时事件风险，HR<1 表示较低瞬时事件风险；请结合95%CI与P值解释。"
                if lang == "zh" else
                "Cox proportional hazards model completed. HR>1 indicates higher instantaneous event hazard and HR<1 lower hazard; interpret with 95% CI and P values."
            )
            details = [{"metric": "n", "value": int(len(survival_df))}]
            return self._result("Cox proportional hazards", None, summary, _image(fig), conclusion, details)

        return self._result("Kaplan–Meier + Log-rank", p, summary, _image(fig), conclusion, details)

    def build_html_report(self, df, config, result, question, lang="zh") -> str:
        profile = self.profile(df)
        summary_html = pd.DataFrame(result.get("summary", [])).to_html(
            index=False, border=0, classes="summary-table"
        )
        chart_uri = "data:image/png;base64," + result["image"]
        p_text = "N/A" if result.get("p") is None else f'{result["p"]:.6g}'
        title = "海研分析 · 自助科研分析报告" if lang == "zh" else "Haiyan Analysis · Self-Service Research Report"
        note = (
            "本报告由上传/粘贴的数据自动计算生成。统计结论依据实际数据，不会按照用户预设方向修改结果。"
            if lang == "zh" else
            "This report is computed from the supplied dataset. Conclusions follow the observed data and are not altered to match a preferred result."
        )
        return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;max-width:1050px;margin:40px auto;color:#183047;line-height:1.65}}
h1,h2{{color:#12324b}} .card{{border:1px solid #dfe8ee;border-radius:14px;padding:18px;margin:14px 0}}
.meta{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}} .meta div{{background:#f5f9fb;padding:12px;border-radius:10px}}
.summary-table{{border-collapse:collapse;width:100%;font-size:13px}} .summary-table th,.summary-table td{{padding:8px;border-bottom:1px solid #e7edf1;text-align:left}}
img{{max-width:100%}} .note{{background:#eef9f6;border:1px solid #d8eee8;padding:14px;border-radius:12px}}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<div class="card"><strong>{"研究问题" if lang=="zh" else "Research question"}：</strong>{html.escape(question)}</div>
<div class="meta">
<div><strong>N</strong><br>{profile.rows}</div>
<div><strong>{"变量" if lang=="zh" else "Variables"}</strong><br>{profile.columns}</div>
<div><strong>{"方法" if lang=="zh" else "Method"}</strong><br>{html.escape(result["method"])}</div>
<div><strong>P</strong><br>{p_text}</div>
</div>
<div class="card"><h2>{"统计结论" if lang=="zh" else "Conclusion"}</h2><p>{html.escape(result["conclusion"])}</p></div>
<div class="card"><h2>{"分析图" if lang=="zh" else "Analysis chart"}</h2><img src="{chart_uri}"></div>
<div class="card"><h2>{"统计摘要" if lang=="zh" else "Summary"}</h2>{summary_html}</div>
<div class="note">{html.escape(note)}</div>
</body></html>"""

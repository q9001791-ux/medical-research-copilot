from dataclasses import dataclass, asdict
import re
from concept_resolver import resolve_disease, resolve_molecular

@dataclass
class ResearchPlan:
    original_query: str
    years: int | None
    disease: str | None
    diagnosis_code: str | None
    gene: str | None
    gene_result: str | None
    group_by: str | None
    endpoint: str | None
    endpoint_type: str | None
    analysis_methods: list[str]
    covariates: list[str]
    explanation: list[str]
    def to_dict(self):
        return asdict(self)

class ResearchAgent:
    def _years(self, text):
        m = re.search(r"近\s*(\d+)\s*年", text)
        if m:
            return int(m.group(1))
        cn = {"一":1,"二":2,"两":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
        m = re.search(r"近\s*([一二两三四五六七八九十])\s*年", text)
        if m:
            return cn[m.group(1)]
        m = re.search(r"(?:past|last)\s+(\d+)\s+years?", text, re.I)
        if m:
            return int(m.group(1))
        words = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
        m = re.search(r"(?:past|last)\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+years?", text, re.I)
        return words[m.group(1).lower()] if m else None

    def plan(self, query, lang="zh"):
        low = query.lower()
        disease = resolve_disease(query)
        molecular = resolve_molecular(query)
        years = self._years(query)
        group_by = "regimen" if any(x in low for x in ["治疗方案","不同治疗","治疗组","用药方案","treatment regimen","treatment regimens","different treatment","therapy"]) else None
        if any(x in low for x in ["hba1c","糖化血红蛋白"]):
            endpoint, endpoint_type, methods = "HBA1C_FOLLOWUP", "continuous", ["Descriptive", "ANOVA / Kruskal-Wallis"]
        elif any(x in low for x in ["控制率","血压控制","blood pressure control","controlled blood pressure"]):
            endpoint, endpoint_type, methods = "BP_CONTROL", "categorical", ["Contingency table", "Chi-square"]
        elif any(x in low for x in ["生存","survival","死亡","death"]):
            endpoint, endpoint_type, methods = "OS", "survival", ["Kaplan-Meier", "Log-rank", "Cox PH"]
        else:
            endpoint, endpoint_type, methods = None, None, []
        explanation = []
        if lang == "en":
            if disease: explanation.append(f"Disease mapped to {disease['canonical']} ({disease['code']}).")
            if molecular: explanation.append(f"Molecular criterion mapped to {molecular['gene']}={molecular['result']}.")
            if years: explanation.append(f"Time window: diagnosis within the past {years} years.")
            if group_by: explanation.append("Grouping: first treatment regimen after index diagnosis.")
            if endpoint == "OS": explanation.append("Endpoint: overall survival from treatment start to death or last follow-up.")
            if endpoint == "HBA1C_FOLLOWUP": explanation.append("Endpoint: follow-up HbA1c after treatment initiation.")
            if endpoint == "BP_CONTROL": explanation.append("Endpoint: blood-pressure control, defined as SBP <140 and DBP <90 mmHg.")
            if methods: explanation.append("Statistical strategy: " + " + ".join(methods))
        else:
            if disease: explanation.append(f"疾病映射：{disease['canonical']}（{disease['code']}）。")
            if molecular: explanation.append(f"分子条件映射：{molecular['gene']}={molecular['result']}。")
            if years: explanation.append(f"时间窗：索引诊断位于近{years}年。")
            if group_by: explanation.append("分组变量：索引诊断后的首个治疗方案。")
            if endpoint == "OS": explanation.append("研究终点：总生存期OS，自治疗开始至死亡或末次随访。")
            if endpoint == "HBA1C_FOLLOWUP": explanation.append("研究终点：治疗后的随访HbA1c连续指标。")
            if endpoint == "BP_CONTROL": explanation.append("研究终点：随访期血压控制率（SBP<140且DBP<90）。")
            if methods: explanation.append("自动统计策略：" + " + ".join(methods))
        return ResearchPlan(
            query, years,
            disease["canonical"] if disease else None,
            disease["code"] if disease else None,
            molecular["gene"] if molecular else None,
            molecular["result"] if molecular else None,
            group_by, endpoint, endpoint_type, methods, ["age","sex"], explanation
        )

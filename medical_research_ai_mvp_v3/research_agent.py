from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal
import os
import re

from pydantic import BaseModel, Field
from concept_resolver import (
    resolve_disease,
    resolve_molecular,
    normalize_text,
)


# =====================================================================
# Public ResearchPlan consumed by the rest of the application
# =====================================================================
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

    # Extended AI metadata
    demo_supported: bool | None = None
    confidence_notes: list[str] | None = None
    parser_mode: str = "rule"
    parser_model: str | None = None
    research_summary: str | None = None
    inclusion_criteria: list[str] | None = None
    exclusion_criteria: list[str] | None = None
    assumptions: list[str] | None = None
    clarification_needed: bool = False
    clarification_question: str | None = None
    confidence: float | None = None
    executable: bool = True
    execution_warning: str | None = None

    def to_dict(self):
        return asdict(self)


# =====================================================================
# Pydantic schema returned by the LLM using Structured Outputs
# =====================================================================
class LLMResearchExtraction(BaseModel):
    detected_language: Literal["zh", "en", "mixed"] = "mixed"

    research_summary: str = Field(
        description="One concise sentence summarizing the user's intended research question."
    )

    disease_text: str | None = Field(
        default=None,
        description="Disease/condition exactly or approximately described by the user."
    )
    disease_canonical: str | None = Field(
        default=None,
        description="A standard/common English disease name or acronym, without inventing billing/database codes."
    )

    molecular_gene: str | None = Field(
        default=None,
        description="Gene/biomarker if present, such as EGFR, HER2, KRAS, ALK, PD-L1."
    )
    molecular_status: Literal["MUT", "POS", "NEG", "WT", "UNKNOWN"] | None = None

    years: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Relative retrospective time window in years if the user specified one."
    )

    group_by: Literal[
        "regimen",
        "molecular_status",
        "sex",
        "age_group",
        "none",
        "unknown",
    ] = "unknown"

    endpoint: Literal[
        "OS",
        "PFS",
        "HBA1C_FOLLOWUP",
        "BP_CONTROL",
        "RESPONSE_RATE",
        "READMISSION",
        "LAB_VALUE",
        "UNKNOWN",
    ] = "UNKNOWN"

    endpoint_type: Literal[
        "survival",
        "continuous",
        "categorical",
        "binary",
        "unknown",
    ] = "unknown"

    covariates: list[str] = Field(default_factory=list)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    requested_analysis: list[str] = Field(
        default_factory=list,
        description="Statistical analyses explicitly requested or strongly implied."
    )

    clarification_needed: bool = False
    clarification_question: str | None = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


# =====================================================================
# Deterministic bilingual fallback parser
# =====================================================================
class RuleResearchAgent:
    CN_NUM = {
        "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }
    EN_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }

    @staticmethod
    def _any(text: str, phrases: list[str]) -> bool:
        return any(p in text for p in phrases)

    def _extract_years(self, query: str) -> int | None:
        text = normalize_text(query)

        patterns = [
            r"(?:近|最近|过去|近来的)\s*(\d+)\s*年",
            r"(\d+)\s*年(?:内|以来|期间)",
            r"(?:past|last|previous|within the last|within past)\s+(\d+)\s+years?",
            r"(?:in|during)\s+the\s+(?:past|last|previous)\s+(\d+)\s+years?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                return int(match.group(1))

        for pattern in [
            r"(?:近|最近|过去)\s*([一二两三四五六七八九十])\s*年",
            r"([一二两三四五六七八九十])\s*年(?:内|以来|期间)",
        ]:
            match = re.search(pattern, text)
            if match:
                return self.CN_NUM[match.group(1)]

        match = re.search(
            r"(?:past|last|previous|within the last|within past)\s+"
            r"(one|two|three|four|five|six|seven|eight|nine|ten)\s+years?",
            text,
            flags=re.I,
        )
        if match:
            return self.EN_NUM[match.group(1).lower()]
        return None

    def _infer_group(self, text: str) -> str | None:
        terms = [
            "不同治疗", "不同方案", "治疗方案", "治疗组", "用药方案",
            "不同用药", "不同药物", "几种治疗", "治疗方式", "治疗方法",
            "哪个方案", "哪种方案", "哪种治疗", "方案之间", "疗法之间",
            "treatment regimen", "treatment regimens", "regimen", "regimens",
            "different treatment", "different treatments", "different therapy",
            "by treatment", "by therapy", "by regimen", "across treatment",
            "across regimens", "which treatment", "which therapy",
        ]
        return "regimen" if self._any(text, terms) else None

    def _infer_endpoint(self, text: str, disease: str | None):
        survival_terms = [
            "生存期", "总生存", "生存率", "生存曲线", "死亡风险",
            "存活", "活得更久", "活多久", "活得", "活着", "预后",
            "死亡", "overall survival", "survival", "mortality",
            "death risk", "prognosis", "live longer", "outcome",
        ]
        hba1c_terms = [
            "hba1c", "糖化血红蛋白", "糖化", "血糖控制",
            "降糖效果", "降糖疗效", "控糖效果",
            "glycemic control", "glycaemic control", "blood sugar control",
        ]
        bp_terms = [
            "血压控制率", "血压控制", "降压效果", "降压疗效",
            "血压达标", "控制血压", "blood pressure control",
            "bp control", "hypertension control", "lower blood pressure",
        ]

        if self._any(text, hba1c_terms):
            return (
                "HBA1C_FOLLOWUP",
                "continuous",
                ["Descriptive statistics", "ANOVA / Kruskal-Wallis"],
            )
        if self._any(text, bp_terms):
            return (
                "BP_CONTROL",
                "categorical",
                ["Contingency table", "Chi-square / Fisher"],
            )
        if self._any(text, survival_terms):
            return (
                "OS",
                "survival",
                ["Kaplan-Meier", "Log-rank", "Cox PH"],
            )

        oncology = {
            "NSCLC", "SCLC", "BREAST_CANCER", "COLORECTAL_CANCER",
            "GASTRIC_CANCER", "HCC", "PANCREATIC_CANCER",
            "PROSTATE_CANCER", "OVARIAN_CANCER", "CERVICAL_CANCER",
        }
        vague_compare = [
            "哪个好", "哪个更好", "效果更好", "疗效更好", "差异",
            "有没有差别", "比较", "对比", "which is better",
            "better outcome", "compare", "difference", "outcomes",
        ]
        if disease in oncology and self._any(text, vague_compare):
            return (
                "OS", "survival",
                ["Kaplan-Meier", "Log-rank", "Cox PH"],
            )
        if disease == "T2DM" and self._any(text, vague_compare):
            return (
                "HBA1C_FOLLOWUP", "continuous",
                ["Descriptive statistics", "ANOVA / Kruskal-Wallis"],
            )
        if disease == "HYPERTENSION" and self._any(text, vague_compare):
            return (
                "BP_CONTROL", "categorical",
                ["Contingency table", "Chi-square / Fisher"],
            )
        return None, None, []

    def plan(self, query: str, lang: str = "zh") -> ResearchPlan:
        text = normalize_text(query)
        disease_obj = resolve_disease(query)
        molecular_obj = resolve_molecular(query)

        disease = disease_obj["canonical"] if disease_obj else None
        diagnosis_code = disease_obj["code"] if disease_obj else None
        demo_supported = disease_obj.get("demo_supported") if disease_obj else None

        years = self._extract_years(query)
        group_by = self._infer_group(text)
        endpoint, endpoint_type, methods = self._infer_endpoint(text, disease)

        compare_terms = [
            "比较", "对比", "差异", "哪个好", "哪个更好", "有无差别",
            "compare", "versus", " vs ", "difference", "different", "better",
        ]
        treatment_terms = [
            "治疗", "方案", "药物", "用药",
            "therapy", "treatment", "regimen", "medication",
        ]
        if (
            group_by is None
            and self._any(text, compare_terms)
            and self._any(text, treatment_terms)
        ):
            group_by = "regimen"

        gene = molecular_obj["gene"] if molecular_obj else None
        gene_result = molecular_obj["result"] if molecular_obj else None

        explanations = []
        if lang == "en":
            if disease_obj:
                explanations.append(
                    f"Disease interpreted as {disease} ({diagnosis_code})."
                )
            if molecular_obj:
                explanations.append(
                    f"Molecular criterion interpreted as {gene}={gene_result}."
                )
            if years:
                explanations.append(f"Time window interpreted as the past {years} years.")
            if group_by:
                explanations.append("Comparison/grouping interpreted as treatment regimen.")
            if endpoint:
                explanations.append(f"Endpoint interpreted as {endpoint}.")
            if methods:
                explanations.append("Statistical route: " + " + ".join(methods))
        else:
            if disease_obj:
                explanations.append(f"疾病理解为：{disease}（{diagnosis_code}）。")
            if molecular_obj:
                explanations.append(f"分子条件理解为：{gene}={gene_result}。")
            if years:
                explanations.append(f"时间范围理解为：近{years}年。")
            if group_by:
                explanations.append("比较/分组意图理解为：按治疗方案分组。")
            if endpoint:
                explanations.append(f"研究终点理解为：{endpoint}。")
            if methods:
                explanations.append("自动统计路线：" + " + ".join(methods))

        executable = bool(
            diagnosis_code
            and demo_supported
            and endpoint in {"OS", "HBA1C_FOLLOWUP", "BP_CONTROL"}
        )

        warning = None
        if disease_obj and not demo_supported:
            warning = (
                "The disease was understood, but the current synthetic database "
                "does not yet contain matching cases."
                if lang == "en"
                else "系统已理解该疾病，但当前模拟数据库暂未生成对应病例。"
            )

        return ResearchPlan(
            original_query=query,
            years=years,
            disease=disease,
            diagnosis_code=diagnosis_code,
            gene=gene,
            gene_result=gene_result,
            group_by=group_by,
            endpoint=endpoint,
            endpoint_type=endpoint_type,
            analysis_methods=methods,
            covariates=["age", "sex"],
            explanation=explanations,
            demo_supported=demo_supported,
            confidence_notes=[],
            parser_mode="rule_fallback",
            parser_model=None,
            research_summary=query,
            inclusion_criteria=[],
            exclusion_criteria=[],
            assumptions=[],
            clarification_needed=False,
            clarification_question=None,
            confidence=None,
            executable=executable,
            execution_warning=warning,
        )


# =====================================================================
# Hybrid agent: LLM interpretation -> deterministic validator -> fallback
# =====================================================================
class ResearchAgent:
    """
    Hybrid medical-research intent agent.

    Privacy boundary:
    - Only the user's research QUESTION is sent to the LLM.
    - Patient-level cohort/dataframes are NOT sent to the LLM.
    - SQL is NOT generated by the LLM.
    - The deterministic query engine remains the only database execution layer.
    """

    SUPPORTED_ENDPOINTS = {
        "OS": (
            "survival",
            ["Kaplan-Meier", "Log-rank", "Cox PH"],
        ),
        "HBA1C_FOLLOWUP": (
            "continuous",
            ["Descriptive statistics", "ANOVA / Kruskal-Wallis"],
        ),
        "BP_CONTROL": (
            "categorical",
            ["Contingency table", "Chi-square / Fisher"],
        ),
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.rule_agent = RuleResearchAgent()

    @property
    def ai_enabled(self) -> bool:
        return bool(self.api_key)

    def _system_prompt(self, lang: str) -> str:
        return f"""
You are the semantic interpretation layer of a medical research analytics platform.

Your ONLY job is to understand a researcher's natural-language question and
return a structured research intent. Do NOT generate SQL. Do NOT analyze patient
data. Do NOT invent statistical results.

The user may write:
- Chinese, English, or mixed Chinese-English;
- colloquial or incomplete phrases;
- acronyms, synonyms, typos, shorthand, or clinician-style language;
- a full retrospective cohort question, or a loose idea such as
  "HER2+ breast cancer, which treatment has better prognosis?"

Interpret intent semantically rather than requiring any fixed command grammar.

Key interpretation principles:
1. Extract the disease/condition in the user's own wording and a common standard
   English name/acronym when possible.
2. Extract biomarkers/molecular status if present.
3. Understand flexible time phrases such as:
   最近三年, 3年内, 过去几年, last three years, within the past 5 years.
   If the user says "past few years" without a number, do NOT invent a number.
4. Infer treatment-regimen grouping when the user compares therapies, drugs,
   regimens, treatment approaches, or asks "which treatment is better."
5. Infer endpoints carefully:
   - oncology prognosis / living longer / survival / mortality -> OS
   - HbA1c / glycemic control / diabetes treatment effectiveness -> HBA1C_FOLLOWUP
   - hypertension control / BP target / pressure control -> BP_CONTROL
   - progression-free survival -> PFS
   - response/remission rate -> RESPONSE_RATE
   - readmission -> READMISSION
6. Statistical reasoning:
   - OS/PFS -> survival
   - HbA1c or numeric lab values -> continuous
   - control/response/readmission rates -> categorical or binary
7. Covariates: capture factors the user explicitly asks to adjust for, such as
   age, sex, stage, smoking, BMI, comorbidities. Do not invent covariates merely
   because they are common.
8. Be helpful rather than rigid. Only request clarification when different
   interpretations would materially change the research design. If a reasonable
   interpretation is strongly implied, infer it and record it in assumptions.
9. Do NOT invent hospital/database codes.
10. The requested UI language is {lang}; research_summary and clarification
    question should preferably use that language.

Return only the structured schema requested by the API.
""".strip()

    def _parse_with_llm(
        self,
        query: str,
        lang: str,
    ) -> LLMResearchExtraction:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        response = client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": self._system_prompt(lang),
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            text_format=LLMResearchExtraction,
            max_output_tokens=1800,
        )

        # Current OpenAI Python SDK exposes parsed content on output text items.
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            return parsed

        for output_item in response.output:
            if getattr(output_item, "type", None) != "message":
                continue
            for content_item in getattr(output_item, "content", []):
                item_parsed = getattr(content_item, "parsed", None)
                if item_parsed is not None:
                    return item_parsed

        raise RuntimeError("LLM returned no parsed ResearchPlan.")

    @staticmethod
    def _normalize_gene_status(
        gene: str | None,
        status: str | None,
    ) -> tuple[str | None, str | None]:
        if not gene:
            return None, None
        gene = gene.strip().upper()
        if gene in {"PDL1", "PD-L1"}:
            gene = "PD-L1"

        if not status or status == "UNKNOWN":
            return gene, None

        # Match DB demo conventions.
        if status in {"MUT", "POS", "NEG", "WT"}:
            return gene, status
        return gene, None

    def _merge_llm(
        self,
        query: str,
        lang: str,
        llm: LLMResearchExtraction,
    ) -> ResearchPlan:
        # ---------------- Disease validation ----------------
        disease_probe = " ".join(
            x for x in [llm.disease_text, llm.disease_canonical] if x
        ).strip()

        disease_obj = (
            resolve_disease(disease_probe)
            or resolve_disease(query)
        )

        if disease_obj:
            disease = disease_obj["canonical"]
            diagnosis_code = disease_obj["code"]
            demo_supported = disease_obj.get("demo_supported")
        else:
            # Preserve LLM understanding, but do not invent a DB code.
            disease = llm.disease_canonical or llm.disease_text
            diagnosis_code = None
            demo_supported = False if disease else None

        # ---------------- Molecular validation ----------------
        molecular_obj = resolve_molecular(query)
        if molecular_obj:
            gene = molecular_obj["gene"]
            gene_result = molecular_obj["result"]
        else:
            gene, gene_result = self._normalize_gene_status(
                llm.molecular_gene,
                llm.molecular_status,
            )

        # ---------------- Endpoint deterministic validation ----------------
        endpoint = None if llm.endpoint == "UNKNOWN" else llm.endpoint
        if endpoint in self.SUPPORTED_ENDPOINTS:
            endpoint_type, methods = self.SUPPORTED_ENDPOINTS[endpoint]
        else:
            endpoint_type = (
                None if llm.endpoint_type == "unknown" else llm.endpoint_type
            )
            methods = list(llm.requested_analysis)

        group_by = (
            None
            if llm.group_by in {"none", "unknown"}
            else llm.group_by
        )

        # Our current executable query layer supports regimen grouping.
        if group_by and group_by != "regimen":
            execution_warning = (
                f"Current demo understood grouping '{group_by}', "
                "but the executable demo currently supports treatment-regimen grouping."
                if lang == "en"
                else f"系统已理解分组变量“{group_by}”，但当前可执行演示暂只支持按治疗方案分组。"
            )
        else:
            execution_warning = None

        supported_endpoint = endpoint in self.SUPPORTED_ENDPOINTS
        executable = bool(
            diagnosis_code
            and demo_supported
            and supported_endpoint
            and (group_by in {None, "regimen"})
        )

        if disease and not demo_supported:
            execution_warning = (
                "The disease/condition was understood semantically, but the current "
                "synthetic demo database does not yet contain matching cases."
                if lang == "en"
                else "系统已理解该疾病/条件，但当前模拟数据库尚未生成对应病例，因此暂不能执行数据分析。"
            )
            executable = False

        if endpoint and not supported_endpoint:
            execution_warning = (
                f"The endpoint '{endpoint}' was understood, but the current statistics "
                "engine has not yet implemented that endpoint."
                if lang == "en"
                else f"系统已理解研究终点“{endpoint}”，但当前统计引擎尚未实现该终点的执行算法。"
            )
            executable = False

        if not diagnosis_code and disease:
            execution_warning = (
                "The disease was understood by the LLM, but it has not yet been mapped "
                "to the demo database semantic dictionary."
                if lang == "en"
                else "大模型已经理解疾病名称，但该疾病尚未映射到当前演示数据库语义字典。"
            )
            executable = False

        # ---------------- Clarification policy ----------------
        clarification_needed = bool(llm.clarification_needed)
        clarification_question = llm.clarification_question

        # Don't ask needless clarification if we have enough to execute.
        if executable:
            clarification_needed = False
            clarification_question = None

        # Essential fields truly absent -> ask one concise question.
        if not disease and not clarification_needed:
            clarification_needed = True
            clarification_question = (
                "Which disease or patient population would you like to study?"
                if lang == "en"
                else "你希望研究哪一种疾病或患者人群？"
            )

        if not endpoint and not clarification_needed:
            clarification_needed = True
            clarification_question = (
                "What outcome would you like to compare (for example survival, "
                "HbA1c, blood-pressure control, response rate, or another endpoint)?"
                if lang == "en"
                else "你最希望比较什么结局？例如生存期、HbA1c、血压控制率、治疗响应率或其他指标。"
            )

        explanations = []
        if lang == "en":
            explanations.append(
                f"AI semantic parser: {llm.research_summary}"
            )
            if disease:
                explanations.append(
                    f"Disease/condition interpreted as {disease}"
                    + (f" ({diagnosis_code})" if diagnosis_code else "")
                    + "."
                )
            if gene:
                explanations.append(
                    f"Molecular criterion interpreted as {gene}"
                    + (f"={gene_result}" if gene_result else "")
                    + "."
                )
            if llm.years:
                explanations.append(
                    f"Retrospective window interpreted as the past {llm.years} years."
                )
            if group_by:
                explanations.append(
                    f"Grouping interpreted as {group_by}."
                )
            if endpoint:
                explanations.append(
                    f"Endpoint interpreted as {endpoint} ({endpoint_type or 'unknown type'})."
                )
            if methods:
                explanations.append(
                    "Validated statistical route: " + " + ".join(methods)
                )
        else:
            explanations.append(
                f"AI语义理解：{llm.research_summary}"
            )
            if disease:
                explanations.append(
                    f"疾病/研究人群理解为：{disease}"
                    + (f"（{diagnosis_code}）" if diagnosis_code else "")
                    + "。"
                )
            if gene:
                explanations.append(
                    f"分子条件理解为：{gene}"
                    + (f"={gene_result}" if gene_result else "")
                    + "。"
                )
            if llm.years:
                explanations.append(
                    f"回顾时间范围理解为：近{llm.years}年。"
                )
            if group_by:
                explanations.append(
                    f"分组意图理解为：{group_by}。"
                )
            if endpoint:
                explanations.append(
                    f"研究终点理解为：{endpoint}（{endpoint_type or '类型待确认'}）。"
                )
            if methods:
                explanations.append(
                    "经确定性校验后的统计路线：" + " + ".join(methods)
                )

        notes = []
        if execution_warning:
            notes.append("execution_limited_by_demo")
        if llm.assumptions:
            notes.append("llm_made_explicit_assumptions")

        return ResearchPlan(
            original_query=query,
            years=llm.years,
            disease=disease,
            diagnosis_code=diagnosis_code,
            gene=gene,
            gene_result=gene_result,
            group_by=group_by,
            endpoint=endpoint,
            endpoint_type=endpoint_type,
            analysis_methods=methods,
            covariates=list(llm.covariates),
            explanation=explanations,
            demo_supported=demo_supported,
            confidence_notes=notes,
            parser_mode="llm_structured_output",
            parser_model=self.model,
            research_summary=llm.research_summary,
            inclusion_criteria=list(llm.inclusion_criteria),
            exclusion_criteria=list(llm.exclusion_criteria),
            assumptions=list(llm.assumptions),
            clarification_needed=clarification_needed,
            clarification_question=clarification_question,
            confidence=float(llm.confidence),
            executable=executable,
            execution_warning=execution_warning,
        )

    def plan(self, query: str, lang: str = "zh") -> ResearchPlan:
        if not self.ai_enabled:
            plan = self.rule_agent.plan(query, lang)
            plan.parser_mode = "rule_fallback_no_api_key"
            plan.execution_warning = plan.execution_warning
            return plan

        try:
            llm = self._parse_with_llm(query, lang)
            return self._merge_llm(query, lang, llm)
        except Exception as exc:
            # High availability: an API outage or schema issue must not kill the app.
            plan = self.rule_agent.plan(query, lang)
            plan.parser_mode = "rule_fallback_api_error"
            plan.parser_model = self.model
            plan.confidence_notes = list(plan.confidence_notes or []) + [
                f"llm_error:{type(exc).__name__}"
            ]
            fallback_message = (
                "AI semantic parsing was temporarily unavailable, so the platform "
                "automatically used the deterministic fallback parser."
                if lang == "en"
                else "AI语义解析暂时不可用，平台已自动切换到确定性规则解析作为兜底。"
            )
            plan.explanation = [fallback_message] + list(plan.explanation)
            return plan

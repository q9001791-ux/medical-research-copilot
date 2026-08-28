from pathlib import Path
import os
import base64
import html
import pandas as pd
import streamlit as st

from i18n import tr
from research_agent import ResearchAgent
from query_engine import QueryEngine
from stats_engine import StatsEngine
from template_store import TemplateStore
from custom_data_engine import CustomDataEngine, METHODS, method_label, PLATFORM_DATASETS

# -------------------------------------------------------------------
# App bootstrap
# -------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parent / "data" / "medical_demo.db"
if not DB_PATH.exists():
    from generate_demo_data import main as generate_data
    generate_data()

st.set_page_config(
    page_title="海研分析 · Medical Research Analytics Platform",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "page" not in st.session_state:
    st.session_state.page = "home"

# -------------------------------------------------------------------
# UI copy
# -------------------------------------------------------------------
COPY = {
    "zh": {
        "brand": "海研分析",
        "brand_sub": "医疗科研智能分析平台",
        "home": "首页",
        "analysis": "科研分析",
        "templates": "科研模板",
        "about": "平台说明",
        "hero_badge": "AI 驱动的临床科研分析平台",
        "hero_line1": "让复杂医疗数据",
        "hero_line2": "直接回答科研问题",
        "hero_desc": "从自然语言研究问题出发，自动完成医学语义解析、病例队列构建、统计方法选择、科研图表与可复用分析模板。",
        "start": "立即开始分析",
        "view_examples": "查看科研场景",
        "hero_stat_1": "5 类",
        "hero_stat_1_label": "模拟科研场景",
        "hero_stat_2": "3 套",
        "hero_stat_2_label": "自动统计路线",
        "hero_stat_3": "3,000+",
        "hero_stat_3_label": "模拟脱敏病例",
        "ability_title": "核心能力，从问题到证据",
        "ability_desc": "不是让科研人员学习数据库和统计代码，而是把复杂技术流程压缩成一条可解释、可复用的科研路径。",
        "step_1_title": "自然语言理解",
        "step_1_desc": "识别疾病、分子标志物、时间窗口、分组变量和研究终点。",
        "step_1_demo": "“近三年 EGFR 突变 NSCLC，不同治疗方案生存期”",
        "step_2_title": "智能病例队列",
        "step_2_desc": "跨诊断、基因、治疗、检验、随访等表进行受控多表关联。",
        "step_2_demo": "Diagnosis + Molecular + Treatment + Follow-up",
        "step_3_title": "统计学决策",
        "step_3_desc": "根据结局类型自动切换生存分析、连续变量比较或分类变量检验。",
        "step_3_demo": "KM / Log-rank / Cox · ANOVA · Chi-square",
        "step_4_title": "科研资产沉淀",
        "step_4_desc": "将一次性筛选条件、终点定义、统计方法与 SQL 路径保存成模板。",
        "step_4_demo": "ResearchPlan → Reusable Template",
        "scenes_title": "内置科研演示场景",
        "scenes_desc": "这些并不是固定答案，而是用于展示不同医学数据结构和统计路线的模拟研究。",
        "scene_lung": "肺癌精准治疗",
        "scene_lung_desc": "EGFR 突变 NSCLC · 不同方案总生存",
        "scene_breast": "乳腺癌靶向治疗",
        "scene_breast_desc": "HER2 阳性乳腺癌 · 不同方案总生存",
        "scene_crc": "结直肠癌分子分型",
        "scene_crc_desc": "KRAS 突变结直肠癌 · 不同方案总生存",
        "scene_dm": "糖尿病疗效比较",
        "scene_dm_desc": "不同治疗方案 · 随访 HbA1c",
        "scene_htn": "高血压控制评价",
        "scene_htn_desc": "不同治疗方案 · 血压控制率",
        "workspace_badge": "RESEARCH WORKSPACE",
        "workspace_title": "新建科研分析",
        "workspace_desc": "选择一个示例或直接输入研究问题。系统将按纵向步骤展示每一个推理与执行阶段。",
        "example": "选择示例科研场景",
        "question": "研究问题",
        "question_hint": "你可以修改示例中的疾病、时间窗口或比较目标。",
        "run": "生成科研分析",
        "load_template": "加载科研模板",
        "none": "不加载",
        "stage1": "科研逻辑解析",
        "stage2": "病例队列构建",
        "stage3": "自动统计分析",
        "stage4": "科研资产沉淀",
        "stage1_desc": "将自然语言转化为结构化 ResearchPlan",
        "stage2_desc": "通过受控 SQL 形成可分析病例队列",
        "stage3_desc": "根据结局数据类型自动选择统计方法",
        "stage4_desc": "保存分析路径，形成可复用科研模板",
        "structured": "查看结构化 ResearchPlan",
        "sql": "查看受控 SQL",
        "included": "纳入病例",
        "groups": "治疗分组",
        "endpoint": "研究终点",
        "method": "统计方法",
        "p": "P 值",
        "data_preview": "病例数据预览",
        "summary": "分组统计摘要",
        "conclusion": "智能统计结论",
        "cox": "Cox 比例风险回归",
        "download": "下载分析数据 CSV",
        "template_name": "模板名称",
        "save": "保存为科研模板",
        "saved": "科研模板已保存",
        "failed": "分析失败",
        "empty": "当前条件下没有可分析病例。",
        "template_center": "科研模板中心",
        "template_center_desc": "把已经验证过的病例定义、终点和统计路径沉淀为可复用的数据资产。",
        "no_templates": "当前还没有保存的科研模板。",
        "created": "创建时间",
        "original_q": "原始研究问题",
        "about_title": "平台设计逻辑",
        "about_desc": "医研智析把大模型/语义理解放在“理解层”，把数据库查询和统计计算放在“受控执行层”，避免让模型直接拥有任意 SQL 权限。",
        "safety_title": "数据安全边界",
        "safety_desc": "当前公网版本仅使用程序生成的模拟脱敏数据。真实医院部署需要院内数据仓库、身份认证、项目授权、审计、伦理审批以及行列级访问控制。",
        "public_demo": "PUBLIC RESEARCH DEMO",
        "lang": "语言",
        "template_note": "公网演示环境中的本地文件型模板不保证跨服务器重启永久保存。",
        "visual_nl": "自然语言 → ResearchPlan",
        "visual_semantic_done": "医学语义解析完成",
        "visual_cohort": "病例队列构建",
        "visual_eligible": "例符合条件患者",
        "visual_km": "Kaplan-Meier 生存分析",
        "visual_adjusted": "校正后模型",
        "visual_result": "科研统计结果",
        "ai_mode": "语义理解模式",
        "ai_llm": "LLM结构化语义解析 + 确定性校验",
        "ai_rule": "规则兜底模式（未配置AI密钥）",
        "ai_fallback": "AI异常，已自动启用规则兜底",
        "ai_model": "解析模型",
        "clarification": "需要补充一点研究信息",
        "understood_but_not_executable": "已理解研究问题，但当前演示数据/算法暂不能直接执行",
        "assumptions_title": "AI采用的解释/假设",
        "settings": "设置",
        "settings_title": "平台设置",
        "settings_desc": "管理当前访问身份、科研模板、语言、API配置与平台偏好。",
        "account_section": "账户与访问",
        "guest_mode": "游客模式",
        "guest_desc": "当前为演示版访问模式，不需要真实账号即可使用科研分析功能。",
        "login": "登录",
        "logged_guest": "目前已使用游客模式登录",
        "logout_guest": "退出游客模式",
        "login_note": "演示版暂不接入真实用户认证与账号数据库。",
        "template_manage": "管理我的科研模板",
        "template_manage_desc": "查看、重命名或删除当前环境中保存的科研分析模板。",
        "rename": "重命名",
        "delete": "删除",
        "new_name": "新模板名称",
        "confirm_delete": "确认删除",
        "template_deleted": "模板已删除",
        "template_renamed": "模板已重命名",
        "language_section": "语言与显示",
        "language_desc": "平台语言统一在此设置。支持中文与 English，切换后全站界面与科研语义说明同步更新。",
        "api_section": "API 配置",
        "api_desc": "预留大模型 API 配置入口。当前无需配置即可使用规则解析与演示功能。",
        "api_status": "API 状态",
        "api_not_configured": "未配置（当前使用规则/本地解析能力）",
        "api_configured": "已检测到配置",
        "api_provider": "模型服务",
        "api_model": "模型名称",
        "api_key_placeholder": "API Key（演示占位，不会保存）",
        "api_save_demo": "保存配置（演示）",
        "api_demo_saved": "已记录为界面演示状态，本版本不会把 API Key 写入磁盘。",
        "privacy_section": "数据与隐私",
        "privacy_desc": "公网演示仅使用程序生成的模拟脱敏数据；真实医院部署时需接入院内身份认证、项目授权、审计和数据访问控制。",
        "privacy_point1": "患者级数据不用于游客身份识别",
        "privacy_point2": "当前示例数据库为合成数据，不包含真实患者信息",
        "privacy_point3": "真实环境建议采用医院内网与项目级权限控制",
        "system_section": "系统信息",
        "version": "版本",
        "version_value": "Haiyan Analysis Demo · V4",
        "runtime": "运行模式",
        "runtime_value": "Streamlit Web Application",
        "data_mode": "数据模式",
        "data_mode_value": "Synthetic Research Database",
        "danger_section": "本地数据管理",
        "danger_desc": "这里仅管理平台内部模板，不会删除你的 Python 环境或项目文件。",
        "no_saved_templates": "当前没有已保存的科研模板。",



        "expand_details": "放大查看",
        "collapse_details": "收起详情",
        "expand_data": "放大数据表",
        "collapse_data": "收起数据表",
        "expand_chart": "放大分析图",
        "collapse_chart": "恢复缩略图",
        "export_chart": "导出分析图 PNG",
        "export_summary": "导出统计摘要 CSV",
        "result_focus": "核心分析结果",
        "result_focus_desc": "系统已完成队列构建与统计计算，以下区域优先呈现最终科研结果。",
        "compact_hint": "默认缩略显示，点击放大可查看完整内容。",
        "rows_preview": "缩略预览",
        "data_source": "数据来源",
        "source_demo": "平台示例数据库",
        "source_custom": "导入 / 粘贴我的数据",
        "import_stage": "00 · 导入研究数据",
        "import_desc": "上传 CSV/XLS/XLSX，直接粘贴 CSV/TSV，或把表格内容连同研究问题一起输入。",
        "upload_data": "上传数据文件",
        "paste_data": "粘贴表格数据",
        "paste_placeholder": "例如：\ngroup,outcome,age\nA,7.2,61\nB,6.5,58",
        "format_rules": "数据模板与格式要求",
        "format_rule_1": "第一行为变量名，变量名必须非空且建议唯一；不要使用合并单元格。",
        "format_rule_2": "一行代表一个观察对象/患者，一列代表一个变量。",
        "format_rule_3": "连续变量只填数字，不要把单位写入单元格；缺失值留空或使用 NA。",
        "format_rule_4": "二分类变量建议使用 0/1；生存分析 event 建议 1=事件发生、0=删失。",
        "format_rule_5": "日期推荐 YYYY-MM-DD；分类标签前后保持一致。",
        "format_rule_6": "公网演示不要上传姓名、身份证、住院号、电话等可识别真实患者的信息。",
        "supported_files": "支持格式：CSV、XLS、XLSX；演示版建议 ≤20MB，≤100,000行。",
        "download_template": "下载数据模板",
        "template_group_numeric": "两/多组连续变量模板",
        "template_survival": "生存分析模板",
        "template_binary": "分类结局模板",
        "data_loaded": "数据已载入",
        "rows": "行数",
        "columns": "变量数",
        "missing_rate": "缺失率",
        "numeric_count": "连续/数值变量",
        "categorical_count": "分类变量",
        "custom_question_hint": "例如：比较 treatment 两组的 outcome 是否有差异，使用 Mann-Whitney；或用 time/event 按 group 做 Kaplan-Meier。也可以把CSV/TSV表格直接粘到这个研究问题框中。",
        "analysis_method": "统计分析方法",
        "auto_recommend": "系统推荐",
        "group_variable": "分组变量",
        "outcome_variable": "结局 / 因变量",
        "x_variable": "变量 X / 治疗前",
        "y_variable": "变量 Y / 治疗后",
        "time_variable": "时间变量",
        "event_variable": "事件变量（1=事件，0=删失）",
        "predictors": "自变量 / 协变量",
        "variable_config": "变量角色确认",
        "custom_run": "生成自助分析报告",
        "custom_result": "自助数据分析结果",
        "report_export": "导出完整分析报告 HTML",
        "data_quality": "数据质量概览",
        "embedded_data_detected": "已从研究问题中识别出表格数据。",
        "need_custom_data": "请先上传、粘贴数据，或在研究问题中附上 CSV/TSV 表格。",
        "result_integrity": "科研完整性说明：你可以写希望回答的问题，但平台会依据实际数据生成结论，不会为了符合预设结论而修改统计结果。",
        "preview_format": "模板预览",
        "no_group": "不分组",
        "instruction_stage": "01 · 输入分析指令",
        "instruction_title": "告诉海研分析你想回答什么问题",
        "instruction_desc": "用自然语言描述研究目的、需要比较的变量、希望使用的统计方法或需要校正的因素。无需固定句式。",
        "instruction_label": "分析指令 / 研究问题",
        "instruction_example_title": "可以这样写",
        "instruction_example_1": "比较 treatment A/B 两组的 outcome 是否有差异，使用 Mann-Whitney U 检验。",
        "instruction_example_2": "按 group 比较 time/event 的生存情况，生成 Kaplan-Meier 曲线并做 Log-rank 检验。",
        "instruction_example_3": "分析 age 和 score 的相关性，使用 Spearman；同时给出相关系数和 P 值。",
        "instruction_example_4": "以 outcome 为二分类结局，使用 age、sex、BMI 做 Logistic 回归。",
        "instruction_empty_hint": "如果暂时不填写，系统仍可根据数据结构进行基础推荐；填写后推荐会更准确。",
        "unified_source_title": "选择研究数据",
        "unified_source_desc": "平台数据库、上传文件和粘贴数据使用同一套分析流程。",
        "platform_dataset": "平台科研数据库",
        "choose_platform_dataset": "选择平台数据集",
        "my_data": "导入自己的数据",
        "current_source": "当前数据来源",
        "source_platform": "平台数据库",
        "source_upload": "上传文件",
        "source_paste": "粘贴数据",
        "source_embedded": "指令内嵌数据",
        "available_fields": "可分析字段",
        "data_preview_title": "研究数据预览",
        "expand_preview": "展开数据",
        "collapse_preview": "收起数据",
        "step_method": "统计策略",
        "step_variables": "变量配置",
        "recommended_method": "推荐方法",
        "run_analysis_now": "开始计算并生成报告",
        "report_center": "科研分析结果",
        "report_center_desc": "以下结论由当前数据与统计方法直接计算生成。",
        "import_dialog_title": "导入研究数据",
        "import_project_name": "项目名称",
        "import_project_background": "项目背景",
        "import_project_summary": "项目概要",
        "import_project_name_ph": "例如：乳腺癌术后疗效比较",
        "import_background_ph": "简要说明研究背景、数据来源或研究目的（可选）",
        "import_summary_ph": "简要说明主要变量、研究设计或希望分析的内容（可选）",
        "open_import_dialog": "导入我的数据",
        "reimport_data": "重新导入",
        "clear_import": "移除数据",
        "confirm_import": "确认导入",
        "cancel_import": "取消",
        "import_success": "研究数据已成功导入",
        "file_required": "请上传文件或粘贴表格数据后再确认。",
        "project_name_required": "请填写项目名称。",
        "template_preview": "数据格式示意",
        "template_general": "通用分组",
        "template_survival_short": "生存分析",
        "template_binary_short": "分类结局",
        "template_instruction": "第一行为变量名，从第二行开始为数据。变量名不要合并单元格，也不要为空。",
        "imported_project": "已导入项目",
        "use_platform_dataset": "使用此平台数据",
        "platform_active": "当前使用平台数据",
        "import_active": "当前使用导入数据",
        "no_import_yet": "尚未导入自己的研究数据",
        "import_card_desc": "从本地上传 CSV / XLS / XLSX，或粘贴 CSV / TSV。导入过程将在独立窗口中完成。",
        "platform_card_desc": "选择平台内置的模拟科研数据，再自由输入你自己的研究问题和统计方法。",





    },
    "en": {
        "brand": "Haiyan Analytics",
        "brand_sub": "医疗科研智能分析平台",
        "home": "Home",
        "analysis": "Research",
        "templates": "Templates",
        "about": "About",
        "hero_badge": "AI-DRIVEN CLINICAL RESEARCH ANALYTICS",
        "hero_line1": "Turn complex medical data",
        "hero_line2": "into research evidence",
        "hero_desc": "Start with a natural-language research question and automatically generate medical semantic parsing, cohorts, statistical methods, research charts and reusable analysis templates.",
        "start": "Start analysis",
        "view_examples": "Explore scenarios",
        "hero_stat_1": "5",
        "hero_stat_1_label": "Research scenarios",
        "hero_stat_2": "3",
        "hero_stat_2_label": "Statistical routes",
        "hero_stat_3": "3,000+",
        "hero_stat_3_label": "Synthetic patients",
        "ability_title": "From question to evidence",
        "ability_desc": "Researchers should not need to master database schemas and statistical code. The platform compresses those technical steps into an explainable and reusable workflow.",
        "step_1_title": "Natural-language understanding",
        "step_1_desc": "Identify disease, molecular markers, time windows, grouping variables and endpoints.",
        "step_1_demo": "“EGFR-mutant NSCLC in the past 3 years, compare survival by regimen”",
        "step_2_title": "Intelligent cohort building",
        "step_2_desc": "Controlled joins across diagnosis, molecular, treatment, laboratory and follow-up data.",
        "step_2_demo": "Diagnosis + Molecular + Treatment + Follow-up",
        "step_3_title": "Statistical decision engine",
        "step_3_desc": "Automatically switch between survival, continuous and categorical analyses based on endpoint type.",
        "step_3_demo": "KM / Log-rank / Cox · ANOVA · Chi-square",
        "step_4_title": "Research asset reuse",
        "step_4_desc": "Save cohort criteria, endpoints, methods and query paths as reusable templates.",
        "step_4_demo": "ResearchPlan → Reusable Template",
        "scenes_title": "Built-in research scenarios",
        "scenes_desc": "These are not fixed answers. They demonstrate different clinical data structures and statistical routes.",
        "scene_lung": "Precision lung cancer",
        "scene_lung_desc": "EGFR-mutant NSCLC · Overall survival",
        "scene_breast": "Breast cancer targeted therapy",
        "scene_breast_desc": "HER2-positive breast cancer · Overall survival",
        "scene_crc": "Colorectal molecular subtype",
        "scene_crc_desc": "KRAS-mutant colorectal cancer · Overall survival",
        "scene_dm": "Diabetes effectiveness",
        "scene_dm_desc": "Treatment regimens · Follow-up HbA1c",
        "scene_htn": "Hypertension control",
        "scene_htn_desc": "Treatment regimens · BP control rate",
        "workspace_badge": "RESEARCH WORKSPACE",
        "workspace_title": "Create a research analysis",
        "workspace_desc": "Choose an example or enter your own question. Every reasoning and execution step is shown vertically.",
        "example": "Select research scenario",
        "question": "Research question",
        "question_hint": "You may change the disease, time window or comparison target.",
        "run": "Generate research analysis",
        "load_template": "Load research template",
        "none": "None",
        "stage1": "Research logic parsing",
        "stage2": "Cohort construction",
        "stage3": "Automated statistical analysis",
        "stage4": "Research asset reuse",
        "stage1_desc": "Convert natural language into a structured ResearchPlan",
        "stage2_desc": "Build an analyzable cohort through controlled SQL",
        "stage3_desc": "Select statistics automatically based on endpoint type",
        "stage4_desc": "Save the analysis path as a reusable research template",
        "structured": "View structured ResearchPlan",
        "sql": "View controlled SQL",
        "included": "Patients",
        "groups": "Groups",
        "endpoint": "Endpoint",
        "method": "Method",
        "p": "P value",
        "data_preview": "Cohort data preview",
        "summary": "Group summary",
        "conclusion": "Statistical interpretation",
        "cox": "Cox proportional hazards regression",
        "download": "Download analysis data CSV",
        "template_name": "Template name",
        "save": "Save research template",
        "saved": "Research template saved",
        "failed": "Analysis failed",
        "empty": "No analyzable patients were found.",
        "template_center": "Research Template Center",
        "template_center_desc": "Turn validated cohort definitions, endpoints and statistical paths into reusable research assets.",
        "no_templates": "No saved research templates yet.",
        "created": "Created",
        "original_q": "Original question",
        "about_title": "Platform design logic",
        "about_desc": "The semantic/AI layer interprets research intent, while database and statistics live in a controlled execution layer. The model does not receive arbitrary SQL privileges.",
        "safety_title": "Data safety boundary",
        "safety_desc": "The public demo uses only programmatically generated synthetic data. Real hospital deployment requires an internal data warehouse, authentication, project authorization, auditing, ethics approval and row/column-level access control.",
        "public_demo": "PUBLIC RESEARCH DEMO",
        "lang": "Language",
        "template_note": "File-based templates in the public demo are not guaranteed to persist across cloud server restarts.",
        "visual_nl": "Natural language → ResearchPlan",
        "visual_semantic_done": "Semantic parsing completed",
        "visual_cohort": "Cohort discovery",
        "visual_eligible": "eligible patients",
        "visual_km": "Kaplan-Meier survival",
        "visual_adjusted": "Adjusted model",
        "visual_result": "Research result",
        "ai_mode": "Semantic understanding mode",
        "ai_llm": "LLM structured parsing + deterministic validation",
        "ai_rule": "Rule fallback mode (AI key not configured)",
        "ai_fallback": "AI unavailable; deterministic fallback activated",
        "ai_model": "Parser model",
        "clarification": "A little more research information is needed",
        "understood_but_not_executable": "The question was understood, but the current demo data/algorithm cannot execute it yet",
        "assumptions_title": "AI interpretation / assumptions",
        "settings": "Settings",
        "settings_title": "Platform Settings",
        "settings_desc": "Manage access identity, research templates, language, API placeholders and platform preferences.",
        "account_section": "Account & Access",
        "guest_mode": "Guest mode",
        "guest_desc": "The demo can be used without a real account or authentication backend.",
        "login": "Log in",
        "logged_guest": "Currently logged in using guest mode",
        "logout_guest": "Exit guest mode",
        "login_note": "The demo does not connect to a real authentication or account database.",
        "template_manage": "Manage my research templates",
        "template_manage_desc": "View, rename or delete research analysis templates saved in the current environment.",
        "rename": "Rename",
        "delete": "Delete",
        "new_name": "New template name",
        "confirm_delete": "Confirm delete",
        "template_deleted": "Template deleted",
        "template_renamed": "Template renamed",
        "language_section": "Language & Display",
        "language_desc": "Language is managed here. Switching Chinese / English updates the full interface and research semantic explanations.",
        "api_section": "API Configuration",
        "api_desc": "Reserved model API settings. No API is required for the current rule-based/demo functionality.",
        "api_status": "API status",
        "api_not_configured": "Not configured (using local/rule parsing)",
        "api_configured": "Configuration detected",
        "api_provider": "Model provider",
        "api_model": "Model name",
        "api_key_placeholder": "API Key (demo placeholder; not persisted)",
        "api_save_demo": "Save configuration (demo)",
        "api_demo_saved": "Saved only as UI demo state. The API key is not written to disk.",
        "privacy_section": "Data & Privacy",
        "privacy_desc": "The public demo uses only synthetic de-identified data. Real hospital deployment requires internal authentication, project authorization, auditing and access control.",
        "privacy_point1": "Patient-level data is not used for guest identity",
        "privacy_point2": "The demo database is synthetic and contains no real patient records",
        "privacy_point3": "Production should use hospital-internal project-level access control",
        "system_section": "System Information",
        "version": "Version",
        "version_value": "Haiyan Analysis Demo · V4",
        "runtime": "Runtime",
        "runtime_value": "Streamlit Web Application",
        "data_mode": "Data mode",
        "data_mode_value": "Synthetic Research Database",
        "danger_section": "Local Data Management",
        "danger_desc": "This area manages platform templates only. It does not delete Python or your project files.",
        "no_saved_templates": "No saved research templates.",



        "expand_details": "Expand details",
        "collapse_details": "Collapse",
        "expand_data": "Expand data table",
        "collapse_data": "Collapse data table",
        "expand_chart": "Enlarge chart",
        "collapse_chart": "Restore compact chart",
        "export_chart": "Export chart PNG",
        "export_summary": "Export summary CSV",
        "result_focus": "Primary analysis result",
        "result_focus_desc": "Cohort construction and statistical computation are complete. The final research result is prioritized below.",
        "compact_hint": "Compact by default. Expand when detailed inspection is needed.",
        "rows_preview": "Compact preview",
        "data_source": "Data source",
        "source_demo": "Built-in demo database",
        "source_custom": "Import / paste my data",
        "import_stage": "00 · Import research data",
        "import_desc": "Upload CSV/XLS/XLSX, paste CSV/TSV directly, or include a delimited table inside the research question.",
        "upload_data": "Upload data file",
        "paste_data": "Paste tabular data",
        "paste_placeholder": "Example:\ngroup,outcome,age\nA,7.2,61\nB,6.5,58",
        "format_rules": "Data template & format requirements",
        "format_rule_1": "The first row must contain non-empty variable names; use unique names and no merged cells.",
        "format_rule_2": "One row = one observation/patient; one column = one variable.",
        "format_rule_3": "Numeric variables should contain numbers only; keep units out of cells. Leave missing values blank or use NA.",
        "format_rule_4": "Binary variables should preferably use 0/1; for survival analysis, event should preferably be 1=event and 0=censored.",
        "format_rule_5": "Use YYYY-MM-DD for dates and keep categorical labels consistent.",
        "format_rule_6": "Do not upload identifiable real-patient data to the public demo (names, IDs, phone numbers, etc.).",
        "supported_files": "Supported: CSV, XLS, XLSX. Demo recommendation: ≤20MB and ≤100,000 rows.",
        "download_template": "Download data template",
        "template_group_numeric": "Grouped numeric template",
        "template_survival": "Survival template",
        "template_binary": "Categorical outcome template",
        "data_loaded": "Data loaded",
        "rows": "Rows",
        "columns": "Variables",
        "missing_rate": "Missing rate",
        "numeric_count": "Numeric variables",
        "categorical_count": "Categorical variables",
        "custom_question_hint": "Example: compare outcome across treatment groups using Mann-Whitney; or use time/event grouped by group for Kaplan-Meier. CSV/TSV data may also be pasted directly into this question box.",
        "analysis_method": "Statistical method",
        "auto_recommend": "Recommended",
        "group_variable": "Group variable",
        "outcome_variable": "Outcome / dependent variable",
        "x_variable": "Variable X / pre-treatment",
        "y_variable": "Variable Y / post-treatment",
        "time_variable": "Time variable",
        "event_variable": "Event variable (1=event, 0=censored)",
        "predictors": "Predictors / covariates",
        "variable_config": "Confirm variable roles",
        "custom_run": "Generate self-service analysis report",
        "custom_result": "Self-service analysis result",
        "report_export": "Export full HTML analysis report",
        "data_quality": "Data quality overview",
        "embedded_data_detected": "Tabular data was detected inside the research question.",
        "need_custom_data": "Upload or paste data first, or include a CSV/TSV table in the research question.",
        "result_integrity": "Research integrity: you may state the question you hope to answer, but conclusions are computed from the actual data and will not be altered to match a preferred result.",
        "preview_format": "Template preview",
        "no_group": "No grouping",
        "instruction_stage": "01 · Enter analysis instruction",
        "instruction_title": "Tell Haiyan Analysis what you want to answer",
        "instruction_desc": "Describe the research objective, variables to compare, preferred statistical method, and covariates in natural language. No fixed command grammar is required.",
        "instruction_label": "Analysis instruction / research question",
        "instruction_example_title": "Examples",
        "instruction_example_1": "Compare outcome between treatment A and B using the Mann-Whitney U test.",
        "instruction_example_2": "Compare survival by group using time/event, generate Kaplan-Meier curves and perform a Log-rank test.",
        "instruction_example_3": "Assess the correlation between age and score using Spearman and report the coefficient and P value.",
        "instruction_example_4": "Use outcome as a binary endpoint and run logistic regression with age, sex and BMI.",
        "instruction_empty_hint": "If left blank, the platform can still make a basic recommendation from the data structure; adding an instruction improves the recommendation.",
        "unified_source_title": "Choose research data",
        "unified_source_desc": "Platform datasets, file uploads and pasted data share one analysis workflow.",
        "platform_dataset": "Platform research database",
        "choose_platform_dataset": "Select platform dataset",
        "my_data": "Import my own data",
        "current_source": "Current data source",
        "source_platform": "Platform database",
        "source_upload": "Uploaded file",
        "source_paste": "Pasted data",
        "source_embedded": "Data embedded in instruction",
        "available_fields": "Available variables",
        "data_preview_title": "Research data preview",
        "expand_preview": "Expand data",
        "collapse_preview": "Collapse data",
        "step_method": "Statistical strategy",
        "step_variables": "Variable configuration",
        "recommended_method": "Recommended method",
        "run_analysis_now": "Run analysis and generate report",
        "report_center": "Research analysis result",
        "report_center_desc": "The following findings are computed directly from the current data and selected statistical method.",
        "import_dialog_title": "Import Research Data",
        "import_project_name": "Project name",
        "import_project_background": "Project background",
        "import_project_summary": "Project summary",
        "import_project_name_ph": "Example: Postoperative breast cancer effectiveness comparison",
        "import_background_ph": "Briefly describe the study background, data source or objective (optional)",
        "import_summary_ph": "Briefly describe key variables, design or intended analysis (optional)",
        "open_import_dialog": "Import my data",
        "reimport_data": "Re-import",
        "clear_import": "Remove data",
        "confirm_import": "Confirm import",
        "cancel_import": "Cancel",
        "import_success": "Research data imported successfully",
        "file_required": "Upload a file or paste tabular data before confirming.",
        "project_name_required": "Enter a project name.",
        "template_preview": "Data format example",
        "template_general": "Grouped numeric",
        "template_survival_short": "Survival",
        "template_binary_short": "Categorical outcome",
        "template_instruction": "The first row contains variable names and data begin on row two. Do not merge header cells or leave variable names blank.",
        "imported_project": "Imported project",
        "use_platform_dataset": "Use this platform dataset",
        "platform_active": "Platform dataset active",
        "import_active": "Imported data active",
        "no_import_yet": "No personal research data imported yet",
        "import_card_desc": "Upload CSV / XLS / XLSX or paste CSV / TSV. Import is completed in a dedicated modal window.",
        "platform_card_desc": "Choose a built-in synthetic research dataset, then ask your own research question and select your preferred statistical method.",





    },
}

EXAMPLES = {
    "zh": {
        "肺癌：EGFR突变患者生存分析": "筛选出近三年所有非小细胞肺癌且EGFR突变的患者，对比不同治疗方案的生存期",
        "乳腺癌：HER2阳性患者生存分析": "筛选近四年HER2阳性乳腺癌患者，对比不同治疗方案的生存期",
        "结直肠癌：KRAS突变患者生存分析": "筛选近三年KRAS突变结直肠癌患者，对比不同治疗方案的生存期",
        "糖尿病：不同方案HbA1c比较": "筛选近三年2型糖尿病患者，比较不同治疗方案治疗后的HbA1c水平",
        "高血压：不同方案血压控制率": "筛选近三年高血压患者，比较不同治疗方案的血压控制率",
    },
    "en": {
        "Lung cancer: EGFR-mutant survival": "Identify patients with NSCLC and EGFR mutations in the past 3 years and compare overall survival across treatment regimens",
        "Breast cancer: HER2-positive survival": "Identify HER2-positive breast cancer patients in the past 4 years and compare survival across treatment regimens",
        "Colorectal cancer: KRAS-mutant survival": "Identify KRAS-mutant colorectal cancer patients in the past 3 years and compare survival across treatment regimens",
        "Diabetes: follow-up HbA1c": "Identify type 2 diabetes patients in the past 3 years and compare follow-up HbA1c across treatment regimens",
        "Hypertension: BP control": "Identify hypertension patients in the past 3 years and compare blood pressure control rates across treatment regimens",
    },
}

# -------------------------------------------------------------------
# Styling
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --ink:#10243E;
        --ink-2:#324A63;
        --muted:#708196;
        --line:#E5EDF2;
        --panel:#FFFFFF;
        --soft:#F7FAFC;
        --mint:#1FAF9A;
        --mint-dark:#148775;
        --mint-soft:#EAF8F4;
        --blue:#4D7DFF;
        --purple:#8166E8;
        --orange:#E89B45;
        --shadow:0 14px 36px rgba(30,56,78,.08);
    }

    html, body, [class*="css"] {
        font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 78% 5%, rgba(31,175,154,.06), transparent 24rem),
            linear-gradient(180deg,#FBFDFE 0%,#FFFFFF 44%,#F7FAFC 100%);
        color:var(--ink);
    }

    .block-container {
        max-width: 1280px;
        padding-top:.12rem !important;
        padding-bottom:3rem;
    }

    [data-testid="stSidebar"] { display:none; }
    [data-testid="stHeader"] { display:none !important; height:0 !important; }
    [data-testid="stToolbar"] { display:none !important; height:0 !important; }
    [data-testid="stDecoration"] { display:none !important; }
    #MainMenu { visibility:hidden; }
    footer { visibility:hidden; }

    /* Streamlit controls */
    .stButton > button {
        min-height:46px;
        border-radius:12px;
        font-weight:700;
        border:1px solid var(--line);
        transition:.18s ease;
    }
    .stButton > button:hover {
        transform:translateY(-1px);
        border-color:#B7DAD2;
    }
    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,var(--mint),#21B7A2);
        border:none;
        color:white;
        box-shadow:0 10px 24px rgba(31,175,154,.20);
    }
    .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div,
    .stTextInput input {
        border-radius:12px !important;
        border-color:#DFE8EE !important;
        background:#FCFEFF !important;
    }
    [data-testid="stMetric"] {
        background:#fff;
        border:1px solid var(--line);
        border-radius:14px;
        padding:1rem 1.05rem;
        box-shadow:0 4px 14px rgba(38,61,80,.035);
    }
    [data-testid="stMetricLabel"] { color:var(--muted); }
    [data-testid="stDataFrame"] {
        border:1px solid var(--line);
        border-radius:14px;
        overflow:hidden;
    }
    [data-testid="stExpander"] {
        border:1px solid var(--line);
        border-radius:12px;
        background:#fff;
    }

    /* Top nav */
    .topbar {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:1rem;
        border-bottom:1px solid rgba(229,237,242,.85);
        padding:.25rem 0 .85rem;
        margin-bottom:1.2rem;
    }
    .brand-wrap {
        display:flex;
        align-items:center;
        gap:.7rem;
    }
    .brand-mark {
        width:42px;height:42px;border-radius:13px;
        display:flex;align-items:center;justify-content:center;
        background:linear-gradient(135deg,#1FAF9A,#68D2C1);
        color:white;font-size:1.15rem;font-weight:900;
        box-shadow:0 8px 18px rgba(31,175,154,.20);
    }
    .brand-name { font-size:1.08rem;font-weight:850;color:var(--ink);line-height:1.05; }
    .brand-sub { font-size:.67rem;color:var(--muted);margin-top:.18rem;letter-spacing:.02em; }

    /* Hero */
    .hero-grid {
        display:grid;
        grid-template-columns:minmax(0,1.08fr) minmax(420px,.92fr);
        gap:2.2rem;
        align-items:center;
        padding:2.6rem 0 2.3rem;
    }
    .badge {
        display:inline-flex;align-items:center;gap:.45rem;
        padding:.43rem .74rem;border-radius:999px;
        background:var(--mint-soft);color:var(--mint-dark);
        font-size:.77rem;font-weight:800;
        border:1px solid #D6F1EA;
        margin-bottom:1.15rem;
    }
    .hero-title {
        font-size:3.35rem;
        line-height:1.08;
        font-weight:900;
        letter-spacing:-.055em;
        color:var(--ink);
        margin:0 0 1rem;
    }
    .hero-accent {
        color:var(--mint);
        display:block;
    }
    .hero-desc {
        max-width:660px;
        font-size:1.02rem;
        line-height:1.85;
        color:#52677B;
        margin:0 0 1.5rem;
    }
    .hero-stats {
        display:flex;gap:1.65rem;flex-wrap:wrap;margin-top:1.25rem;
    }
    .hero-stat {
        padding-right:1.55rem;border-right:1px solid var(--line);
    }
    .hero-stat:last-child { border-right:none; }
    .hero-stat strong { display:block;font-size:1.55rem;color:var(--ink); }
    .hero-stat span { display:block;color:var(--muted);font-size:.78rem;margin-top:.15rem; }

    /* Illustration */
    .visual-shell {
        position:relative;
        min-height:430px;
        border:1px solid #E9F0F4;
        border-radius:30px;
        background:
          linear-gradient(145deg,rgba(255,255,255,.96),rgba(246,251,252,.96));
        box-shadow:var(--shadow);
        overflow:hidden;
    }
    .visual-grid {
        position:absolute;inset:0;
        background-image:
          linear-gradient(rgba(28,79,94,.035) 1px,transparent 1px),
          linear-gradient(90deg,rgba(28,79,94,.035) 1px,transparent 1px);
        background-size:28px 28px;
        mask-image:linear-gradient(to bottom,black,transparent);
    }
    .mini-card {
        position:absolute;background:#fff;border:1px solid #E5EDF2;
        border-radius:17px;box-shadow:0 12px 28px rgba(31,54,72,.10);
        padding:.9rem;
    }
    .mini-label {font-size:.68rem;color:var(--muted);font-weight:700;margin-bottom:.4rem}
    .mini-value {font-size:.9rem;color:var(--ink);font-weight:850}
    .v-agent {left:42px;top:45px;width:190px}
    .v-cohort {right:35px;top:100px;width:205px}
    .v-chart {left:92px;bottom:52px;width:225px}
    .v-model {right:42px;bottom:42px;width:180px}
    .center-orbit {
        position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
        width:132px;height:132px;border-radius:50%;
        background:radial-gradient(circle,#fff 0 38%,#E9F8F4 39% 61%,transparent 62%);
        border:1px solid #DCECE8;
        display:flex;align-items:center;justify-content:center;text-align:center;
        color:var(--mint-dark);font-size:.78rem;font-weight:900;letter-spacing:.02em;
    }
    .dot {position:absolute;border-radius:50%}
    .dot.a{width:16px;height:16px;background:#1FAF9A;left:27%;top:39%}
    .dot.b{width:12px;height:12px;background:#4D7DFF;right:26%;top:38%}
    .dot.c{width:14px;height:14px;background:#8166E8;left:34%;bottom:30%}
    .link {
        position:absolute;height:1px;background:#CDE3DD;transform-origin:left center;
    }
    .link.l1{width:125px;left:30%;top:42%;transform:rotate(18deg)}
    .link.l2{width:118px;right:26%;top:43%;transform:rotate(160deg)}
    .link.l3{width:95px;left:34%;bottom:34%;transform:rotate(-22deg)}
    .spark {
        display:flex;align-items:end;gap:5px;height:60px;margin-top:.5rem;
    }
    .spark i {display:block;width:13px;border-radius:4px 4px 2px 2px;background:#BDE9E0}
    .spark i:nth-child(1){height:25%}.spark i:nth-child(2){height:38%}
    .spark i:nth-child(3){height:30%}.spark i:nth-child(4){height:63%;background:#7AD8C7}
    .spark i:nth-child(5){height:52%}.spark i:nth-child(6){height:86%;background:#1FAF9A}
    .spark i:nth-child(7){height:72%}
    .curve {
        width:100%;height:55px;margin-top:.45rem;
    }

    /* Sections */
    .section-intro {text-align:center;max-width:780px;margin:3.2rem auto 2rem;}
    .section-kicker {font-size:.75rem;font-weight:850;color:var(--mint);letter-spacing:.12em}
    .section-title {font-size:2.1rem;line-height:1.2;font-weight:900;letter-spacing:-.035em;color:var(--ink);margin:.5rem 0 .65rem}
    .section-desc {font-size:.95rem;line-height:1.75;color:var(--muted);margin:0}

    /* Vertical flow */
    .vertical-flow {max-width:900px;margin:0 auto 3.5rem;position:relative}
    .vertical-flow:before {
        content:"";position:absolute;left:31px;top:40px;bottom:40px;
        width:2px;background:linear-gradient(var(--mint),#DDEAE6);
    }
    .flow-step {
        position:relative;
        display:grid;
        grid-template-columns:64px minmax(0,1fr);
        gap:1rem;
        margin-bottom:1rem;
    }
    .flow-index {
        width:64px;height:64px;border-radius:18px;
        background:#fff;border:1px solid #DCEAE6;
        box-shadow:0 7px 20px rgba(28,71,61,.07);
        display:flex;align-items:center;justify-content:center;
        color:var(--mint-dark);font-weight:900;z-index:2;
    }
    .flow-card {
        background:#fff;border:1px solid var(--line);border-radius:18px;
        padding:1.15rem 1.25rem;box-shadow:0 8px 25px rgba(40,65,84,.045);
    }
    .flow-card h3 {font-size:1rem;margin:0 0 .35rem;color:var(--ink)}
    .flow-card p {font-size:.88rem;line-height:1.65;color:var(--muted);margin:0}
    .flow-demo {
        display:inline-block;margin-top:.7rem;padding:.38rem .6rem;border-radius:8px;
        background:#F4F8FA;color:#536A7D;font-size:.74rem;font-family:ui-monospace,Consolas,monospace;
    }

    /* Scenario cards */
    .scene-grid {
        display:grid;grid-template-columns:repeat(5,minmax(0,1fr));
        gap:.75rem;margin:0 0 3rem;
    }
    .scene-card {
        background:#fff;border:1px solid var(--line);border-radius:17px;
        padding:1rem;min-height:150px;
        box-shadow:0 7px 20px rgba(35,60,79,.04);
    }
    .scene-icon {
        width:38px;height:38px;border-radius:11px;
        display:flex;align-items:center;justify-content:center;
        background:var(--mint-soft);color:var(--mint-dark);font-weight:900;
        margin-bottom:.75rem;
    }
    .scene-card strong {font-size:.88rem;color:var(--ink);display:block;margin-bottom:.38rem}
    .scene-card span {font-size:.76rem;line-height:1.55;color:var(--muted)}

    /* Workspace */
    .workspace-head {
        background:linear-gradient(135deg,#F7FBFA,#FFFFFF);
        border:1px solid #E2ECE8;
        border-radius:22px;
        padding:1.4rem 1.5rem;
        margin:1rem 0 1.15rem;
    }
    .workspace-head .wk {font-size:.72rem;color:var(--mint);font-weight:850;letter-spacing:.11em}
    .workspace-head h1 {font-size:1.75rem;margin:.35rem 0 .4rem;color:var(--ink);letter-spacing:-.03em}
    .workspace-head p {margin:0;color:var(--muted);font-size:.9rem}

    .project-card {
        background:#fff;border:1px solid var(--line);border-radius:20px;
        padding:1.2rem 1.3rem;margin-bottom:1rem;
        box-shadow:0 10px 30px rgba(38,63,81,.045);
    }
    .project-card-title {
        display:flex;align-items:center;gap:.6rem;font-size:1rem;font-weight:850;color:var(--ink);
        margin-bottom:.8rem;
    }
    .tiny-icon {
        width:31px;height:31px;border-radius:9px;background:var(--mint-soft);
        color:var(--mint-dark);display:flex;align-items:center;justify-content:center;font-weight:900;
    }

    .stage-head {
        display:grid;grid-template-columns:46px 1fr;
        gap:.75rem;align-items:center;
        margin:1.5rem 0 .65rem;
    }
    .stage-no {
        width:46px;height:46px;border-radius:14px;background:linear-gradient(145deg,#E7F8F3,#F8FFFD);
        border:1px solid #D4ECE5;color:var(--mint-dark);font-weight:900;
        display:flex;align-items:center;justify-content:center;
    }
    .stage-head strong {display:block;color:var(--ink);font-size:1.03rem}
    .stage-head small {display:block;color:var(--muted);font-size:.78rem;margin-top:.2rem}

    .insight-box {
        background:linear-gradient(135deg,#F1FBF8,#FBFEFD);
        border:1px solid #D7EEE7;
        border-radius:16px;padding:1rem 1.1rem;color:#2F5A52;
        line-height:1.65;font-size:.88rem;
    }

    .compact-panel {
        background:#fff;
        border:1px solid var(--line);
        border-radius:16px;
        padding:.82rem 1rem;
        margin:.25rem 0 .6rem;
        box-shadow:0 5px 16px rgba(38,63,81,.035);
    }
    .compact-note {
        color:var(--muted);
        font-size:.75rem;
        line-height:1.55;
    }
    .mini-list {
        display:flex;
        flex-wrap:wrap;
        gap:.42rem;
        margin-top:.55rem;
    }
    .mini-chip {
        padding:.32rem .52rem;
        border-radius:8px;
        background:#F3F8F9;
        color:#50697A;
        border:1px solid #E4EEF0;
        font-size:.72rem;
    }
    .import-panel {
        border:1px solid #DCEAE6;
        background:linear-gradient(135deg,#FAFDFC,#FFFFFF);
        border-radius:18px;
        padding:1.05rem 1.15rem;
        margin:.65rem 0 .9rem;
        box-shadow:0 8px 24px rgba(35,75,65,.04);
    }
    .format-box {
        border:1px solid #E3EBF0;
        background:#FBFDFE;
        border-radius:15px;
        padding:.95rem 1rem;
        min-height:225px;
    }
    .format-box h4 {margin:.05rem 0 .55rem;color:#1F3B51;font-size:.92rem}
    .format-box ul {margin:.3rem 0 0 1.15rem;padding:0;color:#718493;font-size:.76rem;line-height:1.65}
    .quality-strip {
        display:grid;
        grid-template-columns:repeat(5,minmax(0,1fr));
        gap:.55rem;
        margin:.55rem 0 .8rem;
    }
    .quality-item {
        border:1px solid #E5EDF1;
        border-radius:12px;
        padding:.65rem .72rem;
        background:#fff;
    }
    .quality-item b {display:block;color:#17334A;font-size:.96rem}
    .quality-item span {display:block;color:#8393A0;font-size:.68rem;margin-top:.15rem}
    .integrity-note {
        background:#FFF9EC;
        border:1px solid #F1E2B8;
        color:#7A6429;
        border-radius:12px;
        padding:.75rem .85rem;
        font-size:.76rem;
        line-height:1.6;
        margin:.6rem 0;
    }


    .research-shell {
        border:1px solid #E2ECE9;
        border-radius:22px;
        background:
            radial-gradient(circle at 92% 2%,rgba(31,175,154,.08),transparent 16rem),
            #FFFFFF;
        box-shadow:0 12px 34px rgba(28,61,78,.05);
        padding:1rem 1.05rem;
        margin:.8rem 0;
    }
    .research-stepbar {
        display:grid;
        grid-template-columns:repeat(4,minmax(0,1fr));
        gap:.55rem;
        margin:.75rem 0 1rem;
    }
    .research-step-pill {
        border:1px solid #E3ECEF;
        border-radius:12px;
        padding:.6rem .7rem;
        background:#FBFDFE;
    }
    .research-step-pill b {
        color:#1AA48F;
        font-size:.7rem;
        display:block;
        margin-bottom:.12rem;
    }
    .research-step-pill span {
        color:#38546A;
        font-size:.73rem;
        font-weight:800;
    }
    .source-card-title {
        display:flex;
        align-items:center;
        gap:.5rem;
        color:#17364D;
        font-weight:900;
        font-size:.94rem;
        margin-bottom:.25rem;
    }
    .source-card-desc {
        color:#7A8C99;
        font-size:.72rem;
        line-height:1.55;
        margin-bottom:.6rem;
    }
    .source-icon {
        width:30px;height:30px;border-radius:9px;
        display:inline-flex;align-items:center;justify-content:center;
        background:#EAF8F4;color:#188E7B;font-weight:900;
    }
    .platform-schema {
        display:flex;
        flex-wrap:wrap;
        gap:.32rem;
        margin-top:.5rem;
    }
    .schema-chip {
        border:1px solid #E1EBEE;
        background:#F6FAFB;
        color:#637987;
        border-radius:999px;
        padding:.26rem .46rem;
        font-size:.65rem;
    }
    .source-active {
        display:inline-flex;
        align-items:center;
        gap:.28rem;
        background:#EAF8F4;
        border:1px solid #D3ECE5;
        color:#178D79;
        border-radius:999px;
        padding:.34rem .55rem;
        font-size:.7rem;
        font-weight:850;
        margin:.25rem 0 .65rem;
    }
    .compact-guide {
        border:1px solid #E4ECEF;
        border-radius:14px;
        background:#FBFDFE;
        padding:.75rem .82rem;
        min-height:100%;
    }
    .compact-guide h4 {
        color:#28465B;
        font-size:.79rem;
        margin:0 0 .35rem;
    }
    .compact-guide p {
        color:#7B8D99;
        font-size:.68rem;
        line-height:1.55;
        margin:.15rem 0;
    }
    .preview-head {
        display:flex;align-items:center;justify-content:space-between;
        gap:.8rem;margin:.85rem 0 .4rem;
    }
    .preview-head strong {font-size:.9rem;color:#19374E}
    .analysis-command {
        border:1px solid #C7E4DC;
        border-radius:19px;
        padding:1.05rem 1.1rem;
        background:
            radial-gradient(circle at 95% 5%,rgba(31,175,154,.10),transparent 11rem),
            linear-gradient(135deg,#F5FBF9,#FFFFFF);
        margin:1rem 0 .7rem;
        box-shadow:0 8px 22px rgba(39,89,76,.04);
    }
    .analysis-command .kicker {
        color:#1BA48F;font-size:.68rem;font-weight:900;letter-spacing:.1em;
    }
    .analysis-command h3 {
        margin:.22rem 0 .2rem;color:#17374E;font-size:1.02rem;
    }
    .analysis-command p {
        color:#778A98;font-size:.74rem;line-height:1.6;margin:0 0 .6rem;
    }

    .analysis-command-grid {
        display:grid;
        grid-template-columns:minmax(0,1.15fr) minmax(330px,.85fr);
        gap:1rem;
        align-items:stretch;
    }
    .analysis-command-examples {
        border:1px solid #DFEBE7;
        border-radius:14px;
        background:rgba(255,255,255,.78);
        padding:.72rem .78rem;
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:.42rem;
        align-content:center;
    }
    .analysis-command-examples-title {
        grid-column:1 / -1;
        color:#67808D;
        font-size:.66rem;
        font-weight:800;
        margin-bottom:.08rem;
    }
    .analysis-example-chip {
        border:1px solid #E2ECE8;
        border-radius:9px;
        background:#F8FBFA;
        padding:.42rem .48rem;
        color:#516B78;
        font-size:.65rem;
        line-height:1.38;
        min-height:46px;
        display:flex;
        align-items:center;
    }

    /* Stronger contrast for the main research-instruction textarea */
    textarea[aria-label="分析指令 / 研究问题"],
    textarea[aria-label="Analysis instruction / research question"] {
        background:#EEF3F6 !important;
        border:1px solid #C5D2DA !important;
        color:#20384A !important;
        box-shadow:inset 0 1px 2px rgba(31,55,72,.04) !important;
        min-height:150px !important;
    }

    textarea[aria-label="分析指令 / 研究问题"]::placeholder,
    textarea[aria-label="Analysis instruction / research question"]::placeholder {
        color:#687A87 !important;
        opacity:1 !important;
    }

    textarea[aria-label="分析指令 / 研究问题"]:focus,
    textarea[aria-label="Analysis instruction / research question"]:focus {
        background:#FFFFFF !important;
        border-color:#20AB96 !important;
        box-shadow:0 0 0 3px rgba(32,171,150,.11) !important;
        outline:none !important;
    }

    @media(max-width:900px){
        .analysis-command-grid{grid-template-columns:1fr}
        .analysis-command-examples{grid-template-columns:repeat(2,1fr)}
    }
    .method-card {
        border:1px solid #DFE9ED;
        background:#FFFFFF;
        border-radius:16px;
        padding:.85rem .9rem;
        min-height:114px;
    }
    .method-card-label {
        color:#8796A2;font-size:.68rem;font-weight:700;
    }
    .method-card-value {
        color:#17354B;font-size:1rem;font-weight:900;margin-top:.25rem;
    }
    .method-card-note {
        color:#1B9B86;font-size:.68rem;margin-top:.35rem;
    }
    .variable-panel {
        border:1px solid #E0E9ED;
        border-radius:17px;
        padding:.85rem .9rem;
        background:#FFFFFF;
        margin:.65rem 0;
    }
    .run-panel {
        padding:.2rem 0 .55rem;
    }
    .report-hero {
        border:1px solid #CFE9E2;
        border-radius:21px;
        padding:1.05rem 1.1rem;
        background:
            radial-gradient(circle at 92% 10%,rgba(31,175,154,.10),transparent 14rem),
            linear-gradient(135deg,#F3FBF8,#FFFFFF);
        margin:1.3rem 0 .75rem;
        box-shadow:0 10px 28px rgba(31,109,90,.05);
    }
    .report-hero small {
        color:#1BA48F;font-weight:900;letter-spacing:.1em;
    }
    .report-hero h2 {
        color:#17364D;font-size:1.35rem;margin:.28rem 0 .28rem;
    }
    .report-hero p {
        color:#778A98;font-size:.76rem;margin:0;
    }
    /* Modal data-import experience */
    div[data-testid="stDialog"] div[role="dialog"] {
        width:min(1180px,94vw) !important;
        max-width:1180px !important;
        border-radius:22px !important;
        border:1px solid #DFE8EC !important;
        box-shadow:0 28px 80px rgba(25,48,67,.20) !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] > div {
        border-radius:22px !important;
    }
    .import-dialog-kicker {
        color:#1AA58F;
        font-size:.68rem;
        font-weight:900;
        letter-spacing:.1em;
        margin-bottom:.18rem;
    }
    .import-dialog-sub {
        color:#7C8D99;
        font-size:.73rem;
        line-height:1.55;
        margin-bottom:.65rem;
    }
    .template-preview-head {
        color:#19384F;
        font-size:.95rem;
        font-weight:900;
        margin-bottom:.28rem;
    }

    .format-main-card {
        border:1px solid #DDE8EC;
        border-radius:17px;
        background:
            radial-gradient(circle at 95% 4%,rgba(31,175,154,.06),transparent 10rem),
            #FBFDFE;
        padding:1rem 1.05rem;
        min-height:430px;
    }
    .format-main-title {
        color:#17364D;
        font-size:1.02rem;
        font-weight:900;
        margin-bottom:.28rem;
    }
    .format-main-sub {
        color:#7B8D99;
        font-size:.72rem;
        line-height:1.55;
        margin-bottom:.85rem;
    }
    .format-rule-row {
        display:grid;
        grid-template-columns:34px 1fr;
        gap:.55rem;
        align-items:flex-start;
        border-bottom:1px solid #E8EFF2;
        padding:.68rem 0;
        color:#536B7C;
        font-size:.76rem;
        line-height:1.55;
    }
    .format-rule-row:last-of-type {
        border-bottom:none;
    }
    .format-rule-no {
        width:28px;
        height:28px;
        border-radius:8px;
        display:flex;
        align-items:center;
        justify-content:center;
        background:#EAF8F4;
        color:#188F7B;
        font-size:.64rem;
        font-weight:900;
    }
    .format-supported {
        margin-top:.8rem;
        padding:.58rem .65rem;
        border-radius:10px;
        background:#F2F7F8;
        color:#7A8C98;
        font-size:.68rem;
        line-height:1.5;
    }
    .mini-template-wrap {
        margin-top:.75rem;
        border:1px solid #E3EBEE;
        border-radius:13px;
        background:#FFFFFF;
        padding:.72rem .75rem;
    }
    .mini-template-head {
        display:flex;
        justify-content:space-between;
        align-items:flex-start;
        margin-bottom:.5rem;
    }
    .mini-template-head strong {
        display:block;
        color:#29465A;
        font-size:.78rem;
        margin-bottom:.12rem;
    }
    .mini-template-head span {
        display:block;
        color:#8A98A3;
        font-size:.62rem;
        line-height:1.4;
    }
    .mini-template-table {
        width:100%;
        border-collapse:collapse;
        font-size:.65rem;
        color:#52697A;
    }
    .mini-template-table th {
        text-align:left;
        background:#F5F8FA;
        color:#405C6E;
        font-weight:800;
        padding:.38rem .42rem;
        border:1px solid #E6EDF0;
    }
    .mini-template-table td {
        padding:.34rem .42rem;
        border:1px solid #E8EEF1;
        background:#FFFFFF;
    }
    .template-preview-note {
        color:#7E8F9C;
        font-size:.69rem;
        line-height:1.5;
        margin-bottom:.55rem;
    }
    .import-status-card {
        border:1px solid #DCE9E5;
        border-radius:15px;
        padding:.8rem .85rem;
        background:linear-gradient(135deg,#F6FCFA,#FFFFFF);
        min-height:116px;
    }
    .import-status-card strong {
        display:block;
        color:#17364D;
        font-size:.86rem;
        margin-bottom:.24rem;
    }
    .import-status-card span {
        color:#7B8D99;
        font-size:.7rem;
        line-height:1.5;
    }
    .import-status-pill {
        display:inline-flex;
        align-items:center;
        padding:.3rem .52rem;
        border-radius:999px;
        background:#EAF8F4;
        border:1px solid #D3ECE5;
        color:#178D79;
        font-size:.68rem;
        font-weight:850;
        margin-top:.48rem;
    }


    /* Stronger form-field contrast inside the import modal */
    div[data-testid="stDialog"] [data-testid="stTextInput"] input,
    div[data-testid="stDialog"] [data-testid="stTextArea"] textarea {
        background:#F3F7F9 !important;
        border:1px solid #CEDAE1 !important;
        color:#20384A !important;
        box-shadow:inset 0 1px 2px rgba(31,55,72,.035) !important;
        transition:border-color .16s ease, box-shadow .16s ease, background .16s ease;
    }

    div[data-testid="stDialog"] [data-testid="stTextInput"] input {
        min-height:44px !important;
    }

    div[data-testid="stDialog"] [data-testid="stTextInput"] input::placeholder,
    div[data-testid="stDialog"] [data-testid="stTextArea"] textarea::placeholder {
        color:#6F808D !important;
        opacity:1 !important;
    }

    div[data-testid="stDialog"] [data-testid="stTextInput"] input:focus,
    div[data-testid="stDialog"] [data-testid="stTextArea"] textarea:focus {
        background:#FFFFFF !important;
        border-color:#21AD98 !important;
        box-shadow:0 0 0 3px rgba(33,173,152,.10) !important;
        outline:none !important;
    }

    div[data-testid="stDialog"] [data-testid="stTextInput"] label,
    div[data-testid="stDialog"] [data-testid="stTextArea"] label {
        color:#253D50 !important;
        font-weight:700 !important;
    }
    @media(max-width:800px){
        .research-stepbar{grid-template-columns:repeat(2,1fr)}
    }

    .instruction-panel {
        margin:.95rem 0 .9rem;
        border:1px solid #CFE8E2;
        border-radius:18px;
        padding:1rem 1.05rem;
        background:
            radial-gradient(circle at 95% 8%,rgba(31,175,154,.08),transparent 12rem),
            linear-gradient(135deg,#F7FCFA,#FFFFFF);
        box-shadow:0 8px 22px rgba(34,91,76,.045);
    }
    .instruction-kicker {
        color:#1FAF9A;
        font-size:.7rem;
        font-weight:900;
        letter-spacing:.1em;
        margin-bottom:.25rem;
    }
    .instruction-title {
        color:#15344B;
        font-size:1.02rem;
        font-weight:900;
        margin-bottom:.22rem;
    }
    .instruction-desc {
        color:#728594;
        font-size:.78rem;
        line-height:1.6;
    }
    .instruction-examples {
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:.42rem;
        margin:.65rem 0 .25rem;
    }
    .instruction-example {
        border:1px solid #E2ECE9;
        background:#FFFFFF;
        border-radius:10px;
        padding:.5rem .58rem;
        color:#587080;
        font-size:.7rem;
        line-height:1.45;
    }
    @media(max-width:760px){
        .instruction-examples{grid-template-columns:1fr}
    }
    @media(max-width:760px){.quality-strip{grid-template-columns:repeat(2,1fr)}}

    .result-focus {
        margin:1.5rem 0 .85rem;
        padding:1.15rem 1.2rem;
        border-radius:18px;
        border:1px solid #CFEAE3;
        background:
            radial-gradient(circle at 92% 10%,rgba(31,175,154,.09),transparent 13rem),
            linear-gradient(135deg,#F5FCFA,#FFFFFF);
        box-shadow:0 12px 28px rgba(31,94,79,.055);
    }
    .result-focus .rf-kicker {
        color:var(--mint);
        font-size:.72rem;
        font-weight:900;
        letter-spacing:.11em;
    }
    .result-focus h2 {
        color:var(--ink);
        font-size:1.45rem;
        margin:.28rem 0 .35rem;
        letter-spacing:-.025em;
    }
    .result-focus p {
        color:var(--muted);
        font-size:.83rem;
        margin:0;
    }
    .data-preview-label {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:1rem;
        color:var(--ink);
        font-weight:800;
        margin:.35rem 0 .45rem;
    }

    .template-card {
        background:#fff;border:1px solid var(--line);border-radius:17px;
        padding:1rem 1.1rem;margin-bottom:.75rem;
        box-shadow:0 7px 20px rgba(35,60,79,.04);
    }
    .template-card strong{color:var(--ink)}
    .template-card small{color:var(--muted);line-height:1.7}

    .about-card {
        background:#fff;border:1px solid var(--line);border-radius:18px;
        padding:1.2rem 1.3rem;margin-bottom:.8rem;
    }

    .settings-grid {
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:.85rem;
        margin:.85rem 0 1rem;
    }
    .settings-card {
        background:#fff;
        border:1px solid var(--line);
        border-radius:18px;
        padding:1.05rem 1.15rem;
        box-shadow:0 7px 22px rgba(35,60,79,.04);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color:#E4ECF1 !important;
        border-radius:18px !important;
        background:#FFFFFF !important;
        box-shadow:0 7px 22px rgba(35,60,79,.04);
    }

    .template-empty-state {
        min-height:145px;
        border:1px dashed #DCE7EC;
        border-radius:14px;
        background:#FAFCFD;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        text-align:center;
        padding:1rem;
    }
    .template-empty-icon {
        width:38px;
        height:38px;
        border-radius:11px;
        background:#EAF8F4;
        color:#1B9F8B;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:1.2rem;
        font-weight:800;
        margin-bottom:.55rem;
    }
    .template-empty-title {
        color:#244057;
        font-size:.84rem;
        font-weight:800;
        margin-bottom:.25rem;
    }
    .template-empty-sub {
        color:#8393A2;
        font-size:.73rem;
        line-height:1.55;
        max-width:330px;
    }
    .template-mini-row {
        display:flex;
        align-items:center;
        justify-content:space-between;
        padding:.72rem .78rem;
        border:1px solid #E6EDF1;
        background:#FBFDFE;
        border-radius:12px;
        margin-bottom:.45rem;
    }
    .template-mini-name {
        color:#203B52;
        font-size:.82rem;
        font-weight:800;
        margin-bottom:.18rem;
    }
    .template-mini-meta {
        color:#8292A0;
        font-size:.68rem;
    }
    .api-note-box {
        margin-top:.85rem;
        padding:.78rem .85rem;
        border-radius:12px;
        background:#F6FAFB;
        border:1px solid #E6EEF2;
    }
    .api-note-title {
        color:#3A556B;
        font-size:.76rem;
        font-weight:800;
        margin-bottom:.25rem;
    }
    .api-note-text {
        color:#7A8B99;
        font-size:.72rem;
        line-height:1.55;
    }
    .settings-card h3 {
        margin:.05rem 0 .35rem;
        color:var(--ink);
        font-size:1rem;
    }
    .settings-card p {
        margin:0;
        color:var(--muted);
        font-size:.82rem;
        line-height:1.65;
    }
    .status-pill {
        display:inline-flex;
        align-items:center;
        gap:.35rem;
        padding:.36rem .6rem;
        border-radius:999px;
        background:#EDF9F6;
        border:1px solid #D4EFE7;
        color:#188B78;
        font-size:.73rem;
        font-weight:800;
    }
    .settings-section-title {
        margin:1.35rem 0 .55rem;
        font-weight:900;
        color:var(--ink);
        font-size:1.05rem;
    }
    .template-manage-row {
        background:#fff;
        border:1px solid var(--line);
        border-radius:14px;
        padding:.8rem .9rem;
        margin-bottom:.55rem;
    }
    @media(max-width:780px){
        .settings-grid{grid-template-columns:1fr}
    }
    .about-card h3{margin:0 0 .45rem;font-size:1rem;color:var(--ink)}
    .about-card p{margin:0;color:var(--muted);line-height:1.75;font-size:.88rem}

    .footer-note {
        color:#91A0AE;font-size:.73rem;text-align:center;margin-top:3rem;
    }

    @media(max-width:980px){
        .hero-grid{grid-template-columns:1fr}.visual-shell{min-height:390px}
        .scene-grid{grid-template-columns:repeat(2,1fr)}
        .hero-title{font-size:2.65rem}
    }
    @media(max-width:620px){
        .hero-title{font-size:2.15rem}
        .scene-grid{grid-template-columns:1fr}
        .hero-stats{gap:.8rem}.hero-stat{padding-right:.8rem}
        .visual-shell{min-height:360px}
        .v-agent{left:18px;top:35px}.v-cohort{right:15px;top:105px}
        .v-chart{left:24px;bottom:36px}.v-model{right:15px;bottom:30px}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_resource
def services():
    return ResearchAgent(), QueryEngine(), StatsEngine(), TemplateStore(), CustomDataEngine()

agent, qe, se, ts, custom_engine = services()

# The LLM receives only the research question text, never patient-level data.
AI_ENABLED = bool(getattr(agent, "ai_enabled", False))

# -------------------------------------------------------------------
# Language + top navigation
# -------------------------------------------------------------------
def sync_language():
    # Explicit callback makes language switching deterministic on Streamlit Cloud.
    # Streamlit reruns the whole script after updating session_state.
    pass

# Read the previous language selection before rendering the header.
# The selectbox is placed directly inside the nav row so it does not
# create an empty strip above the brand.
language = st.session_state.get("language_top", "中文")
lang = "zh" if language == "中文" else "en"
c = COPY[lang]

brand_col, nav1, nav2, nav3, nav4, nav5 = st.columns(
    [4.6, .9, 1.05, 1.05, .95, .85],
    gap="small",
)
with brand_col:
    st.markdown(
        f"""
        <div class="brand-wrap">
            <div class="brand-mark">✦</div>
            <div>
                <div class="brand-name">{c["brand"]}</div>
                <div class="brand-sub">{c["brand_sub"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def goto(page):
    st.session_state.page = page
    st.rerun()

with nav1:
    if st.button(c["home"], use_container_width=True, key="nav_home"):
        goto("home")
with nav2:
    if st.button(c["analysis"], use_container_width=True, key="nav_analysis"):
        goto("analysis")
with nav3:
    if st.button(c["templates"], use_container_width=True, key="nav_templates"):
        goto("templates")
with nav4:
    if st.button(c["about"], use_container_width=True, key="nav_about"):
        goto("about")
with nav5:
    if st.button("⚙ " + c["settings"], use_container_width=True, key="nav_settings"):
        goto("settings")

st.markdown(
    '<div style="height:.15rem;border-bottom:1px solid #E9EFF3;margin-bottom:.25rem"></div>',
    unsafe_allow_html=True,
)


def _render_common_result_area(df, result, lang, c, source="demo", report_html=None):
    st.markdown(
        f"""
        <div class="result-focus">
            <div class="rf-kicker">ANALYSIS RESULT</div>
            <h2>{c["result_focus"]}</h2>
            <p>{c["result_focus_desc"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="stage-head">
            <div class="stage-no">03</div>
            <div>
                <strong>{c["stage3"]}</strong>
                <small>{c["stage3_desc"]}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r1, r2 = st.columns([1.55, .65])
    r1.metric(c["method"], result["method"])
    r2.metric(
        c["p"],
        "N/A" if result.get("p") is None else f'{result["p"]:.4g}',
    )

    chart_bytes = base64.b64decode(result["image"])
    state_key = f"chart_expanded_{source}"
    chart_expanded = st.session_state.get(state_key, False)

    a1, a2 = st.columns([1.2, 1.25])
    with a1:
        if st.button(
            ("↙ " if chart_expanded else "↗ ")
            + (c["collapse_chart"] if chart_expanded else c["expand_chart"]),
            use_container_width=True,
            key=f"toggle_chart_{source}",
        ):
            st.session_state[state_key] = not chart_expanded
            st.rerun()
    with a2:
        st.download_button(
            "↓ " + c["export_chart"],
            chart_bytes,
            file_name=f"haiyan_{source}_analysis_chart.png",
            mime="image/png",
            use_container_width=True,
            key=f"download_chart_{source}",
        )

    if chart_expanded:
        st.image(chart_bytes, use_container_width=True)
        st.markdown(f"**{c['summary']}**")
        st.dataframe(
            pd.DataFrame(result["summary"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        chart_col, summary_col = st.columns([1.28, .72], gap="large")
        with chart_col:
            st.image(chart_bytes, use_container_width=True)
        with summary_col:
            st.markdown(f"**{c['summary']}**")
            st.dataframe(
                pd.DataFrame(result["summary"]),
                use_container_width=True,
                hide_index=True,
                height=300,
            )

    st.markdown(f"**{c['conclusion']}**")
    st.markdown(
        f'<div class="insight-box">✦ {html.escape(result["conclusion"])}</div>',
        unsafe_allow_html=True,
    )

    if result.get("cox"):
        with st.expander(c["cox"], expanded=False):
            st.dataframe(
                pd.DataFrame(result["cox"]),
                use_container_width=True,
                hide_index=True,
            )

    export1, export2 = st.columns(2)
    with export1:
        st.download_button(
            c["download"],
            df.to_csv(index=False).encode("utf-8-sig"),
            f"haiyan_{source}_analysis_data.csv",
            "text/csv",
            use_container_width=True,
            key=f"download_data_{source}",
        )
    with export2:
        st.download_button(
            c["export_summary"],
            pd.DataFrame(result["summary"]).to_csv(index=False).encode("utf-8-sig"),
            f"haiyan_{source}_analysis_summary.csv",
            "text/csv",
            use_container_width=True,
            key=f"download_summary_{source}",
        )



def _show_data_import_dialog(lang, c):
    """
    Modal import flow. Data are parsed only when the user confirms.
    The parsed DataFrame is stored in Streamlit session state and then
    re-enters the same research-analysis workflow as platform datasets.
    """

    @st.dialog(c["import_dialog_title"], width="large")
    def _dialog():
        left, right = st.columns([1.04, .96], gap="large")

        with left:
            st.markdown(
                f"""
                <div class="import-dialog-kicker">RESEARCH DATA IMPORT</div>
                <div class="import-dialog-sub">
                    {
                        "填写基本项目信息后上传数据。项目说明仅用于本次分析界面展示，不会改变统计结果。"
                        if lang == "zh"
                        else
                        "Add basic project information and import the dataset. Project notes are for workflow context only and do not alter statistical results."
                    }
                </div>
                """,
                unsafe_allow_html=True,
            )

            project_name = st.text_input(
                c["import_project_name"] + " *",
                value=st.session_state.get("import_project_name", ""),
                placeholder=c["import_project_name_ph"],
                key="dialog_project_name",
            )
            project_background = st.text_area(
                c["import_project_background"],
                value=st.session_state.get("import_project_background", ""),
                placeholder=c["import_background_ph"],
                height=92,
                key="dialog_project_background",
            )
            project_summary = st.text_area(
                c["import_project_summary"],
                value=st.session_state.get("import_project_summary", ""),
                placeholder=c["import_summary_ph"],
                height=92,
                key="dialog_project_summary",
            )

            upload_tab, paste_tab = st.tabs([c["upload_data"], c["paste_data"]])
            dialog_uploaded = None
            dialog_pasted = ""

            with upload_tab:
                dialog_uploaded = st.file_uploader(
                    c["upload_data"],
                    type=["csv", "xls", "xlsx"],
                    key="dialog_upload_file",
                    help=c["supported_files"],
                )
                st.caption(c["supported_files"])

            with paste_tab:
                dialog_pasted = st.text_area(
                    c["paste_data"],
                    placeholder=c["paste_placeholder"],
                    height=145,
                    key="dialog_paste_data",
                )

        with right:
            st.html(
                f"""
                <div class="format-main-card">
                    <div class="format-main-title">✓ {c["format_rules"]}</div>
                    <div class="format-main-sub">
                        {
                            "请优先按以下规范整理数据。格式正确时，系统才能更稳定地识别变量类型、统计方法和分析结果。"
                            if lang == "zh"
                            else
                            "Please structure the dataset according to these rules so the platform can reliably identify variable types, statistical methods and analysis outputs."
                        }
                    </div>

                    <div class="format-rule-row">
                        <span class="format-rule-no">01</span>
                        <div>{c["format_rule_1"]}</div>
                    </div>
                    <div class="format-rule-row">
                        <span class="format-rule-no">02</span>
                        <div>{c["format_rule_2"]}</div>
                    </div>
                    <div class="format-rule-row">
                        <span class="format-rule-no">03</span>
                        <div>{c["format_rule_3"]}</div>
                    </div>
                    <div class="format-rule-row">
                        <span class="format-rule-no">04</span>
                        <div>{c["format_rule_4"]}</div>
                    </div>
                    <div class="format-rule-row">
                        <span class="format-rule-no">05</span>
                        <div>{c["format_rule_5"]}</div>
                    </div>
                    <div class="format-rule-row">
                        <span class="format-rule-no">06</span>
                        <div>{c["format_rule_6"]}</div>
                    </div>

                    <div class="format-supported">
                        {c["supported_files"]}
                    </div>
                </div>
                """
            )

            st.html(
                f"""
                <div class="mini-template-wrap">
                    <div class="mini-template-head">
                        <div>
                            <strong>▦ {c["template_preview"]}</strong>
                            <span>{c["template_instruction"]}</span>
                        </div>
                    </div>

                    <table class="mini-template-table">
                        <thead>
                            <tr>
                                <th>{"患者编号" if lang == "zh" else "patient_id"}</th>
                                <th>{"分组" if lang == "zh" else "group"}</th>
                                <th>{"结局指标" if lang == "zh" else "outcome"}</th>
                                <th>{"年龄" if lang == "zh" else "age"}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>P001</td>
                                <td>A</td>
                                <td>7.2</td>
                                <td>61</td>
                            </tr>
                            <tr>
                                <td>P002</td>
                                <td>B</td>
                                <td>6.5</td>
                                <td>58</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """
            )

            if lang == "zh":
                generic_template = (
                    "患者编号,分组,结局指标,年龄,性别\n"
                    "P001,A,7.2,61,女\n"
                    "P002,B,6.5,58,男\n"
                ).encode("utf-8-sig")
                generic_template_name = "海研分析_通用数据模板.csv"
            else:
                generic_template = (
                    "patient_id,group,outcome,age,sex\n"
                    "P001,A,7.2,61,F\n"
                    "P002,B,6.5,58,M\n"
                ).encode("utf-8-sig")
                generic_template_name = "haiyan_data_template.csv"

            st.download_button(
                "↓ " + c["download_template"],
                generic_template,
                generic_template_name,
                "text/csv",
                use_container_width=True,
                key="dialog_download_generic_template",
            )

        st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
        cancel_col, confirm_col = st.columns([1, 1])

        with cancel_col:
            if st.button(
                c["cancel_import"],
                use_container_width=True,
                key="dialog_cancel_import",
            ):
                st.rerun()

        with confirm_col:
            if st.button(
                c["confirm_import"],
                type="primary",
                use_container_width=True,
                key="dialog_confirm_import",
            ):
                if not project_name.strip():
                    st.error(c["project_name_required"])
                elif dialog_uploaded is None and not dialog_pasted.strip():
                    st.error(c["file_required"])
                else:
                    try:
                        if dialog_uploaded is not None:
                            imported_df = custom_engine.load_uploaded(dialog_uploaded)
                            imported_name = dialog_uploaded.name
                            imported_kind = c["source_upload"]
                        else:
                            imported_df = custom_engine.load_pasted(dialog_pasted)
                            imported_name = (
                                "pasted_data"
                                if lang == "en"
                                else "粘贴数据"
                            )
                            imported_kind = c["source_paste"]

                        st.session_state["workspace_imported_df"] = imported_df
                        st.session_state["workspace_imported_name"] = imported_name
                        st.session_state["workspace_imported_kind"] = imported_kind
                        st.session_state["import_project_name"] = project_name.strip()
                        st.session_state["import_project_background"] = project_background.strip()
                        st.session_state["import_project_summary"] = project_summary.strip()
                        st.session_state["workspace_active_source"] = "imported"
                        st.session_state["workspace_platform_active"] = "none"
                        st.session_state.pop("workspace_result", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f'{c["failed"]}: {exc}')

    _dialog()



# -------------------------------------------------------------------
# HOME
# -------------------------------------------------------------------
if st.session_state.page == "home":
    left, right = st.columns([1.08, .92], gap="large")

    with left:
        st.markdown(
            f"""
            <div style="padding-top:2.6rem">
                <div class="badge">✦ {c["hero_badge"]}</div>
                <h1 class="hero-title">
                    {c["hero_line1"]}
                    <span class="hero-accent">{c["hero_line2"]}</span>
                </h1>
                <p class="hero-desc">{c["hero_desc"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b1, b2 = st.columns([1.1, 1])
        with b1:
            if st.button("→  " + c["start"], type="primary", use_container_width=True, key="hero_start"):
                goto("analysis")
        with b2:
            st.button(c["view_examples"], use_container_width=True, disabled=True, help=c["scenes_title"], key="hero_examples")

        st.markdown(
            f"""
            <div class="hero-stats">
                <div class="hero-stat"><strong>{c["hero_stat_1"]}</strong><span>{c["hero_stat_1_label"]}</span></div>
                <div class="hero-stat"><strong>{c["hero_stat_2"]}</strong><span>{c["hero_stat_2_label"]}</span></div>
                <div class="hero-stat"><strong>{c["hero_stat_3"]}</strong><span>{c["hero_stat_3_label"]}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.html(
            f"""
            <div class="visual-shell">
                <div class="visual-grid"></div>
                <div class="link l1"></div><div class="link l2"></div><div class="link l3"></div>
                <div class="dot a"></div><div class="dot b"></div><div class="dot c"></div>
                <div class="center-orbit">{c["visual_result"].upper()}<br>AGENT</div>

                <div class="mini-card v-agent">
                    <div class="mini-label">{c["visual_nl"]}</div>
                    <div class="mini-value">NSCLC · EGFR MUT · OS</div>
                    <div style="margin-top:.55rem;font-size:.7rem;color:#7B8C9B">
                        {c["visual_semantic_done"]} ✓
                    </div>
                </div>

                <div class="mini-card v-cohort">
                    <div class="mini-label">{c["visual_cohort"]}</div>
                    <div class="mini-value">412 {c["visual_eligible"]}</div>
                    <div class="spark">
                        <i></i><i></i><i></i><i></i><i></i><i></i><i></i>
                    </div>
                </div>

                <div class="mini-card v-chart">
                    <div class="mini-label">{c["visual_km"]}</div>
                    <div class="mini-value">Log-rank P = 0.003</div>
                    <svg class="curve" viewBox="0 0 220 55">
                        <path d="M4 7 H36 V13 H69 V20 H103 V26 H139 V34 H174 V41 H215 V46"
                              fill="none" stroke="#1FAF9A" stroke-width="3"/>
                        <path d="M4 8 H32 V18 H62 V25 H96 V35 H133 V39 H172 V48 H215 V51"
                              fill="none" stroke="#4D7DFF" stroke-width="2.5"/>
                        <line x1="3" y1="52" x2="216" y2="52" stroke="#DDE6EC"/>
                    </svg>
                </div>

                <div class="mini-card v-model">
                    <div class="mini-label">{c["visual_adjusted"]}</div>
                    <div class="mini-value">Cox PH · HR 0.71</div>
                    <div style="margin-top:.5rem;height:7px;background:#EEF3F6;border-radius:99px;overflow:hidden">
                        <div style="width:71%;height:100%;background:#8166E8;border-radius:99px"></div>
                    </div>
                    <div style="margin-top:.45rem;font-size:.68rem;color:#7B8C9B">
                        95% CI 0.56–0.90
                    </div>
                </div>
            </div>
            """,
        )

    st.markdown(
        f"""
        <div class="section-intro">
            <div class="section-kicker">CORE WORKFLOW</div>
            <div class="section-title">{c["ability_title"]}</div>
            <p class="section-desc">{c["ability_desc"]}</p>
        </div>

        <div class="vertical-flow">
            <div class="flow-step">
                <div class="flow-index">01</div>
                <div class="flow-card">
                    <h3>{c["step_1_title"]}</h3>
                    <p>{c["step_1_desc"]}</p>
                    <span class="flow-demo">{c["step_1_demo"]}</span>
                </div>
            </div>
            <div class="flow-step">
                <div class="flow-index">02</div>
                <div class="flow-card">
                    <h3>{c["step_2_title"]}</h3>
                    <p>{c["step_2_desc"]}</p>
                    <span class="flow-demo">{c["step_2_demo"]}</span>
                </div>
            </div>
            <div class="flow-step">
                <div class="flow-index">03</div>
                <div class="flow-card">
                    <h3>{c["step_3_title"]}</h3>
                    <p>{c["step_3_desc"]}</p>
                    <span class="flow-demo">{c["step_3_demo"]}</span>
                </div>
            </div>
            <div class="flow-step">
                <div class="flow-index">04</div>
                <div class="flow-card">
                    <h3>{c["step_4_title"]}</h3>
                    <p>{c["step_4_desc"]}</p>
                    <span class="flow-demo">{c["step_4_demo"]}</span>
                </div>
            </div>
        </div>

        <div class="section-intro" style="margin-top:2.4rem">
            <div class="section-kicker">SYNTHETIC RESEARCH DATABASE</div>
            <div class="section-title">{c["scenes_title"]}</div>
            <p class="section-desc">{c["scenes_desc"]}</p>
        </div>

        <div class="scene-grid">
            <div class="scene-card"><div class="scene-icon">L</div><strong>{c["scene_lung"]}</strong><span>{c["scene_lung_desc"]}</span></div>
            <div class="scene-card"><div class="scene-icon">B</div><strong>{c["scene_breast"]}</strong><span>{c["scene_breast_desc"]}</span></div>
            <div class="scene-card"><div class="scene-icon">C</div><strong>{c["scene_crc"]}</strong><span>{c["scene_crc_desc"]}</span></div>
            <div class="scene-card"><div class="scene-icon">D</div><strong>{c["scene_dm"]}</strong><span>{c["scene_dm_desc"]}</span></div>
            <div class="scene-card"><div class="scene-icon">H</div><strong>{c["scene_htn"]}</strong><span>{c["scene_htn_desc"]}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------------------------
# ANALYSIS
# -------------------------------------------------------------------
elif st.session_state.page == "analysis":
    # ================================================================
    # Research workspace header
    # ================================================================
    st.markdown(
        f"""
        <div class="workspace-head">
            <div class="wk">RESEARCH WORKSPACE</div>
            <h1>{c["workspace_title"]}</h1>
            <p>
                {
                    "选择平台科研数据库或导入自己的数据，用自然语言描述研究问题，平台将自动推荐统计路径并生成结果报告。"
                    if lang == "zh"
                    else
                    "Choose a platform research dataset or import your own data, describe the research question naturally, and receive a recommended statistical path and report."
                }
            </p>
        </div>
        <div class="research-stepbar">
            <div class="research-step-pill"><b>01</b><span>{c["unified_source_title"]}</span></div>
            <div class="research-step-pill"><b>02</b><span>{c["instruction_title"]}</span></div>
            <div class="research-step-pill"><b>03</b><span>{c["step_method"]} · {c["step_variables"]}</span></div>
            <div class="research-step-pill"><b>04</b><span>{c["report_center"]}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ================================================================
    # STEP 01 — Unified data source
    # ================================================================
    if "workspace_active_source" not in st.session_state:
        st.session_state["workspace_active_source"] = None
    if "workspace_platform_active" not in st.session_state:
        st.session_state["workspace_platform_active"] = "none"

    st.markdown('<div class="research-shell">', unsafe_allow_html=True)
    import_col, platform_col = st.columns([1, 1], gap="large")

    # ---------------- Import own data: modal entry only ----------------
    with import_col:
        imported_df_state = st.session_state.get("workspace_imported_df")
        imported_name = st.session_state.get("workspace_imported_name")
        project_name = st.session_state.get("import_project_name")

        st.markdown(
            f"""
            <div class="source-card-title">
                <span class="source-icon">⇧</span>
                {c["my_data"]}
            </div>
            <div class="source-card-desc">{c["import_card_desc"]}</div>
            """,
            unsafe_allow_html=True,
        )

        if imported_df_state is not None:
            st.markdown(
                f"""
                <div class="import-status-card">
                    <strong>{html.escape(str(project_name or imported_name or c["imported_project"]))}</strong>
                    <span>
                        {html.escape(str(imported_name or ""))}
                        · {len(imported_df_state):,} {c["rows"]}
                        · {len(imported_df_state.columns)} {c["columns"]}
                    </span>
                    <div class="import-status-pill">● {c["import_active"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            r1, r2 = st.columns([1.35, .75])
            with r1:
                if st.button(
                    "⇧ " + c["reimport_data"],
                    use_container_width=True,
                    key="open_reimport_dialog",
                ):
                    _show_data_import_dialog(lang, c)
            with r2:
                if st.button(
                    c["clear_import"],
                    use_container_width=True,
                    key="clear_imported_data",
                ):
                    for key in [
                        "workspace_imported_df",
                        "workspace_imported_name",
                        "workspace_imported_kind",
                        "import_project_name",
                        "import_project_background",
                        "import_project_summary",
                    ]:
                        st.session_state.pop(key, None)
                    if st.session_state.get("workspace_active_source") == "imported":
                        st.session_state["workspace_active_source"] = None
                    st.session_state.pop("workspace_result", None)
                    st.rerun()
        else:
            st.markdown(
                f"""
                <div class="import-status-card">
                    <strong>{c["no_import_yet"]}</strong>
                    <span>
                        {
                            "点击下方按钮后，将以独立浮层窗口完成项目说明、文件上传、模板查看与格式校验。"
                            if lang == "zh"
                            else
                            "Open the modal below to add project notes, upload/paste data, review templates and validate the format."
                        }
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "＋ " + c["open_import_dialog"],
                type="primary",
                use_container_width=True,
                key="open_import_dialog",
            ):
                _show_data_import_dialog(lang, c)

    # ---------------- Platform research database ----------------
    with platform_col:
        st.markdown(
            f"""
            <div class="source-card-title">
                <span class="source-icon">▦</span>
                {c["platform_dataset"]}
            </div>
            <div class="source-card-desc">{c["platform_card_desc"]}</div>
            """,
            unsafe_allow_html=True,
        )

        platform_options = custom_engine.platform_dataset_options(lang)
        option_codes = [x[0] for x in platform_options]
        label_map = dict(platform_options)

        current_platform = st.session_state.get("workspace_platform_active", "none")
        default_platform_idx = (
            option_codes.index(current_platform)
            if current_platform in option_codes
            else 0
        )

        platform_code = st.selectbox(
            c["choose_platform_dataset"],
            option_codes,
            index=default_platform_idx,
            format_func=lambda x: label_map[x],
            key="workspace_platform_dataset_selector",
            label_visibility="collapsed",
        )

        platform_desc = custom_engine.platform_dataset_description(platform_code, lang)
        st.caption(platform_desc)

        fields = custom_engine.platform_dataset_fields(platform_code)
        if fields:
            chips = "".join(
                f'<span class="schema-chip">{html.escape(str(field))}</span>'
                for field in fields
            )
            st.markdown(
                f"""
                <div style="font-size:.68rem;color:#8998A4;margin-top:.35rem">
                    {c["available_fields"]}
                </div>
                <div class="platform-schema">{chips}</div>
                """,
                unsafe_allow_html=True,
            )

        if platform_code != "none":
            use_platform = st.button(
                "▦ " + c["use_platform_dataset"],
                type=(
                    "primary"
                    if st.session_state.get("workspace_active_source") != "platform"
                    or current_platform != platform_code
                    else "secondary"
                ),
                use_container_width=True,
                key="activate_platform_dataset",
            )
            if use_platform:
                st.session_state["workspace_platform_active"] = platform_code
                st.session_state["workspace_active_source"] = "platform"
                st.session_state.pop("workspace_result", None)
                st.rerun()

        if (
            st.session_state.get("workspace_active_source") == "platform"
            and st.session_state.get("workspace_platform_active") != "none"
        ):
            active_code = st.session_state["workspace_platform_active"]
            st.markdown(
                f'<div class="import-status-pill">● {c["platform_active"]}: '
                f'{html.escape(label_map.get(active_code, active_code))}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # ================================================================
    # Resolve current active dataset.
    # ================================================================
    research_df = None
    source_label = None

    try:
        active_source = st.session_state.get("workspace_active_source")

        if active_source == "imported":
            research_df = st.session_state.get("workspace_imported_df")
            source_label = (
                f'{c["source_upload"]} · '
                f'{st.session_state.get("workspace_imported_name", "")}'
            )

        elif active_source == "platform":
            active_platform_code = st.session_state.get(
                "workspace_platform_active",
                "none",
            )
            if active_platform_code != "none":
                research_df = custom_engine.load_platform_dataset(
                    active_platform_code
                )
                source_label = (
                    f'{c["source_platform"]} · '
                    f'{label_map.get(active_platform_code, active_platform_code)}'
                )
    except Exception as exc:
        st.error(f'{c["failed"]}: {exc}')

    # ================================================================
    # STEP 02 — Analysis instruction.
    # It remains visible even before a dataset is available so users
    # may paste a table directly into the instruction.
    # ================================================================
    st.html(
        f"""
        <div class="analysis-command">
            <div class="analysis-command-grid">
                <div>
                    <div class="kicker">02 · ANALYSIS INSTRUCTION</div>
                    <h3>{c["instruction_title"]}</h3>
                    <p>{c["instruction_desc"]}</p>
                </div>

                <div class="analysis-command-examples">
                    <div class="analysis-command-examples-title">
                        {"示例指令" if lang == "zh" else "Example prompts"}
                    </div>
                    <div class="analysis-example-chip">① {c["instruction_example_1"]}</div>
                    <div class="analysis-example-chip">② {c["instruction_example_2"]}</div>
                    <div class="analysis-example-chip">③ {c["instruction_example_3"]}</div>
                    <div class="analysis-example-chip">④ {c["instruction_example_4"]}</div>
                </div>
            </div>
        </div>
        """
    )

    if "workspace_question" not in st.session_state:
        st.session_state["workspace_question"] = ""

    research_question = st.text_area(
        c["instruction_label"],
        key="workspace_question",
        height=150,
        placeholder=c["custom_question_hint"],
        label_visibility="collapsed",
    )
    st.caption(c["instruction_empty_hint"])

    # If no other source exists, attempt table extraction from the question.
    if research_df is None and research_question.strip():
        try:
            embedded = custom_engine.extract_from_question(research_question)
            if embedded is not None:
                research_df = embedded
                source_label = c["source_embedded"]
                st.success(c["embedded_data_detected"])
        except Exception:
            pass

    st.markdown(
        f'<div class="integrity-note">⚖ {c["result_integrity"]}</div>',
        unsafe_allow_html=True,
    )

    if research_df is None:
        st.info(c["need_custom_data"])
    else:
        # ============================================================
        # Data profile + compact preview
        # ============================================================
        profile = custom_engine.profile(research_df)
        st.markdown(
            f'<div class="source-active">● {c["current_source"]}: {html.escape(str(source_label))}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="quality-strip">
                <div class="quality-item"><b>{profile.rows:,}</b><span>{c["rows"]}</span></div>
                <div class="quality-item"><b>{profile.columns}</b><span>{c["columns"]}</span></div>
                <div class="quality-item"><b>{profile.missing_rate:.1%}</b><span>{c["missing_rate"]}</span></div>
                <div class="quality-item"><b>{len(profile.numeric_columns)}</b><span>{c["numeric_count"]}</span></div>
                <div class="quality-item"><b>{len(profile.categorical_columns)}</b><span>{c["categorical_count"]}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "workspace_data_expanded" not in st.session_state:
            st.session_state["workspace_data_expanded"] = False

        ph1, ph2 = st.columns([4.6, 1])
        with ph1:
            st.markdown(f"### {c['data_preview_title']}")
        with ph2:
            label = (
                c["collapse_preview"]
                if st.session_state["workspace_data_expanded"]
                else c["expand_preview"]
            )
            if st.button(label, use_container_width=True, key="workspace_preview_toggle"):
                st.session_state["workspace_data_expanded"] = not st.session_state["workspace_data_expanded"]
                st.rerun()

        st.dataframe(
            research_df.head(50 if st.session_state["workspace_data_expanded"] else 7),
            use_container_width=True,
            hide_index=True,
            height=500 if st.session_state["workspace_data_expanded"] else 255,
        )

        # ============================================================
        # STEP 03 — Method recommendation + variable roles
        # ============================================================
        intent = custom_engine.infer_intent(research_question, research_df)
        method_keys = list(METHODS.keys())
        recommended = intent["method"] if intent["method"] in method_keys else "descriptive"

        st.markdown(
            f"""
            <div class="stage-head" style="margin-top:1.1rem">
                <div class="stage-no">03</div>
                <div>
                    <strong>{c["step_method"]} · {c["step_variables"]}</strong>
                    <small>
                        {
                            "系统根据你的分析指令和变量类型给出推荐，你仍可手动修改。"
                            if lang == "zh"
                            else
                            "The platform recommends a method from your instruction and variable types; you can still override it."
                        }
                    </small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        method_left, method_right = st.columns([.72, 1.28], gap="large")

        with method_left:
            st.markdown(
                f"""
                <div class="method-card">
                    <div class="method-card-label">{c["recommended_method"]}</div>
                    <div class="method-card-value">{html.escape(method_label(recommended, lang))}</div>
                    <div class="method-card-note">
                        {'来自指令 + 数据结构推断' if lang == 'zh' else 'Inferred from instruction + data structure'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with method_right:
            selected_method = st.selectbox(
                c["analysis_method"],
                method_keys,
                index=method_keys.index(recommended),
                format_func=lambda x: method_label(x, lang),
                key="workspace_method",
            )

        method = intent["method"] if selected_method == "auto" else selected_method
        if method == "auto":
            method = recommended

        st.markdown('<div class="variable-panel">', unsafe_allow_html=True)

        cols = list(research_df.columns)
        numeric_cols = profile.numeric_columns
        categorical_cols = profile.categorical_columns

        def _pick_index(options, guess, fallback=0):
            if not options:
                return 0
            if guess in options:
                return options.index(guess)
            return min(fallback, len(options)-1)

        config = {"method": method}

        if method in {"t_test", "mann_whitney", "anova", "kruskal"}:
            a, b = st.columns(2)
            group_opts = categorical_cols or cols
            outcome_opts = numeric_cols or cols
            with a:
                group = st.selectbox(
                    c["group_variable"],
                    group_opts,
                    index=_pick_index(group_opts, intent.get("group")),
                    key="workspace_group",
                )
            with b:
                outcome = st.selectbox(
                    c["outcome_variable"],
                    outcome_opts,
                    index=_pick_index(outcome_opts, intent.get("outcome")),
                    key="workspace_outcome",
                )
            config.update(group=group, outcome=outcome)

        elif method in {"paired_t", "wilcoxon", "pearson", "spearman"}:
            a, b = st.columns(2)
            opts = numeric_cols or cols
            with a:
                x = st.selectbox(
                    c["x_variable"],
                    opts,
                    index=_pick_index(opts, intent.get("x"), 0),
                    key="workspace_x",
                )
            with b:
                y = st.selectbox(
                    c["y_variable"],
                    opts,
                    index=_pick_index(opts, intent.get("y"), 1),
                    key="workspace_y",
                )
            config.update(x=x, y=y)

        elif method in {"chi_square", "fisher"}:
            a, b = st.columns(2)
            opts = categorical_cols or cols
            with a:
                group = st.selectbox(
                    c["group_variable"],
                    opts,
                    index=_pick_index(opts, intent.get("group"), 0),
                    key="workspace_cat_group",
                )
            with b:
                outcome = st.selectbox(
                    c["outcome_variable"],
                    opts,
                    index=_pick_index(opts, intent.get("outcome"), 1),
                    key="workspace_cat_outcome",
                )
            config.update(group=group, outcome=outcome)

        elif method in {"linear_regression", "logistic_regression"}:
            a, b = st.columns([.8, 1.2])
            if method == "linear_regression":
                outcome_opts = numeric_cols or cols
            else:
                outcome_opts = [
                    col for col in cols
                    if 1 < research_df[col].nunique(dropna=True) <= 2
                ] or cols
            with a:
                outcome = st.selectbox(
                    c["outcome_variable"],
                    outcome_opts,
                    index=_pick_index(outcome_opts, intent.get("outcome"), 0),
                    key="workspace_reg_outcome",
                )
            with b:
                pred_opts = [x for x in cols if x != outcome]
                default_preds = [x for x in intent.get("predictors", []) if x in pred_opts]
                predictors = st.multiselect(
                    c["predictors"],
                    pred_opts,
                    default=default_preds[:6],
                    key="workspace_predictors",
                )
            config.update(outcome=outcome, predictors=predictors)

        elif method in {"survival", "cox"}:
            a, b, d = st.columns(3)
            numeric_opts = numeric_cols or cols
            binary_opts = [
                x for x in cols
                if 1 < research_df[x].nunique(dropna=True) <= 2
            ] or cols
            with a:
                time_col = st.selectbox(
                    c["time_variable"],
                    numeric_opts,
                    index=_pick_index(numeric_opts, intent.get("time"), 0),
                    key="workspace_time",
                )
            with b:
                event_col = st.selectbox(
                    c["event_variable"],
                    binary_opts,
                    index=_pick_index(binary_opts, intent.get("event"), 0),
                    key="workspace_event",
                )
            with d:
                group_opts = [c["no_group"]] + (categorical_cols or cols)
                group_display = st.selectbox(
                    c["group_variable"],
                    group_opts,
                    index=_pick_index(group_opts, intent.get("group"), 0),
                    key="workspace_survival_group",
                )
                group = None if group_display == c["no_group"] else group_display
            config.update(time=time_col, event=event_col, group=group)

            if method == "cox":
                pred_opts = [
                    x for x in cols
                    if x not in {time_col, event_col}
                ]
                predictors = st.multiselect(
                    c["predictors"],
                    pred_opts,
                    default=[x for x in intent.get("predictors", []) if x in pred_opts][:6],
                    key="workspace_cox_predictors",
                )
                config["predictors"] = predictors

        else:
            st.caption(
                "描述性统计将自动汇总全部变量。"
                if lang == "zh"
                else "Descriptive statistics will summarize all variables automatically."
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # Run
        # ============================================================
        st.markdown('<div class="run-panel">', unsafe_allow_html=True)
        run_analysis = st.button(
            "✦ " + c["run_analysis_now"],
            type="primary",
            use_container_width=True,
            key="workspace_run_analysis",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if run_analysis:
            try:
                result = custom_engine.analyze(research_df, config, lang)
                report_html = custom_engine.build_html_report(
                    research_df,
                    config,
                    result,
                    research_question,
                    lang,
                )
                st.session_state["workspace_result"] = {
                    "df": research_df,
                    "config": config,
                    "result": result,
                    "question": research_question,
                    "report_html": report_html,
                    "source_label": source_label,
                }
                st.session_state["workspace_chart_expanded"] = False
            except Exception as exc:
                st.error(f'{c["failed"]}: {exc}')

        # ============================================================
        # STEP 04 — Result priority
        # ============================================================
        payload = st.session_state.get("workspace_result")
        if payload:
            result = payload["result"]
            chart_bytes = base64.b64decode(result["image"])
            report_html = payload["report_html"]

            st.markdown(
                f"""
                <div class="report-hero">
                    <small>04 · ANALYSIS RESULT</small>
                    <h2>{c["report_center"]}</h2>
                    <p>{c["report_center_desc"]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            r1, r2, r3 = st.columns([1.3, .65, .65])
            r1.metric(c["method"], result["method"])
            r2.metric(
                c["p"],
                "N/A" if result.get("p") is None else f'{result["p"]:.4g}',
            )
            r3.metric("N", len(payload["df"]))

            act1, act2, act3 = st.columns([1, 1.05, 1.25])
            with act1:
                if st.button(
                    c["expand_chart"] if not st.session_state.get("workspace_chart_expanded", False) else c["collapse_chart"],
                    use_container_width=True,
                    key="workspace_chart_toggle",
                ):
                    st.session_state["workspace_chart_expanded"] = not st.session_state.get("workspace_chart_expanded", False)
                    st.rerun()
            with act2:
                st.download_button(
                    "↓ " + c["export_chart"],
                    chart_bytes,
                    "haiyan_analysis_chart.png",
                    "image/png",
                    use_container_width=True,
                    key="workspace_export_png",
                )
            with act3:
                st.download_button(
                    "↓ " + c["report_export"],
                    report_html.encode("utf-8"),
                    "haiyan_analysis_report.html",
                    "text/html",
                    use_container_width=True,
                    key="workspace_export_report",
                )

            if st.session_state.get("workspace_chart_expanded", False):
                st.image(chart_bytes, use_container_width=True)
                st.dataframe(
                    pd.DataFrame(result["summary"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                chart_col, side_col = st.columns([1.25, .75], gap="large")
                with chart_col:
                    st.image(chart_bytes, use_container_width=True)
                with side_col:
                    st.markdown(f"**{c['conclusion']}**")
                    st.markdown(
                        f'<div class="insight-box">✦ {html.escape(result["conclusion"])}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{c['summary']}**")
                    st.dataframe(
                        pd.DataFrame(result["summary"]),
                        use_container_width=True,
                        hide_index=True,
                        height=250,
                    )

            e1, e2 = st.columns(2)
            with e1:
                st.download_button(
                    c["download"],
                    payload["df"].to_csv(index=False).encode("utf-8-sig"),
                    "haiyan_analysis_data.csv",
                    "text/csv",
                    use_container_width=True,
                    key="workspace_export_data",
                )
            with e2:
                st.download_button(
                    c["export_summary"],
                    pd.DataFrame(result["summary"]).to_csv(index=False).encode("utf-8-sig"),
                    "haiyan_analysis_summary.csv",
                    "text/csv",
                    use_container_width=True,
                    key="workspace_export_summary",
                )

# -------------------------------------------------------------------
# TEMPLATE CENTER
# -------------------------------------------------------------------
elif st.session_state.page == "templates":
    st.markdown(
        f"""
        <div class="workspace-head">
            <div class="wk">RESEARCH ASSET LIBRARY</div>
            <h1>{c["template_center"]}</h1>
            <p>{c["template_center_desc"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    items = ts.list()
    if not items:
        st.info(c["no_templates"])
    else:
        for item in reversed(items):
            title = html.escape(str(item.get("template_name", "-")))
            created = html.escape(str(item.get("created_at", "-")))
            question = html.escape(str(item.get("plan", {}).get("original_query", "-")))
            st.markdown(
                f"""
                <div class="template-card">
                    <strong>{title}</strong><br>
                    <small>{c["created"]}: {created}<br>{c["original_q"]}: {question}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

# -------------------------------------------------------------------
# ABOUT
# -------------------------------------------------------------------
elif st.session_state.page == "about":
    st.markdown(
        f"""
        <div class="workspace-head">
            <div class="wk">{c["public_demo"]}</div>
            <h1>{c["about_title"]}</h1>
            <p>{c["about_desc"]}</p>
        </div>

        <div class="about-card">
            <h3>Research architecture</h3>
            <p>Natural Language → Medical Concepts → ResearchPlan → Controlled SQL → Cohort → Cleaning → Statistical Decision → Research Result → Template</p>
        </div>

        <div class="about-card">
            <h3>{c["safety_title"]}</h3>
            <p>{c["safety_desc"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# SETTINGS
# -------------------------------------------------------------------
elif st.session_state.page == "settings":
    st.markdown(
        f"""
        <div class="workspace-head">
            <div class="wk">PLATFORM SETTINGS</div>
            <h1>{c["settings_title"]}</h1>
            <p>{c["settings_desc"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------
    # Account / guest mode
    # --------------------------------------------------------------
    if "guest_logged_in" not in st.session_state:
        st.session_state["guest_logged_in"] = False

    st.markdown(f'<div class="settings-section-title">{c["account_section"]}</div>', unsafe_allow_html=True)
    account_left, account_right = st.columns([1.7, .8])

    with account_left:
        guest_status = (
            c["logged_guest"]
            if st.session_state["guest_logged_in"]
            else c["guest_desc"]
        )
        st.markdown(
            f"""
            <div class="settings-card">
                <h3>👤 {c["guest_mode"]}</h3>
                <p>{guest_status}</p>
                <div style="margin-top:.7rem">
                    <span class="status-pill">● {c["guest_mode"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with account_right:
        st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
        if not st.session_state["guest_logged_in"]:
            if st.button(
                c["login"],
                type="primary",
                use_container_width=True,
                key="guest_login_btn",
            ):
                st.session_state["guest_logged_in"] = True
                st.rerun()
        else:
            st.success(c["logged_guest"])
            if st.button(
                c["logout_guest"],
                use_container_width=True,
                key="guest_logout_btn",
            ):
                st.session_state["guest_logged_in"] = False
                st.rerun()
        st.caption(c["login_note"])

    # --------------------------------------------------------------
    # Language / Template management / API
    # --------------------------------------------------------------
    st.markdown(
        f'<div class="settings-section-title">{c["language_section"]}</div>',
        unsafe_allow_html=True,
    )

    left_settings, right_settings = st.columns([1, 1], gap="large")

    # ==============================================================
    # LEFT COLUMN: Language + Research Templates
    # ==============================================================
    with left_settings:
        # ---------------- Language card ----------------
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="margin-bottom:.75rem">
                    <div style="font-size:1rem;font-weight:850;color:#10243E;margin-bottom:.35rem">
                        🌐 {c["language_section"]}
                    </div>
                    <div style="font-size:.82rem;line-height:1.65;color:#708196">
                        {c["language_desc"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            current_language = st.session_state.get("language_top", "中文")
            settings_language = st.selectbox(
                c["language_section"],
                ["中文", "English"],
                index=0 if current_language == "中文" else 1,
                key="settings_language_choice",
                label_visibility="collapsed",
            )

            if settings_language != current_language:
                st.session_state["language_top"] = settings_language
                st.rerun()

            lang_status = (
                "当前语言：中文"
                if settings_language == "中文" and lang == "zh"
                else (
                    "Current language: English"
                    if settings_language == "English" and lang == "en"
                    else settings_language
                )
            )
            st.caption("● " + lang_status)

        # ---------------- Template management compact card ----------------
        st.markdown("<div style='height:.65rem'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="margin-bottom:.7rem">
                    <div style="font-size:1rem;font-weight:850;color:#10243E;margin-bottom:.35rem">
                        🗂 {c["template_manage"]}
                    </div>
                    <div style="font-size:.82rem;line-height:1.65;color:#708196">
                        {c["template_manage_desc"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            managed_templates = ts.list()

            if not managed_templates:
                st.markdown(
                    f"""
                    <div class="template-empty-state">
                        <div class="template-empty-icon">＋</div>
                        <div class="template-empty-title">{c["no_saved_templates"]}</div>
                        <div class="template-empty-sub">
                            {'完成一次科研分析并保存后，模板会显示在这里。' if lang == 'zh' else 'Saved analysis templates will appear here after you complete and save a research analysis.'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # Show up to the latest 3 templates in compact mode.
                for idx, item in enumerate(reversed(managed_templates[-3:])):
                    file_name = item.get("_file_name", "")
                    template_name = item.get("template_name", "Unnamed")
                    created_at = item.get("created_at", "-")
                    question = item.get("plan", {}).get("original_query", "-")

                    st.markdown(
                        f"""
                        <div class="template-mini-row">
                            <div class="template-mini-main">
                                <div class="template-mini-name">{html.escape(str(template_name))}</div>
                                <div class="template-mini-meta">
                                    {c["created"]}: {html.escape(str(created_at))}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    with st.expander(
                        f'{c["template_manage"]} · {template_name}',
                        expanded=False,
                    ):
                        st.caption(
                            f'{c["original_q"]}: {question}'
                        )

                        rename_col, delete_col = st.columns([1.55, .75])

                        with rename_col:
                            new_name = st.text_input(
                                c["new_name"],
                                value=str(template_name),
                                key=f"rename_template_compact_{idx}",
                            )
                            if st.button(
                                c["rename"],
                                key=f"rename_btn_compact_{idx}",
                                use_container_width=True,
                            ):
                                try:
                                    ts.rename(file_name, new_name)
                                    st.success(c["template_renamed"])
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))

                        with delete_col:
                            confirm = st.checkbox(
                                c["confirm_delete"],
                                key=f"confirm_delete_compact_{idx}",
                            )
                            if st.button(
                                c["delete"],
                                key=f"delete_template_compact_{idx}",
                                disabled=not confirm,
                                use_container_width=True,
                            ):
                                if ts.delete(file_name):
                                    st.success(c["template_deleted"])
                                    st.rerun()

                if len(managed_templates) > 3:
                    st.caption(
                        (
                            f"当前共保存 {len(managed_templates)} 个模板，这里显示最近 3 个。"
                            if lang == "zh"
                            else f"{len(managed_templates)} templates saved; showing the 3 most recent."
                        )
                    )

    # ==============================================================
    # RIGHT COLUMN: API configuration
    # ==============================================================
    with right_settings:
        with st.container(border=True):
            api_detected = bool(os.getenv("OPENAI_API_KEY"))
            api_status_text = (
                c["api_configured"]
                if api_detected
                else c["api_not_configured"]
            )

            st.markdown(
                f"""
                <div style="margin-bottom:.7rem">
                    <div style="font-size:1rem;font-weight:850;color:#10243E;margin-bottom:.35rem">
                        ⌘ {c["api_section"]}
                    </div>
                    <div style="font-size:.82rem;line-height:1.65;color:#708196">
                        {c["api_desc"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption("● " + api_status_text)

            provider = st.selectbox(
                c["api_provider"],
                ["OpenAI", "Other / Custom"],
                key="settings_api_provider",
            )

            model_name = st.text_input(
                c["api_model"],
                value=st.session_state.get(
                    "api_demo_model",
                    "gpt-5.6-luna",
                ),
                key="settings_api_model",
            )

            demo_key = st.text_input(
                c["api_key_placeholder"],
                value="",
                type="password",
                key="settings_api_key_demo",
                placeholder="sk-••••••••••••••••",
            )

            if st.button(
                c["api_save_demo"],
                key="settings_api_save_demo",
                type="primary",
                use_container_width=True,
            ):
                # Interface demonstration only.
                # Credentials are deliberately not persisted.
                st.session_state["api_demo_provider"] = provider
                st.session_state["api_demo_model"] = model_name
                st.session_state["api_demo_key_entered"] = bool(demo_key)
                st.success(c["api_demo_saved"])

            st.markdown(
                f"""
                <div class="api-note-box">
                    <div class="api-note-title">
                        {'配置说明' if lang == 'zh' else 'Configuration note'}
                    </div>
                    <div class="api-note-text">
                        {
                            '当前入口用于展示平台的模型配置能力。未配置 API 时，平台仍可使用本地规则解析与现有演示功能。'
                            if lang == 'zh'
                            else
                            'This panel demonstrates model configuration. Without an API, the platform continues to use local rule parsing and existing demo functions.'
                        }
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------------
    # Privacy + system
    # --------------------------------------------------------------
    st.markdown(f'<div class="settings-section-title">{c["privacy_section"]}</div>', unsafe_allow_html=True)

    privacy_col, system_col = st.columns(2)

    with privacy_col:
        st.markdown(
            f"""
            <div class="settings-card">
                <h3>🔒 {c["privacy_section"]}</h3>
                <p>{c["privacy_desc"]}</p>
                <div class="mini-list" style="margin-top:.8rem">
                    <span class="mini-chip">✓ {c["privacy_point1"]}</span>
                    <span class="mini-chip">✓ {c["privacy_point2"]}</span>
                    <span class="mini-chip">✓ {c["privacy_point3"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with system_col:
        st.markdown(
            f"""
            <div class="settings-card">
                <h3>◫ {c["system_section"]}</h3>
                <p>
                    <strong>{c["version"]}:</strong> {c["version_value"]}<br>
                    <strong>{c["runtime"]}:</strong> {c["runtime_value"]}<br>
                    <strong>{c["data_mode"]}:</strong> {c["data_mode_value"]}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f'<div class="settings-section-title">{c["danger_section"]}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="about-card">
            <h3>🗂 {c["danger_section"]}</h3>
            <p>{c["danger_desc"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="footer-note">Medical Research Copilot · Synthetic data research prototype · Not for clinical decision making</div>',
    unsafe_allow_html=True,
)

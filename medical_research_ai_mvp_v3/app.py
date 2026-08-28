from pathlib import Path
import base64
import html
import pandas as pd
import streamlit as st

from i18n import tr
from research_agent import ResearchAgent
from query_engine import QueryEngine
from stats_engine import StatsEngine
from template_store import TemplateStore

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
        padding-top:.7rem;
        padding-bottom:4rem;
    }

    [data-testid="stSidebar"] { display:none; }
    [data-testid="stHeader"] {
        background:rgba(255,255,255,.82);
        backdrop-filter:blur(12px);
    }
    [data-testid="stToolbar"] { visibility:hidden; height:0; }

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
    return ResearchAgent(), QueryEngine(), StatsEngine(), TemplateStore()

agent, qe, se, ts = services()

# -------------------------------------------------------------------
# Language + top navigation
# -------------------------------------------------------------------
lang_col, _ = st.columns([1, 5])
with lang_col:
    language = st.selectbox(
        "Language / 语言",
        ["中文", "English"],
        index=0,
        label_visibility="collapsed",
        key="language_top",
    )
lang = "zh" if language == "中文" else "en"
c = COPY[lang]

# Header row: brand + native navigation controls
brand_col, nav1, nav2, nav3, nav4 = st.columns([5.4, 1, 1.15, 1.15, 1])
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

st.markdown('<div style="height:.5rem;border-bottom:1px solid #E9EFF3;margin-bottom:.4rem"></div>', unsafe_allow_html=True)

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
            """
            <div class="visual-shell">
                <div class="visual-grid"></div>
                <div class="link l1"></div><div class="link l2"></div><div class="link l3"></div>
                <div class="dot a"></div><div class="dot b"></div><div class="dot c"></div>
                <div class="center-orbit">RESEARCH<br>AGENT</div>

                <div class="mini-card v-agent">
                    <div class="mini-label">Natural language → ResearchPlan</div>
                    <div class="mini-value">NSCLC · EGFR MUT · OS</div>
                    <div style="margin-top:.55rem;font-size:.7rem;color:#7B8C9B">Semantic parsing completed ✓</div>
                </div>

                <div class="mini-card v-cohort">
                    <div class="mini-label">Cohort discovery</div>
                    <div class="mini-value">412 eligible patients</div>
                    <div class="spark">
                        <i></i><i></i><i></i><i></i><i></i><i></i><i></i>
                    </div>
                </div>

                <div class="mini-card v-chart">
                    <div class="mini-label">Kaplan-Meier survival</div>
                    <div class="mini-value">Log-rank P = 0.003</div>
                    <svg class="curve" viewBox="0 0 220 55">
                        <path d="M4 7 H36 V13 H69 V20 H103 V26 H139 V34 H174 V41 H215 V46" fill="none" stroke="#1FAF9A" stroke-width="3"/>
                        <path d="M4 8 H32 V18 H62 V25 H96 V35 H133 V39 H172 V48 H215 V51" fill="none" stroke="#4D7DFF" stroke-width="2.5"/>
                        <line x1="3" y1="52" x2="216" y2="52" stroke="#DDE6EC"/>
                    </svg>
                </div>

                <div class="mini-card v-model">
                    <div class="mini-label">Adjusted model</div>
                    <div class="mini-value">Cox PH · HR 0.71</div>
                    <div style="margin-top:.5rem;height:7px;background:#EEF3F6;border-radius:99px;overflow:hidden">
                        <div style="width:71%;height:100%;background:#8166E8;border-radius:99px"></div>
                    </div>
                    <div style="margin-top:.45rem;font-size:.68rem;color:#7B8C9B">95% CI 0.56–0.90</div>
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
    st.markdown(
        f"""
        <div class="workspace-head">
            <div class="wk">{c["workspace_badge"]}</div>
            <h1>{c["workspace_title"]}</h1>
            <p>{c["workspace_desc"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    existing = ts.list()
    template_names = [c["none"]] + [item["template_name"] for item in existing]

    st.markdown(
        f"""
        <div class="project-card">
            <div class="project-card-title">
                <span class="tiny-icon">＋</span>
                {c["workspace_title"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([1.15, .85])
    with col_a:
        example_name = st.selectbox(c["example"], list(EXAMPLES[lang].keys()), key=f"example_{lang}")
    with col_b:
        selected_template = st.selectbox(c["load_template"], template_names, key=f"tpl_{lang}")

    selected_payload = None
    if selected_template != c["none"]:
        selected_payload = next(
            (x for x in existing if x["template_name"] == selected_template),
            None,
        )

    default_query = EXAMPLES[lang][example_name]
    if selected_payload:
        default_query = selected_payload["plan"].get("original_query", default_query)

    query = st.text_area(
        c["question"],
        value=default_query,
        height=125,
        help=c["question_hint"],
        key=f"research_question_{lang}_{example_name}_{selected_template}",
    )

    run = st.button(
        "✦  " + c["run"],
        type="primary",
        use_container_width=True,
        key="run_analysis",
    )

    if run:
        try:
            plan = agent.plan(query, lang)

            # ---- Stage 1
            st.markdown(
                f"""
                <div class="stage-head">
                    <div class="stage-no">01</div>
                    <div><strong>{c["stage1"]}</strong><small>{c["stage1_desc"]}</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="project-card">', unsafe_allow_html=True)
            for item in plan.explanation:
                st.markdown(f"**✓** {html.escape(item)}")
            with st.expander(c["structured"]):
                st.json(plan.to_dict())
            st.markdown("</div>", unsafe_allow_html=True)

            # ---- Stage 2
            df, sql = qe.run(plan.to_dict())
            st.markdown(
                f"""
                <div class="stage-head">
                    <div class="stage-no">02</div>
                    <div><strong>{c["stage2"]}</strong><small>{c["stage2_desc"]}</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            m1, m2, m3 = st.columns(3)
            m1.metric(c["included"], len(df))
            m2.metric(c["groups"], df["regimen"].nunique() if not df.empty else 0)
            m3.metric(c["endpoint"], plan.endpoint or "-")
            with st.expander(c["sql"]):
                st.code(sql, language="sql")
            if df.empty:
                st.warning(c["empty"])
                st.stop()
            st.markdown(f"**{c['data_preview']}**")
            st.dataframe(df.head(50), use_container_width=True, hide_index=True)

            # ---- Stage 3
            result = se.analyze(df, plan.to_dict(), lang)
            if "error" in result:
                st.error(result["error"])
                st.stop()

            st.markdown(
                f"""
                <div class="stage-head">
                    <div class="stage-no">03</div>
                    <div><strong>{c["stage3"]}</strong><small>{c["stage3_desc"]}</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            r1, r2 = st.columns([1.55, .65])
            r1.metric(c["method"], result["method"])
            r2.metric(c["p"], f'{result["p"]:.4g}')

            chart_col, summary_col = st.columns([1.18, .82], gap="large")
            with chart_col:
                st.image(base64.b64decode(result["image"]), use_container_width=True)
            with summary_col:
                st.markdown(f"**{c['summary']}**")
                st.dataframe(
                    pd.DataFrame(result["summary"]),
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown(f"**{c['conclusion']}**")
            st.markdown(
                f'<div class="insight-box">✦ {html.escape(result["conclusion"])}</div>',
                unsafe_allow_html=True,
            )

            if result.get("cox"):
                st.markdown(f"**{c['cox']}**")
                st.dataframe(
                    pd.DataFrame(result["cox"]),
                    use_container_width=True,
                    hide_index=True,
                )

            st.download_button(
                c["download"],
                df.to_csv(index=False).encode("utf-8-sig"),
                "analysis_data.csv",
                "text/csv",
                use_container_width=True,
            )

            # ---- Stage 4
            st.markdown(
                f"""
                <div class="stage-head">
                    <div class="stage-no">04</div>
                    <div><strong>{c["stage4"]}</strong><small>{c["stage4_desc"]}</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            template_name = st.text_input(
                c["template_name"],
                value=f"{plan.disease or 'research'}_{plan.endpoint or 'analysis'}",
                key="save_template_name",
            )
            if st.button(c["save"], use_container_width=True, key="save_template_btn"):
                path = ts.save(template_name, plan.to_dict(), sql)
                st.success(f'{c["saved"]}: {path.name}')

            st.caption(c["template_note"])

        except Exception as exc:
            st.error(f'{c["failed"]}: {exc}')

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
else:
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

st.markdown(
    '<div class="footer-note">Medical Research Copilot · Synthetic data research prototype · Not for clinical decision making</div>',
    unsafe_allow_html=True,
)

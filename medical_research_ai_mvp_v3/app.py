from pathlib import Path
import base64
import pandas as pd
import streamlit as st
from i18n import tr
from research_agent import ResearchAgent
from query_engine import QueryEngine
from stats_engine import StatsEngine
from template_store import TemplateStore

DB_PATH=Path(__file__).resolve().parent/"data"/"medical_demo.db"
if not DB_PATH.exists():
    from generate_demo_data import main as generate_data
    generate_data()

st.set_page_config(page_title="Medical Research Copilot",page_icon="🧬",layout="wide",initial_sidebar_state="expanded")
st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#f6fbff 0%,#fff 34%)}
.block-container{max-width:1450px;padding-top:1.2rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#f7fafc;border-right:1px solid #dfe8ef}
.hero{background:#fff;border:1px solid #dfe8ef;border-radius:18px;padding:1.25rem 1.5rem;margin-bottom:.85rem}
.eyebrow{font-size:.75rem;font-weight:800;letter-spacing:.1em;color:#155b8e;margin-bottom:.35rem}
.hero h1{font-size:1.9rem;margin:0;color:#17212b;line-height:1.25}.hero p{color:#66798b;margin:.5rem 0 0}
.status{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.4rem 0 1rem}
.card{background:#fff;border:1px solid #dfe8ef;border-radius:13px;padding:.8rem .9rem}.label{color:#66798b;font-size:.75rem}.value{font-weight:750;color:#17212b;margin-top:.15rem}
.section{display:flex;gap:.55rem;align-items:center;margin:1rem 0 .55rem}.num{width:30px;height:30px;border-radius:9px;background:#eaf3fa;color:#155b8e;display:inline-flex;align-items:center;justify-content:center;font-weight:800}.stitle{font-size:1.08rem;font-weight:800;color:#17212b}
.flow{display:flex;gap:.45rem;flex-wrap:wrap;margin:.3rem 0 .9rem}.flow span{background:#fff;border:1px solid #dfe8ef;border-radius:999px;padding:.4rem .68rem;font-size:.82rem;color:#3d5264}
.info-card{background:#fff;border:1px solid #dfe8ef;border-radius:14px;padding:1rem;margin-bottom:.65rem}
@media(max-width:900px){.status{grid-template-columns:repeat(2,1fr)}.hero h1{font-size:1.55rem}}@media(max-width:520px){.status{grid-template-columns:1fr}}
</style>
""",unsafe_allow_html=True)

@st.cache_resource
def services():
    return ResearchAgent(),QueryEngine(),StatsEngine(),TemplateStore()
agent,qe,se,ts=services()

EXAMPLES={
"zh":{
"肺癌：EGFR突变患者生存分析":"筛选出近三年所有非小细胞肺癌且EGFR突变的患者，对比不同治疗方案的生存期",
"乳腺癌：HER2阳性患者生存分析":"筛选近四年HER2阳性乳腺癌患者，对比不同治疗方案的生存期",
"结直肠癌：KRAS突变患者生存分析":"筛选近三年KRAS突变结直肠癌患者，对比不同治疗方案的生存期",
"糖尿病：不同方案HbA1c比较":"筛选近三年2型糖尿病患者，比较不同治疗方案治疗后的HbA1c水平",
"高血压：不同方案血压控制率":"筛选近三年高血压患者，比较不同治疗方案的血压控制率"},
"en":{
"Lung cancer: EGFR-mutant survival":"Identify patients with NSCLC and EGFR mutations in the past 3 years and compare overall survival across treatment regimens",
"Breast cancer: HER2-positive survival":"Identify HER2-positive breast cancer patients in the past 4 years and compare survival across treatment regimens",
"Colorectal cancer: KRAS-mutant survival":"Identify KRAS-mutant colorectal cancer patients in the past 3 years and compare survival across treatment regimens",
"Diabetes: follow-up HbA1c":"Identify type 2 diabetes patients in the past 3 years and compare follow-up HbA1c across treatment regimens",
"Hypertension: BP control":"Identify hypertension patients in the past 3 years and compare blood pressure control rates across treatment regimens"}}

with st.sidebar:
    language=st.selectbox("🌐 Language / 语言",["中文","English"],index=0)
lang="zh" if language=="中文" else "en"; t=lambda k:tr(lang,k)
with st.sidebar:
    nav=st.radio("Nav",[t("workspace"),t("templates"),t("about")],label_visibility="collapsed")
    st.markdown("---")
    existing=ts.list(); names=[t("none")]+[x["template_name"] for x in existing]
    selected=st.selectbox(t("load_template"),names)
    selected_payload=next((x for x in existing if x["template_name"]==selected),None) if selected!=t("none") else None
    st.caption(t("cloud_note"))

st.markdown(f'<div class="hero"><div class="eyebrow">MEDICAL RESEARCH COPILOT · PUBLIC DEMO V3</div><h1>{t("title")}</h1><p>{t("subtitle")}</p></div>',unsafe_allow_html=True)
st.markdown(
    '<div class="status">'
    f'<div class="card"><div class="label">{t("status")}</div><div class="value">● {t("ready")}</div></div>'
    f'<div class="card"><div class="label">{t("db")}</div><div class="value">{t("db_value")}</div></div>'
    f'<div class="card"><div class="label">{t("language")}</div><div class="value">{language}</div></div>'
    f'<div class="card"><div class="label">{t("agent")}</div><div class="value">{t("agent_value")}</div></div>'
    '</div>',unsafe_allow_html=True)

if nav==t("workspace"):
    keys=list(EXAMPLES[lang]); example=st.selectbox(t("example"),keys); default=EXAMPLES[lang][example]
    if selected_payload: default=selected_payload["plan"]["original_query"]
    query=st.text_area(t("question"),value=default,height=110,key=f"q_{lang}_{example}_{selected}")
    st.markdown('<div class="flow"><span>1 · NL → ResearchPlan</span><span>2 · Multi-table cohort</span><span>3 · Statistical decision</span><span>4 · Result & template</span></div>',unsafe_allow_html=True)
    if st.button("▶ "+t("run"),type="primary",use_container_width=True):
        try:
            plan=agent.plan(query,lang)
            st.markdown(f'<div class="section"><span class="num">01</span><span class="stitle">{t("plan")}</span></div>',unsafe_allow_html=True)
            for item in plan.explanation: st.write("•",item)
            with st.expander(t("structured")): st.json(plan.to_dict())
            df,sql=qe.run(plan.to_dict())
            st.markdown(f'<div class="section"><span class="num">02</span><span class="stitle">{t("cohort")}</span></div>',unsafe_allow_html=True)
            c1,c2,c3=st.columns(3); c1.metric(t("included"),len(df)); c2.metric(t("groups"),df["regimen"].nunique() if not df.empty else 0); c3.metric(t("endpoint"),plan.endpoint or "-")
            with st.expander(t("sql")): st.code(sql,language="sql")
            if df.empty: st.warning(t("empty")); st.stop()
            st.markdown("**"+t("data_preview")+"**"); st.dataframe(df.head(50),use_container_width=True,hide_index=True)
            result=se.analyze(df,plan.to_dict(),lang)
            if "error" in result: st.error(result["error"]); st.stop()
            st.markdown(f'<div class="section"><span class="num">03</span><span class="stitle">{t("statistics")}</span></div>',unsafe_allow_html=True)
            m1,m2=st.columns(2); m1.metric(t("method"),result["method"]); m2.metric(t("p"),f'{result["p"]:.4g}')
            st.image(base64.b64decode(result["image"])); st.markdown("**"+t("summary")+"**"); st.dataframe(pd.DataFrame(result["summary"]),use_container_width=True,hide_index=True)
            st.markdown("**"+t("conclusion")+"**"); st.info(result["conclusion"])
            if result.get("cox"): st.markdown("**"+t("cox")+"**"); st.dataframe(pd.DataFrame(result["cox"]),use_container_width=True,hide_index=True)
            st.download_button(t("download"),df.to_csv(index=False).encode("utf-8-sig"),"analysis_data.csv","text/csv",use_container_width=True)
            st.markdown(f'<div class="section"><span class="num">04</span><span class="stitle">{t("asset")}</span></div>',unsafe_allow_html=True)
            name=st.text_input(t("template_name"),value=f"{plan.disease or 'research'}_{plan.endpoint or 'analysis'}")
            if st.button(t("save"),use_container_width=True):
                path=ts.save(name,plan.to_dict(),sql); st.success(f'{t("saved")}: {path.name}')
        except Exception as exc:
            st.error(f'{t("failed")}: {exc}')
elif nav==t("templates"):
    st.markdown("### "+t("template_center")); st.caption(t("template_desc")); items=ts.list()
    if not items: st.info(t("no_templates"))
    for item in reversed(items):
        st.markdown(f'<div class="info-card"><strong>{item.get("template_name","-")}</strong><br><small>{t("created")}: {item.get("created_at","-")}<br>{t("original_q")}: {item.get("plan",{}).get("original_query","-")}</small></div>',unsafe_allow_html=True)
else:
    st.markdown("### "+t("about")); st.markdown(f'<div class="info-card"><p>{t("about_intro")}</p></div>',unsafe_allow_html=True); st.markdown(f'<div class="info-card"><strong>Core flow</strong><p>{t("flow")}</p></div>',unsafe_allow_html=True); st.markdown(f'<div class="info-card"><strong>{t("safety")}</strong><p>{t("safety_text")}</p></div>',unsafe_allow_html=True)

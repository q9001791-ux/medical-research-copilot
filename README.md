# 医疗科研数据自助式挖掘与智能分析平台 V3

V3新增：
- 公网部署结构（Streamlit Community Cloud）
- 默认中文 / English切换
- 多疾病模拟数据库
- 多种统计类型自动选择

内置场景：
1. NSCLC + EGFR突变 → KM / Log-rank / Cox
2. HER2阳性乳腺癌 → KM / Log-rank / Cox
3. KRAS突变结直肠癌 → KM / Log-rank / Cox
4. 2型糖尿病 → HbA1c连续变量比较 → ANOVA / Kruskal-Wallis
5. 高血压 → 血压控制率 → Chi-square

本地启动：
`py generate_demo_data.py`
`py -m streamlit run app.py`

公网部署见 `DEPLOYMENT_GUIDE.md`。
本地清理见 `UNINSTALL_GUIDE.md`。

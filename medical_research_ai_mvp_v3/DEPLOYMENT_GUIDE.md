# 公网部署指南：Streamlit Community Cloud

部署后，其他人无需安装 Python，只需要打开你的 `*.streamlit.app` 链接。

## 准备
1. 注册/登录 GitHub。
2. 新建 repository，例如 `medical-research-copilot-demo`。
3. 把本项目所有文件上传到仓库根目录。
4. 登录 Streamlit Community Cloud，并使用 GitHub 授权。

## 创建应用
1. 点击 Create app。
2. 选择你的 GitHub repository。
3. Main file path 填 `app.py`。
4. Advanced settings 选择 Python 3.12。
5. 当前版本无需填写 Secrets。
6. 点击 Deploy。

部署成功后会得到类似：
`https://your-app-name.streamlit.app`

## 重要说明
- 当前患者全部是程序生成的模拟数据，可用于公开演示。
- 不要把真实患者数据上传到公开 GitHub 或公共 Demo。
- Community Cloud 上的本地文件不应当作为永久数据库；多人长期保存科研模板时，应改为 PostgreSQL/Supabase/医院内网数据库。

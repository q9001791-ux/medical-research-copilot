# 本地卸载与清理指南

## 删除项目、模拟数据库、科研模板
停止 Streamlit（CMD 中按 `Ctrl+C`），然后直接删除整个项目文件夹。
项目里的 `data/medical_demo.db` 和 `templates/` 会一起删除。

## Python 不需要一起删
你当前的 Python 位于 `D:\Python\python.exe`。它不是本项目专属内容，通常保留即可。

## 卸载这次项目使用的 Python 包
你之前把依赖装进了全局 Python 环境。如果其他项目也需要 pandas/numpy/scipy/matplotlib/streamlit，删除它们会影响其他项目。
只有确认这些库不再需要时，才运行：

`py -m pip uninstall -r requirements.txt`

## 清理 pip 下载缓存（可选）
查看：`py -m pip cache dir`
清理：`py -m pip cache purge`

## 删除公网版本
删除本地目录不会删除公网应用。还需要分别在 Streamlit Community Cloud 删除 app，在 GitHub 删除 repository（如果也不再需要）。

## 以后推荐使用虚拟环境
`py -m venv .venv`
`.venv\Scripts\activate`
`python -m pip install -r requirements.txt`
以后不需要项目时，直接删除项目目录和 `.venv` 即可，不影响 D 盘 Python 的其他项目。

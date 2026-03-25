# Private KB QA Project

一个基于 LangChain Tools + OpenAI API 兼容本地模型服务 的私有知识库问答系统。

## 功能
- 上传 pdf / txt / md / docx
- 文档入库到 Chroma
- LangChain agent + tool 检索知识库
- 问答返回答案和参考来源
- Streamlit 简单前端

## 1. 启动本地模型服务
确保你的 OpenAI API 兼容服务已运行在：

http://127.0.0.1:40051/v1

并且至少提供：
- 一个聊天模型
- 一个 embedding 模型

## 2. 启动后端

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 58000

## 3. 启动前端

cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 58501

## 4. 打开页面

前端: http://127.0.0.1:58501

后端 Swagger: http://127.0.0.1:58000/docs
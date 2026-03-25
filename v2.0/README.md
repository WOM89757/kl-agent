# KL Agent v2.0 — 私有知识库问答系统

## 架构概览

```
v2.0/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口，路由注册，启动事件
│   │   ├── config.py           # 统一配置（环境变量）
│   │   ├── database.py         # PostgreSQL 连接（SQLAlchemy）
│   │   ├── models/             # ORM 模型
│   │   │   └── document.py     # Document 表
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   │   ├── document.py
│   │   │   └── chat.py
│   │   ├── api/v1/             # 版本化 API 路由
│   │   │   ├── router.py       # 路由聚合
│   │   │   ├── documents.py    # 文档 CRUD
│   │   │   ├── chat.py         # 问答接口
│   │   │   └── health.py       # 健康检查
│   │   └── services/           # 业务逻辑层
│   │       ├── ingest.py       # 文档入库（PG + Chroma）
│   │       ├── workflow.py     # LangGraph RAG 流程
│   │       ├── llm.py          # LLM / Embedding 客户端
│   │       ├── query_rewrite.py
│   │       ├── rerank.py
│   │       ├── retrieval/      # 混合检索（向量 + BM25）
│   │       ├── chunking/       # 文档分块策略
│   │       └── parsing/        # 文档解析（PDF/DOCX/TXT/MD）
│   ├── .env.example
│   └── requirements.txt
└── frontend/                   # 纯 HTML + JS 前端
    ├── index.html              # 智能问答界面（支持图片/视频）
    ├── admin.html              # 知识库管理界面（CRUD）
    └── static/
        ├── css/style.css
        └── js/
            ├── api.js          # 统一 API 客户端
            ├── chat.js         # 问答页逻辑
            └── admin.js        # 管理页逻辑
```

## 快速启动

### 1. 准备 PostgreSQL

```bash
# 创建数据库
createdb kl_agent
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填写 LLM 服务地址和 PostgreSQL 连接串
```

### 3. 安装依赖并启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 58000
```

启动后自动建表（无需手动执行 SQL）。

### 4. 访问界面

| 页面 | 地址 |
|------|------|
| 智能问答 | http://127.0.0.1:58000/ |
| 知识库管理 | http://127.0.0.1:58000/admin |
| API 文档 | http://127.0.0.1:58000/docs |

## API 接口

### 文档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/documents` | 分页列表，支持关键词搜索 |
| GET | `/api/v1/documents/{doc_id}` | 获取单个文档详情 |
| POST | `/api/v1/documents` | 上传文档（multipart/form-data） |
| PATCH | `/api/v1/documents/{doc_id}` | 更新文档备注 |
| DELETE | `/api/v1/documents/{doc_id}` | 删除文档 |

### 问答

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/ask` | 知识库问答，支持多模态 |

```json
// 请求体
{
  "question": "年假政策是什么？",
  "top_k": 5,
  "image_base64": null,    // 可选，base64 图片
  "media_type": null       // 可选，如 "image/jpeg"
}
```

## 主要升级点（对比 v1.0）

| 项目 | v1.0 | v2.0 |
|------|------|------|
| 元数据存储 | JSON 文件 | PostgreSQL |
| 路由组织 | 单文件 main.py | 按域划分 api/v1/* |
| 前端 | Streamlit | 原生 HTML + JS |
| 问答界面 | 基础文本 | 文字 + 图片 + 视频多模态 |
| 文档管理 | 无 | 完整 CRUD + 搜索分页 |
| API 版本 | 无版本 | /api/v1/ |
| 文件大小记录 | 无 | 有 |
| 文档备注 | 无 | 有 |

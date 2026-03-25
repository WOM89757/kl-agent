# 日志系统使用指南

## 概述

v1.0 版本已集成统一的日志管理模块，支持：
- ✅ 文件日志输出（自动轮转，单文件最大 10MB，保留 5 个备份）
- ✅ 终端控制台输出
- ✅ 可配置的日志级别
- ✅ 分级日志记录（DEBUG/INFO/WARNING/ERROR）

## 配置方式

在 `.env` 文件中配置：

```bash
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 是否写入文件
LOG_TO_FILE=true

# 是否输出到终端
LOG_TO_CONSOLE=true
```

## 日志文件位置

日志文件默认存储在：`v1.0/logs/` 目录下
每个模块有独立的日志文件，例如：
- `root.log` - 根日志器
- `app.main.log` - 主应用日志
- `app.services.ingest.log` - 数据导入服务日志

## 使用方法

在各模块中引入并使用：

```python
from app.logger import get_logger

logger = get_logger(__name__)

# 使用示例
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # 包含异常堆栈
```

## 日志级别说明

- **DEBUG**: 详细的调试信息（开发时使用）
- **INFO**: 一般的信息性消息（默认级别）
- **WARNING**: 警告信息，不影响正常运行
- **ERROR**: 错误信息，影响功能正常使用
- **CRITICAL**: 严重错误，程序可能无法继续运行

## 各模块日志点

### main.py (API 接口层)
- API 请求接收
- 参数验证
- 处理流程
- 异常错误

### services/agent.py (问答代理)
- 问题处理流程
- 上下文检索
- Agent 调用

### services/ingest.py (文档导入)
- 文件上传
- 文本提取
- 向量入库
- 文档删除

### services/retrieval.py (检索服务)
- 相似度搜索
- 文档序列化
- 结果转换

### services/storage.py (存储管理)
- 元数据读写
- 文件管理

### services/llm.py (LLM 服务)
- 模型初始化
- Embedding 初始化

### services/parser.py (文档解析)
- 文件读取（TXT/PDF/DOCX）
- 文本提取

## 环境变量示例

```bash
# 开发环境：详细日志，输出到终端
LOG_LEVEL=DEBUG
LOG_TO_FILE=true
LOG_TO_CONSOLE=true

# 生产环境：简洁日志，主要写文件
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_TO_CONSOLE=false

# 静默模式：仅记录错误
LOG_LEVEL=ERROR
LOG_TO_FILE=true
LOG_TO_CONSOLE=false
```

## 注意事项

1. 日志目录会自动创建，无需手动建立
2. 日志文件会自动轮转，避免单个文件过大
3. 建议开发时使用 DEBUG 级别，生产环境使用 INFO 或 WARNING
4. 错误日志会记录完整的异常堆栈信息
5. 敏感信息不会记录到日志中

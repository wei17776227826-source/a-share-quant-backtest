# A股量化回测平台

> 专注 A 股市场的量化回测系统，BeeQuant 风格前端重构中

当前基于 FastAPI + SQLite + 东方财富数据源，正在从 Jinja2 模板升级为 React 前端。

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database/models.py

# 启动服务器
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.x, FastAPI, SQLAlchemy, SQLite |
| 数据源 | 东方财富 API（A 股） |
| 前端(当前) | Jinja2 模板 |
| 前端(目标) | React + Vite + Tailwind CSS |

## 访问

- 地址: http://119.23.56.57:8000
- 管理员: root / WEI533400rui

## 路线图

详见 [ROADMAP.md](ROADMAP.md)

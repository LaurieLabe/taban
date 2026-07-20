# 她伴 (TāBàn)

> 去性缘化的女性搭子匹配平台

让女性轻松找到非恋爱导向的、精神同频的女性伙伴。

---

## 项目简介

**她伴**解决成年女性离开学校后，同性友缘关系因缺乏制度化的匹配工具而被性缘关系侵蚀和替代的困境。通过"匹配人"和"匹配事"双模块，结合 AI 驱动的双层画像体系，帮助女性在物理空间内找到合拍的搭子。

**核心特色：**

- 🚫 **去性缘化** — 纯女性空间，不做恋爱匹配
- 🧠 **AI 双层匹配** — 显性标签（用户自知）+ 隐性量表（AI 推断）
- 🎯 **目的性克制** — 首页展示"事"而非"人"，不让关系变商品
- 💬 **轻量连接** — 单向发起，温和节奏，每日上限 5 次

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | HTML5 + Tailwind CSS (CDN) + Alpine.js (CDN) |
| 后端 | Python 3.11+ FastAPI |
| 数据库 | SQLite |
| AI | DeepSeek V4 Pro API |
| 部署 | Railway |

---

## 项目结构

```
taban/
├── backend/
│   ├── main.py                 # FastAPI 入口，托管前端静态文件
│   ├── database.py             # 数据库连接与建表
│   ├── models.py               # Pydantic 数据模型
│   ├── frontend/
│   │   └── index.html          # 单文件前端
│   ├── routers/                # API 路由
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── events.py
│   │   ├── messages.py
│   │   └── match.py
│   ├── services/               # 业务逻辑
│   │   ├── ai_service.py       # DeepSeek API 调用
│   │   └── match_service.py    # 匹配算法
│   └── requirements.txt
├── railway.json                # Railway 部署配置
├── requirements.txt            # 根目录依赖
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── IMPLEMENTATION.md
└── OPTIMIZATION.md
```

---

## 在线体验

**https://taban-production.up.railway.app/app**

## 快速开始

### 环境要求

- Python 3.11+
- DeepSeek API Key（[申请地址](https://platform.deepseek.com)）

### 本地运行

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置 API Key
export DEEPSEEK_API_KEY="sk-xxx"

# 4. 启动后端
uvicorn main:app --reload --port 8000

# 5. 打开浏览器访问 http://localhost:8000/app
```

### 部署

项目通过 Railway 统一部署，前端和后端在同一端口。部署时需设置环境变量 `DEEPSEEK_API_KEY`。

---

## 文档

- [PRD.md](./PRD.md) — 产品需求文档
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 架构设计文档
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) — 代码实施计划
- [OPTIMIZATION.md](./OPTIMIZATION.md) — 优化迭代计划

---

## 产品边界

| 规则 | 说明 |
|------|------|
| 用户范围 | 纯女性 |
| 每日发起上限 | 5次/天 |
| 距离默认 | 同城，可自定义 |
| 人格卡片 | 仅文字 + 预设图片 |
| 事件性别 | 纯女性 |

---

> 她伴 — 你的生命花园里，不该只有一棵树。
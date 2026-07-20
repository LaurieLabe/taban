# 她伴 · 架构设计文档

> 版本：v1.1 | 2026-07-20

---

## 一、技术栈选择及原因

| 层 | 技术 | 选择理由 |
|----|------|----------|
| **前端** | HTML5 + Tailwind CSS CDN + Alpine.js CDN | 零构建工具，单文件即可运行，AI 生成代码质量最高。Alpine.js 提供轻量响应式状态管理，无需引入 React/Vue 级别的框架 |
| **后端** | Python 3.11+ FastAPI | Python 是 AI 生成代码最成熟的语言，FastAPI 代码量少、自动生成 API 文档、异步支持好、RESTful 路由清晰 |
| **数据库** | SQLite | 零配置，文件即数据库，Python 内置 `sqlite3` 模块无需额外安装。项目数据量小，SQLite 完全够用，不需要单独部署数据库服务 |
| **AI** | DeepSeek V4 Pro API | 兼容 OpenAI SDK，调用方式极简。支持 JSON Mode，AI 可直接返回结构化的隐性量表数据。新账户 500 万免费 Token |
| **部署** | Railway 统一部署 | 前后端同一端口，FastAPI 托管前端静态文件，配置极简（`railway.json` + `requirements.txt`） |

**不选的方案及原因：**

| 未选方案 | 原因 |
|----------|------|
| React / Vue | 需要构建工具、组件拆分、状态管理，28 小时内维护成本高，出问题排查难 |
| PostgreSQL | 需要单独部署和管理数据库服务，项目规模不需要 |
| Node.js Express | Python 在 AI 代码生成方面比 JavaScript 更成熟可靠 |
| 小程序 | 需要微信审核、真机调试、后端域名备案，时间不可控 |

---

## 二、项目目录结构

```
taban/
├── backend/
│   ├── main.py                 # FastAPI 入口，托管前端静态文件
│   ├── database.py             # 数据库连接，建表，初始化
│   ├── models.py               # Pydantic 请求/响应模型
│   ├── frontend/
│   │   └── index.html          # 单文件前端，全部页面视图
│   ├── routers/
│   │   ├── auth.py             # POST /api/auth/register, /api/auth/login
│   │   ├── users.py            # 用户画像、标签、人格卡片、AI对话
│   │   ├── events.py           # 事件 CRUD、列表、排序、加入、审批
│   │   ├── messages.py         # 消息收发、会话列表、聊天记录
│   │   └── match.py            # 推荐人和事件的排序接口
│   ├── services/
│   │   ├── ai_service.py       # DeepSeek API 调用（requests 直调）
│   │   └── match_service.py    # 匹配得分计算、事件推荐排序
│   └── requirements.txt
├── railway.json                # Railway 部署配置
├── requirements.txt            # 根目录 Python 依赖
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── IMPLEMENTATION.md
└── OPTIMIZATION.md
```

---

## 三、核心模块说明

### 3.1 前端 (index.html)

**架构：** 单 HTML 文件，所有页面视图通过 Alpine.js 的 `x-show` 控制显隐。

**页面视图拆分：**

| 视图组 | 视图 | 触发方式 |
|--------|------|----------|
| 注册 | 欢迎页 → 问卷页1-6 → AI对话 → 画像确认 → 卡片创建 → 大门动画 | 线性流程，`x-data` 状态机控制 |
| 主页 | 事（首页）/ 人 / 消息 / 我 | 底部导航切换 |
| 详情 | 事件详情 / 人格卡片详情 | 点击卡片进入 |
| 弹窗 | 发布事件 / 聊天界面 | 按钮触发 |

**全局状态管理 (Alpine.js store)：**

```javascript
// 全局状态
store = {
  currentUser: null,        // 当前登录用户
  currentTab: 'events',     // 当前底部导航标签
  currentView: 'welcome',   // 当前视图（注册流程用）
  events: [],               // 事件列表
  persons: [],              // 推荐的人列表
  messages: [],             // 消息列表
  chatTarget: null,         // 当前聊天对象
  aiConversation: [],       // AI 对话历史
  latentTraits: null,       // 隐性量表（AI推断结果）
}
```

**API 调用封装：**

```javascript
async function api(path, options = {}) {
  const res = await fetch(BACKEND_URL + path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  return res.json();
}
```

---

### 3.2 后端路由 (routers/)

**auth.py — 注册与登录**

| 接口 | 功能 |
|------|------|
| `POST /api/auth/register` | 昵称+密码注册，返回用户ID和token |
| `POST /api/auth/login` | 昵称+密码登录，返回用户ID和token |

认证方式：简单的 token 机制（用户ID + 随机字符串，存内存字典），不接 JWT。

**users.py — 用户画像**

| 接口 | 功能 |
|------|------|
| `GET /api/users/me` | 获取当前用户完整信息 |
| `PUT /api/users/me` | 更新昵称、卡片 |
| `POST /api/users/me/tags` | 保存显性标签（6维度） |
| `POST /api/users/me/card` | 保存人格卡片 |
| `GET /api/users/me/events` | 获取我的事件（发起/申请/参加） |
| `POST /api/chat` | AI 对话（DeepSeek V4 Pro） |

**events.py — 搭子事件**

| 接口 | 功能 |
|------|------|
| `GET /api/events` | 事件列表，支持排序 |
| `POST /api/events` | 发布事件 |
| `GET /api/events/{id}` | 事件详情（含发起人标签） |
| `POST /api/events/{id}/join` | 申请加入事件 |
| `GET /api/events/{id}/applicants` | 查看申请者列表 |
| `POST /api/events/{id}/applicants/{uid}/accept` | 通过申请 |
| `POST /api/events/{id}/applicants/{uid}/reject` | 拒绝申请 |

**messages.py — 消息**

| 接口 | 功能 |
|------|------|
| `GET /api/messages` | 当前用户的消息列表（按会话聚合） |
| `POST /api/messages` | 发送消息（需指定 `to_user_id` 和 `context_type`） |
| `GET /api/messages/{user_id}` | 与某人的聊天记录 |

**match.py — 匹配推荐**

| 接口 | 功能 |
|------|------|
| `GET /api/match/persons` | 推荐的人列表（人格卡片），按匹配度降序 |
| `GET /api/events` | 事件推荐排序（由 events.py 调用 match_service） |

---

### 3.3 业务服务 (services/)

**ai_service.py — DeepSeek API 调用**

职责：封装所有与 DeepSeek 的交互。

核心函数：

```python
def chat_with_ai(conversation_history: list, user_message: str) -> dict:
    """
    参数：
      conversation_history: 对话历史 [{"role":"user/assistant","content":"..."}]
      user_message: 用户最新消息
    
    返回：
      {
        "reply": "AI的回复文本",
        "traits": {           # 隐性量表（JSON Mode 直接返回）
          "empathy": 72,
          "agency": 55,
          "energy": 38,
          "sensitivity": 80,
          "openness": 65
        }
      }
    """
```

System Prompt 设计要点：
- AI 以"第一个搭子/朋友"的口吻对话
- 要求 AI 在每次回复后，内部分析用户的隐性特质
- 用 JSON Mode 让 AI 直接返回结构化数据
- 对话 3-5 轮后，AI 综合评估给出最终隐性量表

**match_service.py — 匹配算法**

职责：计算用户间匹配度，生成推荐排序。

核心函数：

```python
def calculate_match_score(user_a: dict, user_b: dict) -> float:
    """
    显性维度匹配 (60%) + 隐性维度匹配 (40%)
    
    显性维度匹配：
      - 人格气质：是否相同类型 → 0/1
      - 兴趣活动：Jaccard 相似度 (交集/并集)
      - 聊天话题：Jaccard 相似度
      - 消费观：相同 → 1，不同 → 0
      - 生活节奏：相同 → 1，不同 → 0
      - 距离范围：不参与计算，仅做硬过滤
    
    隐性维度匹配：
      - 5个维度分别计算余弦相似度
      - 取平均值
    """

def get_recommended_persons(user_id: int, limit: int = 20) -> list:
    """返回按匹配度降序排列的推荐用户列表"""

def get_recommended_events(user_id: int, sort_by: str) -> list:
    """返回按指定排序方式的事件列表"""
```

---

## 四、数据模型设计

### 4.1 users

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    avatar        TEXT DEFAULT '',
    bio           TEXT DEFAULT '',
    card_image    TEXT DEFAULT '',
    
    -- 显性标签
    personality   TEXT,
    interests     TEXT,       -- JSON数组
    topics        TEXT,       -- JSON数组
    consumption   TEXT,
    life_rhythm   TEXT,
    distance      TEXT DEFAULT 'city',
    
    -- 隐性量表（0-100）
    empathy       INTEGER DEFAULT 50,
    agency        INTEGER DEFAULT 50,
    energy        INTEGER DEFAULT 50,
    sensitivity   INTEGER DEFAULT 50,
    openness      INTEGER DEFAULT 50,
    
    birth_date    TEXT DEFAULT '',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 events

```sql
CREATE TABLE events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id      INTEGER NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT DEFAULT '',
    location        TEXT NOT NULL,
    event_date      TEXT NOT NULL,
    event_duration  TEXT DEFAULT '2小时',
    max_participants INTEGER DEFAULT 5,
    category        TEXT DEFAULT '',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);
```

### 4.3 messages

```sql
CREATE TABLE messages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id  INTEGER NOT NULL,
    to_user_id    INTEGER NOT NULL,
    content       TEXT NOT NULL,
    context_type  TEXT DEFAULT 'person',
    context_id    INTEGER,
    is_read       INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user_id) REFERENCES users(id),
    FOREIGN KEY (to_user_id) REFERENCES users(id)
);
```

### 4.4 likes

```sql
CREATE TABLE likes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id  INTEGER NOT NULL,
    to_user_id    INTEGER NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user_id) REFERENCES users(id),
    FOREIGN KEY (to_user_id) REFERENCES users(id),
    UNIQUE(from_user_id, to_user_id)
);
```

### 4.5 event_participants

```sql
CREATE TABLE event_participants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    status        TEXT DEFAULT 'pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(event_id, user_id)
);
```

### 表关系图

```
users ──1:N──→ events (creator_id)
users ──1:N──→ messages (from_user_id / to_user_id)
users ──1:N──→ likes (from_user_id / to_user_id)
users ──1:N──→ event_participants (user_id)
events ──1:N──→ event_participants (event_id)
```

---

## 五、代码规范

### 5.1 Python 后端

**命名：**
- 变量/函数：`snake_case`（`get_user`, `match_score`）
- 类：`PascalCase`（`RegisterRequest`, `UserResponse`）
- 常量：`UPPER_SNAKE_CASE`

**文件组织：**
- 每个 router 文件不超过 100 行
- 数据库操作写原生 SQL，不用 ORM
- `services/` 放纯业务逻辑，不操作 HTTP 请求/响应

**API 返回格式：**
```python
# 成功
{"ok": true, "data": {...}}

# 失败
{"ok": false, "error": "错误描述"}
```

**错误处理：**
- 只在具体可能出错的地方加 try-except（如数据库写入、API 调用）
- 不要用 try-except 包裹整个路由函数

**数据库：**
- 用 `sqlite3` 内置模块
- 数据库文件：`backend/taban.db`
- 连接通过 `database.py` 的 `get_db()` 获取

### 5.2 前端 HTML

**文件组织：**
- 每个视图区块用 `<!-- 视图名称 -->` 注释分隔
- Alpine.js 全局 store 放在 `<script>` 顶部
- API 调用统一用封装的 `api()` 函数

**CSS：**
- 全部用 Tailwind 类名，不写自定义 CSS
- 页面最大宽度 414px，居中显示
- 底部导航：flex 布局，5 等宽 `grid grid-cols-5`，作为页面 flex 子元素固定底部

**状态管理：**
- 用 Alpine.js `x-data` 管理局部状态
- 全局状态用 `Alpine.store()`
- 不引入额外的状态管理库

### 5.3 通用

**注释：**
- 不写注释解释"做了什么"（代码自解释）
- 只写注释解释"为什么"（如算法选择理由、边界条件处理）

**提交：**
- 每完成一个模块 commit 一次
- commit message 格式：`[模块] 简短描述`（如 `[auth] 实现注册登录接口`）

---

## 六、安全注意事项

- 密码存储：`hashlib.sha256(password + salt).hexdigest()`
- DeepSeek API Key：后端环境变量 `DEEPSEEK_API_KEY`，不提交到代码
- 隐性量表：API 不返回给前端，只在后端匹配计算时使用
- 用户认证：简单 token 机制，token 存储在服务端内存字典

---

> **文档版本：** v1.0
> **最后更新：** 2026-07-19
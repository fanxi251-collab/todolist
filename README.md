# 智能生活助手

一个基于 FastAPI 的智能生活管理平台，支持便签管理、账本记录、天气查询和智能对话功能。

## 功能特性

- 📝 **便签管理** - 创建、编辑、删除便签，支持图片和附件
- ✅ **今日待办** - 按日期查看待办事项
- 🏷️ **标签系统** - 为便签添加分类标签
- 🗑️ **回收站** - 恢复或彻底删除便签
- 💰 **账本** - 记录收入和支出，支持分类统计
- 🌤️ **天气查询** - 查询城市天气（需要高德地图 API）
- 💬 **智能对话** - AI 助手，可通过对话创建便签（需要通义千问 API）

## 环境配置

### 1. 激活 conda 环境

```bash
conda activate todolist
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件或设置系统环境变量：

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `WEATHER_API` | ✅ | 高德地图 API Key（用于天气查询） |
| `DASHSCOPE_API_KEY` | ✅ | 阿里云通义千问 API Key（用于智能对话） |

获取 API 密钥：
- 高德地图: https://console.amap.com/
- 阿里云百炼: https://dashscope.console.aliyun.com/

### 4. 启动服务

```bash
python main.py
```

服务地址: http://127.0.0.1:8000

## 项目结构

```
todolist/
├── main.py              # FastAPI 入口
├── database.py          # 数据库配置
├── models.py            # 数据模型
├── schemas.py           # Pydantic schemas
├── crud.py              # 数据库操作
├── routers/             # API 路由
│   ├── notes.py        # 便签 API
│   ├── account.py      # 账目 API
│   ├── chat.py         # 智能对话 API
│   ├── recycle.py      # 回收站 API
│   └── weather.py      # 天气 API
├── static/             # 前端静态文件
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── services/           # 业务服务
    └── weather_service.py
```

## API 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/notes` | 创建便签 |
| GET | `/notes` | 获取便签列表 |
| PUT | `/notes/{id}` | 更新便签 |
| DELETE | `/notes/{id}` | 删除便签 |
| GET | `/notes/today` | 今日待办 |
| POST | `/chat` | 智能对话 |
| GET | `/weather` | 天气查询 |
| POST | `/account/expenses` | 添加支出 |
| POST | `/account/incomes` | 添加收入 |
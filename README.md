# 校园图书个性化推荐系统（Django）

本项目用于本科毕业设计演示，采用 **Django 单体架构**（后端+模板前端），避免前后端分离的运维复杂度，同时保留清晰分层，便于后续扩展为 Vue + Django API 模式。

## 功能覆盖

### 1) 普通用户
- 用户注册、登录、重置密码、登录验证码、登录后修改密码
- 图书分类浏览 + 多条件检索（书名、作者、ISBN、分类）
- 图书详情（简介、封面链接、馆藏量）
- 图书借阅、归还、续借
- 图书收藏、评分、评论
- 首页推荐：热门图书 / 新书推荐 / 个性化推荐 / 猜你喜欢
- 借阅历史、收藏历史、浏览足迹
- 消息通知（借阅成功、到期提醒）

### 2) 管理员
- 图书管理（增删改查）
- 用户管理（查看、启用/禁用）
- 借阅管理（查询/统计）
- 评论管理（删除违规评论）
- 推荐系统管理（刷新日志）
- Dashboard（借阅量、热门图书、活跃用户）

### 3) 推荐核心策略
- 热门图书推荐（全局借阅次数）
- 新书推荐（按录入时间）
- 基于借阅历史的个性化推荐（用户偏好分类）
- 相似图书推荐（借阅同书用户的共现图书）
- 猜你喜欢（综合评分优先）

---

## 项目结构

```text
campuslib/                     # Django 项目配置
  settings.py                  # 全局配置
  urls.py                      # 根路由
library/                       # 业务 app
  models.py                    # 业务模型（图书/借阅/收藏/评分/评论/通知/足迹/推荐日志）
  views.py                     # 用户端 + 管理端视图
  urls.py                      # 业务路由
  forms.py                     # 注册登录/图书/评论表单
  recommendation.py            # 推荐算法实现
  management/commands/
    seed_demo_data.py          # 一键填充演示数据（>=320 本图书）
  static/library/style.css     # UI 样式
templates/                     # 页面模板
  auth/                        # 登录/注册/重置密码/修改密码
  dashboard/                   # 管理端页面
  home.html                    # 推荐首页
  book_list.html               # 图书检索页
  book_detail.html             # 图书详情页
  history.html                 # 个人历史
  notifications.html           # 消息页
manage.py
requirements.txt
```

---

## Windows + PyCharm Terminal 命令部署（推荐）

> 以下步骤默认你已安装 Python 3.10+ 与 PyCharm。

### 第 1 步：打开项目
1. 打开 PyCharm
2. `File -> Open` 选择本项目根目录

### 第 2 步：在 PyCharm Terminal 创建并激活虚拟环境

```bash
python -m venv .venv
```

激活虚拟环境（按你的终端类型选择一条）：

```bash
# CMD
.venv\Scripts\activate

# PowerShell
.venv\Scripts\Activate.ps1
```

### 第 3 步：安装依赖
在已激活虚拟环境的 PyCharm Terminal 执行：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> 看到终端前缀出现 `(.venv)` 再继续执行后续命令。

### 第 4 步：初始化数据库
在 PyCharm Terminal 执行：

```bash
python manage.py makemigrations
python manage.py migrate
```

### 第 5 步：填充演示数据（重点）
在 PyCharm Terminal 执行：

```bash
python manage.py seed_demo_data
```

将自动创建：
- 管理员：`admin / Admin123!`
- 普通用户：`user001` ~ `user060`（密码：`User12345!`）
- 图书：至少 320 本
- 借阅/收藏/评分/评论/通知等演示数据

### 第 6 步：启动系统
在 PyCharm Terminal 执行：

```bash
python manage.py runserver
```

浏览器访问：
- 用户入口：`http://127.0.0.1:8000/login/`
- Django 管理后台：`http://127.0.0.1:8000/admin/`
- 管理端业务看板（需 staff）：`http://127.0.0.1:8000/dashboard/`

---

## 演示建议流程

1. 用普通用户登录，查看首页推荐位
2. 进入图书检索，按作者/ISBN/分类组合搜索
3. 进入图书详情，执行借阅、收藏、评分、评论
4. 查看历史与消息提醒
5. 切换管理员账号进入 Dashboard，演示图书/用户/评论/借阅/推荐日志管理

---

## 说明

- 当前实现以毕业设计答辩“可展示、可说明、可扩展”为目标。
- 若后续需要 Vue 前后端分离，可在 `library` 中按现有业务逻辑平滑拆分为 REST API。

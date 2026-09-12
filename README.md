# 校园活动管理系统 V1.0

软件工程实验一：基于工程意图的软件迭代开发。

- 组名：心之钢
- 技术栈：Python Flask + SQLite (SQLAlchemy) + 原生 HTML/CSS/JS
- 角色：学生 / 教师

## 功能

- 注册 / 登录 / 退出（密码哈希存储）
- 学生：浏览活动列表与详情、在线报名（防重复、满员限制）、我的报名、取消待审核报名
- 教师：发布活动、查看报名名单、通过/驳回报名
- 活动状态由时间自动驱动：报名中 → 已截止 → 已结束

## 运行

```bash
pip install -r requirements.txt
python run.py
```

浏览器访问 http://127.0.0.1:5000

## 目录结构

```
campus_activity/
├── app/
│   ├── __init__.py      # 应用工厂
│   ├── models.py        # User / Activity / Registration
│   ├── auth.py          # 注册登录蓝图
│   ├── activities.py    # 活动浏览/发布蓝图
│   ├── registrations.py # 报名/审核蓝图
│   ├── decorators.py    # 登录与角色校验装饰器
│   ├── templates/       # Jinja2 模板
│   └── static/          # CSS
├── run.py               # 入口
├── requirements.txt
└── .gitignore
```

> 注意：正式部署前请修改 `app/__init__.py` 中的 SECRET_KEY。

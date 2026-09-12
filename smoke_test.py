# -*- coding: utf-8 -*-
"""端到端冒烟测试：覆盖 REQ-01~06 核心业务链路"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, r"C:/Users/a'su's/Doubao/chats/2026-09-11/new-chat/campus_activity")

from app import create_app
from app.models import db, User, Activity, Registration

app = create_app()
client = app.test_client()

results = []


def check(name, ok, extra=""):
    results.append((name, ok, extra))
    print(("PASS" if ok else "FAIL"), name, extra)


with app.app_context():
    db.drop_all()
    db.create_all()

# --- REQ-01 注册登录 ---
r = client.post('/auth/register', data={
    'username': 'teacher1', 'real_name': '王老师', 'role': 'teacher',
    'password': '123456', 'confirm': '123456'})
check('REQ-01 教师注册', r.status_code == 302)
r = client.post('/auth/register', data={
    'username': 'stu1', 'real_name': '张玮', 'role': 'student',
    'password': '123456', 'confirm': '123456'})
check('REQ-01 学生注册', r.status_code == 302)
r = client.post('/auth/register', data={
    'username': 'stu2', 'real_name': '王炜', 'role': 'student',
    'password': '123456', 'confirm': '123456'})
check('REQ-01 学生2注册', r.status_code == 302)
r = client.post('/auth/register', data={
    'username': 'stu3', 'real_name': '闫梓昊', 'role': 'student',
    'password': '123456', 'confirm': '123456'})
check('REQ-01 学生3注册', r.status_code == 302)
r = client.post('/auth/register', data={
    'username': 'stu1', 'real_name': '重复', 'role': 'student',
    'password': '123456', 'confirm': '123456'})
check('REQ-01 重复用户名被拒', r.status_code == 200 and '用户名已存在' in r.get_data(as_text=True))

r = client.post('/auth/login', data={'username': 'stu1', 'password': 'wrong'}, follow_redirects=True)
check('REQ-01 错误密码被拒', '用户名或密码错误' in r.get_data(as_text=True))
r = client.post('/auth/login', data={'username': 'stu1', 'password': '123456'}, follow_redirects=True)
check('REQ-01 正确登录成功', '活动列表' in r.get_data(as_text=True))
client.get('/auth/logout')

with app.app_context():
    u = User.query.filter_by(username='stu1').first()
    check('REQ-01 密码已哈希存储', u.password_hash != '123456' and u.password_hash.startswith('scrypt'))

# --- REQ-04 教师发布活动 ---
client.post('/auth/login', data={'username': 'teacher1', 'password': '123456'})
start = datetime.now() + timedelta(days=2)
r = client.post('/activities/publish', data={
    'title': 'AI 前沿讲座', 'category': '讲座', 'location': '图书馆报告厅',
    'start_time': start.strftime('%Y-%m-%dT%H:%M'),
    'end_time': (start + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
    'signup_deadline': (start - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M'),
    'capacity': 2, 'detail': '介绍大模型前沿进展'}, follow_redirects=True)
check('REQ-04 教师发布活动', '活动发布成功' in r.get_data(as_text=True))
r = client.post('/activities/publish', data={
    'title': '足球友谊赛', 'category': '比赛', 'location': '操场',
    'start_time': start.strftime('%Y-%m-%dT%H:%M'),
    'end_time': (start + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
    'signup_deadline': (start + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
    'capacity': 10, 'detail': ''}, follow_redirects=True)
check('REQ-04 截止晚于开始被拒', '报名截止时间必须早于活动开始时间' in r.get_data(as_text=True))
client.get('/auth/logout')

# --- REQ-02 学生浏览 ---
client.post('/auth/login', data={'username': 'stu1', 'password': '123456'})
r = client.get('/')
check('REQ-02 活动列表可见', 'AI 前沿讲座' in r.get_data(as_text=True))
with app.app_context():
    aid = Activity.query.filter_by(title='AI 前沿讲座').first().id
r = client.get('/activities/%d' % aid)
check('REQ-02 活动详情可见', '图书馆报告厅' in r.get_data(as_text=True))

# --- REQ-03 报名 + 防重复 + 满员限制 ---
r = client.post('/registrations/%d/signup' % aid, follow_redirects=True)
check('REQ-03 学生报名成功', '报名成功' in r.get_data(as_text=True))
r = client.post('/registrations/%d/signup' % aid, follow_redirects=True)
check('REQ-03 重复报名被拒', '请勿重复报名' in r.get_data(as_text=True))

client.get('/auth/logout')
client.post('/auth/login', data={'username': 'stu2', 'password': '123456'})
r = client.post('/registrations/%d/signup' % aid, follow_redirects=True)
check('REQ-03 学生2报名成功', '报名成功' in r.get_data(as_text=True))

client.get('/auth/logout')
client.post('/auth/login', data={'username': 'stu3', 'password': '123456'})
r = client.post('/registrations/%d/signup' % aid, follow_redirects=True)
check('REQ-03 满员后报名被拒', '人数已满' in r.get_data(as_text=True))
client.get('/auth/logout')

# --- REQ-05 教师审核 ---
client.post('/auth/login', data={'username': 'teacher1', 'password': '123456'})
r = client.get('/activities/%d/manage' % aid)
check('REQ-05 教师查看报名名单', '张玮' in r.get_data(as_text=True) and '王炜' in r.get_data(as_text=True))
with app.app_context():
    regs = Registration.query.filter_by(activity_id=aid).order_by(Registration.id).all()
reg1, reg2 = regs[0], regs[1]
r = client.post('/registrations/%d/review' % aid,
                data={'registration_id': reg1.id, 'action': 'approve'}, follow_redirects=True)
check('REQ-05 教师通过第一条报名', '已通过' in r.get_data(as_text=True))
r = client.post('/registrations/%d/review' % aid,
                data={'registration_id': reg2.id, 'action': 'approve'}, follow_redirects=True)
check('REQ-05 教师通过第二条报名', '已通过' in r.get_data(as_text=True))
r = client.post('/registrations/%d/review' % aid,
                data={'registration_id': reg2.id, 'action': 'reject'}, follow_redirects=True)
check('REQ-05 已通过后不能再驳回', '未知操作' not in r.get_data(as_text=True))

# --- 权限校验：学生访问发布页被拦截 ---
client.get('/auth/logout')
client.post('/auth/login', data={'username': 'stu1', 'password': '123456'})
r = client.get('/activities/publish', follow_redirects=True)
check('权限 学生访问发布页被拦截', '该操作仅教师可用' in r.get_data(as_text=True))

# --- 学生端状态同步 ---
r = client.get('/registrations/my')
check('REQ-05 学生端状态同步为已通过', '已通过' in r.get_data(as_text=True))

print("\n==== 结果汇总 ====")
passed = sum(1 for _, ok, _ in results if ok)
print("通过 %d / %d" % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import random
import requests
import pytz

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "work_history.csv"
MD_FILE = "Diary.md"

BACKUP_QUOTES = [
"“在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞。” —— 余秀华",
"“满地都是六便士，他却抬头看见了月亮。” —— 毛姆《月亮与六便士》",
"“一个人可以被毁灭，但不能给打败。” —— 海明威《老人与海》"
]

# ================= 时间函数 =================
def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

# ================= 打卡统计系统 =================
def get_all_dates():

    if not os.path.exists(LOG_FILE):
        return []

    dates = []

    try:
        with open(LOG_FILE, encoding="utf-8-sig") as f:

            reader = csv.reader(f)

            next(reader, None)

            for row in reader:
                if row:
                    date = row[0].split(" ")[0]
                    dates.append(date)

    except:
        return []

    return dates


def get_total_days():
    dates = get_all_dates()
    return len(set(dates))


def get_current_streak():

    dates = sorted(set(get_all_dates()))

    if not dates:
        return 0

    today = get_beijing_time().strftime("%Y/%m/%d")

    if dates[-1] != today:
        return 0

    streak = 1

    for i in range(len(dates)-1, 0, -1):

        d1 = datetime.strptime(dates[i], "%Y/%m/%d")
        d2 = datetime.strptime(dates[i-1], "%Y/%m/%d")

        if (d1 - d2).days == 1:
            streak += 1
        else:
            break

    return streak


def get_longest_streak():

    dates = sorted(set(get_all_dates()))

    if not dates:
        return 0

    longest = 1
    current = 1

    for i in range(1, len(dates)):

        d1 = datetime.strptime(dates[i], "%Y/%m/%d")
        d2 = datetime.strptime(dates[i-1], "%Y/%m/%d")

        if (d1 - d2).days == 1:
            current += 1
        else:
            longest = max(longest, current)
            current = 1

    longest = max(longest, current)

    return longest


# ================= 成就系统 =================
ACHIEVEMENTS = [
{"name": "🥉 初出茅庐", "days": 7},
{"name": "🥈 坚持者", "days": 30},
{"name": "🥇 自律达人", "days": 100},
{"name": "👑 传奇", "days": 365}
]


def check_achievements(days):

    unlocked = []

    for ach in ACHIEVEMENTS:
        if days >= ach["days"]:
            unlocked.append(ach["name"])

    return unlocked


# ================= 页面设置 =================
st.set_page_config(page_title="自律成就系统", page_icon="🚀", layout="centered")

st.markdown("""
<style>
.center-box {
    display:flex;
    justify-content:center;
    align-items:center;
    height:70vh;
    text-align:center;
    flex-direction:column;
}
.quote-card {
    background:#f9f9f9;
    padding:30px;
    border-left:8px solid #4CAF50;
    border-radius:12px;
    margin:20px 0;
}
</style>
""", unsafe_allow_html=True)

# ================= Session 初始化 =================
if 'entered' not in st.session_state:
    st.session_state['entered'] = False

if 'show_summary' not in st.session_state:
    st.session_state['show_summary'] = False


# ================= 获取金句 =================
def get_refined_quote():

    try:
        response = requests.get(
            "https://v1.hitokoto.cn/?c=d&c=k&min_length=15&max_length=35",
            timeout=3
        )

        if response.status_code == 200:

            data = response.json()

            return f"“{data['hitokoto']}”", f"—— {data['from_who'] or '佚名'} 《{data['from']}》"

    except:
        pass

    q = random.choice(BACKUP_QUOTES).split(" —— ")

    return q[0], q[1]


if 'quote_data' not in st.session_state:
    st.session_state['quote_data'] = get_refined_quote()


# ================= 欢迎页 =================
if not st.session_state['entered']:

    st.balloons()

    total_days = get_total_days()

    st.markdown("<h1 style='text-align:center;color:#4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)

    st.markdown(
    "<p style='text-align:center;color:#888;font-style:italic;'>欢迎回来，新的机遇与挑战正在等着你 ✨</p>",
    unsafe_allow_html=True)

    st.markdown(
    f"<p style='text-align:center;'>🕒 <b>北京时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</b></p>",
    unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align:center;margin-bottom:10px;'>
        <span style='font-size:20px;color:#666;'>已累计坚持</span>
        <span style='font-size:36px;font-weight:bold;color:#4CAF50;margin:0 10px;'>{total_days}</span>
        <span style='font-size:20px;color:#666;'>天</span>
    </div>
    """, unsafe_allow_html=True)

    content, meta = st.session_state['quote_data']

    st.markdown(
        f"<div class='quote-card'><h3>{content}</h3><p style='text-align:right;'>{meta}</p></div>",
        unsafe_allow_html=True
    )

    if st.button("✨ 开启今日挑战", use_container_width=True):

        st.session_state['entered'] = True
        st.rerun()

    st.stop()


# ================= 主界面 =================
if not st.session_state['show_summary']:

    st.title("🎯 进度实时看板")

    total_days = get_total_days()
    current_streak = get_current_streak()
    longest_streak = get_longest_streak()

    c1,c2,c3 = st.columns(3)

    with c1:
        st.metric("🏆 累计坚持", f"{total_days} 天")

    with c2:
        st.metric("🔥 当前连续", f"{current_streak} 天")

    with c3:
        st.metric("👑 历史最长", f"{longest_streak} 天")

    st.divider()

    # 成就墙
    st.subheader("🏅 成就墙")

    unlocked = check_achievements(total_days)

    for ach in ACHIEVEMENTS:

        if ach["name"] in unlocked:
            st.success(f"{ach['name']} ✔ （{ach['days']}天）")

        else:
            st.write(f"{ach['name']} 🔒 （{ach['days']}天）")

    st.divider()

    # ================= 今日任务 =================
    st.subheader("📅 今日任务")

    done_list = []

    for task in DAILY_TASKS:

        if st.checkbox(task):

            done_list.append(task)

    # 进度条
    progress = len(done_list) / len(DAILY_TASKS)

    st.markdown("### 📊 今日完成度")

    st.progress(progress)

    st.write(f"已完成 **{len(done_list)} / {len(DAILY_TASKS)}** 项任务")

   # ================= 提交打卡 =================
    if st.button("🚀 提交今日打卡", use_container_width=True):
        today = get_beijing_time().strftime("%Y/%m/%d %H:%M")
        header = ["时间"] + DAILY_TASKS
        row = [today]
        for t in DAILY_TASKS:
            row.append("✔" if t in done_list else "")

        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(row)

        # ✨ 关键修复点 1：切换到总结页面
        st.session_state['show_summary'] = True
        
        # ✨ 关键修复点 2：把今天的数据存一下，方便写总结时调用
        st.session_state['temp_done_list'] = done_list 
        
        st.toast("打卡成功！")

        new_days = get_total_days()
        for ach in ACHIEVEMENTS:
            if new_days == ach["days"]:
                st.balloons()
                st.toast(f"🎉 成就解锁：{ach['name']}！")

        # 重新运行以进入 elif 逻辑（即总结界面）
        st.rerun()

# ================= 总结界面 (你代码中缺失的 else 部分) =================
else:
    st.title("📝 今日感悟总结")
    
    # 获取刚才暂存的任务
    done_tasks = st.session_state.get('temp_done_list', [])
    st.write(f"🌟 今日已完成：{', '.join(done_tasks) if done_tasks else '无'}")
    
    mood = st.radio("当前心情：", ["😊 动力满满", "😐 正常执行", "😫 稍感疲惫"], horizontal=True)
    summary_input = st.text_area("追加一段感悟...", height=150)
    
    if st.button("✅ 提交感悟并返回主页", use_container_width=True):
        # 这里你可以添加把总结存入 MD_FILE 的逻辑
        # ... 存入 MD 逻辑 ...
        
        # 重置状态，回到主界面
        st.session_state['show_summary'] = False
        st.toast("记录已保存！")
        st.rerun()
# ================= 侧边栏 =================
with st.sidebar:

    st.header("📂 数据中心")

    sb_days = get_total_days()

    st.markdown(f"""
    <div style='background:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid #4CAF50;'>
        <p style='margin:0;font-size:14px;color:#666;'>已累计坚持</p>
        <h2 style='margin:0;color:#4CAF50;'>{sb_days} 天</h2>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if os.path.exists(LOG_FILE):

        st.download_button(
        "📊 导出 CSV",
        open(LOG_FILE, "rb"),
        "history.csv",
        "text/csv")

    if os.path.exists(MD_FILE):

        st.download_button(
        "📖 导出 Markdown",
        open(MD_FILE, "rb"),
        "diary.md",
        "text/markdown")

    st.divider()

    st.write("🏃 坚持就是胜利！")


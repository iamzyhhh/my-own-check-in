import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import random
import requests
import pytz

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程","大英赛每日汉译英","每日英语单词","408循环记忆","vibe coding课程学习"]
LOG_FILE = "work_history.csv"
MD_FILE = "Diary.md"

BACKUP_QUOTES = [
"在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞 —— 余秀华",
"满地都是六便士，他却抬头看见了月亮 —— 毛姆",
"一个人可以被毁灭，但不能被打败 —— 海明威"
]

# ================= 时间 =================
def get_beijing_time():
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz)

# ================= 统计 =================
def get_all_dates():

    if not os.path.exists(LOG_FILE):
        return []

    dates=[]

    with open(LOG_FILE,encoding="utf-8-sig") as f:

        reader=csv.reader(f)
        next(reader,None)

        for row in reader:
            if row:
                date=row[0].split(" ")[0]
                dates.append(date)

    return dates


def get_total_days():
    return len(set(get_all_dates()))


def get_current_streak():

    dates=sorted(set(get_all_dates()))

    if not dates:
        return 0

    today=get_beijing_time().strftime("%Y/%m/%d")

    if dates[-1]!=today:
        return 0

    streak=1

    for i in range(len(dates)-1,0,-1):

        d1=datetime.strptime(dates[i],"%Y/%m/%d")
        d2=datetime.strptime(dates[i-1],"%Y/%m/%d")

        if (d1-d2).days==1:
            streak+=1
        else:
            break

    return streak


def get_longest_streak():

    dates=sorted(set(get_all_dates()))

    if not dates:
        return 0

    longest=1
    current=1

    for i in range(1,len(dates)):

        d1=datetime.strptime(dates[i],"%Y/%m/%d")
        d2=datetime.strptime(dates[i-1],"%Y/%m/%d")

        if (d1-d2).days==1:
            current+=1
        else:
            longest=max(longest,current)
            current=1

    longest=max(longest,current)

    return longest


# ================= 成就 =================
ACHIEVEMENTS=[
{"name":"🥉 初出茅庐","days":7},
{"name":"🥈 坚持者","days":30},
{"name":"🥇 自律达人","days":100},
{"name":"👑 传奇","days":365}
]


def check_achievements(days):

    unlocked=[]

    for ach in ACHIEVEMENTS:
        if days>=ach["days"]:
            unlocked.append(ach["name"])

    return unlocked


# ================= 页面 =================
st.set_page_config(page_title="自律成就系统",page_icon="🚀")

# ================= session =================
if "entered" not in st.session_state:
    st.session_state.entered=False

# ================= 金句 =================
def get_quote():

    try:
        r=requests.get("https://v1.hitokoto.cn/?c=d&c=k",timeout=3)

        if r.status_code==200:

            data=r.json()

            return f"{data['hitokoto']} —— {data['from']}"

    except:
        pass

    return random.choice(BACKUP_QUOTES)


# ================= 欢迎页 =================
if not st.session_state.entered:

    st.title("🏆 欢迎回来")

    st.write("北京时间：",get_beijing_time().strftime("%Y-%m-%d %H:%M:%S"))

    st.metric("累计坚持",f"{get_total_days()} 天")

    st.info(get_quote())

    if st.button("✨ 开启今日挑战"):

        st.session_state.entered=True
        st.rerun()

    st.stop()


# ================= 主界面 =================
st.title("🎯 进度实时看板")

total_days=get_total_days()
current=get_current_streak()
longest=get_longest_streak()

c1,c2,c3=st.columns(3)

c1.metric("🏆累计",f"{total_days}天")
c2.metric("🔥连续",f"{current}天")
c3.metric("👑最长",f"{longest}天")

st.divider()

# ================= 成就 =================
st.subheader("🏅 成就墙")

unlocked=check_achievements(total_days)

for ach in ACHIEVEMENTS:

    if ach["name"] in unlocked:
        st.success(f"{ach['name']} ✔ ({ach['days']}天)")
    else:
        st.write(f"{ach['name']} 🔒 ({ach['days']}天)")


st.divider()

# ================= 今日任务 =================
st.subheader("📅 今日任务")

done_list=[]

for task in DAILY_TASKS:

    if st.checkbox(task):
        done_list.append(task)


# ===== 进度条 =====
progress=len(done_list)/len(DAILY_TASKS)

st.markdown("### 📊 今日完成度")

st.progress(progress)

st.write(f"完成 {len(done_list)} / {len(DAILY_TASKS)} 项")


# ================= 打卡 =================
if st.button("🚀 提交今日打卡"):

    today=get_beijing_time().strftime("%Y/%m/%d %H:%M")

    header=["时间"]+DAILY_TASKS

    row=[today]

    for t in DAILY_TASKS:
        row.append("✔" if t in done_list else "")

    file_exists=os.path.exists(LOG_FILE)

    with open(LOG_FILE,"a",newline="",encoding="utf-8-sig") as f:

        writer=csv.writer(f)

        if not file_exists:
            writer.writerow(header)

        writer.writerow(row)

    st.success("打卡成功！")

    new_days=get_total_days()

    for ach in ACHIEVEMENTS:

        if new_days==ach["days"]:

            st.balloons()
            st.toast(f"🎉 成就解锁：{ach['name']}")

    st.rerun()


# ================= 侧边栏 =================
with st.sidebar:

    st.header("📂 数据中心")

    st.metric("累计坚持",f"{get_total_days()} 天")

    if os.path.exists(LOG_FILE):

        st.download_button(
        "📊 导出CSV",
        open(LOG_FILE,"rb"),
        "history.csv"
        )

    st.write("🏃 坚持就是胜利")


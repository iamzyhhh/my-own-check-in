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

# --- 1. 记事本格式化函数 (增强版：加入荣耀时刻) ---
def format_log_for_notepads(date, progress, mood, summary, done_tasks):
    tasks_str = "\n".join([f"  * {t}" for t in done_tasks]) if done_tasks else "  * (今日无勾选任务)"
    log_content = f"""
================================
📅 打卡时间: {date}
📈 今日进度: {progress}
🌈 今日心情: {mood}

🏆 ✅ 荣耀时刻 (已完成项目):
{tasks_str}

📝 随笔流水账:
{summary if summary else "今日无感悟，继续加油！"}
================================
"""
    return log_content

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

# ===========================================

st.set_page_config(page_title="自律成就系统", page_icon="🚀", layout="centered")

now_bj = get_beijing_time()
today_full_str = now_bj.strftime("%Y年%m月%d日")

# --- 核心保存函数 (仅保存到本地 CSV) ---
def save_local_csv(row_data, summary_text="", mood=""):
    header = ["时间", "进度", "详情", "总结"]
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow([row_data[0], row_data[1], mood, summary_text])

# --- 页面状态管理 ---
if 'entered' not in st.session_state: st.session_state['entered'] = False
if 'show_summary' not in st.session_state: st.session_state['show_summary'] = False
if 'ready_to_download' not in st.session_state: st.session_state['ready_to_download'] = False
if 'done_list' not in st.session_state: st.session_state['done_list'] = []

if not st.session_state['entered']:
    st.balloons()
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    if st.button("✨ 开启今日挑战", use_container_width=True):
        st.session_state['entered'] = True
        st.rerun()
    st.stop()

# --- 打卡主界面 ---
if not st.session_state['show_summary']:
    st.title("🎯 进度实时看板")
    st.subheader(f"📅 {today_full_str}")
    
    current_done = []
    for task in DAILY_TASKS:
        if st.checkbox(f"**{task}**", key=f"check_{task}"):
            current_done.append(task)

    if st.button("🚀 下一步：写感悟", use_container_width=True):
        st.session_state['done_list'] = current_done # 保存勾选的任务
        N = len(DAILY_TASKS)
        st.session_state['temp_progress'] = f"{(len(current_done)/N*100):.0f}%"
        st.session_state['show_summary'] = True
        st.rerun()

# --- 累计复盘界面 ---
else:
    st.title("📝 随笔累计")
    mood = st.radio("当前心情：", ["😊 动力满满", "😐 正常执行", "😫 稍感疲惫"], horizontal=True)
    summary_input = st.text_area("今天学到了什么？", height=150)
    
    if st.button("✅ 确认并生成备份", use_container_width=True):
        st.session_state['ready_to_download'] = True
        st.toast("记录已生成！")

    if st.session_state['ready_to_download']:
        st.divider()
        st.success("🎉 荣耀时刻已装载！请下载后粘贴至 OneNote")
        
        # 调用增强版模具，把 done_list 传进去
        note_content = format_log_for_notepads(
            get_beijing_time().strftime("%Y-%m-%d %H:%M"),
            st.session_state['temp_progress'],
            mood,
            summary_input,
            st.session_state['done_list']
        )
        
        st.download_button(
            label="💾 📥 点击下载带“荣耀时刻”的记录",
            data=note_content,
            file_name=f"Study_Log_{get_beijing_time().strftime('%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        if st.button("完成打卡并返回"):
            st.session_state['ready_to_download'] = False
            st.session_state['show_summary'] = False
            st.rerun()


# --- 8. 侧边栏 ---
with st.sidebar:
    st.header("📂 数据中心")
    if os.path.exists(LOG_FILE):
        st.download_button("📊 导出历史 CSV", open(LOG_FILE, "rb"), f"History.csv", "text/csv")
    st.divider()
    st.write("🏃 **坚持就是胜利！**")

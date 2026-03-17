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

BACKUP_QUOTES = [
    "“在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞。” —— 余秀华",
    "“满地都是六便士，他却抬头看见了月亮。” —— 毛姆《月亮与六便士》",
    "“一个人可以被毁灭，但不能给打败。” —— 海明威《老人与海》"
]

# ================= 核心功能函数 =================
def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

def format_txt_content(date, done_list, mood, summary):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    done_str = "\n".join([f" ✅ {t}" for t in done_list]) if done_list else " ⚪ 暂无完成"
    todo_str = "\n".join([f" ❌ {t}" for t in todo_list]) if todo_list else " 🎉 今日全达成！"
    return f"""================================
📅 打卡日期: {date}
🌈 今日心情: {mood}
📊 完成进度: {len(done_list)}/{len(DAILY_TASKS)}

🏆 荣耀时刻 (已完成):
{done_str}

⚠️ 仍需努力 (未完成):
{todo_str}

📝 随笔感悟:
{summary if summary else "今日无感悟记录"}
================================"""

# ================= 页面设置 =================
st.set_page_config(page_title="自律打卡系统", page_icon="🚀", layout="centered")

# ================= 样式美化区域 (精修对齐) =================
st.markdown("""
<style>
/* 1. 针对复选框文字容器：强制使用 Flex 布局并居中 */
.stCheckbox div[data-testid="stMarkdownContainer"] p {
    font-size: 24px !important;  
    font-weight: 600 !important; 
    color: #333 !important;      
    /* 关键：设置行高为 1，并确保没有上下 margin 干扰 */
    line-height: 1.0 !important; 
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
}

/* 2. 针对方框（Input）本身：放大并微调位移 */
[data-testid="stCheckbox"] input {
    width: 20px !important;
    height: 20px !important;
}

/* 3. 针对整个 Label 容器：这是方框和文字的共同父级 */
[data-testid="stCheckbox"] label {
    display: flex !important;
    align-items: center !important; /* 强制垂直居中 */
    gap: 12px !important;          /* 方框和文字的间距 */
    padding: 8px 0 !important;      /* 增加行间距，避免太挤 */
    min-height: 40px !important;   /* 确保容器高度足够 */
}

/* 4. 欢迎页卡片样式 */
.quote-card {
    background:#f9f9f9; 
    padding:30px; 
    border-left:8px solid #4CAF50; 
    border-radius:12px; 
    margin:20px 0;
}
</style>
""", unsafe_allow_html=True)

# Session 初始化
if 'entered' not in st.session_state: st.session_state['entered'] = False
if 'show_summary' not in st.session_state: st.session_state['show_summary'] = False
if 'note_ready' not in st.session_state: st.session_state['note_ready'] = False

def get_refined_quote():
    MIN_LEN, MAX_LEN, MAX_RETRIES = 15, 35, 5
    for _ in range(MAX_RETRIES):
        try:
            url = f"https://v1.hitokoto.cn/?c=d&c=k&c=i&min_length={MIN_LEN}&max_length={MAX_LEN}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                content = data['hitokoto']
                bad_words = ["轻小说", "漫画", "动画", "游戏"]
                if any(word in data['from'] for word in bad_words): continue
                if MIN_LEN <= len(content) <= MAX_LEN:
                    author = data['from_who'] or "佚名"
                    return f"“{content}”", f"—— {author} 《{data['from']}》"
        except: break
    return random.choice(BACKUP_QUOTES).split(" —— ")

if 'quote_data' not in st.session_state:
    st.session_state['quote_data'] = get_refined_quote()

# ================= 欢迎页 =================
if not st.session_state['entered']:
    st.balloons()
    st.markdown("<h1 style='text-align:center;color:#4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#555;font-size:22px;'>新的机遇与挑战正在等着你 ✨</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:#888;'>🕒 <b>北京时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M')}</b></p>", unsafe_allow_html=True)
    
    content, meta = st.session_state['quote_data']
    st.markdown(f"<div class='quote-card'><h3>{content}</h3><p style='text-align:right;'>{meta}</p></div>", unsafe_allow_html=True)
    
    if st.button("✨ 开启今日挑战", use_container_width=True):
        st.session_state['entered'] = True
        st.rerun()
    st.stop()

# ================= 1. 打卡主界面 =================
if not st.session_state['show_summary']:
    st.title("🎯 今日任务看板")
    st.markdown(f"📅 **日期：{get_beijing_time().strftime('%Y/%m/%d')}**")
    
    st.divider()
    st.subheader("📝 任务清单")

    done_list = []
    for task in DAILY_TASKS:
        if st.checkbox(task, key=f"main_{task}"): 
            done_list.append(task)
    
    st.write("") 
    st.markdown("### 📊 完成进度")
    progress_val = len(done_list) / len(DAILY_TASKS)
    st.progress(progress_val)
    st.write(f"已完成 **{len(done_list)} / {len(DAILY_TASKS)}** 项任务")

    if st.button("🚀 提交今日成果", use_container_width=True):
        st.session_state['temp_done_list'] = done_list
        st.session_state['show_summary'] = True
        st.rerun()

# ================= 2. 总结与导出界面 =================
else:
    st.title("📝 今日感悟总结")
    done_list = st.session_state.get('temp_done_list', [])
    
    mood = st.radio("当前心情：", ["😊 动力满满", "😐 正常执行", "😫 稍感疲惫"], horizontal=True)
    summary_input = st.text_area("想对自己说点什么吗？", height=150)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ 返回修改"):
            st.session_state['show_summary'] = False
            st.rerun()
    with col2:
        if st.button("⏩ 直接打卡"):
            today_full = get_beijing_time().strftime("%Y/%m/%d %H:%M")
            row = [today_full] + ["✔" if t in done_list else "" for t in DAILY_TASKS]
            with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(row)
            st.toast("已同步！")
            st.session_state['show_summary'] = False
            st.rerun()
    with col3:
        if st.button("✅ 提交并导出"):
            today_full = get_beijing_time().strftime("%Y/%m/%d %H:%M")
            row = [today_full] + ["✔" if t in done_list else "" for t in DAILY_TASKS]
            with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(row)
            st.session_state['final_txt'] = format_txt_content(today_full, done_list, mood, summary_input)
            st.session_state['note_ready'] = True
            st.toast("保存成功！")

    if st.session_state.get('note_ready', False):
        st.divider()
        st.download_button(
            label="💾 下载今日总结 (.txt)",
            data=st.session_state['final_txt'],
            file_name=f"Daily_Note_{get_beijing_time().strftime('%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        if st.button("打卡圆满结束"):
            st.session_state['note_ready'] = False
            st.session_state['show_summary'] = False
            st.rerun()

# ================= 侧边栏 =================
with st.sidebar:
    st.header("📂 历史记录")
    if os.path.exists(LOG_FILE):
        st.download_button("📊 导出历史数据 (CSV)", open(LOG_FILE, "rb"), "history.csv", "text/csv")
    st.write("🏃 专注当下，便是胜利。")

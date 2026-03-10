import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import time
import random
import requests

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "my_study_log.csv"

BACKUP_QUOTES = [
    "“在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞。” —— 余秀华",
    "“满地都是六便士，他却抬头看见了月亮。” —— 毛姆《月亮与六便士》",
    "“一个人可以被毁灭，但不能给打败。” —— 海明威《老人与海》"
]
# ===========================================

st.set_page_config(page_title="自律成就系统", page_icon="🎯", layout="centered")
today_date_only = datetime.now().strftime("%Y/%m/%d")
today_full_str = datetime.now().strftime("%Y年%m月%d日")

# --- 联网获取文学语录 ---
def get_refined_quote():
    try:
        # 筛选文学和哲学类，长度20字左右
        response = requests.get("https://v1.hitokoto.cn/?c=d&c=k&min_length=15&max_length=35", timeout=3)
        if response.status_code == 200:
            data = response.json()
            author = data['from_who'] if data['from_who'] else "佚名"
            return f"“{data['hitokoto']}”", f"—— {author} 《{data['from']}》"
    except: pass
    q = random.choice(BACKUP_QUOTES)
    parts = q.split(" —— ")
    return parts[0], parts[1]

# --- 核心保存逻辑（日期去重版） ---
def save_to_csv(row_data, summary_text="", mood=""):
    # 组合总结内容：[心情图标] 总结文字
    final_summary = f"[{mood}] {summary_text}" if mood else summary_text
    row_data.append(final_summary)
    
    N = len(DAILY_TASKS)
    header = ["时间", "进度"] + [f"已完成_{i+1}" for i in range(N)] + ["隔离"] + [f"未完成_{i+1}" for i in range(N)] + ["今日总结"]
    
    all_data = []
    found_today = False
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f))
            if len(reader) > 0:
                all_data.append(header)
                for row in reader[1:]:
                    if not row: continue
                    # 检查是否是今天（按日期覆盖）
                    if row[0].startswith(today_date_only):
                        all_data.append(row_data)
                        found_today = True
                    else:
                        while len(row) < len(header): row.append("")
                        all_data.append(row)
    
    if not found_today:
        if not all_data: all_data.append(header)
        all_data.append(row_data)

    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(all_data)

# --- 状态管理 ---
if 'entered' not in st.session_state: st.session_state['entered'] = False
if 'quote_data' not in st.session_state: st.session_state['quote_data'] = get_refined_quote()
if 'show_summary' not in st.session_state: st.session_state['show_summary'] = False
if 'temp_data' not in st.session_state: st.session_state['temp_data'] = None

# --- 欢迎页面（CSS淡入动画方案二） ---
if not st.session_state['entered']:
    st.balloons()
    st.markdown("""
        <style>
        @keyframes customFadeIn { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
        .quote-card {
            animation: customFadeIn 2.5s ease-out;
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            padding: 40px; border-radius: 30px; border-left: 8px solid #4CAF50;
            box-shadow: 10px 10px 30px rgba(0,0,0,0.05); margin: 20px 0;
        }
        .welcome-title { animation: customFadeIn 1.5s ease-out; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 class='welcome-title' style='text-align: center; color: #4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: #34495e;'>{today_full_str}</h2>", unsafe_allow_html=True)
    content, meta = st.session_state['quote_data']
    st.markdown(f"<div class='quote-card'><div style='font-size:1.5rem; font-family:serif; line-height:1.8;'>{content}</div><div style='text-align:right; font-style:italic; color:#7f8c8d;'>{meta}</div></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("✨ 开启今日挑战", use_container_width=True):
            st.session_state['entered'] = True
            st.rerun()
    st.stop()

# --- 核心统计逻辑 ---
def get_stats():
    stats = {task: {"streak": 0, "fail": 0, "total": 0} for task in DAILY_TASKS}
    if not os.path.exists(LOG_FILE): return stats
    try:
        df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
        if df.empty: return stats
        for t in DAILY_TASKS:
            stats[t]["total"] = sum(1 for v in df.values.flatten() if t.strip() in str(v) and "❌" not in str(v))
        df_s = df.sort_values(by=df.columns[0], ascending=False)
        for t in DAILY_TASKS:
            count, mode = 0, None
            for _, r in df_s.iterrows():
                row_str = " ".join([str(x) for x in r.values if pd.notna(x)])
                is_done = (t.strip() in row_str and any(i in row_str for i in ["🔥", "✨", "👑"]) and "❌" not in row_str)
                is_fail = (t.strip() in row_str and "❌" in row_str)
                if not is_done and not is_fail: continue
                if mode is None:
                    if is_done: mode, count = 'doing', 1
                    else: mode, count = 'failing', 1
                else:
                    if mode == 'doing' and is_done: count += 1
                    elif mode == 'failing' and is_fail: count += 1
                    else: break
            if mode == 'doing': stats[t]["streak"] = count
            else: stats[t]["fail"] = count
    except: pass
    return stats

# --- 打卡主界面 ---
if not st.session_state['show_summary']:
    st.title("🎯 我的成就系统")
    stats = get_stats()
    done_list = []
    st.subheader("今日任务清单")
    for task in DAILY_TASKS:
        s, f = stats[task]['streak'], stats[task]['fail']
        badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
        c1, c2 = st.columns([3, 1])
        with c1:
            if st.checkbox(f"{task}", key=task): done_list.append(task)
        with c2: st.write(f"{badge}")

    if st.button("🚀 准备提交今日成果", use_container_width=True):
        todo_list = [t for t in DAILY_TASKS if t not in done_list]
        N = len(DAILY_TASKS)
        date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
        new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
        
        # 计算荣耀/追责榜
        sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
        for i in range(N):
            if i < len(sorted_done):
                t = sorted_done[i]; d = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
                icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
                new_row.append(f"{icon}{d}/{stats[t]['total'] + 1}d {t}")
            else: new_row.append("")
        new_row.append(">>>")
        sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
        for i in range(N):
            if i < len(sorted_todo):
                t = sorted_todo[i]; f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
                new_row.append(f"❌{f}d {t}")
            else: new_row.append("")
        
        st.session_state['temp_data'] = new_row
        st.session_state['show_summary'] = True
        st.rerun()

# --- 总结界面（带心情选择与美化） ---
else:
    st.title("📝 今日复盘 · 随笔")
    st.markdown("""<style>.summary-box { background-color: #fffbef; padding: 25px; border-radius: 15px; border: 1px dashed #d4af37; box-shadow: 5px 5px 15px rgba(0,0,0,0.05); }</style>""", unsafe_allow_html=True)
    
    # 1. 心情选择
    st.subheader("今日状态")
    mood_choice = st.radio(
        "选择今天的心情标签：",
        ["😊 状态拉满，高效一天", "😐 平平淡淡，贵在坚持", "😫 累但挺住了，明天继续"],
        horizontal=True
    )
    
    # 2. 总结输入
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    summary_input = st.text_area("“回首今日，有哪些收获或遗憾？”", placeholder="在这里写下你的感悟...", height=200)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ 封存今日回忆", use_container_width=True):
            save_to_csv(st.session_state['temp_data'], summary_input, mood_choice)
            st.balloons()
            st.toast("今日日志已装裱存入！")
            time.sleep(2)
            st.session_state['show_summary'] = False
            st.rerun()
    with col_b:
        if st.button("⏩ 下次再写", use_container_width=True):
            save_to_csv(st.session_state['temp_data'], "", mood_choice)
            st.session_state['show_summary'] = False
            st.rerun()
    st.stop()

# --- 下载区域 ---
st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("📂 下载完整日志 (CSV)", f, f"Log_{datetime.now().strftime('%m%d')}.csv", "text/csv", use_container_width=True)

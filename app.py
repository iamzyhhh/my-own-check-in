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

# 备用高质量文学语录（网络不稳定时使用）
BACKUP_QUOTES = [
    "“人生的磨难是很多的，所以我们不可对于每一件轻微的伤害都过于敏感。” —— 勃朗特《简·爱》",
    "“在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞。” —— 余秀华",
    "“满地都是六便士，他却抬头看见了月亮。” —— 毛姆《月亮与六便士》",
    "“一个人可以被毁灭，但不能给打败。” —— 海明威《老人与海》"
]
# ===========================================

st.set_page_config(page_title="自律成就系统", page_icon="🎯", layout="centered")

# 获取日期
today_str = datetime.now().strftime("%Y年%m月%d日")

# --- 联网获取语录（精准筛选版） ---
def get_refined_quote():
    try:
        # c=d (文学), c=k (哲学)
        response = requests.get("https://v1.hitokoto.cn/?c=d&c=k&min_length=15&max_length=30", timeout=3)
        if response.status_code == 200:
            data = response.json()
            # 拼接格式：语录 + 作者 + 来源
            author = data['from_who'] if data['from_who'] else "佚名"
            source = data['from']
            return f"“{data['hitokoto']}”", f"—— {author} 《{source}》"
    except:
        pass
    # 如果失败，从备份中随机挑一句并拆分
    q = random.choice(BACKUP_QUOTES)
    parts = q.split(" —— ")
    return parts[0], parts[1]

# --- 1. 状态管理 ---
if 'entered' not in st.session_state:
    st.session_state['entered'] = False

if 'quote_data' not in st.session_state:
    with st.spinner('正在为您翻阅书卷...'):
        st.session_state['quote_data'] = get_refined_quote()

# --- 2. 流动感欢迎页面 ---
if not st.session_state['entered']:
    st.balloons()
    
    # 注入自定义 CSS 打造流动感背景
    st.markdown("""
        <style>
        .quote-card {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            padding: 40px;
            border-radius: 30px;
            border-left: 8px solid #4CAF50;
            box-shadow: 10px 10px 30px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            margin: 20px 0;
        }
        .quote-text {
            color: #2c3e50;
            font-size: 1.5rem;
            font-family: "Noto Serif SC", serif;
            line-height: 1.8;
            margin-bottom: 20px;
            font-weight: 500;
        }
        .quote-author {
            color: #7f8c8d;
            font-size: 1.1rem;
            text-align: right;
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: #34495e;'>{today_str}</h2>", unsafe_allow_html=True)
    
    # 获取拆分后的语录和作者
    content, meta = st.session_state['quote_data']
    
    # 渲染语录卡片
    st.markdown(f"""
        <div class="quote-card">
            <div class="quote-text">{content}</div>
            <div class="quote-author">{meta}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("✨ 开启今日挑战", use_container_width=True):
            st.session_state['entered'] = True
            st.rerun()
    st.stop()

# --- 3. 核心功能逻辑 ---
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

st.title("🎯 我的成就系统")
st.caption(f"📅 记录于 {today_str}")

stats = get_stats()
done_list = []

st.subheader("今日任务")
for task in DAILY_TASKS:
    s, f = stats[task]['streak'], stats[task]['fail']
    badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox(f"{task}", key=task): done_list.append(task)
    with col2:
        st.write(f"{badge}")

if st.button("🚀 确认提交", use_container_width=True):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    N = len(DAILY_TASKS)
    date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
    
    sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
    for i in range(N):
        if i < len(sorted_done):
            t = sorted_done[i]
            d = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
            tot = stats[t]['total'] + 1
            icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
            new_row.append(f"{icon}{d}/{tot}d {t}")
        else: new_row.append("")
    new_row.append(">>>")
    
    sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
    for i in range(N):
        if i < len(sorted_todo):
            t = sorted_todo[i]
            f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
            new_row.append(f"❌{f}d {t}")
        else: new_row.append("")

    header = ["时间", "进度"] + [f"已完成_{i+1}" for i in range(N)] + ["隔离"] + [f"未完成_{i+1}" for i in range(N)]
    all_data = [header]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            old_rows = list(csv.reader(f))
            for row in old_rows[1:]:
                if not row or len(row) < 2: continue
                d_items = [it for it in row if any(x in str(it) for x in ["🔥", "✨", "👑"])]
                f_items = [it for it in row if "❌" in str(it)]
                rebuilt = [row[0], row[1]]
                for i in range(N): rebuilt.append(d_items[i] if i < len(d_items) else "")
                rebuilt.append(">>>")
                for i in range(N): rebuilt.append(f_items[i] if i < len(f_items) else "")
                all_data.append(rebuilt)
    
    all_data.append(new_row)
    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(all_data)
    
    st.balloons()
    st.success("同步成功！")
    time.sleep(1.5)
    st.rerun()

st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("📂 下载 CSV 记录", f, f"CheckIn_{datetime.now().strftime('%m%d')}.csv", "text/csv", use_container_width=True)

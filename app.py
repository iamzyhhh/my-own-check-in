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
    "“人生的磨难是很多的，所以我们不可对于每一件轻微的伤害都过于敏感。” —— 勃朗特《简·爱》",
    "“在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞。” —— 余秀华",
    "“满地都是六便士，他却抬头看见了月亮。” —— 毛姆《月亮与六便士》",
    "“一个人可以被毁灭，但不能给打败。” —— 海明威《老人与海》"
]
# ===========================================

st.set_page_config(page_title="自律成就系统", page_icon="🎯", layout="centered")
today_str = datetime.now().strftime("%Y年%m月%d日")

# --- 联网获取语录 ---
def get_refined_quote():
    try:
        response = requests.get("https://v1.hitokoto.cn/?c=d&c=k&min_length=15&max_length=35", timeout=3)
        if response.status_code == 200:
            data = response.json()
            author = data['from_who'] if data['from_who'] else "佚名"
            return f"“{data['hitokoto']}”", f"—— {author} 《{data['from']}》"
    except: pass
    q = random.choice(BACKUP_QUOTES)
    parts = q.split(" —— ")
    return parts[0], parts[1]

# --- 状态管理 ---
if 'entered' not in st.session_state: st.session_state['entered'] = False
if 'quote_data' not in st.session_state: st.session_state['quote_data'] = get_refined_quote()
if 'show_summary' not in st.session_state: st.session_state['show_summary'] = False
if 'temp_data' not in st.session_state: st.session_state['temp_data'] = None

# --- 2. 欢迎入场页面 ---
if not st.session_state['entered']:
    st.balloons() 
    
    # 注入带有动画效果的 CSS
    st.markdown("""
        <style>
        /* 关键帧动画：从下方 30px 处淡入并上移 */
        @keyframes customFadeIn {
            0% { opacity: 0; transform: translateY(30px); filter: blur(5px); }
            100% { opacity: 1; transform: translateY(0); filter: blur(0); }
        }

        /* 应用于卡片的动画：持续 2.5 秒，平滑减速 */
        .quote-card {
            animation: customFadeIn 2.5s cubic-bezier(0.22, 1, 0.36, 1);
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            padding: 40px;
            border-radius: 30px;
            border-left: 8px solid #4CAF50;
            box-shadow: 10px 10px 30px rgba(0,0,0,0.05);
            margin: 20px 0;
        }

        /* 让标题和日期也带有不同速度的淡入感，更有层次 */
        .welcome-title {
            animation: customFadeIn 1.5s ease-out;
        }
        .welcome-date {
            animation: customFadeIn 2s ease-out;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 使用类名应用动画
    st.markdown(f"<h1 class='welcome-title' style='text-align: center; color: #4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='welcome-date' style='text-align: center; color: #34495e;'>{today_str}</h2>", unsafe_allow_html=True)
    
    content, meta = st.session_state['quote_data']
    
    # 卡片现在会慢慢“浮”上来
    st.markdown(f"""
        <div class="quote-card">
            <div class="quote-text" style="color: #2c3e50; font-size: 1.5rem; font-family: serif; line-height: 1.8; margin-bottom: 20px; font-weight: 500;">{content}</div>
            <div class="quote-author" style="color: #7f8c8d; font-size: 1.1rem; text-align: right; font-style: italic;">{meta}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 按钮保持在原位，但你也可以给它加个微小的延迟感
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("✨ 开启今日挑战", use_container_width=True):
            st.session_state['entered'] = True
            st.rerun()
    st.stop()

# --- 核心功能逻辑 ---
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

def save_to_csv(row_data, summary_text=""):
    # 在行末尾追加总结
    row_data.append(summary_text)
    
    N = len(DAILY_TASKS)
    header = ["时间", "进度"] + [f"已完成_{i+1}" for i in range(N)] + ["隔离"] + [f"未完成_{i+1}" for i in range(N)] + ["今日总结"]
    
    all_data = [header]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            old_rows = list(csv.reader(f))
            for row in old_rows[1:]:
                if not row or len(row) < 2: continue
                # 保持旧数据的列数对齐
                while len(row) < len(header): row.append("")
                all_data.append(row)
    
    all_data.append(row_data)
    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(all_data)

# --- 主界面 ---
if not st.session_state['show_summary']:
    st.title("🎯 我的成就系统")
    stats = get_stats()
    done_list = []
    st.subheader("今日任务")
    for task in DAILY_TASKS:
        s, f = stats[task]['streak'], stats[task]['fail']
        badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.checkbox(f"{task}", key=task): done_list.append(task)
        with col2: st.write(f"{badge}")

    if st.button("🚀 准备提交", use_container_width=True):
        # 预计算数据
        todo_list = [t for t in DAILY_TASKS if t not in done_list]
        N = len(DAILY_TASKS)
        date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
        new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
        
        sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
        for i in range(N):
            if i < len(sorted_done):
                t = sorted_done[i]
                d = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
                icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
                new_row.append(f"{icon}{d}/{stats[t]['total'] + 1}d {t}")
            else: new_row.append("")
        new_row.append(">>>")
        sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
        for i in range(N):
            if i < len(sorted_todo):
                t = sorted_todo[i]
                f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
                new_row.append(f"❌{f}d {t}")
            else: new_row.append("")
            
        st.session_state['temp_data'] = new_row
        st.session_state['show_summary'] = True
        st.rerun()

# --- 总结与最终提交界面 ---
else:
    st.title("📝 今日复盘")
    st.info("任务已记录！是否需要为今天写下一点感悟？")
    
    summary_input = st.text_area("输入总结内容（可选）：", placeholder="今天学到了什么？有什么想对自己说的？", height=150)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 完成总结并提交", use_container_width=True):
            save_to_csv(st.session_state['temp_data'], summary_input)
            st.balloons()
            st.success("日志已同步！")
            time.sleep(1.5)
            # 重置状态
            st.session_state['show_summary'] = False
            st.session_state['temp_data'] = None
            st.rerun()
    with c2:
        if st.button("⏩ 跳过总结，直接提交", use_container_width=True):
            save_to_csv(st.session_state['temp_data'], "")
            st.success("打卡已同步！")
            time.sleep(1)
            st.session_state['show_summary'] = False
            st.session_state['temp_data'] = None
            st.rerun()

# --- 下载区域 ---
st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("📂 下载完整日志 (CSV)", f, f"Log_{datetime.now().strftime('%m%d')}.csv", "text/csv", use_container_width=True)

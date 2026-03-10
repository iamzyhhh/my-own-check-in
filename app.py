import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import time
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

# --- 【修正后的格式化函数：加入仍需努力部分】 ---
def format_log_for_notepads(date, progress, mood, summary, row_data):
    N = len(DAILY_TASKS)
    # 提取带图标的已完成任务 (索引 2 到 2+N)
    done_tasks = [t for t in row_data[2:2+N] if t] 
    # 提取带图标的未完成任务 (索引 3+N 之后)
    todo_tasks = [t for t in row_data[3+N:3+2*N] if t]
    
    done_str = "\n".join([f"  * {t}" for t in done_tasks]) if done_tasks else "  * 暂无记录"
    todo_str = "\n".join([f"  * {t}" for t in todo_tasks]) if todo_tasks else "  * 今日全达成！🎉"
    
    log_content = f"""
================================
📅 打卡时间: {date}
📊 今日进度: {progress}
🌈 今日心情: {mood}

🏆 ✅ 荣耀时刻:
{done_str}

⚠️ ⏳ 仍需努力:
{todo_str}

📝 随笔流水账:
{summary if summary else "无感悟内容"}
================================
"""
    return log_content

# --- 统一获取北京时间的函数 ---
def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

# ===========================================

st.set_page_config(page_title="自律成就系统", page_icon="🚀", layout="centered")

now_bj = get_beijing_time()
today_date_only = now_bj.strftime("%Y/%m/%d")
today_full_str = now_bj.strftime("%Y年%m月%d日")

# --- 1. 核心数据保存函数 (原封不动) ---
def save_dual_format(row_data, summary_text="", mood=""):
    N = len(DAILY_TASKS)
    header = ["时间", "进度"] + [f"已完成_{i+1}" for i in range(N)] + ["隔离"] + [f"未完成_{i+1}" for i in range(N)] + ["今日总结"]
    
    all_csv_data = []
    accumulated_summary = ""

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f))
            if len(reader) > 0:
                for row in reader[1:]:
                    if not row: continue
                    if row[0].startswith(today_date_only):
                        accumulated_summary = row[-1]
                    else:
                        while len(row) < len(header): row.append("")
                        all_csv_data.append(row)

    now_time = get_beijing_time().strftime("%H:%M")
    new_entry = f"[{now_time} | {mood}] {summary_text}" if summary_text else f"[{now_time} | {mood}]"
    final_summary = f"{accumulated_summary}\n\n{new_entry}" if accumulated_summary else new_entry
    
    save_row = row_data.copy()
    save_row.append(final_summary)
    final_csv = [header] + all_csv_data + [save_row]
    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(final_csv)

    done_tasks = [t for t in save_row[2:2+N] if t]
    todo_tasks = [t for t in save_row[3+N:3+2*N] if t]
    
    new_md_block = f"## 📅 {today_full_str}\n"
    new_md_block += f"**📊 最新完成度：{save_row[1]}**\n\n"
    new_md_block += "### ✅ 荣耀时刻\n" + ("\n".join([f"* {t}" for t in done_tasks]) if done_tasks else "* 暂无记录") + "\n\n"
    new_md_block += "### ⚠️ 仍需努力\n" + ("\n".join([f"* {t}" for t in todo_tasks]) if todo_tasks else "* 今日全达成！🎉") + "\n\n"
    new_md_block += "### ✍️ 随笔流水账\n" + final_summary + "\n\n---\n"

    full_md_content = "# 📖 我的自律手帐\n\n"
    if os.path.exists(MD_FILE):
        with open(MD_FILE, 'r', encoding='utf-8-sig') as f:
            old_content = f.read()
            if f"## 📅 {today_full_str}" in old_content:
                parts = old_content.split("---")
                other_days = [p.strip() for p in parts if f"## 📅 {today_full_str}" not in p and "# 📖" not in p and p.strip()]
                full_md_content += new_md_block + "\n" + "\n---\n".join(other_days)
            else:
                actual_old = old_content.replace("# 📖 我的自律手帐\n\n", "")
                full_md_content += new_md_block + "\n" + actual_old
    else:
        full_md_content += new_md_block

    with open(MD_FILE, 'w', encoding='utf-8-sig') as f:
        f.write(full_md_content)

# --- 2. 辅助函数 (原封不动) ---
def get_refined_quote():
    try:
        response = requests.get("https://v1.hitokoto.cn/?c=d&c=k&min_length=15&max_length=35", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return f"“{data['hitokoto']}”", f"—— {data['from_who'] or '佚名'} 《{data['from']}》"
    except: pass
    q = random.choice(BACKUP_QUOTES).split(" —— ")
    return q[0], q[1]

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
                    mode, count = ('doing', 1) if is_done else ('failing', 1)
                else:
                    if (mode == 'doing' and is_done) or (mode == 'failing' and is_fail): count += 1
                    else: break
            stats[t]["streak" if mode == 'doing' else "fail"] = count
    except: pass
    return stats

# --- 3. 页面状态与欢迎页 (原封不动) ---
if 'entered' not in st.session_state: st.session_state['entered'] = False
if 'quote_data' not in st.session_state: st.session_state['quote_data'] = get_refined_quote()
if 'show_summary' not in st.session_state: st.session_state['show_summary'] = False

if not st.session_state['entered']:
    st.balloons()
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    content, meta = st.session_state['quote_data']
    st.markdown(f"<div style='background: #f9f9f9; padding: 30px; border-left: 8px solid #4CAF50; border-radius: 10px; margin: 20px 0;'><h3>{content}</h3><p style='text-align:right;'>{meta}</p></div>", unsafe_allow_html=True)
    if st.button("✨ 开启今日挑战", use_container_width=True):
        st.session_state['entered'] = True
        st.rerun()
    st.stop()

# --- 4. 打卡主界面 (原封不动) ---
if not st.session_state['show_summary']:
    st.title("🎯 进度实时看板")
    stats = get_stats()
    done_list = []
    
    st.subheader(f"📅 {today_full_str}")
    for task in DAILY_TASKS:
        s, f = stats[task]['streak'], stats[task]['fail']
        badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.checkbox(f"**{task}**", key=task): done_list.append(task)
        with c2: st.write(badge)

    if st.button("🚀 提交/更新今日状态", use_container_width=True):
        todo_list = [t for t in DAILY_TASKS if t not in done_list]
        N = len(DAILY_TASKS)
        new_row = [get_beijing_time().strftime("%Y/%m/%d %H:%M"), f"{(len(done_list)/N*100):.0f}%"]
        
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

# --- 5. 累计复盘界面 (在此处新增导出按钮，逻辑完整捕获未完成项) ---
else:
    st.title("📝 随笔累计")
    mood = st.radio("当前心情：", ["😊 动力满满", "😐 正常执行", "😫 稍感疲惫"], horizontal=True)
    summary_input = st.text_area("追加一段感悟...", height=150)
    
    c_back, c_skip, c_save = st.columns(3)
    with c_back:
        if st.button("⬅️ 返回修改清单"):
            st.session_state['show_summary'] = False
            st.rerun()
    with c_skip:
        if st.button("⏩ 仅更新任务状态"):
            save_dual_format(st.session_state['temp_data'], "", mood)
            st.session_state['show_summary'] = False
            st.rerun()
    with c_save:
        if st.button("✅ 提交感悟并同步"):
            save_dual_format(st.session_state['temp_data'], summary_input, mood)
            st.toast("云端数据已同步！")
            st.session_state['note_ready'] = True

    if st.session_state.get('note_ready', False):
        st.divider()
        st.success("✅ 记事本备份已就绪 (包含今日未完成项)：")
        
        final_txt = format_log_for_notepads(
            get_beijing_time().strftime("%Y-%m-%d %H:%M"),
            st.session_state['temp_data'][1],
            mood,
            summary_input,
            st.session_state['temp_data']
        )
        
        st.download_button(
            label="💾 下载完整荣耀记录 (.txt)",
            data=final_txt,
            file_name=f"Daily_Record_{now_bj.strftime('%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        if st.button("打卡流程结束"):
            st.session_state['note_ready'] = False
            st.session_state['show_summary'] = False
            st.rerun()

# --- 6. 侧边栏 (原封不动) ---
with st.sidebar:
    st.header("📂 数据中心")
    if os.path.exists(LOG_FILE):
        st.download_button("📊 导出 CSV", open(LOG_FILE, "rb"), f"History_{now_bj.strftime('%m%d')}.csv", "text/csv")
    if os.path.exists(MD_FILE):
        st.download_button("📖 导出 Markdown", open(MD_FILE, "rb"), f"Diary_{now_bj.strftime('%m%d')}.md", "text/markdown")
    st.divider()
    st.write("🏃 **坚持就是胜利！**")

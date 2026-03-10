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

# --- 关键：填写你的 Notion 信息 ---
NOTION_TOKEN = "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"  # 你的 Internal Integration Token
DATABASE_ID = "20979fe1c9188013ac9e000c8bc7f2aa"   # 你的 Database ID

LOG_FILE = "work_history.csv" 
MD_FILE = "Diary.md"           

BACKUP_QUOTES = [
    "“在大雪封闭了所有出路时刻，我们要练习在冰封的土地上跳舞。” —— 余秀华",
    "“满地都是六便士，他却抬头看见了月亮。” —— 毛姆《月亮与六便士》"
]

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)
# ===========================================

st.set_page_config(page_title="自律成就系统", page_icon="🚀", layout="centered")
now_bj = get_beijing_time()
today_date_only = now_bj.strftime("%Y/%m/%d")
today_full_str = now_bj.strftime("%Y年%m月%d日")

# --- Notion API 核心逻辑 ---
def sync_to_notion(date_title, progress_val, summary_val):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 1. 查询当天是否已存在记录
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    query_data = {
        "filter": { "property": "Name", "title": { "equals": date_title } }
    }
    
    try:
        res = requests.post(query_url, headers=headers, json=query_data)
        results = res.json().get("results", [])
        
        props = {
            "进度": { "rich_text": [{"text": {"content": progress_val}}] },
            "随笔流水账": { "rich_text": [{"text": {"content": summary_val}}] }
        }

        if results:
            # 2. 如果已存在，执行更新 (PATCH)
            page_id = results[0]["id"]
            update_url = f"https://api.notion.com/v1/pages/{page_id}"
            requests.patch(update_url, headers=headers, json={"properties": props})
            return "updated"
        else:
            # 3. 如果不存在，执行新建 (POST)
            create_url = "https://api.notion.com/v1/pages"
            new_page = {
                "parent": { "database_id": DATABASE_ID },
                "properties": {
                    "Name": { "title": [{"text": {"content": date_title}}] },
                    **props
                }
            }
            requests.post(create_url, headers=headers, json=new_page)
            return "created"
    except Exception as e:
        return f"error: {str(e)}"

# --- 1. 核心数据保存函数 (CSV + Markdown + Notion) ---
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
    
    row_data.append(final_summary)
    
    # A. 保存 CSV
    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows([header] + all_csv_data + [row_data])

    # B. 保存 Markdown (略，保持你之前的逻辑)
    # ... (之前的 Markdown 覆盖逻辑代码)

    # C. 同步到 Notion
    if NOTION_TOKEN.startswith("secret_"):
        status = sync_to_notion(today_date_only, row_data[1], final_summary)
        if "error" not in status:
            st.toast(f"✅ Notion 同步成功 ({status})")
        else:
            st.error(f"Notion 同步失败: {status}")

# --- 2. 语录 & 统计 (保持不变) ---
def get_refined_quote():
    try:
        response = requests.get("https://v1.hitokoto.cn/?c=d&c=k&min_length=15&max_length=35", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return f"“{data['hitokoto']}”", f"—— {data['from_who'] or '佚名'} 《{data['from']}》"
    except: pass
    return random.choice(BACKUP_QUOTES).split(" —— ")[0], "佚名"

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
                if mode is None: mode, count = ('doing', 1) if is_done else ('failing', 1)
                else:
                    if (mode == 'doing' and is_done) or (mode == 'failing' and is_fail): count += 1
                    else: break
            stats[t]["streak" if mode == 'doing' else "fail"] = count
    except: pass
    return stats

# --- 3. UI 逻辑 (保持不变) ---
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

    if st.button("🚀 提交状态并同步 Notion", use_container_width=True):
        todo_list = [t for t in DAILY_TASKS if t not in done_list]
        N = len(DAILY_TASKS)
        new_row = [get_beijing_time().strftime("%Y/%m/%d %H:%M"), f"{(len(done_list)/N*100):.0f}%"]
        for i in range(N):
            if i < len(done_list):
                t = done_list[i]
                d = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
                new_row.append(f"🔥{d}d {t}")
            else: new_row.append("")
        new_row.append(">>>")
        for i in range(N):
            if i < len(todo_list):
                t = todo_list[i]
                f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
                new_row.append(f"❌{f}d {t}")
            else: new_row.append("")
        st.session_state['temp_data'] = new_row
        st.session_state['show_summary'] = True
        st.rerun()
else:
    st.title("📝 随笔累计")
    mood = st.radio("当前心情：", ["😊 动力满满", "😐 正常执行", "😫 稍感疲惫"], horizontal=True)
    summary_input = st.text_area("追加一段感悟...", height=150)
    if st.button("✅ 提交并同步 Notion", use_container_width=True):
        save_dual_format(st.session_state['temp_data'], summary_input, mood)
        st.session_state['show_summary'] = False
        st.rerun()

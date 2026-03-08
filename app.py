import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "work_history.csv"
# ===========================================

st.set_page_config(page_title="终极同步打卡系统", page_icon="🏆")

def get_stats():
    """全功能统计：累计、连胜、断点"""
    stats = {task: {"streak": 0, "fail": 0, "total": 0} for task in DAILY_TASKS}
    if not os.path.exists(LOG_FILE): return stats
    try:
        df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
        if df.empty: return stats
        # 累计次数
        for t in DAILY_TASKS:
            stats[t]["total"] = sum(1 for v in df.values.flatten() if t in str(v) and "❌" not in str(v))
        # 连胜状态
        df_s = df.sort_values(by=df.columns[0], ascending=False)
        for t in DAILY_TASKS:
            s, f, mode = 0, 0, None
            for _, r in df_s.iterrows():
                r_str = " ".join(map(str, r.values))
                is_d = (t in r_str and "❌" not in r_str)
                is_f = (t in r_str and "❌" in r_str)
                if mode is None:
                    if is_d: mode, s = 'doing', 1
                    elif is_f: mode, f = 'failing', 1
                    else: continue
                else:
                    if mode == 'doing' and is_d: s += 1
                    elif mode == 'failing' and is_f: f += 1
                    else: break
            stats[t]["streak"], stats[t]["fail"] = s, f
    except: pass
    return stats

# --- 核心 UI ---
st.title("🏆 终极同步打卡系统")
stats = get_stats()
done_list = []

st.subheader("今日任务确认")
for task in DAILY_TASKS:
    s, f, tot = stats[task]['streak'], stats[task]['fail'], stats[task]['total']
    badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox(f"{task}", key=task):
            done_list.append(task)
    with col2:
        st.write(f"{badge} (累计:{tot})")

if st.button("🚀 确认提交并同步 (双端通用)", use_container_width=True):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    N = len(DAILY_TASKS)
    date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 构造新行
    sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
    sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
    
    new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
    for i in range(N): # 荣耀榜
        if i < len(sorted_done):
            t = sorted_done[i]
            d, tot = stats[t]['streak'] + 1, stats[t]['total'] + 1
            icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
            new_row.append(f"{icon}{d}/{tot}d {t}")
        else: new_row.append("")
    
    new_row.append(">>>")
    for i in range(N): # 追责榜
        if i < len(sorted_todo):
            t = sorted_todo[i]
            f = stats[t]['fail'] + 1
            new_row.append(f"❌{f}d {t}")
        else: new_row.append("")

    # 读取旧数据并全量重排（防止乱码和格式错乱）
    old_rows = []
    header = ["时间", "进度"] + [f"荣耀_{i+1}" for i in range(N)] + ["隔离"] + [f"追责_{i+1}" for i in range(N)]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f))
            if len(reader) > 1: old_rows = reader[1:]

    # 合并并保存
    final_output = [header]
    for row in old_rows:
        if not row: continue
        d_items = [it for it in row if any(x in str(it) for x in ["🔥", "✨", "👑"])]
        f_items = [it for it in row if "❌" in str(it)]
        rebuilt = [row[0], row[1]]
        for i in range(N): rebuilt.append(d_items[i] if i < len(d_items) else "")
        rebuilt.append(">>>")
        for i in range(N): rebuilt.append(f_items[i] if i < len(f_items) else "")
        final_output.append(rebuilt)
    final_output.append(new_row)

    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(final_output)
    
    st.success("数据已成功同步！快去刷新网页或下载备份吧！")
    st.balloons()

# 下载备份按钮
st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as file:
        st.download_button("📂 下载 Excel 兼容版记录 (CSV)", data=file, 
                           file_name=f"同步备份_{datetime.now().strftime('%m%d')}.csv", 
                           mime="text/csv", use_container_width=True)

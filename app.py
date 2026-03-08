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
    """极其严格的状态回溯：确保状态切换时计数立即重置"""
    stats = {task: {"streak": 0, "fail": 0, "total": 0} for task in DAILY_TASKS}
    if not os.path.exists(LOG_FILE): return stats
    try:
        # 强制使用 utf-8-sig 读取
        df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
        if df.empty: return stats
        
        # 1. 累计总完成天数
        for t in DAILY_TASKS:
            stats[t]["total"] = sum(1 for v in df.values.flatten() if t in str(v) and "❌" not in str(v))
        
        # 2. 连续状态统计 (倒序回溯)
        df_s = df.sort_values(by=df.columns[0], ascending=False)
        for t in DAILY_TASKS:
            s_count, f_count, mode = 0, 0, None
            for _, r in df_s.iterrows():
                r_str = " ".join([str(val) for val in r.values if pd.notna(val)])
                # 精准匹配：任务名和图标必须同时存在
                is_done = (t in r_str and any(icon in r_str for icon in ["🔥", "✨", "👑"]) and "❌" not in r_str)
                is_fail = (t in r_str and "❌" in r_str)

                if mode is None:
                    if is_done: mode, s_count = 'doing', 1
                    elif is_fail: mode, f_count = 'failing', 1
                    else: continue # 这天没记该任务
                else:
                    if mode == 'doing':
                        if is_done: s_count += 1
                        else: break # 只要遇到一次没做，连胜立刻终止
                    elif mode == 'failing':
                        if is_fail: f_count += 1
                        else: break # 只要遇到一次做了，失败天数立刻终止
            stats[t]["streak"], stats[t]["fail"] = s_count, f_count
    except: pass
    return stats

st.title("🏆 终极同步打卡系统")
stats = get_stats()
done_list = []

st.subheader("今日任务确认")
for task in DAILY_TASKS:
    s, f, tot = stats[task]['streak'], stats[task]['fail'], stats[task]['total']
    # UI 显示：根据回溯结果显示当前状态
    badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox(f"{task}", key=task):
            done_list.append(task)
    with col2:
        st.write(f"{badge} (累计:{tot})")

if st.button("🚀 确认提交并同步 (严格重置版)", use_container_width=True):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    N = len(DAILY_TASKS)
    date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 构造新行数据
    # 只有今天勾选的才算连胜，没勾选的算失败
    new_row_data = []
    
    # 荣耀榜逻辑
    sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
    new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
    
    for i in range(N):
        if i < len(sorted_done):
            t = sorted_done[i]
            # 如果昨天是失败(f>0)，今天完成则天数强制重置为1
            d = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
            tot = stats[t]['total'] + 1
            icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
            new_row.append(f"{icon}{d}/{tot}d {t}")
        else: new_row.append("")
    
    new_row.append(">>>")
    
    # 追责榜逻辑
    sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
    for i in range(N):
        if i < len(sorted_todo):
            t = sorted_todo[i]
            # 如果昨天是成功(s>0)，今天失败则天数强制重置为1
            f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
            new_row.append(f"❌{f}d {t}")
        else: new_row.append("")

    # --- 全量对齐重写逻辑 (解决乱码与错位) ---
    header = ["时间", "进度"] + [f"已完成_{i+1}" for i in range(N)] + ["隔离"] + [f"未完成_{i+1}" for i in range(N)]
    old_rows = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f))
            if len(reader) > 1: old_rows = reader[1:]

    final_output = [header]
    for row in old_rows:
        if not row or len(row) < 2: continue
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
    
    st.success("同步成功！状态已严格校准。")
    st.balloons()

# 下载区域
st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("📂 下载全功能 Excel 记录", data=f, 
                           file_name=f"CheckIn_Backup_{datetime.now().strftime('%m%d')}.csv", 
                           mime="text/csv", use_container_width=True)

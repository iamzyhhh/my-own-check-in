import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import time  # 导入时间模块用于延迟

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "work_history.csv"
# ===========================================

st.set_page_config(page_title="独立连击打卡系统", page_icon="🎯")

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

st.title("🏆 独立连击打卡系统")
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
    
    # 荣耀榜
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
    # 追责榜
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
    
    # --- 改进后的动画逻辑 ---
    st.balloons() # 飞气球
    st.success("同步成功！各项目连击已独立锁定。") # 弹出绿色成功框
    time.sleep(1.5) # 给动画留 1.5 秒的表演时间
    st.rerun() # 之后再刷新，确保下载按钮出现

# --- 下载区域 ---
st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("📂 下载 CSV 记录", f, f"CheckIn_{datetime.now().strftime('%m%d')}.csv", "text/csv", use_container_width=True)

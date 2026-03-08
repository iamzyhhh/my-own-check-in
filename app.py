import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "work_history.csv"
# ===========================================

st.set_page_config(page_title="硬核断点打卡系统", page_icon="🎯")

def get_stats():
    """
    最严格的回溯逻辑：
    只要状态一变（勾选变未勾选，或反之），计数立刻停止。
    """
    stats = {task: {"streak": 0, "fail": 0, "total": 0} for task in DAILY_TASKS}
    if not os.path.exists(LOG_FILE): return stats
    try:
        df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
        if df.empty: return stats
        
        # 1. 累计完成总数 (仅做数据展示，不参与连击计算)
        for t in DAILY_TASKS:
            stats[t]["total"] = sum(1 for v in df.values.flatten() if t.strip() in str(v) and "❌" not in str(v))
        
        # 2. 严格连击/连败回溯 (倒序)
        df_s = df.sort_values(by=df.columns[0], ascending=False)
        for t in DAILY_TASKS:
            count, mode = 0, None
            for _, r in df_s.iterrows():
                row_str = " ".join([str(x) for x in r.values if pd.notna(x)])
                is_done = (t.strip() in row_str and any(i in row_str for i in ["🔥", "✨", "👑"]) and "❌" not in row_str)
                is_fail = (t.strip() in row_str and "❌" in row_str)

                if mode is None: # 确定第一份记录的状态
                    if is_done: mode, count = 'doing', 1
                    elif is_fail: mode, count = 'failing', 1
                    else: continue 
                else: # 持续检查直到状态断裂
                    if mode == 'doing' and is_done: count += 1
                    elif mode == 'failing' and is_fail: count += 1
                    else: break # 状态变了，立刻退出循环
            
            if mode == 'doing': stats[t]["streak"] = count
            if mode == 'failing': stats[t]["fail"] = count
    except: pass
    return stats

st.title("🏆 硬核断点同步系统")
stats = get_stats()
done_list = []

st.subheader("今日任务")
for task in DAILY_TASKS:
    s, f = stats[task]['streak'], stats[task]['fail']
    # UI显示：🔥代表连胜，❌代表连败
    badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox(f"{task}", key=task):
            done_list.append(task)
    with col2:
        st.write(f"{badge}")

if st.button("🚀 确认提交 (全同步)", use_container_width=True):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    N = len(DAILY_TASKS)
    date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
    
    # 1. 处理已完成 (荣耀榜)
    sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
    for i in range(N):
        if i < len(sorted_done):
            t = sorted_done[i]
            # 严格重置：如果昨天是失败状态(fail > 0)，今天天数必须强制为 1
            current_s = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
            current_t = stats[t]['total'] + 1
            icon = "👑" if current_s > 7 else ("✨" if current_s > 3 else "🔥")
            # 存入 Excel 的格式：图标+连胜/总累计
            new_row.append(f"{icon}{current_s}/{current_t}d {t}")
        else: new_row.append("")
    
    new_row.append(">>>")
    
    # 2. 处理未完成 (追责榜)
    sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
    for i in range(N):
        if i < len(sorted_todo):
            t = sorted_todo[i]
            # 严格重置：如果昨天是成功状态(streak > 0)，今天失败计数强制为 1
            current_f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
            new_row.append(f"❌{current_f}d {t}")
        else: new_row.append("")

    # 保存与重构逻辑
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
    
    st.success("同步成功！已执行最严断点重置。")
    st.balloons()
    st.rerun()

# --- 下载区域 ---
st.markdown("---")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("📂 下载 CSV 记录", f, f"CheckIn_{datetime.now().strftime('%m%d')}.csv", "text/csv", use_container_width=True)

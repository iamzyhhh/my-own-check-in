import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "work_history.csv"
# ===========================================

st.set_page_config(page_title="终极同步系统-严格版", page_icon="🎯")

def get_stats():
    """极其严格的状态回溯：确保状态切换时计数立即重置"""
    stats = {task: {"streak": 0, "fail": 0, "total": 0} for task in DAILY_TASKS}
    if not os.path.exists(LOG_FILE): return stats
    try:
        df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
        if df.empty: return stats
        
        # 1. 累计完成总数 (物理计数，不影响连续天数)
        for t in DAILY_TASKS:
            stats[t]["total"] = sum(1 for v in df.values.flatten() if t.strip() in str(v) and "❌" not in str(v))
        
        # 2. 连续状态统计 (按时间倒序回溯)
        df_s = df.sort_values(by=df.columns[0], ascending=False)
        for t in DAILY_TASKS:
            s_c, f_c, mode = 0, 0, None
            for _, r in df_s.iterrows():
                row_str = " ".join([str(x) for x in r.values if pd.notna(x)])
                # 判断当前行对于该任务的状态
                is_done = (t.strip() in row_str and any(i in row_str for i in ["🔥", "✨", "👑"]) and "❌" not in row_str)
                is_fail = (t.strip() in row_str and "❌" in row_str)

                if mode is None: # 确定起始状态（昨天或最近一次记录的状态）
                    if is_done: mode, s_c = 'doing', 1
                    elif is_fail: mode, f_c = 'failing', 1
                    else: continue 
                else: # 开始回溯连胜/连败
                    if mode == 'doing':
                        if is_done: s_c += 1
                        else: break # 遇到失败或缺失，连胜立刻切断
                    elif mode == 'failing':
                        if is_fail: f_c += 1
                        else: break # 遇到成功或缺失，连败立刻切断
            stats[t]["streak"], stats[t]["fail"] = s_c, f_c
    except: pass
    return stats

st.title("🏆 终极同步打卡系统")
stats = get_stats()
done_list = []

st.subheader("今日任务")
for task in DAILY_TASKS:
    s, f, tot = stats[task]['streak'], stats[task]['fail'], stats[task]['total']
    # 逻辑：如果昨天是勾选(s>0)，今天还没勾选前，状态显示为 🔥sd
    # 如果昨天是失败(f>0)，显示为 ❌fd
    badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox(f"{task}", key=task):
            done_list.append(task)
    with col2:
        st.write(f"{badge} (累计:{tot}d)")

if st.button("🚀 确认提交 (严格校准版)", use_container_width=True):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    N = len(DAILY_TASKS)
    date_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 构造新行数据
    new_row = [date_str, f"{(len(done_list)/N*100):.0f}%"]
    
    # 1. 荣耀榜 (今日完成的)
    sorted_done = sorted(done_list, key=lambda x: stats[x]['streak'], reverse=True)
    for i in range(N):
        if i < len(sorted_done):
            t = sorted_done[i]
            # 严格重置：如果昨天是失败状态，今天天数必须从 1 开始，不能累加旧天数
            d = 1 if stats[t]['fail'] > 0 else stats[t]['streak'] + 1
            tot = stats[t]['total'] + 1
            icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
            new_row.append(f"{icon}{d}/{tot}d {t}")
        else: new_row.append("")
    
    new_row.append(">>>")
    
    # 2. 追责榜 (今日未完成的)
    sorted_todo = sorted(todo_list, key=lambda x: stats[x]['fail'], reverse=True)
    for i in range(N):
        if i < len(sorted_todo):
            t = sorted_todo[i]
            # 严格重置：如果昨天是成功状态，今天失败天数必须从 1 开始
            f = 1 if stats[t]['streak'] > 0 else stats[t]['fail'] + 1
            new_row.append(f"❌{f}d {t}")
        else: new_row.append("")

    # --- 数据保存与重构 ---
    header = ["时间", "进度"] + [f"已完成_{i+1}" for i in range(N)] + ["隔离"] + [f"未完成_{i+1}" for i in range(N)]
    all_data = [header]
    if os.path.exists(LOG_FILE):
        # --- 强制显示下载按钮 ---
st.markdown("---")
try:
    with open(LOG_FILE, "rb") as f:
        st.download_button(
            label="📂 点击下载打卡记录 (CSV)", 
            data=f, 
            file_name=f"CheckIn_Backup_{datetime.now().strftime('%m%d')}.csv", 
            mime="text/csv", 
            use_container_width=True
        )
except FileNotFoundError:
    # 如果真的没文件，显示一个灰色的占位说明
    st.button("📂 暂无记录可供下载", disabled=True, use_container_width=True)
    st.info("💡 如果你刚提交过，请点击右上角 'Rerun' 刷新网页。")
    
    all_data.append(new_row)
    with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(all_data)
    
    st.success("提交成功！状态已强制校准。")
    st.balloons()

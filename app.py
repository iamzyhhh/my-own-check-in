import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ================= 配置区域 =================
DAILY_TASKS = ["数学每日进程", "大英赛每日汉译英", "每日英语单词", "408循环记忆", "vibe coding课程学习"]
LOG_FILE = "work_history.csv"
# ===========================================

st.set_page_config(page_title="打卡成就系统", page_icon="🔥")

# 加载数据逻辑
def get_stats():
    stats = {task: {"streak": 0, "fail": 0, "total": 0} for task in DAILY_TASKS}
    if not os.path.exists(LOG_FILE): return stats
    try:
        df = pd.read_csv(LOG_FILE)
        if df.empty: return stats
        # 累计总数
        for t in DAILY_TASKS:
            stats[t]["total"] = sum(1 for v in df.values.flatten() if t in str(v) and "❌" not in str(v))
        # 连胜重置逻辑
        df_s = df.sort_values(by=df.columns[0], ascending=False)
        for t in DAILY_TASKS:
            s, f, mode = 0, 0, None
            for _, r in df_s.iterrows():
                r_str = " ".join(map(str, r.values))
                is_d, is_f = (t in r_str and "❌" not in r_str), (t in r_str and "❌" in r_str)
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

# 网页界面
st.title("🏆 我的打卡成就系统")
st.write(f"今天是：{datetime.now().strftime('%Y/%m/%d')}")

stats = get_stats()
done_list = []

# 手机端适配的勾选列表
st.subheader("今日任务确认")
for task in DAILY_TASKS:
    s, f, tot = stats[task]['streak'], stats[task]['fail'], stats[task]['total']
    badge = f"🔥{s}d" if s > 0 else (f"❌{f}d" if f > 0 else "🆕")
    # 每一行显示任务和状态
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox(f"{task}", key=task):
            done_list.append(task)
    with col2:
        st.write(f"{badge} ({tot}d)")

if st.button("🚀 确认提交今日战果", use_container_width=True):
    # 这里保存数据的逻辑和之前完全一样
    # 由于网页版特殊性，我们简化处理直接追加
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    
    # 构造新行（省略全量对齐重排的复杂逻辑以适应云端）
    N = len(DAILY_TASKS)
    new_data = {
        "时间": [datetime.now().strftime("%Y/%m/%d %H:%M")],
        "进度": [f"{len(done_list)/N*100:.0f}%"]
    }
    # 简单模拟荣耀格
    for i, t in enumerate(sorted(done_list)):
        d = stats[t]['streak'] + 1
        icon = "👑" if d > 7 else ("✨" if d > 3 else "🔥")
        new_data[f"荣耀_{i+1}"] = [f"{icon}{d}d {t}"]
    
    new_df = pd.DataFrame(new_data)
    if not os.path.exists(LOG_FILE):
        new_df.to_csv(LOG_FILE, index=False)
    else:
        new_df.to_csv(LOG_FILE, mode='a', header=False, index=False)
    
    st.success("提交成功！加油，明天见！")
    st.balloons() # 撒花庆祝
    # --- 这一段是新增的下载功能 ---
st.markdown("---")
if os.path.exists(LOG_FILE):
    # 读取最新的数据
    with open(LOG_FILE, "rb") as file:
        st.download_button(
            label="📂 点击下载打卡记录 (CSV)",
            data=file,
            file_name=f"我的打卡备份_{datetime.now().strftime('%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("💡 还没有历史记录，先完成一次打卡吧！")

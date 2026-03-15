import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
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

ACHIEVEMENTS = [
    {"name": "🥉 初出茅庐", "days": 7},
    {"name": "🥈 坚持者", "days": 30},
    {"name": "🥇 自律达人", "days": 100},
    {"name": "👑 传奇", "days": 365}
]

# ================= 时间与统计函数 =================
def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

def get_all_dates():
    if not os.path.exists(LOG_FILE): return []
    dates = []
    try:
        with open(LOG_FILE, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row: dates.append(row[0].split(" ")[0])
    except: return []
    return dates

def get_total_days():
    if not os.path.exists(LOG_FILE): 
        return 0
    
    try:
        with open(LOG_FILE, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None) # 跳过表头
            first_row = next(reader, None) # 获取第一条打卡记录
            if first_row:
                # 拿到你人生中第一次打卡的日期
                start_date_str = first_row[0].split(" ")[0].replace("-", "/")
                start_date = datetime.strptime(start_date_str, "%Y/%m/%d")
                # 计算今天和第一天的差值
                today = datetime.now()
                return (today - start_date).days + 1
    except:
        pass
    return 0

def get_current_streak():
    dates = sorted(set(get_all_dates()))
    if not dates: return 0
    today = get_beijing_time().strftime("%Y/%m/%d")
    if dates[-1] != today: return 0
    streak = 1
    for i in range(len(dates)-1, 0, -1):
        d1 = datetime.strptime(dates[i], "%Y/%m/%d")
        d2 = datetime.strptime(dates[i-1], "%Y/%m/%d")
        if (d1 - d2).days == 1: streak += 1
        else: break
    return streak

def get_longest_streak():
    dates = sorted(set(get_all_dates()))
    if not dates: return 0
    longest = current = 1
    for i in range(1, len(dates)):
        d1 = datetime.strptime(dates[i], "%Y/%m/%d")
        d2 = datetime.strptime(dates[i-1], "%Y/%m/%d")
        if (d1 - d2).days == 1: current += 1
        else:
            longest = max(longest, current)
            current = 1
    return max(longest, current)

def check_achievements(days):
    return [ach["name"] for ach in ACHIEVEMENTS if days >= ach["days"]]

def format_txt_content(date, done_list, mood, summary):
    todo_list = [t for t in DAILY_TASKS if t not in done_list]
    done_str = "\n".join([f" ✅ {t}" for t in done_list]) if done_list else " ⚪ 暂无完成"
    todo_str = "\n".join([f" ❌ {t}" for t in todo_list]) if todo_list else " 🎉 今日全达成！"
    return f"""================================
📅 打卡日期: {date}
🌈 今日心情: {mood}
📊 完成进度: {len(done_list)}/{len(DAILY_TASKS)}

🏆 荣耀时刻 (已完成):
{done_str}

⚠️ 仍需努力 (未完成):
{todo_str}

📝 随笔感悟:
{summary if summary else "今日无感悟记录"}
================================"""

# ================= 页面设置 =================
st.set_page_config(page_title="自律成就系统", page_icon="🚀", layout="centered")

# ================= 样式美化区域 (修复对齐) =================
st.markdown("""
<style>
/* 1. 放大复选框文字，强制垂直居中对齐 */
.stCheckbox div[data-testid="stMarkdownContainer"] p {
    font-size: 24px !important;  
    font-weight: 600 !important; 
    color: #333 !important;      
    line-height: 1.2 !important; 
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
}

/* 2. 放大勾选框并修正位置偏差 */
[data-testid="stCheckbox"] {
    transform: scale(1.3);
    margin-right: 15px;
    display: inline-flex !important;
    align-items: center !important;
}

/* 3. 修正 Label 容器高度，防止文字飘起 */
[data-testid="stCheckbox"] label {
    display: flex !important;
    align-items: center !important;
    padding: 10px 0 !important;
}

.quote-card {
    background:#f9f9f9; padding:30px; border-left:8px solid #4CAF50; border-radius:12px; margin:20px 0;
}
</style>
""", unsafe_allow_html=True)

# Session 初始化
if 'entered' not in st.session_state: st.session_state['entered'] = False
if 'show_summary' not in st.session_state: st.session_state['show_summary'] = False
if 'note_ready' not in st.session_state: st.session_state['note_ready'] = False

def get_refined_quote():
    # 允许的字数范围：严格限制在 15-35 字之间，保证 20 字左右的观感
    MIN_LEN = 15
    MAX_LEN = 35
    
    # 尝试抓取次数上限，防止死循环
    MAX_RETRIES = 5 
    
    for _ in range(MAX_RETRIES):
        try:
            # c=d (哲学), c=k (诗词), c=i (励志)
            url = f"https://v1.hitokoto.cn/?c=d&c=k&c=i&min_length={MIN_LEN}&max_length={MAX_LEN}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                content = data['hitokoto']
                
                # 额外的关键词过滤：过滤掉过于二次元或口水话的内容
                bad_words = ["轻小说", "漫画", "动画", "游戏"]
                if any(word in data['from'] for word in bad_words):
                    continue
                
                # 检查字数是否符合你的“20字左右”
                if MIN_LEN <= len(content) <= MAX_LEN:
                    author = data['from_who'] or "佚名"
                    source = f"《{data['from']}》"
                    return f"“{content}”", f"—— {author} {source}"
        except:
            break # 报错则跳出循环使用备用金句
            
    # 如果接口没刷出合适的，或者网络报错，则从你认可的高质量本地库里随机选
    return random.choice(BACKUP_QUOTES).split(" —— ")

if 'quote_data' not in st.session_state:
    st.session_state['quote_data'] = get_refined_quote()

# ================= 欢迎页 =================
if not st.session_state['entered']:
    st.balloons()
    total_days = get_total_days()
    st.markdown("<h1 style='text-align:center;color:#4CAF50;'>🏆 欢迎回来</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#555;font-size:24px;font-weight:bold;'>欢迎回来，新的机遇与挑战正在等着你 ✨</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>🕒 <b>北京时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</b></p>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;margin-bottom:10px;'><span style='font-size:20px;color:#666;'>已累计坚持</span><span style='font-size:36px;font-weight:bold;color:#4CAF50;margin:0 10px;'>{total_days}</span><span style='font-size:20px;color:#666;'>天</span></div>", unsafe_allow_html=True)
    
    content, meta = st.session_state['quote_data']
    st.markdown(f"<div class='quote-card'><h3>{content}</h3><p style='text-align:right;'>{meta}</p></div>", unsafe_allow_html=True)
    
    if st.button("✨ 开启今日挑战", use_container_width=True):
        st.session_state['entered'] = True
        st.rerun()
    st.stop()

# ================= 1. 打卡主界面 =================
if not st.session_state['show_summary']:
    st.title("🎯 进度实时看板")
    total_days = get_total_days()
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 累计坚持", f"{total_days} 天")
    c2.metric("🔥 当前连续", f"{get_current_streak()} 天")
    c3.metric("👑 历史最长", f"{get_longest_streak()} 天")

    st.subheader("🏅 成就墙")
    unlocked = check_achievements(total_days)
    cols = st.columns(2)
    for idx, ach in enumerate(ACHIEVEMENTS):
        with cols[idx % 2]:
            if ach["name"] in unlocked: st.success(f"{ach['name']} ✔")
            else: st.write(f"🔒 {ach['name']} ({ach['days']}天)")

    st.divider()
    st.subheader("📅 今日任务清单")

    done_list = []
    for task in DAILY_TASKS:
        if st.checkbox(task, key=f"main_{task}"): 
            done_list.append(task)
    
    st.write("") 
    st.markdown("### 📊 今日完成度")
    progress_val = len(done_list) / len(DAILY_TASKS)
    st.progress(progress_val)
    st.write(f"已完成 **{len(done_list)} / {len(DAILY_TASKS)}** 项任务")

    if st.button("🚀 确认完成，进入总结", use_container_width=True):
        st.session_state['temp_done_list'] = done_list
        st.session_state['show_summary'] = True
        st.rerun()

# ================= 2. 总结与导出界面 =================
else:
    st.title("📝 今日感悟总结")
    done_list = st.session_state.get('temp_done_list', [])
    st.info(f"今日已勾选完成 {len(done_list)} 项任务。")
    
    mood = st.radio("当前心情：", ["😊 动力满满", "😐 正常执行", "😫 稍感疲惫"], horizontal=True)
    summary_input = st.text_area("想对自己说点什么吗？要天天开心哦 😄", height=150)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ 返回修改清单"):
            st.session_state['show_summary'] = False
            st.rerun()
            
    with col2:
        if st.button("⏩ 跳过感悟直接打卡"):
            today_full = get_beijing_time().strftime("%Y/%m/%d %H:%M")
            row = [today_full] + ["✔" if t in done_list else "" for t in DAILY_TASKS]
            with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(row)
            st.toast("任务状态已成功同步！")
            st.session_state['show_summary'] = False
            st.rerun()

    with col3:
        if st.button("✅ 提交总结并导出"):
            today_full = get_beijing_time().strftime("%Y/%m/%d %H:%M")
            row = [today_full] + ["✔" if t in done_list else "" for t in DAILY_TASKS]
            with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(row)
            
            new_days = get_total_days()
            for ach in ACHIEVEMENTS:
                if new_days == ach["days"]:
                    st.balloons()
                    st.toast(f"🎉 解锁成就: {ach['name']}!")
            
            st.session_state['final_txt'] = format_txt_content(today_full, done_list, mood, summary_input)
            st.session_state['note_ready'] = True
            st.toast("总结记录成功！")

    if st.session_state.get('note_ready', False):
        st.divider()
        st.success("✨ 今日总结文档已生成：")
        st.download_button(
            label="💾 点击下载今日总结 (.txt)",
            data=st.session_state['final_txt'],
            file_name=f"Daily_Note_{get_beijing_time().strftime('%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        if st.button("打卡圆满结束"):
            st.session_state['note_ready'] = False
            st.session_state['show_summary'] = False
            st.rerun()

# ================= 侧边栏 =================
with st.sidebar:
    st.header("📂 数据中心")
    sb_days = get_total_days()
    st.markdown(f"<div style='background:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid #4CAF50;'><p style='margin:0;font-size:14px;color:#666;'>已累计坚持</p><h2 style='margin:0;color:#4CAF50;'>{sb_days} 天</h2></div>", unsafe_allow_html=True)
    st.divider()
    if os.path.exists(LOG_FILE):
        st.download_button("📊 导出历史 CSV", open(LOG_FILE, "rb"), "history.csv", "text/csv")
    st.write("🏃 坚持就是胜利！")

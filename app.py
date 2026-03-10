import streamlit as st
import requests

# 填入你的信息
TOKEN = "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"
DB_ID = "20979fe1c91880e4b060c95b76564c88"

st.title("🧪 Notion 连通性暴力测试")

test_msg = st.text_input("随便写点什么测试：", "Hello Notion!")

if st.button("🚀 点击强行发送"):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": { "database_id": DB_ID },
        "properties": {
            "Name": { "title": [{"text": {"content": test_msg}}] }
        }
    }
    res = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    
    if res.status_code == 200:
        result = res.json()
        st.success("✅ 发送成功！")
        st.markdown(f"🔗 [点击这个链接去 Notion 找它]({result.get('url')})")
    else:
        st.error(f"❌ 还是失败了，状态码：{res.status_code}")
        st.json(res.json())

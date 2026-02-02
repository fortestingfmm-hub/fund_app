import streamlit as st
import requests
import json
import re
import pandas as pd
from datetime import datetime

# 设置页面配置
st.set_page_config(page_title="实时基金估值监控", layout="wide")

# --- 数据抓取逻辑 ---
def get_fund_estimate(fund_code):
    """从天天基金获取实时估值"""
    url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    try:
        response = requests.get(url, timeout=5)
        # 接口返回的是 jsonpgz({...}) 格式，需要正则提取
        content = response.text
        json_str = re.findall(r"jsonpgz\((.*)\)", content)[0]
        data = json.loads(json_str)
        return {
            "代码": data['fundcode'],
            "名称": data['name'],
            "单位净值": data['dwjz'],
            "估值": data['gsz'],
            "日涨幅(%)": data['gszzl'],
            "更新时间": data['gztime']
        }
    except Exception as e:
        return None

# --- 初始化持仓数据 ---
if 'holdings' not in st.session_state:
    # 默认展示几个常用基金
    st.session_state.holdings = ['000001', '320007']

# --- UI 界面布局 ---
st.title("📈 基金实时估值助手")

# 侧边栏：添加持仓
with st.sidebar:
    st.header("添加持仓")
    new_code = st.text_input("输入基金代码 (6位)", max_chars=6)
    if st.button("➕ 加入持仓"):
        if new_code and len(new_code) == 6:
            if new_code not in st.session_state.holdings:
                st.session_state.holdings.append(new_code)
                st.success(f"代码 {new_code} 已添加")
                st.rerun() # 立即刷新
            else:
                st.warning("该基金已在列表中")
        else:
            st.error("请输入有效的6位代码")

    st.divider()
    if st.button("🗑️ 清空所有"):
        st.session_state.holdings = []
        st.rerun()

# 主页面操作栏
col1, col2 = st.columns([1, 6])
with col1:
    if st.button("🔄 手动刷新"):
        st.rerun()
with col2:
    st.write(f"最后刷新时间: {datetime.now().strftime('%H:%M:%S')}")

# --- 展示持仓列表 ---
if not st.session_state.holdings:
    st.info("当前持仓为空，请在侧边栏添加基金代码。")
else:
    all_data = []
    with st.spinner('正在获取实时估值...'):
        for code in st.session_state.holdings:
            res = get_fund_estimate(code)
            if res:
                all_data.append(res)
            else:
                st.error(f"无法获取代码 {code} 的数据，请检查代码是否正确")

    if all_data:
        df = pd.DataFrame(all_data)
        
        # 样式美化：涨红跌绿
        def color_growth(val):
            val = float(val)
            color = 'red' if val > 0 else 'green' if val < 0 else 'black'
            return f'color: {color}'

        # 显示表格
        st.dataframe(
            df.style.applymap(color_growth, subset=['日涨幅(%)']),
            use_container_width=True,
            hide_index=True
        )

        # 简单的统计展示
        avg_gain = df['日涨幅(%)'].astype(float).mean()
        st.metric("今日平均涨幅", f"{avg_gain:.2f}%", delta=f"{avg_gain:.2f}%")
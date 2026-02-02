import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 页面基础配置
st.set_page_config(page_title="全品种基金实时监控", layout="wide")

# --- 核心：使用东方财富 App 接口 ---
def get_realtime_data(fund_code):
    """
    通过东方财富 Mobile 接口获取实时估值
    支持普通基金、LOF(161226)、ETF联接等
    """
    # 东方财富实时估值详情接口
    url = f"https://fundmobapi.eastmoney.com/FundMApi/FundVarietieValuationDetail.ashx"
    params = {
        "FCODE": fund_code,
        "deviceid": "123456",
        "version": "6.5.5",
        "appversion": "6.5.5",
        "plat": "Android"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        res_json = response.json()
        
        if res_json['ErrCode'] == 0:
            data = res_json['Datas']
            # gsz: 估值, gszzl: 估值涨幅, jztime: 估值时间
            return {
                "基金代码": fund_code,
                "基金名称": data['SHORTNAME'],
                "实时估值": data['gz'],
                "当日涨跌幅": f"{data['gszzl']}%",
                "数值涨幅": float(data['gszzl']) if data['gszzl'] else 0.0,
                "单位净值(昨日)": data['dwjz'],
                "更新时间": data['gztime']
            }
        else:
            return None
    except Exception as e:
        return None

# --- Session State 初始化 ---
if 'my_funds' not in st.session_state:
    # 默认加入 161226 (白银期货) 和 000001
    st.session_state.my_funds = ['161226', '000001']

# --- 侧边栏：增删管理 ---
with st.sidebar:
    st.header("⚙️ 持仓管理")
    
    # 添加基金
    new_fund = st.text_input("输入基金代码", max_chars=6, placeholder="例如: 161226")
    if st.button("➕ 加入持仓", use_container_width=True):
        if new_fund and len(new_fund) == 6:
            if new_fund not in st.session_state.my_funds:
                st.session_state.my_funds.append(new_fund)
                st.rerun()
            else:
                st.warning("该基金已在列表中")
        else:
            st.error("请输入6位基金代码")

    st.divider()
    
    # 删除基金
    st.subheader("🗑️ 移除持仓")
    for code in st.session_state.my_funds:
        col_code, col_btn = st.columns([3, 1])
        col_code.write(code)
        if col_btn.button("❌", key=f"del_{code}"):
            st.session_state.my_funds.remove(code)
            st.rerun()

# --- 主界面 ---
st.title("📊 基金/LOF 实时估值看板")

# 顶部操作栏
c1, c2 = st.columns([1, 4])
with c1:
    if st.button("🔄 刷新行情", type="primary"):
        st.rerun()
with c2:
    st.write(f"最后刷新：{datetime.now().strftime('%H:%M:%S')}")

# 获取并显示数据
if not st.session_state.my_funds:
    st.info("左侧菜单输入代码，开始监控基金。")
else:
    results = []
    with st.spinner('正在调取最新接口数据...'):
        for code in st.session_state.my_funds:
            data = get_realtime_data(code)
            if data:
                results.append(data)
    
    if results:
        df = pd.DataFrame(results)
        
        # 涨跌幅颜色处理
        def color_pick(val):
            try:
                num = float(val.replace('%', ''))
                if num > 0: return 'color: #ef5350; font-weight: bold;' # 红
                if num < 0: return 'color: #26a69a; font-weight: bold;' # 绿
            except:
                pass
            return 'color: gray;'

        # 渲染表格
        st.table(df.drop(columns=['数值涨幅']).style.applymap(color_pick, subset=['当日涨跌幅']))
        
        # 备注
        st.caption("注：数据来源东方财富实时接口。161226(白银期货)在交易时段会显示最新估值。")
    else:
        st.warning("未抓取到数据，请检查网络或代码是否正确。")

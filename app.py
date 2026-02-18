import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ตรวจสอบ Library สำหรับการทำนาย
try:
    from sklearn.linear_model import LinearRegression
    has_sklearn = True
except ImportError:
    has_sklearn = False

# 1. Page Configuration
st.set_page_config(page_title="KOON Modern Trade Intelligence", page_icon="🟠", layout="wide")

# KOON Brand Color
KOON_ORANGE = "#FF914D"
ZONE_COLORS = {"City": "#003f5c", "Residential": "#bc5090", "Provincial": "#ffa600"}

# แก้ไข CSS ใหม่: เน้นเปลี่ยนสีแต่ไม่ขัดขวางการคลิก
st.markdown(f"""
    <style>
    /* เปลี่ยนสีพื้นหลัง Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {KOON_ORANGE} !important;
    }}
    /* เปลี่ยนสีหัวข้อและตัวอักษรใน Sidebar */
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3, 
    section[data-testid="stSidebar"] label {{
        color: white !important;
    }}
    /* ปรับแต่ง MultiSelect ให้มองเห็นชัดแต่ยังคลิกได้ */
    div[data-baseweb="select"] {{
        background-color: white !important;
        border-radius: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Data Engine & Cleaning
@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files: return None, "No CSV found"
    target_file = next((f for f in csv_files if 'modern trade' in f.lower()), csv_files[0])
    
    for enc in ['utf-8', 'tis-620', 'cp874', 'latin1']:
        try:
            df = pd.read_csv(target_file, encoding=enc)
            df['SaleAmount (ExVat)'] = pd.to_numeric(df['SaleAmount (ExVat)'], errors='coerce').fillna(0)
            df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
            
            def clean_name(name):
                name = str(name)
                if 'แป้งนวล' in name: return 'แป้งนวล'
                if 'วาราบิโมจิ' in name: return 'แป้งวาราบิโมจิ'
                if 'ไดฟูกุ' in name: return 'แป้งไดฟูกุ'
                if 'คินาโกะ' in name or 'ถั่วเหลือง' in name: return 'คินาโกะ'
                return name
            df['PrName'] = df['PrName'].apply(clean_name)
            
            m_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            df['MonthName'] = df['Month'].map(m_map)
            df['MonthName'] = pd.Categorical(df['MonthName'], categories=m_map.values(), ordered=True)
            return df, target_file
        except: continue
    return None, "File Error"

df, source = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🟠 KOON Control")
    
    year_list = sorted(df['Year'].unique())
    selected_years = st.sidebar.multiselect("ปี (Year)", year_list, default=year_list)
    
    zone_list = sorted(df['Zone'].unique())
    selected_zones = st.sidebar.multiselect("พื้นที่ (Zone)", zone_list, default=zone_list)
    
    branch_list = sorted(df['BrName'].unique())
    selected_branches = st.sidebar.multiselect("ค้นหาสาขา (Branch)", branch_list)
    
    prod_list = sorted(df['PrName'].unique())
    selected_products = st.sidebar.multiselect("สินค้า (Product)", prod_list, default=prod_list)

    # Filter Logic
    mask = df['Year'].isin(selected_years) & df['Zone'].isin(selected_zones) & df['PrName'].isin(selected_products)
    if selected_branches: mask = mask & df['BrName'].isin(selected_branches)
    f_df = df[mask]

    # --- HEADER & KPI ---
    st.title("🟠 KOON Modern Trade Performance")
    
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    total_rev = f_df['SaleAmount (ExVat)'].sum()
    total_qty = f_df['Qty'].sum()
    k1.metric("ยอดขายรวม (ExVat)", f"฿{total_rev:,.0f}")
    k2.metric("จำนวนชิ้นรวม", f"{total_qty:,.0f}")
    k3.metric("เฉลี่ย/ชิ้น", f"฿{total_rev/total_qty if total_qty > 0 else 0:,.1f}")
    k4.metric("สาขาที่มีการขาย", f"{f_df[f_df['Qty'] > 0]['BrName'].nunique()}")

    # --- TOP 15 BRANCHES BY ZONE ---
    st.divider()
    st.subheader("🥇 อันดับสาขาที่มียอดขายสูงสุด (Top Branches by Zone)")
    br_sum = f_df.groupby(['BrName', 'Zone'])['SaleAmount (ExVat)'].sum().reset_index()
    br_sum = br_sum.sort_values('SaleAmount (ExVat)', ascending=True).tail(15)
    
    fig_br = px.bar(br_sum, x='SaleAmount (ExVat)', y='BrName', color='Zone',
                   color_discrete_map=ZONE_COLORS, orientation='h',
                   template="plotly_white")
    st.plotly_chart(fig_br, use_container_width=True)

    # --- HABIT & PRODUCT MIX ---
    st.divider()
    c_l, c_r = st.columns(2)
    with c_l:
        st.subheader("📈 Monthly Habits")
        h_df = f_df.groupby(['Year', 'MonthName'])['SaleAmount (ExVat)'].sum().reset_index()
        h_df['Year'] = h_df['Year'].astype(str)
        st.plotly_chart(px.line(h_df, x='MonthName', y='SaleAmount (ExVat)', color='Year', 
                               markers=True, line_shape="spline"), use_container_width=True)
    with c_r:
        st.subheader("🍕 Product Mix")
        p_df = f_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.pie(p_df, values='SaleAmount (ExVat)', names='PrName', hole=0.5, 
                               color_discrete_sequence=[KOON_ORANGE, "#003f5c", "#bc5090", "#CCCCCC"]), use_container_width=True)

    # --- MATRIX ---
    with st.expander("🔍 Detailed Sales Matrix"):
        pivot = f_df.pivot_table(index='BrName', columns='PrName', values='SaleAmount (ExVat)', aggfunc='sum', fill_value=0)
        st.dataframe(pivot.style.background_gradient(cmap='Oranges'), use_container_width=True)

    # --- FORECAST (BOTTOM) ---
    st.divider()
    st.subheader("🔮 Sales Forecast (3-Month)")
    if has_sklearn:
        ts = f_df.groupby(['Year', 'Month'])['SaleAmount (ExVat)'].sum().reset_index()
        if len(ts) >= 3:
            X = np.arange(len(ts)).reshape(-1, 1)
            y = ts['SaleAmount (ExVat)'].values
            model = LinearRegression().fit(X, y)
            preds = model.predict(np.arange(len(ts), len(ts)+3).reshape(-1, 1))
            
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=ts.index, y=y, name="Actual", line=dict(color=KOON_ORANGE, width=3)))
            fig_f.add_trace(go.Scatter(x=list(range(len(ts)-1, len(ts)+2)), y=[y[-1]]+list(preds), 
                                     name="Forecast", line=dict(color='#333333', width=4, dash='dot')))
            fig_f.update_layout(template="plotly_white")
            st.plotly_chart(fig_f, use_container_width=True)

else:
    st.error("Error loading data")
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

# 1. Page Configuration & Brand Styling
st.set_page_config(page_title="KOON Modern Trade Intelligence", page_icon="🟠", layout="wide")

# KOON Brand Color (สีส้มดอกไม้)
KOON_ORANGE = "#FF914D"
ZONE_COLORS = {"City": "#003f5c", "Residential": "#bc5090", "Provincial": "#ffa600"}

# Custom CSS เพื่อเปลี่ยนสี Sidebar เป็นสีส้มตามแบรนด์
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{
        background-color: {KOON_ORANGE};
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: white !important;
        color: {KOON_ORANGE} !important;
    }}
    </style>
    """, unsafe_allow_stdio=True)

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
            
            # --- ตัดคำฟุ่มเฟือยชื่อสินค้า ---
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
    # --- SIDEBAR FILTERS (Brand Orange) ---
    st.sidebar.title("🟠 KOON Filters")
    
    year_list = sorted(df['Year'].unique())
    selected_years = st.sidebar.multiselect("ปี (Year)", year_list, default=year_list)
    
    zone_list = sorted(df['Zone'].unique())
    selected_zones = st.sidebar.multiselect("พื้นที่ (Zone)", zone_list, default=zone_list)
    
    branch_list = sorted(df['BrName'].unique())
    selected_branches = st.sidebar.multiselect("ค้นหาชื่อสาขา (Branch)", branch_list)
    
    prod_list = sorted(df['PrName'].unique())
    selected_products = st.sidebar.multiselect("สินค้า (Product)", prod_list, default=prod_list)

    # Filter Logic
    mask = df['Year'].isin(selected_years) & df['Zone'].isin(selected_zones) & df['PrName'].isin(selected_products)
    if selected_branches: mask = mask & df['BrName'].isin(selected_branches)
    f_df = df[mask]

    # --- HEADER ---
    st.title("🟠 KOON Modern Trade Performance")
    st.write(f"วิเคราะห์ยอดขายเชิงลึกรายสาขาและพื้นที่ | แหล่งข้อมูล: `{source}`")

    # --- KPI CARDS ---
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    total_rev = f_df['SaleAmount (ExVat)'].sum()
    total_qty = f_df['Qty'].sum()
    k1.metric("ยอดขายรวม (ExVat)", f"฿{total_rev:,.0f}")
    k2.metric("จำนวนที่ขายได้", f"{total_qty:,.0f} ชิ้น")
    k3.metric("ยอดเฉลี่ย/ชิ้น", f"฿{total_rev/total_qty if total_qty > 0 else 0:,.2f}")
    k4.metric("สาขาที่มีการเคลื่อนไหว", f"{f_df[f_df['Qty'] > 0]['BrName'].nunique()} สาขา")

    # --- SECTION: BRANCH PERFORMANCE BY ZONE ---
    st.divider()
    st.subheader("🥇 อันดับสาขาที่มียอดขายสูงสุด (Top Branches by Revenue)")
    
    # ดึงข้อมูล 15 อันดับสาขาแรกเพื่อให้เห็นภาพรวมที่กว้างขึ้น
    br_sum = f_df.groupby(['BrName', 'Zone'])['SaleAmount (ExVat)'].sum().reset_index()
    br_sum = br_sum.sort_values('SaleAmount (ExVat)', ascending=True).tail(15)
    
    fig_br = px.bar(br_sum, x='SaleAmount (ExVat)', y='BrName', color='Zone',
                   title="Top 15 สาขาขายดี (ระบุตาม Zone)",
                   color_discrete_map=ZONE_COLORS, # ใช้สีประจำโซน
                   orientation='h',
                   labels={'SaleAmount (ExVat)': 'ยอดขาย (บาท)', 'BrName': 'ชื่อสาขา'},
                   template="plotly_white")
    
    fig_br.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_br, use_container_width=True)

    # --- SECTION: HABIT & PRODUCT MIX ---
    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("📈 Monthly Habits Comparison")
        h_df = f_df.groupby(['Year', 'MonthName'])['SaleAmount (ExVat)'].sum().reset_index()
        h_df['Year'] = h_df['Year'].astype(str)
        fig_line = px.line(h_df, x='MonthName', y='SaleAmount (ExVat)', color='Year',
                          markers=True, line_shape="spline", color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig_line, use_container_width=True)

    with col_r:
        st.subheader("🍕 Product Mix (Cleaned Names)")
        p_df = f_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.pie(p_df, values='SaleAmount (ExVat)', names='PrName', hole=0.5, 
                               color_discrete_sequence=[KOON_ORANGE, "#333333", "#CCCCCC", "#EEEEEE"]), use_container_width=True)

    # --- SECTION: FORECASTING ---
    st.divider()
    st.subheader("🔮 3-Month Sales Trend Forecast")
    if has_sklearn:
        ts = f_df.groupby(['Year', 'Month'])['SaleAmount (ExVat)'].sum().reset_index()
        if len(ts) >= 3:
            X = np.arange(len(ts)).reshape(-1, 1)
            y = ts['SaleAmount (ExVat)'].values
            model = LinearRegression().fit(X, y)
            future_X = np.arange(len(ts), len(ts)+3).reshape(-1, 1)
            preds = model.predict(future_X)
            
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=ts.index, y=y, name="ยอดขายจริง", line=dict(color=KOON_ORANGE, width=3)))
            fig_f.add_trace(go.Scatter(x=list(range(len(ts)-1, len(ts)+2)), y=[y[-1]]+list(preds), 
                                     name="ทำนายอนาคต", line=dict(color='#333333', width=4, dash='dot')))
            fig_f.update_layout(template="plotly_white", xaxis_title="Time (Months)")
            st.plotly_chart(fig_f, use_container_width=True)
        else:
            st.warning("ข้อมูลไม่เพียงพอสำหรับการพยากรณ์")

    # --- DETAILED MATRIX ---
    with st.expander("🔍 Detailed Sales Matrix"):
        pivot = f_df.pivot_table(index='BrName', columns='PrName', values='SaleAmount (ExVat)', aggfunc='sum', fill_value=0)
        st.dataframe(pivot.style.background_gradient(cmap='Oranges'), use_container_width=True)

else:
    st.error("ไม่สามารถโหลดข้อมูลได้")
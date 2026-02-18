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
st.set_page_config(page_title="Executive Intelligence Dashboard", page_icon="📈", layout="wide")

# คุมโทนสี Professional (High Contrast)
C_PALETTE = ["#003f5c", "#ffa600", "#bc5090", "#58508d", "#ff6361", "#00818a"]

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
            m_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            df['MonthName'] = df['Month'].map(m_map)
            df['MonthName'] = pd.Categorical(df['MonthName'], categories=m_map.values(), ordered=True)
            return df, target_file
        except: continue
    return None, "File Error"

df, source = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🎛️ ตัวกรองข้อมูล")
    
    year_list = sorted(df['Year'].unique())
    sel_years = st.sidebar.multiselect("เลือกปี (Year)", year_list, default=year_list)
    
    zone_list = sorted(df['Zone'].unique())
    sel_zones = st.sidebar.multiselect("พื้นที่ (Zone)", zone_list, default=zone_list)
    
    branch_list = sorted(df['BrName'].unique())
    sel_branches = st.sidebar.multiselect("เลือกสาขาเจาะจง (Branch)", branch_list)
    
    prod_list = sorted(df['PrName'].unique())
    sel_prods = st.sidebar.multiselect("สินค้า (Product)", prod_list, default=prod_list)

    # Filter Logic
    mask = df['Year'].isin(sel_years) & df['Zone'].isin(sel_zones) & df['PrName'].isin(sel_prods)
    if sel_branches: mask = mask & df['BrName'].isin(sel_branches)
    f_df = df[mask]

    # --- HEADER ---
    st.title("🏛️ Modern Trade Executive Intelligence")
    st.write(f"วิเคราะห์ข้อมูลพฤติกรรมผู้บริโภค | แหล่งข้อมูล: `{source}`")

    # --- SECTION 1: BASIC KPI CARDS (ยอดขายรวม/สาขา/ใดๆ) ---
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    total_rev = f_df['SaleAmount (ExVat)'].sum()
    total_qty = f_df['Qty'].sum()
    active_br = f_df[f_df['Qty'] > 0]['BrName'].nunique()
    
    k1.metric("ยอดขายรวม (ExVat)", f"฿{total_rev:,.0f}")
    k2.metric("จำนวนชิ้นรวม", f"{total_qty:,.0f} Pcs")
    k3.metric("ยอดซื้อเฉลี่ยต่อชิ้น", f"฿{total_rev/total_qty if total_qty > 0 else 0:,.2f}")
    k4.metric("จำนวนสาขาที่มีการขาย", f"{active_br} สาขา")

    # --- SECTION 2: GROWTH & HABIT ---
    st.divider()
    col_habit, col_growth = st.columns([2, 1])

    with col_habit:
        st.subheader("📈 พฤติกรรมการซื้อรายเดือนเปรียบเทียบรายปี")
        h_df = f_df.groupby(['Year', 'MonthName'])['SaleAmount (ExVat)'].sum().reset_index()
        h_df['Year'] = h_df['Year'].astype(str)
        fig_line = px.line(h_df, x='MonthName', y='SaleAmount (ExVat)', color='Year',
                          markers=True, line_shape="spline", color_discrete_sequence=C_PALETTE)
        fig_line.update_layout(template="plotly_white", xaxis_title="")
        st.plotly_chart(fig_line, use_container_width=True)

    with col_growth:
        st.subheader("🚀 สาขาที่เติบโตสูงสุด (YoY)")
        if len(year_list) >= 2:
            cy, ly = max(year_list), max(year_list)-1
            g_df = df[df['Year'].isin([ly, cy])].groupby(['Year', 'BrName'])['SaleAmount (ExVat)'].sum().unstack(0)
            g_df.columns = ['LY', 'CY']
            g_df['Pct'] = (g_df['CY'] - g_df['LY']) / g_df['LY'] * 100
            top_g = g_df.replace([np.inf, -np.inf], np.nan).dropna().sort_values('Pct', ascending=False).head(3)
            for br, row in top_g.iterrows():
                st.write(f"**{br}**")
                st.caption(f"ยอดขาย: ฿{row['CY']:,.0f} | เติบโต: {row['Pct']:.1f}%")
        else:
            st.info("ต้องการข้อมูล 2 ปีเพื่อดูการเติบโต")

    # --- SECTION 3: PRODUCT MIX & BRANCH TOP 10 ---
    st.divider()
    c_pie, c_bar = st.columns(2)
    with c_pie:
        st.subheader("🍩 Product Contribution")
        p_df = f_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.pie(p_df, values='SaleAmount (ExVat)', names='PrName', hole=0.5, color_discrete_sequence=C_PALETTE), use_container_width=True)
    with c_bar:
        st.subheader("🥇 Top 10 Branches")
        b_df = f_df.groupby('BrName')['SaleAmount (ExVat)'].sum().reset_index().sort_values('SaleAmount (ExVat)').tail(10)
        st.plotly_chart(px.bar(b_df, x='SaleAmount (ExVat)', y='BrName', orientation='h', color='SaleAmount (ExVat)', color_continuous_scale="YlGnBu"), use_container_width=True)

    # --- SECTION 4: DETAILED MATRIX ---
    st.subheader("📋 รายละเอียดข้อมูลรายสาขาและสินค้า")
    pivot = f_df.pivot_table(index='BrName', columns='PrName', values='SaleAmount (ExVat)', aggfunc='sum', fill_value=0)
    st.dataframe(pivot.style.background_gradient(cmap='YlGnBu'), use_container_width=True)

    # --- SECTION 5: FORECASTING (BOTTOM) ---
    st.divider()
    st.subheader("🔮 การทำนายแนวโน้มยอดขาย (Sales Forecast)")
    if has_sklearn:
        # เตรียมข้อมูล Time Series (เฉลี่ยทุกโซนและสินค้าที่เลือก)
        ts = f_df.groupby(['Year', 'Month'])['SaleAmount (ExVat)'].sum().reset_index()
        if len(ts) > 2:
            X = np.arange(len(ts)).reshape(-1, 1)
            y = ts['SaleAmount (ExVat)'].values
            model = LinearRegression().fit(X, y)
            
            future_X = np.arange(len(ts), len(ts)+3).reshape(-1, 1)
            preds = model.predict(future_X)
            
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=ts.index, y=y, name="Actual", line=dict(color='#003f5c', width=3)))
            fig_f.add_trace(go.Scatter(x=list(range(len(ts)-1, len(ts)+2)), y=[y[-1]]+list(preds), 
                                     name="Forecast", line=dict(color='#ff6361', width=4, dash='dot')))
            fig_f.update_layout(template="plotly_white", xaxis_title="Timeline (Months)", yaxis_title="Sales (THB)")
            st.plotly_chart(fig_f, use_container_width=True)
            st.caption("พยากรณ์ล่วงหน้า 3 เดือนโดยอิงจากแนวโน้มข้อมูลที่เลือก")
        else:
            st.warning("ข้อมูลไม่เพียงพอสำหรับการทำนาย (ต้องการอย่างน้อย 3 เดือน)")
    else:
        st.info("ติดตั้ง scikit-learn เพื่อเปิดระบบทำนาย")

else:
    st.error("ไม่สามารถโหลดข้อมูลได้")
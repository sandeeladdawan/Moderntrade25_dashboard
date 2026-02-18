import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# 1. Page Configuration
st.set_page_config(page_title="Strategic Growth & Forecast Dashboard", page_icon="🚀", layout="wide")

# Professional Color Palette
C_PALETTE = ["#003f5c", "#ffa600", "#bc5090", "#58508d", "#ff6361", "#00818a"]

@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files: return None, "No CSV found"
    target_file = next((f for f in csv_files if 'modern trade' in f.lower()), csv_files[0])
    
    for enc in ['utf-8', 'tis-620', 'cp874']:
        try:
            df = pd.read_csv(target_file, encoding=enc)
            df['SaleAmount (ExVat)'] = pd.to_numeric(df['SaleAmount (ExVat)'], errors='coerce').fillna(0)
            df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
            month_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 
                         7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            df['MonthName'] = df['Month'].map(month_map)
            df['MonthName'] = pd.Categorical(df['MonthName'], categories=month_map.values(), ordered=True)
            return df, target_file
        except: continue
    return None, "File Error"

df, source = load_data()

if df is not None:
    # --- Sidebar ---
    st.sidebar.title("🚀 Advanced Analytics")
    year_list = sorted(df['Year'].unique())
    selected_years = st.sidebar.multiselect("เลือกปีที่ต้องการดู", year_list, default=year_list)
    prod_list = sorted(df['PrName'].unique())
    selected_products = st.sidebar.multiselect("เลือกสินค้า", prod_list, default=prod_list)

    mask = df['Year'].isin(selected_years) & df['PrName'].isin(selected_products)
    f_df = df[mask]

    st.title("🚀 Strategic Growth & Forecasting Dashboard")
    st.markdown(f"**Data Intelligence** | Source: `{source}`")

    # --- Section 1: Growth Analysis ---
    st.divider()
    st.subheader("📈 สาขาที่เติบโตแรงที่สุด (Year-on-Year Growth)")
    
    if len(year_list) >= 2:
        current_year = max(year_list)
        last_year = current_year - 1
        
        growth_df = df[df['Year'].isin([last_year, current_year])].groupby(['Year', 'BrName'])['SaleAmount (ExVat)'].sum().unstack(level=0)
        growth_df.columns = ['LastYear', 'CurrentYear']
        growth_df['Growth_Value'] = growth_df['CurrentYear'] - growth_df['LastYear']
        growth_df['Growth_Pct'] = (growth_df['Growth_Value'] / growth_df['LastYear']) * 100
        
        # กรองเฉพาะสาขาที่มีขายทั้งสองปีและตัดค่า Infinity
        top_growth = growth_df.replace([np.inf, -np.inf], np.nan).dropna().sort_values('Growth_Pct', ascending=False).head(5)
        
        cols = st.columns(len(top_growth))
        for i, (branch, row) in enumerate(top_growth.iterrows()):
            cols[i].metric(branch, f"฿{row['CurrentYear']:,.0f}", f"{row['Growth_Pct']:.1f}% Growth")
    else:
        st.info("ต้องการข้อมูลอย่างน้อย 2 ปีในการวิเคราะห์การเติบโต")

    # --- Section 2: Sales Forecasting ---
    st.divider()
    st.subheader("🔮 การพยากรณ์ยอดขาย (3-Month Sales Forecast)")
    
    # เตรียมข้อมูล Time Series
    ts_df = df.groupby(['Year', 'Month'])['SaleAmount (ExVat)'].sum().reset_index()
    ts_df['TimeIndex'] = np.arange(len(ts_df))
    
    # สร้าง Model Linear Regression
    X = ts_df[['TimeIndex']].values
    y = ts_df['SaleAmount (ExVat)'].values
    model = LinearRegression().fit(X, y)
    
    # พยากรณ์ไปข้างหน้า 3 เดือน
    future_index = np.array([[len(ts_df)], [len(ts_df)+1], [len(ts_df)+2]])
    future_pred = model.predict(future_index)
    
    # สร้างกราฟพยากรณ์
    fig_forecast = go.Figure()
    # ข้อมูลจริง
    fig_forecast.add_trace(go.Scatter(x=ts_df.index, y=y, name='Actual Sales', line=dict(color='#003f5c', width=3)))
    # เส้น Trend Line
    fig_forecast.add_trace(go.Scatter(x=ts_df.index, y=model.predict(X), name='Trend Line', line=dict(color='#ffa600', dash='dash')))
    # ส่วนพยากรณ์
    fig_forecast.add_trace(go.Scatter(x=[len(ts_df)-1, len(ts_df), len(ts_df)+1, len(ts_df)+2], 
                                     y=[y[-1], future_pred[0], future_pred[1], future_pred[2]], 
                                     name='Forecast', line=dict(color='#ff6361', width=4)))
    
    fig_forecast.update_layout(template="plotly_white", xaxis_title="Timeline (Months)", yaxis_title="Sales Amount")
    st.plotly_chart(fig_forecast, use_container_width=True)

    # --- Section 3: Professional Visuals ---
    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🍩 Product Contribution")
        p_mix = f_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.pie(p_mix, values='SaleAmount (ExVat)', names='PrName', hole=0.5, color_discrete_sequence=C_PALETTE), use_container_width=True)
        
    with c2:
        st.subheader("📍 ยอดขายรายโซน")
        z_mix = f_df.groupby('Zone')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.bar(z_mix, x='Zone', y='SaleAmount (ExVat)', color='Zone', color_discrete_sequence=C_PALETTE), use_container_width=True)

    # Detailed Matrix with Heatmap
    st.subheader("📋 Detailed Performance Matrix")
    pivot = f_df.pivot_table(index='BrName', columns='PrName', values='SaleAmount (ExVat)', aggfunc='sum', fill_value=0)
    st.dataframe(pivot.style.background_gradient(cmap='YlGnBu'), use_container_width=True)

else:
    st.error("กรุณาตรวจสอบไฟล์ข้อมูลบน GitHub")
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ตรวจสอบว่ามี sklearn ไหม ถ้าไม่มีให้ข้ามส่วน Forecast เพื่อไม่ให้ App พัง
try:
    from sklearn.linear_model import LinearRegression
    has_sklearn = True
except ImportError:
    has_sklearn = False

st.set_page_config(page_title="Strategic Growth Dashboard", page_icon="🚀", layout="wide")

# คุมโทนสี Professional
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
            # จัดการวันที่
            m_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            df['MonthName'] = df['Month'].map(m_map)
            df['MonthName'] = pd.Categorical(df['MonthName'], categories=m_map.values(), ordered=True)
            return df, target_file
        except: continue
    return None, "File Error"

df, source = load_data()

if df is not None:
    st.title("🚀 Strategic Growth & Forecasting Intelligence")
    
    # --- Side Bar ---
    st.sidebar.header("Filter Options")
    year_list = sorted(df['Year'].unique())
    sel_years = st.sidebar.multiselect("Select Years", year_list, default=year_list)
    prod_list = sorted(df['PrName'].unique())
    sel_prods = st.sidebar.multiselect("Select Products", prod_list, default=prod_list)
    
    f_df = df[df['Year'].isin(sel_years) & df['PrName'].isin(sel_prods)]

    # --- Section 1: Top Growth Branches ---
    st.subheader("📈 สาขาที่เติบโตแรงที่สุด (Top Growth)")
    if len(year_list) >= 2:
        curr_y = max(year_list)
        last_y = curr_y - 1
        g_df = df[df['Year'].isin([last_y, curr_y])].groupby(['Year', 'BrName'])['SaleAmount (ExVat)'].sum().unstack(level=0)
        g_df.columns = ['LastYear', 'CurrYear']
        g_df['Pct'] = ((g_df['CurrYear'] - g_df['LastYear']) / g_df['LastYear'] * 100)
        top_g = g_df.replace([np.inf, -np.inf], np.nan).dropna().sort_values('Pct', ascending=False).head(4)
        
        m1, m2, m3, m4 = st.columns(4)
        metrics = [m1, m2, m3, m4]
        for i, (branch, row) in enumerate(top_g.iterrows()):
            if i < 4:
                metrics[i].metric(branch, f"฿{row['CurrYear']:,.0f}", f"{row['Pct']:.1f}%")
    else:
        st.info("ต้องการข้อมูลอย่างน้อย 2 ปีเพื่อวิเคราะห์การเติบโต")

    st.divider()

    # --- Section 2: Forecasting ---
    st.subheader("🔮 Sales Trend & 3-Month Forecast")
    if has_sklearn:
        ts = df.groupby(['Year', 'Month'])['SaleAmount (ExVat)'].sum().reset_index()
        X = np.arange(len(ts)).reshape(-1, 1)
        y = ts['SaleAmount (ExVat)'].values
        model = LinearRegression().fit(X, y)
        
        future_X = np.arange(len(ts), len(ts)+3).reshape(-1, 1)
        preds = model.predict(future_X)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts.index, y=y, name="Actual Sales", line=dict(color='#003f5c', width=3)))
        fig.add_trace(go.Scatter(x=list(range(len(ts)-1, len(ts)+2)), y=[y[-1]]+list(preds), 
                                 name="Forecast", line=dict(color='#ff6361', width=4, dash='dot')))
        fig.update_layout(template="plotly_white", xaxis_title="Timeline (Months)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("กรุณาเพิ่ม scikit-learn ใน requirements.txt เพื่อเปิดใช้งานระบบทำนายยอดขาย")

    # --- Section 3: Professional Visuals ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🍕 Product Contribution")
        st.plotly_chart(px.pie(f_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index(), 
                               values='SaleAmount (ExVat)', names='PrName', hole=0.5, 
                               color_discrete_sequence=C_PALETTE), use_container_width=True)
    with c2:
        st.subheader("📍 Monthly Habit Comparison")
        h_df = f_df.groupby(['Year', 'MonthName'])['SaleAmount (ExVat)'].sum().reset_index()
        h_df['Year'] = h_df['Year'].astype(str)
        st.plotly_chart(px.line(h_df, x='MonthName', y='SaleAmount (ExVat)', color='Year', markers=True,
                                 color_discrete_sequence=C_PALETTE, template="plotly_white"), use_container_width=True)

    st.subheader("📋 Detailed Performance Matrix")
    pivot = f_df.pivot_table(index='BrName', columns='PrName', values='SaleAmount (ExVat)', aggfunc='sum', fill_value=0)
    try:
        st.dataframe(pivot.style.background_gradient(cmap='YlGnBu'), use_container_width=True)
    except:
        st.dataframe(pivot, use_container_width=True)
else:
    st.error("ไม่สามารถโหลดข้อมูลได้")
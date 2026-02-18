import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. หน้าจอและการตั้งค่าเบื้องต้น
st.set_page_config(page_title="Modern Trade Insight Dashboard", page_icon="📈", layout="wide")

# คลุมโทนสีหลัก (Professional Palette)
COLOR_THEME = px.colors.qualitative.Prism # โทนสีสวยสะอาดตาสำหรับข้อมูลหมวดหมู่
SEQUENTIAL_THEME = px.colors.sequential.Tealgrn # โทนสีไล่เฉดเขียว-น้ำเงินเข้ม

# 2. ฟังก์ชันโหลดข้อมูล (คงเดิมแต่ปรับให้เสถียรขึ้น)
@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files: return None, "ไม่พบไฟล์ .csv"
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
    return None, "Error Reading File"

df, source_info = load_data()

if df is not None:
    # --- Sidebar Filter ---
    st.sidebar.markdown("### 🔍 ค้นหาและกรองข้อมูล")
    
    year_list = sorted(df['Year'].unique().tolist())
    selected_years = st.sidebar.multiselect("เลือกปีที่ต้องการเปรียบเทียบ", year_list, default=year_list)
    
    zone_list = sorted([x for x in df['Zone'].unique() if pd.notna(x)])
    selected_zones = st.sidebar.multiselect("พื้นที่ (Zone)", zone_list, default=zone_list)
    
    branch_list = sorted([x for x in df['BrName'].unique() if pd.notna(x)])
    selected_branches = st.sidebar.multiselect("สาขาเฉพาะที่ (Branch)", branch_list)
    
    prod_list = sorted([x for x in df['PrName'].unique() if pd.notna(x)])
    selected_products = st.sidebar.multiselect("เลือกสินค้า", prod_list, default=prod_list)

    # Filter Logic
    mask = df['Year'].isin(selected_years) & df['Zone'].isin(selected_zones) & df['PrName'].isin(selected_products)
    if selected_branches:
        mask = mask & df['BrName'].isin(selected_branches)
    
    f_df = df[mask]

    # --- Header ---
    st.title("🏛️ Modern Trade Executive Insight")
    st.markdown(f"**Data Status:** ข้อมูลผ่านการทำความสะอาดแล้วจากไฟล์ `{source_info}`")
    
    # --- KPI Section (ปรับ Design) ---
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Revenue", f"฿{f_df['SaleAmount (ExVat)'].sum():,.0f}")
    with kpi2:
        st.metric("Total Quantity", f"{f_df['Qty'].sum():,.0f} Pcs")
    with kpi3:
        st.metric("Avg. Price/Unit", f"฿{f_df['SaleAmount (ExVat)'].sum()/f_df['Qty'].sum() if f_df['Qty'].sum()>0 else 0:,.2f}")
    with kpi4:
        st.metric("Active Branches", f"{f_df[f_df['Qty']>0]['BrName'].nunique()}")

    # --- Main Visualization ---
    st.markdown("### 📈 พฤติกรรมการซื้อรายเดือนเปรียบเทียบแต่ละปี (Monthly Habits)")
    
    habit_df = f_df.groupby(['Year', 'MonthName'])['SaleAmount (ExVat)'].sum().reset_index()
    habit_df['Year'] = habit_df['Year'].astype(str)
    
    fig_line = px.line(
        habit_df, x='MonthName', y='SaleAmount (ExVat)', color='Year',
        markers=True, line_shape="spline", # เส้นโค้งมนดูพรีเมียม
        color_discrete_sequence=COLOR_THEME,
        template="plotly_white"
    )
    fig_line.update_layout(
        hovermode="x unified",
        xaxis_title="", yaxis_title="ยอดขาย (บาท)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Second Row Visuals ---
    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("### 🥧 สัดส่วนสินค้าตามยอดขาย")
        prod_sum = f_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        fig_pie = px.pie(
            prod_sum, values='SaleAmount (ExVat)', names='PrName',
            hole=0.5, color_discrete_sequence=px.colors.sequential.Teal_r
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.markdown("### 🏆 10 อันดับสาขาที่ทำยอดสูงสุด")
        br_sum = f_df.groupby('BrName')['SaleAmount (ExVat)'].sum().reset_index().sort_values('SaleAmount (ExVat)', ascending=True).tail(10)
        
        # ใช้สีไล่เฉด (Gradient) ตามยอดขาย
        fig_bar = px.bar(
            br_sum, x='SaleAmount (ExVat)', y='BrName',
            orientation='h',
            color='SaleAmount (ExVat)', # ไล่สีตามยอดขาย
            color_continuous_scale='Tealgrn',
            template="plotly_white"
        )
        fig_bar.update_layout(coloraxis_showscale=False, showlegend=False, yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Data Detail Section ---
    with st.expander("📄 ดูตารางข้อมูลสรุปรายสาขา"):
        pivot_br = f_df.pivot_table(
            index='BrName', 
            columns='PrName', 
            values='SaleAmount (ExVat)', 
            aggfunc='sum', 
            fill_value=0
        )
        st.dataframe(pivot_br.style.background_gradient(cmap='Greens'), use_container_width=True)

else:
    st.error("ไม่สามารถแสดง Dashboard ได้ กรุณาตรวจสอบไฟล์ข้อมูล")
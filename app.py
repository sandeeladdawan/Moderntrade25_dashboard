import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Executive Dashboard", layout="wide")

@st.cache_data
def load_data():
    # แก้ชื่อไฟล์ให้ตรงกับที่คุณอัพโหลดขึ้น GitHub
    file_name = 'modern trade analysis 2.csv'
    df = pd.read_csv(file_name)
    # แปลงรูปแบบวันที่เล็กน้อย
    df['Period'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')
    return df

try:
    df = load_data()

    # --- Sidebar ---
    st.sidebar.header("เลือกข้อมูลที่ต้องการดู")
    selected_zone = st.sidebar.multiselect("เลือก Zone", options=df['Zone'].unique(), default=df['Zone'].unique())
    selected_product = st.sidebar.multiselect("เลือกสินค้า", options=df['PrName'].unique(), default=df['PrName'].unique())

    # กรองข้อมูล
    mask = (df['Zone'].isin(selected_zone)) & (df['PrName'].isin(selected_product))
    df_filtered = df[mask]

    # --- Dashboard UI ---
    st.title("📊 Moderntrade25_dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ยอดขายรวม (ExVat)", f"{df_filtered['SaleAmount (ExVat)'].sum():,.2f} THB")
    col2.metric("จำนวนที่ขายได้ (Qty)", f"{df_filtered['Qty'].sum():,.0f} Pcs")
    col3.metric("จำนวนสาขาที่มีการขาย", len(df_filtered[df_filtered['Qty']>0]['BrName'].unique()))

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ยอดขายแบ่งตามสินค้า")
        fig1 = px.pie(df_filtered, values='SaleAmount (ExVat)', names='PrName', hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
    
    with c2:
        st.subheader("แนวโน้มยอดขายรายเดือน")
        trend_df = df_filtered.groupby('Period')['SaleAmount (ExVat)'].sum().reset_index()
        fig2 = px.line(trend_df, x='Period', y='SaleAmount (ExVat)', markers=True)
        st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: ตรวจสอบว่าคุณได้อัพโหลดไฟล์ CSV ชื่อ 'modern trade analysis 2.xlsx - sum by area.csv' ขึ้น GitHub หรือยัง?")
    st.info("รายละเอียด Error: " + str(e))
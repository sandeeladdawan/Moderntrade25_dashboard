import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Executive Dashboard", page_icon="📊", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูลที่รองรับภาษาไทย (แก้ปัญหา Encoding)
@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        return None, "ไม่พบไฟล์ .csv ในระบบ"
    
    target_file = next((f for f in csv_files if 'modern trade' in f.lower()), csv_files[0])
    
    # พยายามอ่านไฟล์ด้วยหลายรูปแบบ (Encodings) เพื่อกันปัญหาภาษาไทยตัวต่างดาว
    encodings = ['utf-8', 'tis-620', 'cp874', 'latin1']
    df = None
    error_msg = ""
    
    for enc in encodings:
        try:
            df = pd.read_csv(target_file, encoding=enc)
            break # ถ้าอ่านผ่านให้หยุดลอง
        except Exception as e:
            error_msg = str(e)
            continue
            
    if df is not None:
        # ตรวจสอบและแปลงวันที่
        if 'Year' in df.columns and 'Month' in df.columns:
            df['Period'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')
        return df, target_file
    else:
        return None, f"ไม่สามารถอ่านไฟล์ได้ (ปัญหาเรื่องตัวอักษร): {error_msg}"

# 3. เริ่มรันหน้า Dashboard
df, source_info = load_data()

if df is None:
    st.error(f"❌ {source_info}")
    st.info("💡 วิธีแก้: ลองเปิดไฟล์ CSV ใน Excel แล้วเลือก 'Save As' เป็น 'CSV UTF-8 (Comma delimited)' แล้วอัพโหลดใหม่")
else:
    # --- ส่วนแสดงผล Dashboard (เหมือนเดิม) ---
    st.title("📊 Modern Trade Sales Analysis")
    st.caption(f"กำลังใช้ไฟล์: {source_info}")
    st.divider()

    # Sidebar
    st.sidebar.header("🎛️ ตัวกรองข้อมูล")
    selected_zones = st.sidebar.multiselect("เลือกพื้นที่ (Zone)", df['Zone'].unique(), default=df['Zone'].unique())
    selected_products = st.sidebar.multiselect("เลือกสินค้า", df['PrName'].unique(), default=df['PrName'].unique())
    
    filtered_df = df[(df['Zone'].isin(selected_zones)) & (df['PrName'].isin(selected_products))]

    # KPI Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("ยอดขายรวม", f"฿{filtered_df['SaleAmount (ExVat)'].sum():,.2f}")
    c2.metric("จำนวนที่ขายได้", f"{filtered_df['Qty'].sum():,.0f} ชิ้น")
    c3.metric("สาขาที่มีการเคลื่อนไหว", len(filtered_df[filtered_df['Qty']>0]['BrName'].unique()))

    # Graphs
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("ยอดขายรายเดือน")
        trend = filtered_df.groupby('Period')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Period', y='SaleAmount (ExVat)'), use_container_width=True)
    with g2:
        st.subheader("สัดส่วนยอดขาย")
        pie_data = filtered_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.pie(pie_data, values='SaleAmount (ExVat)', names='PrName'), use_container_width=True)

    st.subheader("🏆 สาขาที่ยอดขายสูงสุด")
    st.dataframe(filtered_df.groupby(['BrName', 'Zone'])['SaleAmount (ExVat)'].sum().reset_index().sort_values('SaleAmount (ExVat)', ascending=False).head(10), use_container_width=True)


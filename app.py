import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Executive Dashboard", page_icon="📊", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูลที่รองรับภาษาไทยและจัดการข้อมูลเสีย
@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        return None, "ไม่พบไฟล์ .csv ในระบบ"
    
    target_file = next((f for f in csv_files if 'modern trade' in f.lower()), csv_files[0])
    
    encodings = ['utf-8', 'tis-620', 'cp874', 'latin1']
    df = None
    
    for enc in encodings:
        try:
            df = pd.read_csv(target_file, encoding=enc)
            break
        except:
            continue
            
    if df is not None:
        # --- จุดแก้ไข: ล้างข้อมูลให้เป็นตัวเลขที่คำนวณได้ ---
        # แปลง SaleAmount และ Qty ให้เป็นตัวเลข (ถ้าไม่ใช่ตัวเลขจะกลายเป็น NaN แล้วแทนที่ด้วย 0)
        df['SaleAmount (ExVat)'] = pd.to_numeric(df['SaleAmount (ExVat)'], errors='coerce').fillna(0)
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        
        # ตรวจสอบและแปลงวันที่
        if 'Year' in df.columns and 'Month' in df.columns:
            df['Period'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')
        return df, target_file
    else:
        return None, "ไม่สามารถอ่านไฟล์ได้"

# 3. เริ่มรันหน้า Dashboard
df, source_info = load_data()

if df is None:
    st.error(f"❌ {source_info}")
else:
    st.title("📊 Modern Trade Sales Analysis")
    st.caption(f"กำลังใช้ไฟล์: {source_info}")
    st.divider()

    # Sidebar
    st.sidebar.header("🎛️ ตัวกรองข้อมูล")
    # ป้องกันค่าว่างใน Filter
    zone_options = [x for x in df['Zone'].unique() if pd.notna(x)]
    prod_options = [x for x in df['PrName'].unique() if pd.notna(x)]
    
    selected_zones = st.sidebar.multiselect("เลือกพื้นที่ (Zone)", zone_options, default=zone_options)
    selected_products = st.sidebar.multiselect("เลือกสินค้า", prod_options, default=prod_options)
    
    filtered_df = df[(df['Zone'].isin(selected_zones)) & (df['PrName'].isin(selected_products))]

    # KPI Cards (ใช้การคำนวณที่ปลอดภัยขึ้น)
    total_sales = float(filtered_df['SaleAmount (ExVat)'].sum())
    total_qty = float(filtered_df['Qty'].sum())
    
    c1, c2, c3 = st.columns(3)
    c1.metric("ยอดขายรวม", f"฿{total_sales:,.2f}")
    c2.metric("จำนวนที่ขายได้", f"{total_qty:,.0f} ชิ้น")
    
    # นับสาขาเฉพาะที่มีชื่อสาขาจริงๆ
    active_br = filtered_df[filtered_df['Qty'] > 0]['BrName'].nunique()
    c3.metric("สาขาที่มีการเคลื่อนไหว", f"{active_br} สาขา")

    # Graphs
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📈 แนวโน้มยอดขายรายเดือน")
        trend = filtered_df.groupby('Period')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Period', y='SaleAmount (ExVat)', markers=True), use_container_width=True)
    with g2:
        st.subheader("🍕 สัดส่วนยอดขายตามสินค้า")
        pie_data = filtered_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        st.plotly_chart(px.pie(pie_data, values='SaleAmount (ExVat)', names='PrName'), use_container_width=True)

    st.subheader("🏆 สาขาที่ยอดขายสูงสุด 10 อันดับ")
    top_branches = filtered_df.groupby(['BrName', 'Zone'])['SaleAmount (ExVat)'].sum().reset_index().sort_values('SaleAmount (ExVat)', ascending=False).head(10)
    st.dataframe(top_branches, use_container_width=True, hide_index=True)
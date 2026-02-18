import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. ตั้งค่าหน้าเว็บให้สวยงาม
st.set_page_config(
    page_title="Modern Trade Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. ฟังก์ชันโหลดข้อมูล (ปรับปรุงใหม่เพื่อป้องกันปัญหาชื่อไฟล์ไม่ตรง)
@st.cache_data
def load_data():
    # ค้นหาไฟล์ .csv ทั้งหมดในโฟลเดอร์
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        return None, "ไม่พบไฟล์ .csv ใน Repository ของคุณ"
    
    # พยายามเลือกไฟล์ที่มีคำว่า 'modern trade' ก่อน ถ้าไม่มีก็เอาไฟล์แรกที่เจอ
    target_file = None
    for f in csv_files:
        if 'modern trade' in f.lower():
            target_file = f
            break
    if not target_file:
        target_file = csv_files[0]
        
    try:
        df = pd.read_csv(target_file)
        # ตรวจสอบชื่อคอลัมน์และแปลงวันที่
        if 'Year' in df.columns and 'Month' in df.columns:
            df['Period'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')
        return df, target_file
    except Exception as e:
        return None, str(e)

# 3. เริ่มรัน Dashboard
df, source_info = load_data()

if df is None:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {source_info}")
    st.info("คำแนะนำ: ตรวจสอบว่าคุณได้อัพโหลดไฟล์ .csv ขึ้น GitHub แล้วจริงๆ")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("🎛️ ตัวกรองข้อมูล")
    
    # เลือกโซน
    zones = df['Zone'].unique().tolist()
    selected_zones = st.sidebar.multiselect("เลือกพื้นที่ (Zone)", zones, default=zones)
    
    # เลือกสินค้า
    products = df['PrName'].unique().tolist()
    selected_products = st.sidebar.multiselect("เลือกสินค้า (Product)", products, default=products)
    
    # กรองข้อมูลตามที่เลือก
    filtered_df = df[
        (df['Zone'].isin(selected_zones)) & 
        (df['PrName'].isin(selected_products))
    ]

    # --- Header ---
    st.title("📊 Modern Trade Sales Analysis")
    st.markdown(f"**แหล่งข้อมูล:** `{source_info}`")
    st.divider()

    # --- ส่วนที่ 1: KPI Cards (ตัวเลขสรุป) ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = filtered_df['SaleAmount (ExVat)'].sum()
        st.metric("ยอดขายรวม (ExVat)", f"฿{total_sales:,.2f}")
    
    with col2:
        total_qty = filtered_df['Qty'].sum()
        st.metric("จำนวนชิ้นที่ขายได้", f"{total_qty:,.0f} ชิ้น")
        
    with col3:
        avg_sale = total_sales / total_qty if total_qty > 0 else 0
        st.metric("ยอดซื้อเฉลี่ยต่อชิ้น", f"฿{avg_sale:,.2f}")
        
    with col4:
        active_branches = len(filtered_df[filtered_df['Qty'] > 0]['BrName'].unique())
        st.metric("จำนวนสาขาที่มีการขาย", f"{active_branches} สาขา")

    st.divider()

    # --- ส่วนที่ 2: กราฟวิเคราะห์ ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 แนวโน้มยอดขายรายเดือน (Sales Trend)")
        trend_data = filtered_df.groupby('Period')['SaleAmount (ExVat)'].sum().reset_index()
        fig_trend = px.line(trend_data, x='Period', y='SaleAmount (ExVat)', markers=True)
        fig_trend.update_layout(xaxis_title="เดือน/ปี", yaxis_title="ยอดขาย (บาท)")
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("🍕 สัดส่วนยอดขายตามสินค้า (Product Mix)")
        prod_data = filtered_df.groupby('PrName')['SaleAmount (ExVat)'].sum().reset_index()
        fig_pie = px.pie(prod_data, values='SaleAmount (ExVat)', names='PrName', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- ส่วนที่ 3: วิเคราะห์รายสาขาและคำแนะนำ ---
    c3, c4 = st.columns([2, 1])

    with c3:
        st.subheader("🏆 สาขาที่มียอดขายสูงสุด 10 อันดับ")
        branch_sales = filtered_df.groupby(['BrName', 'Zone'])['SaleAmount (ExVat)'].sum().reset_index()
        top_10_branches = branch_sales.sort_values('SaleAmount (ExVat)', ascending=False).head(10)
        st.dataframe(top_10_branches, use_container_width=True, hide_index=True)

    with c4:
        st.subheader("💡 กลยุทธ์แนะนำ")
        st.success("""
        **1. เร่งยอดกลุ่มสินค้าเสริม:** แป้งนวลและผงคินาโกะ มียอดขายน้อยเมื่อเทียบกับแป้งหลัก ควรจัดเซ็ต Bundle
        
        **2. เจาะกลุ่ม Residential:**
        จากข้อมูล โซนที่พักอาศัยคือหัวใจหลัก ควรเพิ่มสต็อกแป้ง 800G ในสาขาเหล่านี้
        
        **3. จัดการสาขาที่ยอดเป็น 0:**
        ตรวจสอบสาขาที่ไม่มีการเคลื่อนไหว เพื่อประเมินการวางสินค้าใหม่
        """)

    # ส่วนท้าย (Footer)
    st.divider()
    st.caption("Dashboard นี้จัดทำขึ้นเพื่อการวิเคราะห์พฤติกรรมผู้บริโภคใน Modern Trade")
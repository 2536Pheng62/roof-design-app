import streamlit as st # type: ignore
import pandas as pd # type: ignore
import os
from purlin_design import PurlinDesign
from data_utils import load_data, SteelMaterial
from report_generator import PurlinReportGenerator
from theme_manager import use_theme
from section_3d import create_c_channel_3d, create_purlin_system_3d

st.set_page_config(page_title="ออกแบบแปเหล็ก", layout="wide")
use_theme()

st.title("🏗️ โมดูลออกแบบแปเหล็กขึ้นรูปเย็น")

# --- 1. Project Information ---
with st.expander("📝 Project Information", expanded=True):
    c1, c2, c3 = st.columns(3)
    project_name = c1.text_input("Project Name", "Warehouse A")
    owner = c2.text_input("Owner", "Customer X")
    engineer = c3.text_input("Engineer", "Eng. Sarayut")

# --- 2. Load Data ---
@st.cache_data
def get_data():
    return load_data("Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv")

df = get_data()

if df.empty:
    st.error("Failed to load section data.")
    st.stop()

# Debug: Check columns to ensure 'Area' exists
# st.write("Debug Columns:", df.columns.tolist()) 

# --- 3. Inputs ---
col_in1, col_in2 = st.columns([1, 2])

# Initialize session state for live calculation
if 'auto_calculate' not in st.session_state:
    st.session_state.auto_calculate = False

with col_in1:
    st.header("กำหนดพารามิเตอร์")
    
    # Geometry
    st.subheader("1. มิติเรขาคณิต")
    span = st.number_input("ช่วงพาดแป (เมตร)", value=6.0, step=0.5, key="span")
    spacing = st.number_input("ระยะแป (เมตร)", value=1.5, step=0.1, key="spacing")
    slope = st.number_input("ความชันหลังคา (องศา)", value=5.0, step=0.5, key="slope")
    
    # Loads
    st.subheader("2. น้ำหนักบรรทุก")
    dl = st.number_input("น้ำหนักบรรทุกคงที่ DL (กก./ตร.ม.)", value=20.0, step=5.0, key="dl")
    ll = st.number_input("น้ำหนักใช้งาน LL (กก./ตร.ม.)", value=30.0, step=5.0, key="ll")
    wl = st.number_input("แรงลม WL (กก./ตร.ม.)", value=50.0, step=5.0, key="wl")
    
    # Materials
    st.subheader("3. วัสดุ")
    mat_cls = SteelMaterial()
    # Let user override or just use standard inputs
    fy = st.number_input("กำลังคราก Fy (กก./ตร.ซม.)", value=2450.0, step=50.0, key="fy")
    E = st.number_input("มอดูลัสยืดหยุ่น E (กก./ตร.ซม.)", value=2.04e6, format="%.2e", key="E")
    
    # Section Selection
    st.subheader("4. เลือกหน้าตัด")
    section_name = st.selectbox("เลือกหน้าตัด", df['Section'].unique(), key="section")
    
    # Live Calculation Toggle
    st.divider()
    live_calc = st.checkbox("🔴 Live Calculation (คำนวณอัตโนมัติ)", value=True, key="live_calc")
    if live_calc:
        st.caption("⚡ กราฟจะอัปเดตทันทีเมื่อแก้ไขค่า")

with col_in2:
    st.header("ผลการคำนวณ")
    
    # Auto-calculate if live calculation is enabled, or manual button
    should_calculate = live_calc
    if not live_calc:
        should_calculate = st.button("เริ่มคำนวณ", type="primary")
    
    if should_calculate:
        # Get section data
        row = df[df['Section'] == section_name].iloc[0]
        
        # Prepare inputs
        section_data = {
            'name': section_name,
            'Zx': row.get('Zx', 0),
            'Ix': row.get('Ix', 0),
            'Weight': row.get('Weight', 0),
            'h': row.get('h', 0),
            't': row.get('t', 0),
            'Area': row.get('Area', 0) 
        }
        
        geometry = {'span': span, 'spacing': spacing, 'slope': slope}
        loads = {'DL': dl, 'LL': ll, 'WL': wl}
        materials = {'Fy': fy, 'E': E}
        
        # Run Design
        designer = PurlinDesign(section_data, geometry, loads, materials)
        res = designer.run_design()
        
        checks = res['Checks']['Status']
        ratios = res['Checks']['Ratios']
        defl_detail = res['Checks']['Deflection']
        
        # Summary with Emoji Reactions
        st.markdown(f"**หน้าตัดที่เลือก:** {section_name}")
        
        # Status Metrics with Emoji Reactions
        m1, m2, m3 = st.columns(3)
        
        # Moment status with emoji reaction
        moment_emoji = "✅" if checks['Moment'] else ("⚠️" if ratios['Moment'] > 0.8 else "❌")
        moment_class = "status-pass" if checks['Moment'] else ("status-warning" if ratios['Moment'] > 0.8 else "status-fail")
        m1.markdown(f"""
        <div style="text-align: center;">
            <div style="font-size: 3rem;">{moment_emoji}</div>
            <div style="font-size: 0.9rem; color: #b0b0b0;">กำลังดัด</div>
            <div style="font-size: 2rem; font-weight: 700;" class="{moment_class}">{ratios['Moment']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Shear status with emoji reaction
        shear_emoji = "✅" if checks['Shear'] else ("⚠️" if ratios['Shear'] > 0.8 else "❌")
        shear_class = "status-pass" if checks['Shear'] else ("status-warning" if ratios['Shear'] > 0.8 else "status-fail")
        m2.markdown(f"""
        <div style="text-align: center;">
            <div style="font-size: 3rem;">{shear_emoji}</div>
            <div style="font-size: 0.9rem; color: #b0b0b0;">กำลังเฉือน</div>
            <div style="font-size: 2rem; font-weight: 700;" class="{shear_class}">{ratios['Shear']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Deflection status with emoji reaction
        defl_emoji = "✅" if checks['Deflection'] else ("⚠️" if ratios['Deflection'] > 0.8 else "❌")
        defl_class = "status-pass" if checks['Deflection'] else ("status-warning" if ratios['Deflection'] > 0.8 else "status-fail")
        m3.markdown(f"""
        <div style="text-align: center;">
            <div style="font-size: 3rem;">{defl_emoji}</div>
            <div style="font-size: 0.9rem; color: #b0b0b0;">การโก่งตัว</div>
            <div style="font-size: 2rem; font-weight: 700;" class="{defl_class}">{ratios['Deflection']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        demand = res['Checks']['Demand']
        capacity = res['Checks']['Capacity']

        st.subheader("📊 เปรียบเทียบค่ากำลังและการโก่งตัว")
        summary_df = pd.DataFrame({
            "การตรวจสอบ": ["กำลังดัด", "กำลังเฉือน", "การโก่งตัวรวม", "การโก่งตัวจาก LL"],
            "ค่าที่ต้องรับ": [
                f"{demand['Mu']:.2f} กก.-ม.",
                f"{demand['Vu']:.2f} กก.",
                f"{defl_detail['Total']['value']:.3f} ซม.",
                f"{defl_detail['Live']['value']:.3f} ซม.",
            ],
            "ค่ากำลัง/เกณฑ์": [
                f"{capacity['Phi_Mn']:.2f} กก.-ม.",
                f"{capacity['Phi_Vn']:.2f} กก.",
                f"{capacity['Delta_Limit_Total']:.3f} ซม.",
                f"{capacity['Delta_Limit_Live']:.3f} ซม.",
            ],
            "อัตราส่วน": [
                ratios['Moment'],
                ratios['Shear'],
                defl_detail['Total']['ratio'],
                defl_detail['Live']['ratio'],
            ],
            "ผล": [
                "✅ ผ่าน" if checks['Moment'] else "❌ ไม่ผ่าน",
                "✅ ผ่าน" if checks['Shear'] else "❌ ไม่ผ่าน",
                "✅ ผ่าน" if defl_detail['Total']['pass'] else "❌ ไม่ผ่าน",
                "✅ ผ่าน" if defl_detail['Live']['pass'] else "❌ ไม่ผ่าน",
            ],
        })
        
        # Apply styling to dataframe with neon colors
        def style_result(val):
            if "ผ่าน" in str(val):
                return 'color: #00ff41; text-shadow: 0 0 6px rgba(0, 255, 65, 0.5); font-weight: 700;'
            elif "ไม่ผ่าน" in str(val):
                return 'color: #ff0040; text-shadow: 0 0 6px rgba(255, 0, 64, 0.5); font-weight: 700;'
            return ''
        
        styled_df = summary_df.style.format({"อัตราส่วน": "{:.2f}"}).map(style_result, subset=['ผล'])
        st.dataframe(styled_df, use_container_width=True)

        st.divider()
        
        # 3D Section Preview
        with st.expander("🔧 3D Preview หน้าตัดเหล็ก", expanded=False):
            col3d1, col3d2 = st.columns(2)
            
            with col3d1:
                # Parse section dimensions from name (e.g., C-100x50x20x3.2)
                try:
                    parts = section_name.replace('C-', '').split('x')
                    h_3d = float(parts[0]) if len(parts) > 0 else 100
                    b_3d = float(parts[1]) if len(parts) > 1 else 50
                    c_3d = float(parts[2]) if len(parts) > 2 else 20
                    t_3d = float(parts[3]) if len(parts) > 3 else 3.2
                except:
                    h_3d, b_3d, c_3d, t_3d = 100, 50, 20, 3.2
                
                fig_section = create_c_channel_3d(
                    h=h_3d, b=b_3d, c=c_3d, t=t_3d,
                    length=500, name=section_name
                )
                st.plotly_chart(fig_section, use_container_width=True)
            
            with col3d2:
                fig_system = create_purlin_system_3d(
                    span=span, spacing=spacing, num_purlins=5, h=h_3d, slope=slope
                )
                st.plotly_chart(fig_system, use_container_width=True)
        
        # Detailed Steps with LaTeX
        with st.expander("📝 ขั้นตอนการคำนวณแบบละเอียด", expanded=True):
            for step in res['Steps']:
                status = step.get('status')
                icon = "✅" if status == 'PASS' else ("❌" if status == 'FAIL' else "ℹ️")
                st.markdown(f"**{icon} {step['title']}**")
                st.latex(step['latex'])
                if step.get('note'):
                    st.markdown(f"_{step['note']}_")
                st.markdown("---")
        


        # Report Generation
        st.subheader("📄 รายงานผลคำนวณ")
        proj_info = {'Project Name': project_name, 'Owner': owner, 'Engineer': engineer}
        
        # We need to save inputs too
        inputs_dict = {'geometry': geometry, 'loads': loads, 'materials': materials}
        
        if st.button("สร้างรายงาน PDF"):
            report = PurlinReportGenerator(proj_info, inputs_dict, res, section_data)
            success, result_path = report.generate("Purlin_Design_Report.pdf")
            
            if success:
                st.success("สร้างรายงานสำเร็จ")
                with open(result_path, "rb") as f:
                    st.download_button(
                        label="ดาวน์โหลดรายงาน",
                        data=f,
                        file_name="Purlin_Design_Report.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error(f"ไม่สามารถสร้างรายงานได้: {result_path}")
                # Print exception for valid string debugging
                print(f"PDF Error: {result_path}")
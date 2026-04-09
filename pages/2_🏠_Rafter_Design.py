import streamlit as st
import pandas as pd
from rafter_design import RafterDesign
from data_utils import load_data
from theme_manager import use_theme

st.set_page_config(page_title="ออกแบบจันทัน", layout="wide")
use_theme()

st.title("🏠 โมดูลออกแบบจันทันเหล็กรีดร้อน")
st.markdown("---")

# --- 1. Load Data ---
DATA_FILE_CF = "Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv" # Cold Formed
DATA_FILE_HR = "tis_1227_steel.csv" # Hot Rolled

@st.cache_data
def get_data_cf():
    return load_data(DATA_FILE_CF)

@st.cache_data
def get_data_hr():
    # Load hot rolled directly since it's cleaner
    if pd.io.common.file_exists(DATA_FILE_HR):
        return pd.read_csv(DATA_FILE_HR)
    return pd.DataFrame()

df_cf = get_data_cf()
df_hr = get_data_hr()


# --- 2. Sidebar Inputs ---
with st.sidebar:
    st.header("1. มิติทางเรขาคณิต")
    span = st.number_input("ช่วงพาดตามความลาด (เมตร)", value=6.0, step=0.1, format="%.2f", key="rafter_span")
    spacing = st.number_input("ระยะห่างจันทัน (เมตร)", value=1.5, step=0.1, format="%.2f", key="rafter_spacing")
    slope = st.number_input("ความชันหลังคา (องศา)", value=10.0, step=0.1, format="%.1f", key="rafter_slope")
    lb = st.number_input("ความยาวไม่ค้ำยัน Lb (เมตร)", value=1.5, step=0.1, format="%.2f", key="rafter_lb")

    st.header("2. น้ำหนักบรรทุก")
    dl = st.number_input("น้ำหนักบรรทุกคงที่ DL (กก./ตร.ม.)", value=20.0, step=1.0, key="rafter_dl")
    ll = st.number_input("น้ำหนักใช้งาน LL (กก./ตร.ม.)", value=30.0, step=1.0, key="rafter_ll")
    wl = st.number_input("แรงลม WL (กก./ตร.ม.)", value=50.0, step=1.0, key="rafter_wl")

    st.header("3. คุณสมบัติวัสดุ")
    fy = st.number_input("กำลังคราก Fy (กก./ตร.ซม.)", value=2400.0, step=100.0, key="rafter_fy")
    E = st.number_input("มอดูลัสยืดหยุ่น E (กก./ตร.ซม.)", value=2.04e6, format="%.2e", key="rafter_E")

    st.header("4. เลือกหน้าตัด")
    # Section Type Toggle - Lip-C Default for Rafter per user request
    steel_type = st.radio("ชนิดเหล็ก", ["Hot-Rolled (H-Beam/I-Beam มอก. 1227)", "Cold-Formed (Lip-C มอก. 1228)"], index=1)
    
    if steel_type == "Hot-Rolled (H-Beam/I-Beam มอก. 1227)":
        df = df_hr
        if df.empty: st.error("ไม่พบข้อมูลเหล็กรีดร้อน"); st.stop()
    else:
        df = df_cf
        if df.empty: st.error("ไม่พบข้อมูลเหล็กขึ้นรูปเย็น"); st.stop()
        
    section_name = st.selectbox("เลือกหน้าตัด", df['Section'].astype(str).unique(), key="rafter_section")
    
    # Live Calculation Toggle
    st.divider()
    live_calc_rafter = st.checkbox("🔴 Live Calculation (คำนวณอัตโนมัติ)", value=True, key="live_calc_rafter")
    if live_calc_rafter:
        st.caption("⚡ กราฟจะอัปเดตทันทีเมื่อแก้ไขค่า")

# --- 3. Main Content: Section Details & Run ---
st.subheader("คุณสมบัติหน้าตัด")

# Get selected row
row = df[df['Section'] == section_name].iloc[0]

if steel_type == "Hot-Rolled (H-Beam/I-Beam มอก. 1227)":
    # Mapped directly from headers generated in generate_tis_hotrolled.py
    # h, b, tw, tf, Area, Ix, Iy, Sx, Zx, ry, Weight
    
    # Defaults in CM
    def get_val(key, default=0.0): return float(row.get(key, default))
    
    default_d = get_val('h') / 10.0
    default_bf = get_val('b') / 10.0
    default_tf = get_val('tf') / 10.0 # mm -> cm
    default_tw = get_val('tw') / 10.0 # mm -> cm
    default_A = get_val('Area')
    default_Ix = get_val('Ix')
    default_Zx = get_val('Zx') # Plastic Zx
    default_Sx = get_val('Sx') # Elastic Sx
    default_ry = get_val('ry')
    
else:
    # Cold Formed (Lip-C) logic
    # Extract basic props from CSV (mapped by data_utils)
    # Note: data_utils maps 'h', 't', 'Area', 'Ix', 'Zx', 'Weight'
    # We need to map these to RafterDesign expectations: Zx, Ix, Sx, Area, d, bf, tf, tw, ry
    csv_d = row.get('h', 0) / 10.0 # mm to cm

    # Helper to safely get mm and convert to cm
    def get_cm(key, default_val=0.0):
        val = row.get(key)
        if pd.isna(val): return default_val
        return float(val) / 10.0

    default_d = get_cm('h', 10.0)
    # C-Channel 'b' column (from generate_tis_steel.py) or default
    if 'b' in row:
        default_bf = get_cm('b')
    else:
        # Fallback if specific col not found, assume 1228 standard ratios
        default_bf = default_d / 2.0 
        
    default_tf = get_cm('t', 0.5)
    default_tw = get_cm('t', 0.5)
    
    pass # Continue to code block below for usage

    default_A = float(row.get('Area', 0))
    default_Ix = float(row.get('Ix', 0))
    default_Zx = float(row.get('Zx', 0)) # Usually Elastic in CF table
    default_Sx = default_Zx # Approx if missing
    default_ry = default_d * 0.40 # Rough approx for C-channel


with st.expander("ตั้งค่าคุณสมบัติหน้าตัดเพิ่มเติม", expanded=True):
    c1, c2, c3 = st.columns(3)
    
    # Column 1: Basic Dimensions
    with c1:
        d_cm = st.number_input("ความลึกหน้าตัด d (ซม.)", value=default_d, format="%.2f")
        bf_cm = st.number_input("ความกว้างปีก bf (ซม.)", value=default_bf, format="%.2f")
        tf_cm = st.number_input("ความหนาปีก tf (ซม.)", value=default_tf, format="%.3f")
        tw_cm = st.number_input("ความหนาเว็บ tw (ซม.)", value=default_tw, format="%.3f")
        
    # Column 2: Structural Properties
    with c2:
        area_cm2 = st.number_input("พื้นที่หน้าตัด (ตร.ซม.)", value=default_A, format="%.2f")
        ix_cm4 = st.number_input("โมเมนต์ความเฉื่อย Ix (ซม.^4)", value=default_Ix, format="%.2f")
        zx_cm3 = st.number_input("โมดูลัสต้านทาน Zx (ซม.^3)", value=default_Zx, format="%.2f")
        sx_cm3 = st.number_input("โมดูลัสหน้าตัด Sx (ซม.^3)", value=default_Sx, format="%.2f")
        
    # Column 3: Advanced / LTB
    with c3:
        ry_cm = st.number_input("รัศมีความเฉื่อย ry (ซม.)", value=default_ry, format="%.2f")
        st.markdown("**กรอกค่าพารามิเตอร์ LTB หากมีข้อมูล**")
        rts_cm = st.number_input("rts (ซม.)", value=0.0, format="%.2f")
        J_cm4 = st.number_input("J (ซม.^4)", value=0.0, format="%.2f")
        h0_cm = st.number_input("h0 (ซม.)", value=0.0, format="%.2f")

# Auto-calculate if live calculation is enabled, or manual button
should_calculate_rafter = live_calc_rafter
if not live_calc_rafter:
    should_calculate_rafter = st.button("เริ่มคำนวณ", type="primary")

if should_calculate_rafter:
    # 1. Prepare Data
    # Handle inputs
    section_data = {
        'd': d_cm,
        'bf': bf_cm,
        'tf': tf_cm,
        'tw': tw_cm,
        'Area': area_cm2,
        'Ix': ix_cm4,
        'Zx': zx_cm3,
        'Sx': sx_cm3,
        'ry': ry_cm,
        'Weight': row.get('Weight', 0)
    }
    
    # Add optional if provided
    if rts_cm > 0: section_data['rts'] = rts_cm
    if J_cm4 > 0: section_data['J'] = J_cm4
    if h0_cm > 0: section_data['h0'] = h0_cm
    
    geometry = {
        'span': span,
        'spacing': spacing,
        'slope': slope,
        'Lb': lb
    }
    
    load_inputs = {
        'DL': dl,
        'LL': ll,
        'WL': wl
    }
    
    materials = {
        'Fy': fy,
        'E': E
    }
    
    # 2. Run Design
    design = RafterDesign(section_data, geometry, load_inputs, materials)
    res = design.run_design()
    
    # 3. Display Results
    
    # A. Summary Status with Emoji Reactions
    checks = res['Checks']['Status']
    all_pass = all(checks.values())
    
    overall_emoji = "✅" if all_pass else "❌"
    st.markdown(f'<div style="text-align: center; font-size: 4rem;">{overall_emoji}</div>', unsafe_allow_html=True)
    if all_pass:
        st.markdown('<div class="status-pass" style="text-align: center; font-size: 1.5rem; font-weight: 700;">ผ่านเกณฑ์การออกแบบ</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-fail" style="text-align: center; font-size: 1.5rem; font-weight: 700;">ไม่ผ่านเกณฑ์การออกแบบ</div>', unsafe_allow_html=True)
        
    # Display Ratios with Emoji Reactions
    ratios = res['Checks']['Ratios']
    defl_detail = res['Checks'].get('Deflection', {})
    c_res1, c_res2, c_res3 = st.columns(3)
    
    # Moment
    moment_emoji_r = "✅" if checks['Moment'] else ("⚠️" if ratios['Moment'] > 0.8 else "❌")
    moment_class_r = "status-pass" if checks['Moment'] else ("status-warning" if ratios['Moment'] > 0.8 else "status-fail")
    c_res1.markdown(f"""
    <div style="text-align: center;">
        <div style="font-size: 3rem;">{moment_emoji_r}</div>
        <div style="font-size: 0.9rem; color: #b0b0b0;">กำลังดัด</div>
        <div style="font-size: 2rem; font-weight: 700;" class="{moment_class_r}">{ratios['Moment']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Shear
    shear_emoji_r = "✅" if checks['Shear'] else ("⚠️" if ratios['Shear'] > 0.8 else "❌")
    shear_class_r = "status-pass" if checks['Shear'] else ("status-warning" if ratios['Shear'] > 0.8 else "status-fail")
    c_res2.markdown(f"""
    <div style="text-align: center;">
        <div style="font-size: 3rem;">{shear_emoji_r}</div>
        <div style="font-size: 0.9rem; color: #b0b0b0;">กำลังเฉือน</div>
        <div style="font-size: 2rem; font-weight: 700;" class="{shear_class_r}">{ratios['Shear']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Deflection
    defl_emoji_r = "✅" if checks['Deflection'] else ("⚠️" if ratios['Deflection'] > 0.8 else "❌")
    defl_class_r = "status-pass" if checks['Deflection'] else ("status-warning" if ratios['Deflection'] > 0.8 else "status-fail")
    c_res3.markdown(f"""
    <div style="text-align: center;">
        <div style="font-size: 3rem;">{defl_emoji_r}</div>
        <div style="font-size: 0.9rem; color: #b0b0b0;">การโก่งตัว</div>
        <div style="font-size: 2rem; font-weight: 700;" class="{defl_class_r}">{ratios['Deflection']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    # B. Detailed Steps
    st.markdown("### 📝 รายละเอียดการคำนวณ")
    
    for step in res['Steps']:
        with st.container():
            # Title with Icon based on status
            icon = "✅" if step.get('status') == 'PASS' else ("❌" if step.get('status') == 'FAIL' else "ℹ️")
            st.markdown(f"**{icon} {step['title']}**")
            
            st.latex(step['latex'])
            note = step.get('note')
            if note:
                st.markdown(f"_{note}_")
            st.divider()

    # C. Result Summary Table
    st.markdown("### 📊 เปรียบเทียบความต้องการกับกำลังต้านทาน")
    demand = res['Checks']['Demand']
    capacity = res['Checks']['Capacity']
    defl_total = defl_detail.get('Total') or {'value': float('nan'), 'limit': float('nan'), 'ratio': float('nan'), 'pass': False}
    defl_live = defl_detail.get('Live') or {'value': float('nan'), 'limit': float('nan'), 'ratio': float('nan'), 'pass': False}

    summary_data = {
        "การตรวจสอบ": ["กำลังดัด", "กำลังเฉือน", "การโก่งตัวรวม", "การโก่งตัวจาก LL"],
        "ค่าที่ต้องรับ": [
            f"{demand['Mu']:.2f} กก.-ม.",
            f"{demand['Vu']:.2f} กก.",
            f"{defl_total['value']:.2f} ซม.",
            f"{defl_live['value']:.2f} ซม."
        ],
        "ค่ากำลัง/เกณฑ์": [
            f"{capacity['Phi_Mn']:.2f} กก.-ม.",
            f"{capacity['Phi_Vn']:.2f} กก.",
            f"{capacity['Delta_Limit_Total']:.2f} ซม.",
            f"{capacity['Delta_Limit_Live']:.2f} ซม."
        ],
        "อัตราส่วน": [
            ratios['Moment'],
            ratios['Shear'],
            defl_total['ratio'],
            defl_live['ratio']
        ],
        "ผลการตรวจ": [
            "ผ่าน" if checks['Moment'] else "ไม่ผ่าน",
            "ผ่าน" if checks['Shear'] else "ไม่ผ่าน",
            "ผ่าน" if defl_total['pass'] else "ไม่ผ่าน",
            "ผ่าน" if defl_live['pass'] else "ไม่ผ่าน"
        ]
    }
    st.dataframe(pd.DataFrame(summary_data).style.format({'อัตราส่วน': '{:.2f}'}))
    
    st.divider()
    
    # D. Report Generation
    st.subheader("📄 รายงานผลคำนวณ")
    
    with st.expander("รายละเอียดโครงการสำหรับรายงาน"):
        col1, col2, col3 = st.columns(3)
        p_name = col1.text_input("ชื่อโครงการ", "New Warehouse")
        p_owner = col2.text_input("เจ้าของโครงการ", "Client A")
        p_eng = col3.text_input("วิศวกรผู้ออกแบบ", "Eng. Sarayut")
        
    project_info = {'Project Name': p_name, 'Owner': p_owner, 'Engineer': p_eng}
    inputs_dict = {'geometry': geometry, 'loads': load_inputs, 'materials': materials}
    
    if st.button("สร้างรายงาน PDF", key="rafter_pdf"):
        from report_generator import RafterReportGenerator
        
        # Add extra fields to section data for report
        section_data['name'] = section_name
        # section_data already has d, bf, tf etc. from Run Design step
        
        report = RafterReportGenerator(project_info, inputs_dict, res, section_data)
        success, result_path = report.generate("Rafter_Design_Report.pdf")
        
        if success:
            st.success("สร้างรายงานสำเร็จ")
            with open(result_path, "rb") as f:
                st.download_button("ดาวน์โหลดรายงาน", f, "Rafter_Design_Report.pdf", "application/pdf")
        else:
            st.error(f"ไม่สามารถสร้างรายงานได้: {result_path}")
            print(f"Rafter PDF Error: {result_path}")

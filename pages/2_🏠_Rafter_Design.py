import streamlit as st
import pandas as pd
from rafter_design import RafterDesign
from theme_manager import use_theme

st.set_page_config(page_title="ออกแบบจันทัน", layout="wide")
use_theme()

st.title("🏠 โมดูลออกแบบจันทันเหล็ก")
st.markdown("**อ้างอิง:** AISC 360-16 · วิธี LRFD · รองรับ มอก. 1227 (รีดร้อน) และ มอก. 1228 (ขึ้นรูปเย็น)")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# โหลดข้อมูลหน้าตัด
# ─────────────────────────────────────────────────────────────
DATA_HR = "tis_1227_steel.csv"
DATA_CF = "Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv"


@st.cache_data
def _load_hr():
    if pd.io.common.file_exists(DATA_HR):
        df = pd.read_csv(DATA_HR)
        # fallback: ถ้าไม่มีคอลัมน์ Type ให้เพิ่มเป็น HN ทั้งหมด
        if "Type" not in df.columns:
            df["Type"] = "HN"
        return df
    return pd.DataFrame()


@st.cache_data
def _load_cf():
    from data_utils import load_data
    df = load_data(DATA_CF)
    # ถ้า load_data ไม่ได้ข้อมูล ให้ลอง tis_1228 โดยตรง
    if df.empty and pd.io.common.file_exists("tis_1228_steel.csv"):
        df = pd.read_csv("tis_1228_steel.csv")
    return df


df_hr = _load_hr()
df_cf = _load_cf()

# ─────────────────────────────────────────────────────────────
# SIDEBAR — Inputs
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📐 1. มิติเรขาคณิต")
    span    = st.number_input("ช่วงพาด L (เมตร)",           value=6.0,  step=0.5,  format="%.2f", key="rf_span")
    spacing = st.number_input("ระยะห่างจันทัน s (เมตร)",    value=1.5,  step=0.1,  format="%.2f", key="rf_spacing")
    slope   = st.number_input("ความชันหลังคา (องศา)",       value=10.0, step=0.5,  format="%.1f", key="rf_slope")
    lb      = st.number_input("ความยาวไม่ค้ำยัน Lb (เมตร)", value=1.5,  step=0.1,  format="%.2f", key="rf_lb")

    st.header("⚖️ 2. น้ำหนักบรรทุก")
    dl = st.number_input("น้ำหนักคงที่ DL (กก./ตร.ม.)",  value=20.0, step=5.0, key="rf_dl")
    ll = st.number_input("น้ำหนักใช้งาน LL (กก./ตร.ม.)", value=30.0, step=5.0, key="rf_ll")
    wl = st.number_input("แรงลม WL (กก./ตร.ม.)",         value=50.0, step=5.0, key="rf_wl")

    st.header("🔩 3. เลือกหน้าตัด")

    # ── ก. มาตรฐานวัสดุ ──────────────────────────────────────
    std_choice = st.radio(
        "มาตรฐานวัสดุ",
        ["🏗 มอก. 1227 — เหล็กรีดร้อน (H-Beam / I-Beam)", "📦 มอก. 1228 — เหล็กขึ้นรูปเย็น (Lip-C)"],
        key="rf_std",
    )
    is_hr = std_choice.startswith("🏗")

    if is_hr:
        # ── ข. ชนิดหน้าตัด H-Beam ─────────────────────────────
        if df_hr.empty:
            st.error("ไม่พบ tis_1227_steel.csv")
            st.stop()

        type_labels = {
            "HN": "HN — ปีกแคบ (คาน / จันทัน)",
            "HM": "HM — ปีกกลาง (คาน-เสา)",
            "HW": "HW — ปีกกว้าง (เสา)",
            "I":  "I  — I-Beam ปีกลิ่ม",
        }
        available_types = [t for t in ["HN", "HM", "HW", "I"] if t in df_hr["Type"].values]
        type_sel = st.selectbox(
            "ชนิดหน้าตัด",
            available_types,
            format_func=lambda t: type_labels.get(t, t),
            key="rf_type",
        )

        df_filtered = df_hr[df_hr["Type"] == type_sel].copy()

        # ── ค. กรองตามความลึก ─────────────────────────────────
        h_vals = sorted(df_filtered["h"].unique())
        h_min, h_max = int(min(h_vals)), int(max(h_vals))
        depth_range = st.select_slider(
            "กรองตามความลึก h (mm)",
            options=sorted(df_filtered["h"].unique().tolist()),
            value=(h_min, h_max),
            key="rf_depth",
        )
        df_show = df_filtered[
            (df_filtered["h"] >= depth_range[0]) & (df_filtered["h"] <= depth_range[1])
        ]

        if df_show.empty:
            st.warning("ไม่พบหน้าตัดในช่วงที่เลือก")
            st.stop()

        section_name = st.selectbox(
            "เลือกหน้าตัด",
            df_show["Section"].astype(str).unique(),
            key="rf_sec_hr",
        )
        row = df_hr[df_hr["Section"] == section_name].iloc[0]

        # ── ง. คุณสมบัติวัสดุ SS400 / SM490 ──────────────────
        grade_map = {
            "SS400  (Fy=2,500 / Fu=4,080 ksc)": (2500.0, 4080.0),
            "SM490  (Fy=3,313 / Fu=4,894 ksc)": (3313.0, 4894.0),
            "SM570  (Fy=4,587 / Fu=5,709 ksc)": (4587.0, 5709.0),
            "กำหนดเอง": (0.0, 0.0),
        }
        grade_sel = st.selectbox("เกรดเหล็ก มอก. 1227", list(grade_map.keys()), key="rf_grade")
        fy_def, _ = grade_map[grade_sel]
        if grade_sel == "กำหนดเอง":
            fy = st.number_input("Fy (ksc)", value=2500.0, step=50.0, key="rf_fy_c")
        else:
            fy = fy_def
            st.info(f"Fy = {fy:,.0f} ksc")
        E = st.number_input("E (ksc)", value=2.04e6, format="%.3e", key="rf_E_hr")

    else:
        # ── ข. C-Channel มอก. 1228 ───────────────────────────
        if df_cf.empty:
            st.error("ไม่พบข้อมูล มอก. 1228")
            st.stop()

        # กรองตามความลึก
        h_col = "h" if "h" in df_cf.columns else df_cf.columns[0]
        h_vals_cf = sorted(df_cf[h_col].unique().tolist()) if h_col in df_cf.columns else []
        if h_vals_cf:
            depth_range_cf = st.select_slider(
                "กรองตามความลึก h (mm)",
                options=h_vals_cf,
                value=(min(h_vals_cf), max(h_vals_cf)),
                key="rf_depth_cf",
            )
            df_show_cf = df_cf[
                (df_cf[h_col] >= depth_range_cf[0]) & (df_cf[h_col] <= depth_range_cf[1])
            ]
        else:
            df_show_cf = df_cf

        section_name = st.selectbox(
            "เลือกหน้าตัด C-Channel",
            df_show_cf["Section"].astype(str).unique(),
            key="rf_sec_cf",
        )
        row = df_cf[df_cf["Section"] == section_name].iloc[0]

        # วัสดุ SSC400 มอก. 1228
        st.markdown("**เกรดเหล็ก:** SSC400 (มอก. 1228-2549)")
        fy = st.number_input("Fy (ksc)", value=2450.0, step=50.0, key="rf_fy_cf")
        E  = st.number_input("E  (ksc)", value=2.04e6, format="%.3e", key="rf_E_cf")

    st.divider()
    live_calc = st.checkbox("🔴 Live Calculation", value=True, key="rf_live")

# ─────────────────────────────────────────────────────────────
# MAIN AREA — Section Properties & Results
# ─────────────────────────────────────────────────────────────

# ── แสดงคุณสมบัติหน้าตัดอัตโนมัติ ────────────────────────────
st.subheader("📋 คุณสมบัติหน้าตัด")

def _fv(key, default=0.0):
    v = row.get(key, default)
    return float(v) if v is not None and str(v) != "nan" else default

if is_hr:
    # แปลง mm → cm
    d_cm   = _fv("h")  / 10.0
    bf_cm  = _fv("b")  / 10.0
    tf_cm  = _fv("tf") / 10.0
    tw_cm  = _fv("tw") / 10.0
    area   = _fv("Area")
    Ix_v   = _fv("Ix")
    Sx_v   = _fv("Sx")
    Zx_v   = _fv("Zx")
    ry_v   = _fv("ry")
    rts_v  = _fv("rts")
    J_v    = _fv("J")
    h0_v   = _fv("h0")
    wt_v   = _fv("Weight")
    rx_v   = _fv("rx")

    prop_cols = st.columns(4)
    prop_cols[0].metric("น้ำหนัก", f"{wt_v:.2f} kg/m")
    prop_cols[1].metric("Area",    f"{area:.3f} cm²")
    prop_cols[2].metric("Ix",      f"{Ix_v:.1f} cm⁴")
    prop_cols[3].metric("Zx (Plastic)", f"{Zx_v:.2f} cm³")
    prop_cols2 = st.columns(4)
    prop_cols2[0].metric("rx",  f"{rx_v:.3f} cm")
    prop_cols2[1].metric("ry",  f"{ry_v:.3f} cm")
    prop_cols2[2].metric("rts", f"{rts_v:.3f} cm")
    prop_cols2[3].metric("J",   f"{J_v:.4f} cm⁴")

    with st.expander("ดูคุณสมบัติครบทุกคอลัมน์", expanded=False):
        st.dataframe(
            pd.DataFrame([row]).T.rename(columns={0: "ค่า"}),
            use_container_width=True,
        )

else:
    d_cm  = _fv("h")  / 10.0
    bf_cm = _fv("b")  / 10.0
    tf_cm = _fv("t")  / 10.0
    tw_cm = _fv("t")  / 10.0
    area  = _fv("Area")
    Ix_v  = _fv("Ix")
    Sx_v  = _fv("Sx") if "Sx" in row.index else _fv("Zx")
    Zx_v  = _fv("Zx")
    ry_v  = d_cm * 0.28   # approximate for C-channel
    rts_v = 0.0
    J_v   = 0.0
    h0_v  = 0.0
    wt_v  = _fv("Weight")

    prop_cols = st.columns(4)
    prop_cols[0].metric("น้ำหนัก", f"{wt_v:.2f} kg/m")
    prop_cols[1].metric("Area",   f"{area:.3f} cm²")
    prop_cols[2].metric("Ix",     f"{Ix_v:.1f} cm⁴")
    prop_cols[3].metric("Zx/Sx",  f"{Zx_v:.2f} cm³")

# ── (Optional) Override ────────────────────────────────────────
with st.expander("✏️ แก้ไขค่าคุณสมบัติด้วยตนเอง (Optional Override)", expanded=False):
    oc1, oc2, oc3 = st.columns(3)
    d_cm   = oc1.number_input("d (cm)",    value=d_cm,   format="%.3f", key="rf_ov_d")
    bf_cm  = oc1.number_input("bf (cm)",   value=bf_cm,  format="%.3f", key="rf_ov_bf")
    tf_cm  = oc1.number_input("tf (cm)",   value=tf_cm,  format="%.4f", key="rf_ov_tf")
    tw_cm  = oc1.number_input("tw (cm)",   value=tw_cm,  format="%.4f", key="rf_ov_tw")
    area   = oc2.number_input("Area (cm²)",value=area,   format="%.3f", key="rf_ov_A")
    Ix_v   = oc2.number_input("Ix (cm⁴)",  value=Ix_v,   format="%.2f", key="rf_ov_Ix")
    Zx_v   = oc2.number_input("Zx (cm³)",  value=Zx_v,   format="%.2f", key="rf_ov_Zx")
    Sx_v   = oc2.number_input("Sx (cm³)",  value=Sx_v,   format="%.2f", key="rf_ov_Sx")
    ry_v   = oc3.number_input("ry (cm)",   value=ry_v,   format="%.4f", key="rf_ov_ry")
    rts_v  = oc3.number_input("rts (cm)",  value=rts_v,  format="%.4f", key="rf_ov_rts")
    J_v    = oc3.number_input("J (cm⁴)",   value=J_v,    format="%.4f", key="rf_ov_J")
    h0_v   = oc3.number_input("h0 (cm)",   value=h0_v,   format="%.3f", key="rf_ov_h0")

st.divider()

# ─────────────────────────────────────────────────────────────
# RUN DESIGN
# ─────────────────────────────────────────────────────────────
should_calc = live_calc
if not live_calc:
    should_calc = st.button("เริ่มคำนวณ", type="primary", key="rf_calc_btn")

if should_calc:
    section_data = {
        "name":   section_name,
        "d":      d_cm,
        "bf":     bf_cm,
        "tf":     tf_cm,
        "tw":     tw_cm,
        "Area":   area,
        "Ix":     Ix_v,
        "Zx":     Zx_v,
        "Sx":     Sx_v,
        "ry":     ry_v,
        "Weight": wt_v,
    }
    if rts_v > 0: section_data["rts"] = rts_v
    if J_v   > 0: section_data["J"]   = J_v
    if h0_v  > 0: section_data["h0"]  = h0_v

    geometry   = {"span": span, "spacing": spacing, "slope": slope, "Lb": lb}
    load_input = {"DL": dl, "LL": ll, "WL": wl}
    materials  = {"Fy": fy, "E": E}

    design = RafterDesign(section_data, geometry, load_input, materials)
    res    = design.run_design()

    checks = res["Checks"]["Status"]
    ratios = res["Checks"]["Ratios"]
    defl_detail = res["Checks"].get("Deflection", {})
    all_pass = all(checks.values())

    # ── Status Banner ─────────────────────────────────────────
    banner_emoji = "✅" if all_pass else "❌"
    banner_class = "status-pass" if all_pass else "status-fail"
    banner_text  = "ผ่านเกณฑ์การออกแบบ" if all_pass else "ไม่ผ่านเกณฑ์การออกแบบ"
    st.markdown(
        f'<div style="text-align:center;font-size:3.5rem;">{banner_emoji}</div>'
        f'<div class="{banner_class}" style="text-align:center;font-size:1.4rem;font-weight:700;">'
        f'{banner_text}</div>',
        unsafe_allow_html=True,
    )

    # ── Ratio Cards ───────────────────────────────────────────
    st.markdown("")
    c1, c2, c3 = st.columns(3)
    for col, key, label in [(c1, "Moment", "กำลังดัด"), (c2, "Shear", "กำลังเฉือน"), (c3, "Deflection", "การโก่งตัว")]:
        ok  = checks[key]
        r   = ratios[key]
        em  = "✅" if ok else ("⚠️" if r > 0.8 else "❌")
        cls = "status-pass" if ok else ("status-warning" if r > 0.8 else "status-fail")
        col.markdown(
            f'<div style="text-align:center;">'
            f'<div style="font-size:2.8rem;">{em}</div>'
            f'<div style="font-size:0.85rem;color:#b0b0b0;">{label}</div>'
            f'<div style="font-size:1.9rem;font-weight:700;" class="{cls}">{r:.2f}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Summary Table ─────────────────────────────────────────
    st.markdown("### 📊 เปรียบเทียบความต้องการกับกำลังต้านทาน")

    demand   = res["Checks"]["Demand"]
    capacity = res["Checks"]["Capacity"]
    dt = defl_detail.get("Total") or {"value": float("nan"), "limit": float("nan"), "ratio": float("nan"), "pass": False}
    dl_ = defl_detail.get("Live")  or {"value": float("nan"), "limit": float("nan"), "ratio": float("nan"), "pass": False}

    def _rs(val):
        v = str(val)
        if "ผ่าน" in v:  return "color:#00ff41;font-weight:700;"
        if "ไม่ผ่าน" in v: return "color:#ff0040;font-weight:700;"
        return ""

    summary = pd.DataFrame({
        "การตรวจสอบ": ["กำลังดัด", "กำลังเฉือน", "การโก่งตัวรวม", "การโก่งตัวจาก LL"],
        "ค่าที่ต้องรับ": [
            f"{demand['Mu']:.2f} กก.-ม.",
            f"{demand['Vu']:.2f} กก.",
            f"{dt['value']:.3f} ซม.",
            f"{dl_['value']:.3f} ซม.",
        ],
        "ค่ากำลัง/เกณฑ์": [
            f"{capacity['Phi_Mn']:.2f} กก.-ม.",
            f"{capacity['Phi_Vn']:.2f} กก.",
            f"{capacity['Delta_Limit_Total']:.3f} ซม.",
            f"{capacity['Delta_Limit_Live']:.3f} ซม.",
        ],
        "อัตราส่วน": [ratios["Moment"], ratios["Shear"], dt["ratio"], dl_["ratio"]],
        "ผล": [
            "✅ ผ่าน" if checks["Moment"] else "❌ ไม่ผ่าน",
            "✅ ผ่าน" if checks["Shear"]  else "❌ ไม่ผ่าน",
            "✅ ผ่าน" if dt["pass"]       else "❌ ไม่ผ่าน",
            "✅ ผ่าน" if dl_["pass"]      else "❌ ไม่ผ่าน",
        ],
    })
    st.dataframe(
        summary.style.format({"อัตราส่วน": "{:.3f}"}).map(_rs, subset=["ผล"]),
        use_container_width=True,
    )

    # ── Calculation Steps ─────────────────────────────────────
    with st.expander("📝 ขั้นตอนการคำนวณแบบละเอียด", expanded=False):
        for step in res["Steps"]:
            icon = "✅" if step.get("status") == "PASS" else ("❌" if step.get("status") == "FAIL" else "ℹ️")
            st.markdown(f"**{icon} {step['title']}**")
            st.latex(step["latex"])
            if step.get("note"):
                st.markdown(f"_{step['note']}_")
            st.divider()

    # ── PDF Report ────────────────────────────────────────────
    st.subheader("📄 รายงานผลคำนวณ")
    with st.expander("ข้อมูลโครงการสำหรับรายงาน"):
        rc1, rc2, rc3 = st.columns(3)
        p_name  = rc1.text_input("ชื่อโครงการ",      "New Warehouse",  key="rf_pname")
        p_owner = rc2.text_input("เจ้าของโครงการ",   "Client A",       key="rf_powner")
        p_eng   = rc3.text_input("วิศวกรผู้ออกแบบ",  "Eng. Sarayut",   key="rf_peng")

    if st.button("สร้างรายงาน PDF", key="rf_pdf"):
        from report_generator import RafterReportGenerator
        proj_info = {"Project Name": p_name, "Owner": p_owner, "Engineer": p_eng}
        inputs    = {"geometry": geometry, "loads": load_input, "materials": materials}
        section_data["name"] = section_name
        report = RafterReportGenerator(proj_info, inputs, res, section_data)
        ok_pdf, path_or_err = report.generate("Rafter_Design_Report.pdf")
        if ok_pdf:
            st.success("สร้างรายงานสำเร็จ")
            with open(path_or_err, "rb") as f:
                st.download_button("ดาวน์โหลดรายงาน PDF", f,
                                   "Rafter_Design_Report.pdf", "application/pdf")
        else:
            st.error(f"สร้างรายงานไม่สำเร็จ: {path_or_err}")

import math

import pandas as pd
import streamlit as st

from tension_design import TensionDesign, SHEAR_LAG_TABLE
from theme_manager import use_theme

st.set_page_config(page_title="ออกแบบสมาชิกรับแรงดึง", layout="wide")
use_theme()

st.title("🔩 โมดูลออกแบบสมาชิกรับแรงดึง (Tension Member)")
st.markdown(
    "**อ้างอิง:** AISC 360-16 Chapter D · วิธี LRFD · "
    "ตรวจสอบ Yielding (Gross Section) + Net Section Fracture + Shear Lag"
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# โหลดข้อมูลหน้าตัดเหล็ก
# ─────────────────────────────────────────────────────────────
DATA_HR  = "tis_1227_steel.csv"
DATA_CF  = "Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv"


@st.cache_data
def _load_hr():
    if pd.io.common.file_exists(DATA_HR):
        return pd.read_csv(DATA_HR)
    return pd.DataFrame()


@st.cache_data
def _load_cf():
    from data_utils import load_data
    return load_data(DATA_CF)


df_hr = _load_hr()
df_cf = _load_cf()

# ─────────────────────────────────────────────────────────────
# ข้อมูลโครงการ
# ─────────────────────────────────────────────────────────────
with st.expander("📝 ข้อมูลโครงการ", expanded=False):
    pi1, pi2, pi3 = st.columns(3)
    project_name = pi1.text_input("ชื่อโครงการ", "Building A", key="tn_proj")
    owner        = pi2.text_input("เจ้าของโครงการ", "Customer X", key="tn_owner")
    engineer     = pi3.text_input("วิศวกรผู้คำนวณ", "Eng. Sarayut", key="tn_eng")

# ─────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────
col_in, col_out = st.columns([1, 2])

# ═════════════════════════════════════════
# INPUT COLUMN
# ═════════════════════════════════════════
with col_in:
    st.header("กำหนดพารามิเตอร์")

    # ── 1. หน้าตัดเหล็ก ──────────────────
    st.subheader("1. หน้าตัดเหล็ก")
    input_mode = st.radio(
        "วิธีระบุหน้าตัด",
        ["H-Beam มอก. 1227 (รีดร้อน)", "C-Channel มอก. 1228 (ขึ้นรูปเย็น)", "ป้อนค่าเอง"],
        key="tn_mode",
    )

    if input_mode == "H-Beam มอก. 1227 (รีดร้อน)":
        if df_hr.empty:
            st.error("ไม่พบไฟล์ tis_1227_steel.csv")
            st.stop()
        sec_name = st.selectbox("เลือกหน้าตัด H-Beam", df_hr["Section"].astype(str).unique(), key="tn_hr_sec")
        row  = df_hr[df_hr["Section"] == sec_name].iloc[0]
        Ag_v = float(row.get("Area", 0))
        Ix_v = float(row.get("Ix",   0))
        ry_v = float(row.get("ry",   0))
        r_min_v = ry_v  # ry เป็นรัศมีไจเรชันน้อยที่สุดของ H-Beam
        t_el_v  = float(row.get("tf", 0)) / 10.0  # mm→cm (ใช้ tf สำหรับ bolt hole calc)

        prop_df = pd.DataFrame({
            "คุณสมบัติ": ["น้ำหนัก (kg/m)", "Ag (cm²)", "Ix (cm⁴)", "ry (cm)", "tf (mm)"],
            "ค่า":        [f"{float(row.get('Weight',0)):.2f}", f"{Ag_v:.3f}",
                           f"{Ix_v:.1f}", f"{ry_v:.3f}", f"{float(row.get('tf',0)):.1f}"],
        })
        st.dataframe(prop_df, hide_index=True, use_container_width=True)

    elif input_mode == "C-Channel มอก. 1228 (ขึ้นรูปเย็น)":
        if df_cf.empty:
            st.error("ไม่พบข้อมูลหน้าตัด มอก. 1228")
            st.stop()
        sec_name = st.selectbox("เลือกหน้าตัด C-Channel", df_cf["Section"].astype(str).unique(), key="tn_cf_sec")
        row  = df_cf[df_cf["Section"] == sec_name].iloc[0]
        Ag_v = float(row.get("Area", 0))
        Ix_v = float(row.get("Ix",   0))
        h_mm = float(row.get("h",  100))
        t_mm = float(row.get("t",  2.0))
        # ประมาณ ry สำหรับ Lip-C: ry ≈ 0.28 × b (rough estimate)
        # ใช้ข้อมูลที่มีอยู่ — คำนวณ ry จาก: สำหรับ C-channel ry ≈ sqrt(Iy/Ag)
        # เนื่องจาก Iy ไม่มีในไฟล์ CSV ให้ประมาณจาก geometry
        # ry_approx = t_mm * sqrt(h_mm/t_mm / 12) ≈ h / (2√3 * aspect) ... rough
        # ใช้ r_min = t / sqrt(3) as lower bound for thin plates (very conservative)
        r_min_v = t_mm / (math.sqrt(3) * 10.0)  # mm→cm, conservative
        t_el_v  = t_mm / 10.0  # mm→cm

        st.warning(
            f"⚠️ สำหรับ C-Channel มอก.1228 ค่า r_min ถูกประมาณเบื้องต้น "
            f"(r_min ≈ {r_min_v:.4f} cm) แนะนำให้ป้อนค่า r_min ที่ถูกต้องด้วย 'ป้อนค่าเอง'"
        )
        prop_df = pd.DataFrame({
            "คุณสมบัติ": ["น้ำหนัก (kg/m)", "Ag (cm²)", "Ix (cm⁴)", "h (mm)", "t (mm)"],
            "ค่า":        [f"{float(row.get('Weight',0)):.2f}", f"{Ag_v:.3f}",
                           f"{Ix_v:.1f}", f"{h_mm:.1f}", f"{t_mm:.1f}"],
        })
        st.dataframe(prop_df, hide_index=True, use_container_width=True)

    else:  # Manual
        sec_name = st.text_input("ชื่อหน้าตัด", "Custom Tension Member", key="tn_sec_name")
        c1m, c2m = st.columns(2)
        Ag_v    = c1m.number_input("Ag (cm²)",    value=15.0, step=0.5, key="tn_Ag")
        r_min_v = c1m.number_input("r_min (cm)",  value=1.5,  step=0.1, key="tn_rmin")
        t_el_v  = c2m.number_input("ความหนาองค์ประกอบ t (cm)", value=0.7, step=0.05, key="tn_tel")

    # ── 2. วัสดุ ─────────────────────────
    st.subheader("2. วัสดุ")
    grade_map = {
        "SS400  (Fy=2,500 ksc / Fu=4,080 ksc)":  (2500.0, 4080.0),
        "SM490  (Fy=3,313 ksc / Fu=4,894 ksc)":  (3313.0, 4894.0),
        "SSC400 มอก.1228 (Fy=2,450 ksc / Fu=4,080 ksc)": (2450.0, 4080.0),
        "กำหนดเอง": (0.0, 0.0),
    }
    grade_sel = st.selectbox("เกรดเหล็ก", list(grade_map.keys()), key="tn_grade")
    fy_def, fu_def = grade_map[grade_sel]
    if grade_sel == "กำหนดเอง":
        g1, g2 = st.columns(2)
        fy_v = g1.number_input("Fy (ksc)", value=2500.0, step=50.0, key="tn_fy_c")
        fu_v = g2.number_input("Fu (ksc)", value=4080.0, step=50.0, key="tn_fu_c")
    else:
        fy_v, fu_v = fy_def, fu_def
        st.info(f"Fy = {fy_v:,.0f} ksc  |  Fu = {fu_v:,.0f} ksc")
    E_v = st.number_input("E (ksc)", value=2.04e6, format="%.3e", key="tn_E")

    # ── 3. ความยาวสมาชิก ─────────────────
    st.subheader("3. ความยาวสมาชิก")
    L_v = st.number_input("ความยาว L (เมตร)", value=3.0, step=0.5, key="tn_L")

    # ── 4. รายละเอียดการต่อ ──────────────
    st.subheader("4. รายละเอียดการต่อ (Connection)")
    conn_type = st.radio(
        "ชนิดการต่อ", ["การเชื่อม (Welded)", "สลักเกลียว (Bolted)"],
        horizontal=True, key="tn_conn",
    )
    is_bolted = conn_type == "สลักเกลียว (Bolted)"

    # Shear Lag Factor U
    u_labels = {k: v[1] for k, v in SHEAR_LAG_TABLE.items()}
    u_sel = st.selectbox("Shear Lag Factor U", list(u_labels.keys()),
                         format_func=lambda k: u_labels[k], key="tn_u_sel")

    if u_sel == "custom":
        U_cust = st.number_input("ระบุค่า U (0 ≤ U ≤ 1)", value=0.85, min_value=0.0,
                                 max_value=1.0, step=0.01, key="tn_u_val")
    else:
        U_cust = SHEAR_LAG_TABLE[u_sel][0] or 0.85

    # Bolt details (แสดงเฉพาะเมื่อต่อด้วยสลัก)
    if is_bolted:
        st.markdown("**รายละเอียดสลักเกลียว**")
        b1, b2, b3 = st.columns(3)
        n_lines_v  = b1.number_input("แนวรูที่ตัดหน้าตัดวิกฤติ", value=1, min_value=1, step=1, key="tn_nlines")
        bolt_d_mm  = b2.number_input("∅ สลัก (มม.)", value=16.0, step=2.0, key="tn_boltd")
        bolt_d_cm  = bolt_d_mm / 10.0
        b3.metric("∅ รู (มม.)", f"{bolt_d_mm + 3.2:.1f}")
    else:
        n_lines_v = 1
        bolt_d_cm = 2.0

    # ── 5. แรงประลัย ─────────────────────
    st.subheader("5. แรงดึงประลัย Tu")
    tu_unit = st.radio("หน่วยแรง", ["ตัน (ton)", "กิโลกรัม (kg)"], horizontal=True, key="tn_tu_unit")
    if tu_unit == "ตัน (ton)":
        tu_in = st.number_input("Tu (ตัน)", value=30.0, step=5.0, key="tn_tu_ton")
        Tu_v  = tu_in * 1000.0
        st.caption(f"= {Tu_v:,.0f} กก.")
    else:
        Tu_v = st.number_input("Tu (กก.)", value=30000.0, step=1000.0, key="tn_tu_kg")

    st.divider()
    live_calc = st.checkbox("🔴 Live Calculation", value=True, key="tn_live")

# ═════════════════════════════════════════
# OUTPUT COLUMN
# ═════════════════════════════════════════
with col_out:
    st.header("ผลการคำนวณ")

    should_calc = live_calc
    if not live_calc:
        should_calc = st.button("เริ่มคำนวณ", type="primary", key="tn_btn")

    if should_calc:
        try:
            designer = TensionDesign(
                section_name=sec_name,
                Ag=Ag_v, r_min=r_min_v,
                Fy=fy_v, Fu=fu_v, E=E_v,
                L=L_v,
                connection_type="bolted" if is_bolted else "welded",
                U_key=u_sel,
                U_custom=U_cust,
                n_bolt_lines=n_lines_v,
                bolt_diameter=bolt_d_cm,
                t_element=t_el_v,
                Tu=Tu_v,
            )
            res = designer.run_design()
        except Exception as exc:
            st.error(f"เกิดข้อผิดพลาด: {exc}")
            st.stop()

        slen  = res["Slenderness"]
        na    = res["NetArea"]
        cap   = res["Capacity"]
        ratio = res["Ratio"]
        ok    = res["Status"]

        # ── Status Cards ─────────────────
        st.markdown(f"**หน้าตัด:** `{sec_name}`")
        m1, m2, m3 = st.columns(3)

        def _card(col, emoji, label, value, sub, css_cls):
            col.markdown(
                f"""<div style="text-align:center;">
                    <div style="font-size:2.8rem;">{emoji}</div>
                    <div style="font-size:0.85rem;color:var(--text-muted,#737373);">{label}</div>
                    <div style="font-size:1.9rem;font-weight:700;" class="{css_cls}">{value}</div>
                    <div style="font-size:0.75rem;color:var(--text-muted,#737373);">{sub}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        s_ok   = slen["OK"]
        tens_ok = ok

        # L/r
        lr_val = f"{slen['L_r']:.1f}" if slen["r_min"] > 0 else "N/A"
        _card(m1,
              "✅" if s_ok else "⚠️",
              "ความชะลูด L/r",
              lr_val, "≤ 300 (แนะนำ)",
              "status-pass" if s_ok else "status-warning")

        # Ae / Ag
        ae_ratio = na["Ae"] / Ag_v if Ag_v > 0 else 0
        _card(m2,
              "✅",
              "Ae / Ag (Net Ratio)",
              f"{ae_ratio:.3f}",
              f"U={na['U']:.2f}",
              "status-pass")

        # Tu / φtTn
        _card(m3,
              "✅" if tens_ok else "❌",
              "Tu / φtTn",
              f"{ratio:.3f}",
              "ผ่าน" if tens_ok else "ไม่ผ่าน",
              "status-pass" if tens_ok else "status-fail")

        # ── Key Metrics ──────────────────
        st.markdown("---")
        km1, km2, km3, km4 = st.columns(4)
        km1.metric("φtTn (ตัน)",          f"{cap['phi_Tn']/1000:.2f}")
        km2.metric("Yielding φtTn (ตัน)", f"{cap['phi_Tn_yield']/1000:.2f}")
        km3.metric("Fracture φtTn (ตัน)", f"{cap['phi_Tn_fracture']/1000:.2f}")
        km4.metric("Ae (cm²)",            f"{na['Ae']:.3f}")

        # ── Summary Table ────────────────
        st.subheader("📊 ตารางสรุปผลการออกแบบ")

        def _res_style(val):
            v = str(val)
            if ("ผ่าน" in v or "OK" in v) and "ไม่" not in v:
                return "color:#22c55e;font-weight:700;"
            if "ไม่ผ่าน" in v or "เกิน" in v or "FAIL" in v:
                return "color:#ef4444;font-weight:700;"
            return ""

        ctrl_lbl = cap["Controlling"]
        summary = pd.DataFrame({
            "สภาวะขีดจำกัด": [
                "ความชะลูด L/r (แนะนำ ≤ 300)",
                "พื้นที่สุทธิ An / Ae",
                "การคราก: φtFyAg",
                "การแตกหัก: φtFuAe",
                f"กำลังออกแบบ φtTn ({ctrl_lbl[:20]})",
            ],
            "ค่าที่คำนวณ": [
                f"{slen['L_r']:.2f}" if slen["r_min"] > 0 else "ไม่ระบุ",
                f"An={na['An']:.4f} cm²  |  Ae={na['Ae']:.4f} cm²  |  U={na['U']:.3f}",
                f"{cap['phi_Tn_yield']:,.0f} กก.",
                f"{cap['phi_Tn_fracture']:,.0f} กก.",
                f"Tu = {Tu_v:,.0f} กก.",
            ],
            "เกณฑ์ / กำลัง": [
                "≤ 300",
                f"Ag = {Ag_v:.4f} cm²",
                f"φt=0.90, Fy={fy_v:.0f} ksc",
                f"φt=0.75, Fu={fu_v:.0f} ksc",
                f"φtTn = {cap['phi_Tn']:,.0f} กก.",
            ],
            "อัตราส่วน": [
                f"{slen['L_r']/300:.3f}" if slen["r_min"] > 0 else "-",
                f"{ae_ratio:.3f}",
                f"{Tu_v/cap['phi_Tn_yield']:.3f}",
                f"{Tu_v/cap['phi_Tn_fracture']:.3f}",
                f"{ratio:.3f}",
            ],
            "ผล": [
                "✅ OK" if s_ok else "⚠️ เกินข้อแนะนำ",
                "-",
                "✅ ผ่าน" if Tu_v <= cap["phi_Tn_yield"] else "❌ ไม่ผ่าน",
                "✅ ผ่าน" if Tu_v <= cap["phi_Tn_fracture"] else "❌ ไม่ผ่าน",
                "✅ ผ่าน" if tens_ok else "❌ ไม่ผ่าน",
            ],
        })

        styled = summary.style.map(_res_style, subset=["ผล"])
        st.dataframe(styled, use_container_width=True)

        # ── Calculation Steps ────────────
        with st.expander("📝 ขั้นตอนการคำนวณแบบละเอียด (Step-by-Step)", expanded=True):
            for step in res["Steps"]:
                status = step.get("status")
                icon   = ("✅" if status == "PASS"
                          else "❌" if status == "FAIL"
                          else "⚠️" if status == "WARN"
                          else "ℹ️")
                st.markdown(f"**{icon} {step['title']}**")
                st.latex(step["latex"])
                if step.get("note"):
                    st.markdown(f"_{step['note']}_")
                st.markdown("---")

        # ── ตารางอ้างอิง Shear Lag U ─────
        with st.expander("📖 ตารางอ้างอิง Shear Lag Factor U (AISC 360-16 Table D3.1)", expanded=False):
            u_ref = pd.DataFrame([
                {"สถานการณ์": v[1], "U": f"{v[0]:.2f}" if v[0] else "คำนวณ"}
                for v in SHEAR_LAG_TABLE.values()
            ])
            st.dataframe(u_ref, hide_index=True, use_container_width=True)
            st.markdown(
                "**หมายเหตุ:** ทางเลือก — ใช้สูตร `U = 1 − x̄/L` "
                "โดย x̄ = ระยะ eccentricity ของหน้าตัดย่อย, L = ความยาวการต่อ"
            )

        # ── ข้อสรุป ──────────────────────
        st.subheader("📋 ข้อสรุปและคำแนะนำ")
        if tens_ok and s_ok:
            st.success(
                f"✅ หน้าตัด **{sec_name}** ผ่านการออกแบบ — "
                f"Tu/φtTn = {ratio:.3f} "
                f"(φtTn = {cap['phi_Tn']/1000:.2f} ตัน, ควบคุมโดย{ctrl_lbl})"
            )
        elif not tens_ok:
            st.error(
                f"❌ หน้าตัด **{sec_name}** ไม่ผ่าน — "
                f"Tu/φtTn = {ratio:.3f} > 1.0 "
                f"กรุณาเลือกหน้าตัดที่มีกำลังมากกว่า {Tu_v/1000:.1f} ตัน"
            )
        if not s_ok:
            st.warning(
                f"⚠️ L/r = {slen['L_r']:.1f} > 300 — "
                "เกินข้อแนะนำ AISC 360-16 Sec. D1 "
                "พิจารณาเพิ่มค้ำยันกลางช่วงหรือเลือกหน้าตัดที่มี r ใหญ่กว่า"
            )

        st.info(
            "📌 **หมายเหตุ:** การก่อสร้างจริงต้องได้รับการตรวจสอบและลงนามรับรอง "
            "โดยวิศวกรที่ได้รับใบอนุญาต (สามัญวิศวกร/วุฒิวิศวกร) "
            "ตาม พ.ร.บ. วิชาชีพวิศวกรรม พ.ศ. 2542"
        )

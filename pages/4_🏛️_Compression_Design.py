import math

import pandas as pd
import streamlit as st

from compression_design import CompressionDesign
from theme_manager import use_theme

st.set_page_config(page_title="ออกแบบสมาชิกรับแรงอัด", layout="wide")
use_theme()

st.title("🏛️ โมดูลออกแบบสมาชิกรับแรงอัด (Compression Member)")
st.markdown(
    "**อ้างอิง:** AISC 360-16 Chapter E · วิธี LRFD · "
    "ตรวจสอบ Flexural Buckling + Local Buckling (Q-factor)"
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# โหลดข้อมูลหน้าตัดเหล็กรีดร้อน มอก. 1227
# ─────────────────────────────────────────────────────────────
DATA_HR = "tis_1227_steel.csv"


@st.cache_data
def _load_hr():
    if pd.io.common.file_exists(DATA_HR):
        return pd.read_csv(DATA_HR)
    return pd.DataFrame()


df_hr = _load_hr()

# ─────────────────────────────────────────────────────────────
# ข้อมูลโครงการ
# ─────────────────────────────────────────────────────────────
with st.expander("📝 ข้อมูลโครงการ", expanded=False):
    pi1, pi2, pi3 = st.columns(3)
    project_name = pi1.text_input("ชื่อโครงการ", "Building A", key="cp_proj")
    owner        = pi2.text_input("เจ้าของโครงการ", "Customer X", key="cp_owner")
    engineer     = pi3.text_input("วิศวกรผู้คำนวณ", "Eng. Sarayut", key="cp_eng")

# ─────────────────────────────────────────────────────────────
# Layout: Input (ซ้าย) | Results (ขวา)
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
        ["เลือกจาก มอก. 1227 (H-Beam)", "ป้อนค่าเอง (Manual Input)"],
        horizontal=True, key="cp_mode",
    )

    if input_mode == "เลือกจาก มอก. 1227 (H-Beam)":
        if df_hr.empty:
            st.error("ไม่พบไฟล์ tis_1227_steel.csv กรุณาตรวจสอบ")
            st.stop()
        sec_name = st.selectbox(
            "เลือกหน้าตัด H-Beam", df_hr["Section"].astype(str).unique(), key="cp_sec"
        )
        row = df_hr[df_hr["Section"] == sec_name].iloc[0]
        Ag_v  = float(row.get("Area", 0))
        Ix_v  = float(row.get("Ix",   0))
        ry_v  = float(row.get("ry",   0))
        rx_v  = math.sqrt(Ix_v / Ag_v) if Ag_v > 0 else 0.0
        h_v   = float(row.get("h",   0))
        bf_v  = float(row.get("b",   0))
        tw_v  = float(row.get("tw",  0))
        tf_v  = float(row.get("tf",  0))
        wt_v  = float(row.get("Weight", 0))
        Iy_v  = float(row.get("Iy",  0))

        # ตารางสรุปหน้าตัด
        st.markdown(f"**หน้าตัดที่เลือก: {sec_name}**")
        prop_df = pd.DataFrame({
            "คุณสมบัติ": ["น้ำหนัก (kg/m)", "Ag (cm²)", "Ix (cm⁴)", "Iy (cm⁴)",
                          "rx (cm)", "ry (cm)", "h (mm)", "bf (mm)", "tw (mm)", "tf (mm)"],
            "ค่า":        [f"{wt_v:.2f}", f"{Ag_v:.3f}", f"{Ix_v:.1f}", f"{Iy_v:.1f}",
                           f"{rx_v:.3f}", f"{ry_v:.3f}", f"{h_v:.1f}",  f"{bf_v:.1f}",
                           f"{tw_v:.1f}", f"{tf_v:.1f}"],
        })
        st.dataframe(prop_df, hide_index=True, use_container_width=True)

    else:  # Manual Input
        sec_name = st.text_input("ชื่อหน้าตัด", "Custom Column", key="cp_sec_name")
        c1m, c2m = st.columns(2)
        Ag_v  = c1m.number_input("Ag (cm²)",  value=20.0,  step=0.5,  key="cp_Ag")
        rx_v  = c1m.number_input("rx (cm)",   value=5.0,   step=0.1,  key="cp_rx")
        ry_v  = c1m.number_input("ry (cm)",   value=2.5,   step=0.1,  key="cp_ry")
        h_v   = c2m.number_input("h  (mm)",   value=200.0, step=5.0,  key="cp_h")
        bf_v  = c2m.number_input("bf (mm)",   value=100.0, step=5.0,  key="cp_bf")
        tw_v  = c2m.number_input("tw (mm)",   value=6.0,   step=0.5,  key="cp_tw")
        tf_v  = c2m.number_input("tf (mm)",   value=9.0,   step=0.5,  key="cp_tf")

    # ── 2. วัสดุ ─────────────────────────
    st.subheader("2. วัสดุ")
    grade_map = {
        "SS400  (Fy = 2,500 ksc / 245 MPa)":  (2500.0, 4080.0),
        "SM490  (Fy = 3,313 ksc / 325 MPa)":  (3313.0, 4894.0),
        "SM570  (Fy = 4,587 ksc / 450 MPa)":  (4587.0, 5709.0),
        "กำหนดเอง": (0.0, 0.0),
    }
    grade_sel = st.selectbox("เกรดเหล็ก", list(grade_map.keys()), key="cp_grade")
    fy_def, fu_def = grade_map[grade_sel]
    if grade_sel == "กำหนดเอง":
        fy_v = st.number_input("Fy (ksc)", value=2500.0, step=50.0, key="cp_fy_c")
    else:
        fy_v = fy_def
        st.info(f"Fy = {fy_v:,.0f} ksc")
    E_v = st.number_input("E (ksc)", value=2.04e6, format="%.3e", key="cp_E")

    # ── 3. เรขาคณิตเสา ──────────────────
    st.subheader("3. เรขาคณิตเสา")

    k_map = {
        "Pin–Pin  (K = 1.00)":       1.00,
        "Fixed–Pin  (K = 0.70)":     0.70,
        "Fixed–Fixed  (K = 0.50)":   0.50,
        "Fixed–Free / Cantilever  (K = 2.00)": 2.00,
        "กำหนดเอง": 0.0,
    }

    col_lk1, col_lk2 = st.columns(2)
    with col_lk1:
        st.markdown("**แกน x-x**")
        Lx_v   = st.number_input("Lx (m)", value=3.0, step=0.5, key="cp_Lx")
        kx_sel = st.selectbox("เงื่อนไขขอบ Kx", list(k_map.keys()), key="cp_kx_s")
        Kx_v   = st.number_input("Kx", value=k_map[kx_sel] if kx_sel != "กำหนดเอง" else 1.0,
                                  step=0.05, key="cp_kx_v") if kx_sel == "กำหนดเอง" \
                 else k_map[kx_sel]
        if kx_sel != "กำหนดเอง":
            st.info(f"Kx = {Kx_v:.2f}")

    with col_lk2:
        st.markdown("**แกน y-y**")
        Ly_v   = st.number_input("Ly (m)", value=3.0, step=0.5, key="cp_Ly")
        ky_sel = st.selectbox("เงื่อนไขขอบ Ky", list(k_map.keys()), key="cp_ky_s")
        Ky_v   = st.number_input("Ky", value=k_map[ky_sel] if ky_sel != "กำหนดเอง" else 1.0,
                                  step=0.05, key="cp_ky_v") if ky_sel == "กำหนดเอง" \
                 else k_map[ky_sel]
        if ky_sel != "กำหนดเอง":
            st.info(f"Ky = {Ky_v:.2f}")

    # ── 4. แรงประลัย ─────────────────────
    st.subheader("4. แรงอัดประลัย Pu")
    pu_unit = st.radio("หน่วยแรง", ["ตัน (ton)", "กิโลกรัม (kg)"], horizontal=True, key="cp_pu_unit")
    if pu_unit == "ตัน (ton)":
        pu_in = st.number_input("Pu (ตัน)", value=50.0, step=5.0, key="cp_pu_ton")
        Pu_v  = pu_in * 1000.0
        st.caption(f"= {Pu_v:,.0f} กก.")
    else:
        Pu_v = st.number_input("Pu (กก.)", value=50000.0, step=1000.0, key="cp_pu_kg")

    st.divider()
    live_calc = st.checkbox("🔴 Live Calculation", value=True, key="cp_live")

# ═════════════════════════════════════════
# OUTPUT COLUMN
# ═════════════════════════════════════════
with col_out:
    st.header("ผลการคำนวณ")

    should_calc = live_calc
    if not live_calc:
        should_calc = st.button("เริ่มคำนวณ", type="primary", key="cp_btn")

    if should_calc:
        try:
            designer = CompressionDesign(
                section_name=sec_name,
                Ag=Ag_v, rx=rx_v, ry=ry_v,
                h=h_v, bf=bf_v, tw=tw_v, tf=tf_v,
                Fy=fy_v, E=E_v,
                Lx=Lx_v, Ly=Ly_v,
                Kx=Kx_v, Ky=Ky_v,
                Pu=Pu_v,
            )
            res = designer.run_design()
        except Exception as exc:
            st.error(f"เกิดข้อผิดพลาด: {exc}")
            st.stop()

        slen  = res["Slenderness"]
        lb    = res["LocalBuckling"]
        buck  = res["Buckling"]
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

        # KL/r
        s_ok = slen["OK"]
        _card(m1,
              "✅" if s_ok else "⚠️",
              "ความชะลูด KL/r",
              f"{slen['KL_r']:.1f}",
              f"แกน {slen['Governing']} · ≤ 200",
              "status-pass" if s_ok else "status-warning")

        # Q (Local Buckling)
        lb_ok = lb["OK"]
        _card(m2,
              "✅" if lb_ok else "⚠️",
              "Local Buckling Q",
              f"{lb['Q']:.3f}",
              "Non-slender" if lb_ok else "มีองค์ประกอบชะลูด",
              "status-pass" if lb_ok else "status-warning")

        # Pu / φcPn
        _card(m3,
              "✅" if ok else "❌",
              "Pu / φcPn",
              f"{ratio:.3f}",
              "ผ่าน" if ok else "ไม่ผ่าน",
              "status-pass" if ok else "status-fail")

        # ── Key Metrics ──────────────────
        st.markdown("---")
        km1, km2, km3, km4 = st.columns(4)
        km1.metric("φcPn (ตัน)", f"{cap['phi_Pn']/1000:.2f}")
        km2.metric("Pn  (ตัน)",  f"{cap['Pn']/1000:.2f}")
        km3.metric("Fcr (ksc)",  f"{buck['Fcr']:.0f}")
        km4.metric("Fe  (ksc)",  f"{buck['Fe']:.0f}")

        # ── Summary Table ────────────────
        st.subheader("📊 ตารางสรุปผลการออกแบบ")

        def _res_style(val):
            v = str(val)
            if ("ผ่าน" in v or "OK" in v) and "ไม่" not in v:
                return "color:#22c55e;font-weight:700;"
            if "ไม่ผ่าน" in v or "เกิน" in v or "FAIL" in v:
                return "color:#ef4444;font-weight:700;"
            return ""

        summary = pd.DataFrame({
            "รายการตรวจสอบ": [
                "ความชะลูด KL/r (แนะนำ ≤ 200)",
                "Local Buckling Q",
                f"โก่งเดาะ: {buck['Mode'][:30]}",
                "กำลังรับแรงอัด Pu ≤ φcPn",
            ],
            "ค่าที่คำนวณ": [
                f"{slen['KL_r']:.2f}  (แกน {slen['Governing']})",
                f"Qs={lb['Qs']:.3f}, Qa={lb['Qa']:.3f}, Q={lb['Q']:.3f}",
                f"Fe = {buck['Fe']:.0f} ksc, Fcr = {buck['Fcr']:.0f} ksc",
                f"Pu = {Pu_v:,.0f} กก.",
            ],
            "เกณฑ์ / กำลัง": [
                "≤ 200",
                "Q = 1.0 (ไม่ชะลูด)",
                f"φcPn = {cap['phi_Pn']:,.0f} กก.",
                f"φcPn = {cap['phi_Pn']:,.0f} กก.",
            ],
            "อัตราส่วน": [
                f"{slen['KL_r']/200:.3f}",
                f"{lb['Q']:.3f}",
                "-",
                f"{ratio:.3f}",
            ],
            "ผล": [
                "✅ OK" if s_ok else "⚠️ เกินข้อแนะนำ",
                "✅ Non-slender" if lb_ok else "⚠️ มีองค์ประกอบชะลูด",
                "-",
                "✅ ผ่าน" if ok else "❌ ไม่ผ่าน",
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

        # ── ข้อสรุปและคำแนะนำ ──────────
        st.subheader("📋 ข้อสรุปและคำแนะนำ")
        if ok and s_ok:
            st.success(
                f"✅ หน้าตัด **{sec_name}** ผ่านการออกแบบ — "
                f"อัตราส่วน Pu/φcPn = {ratio:.3f} "
                f"(φcPn = {cap['phi_Pn']/1000:.2f} ตัน)"
            )
        elif not ok:
            st.error(
                f"❌ หน้าตัด **{sec_name}** ไม่ผ่าน — "
                f"Pu/φcPn = {ratio:.3f} > 1.0 "
                f"กรุณาเลือกหน้าตัดที่มีกำลังมากกว่า {Pu_v/1000:.1f} ตัน"
            )
        if not s_ok:
            st.warning(
                f"⚠️ KL/r = {slen['KL_r']:.1f} > 200 — "
                "เกินข้อแนะนำ AISC Table C-A-7.1 "
                "พิจารณาเพิ่มค้ำยันกลางช่วงหรือเปลี่ยนหน้าตัดที่มี r ใหญ่กว่า"
            )
        if not lb_ok:
            st.warning(
                f"⚠️ มีองค์ประกอบชะลูด Q = {lb['Q']:.3f} — "
                "กำลังรับแรงอัดถูกลดทอนด้วยตัวคูณ Q แล้ว (AISC 360-16 Sec. E7)"
            )

        st.info(
            "📌 **หมายเหตุ:** การก่อสร้างจริงต้องได้รับการตรวจสอบและลงนามรับรอง "
            "โดยวิศวกรที่ได้รับใบอนุญาต (สามัญวิศวกร/วุฒิวิศวกร) "
            "ตาม พ.ร.บ. วิชาชีพวิศวกรรม พ.ศ. 2542"
        )

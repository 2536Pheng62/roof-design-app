import streamlit as st # type: ignore
import pandas as pd
from data_utils import load_data
from theme_manager import use_theme
from beam_design import ColdFormedBeamDesign

st.set_page_config(page_title="ออกแบบคานเหล็กขึ้นรูปเย็น", layout="wide")
use_theme()

st.title("🏗️ โมดูลออกแบบคาน/อเส เหล็กขึ้นรูปเย็น")
st.caption("อ้างอิง มอก. 1228-2549 และ LRFD Load Combination ของ วสท.")

DATA_FILE = "Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv"


@st.cache_data
def get_sections() -> pd.DataFrame:
	return load_data(DATA_FILE)


sections = get_sections()

required_cols = {"Section", "Zx", "Ix", "Area"}
missing = required_cols - set(sections.columns)
if missing:
	st.error(f"ข้อมูลหน้าตัดขาดคอลัมน์สำคัญ: {', '.join(sorted(missing))}")
	st.stop()


with st.sidebar:
	st.header("กำหนดพารามิเตอร์")
	span = st.number_input("ช่วงพาด L (เมตร)", min_value=0.5, value=6.0, step=0.1, key="beam_span")
	spacing = st.number_input("ระยะแป/จันทัน (เมตร)", min_value=0.1, value=1.0, step=0.1, key="beam_spacing")
	st.markdown("---")
	st.header("น้ำหนักบรรทุก (กก./ม.)")
	dead = st.number_input("น้ำหนักคงที่ D", min_value=0.0, value=150.0, step=5.0, key="beam_dead")
	live = st.number_input("น้ำหนักใช้งาน L", min_value=0.0, value=120.0, step=5.0, key="beam_live")
	wind = st.number_input("แรงลม W", min_value=-200.0, value=60.0, step=5.0,
						  help="ค่าบวก = แรงกด, ค่าลบ = แรงยก", key="beam_wind")
	
	# Live Calculation Toggle
	st.divider()
	live_calc_beam = st.checkbox("🔴 Live Calculation (คำนวณอัตโนมัติ)", value=True, key="live_calc_beam")
	if live_calc_beam:
		st.caption("⚡ กราฟจะอัปเดตทันทีเมื่อแก้ไขค่า")

st.subheader("เลือกหน้าตัดจากมาตรฐาน มอก. 1228-2549")
col_section, col_props = st.columns([1.2, 1.0])

with col_section:
	section_name = st.selectbox("หน้าตัด", sections["Section"].astype(str).unique())

section_row = sections[sections["Section"] == section_name].iloc[0]


def _clean_value(label: str, raw: float) -> float:
	if pd.isna(raw) or raw <= 0:
		st.error(f"ค่าของ {label} สำหรับหน้าตัด {section_name} ไม่ถูกต้อง")
		st.stop()
	return float(raw)


with col_props:
	zx_val = _clean_value('Zx', section_row['Zx'])
	ix_val = _clean_value('Ix', section_row['Ix'])
	area_val = _clean_value('Area', section_row['Area'])
	st.metric("Zx (ซม.^3)", f"{zx_val:.2f}")
	st.metric("Ix (ซม.^4)", f"{ix_val:.2f}")
	st.metric("Area (ตร.ซม.)", f"{area_val:.2f}")

Aw_val = section_row.get("Aw")
if Aw_val is not None and Aw_val > 0:
	st.metric("A_w (ตร.ซม.)", f"{Aw_val:.2f}")


# Auto-calculate if live calculation is enabled, or manual button
should_calculate_beam = live_calc_beam
if not live_calc_beam:
	should_calculate_beam = st.button("เริ่มคำนวณ", type="primary")

if should_calculate_beam:
	section_data = {
		"name": section_name,
		"Zx": float(zx_val),
		"Ix": float(ix_val),
		"Area": float(area_val),
	}

	if Aw_val is not None and Aw_val > 0:
		section_data["Aw"] = float(Aw_val)
	if "Weight" in section_row and not pd.isna(section_row["Weight"]):
		section_data["Weight"] = float(section_row["Weight"])

	design = ColdFormedBeamDesign(
		section=section_data,
		geometry={"span": span, "spacing": spacing},
		loads={"D": dead, "L": live, "W": wind}
	)

	try:
		result = design.run_design()
	except ValueError as err:
		st.error(str(err))
		st.stop()

	status = result["Checks"]["Status"]
	ratios = result["Checks"]["Ratios"]

	all_pass_beam = all(status.values())
	overall_emoji_b = "✅" if all_pass_beam else "❌"
	st.markdown(f'<div style="text-align: center; font-size: 4rem;">{overall_emoji_b}</div>', unsafe_allow_html=True)
	if all_pass_beam:
		st.markdown('<div class="status-pass" style="text-align: center; font-size: 1.5rem; font-weight: 700;">ผ่านทุกเกณฑ์การออกแบบ</div>', unsafe_allow_html=True)
	else:
		st.markdown('<div class="status-fail" style="text-align: center; font-size: 1.5rem; font-weight: 700;">มีรายการไม่ผ่านเงื่อนไข</div>', unsafe_allow_html=True)

	m1, m2, m3 = st.columns(3)
	
	# Moment
	moment_emoji_b = "✅" if status['Moment'] else ("⚠️" if ratios['Moment'] > 0.8 else "❌")
	moment_class_b = "status-pass" if status['Moment'] else ("status-warning" if ratios['Moment'] > 0.8 else "status-fail")
	m1.markdown(f"""
	<div style="text-align: center;">
		<div style="font-size: 3rem;">{moment_emoji_b}</div>
		<div style="font-size: 0.9rem; color: #b0b0b0;">กำลังดัด</div>
		<div style="font-size: 2rem; font-weight: 700;" class="{moment_class_b}">{ratios['Moment']:.2f}</div>
	</div>
	""", unsafe_allow_html=True)
	
	# Shear
	shear_emoji_b = "✅" if status['Shear'] else ("⚠️" if ratios['Shear'] > 0.8 else "❌")
	shear_class_b = "status-pass" if status['Shear'] else ("status-warning" if ratios['Shear'] > 0.8 else "status-fail")
	m2.markdown(f"""
	<div style="text-align: center;">
		<div style="font-size: 3rem;">{shear_emoji_b}</div>
		<div style="font-size: 0.9rem; color: #b0b0b0;">กำลังเฉือน</div>
		<div style="font-size: 2rem; font-weight: 700;" class="{shear_class_b}">{ratios['Shear']:.2f}</div>
	</div>
	""", unsafe_allow_html=True)
	
	# Deflection
	defl_emoji_b = "✅" if status['Deflection'] else ("⚠️" if ratios['Deflection'] > 0.8 else "❌")
	defl_class_b = "status-pass" if status['Deflection'] else ("status-warning" if ratios['Deflection'] > 0.8 else "status-fail")
	m3.markdown(f"""
	<div style="text-align: center;">
		<div style="font-size: 3rem;">{defl_emoji_b}</div>
		<div style="font-size: 0.9rem; color: #b0b0b0;">การโก่งตัว</div>
		<div style="font-size: 2rem; font-weight: 700;" class="{defl_class_b}">{ratios['Deflection']:.2f}</div>
	</div>
	""", unsafe_allow_html=True)
	m1.metric("อัตราส่วนโมเมนต์", f"{ratios['Moment']:.2f}",
			  delta="PASS" if status["Moment"] else "FAIL",
			  delta_color="inverse" if status["Moment"] else "normal")
	m2.metric("อัตราส่วนเฉือน", f"{ratios['Shear']:.2f}",
			  delta="PASS" if status["Shear"] else "FAIL",
			  delta_color="inverse" if status["Shear"] else "normal")
	m3.metric("อัตราส่วนการโก่งตัว", f"{ratios['Deflection']:.2f}",
			  delta="PASS" if status["Deflection"] else "FAIL",
			  delta_color="inverse" if status["Deflection"] else "normal")

	st.markdown("---")
	st.markdown(f"**กรณีโหลดที่ควบคุม:** {result['Checks']['Controlling_Load']}")

	demands = result["Checks"]["Demand"]
	capacity = result["Checks"]["Capacity"]

	st.subheader("เปรียบเทียบค่ากำลัง")
	summary_df = pd.DataFrame({
		"การตรวจสอบ": ["โมเมนต์", "แรงเฉือน", "การโก่งตัว"],
		"ค่าที่ต้องรับ": [f"{demands['Mu']:.2f} กก.-ม.", f"{demands['Vu']:.2f} กก.", f"{demands['Delta']:.3f} ซม."],
		"ค่ากำลัง/เกณฑ์": [f"{capacity['Phi_Mn']:.2f} กก.-ม.", f"{capacity['Phi_Vn']:.2f} กก.", f"{capacity['Delta_Limit']:.3f} ซม."],
		"อัตราส่วน": [ratios['Moment'], ratios['Shear'], ratios['Deflection']],
		"ผล": ["ผ่าน" if status['Moment'] else "ไม่ผ่าน",
			   "ผ่าน" if status['Shear'] else "ไม่ผ่าน",
			   "ผ่าน" if status['Deflection'] else "ไม่ผ่าน"]
	})
	st.dataframe(summary_df.style.format({"อัตราส่วน": "{:.2f}"}))

	st.subheader("บันทึกการคำนวณ")
	with st.expander("รายละเอียดขั้นตอน", expanded=True):
		for step in result["Steps"]:
			st.markdown(f"**{step['title']}**")
			st.latex(step['latex'])
			if step['subst'] != "--":
				st.markdown(f"$$ {step['subst']} $$")
			st.markdown(f"**= {step['result']}**")
			st.markdown("---")

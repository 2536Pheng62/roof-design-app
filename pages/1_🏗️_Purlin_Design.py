import streamlit as st
import pandas as pd
from data_utils import load_data, DEFAULT_FILENAME, SteelMaterial
from purlin_design import PurlinDesign

# Page Config
st.set_page_config(
    page_title="Cold-Formed Steel Purlin Design (LRFD)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏗️ Cold-Formed Steel Purlin Design")
st.markdown("**Method:** LRFD (Thai Standards) | **Author:** Antigravity")
st.markdown("---")

# 1. Load Data
# 1. Load Data
# Removed cache to ensure fresh data load and fix potential stale cache issues
def get_data():
    return load_data(DEFAULT_FILENAME)

df = get_data()

if df.empty:
    st.error("Failed to load section data. Please check the CSV file.")
    st.stop()

# 2. Sidebar Inputs
st.sidebar.header("1. Project Information")
proj_name = st.sidebar.text_input("Project Name", "Warehouse A")
owner = st.sidebar.text_input("Owner", "Safe Structures Co.")
engineer = st.sidebar.text_input("Engineer", "Sarayut")

st.sidebar.header("2. Geometry")
spacing = st.sidebar.number_input("Purlin Spacing (m)", value=1.0, step=0.1)
span = st.sidebar.number_input("Rafter Span / Purlin Span (m)", value=4.0, step=0.1)
slope = st.sidebar.number_input("Roof Slope (degrees)", value=5.0, step=0.5)

st.sidebar.header("3. Loads")
dl = st.sidebar.number_input("Dead Load (DL) (kg/m²)", value=10.0, step=1.0, help="Exclude self-weight")
ll = st.sidebar.number_input("Live Load (LL) (kg/m²)", value=30.0, step=1.0)
wl = st.sidebar.number_input("Wind Load (WL) (kg/m²)", value=50.0, step=5.0)

st.sidebar.header("4. Section Selection")
section_name = st.sidebar.selectbox("Select Steel Section", df['Section'].unique())

# Get selected section data
section_data = df[df['Section'] == section_name].iloc[0].to_dict()

st.sidebar.header("5. Material Properties")
# Retrieve material properties using SteelMaterial class
steel_mat = SteelMaterial()
t_val = section_data.get('t', 0.0)
mat_props = steel_mat.get_properties(t_val, unit='ksc')

st.sidebar.info(f"Standard: TIS 1228-2549 (Grade {mat_props['Grade']})")

fy = st.sidebar.number_input("Fy (Yield Strength) (ksc)", value=float(mat_props['Fy']), disabled=True)
e_mod = st.sidebar.number_input("E (Elastic Modulus) (ksc)", value=float(mat_props['E']), disabled=True)

# 3. Calculation
inputs = {
    'geometry': {'spacing': spacing, 'span': span, 'slope': slope},
    'loads': {'DL': dl, 'LL': ll, 'WL': wl},
    'materials': {'Fy': fy, 'E': e_mod}
}

designer = PurlinDesign(section_data, inputs['geometry'], inputs['loads'], inputs['materials'])
results = designer.run_design()

# 4. Display Outputs

# Summary of Inputs (Top)
with st.expander("📝 Input Summary", expanded=False):
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Project:** {proj_name}")
    c2.write(f"**Owner:** {owner}")
    c3.write(f"**Engineer:** {engineer}")
    
    c1.write(f"**Spacing:** {spacing} m")
    c2.write(f"**Span:** {span} m")
    c3.write(f"**Slope:** {slope}°")

# -- Results Container --
st.header("📊 Calculation Results")

# Tabs for better organization
tab1, tab2, tab3 = st.tabs(["Dashboard", "Detailed Analysis", "🖨️ Report"])

with tab1:
    # Section Properties Display
    st.subheader("Selected Section Properties")
    cols = st.columns(len(section_data))
    for i, (k, v) in enumerate(section_data.items()):
        cols[i].metric(label=k, value=v)

    st.divider()
    
    # Dashboard Checks
    checks = results['Checks']
    ratios = checks['Ratios']
    status = checks['Status']
    
    # Status Helper
    def status_pill(passed):
        return ":green[PASS] ✅" if passed else ":red[FAIL] ❌"

    def color_ratio(ratio):
        color = "red" if ratio > 1.0 else "green"
        return f":{color}[{ratio:.3f}]"
    
    # High-level summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Bending Ratio", f"{ratios['Moment']:.3f}", delta_color="inverse" if ratios['Moment'] <= 1 else "normal")
    col2.metric("Shear Ratio", f"{ratios['Shear']:.3f}")
    col3.metric("Deflection Ratio", f"{ratios['Deflection']:.3f}")

    if all(status.values()):
        st.success("### ✅ DESIGN PASSED")
    else:
        st.error("### ❌ DESIGN FAILED")

with tab2:
    st.subheader("📝 Step-by-Step Calculation")
    
    steps = results.get('Steps', [])
    if not steps:
        st.warning("No detailed steps available.")
    
    for step in steps:
        with st.container():
            st.markdown(f"#### {step['title']}")
            
            # 1. General Formula
            st.latex(step['latex'])
            
            # 2. Substitution
            st.markdown("**Substitution:**")
            st.latex(step['subst'])
            
            # 3. Result & Status
            # Create a nice colored box or line for the result
            res_col, stat_col = st.columns([3, 1])
            
            res_col.markdown(f"**Result:** :blue-background[{step['result']}]")
            
            if step.get('status'):
                if step['status'] == "PASS":
                     stat_col.success("PASS")
                else:
                     stat_col.error("FAIL")
            
            st.divider()

with tab3:
    st.subheader("Generate PDF Report")
    
    # Initialize session state for report if not exists
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
    if 'pdf_name' not in st.session_state:
        st.session_state.pdf_name = None

    if st.button("📄 Generate Report"):
        from report_generator import ReportGenerator
        import os
        
        # Prepare Data
        proj_info = {"Project Name": proj_name, "Owner": owner, "Engineer": engineer}
        
        with st.spinner("Generating PDF..."):
            gen = ReportGenerator(proj_info, inputs, results, section_data)
            success, result_path = gen.generate(f"Report_{proj_name}.pdf")
            
            if success:
                st.success(f"Report generated successfully!")
                
                # Verify file exists and load into session state
                if os.path.exists(result_path):
                    with open(result_path, "rb") as f:
                        st.session_state.pdf_data = f.read()
                    st.session_state.pdf_name = result_path
            else:
                st.error(f"Failed to generate report: {result_path}")

    # Display Download Button if data is available
    if st.session_state.pdf_data is not None:
        st.download_button(
            label="📥 Download PDF Report",
            data=st.session_state.pdf_data,
            file_name=st.session_state.pdf_name,
            mime="application/pdf"
        )

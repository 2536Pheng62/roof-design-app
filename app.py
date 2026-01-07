import streamlit as st

st.set_page_config(
    page_title="Steel Structure Design Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏗️ Steel Structure Design Assistant")
st.markdown("### Welcome to your engineering companion.")

st.markdown("""
---
Please select a design module from the sidebar to begin:

### Available Modules:

#### 1. [Purlin Design (แป)](/Purlin_Design)
   - Cold-formed steel purlin design using LRFD method (Thai Standards).
   - Check Bending, Shear, and Deflection.
   - Generate detailed PDF calculation reports.

#### 2. Rafter Design (จันทัน) *[Coming Soon]*
   - Design rafters for various roof slopes and spans.

#### 3. Beam/Eaves Design (อเส) *[Coming Soon]*
   - Structural design for beams and eaves.

---
**Author:** Antigravity  
**Version:** 1.0.0
""")

st.sidebar.success("Select a module above.")

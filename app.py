import streamlit as st
from theme_manager import use_theme

st.set_page_config(
   page_title="ผู้ช่วยออกแบบโครงสร้างเหล็ก",
   layout="wide",
   initial_sidebar_state="expanded"
)

use_theme(page="landing")

st.markdown(
   """
   <div class="hero-wrapper">
      <div class="floating-layer one"></div>
      <div class="floating-layer two"></div>

      <div class="glass-panel">
         <div class="hero-eyebrow">มาตรฐานวิศวกรรมไทย</div>
         <div class="hero-title">ผู้ช่วยออกแบบโครงสร้างเหล็ก</div>
         <div class="hero-lead">
            เครื่องมือออกแบบที่รวบรวมสูตรคำนวณตาม มอก. 1227 / 1228 และหลัก LRFD
            ครอบคลุม แป จันทัน คาน สมาชิกรับแรงอัด และสมาชิกรับแรงดึง
            พร้อมรายงานภาษาไทยและขั้นตอนคำนวณแบบโปร่งใส
         </div>
         <div class="hero-metrics">
            <div class="metric-chip">พร้อมรายงาน PDF ภาษาไทย</div>
            <div class="metric-chip">Bending / Shear / Deflection / Compression / Tension</div>
            <div class="metric-chip">5 โมดูล · AISC 360-16 LRFD · มอก.1227/1228</div>
         </div>
      </div>

      <div class="bento-grid">
         <a class="bento-card" href="/Purlin_Design">
            <div class="inline-badge">พร้อมใช้งาน</div>
            <h3>🏗️ โมดูลออกแบบแปเหล็ก</h3>
            <p>คำนวณแปเหล็กขึ้นรูปเย็นครบถ้วนตามวิธี LRFD ของไทย
               พร้อม Step-by-step log และดาวน์โหลดผลเป็น PDF</p>
            <div class="card-actions">เปิดโมดูล <span>→</span></div>
         </a>
         <a class="bento-card" href="/Rafter_Design">
            <div class="inline-badge">พร้อมใช้งาน</div>
            <h3>🏠 โมดูลออกแบบจันทัน</h3>
            <p>จันทันเหล็กรีดร้อน รองรับการปรับความชัน ช่วงพาด
               และการตรวจสอบ LTB (Lateral-Torsional Buckling) ตาม AISC</p>
            <div class="card-actions">เปิดโมดูล <span>→</span></div>
         </a>
         <a class="bento-card" href="/Compression_Design">
            <div class="inline-badge">พร้อมใช้งาน</div>
            <h3>🏛️ โมดูลออกแบบรับแรงอัด</h3>
            <p>ออกแบบเสาและสมาชิกรับแรงอัดตาม AISC 360-16 Chapter E
               ครอบคลุม Flexural Buckling + Local Buckling (Q-factor)
               พร้อม Step-by-step LaTeX</p>
            <div class="card-actions">เปิดโมดูล <span>→</span></div>
         </a>
         <a class="bento-card" href="/Tension_Design">
            <div class="inline-badge">พร้อมใช้งาน</div>
            <h3>🔩 โมดูลออกแบบรับแรงดึง</h3>
            <p>ออกแบบสมาชิกรับแรงดึงตาม AISC 360-16 Chapter D
               ตรวจสอบ Yielding + Net Section Fracture + Shear Lag (U)
               รองรับการต่อทั้งแบบเชื่อมและสลักเกลียว</p>
            <div class="card-actions">เปิดโมดูล <span>→</span></div>
         </a>
         <a class="bento-card" href="/Beam_Design">
            <div class="inline-badge">พร้อมใช้งาน</div>
            <h3>🔧 โมดูลออกแบบคาน</h3>
            <p>คานเหล็กขึ้นรูปเย็น ตรวจสอบ Bending / Shear / Deflection
               ตามมาตรฐาน มอก. 1228 พร้อมรายงานภาษาไทย</p>
            <div class="card-actions">เปิดโมดูล <span>→</span></div>
         </a>
         <div class="bento-card">
            <div class="inline-badge">Workflow</div>
            <h3>📋 ขั้นตอนการทำงาน</h3>
            <p>1) เลือกโมดูล 2) กรอกค่าพารามิเตอร์ 3) ตรวจสอบผล 4) ส่งออก PDF
               พร้อมข้อมูลโครงการครบถ้วนสำหรับส่งตรวจ</p>
            <div class="card-actions">เรียนรู้เพิ่มเติม <span>→</span></div>
         </div>
      </div>

      <div class="note-footer">
         พัฒนาโดย Antigravity · เวอร์ชัน 1.0.0 · รองรับการใช้งานบนอุปกรณ์ที่มีหน้าจอความละเอียดสูง
      </div>
   </div>
   """,
   unsafe_allow_html=True
)

st.sidebar.success("เลือกโมดูลที่ต้องการทางด้านบน")

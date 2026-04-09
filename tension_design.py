"""
tension_design.py
ออกแบบสมาชิกรับแรงดึง (Tension Member Design)
อ้างอิง: AISC 360-16 Chapter D — วิธี LRFD
         มาตรฐานวิศวกรรมสถานแห่งประเทศไทย (วสท.)

หน่วยที่ใช้ภายใน:
  แรง       : kg
  หน่วยแรง  : ksc (kg/cm²)
  ความยาว   : cm
  พื้นที่    : cm²
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from design_logging import CalculationLogMixin


def _pos(name: str, value: float) -> float:
    if value is None or value <= 0:
        raise ValueError(f"ต้องระบุ '{name}' เป็นค่าบวก")
    return float(value)


# ─────────────────────────────────────────────────────────────
# ตาราง Shear Lag Factor U (AISC 360-16 Table D3.1)
# ─────────────────────────────────────────────────────────────
SHEAR_LAG_TABLE = {
    "welded_all":       (1.00, "เชื่อมต่อทุกองค์ประกอบ (ทุกชิ้นส่วน) — U = 1.00"),
    "bolted_all":       (1.00, "สลักเกลียวต่อทุกองค์ประกอบ (ทุกชิ้นส่วน) — U = 1.00"),
    "W_flange_ge3":     (0.90, "W-shape ต่อผ่านปีก ≥ 3 สลัก (bf ≥ 2/3 d) — U = 0.90"),
    "W_flange_ge2":     (0.85, "W-shape ต่อผ่านปีก ≥ 2 สลัก (bf < 2/3 d) — U = 0.85"),
    "W_web_ge3":        (0.70, "W-shape ต่อผ่านแผ่นเอว ≥ 3 สลัก — U = 0.70"),
    "angle_ge4":        (0.80, "ฉาก 1 แขน (Single Angle) ≥ 4 สลัก — U = 0.80"),
    "angle_2_3":        (0.60, "ฉาก 1 แขน (Single Angle) 2–3 สลัก — U = 0.60"),
    "custom":           (None, "กำหนด U เอง (Alternative: U = 1 − x̄/L)"),
}


@dataclass
class TensionDesign(CalculationLogMixin):
    """
    ออกแบบสมาชิกรับแรงดึง (เหล็กค้ำยัน / ท่อนดึง) ตาม AISC 360-16 Chapter D
    ตรวจสอบ 2 สภาวะขีดจำกัด:
      1. การคราก (Yielding) ของพื้นที่รวม   — φt = 0.90
      2. การแตกหัก (Fracture) ที่หน้าตัดสุทธิ — φt = 0.75
    พร้อมตรวจสอบความชะลูด L/r ≤ 300 (ข้อแนะนำ)
    """

    # ──────────────────────────────────────────
    # คุณสมบัติหน้าตัด (Section Properties)
    # ──────────────────────────────────────────
    section_name: str  = ""
    Ag:   float = 0.0  # cm²  พื้นที่หน้าตัดรวม (Gross Area)
    r_min: float = 0.0 # cm   รัศมีไจเรชันน้อยที่สุด (Minimum radius of gyration)

    # ──────────────────────────────────────────
    # คุณสมบัติวัสดุ
    # ──────────────────────────────────────────
    Fy: float = 2500.0  # ksc  กำลังคราก
    Fu: float = 4080.0  # ksc  กำลังต้านทานแรงดึง  SS400: 400MPa ≈ 4080 ksc
    E:  float = 2.04e6  # ksc  โมดูลัสยืดหยุ่น

    # ──────────────────────────────────────────
    # เรขาคณิตสมาชิก
    # ──────────────────────────────────────────
    L: float = 3.0  # m  ความยาวสมาชิก

    # ──────────────────────────────────────────
    # รายละเอียดการต่อ (Connection Details)
    # ──────────────────────────────────────────
    connection_type: str = "welded"  # "welded" | "bolted"
    # Shear lag factor
    U_key: str   = "welded_all"     # key จาก SHEAR_LAG_TABLE
    U_custom: float = 1.0           # ใช้เมื่อ U_key == "custom"
    # รายละเอียดสลักเกลียว (ใช้เมื่อ connection_type == "bolted")
    n_bolt_lines:  int   = 1    # จำนวนแนวรูสลักเกลียวตัดผ่านหน้าตัดวิกฤติ
    bolt_diameter: float = 2.0  # cm  เส้นผ่านศูนย์กลางสลักเกลียว
    t_element:     float = 1.0  # cm  ความหนาองค์ประกอบที่ถูกเจาะรู

    # ──────────────────────────────────────────
    # แรงกระทำ
    # ──────────────────────────────────────────
    Tu: float = 0.0  # kg  แรงดึงประลัย (Factored Tensile Force)

    # (จัดการโดย CalculationLogMixin)
    steps: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    def run_design(self) -> Dict[str, Any]:
        """คำนวณและตรวจสอบกำลังรับแรงดึง — คืนค่า dict ผลลัพธ์ครบถ้วน"""
        self.reset_steps()

        Fy  = _pos("Fy", self.Fy)
        Fu  = _pos("Fu", self.Fu)
        Ag  = _pos("Ag", self.Ag)
        Tu  = max(self.Tu, 0.0)
        L_cm = self.L * 100.0

        # ══════════════════════════════════════════════════════════════
        # 1. ตรวจสอบความชะลูด L/r ≤ 300 (ข้อแนะนำ AISC D1)
        # ══════════════════════════════════════════════════════════════
        r_min = self.r_min
        if r_min > 0:
            L_r = L_cm / r_min
            slen_ok = L_r <= 300.0
            self.add_step(
                "ความชะลูด L/r (AISC 360-16 Sec. D1 — ข้อแนะนำ)",
                r"\frac{L}{r_{\min}} \leq 300",
                rf"\frac{{{L_cm:.1f}}}{{{r_min:.3f}}} = {L_r:.2f}",
                rf"L/r = {L_r:.2f} \;{'\\leq' if slen_ok else '>'}\; 300 "
                rf"\;\Rightarrow\; \text{{{'OK' if slen_ok else 'เกินข้อแนะนำ'}}}",
                status=None if slen_ok else "WARN",
                note=(
                    "AISC 360-16 Section D1: L/r ≤ 300 เป็นข้อแนะนำ (ไม่ใช่ข้อบังคับ) "
                    "สำหรับสมาชิกรับแรงดึงหลัก"
                ),
            )
        else:
            L_r = 0.0
            slen_ok = True
            self.add_step(
                "ความชะลูด L/r",
                r"\text{ไม่ได้ระบุ } r_{\min} \text{ — ข้ามการตรวจสอบ}",
                None,
                None,
                note="กรุณาระบุ r_min เพื่อตรวจสอบความชะลูด",
            )

        # ══════════════════════════════════════════════════════════════
        # 2. คำนวณพื้นที่หน้าตัดสุทธิ An
        # ══════════════════════════════════════════════════════════════
        if self.connection_type == "bolted":
            # เส้นผ่านศูนย์กลางรูมาตรฐาน = ∅สลัก + 3.2 mm = ∅สลัก + 0.32 cm
            dh_cm = self.bolt_diameter + 0.32
            hole_area = self.n_bolt_lines * dh_cm * self.t_element  # cm²
            An = max(Ag - hole_area, 0.0)
            self.add_step(
                "พื้นที่หน้าตัดสุทธิ An — การต่อสลักเกลียว (Bolted)",
                r"A_n = A_g - n_{lines}\cdot(d_h + \tfrac{3.2}{10})\cdot t",
                (
                    rf"d_h = {self.bolt_diameter:.3f}+0.32 = {dh_cm:.3f}\,\text{{cm}}"
                    rf",\quad A_n = {Ag:.4f} - {self.n_bolt_lines}\times{dh_cm:.3f}\times{self.t_element:.3f}"
                ),
                rf"A_n = {An:.4f}\;\text{{cm}}^2",
                note=(
                    "AISC 360-16 Sec. B4.3b: ขนาดรูมาตรฐาน = ∅สลัก + 1/16″ = ∅สลัก + 1.6 mm "
                    "(หรือ +3.2 mm รวม clearance ทั้งสองด้าน)"
                ),
            )
        else:
            An = Ag
            self.add_step(
                "พื้นที่หน้าตัดสุทธิ An — การต่อด้วยการเชื่อม (Welded)",
                r"A_n = A_g \quad (\text{ไม่มีรูสลักเกลียว})",
                rf"A_n = {An:.4f}\;\text{{cm}}^2",
                None,
                note="การต่อด้วยการเชื่อม: ไม่มีการสูญเสียพื้นที่หน้าตัด An = Ag",
            )

        # ══════════════════════════════════════════════════════════════
        # 3. ตัวคูณ Shear Lag U และ Ae
        # ══════════════════════════════════════════════════════════════
        if self.U_key == "custom":
            U = self.U_custom
            u_note = f"กำหนด U เอง = {U:.3f} (ใช้สูตร U = 1 − x̄/L หรือค่าจากตาราง)"
        else:
            entry = SHEAR_LAG_TABLE.get(self.U_key, (1.0, ""))
            U = entry[0] if entry[0] is not None else self.U_custom
            u_note = entry[1]

        U = float(U)
        Ae = U * An

        self.add_step(
            "ตัวคูณ Shear Lag U และพื้นที่ประสิทธิผล Ae",
            r"A_e = U \times A_n",
            rf"U = {U:.3f}\quad (\text{{{u_note}}})",
            rf"A_e = {U:.3f} \times {An:.4f} = {Ae:.4f}\;\text{{cm}}^2",
            note="AISC 360-16 Table D3.1: ค่า U สะท้อนผลของ Shear Lag ที่จุดต่อ",
        )

        # ══════════════════════════════════════════════════════════════
        # 4. กรณีที่ 1 — Yielding of Gross Section (AISC Eq. D2-1)
        # ══════════════════════════════════════════════════════════════
        phi_t1 = 0.90
        Tn_yield = phi_t1 * Fy * Ag
        self.add_step(
            "กรณีที่ 1: การคราก Gross Section Yielding (AISC 360-16 Eq. D2-1)",
            r"\phi_t T_n = 0.90 \times F_y \times A_g",
            rf"= 0.90 \times {Fy:.0f} \times {Ag:.4f}",
            rf"= {Tn_yield:.2f}\;\text{{kg}}",
            note="φt = 0.90 สำหรับการคราก; สภาวะขีดจำกัดที่ต้านทานด้วยพื้นที่รวม",
        )

        # ══════════════════════════════════════════════════════════════
        # 5. กรณีที่ 2 — Net Section Fracture (AISC Eq. D2-2)
        # ══════════════════════════════════════════════════════════════
        phi_t2 = 0.75
        Tn_fracture = phi_t2 * Fu * Ae
        self.add_step(
            "กรณีที่ 2: การแตกหัก Net Section Fracture (AISC 360-16 Eq. D2-2)",
            r"\phi_t T_n = 0.75 \times F_u \times A_e",
            rf"= 0.75 \times {Fu:.0f} \times {Ae:.4f}",
            rf"= {Tn_fracture:.2f}\;\text{{kg}}",
            note="φt = 0.75 สำหรับการแตกหัก; ใช้ Fu และ Ae (รวม Shear Lag Factor U)",
        )

        # ══════════════════════════════════════════════════════════════
        # 6. กำลังรับแรงดึงออกแบบ — ค่าน้อยสุดจากทั้งสองกรณี
        # ══════════════════════════════════════════════════════════════
        phi_Tn = min(Tn_yield, Tn_fracture)
        ctrl   = "การคราก (Yielding)" if Tn_yield <= Tn_fracture else "การแตกหัก (Fracture)"
        self.add_step(
            "กำลังรับแรงดึงออกแบบ φtTn (Design Tensile Strength)",
            r"\phi_t T_n = \min\!\left(\phi_t T_{n,\text{yield}},\;\phi_t T_{n,\text{fracture}}\right)",
            rf"= \min\!\left({Tn_yield:.2f},\;{Tn_fracture:.2f}\right)",
            rf"= {phi_Tn:.2f}\;\text{{kg}}\quad(\text{{ควบคุมโดย{ctrl}}})",
            note=f"สภาวะขีดจำกัดที่ควบคุม: {ctrl}",
        )

        # ══════════════════════════════════════════════════════════════
        # 7. ตรวจสอบ Tu ≤ φtTn
        # ══════════════════════════════════════════════════════════════
        ratio = Tu / phi_Tn if phi_Tn > 0 else 999.0
        tens_pass = ratio <= 1.0

        self.add_step(
            "ตรวจสอบความปลอดภัย Tu ≤ φtTn (Tension Check)",
            r"\frac{T_u}{\phi_t T_n} \leq 1.0",
            rf"\frac{{{Tu:,.2f}}}{{{phi_Tn:,.2f}}} = {ratio:.4f}",
            rf"{ratio:.4f} \;{'\\leq' if tens_pass else '>'}\; 1.0 "
            rf"\;\Rightarrow\; \text{{{'PASS ✓' if tens_pass else 'FAIL ✗'}}}",
            status="PASS" if tens_pass else "FAIL",
            note="AISC 360-16 Chapter D: ต้องการ Tu ≤ φtTn",
        )

        # ══════════════════════════════════════════════════════════════
        # Return
        # ══════════════════════════════════════════════════════════════
        return {
            "Slenderness": {
                "L_r":    L_r,
                "r_min":  r_min,
                "OK":     slen_ok,
            },
            "NetArea": {
                "An":   An,
                "Ae":   Ae,
                "U":    U,
                "U_note": u_note,
                "connection_type": self.connection_type,
            },
            "Capacity": {
                "phi_Tn_yield":    Tn_yield,
                "phi_Tn_fracture": Tn_fracture,
                "phi_Tn":          phi_Tn,
                "Controlling":     ctrl,
            },
            "Demand": {"Tu": Tu},
            "Ratio":  ratio,
            "Status": tens_pass,
            "SlendernessOK": slen_ok,
            "Steps":  self.steps,
        }

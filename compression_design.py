"""
compression_design.py
ออกแบบสมาชิกรับแรงอัด (Compression Member Design)
อ้างอิง: AISC 360-16 Chapter E — วิธี LRFD
         มาตรฐานวิศวกรรมสถานแห่งประเทศไทย (วสท.)

หน่วยที่ใช้ภายใน:
  แรง  : kg
  หน่วยแรง : ksc (kg/cm²)
  ความยาว  : cm (ยกเว้นมิติหน้าตัด h, bf, tw, tf ใช้ mm)
  พื้นที่    : cm²
  โมเมนต์ความเฉื่อย : cm⁴
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from design_logging import CalculationLogMixin


def _pos(name: str, value: float) -> float:
    if value is None or value <= 0:
        raise ValueError(f"ต้องระบุ '{name}' เป็นค่าบวก")
    return float(value)


@dataclass
class CompressionDesign(CalculationLogMixin):
    """
    ออกแบบสมาชิกรับแรงอัด (เสา / ค้ำยัน) ตาม AISC 360-16 Chapter E
    รองรับทั้งหน้าตัดกะทัดรัด (Non-slender) และหน้าตัดชะลูด (Slender)
    โดยใช้ตัวคูณลด Q = Qs × Qa ตาม Section E7
    """

    # ──────────────────────────────────────────
    # คุณสมบัติหน้าตัด (Section Properties)
    # ──────────────────────────────────────────
    section_name: str = ""
    Ag: float = 0.0    # cm²  พื้นที่หน้าตัดรวม
    rx: float = 0.0    # cm   รัศมีไจเรชันแกน x-x
    ry: float = 0.0    # cm   รัศมีไจเรชันแกน y-y
    # มิติสำหรับตรวจสอบ local buckling (ใช้ mm)
    h:  float = 0.0    # mm   ความสูง / ความลึกหน้าตัด
    bf: float = 0.0    # mm   ความกว้างปีก
    tw: float = 0.0    # mm   ความหนาแผ่นเอว
    tf: float = 0.0    # mm   ความหนาปีก

    # ──────────────────────────────────────────
    # คุณสมบัติวัสดุ (Material)
    # ──────────────────────────────────────────
    Fy: float = 2500.0   # ksc  SS400: 245 MPa ≈ 2500 ksc
    E:  float = 2.04e6   # ksc  โมดูลัสยืดหยุ่น

    # ──────────────────────────────────────────
    # เรขาคณิตเสา (Column Geometry)
    # ──────────────────────────────────────────
    Lx: float = 3.0   # m  ความยาวไม่ค้ำยันแกน x-x
    Ly: float = 3.0   # m  ความยาวไม่ค้ำยันแกน y-y
    Kx: float = 1.0   # -  สัมประสิทธิ์ความยาวประสิทธิผลแกน x-x
    Ky: float = 1.0   # -  สัมประสิทธิ์ความยาวประสิทธิผลแกน y-y

    # ──────────────────────────────────────────
    # แรงกระทำ (Load)
    # ──────────────────────────────────────────
    Pu: float = 0.0   # kg  แรงอัดประลัย (Factored Axial Compression)

    # (จัดการโดย CalculationLogMixin)
    steps: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    def run_design(self) -> Dict[str, Any]:
        """คำนวณและตรวจสอบกำลังรับแรงอัด — คืนค่า dict ผลลัพธ์ครบถ้วน"""
        self.reset_steps()

        Fy  = _pos("Fy", self.Fy)
        E   = _pos("E",  self.E)
        Ag  = _pos("Ag", self.Ag)
        rx  = _pos("rx", self.rx)
        ry  = _pos("ry", self.ry)
        Lx_cm = self.Lx * 100.0
        Ly_cm = self.Ly * 100.0
        Kx, Ky = self.Kx, self.Ky
        Pu = max(self.Pu, 0.0)
        phi_c = 0.90

        # ══════════════════════════════════════════════════════════════
        # 1. อัตราส่วนความชะลูด KL/r
        # ══════════════════════════════════════════════════════════════
        KLx_rx = (Kx * Lx_cm) / rx
        KLy_ry = (Ky * Ly_cm) / ry
        KL_r   = max(KLx_rx, KLy_ry)
        gov_axis = "x-x" if KLx_rx >= KLy_ry else "y-y"
        slenderness_ok = KL_r <= 200.0

        self.add_step(
            "อัตราส่วนความชะลูดประสิทธิผล KL/r",
            r"\frac{KL}{r} = \max\!\left(\frac{K_x L_x}{r_x},\;\frac{K_y L_y}{r_y}\right)",
            (
                rf"\frac{{K_x L_x}}{{r_x}} = \frac{{{Kx:.2f}\times{Lx_cm:.1f}}}{{{rx:.3f}}} = {KLx_rx:.2f}"
                rf",\quad \frac{{K_y L_y}}{{r_y}} = \frac{{{Ky:.2f}\times{Ly_cm:.1f}}}{{{ry:.3f}}} = {KLy_ry:.2f}"
            ),
            rf"\frac{{KL}}{{r}} = {KL_r:.2f} \quad (\text{{ควบคุมโดยแกน }}{gov_axis})",
            status=None if slenderness_ok else "WARN",
            note=(
                "AISC 360-16 Commentary Table C-A-7.1: "
                "แนะนำ KL/r ≤ 200 สำหรับสมาชิกรับแรงอัด"
                + ("" if slenderness_ok else f" ⚠ KL/r = {KL_r:.1f} > 200")
            ),
        )

        # ══════════════════════════════════════════════════════════════
        # 2. ตรวจสอบ Local Buckling — Q = Qs × Qa
        #    AISC 360-16 Table B4.1a & Section E7
        # ══════════════════════════════════════════════════════════════
        Qs = 1.0
        Qa = 1.0
        local_notes: List[str] = []
        has_dim = (self.bf > 0 and self.tf > 0 and self.tw > 0 and self.h > 0)

        if has_dim:
            # ── ปีก (Unstiffened element, Table B4.1a Case 1) ──────────
            lam_f  = self.bf / (2.0 * self.tf)
            lam_rf = 0.56 * math.sqrt(E / Fy)
            flange_ok = lam_f <= lam_rf

            _f_cmp = r"\leq" if flange_ok else ">"
            self.add_step(
                "ตรวจสอบ Local Buckling ปีก (Flange, Unstiffened)",
                r"\lambda_f = \frac{b_f}{2t_f},\quad \lambda_{rf} = 0.56\sqrt{\frac{E}{F_y}}",
                (
                    rf"\lambda_f = \frac{{{self.bf:.1f}}}{{2\times{self.tf:.1f}}} = {lam_f:.3f}"
                    rf",\quad \lambda_{{rf}} = 0.56\sqrt{{\frac{{{E:.3e}}}{{{Fy:.0f}}}}} = {lam_rf:.3f}"
                ),
                rf"\lambda_f = {lam_f:.3f} \;{_f_cmp}\; \lambda_{{rf}} = {lam_rf:.3f}"
                rf"\;\Rightarrow\; \textbf{{{'Non-Slender' if flange_ok else 'Slender'}}}",
                status="PASS" if flange_ok else "WARN",
                note="AISC 360-16 Table B4.1a Case 1: ปีกรับแรงอัดแบบ Unstiffened",
            )

            if not flange_ok:
                # คำนวณ Qs ตาม Section E7.1(a)
                lam2 = 1.03 * math.sqrt(E / Fy)
                if lam_f <= lam2:
                    Qs = 1.415 - 0.74 * lam_f * math.sqrt(Fy / E)
                    qs_expr = rf"Q_s = 1.415 - 0.74\lambda_f\sqrt{{F_y/E}} = 1.415 - 0.74\times{lam_f:.3f}\times{math.sqrt(Fy/E):.6f}"
                else:
                    Qs = 0.69 * E / (Fy * lam_f ** 2)
                    qs_expr = rf"Q_s = \frac{{0.69E}}{{F_y\lambda_f^2}} = \frac{{0.69\times{E:.3e}}}{{{Fy:.0f}\times{lam_f:.3f}^2}}"
                Qs = max(Qs, 0.0)
                self.add_step(
                    "ตัวคูณลดกำลังปีกชะลูด Qs (AISC 360-16 Sec. E7.1a)",
                    r"Q_s = \begin{cases}1.415-0.74\lambda\sqrt{F_y/E} & 0.56<\lambda\leq 1.03\sqrt{E/F_y}\\"
                    r"\dfrac{0.69E}{F_y\lambda^2} & \lambda>1.03\sqrt{E/F_y}\end{cases}",
                    qs_expr,
                    rf"Q_s = {Qs:.4f}",
                    status="WARN",
                    note=f"ปีกชะลูด (λf={lam_f:.2f} > λrf={lam_rf:.2f}) → ใช้ตัวคูณลดกำลัง Qs",
                )
                local_notes.append(f"ปีกชะลูด Qs={Qs:.3f}")

            # ── แผ่นเอว (Stiffened element, Table B4.1a Case 5) ─────────
            h_clear = self.h - 2.0 * self.tf  # mm ความสูงชัดเจน
            lam_w   = h_clear / self.tw if self.tw > 0 else 0.0
            lam_rw  = 1.49 * math.sqrt(E / Fy)
            web_ok  = lam_w <= lam_rw

            self.add_step(
                "ตรวจสอบ Local Buckling แผ่นเอว (Web, Stiffened)",
                r"\lambda_w = \frac{h}{t_w},\quad \lambda_{rw} = 1.49\sqrt{\frac{E}{F_y}}",
                (
                    rf"\lambda_w = \frac{{{h_clear:.1f}}}{{{self.tw:.1f}}} = {lam_w:.3f}"
                    rf",\quad \lambda_{{rw}} = 1.49\sqrt{{\frac{{{E:.3e}}}{{{Fy:.0f}}}}} = {lam_rw:.3f}"
                ),
                rf"\lambda_w = {lam_w:.3f} \;{'\\leq' if web_ok else '>'}\; \lambda_{{rw}} = {lam_rw:.3f}"
                rf"\;\Rightarrow\; \textbf{{{'Non-Slender' if web_ok else 'Slender'}}}",
                status="PASS" if web_ok else "WARN",
                note="AISC 360-16 Table B4.1a Case 5: แผ่นเอวรับแรงอัดแบบ Stiffened",
            )

            if not web_ok:
                # คำนวณ Qa ด้วย Effective Width Method (Sec. E7.2a)
                # ใช้ f = Fy (conservative) ในรอบแรก
                f_use  = Fy
                ratio_w = h_clear / self.tw
                sqrt_Ef = math.sqrt(E / f_use)
                be = (1.92 * self.tw * sqrt_Ef
                      * (1.0 - (0.34 / ratio_w) * sqrt_Ef))
                be = max(min(be, h_clear), 0.0)
                # พื้นที่ที่ถูกหักออก = (h_clear - be) × tw / 100 cm²
                A_eff = Ag - (h_clear - be) * self.tw / 100.0
                A_eff = max(A_eff, 0.0)
                Qa = A_eff / Ag if Ag > 0 else 1.0

                self.add_step(
                    "ตัวคูณลดกำลังเอวชะลูด Qa (AISC 360-16 Sec. E7.2a)",
                    r"b_e = 1.92t\sqrt{\frac{E}{f}}\!\left[1-\frac{0.34}{(b/t)\sqrt{E/f}}\right]\leq b"
                    r",\quad Q_a = \frac{A_{eff}}{A_g}",
                    (
                        rf"b_e = 1.92\times{self.tw:.1f}\times{sqrt_Ef:.4f}"
                        rf"\left[1-\frac{{0.34}}{{{ratio_w:.2f}\times{sqrt_Ef:.4f}}}\right]"
                        rf"= {be:.3f}\,\text{{mm}}"
                        rf",\quad A_{{eff}} = {A_eff:.4f}\,\text{{cm}}^2"
                    ),
                    rf"Q_a = \frac{{{A_eff:.4f}}}{{{Ag:.4f}}} = {Qa:.4f}",
                    status="WARN",
                    note=f"เอวชะลูด (λw={lam_w:.2f} > λrw={lam_rw:.2f}) → ใช้ความกว้างประสิทธิผล",
                )
                local_notes.append(f"เอวชะลูด Qa={Qa:.3f}")

        Q = Qs * Qa
        if has_dim and Q < 1.0:
            self.add_step(
                "ตัวคูณลดกำลังรวม Q = Qs × Qa",
                r"Q = Q_s \times Q_a",
                rf"= {Qs:.4f} \times {Qa:.4f}",
                rf"= {Q:.4f}",
                status="WARN",
                note="Q < 1.0 → หน้าตัดมีองค์ประกอบชะลูด กำลังรับแรงอัดจะลดลง",
            )

        local_note_str = (
            "ทุกองค์ประกอบ Non-slender (Q = 1.0)"
            if not local_notes
            else "; ".join(local_notes) + f" → Q = {Q:.3f}"
        )

        # ══════════════════════════════════════════════════════════════
        # 3. หน่วยแรงโก่งเดาะยืดหยุ่น Fe
        # ══════════════════════════════════════════════════════════════
        Fe = (math.pi ** 2 * E) / (KL_r ** 2)
        self.add_step(
            "หน่วยแรงโก่งเดาะยืดหยุ่น Fe (Elastic Critical Stress)",
            r"F_e = \frac{\pi^2 E}{(KL/r)^2}",
            rf"= \frac{{\pi^2 \times {E:.4e}}}{{{KL_r:.3f}^2}}",
            rf"= {Fe:.2f}\;\text{{ksc}}",
            note="AISC 360-16 Eq. E3-4: หน่วยแรงวิกฤติ Euler",
        )

        # ══════════════════════════════════════════════════════════════
        # 4. หน่วยแรงวิกฤติ Fcr
        #    ใช้ Q-modified limit: 4.71√(E / QFy)
        # ══════════════════════════════════════════════════════════════
        lim_KLr = 4.71 * math.sqrt(E / (Q * Fy)) if Q > 0 else float("inf")

        if KL_r <= lim_KLr:
            # Inelastic buckling (AISC E7-2 / E3-2)
            Fcr = Q * (0.658 ** (Q * Fy / Fe)) * Fy
            mode = "Inelastic Buckling (โก่งเดาะแบบอไนลาสติก)"
            self.add_step(
                "หน่วยแรงวิกฤติ Fcr — Inelastic Buckling",
                r"F_{cr} = Q\!\left[0.658^{QF_y/F_e}\right]\!F_y",
                rf"= {Q:.4f}\!\left[0.658^{{{Q:.4f}\times{Fy:.0f}/{Fe:.3f}}}\right]\!\times{Fy:.0f}",
                rf"= {Fcr:.2f}\;\text{{ksc}}",
                note=(
                    f"AISC 360-16 Eq. E7-2: KL/r = {KL_r:.2f} ≤ 4.71√(E/QFy) = {lim_KLr:.2f} "
                    "→ Inelastic Buckling"
                ),
            )
        else:
            # Elastic buckling (AISC E7-3 / E3-3)
            Fcr = 0.877 * Fe
            mode = "Elastic Buckling (โก่งเดาะแบบยืดหยุ่น)"
            self.add_step(
                "หน่วยแรงวิกฤติ Fcr — Elastic Buckling",
                r"F_{cr} = 0.877\,F_e",
                rf"= 0.877 \times {Fe:.2f}",
                rf"= {Fcr:.2f}\;\text{{ksc}}",
                note=(
                    f"AISC 360-16 Eq. E7-3: KL/r = {KL_r:.2f} > 4.71√(E/QFy) = {lim_KLr:.2f} "
                    "→ Elastic Buckling"
                ),
            )

        # ══════════════════════════════════════════════════════════════
        # 5. กำลังรับแรงอัดตามชื่อ Pn และกำลังออกแบบ φcPn
        # ══════════════════════════════════════════════════════════════
        Pn     = Fcr * Ag        # kg
        phi_Pn = phi_c * Pn      # kg

        self.add_step(
            "กำลังรับแรงอัดตามชื่อ Pn",
            r"P_n = F_{cr} \times A_g",
            rf"= {Fcr:.3f} \times {Ag:.4f}",
            rf"= {Pn:.2f}\;\text{{kg}}",
            note="Nominal Compressive Strength (AISC 360-16 Sec. E7)",
        )
        self.add_step(
            "กำลังรับแรงอัดออกแบบ φcPn",
            r"\phi_c P_n = 0.90 \times P_n",
            rf"= 0.90 \times {Pn:.2f}",
            rf"= {phi_Pn:.2f}\;\text{{kg}}",
            note="φc = 0.90 ตาม AISC 360-16 Section E1 (LRFD)",
        )

        # ══════════════════════════════════════════════════════════════
        # 6. ตรวจสอบ Pu ≤ φcPn
        # ══════════════════════════════════════════════════════════════
        ratio = Pu / phi_Pn if phi_Pn > 0 else 999.0
        comp_pass = ratio <= 1.0

        self.add_step(
            "ตรวจสอบความปลอดภัย Pu ≤ φcPn (Compression Check)",
            r"\frac{P_u}{\phi_c P_n} \leq 1.0",
            rf"\frac{{{Pu:,.2f}}}{{{phi_Pn:,.2f}}} = {ratio:.4f}",
            rf"{ratio:.4f} \;{'\\leq' if comp_pass else '>'}\; 1.0 "
            rf"\;\Rightarrow\; \text{{{'PASS ✓' if comp_pass else 'FAIL ✗'}}}",
            status="PASS" if comp_pass else "FAIL",
            note="AISC 360-16 Chapter E: ต้องการ Pu ≤ φcPn",
        )

        # ══════════════════════════════════════════════════════════════
        # Return
        # ══════════════════════════════════════════════════════════════
        return {
            "Slenderness": {
                "KLx_rx": KLx_rx,
                "KLy_ry": KLy_ry,
                "KL_r":   KL_r,
                "Governing": gov_axis,
                "OK": slenderness_ok,
            },
            "LocalBuckling": {
                "Qs": Qs,
                "Qa": Qa,
                "Q":  Q,
                "Note": local_note_str,
                "OK": len(local_notes) == 0,
            },
            "Buckling": {
                "Fe":       Fe,
                "Fcr":      Fcr,
                "Mode":     mode,
                "Lim_KLr":  lim_KLr,
            },
            "Capacity": {
                "Pn":     Pn,
                "phi_Pn": phi_Pn,
                "phi_c":  phi_c,
            },
            "Demand": {"Pu": Pu},
            "Ratio":  ratio,
            "Status": comp_pass,          # True = ผ่าน
            "SlendernessOK": slenderness_ok,
            "Steps":  self.steps,
        }

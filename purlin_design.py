import math

from design_logging import CalculationLogMixin


def _ensure_positive(name: str, value: float) -> float:
    if value is None or value <= 0:
        raise ValueError(f"ต้องระบุ {name} เป็นค่าบวกตามตาราง มอก. 1228")
    return value


class PurlinDesign(CalculationLogMixin):
    def __init__(self, section_data, geometry, loads, materials):
        self.sec = section_data
        self.geo = geometry
        self.loads = loads
        self.mat = materials
        CalculationLogMixin.__init__(self)

    def run_design(self):
        self.reset_steps()

        spacing = _ensure_positive("spacing", self.geo.get('spacing'))
        span = _ensure_positive("span", self.geo.get('span'))
        slope = self.geo.get('slope', 0.0)
        slope_rad = math.radians(slope)
        cos_slope = math.cos(slope_rad)

        dl_surf = max(self.loads.get('DL', 0.0), 0.0)
        ll_surf = max(self.loads.get('LL', 0.0), 0.0)
        wl_surf = self.loads.get('WL', 0.0)

        self_weight = max(self.sec.get('Weight', 0.0), 0.0)

        dl_line = dl_surf * spacing + self_weight
        self.add_step(
            "น้ำหนักบรรทุกคงที่รวม",
            r"w_{DL} = (w_{DL,\text{surf}} \times s) + w_{self}",
            f"= ({dl_surf:.2f} \\times {spacing:.2f}) + {self_weight:.2f}",
            f"= {dl_line:.2f}\\,\\text{{kg/m}}"
        )

        ll_line = ll_surf * spacing
        self.add_step(
            "น้ำหนักใช้งานบนสมาชิก",
            r"w_{LL} = w_{LL,\text{surf}} \times s",
            f"= {ll_surf:.2f} \\times {spacing:.2f}",
            f"= {ll_line:.2f}\\,\\text{{kg/m}}"
        )

        wl_line_surface = wl_surf * spacing
        wl_line_normal = wl_line_surface * cos_slope
        self.add_step(
            "แรงลมปกติต่อผิว",
            r"w_{W} = (w_{W,\text{surf}} \times s) \cos\theta",
            f"= ({wl_surf:.2f} \\times {spacing:.2f}) \\cos {slope:.1f}^\\circ",
            f"= {wl_line_normal:.2f}\\,\\text{{kg/m}}"
        )

        loads = {
            'SelfWeight': self_weight,
            'DL_line': dl_line,
            'LL_line': ll_line,
            'Wind_line': wl_line_normal,
        }

        # Load Combinations ตาม มอก. 1228-2549 และ LRFD (หลัก วสท.)
        # LC1: น้ำหนักบรรทุกถาวรและน้ำหนักใช้สอยเต็มรูป
        wu1 = 1.4 * dl_line + 1.7 * ll_line
        
        # LC2: พิจารณาแรงลมร่วมด้วย (ตามหลัก LRFD ของไทย)
        combo_base = 0.75 * (1.4 * dl_line + 1.7 * ll_line)
        wind_effect = abs(wl_line_normal)
        wu2_pos = combo_base + 1.6 * wind_effect  # ลมกด
        wu2_neg = combo_base - 1.6 * wind_effect  # ลมดูด

        self.add_step(
            "LC1: 1.4D + 1.7L (ตาม มอก. 1228-2549)",
            r"w_{u1} = 1.4w_{DL} + 1.7w_{LL}",
            f"= 1.4({dl_line:.2f}) + 1.7({ll_line:.2f})",
            f"= {wu1:.2f}\\,\\text{{kg/m}}",
            note="โหลดแฟคเตอร์ตามหลัก LRFD ของ วสท."
        )
        self.add_step(
            "LC2+: 0.75(1.4D+1.7L) + 1.6W (ลมกด)",
            r"w_{u2+} = 0.75(1.4w_{DL} + 1.7w_{LL}) + 1.6|w_W|",
            f"= 0.75(1.4 \\times {dl_line:.2f} + 1.7 \\times {ll_line:.2f}) + 1.6({wind_effect:.2f})",
            f"= {wu2_pos:.2f}\\,\\text{{kg/m}}",
            note="พิจารณาแรงลมกดตามมาตรฐานไทย"
        )
        self.add_step(
            "LC2-: 0.75(1.4D+1.7L) - 1.6W (ลมดูด)",
            r"w_{u2-} = 0.75(1.4w_{DL} + 1.7w_{LL}) - 1.6|w_W|",
            f"= 0.75(1.4 \\times {dl_line:.2f} + 1.7 \\times {ll_line:.2f}) - 1.6({wind_effect:.2f})",
            f"= {wu2_neg:.2f}\\,\\text{{kg/m}}",
            note="พิจารณาแรงลมดูดตามมาตรฐานไทย"
        )

        wu_candidates = {
            "1.4D+1.7L": wu1,
            "0.75(1.4D+1.7L)+1.6W": wu2_pos,
            "0.75(1.4D+1.7L)-1.6W": wu2_neg,
        }
        controlling_combo, wu_design = max(wu_candidates.items(), key=lambda item: abs(item[1]))

        mu = wu_design * span ** 2 / 8
        self.add_step(
            "โมเมนต์ออกแบบ",
            r"M_u = \frac{w_u L^2}{8}",
            f"= {wu_design:.2f} \\times {span:.2f}^2 / 8",
            f"= {mu:.2f}\\,\\text{{kg-m}}",
            note=f"กรณีควบคุม: {controlling_combo}"
        )

        vu = wu_design * span / 2
        self.add_step(
            "แรงเฉือนออกแบบ",
            r"V_u = \frac{w_u L}{2}",
            f"= {wu_design:.2f} \\times {span:.2f} / 2",
            f"= {vu:.2f}\\,\\text{{kg}}"
        )

        zx = _ensure_positive("Z_x", self.sec.get('Zx'))
        ix = _ensure_positive("I_x", self.sec.get('Ix'))
        fy = _ensure_positive("F_y", self.mat.get('Fy'))
        E = _ensure_positive("E", self.mat.get('E'))

        h_mm = _ensure_positive("h", self.sec.get('h'))
        t_mm = _ensure_positive("t", self.sec.get('t'))
        aw_cm2 = (h_mm * t_mm) / 100.0

        # กำลังดัดรับ ตาม มอก. 1228-2549 (Cold-formed Steel)
        mn = zx * fy / 100.0  # Nominal moment capacity
        phi_mn = 0.90 * mn     # Φ = 0.90 สำหรับ bending (ตามหลัก LRFD)
        moment_ratio = mu / phi_mn
        moment_pass = moment_ratio <= 1.0
        self.add_step(
            "กำลังดัดรับออกแบบ (ตาม มอก. 1228-2549)",
            r"\phi M_n = 0.90 \times F_y \times Z_x / 100",
            f"= 0.90 \\times {fy:.0f} \\times {zx:.2f} / 100",
            f"= {phi_mn:.2f}\\,\\text{{kg-m}}",
            status="PASS" if moment_pass else "FAIL",
            note="Φ = 0.90 สำหรับการดัด (LRFD)"
        )

        # กำลังเฉือนรับ ตาม มอก. 1228-2549
        phi_vn = 0.95 * 0.6 * fy * aw_cm2  # Φ = 0.95 สำหรับ shear (ตามหลัก LRFD)
        shear_ratio = vu / phi_vn
        shear_pass = shear_ratio <= 1.0
        self.add_step(
            "กำลังเฉือนรับออกแบบ (ตาม มอก. 1228-2549)",
            r"\phi V_n = 0.95 \times 0.6 \times F_y \times A_w",
            f"= 0.95 \\times 0.6 \\times {fy:.0f} \\times {aw_cm2:.2f}",
            f"= {phi_vn:.2f}\\,\\text{{kg}}",
            status="PASS" if shear_pass else "FAIL",
            note="Φ = 0.95 สำหรับการเฉือน (LRFD), V = 0.6FyAw"
        )

        span_cm = span * 100.0
        w_total_cm = (dl_line + ll_line) / 100.0
        w_live_cm = ll_line / 100.0

        delta_total = (5 * w_total_cm * span_cm ** 4) / (384 * E * ix)
        delta_live = (5 * w_live_cm * span_cm ** 4) / (384 * E * ix)
        limit_total = span_cm / 240.0
        limit_live = span_cm / 360.0

        self.add_step(
            "การโก่งตัวรวม DL+LL",
            r"\Delta_{tot} = \frac{5 w_{DL+LL} L^4}{384 E I_x}",
            f"= 5 \\times {w_total_cm:.4f} \\times {span_cm:.1f}^4 / (384 \\times {E:.2e} \\times {ix:.2f})",
            f"= {delta_total:.3f}\\,\\text{{cm}}",
            note="สูตรการโก่งตัวคานรับแรงกระจาย (Simply Supported Beam)"
        )
        self.add_step(
            "การโก่งตัวจาก Live Load",
            r"\Delta_L = \frac{5 w_L L^4}{384 E I_x}",
            f"= 5 \\times {w_live_cm:.4f} \\times {span_cm:.1f}^4 / (384 \\times {E:.2e} \\times {ix:.2f})",
            f"= {delta_live:.3f}\\,\\text{{cm}}",
            note="คำนวณการโก่งตัวจาก Live Load เพียงอย่างเดียว"
        )
        self.add_step(
            "เกณฑ์การโก่งตัวตามกฎกระทรวง วสท.",
            r"\Delta_{allow,tot} = \frac{L}{240},\quad \Delta_{allow,L} = \frac{L}{360}",
            f"= {span_cm:.1f}/240,\\; {span_cm:.1f}/360",
            f"= {limit_total:.3f},\\; {limit_live:.3f}\\,\\text{{cm}}",
            note="หลักเกณฑ์ตามกฎกระทรวง ฉบับที่ 55 (พ.ศ. 2543) วิศวกรรมสถานแห่งประเทศไทย"
        )

        defl_total_ok = delta_total <= limit_total
        defl_live_ok = delta_live <= limit_live
        defl_pass = defl_total_ok and defl_live_ok

        checks = {
            'Capacity': {
                'Phi_Mn': phi_mn,
                'Phi_Vn': phi_vn,
                'Delta_Limit_Total': limit_total,
                'Delta_Limit_Live': limit_live,
            },
            'Demand': {
                'Mu': mu,
                'Vu': vu,
                'Delta_Total': delta_total,
                'Delta_Live': delta_live,
            },
            'Ratios': {
                'Moment': moment_ratio,
                'Shear': shear_ratio,
                'Deflection': max(
                    delta_total / limit_total if limit_total else float('inf'),
                    delta_live / limit_live if limit_live else float('inf'),
                ),
                'h/t': h_mm / t_mm,
            },
            'Status': {
                'Moment': moment_pass,
                'Shear': shear_pass,
                'Deflection': defl_pass,
            },
            'Deflection': {
                'Total': {
                    'value': delta_total,
                    'limit': limit_total,
                    'ratio': delta_total / limit_total if limit_total else float('inf'),
                    'pass': defl_total_ok,
                },
                'Live': {
                    'value': delta_live,
                    'limit': limit_live,
                    'ratio': delta_live / limit_live if limit_live else float('inf'),
                    'pass': defl_live_ok,
                },
            }
        }

        combinations = {
            'Wu1': wu1,
            'Wu2_pos': wu2_pos,
            'Wu2_neg': wu2_neg,
            'Wu_design': wu_design,
            'Controlling': controlling_combo,
        }

        forces = {'Mu_kgm': mu, 'Vu_kg': vu}

        return {
            'Loads': loads,
            'Combinations': combinations,
            'Forces': forces,
            'Checks': checks,
            'Steps': self.steps,
        }

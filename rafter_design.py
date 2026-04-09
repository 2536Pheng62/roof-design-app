import math

class RafterDesign:
    def __init__(self, section_data, geometry, loads, materials):
        """
        Initialize the RafterDesign object.
        
        Args:
            section_data (dict): Properties like Zx, Ix, Sx, Area, d, bf, tf, tw, ry
            geometry (dict): span (m), spacing (m), slope (degrees), Lb (m)
            loads (dict): DL, LL, WL (kg/m2)
            materials (dict): Fy, E (ksc)
        """
        self.sec = section_data
        self.geo = geometry
        self.loads = loads
        self.mat = materials
        self.log = [] # List of steps
        
    def add_step(self, title, latex, subst, result, status=None, note=None):
        lines = [latex]
        if subst is not None:
            lines.append(subst)
        if result is not None:
            lines.append(result)
        aligned = r"\begin{aligned}" + " \\ ".join(lines) + r"\end{aligned}"
        self.log.append({
            'title': title,
            'latex': aligned,
            'status': status,
            'note': note
        })

    def run_design(self):
        """Run all steps and return full results with detailed log."""
        self.log = [] # Reset log
        
        # --- Step A: Load Transformation ---
        # Geometry
        span_horiz = self.geo['span'] # span assumed horizontal projection based on standard input
        spacing = self.geo['spacing']
        slope_deg = self.geo['slope']
        slope_rad = math.radians(slope_deg)
        cos_theta = math.cos(slope_rad)
        sin_theta = math.sin(slope_rad)
        span_slope = span_horiz / cos_theta
        
        # Loads (Assumptions: DL is gravity, LL is horizontal proj, WL is normal)
        dl_surf = self.loads['DL']
        ll_surf = self.loads['LL']
        wl_surf = self.loads['WL']
        
        self_weight = self.sec.get('Weight', 0) # kg/m
        
        # Dead Load (Gravity)
        # Convert surface DL (on slope) to vertical line load?
        # Standard: DL is usually specified on slope area for roofing.
        # Vertical Resultant = DL_surf * Spacing
        # Line load w_DL_vert acts vertically.
        w_dl_vert = (dl_surf * spacing) + self_weight
        self.add_step(
            "น้ำหนักบรรทุกคงที่ (แนวดิ่ง)",
            r"w_{DL} = (DL_{surf} \times S) + W_{self}",
            f"w_{{DL}} = ({dl_surf} \\times {spacing}) + {self_weight}",
            f"{w_dl_vert:.2f} กก./ม."
        )
        
        # Live Load (Gravity)
        # LL on horizontal projection.
        # Vertical Resultant = LL_surf * Spacing
        w_ll_vert = ll_surf * spacing
        self.add_step(
            "น้ำหนักใช้งาน (แนวดิ่ง)",
            r"w_{LL} = LL_{surf} \times S",
            f"w_{{LL}} = {ll_surf} \\times {spacing}",
            f"{w_ll_vert:.2f} กก./ม."
        )
        
        # Wind Load (Perpendicular to Roof)
        # Assumed Normal to surface
        w_wl_norm = wl_surf * spacing
        self.add_step(
            "แรงลมตั้งฉากผิวหลังคา",
            r"w_{WL} = WL_{surf} \times S",
            f"w_{{WL}} = {wl_surf} \\times {spacing}",
            f"{w_wl_norm:.2f} กก./ม."
        )
        
        loads = {
            'SelfWeight': self_weight,
            'w_dl_vert': w_dl_vert,
            'w_ll_vert': w_ll_vert,
            'w_wl_norm': w_wl_norm
        }

        # --- Step B: Combinations (LRFD/EIT) ---
        # 1. Gravity Only: 1.4D + 1.7L
        # Calculate Vertical Combination first, then resolving forces?
        # Or resolve first?
        # Generally easier to combine acting forces.
        
        # Decompose Vertical Gravity Loads into Normal component
        # w_n = w_vert * cos(theta)
        w_dl_norm = w_dl_vert * cos_theta
        w_ll_norm = w_ll_vert * cos_theta
        
        self.add_step(
            "แรงฉากกับแนวหน้าตัดจากน้ำหนักบรรทุก",
            r"w_{n} = w_{vert} \cos(\theta)",
            f"w_{{DL,n}} = {w_dl_vert:.2f}\\cos({slope_deg}^\\circ) = {w_dl_norm:.2f}, \\quad w_{{LL,n}} = {w_ll_vert:.2f}\\cos({slope_deg}^\\circ) = {w_ll_norm:.2f}",
            f"DL_n: {w_dl_norm:.2f}, LL_n: {w_ll_norm:.2f} กก./ม."
        )

        # Load Combinations ตาม LRFD (หลัก วสท. และ AISC 360)
        # LC1: โหลดบรรทุกเต็มรูปแบบ
        wu1_norm = 1.4 * w_dl_norm + 1.7 * w_ll_norm
        self.add_step(
            "LC1: 1.4D + 1.7L (ตาม LRFD)",
            r"w_{u1} = 1.4 w_{DL,n} + 1.7 w_{LL,n}",
            f"w_{{u1}} = 1.4({w_dl_norm:.2f}) + 1.7({w_ll_norm:.2f})",
            f"{wu1_norm:.2f} กก./ม.",
            note="โหลดแฟคเตอร์ตามหลัก LRFD ของ วสท."
        )
        
        # LC2: พิจารณาแรงลมร่วมด้วย
        wu2_norm = 0.75 * (1.4 * w_dl_norm + 1.7 * w_ll_norm) + 1.6 * w_wl_norm
        self.add_step(
            "LC2: 0.75(1.4D+1.7L) + 1.6W (ตาม LRFD)",
            r"w_{u2} = 0.75(1.4 w_{DL,n} + 1.7 w_{LL,n}) + 1.6 w_{WL}",
            f"w_{{u2}} = 0.75(1.4 \\times {w_dl_norm:.2f} + 1.7 \\times {w_ll_norm:.2f}) + 1.6({w_wl_norm:.2f})",
            f"{wu2_norm:.2f} กก./ม.",
            note="พิจารณาแรงลมร่วมตามมาตรฐานไทย"
        )
        
        wu_design = max(abs(wu1_norm), abs(wu2_norm)) # Use absolute max for design
        combinations = {'Wu1': wu1_norm, 'Wu2': wu2_norm, 'Wu_design': wu_design}
        
        # --- Step C: Internal Forces ---
        # Moment (Simple Span, Distributed Load)
        # M_u = w * L^2 / 8. L is span length along member = span_slope
        mu_kgm = (wu_design * span_slope**2) / 8
        self.add_step(
            "โมเมนต์ออกแบบ (M_u)",
            r"M_u = \frac{w_u L_{slope}^2}{8}",
            f"M_u = \\frac{{{wu_design:.2f} \\times {span_slope:.2f}^2}}{{8}}",
            f"{mu_kgm:.2f} กก.-ม."
        )
        
        # Shear (Simple Span)
        # V_u = w * L / 2
        vu_kg = (wu_design * span_slope) / 2
        self.add_step(
            "แรงเฉือนออกแบบ (V_u)",
            r"V_u = \frac{w_u L_{slope}}{2}",
            f"V_u = \\frac{{{wu_design:.2f} \\times {span_slope:.2f}}}{{2}}",
            f"{vu_kg:.2f} กก."
        )
        
        forces = {'Mu_kgm': mu_kgm, 'Vu_kg': vu_kg}
        
        # --- Step D: Capacity Checks (AISC 360 Hot-Rolled) ---
        # Properties
        fy = self.mat['Fy'] # ksc
        E = self.mat['E']   # ksc
        zx = self.sec['Zx'] # cm3
        sx = self.sec['Sx'] # cm3
        ix = self.sec['Ix'] # cm4
        iy = self.sec.get('Iy', self.sec['Area'] * self.sec['ry']**2) # cm4 approx if missing
        bf = self.sec['bf'] # cm
        tf = self.sec['tf'] # cm
        h = self.sec['d']   # cm (Depth)
        tw = self.sec['tw'] # cm
        aw = h * tw         # cm2 (Approx for rolled shape shear area)
        ry = self.sec['ry'] # cm
        
        # 1. Compactness Check
        # Flange
        lambda_f = (bf/2) / tf # bf is usually total width
        lambda_p_f = 0.38 * math.sqrt(E / fy)
        lambda_r_f = 1.0 * math.sqrt(E / fy)
        
        compact_f = lambda_f <= lambda_p_f
        
        self.add_step(
            "ตรวจสอบความเพรียวบาง (ปีก)",
            r"\lambda_f = \frac{b_f}{2t_f} \le \lambda_p = 0.38\sqrt{\frac{E}{F_y}}",
            f"{lambda_f:.2f} \\le {lambda_p_f:.2f}",
            "ปีกกะทัดรัด" if compact_f else ("ปีกกึ่งกะทัดรัด" if lambda_f <= lambda_r_f else "ปีกบางมาก"),
            status="PASS" if compact_f else "WARNING"
        )

        # Web
        h_web = h - 2*tf # Clear distance approx
        lambda_w = h_web / tw
        lambda_p_w = 3.76 * math.sqrt(E / fy)
        compact_w = lambda_w <= lambda_p_w
        
        self.add_step(
            "ตรวจสอบความเพรียวบาง (เอว)",
            r"\lambda_w = \frac{h}{t_w} \le \lambda_p = 3.76\sqrt{\frac{E}{F_y}}",
            f"{lambda_w:.2f} \\le {lambda_p_w:.2f}",
            "เอวกะทัดรัด" if compact_w else "เอวบาง/เกินเกณฑ์",
            status="PASS" if compact_w else "WARNING"
        )
        
        # 2. Moment Capacity (Phi Mn)
        # LTB Constants
        # Available Data: rts, J, h0. Create if missing.
        h0 = self.sec.get('h0', h - tf) # Distance between flange centroids
        J = self.sec.get('J', (2 * bf * tf**3 + (h - 2*tf) * tw**3) / 3) # Torsion constant approx
        
        # rts calculation if missing
        # rts^2 = sqrt(Iy * Cw) / Sx
        # Cw = Iy * h0^2 / 4
        cw = (iy * h0**2) / 4
        if sx > 0 and cw >= 0:
             rts_calc = math.sqrt(math.sqrt(iy * cw) / sx)
        else:
             rts_calc = 1.0 # Fallback safety
        
        rts = self.sec.get('rts', rts_calc)
        if rts <= 0: rts = 1.0 # Avoid division by zero later
        
        # Lengths
        Lb = self.geo['Lb'] * 100 # cm (Unbraced Length)
        
        # Lp = 1.76 * ry * sqrt(E/Fy)
        Lp = 1.76 * ry * math.sqrt(E / fy)
        
        # Lr
        # Lr = 1.95 * rts * E / (0.7Fy) * sqrt... complicated.
        # Simplified AISC formula for Lr:
        # Lr = 1.95 * rts * (E / (0.7 * fy)) * sqrt( (J*c)/(Sx*h0) + sqrt( ((J*c)/(Sx*h0))^2 + 6.76 * (0.7*fy/E)^2 ) )
        c = 1.0 # Doubly symmetric
        term1 = (J * c) / (sx * h0)
        term2 = (0.7 * fy / E)**2
        Lr = 1.95 * rts * (E / (0.7 * fy)) * math.sqrt(term1 + math.sqrt(term1**2 + 6.76 * term2))
        
        self.add_step(
            "ค่าความยาววิกฤตสำหรับ LTB",
            r"L_p = 1.76 r_y \sqrt{\frac{E}{F_y}}, \quad L_r",
            f"L_p = {Lp:.0f} cm, \\quad L_r = {Lr:.0f} cm, \\quad L_b = {Lb:.0f} cm",
            f"ช่วงการวิบัติ: {('โซน 1 (ยอมคราก)' if Lb <= Lp else ('โซน 2 (วิบัติ LTB ไม่เป็นเชิงเส้น)' if Lb <= Lr else 'โซน 3 (วิบัติ LTB เชิงเส้น)'))}"
        )
        
        # Mp
        mp_kgm = (fy * zx) / 100 # kg-m
        
        # Mn Calculation
        if Lb <= Lp:
            mn = mp_kgm * 100 # kg-cm
            zone = "ยอมคราก"
            formula = r"M_n = M_p"
        elif Lb <= Lr:
            cb = 1.0 # Conservative
            mn = cb * (mp_kgm*100 - (mp_kgm*100 - 0.7 * fy * sx) * ((Lb - Lp) / (Lr - Lp)))
            mn = min(mn, mp_kgm*100)
            zone = "LTB ไม่เป็นเชิงเส้น"
            formula = r"M_n = C_b [M_p - (M_p - 0.7F_y S_x)(\frac{L_b - L_p}{L_r - L_p})]"
        else:
            cb = 1.0
            # Fcr = (Cb * pi^2 * E) / (Lb/rts)^2 * sqrt(1 + 0.078 * (J*c)/(Sx*h0) * (Lb/rts)^2)
            lb_rts = Lb / rts
            fcr = (cb * math.pi**2 * E) / (lb_rts**2) * math.sqrt(1 + 0.078 * (J * c) / (sx * h0) * (lb_rts**2))
            mn = fcr * sx
            mn = min(mn, mp_kgm*100)
            zone = "LTB เชิงเส้น"
            formula = r"M_n = F_{cr} S_x"
            
        mn_kgm_final = mn / 100
        phi = 0.90  # ϕ = 0.90 สำหรับ bending (ตาม AISC 360 และ LRFD)
        phi_mn = phi * mn_kgm_final
        
        moment_ratio = mu_kgm / phi_mn
        moment_pass = moment_ratio <= 1.0
        
        self.add_step(
            f"กำลังดัดรับ ({zone}) - ตาม AISC 360",
            formula,
            f"M_n = {mn_kgm_final:.2f} กก.-ม.",
            f"\\phi M_n = {phi_mn:.2f} กก.-ม. (อัตราส่วน = {moment_ratio:.2f})",
            status="PASS" if moment_pass else "FAIL",
            note="ϕ = 0.90 สำหรับการดัด (LRFD)"
        )
        
        # กำลังเฉือนรับ ตาม AISC 360
        vn = 0.6 * fy * aw
        phi_v = 1.0 # ϕ = 1.0 สำหรับ shear (AISC 360 G2.1a: h/tw <= 2.24√(E/Fy))
        # หมายเหตุ: ถ้า h/tw เกินเกณฑ์ อาจต้องใช้ ϕ = 0.9
        phi_vn = phi_v * vn
        
        shear_ratio = vu_kg / phi_vn
        shear_pass = shear_ratio <= 1.0
        
        self.add_step(
            "กำลังเฉือนรับ - ตาม AISC 360",
            r"\phi V_n = 1.0 \times 0.6 F_y A_w",
            f"\\phi V_n = 1.0 \\times 0.6 \\times {fy} \\times {aw:.2f}",
            f"{phi_vn:.2f} กก. (อัตราส่วน = {shear_ratio:.2f})",
            status="PASS" if shear_pass else "FAIL",
            note="ϕ = 1.0 สำหรับการเฉือน (AISC 360)"
        )
        
        # 4. Deflection
        # Service Load (Vertical) -> Normal component
        # w_ser_vert = w_dl_vert + w_ll_vert
        # w_ser_norm = w_ser_vert * cos_theta
        w_total_norm = (w_dl_vert + w_ll_vert) * cos_theta
        w_live_norm = w_ll_vert * cos_theta
        w_total_cm = w_total_norm / 100
        w_live_cm = w_live_norm / 100
        
        span_cm = span_slope * 100 # L along beam
        
        delta_total = (5 * w_total_cm * span_cm**4) / (384 * E * ix)
        delta_live = (5 * w_live_cm * span_cm**4) / (384 * E * ix)
        limit_total = span_cm / 240
        limit_live = span_cm / 360
        
        defl_total_ok = delta_total <= limit_total
        defl_live_ok = delta_live <= limit_live
        defl_ratio = max(
            delta_total / limit_total if limit_total else float('inf'),
            delta_live / limit_live if limit_live else float('inf')
        )
        defl_pass = defl_total_ok and defl_live_ok
        
        self.add_step(
            "การโก่งตัวรวม DL+LL",
            r"\Delta_{tot} = \frac{5 w_{tot} L^4}{384 E I_x}",
            f"= \\frac{{5 \\times {w_total_cm:.2f} \\times {span_cm:.0f}^4}}{{384 \\times {E} \\times {ix}}}",
            f"= {delta_total:.2f} \\text{{ cm}}",
            status="PASS" if defl_total_ok else "FAIL",
            note="เกณฑ์ L/240 สำหรับ Total Load (DL+LL)"
        )
        self.add_step(
            "การโก่งตัวจาก Live Load",
            r"\Delta_L = \frac{5 w_L L^4}{384 E I_x}",
            f"= \\frac{{5 \\times {w_live_cm:.2f} \\times {span_cm:.0f}^4}}{{384 \\times {E} \\times {ix}}}",
            f"= {delta_live:.2f} \\text{{ cm}}",
            status="PASS" if defl_live_ok else "FAIL",
            note="เกณฑ์ L/360 สำหรับ Live Load เพียงอย่างเดียว"
        )
        self.add_step(
            "เกณฑ์การโก่งตัวตาม กฎกระทรวง ฉบับที่ 55 (พ.ศ. 2543)",
            r"\Delta_{allow,tot} = \frac{L}{240},\; \Delta_{allow,L} = \frac{L}{360}",
            f"= {span_cm:.0f}/240,\\; {span_cm:.0f}/360",
            f"= {limit_total:.2f},\\; {limit_live:.2f} \\text{{ cm}}",
            note="หลักเกณฑ์ของ วิศวกรรมสถานแห่งประเทศไทย"
        )
        
        checks = {
            'Capacity': {
                'Phi_Mn': phi_mn,
                'Phi_Vn': phi_vn,
                'Delta_Limit_Total': limit_total,
                'Delta_Limit_Live': limit_live
            },
            'Demand': {
                'Mu': mu_kgm,
                'Vu': vu_kg,
                'Delta_Total': delta_total,
                'Delta_Live': delta_live
            },
            'Ratios': {
                'Moment': moment_ratio,
                'Shear': shear_ratio,
                'Deflection': defl_ratio,
                'Compactness': lambda_f/lambda_p_f
            },
            'Status': {'Moment': moment_pass, 'Shear': shear_pass, 'Deflection': defl_pass},
            'Deflection': {
                'Total': {
                    'value': delta_total,
                    'limit': limit_total,
                    'ratio': delta_total / limit_total if limit_total else float('inf'),
                    'pass': defl_total_ok
                },
                'Live': {
                    'value': delta_live,
                    'limit': limit_live,
                    'ratio': delta_live / limit_live if limit_live else float('inf'),
                    'pass': defl_live_ok
                }
            }
        }
        
        return {
            'Loads': loads,
            'Combinations': combinations,
            'Forces': forces,
            'Checks': checks,
            'Steps': self.log
        }

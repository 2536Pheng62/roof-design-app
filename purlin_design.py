import math

class PurlinDesign:
    def __init__(self, section_data, geometry, loads, materials):
        """
        Initialize the Design object.
        """
        self.sec = section_data
        self.geo = geometry
        self.loads = loads
        self.mat = materials
        self.log = [] # List of steps
        
    def add_step(self, title, latex, subst, result, status=None):
        self.log.append({
            'title': title,
            'latex': latex,
            'subst': subst,
            'result': result,
            'status': status
        })

    def run_design(self):
        """Run all steps and return full results with detailed log."""
        self.log = [] # Reset log
        
        # --- Step A: Load Transformation ---
        spacing = self.geo['spacing']
        span = self.geo['span']
        slope = self.geo['slope']
        slope_rad = math.radians(slope)
        cos_slope = math.cos(slope_rad)
        
        dl_surf = self.loads['DL']
        ll_surf = self.loads['LL']
        wl_surf = self.loads['WL']
        
        self_weight = self.sec['Weight']
        
        # Dead Load
        dl_line = (dl_surf * spacing) + self_weight
        self.add_step(
            "Dead Load (DL)",
            r"w_{DL} = (DL_{surf} \times S) + W_{self}",
            f"w_{{DL}} = ({dl_surf} \\times {spacing}) + {self_weight}",
            f"{dl_line:.2f} kg/m"
        )
        
        # Live Load
        ll_line = ll_surf * spacing
        self.add_step(
            "Live Load (LL)",
            r"w_{LL} = LL_{surf} \times S",
            f"w_{{LL}} = {ll_surf} \\times {spacing}",
            f"{ll_line:.2f} kg/m"
        )
        
        # Wind Load
        wl_perp = (wl_surf * spacing) * cos_slope
        self.add_step(
            "Wind Load (Perpendicular)",
            r"w_{WL} = (WL_{surf} \times S) \times \cos(\theta)",
            f"w_{{WL}} = ({wl_surf} \\times {spacing}) \\times {cos_slope:.4f}",
            f"{wl_perp:.2f} kg/m"
        )
        
        loads = {
            'SelfWeight': self_weight,
            'DL_line': dl_line,
            'LL_line': ll_line,
            'WL_perp': wl_perp
        }

        # --- Step B: Combinations ---
        # Wu1
        wu1 = 1.4 * dl_line + 1.7 * ll_line
        self.add_step(
            "Load Combination 1 (Gravity)",
            r"w_{u1} = 1.4D + 1.7L",
            f"w_{{u1}} = 1.4({dl_line:.2f}) + 1.7({ll_line:.2f})",
            f"{wu1:.2f} kg/m"
        )
        
        # Wu2
        wu2 = 0.75 * (1.4 * dl_line + 1.7 * ll_line) + 1.6 * wl_perp
        self.add_step(
            "Load Combination 2 (Combined)",
            r"w_{u2} = 0.75(1.4D + 1.7L) + 1.6W",
            f"w_{{u2}} = 0.75(1.4 \\times {dl_line:.2f} + 1.7 \\times {ll_line:.2f}) + 1.6({wl_perp:.2f})",
            f"{wu2:.2f} kg/m"
        )
        
        wu_design = max(wu1, wu2)
        combinations = {'Wu1': wu1, 'Wu2': wu2, 'Wu_design': wu_design}
        
        # --- Step C: Internal Forces ---
        # Moment
        mu = (wu_design * span**2) / 8
        self.add_step(
            "Design Moment (Mu)",
            r"M_u = \frac{w_u L^2}{8}",
            f"M_u = \\frac{{{wu_design:.2f} \\times {span}^2}}{{8}}",
            f"{mu:.2f} kg-m"
        )
        
        # Shear
        vu = (wu_design * span) / 2
        self.add_step(
            "Design Shear (Vu)",
            r"V_u = \frac{w_u L}{2}",
            f"V_u = \\frac{{{wu_design:.2f} \\times {span}}}{{2}}",
            f"{vu:.2f} kg"
        )
        
        forces = {'Mu_kgm': mu, 'Vu_kg': vu}

        # --- Step D: Checks ---
        zx = self.sec['Zx']
        fy = self.mat['Fy']
        h_mm = self.sec['h']
        t_mm = self.sec['t']
        aw_cm2 = (h_mm * t_mm) / 100
        
        # 1. Moment Capacity
        mn_kgm = (zx * fy) / 100
        phi_mn = 0.90 * mn_kgm
        moment_ratio = mu / phi_mn
        moment_pass = moment_ratio <= 1.0
        
        self.add_step(
            "Moment Capacity (Phi Mn)",
            r"\phi M_n = 0.90 (Z_x F_y)",
            f"\\phi M_n = 0.90 ({zx} \\times {fy}) / 100",
            f"{phi_mn:.2f} kg-m",
            status="PASS" if moment_pass else "FAIL"
        )
        
        # 2. Shear Capacity
        vn = 0.6 * fy * aw_cm2
        phi_vn = vn # Phi=1.0 assumed
        shear_ratio = vu / phi_vn
        shear_pass = shear_ratio <= 1.0
        
        self.add_step(
            "Shear Capacity (Phi Vn)",
            r"\phi V_n = 0.6 F_y A_w",
            f"\\phi V_n = 0.6 \\times {fy} \\times {aw_cm2:.2f}",
            f"{phi_vn:.2f} kg",
            status="PASS" if shear_pass else "FAIL"
        )
        
        # 3. Deflection
        w_ser = dl_line + ll_line
        e_ksc = self.mat['E']
        ix = self.sec['Ix']
        
        # Convert to cm units for formula
        w_ser_cm = w_ser / 100 # kg/cm
        span_cm = span * 100
        
        delta = (5 * w_ser_cm * (span_cm**4)) / (384 * e_ksc * ix)
        limit = span_cm / 360
        defl_ratio = delta / limit
        defl_pass = defl_ratio <= 1.0
        
        self.add_step(
            "Deflection (Delta)",
            r"\Delta = \frac{5 w_{ser} L^4}{384 E I_x}",
            f"\\Delta = \\frac{{5 \\times {w_ser_cm:.2f} \\times {span_cm:.0f}^4}}{{384 \\times {e_ksc} \\times {ix}}}",
            f"{delta:.2f} cm (Limit: {limit:.2f} cm)",
            status="PASS" if defl_pass else "FAIL"
        )
        
        checks = {
            'Capacity': {'Phi_Mn': phi_mn, 'Phi_Vn': phi_vn, 'Delta_Limit': limit},
            'Demand': {'Mu': mu, 'Vu': vu, 'Delta': delta},
            'Ratios': {'Moment': moment_ratio, 'Shear': shear_ratio, 'Deflection': defl_ratio, 'h/t': h_mm/t_mm},
            'Status': {'Moment': moment_pass, 'Shear': shear_pass, 'Deflection': defl_pass}
        }

        return {
            'Loads': loads,
            'Combinations': combinations,
            'Forces': forces,
            'Checks': checks,
            'Steps': self.log
        }

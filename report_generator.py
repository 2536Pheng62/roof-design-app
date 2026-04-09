from fpdf import FPDF
import os
import io
import matplotlib.pyplot as plt
import matplotlib

# Set backend to Agg to avoid GUI issues in threads
matplotlib.use('Agg')

class BaseReportGenerator(FPDF):
    def __init__(self, project_info, inputs, results, section_data):
        super().__init__()
        self.project_info = project_info
        self.inputs = inputs
        self.results = results
        self.sec = section_data
        
        # Font settings
        self.font_path_regular = "THSarabunNew.ttf"
        self.font_path_bold = "THSarabunNew Bold.ttf"
        
        # Fallback if bold missing
        if not os.path.exists(self.font_path_bold):
             self.font_path_bold = self.font_path_regular

        self.has_thai_font = False
        self._setup_font()

    def sanitize(self, text):
        """Clean text to avoid encoding errors if Thai font is missing."""
        if self.has_thai_font:
            return str(text)
        
        # If no Thai font, strip non-latin chars to prevent 'ordinal not in range(256)'
        # or replace them.
        try:
            return text.encode('latin-1', 'ignore').decode('latin-1')
        except:
            return str(text).encode('ascii', 'ignore').decode('ascii')


    def _setup_font(self):
        self.add_page()
        if os.path.exists(self.font_path_regular):
            try:
                # Add font (supports both fpdf and fpdf2 styles safely)
                try:
                    self.add_font('Sarabun', '', self.font_path_regular)
                    self.add_font('Sarabun', 'B', self.font_path_bold)
                except TypeError:
                    self.add_font('Sarabun', '', self.font_path_regular, uni=True)
                    self.add_font('Sarabun', 'B', self.font_path_bold, uni=True)
                
                self.set_font('Sarabun', '', 14)
                self.has_thai_font = True
            except Exception as e:
                print(f"Error loading Thai font: {e}")
                self.set_font('Arial', '', 12)
        else:
            print(f"Warning: {self.font_path_regular} not found. Using Arial.")
            self.set_font('Arial', '', 12)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        if self.has_thai_font:
             self.set_font('Sarabun', '', 10)
        else:
             self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.ln(5)
        if self.has_thai_font:
            self.set_font('Sarabun', 'B', 16)
        else:
            self.set_font('Arial', 'B', 14)
        
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, self.sanitize(title), 0, 1, 'L', fill=True)
        
        # Reset
        if self.has_thai_font:
            self.set_font('Sarabun', '', 14)
        else:
            self.set_font('Arial', '', 12)
        self.ln(2)

    def kv_line(self, key, value):
        self.set_font('', 'B')
        self.cell(50, 7, f"{self.sanitize(key)}:", 0, 0)
        self.set_font('', '')
        self.cell(0, 7, f"{self.sanitize(value)}", 0, 1)

    def _render_latex(self, formula, filename):
        try:
            fig = plt.figure(figsize=(0.1, 0.1))
            # Clean up unsupported commands for Matplotlib
            clean_formula = formula.strip().strip('$')
            clean_formula = clean_formula.replace(r'\begin{aligned}', '').replace(r'\end{aligned}', '')
            clean_formula = clean_formula.replace(r'\\', r'\quad ')  # Replace newline with space
            
            if not clean_formula: return None
            
            txt = f"${clean_formula}$"
            fig.text(0, 0, txt, fontsize=12, va='bottom', ha='left')
            
            buf = io.BytesIO()
            plt.axis('off')
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, pad_inches=0.1, 
                       transparent=False, facecolor='white')
            plt.close(fig)
            
            buf.seek(0)
            with open(filename, 'wb') as f:
                f.write(buf.read())
            return filename
        except Exception as e:
            print(f"Error rendering latex for '{formula}': {e}")
            return None

    def add_project_info(self):
        self.section_title("1. ข้อมูลโครงการ (Project Information)")
        self.kv_line("Project Name", self.project_info.get('Project Name', '-'))
        self.kv_line("Owner", self.project_info.get('Owner', '-'))
        self.kv_line("Engineer", self.project_info.get('Engineer', '-'))
        self.ln(5)

    def add_detailed_steps(self):
        self.section_title("4. รายการคำนวณละเอียด (Detailed Calculations)")
        steps = self.results.get('Steps', [])
        if not steps:
            self.cell(0, 8, self.sanitize("No detailed steps available."), 0, 1)
            return

        temp_images = []
        for i, step in enumerate(steps):
            if self.get_y() > 250:
                self.add_page()

            self.set_font('', 'B')
            self.cell(0, 8, self.sanitize(f"{i+1}. {step.get('title','')}") , 0, 1)
            self.set_font('', '')

            latex_block = step.get('latex')
            if latex_block:
                f_path = self._render_latex(latex_block, f"temp_eq_{i}_f.png")
                if f_path:
                    temp_images.append(f_path)
                    self.image(f_path, x=self.get_x(), y=self.get_y(), h=10)
                    self.ln(12)
                else:
                    self.multi_cell(0, 8, self.sanitize(latex_block))

            note = step.get('note')
            if note:
                self.multi_cell(0, 7, self.sanitize(f"Note: {note}"))

            status = step.get('status')
            if status:
                self.set_font('', 'B')
                self.set_text_color(0, 150, 0) if 'PASS' in status.upper() else self.set_text_color(200, 0, 0)
                self.cell(0, 8, self.sanitize(f"[{status}]"), 0, 1)
                self.set_text_color(0, 0, 0)
                self.set_font('', '')
            else:
                self.ln(4)

            self.set_draw_color(220, 220, 220)
            self.line(self.get_x(), self.get_y()+1, 200, self.get_y()+1)
            self.ln(3)
            self.set_draw_color(0, 0, 0)

        # Cleanup
        for img in temp_images:
            if os.path.exists(img):
                try: os.remove(img)
                except: pass

    def _check_row(self, name, demand, capacity, ratio, status):
        col_w = 38
        self.cell(col_w, 8, self.sanitize(name), 1)
        self.cell(col_w, 8, self.sanitize(demand), 1, 0, 'C')
        self.cell(col_w, 8, self.sanitize(capacity), 1, 0, 'C')
        
        if ratio > 1.0:
            self.set_text_color(200, 0, 0)
            self.set_font('', 'B')
        self.cell(25, 8, f"{ratio:.2f}", 1, 0, 'C')
        self.set_text_color(0, 0, 0)
        self.set_font('', '')
        
        res_text = "PASS" if status else "FAIL"
        self.set_font('', 'B')
        if not status:
            self.set_text_color(255, 255, 255)
            self.set_fill_color(200, 50, 50)
        else:
            self.set_text_color(255, 255, 255)
            self.set_fill_color(50, 150, 50)
        self.cell(30, 8, self.sanitize(res_text), 1, 1, 'C', True)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)
        self.set_font('', '')

    def generate(self, output_path="report.pdf"):
        # Template method
        if self.has_thai_font:
            self.set_font('Sarabun', 'B', 22)
        else:
            self.set_font('Arial', 'B', 20)
        
        self.cell(0, 15, self.sanitize(self.report_title), 0, 1, 'C')
        self.ln(5)
        
        self.add_project_info()
        self.add_input_summary()
        self.add_detailed_steps()
        self.add_calculation_summary()
        self.add_conclusion()
        
        try:
            self.output(output_path)
            return True, output_path
        except Exception as e:
            return False, str(e)


class PurlinReportGenerator(BaseReportGenerator):
    report_title = "รายการคำนวณออกแบบแปเหล็ก (Cold-Formed Steel Purlin)"

    def add_input_summary(self):
        self.section_title("2. พารามิเตอร์การออกแบบ (Design Parameters)")
        geo = self.inputs.get('geometry', {})
        lds = self.inputs.get('loads', {})
        mat = self.inputs.get('materials', {})
        
        col_w = 63
        self.set_font('', 'B')
        self.cell(col_w, 8, self.sanitize("Geometry"), 1, 0, 'C')
        self.cell(col_w, 8, self.sanitize("Loads"), 1, 0, 'C')
        self.cell(col_w, 8, self.sanitize("Materials"), 1, 1, 'C')
        self.set_font('', '')
        
        self.cell(col_w, 8, self.sanitize(f"Spacing: {geo.get('spacing','-')} m"), 1)
        self.cell(col_w, 8, self.sanitize(f"DL: {lds.get('DL','-')} kg/m2"), 1)
        self.cell(col_w, 8, self.sanitize(f"Fy: {mat.get('Fy','-')} ksc"), 1)
        self.ln()
        
        self.cell(col_w, 8, self.sanitize(f"Span: {geo.get('span','-')} m"), 1)
        self.cell(col_w, 8, self.sanitize(f"LL: {lds.get('LL','-')} kg/m2"), 1)
        self.cell(col_w, 8, self.sanitize(f"E: {mat.get('E','-')} ksc"), 1)
        self.ln()
        
        self.cell(col_w, 8, self.sanitize(f"Slope: {geo.get('slope','-')} deg"), 1)
        self.cell(col_w, 8, self.sanitize(f"WL: {lds.get('WL','-')} kg/m2"), 1)
        self.cell(col_w, 8, self.sanitize(""), 1)
        self.ln(10)
        
        self.section_title("3. คุณสมบัติหน้าตัด (Section Properties)")
        self.kv_line("Section Name", self.sec.get('name', 'Unknown'))
        props = f"Weight: {self.sec.get('Weight')} kg/m  |  Ix: {self.sec.get('Ix')} cm4  |  Zx: {self.sec.get('Zx')} cm3"
        self.multi_cell(0, 8, self.sanitize(props), border=1, align='C')
        self.ln(5)

    def add_calculation_summary(self):
        if self.get_y() > 220: self.add_page()
        self.section_title("5. สรุปผลการออกแบบ (Summary of Results)")
        
        checks = self.results.get('Checks', {})
        demand = checks.get('Demand', {})
        capacity = checks.get('Capacity', {})
        ratios = checks.get('Ratios', {})
        status = checks.get('Status', {})
        
        # Header
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        self.set_font('', 'B')
        self.cell(38, 9, self.sanitize("Check"), 1, 0, 'C', True)
        self.cell(38, 9, self.sanitize("Demand"), 1, 0, 'C', True)
        self.cell(38, 9, self.sanitize("Capacity"), 1, 0, 'C', True)
        self.cell(25, 9, self.sanitize("Ratio"), 1, 0, 'C', True)
        self.cell(30, 9, self.sanitize("Result"), 1, 1, 'C', True)
        self.set_text_color(0, 0, 0)
        self.set_font('', '')

        self._check_row("Moment", f"{demand.get('Mu',0):.2f}", f"{capacity.get('Phi_Mn',0):.2f}", ratios.get('Moment',0), status.get('Moment',False))
        self._check_row("Shear", f"{demand.get('Vu',0):.2f}", f"{capacity.get('Phi_Vn',0):.2f}", ratios.get('Shear',0), status.get('Shear',False))
        self._check_row("Deflection", f"{demand.get('Delta',0):.2f}", f"{capacity.get('Delta_Limit',0):.2f}", ratios.get('Deflection',0), status.get('Deflection',False))

    def add_conclusion(self):
        self.ln(10)
        ratios = self.results.get('Checks', {}).get('Ratios', {})
        max_r = max(ratios.get('Moment',0), ratios.get('Shear',0), ratios.get('Deflection',0))
        status = "PASSED" if max_r <= 1.0 else "FAILED"
        self.set_font('', 'B')
        self.cell(0, 10, self.sanitize(f"Design Conclusion: {status} (Max Ratio: {max_r:.2f})"), 0, 1)


class RafterReportGenerator(BaseReportGenerator):
    report_title = "รายการคำนวณออกแบบจันทัน (Rafter Design)"

    def add_input_summary(self):
        self.section_title("2. พารามิเตอร์การออกแบบ (Design Parameters)")
        geo = self.inputs.get('geometry', {})
        lds = self.inputs.get('loads', {})
        mat = self.inputs.get('materials', {})
        
        col_w = 63
        self.set_font('', 'B')
        self.cell(col_w, 8, self.sanitize("Geometry"), 1, 0, 'C')
        self.cell(col_w, 8, self.sanitize("Loads"), 1, 0, 'C')
        self.cell(col_w, 8, self.sanitize("Materials"), 1, 1, 'C')
        self.set_font('', '')
        
        # Row 1
        self.cell(col_w, 8, self.sanitize(f"Span: {geo.get('span','-')} m"), 1)
        self.cell(col_w, 8, self.sanitize(f"DL: {lds.get('DL','-')} kg/m2"), 1)
        self.cell(col_w, 8, self.sanitize(f"Fy: {mat.get('Fy','-')} ksc"), 1)
        self.ln()
        # Row 2
        self.cell(col_w, 8, self.sanitize(f"Spacing: {geo.get('spacing','-')} m"), 1)
        self.cell(col_w, 8, self.sanitize(f"LL: {lds.get('LL','-')} kg/m2"), 1)
        self.cell(col_w, 8, self.sanitize(f"E: {mat.get('E','-')} ksc"), 1)
        self.ln()
        # Row 3
        self.cell(col_w, 8, self.sanitize(f"Slope: {geo.get('slope','-')} deg"), 1)
        self.cell(col_w, 8, self.sanitize(f"WL: {lds.get('WL','-')} kg/m2"), 1)
        self.cell(col_w, 8, self.sanitize(f"Lb: {geo.get('Lb','-')} m"), 1)
        self.ln(10)
        
        self.section_title("3. คุณสมบัติหน้าตัด (Section Properties)")
        # Rafter has more props like bf, tf, d
        props_str = f"d: {self.sec.get('d')} cm | bf: {self.sec.get('bf')} cm | tf: {self.sec.get('tf')} cm | tw: {self.sec.get('tw')} cm\n"
        props_str += f"Area: {self.sec.get('Area')} cm2 | Ix: {self.sec.get('Ix')} cm4 | Zx: {self.sec.get('Zx')} cm3 | ry: {self.sec.get('ry')} cm"
        
        self.kv_line("Section", self.sec.get('name', 'Custom'))
        self.multi_cell(0, 8, self.sanitize(props_str), border=1, align='C')
        self.ln(5)

    def add_calculation_summary(self):
        if self.get_y() > 220: self.add_page()
        self.section_title("5. สรุปผลการออกแบบ (Summary of Results)")
        
        checks = self.results.get('Checks', {})
        demand = checks.get('Demand', {})
        capacity = checks.get('Capacity', {})
        ratios = checks.get('Ratios', {})
        status = checks.get('Status', {})
        
        # Header
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        self.set_font('', 'B')
        self.cell(38, 9, self.sanitize("Check"), 1, 0, 'C', True)
        self.cell(38, 9, self.sanitize("Demand"), 1, 0, 'C', True)
        self.cell(38, 9, self.sanitize("Capacity"), 1, 0, 'C', True)
        self.cell(25, 9, self.sanitize("Ratio"), 1, 0, 'C', True)
        self.cell(30, 9, self.sanitize("Result"), 1, 1, 'C', True)
        self.set_text_color(0, 0, 0)
        self.set_font('', '')

        self._check_row("Moment", f"{demand.get('Mu',0):.2f}", f"{capacity.get('Phi_Mn',0):.2f}", ratios.get('Moment',0), status.get('Moment',False))
        self._check_row("Shear", f"{demand.get('Vu',0):.2f}", f"{capacity.get('Phi_Vn',0):.2f}", ratios.get('Shear',0), status.get('Shear',False))
        self._check_row("Deflection", f"{demand.get('Delta',0):.2f}", f"{capacity.get('Delta_Limit',0):.2f}", ratios.get('Deflection',0), status.get('Deflection',False))

    def add_conclusion(self):
        self.ln(10)
        ratios = self.results.get('Checks', {}).get('Ratios', {})
        # Rafter might have Compactness check too, normally just status checks
        # If any check fails (false in status dict), overall fail
        status_dict = self.results.get('Checks', {}).get('Status', {})
        all_passed = all(status_dict.values())
        
        status = "PASSED" if all_passed else "FAILED"
        
        max_r = 0
        if ratios:
            max_r = max(ratios.values())

        self.set_font('', 'B')
        self.cell(0, 10, self.sanitize(f"Design Conclusion: {status} (Max Ratio: {max_r:.2f})"), 0, 1)


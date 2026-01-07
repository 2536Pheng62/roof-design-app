from fpdf import FPDF
import os
import io
import matplotlib.pyplot as plt

class ReportGenerator(FPDF):
    def __init__(self, project_info, inputs, results, section_data):
        super().__init__()
        self.project_info = project_info
        self.inputs = inputs
        self.results = results
        self.sec = section_data
        
        # Font settings
        self.font_path = "THSarabunNew.ttf"
        self.has_thai_font = False
        self._setup_font()

    def _setup_font(self):
        self.add_page()
        if os.path.exists(self.font_path):
            try:
                self.add_font('Sarabun', '', self.font_path, uni=True)
                self.add_font('Sarabun', 'B', self.font_path, uni=True) # Assuming regular can handle bold or separate file invalid
                self.set_font('Sarabun', '', 14)
                self.has_thai_font = True
            except Exception as e:
                print(f"Error loading font: {e}")
                self.set_font('Arial', '', 12)
        else:
            print(f"Warning: {self.font_path} not found. Using Arial.")
            self.set_font('Arial', '', 12)

    def header(self):
        # Logo or Title can go here
        pass

    def footer(self):
        self.set_y(-15)
        if self.has_thai_font:
             self.set_font('Sarabun', '', 10)
        else:
             self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def generate(self, output_path="report.pdf"):
        self.add_title_section()
        self.add_input_summary()
        self.add_detailed_steps()
        self.add_calculation_summary()
        self.add_conclusion()
        
        try:
            self.output(output_path)
            return True, output_path
        except Exception as e:
            return False, str(e)

    def section_title(self, title):
        if self.has_thai_font:
            self.set_font('Sarabun', 'B', 16)
        else:
            self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        # Reset to normal
        if self.has_thai_font:
            self.set_font('Sarabun', '', 14)
        else:
            self.set_font('Arial', '', 12)

    def kv_line(self, key, value):
        # Helper to print Key: Value
        self.cell(50, 8, f"{key}:", 0, 0)
        self.cell(0, 8, f"{value}", 0, 1)

    def _render_latex(self, formula, filename):
        """Render LaTeX formula to an image file using Matplotlib."""
        try:
            # Setup plot
            fig = plt.figure(figsize=(0.1, 0.1))  # Dummy size, will be cropped
            # Add text
            # We wrap in $...$ if not already, but our inputs usually don't have them for the whole string in the logs
            # Actually our logs have mixed. Let's assume the input is valid latex math body.
            # We strip existing $ to avoid double wrapping if simple
            clean_formula = formula.strip().strip('$')
            
            # Simple check for empty
            if not clean_formula:
                return None
                
            txt = f"${clean_formula}$"
            
            # Render
            fig.text(0, 0, txt, fontsize=12, va='bottom', ha='left')
            
            # Save to buffer
            buf = io.BytesIO()
            plt.axis('off')
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, pad_inches=0.1)
            plt.close(fig)
            
            # Save to temp file for FPDF
            buf.seek(0)
            with open(filename, 'wb') as f:
                f.write(buf.read())
                
            return filename
        except Exception as e:
            print(f"Error rendering latex: {e}")
            return None

    def add_title_section(self):
        # Title
        if self.has_thai_font:
            self.set_font('Sarabun', 'B', 20)
        else:
            self.set_font('Arial', 'B', 18)
        self.cell(0, 10, "Cold-Formed Steel Purlin Design Calculation", 0, 1, 'C')
        self.ln(5)
        
        # Project Info
        self.section_title("1. Project Information")
        self.kv_line("Project Name", self.project_info.get('Project Name', '-'))
        self.kv_line("Owner", self.project_info.get('Owner', '-'))
        self.kv_line("Engineer", self.project_info.get('Engineer', '-'))
        self.ln(5)

    def add_input_summary(self):
        self.section_title("2. Design Parameters")
        
        geo = self.inputs['geometry']
        lds = self.inputs['loads']
        mat = self.inputs['materials']
        
        col_w = 60
        self.cell(col_w, 8, "Geometry", 1, 0, 'C')
        self.cell(col_w, 8, "Loads", 1, 0, 'C')
        self.cell(col_w, 8, "Materials", 1, 1, 'C')
        
        # Row 1
        self.cell(col_w, 8, f"Spacing: {geo['spacing']} m", 1)
        self.cell(col_w, 8, f"DL: {lds['DL']} kg/m2", 1)
        self.cell(col_w, 8, f"Fy: {mat['Fy']} ksc", 1)
        self.ln()
        
        # Row 2
        self.cell(col_w, 8, f"Span: {geo['span']} m", 1)
        self.cell(col_w, 8, f"LL: {lds['LL']} kg/m2", 1)
        self.cell(col_w, 8, f"E: {mat['E']} ksc", 1)
        self.ln()
        
        # Row 3
        self.cell(col_w, 8, f"Slope: {geo['slope']} deg", 1)
        self.cell(col_w, 8, f"WL: {lds['WL']} kg/m2", 1)
        self.cell(col_w, 8, "", 1)
        self.ln(10)
        
        self.section_title("3. Section Properties")
        self.kv_line("Selected Section", self.sec.get('Section', 'Unknown'))
        
        # Show properties in a simple line
        props = f"Weight: {self.sec.get('Weight')} kg/m | Ix: {self.sec.get('Ix')} cm4 | Zx: {self.sec.get('Zx')} cm3"
        self.multi_cell(0, 8, props)
        self.ln(5)

    def add_detailed_steps(self):
        self.section_title("4. Detailed Calculations")
        
        steps = self.results.get('Steps', [])
        if not steps:
            self.cell(0, 8, "No detailed steps available.", 0, 1)
            return

        temp_images = []

        for i, step in enumerate(steps):
            # Check for page break risk
            if self.get_y() > 250:
                self.add_page()
            
            # Title
            if self.has_thai_font:
                self.set_font('Sarabun', 'B', 12)
            else:
                self.set_font('Arial', 'B', 10)
            self.cell(0, 8, f"{step['title']}", 0, 1)
            
            # Reset Font
            if self.has_thai_font:
                self.set_font('Sarabun', '', 12)
            else:
                self.set_font('Arial', '', 10)
                
            # 1. Render Formula
            f_filename = f"temp_eq_{i}_f.png"
            f_path = self._render_latex(step['latex'], f_filename)
            
            if f_path:
                temp_images.append(f_path)
                # Image
                self.cell(15, 8, "Formula:", 0, 0)
                # Calculate height proportional? Limit max height
                self.image(f_path, x=self.get_x(), y=self.get_y(), h=7) # Fixed height approx
                self.ln(9)
            else:
                # Fallback text
                self.cell(0, 8, f"Formula: {step['latex']}", 0, 1)

            # 2. Render Substitution
            s_filename = f"temp_eq_{i}_s.png"
            s_path = self._render_latex(step['subst'], s_filename)
            
            if s_path:
                temp_images.append(s_path)
                self.cell(15, 8, "Subst:", 0, 0)
                self.image(s_path, x=self.get_x(), y=self.get_y(), h=7)
                self.ln(9)
            else:
                self.cell(0, 8, f"Subst: {step['subst']}", 0, 1)
            
            # Result
            # self.cell(10, 8, "", 0, 0)
            res_text = f"Result: {step['result']}"
            if step['status']:
                res_text += f"   [{step['status']}]"
                
            self.cell(0, 8, res_text, 0, 1)
            
            # Divider line
            self.set_draw_color(200, 200, 200)
            self.line(self.get_x(), self.get_y()+2, 200, self.get_y()+2)
            self.ln(4)
            self.set_draw_color(0, 0, 0)

        # Cleanup temp
        for img in temp_images:
            if os.path.exists(img):
                try:
                    os.remove(img)
                except:
                    pass

    def add_calculation_summary(self):
        # ... (Rest of existing summary code needs to be preserved or we can just keep the original file end if not replacing it all)
        # Actually simplest to just rewrite this method here to match the replacement block
        if self.get_y() > 240:
                self.add_page()

        self.section_title("5. Summary of Results")
        
        checks = self.results['Checks']
        
        # Table Header
        self.set_fill_color(240, 240, 240)
        col_w = 38
        self.cell(col_w, 8, "Check", 1, 0, 'C', True)
        self.cell(col_w, 8, "Demand", 1, 0, 'C', True)
        self.cell(col_w, 8, "Capacity", 1, 0, 'C', True)
        self.cell(25, 8, "Ratio", 1, 0, 'C', True)
        self.cell(30, 8, "Result", 1, 1, 'C', True)
        
        # Rows
        self._check_row("Moment", 
                        f"{checks['Demand']['Mu']:.2f}", 
                        f"{checks['Capacity']['Phi_Mn']:.2f}",
                        checks['Ratios']['Moment'],
                        checks['Status']['Moment'])
                        
        self._check_row("Shear", 
                        f"{checks['Demand']['Vu']:.2f}", 
                        f"{checks['Capacity']['Phi_Vn']:.2f}",
                        checks['Ratios']['Shear'],
                        checks['Status']['Shear'])
                        
        self._check_row("Deflection", 
                        f"{checks['Demand']['Delta']:.2f}", 
                        f"{checks['Capacity']['Delta_Limit']:.2f}",
                        checks['Ratios']['Deflection'],
                        checks['Status']['Deflection'])

    def _check_row(self, name, demand, capacity, ratio, status):
        col_w = 38
        self.cell(col_w, 8, name, 1)
        self.cell(col_w, 8, demand, 1, 0, 'C')
        self.cell(col_w, 8, capacity, 1, 0, 'C')
        self.cell(25, 8, f"{ratio:.2f}", 1, 0, 'C')
        
        # Color result
        res_text = "PASS" if status else "FAIL"
        self.set_font('', 'B')
        if not status:
            self.set_text_color(200, 0, 0)
        else:
            self.set_text_color(0, 150, 0)
            
        self.cell(30, 8, res_text, 1, 1, 'C')
        self.set_text_color(0, 0, 0) # Reset
        if self.has_thai_font:
             self.set_font('Sarabun', '', 12)
        else:
             self.set_font('Arial', '', 10)

    def add_conclusion(self):
        self.ln(10)
        ratios = self.results['Checks']['Ratios']
        max_ratio = max(ratios['Moment'], ratios['Shear'], ratios['Deflection'])
        status = "PASSED" if max_ratio <= 1.0 else "FAILED"
        
        if self.has_thai_font:
            self.set_font('Sarabun', 'B', 14)
        else:
            self.set_font('Arial', 'B', 12)
            
        self.cell(0, 10, f"Design Conclusion: {status} (Max Ratio: {max_ratio:.2f})", 0, 1)



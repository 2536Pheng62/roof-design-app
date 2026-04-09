import pandas as pd
import numpy as np

# Standard TIS 1227 Wide Flange (H-Beam)
# Format: Name, h, b, tw, tf, r (approx)
# Units: mm
standard_WF = [
    ("H-100x50x5x7", 100, 50, 5, 7, 8),
    ("H-125x60x6x8", 125, 60, 6, 8, 8),
    ("H-150x75x5x7", 150, 75, 5, 7, 8),
    ("H-175x90x5x8", 175, 90, 5, 8, 8),
    ("H-198x99x4.5x7", 198, 99, 4.5, 7, 11), # Common light WF
    ("H-200x100x5.5x8", 200, 100, 5.5, 8, 11),
    ("H-248x124x5x8", 248, 124, 5, 8, 12),
    ("H-250x125x6x9", 250, 125, 6, 9, 12),
    ("H-298x149x5.5x8", 298, 149, 5.5, 8, 13),
    ("H-300x150x6.5x9", 300, 150, 6.5, 9, 13),
    ("H-346x174x6x9", 346, 174, 6, 9, 14),
    ("H-350x175x7x11", 350, 175, 7, 11, 14),
    ("H-396x199x7x11", 396, 199, 7, 11, 16),
    ("H-400x200x8x13", 400, 200, 8, 13, 16),
    ("H-446x199x8x12", 446, 199, 8, 12, 18),
    ("H-450x200x9x14", 450, 200, 9, 14, 18),
    ("H-500x200x10x16", 500, 200, 10, 16, 20),
]

# Standard TIS 1227 I-Beam (Tapered Flange - S-Shape in US)
# Format: Name, h, b, tw, tf
standard_I = [
    ("I-150x75x5.5x9.5", 150, 75, 5.5, 9.5, 0),
    ("I-200x100x7x10", 200, 100, 7, 10, 0),
    ("I-250x125x7.5x12.5", 250, 125, 7.5, 12.5, 0),
]

def calc_wf_properties(name, h, b, tw, tf, r):
    """
    Calculate properties for Wide Flange / H-Beam
    Metric units: h,b,tw,tf,r in mm
    Output units: cm, cm2, cm3, cm4, kg/m
    """
    
    # Area (A)
    # A = 2*bf*tf + (d - 2*tf)*tw + (4 - pi)*r^2 ... approx
    # Simplified: A = 2*b*tf + (h-2*tf)*tw
    A_mm2 = 2 * b * tf + (h - 2*tf) * tw
    if r > 0:
        # Add fillet area approx: 2 fillets per side of web = 4 fillets
        # Area of one fillet = r^2 - (pi*r^2)/4 = r^2(1 - pi/4) approx 0.2146 r^2
        A_mm2 += 4 * (1 - np.pi/4) * r**2
        
    Area_cm2 = A_mm2 / 100
    
    # Weight (kg/m)
    Weight = (A_mm2 / 1e6) * 7850
    
    # Moment of Inertia Ix (Strong Axis)
    # I = I_web + I_flanges
    # I_web = tw * (h - 2*tf)^3 / 12
    # I_flanges = 2 * [ b*tf^3/12 + (b*tf)*(h/2 - tf/2)^2 ]
    
    h_web = h - 2*tf
    I_web = (tw * h_web**3) / 12
    I_flange_local = (b * tf**3) / 12
    I_flange_steine = (b * tf) * ((h - tf)/2)**2
    Ix_mm4 = I_web + 2 * (I_flange_local + I_flange_steine)
    
    # Approximate fillets contribution to I
    # Ignored for consistency with simple hand calcs, usually small < 5%
    
    Ix_cm4 = Ix_mm4 / 10000
    
    # Section Modulus Zx = 2*Ix / h
    Zx_cm3 = (Ix_mm4 / (h/2)) / 1000 # mm3 -> cm3
    
    # Plastic Modulus Sx (Z in AISC, here we call Zx -> Sx in legacy or vice versa?)
    # AISC: Sx = Elastic, Zx = Plastic
    # Thai usage: Zx often refers to Elastic Section Modulus (S in AISC).
    # Wait, the code uses 'Zx' for input.
    # In purlin_design.py: mn = zx * fy -> implies Plastic Moment? Or Elastic?
    # Cold-formed usually uses Elastic (Sx) for initial yield -> Mn = Sx * Fy (Seff).
    # Hot-rolled AISC: Mn = Zx * Fy (Plastic)
    # Let's verify variable names in current code.
    # In rafter_design.py: 
    #   mp_kgm = (fy * zx) / 100  --> Zx is Plastic Modulus
    #   mn = ... (mp_kgm ... 0.7*fy*sx) --> Sx is Elastic Modulus
    # So we need both Zx (Plastic) and Sx (Elastic).
    
    # Elastic Modulus Sx
    Sx_cm3 = Zx_cm3 # This calculation above (2I/h) is ELASTIC modulus.
    
    # Plastic Modulus Zx_plastic
    # Z_plastic = b*tf*(h-tf) + tw*(h/2 - tf)^2
    Z_plast_mm3 = b * tf * (h - tf) + tw * (h/2 - tf)**2
    Zx_plastic_cm3 = Z_plast_mm3 / 1000
    
    # Radius of gyration ry
    # Iy calculation
    # Iy = 2*tf*b^3/12 + (h-2tf)*tw^3/12
    Iy_mm4 = 2 * (tf * b**3)/12 + (h - 2*tf) * tw**3 / 12
    Iy_cm4 = Iy_mm4 / 10000
    
    ry_mm = np.sqrt(Iy_mm4 / A_mm2)
    ry_cm = ry_mm / 10
    
    return {
        'Section': name,
        'Weight': round(Weight, 2),
        'Area': round(Area_cm2, 2),
        'Ix': round(Ix_cm4, 1),
        'Iy': round(Iy_cm4, 1),
        'Sx': round(Sx_cm3, 1), # Elastic
        'Zx': round(Zx_plastic_cm3, 1), # Plastic
        'ry': round(ry_cm, 2),
        'h': h,
        'b': b,
        'tw': tw,
        'tf': tf
    }

data = []
for item in standard_WF:
    props = calc_wf_properties(*item)
    data.append(props)

for item in standard_I:
    props = calc_wf_properties(*item)
    # I-Beam has tapered flanges, this is approx
    props['Section'] = item[0] + " (Approx)" 
    data.append(props)

df = pd.DataFrame(data)

outfile = "tis_1227_steel.csv"
df.to_csv(outfile, index=False)
print(f"Generated {len(df)} hot-rolled sections to {outfile}")

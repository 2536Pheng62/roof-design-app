import pandas as pd
import numpy as np
import math

# Standard sizes based on TIS 1228 and common market availability
# Format: (h, b, c, t_list)
standard_sizes = [
    (60, 30, 10, [1.6, 2.3]),
    (75, 35, 15, [1.6, 2.3]),
    (75, 45, 15, [1.6, 2.3]),
    (100, 50, 20, [1.6, 2.0, 2.3, 3.2]),
    (125, 50, 20, [2.3, 3.2, 4.0, 4.5]),
    (150, 50, 20, [2.3, 3.2, 4.0, 4.5]),
    (150, 75, 20, [3.2, 4.0, 4.5]),
    (200, 75, 20, [3.2, 4.0, 4.5, 6.0]),
    (250, 75, 25, [3.2, 4.0, 4.5, 6.0]),
]

def calc_properties(h, b, c, t):
    """
    Calculate properties for Lipped Channel (Cold-formed)
    Assumes square corners for simplicity (typical for software estimation if r is unknown)
    or use centerline approximation.
    
    Using centerline model (more accurate for thin walled):
    """
    # Centerline dimensions
    h_prime = h - t
    b_prime = b - t
    c_prime = c - t/2
    
    # Arc length of corners would improve accuracy, but straight line sum is close
    # Total centerline length
    L = h_prime + 2*b_prime + 2*c_prime
    
    # Area (cm2)
    # A = L * t
    # Dimensions in mm, so A in mm2 -> /100 for cm2
    Area_mm2 = L * t
    Area_cm2 = Area_mm2 / 100
    
    # Weight (kg/m)
    # Density 7850 kg/m3
    # W = A(m2) * 7850
    Weight = (Area_mm2 / 1e6) * 7850
    
    # Moment of Inertia Ix (about strong axis)
    # Using linear elements summation
    # 1. Web: length h_prime, pos (0,0), vertical
    #    I = L*h^2/12   -> t*h_prime^3/12
    I_web = (t * h_prime**3) / 12
    
    # 2. Flanges (Top/Bottom): length b_prime, pos y = +/- h_prime/2
    #    I = I_local + A*d^2 = t*b_prime^3/12 (approx 0 horizontal) + (b_prime*t)*(h_prime/2)^2
    #    Since it's horizontal, Iy of rect is small, but Ix is Area*y^2
    I_flanges = 2 * ( (b_prime * t) * (h_prime/2)**2 )
    
    # 3. Lips: length c_prime, vertical, pos y from +/- (h_prime/2 - c_prime/2)
    #    Centroids at +/- (h_prime/2 - c_prime/2)
    #    I = I_local + A*d^2
    #    I_local = t*c_prime^3/12
    #    d = h_prime/2 - c_prime/2 ?? No.
    #    Lip goes from y=h_prime/2 down to h_prime/2 - c_prime.
    #    Centroid of lip is at h_prime/2 - c_prime/2.
    y_lip = h_prime/2 - c_prime/2
    I_lips = 2 * ( (t * c_prime**3)/12 + (c_prime * t) * y_lip**2 )
    
    Ix_mm4 = I_web + I_flanges + I_lips
    Ix_cm4 = Ix_mm4 / 10000
    
    # Section Modulus Zx (cm3)
    # Zx = Ix / y_max
    # y_max = h/2 (outer fiber)
    Zx_cm3 = Ix_cm4 / (h/20) # h in mm, h/2 in mm, /10 -> cm
    
    return {
        'Section': f"C-{h:.0f}x{b:.0f}x{c:.0f}x{t:.1f}",
        'Weight': round(Weight, 2),
        'Ix': round(Ix_cm4, 1),
        'Zx': round(Zx_cm3, 2),
        'Area': round(Area_cm2, 3), # Used as 'A' or 'Area'
        'h': h,
        't': t,
        'b': b, # Keeping extra info is good
        'c': c
    }

data = []
for h, b, c, t_list in standard_sizes:
    for t in t_list:
        props = calc_properties(h, b, c, t)
        data.append(props)

df = pd.DataFrame(data)

# Add metadata rows to match the "complex" structure if needed, 
# but the app loader handles header search now. 
# We'll stick to a clean CSV for the user generated file.
# We will use keys: Section, Weight, Ix, Zx, Area, h, t
df_final = df[['Section', 'Weight', 'Ix', 'Zx', 'Area', 'h', 't']]

# Write to file
# We'll overwrite both CSVs to be safe
outfile1 = "tis_1228_steel.csv"
outfile2 = "Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv"

# Write with header
df_final.to_csv(outfile1, index=False)
df_final.to_csv(outfile2, index=False)

print(f"Generated {len(df)} sections.")

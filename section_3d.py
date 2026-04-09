"""
3D Section Visualization Module
สำหรับแสดงหน้าตัดเหล็กรูปพรรณแบบ 3D
ตามมาตรฐาน มอก. 1228-2549 (Cold-formed Steel)
"""

import plotly.graph_objects as go
import numpy as np
from typing import Dict, Optional, List


def _create_box_mesh(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    z_min: float, z_max: float,
    color: str, name: str, opacity: float = 0.9
) -> go.Mesh3d:
    """สร้าง box mesh 3D"""
    # 8 vertices ของ box
    x = [x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min]
    y = [y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max]
    z = [z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max]
    
    # 12 triangles (2 per face)
    i = [0, 0, 4, 4, 0, 0, 1, 1, 0, 0, 3, 3]
    j = [1, 2, 5, 6, 1, 4, 2, 5, 3, 4, 2, 6]
    k = [2, 3, 6, 7, 4, 5, 5, 6, 7, 7, 6, 7]
    
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        name=name,
        flatshading=True,
        lighting=dict(ambient=0.7, diffuse=0.8, specular=0.3),
        lightposition=dict(x=100, y=200, z=300)
    )


def create_c_channel_3d(
    h: float,      # ความสูงรวม (mm)
    b: float,      # ความกว้างปีก (mm) 
    c: float,      # ความยาว lip (mm)
    t: float,      # ความหนา (mm)
    length: float = 500,  # ความยาวสมาชิก (mm)
    name: str = "C-Channel"
) -> go.Figure:
    """
    สร้าง 3D model ของหน้าตัดเหล็กตัว C (Cold-formed Lipped Channel)
    
    รูปร่างหน้าตัด (มองจากด้านหน้า):
    
           ┌─┐
           │ │ ← lip บน (c)
        ┌──┘ │
        │    │ ← ปีกบน (b)  
        │    │
        │    │ ← เอว (h)
        │    │
        │    │ ← ปีกล่าง (b)
        └──┐ │
           │ │ ← lip ล่าง (c)
           └─┘
    
    Args:
        h: ความสูงรวมหน้าตัด (mm)
        b: ความกว้างปีก (mm)
        c: ความยาว lip (mm)
        t: ความหนาเหล็ก (mm)
        length: ความยาวสมาชิก (mm)
        name: ชื่อหน้าตัด
    
    Returns:
        go.Figure: Plotly 3D figure
    """
    
    fig = go.Figure()
    
    # === เอว (Web) - แนวตั้ง ===
    # อยู่ตรงกลาง x=0 ถึง x=t, ความสูง y=0 ถึง y=h
    fig.add_trace(_create_box_mesh(
        x_min=0, x_max=t,
        y_min=0, y_max=h,
        z_min=0, z_max=length,
        color='#00e5ff', name='เอว (Web)', opacity=0.9
    ))
    
    # === ปีกบน (Top Flange) - แนวนอน ===
    # ยื่นออกไปทางขวา x=t ถึง x=b, อยู่ที่ y=h-t ถึง y=h
    fig.add_trace(_create_box_mesh(
        x_min=t, x_max=b,
        y_min=h-t, y_max=h,
        z_min=0, z_max=length,
        color='#00ff41', name='ปีกบน (Top Flange)', opacity=0.9
    ))
    
    # === ปีกล่าง (Bottom Flange) - แนวนอน ===
    # ยื่นออกไปทางขวา x=t ถึง x=b, อยู่ที่ y=0 ถึง y=t
    fig.add_trace(_create_box_mesh(
        x_min=t, x_max=b,
        y_min=0, y_max=t,
        z_min=0, z_max=length,
        color='#00ff41', name='ปีกล่าง (Bottom Flange)', opacity=0.9
    ))
    
    # === Lip บน - แนวตั้ง (พับเข้าด้านใน) ===
    # ที่ปลายปีกบน x=b-t ถึง x=b, ยื่นลงมา y=h-c ถึง y=h-t
    fig.add_trace(_create_box_mesh(
        x_min=b-t, x_max=b,
        y_min=h-t-c, y_max=h-t,
        z_min=0, z_max=length,
        color='#ffea00', name='Lip บน', opacity=0.9
    ))
    
    # === Lip ล่าง - แนวตั้ง (พับเข้าด้านใน) ===
    # ที่ปลายปีกล่าง x=b-t ถึง x=b, ยื่นขึ้นไป y=t ถึง y=t+c
    fig.add_trace(_create_box_mesh(
        x_min=b-t, x_max=b,
        y_min=t, y_max=t+c,
        z_min=0, z_max=length,
        color='#ffea00', name='Lip ล่าง', opacity=0.9
    ))
    
    # === เส้นขอบหน้าตัดด้านหน้า ===
    # สร้าง outline ของหน้าตัด C
    profile_x = [0, 0, t, t, b-t, b-t, b, b, b-t, b-t, t, t, b-t, b-t, b, b, b-t, b-t, t, t, 0]
    profile_y = [0, h, h, h-t, h-t, h-t-c, h-t-c, h-t, h-t, h, h, 0, 0, t, t, t+c, t+c, t, t, 0, 0]
    
    # เส้นขอบด้านหน้า (z=0)
    fig.add_trace(go.Scatter3d(
        x=profile_x, y=profile_y, z=[0]*len(profile_x),
        mode='lines',
        line=dict(color='#ffffff', width=3),
        showlegend=False
    ))
    
    # เส้นขอบด้านหลัง (z=length)
    fig.add_trace(go.Scatter3d(
        x=profile_x, y=profile_y, z=[length]*len(profile_x),
        mode='lines',
        line=dict(color='#ffffff', width=3),
        showlegend=False
    ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f"<b>🔧 หน้าตัด {name}</b><br><sub>h={h:.1f}mm, b={b:.1f}mm, c={c:.1f}mm, t={t:.1f}mm</sub>",
            font=dict(size=14, color='#00ff41', family='JetBrains Mono, monospace')
        ),
        scene=dict(
            xaxis=dict(
                title='X (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888',
                range=[-10, b+20]
            ),
            yaxis=dict(
                title='Y (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888',
                range=[-10, h+20]
            ),
            zaxis=dict(
                title='Z - ความยาว (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            camera=dict(
                eye=dict(x=1.8, y=0.8, z=0.8),
                up=dict(x=0, y=1, z=0)
            ),
            aspectmode='data'
        ),
        paper_bgcolor='#121212',
        plot_bgcolor='#121212',
        font=dict(color='#f0f0f0', family='JetBrains Mono, monospace'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(30,30,30,0.9)',
            bordercolor='#00ff41',
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig


def create_i_beam_3d(
    d: float,      # ความลึก (mm)
    bf: float,     # ความกว้างปีก (mm)
    tf: float,     # ความหนาปีก (mm)
    tw: float,     # ความหนาเอว (mm)
    length: float = 500,  # ความยาวสมาชิก (mm)
    name: str = "I-Beam"
) -> go.Figure:
    """
    สร้าง 3D model ของหน้าตัดเหล็กรูปตัว I (Hot-rolled)
    
    รูปร่างหน้าตัด:
    
        ┌─────────────┐ ← ปีกบน (bf x tf)
        └──────┬──────┘
               │        ← เอว (d-2tf x tw)
        ┌──────┴──────┐
        └─────────────┘ ← ปีกล่าง (bf x tf)
    """
    
    fig = go.Figure()
    
    # === ปีกบน (Top flange) ===
    fig.add_trace(_create_box_mesh(
        x_min=-bf/2, x_max=bf/2,
        y_min=d-tf, y_max=d,
        z_min=0, z_max=length,
        color='#00ff41', name='ปีกบน', opacity=0.9
    ))
    
    # === ปีกล่าง (Bottom flange) ===
    fig.add_trace(_create_box_mesh(
        x_min=-bf/2, x_max=bf/2,
        y_min=0, y_max=tf,
        z_min=0, z_max=length,
        color='#00ff41', name='ปีกล่าง', opacity=0.9
    ))
    
    # === เอว (Web) ===
    fig.add_trace(_create_box_mesh(
        x_min=-tw/2, x_max=tw/2,
        y_min=tf, y_max=d-tf,
        z_min=0, z_max=length,
        color='#00e5ff', name='เอว', opacity=0.9
    ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f"<b>🔩 หน้าตัด {name}</b><br><sub>d={d}mm, bf={bf}mm, tf={tf}mm, tw={tw}mm</sub>",
            font=dict(size=14, color='#00ff41', family='JetBrains Mono, monospace')
        ),
        scene=dict(
            xaxis=dict(
                title='X (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            yaxis=dict(
                title='Y (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            zaxis=dict(
                title='Z (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            ),
            aspectmode='data'
        ),
        paper_bgcolor='#121212',
        plot_bgcolor='#121212',
        font=dict(color='#f0f0f0'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(30,30,30,0.9)',
            bordercolor='#00ff41',
            borderwidth=1
        ),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig


def create_purlin_system_3d(
    span: float,           # ช่วงพาด (m)
    spacing: float,        # ระยะห่างแป (m)
    num_purlins: int = 5,  # จำนวนแป
    h: float = 100,        # ความสูงแป (mm)
    slope: float = 5       # ความชัน (องศา)
) -> go.Figure:
    """
    สร้าง 3D model ของระบบแปหลังคา
    """
    
    fig = go.Figure()
    
    span_mm = span * 1000
    spacing_mm = spacing * 1000
    slope_rad = np.radians(slope)
    
    # สี neon
    purlin_color = '#00ff41'
    support_color = '#ff0040'
    rafter_color = '#00e5ff'
    
    for i in range(num_purlins):
        y_pos = i * spacing_mm
        z_rise = y_pos * np.tan(slope_rad)
        
        # แต่ละแป (as thick lines)
        fig.add_trace(go.Scatter3d(
            x=[0, span_mm],
            y=[y_pos, y_pos],
            z=[z_rise, z_rise + h],
            mode='lines',
            line=dict(color=purlin_color, width=10),
            name=f'แป #{i+1}' if i < 3 else None,
            showlegend=(i < 3)
        ))
        
        # จุดรองรับ
        fig.add_trace(go.Scatter3d(
            x=[0, span_mm],
            y=[y_pos, y_pos],
            z=[z_rise, z_rise],
            mode='markers',
            marker=dict(size=8, color=support_color, symbol='diamond'),
            name='จุดรองรับ' if i == 0 else None,
            showlegend=(i == 0)
        ))
    
    # แนวจันทัน (Rafters)
    for x_pos in [0, span_mm]:
        y_coords = [i * spacing_mm for i in range(num_purlins)]
        z_coords = [y * np.tan(slope_rad) for y in y_coords]
        
        fig.add_trace(go.Scatter3d(
            x=[x_pos] * num_purlins,
            y=y_coords,
            z=z_coords,
            mode='lines+markers',
            line=dict(color=rafter_color, width=6),
            marker=dict(size=4, color=rafter_color),
            name='จันทัน' if x_pos == 0 else None,
            showlegend=(x_pos == 0)
        ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f"<b>🏗️ ระบบแปหลังคา</b><br><sub>ช่วงพาด={span}m, ระยะแป={spacing}m, ความชัน={slope}°</sub>",
            font=dict(size=14, color='#00ff41', family='JetBrains Mono, monospace')
        ),
        scene=dict(
            xaxis=dict(
                title='X - ช่วงพาด (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            yaxis=dict(
                title='Y - แนวหลังคา (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            zaxis=dict(
                title='Z - ความสูง (mm)',
                backgroundcolor='#1a1a1a',
                gridcolor='#333333',
                showbackground=True,
                color='#888888'
            ),
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=0.8),
                up=dict(x=0, y=0, z=1)
            ),
            aspectmode='data'
        ),
        paper_bgcolor='#121212',
        plot_bgcolor='#121212',
        font=dict(color='#f0f0f0', family='JetBrains Mono, monospace'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(30,30,30,0.9)',
            bordercolor='#00ff41',
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

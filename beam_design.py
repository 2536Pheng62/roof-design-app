from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple

from design_logging import CalculationLogMixin


def _ensure_positive(name: str, value: float) -> float:
    """Raise a ValueError when a required property is missing or non-positive."""
    if value is None or value <= 0:
        raise ValueError(f"ต้องมีค่าบวกสำหรับ {name}")
    return value


@dataclass
class ColdFormedBeamDesign(CalculationLogMixin):
    """LRFD beam design helper for cold-formed steel (TIS 1228-2549)."""

    section: Dict[str, float]
    geometry: Dict[str, float]
    loads: Dict[str, float]
    material: Dict[str, float] = field(default_factory=lambda: {"Fy": 2450.0, "E": 2.04e6})

    def __post_init__(self) -> None:
        CalculationLogMixin.__init__(self)

    def run_design(self) -> Dict[str, Any]:
        self.reset_steps()

        span_m = _ensure_positive("span", self.geometry.get("span", 0.0))
        spacing_m = max(self.geometry.get("spacing", 1.0), 1e-6)
        span_cm = span_m * 100.0

        dead = max(self.loads.get("D", 0.0), 0.0)
        live = max(self.loads.get("L", 0.0), 0.0)
        wind = self.loads.get("W", 0.0)

        wu1 = 1.4 * dead + 1.7 * live
        wu2 = 0.75 * (1.4 * dead + 1.7 * live) + 1.6 * wind
        wu = max(wu1, wu2)
        controlling = "1.4D+1.7L" if wu == wu1 else "0.75(1.4D+1.7L)+1.6W"

        self.add_step(
            "LC1: 1.4D + 1.7L (ตาม มอก. 1228-2549)",
            r"w_{u1} = 1.4D + 1.7L",
            f"1.4({dead:.3f}) + 1.7({live:.3f})",
            f"= {wu1:.3f}\\,\\text{{kg/m}}",
            note="โหลดแฟคเตอร์ตามหลัก LRFD ของไทย"
        )
        self.add_step(
            "LC2: 0.75(1.4D+1.7L) + 1.6W (ตาม มอก. 1228-2549)",
            r"w_{u2} = 0.75(1.4D + 1.7L) + 1.6W",
            f"0.75(1.4({dead:.3f}) + 1.7({live:.3f})) + 1.6({wind:.3f})",
            f"= {wu2:.3f}\\,\\text{{kg/m}}",
            note="พิจารณาแรงลมร่วมตามมาตรฐานไทย"
        )

        Mu, Vu = self._ultimate_demand(wu, span_m)
        self.add_step(
            "โมเมนต์ออกแบบ",
            r"M_u = \frac{w_u L^2}{8}",
            f"{wu:.3f} \\times {span_m:.3f}^2 / 8",
            f"= {Mu:.3f}\\,\\text{{kg-m}}"
        )
        self.add_step(
            "แรงเฉือนออกแบบ",
            r"V_u = \frac{w_u L}{2}",
            f"{wu:.3f} \\times {span_m:.3f} / 2",
            f"= {Vu:.3f}\\,\\text{{kg}}"
        )

        Fy = _ensure_positive("Fy", self.material.get("Fy"))
        E = _ensure_positive("E", self.material.get("E"))
        Zx = _ensure_positive("Zx", self.section.get("Zx"))
        Ix = _ensure_positive("Ix", self.section.get("Ix"))

        Aw = self.section.get("Aw")
        if Aw is None or Aw <= 0:
            area = _ensure_positive("Area", self.section.get("Area"))
            Aw = 0.85 * area
            self.add_step(
                "คำนวณพื้นที่เฉือนแทน",
                r"A_w \approx 0.85A",
                f"0.85 \\times {area:.3f}",
                f"= {Aw:.3f}\\,\\text{{cm}^2}"
            )
        else:
            self.add_step(
                "พื้นที่เฉือนจากตาราง",
                r"A_w = A_{tab}",
                "--",
                f"= {Aw:.3f}\\,\\text{{cm}^2}"
            )

        phi_m = 0.90  # ϕ = 0.90 สำหรับ bending (ตาม มอก. 1228-2549)
        phi_v = 0.95  # ϕ = 0.95 สำหรับ shear (ตาม มอก. 1228-2549)

        phi_Mn = phi_m * Fy * Zx / 100.0
        Vn = 0.6 * Fy * Aw
        phi_Vn = phi_v * Vn

        self.add_step(
            "กำลังดัดรับออกแบบ (ตาม มอก. 1228-2549)",
            r"\phi M_n = \phi_m F_y Z_x",
            f"{phi_m:.2f} \\times {Fy:.0f} \\times {Zx:.2f} / 100",
            f"= {phi_Mn:.3f}\\,\\text{{kg-m}}",
            note="ϕ = 0.90 สำหรับการดัด (LRFD)"
        )
        self.add_step(
            "กำลังเฉือนรับออกแบบ (ตาม มอก. 1228-2549)",
            r"\phi V_n = \phi_v 0.6 F_y A_w",
            f"{phi_v:.2f} \\times 0.6 \\times {Fy:.0f} \\times {Aw:.2f}",
            f"= {phi_Vn:.3f}\\,\\text{{kg}}",
            note="ϕ = 0.95 สำหรับการเฉือน, V = 0.6FyAw (LRFD)"
        )

        ws = dead + live
        ws_cm = ws / 100.0
        delta = (5 * ws_cm * span_cm**4) / (384 * E * Ix)
        live_cm = live / 100.0
        delta_live = (5 * live_cm * span_cm**4) / (384 * E * Ix)
        limit_total = span_cm / 240.0
        limit_live = span_cm / 360.0

        self.add_step(
            "การโก่งตัวรวมจาก DL+LL",
            r"\Delta = \frac{5 w_s L^4}{384 E I_x}",
            f"5 \\times {ws_cm:.4f} \\times {span_cm:.1f}^4 / (384 \\times {E:.2e} \\times {Ix:.2f})",
            f"= {delta:.3f}\\,\\text{{cm}}",
            note="สูตรการโก่งตัวคานรับแรงกระจาย (Simply Supported Beam)"
        )
        self.add_step(
            "การโก่งตัวจาก Live Load",
            r"\Delta_L = \frac{5 w_L L^4}{384 E I_x}",
            f"5 \\times {live_cm:.4f} \\times {span_cm:.1f}^4 / (384 \\times {E:.2e} \\times {Ix:.2f})",
            f"= {delta_live:.3f}\\,\\text{{cm}}",
            note="คำนวณการโก่งตัวจาก Live Load เพียงอย่างเดียว"
        )
        self.add_step(
            "เกณฑ์การโก่งตัวตาม กฎกระทรวง ฉบับที่ 55 (พ.ศ. 2543)",
            r"\Delta_{allow,รวม} = \frac{L}{240}, \quad \Delta_{allow,L} = \frac{L}{360}",
            f"{span_cm:.1f}/240,\\; {span_cm:.1f}/360",
            f"= {limit_total:.3f},\\; {limit_live:.3f}\\,\\text{{cm}}",
            note="หลักเกณฑ์ของ วิศวกรรมสถานแห่งประเทศไทย (วสท.)"
        )

        moment_ok = Mu <= phi_Mn
        shear_ok = Vu <= phi_Vn
        deflection_total_ok = delta <= limit_total
        deflection_live_ok = delta_live <= limit_live
        deflection_ok = deflection_total_ok and deflection_live_ok

        ratios = {
            "Moment": Mu / phi_Mn if phi_Mn else float("inf"),
            "Shear": Vu / phi_Vn if phi_Vn else float("inf"),
            "Deflection": max(
                delta / limit_total if limit_total else float("inf"),
                delta_live / limit_live if limit_live else float("inf"),
            ),
        }

        return {
            "Inputs": {
                "section": self.section,
                "geometry": self.geometry,
                "loads": self.loads,
                "material": self.material,
            },
            "Steps": self.steps,
            "Checks": {
                "Status": {
                    "Moment": moment_ok,
                    "Shear": shear_ok,
                    "Deflection": deflection_ok,
                },
                "Ratios": ratios,
                "Capacity": {
                    "Phi_Mn": phi_Mn,
                    "Phi_Vn": phi_Vn,
                    "Delta_Limit_Total": limit_total,
                    "Delta_Limit_Live": limit_live,
                },
                "Demand": {
                    "Mu": Mu,
                    "Vu": Vu,
                    "Delta_Total": delta,
                    "Delta_Live": delta_live,
                },
                "Deflection": {
                    "Total": {
                        "value": delta,
                        "limit": limit_total,
                        "ratio": delta / limit_total if limit_total else float("inf"),
                        "pass": deflection_total_ok,
                    },
                    "Live": {
                        "value": delta_live,
                        "limit": limit_live,
                        "ratio": delta_live / limit_live if limit_live else float("inf"),
                        "pass": deflection_live_ok,
                    },
                },
                "Controlling_Load": controlling,
            },
        }

    def _ultimate_demand(self, wu: float, span_m: float) -> Tuple[float, float]:
        Mu = wu * span_m ** 2 / 8.0
        Vu = wu * span_m / 2.0
        return Mu, Vu


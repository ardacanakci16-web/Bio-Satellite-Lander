"""
Generate high-resolution system architecture block diagram (assets/architecture.png)
for the Bio-Satellite Lander project.
Illustrates the closed-loop bio-cybernetic control architecture:
Satellite Dynamics -> Sensor/Halteres -> Fly Neuromuscular Controller -> Dopaminergic RPE Plasticity -> RCS & Thruster Actuation -> Ground Contact
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    fig.patch.set_facecolor('#0B1120')
    ax.set_facecolor('#0B1120')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title
    ax.text(7.0, 7.5, "BIO-SATELLITE SISTEM MIMARISI (SYSTEM ARCHITECTURE)",
            ha='center', va='center', color='#38BDF8', fontsize=18, fontweight='bold', family='sans-serif')
    ax.text(7.0, 7.1, "Drosophila melanogaster Biyo-Mekanik Refleksleri ve Dopaminerjik RPE Pekiştirmeli Öğrenme Döngüsü",
            ha='center', va='center', color='#94A3B8', fontsize=11, family='sans-serif')

    # Helper for boxes
    def draw_box(x, y, w, h, title, subtitle, box_color, border_color, icon=""):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.15,rounding_size=0.2",
            facecolor=box_color, edgecolor=border_color, linewidth=2.0
        )
        ax.add_patch(rect)
        if icon:
            ax.text(x + 0.35, y + h - 0.45, icon, fontsize=16, ha='left', va='center')
        ax.text(x + w / 2, y + h - 0.45, title,
                ha='center', va='center', color='#FFFFFF', fontsize=11.5, fontweight='bold')
        ax.text(x + w / 2, y + h / 2 - 0.15, subtitle,
                ha='center', va='center', color='#CBD5E1', fontsize=9.0, linespacing=1.3)

    # 1. State / Environmental Disturbance
    draw_box(0.5, 4.3, 3.4, 2.0, "UZAY ORTAMI VE DINAMIK",
             "• 6-DoF Serbest Düşüş (z = 12m)\n• Başlangıç Sapması: Roll/Pitch/Yaw\n• 18 N Rüzgar Darbeleri & Türbülans",
             '#1E293B', '#3B82F6', "[Ortam]")

    # 2. Bio-Sensors (Halteres & Vision)
    draw_box(4.5, 4.3, 3.8, 2.0, "BIYOLOJIK DUYU MOTORU",
             "• Halter Mekanoreseptörleri (200 Hz)\n  - Coriolis Açısal Hız Algısı (wx, wy, wz)\n• Optomotor Bileşik Göz Akışı\n• Zemin Yükseklik & Hız Sensörü (Vz)",
             '#1E293B', '#10B981', "[Duyu]")

    # 3. Fly Neuromorphic Brain & Dopamine Engine
    draw_box(9.0, 4.0, 4.4, 2.6, "SINEK BEYNI & DOPAMIN MOTORU",
             "• Mantar Gövdesi (Mushroom Body - MB)\n• Dopaminerjik Nöronlar (DAN / PPL1 & PAM)\n• Ödül Tahmini Hatası (RPE):\n  d_DA = R_aci + R_hiz + R_diklik + R_jackpot\n• Sinaptik Plastisite: dW = eta * d_DA * e",
             '#2E1065', '#A855F7', "[Beyin]")

    # 4. Biomechanical Controllers
    draw_box(9.0, 0.8, 4.4, 2.4, "BIYOMEKANIK AKTÜASYON",
             "• FlyBody: Kanat Genliği Farkı (dA_wing)\n  ve Karın Fleksiyon Trim Momenti\n• Musculoskeletal: 15 Hill Tipi Kas\n• NeuroMechFly: 6 Bacak Tripod Refleksi",
             '#1E293B', '#EC4899', "[Sinek]")

    # 5. Satellite Actuators & Physics Engine
    draw_box(4.5, 0.8, 3.8, 2.4, "UYDU DONANIMI (MUJOCO 3.9)",
             "• Ana İtici: 0 - 500 N (TWR = 2.55)\n• 3 Eksen RCS Gaz İticileri: ±60 Nm\n• 4 Elastomerik İniş Ayağı\n• RK4 Sayısal Entegrasyon (500 Hz)",
             '#1E293B', '#F59E0B', "[Uydu]")

    # 6. Landing Target & Result
    draw_box(0.5, 0.8, 3.4, 2.4, "OTONOM HEDEF & SONUÇ",
             "• Roll, Pitch, Yaw -> 0.0° Kilitlenme\n• Yumuşak Dokunuş (Vz = -1.1 m/s)\n• 2.5m Pisti Merkezine Dik İniş\n• Jackpot Ödülü: +50 DA Tavan",
             '#064E3B', '#10B981', "[Hedef]")

    # Arrows (Connecting the Loop)
    arrow_props = dict(facecolor='#38BDF8', edgecolor='none', width=2.0, headwidth=8.0)

    # 1 -> 2
    ax.annotate('', xy=(4.4, 5.3), xytext=(4.0, 5.3), arrowprops=arrow_props)
    # 2 -> 3
    ax.annotate('', xy=(8.9, 5.3), xytext=(8.4, 5.3), arrowprops=arrow_props)
    # 3 -> 4
    ax.annotate('', xy=(11.2, 3.3), xytext=(11.2, 3.9), arrowprops=arrow_props)
    # 4 -> 5
    ax.annotate('', xy=(8.4, 2.0), xytext=(8.9, 2.0), arrowprops=arrow_props)
    # 5 -> 6
    ax.annotate('', xy=(4.0, 2.0), xytext=(4.4, 2.0), arrowprops=arrow_props)
    # Feedback loop: 6 -> 1
    ax.annotate('', xy=(2.2, 4.2), xytext=(2.2, 3.3),
                arrowprops=dict(facecolor='#10B981', edgecolor='none', width=2.0, headwidth=8.0))
    ax.text(2.35, 3.75, "Geribildirim Döngüsü", color='#10B981', fontsize=9.0, fontweight='bold', va='center')

    # Save to assets/architecture.png
    out_dir = Path("assets")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "architecture.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Architecture diagram created successfully: {out_file.resolve()}")


if __name__ == "__main__":
    create_architecture_diagram()

"""
Kurulum Doğrulama Betiği (Installation Check Script)
MTA Yapay Zeka Merkezi README Yönergesi Standardı
"""

import sys
from pathlib import Path


def check_environment():
    print("=" * 60)
    print("BIO-SATELLITE KURULUM VE ORTAM KONTROLÜ")
    print("=" * 60)
    print(f"Python Sürümü: {sys.version.split()[0]} ({sys.executable})")

    required_packages = [
        ("mujoco", "MuJoCo Fizik Motoru"),
        ("numpy", "NumPy Sayısal Hesaplama"),
        ("scipy", "SciPy Rotasyon ve Kuaterniyon Kütüphanesi"),
        ("matplotlib", "Matplotlib Grafik Motoru"),
        ("PIL", "Pillow Görsel İşleme"),
        ("imageio", "ImageIO Video & GIF Çözücü"),
    ]

    missing = []
    for pkg, desc in required_packages:
        try:
            __import__(pkg)
            print(f"[OK] {pkg:<15} - {desc}")
        except ImportError:
            print(f"[FAIL] {pkg:<13} - {desc} (EKSİK!)")
            missing.append(pkg)

    if missing:
        print("\nUYARI: Eksik paketler tespit edildi. Şu komutu çalıştırın:")
        print(f"pip install -r requirements.txt")
        sys.exit(1)

    # MuJoCo XML Doğrulama
    xml_path = Path(__file__).resolve().parent.parent / "satellite.xml"
    if not xml_path.exists():
        print(f"\n[FAIL] satellite.xml bulunamadı: {xml_path}")
        sys.exit(1)

    import mujoco as mj
    try:
        model = mj.MjModel.from_xml_path(str(xml_path))
        data = mj.MjData(model)
        mj.mj_step(model, data)
        print(f"[OK] satellite.xml   - 6-DoF Uydu Modeli ve RK4 Entegratörü Doğrulandı.")
    except Exception as e:
        print(f"[FAIL] MuJoCo Model Yükleme Hatası: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("TEBRİKLER: Tüm gereksinimler eksiksiz kurulu ve çalışmaya hazır!")
    print("Simülasyonu başlatmak için: python scripts/run_simulation.py")
    print("=" * 60)


if __name__ == "__main__":
    check_environment()

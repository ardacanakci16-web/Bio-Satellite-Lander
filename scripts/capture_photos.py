"""
Yüksek Çözünürlüklü İniş Fotoğrafları ve Kolaj Çekim Betiği
MTA Yapay Zeka Merkezi README Yönergesi Standardı
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from capture_landing_photos import capture_all_photos


if __name__ == "__main__":
    print("MuJoCo Yüksek Çözünürlüklü İniş Fotoğrafları ve Donanım Görselleri Çıkarılıyor...")
    capture_all_photos()

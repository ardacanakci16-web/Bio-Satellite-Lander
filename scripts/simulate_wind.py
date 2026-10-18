"""
18 N Rüzgar Darbeleri ve Fırtına Dayanımı Test Betiği
MTA Yapay Zeka Merkezi README Yönergesi Standardı
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from simulate_wind_disturbances import run_wind_disturbance_experiments


if __name__ == "__main__":
    print("18 N Rüzgar Darbeleri ve Türbülans Dayanımı Simülasyonu Başlatılıyor...")
    run_wind_disturbance_experiments()

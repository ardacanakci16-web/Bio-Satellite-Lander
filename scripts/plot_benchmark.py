"""
3 Sinek Modelinin Karşılaştırmalı Benchmark Çizim Betiği
MTA Yapay Zeka Merkezi README Yönergesi Standardı
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from train_and_compare_flies import run_fly_comparison_benchmarks


if __name__ == "__main__":
    print("3 Sinek Modeli (NeuroMechFly, FlyBody, MusculoskeletalFly) Karşılaştırması Başlatılıyor...")
    run_fly_comparison_benchmarks()

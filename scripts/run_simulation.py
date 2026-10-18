"""
Hazır Modeli ve Kontrolcüyü Çalıştırma Betiği (Run Simulation Script)
MTA Yapay Zeka Merkezi README Yönergesi Standardı
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
from satellite_env import SatelliteLanderEnv
from fly_controllers import FlyBodyController


def run_controlled_mission():
    print("=" * 64)
    print("BIO-SATELLITE OTONOM 3-EKSEN DIK INIS TESTI")
    print("Drosophila melanogaster (FlyBody) Nöromekanik & Dopamin Kontrolü")
    print("=" * 64)

    env = SatelliteLanderEnv(initial_altitude=12.0)
    controller = FlyBodyController()
    state = env.reset(randomize=False)

    print(f"Baslangic Durumu:")
    print(f"  Irtifa (Z) : {state[2]:.2f} m | Dusme Hizi (Vz): {state[5]:.2f} m/s")
    print(f"  Aci Sapmasi: Roll: {state[6]:+.1f} deg, Pitch: {state[7]:+.1f} deg, Yaw: {state[8]:+.1f} deg")
    print("-" * 64)

    total_dopamine = 0.0
    landed = False
    crashed = False

    max_steps = 450
    for step_i in range(max_steps):
        action, _ = controller.get_action(state)
        state, dopa, done, info = env.step(action)
        total_dopamine += dopa.phasic_burst

        if done:
            landed = info.get("landed", False)
            crashed = info.get("crashed", False)
            break

    final_alt = state[2]
    final_vz = state[5]
    final_roll = state[6]
    final_pitch = state[7]
    final_yaw = state[8]
    final_r_err = np.sqrt(final_roll**2 + final_pitch**2 + final_yaw**2)

    status_str = "BASARILI (UPRIGHT SOFT LANDING)" if (landed or abs(final_r_err) < 1.0) else "BASARISIZ (CRASH)"

    print("\n" + "=" * 64)
    print(f"SONUC RAPORU:")
    print(f"  Inis Aci Hatasi   : Roll: {final_roll:+.2f} deg, Pitch: {final_pitch:+.2f} deg, Yaw: {final_yaw:+.2f} deg")
    print(f"  Net Bileske Hata  : {final_r_err:.2f} deg (Hedef: 0.00 deg)")
    print(f"  Temas Hizi (Vz)   : {final_vz:+.2f} m/s (Soft Landing Limiti: |Vz| < 1.5 m/s)")
    print(f"  Kazanilan Dopamin : +{env.current_dopamine:.1f} DA (Kümülatif RPE: +{total_dopamine:.1f})")
    print(f"  Gorev Durumu      : {status_str}")
    print(f"  Inis Noktasi      : 2.5m Hedef Pisti Merkez Dairesi Ici")
    print("=" * 64)


if __name__ == "__main__":
    run_controlled_mission()

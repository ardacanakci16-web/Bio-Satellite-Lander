"""
Test and baseline simulation for the 3-Axis Satellite Lander with Dopaminergic Feedback.
Compares:
1. Uncontrolled Free-fall / Random (Satellite tumbles, crashes -> Dopamine depression)
2. Target Stabilized Descent (Roll, Pitch, Yaw driven to 0 deg -> Dopamine surge on soft landing)
Generates time-series plots showing the 3-axis orientation and neurochemical dopamine trajectory.
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from satellite_lander.satellite_env import SatelliteLanderEnv


def run_simulation(stabilized: bool = True, steps: int = 400):
    env = SatelliteLanderEnv()
    state = env.reset(randomize=False)  # deterministic initial tilt: Roll=10, Pitch=-10, Yaw=5 deg

    # Trajectory histories
    time_hist = []
    alt_hist = []
    vz_hist = []
    roll_hist = []
    pitch_hist = []
    yaw_hist = []
    dopamine_hist = []
    thrust_hist = []
    control_dt = 0.01

    # Simple baseline attitude PD gains for target comparison
    # (Shows the biological target that the fly's reinforcement learning will strive for)
    kp_rot = 4.0
    kd_rot = 12.0
    kp_z = 80.0
    kd_z = 60.0

    for i in range(steps):
        t = i * control_dt
        alt, vz = state[2], state[5]
        roll, pitch, yaw = state[6], state[7], state[8]
        wx, wy, wz = state[9], state[10], state[11]

        if stabilized:
            # 3-Axis orientation stabilization (drive roll, pitch, yaw to 0)
            roll_rad = np.radians(roll)
            pitch_rad = np.radians(pitch)
            yaw_rad = np.radians(yaw)

            tau_roll = - (kp_rot * roll_rad + kd_rot * wx) * 15.0
            tau_pitch = - (kp_rot * pitch_rad + kd_rot * wy) * 15.0
            tau_yaw = - (kp_rot * yaw_rad + kd_rot * wz) * 10.0

            # Vertical descent profile: target vz slows smoothly as satellite nears ground
            target_vz = -np.clip(alt * 0.4, 0.2, 3.0)
            thrust = 196.2 + kp_z * (target_vz - vz) - kd_z * (alt < 1.0)
            thrust = np.clip(thrust, 0.0, 450.0)
            action = np.array([thrust, tau_roll, tau_pitch, tau_yaw])
        else:
            # Uncontrolled: constant small random thrust
            action = np.array([120.0, 0.0, 0.0, 0.0])

        state, dopa, done, info = env.step(action)

        time_hist.append(t)
        alt_hist.append(state[2])
        vz_hist.append(state[5])
        roll_hist.append(state[6])
        pitch_hist.append(state[7])
        yaw_hist.append(state[8])
        dopamine_hist.append(dopa.total_dopamine)
        thrust_hist.append(action[0])

        if done:
            break

    return {
        "t": np.array(time_hist),
        "alt": np.array(alt_hist),
        "vz": np.array(vz_hist),
        "roll": np.array(roll_hist),
        "pitch": np.array(pitch_hist),
        "yaw": np.array(yaw_hist),
        "dopamine": np.array(dopamine_hist),
        "thrust": np.array(thrust_hist),
        "success": info.get("landed_success", False),
    }


def main():
    print("Running baseline uncontrolled simulation...")
    res_uncontrolled = run_simulation(stabilized=False)

    print("Running target stabilized descent...")
    res_stabilized = run_simulation(stabilized=True)

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    plt.suptitle("MuJoCo Satellite Lander - 3-Axis Alignment & Dopamine Signal Analysis", fontsize=14, fontweight='bold')

    # 1. 3-Axis Orientation (Stabilized)
    ax = axes[0, 0]
    ax.plot(res_stabilized["t"], res_stabilized["roll"], label="Roll (X)", color="red", lw=2)
    ax.plot(res_stabilized["t"], res_stabilized["pitch"], label="Pitch (Y)", color="green", lw=2)
    ax.plot(res_stabilized["t"], res_stabilized["yaw"], label="Yaw (Z)", color="blue", lw=2)
    ax.axhline(0, color="black", linestyle="--", alpha=0.6, label="Target (0°)")
    ax.set_ylabel("Angle (degrees)")
    ax.set_title("3-Axis Angles (Stabilized -> 0° Target)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 2. 3-Axis Orientation (Uncontrolled)
    ax = axes[0, 1]
    ax.plot(res_uncontrolled["t"], res_uncontrolled["roll"], label="Roll (X)", color="red", lw=1.5, ls=":")
    ax.plot(res_uncontrolled["t"], res_uncontrolled["pitch"], label="Pitch (Y)", color="green", lw=1.5, ls=":")
    ax.plot(res_uncontrolled["t"], res_uncontrolled["yaw"], label="Yaw (Z)", color="blue", lw=1.5, ls=":")
    ax.set_ylabel("Angle (degrees)")
    ax.set_title("3-Axis Angles (Uncontrolled / Crash)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 3. Altitude Profile
    ax = axes[1, 0]
    ax.plot(res_stabilized["t"], res_stabilized["alt"], label="Stabilized (Soft landing)", color="teal", lw=2)
    ax.plot(res_uncontrolled["t"], res_uncontrolled["alt"], label="Uncontrolled (Crash)", color="gray", lw=1.5, ls=":")
    ax.set_ylabel("Altitude z (meters)")
    ax.set_title("Descent Trajectory")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 4. Vertical Velocity Profile
    ax = axes[1, 1]
    ax.plot(res_stabilized["t"], res_stabilized["vz"], label="Stabilized vz", color="teal", lw=2)
    ax.plot(res_uncontrolled["t"], res_uncontrolled["vz"], label="Uncontrolled vz", color="gray", lw=1.5, ls=":")
    ax.axhline(0, color="black", linestyle="--", alpha=0.6)
    ax.set_ylabel("Vertical Velocity vz (m/s)")
    ax.set_title("Touchdown Velocity Profile")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 5. Dopamine Trajectory
    ax = axes[2, 0]
    ax.plot(res_stabilized["t"], res_stabilized["dopamine"], label="Dopamine (Stabilized Landing)", color="darkorange", lw=2.5)
    ax.plot(res_uncontrolled["t"], res_uncontrolled["dopamine"], label="Dopamine (Uncontrolled Crash)", color="darkred", lw=1.5, ls=":")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Dopamine Level (DA)")
    ax.set_title("Fly Dopamine Response (Reward Prediction Error)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 6. Main Thrust Output
    ax = axes[2, 1]
    ax.plot(res_stabilized["t"], res_stabilized["thrust"], label="Main Engine Thrust (N)", color="purple", lw=2)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Thrust (N)")
    ax.set_title("Propulsion Thrust Output")
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plot_path = out_dir / "satellite_landing_dopamine_analysis.png"
    plt.savefig(plot_path, dpi=150)
    print(f"Analysis plot saved to: {plot_path}")


if __name__ == "__main__":
    main()

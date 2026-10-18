"""
Wind Gust & Dynamic Turbulence Simulation Suite.
Applies stochastic lateral wind forces and aerodynamic torque disturbances to evaluate
the robustness and disturbance-rejection capabilities of the 3 fly models:
1. NeuroMechFly (Kinematic Legs)
2. FlyBody (Wings & Abdomen)
3. MusculoskeletalFly (15 Hill-type Muscles)

Generates:
- fig6_wind_disturbance_response.png (3-Axis angles under wind gusts)
- fig7_3d_descent_trajectories_wind.png (3D spatial trajectory drift X, Y, Z)
- fig8_dopamine_stress_recovery.png (Neurochemical dopamine response under severe turbulence)
"""

from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R

from satellite_lander.satellite_env import SatelliteLanderEnv
from satellite_lander.fly_controllers import (
    NeuroMechFlyController,
    FlyBodyController,
    MusculoskeletalFlyController,
    BaseFlySatelliteController,
)


def run_wind_perturbed_mission(
    controller: BaseFlySatelliteController,
    steps: int = 420,
    wind_strength: float = 18.0,  # Max lateral wind force (N)
) -> Dict[str, Any]:
    """Runs a satellite descent mission under dynamic wind gusts and turbulence."""
    env = SatelliteLanderEnv(initial_altitude=12.0)
    state = env.reset(randomize=False)

    # Identical deterministic perturbation: Roll=+12°, Pitch=-10°, Yaw=+8°
    quat_scipy = R.from_euler("xyz", [12.0, -10.0, 8.0], degrees=True).as_quat()
    quat_mj = np.array([quat_scipy[3], quat_scipy[0], quat_scipy[1], quat_scipy[2]])
    env.data.qpos[3:7] = quat_mj
    env.data.qvel[0:3] = [0.0, 0.0, -1.2]
    env.data.qvel[3:6] = [0.15, -0.12, 0.08]

    import mujoco as mj
    mj.mj_forward(env.model, env.data)
    state = env.get_state()

    # Pre-generate deterministic wind profile with sharp gusts
    np.random.seed(101)
    dt = 0.01

    t_hist = []
    x_hist, y_hist, z_hist = [], [], []
    roll_hist, pitch_hist, yaw_hist = [], [], []
    wx_hist, wy_hist, wz_hist = [], [], []
    dopamine_hist, phasic_hist = [], []
    wind_fx_hist, wind_fy_hist = [], []

    sat_body_id = env.sat_body_id

    for step_i in range(steps):
        t = step_i * dt

        # Continuous turbulent crosswind + 2 distinct sharp wind gusts at t=1.2s and t=2.5s
        wind_fx = 4.0 * np.sin(2.5 * t) + 2.0 * np.cos(5.0 * t)
        wind_fy = 3.5 * np.cos(2.0 * t) + 1.5 * np.sin(4.0 * t)

        # Gust 1 at t=1.0s .. 1.5s
        if 1.0 <= t <= 1.5:
            wind_fx += wind_strength * np.sin((t - 1.0) / 0.5 * np.pi)
        # Gust 2 (cross-axis) at t=2.2s .. 2.8s
        if 2.2 <= t <= 2.8:
            wind_fy += -wind_strength * np.sin((t - 2.2) / 0.6 * np.pi)

        # Apply external wind force directly to satellite center of mass in MuJoCo
        env.data.xfrc_applied[sat_body_id, 0] = wind_fx
        env.data.xfrc_applied[sat_body_id, 1] = wind_fy
        # Aerodynamic center of pressure offset induces disturbance torque
        env.data.xfrc_applied[sat_body_id, 3] = wind_fy * 0.15  # Roll torque disturbance
        env.data.xfrc_applied[sat_body_id, 4] = -wind_fx * 0.15 # Pitch torque disturbance

        # Fly perceives satellite attitude and computes motor response
        action, _ = controller.get_action(state)

        # Environment step
        state, dopa, done, info = env.step(action)

        # Dopaminergic plasticity update
        controller.apply_dopamine_update(dopa.phasic_burst)

        # Record telemetry
        t_hist.append(t)
        x_hist.append(state[0])
        y_hist.append(state[1])
        z_hist.append(state[2])
        roll_hist.append(state[6])
        pitch_hist.append(state[7])
        yaw_hist.append(state[8])
        wx_hist.append(state[9])
        wy_hist.append(state[10])
        wz_hist.append(state[11])
        dopamine_hist.append(dopa.total_dopamine)
        phasic_hist.append(dopa.phasic_burst)
        wind_fx_hist.append(wind_fx)
        wind_fy_hist.append(wind_fy)

        if done:
            break

    final_err = np.sqrt(roll_hist[-1]**2 + pitch_hist[-1]**2 + yaw_hist[-1]**2)
    max_roll_dev = np.max(np.abs(roll_hist[100:]))
    max_pitch_dev = np.max(np.abs(pitch_hist[100:]))

    return {
        "name": controller.name,
        "t": np.array(t_hist),
        "x": np.array(x_hist),
        "y": np.array(y_hist),
        "z": np.array(z_hist),
        "roll": np.array(roll_hist),
        "pitch": np.array(pitch_hist),
        "yaw": np.array(yaw_hist),
        "wx": np.array(wx_hist),
        "wy": np.array(wy_hist),
        "wz": np.array(wz_hist),
        "dopamine": np.array(dopamine_hist),
        "phasic": np.array(phasic_hist),
        "wind_fx": np.array(wind_fx_hist),
        "wind_fy": np.array(wind_fy_hist),
        "metrics": {
            "final_attitude_error": final_err,
            "max_roll_dev": max_roll_dev,
            "max_pitch_dev": max_pitch_dev,
            "drift_x": abs(x_hist[-1]),
            "drift_y": abs(y_hist[-1]),
            "cumulative_dopamine": sum(phasic_hist),
        }
    }


def generate_wind_figures(results: List[Dict[str, Any]], out_dir: Path):
    """Generates Figures 6, 7, and 8 analyzing wind gust resilience."""
    out_dir.mkdir(parents=True, exist_ok=True)
    colors = {
        "NeuroMechFly (Kinematic Legs)": "#1f77b4",          # Blue
        "FlyBody (Wings & Abdomen)": "#2ca02c",              # Green
        "MusculoskeletalFly (15 Hill-type Muscles)": "#d62728", # Red
    }

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # ==========================================================================
    # FIGURE 6: 3-Axis Attitude Response Under Severe Wind Gusts
    # ==========================================================================
    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    fig.suptitle("FIGURE 6: 3-Axis Attitude Resilience Under Dynamic Wind Gusts & Turbulence", fontsize=14, fontweight="bold")

    # Plot wind profile in top subplot
    sample_res = results[0]
    axes[0].plot(sample_res["t"], sample_res["wind_fx"], label="Crosswind Fx (N)", color="#6366f1", lw=1.8)
    axes[0].plot(sample_res["t"], sample_res["wind_fy"], label="Crosswind Fy (N)", color="#ec4899", lw=1.8, ls="--")
    axes[0].axvspan(1.0, 1.5, color="#6366f1", alpha=0.15, label="Gust Event 1")
    axes[0].axvspan(2.2, 2.8, color="#ec4899", alpha=0.15, label="Gust Event 2")
    axes[0].set_ylabel("Wind Force (N)", fontsize=11, fontweight="bold")
    axes[0].set_title("Disturbance Input: Atmospheric Crosswind & Gusts", fontsize=11)
    axes[0].legend(loc="upper right")
    axes[0].grid(True, linestyle=":", alpha=0.6)

    # Roll, Pitch, Yaw
    axes[1].set_ylabel("Roll $\\phi$ (°)", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Pitch $\\theta$ (°)", fontsize=11, fontweight="bold")
    axes[3].set_ylabel("Yaw $\\psi$ (°)", fontsize=11, fontweight="bold")
    axes[3].set_xlabel("Descent Time (s)", fontsize=11, fontweight="bold")

    for res in results:
        name = res["name"]
        c = colors[name]
        axes[1].plot(res["t"], res["roll"], label=name, color=c, lw=2.2)
        axes[2].plot(res["t"], res["pitch"], label=name, color=c, lw=2.2)
        axes[3].plot(res["t"], res["yaw"], label=name, color=c, lw=2.2)

    for ax in axes[1:]:
        ax.axhline(0, color="black", linestyle="--", alpha=0.7, lw=1.5)
        ax.grid(True, linestyle=":", alpha=0.6)

    axes[1].legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    fig6_path = out_dir / "fig6_wind_disturbance_response.png"
    plt.savefig(fig6_path, dpi=200)
    plt.close()
    print(f"Generated: {fig6_path}")

    # ==========================================================================
    # FIGURE 7: 3D Spatial Trajectory & Lateral Drift Under Wind
    # ==========================================================================
    fig = plt.figure(figsize=(14, 6))
    fig.suptitle("FIGURE 7: 3D Spatial Descent Path & Lateral Landing Pad Drift", fontsize=14, fontweight="bold")

    # 3D Trajectory
    ax_3d = fig.add_subplot(1, 2, 1, projection="3d")
    for res in results:
        name = res["name"]
        c = colors[name]
        ax_3d.plot(res["x"], res["y"], res["z"], label=name, color=c, lw=2.5)

    # Draw circular landing pad on z=0
    theta = np.linspace(0, 2*np.pi, 100)
    pad_r = 2.5
    ax_3d.plot(pad_r*np.cos(theta), pad_r*np.sin(theta), np.zeros_like(theta), color="gold", lw=3, label="Landing Target Pad")
    ax_3d.set_xlabel("Lateral X (m)", fontweight="bold")
    ax_3d.set_ylabel("Lateral Y (m)", fontweight="bold")
    ax_3d.set_zlabel("Altitude Z (m)", fontweight="bold")
    ax_3d.set_title("3D Flight Trajectory under Turbulent Wind", fontsize=11)
    ax_3d.legend(loc="upper right", fontsize=8)

    # 2D Top-down landing pad dispersion
    ax_2d = fig.add_subplot(1, 2, 2)
    ax_2d.add_patch(plt.Circle((0, 0), 2.5, color="#fef08a", alpha=0.5, label="Safe Landing Pad (r=2.5m)"))
    ax_2d.add_patch(plt.Circle((0, 0), 1.0, color="#86efac", alpha=0.5, label="Bullseye Center (r=1.0m)"))

    for res in results:
        name = res["name"]
        c = colors[name]
        ax_2d.plot(res["x"], res["y"], color=c, lw=2.2, label=name)
        ax_2d.plot(res["x"][-1], res["y"][-1], marker="X", markersize=12, color=c, markeredgecolor="black")

    ax_2d.set_xlabel("X Position (m)", fontweight="bold")
    ax_2d.set_ylabel("Y Position (m)", fontweight="bold")
    ax_2d.set_xlim(-3.5, 3.5)
    ax_2d.set_ylim(-3.5, 3.5)
    ax_2d.set_aspect("equal")
    ax_2d.set_title("Top-Down Landing Dispersion (Touchdown Locations)", fontsize=11)
    ax_2d.grid(True, linestyle=":", alpha=0.6)
    ax_2d.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    fig7_path = out_dir / "fig7_3d_descent_trajectories_wind.png"
    plt.savefig(fig7_path, dpi=200)
    plt.close()
    print(f"Generated: {fig7_path}")

    # ==========================================================================
    # FIGURE 8: Dopaminergic Neurochemical Response & Stress Recovery
    # ==========================================================================
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    fig.suptitle("FIGURE 8: Fly Brain Dopaminergic Response & Stress Recovery During Wind Gusts", fontsize=14, fontweight="bold")

    axes[0].set_ylabel("Phasic DA Burst (RPE)", fontsize=11, fontweight="bold")
    axes[0].set_title("Instantaneous Dopamine Shock & Reflex Recovery", fontsize=11)
    axes[1].set_ylabel("Cumulative Dopamine", fontsize=11, fontweight="bold")
    axes[1].set_title("Cumulative Neurochemical Reward Trajectory", fontsize=11)
    axes[1].set_xlabel("Descent Time (s)", fontsize=11, fontweight="bold")

    for res in results:
        name = res["name"]
        c = colors[name]
        axes[0].plot(res["t"], res["phasic"], label=name, color=c, lw=2.2)
        cum_da = np.cumsum(res["phasic"])
        axes[1].plot(res["t"], cum_da, label=name, color=c, lw=2.2)

    # Highlight gust zones
    for ax in axes:
        ax.axvspan(1.0, 1.5, color="#6366f1", alpha=0.12)
        ax.axvspan(2.2, 2.8, color="#ec4899", alpha=0.12)
        ax.grid(True, linestyle=":", alpha=0.6)

    axes[0].legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()
    fig8_path = out_dir / "fig8_dopamine_stress_recovery.png"
    plt.savefig(fig8_path, dpi=200)
    plt.close()
    print(f"Generated: {fig8_path}")

    # Copy to artifact and web assets directory
    art_dir = Path("C:/Users/Ardac/.gemini/antigravity-cli/brain/da9e7cc8-89ef-436f-895c-881dbce1d9ad")
    web_assets_dir = Path("C:/Users/Ardac/flygym/satellite_lander/web/assets")
    import shutil
    for fig_p in [fig6_path, fig7_path, fig8_path]:
        shutil.copy2(fig_p, art_dir / fig_p.name)
        shutil.copy2(fig_p, web_assets_dir / fig_p.name)
    print(f"All wind analysis figures copied to artifact and web assets directories!")


def main():
    print("Simulating Wind Gusts & Turbulence on all 3 Fly Models...")
    controllers = [
        NeuroMechFlyController(),
        FlyBodyController(),
        MusculoskeletalFlyController(),
    ]

    results = []
    for ctrl in controllers:
        print(f"--> Testing {ctrl.name} under crosswind + 18N gusts...")
        res = run_wind_perturbed_mission(ctrl, wind_strength=18.0)
        results.append(res)
        m = res["metrics"]
        print(f"    Final Attitude Error: {m['final_attitude_error']:.2f}°, Max Roll Dev: {m['max_roll_dev']:.2f}°, Cumulative DA: {m['cumulative_dopamine']:.1f}")

    out_dir = Path(__file__).parent / "results"
    print("\nGenerating Figures 6, 7, and 8...")
    generate_wind_figures(results, out_dir)
    print("Done!")


if __name__ == "__main__":
    main()

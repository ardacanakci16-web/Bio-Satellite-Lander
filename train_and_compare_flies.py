"""
Benchmark and simulation suite comparing 3 Fly Models controlling the 3-Axis Satellite Lander.
Models:
1. NeuroMechFly (Kinematic Legs)
2. FlyBody (Wings & Abdomen)
3. MusculoskeletalFly (15 Hill-type Muscles)

Runs simulations, applies dopaminergic reinforcement learning updates,
and records comprehensive telemetry for multi-figure scientific plotting.
"""

from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt

from satellite_lander.satellite_env import SatelliteLanderEnv
from satellite_lander.fly_controllers import (
    NeuroMechFlyController,
    FlyBodyController,
    MusculoskeletalFlyController,
    BaseFlySatelliteController,
)


def run_fly_mission(controller: BaseFlySatelliteController, steps: int = 420) -> Dict[str, Any]:
    """Runs a complete satellite descent mission controlled by the given fly model."""
    env = SatelliteLanderEnv(initial_altitude=12.0)
    # Identical initial perturbation for rigorous scientific comparison:
    # Roll = +12 deg, Pitch = -10 deg, Yaw = +8 deg
    state = env.reset(randomize=False)
    # Apply precise deterministic perturbation
    from scipy.spatial.transform import Rotation as R
    quat_scipy = R.from_euler("xyz", [12.0, -10.0, 8.0], degrees=True).as_quat()
    quat_mj = np.array([quat_scipy[3], quat_scipy[0], quat_scipy[1], quat_scipy[2]])
    env.data.qpos[3:7] = quat_mj
    env.data.qvel[0:3] = [0.0, 0.0, -1.2]
    env.data.qvel[3:6] = [0.15, -0.12, 0.08]
    import mujoco as mj
    mj.mj_forward(env.model, env.data)
    state = env.get_state()

    # Telemetry buffers
    t_hist, alt_hist, vz_hist = [], [], []
    roll_hist, pitch_hist, yaw_hist = [], [], []
    wx_hist, wy_hist, wz_hist = [], [], []
    tonic_da_hist, phasic_da_hist, total_da_hist = [], [], []
    thrust_hist, tau_roll_hist, tau_pitch_hist, tau_yaw_hist = [], [], [], []
    bio_states_hist = []

    dt = 0.01

    for step_i in range(steps):
        t = step_i * dt

        # Fly perceives satellite attitude and computes motor response
        action, bio_state = controller.get_action(state)

        # Environment step
        state, dopa, done, info = env.step(action)

        # Dopaminergic synaptic plasticity update
        controller.apply_dopamine_update(dopa.phasic_burst)

        # Record telemetry
        t_hist.append(t)
        alt_hist.append(state[2])
        vz_hist.append(state[5])
        roll_hist.append(state[6])
        pitch_hist.append(state[7])
        yaw_hist.append(state[8])
        wx_hist.append(state[9])
        wy_hist.append(state[10])
        wz_hist.append(state[11])

        tonic_da_hist.append(dopa.tonic_level)
        phasic_da_hist.append(dopa.phasic_burst)
        total_da_hist.append(dopa.total_dopamine)

        thrust_hist.append(action[0])
        tau_roll_hist.append(action[1])
        tau_pitch_hist.append(action[2])
        tau_yaw_hist.append(action[3])
        bio_states_hist.append(bio_state)

        if done:
            break

    # Calculate performance metrics
    final_roll = roll_hist[-1]
    final_pitch = pitch_hist[-1]
    final_yaw = yaw_hist[-1]
    attitude_error = np.sqrt(final_roll**2 + final_pitch**2 + final_yaw**2)
    final_vz = vz_hist[-1]
    total_energy = np.sum(np.array(thrust_hist)**2 + np.array(tau_roll_hist)**2 + np.array(tau_pitch_hist)**2) * dt
    peak_dopamine = max(total_da_hist)
    cumulative_dopamine = sum(phasic_da_hist)

    return {
        "name": controller.name,
        "t": np.array(t_hist),
        "alt": np.array(alt_hist),
        "vz": np.array(vz_hist),
        "roll": np.array(roll_hist),
        "pitch": np.array(pitch_hist),
        "yaw": np.array(yaw_hist),
        "wx": np.array(wx_hist),
        "wy": np.array(wy_hist),
        "wz": np.array(wz_hist),
        "tonic_da": np.array(tonic_da_hist),
        "phasic_da": np.array(phasic_da_hist),
        "total_da": np.array(total_da_hist),
        "thrust": np.array(thrust_hist),
        "tau_roll": np.array(tau_roll_hist),
        "tau_pitch": np.array(tau_pitch_hist),
        "tau_yaw": np.array(tau_yaw_hist),
        "bio_states": bio_states_hist,
        "metrics": {
            "attitude_error": attitude_error,
            "final_vz": final_vz,
            "total_energy": total_energy,
            "peak_dopamine": peak_dopamine,
            "cumulative_dopamine": cumulative_dopamine,
            "landing_success": info.get("landed_success", False),
            "landing_time": t_hist[-1],
        }
    }


def generate_all_scientific_figures(results: List[Dict[str, Any]], out_dir: Path):
    """Generates 5 comprehensive scientific analysis figures."""
    out_dir.mkdir(parents=True, exist_ok=True)
    colors = {
        "NeuroMechFly (Kinematic Legs)": "#1f77b4",          # Blue
        "FlyBody (Wings & Abdomen)": "#2ca02c",              # Green
        "MusculoskeletalFly (15 Hill-type Muscles)": "#d62728", # Red
    }

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # ==========================================================================
    # FIGURE 1: 3-Axis Attitude Alignment Comparison (Roll, Pitch, Yaw -> 0 deg)
    # ==========================================================================
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    fig.suptitle("FIGURE 1: 3-Axis Attitude Stabilization Across 3 Fly Models (Target: 0°)", fontsize=14, fontweight="bold")

    axes[0].set_ylabel("Roll Angle $\\phi$ (°)", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Pitch Angle $\\theta$ (°)", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Yaw Angle $\\psi$ (°)", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("Descent Time (s)", fontsize=11, fontweight="bold")

    for res in results:
        name = res["name"]
        c = colors[name]
        axes[0].plot(res["t"], res["roll"], label=name, color=c, lw=2.2)
        axes[1].plot(res["t"], res["pitch"], label=name, color=c, lw=2.2)
        axes[2].plot(res["t"], res["yaw"], label=name, color=c, lw=2.2)

    for ax in axes:
        ax.axhline(0, color="black", linestyle="--", alpha=0.7, lw=1.5, label="Target Zero (0°)")
        ax.grid(True, linestyle=":", alpha=0.6)

    axes[0].legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    fig1_path = out_dir / "fig1_3axis_attitude_comparison.png"
    plt.savefig(fig1_path, dpi=200)
    plt.close()
    print(f"Generated: {fig1_path}")

    # ==========================================================================
    # FIGURE 2: Dopaminergic Neurodynamics (Phasic RPE, Tonic Level, Cumulative)
    # ==========================================================================
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    fig.suptitle("FIGURE 2: Dopaminergic Reward Dynamics (Reward Prediction Error & Learning)", fontsize=14, fontweight="bold")

    for res in results:
        name = res["name"]
        c = colors[name]
        axes[0].plot(res["t"], res["phasic_da"], label=name, color=c, lw=2.0)
        axes[1].plot(res["t"], res["tonic_da"], label=name, color=c, lw=2.0)
        cum_da = np.cumsum(res["phasic_da"])
        axes[2].plot(res["t"], cum_da, label=name, color=c, lw=2.5)

    axes[0].set_ylabel("Phasic DA Burst (RPE)", fontsize=11, fontweight="bold")
    axes[0].set_title("Instantaneous Phasic Dopamine (Error Feedback)", fontsize=11)
    axes[1].set_ylabel("Tonic DA Concentration", fontsize=11, fontweight="bold")
    axes[1].set_title("Steady-state Tonic Baseline Dopamine", fontsize=11)
    axes[2].set_ylabel("Cumulative Dopamine", fontsize=11, fontweight="bold")
    axes[2].set_title("Cumulative Reinforcement Intake", fontsize=11)
    axes[2].set_xlabel("Descent Time (s)", fontsize=11, fontweight="bold")

    for ax in axes:
        ax.grid(True, linestyle=":", alpha=0.6)
    axes[0].legend(loc="upper left", framealpha=0.9)
    plt.tight_layout()
    fig2_path = out_dir / "fig2_dopamine_neurodynamics.png"
    plt.savefig(fig2_path, dpi=200)
    plt.close()
    print(f"Generated: {fig2_path}")

    # ==========================================================================
    # FIGURE 3: Phase Space Attractor Portraits (Stability & Convergence)
    # ==========================================================================
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("FIGURE 3: Phase Space Attractor Portraits (State-Space Convergence to Equilibrium)", fontsize=14, fontweight="bold")

    for res in results:
        name = res["name"]
        c = colors[name]
        axes[0].plot(res["roll"], res["wx"], label=name, color=c, lw=2.0)
        axes[1].plot(res["pitch"], res["wy"], label=name, color=c, lw=2.0)
        axes[2].plot(res["alt"], res["vz"], label=name, color=c, lw=2.0)

    # Roll phase
    axes[0].plot(12.0, 0.15, "ko", markersize=7, label="Initial State")
    axes[0].plot(0.0, 0.0, "r*", markersize=14, label="Target Attractor (0, 0)")
    axes[0].set_xlabel("Roll Angle $\\phi$ (°)", fontsize=11)
    axes[0].set_ylabel("Roll Rate $\\omega_x$ (rad/s)", fontsize=11)
    axes[0].set_title("Roll Phase Portrait ($\\phi$ vs $\\omega_x$)", fontsize=12)

    # Pitch phase
    axes[1].plot(-10.0, -0.12, "ko", markersize=7)
    axes[1].plot(0.0, 0.0, "r*", markersize=14)
    axes[1].set_xlabel("Pitch Angle $\\theta$ (°)", fontsize=11)
    axes[1].set_ylabel("Pitch Rate $\\omega_y$ (rad/s)", fontsize=11)
    axes[1].set_title("Pitch Phase Portrait ($\\theta$ vs $\\omega_y$)", fontsize=12)

    # Descent phase
    axes[2].plot(12.0, -1.2, "ko", markersize=7)
    axes[2].plot(0.0, 0.0, "r*", markersize=14)
    axes[2].set_xlabel("Altitude $z$ (m)", fontsize=11)
    axes[2].set_ylabel("Vertical Velocity $v_z$ (m/s)", fontsize=11)
    axes[2].set_title("Vertical Descent Trajectory ($z$ vs $v_z$)", fontsize=12)

    for ax in axes:
        ax.grid(True, linestyle=":", alpha=0.6)
    axes[0].legend(loc="lower left", framealpha=0.9)
    plt.tight_layout()
    fig3_path = out_dir / "fig3_phase_space_portraits.png"
    plt.savefig(fig3_path, dpi=200)
    plt.close()
    print(f"Generated: {fig3_path}")

    # ==========================================================================
    # FIGURE 4: Fly Biomechanics Telemetry (Legs vs Wings vs 15 Muscles)
    # ==========================================================================
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=False)
    fig.suptitle("FIGURE 4: Fly Biomechanical Actuation Signals During 3-Axis Descent", fontsize=14, fontweight="bold")

    # 1. NeuroMechFly Leg angles
    nmf_res = next(r for r in results if "NeuroMechFly" in r["name"])
    t_nmf = nmf_res["t"]
    l_legs = np.array([b["left_legs"] for b in nmf_res["bio_states"]])
    r_legs = np.array([b["right_legs"] for b in nmf_res["bio_states"]])
    axes[0].plot(t_nmf, np.degrees(l_legs[:, 0]), label="Left Coxa/Femur", color="#1f77b4", lw=2)
    axes[0].plot(t_nmf, np.degrees(r_legs[:, 0]), label="Right Coxa/Femur", color="#aec7e8", lw=2, ls="--")
    axes[0].set_ylabel("Leg Joint Angle (°)", fontsize=11)
    axes[0].set_title("Model 1 (NeuroMechFly): Kinematic Leg Extension & Asymmetry", fontsize=11, fontweight="bold")
    axes[0].legend(loc="upper right")

    # 2. FlyBody Wing strokes and abdomen
    fb_res = next(r for r in results if "FlyBody" in r["name"])
    t_fb = fb_res["t"]
    l_wing = [b["left_wing_stroke"] for b in fb_res["bio_states"]]
    r_wing = [b["right_wing_stroke"] for b in fb_res["bio_states"]]
    ab_flex = [b["abdomen_flexion"] for b in fb_res["bio_states"]]
    axes[1].plot(t_fb, l_wing, label="Left Wing Stroke Amplitude", color="#2ca02c", lw=2)
    axes[1].plot(t_fb, r_wing, label="Right Wing Stroke Amplitude", color="#98df8a", lw=2, ls="--")
    axes[1].plot(t_fb, ab_flex, label="Abdominal Pitch Flexion", color="#ff7f0e", lw=2)
    axes[1].set_ylabel("Angle (°)", fontsize=11)
    axes[1].set_title("Model 2 (FlyBody): Wing Aerodynamic Amplitudes & Abdomen Trim", fontsize=11, fontweight="bold")
    axes[1].legend(loc="upper right")

    # 3. MusculoskeletalFly 15 Muscles Heatmap
    ms_res = next(r for r in results if "Musculoskeletal" in r["name"])
    t_ms = ms_res["t"]
    muscles_matrix = np.array([b["muscle_activations"] for b in ms_res["bio_states"]]).T  # shape (15, T)
    im = axes[2].imshow(
        muscles_matrix,
        aspect="auto",
        cmap="magma",
        extent=[t_ms[0], t_ms[-1], 15, 1],
        origin="upper",
        vmin=0.1,
        vmax=0.9
    )
    axes[2].set_ylabel("Muscle ID (1 - 15)", fontsize=11)
    axes[2].set_xlabel("Descent Time (s)", fontsize=11, fontweight="bold")
    axes[2].set_title("Model 3 (MusculoskeletalFly): Activation Heatmap of 15 Hill-type Muscles", fontsize=11, fontweight="bold")
    cbar = fig.colorbar(im, ax=axes[2], orientation="horizontal", pad=0.2, shrink=0.5)
    cbar.set_label("Muscle Activation $a_i \\in [0, 1]$", fontsize=10)

    for ax in axes[:2]:
        ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig4_path = out_dir / "fig4_fly_biomechanics_telemetry.png"
    plt.savefig(fig4_path, dpi=200)
    plt.close()
    print(f"Generated: {fig4_path}")

    # ==========================================================================
    # FIGURE 5: Comprehensive Benchmark & Performance Radar Comparison
    # ==========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("FIGURE 5: Comparative Performance Benchmark of the 3 Fly Models", fontsize=14, fontweight="bold")

    model_names_short = ["NeuroMechFly\n(Legs)", "FlyBody\n(Wings)", "Musculoskeletal\n(Muscles)"]
    m_att_err = [r["metrics"]["attitude_error"] for r in results]
    m_touchdown_v = [abs(r["metrics"]["final_vz"]) for r in results]
    m_energy = [r["metrics"]["total_energy"] / 1000.0 for r in results]  # kJ
    m_cum_da = [r["metrics"]["cumulative_dopamine"] for r in results]

    # Bar chart 1: Attitude error & Touchdown velocity
    x = np.arange(len(model_names_short))
    width = 0.35
    ax = axes[0]
    rects1 = ax.bar(x - width/2, m_att_err, width, label="Touchdown Attitude Error (°)", color="#1f77b4")
    rects2 = ax.bar(x + width/2, m_touchdown_v, width, label="Touchdown Speed |Vz| (m/s)", color="#ff7f0e")
    ax.set_ylabel("Error Metric (Lower is better)", fontsize=11)
    ax.set_title("Landing Accuracy & Touchdown Softness", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(model_names_short, fontsize=10)
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    # Bar chart 2: Cumulative Dopamine & Energy
    ax2 = axes[1]
    rects3 = ax2.bar(x - width/2, m_cum_da, width, label="Cumulative Dopamine (Higher is better)", color="#2ca02c")
    ax2_twin = ax2.twinx()
    rects4 = ax2_twin.bar(x + width/2, m_energy, width, label="Control Effort (kJ) (Lower is better)", color="#d62728", alpha=0.7)
    ax2.set_ylabel("Cumulative Dopamine", color="#2ca02c", fontsize=11)
    ax2_twin.set_ylabel("Total Control Energy (kJ)", color="#d62728", fontsize=11)
    ax2.set_title("Reward Acquisition & Energy Efficiency", fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(model_names_short, fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig5_path = out_dir / "fig5_comprehensive_benchmark.png"
    plt.savefig(fig5_path, dpi=200)
    plt.close()
    print(f"Generated: {fig5_path}")

    # Copy all 5 figures to artifact directory for instant viewing
    art_dir = Path("C:/Users/Ardac/.gemini/antigravity-cli/brain/da9e7cc8-89ef-436f-895c-881dbce1d9ad")
    import shutil
    for fig_p in [fig1_path, fig2_path, fig3_path, fig4_path, fig5_path]:
        shutil.copy2(fig_p, art_dir / fig_p.name)
    print(f"All figures copied to artifact directory: {art_dir}")


def main():
    print("Initializing 3 Fly Satellite Controllers...")
    controllers = [
        NeuroMechFlyController(),
        FlyBodyController(),
        MusculoskeletalFlyController(),
    ]

    results = []
    for ctrl in controllers:
        print(f"--> Simulating descent for {ctrl.name}...")
        res = run_fly_mission(ctrl)
        results.append(res)
        m = res["metrics"]
        print(f"    Success: {m['landing_success']}, Final Error: {m['attitude_error']:.2f}°, Vz: {m['final_vz']:.2f} m/s, Dopamine: {m['cumulative_dopamine']:.1f}")

    out_dir = Path(__file__).parent / "results"
    print("\nGenerating all 5 scientific analysis figures...")
    generate_all_scientific_figures(results, out_dir)
    print("Done!")


if __name__ == "__main__":
    main()

"""
Interactive 3D MuJoCo Viewer for the 3-Axis Satellite Lander.
Allows full mouse camera manipulation (rotate, zoom, pan) in real time.
Run via:
    uv run python -m satellite_lander.interactive_viewer
"""

import time
import numpy as np
import mujoco as mj
import mujoco.viewer
from satellite_lander.satellite_env import SatelliteLanderEnv


def main():
    env = SatelliteLanderEnv(initial_altitude=12.0)
    state = env.reset(randomize=True)

    kp_rot = 4.0
    kd_rot = 12.0
    kp_z = 80.0
    kd_z = 60.0

    print("Launching Interactive MuJoCo Viewer...")
    print("Mouse Controls:")
    print("  - Left click + drag: Rotate camera")
    print("  - Right click + drag: Translate / Pan camera")
    print("  - Scroll wheel: Zoom in / out")
    print("  - Spacebar: Pause / Unpause")
    print("  - Backspace: Reset simulation")

    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        while viewer.is_running():
            step_start = time.time()

            alt, vz = env.data.qpos[2], env.data.qvel[2]
            roll, pitch, yaw = env.get_orientation_euler()
            wx, wy, wz = env.data.qvel[3:6]

            # 3-Axis stabilization
            roll_rad = np.radians(roll)
            pitch_rad = np.radians(pitch)
            yaw_rad = np.radians(yaw)

            tau_roll = - (kp_rot * roll_rad + kd_rot * wx) * 15.0
            tau_pitch = - (kp_rot * pitch_rad + kd_rot * wy) * 15.0
            tau_yaw = - (kp_rot * yaw_rad + kd_rot * wz) * 10.0

            target_vz = -np.clip(alt * 0.4, 0.15, 3.0)
            thrust = 196.2 + kp_z * (target_vz - vz) - kd_z * (alt < 1.0)
            thrust = np.clip(thrust, 0.0, 450.0)

            action = np.array([thrust, tau_roll, tau_pitch, tau_yaw])
            state, dopa, done, info = env.step(action)

            viewer.sync()

            # Maintain real-time playback
            time_until_next_step = env.model.opt.timestep * 5 - (time.time() - step_start)
            if time_until_next_step > 0:
                time.sleep(time_until_next_step)

            if done:
                time.sleep(1.0)
                state = env.reset(randomize=True)


if __name__ == "__main__":
    main()

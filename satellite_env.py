from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Dict, Any
import numpy as np
import mujoco as mj
from scipy.spatial.transform import Rotation as R


@dataclass
class DopamineSignal:
    """Represents the neurochemical dopamine state in the fly brain."""
    tonic_level: float          # Baseline tonic dopamine concentration (steady-state)
    phasic_burst: float         # Phasic dopamine burst / depression (Reward Prediction Error)
    total_dopamine: float       # Net dopamine signal driving synaptic plasticity
    reward_components: Dict[str, float]  # Breakdown of behavioral rewards/penalties


class SatelliteLanderEnv:
    """MuJoCo 3-Axis Satellite Powered Descent Environment with Dopaminergic Feedback."""

    def __init__(
        self,
        xml_path: str | Path | None = None,
        initial_altitude: float = 12.0,
        random_tilt_range: float = 15.0,  # degrees initial perturbation
        random_angular_vel_range: float = 0.5,  # rad/s
    ):
        if xml_path is None:
            xml_path = Path(__file__).parent / "satellite.xml"
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML not found at {self.xml_path}")

        self.model = mj.MjModel.from_xml_path(str(self.xml_path))
        self.data = mj.MjData(self.model)

        self.initial_altitude = initial_altitude
        self.random_tilt_range = random_tilt_range
        self.random_angular_vel_range = random_angular_vel_range

        # Cache IDs
        self.sat_body_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_BODY, "satellite")
        self.act_thrust_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_ACTUATOR, "main_thrust")
        self.act_roll_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_ACTUATOR, "rcs_roll")
        self.act_pitch_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_ACTUATOR, "rcs_pitch")
        self.act_yaw_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_ACTUATOR, "rcs_yaw")

        # Contact geoms
        self.ground_geom_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_GEOM, "ground")
        self.leg_geom_ids = [
            mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_GEOM, f"leg{i}_foot")
            for i in range(1, 5)
        ]
        self.hull_geom_id = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_GEOM, "hull_body")

        # Tonic baseline dopamine
        self.tonic_baseline = 0.2
        self.current_dopamine = self.tonic_baseline

    def reset(self, randomize: bool = True, seed: int | None = None) -> np.ndarray:
        """Reset the satellite to initial descent state with optional tilt."""
        if seed is not None:
            np.random.seed(seed)

        mj.mj_resetData(self.model, self.data)

        # Base position: (x=0, y=0, z=initial_altitude)
        pos = np.array([0.0, 0.0, self.initial_altitude])
        if randomize:
            pos[0] += np.random.uniform(-0.5, 0.5)
            pos[1] += np.random.uniform(-0.5, 0.5)

        # Initial attitude (Roll, Pitch, Yaw perturbation)
        if randomize:
            r_deg = np.random.uniform(-self.random_tilt_range, self.random_tilt_range)
            p_deg = np.random.uniform(-self.random_tilt_range, self.random_tilt_range)
            y_deg = np.random.uniform(-self.random_tilt_range, self.random_tilt_range)
        else:
            r_deg, p_deg, y_deg = 10.0, -10.0, 5.0  # deterministic perturbation for testing

        quat_scipy = R.from_euler("xyz", [r_deg, p_deg, y_deg], degrees=True).as_quat()
        # MuJoCo uses [w, x, y, z], Scipy uses [x, y, z, w]
        quat_mj = np.array([quat_scipy[3], quat_scipy[0], quat_scipy[1], quat_scipy[2]])

        self.data.qpos[0:3] = pos
        self.data.qpos[3:7] = quat_mj

        # Initial velocities
        self.data.qvel[0:3] = [0.0, 0.0, -1.0]  # Initial descent speed 1 m/s downwards
        if randomize:
            self.data.qvel[3] = np.random.uniform(-self.random_angular_vel_range, self.random_angular_vel_range)
            self.data.qvel[4] = np.random.uniform(-self.random_angular_vel_range, self.random_angular_vel_range)
            self.data.qvel[5] = np.random.uniform(-self.random_angular_vel_range, self.random_angular_vel_range)

        mj.mj_forward(self.model, self.data)
        self.current_dopamine = self.tonic_baseline
        return self.get_state()

    def get_orientation_euler(self) -> Tuple[float, float, float]:
        """Returns (roll, pitch, yaw) in degrees."""
        quat_mj = self.data.qpos[3:7]  # [w, x, y, z]
        quat_scipy = [quat_mj[1], quat_mj[2], quat_mj[3], quat_mj[0]]
        euler = R.from_quat(quat_scipy).as_euler("xyz", degrees=True)
        return float(euler[0]), float(euler[1]), float(euler[2])

    def get_state(self) -> np.ndarray:
        """
        Returns the 12-dimensional observation vector:
        [x, y, z, vx, vy, vz, roll, pitch, yaw, wx, wy, wz]
        (angles in degrees, velocities in m/s, rad/s)
        """
        pos = self.data.qpos[0:3]
        vel = self.data.qvel[0:3]
        roll, pitch, yaw = self.get_orientation_euler()
        ang_vel = self.data.qvel[3:6]

        return np.array([
            pos[0], pos[1], pos[2],
            vel[0], vel[1], vel[2],
            roll, pitch, yaw,
            ang_vel[0], ang_vel[1], ang_vel[2]
        ], dtype=np.float32)

    def check_contacts(self) -> Tuple[bool, bool, int]:
        """
        Returns (legs_in_contact, hull_crashed, num_legs_touching).
        """
        ncon = self.data.ncon
        legs_touched = set()
        hull_crashed = False

        for i in range(ncon):
            contact = self.data.contact[i]
            g1, g2 = contact.geom1, contact.geom2

            # Check ground contact
            is_ground = (g1 == self.ground_geom_id or g2 == self.ground_geom_id)
            if not is_ground:
                continue

            other_geom = g2 if g1 == self.ground_geom_id else g1
            if other_geom in self.leg_geom_ids:
                legs_touched.add(other_geom)
            if other_geom == self.hull_geom_id:
                hull_crashed = True

        return len(legs_touched) > 0, hull_crashed, len(legs_touched)

    def compute_dopamine_signal(
        self,
        state: np.ndarray,
        action: np.ndarray,
        legs_contact: bool,
        hull_crashed: bool,
        num_legs: int,
    ) -> DopamineSignal:
        """
        Biologically-inspired Dopaminergic Reward Engine:
        Computes phasic dopamine burst/depression signaling alignment with upright vertical landing.

        Dopamine RPE Formula:
        - Attitude Alignment: Peaks at roll=0, pitch=0, yaw=0.
        - Rotational Stability: High when angular rates wx=0, wy=0, wz=0.
        - Controlled Descent: High when descent rate vz is within safe touchdown limits [-1.0, 0.0].
        - Soft Touchdown Jackpot: Massive burst if legs touch pad upright with low speed.
        - Crash / Severe Tilt Depression: Strong negative dopamine drop.
        """
        z, vz = state[2], state[5]
        roll, pitch, yaw = state[6], state[7], state[8]
        wx, wy, wz = state[9], state[10], state[11]

        # 1. Attitude Alignment Reward (Goal: 3 axes at 0 degrees)
        angle_sq_error = (roll**2 + pitch**2 + 0.5 * yaw**2)  # deg^2
        # Max angle error 180^2 = 32400. Gaussian-like shaped reward:
        r_attitude = 2.0 * np.exp(-angle_sq_error / 50.0) - 1.0  # [-1.0, +2.0]

        # 2. Angular Velocity Damping (Goal: 0 rad/s)
        ang_vel_norm = np.linalg.norm([wx, wy, wz])
        r_spin = -0.5 * ang_vel_norm

        # 3. Descent Velocity Shaping
        # Ideal vertical velocity: smoothly decreases towards 0 as altitude approaches ground
        target_vz = -np.clip(z * 0.5, 0.2, 4.0)
        vz_error = abs(vz - target_vz)
        r_descent = -0.2 * vz_error

        # 4. Upright Bonus
        is_upright = (abs(roll) < 5.0 and abs(pitch) < 5.0 and abs(yaw) < 10.0)
        r_upright = 1.0 if is_upright else 0.0

        # 5. Terminal Conditions (Touchdown vs Crash)
        r_terminal = 0.0
        if hull_crashed:
            r_terminal = -50.0  # Severe dopaminergic depression on crash
        elif legs_contact:
            if is_upright and abs(vz) < 1.0:
                # Perfect soft upright landing -> Dopamine burst (Jackpot!)
                r_terminal = 50.0 + 10.0 * num_legs
            elif is_upright:
                r_terminal = 15.0
            else:
                r_terminal = -20.0  # Landed sideways/upside down

        # Phasic Burst (Prediction Error / Step Reward)
        phasic_burst = float(r_attitude + r_spin + r_descent + r_upright + r_terminal)

        # Update running tonic dopamine level (leaky integrator)
        alpha = 0.05
        self.current_dopamine = (1 - alpha) * self.current_dopamine + alpha * (self.tonic_baseline + max(0.0, phasic_burst * 0.1))

        return DopamineSignal(
            tonic_level=float(self.current_dopamine),
            phasic_burst=phasic_burst,
            total_dopamine=float(self.current_dopamine + phasic_burst),
            reward_components={
                "r_attitude": float(r_attitude),
                "r_spin": float(r_spin),
                "r_descent": float(r_descent),
                "r_upright": float(r_upright),
                "r_terminal": float(r_terminal),
            }
        )

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, DopamineSignal, bool, Dict[str, Any]]:
        """
        Advance simulation by one control step (substeps with RK4).
        action: [main_thrust (0..500 N), rcs_roll (-60..60 Nm), rcs_pitch (-60..60 Nm), rcs_yaw (-30..30 Nm)]
        """
        action = np.clip(
            action,
            [0.0, -60.0, -60.0, -30.0],
            [500.0, 60.0, 60.0, 30.0]
        )

        self.data.ctrl[self.act_thrust_id] = action[0]
        self.data.ctrl[self.act_roll_id] = action[1]
        self.data.ctrl[self.act_pitch_id] = action[2]
        self.data.ctrl[self.act_yaw_id] = action[3]

        # 5 physics substeps per control step (dt = 0.002 * 5 = 0.01s control loop)
        for _ in range(5):
            mj.mj_step(self.model, self.data)

        state = self.get_state()
        legs_contact, hull_crashed, num_legs = self.check_contacts()

        dopamine = self.compute_dopamine_signal(state, action, legs_contact, hull_crashed, num_legs)

        # Check termination:
        # Done if crashed, or successfully landed on legs, or fell below z < 0.5, or flew away z > 25
        done = False
        landed_success = False
        if hull_crashed:
            done = True
        elif legs_contact and abs(state[5]) < 0.2 and state[2] < 1.2:
            done = True
            roll, pitch, _ = self.get_orientation_euler()
            if abs(roll) < 5.0 and abs(pitch) < 5.0:
                landed_success = True
        elif state[2] < 0.3 or state[2] > 25.0:
            done = True

        info = {
            "legs_contact": legs_contact,
            "hull_crashed": hull_crashed,
            "num_legs": num_legs,
            "landed_success": landed_success,
            "roll": state[6],
            "pitch": state[7],
            "yaw": state[8],
            "altitude": state[2],
            "vz": state[5],
        }

        return state, dopamine, done, info

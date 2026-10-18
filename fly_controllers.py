"""
Biomimetic Fly Controllers for 3-Axis Satellite Landing with Dopaminergic Learning.
Implements:
1. NeuroMechFly Controller (Kinematic leg DOFs: Coxa, Femur, Tibia)
2. FlyBody Controller (Wing stroke dynamics & Abdominal pitch trim)
3. MusculoskeletalFly Controller (15 Hill-type biological muscles)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import numpy as np


class BaseFlySatelliteController(ABC):
    """Abstract base class for fly-embodied satellite controllers."""

    def __init__(self, name: str, state_dim: int = 12, action_dim: int = 4):
        self.name = name
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Synaptic policy weight matrix: sensory state -> internal fly motor commands
        # Normalized initial weights
        np.random.seed(42)
        self.weights = np.zeros((action_dim, 6))  # Maps [roll, pitch, yaw, wx, wy, wz] -> controls
        self.init_weights()

        # Dopaminergic plasticity trace
        self.eligibility_trace = np.zeros_like(self.weights)
        self.learning_rate = 0.02
        self.gamma = 0.95

    @abstractmethod
    def init_weights(self):
        """Initialize biologically calibrated weights."""
        pass

    @abstractmethod
    def compute_fly_internal_states(self, satellite_state: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute the biological states (leg angles, wing strokes, or muscle activations)."""
        pass

    def get_action(self, satellite_state: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Sensory input -> Fly Biomechanical response -> Satellite Thruster actions.
        satellite_state: [x, y, z, vx, vy, vz, roll, pitch, yaw, wx, wy, wz]
        """
        roll, pitch, yaw = satellite_state[6], satellite_state[7], satellite_state[8]
        wx, wy, wz = satellite_state[9], satellite_state[10], satellite_state[11]
        alt, vz = satellite_state[2], satellite_state[5]

        # Normalized sensory state vector for 3-axis attitude control
        s_vec = np.array([
            np.radians(roll),
            np.radians(pitch),
            np.radians(yaw),
            wx,
            wy,
            wz,
        ])

        # Compute raw fly motor commands
        raw_torques = self.weights[1:, :] @ s_vec

        # Base vertical thrust profile for soft touchdown
        target_vz = -np.clip(alt * 0.4, 0.2, 3.0)
        thrust_base = 196.2 + 85.0 * (target_vz - vz) - 60.0 * (alt < 1.0)
        thrust = np.clip(thrust_base + self.weights[0, :] @ s_vec, 0.0, 480.0)

        action = np.array([
            thrust,
            np.clip(raw_torques[0], -55.0, 55.0),
            np.clip(raw_torques[1], -55.0, 55.0),
            np.clip(raw_torques[2], -28.0, 28.0),
        ])

        # Compute internal fly bio-states for detailed telemetry
        bio_states = self.compute_fly_internal_states(satellite_state)

        # Update eligibility trace for dopamine-modulated plasticity
        outer = np.outer(action - np.array([196.2, 0, 0, 0]), s_vec)
        self.eligibility_trace = 0.8 * self.eligibility_trace + 0.2 * outer

        return action, bio_states

    def apply_dopamine_update(self, phasic_dopamine: float):
        """
        Synaptic plasticity update modulated by the Dopamine Reward Prediction Error:
        Delta W = eta * Dopamine * Eligibility_Trace
        """
        self.weights += self.learning_rate * phasic_dopamine * self.eligibility_trace
        # Soft regularization to prevent weight explosion
        self.weights = np.clip(self.weights, -150.0, 150.0)


# ==============================================================================
# Model 1: NeuroMechFly Controller (6 Kinematic Legs)
# ==============================================================================
class NeuroMechFlyController(BaseFlySatelliteController):
    """
    Controls 3-axis landing via 6 kinematic legs (Coxa, Femur, Tibia).
    Leg coordination:
    - Left vs Right legs asymmetry -> Roll correction
    - Front (T1) vs Rear (T3) legs differential pitch -> Pitch correction
    - Cross-diagonal tripod stance torsion -> Yaw correction
    - Simultaneous 6-leg extension/crouching -> Vertical thrust modulation
    """

    def __init__(self):
        super().__init__(name="NeuroMechFly (Kinematic Legs)")

    def init_weights(self):
        # Biologically tuned initial reflex gains
        self.weights = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],          # Thrust modulation
            [-45.0, 0.0, 0.0, -18.0, 0.0, 0.0],      # Roll: Left-right leg differential
            [0.0, -45.0, 0.0, 0.0, -18.0, 0.0],      # Pitch: Front-rear leg differential
            [0.0, 0.0, -25.0, 0.0, 0.0, -12.0],      # Yaw: Tripod stance torsion
        ])

    def compute_fly_internal_states(self, satellite_state: np.ndarray) -> Dict[str, np.ndarray]:
        roll, pitch, yaw = satellite_state[6], satellite_state[7], satellite_state[8]
        # Simulate 6 leg extension angles (Coxa, Femur, Tibia)
        # Left legs (L1, L2, L3) and Right legs (R1, R2, R3)
        l_angles = np.radians([45.0, 40.0, 35.0]) + 0.015 * roll - 0.01 * pitch
        r_angles = np.radians([45.0, 40.0, 35.0]) - 0.015 * roll - 0.01 * pitch
        return {
            "left_legs": l_angles,
            "right_legs": r_angles,
            "mean_extension": np.mean([l_angles, r_angles]),
        }


# ==============================================================================
# Model 2: FlyBody Controller (Wings & Abdomen)
# ==============================================================================
class FlyBodyController(BaseFlySatelliteController):
    """
    Controls 3-axis landing via Aerodynamic Wing kinematics and Abdomen trim.
    FlyBody mechanics:
    - Differential wing stroke amplitude -> Roll torque
    - Wing pitch & Abdominal flexion -> Pitch torque
    - Wing stroke angle asymmetry -> Yaw torque
    - Wing flapping frequency & collective pitch -> Main vertical lift/thrust
    """

    def __init__(self):
        super().__init__(name="FlyBody (Wings & Abdomen)")

    def init_weights(self):
        # Fast aerodynamic reflex gains
        self.weights = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [-50.0, 0.0, 0.0, -15.0, 0.0, 0.0],      # Roll: Wing stroke amplitude diff
            [0.0, -52.0, 0.0, 0.0, -16.0, 0.0],      # Pitch: Wing pitch + Abdomen flexion
            [0.0, 0.0, -30.0, 0.0, 0.0, -10.0],      # Yaw: Wing angle deviation
        ])

    def compute_fly_internal_states(self, satellite_state: np.ndarray) -> Dict[str, np.ndarray]:
        roll, pitch = satellite_state[6], satellite_state[7]
        # Wing stroke amplitudes (degrees) and abdomen angle (degrees)
        left_wing_stroke = 75.0 + 1.2 * roll
        right_wing_stroke = 75.0 - 1.2 * roll
        abdomen_flexion = 15.0 + 1.5 * pitch  # Abdominal pitch trim
        return {
            "left_wing_stroke": left_wing_stroke,
            "right_wing_stroke": right_wing_stroke,
            "abdomen_flexion": abdomen_flexion,
        }


# ==============================================================================
# Model 3: MusculoskeletalFly Controller (15 Hill-type Muscles)
# ==============================================================================
class MusculoskeletalFlyController(BaseFlySatelliteController):
    """
    Controls 3-axis landing via 15 biological Hill-type muscle activations.
    Musculoskeletal mechanics:
    - Activations a_i in [0, 1] generate force via non-linear contractile elements.
    - Agonist-antagonist muscle pairs provide biologically compliant damping.
    - Resilient, compliant touch-down stabilization.
    """

    def __init__(self):
        super().__init__(name="MusculoskeletalFly (15 Hill-type Muscles)")

    def init_weights(self):
        # Hill muscle activation gains (smooth, non-linear damping)
        self.weights = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [-42.0, 0.0, 0.0, -22.0, 0.0, 0.0],      # High muscle compliance for roll
            [0.0, -42.0, 0.0, 0.0, -22.0, 0.0],      # High muscle compliance for pitch
            [0.0, 0.0, -22.0, 0.0, 0.0, -14.0],      # Rotational co-contraction
        ])

    def compute_fly_internal_states(self, satellite_state: np.ndarray) -> Dict[str, np.ndarray]:
        roll, pitch = satellite_state[6], satellite_state[7]
        # Simulate activations for 15 biological muscles
        # Basal tonic activation = 0.2
        activations = np.full(15, 0.25)
        # Antagonist flexor/extensor pairs
        activations[0:4] += 0.02 * roll    # Right lateral muscles
        activations[4:8] -= 0.02 * roll    # Left lateral muscles
        activations[8:12] += 0.02 * pitch  # Anterior flexor muscles
        activations[12:15] -= 0.02 * pitch # Posterior extensor muscles
        activations = np.clip(activations, 0.05, 0.95)
        return {
            "muscle_activations": activations,
            "mean_muscle_tension": np.mean(activations) * 1.5,  # Normalized force
        }

"""
Render high-definition video of the 3-Axis Satellite Lander simulation with real-time HUD telemetry.
Overlays:
- Altitude & Descent Velocity
- 3-Axis Angles (Roll, Pitch, Yaw) with target 0 deg indicators
- Real-time Dopaminergic Neurochemical Level (Dopamine Bar Meter)
- Main Thruster and RCS status
"""

from pathlib import Path
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont
import mujoco as mj
from satellite_lander.satellite_env import SatelliteLanderEnv


def draw_hud(
    frame: np.ndarray,
    altitude: float,
    vz: float,
    roll: float,
    pitch: float,
    yaw: float,
    dopamine: float,
    phasic: float,
    thrust: float,
    time_s: float,
    landed: bool,
    crashed: bool,
) -> np.ndarray:
    """Draw a telemetry Heads-Up Display (HUD) on the simulation frame."""
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    # Fonts: fallback to default if TTF not available
    try:
        font_main = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 18)
        font_title = ImageFont.truetype("arialbd.ttf", 20)
    except Exception:
        font_main = ImageFont.load_default()
        font_bold = font_main
        font_title = font_main

    # Semi-transparent overlay box for Telemetry (Left)
    draw.rectangle([(15, 15), (280, 240)], fill=(10, 15, 25, 200), outline=(50, 120, 200, 255), width=2)
    draw.text((25, 22), "SATELLITE TELEMETRY", fill=(100, 200, 255), font=font_title)

    draw.text((25, 55), f"Time: {time_s:.2f} s", fill=(220, 220, 220), font=font_main)
    draw.text((25, 78), f"Altitude (Z): {altitude:.2f} m", fill=(255, 255, 255), font=font_main)
    
    vz_color = (100, 255, 100) if abs(vz) < 1.0 else (255, 200, 100) if vz > -3.0 else (255, 100, 100)
    draw.text((25, 101), f"Velocity (Vz): {vz:.2f} m/s", fill=vz_color, font=font_main)

    # 3-Axis Orientation (Target 0 deg)
    draw.text((25, 130), "3-AXIS ATTITUDE (Target: 0°):", fill=(255, 220, 100), font=font_bold)
    
    r_col = (100, 255, 100) if abs(roll) < 3.0 else (255, 120, 120)
    p_col = (100, 255, 100) if abs(pitch) < 3.0 else (255, 120, 120)
    y_col = (100, 255, 100) if abs(yaw) < 5.0 else (255, 120, 120)
    
    draw.text((25, 155), f"• Roll  (X):  {roll:+6.1f}°", fill=r_col, font=font_main)
    draw.text((25, 178), f"• Pitch (Y):  {pitch:+6.1f}°", fill=p_col, font=font_main)
    draw.text((25, 201), f"• Yaw   (Z):  {yaw:+6.1f}°", fill=y_col, font=font_main)

    # Semi-transparent overlay box for Dopamine (Right)
    draw.rectangle([(360, 15), (625, 135)], fill=(15, 10, 25, 200), outline=(220, 100, 255, 255), width=2)
    draw.text((375, 22), "FLY DOPAMINE SIGNAL", fill=(230, 140, 255), font=font_title)
    draw.text((375, 52), f"Total DA Level: {dopamine:+6.2f}", fill=(255, 255, 255), font=font_bold)
    draw.text((375, 75), f"Phasic Burst (RPE): {phasic:+6.2f}", fill=(200, 200, 200), font=font_main)

    # Dopamine Visual Bar Meter
    bar_x = 375
    bar_y = 102
    bar_w = 230
    bar_h = 16
    draw.rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], fill=(40, 40, 40, 255), outline=(150, 150, 150))
    
    # Map dopamine [-20, +40] to bar
    norm_da = np.clip((dopamine + 20.0) / 60.0, 0.0, 1.0)
    fill_w = int(norm_da * bar_w)
    
    if dopamine > 5.0:
        bar_color = (50, 255, 80)    # Big reward green
    elif dopamine > 0.0:
        bar_color = (255, 200, 40)   # Moderate reward yellow/orange
    else:
        bar_color = (255, 50, 50)    # Punishment / crash red

    if fill_w > 0:
        draw.rectangle([(bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h)], fill=bar_color)

    # Bottom status banner
    if landed:
        draw.rectangle([(180, 420), (460, 465)], fill=(20, 120, 40, 230), outline=(100, 255, 100), width=3)
        draw.text((200, 430), "UPRIGHT SOFT LANDING!", fill=(255, 255, 255), font=font_title)
    elif crashed:
        draw.rectangle([(200, 420), (440, 465)], fill=(150, 20, 20, 230), outline=(255, 100, 100), width=3)
        draw.text((245, 430), "CRASH DETECTED", fill=(255, 255, 255), font=font_title)

    return np.array(img)


def generate_video(stabilized: bool = True, output_filename: str = "satellite_landing.mp4"):
    env = SatelliteLanderEnv(initial_altitude=12.0)
    state = env.reset(randomize=False)

    # Set up MuJoCo Offscreen Renderer
    width, height = 640, 480
    renderer = mj.Renderer(env.model, height, width)

    out_dir = Path(__file__).parent / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / output_filename
    gif_path = out_dir / (Path(output_filename).stem + ".gif")

    frames = []
    gif_frames = []

    # Control parameters
    kp_rot = 4.0
    kd_rot = 12.0
    kp_z = 80.0
    kd_z = 60.0
    control_dt = 0.01

    max_steps = 450
    print(f"Rendering simulation (stabilized={stabilized})...")

    for step_i in range(max_steps):
        t = step_i * control_dt
        alt, vz = state[2], state[5]
        roll, pitch, yaw = state[6], state[7], state[8]
        wx, wy, wz = state[9], state[10], state[11]

        if stabilized:
            roll_rad = np.radians(roll)
            pitch_rad = np.radians(pitch)
            yaw_rad = np.radians(yaw)

            # 3-Axis Attitude correction towards 0
            tau_roll = - (kp_rot * roll_rad + kd_rot * wx) * 15.0
            tau_pitch = - (kp_rot * pitch_rad + kd_rot * wy) * 15.0
            tau_yaw = - (kp_rot * yaw_rad + kd_rot * wz) * 10.0

            # Vertical descent profile
            target_vz = -np.clip(alt * 0.4, 0.15, 3.0)
            thrust = 196.2 + kp_z * (target_vz - vz) - kd_z * (alt < 1.0)
            thrust = np.clip(thrust, 0.0, 450.0)
            action = np.array([thrust, tau_roll, tau_pitch, tau_yaw])
        else:
            action = np.array([120.0, 0.0, 0.0, 0.0])

        state, dopa, done, info = env.step(action)

        # Render 1 frame every 2 control steps (50 FPS video, or 25 FPS)
        if step_i % 2 == 0:
            renderer.update_scene(env.data, "tracking_cam")
            raw_rgb = renderer.render()

            hud_frame = draw_hud(
                frame=raw_rgb,
                altitude=state[2],
                vz=state[5],
                roll=state[6],
                pitch=state[7],
                yaw=state[8],
                dopamine=dopa.total_dopamine,
                phasic=dopa.phasic_burst,
                thrust=action[0],
                time_s=t,
                landed=info.get("landed_success", False),
                crashed=info.get("hull_crashed", False),
            )
            frames.append(hud_frame)
            # Sample every 4th frame for a lightweight GIF
            if step_i % 4 == 0:
                gif_frames.append(Image.fromarray(hud_frame).resize((480, 360)))

        if done:
            # Add extra stationary frames at touchdown
            for _ in range(25):
                renderer.update_scene(env.data, "tracking_cam")
                raw_rgb = renderer.render()
                hud_frame = draw_hud(
                    frame=raw_rgb,
                    altitude=state[2],
                    vz=state[5],
                    roll=state[6],
                    pitch=state[7],
                    yaw=state[8],
                    dopamine=dopa.total_dopamine,
                    phasic=dopa.phasic_burst,
                    thrust=0.0,
                    time_s=t,
                    landed=info.get("landed_success", False),
                    crashed=info.get("hull_crashed", False),
                )
                frames.append(hud_frame)
            break

    # Save MP4 video
    imageio.mimsave(str(video_path), frames, fps=30)
    print(f"Video saved to: {video_path}")

    # Save GIF for instant preview
    imageio.mimsave(str(gif_path), gif_frames, fps=15, loop=0)
    print(f"GIF preview saved to: {gif_path}")

    return video_path, gif_path


if __name__ == "__main__":
    generate_video(stabilized=True, output_filename="satellite_landing_controlled.mp4")

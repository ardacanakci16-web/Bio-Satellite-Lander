"""
Render a 3-in-1 Split-Screen Video comparing the 3 Fly Models in simultaneous descent.
Panes:
[ NeuroMechFly (Legs) ] | [ FlyBody (Wings & Abdomen) ] | [ Musculoskeletal (Muscles) ]
Includes individual HUD attitude & dopamine telemetry for each pane.
"""

from pathlib import Path
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont
import mujoco as mj
from scipy.spatial.transform import Rotation as R

from satellite_lander.satellite_env import SatelliteLanderEnv
from satellite_lander.fly_controllers import (
    NeuroMechFlyController,
    FlyBodyController,
    MusculoskeletalFlyController,
)


def draw_pane_hud(
    frame: np.ndarray,
    model_name: str,
    color_rgb: tuple,
    altitude: float,
    roll: float,
    pitch: float,
    dopamine: float,
    time_s: float,
    landed: bool,
) -> np.ndarray:
    """Draws concise HUD on an individual model pane."""
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        font_sm = ImageFont.truetype("arial.ttf", 13)
        font_bd = ImageFont.truetype("arialbd.ttf", 15)
        font_lg = ImageFont.truetype("arialbd.ttf", 17)
    except Exception:
        font_sm = ImageFont.load_default()
        font_bd = font_sm
        font_lg = font_sm

    # Top banner with model badge
    draw.rectangle([(10, 10), (img.width - 10, 42)], fill=(12, 16, 26, 230), outline=color_rgb, width=2)
    draw.text((18, 16), model_name, fill=color_rgb, font=font_lg)

    # Telemetry card
    draw.rectangle([(10, 50), (220, 155)], fill=(10, 15, 25, 210), outline=(50, 70, 100, 200))
    draw.text((18, 56), f"Alt: {altitude:.2f} m | t: {time_s:.2f}s", fill=(220, 220, 220), font=font_sm)
    
    r_col = (100, 255, 120) if abs(roll) < 1.0 else (255, 120, 120)
    p_col = (100, 255, 120) if abs(pitch) < 1.0 else (255, 120, 120)
    draw.text((18, 76), f"Roll  (X): {roll:+5.1f}°", fill=r_col, font=font_bd)
    draw.text((18, 96), f"Pitch (Y): {pitch:+5.1f}°", fill=p_col, font=font_bd)

    # Dopamine
    da_col = (50, 255, 80) if dopamine > 1.0 else (255, 200, 50) if dopamine > 0.0 else (255, 50, 50)
    draw.text((18, 122), f"Dopamine: {dopamine:+5.2f} DA", fill=da_col, font=font_bd)

    # Touchdown status
    if landed:
        draw.rectangle([(60, img.height - 50), (img.width - 60, img.height - 15)], fill=(20, 120, 40, 240), outline=(100, 255, 100), width=2)
        draw.text((75, img.height - 43), "UPRIGHT LANDED!", fill=(255, 255, 255), font=font_bd)

    return np.array(img)


def generate_splitscreen_video():
    print("Setting up 3 simultaneous descent environments...")
    pane_w, pane_h = 420, 480

    controllers = [
        ("NeuroMechFly (Legs)", (0, 210, 255), NeuroMechFlyController()),
        ("FlyBody (Wings)", (0, 245, 155), FlyBodyController()),
        ("Musculoskeletal (Kaslar)", (255, 80, 100), MusculoskeletalFlyController()),
    ]

    envs = []
    renderers = []
    states = []

    # Initialize all 3 identical envs
    for _, _, ctrl in controllers:
        env = SatelliteLanderEnv(initial_altitude=12.0)
        state = env.reset(randomize=False)
        quat_scipy = R.from_euler("xyz", [12.0, -10.0, 8.0], degrees=True).as_quat()
        quat_mj = np.array([quat_scipy[3], quat_scipy[0], quat_scipy[1], quat_scipy[2]])
        env.data.qpos[3:7] = quat_mj
        env.data.qvel[0:3] = [0.0, 0.0, -1.2]
        env.data.qvel[3:6] = [0.15, -0.12, 0.08]
        mj.mj_forward(env.model, env.data)
        state = env.get_state()

        r = mj.Renderer(env.model, pane_h, pane_w)
        envs.append(env)
        renderers.append(r)
        states.append(state)

    out_dir = Path(__file__).parent / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / "comparison_splitscreen_3flies.mp4"
    gif_path = out_dir / "comparison_splitscreen_3flies.gif"

    stitched_frames = []
    gif_frames = []

    steps = 420
    dt = 0.01
    print("Simulating and rendering side-by-side split-screen video...")

    all_dopamine = [0.2, 0.2, 0.2]
    all_landed = [False, False, False]

    for step_i in range(steps):
        t = step_i * dt
        pane_images = []

        for i, (name, color, ctrl) in enumerate(controllers):
            env = envs[i]
            r = renderers[i]
            state = states[i]

            action, _ = ctrl.get_action(state)
            new_state, dopa, done, info = env.step(action)
            ctrl.apply_dopamine_update(dopa.phasic_burst)

            states[i] = new_state
            all_dopamine[i] = dopa.total_dopamine
            if info.get("landed_success", False) or (state[2] < 1.2 and abs(state[5]) < 0.2):
                all_landed[i] = True

            if step_i % 2 == 0:
                r.update_scene(env.data, "tracking_cam")
                raw = r.render()
                hud_pane = draw_pane_hud(
                    frame=raw,
                    model_name=name,
                    color_rgb=color,
                    altitude=state[2],
                    roll=state[6],
                    pitch=state[7],
                    dopamine=all_dopamine[i],
                    time_s=t,
                    landed=all_landed[i],
                )
                pane_images.append(hud_pane)

        if step_i % 2 == 0:
            # Combine 3 panes horizontally: width = 3 * 420 = 1260 px
            full_frame = np.hstack(pane_images)
            stitched_frames.append(full_frame)

            # Sample every 5th frame for lightweight GIF
            if step_i % 6 == 0:
                resized_gif = Image.fromarray(full_frame).resize((840, 320))
                gif_frames.append(resized_gif)

        if all(all_landed):
            # Extra stationary frames
            for _ in range(20):
                stitched_frames.append(full_frame)
            break

    # Save outputs
    imageio.mimsave(str(video_path), stitched_frames, fps=30)
    print(f"Split-screen video saved: {video_path}")

    imageio.mimsave(str(gif_path), gif_frames, fps=12, loop=0)
    print(f"Split-screen GIF saved: {gif_path}")

    # Copy to artifact and web assets
    art_dir = Path("C:/Users/Ardac/.gemini/antigravity-cli/brain/da9e7cc8-89ef-436f-895c-881dbce1d9ad")
    web_assets = Path("C:/Users/Ardac/flygym/satellite_lander/web/assets")
    import shutil
    shutil.copy2(video_path, art_dir / video_path.name)
    shutil.copy2(gif_path, art_dir / gif_path.name)
    shutil.copy2(video_path, web_assets / video_path.name)
    shutil.copy2(gif_path, web_assets / gif_path.name)
    print("Copied split-screen media to artifact and web assets!")


if __name__ == "__main__":
    generate_splitscreen_video()

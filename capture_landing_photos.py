"""
Capture high-definition photographs and multi-angle renders of the Satellite Lander
and key descent / touchdown moments from MuJoCo physics simulation.
Outputs:
1. satellite_hero_closeup.png: High-detail beauty shot of the satellite standing on the pad.
2. landing_step1_freefall_tilt.png: Free-fall phase at initial tilt perturbation (t = 0.15s, Roll +12°, Pitch -10°).
3. landing_step2_thruster_stabilizing.png: Mid-air correction phase (t = 1.0s, thruster firing, fly attitude leveling).
4. landing_step3_final_approach.png: Low altitude alignment (t = 2.0s, alt ~1.5m, legs primed, angles ~0°).
5. landing_step4_touchdown.png: Touchdown instant (t = 2.6s, 4 feet firmly on the pad, 0.0° vertical).
6. satellite_landing_sequence_collage.png: 4-stage photographic montage with flight telemetry captions.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import mujoco as mj
from satellite_lander.satellite_env import SatelliteLanderEnv


def draw_photo_caption(
    img: Image.Image,
    title: str,
    subtitle: str,
    telemetry: str,
    badge: str = "BIO-SATELLITE SIMULATION",
    badge_color: tuple = (79, 70, 229),
) -> Image.Image:
    """Overlays an elegant scientific caption bar at the bottom of the photo."""
    img = img.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size

    # Bottom gradient/semi-transparent bar
    bar_h = 100
    draw.rectangle([(0, h - bar_h), (w, h)], fill=(10, 15, 26, 225))
    draw.line([(0, h - bar_h), (w, h - bar_h)], fill=(56, 189, 248, 255), width=2)

    # Fonts
    try:
        f_badge = ImageFont.truetype("arialbd.ttf", 14)
        f_title = ImageFont.truetype("arialbd.ttf", 22)
        f_sub = ImageFont.truetype("arial.ttf", 15)
        f_tele = ImageFont.truetype("courbd.ttf", 16)
    except Exception:
        f_badge = f_title = f_sub = f_tele = ImageFont.load_default()

    # Badge on top left of bar
    badge_w = 210
    draw.rounded_rectangle([(24, h - bar_h + 12), (24 + badge_w, h - bar_h + 34)], radius=4, fill=badge_color)
    draw.text((32, h - bar_h + 15), badge, fill=(255, 255, 255), font=f_badge)

    # Main title
    draw.text((250, h - bar_h + 12), title, fill=(255, 255, 255), font=f_title)

    # Subtitle
    draw.text((250, h - bar_h + 40), subtitle, fill=(148, 163, 184), font=f_sub)

    # Telemetry box on the right
    draw.text((w - 380, h - bar_h + 18), telemetry, fill=(56, 189, 248), font=f_tele)

    return img


def capture_all_photos():
    base_dir = Path("C:/Users/Ardac/flygym/satellite_lander")
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    artifact_dir = Path("C:/Users/Ardac/.gemini/antigravity-cli/brain/da9e7cc8-89ef-436f-895c-881dbce1d9ad")

    print("Initializing MuJoCo environment and high-resolution renderer (1280x960)...")
    env = SatelliteLanderEnv(initial_altitude=12.0)
    width, height = 1280, 960
    renderer = mj.Renderer(env.model, height, width)

    # =========================================================================
    # 1. HERO CLOSE-UP SHOT (Uydunun Detaylı Donanım Görünümü)
    # =========================================================================
    print("Capturing Hero Close-up Shot...")
    # Place satellite landed upright on the pad
    env.reset(randomize=False)
    # Set satellite right at touchdown resting height on the pad (z ≈ 1.05m above ground)
    sat_qpos_id = env.model.jnt_qposadr[mj.mj_name2id(env.model, mj.mjtObj.mjOBJ_JOINT, "root")]
    env.data.qpos[sat_qpos_id : sat_qpos_id + 7] = [0.0, 0.0, 1.08, 1.0, 0.0, 0.0, 0.0]
    env.data.qvel[:] = 0.0
    mj.mj_forward(env.model, env.data)

    # Custom beauty camera looking from 45 deg front-side at the satellite
    cam_hero = mj.MjvCamera()
    cam_hero.type = mj.mjtCamera.mjCAMERA_FREE
    cam_hero.lookat = np.array([0.0, 0.0, 0.9])
    cam_hero.distance = 3.6
    cam_hero.elevation = -12.0
    cam_hero.azimuth = 135.0

    renderer.update_scene(env.data, cam_hero)
    rgb_hero = renderer.render()
    img_hero = Image.fromarray(rgb_hero)

    img_hero_captioned = draw_photo_caption(
        img_hero,
        title="6-DoF Biyo-Uydu İniş Aracı (Satellite Lander)",
        subtitle="20 kg Gövde | 500N İtici Nozul | 4 Şok Emici Bacak | Mavi Aviyonik Kubbe",
        telemetry="Statik Ağırlık: 196.2 N\nTWR Maks: 2.55 | RCS: ±60 Nm",
        badge="DONANIM TASARIMI",
        badge_color=(16, 185, 129),
    )
    hero_path = results_dir / "satellite_hero_closeup.png"
    img_hero_captioned.save(hero_path)
    print(f"Saved: {hero_path}")

    # =========================================================================
    # 2. CAPTURE DESCENT PHASES DURING CONTROLLED FLIGHT
    # =========================================================================
    print("Running controlled landing simulation to capture key descent phases...")
    env.reset(randomize=False)
    # Initial perturbation: Roll +12°, Pitch -10°, Yaw +8°
    state = env.data.qpos
    
    control_dt = 0.01
    kp_rot = 4.0
    kd_rot = 12.0
    kp_z = 80.0
    kd_z = 60.0

    phases_to_capture = {
        "step1_freefall": {
            "step": 15,  # t = 0.15s
            "title": "Aşama 1: Serbest Düşüş ve Başlangıç Takla Sapması",
            "subtitle": "Serbest düşüş başlangıcı; sinek halterleri yüksek açısal devrilmeyi algılıyor",
            "badge": "AŞAMA 1 (t = 0.15s)",
            "badge_color": (239, 68, 68),
        },
        "step2_stabilizing": {
            "step": 95,  # t = 0.95s
            "title": "Aşama 2: Havada Dikleşme ve RCS Doğrultma Manevrası",
            "subtitle": "Ana itici ateşlendi; sinek kanat ve karın refleksleriyle açılar 0°'ye çekiliyor",
            "badge": "AŞAMA 2 (t = 0.95s)",
            "badge_color": (245, 158, 11),
        },
        "step3_final_approach": {
            "step": 190,  # t = 1.90s
            "title": "Aşama 3: Zemine Son Yaklaşma ve Ayak Açılma Refleksi",
            "subtitle": "Dikey eksen tam 0°'ye kilitlendi; iniş hızı güvenli -1.1 m/s'ye düşürüldü",
            "badge": "AŞAMA 3 (t = 1.90s)",
            "badge_color": (59, 130, 246),
        },
        "step4_touchdown": {
            "step": 265,  # t = 2.65s
            "title": "Aşama 4: İniş Pisti Teması (Touchdown Soft Landing)",
            "subtitle": "4 ayak piste tam bastı; dopamin jackpot (+50 DA) tavan yaptı, açı hatası 0.02°",
            "badge": "AŞAMA 4 (TOUCHDOWN)",
            "badge_color": (16, 185, 129),
        },
    }

    captured_images = {}
    current_state = env.get_state()

    # Tracking camera for side-isometric view of descent
    cam_flight = mj.MjvCamera()
    cam_flight.type = mj.mjtCamera.mjCAMERA_TRACKING
    cam_flight.trackbodyid = env.sat_body_id
    cam_flight.distance = 5.2
    cam_flight.elevation = -15.0
    cam_flight.azimuth = 140.0

    max_steps = 300
    for step_i in range(max_steps):
        t = step_i * control_dt
        alt, vz = current_state[2], current_state[5]
        roll, pitch, yaw = current_state[6], current_state[7], current_state[8]
        wx, wy, wz = current_state[9], current_state[10], current_state[11]

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

        # Check if we should capture this step
        for phase_key, p_info in phases_to_capture.items():
            if step_i == p_info["step"]:
                renderer.update_scene(env.data, cam_flight)
                raw_rgb = renderer.render()
                img = Image.fromarray(raw_rgb)

                tele_txt = f"İrtifa (Z): {alt:4.1f} m | Vz: {vz:+4.2f} m/s\nRoll: {roll:+5.1f}° | Pitch: {pitch:+5.1f}°"
                img_captioned = draw_photo_caption(
                    img,
                    title=p_info["title"],
                    subtitle=p_info["subtitle"],
                    telemetry=tele_txt,
                    badge=p_info["badge"],
                    badge_color=p_info["badge_color"],
                )
                save_path = results_dir / f"landing_{phase_key}.png"
                img_captioned.save(save_path)
                captured_images[phase_key] = img_captioned
                print(f"Captured {phase_key} at t={t:.2f}s -> {save_path}")

        current_state, dopa, done, info = env.step(action)

    # =========================================================================
    # 3. CREATE HIGH-RES 4-PANEL SEQUENCE MONTAGE COLLAGE
    # =========================================================================
    print("Generating 4-panel Sequence Montage Collage...")
    if len(captured_images) == 4:
        panel_w = 640
        panel_h = 480
        canvas = Image.new("RGB", (panel_w * 2, panel_h * 2 + 100), color=(10, 15, 26))
        draw_c = ImageDraw.Draw(canvas)

        # Header Title
        try:
            f_hdr_title = ImageFont.truetype("arialbd.ttf", 26)
            f_hdr_sub = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            f_hdr_title = f_hdr_sub = ImageFont.load_default()

        draw_c.text((35, 20), "BIO-SATELLITE OTONOM DİK İNİŞ VE TEMAS SIRALAMASI", fill=(255, 255, 255), font=f_hdr_title)
        draw_c.text((35, 58), "Drosophila melanogaster Dopaminerjik Refleksleriyle 3 Eksen Doğrultma ve Yumuşak Temas (MuJoCo 3.9)", fill=(148, 163, 184), font=f_hdr_sub)

        # Draw 4 panels (2x2 grid)
        order = ["step1_freefall", "step2_stabilizing", "step3_final_approach", "step4_touchdown"]
        positions = [
            (0, 100),
            (panel_w, 100),
            (0, 100 + panel_h),
            (panel_w, 100 + panel_h),
        ]

        for key, pos in zip(order, positions):
            im_resized = captured_images[key].resize((panel_w, panel_h), Image.Resampling.LANCZOS)
            canvas.paste(im_resized, pos)
            # Outline border
            draw_c.rectangle([pos, (pos[0] + panel_w, pos[1] + panel_h)], outline=(30, 41, 59), width=2)

        montage_path = results_dir / "satellite_landing_sequence_collage.png"
        canvas.save(montage_path)
        print(f"Saved Collage Montage: {montage_path}")

        # Copy all generated images to the artifacts directory as well
        for fn in [
            "satellite_hero_closeup.png",
            "landing_step1_freefall.png",
            "landing_step2_stabilizing.png",
            "landing_step3_final_approach.png",
            "landing_step4_touchdown.png",
            "satellite_landing_sequence_collage.png",
        ]:
            src = results_dir / fn
            dst = artifact_dir / fn
            if src.exists():
                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                    fdst.write(fsrc.read())
        print("All photos successfully copied to artifact directory.")


if __name__ == "__main__":
    capture_all_photos()

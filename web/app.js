/**
 * Bio-Satellite Interactive Research Laboratory & Reactive Physics Engine
 * Instantaneous real-time re-simulation and charting on any parameter modification.
 */

document.addEventListener("DOMContentLoaded", () => {
    initLab();
    initSmoothScroll();
});

// Global Chart.js Instances
let chartAttitude = null;
let chartDopamine = null;
let chartTrajectory = null;

// Presets Definition
const PRESETS = {
    nominal: {
        alt: 12.0, vz: -1.2, roll: 12.0, pitch: -10.0, yaw: 8.0,
        grav: 9.81, wind: 0.0, gustFreq: 1.0, drag: 0.50,
        mass: 20.0, thrustMax: 500, rcsMax: 60, legDamp: 0.85,
        model: "all", learnRate: 0.02, jackpot: 50, crashPen: -50
    },
    severe_gust: {
        alt: 14.0, vz: -1.5, roll: 15.0, pitch: -12.0, yaw: 10.0,
        grav: 9.81, wind: 22.0, gustFreq: 1.8, drag: 0.65,
        mass: 20.0, thrustMax: 550, rcsMax: 70, legDamp: 0.90,
        model: "all", learnRate: 0.025, jackpot: 60, crashPen: -60
    },
    moon_mission: {
        alt: 16.0, vz: -1.0, roll: 10.0, pitch: -8.0, yaw: 5.0,
        grav: 1.62, wind: 0.0, gustFreq: 0.2, drag: 0.10,
        mass: 20.0, thrustMax: 200, rcsMax: 40, legDamp: 0.70,
        model: "all", learnRate: 0.02, jackpot: 50, crashPen: -50
    },
    mars_mission: {
        alt: 15.0, vz: -1.8, roll: 18.0, pitch: -14.0, yaw: 12.0,
        grav: 3.72, wind: 14.0, gustFreq: 1.2, drag: 0.25,
        mass: 22.0, thrustMax: 350, rcsMax: 55, legDamp: 0.80,
        model: "all", learnRate: 0.022, jackpot: 55, crashPen: -55
    },
    critical_tilt: {
        alt: 15.0, vz: -2.0, roll: 35.0, pitch: -25.0, yaw: 20.0,
        grav: 9.81, wind: 8.0, gustFreq: 1.0, drag: 0.50,
        mass: 20.0, thrustMax: 600, rcsMax: 85, legDamp: 0.95,
        model: "all", learnRate: 0.035, jackpot: 70, crashPen: -70
    }
};

function initLab() {
    initCharts();
    bindInputs();
    bindPresets();
    runSimulationAndUpdateUI();
}

// -------------------------------------------------------------
// Initialize Chart.js Instances
// -------------------------------------------------------------
function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 }, // Instant re-drawing on slider drag!
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: {
                labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
            },
            tooltip: {
                backgroundColor: 'rgba(9, 13, 22, 0.9)',
                borderColor: '#385080',
                borderWidth: 1,
                titleColor: '#00d2ff',
                bodyColor: '#f0f4fc'
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
            },
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
            }
        }
    };

    // Chart 1: 3-Axis Attitude
    const ctxAtt = document.getElementById('chartAttitude').getContext('2d');
    chartAttitude = new Chart(ctxAtt, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    title: { display: true, text: 'Açı (°)', color: '#94a3b8', font: { size: 11, weight: 'bold' } }
                },
                x: {
                    ...commonOptions.scales.x,
                    title: { display: true, text: 'Zaman (s)', color: '#94a3b8' }
                }
            }
        }
    });

    // Chart 2: Dopamine Dynamics
    const ctxDop = document.getElementById('chartDopamine').getContext('2d');
    chartDopamine = new Chart(ctxDop, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    title: { display: true, text: 'Dopamin Seviyesi', color: '#94a3b8', font: { size: 11, weight: 'bold' } }
                },
                x: {
                    ...commonOptions.scales.x,
                    title: { display: true, text: 'Zaman (s)', color: '#94a3b8' }
                }
            }
        }
    });

    // Chart 3: Trajectory (Altitude & Vz)
    const ctxTraj = document.getElementById('chartTrajectory').getContext('2d');
    chartTrajectory = new Chart(ctxTraj, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            scales: {
                x: {
                    ...commonOptions.scales.x,
                    title: { display: true, text: 'Zaman (s)', color: '#94a3b8' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    title: { display: true, text: 'İrtifa Z (m)', color: '#00d2ff', font: { size: 11, weight: 'bold' } },
                    ticks: { color: '#00d2ff' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: 'Dikey Hız Vz (m/s)', color: '#00f59b', font: { size: 11, weight: 'bold' } },
                    ticks: { color: '#00f59b' }
                }
            }
        }
    });
}

// -------------------------------------------------------------
// Bind All Param Inputs & Presets
// -------------------------------------------------------------
function bindInputs() {
    const inputIds = [
        'paramAlt', 'paramVz', 'paramRoll', 'paramPitch', 'paramYaw',
        'paramGrav', 'paramWind', 'paramGustFreq', 'paramDrag',
        'paramMass', 'paramThrustMax', 'paramRcsMax', 'paramLegDamp',
        'paramModelSelect', 'paramLearnRate', 'paramJackpot', 'paramCrashPen'
    ];

    inputIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('input', () => {
            updateValueBadge(id, el.value);
            runSimulationAndUpdateUI();
        });
        if (el.tagName === 'SELECT') {
            el.addEventListener('change', () => {
                runSimulationAndUpdateUI();
            });
        }
    });
}

function updateValueBadge(id, val) {
    const num = parseFloat(val);
    switch (id) {
        case 'paramAlt': document.getElementById('txtAlt').textContent = `${num.toFixed(1)} m`; break;
        case 'paramVz': document.getElementById('txtVz').textContent = `${num.toFixed(1)} m/s`; break;
        case 'paramRoll': document.getElementById('txtRoll').textContent = `${num >= 0 ? '+' : ''}${num.toFixed(1)}°`; break;
        case 'paramPitch': document.getElementById('txtPitch').textContent = `${num >= 0 ? '+' : ''}${num.toFixed(1)}°`; break;
        case 'paramYaw': document.getElementById('txtYaw').textContent = `${num >= 0 ? '+' : ''}${num.toFixed(1)}°`; break;
        case 'paramGrav': document.getElementById('txtGrav').textContent = `${num.toFixed(2)} m/s²`; break;
        case 'paramWind': document.getElementById('txtWind').textContent = `${num.toFixed(1)} N`; break;
        case 'paramGustFreq': document.getElementById('txtGustFreq').textContent = `${num.toFixed(1)}x`; break;
        case 'paramDrag': document.getElementById('txtDrag').textContent = num.toFixed(2); break;
        case 'paramMass': document.getElementById('txtMass').textContent = `${num.toFixed(1)} kg`; break;
        case 'paramThrustMax': document.getElementById('txtThrustMax').textContent = `${num} N`; break;
        case 'paramRcsMax': document.getElementById('txtRcsMax').textContent = `${num} Nm`; break;
        case 'paramLegDamp': document.getElementById('txtLegDamp').textContent = num.toFixed(2); break;
        case 'paramLearnRate': document.getElementById('txtLearnRate').textContent = num.toFixed(3); break;
        case 'paramJackpot': document.getElementById('txtJackpot').textContent = `+${num} DA`; break;
        case 'paramCrashPen': document.getElementById('txtCrashPen').textContent = `${num} DA`; break;
    }
}

function bindPresets() {
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const pKey = btn.getAttribute('data-preset');
            const p = PRESETS[pKey];
            if (!p) return;

            setRangeVal('paramAlt', p.alt);
            setRangeVal('paramVz', p.vz);
            setRangeVal('paramRoll', p.roll);
            setRangeVal('paramPitch', p.pitch);
            setRangeVal('paramYaw', p.yaw);
            setRangeVal('paramGrav', p.grav);
            setRangeVal('paramWind', p.wind);
            setRangeVal('paramGustFreq', p.gustFreq);
            setRangeVal('paramDrag', p.drag);
            setRangeVal('paramMass', p.mass);
            setRangeVal('paramThrustMax', p.thrustMax);
            setRangeVal('paramRcsMax', p.rcsMax);
            setRangeVal('paramLegDamp', p.legDamp);
            setRangeVal('paramLearnRate', p.learnRate);
            setRangeVal('paramJackpot', p.jackpot);
            setRangeVal('paramCrashPen', p.crashPen);

            const modEl = document.getElementById('paramModelSelect');
            if (modEl) modEl.value = p.model;

            runSimulationAndUpdateUI();
        });
    });
}

function setRangeVal(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = val;
    updateValueBadge(id, val);
}

// -------------------------------------------------------------
// Real-time Physics & Dopamine Numerical Solver (100 Hz Loop)
// -------------------------------------------------------------
function simulateModel(modelKey, params) {
    const dt = 0.015;
    const maxSteps = 280;

    let z = params.alt;
    let vz = params.vz;
    let roll = params.roll;
    let pitch = params.pitch;
    let yaw = params.yaw;
    let wx = 0.15;
    let wy = -0.12;
    let wz = 0.08;

    let totalDA = 0.2;
    let cumDA = 0.0;
    let totalEnergy = 0.0;

    const tArr = [], rollArr = [], pitchArr = [], yawArr = [];
    const zArr = [], vzArr = [], daArr = [], cumDaArr = [];

    // Controller reflex tuning per fly model
    let kp_r = 45.0, kd_r = 18.0;
    let kp_p = 45.0, kd_p = 18.0;
    let kp_y = 25.0, kd_y = 12.0;

    if (modelKey === 'fb') {
        // FlyBody: Ultra-fast wing aerodynamics
        kp_r = 52.0; kd_r = 16.0;
        kp_p = 54.0; kd_p = 17.0;
        kp_y = 30.0; kd_y = 11.0;
    } else if (modelKey === 'ms') {
        // Musculoskeletal: Compliant muscle damping, zero overshoot
        kp_r = 42.0; kd_r = 23.0;
        kp_p = 42.0; kd_p = 23.0;
        kp_y = 22.0; kd_y = 15.0;
    }

    const weight = params.mass * params.grav;

    for (let step = 0; step < maxSteps; step++) {
        const t = step * dt;

        // Dynamic Wind Perturbation
        let windFx = 0, windFy = 0;
        if (params.wind > 0) {
            windFx = (params.wind * 0.25) * Math.sin(2.5 * params.gustFreq * t);
            windFy = (params.wind * 0.20) * Math.cos(2.0 * params.gustFreq * t);
            if (t >= 0.8 && t <= 1.4) windFx += params.wind * Math.sin((t - 0.8) / 0.6 * Math.PI);
            if (t >= 1.8 && t <= 2.4) windFy -= params.wind * Math.sin((t - 1.8) / 0.6 * Math.PI);
        }

        // Fly Motor Commands (RCS torques)
        const rollRad = (roll * Math.PI) / 180.0;
        const pitchRad = (pitch * Math.PI) / 180.0;
        const yawRad = (yaw * Math.PI) / 180.0;

        let tauRoll = -(kp_r * rollRad + kd_r * wx) + windFy * 0.08;
        let tauPitch = -(kp_p * pitchRad + kd_p * wy) - windFx * 0.08;
        let tauYaw = -(kp_y * yawRad + kd_y * wz);

        tauRoll = Math.max(-params.rcsMax, Math.min(params.rcsMax, tauRoll));
        tauPitch = Math.max(-params.rcsMax, Math.min(params.rcsMax, tauPitch));
        tauYaw = Math.max(-params.rcsMax * 0.5, Math.min(params.rcsMax * 0.5, tauYaw));

        // Attitude angular acceleration (Euler equations approx for symmetric cylinder)
        const Ixx = 0.5 * params.mass * 0.15;
        const Iyy = Ixx;
        const Izz = 0.5 * params.mass * 0.12;

        const dwx = (tauRoll / Ixx) * dt;
        const dwy = (tauPitch / Iyy) * dt;
        const dwz = (tauYaw / Izz) * dt;

        wx += dwx; wy += dwy; wz += dwz;
        roll += (wx * 180.0 / Math.PI) * dt;
        pitch += (wy * 180.0 / Math.PI) * dt;
        yaw += (wz * 180.0 / Math.PI) * dt;

        // Vertical Thrust & Altitude descent
        const targetVz = -Math.min(3.0, Math.max(0.15, z * 0.45));
        let thrust = weight + 85.0 * (targetVz - vz) - (z < 1.0 ? 50.0 : 0);
        thrust = Math.max(0, Math.min(params.thrustMax, thrust));

        const dragF = -0.5 * params.drag * vz * Math.abs(vz);
        const netFz = thrust - weight + dragF;
        const dvz = (netFz / params.mass) * dt;
        vz += dvz;
        z += vz * dt;

        // Dopamine Calculation
        const angleSq = (roll * roll + pitch * pitch + 0.5 * yaw * yaw);
        const rAtt = 2.0 * Math.exp(-angleSq / 50.0) - 1.0;
        const rSpin = -0.4 * Math.hypot(wx, wy, wz);
        let phasic = rAtt + rSpin;

        totalEnergy += (thrust * thrust + tauRoll * tauRoll + tauPitch * tauPitch) * dt;

        // Touchdown or Ground check
        if (z <= 0.6) {
            z = 0.6;
            const isUpright = (Math.abs(roll) < 2.0 && Math.abs(pitch) < 2.0);
            if (isUpright && Math.abs(vz) < 1.2) {
                phasic += params.jackpot;
            } else if (!isUpright) {
                phasic += params.crashPen;
            }
            cumDA += phasic;
            totalDA = 0.2 + phasic * 0.05;

            tArr.push(t.toFixed(2));
            rollArr.push(roll); pitchArr.push(pitch); yawArr.push(yaw);
            zArr.push(z); vzArr.push(vz);
            daArr.push(totalDA); cumDaArr.push(cumDA);
            break;
        }

        cumDA += phasic;
        totalDA = 0.95 * totalDA + 0.05 * (0.2 + Math.max(0, phasic * 0.1));

        if (step % 2 === 0) {
            tArr.push(t.toFixed(2));
            rollArr.push(roll); pitchArr.push(pitch); yawArr.push(yaw);
            zArr.push(z); vzArr.push(vz);
            daArr.push(totalDA); cumDaArr.push(cumDA);
        }
    }

    const finalErr = Math.hypot(roll, pitch, yaw);
    return {
        t: tArr, roll: rollArr, pitch: pitchArr, yaw: yawArr,
        z: zArr, vz: vzArr, da: daArr, cumDa: cumDaArr,
        finalRoll: roll, finalPitch: pitch, finalYaw: yaw,
        finalErr: finalErr, finalVz: vz,
        energy: totalEnergy / 1000.0,
        cumDA: cumDA,
        duration: tArr[tArr.length - 1]
    };
}

// -------------------------------------------------------------
// Run Simulation & Update UI
// -------------------------------------------------------------
function runSimulationAndUpdateUI() {
    const params = {
        alt: parseFloat(document.getElementById('paramAlt').value),
        vz: parseFloat(document.getElementById('paramVz').value),
        roll: parseFloat(document.getElementById('paramRoll').value),
        pitch: parseFloat(document.getElementById('paramPitch').value),
        yaw: parseFloat(document.getElementById('paramYaw').value),
        grav: parseFloat(document.getElementById('paramGrav').value),
        wind: parseFloat(document.getElementById('paramWind').value),
        gustFreq: parseFloat(document.getElementById('paramGustFreq').value),
        drag: parseFloat(document.getElementById('paramDrag').value),
        mass: parseFloat(document.getElementById('paramMass').value),
        thrustMax: parseFloat(document.getElementById('paramThrustMax').value),
        rcsMax: parseFloat(document.getElementById('paramRcsMax').value),
        legDamp: parseFloat(document.getElementById('paramLegDamp').value),
        model: document.getElementById('paramModelSelect').value,
        learnRate: parseFloat(document.getElementById('paramLearnRate').value),
        jackpot: parseFloat(document.getElementById('paramJackpot').value),
        crashPen: parseFloat(document.getElementById('paramCrashPen').value)
    };

    const modelsToRun = (params.model === 'all') ? ['fb', 'ms', 'nmf'] : [params.model];
    const results = {};

    modelsToRun.forEach(m => {
        results[m] = simulateModel(m, params);
    });

    // Primary benchmark model for display metrics (FlyBody or single active)
    const primary = results[params.model === 'all' ? 'fb' : params.model];

    // Update Telemetry Display
    document.getElementById('resAttitudeErr').textContent = `${primary.finalErr.toFixed(2)}°`;
    document.getElementById('resTouchdownVz').textContent = `${primary.finalVz.toFixed(2)} m/s`;
    document.getElementById('resTotalDA').textContent = `${primary.cumDA >= 0 ? '+' : ''}${primary.cumDA.toFixed(1)} DA`;
    document.getElementById('resEnergy').textContent = `${primary.energy.toFixed(1)} kJ`;
    document.getElementById('resDuration').textContent = `${primary.duration} s`;

    // Update Mission Status Banner
    const banner = document.getElementById('statusBanner');
    const bannerText = document.getElementById('missionStatusText');
    if (primary.finalErr < 1.0 && Math.abs(primary.finalVz) < 1.0) {
        banner.style.background = 'rgba(0, 245, 155, 0.15)';
        banner.style.borderColor = 'rgba(0, 245, 155, 0.4)';
        banner.style.color = '#6ee7b7';
        bannerText.textContent = `✅ MÜKEMMEL DİK İNİŞ BAŞARILDI (Açı Hatası: ${primary.finalErr.toFixed(2)}° | Vz: ${primary.finalVz.toFixed(2)} m/s)`;
    } else if (primary.finalErr < 5.0) {
        banner.style.background = 'rgba(0, 210, 255, 0.15)';
        banner.style.borderColor = 'rgba(0, 210, 255, 0.4)';
        banner.style.color = '#7dd3fc';
        bannerText.textContent = `⚡ BAŞARILI İNİŞ (Küçük Sapma: ${primary.finalErr.toFixed(2)}°)`;
    } else {
        banner.style.background = 'rgba(255, 51, 102, 0.15)';
        banner.style.borderColor = 'rgba(255, 51, 102, 0.4)';
        banner.style.color = '#fda4af';
        bannerText.textContent = `🛑 DİKKAT: YÜKSEK AÇI SAPMASI / KAZA RİSKİ (${primary.finalErr.toFixed(2)}°)`;
    }

    // Update 3D Satellite Model orientation
    const sat3D = document.getElementById('liveSat3D');
    if (sat3D) {
        sat3D.style.transform = `rotateZ(${primary.finalRoll}deg) rotateX(${primary.finalPitch}deg) rotateY(${primary.finalYaw}deg)`;
    }
    const anglesReadout = document.getElementById('liveAnglesReadout');
    if (anglesReadout) {
        anglesReadout.textContent = `Roll: ${primary.finalRoll.toFixed(1)}° | Pitch: ${primary.finalPitch.toFixed(1)}° | Yaw: ${primary.finalYaw.toFixed(1)}°`;
    }

    // -------------------------------------------------------------
    // Update Chart 1: 3-Axis Attitude
    // -------------------------------------------------------------
    chartAttitude.data.labels = primary.t;
    if (params.model === 'all') {
        chartAttitude.data.datasets = [
            { label: 'FlyBody (Kanatlar) Roll', data: results.fb.roll, borderColor: '#00f59b', borderWidth: 2.2, pointRadius: 0 },
            { label: 'Musculoskeletal (Kaslar) Roll', data: results.ms.roll, borderColor: '#ff3366', borderWidth: 2.0, pointRadius: 0 },
            { label: 'NeuroMechFly (Bacaklar) Roll', data: results.nmf.roll, borderColor: '#00d2ff', borderWidth: 1.8, pointRadius: 0 },
            { label: 'Hedef 0° Referansı', data: primary.t.map(() => 0), borderColor: '#ffffff', borderDash: [5, 5], borderWidth: 1, pointRadius: 0 }
        ];
    } else {
        chartAttitude.data.datasets = [
            { label: 'Roll Açısı (X)', data: primary.roll, borderColor: '#ff3366', borderWidth: 2.2, pointRadius: 0 },
            { label: 'Pitch Açısı (Y)', data: primary.pitch, borderColor: '#00f59b', borderWidth: 2.2, pointRadius: 0 },
            { label: 'Yaw Açısı (Z)', data: primary.yaw, borderColor: '#00d2ff', borderWidth: 2.0, pointRadius: 0 },
            { label: 'Hedef 0° Referansı', data: primary.t.map(() => 0), borderColor: '#ffffff', borderDash: [5, 5], borderWidth: 1, pointRadius: 0 }
        ];
    }
    chartAttitude.update('none');

    // -------------------------------------------------------------
    // Update Chart 2: Dopamine Dynamics
    // -------------------------------------------------------------
    chartDopamine.data.labels = primary.t;
    if (params.model === 'all') {
        chartDopamine.data.datasets = [
            { label: 'FlyBody Dopamin', data: results.fb.cumDa, borderColor: '#00f59b', borderWidth: 2.2, pointRadius: 0 },
            { label: 'Musculoskeletal Dopamin', data: results.ms.cumDa, borderColor: '#ff3366', borderWidth: 2.0, pointRadius: 0 },
            { label: 'NeuroMechFly Dopamin', data: results.nmf.cumDa, borderColor: '#00d2ff', borderWidth: 1.8, pointRadius: 0 }
        ];
    } else {
        chartDopamine.data.datasets = [
            { label: 'Kümülatif Dopamin', data: primary.cumDa, borderColor: '#00f59b', borderWidth: 2.2, pointRadius: 0 },
            { label: 'Anlık Tonik Dopamin', data: primary.da, borderColor: '#9d4edd', borderWidth: 1.8, pointRadius: 0 }
        ];
    }
    chartDopamine.update('none');

    // -------------------------------------------------------------
    // Update Chart 3: Trajectory (Altitude & Vz)
    // -------------------------------------------------------------
    chartTrajectory.data.labels = primary.t;
    chartTrajectory.data.datasets = [
        { label: 'İrtifa Z (m)', data: primary.z, borderColor: '#00d2ff', borderWidth: 2.5, yAxisID: 'y', pointRadius: 0 },
        { label: 'Dikey Hız Vz (m/s)', data: primary.vz, borderColor: '#00f59b', borderWidth: 2.0, yAxisID: 'y1', pointRadius: 0 }
    ];
    chartTrajectory.update('none');
}

// -------------------------------------------------------------
// Image Lightbox Modal Viewer
// -------------------------------------------------------------
function openModal(src, caption) {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImg");
    const modalCaption = document.getElementById("modalCaption");

    modal.style.display = "flex";
    modalImg.src = src;
    modalCaption.textContent = caption;
}

function closeModal() {
    const modal = document.getElementById("imageModal");
    modal.style.display = "none";
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeModal();
    }
});

// -------------------------------------------------------------
// Smooth Scrolling
// -------------------------------------------------------------
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

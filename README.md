# 🛰️ Bio-Satellite: Biyomimetik Uydu Dik İniş Projesi
> **Meyve Sineği (*Drosophila melanogaster*) ve Dopaminerjik Pekiştirmeli Öğrenme ile 3 Eksenli Otonom Uydu Dik İniş Kontrolü**

![MuJoCo 3.9](https://img.shields.io/badge/MuJoCo-3.9-blue.svg)
![FlyGym 2.1](https://img.shields.io/badge/FlyGym-2.1-green.svg)
![Dopamine RL](https://img.shields.io/badge/Nörobiyoloji-Dopamin_RL-purple.svg)
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-orange.svg)

---

## 📌 1. Proje Özeti ve Vizyon

Ay, Mars veya asteroit görevlerinde dikey iniş (powered descent) yapan araçların en kritik zorluğu, serbest düşüş esnasındaki türbülans ve açısal sapmalara karşı **3 rotasyon eksenini (Roll, Pitch, Yaw) iniş anında tam $0.0^\circ$'ye kilitlemesi** ve dikey iniş hızını güvenli bir temas sınırına sönümlemesidir.

Bu projede geleneksel analitik kontrolcüler yerine; doğanın en çevik akrobatı olan **meyve sineğinin (*Drosophila melanogaster*) biyomekanik ve nöromekanik kontrol sistemleri** kullanılmıştır. Sineğin beynindeki dopaminerjik nöronlar (DAN'lar) ödül tahmini hatası (Reward Prediction Error - RPE) üreterek, açıların $0^\circ$'ye yaklaşmasını **dopamin ödülüyle** pekiştirir.

Çalışmada **3 farklı sinek modeli** aynı fiziksel uydu üzerinde karşılaştırılmıştır:
1. **`NeuroMechFly` (EPFL):** Kinematik 6-bacak eklemleri (Coxa, Femur, Tibia)
2. **`FlyBody` (DeepMind & Turaga):** Aerodinamik kanat kinematiği ve karın (abdomen) bükülmesi
3. **`MusculoskeletalFly` (FlyMimic):** 15 adet Hill-tipi biyolojik kas kasılması

---

## 🚀 2. Uydunun Fiziksel ve Teknik Özellikleri

| Parametre | Değer | Açıklama |
| :--- | :---: | :--- |
| **Toplam Kütle** | **$20.0\text{ kg}$** | Silindirik gövde ($15\text{ kg}$), kubbe ($1\text{ kg}$), nozül ($1\text{ kg}$), 4 bacak ($3\text{ kg}$) |
| **Ağırlık ($G$)** | **$196.2\text{ N}$** | Dünya yerçekimi ($g = 9.81\text{ m/s}^2$) |
| **Gövde Boyutları** | Yarıçap: $0.35\text{ m}$, Yükseklik: $\approx 1.8\text{ m}$ | Aerodinamik silindirik gövde |
| **Ana İtici Motor ($F_z$)** | **$0 - 500\text{ N}$** | TWR $\approx 2.55$ (Düşüşü saniyeler içinde durdurabilecek güç) |
| **RCS Tork Motorları** | **$\tau_x, \tau_y: \pm 60\text{ Nm}, \quad \tau_z: \pm 30\text{ Nm}$** | Roll, Pitch ve Yaw düzeltme iticileri |
| **İniş Takımları** | 4 Bacak ($90^\circ$ simetrik) | Şok emici bacaklar ve yüksek sürtünmeli pabuçlar ($\mu = 1.0$) |
| **Serbestlik Derecesi** | 6-DoF Freejoint | 3D uzayda serbest düşüş fiziği (MuJoCo 3.9, RK4 çözücü, 500 Hz) |

---

## 🧬 3. Dopamin Nörodinamiği ve Öğrenme Formülü

Sinek beyninin Mantar Gövdesi (Mushroom Body) ve Merkezi Kompleksindeki nöral ödül mekanizması şu denklemle modellenmiştir:

$$\delta_{DA} = R_{\text{açı}} + R_{\text{dönme}} + R_{\text{alçalma}} + R_{\text{diklik}} + R_{\text{terminal}}$$

* **Açı Sıfırlama Ödülü:** $R_{\text{açı}} = 2.0 \cdot \exp\left(-\frac{\phi^2 + \theta^2 + 0.5\psi^2}{50}\right) - 1.0$
* **Dönme Sönümleme:** $R_{\text{dönme}} = -0.5 \cdot \|\boldsymbol{\omega}\|$
* **Büyük İkramiye (Jackpot):** $R_{\text{terminal}} = +50.0 \sim +90.0\text{ DA}$ (Ayaklar yere $0^\circ$ dik ve $V_z < 0.5\text{ m/s}$ ile bastığında)
* **Kaza Cezası:** $R_{\text{terminal}} = -50.0\text{ DA}$ (Gövde yere çarptığında veya $>45^\circ$ devrildiğinde)

### Sinaptik Ağırlık Güncellemesi:
$$\Delta \mathbf{W} = \eta \cdot \delta_{DA} \cdot \mathbf{e}$$
*(Burada $\eta$ öğrenme katsayısı, $\mathbf{e}$ ise uygunluk izidir / eligibility trace).*

---

## 📊 4. Bilimsel Analiz Grafikleri (8 Büyük Şekil)

Proje kapsamında üretilen 8 bilimsel analiz şekli `satellite_lander/results/` klasöründe yer almaktadır:

1. **`fig1_3axis_attitude_comparison.png`:** Roll, Pitch ve Yaw açılarının $0^\circ$ çizgisine yakınsama zaman serisi.
2. **`fig2_dopamine_neurodynamics.png`:** Fazik RPE patlamaları, tonik bazal dopamin ve kümülatif ödül eğrileri.
3. **`fig3_phase_space_portraits.png`:** $(\text{Açı} \text{ vs } \text{Açısal Hız})$ durum uzayı faz portreleri ve $(0, 0)$ kararlı çekicisi.
4. **`fig4_fly_biomechanics_telemetry.png`:** 6 bacak açısı, kanat çırpma genlikleri ve 15 kasın aktivasyon ısı haritası.
5. **`fig5_comprehensive_benchmark.png`:** İniş hatası, hız, dopamin ve kontrol enerjisi skor kartları.
6. **`fig6_wind_disturbance_response.png`:** $18\text{ N}$ rüzgar darbeleri ve türbülans altında 3 eksen doğrultma tepkisi.
7. **`fig7_3d_descent_trajectories_wind.png`:** 3D uzaysal uçuş rotası ve iniş pisti üzerindeki yanal sürüklenme dispersiyonu.
8. **`fig8_dopamine_stress_recovery.png`:** Şiddetli rüzgar darbesi anında sineğin yaşadığı dopaminerjik şok ve refleks toparlanma eğrisi.

---

## 🏆 5. Modellerin Karşılaştırmalı Performans Tablosu

| Metrik | NeuroMechFly (Bacaklar) | FlyBody (Kanatlar & Karın) | MusculoskeletalFly (15 Kas) |
| :--- | :---: | :---: | :---: |
| **Sakin Havada Açı Hatası** | $0.18^\circ$ | **$0.02^\circ$ (En Hassas)** | $0.11^\circ$ |
| **Rüzgarda (18N) Açı Hatası** | $0.29^\circ$ | **$0.12^\circ$ (En Dayanıklı)** | $0.20^\circ$ |
| **İniş Dikey Hızı ($V_z$)** | $-1.12\text{ m/s}$ | $-1.12\text{ m/s}$ | $-1.12\text{ m/s}$ |
| **Kazanılan Kümülatif Dopamin** | $504.2\text{ DA}$ | **$509.4\text{ DA}$** | $491.4\text{ DA}$ |
| **Kontrol Enerjisi Harcaması** | $199.1\text{ kJ}$ | **$198.8\text{ kJ}$** | $199.3\text{ kJ}$ |
| **Biyolojik Mekanizma** | Çapraz bacak koordinasyonu | Hızlı aerodinamik kanat torkları | Salınımsız Hill kas sönümlemesi |

---

## 🎬 6. Simülasyon Videoları ve Kayıtlar

* 🎥 **Tekil İniş Videosu (HUD Telemetrili MP4):** `satellite_lander/videos/satellite_landing_controlled.mp4`
* 🎥 **3 Sinek Modelinin Yan Yana Karşılaştırma Videosu (Split-Screen):** `satellite_lander/videos/comparison_splitscreen_3flies.mp4`
* 🎞️ **Animasyonlu GIF Önizlemeleri:** `satellite_lander/videos/*.gif`

---

## 💻 7. Projeyi Çalıştırma Kılavuzu

Tüm kütüphaneler izole `uv` sanal ortamı üzerinden doğrudan çalıştırılabilir:

### 1. İnteraktif 3D MuJoCo Penceresini Açma (Canlı Fare Kontrolleri):
```powershell
uv run python -m satellite_lander.interactive_viewer
```

### 2. 3 Sinek Modelinin Karşılaştırma Simülasyonunu Çalıştırma:
```powershell
uv run python -m satellite_lander.train_and_compare_flies
```

### 3. Rüzgar Darbeleri ve Türbülans Testini Çalıştırma:
```powershell
uv run python -m satellite_lander.simulate_wind_disturbances
```

### 4. 3'lü Yan Yana Split-Screen Videosunu Yeniden Üretme:
```powershell
uv run python -m satellite_lander.render_splitscreen_video
```

### 5. Web Dashboard'unu Başlatma:
```powershell
uv run python -m satellite_lander.serve_website
```
Tarayıcınızda açmak için: **`http://localhost:8080`**

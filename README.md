

# 🧠 EEG Motor Imagery Classification using EEGNet (PyTorch)

This repository presents a complete pipeline for **Motor Imagery EEG (MI-EEG) signal classification** using a **PyTorch implementation of EEGNet**. It covers both **publicly available PhysioNet data** and **locally recorded primary EEG data** collected using the **OpenBCI Ultracortex Mark IV** headset. The project demonstrates reproducible training, evaluation, and analysis for offline BCI research, with scope for real-time extension.

---

## 📁 Repository Structure

* **`Data/`**
  Contains all stages of EEG data used in this project.

  * `Originally_Collected_MI_EEG_data/` – Raw EEG recordings from **OpenBCI Ultracortex Mark IV** headset
  * `DC_offset_removed_MI_EEG_data/` – DC-corrected EEG signals after offset removal
  * `Timestamps_Modified_MI_EEG_data/` – Time-synchronized and resampled EEG data (final format used for training)
  * `marker.ods` – Event marker annotations aligned with motor imagery task cues

* **`Scripts/`**
  Includes all Python scripts for data acquisition, preprocessing, and model execution.

  * `Record_EEG_with_Markers.py` – Records EEG data with real-time markers using **BrainFlow**
  * `model_training_testing.py` – Trains and evaluates **EEGNet** on both PhysioNet and primary EEG datasets

* **`Docs/`**
  Contains all documentation and project materials.

  * Thesis report, presentation slides, and **OHBM** poster for publication reference

* **`Media/`**
  Stores visual and multimedia resources.

  * `Time_corrected_elbow_knee_mi_cue.mp4` – Sample motor imagery cue video synchronized with EEG timestamps

* **`README.md`** – Project overview and usage guide

* **`requirements.txt`** – Python dependencies for reproducing results

* **`LICENSE`** – Open-source license information
---

## ⚙️ Key Details

* **Model**: EEGNet (PyTorch)
* **Sampling Rate**: 125 Hz
* **Channels**: 16 (OpenBCI 10-20 system layout)
* **PhysioNet Accuracy**: 73.31 %
* **Primary Data Accuracy**: 89.59 %
* **Metrics Used**: Accuracy, F1-score, Confusion Matrix

---

## 🧩 How It Works

1. **Data Acquisition**

   * Primary EEG recorded using **OpenBCI** with BrainFlow at 125 Hz.
   * Continuous recording from 24 participants during four MI tasks (left hand, right hand, leg, tongue).

2. **Preprocessing**

   * Channel selection, filtering, common average referencing (CAR), epoching.
   * PhysioNet and primary data aligned to uniform structure.

3. **Model Training**

   * EEGNet trained first on PhysioNet for baseline performance.
   * Fine-tuned and retrained on primary EEG data for subject-specific classification.

4. **Evaluation**

   * Offline evaluation with performance visualization (accuracy, F1, confusion matrix).

---

## 🚀 Reproduction & Extension

To reproduce results:

```bash
git clone https://github.com/<sandzzr>/<Motor-Imagery-EEG-Processing>.git
cd <Motor-Imagery-EEG-Processing>
pip install -r requirements.txt
```

Then open the training notebooks under `notebooks/` to replicate experiments.

To extend this project into **real-time BCI control**:

* Integrate the trained EEGNet model with BrainFlow’s live streaming API.
* Implement a **sliding window** approach for continuous classification.
* Map predicted classes to control commands for assistive devices (e.g., wheelchair, cursor).

---

## 📌 Features

* Unified pipeline for both public and primary datasets
* PyTorch-based EEGNet implementation
* Reproducible offline training and analysis
* Clear modular structure for future real-time BCI integration

---

## 🎓 Ideal For

* Students and researchers in **Brain-Computer Interface (BCI)** and **Neuroengineering**
* Developers exploring **EEG-based motor imagery classification**
* Teams building **assistive or neurofeedback systems**

---

## 🤝 Contributions

Open for contributions!
You can:

* Fork the repository
* Report issues or suggest improvements
* Submit pull requests with enhancements

---

## 📜 License

This project is open-source under the **MIT License**.

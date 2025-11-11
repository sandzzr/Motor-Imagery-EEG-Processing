🧠 Deep Learning-Based Classification of Motor Imagery EEG Signals for Brain–Computer Interface (BCI) Applications
Overview

This repository contains the core files and data used in the study on deep learning-based classification of motor imagery (MI) EEG signals. The goal is to build a reliable and extendable framework for offline EEG-MI decoding, which can later be adapted for real-time BCI control such as assistive device navigation.

Repository Structure
MI_EEG_Classification_BCI/
│
├── Data/
│   ├── Originally_Collected_MI_EEG_data/     → raw recordings
│   ├── DC_offset_removed_MI_EEG_data/        → DC-corrected signals
│   ├── Timestamps_Modified_MI_EEG_data/      → synchronized and resampled data
│   └── marker.ods                            → event markers for MI cues
│
├── Scripts/
│   ├── Record_EEG_with_Markers.py            → data acquisition using BrainFlow
│   ├── model_training_testing.py             → EEGNet-based model training & testing
│
├── Docs/                                     → consent form, thesis, presentation, poster
│
├── Media/
│   └── Time_corrected_elbow_knee_mi_cue.mp4  → visual cue reference
│
├── README.md
├── requirements.txt
└── LICENSE

Reproducibility

Set up environment
Install Python ≥3.10 and run:

pip install -r requirements.txt


Prepare data

Use files under Data/ for training and evaluation.

Each folder represents a preprocessing stage of the same dataset.

You may substitute your own EEG recordings if they follow the same channel order and sampling rate (16 channels, 125 Hz).

Train and test the model

Run model_training_testing.py to reproduce offline results using EEGNet.

Modify training parameters inside the script to tune the model or apply transfer learning to new datasets.

Extend to real-time BCI

Use Record_EEG_with_Markers.py to stream live EEG via BrainFlow.

Implement a sliding-window inference routine within this script to classify ongoing EEG segments in real time.

The trained model weights can be loaded for on-device or PC-based control of assistive hardware (e.g., wheelchair, robotic arm).

Purpose

This work provides a foundation for reproducible EEG-MI classification and an adaptable framework for future real-time BCI implementation.

# 🧠 Brain Tumor Detection Using Convolutional Neural Networks (CNN)

This project builds and trains a Convolutional Neural Network to classify brain MRI scans as either containing a tumor or not. It utilizes medical imaging data and applies deep learning to assist with binary medical diagnosis.

---

## 🎯 Objective

Brain tumors are life-threatening conditions that require timely diagnosis. This project aims to:
- Detect the presence of brain tumors in MRI scans using deep learning.
- Demonstrate the application of computer vision in healthcare.
- Provide a simple and reproducible CNN-based pipeline for binary image classification.

---

## 🧠 Model Summary

- **Architecture:** Sequential CNN with 3 convolutional layers and fully connected classification head
- **Activation:** ReLU + Sigmoid
- **Regularization:** Dropout
- **Loss Function:** Binary Cross-Entropy
- **Optimizer:** Stochastic Gradient Descent (SGD)
- **Evaluation Metric:** Accuracy
- **Tools Used:** TensorFlow/Keras, NumPy, Matplotlib, Google Colab

---

## 🧰 Tech Stack

- Python 3
- TensorFlow/Keras
- NumPy, Scikit-learn
- Google Colab
- Matplotlib
- PIL for image preprocessing

---

## 🗂️ Dataset

- **Source:** Stored on Google Drive (`brain_t/yes` and `brain_t/no` directories)
- **Classes:**
  - `yes`: MRI scan shows presence of a tumor (label = 1)
  - `no`: MRI scan is normal (label = 0)
- **Image Preprocessing:**
  - Resized to 150x150 pixels
  - Normalized pixel values (scaled to [0,1])
  - Dataset split: 80% training, 10% validation, 10% testing

---

## 🚀 How to Run

### 1. Set Up Environment

```bash
pip install torch numpy matplotlib tensorflow

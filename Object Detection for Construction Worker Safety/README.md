# 🦺 PPE Detection Using YOLOv8 (Ultralytics)

This project applies YOLOv8 object detection to identify the use of **personal protective equipment (PPE)**—such as helmets, vests, and masks—from images and videos. The workflow includes model training, evaluation, visualization, and deployment steps, all executed within Google Colab.

---

## 🎯 Objective

To train a lightweight, real-time object detection model capable of accurately detecting various forms of PPE for use in safety compliance and workplace monitoring.

---

## 📁 Dataset

- Located in: `/content/drive/MyDrive/css-data`
- Format: YOLO-compliant dataset with `train`, `val`, and `test` image folders and corresponding labels
- Configuration file: `ppe.yaml` (defines class names and paths)

---

## 🧠 Model & Framework

- **Model:** `YOLOv8n.pt` (Nano variant – optimized for speed and low memory usage)
- **Framework:** [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- **Environment:** Google Colab with GPU

---

## 🚀 How to Use

### 1. Install Dependencies

```bash
pip install ultralytics

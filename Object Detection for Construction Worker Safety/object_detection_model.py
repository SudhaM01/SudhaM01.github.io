
# !pip install  ultralytics
#
# !yolo

from ultralytics import YOLO
import os
from google.colab import drive
drive.mount('/content/drive')
file_path = "/content/drive/MyDrive"

# === STEP 1: SET PATHS ===
# Change this to your actual full dataset path
dataset_dir = "/content/drive/MyDrive/css-data"
data_config = os.path.join(dataset_dir, "ppe.yaml")

# === STEP 2: LOAD MODEL ===
# Choose a base model (yolov8n.pt = Nano, yolov8s.pt = Small, yolov8m.pt = Medium)
model = YOLO("yolov8n.pt")  # lightweight and fast to train

# === STEP 3: TRAIN MODEL ===
results = model.train(
    data="/content/drive/MyDrive/css-data/ppe.yaml",       # Path to your ppe.yaml file
    epochs=30,              # You can increase to improve results
    imgsz=640,              # Image resolution
    batch=16,               # Adjust depending on GPU/CPU power
    name="ppe_yolov8n",     # Output directory under runs/detect/
    verbose=True
)

# === STEP 4 (Optional): VALIDATE AFTER TRAINING ===
metrics = model.val()

# === STEP 5 (Optional): PRINT RESULTS ===
print("Training complete.")
print("Validation mAP:", metrics.box.map)  # Mean Average Precision
print("Results saved in:", results.save_dir)

import zipfile
import os

# Recreate zip if it doesn’t exist
zip_path = "ppe_model_report.zip"
report_path = "report"

if os.path.exists(report_path):
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(report_path):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, report_path)
                zipf.write(filepath, arcname)
    print("✅ Zipped: ppe_model_report.zip")
else:
    print("⚠️ 'report' folder not found. Run earlier steps to create report content.")

# # Check before copying
# import os
# import shutil

# model_path = "runs/detect/ppe_yolov8n2"

# if os.path.exists(model_path):
#     shutil.copy(model_path, "/content/drive/MyDrive/ppe_best_model.pt")
#     print("✅ Model saved to Drive")
# else:
#     print("❌ Trained model not found! Make sure training finished successfully.")
import os
import shutil

model_path = "runs/detect/ppe_yolov8n/weights/best.pt"
destination_path = "/content/drive/MyDrive/ppe_best_model.pt"

if os.path.exists(model_path):
    shutil.copy(model_path, destination_path)
    print("✅ Model saved to Drive")
else:
    print("❌ Trained model file not found! Make sure training finished successfully.")

from ultralytics import YOLO

# Load your best trained model
model = YOLO("runs/detect/ppe_yolov8n/weights/best.pt")

# Evaluate on test set (make sure test: is set in your ppe.yaml)
metrics = model.val(split='test')

print("Results:")
print("mAP50:", metrics.box.map50)
print("mAP50-95:", metrics.box.map)

!zip -r runs.zip runs

import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Path where YOLO saved the predictions
pred_path = "runs/detect/predict/"

# List prediction images
pred_images = [f for f in os.listdir(pred_path) if f.endswith((".jpg", ".png"))]

# Display a few results
for i, img_name in enumerate(pred_images[:4]):  # Show first 4 images
    img_path = os.path.join(pred_path, img_name)
    img = mpimg.imread(img_path)

    plt.figure(figsize=(8, 8))
    plt.imshow(img)
    plt.axis("off")
    plt.title(f"Prediction: {img_name}")
    plt.show()

import shutil

shutil.copy("runs.zip", "/content/drive/MyDrive/runs_backup.zip")
print("✅ Zipped folder saved to Drive.")

from ultralytics import YOLO

# Load the trained model
model = YOLO("/content/drive/MyDrive/ppe_best_model.pt")

# Folder containing test images
test_images_dir = "/content/drive/MyDrive/css-data/test/images/"

# Run prediction
model.predict(
    source=test_images_dir,
    save=True,       # Save the results with bounding boxes
    conf=0.4,        # Confidence threshold
    imgsz=640
)

# Inference on a video (update path to your video)
model.predict(
    source="/content/drive/MyDrive/css-data/test_video.mp4",
    save=True,
    conf=0.4
)
shutil.copy("runs/detect/predict/test_video.mp4", "report/")

from ultralytics import YOLO

model = YOLO("/content/drive/MyDrive/ppe_best_model.pt")
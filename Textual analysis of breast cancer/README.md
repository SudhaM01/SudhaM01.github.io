# 🩺 Breast Cancer Detection Using Random Forest & PCA in R

This project involves a comprehensive analysis of breast cancer data using R. It includes exploratory data analysis (EDA), feature engineering, dimensionality reduction, and classification modeling using a Random Forest algorithm. The goal is to accurately classify malignant and benign tumors based on various cell nuclei measurements.

---

## 🎯 Objective

To build a predictive model that can accurately distinguish between malignant (M) and benign (B) breast cancer cases using features extracted from digitized images of fine needle aspirates (FNA) of breast masses.

---

## 📊 Dataset Overview

- **Source:** `Cancer_Data.csv`
- **Features:** 30 numeric features (e.g., radius_mean, texture_mean, perimeter_mean)
- **Target:** `diagnosis` (Malignant `M` or Benign `B`)
- **Rows:** 569 observations

---

## 🧪 Analysis & Workflow

### 1. 🔍 Exploratory Data Analysis (EDA)
- Visual summaries using `summary()`, `ggplot2`, and `GGally::ggpairs`
- Feature relationships and clustering based on tumor types
- Missing data visualizations using `naniar`

### 2. 🧹 Data Preprocessing
- Conversion of `diagnosis` to a factor
- Removal of non-informative ID column
- Calculation of feature correlations

### 3. 🧠 Model Training
- Data split: 70% training / 30% testing using `createDataPartition`
- Random Forest classifier trained with `caret::train` using 5-fold cross-validation
- Evaluation via confusion matrix and classification metrics (Accuracy, Sensitivity, Specificity)

### 4. 🧬 Dimensionality Reduction
- Principal Component Analysis (PCA) to understand variance and visual class separation
- Visualization of principal components colored by diagnosis

---

## 📦 Libraries Used

```r
caret
tidyverse
ggplot2
GGally
naniar
ranger

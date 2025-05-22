# 🍽️ Recipe Generation Using Seq2Seq & Attention Models (PyTorch)

This project implements multiple deep learning models for **natural language generation** of cooking recipes from a list of ingredients. It follows a progressive architecture design:  
- ✅ Basic Encoder-Decoder (Seq2Seq)  
- ✅ Seq2Seq with Attention  
- ✅ Deep multi-layer Encoder-Decoder  
- ✅ GloVe-embedded Attention-based Seq2Seq  

---

## 🎯 Objective

To build models that generate complete, natural-language recipes from unordered lists of ingredients. The models learn to understand ingredients and generate realistic recipe instructions.

---

## 📚 Datasets

The project uses three CSV files:
- `train.csv`: training set with `Ingredients` and `Recipe`
- `test.csv`: unseen evaluation set
- `dev.csv`: validation set during training

Each file contains:
- **Ingredients**: comma-separated ingredient list
- **Recipe**: corresponding cooking instructions

---

## 🛠️ Model Architectures

### 🔹 Baseline 1: Basic Seq2Seq
- Encoder: LSTM with embedding
- Decoder: LSTM with embedding
- Teacher forcing used

### 🔹 Baseline 2: Seq2Seq with Attention
- Encoder: LSTM
- Decoder: LSTM with attention weights over encoder outputs

### 🔹 Extension 1: Deep Stacked LSTMs
- 4-layer LSTM encoders and decoders
- Increased capacity and depth for better learning

### 🔹 Extension 2: GloVe Pretraining
- Trains GloVe embeddings on the same ingredient+recipe corpus
- Integrates pretrained embeddings into Seq2Seq architecture

---

## ⚙️ Workflow Summary

1. **Text Preprocessing**
   - Unicode normalization, lowercasing, punctuation cleanup
   - Word-to-index mappings (`Lang` class)
2. **Dataset Preparation**
   - Convert pairs to tensors
   - Filter long examples
3. **Model Training**
   - Trains over 50,000 steps with validation monitoring
   - Supports early stopping and checkpointing
4. **Evaluation**
   - Evaluate randomly sampled examples
   - Save comparison CSVs of predictions vs ground truth

---

## 📈 Evaluation & Visualization

- Training & validation loss are logged and plotted
- Attention weights visualized for interpretability
- Final outputs saved as:
  - `gen_vs_test_seq2seq.csv`
  - `gen_vs_test_seq2seq_withattn.csv`
  - `gen_vs_test_seq2seq_layers.csv`
  - `gen_vs_test_seq2seq_glove.csv`

---
## 🔧 Setup & Requirements

```bash
pip install torch numpy matplotlib pandas


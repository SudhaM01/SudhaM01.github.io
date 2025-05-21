# 🏥 Clinical SOAP Note Generator using LLMs (TinyLlama + QLoRA)

This project fine-tunes a lightweight Large Language Model (TinyLlama) using QLoRA (Quantized Low-Rank Adaptation) to convert doctor-patient conversations into structured clinical SOAP notes. The model is trained on real-world ASR transcripts from healthcare settings and demonstrates the ability to assist with clinical documentation.

---

## 📌 Project Objective

Healthcare professionals spend a significant amount of time manually transcribing clinical notes from verbal interactions. This project aims to:
- Convert conversational transcripts into structured SOAP (Subjective, Objective, Assessment, Plan) notes.
- Reduce documentation time and improve workflow efficiency using LLMs.

---

## 🧠 Model & Methodology

- **Base Model:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- **Fine-Tuning:** PEFT (LoRA) with QLoRA (4-bit quantization) for memory efficiency.
- **Data:** Custom dataset of clinical conversations stored in JSON format (`src` for conversations, `tgt` for SOAP notes).
- **Tokenization:** Instruction-style prompt format with shared input-label tokenization.
- **Training Framework:** HuggingFace `transformers` + `Trainer` API.

---

## 🔧 Key Technologies

- Python, PyTorch, Hugging Face Transformers, Datasets
- PEFT (Parameter-Efficient Fine-Tuning)
- QLoRA + BitsandBytes 4-bit quantization
- Google Colab for training
- ROUGE evaluation for summarization quality

---




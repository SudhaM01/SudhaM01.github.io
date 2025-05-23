from google.colab import drive
drive.mount('/content/drive')
file_path = "/content/drive/MyDrive"

# !pip install bitsandbytes accelerate transformers
#
# !pip install -U transformers

import os
import json
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
from transformers import BitsAndBytesConfig

# ========= CONFIGURATION =========
# Base model and tokenizer (LLaMA3-8B)
# MODEL_NAME = "meta-llama/Meta-Llama-Guard-2-8B"
# TOKENIZER_NAME = "meta-llama/Meta-Llama-Guard-2-8B"
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
TOKENIZER_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

import os
import json
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
from transformers import BitsAndBytesConfig
# Path to folder with JSON data files
DATA_DIR = "/content/drive/MyDrive/clinical_notes/src_experiment_data_json"

# Max token length for prompts and outputs
MAX_LENGTH = 4096

#Data preprocessing
# LOAD AND COMBINE DATA
def load_json_data(folder_path):
    """
    Load all .json files from the folder and combine them into a single Dataset object.
    Each record should contain 'src' (ASR text) and 'tgt' (target SOAP note).
    """
    data = {"src": [], "tgt": []}
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                records = json.load(f)["data"]
                for record in records:
                    data["src"].append(record["src"])
                    data["tgt"].append(record["tgt"])
    return Dataset.from_pandas(pd.DataFrame(data))

# Load dataset and split into train/test
dataset = load_json_data(DATA_DIR)
dataset = dataset.train_test_split(test_size=0.1)

#  STEP 2: LOAD TOKENIZER
# Use the LLaMA tokenizer and pad with EOS token
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token


def tokenize_function(example):
    prompt = f"[INSTRUCTION] Convert the following medical conversation into a structured SOAP note:\n\n{example['src']}\n\n[RESPONSE]"
    target = example["tgt"]

    combined = prompt + " " + target

    tokenized = tokenizer(
        combined,
        truncation=True,
        max_length=2048,
        padding="longest"
    )

    return {
        "input_ids": tokenized["input_ids"],
        "attention_mask": tokenized["attention_mask"],
        "labels": tokenized["input_ids"].copy(),  # Don't mask prompt
    }

# STEP 4: LOAD MODEL WITH QLoRA + 4bit
# Load LLaMA3 in 4-bit mode for memory efficiency
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

# Load base model with quantized config
base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto"
)


# Prepare model for parameter-efficient tuning
base_model = prepare_model_for_kbit_training(base_model)

# ========= STEP 5: APPLY PEFT USING LoRA =========
# Fine-tune only attention/feedforward layers for efficiency
peft_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Wrap base model with PEFT (LoRA layers added)
model = get_peft_model(base_model, peft_config)

#STEP 6: TRAINING SETUP
training_args = TrainingArguments(
    output_dir="./checkpoints",
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    # Changed 'evaluation_strategy' to 'eval_strategy'
    eval_strategy="epoch",
    save_strategy="epoch",
    num_train_epochs=8,
    logging_dir="./logs",
    learning_rate=2e-4,
    fp16=True,
    gradient_accumulation_steps=4,
    save_total_limit=2,
    logging_steps=10,
    report_to="none"
)

# Setup Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["test"],
    tokenizer=tokenizer
)

# ========= STEP 7: START TRAINING =========
trainer.train()

import transformers
print(transformers.__version__)

# validate_model.py



# Load the fine-tuned model and tokenizer
model.eval()
# pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Evaluate a few samples from validation set
def validate_on_sample(n=3):
    model.eval()
    for i in range(n):
        src = dataset["test"][i]["src"]
        tgt = dataset["test"][i]["tgt"]

        # Instruction-style prompt
        prompt = f"[INSTRUCTION] Convert the following medical conversation into a structured SOAP note:\n\n{src}\n\n[RESPONSE]"

        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(model.device)

        # Generate output
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False,       # Greedy decoding
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode output
        decoded = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        # Extract part after [RESPONSE]
        if "[RESPONSE]" in decoded:
            soap_note = decoded.split("[RESPONSE]")[-1].strip()
        else:
            soap_note = decoded.strip()

        # Show results
        print(f"\n🔹 Prompt:\n{src[:500]}...\n")
        print(f"✅ Target SOAP Note:\n{tgt[:500]}...\n")
        print(f"🧠 Generated SOAP Note:\n{soap_note[:5000]}...\n")

        print("=" * 80)



validate_on_sample(n=1)

base_model.eval()
prompt = "[INSTRUCTION] Convert the following medical conversation into a structured SOAP note:\n\n[doctor] hello...\n\n[RESPONSE]"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = base_model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=True,
        temperature=0.7,
        top_p=0.95,
        pad_token_id=tokenizer.eos_token_id
    )

decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n--- Raw Decoded Output ---\n")
print(decoded)
print("Generated token IDs:", outputs[0].tolist())

def generate_soap_note(conversation_text):
    """
    Given raw doctor-patient conversation, generate structured SOAP note.
    """
    prompt = f"[INSTRUCTION] Convert the following medical conversation into a structured SOAP note:\n\n{conversation_text}\n\n[RESPONSE]"
    result = pipe(prompt, max_new_tokens=1024)[0]["generated_text"]
    return result.split("[RESPONSE]")[-1].strip()

# Example raw conversation (from user or new file)
new_convo = """
[doctor] hi , andrew . how are you ?
[patient] hey , good to see you .
[doctor] i'm doing well , i'm doing well .
[patient] good .
[doctor] so , i know the nurse told you about dax . i'd like to tell dax a little bit about you .
[patient] sure .
[doctor] uh , so , andrew is a 59-year-old male with a past medical history , significant for depression , type two diabetes , and hypertension who presents today with an upper respiratory infection . so , andrew , what's going on ?
[patient] yeah . we were doing a bit of work out in the yard in the last week or so and i started to feel really tired , was short of breath . um , we- we're not wearing masks as much at the end of the summer and i think i caught my first cold and i think it just got worse .
[doctor] okay . all right . um , now , have you had your covid vaccines ?
[patient] yeah , both .
[doctor] okay . all right . and , um , do you have any history of any seasonal allergies at all ?
[patient] none whatsoever .
[doctor] okay . all right . and when you say you're having some shortness of breath , did you feel short of breath walking around or at rest ?
[patient] uh , usually , it was lifting or carrying something . we were doing some landscaping , so i was carrying some heavy bags of soil and i , i got really winded . it really surprised me .
[doctor] okay . and are you coughing up anything ?
[patient] not yet , but i feel like that's next .
[doctor] okay . and fevers ?
[patient] uh , i felt a little warm , but i , i just thought it was because i was exerting myself .
[doctor] okay . all right . and any other symptoms like muscle aches , joint pain , fatigue ?
[patient] my elbows hurt quite a bit and my knees were pretty tired . l- like i said , i really felt some tension around my knees , but , uh , i think that was a lot to do with , uh , lifting the bags .
[doctor] okay . all right . um , so , you know , how about , how are you doing in terms of your other medical problems , like your depression ? how are you doing with that ? i know we've , you know , talked about not putting you on medication for it because you're on medication for other things . what's going on ?
[patient] i- it's been kind of a crazy year and a half . i was a little concerned about that but , for the most part , i've been , been doing well with it . my , my wife got me into barre classes , to help me relax and i think it's working .
[doctor] okay . all right , great . and , and in terms of your diabetes , how are you doing watching your , your diet and your sugar intake ?
[patient] uh , i've been monitoring my sugar levels while i am going to work during the week . uh , not so , uh , if its saturday or sunday i usually don't remember . uh , the diet's been pretty good for the most part , except for , you know , some house parties and things like that . but , uh , been good for the most part .
[doctor] okay and have they been elevated at all since this episode of your-
[patient] no .
[doctor] okay . and then , how , lastly , for your high blood pressure , have you been monitoring your blood pressures at home ? did you buy the cuff like i suggested ?
[patient] uh , same thing . during the while i'm going to work, i'm regular about monitoring it, but if its a saturday or sunday, not so much . but , uh , it's , it's been under control .
[doctor] but you're taking your medication ?
[patient] yes .
[doctor] okay . all right . well , you know , i know that , you know , you've endorsed , you know , the shortness of breath and some joint pain . um , how about any other symptoms ? nausea or vomiting ? diarrhea ?
[patient] no .
[doctor] anything like that ?
[patient] no .
[doctor] okay . all right . well , i wan na go ahead and do a quick physical exam , all right ? hey , dragon , show me the vital signs . so , your vital signs here in the office look quite good .
[patient] mm-hmm .
[doctor] you know , everything's looking normal , you do n't have a fever , which is really good . um , i'm just gon na go ahead and listen to your heart and your lungs and , kind of , i'll let you know what i hear , okay ?
[patient] sure .
[doctor] okay . so , on your physical exam , you know , your heart sounds nice and strong . your lungs , you do have scattered ronchi bilaterally on your lung exam . uh , it clears with cough . um , i do notice a little bit of , um , some edema of your lower extremities and you do have some pain to palpation of your elbows bilaterally . um , so , let's go ahead , i want to look at some of your results , okay ?
[patient] mm-hmm .
[doctor] hey , dragon . show me the chest x-ray .
[doctor] so , i reviewed the results of your chest x-ray and everything looks good . there's no airspace disease , there's no pneumonia , so that's all very , very good , okay ?
[patient] good .
[doctor] hey , dragon . show me the diabetic labs .
[doctor] and here , looking at your diabetic labs , you know , your hemoglobin a1c is a little elevated at eight .
[patient] mm-hmm .
[doctor] i'd like to see that a little bit better , around six or seven , if possible .
[patient] mm-hmm .

"""

print(generate_soap_note(new_convo))

!pip install evaluate

import evaluate
rouge = evaluate.load("rouge")

# Evaluate generated vs actual
def evaluate_on_validation(n=100):
    preds, refs = [], []
    for i in range(n):
        example = dataset["test"][i]
        prompt = f"[INSTRUCTION] Convert the following medical conversation into a structured SOAP note:\n\n{example['src']}\n\n[RESPONSE]"
        output = pipe(prompt, max_new_tokens=1024)[0]["generated_text"]
        soap = output.split("[RESPONSE]")[-1].strip()
        preds.append(soap)
        refs.append(example["tgt"])

    scores = rouge.compute(predictions=preds, references=refs)
    print("📊 ROUGE Scores:", scores)

evaluate_on_validation(n=50)
import os
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import fitz  # PyMuPDF
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import nltk
# Optional (safe to leave)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

from keybert import KeyBERT
from nltk.tokenize import sent_tokenize
from PyPDF2 import PdfReader

nltk.download('punkt')

# Initialize global models
t5_model_name = "mrm8488/t5-base-finetuned-question-generation-ap"
t5_tokenizer = T5Tokenizer.from_pretrained(t5_model_name, trust_remote_code=True)
t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name, trust_remote_code=True)
kw_model = KeyBERT()

# ✅ PDF to text using PyMuPDF
def extract_text(file_obj):
    try:
        file_obj.seek(0)
        text = ""
        with fitz.open(stream=file_obj.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"[ERROR] Failed to extract PDF text: {e}")
        return ""

# ✅ MCQ generation using Hugging Face model
import random

def generate_mcqs_t5(text, num_questions=5):
    # Download punkt if not already present
    import nltk
    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize, word_tokenize

    prompt = f"generate questions: {text}"
    inputs = t5_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = t5_model.generate(inputs["input_ids"], max_length=256, num_return_sequences=num_questions, do_sample=True)
    decoded_questions = [t5_tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

    # Tokenize the whole document to create a pool of words for distractors
    words = list(set(word_tokenize(text)))
    words = [word for word in words if word.isalpha() and len(word) > 3]  # filter meaningful words

    questions = []
    for q in decoded_questions:
        if '?' not in q:
            continue

        question_text = q.strip().replace("question:", "").strip()

        # Try to extract the correct answer using KeyBERT or fallback to first keyword
        keywords = kw_model.extract_keywords(question_text, keyphrase_ngram_range=(1, 1), stop_words='english')
        correct_answer = keywords[0][0] if keywords else random.choice(words)

        # Pick 3 random incorrect options (ensure they are different from the answer)
        distractors = random.sample([w for w in words if w.lower() != correct_answer.lower()], 3)

        # Combine and shuffle options
        options = distractors + [correct_answer]
        random.shuffle(options)

        questions.append({
            "question": question_text,
            "options": options,
            "answer": correct_answer
        })

        if len(questions) >= num_questions:
            break

    return {"questions": questions}

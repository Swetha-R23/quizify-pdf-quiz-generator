import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import PyPDF2

# Load model once
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

def extract_text(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + ' '
    return text.strip()

def generate_mcqs_from_text(text, num_questions=5):
    if len(text.strip()) == 0:
        return {"questions": []}

    chunks = [text[i:i+400] for i in range(0, len(text), 400)]
    questions = []

    for i, chunk in enumerate(chunks):
        if len(questions) >= num_questions:
            break
        prompt = f"Generate one MCQ from the following text with 4 options and answer:\n\n{chunk}"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)

        try:
            outputs = model.generate(**inputs, max_length=256, do_sample=True)
            output = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Dummy parse logic (adjust this based on real model output)
            q_lines = output.split('\n')
            q_obj = {
                "question": q_lines[0],
                "options": q_lines[1:5],
                "answer": q_lines[5][-1] if len(q_lines) > 5 else "A"
            }
            questions.append(q_obj)

        except Exception as e:
            print(f"Error generating question from chunk {i}: {e}")
            continue

    return {"questions": questions[:num_questions]}
from django.db import models

class UploadedPDF(models.Model):
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class QuizQuestion(models.Model):
    pdf = models.ForeignKey(UploadedPDF, on_delete=models.CASCADE)
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    answer = models.CharField(max_length=1)  # A/B/C/D

    def __str__(self):
        return self.question[:100]

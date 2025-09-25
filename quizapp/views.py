from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadedPDF, QuizQuestion
from .utils import extract_text, generate_mcqs_t5
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Home page
def home(request):
    return render(request, 'quiz/home.html')


# Upload PDF and generate MCQs
def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        uploaded_file = request.FILES['pdf_file']
        pdf_instance = UploadedPDF.objects.create(file=uploaded_file)
        print(f"[DEBUG] File saved: {pdf_instance.file.name}")

        # Extract text from PDF
        text = extract_text(uploaded_file)

        # Get number of questions from form (default 5)
        num_questions = int(request.POST.get('num_questions', 5))

        # Generate MCQs using your utility function
        mcq_data = generate_mcqs_t5(text, num_questions=num_questions)
        print(f"[DEBUG] Generated MCQs: {mcq_data}")

        # Save each question in the database
        for item in mcq_data['questions']:
            options = item['options']
            QuizQuestion.objects.create(
                pdf=pdf_instance,
                question=item["question"],
                option_a=options[0],
                option_b=options[1],
                option_c=options[2],
                option_d=options[3],
                answer=item["answer"]
            )

        # Redirect to take quiz page
        return redirect('take_quiz', pdf_id=pdf_instance.id)

    # Pass number range for dropdown in template
    num_range = range(1, 11)
    return render(request, 'quiz/upload.html', {'num_range': num_range})


# Display the MCQ quiz
def take_mcq(request, pdf_id):
    pdf = get_object_or_404(UploadedPDF, id=pdf_id)
    questions = QuizQuestion.objects.filter(pdf=pdf)

    # Prepare option letters for display
    letters = ["a", "b", "c", "d"]
    for q in questions:
        q.option_list = list(zip(letters, [q.option_a, q.option_b, q.option_c, q.option_d]))

    return render(request, 'quiz/quiz.html', {
        'questions': questions,
        'pdf_id': pdf.id
    })


# Show quiz result
def show_result(request, pdf_id):
    pdf = get_object_or_404(UploadedPDF, id=pdf_id)
    questions = QuizQuestion.objects.filter(pdf=pdf)

    correct = 0
    total = questions.count()
    user_answers = {}

    for i, question in enumerate(questions, start=1):
        user_answer = request.POST.get(f'question_{i}')
        user_answers[question] = {
            "your_answer": user_answer if user_answer else "Not answered",
            "correct_answer": question.answer,
            "is_correct": user_answer == question.answer
        }
        if user_answer == question.answer:
            correct += 1

    score = int((correct / total) * 100) if total > 0 else 0

    context = {
        'pdf': pdf,
        'score': score,
        'total': total,
        'correct': correct,
        'user_answers': user_answers
    }
    return render(request, 'quiz/result.html', context)

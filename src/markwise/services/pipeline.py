import json
import time
from datetime import datetime

from markwise.db.models import Assessment, Grade, Student
from markwise.db.session import get_session
from markwise.services.grader import GradingError, grade_submission
from markwise.services.pdf_reader import extract_content


def run_grading(client, assessment_id, grade_ids, should_stop=lambda: False,
                on_progress=lambda done, total: None, min_interval=0.0, sleep=time.sleep):
    with get_session() as s:
        assessment = s.get(Assessment, assessment_id)
        max_marks, rubric, solution_path = assessment.max_marks, assessment.rubric, assessment.solution_path
    if not solution_path:
        raise GradingError("Choose a sample solution file first.")
    solution = extract_content(solution_path)

    total = len(grade_ids)
    for done, grade_id in enumerate(grade_ids, 1):
        if should_stop():
            break
        called_api = False
        try:
            with get_session() as s:
                grade = s.get(Grade, grade_id)
                student = s.get(Student, grade.student_pk)
                if not student.consent:
                    grade.status = "no_consent"
                    pdf_path = None
                else:
                    pdf_path = grade.pdf_path
            if pdf_path:
                submission = extract_content(pdf_path)
                called_api = True
                result = grade_submission(client, max_marks, rubric, solution, submission, sleep=sleep)
                with get_session() as s:
                    grade = s.get(Grade, grade_id)
                    grade.score = result["score"]
                    grade.feedback = result["feedback"]
                    grade.confidence = result["confidence"]
                    grade.ai_json = json.dumps(result, ensure_ascii=False)
                    grade.status = "graded"
                    grade.overridden = False
                    grade.graded_at = datetime.now()
        except Exception as exc:
            with get_session() as s:
                grade = s.get(Grade, grade_id)
                grade.status = "error"
                grade.feedback = f"{type(exc).__name__}: {exc}"
        on_progress(done, total)
        if called_api and done < total and min_interval:
            sleep(min_interval)

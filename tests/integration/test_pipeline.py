import pymupdf

from markwise.db.models import Assessment, Course, Grade, Offering, Student, User
from markwise.db.session import get_session
from markwise.services.pipeline import run_grading

GOOD = '{"score": 7, "per_question": [], "feedback": "ok", "confidence": "high"}'


class FakeClient:
    def generate(self, prompt, solution, submission):
        return GOOD


def make_pdf(path):
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Answer text " * 20)
    doc.save(str(path))


def test_grades_consenting_student_and_skips_the_other(db, tmp_path):
    solution, work = tmp_path / "solution.pdf", tmp_path / "001_ali.pdf"
    make_pdf(solution)
    make_pdf(work)
    with get_session() as s:
        user = User(username="t", password_hash="x")
        s.add(user)
        s.flush()
        course = Course(code="CS101", title="Intro", owner_id=user.id)
        s.add(course)
        s.flush()
        offering = Offering(course_id=course.id, semester="Fall 2026")
        s.add(offering)
        s.flush()
        assessment = Assessment(offering_id=offering.id, title="Quiz 1", kind="quiz",
                                max_marks=10, solution_path=str(solution))
        ali = Student(offering_id=offering.id, student_id="001", name="Ali", consent=True)
        sara = Student(offering_id=offering.id, student_id="002", name="Sara", consent=False)
        s.add_all([assessment, ali, sara])
        s.flush()
        g1 = Grade(assessment_id=assessment.id, student_pk=ali.id, pdf_path=str(work), status="pending")
        g2 = Grade(assessment_id=assessment.id, student_pk=sara.id, pdf_path=str(work), status="pending")
        s.add_all([g1, g2])
        s.flush()
        assessment_id, ids = assessment.id, [g1.id, g2.id]

    run_grading(FakeClient(), assessment_id, ids, sleep=lambda _: None)

    with get_session() as s:
        first, second = s.get(Grade, ids[0]), s.get(Grade, ids[1])
        assert first.status == "graded" and first.score == 7
        assert second.status == "no_consent" and second.score is None

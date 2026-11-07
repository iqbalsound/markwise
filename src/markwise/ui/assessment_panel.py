from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from markwise.db.models import Assessment, Grade, Student
from markwise.db.session import get_session
from markwise.services import files, keystore
from markwise.services.export import export_rows
from markwise.services.grader import DEFAULT_MODEL, GeminiClient
from markwise.services.pipeline import run_grading
from markwise.ui.dialogs import EditGradeDialog, PdfPreviewDialog

COLUMNS = ["Student ID", "Name", "Consent", "PDF file", "Status", "Score", "Confidence", "Feedback"]


class GradeWorker(QThread):
    progress = Signal(int, int)
    failed = Signal(str)

    def __init__(self, client, assessment_id, grade_ids, min_interval):
        super().__init__()
        self.client = client
        self.assessment_id = assessment_id
        self.grade_ids = grade_ids
        self.min_interval = min_interval
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        try:
            run_grading(
                self.client, self.assessment_id, self.grade_ids,
                should_stop=lambda: self._stop_requested,
                on_progress=self.progress.emit,
                min_interval=self.min_interval,
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class AssessmentPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.assessment_id = None
        self.max_marks = 0.0
        self.rows = []
        self.worker = None

        self.title = QLabel("")
        self.title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.paths_label = QLabel("")
        self.paths_label.setWordWrap(True)
        self.status = QLabel("")
        self.progress = QProgressBar()
        self.progress.setVisible(False)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(lambda *_: self.edit_selected())

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.paths_label)
        layout.addLayout(self._button_row([
            ("Sample solution…", self.choose_solution), ("Submissions folder…", self.choose_folder),
            ("Scan folder", self.scan), ("Assign PDF…", self.assign_pdf),
        ]))
        layout.addLayout(self._button_row([
            ("Grade pending", self.grade_pending), ("Stop", self.stop_grading),
            ("Edit grade", self.edit_selected), ("Preview", self.preview), ("Open PDF", self.open_external),
            ("Download selected", self.download_selected), ("Download all (ZIP)", self.download_all),
            ("Export…", self.export),
        ]))
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.table)

    def _button_row(self, items):
        row = QHBoxLayout()
        for text, slot in items:
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, fn=slot: fn())
            row.addWidget(button)
        row.addStretch()
        return row

    # ---------- loading ----------
    def load(self, assessment_id):
        self.assessment_id = assessment_id
        self.status.setText("")
        self.refresh()

    def refresh(self):
        if self.assessment_id is None:
            return
        with get_session() as s:
            a = s.get(Assessment, self.assessment_id)
            if a is None:
                return
            self.title.setText(f"{a.title}   ({a.kind}, {a.max_marks:g} marks)")
            self.paths_label.setText(
                f"Sample solution: {a.solution_path or 'not set'}\n"
                f"Submissions folder: {a.submissions_folder or 'not set'}"
            )
            self.max_marks = a.max_marks
            students = s.query(Student).filter_by(offering_id=a.offering_id).order_by(Student.student_id).all()
            grades = {g.student_pk: g for g in s.query(Grade).filter_by(assessment_id=a.id)}

        self.rows = []
        self.table.setRowCount(len(students))
        for r, st in enumerate(students):
            g = grades.get(st.id)
            row = {
                "student_pk": st.id, "grade_id": g.id if g else None, "student_id": st.student_id,
                "name": st.name, "consent": st.consent, "pdf": g.pdf_path if g else None,
                "status": g.status if g else "not scanned", "score": g.score if g else None,
                "confidence": g.confidence if g else "", "feedback": g.feedback if g else "",
                "edited": bool(g and g.overridden),
            }
            self.rows.append(row)
            status = row["status"] + (" (edited)" if row["edited"] else "")
            confidence = "low - check" if row["confidence"] == "low" else row["confidence"]
            score = "" if row["score"] is None else f"{row['score']:g}"
            values = [
                row["student_id"], row["name"], "yes" if row["consent"] else "NO",
                Path(row["pdf"]).name if row["pdf"] else "", status, score, confidence,
                row["feedback"].replace("\n", " "),
            ]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _selected_rows(self):
        return sorted({i.row() for i in self.table.selectionModel().selectedRows()})

    def _selected_pdf(self):
        rows = self._selected_rows()
        if not rows:
            QMessageBox.information(self, "MarkWise", "Select a student row first.")
            return None
        pdf = self.rows[rows[0]]["pdf"]
        if not pdf or not Path(pdf).exists():
            QMessageBox.information(self, "MarkWise", "No PDF is available for this student.")
            return None
        return pdf

    # ---------- setup buttons ----------
    def choose_solution(self):
        if self.assessment_id is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Sample solution", "", "Documents (*.pdf *.docx *.png *.jpg *.jpeg)")
        if path:
            with get_session() as s:
                s.get(Assessment, self.assessment_id).solution_path = path
            self.refresh()

    def choose_folder(self):
        if self.assessment_id is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Folder with student PDFs (local or shared drive)")
        if folder:
            with get_session() as s:
                s.get(Assessment, self.assessment_id).submissions_folder = folder
            self.scan()

    def scan(self):
        if self.assessment_id is None:
            return
        with get_session() as s:
            folder = s.get(Assessment, self.assessment_id).submissions_folder
        if not folder:
            QMessageBox.information(self, "MarkWise", "Choose the submissions folder first.")
            return
        try:
            pdfs = files.list_pdfs(folder)
        except OSError as exc:
            QMessageBox.warning(
                self, "Folder not available",
                f"Cannot read:\n{folder}\n\n{exc}\n\nCheck that the shared drive is connected, then press Scan again.")
            return
        matched = set()
        with get_session() as s:
            a = s.get(Assessment, self.assessment_id)
            for st in s.query(Student).filter_by(offering_id=a.offering_id):
                g = s.query(Grade).filter_by(assessment_id=a.id, student_pk=st.id).first()
                if g is None:
                    g = Grade(assessment_id=a.id, student_pk=st.id, status="pending")
                    s.add(g)
                pdf = files.match_pdf(st.student_id, pdfs)
                if pdf is None and g.pdf_path and Path(g.pdf_path).exists():
                    pdf = Path(g.pdf_path)  # keep a manually assigned file
                if pdf is not None:
                    matched.add(pdf)
                if g.status != "graded":
                    g.pdf_path = str(pdf) if pdf else None
                    g.status = "no_consent" if not st.consent else ("pending" if pdf else "no_file")
        unmatched = [p.name for p in pdfs if p not in matched]
        self.status.setText(f"{len(pdfs)} PDFs found, {len(unmatched)} not matched to any student.")
        if unmatched:
            QMessageBox.information(
                self, "Unmatched PDFs",
                "These files did not match any student ID:\n\n" + "\n".join(unmatched[:30])
                + "\n\nSelect a student and use 'Assign PDF…'.")
        self.refresh()

    def assign_pdf(self):
        rows = self._selected_rows()
        if not rows or self.assessment_id is None:
            QMessageBox.information(self, "MarkWise", "Select a student row first.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Choose PDF for this student", "", "PDF (*.pdf)")
        if not path:
            return
        row = self.rows[rows[0]]
        with get_session() as s:
            g = s.query(Grade).filter_by(assessment_id=self.assessment_id, student_pk=row["student_pk"]).first()
            if g is None:
                g = Grade(assessment_id=self.assessment_id, student_pk=row["student_pk"])
                s.add(g)
            g.pdf_path = path
            g.status = "pending" if row["consent"] else "no_consent"
        self.refresh()

    # ---------- grading ----------
    def grade_pending(self):
        if self.assessment_id is None or (self.worker and self.worker.isRunning()):
            return
        api_key = keystore.load_api_key()
        if not api_key:
            QMessageBox.warning(self, "MarkWise", "Add your Gemini API key in Tools → Settings first.")
            return
        with get_session() as s:
            a = s.get(Assessment, self.assessment_id)
            if not a.solution_path:
                QMessageBox.warning(self, "MarkWise", "Choose the sample solution first.")
                return
            ids = [g.id for g in s.query(Grade).filter_by(assessment_id=a.id, status="pending")]
        if not ids:
            QMessageBox.information(self, "MarkWise", "Nothing is pending. Press 'Scan folder' first.")
            return
        settings = QSettings()
        model = settings.value("model", DEFAULT_MODEL, type=str)
        rpm = max(1, settings.value("rpm", 10, type=int))
        try:
            client = GeminiClient(api_key, model)
        except Exception as exc:
            QMessageBox.critical(self, "MarkWise", f"Could not start the Gemini client:\n{exc}")
            return
        self.worker = GradeWorker(client, self.assessment_id, ids, 60.0 / rpm)
        self.worker.progress.connect(self.on_progress)
        self.worker.failed.connect(lambda msg: QMessageBox.critical(self, "Grading stopped", msg))
        self.worker.finished.connect(self.on_finished)
        self.progress.setRange(0, len(ids))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.worker.start()

    def on_progress(self, done, total):
        self.progress.setValue(done)
        self.status.setText(f"Graded {done} of {total} …")

    def on_finished(self):
        self.progress.setVisible(False)
        self.status.setText("Grading finished. Check rows marked 'low - check' or 'error'.")
        self.refresh()

    def stop_grading(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status.setText("Stopping after the current student …")

    def shutdown(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(15000)

    def edit_selected(self):
        rows = self._selected_rows()
        if not rows:
            QMessageBox.information(self, "MarkWise", "Select a student row first.")
            return
        row = self.rows[rows[0]]
        if row["grade_id"] is None:
            QMessageBox.information(self, "MarkWise", "Press 'Scan folder' first.")
            return
        dialog = EditGradeDialog(self.max_marks, row["score"], row["feedback"], self)
        if dialog.exec():
            with get_session() as s:
                g = s.get(Grade, row["grade_id"])
                g.score = dialog.score.value()
                g.feedback = dialog.feedback.toPlainText()
                g.overridden = True
                g.status = "graded"
                g.graded_at = datetime.now()
            self.refresh()

    # ---------- PDFs and export ----------
    def preview(self):
        pdf = self._selected_pdf()
        if pdf:
            try:
                PdfPreviewDialog(pdf, self).exec()
            except ImportError:
                self.open_external()

    def open_external(self):
        pdf = self._selected_pdf()
        if pdf:
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf))

    def _existing_pdfs(self, rows):
        return [Path(self.rows[r]["pdf"]) for r in rows if self.rows[r]["pdf"] and Path(self.rows[r]["pdf"]).exists()]

    def download_selected(self):
        pdfs = self._existing_pdfs(self._selected_rows())
        if not pdfs:
            QMessageBox.information(self, "MarkWise", "Select one or more students that have PDFs.")
            return
        dest = QFileDialog.getExistingDirectory(self, "Copy selected PDFs to …")
        if dest:
            try:
                n = files.copy_files(pdfs, dest)
                QMessageBox.information(self, "MarkWise", f"Copied {n} file(s).")
            except OSError as exc:
                QMessageBox.critical(self, "MarkWise", str(exc))

    def download_all(self):
        pdfs = self._existing_pdfs(range(len(self.rows)))
        if not pdfs:
            QMessageBox.information(self, "MarkWise", "No PDFs found. Press 'Scan folder' first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save ZIP", "submissions.zip", "ZIP (*.zip)")
        if path:
            if not path.lower().endswith(".zip"):
                path += ".zip"
            try:
                n = files.make_zip(pdfs, path)
                QMessageBox.information(self, "MarkWise", f"Saved {n} PDF(s) to the ZIP file.")
            except OSError as exc:
                QMessageBox.critical(self, "MarkWise", str(exc))

    def export(self):
        if not self.rows:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export grades", "grades.xlsx", "Excel (*.xlsx);;CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith((".csv", ".xlsx")):
            path += ".xlsx"
        data = [{
            "Student ID": r["student_id"], "Name": r["name"],
            "PDF file": Path(r["pdf"]).name if r["pdf"] else "", "Status": r["status"],
            "Score": r["score"], "Max marks": self.max_marks, "Confidence": r["confidence"],
            "Feedback": r["feedback"], "Edited by teacher": "yes" if r["edited"] else "",
        } for r in self.rows]
        try:
            export_rows(data, path)
            QMessageBox.information(self, "MarkWise", f"Saved:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "MarkWise", str(exc))

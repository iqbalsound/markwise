from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel,
    QLineEdit, QPlainTextEdit, QSpinBox, QVBoxLayout,
)

from markwise.services import keystore
from markwise.services.grader import DEFAULT_MODEL
from markwise.services.roster import guess_column


class FormDialog(QDialog):
    """Base class: a form with OK and Cancel buttons."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.form = QFormLayout()
        outer = QVBoxLayout(self)
        outer.addLayout(self.form)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        outer.addWidget(self.buttons)


class NewAssessmentDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__("New assignment / quiz", parent)
        self.title_edit = QLineEdit()
        self.kind = QComboBox()
        self.kind.addItems(["assignment", "quiz"])
        self.max_marks = QDoubleSpinBox()
        self.max_marks.setRange(0.5, 1000)
        self.max_marks.setValue(10)
        self.rubric = QPlainTextEdit()
        self.rubric.setPlaceholderText("Optional, e.g. Q1 formula 2 marks, working 3 marks ...")
        self.form.addRow("Title", self.title_edit)
        self.form.addRow("Type", self.kind)
        self.form.addRow("Maximum marks", self.max_marks)
        self.form.addRow("Rubric", self.rubric)

    def accept(self):
        if self.title_edit.text().strip():
            super().accept()

    def values(self):
        return {
            "title": self.title_edit.text().strip(),
            "kind": self.kind.currentText(),
            "max_marks": self.max_marks.value(),
            "rubric": self.rubric.toPlainText().strip(),
        }


class RosterMappingDialog(FormDialog):
    """Lets the teacher say which spreadsheet column is the ID, name, email and consent."""

    NONE = "(none)"

    def __init__(self, columns, row_count, parent=None):
        super().__init__("Import students", parent)
        self.form.addRow(QLabel(f"{row_count} rows found. Match the columns:"))
        self.id_box, self.name_box = QComboBox(), QComboBox()
        self.email_box, self.consent_box = QComboBox(), QComboBox()
        for box in (self.id_box, self.name_box):
            box.addItems(columns)
        for box in (self.email_box, self.consent_box):
            box.addItems([self.NONE] + list(columns))
        for box, words in ((self.id_box, ("id", "roll", "reg")), (self.name_box, ("name",)),
                           (self.email_box, ("mail",)), (self.consent_box, ("consent",))):
            guess = guess_column(columns, words)
            if guess:
                box.setCurrentText(guess)
        self.default_consent = QCheckBox("Students have given consent (used when there is no consent column)")
        self.form.addRow("Student ID column", self.id_box)
        self.form.addRow("Name column", self.name_box)
        self.form.addRow("Email column", self.email_box)
        self.form.addRow("Consent column", self.consent_box)
        self.form.addRow(self.default_consent)

    def values(self):
        def pick(box):
            return None if box.currentText() == self.NONE else box.currentText()

        return {
            "id": self.id_box.currentText(),
            "name": self.name_box.currentText(),
            "email": pick(self.email_box),
            "consent": pick(self.consent_box),
            "default_consent": self.default_consent.isChecked(),
        }


class EditGradeDialog(FormDialog):
    def __init__(self, max_marks, score, feedback, parent=None):
        super().__init__("Edit grade", parent)
        self.score = QDoubleSpinBox()
        self.score.setRange(0, max_marks)
        self.score.setDecimals(2)
        self.score.setValue(score or 0)
        self.feedback = QPlainTextEdit(feedback or "")
        self.form.addRow(f"Score (max {max_marks:g})", self.score)
        self.form.addRow("Feedback", self.feedback)


class SettingsDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        settings = QSettings()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Leave blank to keep the saved key")
        self.model = QLineEdit(settings.value("model", DEFAULT_MODEL, type=str))
        self.rpm = QSpinBox()
        self.rpm.setRange(1, 60)
        self.rpm.setValue(settings.value("rpm", 10, type=int))
        self.theme = QComboBox()
        self.theme.addItems(["light", "dark", "system"])
        self.theme.setCurrentText(settings.value("theme", "light", type=str))
        self.form.addRow("Gemini API key", self.api_key)
        self.form.addRow("Gemini model name", self.model)
        self.form.addRow("Requests per minute", self.rpm)
        self.form.addRow("Theme", self.theme)

    def save(self) -> bool:
        """Save everything. Returns False if the API key could only be kept for this session."""
        settings = QSettings()
        settings.setValue("model", self.model.text().strip() or DEFAULT_MODEL)
        settings.setValue("rpm", self.rpm.value())
        settings.setValue("theme", self.theme.currentText())
        key = self.api_key.text().strip()
        return keystore.save_api_key(key) if key else True


class PdfPreviewDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        from PySide6.QtPdf import QPdfDocument  # imported here so a missing Qt PDF module cannot stop the app
        from PySide6.QtPdfWidgets import QPdfView

        self.setWindowTitle(Path(path).name)
        self.resize(900, 700)
        self.doc = QPdfDocument(self)
        self.doc.load(str(path))
        self.view = QPdfView(self)
        self.view.setDocument(self.doc)
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        QVBoxLayout(self).addWidget(self.view)

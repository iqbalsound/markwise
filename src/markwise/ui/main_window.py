from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
)

from markwise import app_info as info
from markwise.auth.passwords import create_user
from markwise.db.models import Assessment, Course, Offering, Student
from markwise.db.session import get_session
from markwise.services.roster import read_table, rows_from_table
from markwise.ui.about import show_about
from markwise.ui.assessment_panel import AssessmentPanel
from markwise.ui.dialogs import NewAssessmentDialog, RosterMappingDialog, SettingsDialog
from markwise.ui.theme import apply_theme

HELP_TEXT = ("Welcome to MarkWise.\n\n1. File → New course\n2. File → New semester (select the course first)\n"
             "3. Roster → Import students (select the semester)\n"
             "4. File → New assignment / quiz (select the semester)\n"
             "5. Select the assignment, then choose the solution and the submissions folder.")


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"{info.APP_NAME} {info.APP_VERSION} - {user.username}")
        self.resize(1250, 740)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Courses → Semesters → Assignments / Quizzes")
        self.tree.setMinimumWidth(280)
        self.panel = AssessmentPanel()
        self.info = QLabel(HELP_TEXT)
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info.setWordWrap(True)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.info)
        self.stack.addWidget(self.panel)
        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._build_menu()
        self.tree.itemSelectionChanged.connect(self.on_select)
        self.refresh_tree()

    # ---------- menus ----------
    def _act(self, menu, text, fn):
        action = QAction(text, self)
        action.triggered.connect(lambda checked=False: fn())
        menu.addAction(action)

    def _build_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")
        self._act(file_menu, "New course…", self.new_course)
        self._act(file_menu, "New semester…", self.new_offering)
        self._act(file_menu, "New assignment / quiz…", self.new_assessment)
        file_menu.addSeparator()
        self._act(file_menu, "Duplicate semester (copies assignments)…", self.duplicate_offering)
        self._act(file_menu, "Delete selected…", self.delete_selected)
        file_menu.addSeparator()
        self._act(file_menu, "Quit", self.close)
        self._act(bar.addMenu("&Roster"), "Import students from Excel / CSV…", self.import_roster)
        if self.user.role == "admin":
            self._act(bar.addMenu("&Users"), "Add teacher account…", self.add_teacher)
        self._act(bar.addMenu("&View"), "Switch light / dark theme", self.toggle_theme)
        self._act(bar.addMenu("&Tools"), "Settings…", self.open_settings)
        self._act(bar.addMenu("&Help"), f"About {info.APP_NAME}", lambda: show_about(self))

    # ---------- tree ----------
    @staticmethod
    def _item(parent, text, kind, id_):
        item = QTreeWidgetItem(parent, [text])
        item.setData(0, Qt.ItemDataRole.UserRole, (kind, id_))
        return item

    def selected(self):
        items = self.tree.selectedItems()
        if not items:
            return None, None
        return items[0].data(0, Qt.ItemDataRole.UserRole)

    def refresh_tree(self, select=None):
        keep = select or self.selected()
        target = None
        self.tree.blockSignals(True)
        self.tree.clear()
        with get_session() as s:
            query = s.query(Course)
            if self.user.role != "admin":
                query = query.filter(Course.owner_id == self.user.id)
            for course in query.order_by(Course.code):
                course_item = self._item(self.tree, f"{course.code} - {course.title}", "course", course.id)
                if keep == ("course", course.id):
                    target = course_item
                for off in s.query(Offering).filter_by(course_id=course.id).order_by(Offering.id):
                    off_item = self._item(course_item, off.semester, "offering", off.id)
                    if keep == ("offering", off.id):
                        target = off_item
                    for a in s.query(Assessment).filter_by(offering_id=off.id).order_by(Assessment.id):
                        a_item = self._item(off_item, f"[{a.kind}] {a.title}", "assessment", a.id)
                        if keep == ("assessment", a.id):
                            target = a_item
        self.tree.expandAll()
        self.tree.blockSignals(False)
        if target is not None:
            self.tree.setCurrentItem(target)
        self.on_select()

    def context(self):
        """Course, semester and assignment ids that contain the selected tree item."""
        ctx = {"course_id": None, "offering_id": None, "assessment_id": None}
        kind, id_ = self.selected()
        if kind is None:
            return ctx
        with get_session() as s:
            if kind == "assessment":
                a = s.get(Assessment, id_)
                ctx["assessment_id"], id_, kind = a.id, a.offering_id, "offering"
            if kind == "offering":
                o = s.get(Offering, id_)
                ctx["offering_id"], id_ = o.id, o.course_id
            ctx["course_id"] = id_
        return ctx

    def on_select(self):
        kind, id_ = self.selected()
        if kind == "assessment":
            self.panel.load(id_)
            self.stack.setCurrentWidget(self.panel)
            return
        text = HELP_TEXT
        if kind == "offering":
            with get_session() as s:
                count = s.query(Student).filter_by(offering_id=id_).count()
            text = (f"{count} student(s) in this semester.\n\nRoster → Import students loads names and IDs "
                    "from Excel or CSV.\nFile → New assignment / quiz adds work to grade.")
        self.info.setText(text)
        self.stack.setCurrentWidget(self.info)

    def _need(self, what):
        QMessageBox.information(self, "MarkWise", f"Select {what} in the tree first.")

    # ---------- actions ----------
    def new_course(self):
        code, ok = QInputDialog.getText(self, "New course", "Course code (e.g. CS101):")
        if not ok or not code.strip():
            return
        title, ok = QInputDialog.getText(self, "New course", "Course title:")
        if not ok:
            return
        with get_session() as s:
            course = Course(code=code.strip(), title=title.strip(), owner_id=self.user.id)
            s.add(course)
            s.flush()
            new_id = course.id
        self.refresh_tree(("course", new_id))

    def new_offering(self):
        ctx = self.context()
        if not ctx["course_id"]:
            return self._need("a course")
        name, ok = QInputDialog.getText(self, "New semester", "Semester name (e.g. Fall 2026):")
        if not ok or not name.strip():
            return
        with get_session() as s:
            off = Offering(course_id=ctx["course_id"], semester=name.strip())
            s.add(off)
            s.flush()
            new_id = off.id
        self.refresh_tree(("offering", new_id))

    def new_assessment(self):
        ctx = self.context()
        if not ctx["offering_id"]:
            return self._need("a semester")
        dialog = NewAssessmentDialog(self)
        if not dialog.exec():
            return
        with get_session() as s:
            a = Assessment(offering_id=ctx["offering_id"], **dialog.values())
            s.add(a)
            s.flush()
            new_id = a.id
        self.refresh_tree(("assessment", new_id))

    def duplicate_offering(self):
        ctx = self.context()
        if not ctx["offering_id"]:
            return self._need("a semester")
        name, ok = QInputDialog.getText(self, "Duplicate semester", "Name of the new semester:")
        if not ok or not name.strip():
            return
        with get_session() as s:
            old = s.get(Offering, ctx["offering_id"])
            new = Offering(course_id=old.course_id, semester=name.strip())
            s.add(new)
            s.flush()
            for a in s.query(Assessment).filter_by(offering_id=old.id):
                s.add(Assessment(offering_id=new.id, title=a.title, kind=a.kind, max_marks=a.max_marks,
                                 rubric=a.rubric, solution_path=a.solution_path))
            new_id = new.id
        self.refresh_tree(("offering", new_id))

    def delete_selected(self):
        kind, id_ = self.selected()
        if kind is None:
            return self._need("an item")
        reply = QMessageBox.question(
            self, "Delete", "Delete the selected item and everything inside it (students, grades)?\n"
            "This cannot be undone.")
        if reply != QMessageBox.StandardButton.Yes:
            return
        model = {"course": Course, "offering": Offering, "assessment": Assessment}[kind]
        with get_session() as s:
            s.delete(s.get(model, id_))
        self.refresh_tree(("none", 0))

    def import_roster(self):
        ctx = self.context()
        if not ctx["offering_id"]:
            return self._need("a semester")
        path, _ = QFileDialog.getOpenFileName(self, "Student list", "", "Spreadsheets (*.xlsx *.xls *.csv)")
        if not path:
            return
        try:
            df = read_table(path)
        except Exception as exc:
            QMessageBox.critical(self, "Cannot read file", str(exc))
            return
        dialog = RosterMappingDialog(list(df.columns), len(df), self)
        if not dialog.exec():
            return
        v = dialog.values()
        rows, duplicates = rows_from_table(df, v["id"], v["name"], v["email"], v["consent"], v["default_consent"])
        added = updated = 0
        with get_session() as s:
            for r in rows:
                st = s.query(Student).filter_by(offering_id=ctx["offering_id"], student_id=r["student_id"]).first()
                if st is None:
                    s.add(Student(offering_id=ctx["offering_id"], **r))
                    added += 1
                else:
                    st.name, st.email, st.consent = r["name"], r["email"], r["consent"]
                    updated += 1
        QMessageBox.information(
            self, "Import finished",
            f"Added: {added}\nUpdated: {updated}\nSkipped duplicate IDs: {len(duplicates)}")
        self.on_select()

    def add_teacher(self):
        name, ok = QInputDialog.getText(self, "Add teacher", "Username:")
        if not ok or not name.strip():
            return
        password, ok = QInputDialog.getText(self, "Add teacher", "Password (min 8 characters):",
                                            QLineEdit.EchoMode.Password)
        if not ok or len(password) < 8:
            QMessageBox.warning(self, "MarkWise", "Password must be at least 8 characters.")
            return
        try:
            with get_session() as s:
                create_user(s, name.strip(), password, role="teacher")
            QMessageBox.information(self, "MarkWise", "Teacher account created.")
        except Exception:
            QMessageBox.warning(self, "MarkWise", "Could not create the account (the username may already exist).")

    def toggle_theme(self):
        settings = QSettings()
        new = "light" if settings.value("theme", "light", type=str) == "dark" else "dark"
        settings.setValue("theme", new)
        apply_theme(QApplication.instance(), new)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            stored = dialog.save()
            apply_theme(QApplication.instance(), dialog.theme.currentText())
            if not stored:
                QMessageBox.information(
                    self, "MarkWise",
                    "No system keyring was found, so the API key is kept for this session only.\n"
                    "You will need to enter it again next time.")

    def closeEvent(self, event):
        self.panel.shutdown()
        super().closeEvent(event)

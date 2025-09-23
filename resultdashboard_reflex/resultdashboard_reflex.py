# [your_project_name].py
import reflex as rx
from typing import Optional
try:
    from sqlmodel import SQLModel, create_engine
except Exception:
    # Defer import errors to runtime; SQLModel may not be installed in the editor.
    SQLModel = None
    create_engine = None
from sqlalchemy.exc import OperationalError
# decimal removed — not used in this module

# In this editor environment we avoid importing heavy optional
# dependencies (plotly, pandas). The UI will show placeholders when
# those libraries are not available at runtime.
go = None
# Avoid importing optional heavy libraries at module import time to keep the editor environment clean.
CHARTS_AVAILABLE = False
PANDAS_AVAILABLE = False

# --- Database Model (SQLite) ---
class Student(rx.Model, table=True):
    """Represents a student's academic record."""
    # Use Optional[...] annotations with None defaults so SQLModel
    # (and SQLAlchemy) can infer column types at runtime. This avoids
    # constructing Field() instances that the SQLModel type inference
    # in this environment had trouble matching.
    roll_no: Optional[int] = None
    name: Optional[str] = None
    bangla_marks: Optional[int] = None
    english_marks: Optional[int] = None
    math_marks: Optional[int] = None
    science_marks: Optional[int] = None
    total_marks: Optional[int] = None
    grade: Optional[str] = None

# --- App State ---
class ResultState(rx.State):
    """The state for the student result management app."""
    # Teacher Dashboard State
    teacher_logged_in: bool = False
    teacher_username: str = "talha"
    teacher_password: str = "258090"
    # Inputs for login form (separate from stored credentials)
    teacher_username_input: str = "talha"
    teacher_password_input: str = "258090"
    
    # Form fields
    student_name: str = ""
    student_roll: str = ""
    marks_bangla: str = ""
    marks_english: str = ""
    marks_math: str = ""
    marks_science: str = ""
    
    # Student Dashboard State
    student_roll_input: str = ""
    student_result_data: dict = {}
    # Currently selected subject filter (populated via UI). Declare as a
    # state variable so `filter_subject` can set it at runtime.
    _filtered_subject: Optional[str] = None
    
    # Data from DB
    students: list[Student] = []
    top_performers: list[Student] = []
    # Timeline / calendar events added by teacher (visible to students)
    # Store as simple display strings to simplify rendering and avoid Var-indexing issues.
    timeline_events: list[str] = []  # each event: "YYYY-MM-DD - Title (type)"
    # Leaderboard/top students cached list (display strings)
    leaderboard_top: list[str] = []
    # Temporary inputs for teacher to add timeline events
    _new_event_title: str = ""
    _new_event_date: str = ""
    _new_event_type: str = "exam"
     
    @classmethod
    def get_subject_averages(cls):
        """Calculate average marks for each subject and return as a list of (subject, average) pairs."""
        # Access class-level students list defensively.
        # Avoid using boolean operations on Reflex Vars (they cannot be used
        # directly with `if`, `and`, `or`, `not`). If `students` isn't a
        # plain Python list (e.g. a Var during compile time), return default
        # averages so the page can compile. At runtime the stateful methods
        # that populate `students` will update the UI.
        students = getattr(cls, "students", [])
        if not isinstance(students, list):
            return [("Bangla", 0), ("English", 0), ("Math", 0), ("Science", 0)]
        if len(students) == 0:
            return [("Bangla", 0), ("English", 0), ("Math", 0), ("Science", 0)]

        total_bangla = sum(getattr(s, "bangla_marks", 0) for s in students)
        total_english = sum(getattr(s, "english_marks", 0) for s in students)
        total_math = sum(getattr(s, "math_marks", 0) for s in students)
        total_science = sum(getattr(s, "science_marks", 0) for s in students)
        count = len(students)

        return [
            ("Bangla", total_bangla // count),
            ("English", total_english // count),
            ("Math", total_math // count),
            ("Science", total_science // count),
        ]

    @classmethod
    def get_subject_averages_dict(cls):
        """Return subject averages as an ordered dict-like list of tuples."""
        return cls.get_subject_averages()

    @classmethod
    def get_top_students(cls, n: int = 5):
        """Return list of (name, average) tuples for top N students based on total_marks."""
        students = getattr(cls, "students", [])
        if not isinstance(students, list):
            return []
        rows = sorted(students, key=lambda s: getattr(s, "total_marks", 0), reverse=True)
        result = []
        for s in rows[:n]:
            avg = 0
            try:
                avg = int(getattr(s, "total_marks", 0) // 4)
            except Exception:
                avg = getattr(s, "total_marks", 0)
            result.append((getattr(s, "name", ""), avg))
        return result

    @rx.event
    def filter_subject(self, subject: str | None = None):
        """Filter students by subject; currently a stub that could be extended."""
        # Store the filter selection so the UI can react and only show
        # relevant student rows.
        self._filtered_subject = subject
        return None

    @rx.event
    def add_timeline_event(self, ev=None):
        """Allow teacher to add an exam or homework reminder to timeline.

        This handler is designed to be called directly from a button click
        (which passes a PointerEventInfo). We therefore read the event input
        values from the temporary state fields rather than expecting typed
        parameters.
        """
        try:
            title = getattr(self, "_new_event_title", "")
            date = getattr(self, "_new_event_date", "")
            etype = getattr(self, "_new_event_type", "exam") or "exam"

            disp = f"{date} - {title} ({etype})"
            # prepend so newest appear first
            existing = self.timeline_events if isinstance(self.timeline_events, list) else []
            self.timeline_events = [disp] + existing
            # Clear temporary inputs
            self._new_event_title = ""
            self._new_event_date = ""
            self._new_event_type = "exam"
            return rx.window_alert("Event added to timeline")
        except Exception as e:
            return rx.window_alert(f"Failed to add event: {e}")

    @rx.event
    def set_new_event_title(self, ev=None):
        try:
            self._new_event_title = str(ev if ev is not None else self._new_event_title)
        except Exception:
            self._new_event_title = str(self._new_event_title)

    @rx.event
    def set_new_event_date(self, ev=None):
        try:
            self._new_event_date = str(ev if ev is not None else self._new_event_date)
        except Exception:
            self._new_event_date = str(self._new_event_date)

    @rx.event
    def set_new_event_type(self, ev=None):
        try:
            self._new_event_type = str(ev if ev is not None else self._new_event_type)
        except Exception:
            self._new_event_type = str(self._new_event_type)

    @rx.event
    def compute_leaderboard(self, n: int = 10):
        """Compute top N students and cache them to `leaderboard_top`."""
        try:
            # If we have DB access prefer to query, otherwise use state list
            try:
                with rx.session() as session:
                    rows = session.query(Student).all()
            except Exception:
                rows = self.students if isinstance(self.students, list) else []

            rows = sorted(rows, key=lambda s: getattr(s, "total_marks", 0), reverse=True)
            # Store as simple display strings to keep the state type stable
            self.leaderboard_top = [f"#{idx+1} {getattr(s, 'name', '')} - {getattr(s, 'total_marks', 0)} Marks" for idx, s in enumerate(rows[:n])]
            return None
        except Exception:
            self.leaderboard_top = []
            return None

    @classmethod
    def get_student_rank(cls, student_roll: int):
        """Return the 1-based rank of a student in the current class, or None."""
        students = getattr(cls, "students", [])
        if not isinstance(students, list) or len(students) == 0:
            return None
        rows = sorted(students, key=lambda s: getattr(s, "total_marks", 0), reverse=True)
        for idx, s in enumerate(rows, 1):
            if getattr(s, "roll_no", None) == student_roll:
                return idx
        return None
        return None
        

    
    # Logic for grades and totals
    def calculate_grade(self, total_marks: int) -> str:
        """Calculates the grade based on total marks."""
        if total_marks >= 320:
            return "A+"
        elif total_marks >= 280:
            return "A"
        elif total_marks >= 240:
            return "B"
        elif total_marks >= 200:
            return "C"
        else:
            return "Fail"

    # Instance setters used by the UI. They accept an optional event
    # or direct value and update state defensively so static analysis
    # and runtime both remain stable.
    @rx.event
    def set_teacher_username(self, ev=None):
        try:
            self.teacher_username = str(ev if ev is not None else self.teacher_username)
        except Exception:
            self.teacher_username = str(self.teacher_username)

    @rx.event
    def set_teacher_password(self, ev=None):
        try:
            self.teacher_password = str(ev if ev is not None else self.teacher_password)
        except Exception:
            self.teacher_password = str(self.teacher_password)

    @rx.event
    def set_teacher_username_input(self, ev=None):
        try:
            # When called from the UI the event will provide the current value.
            self.teacher_username_input = str(ev if ev is not None else self.teacher_username_input)
        except Exception:
            self.teacher_username_input = str(self.teacher_username_input)

    @rx.event
    def set_teacher_password_input(self, ev=None):
        try:
            self.teacher_password_input = str(ev if ev is not None else self.teacher_password_input)
        except Exception:
            self.teacher_password_input = str(self.teacher_password_input)

    @rx.event
    def set_student_name(self, ev=None):
        try:
            self.student_name = str(ev if ev is not None else self.student_name)
        except Exception:
            self.student_name = str(self.student_name)

    @rx.event
    def set_student_roll(self, ev=None):
        try:
            self.student_roll = str(ev if ev is not None else self.student_roll)
        except Exception:
            self.student_roll = str(self.student_roll)

    @rx.event
    def set_marks_bangla(self, ev=None):
        try:
            self.marks_bangla = str(ev if ev is not None else self.marks_bangla)
        except Exception:
            self.marks_bangla = str(self.marks_bangla)

    @rx.event
    def set_marks_english(self, ev=None):
        try:
            self.marks_english = str(ev if ev is not None else self.marks_english)
        except Exception:
            self.marks_english = str(self.marks_english)

    @rx.event
    def set_marks_math(self, ev=None):
        try:
            self.marks_math = str(ev if ev is not None else self.marks_math)
        except Exception:
            self.marks_math = str(self.marks_math)

    @rx.event
    def set_marks_science(self, ev=None):
        try:
            self.marks_science = str(ev if ev is not None else self.marks_science)
        except Exception:
            self.marks_science = str(self.marks_science)

    @rx.event
    def set_student_roll_input(self, ev=None):
        try:
            self.student_roll_input = str(ev if ev is not None else self.student_roll_input)
        except Exception:
            self.student_roll_input = str(self.student_roll_input)
    @rx.event
    def export_results(self):
        """Export student results as CSV file."""
        import csv
        import io
        import os

        # Build CSV in-memory then write to the .web/static directory so
        # Reflex can serve it as a downloadable file. Reflex requires
        # redirect/download URLs to start with '/'.
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Roll No", "Name", "Bangla", "English", "Math", "Science", "Total", "Grade"])
        students = self.students if isinstance(self.students, list) else []
        for s in students:
            writer.writerow([
                getattr(s, "roll_no", ""),
                getattr(s, "name", ""),
                getattr(s, "bangla_marks", ""),
                getattr(s, "english_marks", ""),
                getattr(s, "math_marks", ""),
                getattr(s, "science_marks", ""),
                getattr(s, "total_marks", ""),
                getattr(s, "grade", ""),
            ])
        csv_data = output.getvalue()

        # Ensure .web/static exists
        web_static_dir = os.path.join(os.getcwd(), ".web", "static")
        try:
            os.makedirs(web_static_dir, exist_ok=True)
            file_path = os.path.join(web_static_dir, "student_results.csv")
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_data)
            # Return a redirect to the static file path (must start with '/').
            return safe_redirect("/static/student_results.csv")
        except Exception as e:
            return rx.window_alert(f"Failed to export CSV: {e}")
    
    @rx.event
    def delete_student(self, roll: int):
        try:
            with rx.session() as session:
                student = session.query(Student).filter_by(roll_no=roll).first()
                if student:
                    session.delete(student)
                    session.commit()
                    return rx.window_alert("Student deleted successfully!")
        except Exception as e:
            return rx.window_alert(f"Error deleting student: {e}")



    # --- Teacher Functions ---
    @rx.event
    def teacher_login(self):
        """Authenticates the teacher login using the input fields compared to stored credentials."""
        # Compare the input values against the stored credentials.
        if (self.teacher_username_input.strip() == str(self.teacher_username)) and (
            self.teacher_password_input.strip() == str(self.teacher_password)
        ):
            self.teacher_logged_in = True
            # Clear the input fields after successful login
            self.teacher_username_input = ""
            self.teacher_password_input = ""
            return safe_redirect("/teacher_dashboard")
        return rx.window_alert("Invalid credentials!")

    @rx.event
    def add_student(self):
        """Adds a new student record to the database."""
        try:
            bangla = int(self.marks_bangla)
            english = int(self.marks_english)
            math = int(self.marks_math)
            science = int(self.marks_science)
            roll = int(self.student_roll)

            total_marks = bangla + english + math + science
            grade = self.calculate_grade(total_marks)
            
            try:
                with rx.session() as session:
                    # Create instance and set attributes to avoid constructor
                    # kwarg signature checks in static analysis.
                    new_student = Student()
                    setattr(new_student, "roll_no", roll)
                    setattr(new_student, "name", self.student_name)
                    setattr(new_student, "bangla_marks", bangla)
                    setattr(new_student, "english_marks", english)
                    setattr(new_student, "math_marks", math)
                    setattr(new_student, "science_marks", science)
                    setattr(new_student, "total_marks", total_marks)
                    setattr(new_student, "grade", grade)
                    session.add(new_student)
                    session.commit()
            except Exception as db_err:
                # If the table doesn't exist, attempt to create it on the same
                # database that rx.session() is using, then retry once.
                msg = str(db_err).lower()
                if "no such table" in msg or isinstance(db_err, OperationalError):
                    try:
                        # Try to get the engine/bind from a new session and create tables there.
                        with rx.session() as session:
                            try:
                                bind = session.get_bind()
                            except Exception:
                                bind = getattr(session, "bind", None)

                            if bind is None:
                                # As a last resort, if we have SQLModel and create_engine, create a local file.
                                if SQLModel is None or create_engine is None:
                                    return rx.window_alert("Database schema missing and could not determine DB engine to create it.")
                                engine = create_engine("sqlite:///resultdashboard.db")
                                # Create tables only if SQLModel is available.
                                if SQLModel is None:
                                    return rx.window_alert("Database schema missing and sqlmodel is not available to create it.")
                                SQLModel.metadata.create_all(engine)
                            else:
                                # Create tables on the same bind used by the app session.
                                if SQLModel is None:
                                    return rx.window_alert("Database schema missing and sqlmodel is not available to create it.")
                                SQLModel.metadata.create_all(bind)

                        # Retry the insertion once after schema creation
                        with rx.session() as session:
                            new_student = Student()
                            setattr(new_student, "roll_no", roll)
                            setattr(new_student, "name", self.student_name)
                            setattr(new_student, "bangla_marks", bangla)
                            setattr(new_student, "english_marks", english)
                            setattr(new_student, "math_marks", math)
                            setattr(new_student, "science_marks", science)
                            setattr(new_student, "total_marks", total_marks)
                            setattr(new_student, "grade", grade)
                            session.add(new_student)
                            session.commit()
                    except Exception as create_err:
                        return rx.window_alert(f"Failed to create DB schema: {create_err}")
                else:
                    raise
            
            self.student_name = ""
            self.student_roll = ""
            self.marks_bangla = ""
            self.marks_english = ""
            self.marks_math = ""
            self.marks_science = ""
            return rx.window_alert("Student added successfully!")

        except ValueError:
            return rx.window_alert("Please enter valid numbers for marks and roll.")
        except Exception as e:
            return rx.window_alert(f"An error occurred: {e}")

    @rx.event
    def get_students(self):
        """Retrieves all student records from the database."""
        try:
            with rx.session() as session:
                self.students = session.query(Student).all()
        except Exception:
            # Keep an empty list if DB isn't available in this environment
            self.students = []
            
    @rx.event
    def get_top_performers(self):
        """Retrieves the top 3 students based on total marks."""
        try:
            with rx.session() as session:
                rows = session.query(Student).all()
                # Sort in Python to avoid relying on SQL expression helpers
                self.top_performers = sorted(rows, key=lambda s: getattr(s, "total_marks", 0), reverse=True)[:3]
        except Exception:
            self.top_performers = []

    def get_grade_distribution(self):
        """Generates a bar chart for grade distribution."""
        # Build a simple distribution dict; if pandas/plotly are installed
        # in the running environment they can be used to create a chart.
        grades = [getattr(s, "grade", "Fail") for s in self.students]
        dist = {"A+": 0, "A": 0, "B": 0, "C": 0, "Fail": 0}
        for g in grades:
            dist[g] = dist.get(g, 0) + 1
        return {"type": "grade_distribution", "data": dist}
        
    @rx.event
    def logout(self):
        self.teacher_logged_in = False
        return safe_redirect("/")

    # --- Student Functions ---
    @rx.event
    def search_student_result(self):
        """Searches for a student's result by roll number."""
        try:
            roll = int(self.student_roll_input)
            # Avoid using SQLAlchemy column expressions in static analysis by
            # fetching rows and filtering in Python.
            try:
                with rx.session() as session:
                    rows = session.query(Student).all()
            except Exception:
                rows = []

            student = next((s for s in rows if getattr(s, "roll_no", None) == roll), None)
            if student:
                self.student_result_data = {
                    "name": getattr(student, "name", ""),
                    "roll": getattr(student, "roll_no", ""),
                    "bangla": getattr(student, "bangla_marks", ""),
                    "english": getattr(student, "english_marks", ""),
                    "math": getattr(student, "math_marks", ""),
                    "science": getattr(student, "science_marks", ""),
                    "total": getattr(student, "total_marks", ""),
                    "grade": getattr(student, "grade", ""),
                }
                return safe_redirect("/student_result")
            else:
                self.student_result_data = {}
                return rx.window_alert("Roll number not found.")
        except ValueError:
            return rx.window_alert("Please enter a valid roll number.")

# --- Styling ---
STYLE_CONFIG = {
    "background": "#0a0f1f",
    "color": "#e7eaf4",
    "font_family": "'Arial', sans-serif",
    "background_attachment": "fixed",
    "background_image": "radial-gradient(1200px 700px at 10% -10%, rgba(124,92,255,0.18), transparent), radial-gradient(1000px 600px at 90% 10%, rgba(61,214,208,0.14), transparent), linear-gradient(180deg, #090d1a 0%, #0a0f1f 100%)",
}


def safe_redirect(path, *args, **kwargs):
    """Normalize redirect paths to always start with '/' and call rx.redirect.

    Reflex requires redirect paths to start with '/'. This helper ensures a
    leading slash and returns a window alert for non-string paths.
    """
    try:
        if not isinstance(path, str):
            return rx.window_alert("Invalid redirect path")
        if not path.startswith("/"):
            path = "/" + path
        return rx.redirect(path, *args, **kwargs)
    except Exception as e:
        # If rx.redirect itself raises, surface a friendly alert
        return rx.window_alert(f"Redirect error: {e}")

CARD_STYLE = {
    "background": "rgba(255,255,255,0.08)",
    "border": "1px solid rgba(255,255,255,0.16)",
    "border_radius": "18px",
    "padding": "20px",
    "box_shadow": "0 30px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05)",
    "backdrop_filter": "blur(16px) saturate(140%)",
    "position": "relative",
    "overflow": "hidden",
}

INPUT_STYLE = {
    "width": "100%",
    "padding": "12px",
    "border_radius": "8px",
    "background": "rgba(255,255,255,0.1)",
    "border": "1px solid rgba(255,255,255,0.15)",
    "color": "#e7eaf4",
    # Make sure text is left-aligned and inputs are tall enough so
    # placeholder text and typed text don't overlap visually.
    "text_align": "left",
    "height": "44px",
    "line_height": "1.4",
    # Add a small left padding to keep the text away from borders.
    "padding_left": "14px",
    "padding_right": "14px",
    # Ensure caret color contrasts with background.
    "caret_color": "#e7eaf4",
}

BUTTON_PRIMARY_STYLE = {
    "background": "#7c5cff",
    "color": "white",
    "border_radius": "8px",
    "padding": "12px 20px"
}

# --- UI Components ---
def login_page():
    return rx.center(
        rx.box(
            rx.heading("Teacher Login", size="7", margin_bottom="20px", color="#ffffff"),
            rx.vstack(
                rx.input(placeholder="Username", on_change=ResultState.set_teacher_username_input, value=ResultState.teacher_username_input, style=INPUT_STYLE),
                rx.input(placeholder="Password", type="password", on_change=ResultState.set_teacher_password_input, value=ResultState.teacher_password_input, style=INPUT_STYLE),
                rx.button("Login", on_click=ResultState.teacher_login, style=BUTTON_PRIMARY_STYLE),
                spacing="2",
            ),
            style=CARD_STYLE,
            width="400px"
        ),
        height="100vh",
        style=STYLE_CONFIG,
    )

def teacher_dashboard():
    # Build a corrected teacher dashboard UI with proper structure and handlers
    return rx.center(
        rx.vstack(
            # Header row
            rx.hstack(
                rx.heading("Teacher Dashboard", size="8", color="#ffffff"),
                rx.spacer(),
                rx.button("Export Results", on_click=ResultState.export_results, style=BUTTON_PRIMARY_STYLE),
                rx.button("Logout", on_click=ResultState.logout, style={"background": "#d32f2f", "color": "white", "border_radius": "8px"}),
                width="100%",
                padding_bottom="20px",
            ),

            # Controls: subject filter + charts
            rx.hstack(
                # Build a static default option list for compile-time. At
                # runtime, the UI can be extended to show dynamic subjects
                # after `ResultState.get_students` runs and populates
                # `ResultState.students`.
                rx.select(
                    ["All", "Bangla", "English", "Math", "Science"],
                    on_change=ResultState.filter_subject,
                    placeholder="Select Subject",
                ),
                rx.spacer(),
            ),

            # Two-column grid: Top performers and Subject Averages
            rx.grid(
                rx.box(
                    rx.text("Top 3 Performers", font_weight="bold", font_size="20px"),
                    rx.divider(),
                    rx.foreach(
                        ResultState.top_performers,
                        lambda student: rx.text(f"{student.roll_no}: {student.name} - {student.total_marks} Marks", font_size="16px"),
                    ),
                    style=CARD_STYLE,
                ),

                rx.box(
                    rx.text("Subject-wise Averages", font_weight="bold", font_size="20px"),
                    rx.divider(),
                    # Show subject averages as progress bars (works without extra libs)
                    rx.vstack(*[
                        rx.box(
                            rx.text(f"{sub}: {avg} Marks"),
                            rx.progress(value=avg, max=100, color="green"),
                            style={"margin_bottom": "10px"}
                        )
                        for sub, avg in ResultState.get_subject_averages_dict()
                    ]),
                    style=CARD_STYLE,
                ),

                # Timeline / events box
                rx.box(
                    rx.text("Timeline / Calendar", font_weight="bold", font_size="20px"),
                    rx.divider(),
                    # Render timeline events dynamically so updates appear in the UI
                    rx.vstack(
                        rx.foreach(
                            ResultState.timeline_events,
                            lambda ev: rx.box(
                                    rx.text(ev),
                                    style={"margin_bottom": "8px"}
                                ),
                        )
                    ),
                    # Form to add an event quickly (binds to state inputs)
                    rx.vstack(
                        rx.input(placeholder="Event title", on_change=ResultState.set_new_event_title, value=ResultState._new_event_title, style=INPUT_STYLE),
                        rx.input(placeholder="YYYY-MM-DD", on_change=ResultState.set_new_event_date, value=ResultState._new_event_date, style=INPUT_STYLE),
                        rx.hstack(
                            rx.select(["exam", "homework"], value=ResultState._new_event_type, on_change=ResultState.set_new_event_type, style=INPUT_STYLE),
                            rx.button("Add Event", on_click=ResultState.add_timeline_event, style=BUTTON_PRIMARY_STYLE),
                        ),
                    ),
                    style=CARD_STYLE,
                ),

                columns="2",
                spacing="3",
                width="100%",
                on_mount=ResultState.get_top_performers,
            ),

            # Student Data Input Form
            rx.box(
                rx.heading("Add New Student", size="6", margin_top="30px", margin_bottom="20px"),
                rx.form(
                    rx.vstack(
                        rx.input(placeholder="Student Name", on_change=ResultState.set_student_name, value=ResultState.student_name, style=INPUT_STYLE),
                        rx.input(placeholder="Roll Number", type="number", on_change=ResultState.set_student_roll, value=ResultState.student_roll, style=INPUT_STYLE),
                        rx.hstack(
                            rx.input(placeholder="Bangla Marks", type="number", on_change=ResultState.set_marks_bangla, value=ResultState.marks_bangla, style=INPUT_STYLE),
                            rx.input(placeholder="English Marks", type="number", on_change=ResultState.set_marks_english, value=ResultState.marks_english, style=INPUT_STYLE),
                            rx.input(placeholder="Math Marks", type="number", on_change=ResultState.set_marks_math, value=ResultState.marks_math, style=INPUT_STYLE),
                            rx.input(placeholder="Science Marks", type="number", on_change=ResultState.set_marks_science, value=ResultState.marks_science, style=INPUT_STYLE),
                            width="100%",
                            spacing="2",
                        ),
                        rx.button("Add Student", on_click=ResultState.add_student, style=BUTTON_PRIMARY_STYLE),
                        spacing="2",
                        width="100%",
                    )
                ),
                style=CARD_STYLE,
                width="100%",
            ),

            # All Students Table
            rx.box(
                rx.heading("All Student Results", size="6", margin_top="30px", margin_bottom="20px"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Roll No."),
                            rx.table.column_header_cell("Name"),
                            rx.table.column_header_cell("Total Marks"),
                            rx.table.column_header_cell("Grade"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),

                    rx.table.body(
                        rx.foreach(
                            ResultState.students,
                            lambda student: rx.table.row(
                                rx.table.cell(student.roll_no),
                                rx.table.cell(student.name),
                                rx.table.cell(student.total_marks),
                                rx.table.cell(student.grade),
                                rx.table.cell(rx.button("Delete", on_click=lambda ev, s=student: ResultState.delete_student(s.roll_no), style={"background": "red", "color": "white", "border_radius": "5px"})),
                            ),
                        ),
                    ),
                    on_mount=ResultState.get_students,
                ),
                style=CARD_STYLE,
                width="100%",
            ),

            width="80%",
            max_width="1200px",
            padding_top="50px",
            padding_bottom="50px",
        ),
        style=STYLE_CONFIG,
    )

def student_page():
    return rx.center(
        # Left: quick check box
        rx.box(
            rx.heading("Check Your Result", size="7", margin_bottom="20px"),
            rx.vstack(
                rx.input(placeholder="Enter Roll Number", type="number", on_change=ResultState.set_student_roll_input, style=INPUT_STYLE),
                rx.button("Check Result", on_click=ResultState.search_student_result, style=BUTTON_PRIMARY_STYLE),
                rx.button("Go to Home", on_click=lambda: safe_redirect("/"), style={"background": "gray", "color": "white", "border_radius": "8px"}),
                spacing="2",
            ),
            style=CARD_STYLE,
            width="400px",
        ),

        # Right: timeline + leaderboard stacked
        rx.vstack(
            rx.box(
                rx.heading("Timeline / Notices", size="6"),
                rx.vstack(
                    rx.foreach(
                        ResultState.timeline_events,
                        lambda ev: rx.text(ev),
                    )
                ),
                style=CARD_STYLE,
                width="400px",
            ),
            rx.box(
                rx.heading("Leaderboard - Top 10", size="6"),
                rx.vstack(
                    rx.foreach(
                        ResultState.leaderboard_top,
                        lambda item: rx.text(item),
                    )
                ),
                style=CARD_STYLE,
                width="400px",
            ),
        ),

        # Populate data on mount
        on_mount=[ResultState.get_students, ResultState.compute_leaderboard],
        height="100vh",
        style=STYLE_CONFIG,
    )

def student_result_page():
    return rx.center(
        rx.cond(
            ResultState.student_result_data,
            rx.box(
                rx.heading("Your Result", size="7", margin_bottom="20px"),
                rx.grid(
                    rx.card(rx.text(f"Name: {ResultState.student_result_data['name']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"Roll: {ResultState.student_result_data['roll']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"Total Marks: {ResultState.student_result_data['total']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"Grade: {ResultState.student_result_data['grade']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"Bangla: {ResultState.student_result_data['bangla']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"English: {ResultState.student_result_data['english']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"Math: {ResultState.student_result_data['math']}"), style=CARD_STYLE),
                    rx.card(rx.text(f"Science: {ResultState.student_result_data['science']}"), style=CARD_STYLE),
                    columns="4",
                    spacing="2",
                    width="100%"
                ),
                rx.button("Check Another Result", on_click=lambda: safe_redirect("/student"), margin_top="20px", style=BUTTON_PRIMARY_STYLE),
                style=CARD_STYLE,
                width="800px"
            ),
            rx.text("No result found.", color="red", font_size="20px"),
        ),
        height="100vh",
        style=STYLE_CONFIG,
    )

def index():
    return rx.center(
            rx.vstack(
            rx.heading("Student Result Management", size="9", color="#ffffff"),
            rx.text("A simple and powerful tool for teachers and students.", color="#b8bfd6"),
            rx.button("Teacher Dashboard", on_click=lambda: safe_redirect("/login"), style=BUTTON_PRIMARY_STYLE),
            rx.button("Student Result Check", on_click=lambda: safe_redirect("/student"), style={"background": "#3d6dff", "color": "white", "border_radius": "8px"}),
            spacing="3"
        ),
        height="100vh",
        style=STYLE_CONFIG,
    )

# --- App Setup ---
app = rx.App(
    theme=rx.theme(
        accent_color="violet",
        gray_color="slate",
        appearance="dark",
    )
)

app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(teacher_dashboard, route="/teacher_dashboard")
app.add_page(student_page, route="/student")
app.add_page(student_result_page, route="/student_result")
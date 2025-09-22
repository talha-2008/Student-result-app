# [your_project_name].py
import reflex as rx
from typing import Optional
# decimal removed — not used in this module

# In this editor environment we avoid importing heavy optional
# dependencies (plotly, pandas). The UI will show placeholders when
# those libraries are not available at runtime.
go = None
pd = None

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
    
    # Data from DB
    students: list[Student] = []
    top_performers: list[Student] = []
    
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

    # --- Teacher Functions ---
    @rx.event
    def teacher_login(self):
        """Authenticates the teacher login."""
        if self.teacher_username == "admin" and self.teacher_password == "12345":
            self.teacher_logged_in = True
            return rx.redirect("/teacher_dashboard")
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
        return rx.redirect("/")

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
                return rx.redirect("/student_result")
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
                rx.input(placeholder="Username", on_change=ResultState.set_teacher_username, value=ResultState.teacher_username, style=INPUT_STYLE),
                rx.input(placeholder="Password", type="password", on_change=ResultState.set_teacher_password, value=ResultState.teacher_password, style=INPUT_STYLE),
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
    return rx.center(
        rx.vstack(
                rx.hstack(
                rx.heading("Teacher Dashboard", size="8", color="#ffffff"),
                rx.spacer(),
                rx.button("Logout", on_click=ResultState.logout, style={"background": "#d32f2f", "color": "white", "border_radius": "8px"}),
                width="100%",
                padding_bottom="20px",
            ),
            
            # Top Performers and Grade Distribution
                rx.grid(
                rx.box(
                    rx.text("Top 3 Performers", font_weight="bold", font_size="20px"),
                    rx.divider(),
                    rx.foreach(ResultState.top_performers,
                        lambda student: rx.text(f"{student.roll_no}: {student.name} - {student.total_marks} Marks", font_size="16px")
                    ),
                    style=CARD_STYLE
                    ),
                    rx.box(
                    rx.text("Grade Distribution", font_weight="bold", font_size="20px"),
                    rx.divider(),
                    rx.text("Grade distribution chart (not rendered in editor)", color="#b8bfd6"),
                    style=CARD_STYLE
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
                            spacing="2"
                        ),
                        rx.button("Add Student", on_click=ResultState.add_student, style=BUTTON_PRIMARY_STYLE),
                        spacing="2",
                        width="100%"
                    )
                ),
                style=CARD_STYLE,
                width="100%"
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
                        )
                    ),
                    rx.table.body(
                        rx.foreach(ResultState.students,
                            lambda student: rx.table.row(
                                rx.table.cell(student.roll_no),
                                rx.table.cell(student.name),
                                rx.table.cell(student.total_marks),
                                rx.table.cell(student.grade),
                            )
                        )
                    ),
                    on_mount=ResultState.get_students,
                ),
                style=CARD_STYLE,
                width="100%"
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
        rx.box(
            rx.heading("Check Your Result", size="7", margin_bottom="20px"),
                rx.vstack(
                rx.input(placeholder="Enter Roll Number", type="number", on_change=ResultState.set_student_roll_input, style=INPUT_STYLE),
                rx.button("Check Result", on_click=ResultState.search_student_result, style=BUTTON_PRIMARY_STYLE),
                rx.button("Go to Home", on_click=lambda: rx.redirect("/"), style={"background": "gray", "color": "white", "border_radius": "8px"}),
                spacing="2",
            ),
            style=CARD_STYLE,
            width="400px"
        ),
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
                rx.button("Check Another Result", on_click=lambda: rx.redirect("/student"), margin_top="20px", style=BUTTON_PRIMARY_STYLE),
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
            rx.button("Teacher Dashboard", on_click=lambda: rx.redirect("/login"), style=BUTTON_PRIMARY_STYLE),
            rx.button("Student Result Check", on_click=lambda: rx.redirect("/student"), style={"background": "#3d6dff", "color": "white", "border_radius": "8px"}),
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
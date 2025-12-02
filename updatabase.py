import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from sqlite3 import Error
import sys

# --- Configuration & Database Logic ---
DATABASE_NAME = "scholarship_awards.db"
TAX_RATE = 0.05 # 5% tax for the Class Rep deduction (vi)

# List of Nigerian States for the dropdown menu (Case is normalized to UPPER)
NIGERIAN_STATES = [
    "ABIA", "ADAMAWA", "AKWA IBOM", "ANAMBRA", "BAUCHI", "BAYELSA", "BENUE", "BORNO", 
    "CROSS RIVER", "DELTA", "EBONYI", "EDO", "EKITI", "ENUGU", "GOMBE", "IMO", 
    "JIGAWA", "KADUNA", "KANO", "KATSINA", "KEBBI", "KOGI", "KWARA", "LAGOS", 
    "NASARAWA", "NIGER", "OGUN", "ONDO", "OSUN", "OYO", "PLATEAU", "RIVERS", 
    "SOKOTO", "TARABA", "YOBE", "ZAMFARA", "FCT"
]

class ScholarshipManager:
    """
    Manages the SQLite database connection, student records, 
    and scholarship award calculations.
    """
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.connect_db()
        self.create_table()

    def connect_db(self):
        """Establishes a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
        except Error as e:
            messagebox.showerror("Database Error", f"Error connecting to database: {e}")
            sys.exit(1)
            
    def close_db(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def create_table(self):
        """Creates the 'students' table if it doesn't exist."""
        sql_create_students_table = """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            state TEXT NOT NULL,
            well_dressed INTEGER NOT NULL,
            well_behaved INTEGER NOT NULL
        );
        """
        try:
            c = self.conn.cursor()
            c.execute(sql_create_students_table)
            self.conn.commit()
        except Error as e:
            messagebox.showerror("Database Error", f"Error creating table: {e}")

    def insert_student(self, name, gender, state, dressed, behaved):
        """Inserts a new student record into the database."""
        sql = """
        INSERT INTO students (name, gender, state, well_dressed, well_behaved)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            c = self.conn.cursor()
            # Normalize case before insertion for consistent calculation
            c.execute(sql, (name.strip(), gender.strip().capitalize(), state.strip().upper(), dressed, behaved))
            self.conn.commit()
            return c.lastrowid
        except Error as e:
            messagebox.showerror("Database Error", f"Error inserting student: {e}")
            return None

    def calculate_award(self, student):
        """
        Calculates the total award and deduction for a single student.
        Returns total_award and deduction.
        """
        # --- Scholarship Award Attributes (Naira) ---
        AWARD_ATTRIBUTES = {
            "well_dressed": 10000,   # (i)
            "general_gift": 20000,   # (ii) - Base Award
            "well_behaved": 5000,    # (iii)
            "osun_state": 15000,     # (iv)
            "female_monthly": 1000   # (v) 
        }

        total_award = AWARD_ATTRIBUTES["general_gift"] # Base award (ii)
        
        if student.get('well_dressed'):
            total_award += AWARD_ATTRIBUTES["well_dressed"] # (i)
            
        if student.get('well_behaved'):
            total_award += AWARD_ATTRIBUTES["well_behaved"] # (iii)

        # State and Gender comparison must match the case used in insertion (UPPER/Capitalized)
        if student.get('state') == 'OSUN':
            total_award += AWARD_ATTRIBUTES["osun_state"] # (iv)

        if student.get('gender') == 'Female':
            total_award += AWARD_ATTRIBUTES["female_monthly"] # (v)
            
        # --- Deduction (vi) ---
        deduction = total_award * TAX_RATE
        
        return {
            "total_award": total_award,
            "deduction": deduction,
            "net_payment": total_award - deduction
        }

    def get_all_scholarship_data(self):
        """Retrieves all students for reporting."""
        sql = "SELECT id, name, gender, state, well_dressed, well_behaved FROM students"
        try:
            c = self.conn.cursor()
            c.execute(sql)
            rows = c.fetchall()
            
            students_data = []
            for row in rows:
                student = {
                    'id': row[0],
                    'name': row[1],
                    'gender': row[2],
                    'state': row[3],
                    # Raw 1/0 from DB is fine for dictionary keys in 'calculate_award'
                    'well_dressed': row[4], 
                    'well_behaved': row[5]
                }
                results = self.calculate_award(student)
                student.update(results)
                students_data.append(student)
                
            return students_data

        except Error as e:
            messagebox.showerror("Database Error", f"Error fetching data: {e}")
            return []

# --- Tkinter GUI Application ---

class ScholarshipApp:
    def __init__(self, master, manager):
        self.manager = manager
        self.master = master
        master.title("Professor's Scholarship Manager")
        master.configure(bg="#e0f7fa") # Light Blue background

        # Variables for Input Fields
        self.name_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="Male") # Default gender
        self.state_var = tk.StringVar(value=NIGERIAN_STATES[0]) # Default state
        self.dressed_var = tk.IntVar()
        self.behaved_var = tk.IntVar()

        # --- Frames ---
        self.input_frame = tk.LabelFrame(master, text="Student Details", padx=10, pady=10, bg="#ffffff")
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.report_frame = tk.LabelFrame(master, text="Scholarship Report", padx=10, pady=10, bg="#ffffff")
        self.report_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=3)


        # --- Input Widgets ---
        self._create_input_widgets()
        
        # --- Report Widgets ---
        self._create_report_widgets()
        
        # Initial population of the report
        self.update_report()


    def _create_input_widgets(self):
        """Creates all entry, dropdown, radio button, and button widgets."""
        
        # 1. Name
        tk.Label(self.input_frame, text="Name:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(self.input_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=5)

        # 2. Gender (Radio Buttons)
        tk.Label(self.input_frame, text="Gender:", bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)
        tk.Radiobutton(self.input_frame, text="Male", variable=self.gender_var, value="Male", bg="#ffffff").grid(row=1, column=1, sticky="w")
        tk.Radiobutton(self.input_frame, text="Female", variable=self.gender_var, value="Female", bg="#ffffff").grid(row=2, column=1, sticky="w")
        
        # 3. State (Dropdown Menu)
        tk.Label(self.input_frame, text="State:", bg="#ffffff").grid(row=3, column=0, sticky="w", pady=5)
        state_menu = tk.OptionMenu(self.input_frame, self.state_var, *NIGERIAN_STATES)
        state_menu.config(width=25)
        state_menu.grid(row=3, column=1, pady=5, padx=5)

        # 4. Well Dressed (Checkbox - 1/0)
        tk.Label(self.input_frame, text="Well Dressed (₦10k):", bg="#ffffff").grid(row=4, column=0, sticky="w", pady=5)
        tk.Checkbutton(self.input_frame, variable=self.dressed_var, onvalue=1, offvalue=0, bg="#ffffff").grid(row=4, column=1, sticky="w")
        
        # 5. Well Behaved (Checkbox - 1/0)
        tk.Label(self.input_frame, text="Well Behaved (₦5k):", bg="#ffffff").grid(row=5, column=0, sticky="w", pady=5)
        tk.Checkbutton(self.input_frame, variable=self.behaved_var, onvalue=1, offvalue=0, bg="#ffffff").grid(row=5, column=1, sticky="w")

        # 6. Save Button
        save_button = tk.Button(self.input_frame, text="Save Student & Calculate Award", command=self.save_student, bg="#4CAF50", fg="white", font=('Arial', 10, 'bold'))
        save_button.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")

        # 7. Exit Button
        exit_button = tk.Button(self.input_frame, text="Exit", command=self.master.quit, bg="#f44336", fg="white", font=('Arial', 10, 'bold'))
        exit_button.grid(row=7, column=0, columnspan=2, pady=5, sticky="ew")

    def _create_report_widgets(self):
        """Creates the display area for the report."""
        
        # Using a Text widget to display a formatted report
        self.report_text = tk.Text(self.report_frame, height=20, width=80, font=('Courier', 10), relief=tk.FLAT)
        self.report_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.report_text.config(state=tk.DISABLED) # Make read-only

    def save_student(self):
        """
        Gathers input data, inserts into the database, and updates the report.
        """
        name = self.name_var.get()
        gender = self.gender_var.get()
        state = self.state_var.get()
        dressed = self.dressed_var.get()
        behaved = self.behaved_var.get()

        if not name or not gender or not state:
            messagebox.showwarning("Input Error", "Please fill in all mandatory fields (Name, Gender, State).")
            return

        # Insert student and get ID
        student_id = self.manager.insert_student(name, gender, state, dressed, behaved)
        
        if student_id:
            messagebox.showinfo("Success", f"Student '{name}' saved successfully (ID: {student_id}).")
            self.update_report()
            # Clear inputs after success
            self.name_var.set("")
            self.dressed_var.set(0)
            self.behaved_var.set(0)

    def update_report(self):
        """
        Fetches all data, formats the report, and displays it in the Text widget.
        """
        students_data = self.manager.get_all_scholarship_data()
        
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        
        if not students_data:
            self.report_text.insert(tk.END, "No student records found. Add a student to begin.")
            self.report_text.config(state=tk.DISABLED)
            return

        # Generate report content
        lines = []
        lines.append("=" * 110)
        lines.append(" " * 30 + "🏆 PROFESSOR'S SCHOLARSHIP AWARD REPORT 🏆")
        lines.append("-" * 110)
        
        # Header (Widths adjusted for visibility)
        lines.append(f"| {'ID':<3} | {'Name':<18} | {'State':<10} | {'Total Award (₦ - Money Paid)':<26} | {'Tax Deduction (₦)':<18} | {'Net Payment (₦)':<18} |")
        lines.append("-" * 110)
        
        total_award_sum = 0
        total_deduction_sum = 0
        total_net_sum = 0
        
        for student in students_data:
            total_award_sum += student['total_award']
            total_deduction_sum += student['deduction']
            total_net_sum += student['net_payment']
            
            lines.append(
                f"| {student['id']:<3} | {student['name']:<18} | {student['state']:<10} | "
                f"₦{student['total_award']:<25,.2f} | ₦{student['deduction']:<17,.2f} | ₦{student['net_payment']:<17,.2f} |"
            )

        lines.append("=" * 110)
        lines.append(f"| {'GRAND TOTALS':<35} | ₦{total_award_sum:<25,.2f} | ₦{total_deduction_sum:<17,.2f} | ₦{total_net_sum:<17,.2f} |")
        lines.append("=" * 110)
        lines.append(f"\nTAX/DEDUCTION RATE: {TAX_RATE * 100:.0f}% paid to the Class Representative.")

        self.report_text.insert(tk.END, "\n".join(lines))
        self.report_text.config(state=tk.DISABLED)


# --- Main Execution ---
if __name__ == '__main__':
    # Initialize database manager
    db_manager = ScholarshipManager(DATABASE_NAME)
    
    # Initialize Tkinter root window
    root = tk.Tk()
    app = ScholarshipApp(root, db_manager)
    
    # Run the Tkinter main loop
    root.mainloop()
    
    # Cleanup database connection upon exit
    db_manager.close_db()

"""
BlackRoad HR System - Human Resources and Employee Management Platform
SQLite-backed HR platform: employees, departments, time tracking, PTO.
"""

import sqlite3
import json
import uuid
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
from calendar import monthrange


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "onleave"
    TERMINATED = "terminated"


class PTOType(str, Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"


class PTOStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Department:
    id: str
    name: str
    head_id: Optional[str] = None
    budget: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Employee:
    id: str
    name: str
    email: str
    department: str
    title: str
    manager_id: Optional[str]
    salary: float
    hire_date: str
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    phone: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TimeEntry:
    id: str
    employee_id: str
    date: str
    hours: float
    project: str
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PTORequest:
    id: str
    employee_id: str
    type: PTOType
    start_date: str
    end_date: str
    status: PTOStatus = PTOStatus.PENDING
    reason: str = ""
    approved_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

class HRDatabase:
    def __init__(self, db_path: str = "hr.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS departments (
                    id          TEXT PRIMARY KEY,
                    name        TEXT UNIQUE NOT NULL,
                    head_id     TEXT,
                    budget      REAL DEFAULT 0,
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS employees (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    email       TEXT UNIQUE NOT NULL,
                    department  TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    manager_id  TEXT,
                    salary      REAL NOT NULL DEFAULT 0,
                    hire_date   TEXT NOT NULL,
                    status      TEXT DEFAULT 'active',
                    phone       TEXT DEFAULT '',
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS time_entries (
                    id          TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL REFERENCES employees(id),
                    date        TEXT NOT NULL,
                    hours       REAL NOT NULL,
                    project     TEXT NOT NULL,
                    notes       TEXT DEFAULT '',
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pto_requests (
                    id          TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL REFERENCES employees(id),
                    type        TEXT NOT NULL,
                    start_date  TEXT NOT NULL,
                    end_date    TEXT NOT NULL,
                    status      TEXT DEFAULT 'pending',
                    reason      TEXT DEFAULT '',
                    approved_by TEXT,
                    created_at  TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees(department);
                CREATE INDEX IF NOT EXISTS idx_time_emp ON time_entries(employee_id);
                CREATE INDEX IF NOT EXISTS idx_pto_emp ON pto_requests(employee_id);
            """)


# ---------------------------------------------------------------------------
# HR Service
# ---------------------------------------------------------------------------

class HRSystem:
    """Main HR service."""

    def __init__(self, db_path: str = "hr.db"):
        self.db = HRDatabase(db_path)
        self.conn = self.db.conn

    # -----------------------------------------------------------------------
    # Department operations
    # -----------------------------------------------------------------------

    def create_department(self, name: str, budget: float = 0.0) -> Department:
        dept = Department(id=str(uuid.uuid4()), name=name, budget=budget)
        with self.conn:
            self.conn.execute(
                "INSERT INTO departments (id, name, budget, created_at) VALUES (?,?,?,?)",
                (dept.id, dept.name, dept.budget, dept.created_at),
            )
        return dept

    def get_department(self, name: str) -> Optional[Department]:
        row = self.conn.execute(
            "SELECT * FROM departments WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return None
        return Department(id=row["id"], name=row["name"], head_id=row["head_id"],
                          budget=row["budget"], created_at=row["created_at"])

    def list_departments(self) -> List[Department]:
        rows = self.conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
        return [Department(id=r["id"], name=r["name"], head_id=r["head_id"],
                           budget=r["budget"], created_at=r["created_at"]) for r in rows]

    # -----------------------------------------------------------------------
    # Employee operations
    # -----------------------------------------------------------------------

    def hire(
        self,
        name: str,
        email: str,
        department: str,
        title: str,
        salary: float,
        manager_id: Optional[str] = None,
        phone: str = "",
        hire_date: Optional[str] = None,
    ) -> Employee:
        """Onboard a new employee."""
        # Auto-create department if missing
        if not self.get_department(department):
            self.create_department(department)
        emp = Employee(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            department=department,
            title=title,
            manager_id=manager_id,
            salary=salary,
            hire_date=hire_date or date.today().isoformat(),
            phone=phone,
        )
        with self.conn:
            self.conn.execute(
                """INSERT INTO employees
                   (id, name, email, department, title, manager_id, salary,
                    hire_date, status, phone, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (emp.id, emp.name, emp.email, emp.department, emp.title,
                 emp.manager_id, emp.salary, emp.hire_date, emp.status.value,
                 emp.phone, emp.created_at),
            )
        return emp

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        row = self.conn.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        return self._row_to_employee(row) if row else None

    def get_employee_by_email(self, email: str) -> Optional[Employee]:
        row = self.conn.execute(
            "SELECT * FROM employees WHERE email = ?", (email,)
        ).fetchone()
        return self._row_to_employee(row) if row else None

    def list_employees(
        self,
        department: Optional[str] = None,
        status: Optional[EmployeeStatus] = None,
    ) -> List[Employee]:
        query = "SELECT * FROM employees WHERE 1=1"
        params: List[Any] = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_employee(r) for r in rows]

    def transfer(self, employee_id: str, new_department: str, new_title: str) -> Optional[Employee]:
        """Transfer employee to a different department/role."""
        if not self.get_employee(employee_id):
            return None
        if not self.get_department(new_department):
            self.create_department(new_department)
        with self.conn:
            self.conn.execute(
                "UPDATE employees SET department = ?, title = ? WHERE id = ?",
                (new_department, new_title, employee_id),
            )
        return self.get_employee(employee_id)

    def terminate(self, employee_id: str, reason: str = "") -> Optional[Employee]:
        """Terminate an employee."""
        emp = self.get_employee(employee_id)
        if not emp:
            return None
        with self.conn:
            self.conn.execute(
                "UPDATE employees SET status = 'terminated' WHERE id = ?",
                (employee_id,),
            )
        return self.get_employee(employee_id)

    def update_salary(self, employee_id: str, new_salary: float) -> Optional[Employee]:
        if not self.get_employee(employee_id):
            return None
        with self.conn:
            self.conn.execute(
                "UPDATE employees SET salary = ? WHERE id = ?",
                (new_salary, employee_id),
            )
        return self.get_employee(employee_id)

    def set_on_leave(self, employee_id: str) -> Optional[Employee]:
        with self.conn:
            self.conn.execute(
                "UPDATE employees SET status = 'onleave' WHERE id = ?",
                (employee_id,),
            )
        return self.get_employee(employee_id)

    def return_from_leave(self, employee_id: str) -> Optional[Employee]:
        with self.conn:
            self.conn.execute(
                "UPDATE employees SET status = 'active' WHERE id = ?",
                (employee_id,),
            )
        return self.get_employee(employee_id)

    # -----------------------------------------------------------------------
    # Time tracking
    # -----------------------------------------------------------------------

    def log_time(
        self,
        employee_id: str,
        hours: float,
        project: str,
        entry_date: Optional[str] = None,
        notes: str = "",
    ) -> TimeEntry:
        if not self.get_employee(employee_id):
            raise ValueError(f"Employee {employee_id} not found")
        if hours <= 0 or hours > 24:
            raise ValueError("Hours must be between 0 and 24")
        entry = TimeEntry(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            date=entry_date or date.today().isoformat(),
            hours=hours,
            project=project,
            notes=notes,
        )
        with self.conn:
            self.conn.execute(
                "INSERT INTO time_entries (id, employee_id, date, hours, project, notes, created_at) VALUES (?,?,?,?,?,?,?)",
                (entry.id, entry.employee_id, entry.date, entry.hours,
                 entry.project, entry.notes, entry.created_at),
            )
        return entry

    def get_time_entries(
        self,
        employee_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[TimeEntry]:
        query = "SELECT * FROM time_entries WHERE employee_id = ?"
        params: List[Any] = [employee_id]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date DESC"
        rows = self.conn.execute(query, params).fetchall()
        return [TimeEntry(id=r["id"], employee_id=r["employee_id"], date=r["date"],
                          hours=r["hours"], project=r["project"], notes=r["notes"],
                          created_at=r["created_at"]) for r in rows]

    def hours_by_project(self, employee_id: str) -> Dict[str, float]:
        rows = self.conn.execute(
            "SELECT project, SUM(hours) as total FROM time_entries WHERE employee_id = ? GROUP BY project",
            (employee_id,),
        ).fetchall()
        return {r["project"]: r["total"] for r in rows}

    # -----------------------------------------------------------------------
    # PTO management
    # -----------------------------------------------------------------------

    def request_pto(
        self,
        employee_id: str,
        pto_type: PTOType,
        start_date: str,
        end_date: str,
        reason: str = "",
    ) -> PTORequest:
        if not self.get_employee(employee_id):
            raise ValueError(f"Employee {employee_id} not found")
        req = PTORequest(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            type=pto_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
        )
        with self.conn:
            self.conn.execute(
                """INSERT INTO pto_requests
                   (id, employee_id, type, start_date, end_date, status, reason, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (req.id, req.employee_id, req.type.value, req.start_date,
                 req.end_date, req.status.value, req.reason, req.created_at),
            )
        return req

    def approve_pto(self, pto_id: str, approver_id: Optional[str] = None) -> Optional[PTORequest]:
        req = self.get_pto_request(pto_id)
        if not req:
            return None
        with self.conn:
            self.conn.execute(
                "UPDATE pto_requests SET status = 'approved', approved_by = ? WHERE id = ?",
                (approver_id, pto_id),
            )
        return self.get_pto_request(pto_id)

    def deny_pto(self, pto_id: str) -> Optional[PTORequest]:
        req = self.get_pto_request(pto_id)
        if not req:
            return None
        with self.conn:
            self.conn.execute(
                "UPDATE pto_requests SET status = 'denied' WHERE id = ?", (pto_id,)
            )
        return self.get_pto_request(pto_id)

    def get_pto_request(self, pto_id: str) -> Optional[PTORequest]:
        row = self.conn.execute(
            "SELECT * FROM pto_requests WHERE id = ?", (pto_id,)
        ).fetchone()
        if not row:
            return None
        return PTORequest(id=row["id"], employee_id=row["employee_id"],
                          type=PTOType(row["type"]), start_date=row["start_date"],
                          end_date=row["end_date"], status=PTOStatus(row["status"]),
                          reason=row["reason"], approved_by=row["approved_by"],
                          created_at=row["created_at"])

    def list_pto_requests(
        self,
        employee_id: Optional[str] = None,
        status: Optional[PTOStatus] = None,
    ) -> List[PTORequest]:
        query = "SELECT * FROM pto_requests WHERE 1=1"
        params: List[Any] = []
        if employee_id:
            query += " AND employee_id = ?"
            params.append(employee_id)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        rows = self.conn.execute(query, params).fetchall()
        return [self.get_pto_request(r["id"]) for r in rows]

    # -----------------------------------------------------------------------
    # Analytics
    # -----------------------------------------------------------------------

    def payroll_summary(self, month: Optional[str] = None) -> Dict[str, Any]:
        """Monthly payroll breakdown by department."""
        rows = self.conn.execute(
            """SELECT department, COUNT(*) as headcount, SUM(salary) as total_salary
               FROM employees WHERE status = 'active' GROUP BY department"""
        ).fetchall()
        departments = {}
        total_payroll = 0.0
        total_headcount = 0
        for r in rows:
            monthly = r["total_salary"] / 12
            departments[r["department"]] = {
                "headcount": r["headcount"],
                "annual_salary": round(r["total_salary"], 2),
                "monthly_payroll": round(monthly, 2),
            }
            total_payroll += monthly
            total_headcount += r["headcount"]
        return {
            "month": month or date.today().strftime("%Y-%m"),
            "total_headcount": total_headcount,
            "total_monthly_payroll": round(total_payroll, 2),
            "by_department": departments,
        }

    def org_chart(self) -> Dict[str, Any]:
        """Return hierarchical org chart as nested dict."""
        employees = self.list_employees(status=EmployeeStatus.ACTIVE)
        emp_map = {e.id: {"id": e.id, "name": e.name, "title": e.title,
                          "department": e.department, "reports": []}
                   for e in employees}
        roots = []
        for e in employees:
            if e.manager_id and e.manager_id in emp_map:
                emp_map[e.manager_id]["reports"].append(emp_map[e.id])
            else:
                roots.append(emp_map[e.id])
        return {"org": roots}

    def headcount_by_department(self) -> Dict[str, int]:
        rows = self.conn.execute(
            "SELECT department, COUNT(*) as count FROM employees WHERE status='active' GROUP BY department"
        ).fetchall()
        return {r["department"]: r["count"] for r in rows}

    def tenure_report(self) -> List[Dict[str, Any]]:
        """Return employees sorted by tenure (longest first)."""
        today = date.today().isoformat()
        rows = self.conn.execute(
            "SELECT id, name, department, title, hire_date FROM employees WHERE status='active' ORDER BY hire_date ASC"
        ).fetchall()
        result = []
        for r in rows:
            try:
                hire = date.fromisoformat(r["hire_date"])
                days = (date.today() - hire).days
                years = round(days / 365.25, 1)
            except Exception:
                days = 0
                years = 0
            result.append({
                "name": r["name"],
                "department": r["department"],
                "title": r["title"],
                "hire_date": r["hire_date"],
                "tenure_years": years,
            })
        return result

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _row_to_employee(self, row: sqlite3.Row) -> Employee:
        return Employee(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            department=row["department"],
            title=row["title"],
            manager_id=row["manager_id"],
            salary=row["salary"],
            hire_date=row["hire_date"],
            status=EmployeeStatus(row["status"]),
            phone=row["phone"],
            created_at=row["created_at"],
        )

    def close(self) -> None:
        self.conn.close()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo() -> None:
    import tempfile, os
    db_file = tempfile.mktemp(suffix=".db")
    hr = HRSystem(db_file)

    print("\n=== Hiring Employees ===")
    hr.create_department("Engineering", budget=1_200_000)
    hr.create_department("Sales", budget=800_000)

    alice = hr.hire("Alice Chen", "alice@co.com", "Engineering", "Senior Engineer", 140_000)
    bob = hr.hire("Bob Martinez", "bob@co.com", "Engineering", "Engineer", 120_000, manager_id=alice.id)
    carol = hr.hire("Carol Lee", "carol@co.com", "Sales", "Account Executive", 90_000)
    print(f"  Hired: {alice.name}, {bob.name}, {carol.name}")

    print("\n=== Transfer & Promotion ===")
    hr.transfer(carol.id, "Sales", "Senior Account Executive")
    print(f"  Transferred Carol to Senior AE")

    print("\n=== Logging Time ===")
    hr.log_time(alice.id, 8, "BlackRoad-Platform", notes="Core module")
    hr.log_time(alice.id, 6, "BlackRoad-Platform")
    hr.log_time(bob.id, 8, "API-Refactor")
    print("  Time entries logged")

    print("\n=== PTO Request ===")
    pto = hr.request_pto(alice.id, PTOType.VACATION, "2025-07-01", "2025-07-07", "Summer break")
    approved = hr.approve_pto(pto.id, approver_id=alice.id)
    print(f"  PTO status: {approved.status.value}")

    print("\n=== Payroll Summary ===")
    summary = hr.payroll_summary()
    print(f"  Total monthly payroll: ${summary['total_monthly_payroll']:,.2f}")
    print(f"  Total headcount: {summary['total_headcount']}")

    print("\n=== Org Chart ===")
    chart = hr.org_chart()
    for node in chart["org"]:
        print(f"  {node['name']} ({node['title']}) — {len(node['reports'])} reports")

    hr.close()
    os.unlink(db_file)
    print("\n✓ Demo complete")


if __name__ == "__main__":
    demo()

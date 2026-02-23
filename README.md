# BlackRoad HR System

> Human Resources and Employee Management Platform — SQLite-backed, zero-dependency Python.

## Features

- **Employees** — hire, transfer, terminate, salary management
- **Departments** — auto-creation, budget tracking, headcount
- **Time Tracking** — log hours per project, per employee
- **PTO Management** — request, approve/deny vacation/sick/personal leave
- **Analytics** — payroll summary, org chart, tenure report

## Quick Start

```python
from hr_system import HRSystem, PTOType

hr = HRSystem("company.db")

# Hire employees
alice = hr.hire("Alice Chen", "alice@co.com", "Engineering", "Senior Engineer", 140_000)
bob = hr.hire("Bob Martinez", "bob@co.com", "Engineering", "Engineer", 120_000,
              manager_id=alice.id)

# Transfer
hr.transfer(bob.id, "Platform", "Senior Engineer")

# Log time
hr.log_time(alice.id, 8, "BlackRoad-Platform", notes="Core module")

# PTO
req = hr.request_pto(alice.id, PTOType.VACATION, "2025-07-01", "2025-07-07")
hr.approve_pto(req.id)

# Analytics
print(hr.payroll_summary())
print(hr.org_chart())
```

## Running Tests

```bash
pip install pytest
pytest test_hr_system.py -v
```

<!-- BlackRoad SEO Enhanced -->

# ulackroad hr system

> Part of **[BlackRoad OS](https://blackroad.io)** — Sovereign Computing for Everyone

[![BlackRoad OS](https://img.shields.io/badge/BlackRoad-OS-ff1d6c?style=for-the-badge)](https://blackroad.io)
[![BlackRoad-Foundation](https://img.shields.io/badge/Org-BlackRoad-Foundation-2979ff?style=for-the-badge)](https://github.com/BlackRoad-Foundation)

**ulackroad hr system** is part of the **BlackRoad OS** ecosystem — a sovereign, distributed operating system built on edge computing, local AI, and mesh networking by **BlackRoad OS, Inc.**

### BlackRoad Ecosystem
| Org | Focus |
|---|---|
| [BlackRoad OS](https://github.com/BlackRoad-OS) | Core platform |
| [BlackRoad OS, Inc.](https://github.com/BlackRoad-OS-Inc) | Corporate |
| [BlackRoad AI](https://github.com/BlackRoad-AI) | AI/ML |
| [BlackRoad Hardware](https://github.com/BlackRoad-Hardware) | Edge hardware |
| [BlackRoad Security](https://github.com/BlackRoad-Security) | Cybersecurity |
| [BlackRoad Quantum](https://github.com/BlackRoad-Quantum) | Quantum computing |
| [BlackRoad Agents](https://github.com/BlackRoad-Agents) | AI agents |
| [BlackRoad Network](https://github.com/BlackRoad-Network) | Mesh networking |

**Website**: [blackroad.io](https://blackroad.io) | **Chat**: [chat.blackroad.io](https://chat.blackroad.io) | **Search**: [search.blackroad.io](https://search.blackroad.io)

---


> HR and employee management platform

Part of the [BlackRoad OS](https://blackroad.io) ecosystem — [BlackRoad-Foundation](https://github.com/BlackRoad-Foundation)

---

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

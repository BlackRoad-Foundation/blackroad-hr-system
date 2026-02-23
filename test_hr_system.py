"""pytest tests for BlackRoad HR System"""
import pytest
from hr_system import HRSystem, EmployeeStatus, PTOType, PTOStatus


@pytest.fixture
def hr(tmp_path):
    h = HRSystem(str(tmp_path / "test.db"))
    yield h
    h.close()


def test_hire_employee(hr):
    e = hr.hire("Alice", "alice@test.com", "Eng", "Engineer", 120_000)
    assert e.id
    assert e.status == EmployeeStatus.ACTIVE

def test_department_auto_created(hr):
    hr.hire("Bob", "bob@test.com", "NewDept", "Mgr", 100_000)
    dept = hr.get_department("NewDept")
    assert dept is not None

def test_transfer(hr):
    e = hr.hire("Carol", "carol@test.com", "Sales", "AE", 80_000)
    updated = hr.transfer(e.id, "Marketing", "Marketing Manager")
    assert updated.department == "Marketing"
    assert updated.title == "Marketing Manager"

def test_terminate(hr):
    e = hr.hire("Dave", "dave@test.com", "HR", "Recruiter", 75_000)
    terminated = hr.terminate(e.id, "Layoff")
    assert terminated.status == EmployeeStatus.TERMINATED

def test_update_salary(hr):
    e = hr.hire("Eve", "eve@test.com", "Finance", "Analyst", 70_000)
    updated = hr.update_salary(e.id, 80_000)
    assert updated.salary == 80_000

def test_log_time(hr):
    e = hr.hire("Frank", "frank@test.com", "Eng", "Dev", 100_000)
    entry = hr.log_time(e.id, 8, "ProjectX")
    assert entry.hours == 8
    assert entry.project == "ProjectX"

def test_log_time_invalid_hours(hr):
    e = hr.hire("Grace", "grace@test.com", "Eng", "Dev", 100_000)
    with pytest.raises(ValueError):
        hr.log_time(e.id, 25, "Overwork")

def test_request_and_approve_pto(hr):
    e = hr.hire("Henry", "henry@test.com", "HR", "Manager", 90_000)
    req = hr.request_pto(e.id, PTOType.VACATION, "2025-07-01", "2025-07-05")
    assert req.status == PTOStatus.PENDING
    approved = hr.approve_pto(req.id)
    assert approved.status == PTOStatus.APPROVED

def test_deny_pto(hr):
    e = hr.hire("Iris", "iris@test.com", "HR", "Staff", 60_000)
    req = hr.request_pto(e.id, PTOType.SICK, "2025-08-01", "2025-08-02")
    denied = hr.deny_pto(req.id)
    assert denied.status == PTOStatus.DENIED

def test_payroll_summary(hr):
    hr.hire("Jack", "jack@test.com", "Finance", "CFO", 200_000)
    hr.hire("Jill", "jill@test.com", "Finance", "Analyst", 80_000)
    summary = hr.payroll_summary()
    assert summary["total_headcount"] == 2
    assert summary["total_monthly_payroll"] > 0

def test_org_chart(hr):
    mgr = hr.hire("Manager", "mgr@test.com", "Eng", "VP", 180_000)
    hr.hire("Report1", "r1@test.com", "Eng", "Dev", 100_000, manager_id=mgr.id)
    chart = hr.org_chart()
    assert len(chart["org"]) >= 1

def test_list_by_department(hr):
    hr.hire("K", "k@test.com", "Sales", "AE", 70_000)
    hr.hire("L", "l@test.com", "Eng", "Dev", 100_000)
    sales = hr.list_employees(department="Sales")
    assert len(sales) == 1

"""Scheduler-agent tools: mock inspection windows, bookings, and reminders."""

import hashlib
from datetime import date, timedelta

from strands import tool

from . import config
from .kb import extract_case


def _all_inspections():
    out = []
    for j in __import__("permit_pal.kb", fromlist=["jurisdictions"]).jurisdictions():
        for pid, p in j["project_types"].items():
            for ins in p["inspections"]:
                out.append((j["id"], pid, ins))
    return out


def _match_inspection(inspection_type: str):
    text = (inspection_type or "").lower()
    for jid, pid, ins in _all_inspections():
        if ins["id"] in text or ins["label"].lower() in text:
            return jid, pid, ins
    # default: footing inspection for the canonical demo case
    j, pid = extract_case("austin-tx deck-addition")
    return j["id"], pid, j["project_types"][pid]["inspections"][0]


def _windows():
    base = date.today()
    slots = []
    for day_offset in (3, 4, 5):
        d = (base + timedelta(days=day_offset)).isoformat()
        slots.append(f"{d} 09:00-11:00")
        slots.append(f"{d} 13:00-15:00")
    return slots


def _get_inspection_windows(inspection_type: str) -> str:
    config.log_call("get_inspection_windows", {"inspection_type": inspection_type})
    jid, pid, ins = _match_inspection(inspection_type)
    slots = _windows()
    lines = [
        f"INSPECTION WINDOWS — {ins['label']} ({jid} / {pid})",
        f"Available windows: {len(slots)}",
    ]
    lines += [f"{i}. {s}" for i, s in enumerate(slots, 1)]
    return "\n".join(lines)


def _book_inspection(inspection_type: str, window: str) -> str:
    config.log_call("book_inspection", {"inspection_type": inspection_type, "window": window})
    jid, pid, ins = _match_inspection(inspection_type)
    code = "PP-" + hashlib.sha1(f"{jid}|{pid}|{ins['id']}|{window}".encode()).hexdigest()[:6].upper()
    return (
        "INSPECTION BOOKED (mock booking — demo)\n"
        f"Confirmation: {code}\n"
        f"Inspection: {ins['label']}\n"
        f"Window: {window}\n"
        "Note: in production this books against the jurisdiction inspection portal."
    )


def _add_deadline_reminder(label: str, due_date: str) -> str:
    config.log_call("add_deadline_reminder", {"label": label, "due_date": due_date})
    config.REMINDERS.append({"label": label, "due_date": due_date})
    return (
        "REMINDER SET (mock — demo)\n"
        f"Label: {label}\n"
        f"Due: {due_date}\n"
        f"Total reminders: {len(config.REMINDERS)}"
    )


@tool
def get_inspection_windows(inspection_type: str) -> str:
    """Get available inspection time windows for an inspection type (e.g. 'footing inspection'). Use this before booking an inspection."""
    return _get_inspection_windows(inspection_type)


@tool
def book_inspection(inspection_type: str, window: str) -> str:
    """Book an inspection in a chosen window. Use this after the homeowner approves the schedule. This is a mock booking in the demo."""
    return _book_inspection(inspection_type, window)


@tool
def add_deadline_reminder(label: str, due_date: str) -> str:
    """Set a deadline reminder (label + YYYY-MM-DD due date). Use this to track permit deadlines and inspection prep."""
    return _add_deadline_reminder(label, due_date)

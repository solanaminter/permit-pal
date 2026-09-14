"""Docs-agent tools: checklist assembly, application-packet generation, validation."""

import os
import re
from datetime import date

from strands import tool

from . import config
from .kb import extract_case, find_project, get_jurisdiction

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")


def _case(jurisdiction: str, project_type: str):
    j = get_jurisdiction(jurisdiction) or extract_case(f"{jurisdiction} {project_type}")[0]
    pid = project_type if project_type in j["project_types"] else find_project(j, project_type)
    if pid is None:
        pid = next(iter(j["project_types"]))
    return j, pid


def _assemble_checklist(jurisdiction: str, project_type: str) -> str:
    config.log_call("assemble_checklist", {"jurisdiction": jurisdiction, "project_type": project_type})
    j, pid = _case(jurisdiction, project_type)
    p = j["project_types"][pid]
    lines = [
        f"PERMIT CHECKLIST — {j['name']} / {p['label']}",
        f"Checklist items: {len(p['required_documents'])}",
        "",
    ]
    for i, d in enumerate(p["required_documents"], 1):
        lines.append(f"[ ] {i}. {d}")
    lines += [
        "",
        "Inspections to schedule:",
    ]
    for ins in p["inspections"]:
        lines.append(f"  * {ins['label']} — {ins['when']}")
    return "\n".join(lines)


def _generate_application_packet(jurisdiction: str, project_type: str, homeowner_name: str) -> str:
    config.log_call(
        "generate_application_packet",
        {"jurisdiction": jurisdiction, "project_type": project_type, "homeowner_name": homeowner_name},
    )
    j, pid = _case(jurisdiction, project_type)
    p = j["project_types"][pid]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fname = f"permit-packet-{j['id']}-{pid}.md"
    path = os.path.join(OUTPUT_DIR, fname)

    req_lines = "\n".join(f"- [{r['id']}] {r['title']}: {r['detail']}" for r in p["requirements"])
    doc_lines = "\n".join(f"- [ ] {d}" for d in p["required_documents"])
    ins_lines = "\n".join(f"- {ins['label']} — {ins['when']}" for ins in p["inspections"])
    trailer = "<!--REQUIRED-DOCS:" + "|||".join(p["required_documents"]) + "-->"

    packet = f"""# Permit Application Packet (SAMPLE — demo data)

**Homeowner:** {homeowner_name}
**Jurisdiction:** {j['name']} — {j['authority']}
**Project:** {p['label']}
**Generated:** {date.today().isoformat()} (Permit Pal demo)

## 1. Requirements ({len(p['requirements'])})
{req_lines}

## 2. Document checklist ({len(p['required_documents'])})
{doc_lines}

## 3. Fees (sample estimates)
- Plan review: {p['fees']['plan_review']}
- Permit: {p['fees']['permit']}
- Example total: {p['fees']['example_total']}

## 4. Inspections
{ins_lines}

## 5. Submission
- Portal: {j['portal']}
- Typical timeline: {p['typical_timeline']}
- Status: READY FOR HOMEOWNER SIGNATURE (demo — not actually submitted)

{trailer}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(packet)
    return (
        "APPLICATION PACKET ASSEMBLED\n"
        f"Packet file: {path}\n"
        f"Sections: 5 (requirements, checklist, fees, inspections, submission)\n"
        f"Checklist items: {len(p['required_documents'])}\n"
        f"Homeowner: {homeowner_name}"
    )


def _validate_packet(packet_text: str) -> str:
    config.log_call("validate_packet", {"packet_chars": len(packet_text)})
    m = re.search(r"<!--REQUIRED-DOCS:(.*?)-->", packet_text or "", re.DOTALL)
    required = [d for d in (m.group(1).split("|||") if m else []) if d.strip()]
    body = (packet_text or "").lower()
    missing = [d for d in required if d.lower() not in body]
    if not required:
        return "PACKET VALIDATION — INCONCLUSIVE\nNo required-documents trailer found in packet text."
    if missing:
        return (
            "PACKET VALIDATION — FAIL\n"
            f"Missing {len(missing)} of {len(required)} required documents:\n"
            + "\n".join(f"- {d}" for d in missing)
        )
    return (
        "PACKET VALIDATION — PASS\n"
        f"All {len(required)} required documents present in the packet.\n"
        "Packet is complete and ready for homeowner signature."
    )


@tool
def assemble_checklist(jurisdiction: str, project_type: str) -> str:
    """Assemble the document checklist for a permit application from the looked-up requirements. Use this when the homeowner needs to know exactly which documents to prepare."""
    return _assemble_checklist(jurisdiction, project_type)


@tool
def generate_application_packet(jurisdiction: str, project_type: str, homeowner_name: str) -> str:
    """Generate the full permit application packet file (requirements, checklist, fees, inspections, submission notes). Use this after the checklist is assembled and approved."""
    return _generate_application_packet(jurisdiction, project_type, homeowner_name)


@tool
def validate_packet(packet_text: str) -> str:
    """Validate a generated application packet against its required-documents list. Use this as a final completeness check before submission."""
    return _validate_packet(packet_text)

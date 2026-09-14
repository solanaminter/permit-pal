"""Research-agent tools: permit-requirement lookup over the bundled KB."""

from strands import tool

from . import config
from .kb import find_jurisdiction, find_project, get_jurisdiction, jurisdictions


def _lookup_permit_requirements(jurisdiction: str, project_type: str) -> str:
    config.log_call(
        "lookup_permit_requirements", {"jurisdiction": jurisdiction, "project_type": project_type}
    )
    j = find_jurisdiction(jurisdiction) or get_jurisdiction("austin-tx")
    pid = find_project(j, project_type) or next(iter(j["project_types"]))
    p = j["project_types"][pid]

    lines = [
        f"PERMIT REQUIREMENTS — {j['name']} / {p['label']}",
        f"Authority: {j['authority']}",
        f"Requirements found: {len(p['requirements'])}",
        "",
    ]
    for r in p["requirements"]:
        lines.append(f"- [{r['id']}] {r['title']}: {r['detail']}")
    lines += ["", f"Required documents ({len(p['required_documents'])}):"]
    for d in p["required_documents"]:
        lines.append(f"  * {d}")
    lines += ["", "Inspections:"]
    for ins in p["inspections"]:
        lines.append(f"  * {ins['label']} — {ins['when']}")
    lines += [
        "",
        f"Fees (sample): plan review {p['fees']['plan_review']}; permit {p['fees']['permit']}.",
        f"Typical timeline: {p['typical_timeline']}",
    ]
    return "\n".join(lines)


def _list_jurisdictions() -> str:
    config.log_call("list_jurisdictions", {})
    lines = ["COVERED JURISDICTIONS (sample seed data):"]
    for j in jurisdictions():
        pts = ", ".join(p["label"] for p in j["project_types"].values())
        lines.append(f"- {j['name']} ({j['authority']}): {pts}")
    return "\n".join(lines)


def _get_project_types(jurisdiction: str) -> str:
    config.log_call("get_project_types", {"jurisdiction": jurisdiction})
    j = find_jurisdiction(jurisdiction) or get_jurisdiction("austin-tx")
    lines = [f"SUPPORTED PROJECT TYPES — {j['name']}:"]
    for pid, p in j["project_types"].items():
        lines.append(f"- {p['label']} (id: {pid})")
    return "\n".join(lines)


@tool
def lookup_permit_requirements(jurisdiction: str, project_type: str) -> str:
    """Look up the building-permit requirements, required documents, fees, and inspections for a project type in a jurisdiction. Use this when the homeowner asks what a permit requires."""
    return _lookup_permit_requirements(jurisdiction, project_type)


@tool
def list_jurisdictions() -> str:
    """List the jurisdictions (cities) covered by the permit knowledge base. Use this when the homeowner asks where or which cities are covered."""
    return _list_jurisdictions()


@tool
def get_project_types(jurisdiction: str) -> str:
    """List the project types supported for a jurisdiction. Use this when the homeowner asks what kinds of projects are supported."""
    return _get_project_types(jurisdiction)

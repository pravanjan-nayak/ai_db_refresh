try:
    # Preferred: dynamic reload support
    from workflows.sop_registry import load_sops
except Exception:
    load_sops = None

try:
    # Fallback if dynamic loader is not available
    from workflows.sop_registry import SOP_REGISTRY
except Exception:
    SOP_REGISTRY = []

from workflows.utils import read_file_content


def normalize_text(text: str) -> str:
    return " ".join(str(text).lower().strip().split())


def get_sop_registry():
    """
    Returns the latest SOP registry.
    If load_sops() exists, refresh on every call.
    Otherwise use SOP_REGISTRY loaded at startup.
    """
    if load_sops:
        try:
            return load_sops()
        except Exception:
            pass

    return SOP_REGISTRY


def match_sop(user_input: str):
    """
    Match user input against SOP keywords.

    Returns:
    {
        "matched": True/False,
        "route": "sop" or "reasoning",
        "task": sop_name or None,
        "title": sop_title or None,
        "confidence": float,
        "description": text,
        "content": sop_markdown or None
    }
    """
    question = normalize_text(user_input)
    sops = get_sop_registry()

    best_match = None
    best_score = 0

    for sop in sops:
        score = 0

        # 1) Match using keywords
        for keyword in sop.get("keywords", []):
            keyword_norm = normalize_text(keyword)

            if keyword_norm and keyword_norm in question:
                score += len(keyword_norm.split())

        # 2) Optional light match using name/title
        if score == 0:
            task_name = normalize_text(sop.get("name", ""))
            title = normalize_text(sop.get("title", ""))

            if task_name and task_name.replace("_", " ") in question:
                score += 1
            elif title and title in question:
                score += 1

        if score > best_score:
            best_score = score
            best_match = sop

    if best_match:
        content = read_file_content(best_match["file"])
        confidence = min(round(0.60 + (best_score * 0.08), 2), 0.99)

        return {
            "matched": True,
            "route": "sop",
            "task": best_match.get("name"),
            "title": best_match.get("title"),
            "confidence": confidence,
            "description": best_match.get("description"),
            "content": content
        }

    return {
        "matched": False,
        "route": "reasoning",
        "task": None,
        "title": None,
        "confidence": 0.0,
        "description": "No SOP matched",
        "content": None
    }
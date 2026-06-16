import os

SOP_DIR = os.path.join(os.path.dirname(__file__), "sops")


def load_sops():
    sop_list = []

    # If SOP folder does not exist, return empty list safely
    if not os.path.exists(SOP_DIR):
        print(f"SOP directory not found: {SOP_DIR}")
        return sop_list

    for file_name in os.listdir(SOP_DIR):
        if not file_name.endswith(".md"):
            continue

        file_path = os.path.join(SOP_DIR, file_name)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            name = None
            title = None
            keywords = []
            description = None

            for line in content.splitlines():
                line = line.strip()

                if line.startswith("# NAME:"):
                    name = line.replace("# NAME:", "").strip()

                elif line.startswith("# TITLE:"):
                    title = line.replace("# TITLE:", "").strip()

                elif line.startswith("# KEYWORDS:"):
                    raw_keywords = line.replace("# KEYWORDS:", "").strip()
                    keywords = [
                        k.strip().lower()
                        for k in raw_keywords.split(",")
                        if k.strip()
                    ]

                elif line.startswith("# DESCRIPTION:"):
                    description = line.replace("# DESCRIPTION:", "").strip()

            # Fallback values if metadata is missing
            if not name:
                name = os.path.splitext(file_name)[0]

            if not title:
                title = name.replace("_", " ").title()

            if not description:
                description = f"SOP loaded from {file_name}"

            sop_list.append({
                "name": name,
                "title": title,
                "file": file_path,
                "keywords": keywords,
                "description": description,
                "content": content
            })

        except Exception as e:
            print(f"Error loading SOP {file_name}: {e}")

    return sop_list


# Load once at startup
SOP_REGISTRY = load_sops()
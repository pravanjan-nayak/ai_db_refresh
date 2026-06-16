
#This utility file reads SOP content from markdown


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as exc:
        return f"Unable to read SOP file: {exc}"

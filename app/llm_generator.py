import os
from typing import Dict, List, Tuple


def generate_app_files(description: str, requirements: List[str] | None = None) -> List[Tuple[str, str]]:

    files: List[Tuple[str, str]] = []

    readme = f"""# Generated App

This app was generated automatically.

Description:

{description}

"""
    files.append(("README.md", readme))

    main_py = (
        "app.py",
        """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from generated app"}
""".lstrip(),
    )
    files.append(main_py)

    if requirements:
        req_txt = "\n".join(requirements) + "\n"
        files.append(("requirements.txt", req_txt))

    return files



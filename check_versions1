# Fixed check_all_versions.py
import sys

# Mapping package name to the actual name used in Python 'import'
packages = {
    "openai": "openai",
    "crewai": "crewai",
    "google-generativeai": "google.generativeai",
    "pydantic": "pydantic",
    "langchain": "langchain"
}

for pkg, import_name in packages.items():
    try:
        mod = __import__(import_name, fromlist=[''])
        version = getattr(mod, "__version__", "unknown")
        print(f"{pkg}: {version}")
    except ImportError:
        print(f"{pkg}: NOT INSTALLED")
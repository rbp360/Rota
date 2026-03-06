import sys
import subprocess

packages = ["openai", "crewai", "google-generativeai", "pydantic", "langchain"]

for pkg in packages:
    try:
        import_name = pkg.replace("-", "_")
        mod = __import__(import_name)
        version = getattr(mod, "__version__", "unknown")
        print(f"{pkg}: {version}")
    except ImportError:
        print(f"{pkg}: NOT INSTALLED")
    except Exception as e:
        print(f"{pkg}: Error checking version: {e}")

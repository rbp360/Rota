try:
    import crewai
    print(f"CrewAI Version: {crewai.__version__}")
except ImportError:
    print("CrewAI not installed in this environment.")

try:
    import google.generativeai as genai
    print(f"google-generativeai Version: {genai.__version__}")
except ImportError:
    print("google-generativeai not installed.")

try:
    import pydantic
    print(f"Pydantic Version: {pydantic.__version__}")
except ImportError:
    print("Pydantic not installed.")

try:
    import langchain
    print(f"LangChain Version: {langchain.__version__}")
except ImportError:
    print("LangChain not installed.")

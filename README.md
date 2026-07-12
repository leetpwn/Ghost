👻 Ghost

Your intelligent desktop companion.

Ghost is an AI-powered desktop assistant that understands natural language and performs actions on your computer through a modular, tool-based architecture.


Prerequisites
-------------
- Python 3.12
- Ollama installed
- qwen3:8b pulled

Backend

python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload

Desktop

python -m venv .venv
pip install -r requirements.txt
python main.py
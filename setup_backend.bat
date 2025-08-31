:: setup_backend.bat
cd backend

:: 1. Create virtual environment (if not exists)
python -m venv venv

:: 2. Activate virtual environment
call venv\Scripts\activate

:: 3. Upgrade pip and install build tools
python -m pip install --upgrade pip setuptools wheel

:: 4. Install dependencies (for pyproject.toml, pip will use PEP 517/518)
pip install .

:: 5. Install spaCy English model
python -m spacy download en_core_web_sm

echo Setup complete. To activate later, run: call backend\venv\Scripts\activate
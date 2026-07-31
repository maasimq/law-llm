@echo off
echo Starting Law LLM...
call .venv\Scripts\activate.bat
streamlit run app\app.py
pause
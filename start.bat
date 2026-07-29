@echo off
cd /d C:\Users\zz79\marketplace-ai
.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502 --server.headless true

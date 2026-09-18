@echo off
setlocal
echo ====================================================
echo Starting Simple RAG Pipeline CLI (Interactive Mode)
echo ====================================================
python src/cli.py --interactive %*
pause

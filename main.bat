@echo off
chcp 65001 >nul

REM バッチファイルのあるディレクトリに移動
cd /d "%~dp0"

echo fontTools のインストール中...
python -m pip install fonttools[woff] --force-reinstall --quiet
echo fontTools のインストールが完了しました

echo.
echo.

python main.py

echo.
pause

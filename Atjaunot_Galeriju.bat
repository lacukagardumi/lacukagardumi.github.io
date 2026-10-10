@echo off
chcp 65001 >nul
echo ============================================
echo   LĀČUKA GARDUMI - GALERIJAS ATJAUNINĀŠANA
echo ============================================
echo.
echo 1. Nolasa datus no galerija.csv un bildes no galerija/ mapes...
python update_gallery.py

echo.
echo 2. Saglabā izmaiņas un nosūta uz mājaslapu...
git add -A
git commit -m "Automātiski atjaunota galerija no galerija.csv"
git push origin main

echo.
echo ============================================
echo   GATAVS! Mājaslapa ir veiksmīgi atjaunināta!
echo ============================================
echo.
pause

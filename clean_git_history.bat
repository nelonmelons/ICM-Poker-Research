@echo off
echo This script will help clean up your git history and remove sensitive information
echo.
echo WARNING: This will rewrite your git history. Make sure you understand the implications.
echo Press Ctrl+C to abort, or
pause

REM Remove the API key from git history
echo Removing API key from Git history...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch 3.5finetuning.py" --prune-empty --tag-name-filter cat -- --all

REM Clean up the repository
echo Cleaning up the repository...
git reflog expire --expire=now --all
git gc --aggressive --prune=now

echo.
echo Your git history has been cleaned.
echo.
echo Now you can force push to the repository with:
echo git push --force origin main
echo.
pause 
git config --global alias.pr-message '!f() { /{프로젝트_절대경로}/.venv/bin/python /{프로젝트_절대경로}/main.py "$1"; }; f'

git pr-message {대상_브랜치}
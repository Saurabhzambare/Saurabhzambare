"""Refresh only the marked README block using public project commit metadata."""
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

OWNER = 'Saurabhzambare'
PROJECTS = {
    'instacart-sql-powerbi-analysis': 'Instacart retail analytics',
    'Real_Estate_Capstone': 'Real estate modelling',
    'gacl-public-disclosure-pipeline': 'Public-disclosure pipeline',
    'Mercedes-Benz-Greener-Manufacturing': 'Mercedes-Benz analysis',
    'discipline-system': 'Discipline System',
}
START = '<!-- RECENT-WORK:START -->'
END = '<!-- RECENT-WORK:END -->'
README = Path(__file__).resolve().parents[1] / 'README.md'


def fetch_commit(repo):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Saurabh-profile-updater'}
    token = os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    request = Request(f'https://api.github.com/repos/{OWNER}/{repo}/commits?per_page=1', headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)[0]


def cell(value):
    return escape(' '.join(value.split())).replace('|', '&#124;').replace('[', '&#91;').replace(']', '&#93;').replace('`', '&#96;').replace('*', '&#42;').replace('_', '&#95;')


def render(commits):
    rows = []
    for repo, commit in commits.items():
        sha = commit['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('Unexpected commit SHA')
        date = datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z', '+00:00')).astimezone(timezone.utc)
        title = commit['commit']['message'].splitlines()[0]
        if len(title) > 88:
            title = title[:85] + '…'
        link = f'https://github.com/{OWNER}/{repo}/commit/{sha}'
        row = f'| {date:%d %b %Y} | [{PROJECTS[repo]}](https://github.com/{OWNER}/{repo}) | [{cell(title)}]({link}) |'
        rows.append((date, repo, row))
    rows.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return '| Date (UTC) | Project | Latest update |\n|---|---|---|\n' + '\n'.join(row for _, _, row in rows)


def update_readme(text, block):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('README must contain exactly one pair of recent-work markers')
    before, rest = text.split(START)
    _, after = rest.split(END)
    return before + START + '\n' + block + '\n' + END + after


def main():
    # Complete every fetch before writing so failures preserve the previous block.
    commits = {repo: fetch_commit(repo) for repo in PROJECTS}
    original = README.read_text(encoding='utf-8')
    updated = update_readme(original, render(commits))
    if original != updated:
        README.write_text(updated, encoding='utf-8')
    print('Recent work checked for five public project repositories.')


if __name__ == '__main__':
    main()

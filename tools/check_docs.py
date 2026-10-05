"""Check local Markdown targets and prevent accidental workspace/secret leakage."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []
files = sorted(ROOT.rglob('*.md'))
for path in files:
    if '.git' in path.parts:
        continue
    text = path.read_text(encoding='utf-8')
    relative = path.relative_to(ROOT)
    if re.search(r'[\u0400-\u04ff]', text):
        errors.append(f'{relative}: repository prose must be English')
    if '/workspace/' in text:
        errors.append(f'{relative}: contains a local workspace path')
    if re.search(r'github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}', text):
        errors.append(f'{relative}: possible credential, redact before publishing')
    # Repository links use simple inline Markdown; code fences are not links.
    prose = re.sub(r'```.*?```', '', text, flags=re.S)
    for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', prose):
        if urlsplit(target).scheme or target.startswith('#'):
            continue
        destination = unquote(target.split('#', 1)[0]).strip('<>')
        if not destination:
            continue
        resolved = (path.parent / destination).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            errors.append(f'{relative}: missing/outside link {target}')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f'Checked local links and publication hygiene in {len(files)} Markdown files.')

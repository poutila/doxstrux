#!/usr/bin/env bash
# apply_four_edits.sh — focused patch for vNext
# 1) Front-matter: remove 'retain regex' wording and route regex func -> line-scanner (SSOT)
# 2) Attributes: delete DENIED_ATTR_PATTERNS; keep string-method checks only
# 3) CI/Tests: enforce single policy (no-regex-in-core); xfail legacy retained-regex tests
# 4) Slug: scrub stray 'import re' when unused
#
# Usage: bash apply_four_edits.sh [repo_root]
# Idempotent and conservative; creates timestamped backups of touched files.
set -euo pipefail

ROOT="${1:-.}"
TS="$(date +%Y%m%d_%H%M%S)"
BAK=".bak_four_edits_$TS"
mkdir -p "$BAK"

backup() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  mkdir -p "$BAK/$(dirname "$f")"
  cp -n "$f" "$BAK/$f" 2>/dev/null || true
}

echo "==> Scanning under: $ROOT"
echo "==> Backups -> $BAK"

#############################################
# 1) Front-matter: SSOT = line-scanner only #
#############################################
# - In code: if both functions exist, alias regex->lines. If only regex exists, delegate to lines.
# - In docs: scrub 'retain regex' phrasing; set "regex_retained": false

while IFS= read -r -d '' f; do
  backup "$f"
  has_lines=false; has_regex=false
  grep -qE 'def[[:space:]]+_parse_frontmatter_lines[[:space:]]*\(' "$f" && has_lines=true || true
  grep -qE 'def[[:space:]]+_parse_frontmatter_regex[[:space:]]*\(' "$f" && has_regex=true || true

  if $has_lines && $has_regex; then
    grep -qE '^[[:space:]]*_parse_frontmatter_regex[[:space:]]*=[[:space:]]*_parse_frontmatter_lines[[:space:]]*$' "$f" ||           printf '\n# vNext: canonicalize to regex-free line scanner\n_parse_frontmatter_regex = _parse_frontmatter_lines\n' >> "$f"
  elif $has_regex && ! $has_lines; then
    awk '
      BEGIN{in_def=0}
      /def[[:space:]]+_parse_frontmatter_regex[[:space:]]*\(.*\)[[:space:]]*:/ {
        print; print "    # vNext: delegate to regex-free line scanner";
        print "    return _parse_frontmatter_lines(text)"; in_def=1; next
      }
      in_def {
        if ($0 ~ /^[[:space:]]]*(def|class)[[:space:]]+/){ in_def=0; print;}
        next
      }
      { print }
    ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  fi
done < <(find "$ROOT" -type f -name "*.py" -print0)

while IFS= read -r -d '' f; do
  backup "$f"
  sed -i 's/"regex_retained"[[:space:]]*:[[:space:]]*true/"regex_retained": false/Ig' "$f"
  sed -i 's/\bretain(ed)? regex\b/regex removed/Ig' "$f"
done < <(find "$ROOT" -type f \( -name "*.md" -o -name "*.json" \) -print0)

###########################################################
# 2) Attributes: remove regex denylist; string methods only
###########################################################
while IFS= read -r -d '' f; do
  backup "$f"
  # Remove list like: DENIED_ATTR_PATTERNS = [ ... ]
  sed -i '/^[[:space:]]*DENIED_ATTR_PATTERNS[[:space:]]*=[[:space:]]*\[/,/]/d' "$f" || true
  # Replace re.match("^on[a-z]+$", name) -> string method
  sed -i "s/re\.match(\s*r'\^on\[a-z\]\+\$'\s*,\s*\([^)]\+\))/((\1).lower().startswith('on') \&\& len(\1)>2 \&\& (\1)[2:].isalpha())/g" "$f" || true
  # Replace re.match("^srcdoc$", name) -> equality
  sed -i "s/re\.match(\s*r'\^srcdoc\$'\s*,\s*\([^)]\+\))/((\1).lower()=='srcdoc')/g" "$f" || true
  # Ensure helper exists (keeps DRY)
  if ! grep -qE 'def[[:space:]]+_is_event_handler\(' "$f"; then
    cat >> "$f" <<'PY'
# vNext: non-regex attribute checks (SSOT)
def _is_event_handler(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    return n.startswith("on") and len(n) > 2 and n[2:].isalpha()
PY
  fi
done < <(find "$ROOT" -type f -name "*.py" -print0)

###############################################
# 3) CI/Tests: single policy, no-regex-in-core
###############################################
# Mark legacy retained-regex/nested-quantifier tests as xfail.
while IFS= read -r -d '' f; do
  backup "$f"
  if grep -qiE 'retained regex|nested quantifier' "$f"; then
    grep -q 'pytestmark = pytest.mark.xfail' "$f" ||           sed -i '1s;^;import pytest\npytestmark = pytest.mark.xfail(reason="vNext: core is regex-free; legacy test disabled")\n\n;' "$f"
  fi
done < <(find "$ROOT" -type f -name "test_*.py" -print0)

##############################################
# 4) Slug: scrub stray 'import re' if unused
##############################################
while IFS= read -r -d '' f; do
  backup "$f"
  if grep -qE 'def[[:space:]]+_generate_deterministic_slug[[:space:]]*\(' "$f"; then
    if grep -q '^import re\b' "$f" && ! grep -q 're\.' <(grep -n 're\.' "$f" | grep -v 'import re' || true); then
      sed -i '/^import re\b/d' "$f"
    fi
  fi
done < <(find "$ROOT" -type f -name "*.py" -print0)

echo "==> Done. Backups saved under: $BAK"
echo "Re-run your tests to validate changes."

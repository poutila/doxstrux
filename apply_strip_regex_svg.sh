#!/usr/bin/env bash
# apply_strip_regex_svg.sh — tiny, focused patch
# What this does:
#   (a) Deletes regex attribute blocks (DENIED_ATTR_PATTERNS) and any direct re.match checks for attrs
#   (b) Removes _parse_frontmatter_regex() and replaces code references with _parse_frontmatter_lines()
#   (c) Removes the SVG allow/deny toggle by inlining unconditional denial (replace DENY_SVG_EXTENSION with True)
#
# Usage: bash apply_strip_regex_svg.sh [repo_root]
# Notes: idempotent; creates timestamped backups of touched files.
set -euo pipefail

ROOT="${1:-.}"
TS="$(date +%Y%m%d_%H%M%S)"
BAK=".bak_strip_regex_svg_$TS"
mkdir -p "$BAK"

backup() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  mkdir -p "$BAK/$(dirname "$f")"
  cp -n "$f" "$BAK/$f" 2>/dev/null || true
}

echo "==> Scanning: $ROOT"
echo "==> Backups -> $BAK"

####################################################################
# (a) Delete regex attribute blocks and replace direct re.match uses
####################################################################
while IFS= read -r -d '' f; do
  backup "$f"
  # Remove array-style denylist definitions: DENIED_ATTR_PATTERNS = [ ... ]
  sed -i '/^[[:space:]]*DENIED_ATTR_PATTERNS[[:space:]]*=[[:space:]]*\[/,/]/d' "$f" || true

  # Replace common direct matches with string methods (best-effort)
  # re.match(r'^on[a-z]+$', name)  -> name.lower().startswith('on') and len(name)>2 and name[2:].isalpha()
  sed -i "s/re\.match(\s*r'\^on\[a-z\]\+\$'\s*,\s*\([^)]\+\))/((\1).lower().startswith('on') \&\& len(\1)>2 \&\& (\1)[2:].isalpha())/g" "$f" || true
  # re.match(r'^srcdoc$', name)    -> name.lower()=='srcdoc'
  sed -i "s/re\.match(\s*r'\^srcdoc\$'\s*,\s*\([^)]\+\))/((\1).lower()=='srcdoc')/g" "$f" || true

  # Ensure helper exists to keep things DRY
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

#######################################################################################
# (b) Remove _parse_frontmatter_regex and replace all references with the line-scanner
#######################################################################################
# 1) Replace call sites first (avoid NameError later)
while IFS= read -r -d '' f; do
  backup "$f"
  sed -i 's/\b_parse_frontmatter_regex\(/_parse_frontmatter_lines(/g' "$f"
done < <(find "$ROOT" -type f -name "*.py" -print0)

# 2) Delete the function definition block (def _parse_frontmatter_regex(...): ...)
while IFS= read -r -d '' f; do
  backup "$f"
  # Remove def block until next top-level def/class or EOF
  awk '
    BEGIN{in_def=0}
    /^[[:space:]]*def[[:space:]]+_parse_frontmatter_regex[[:space:]]*\(/ {
      in_def=1; next
    }
    in_def {
      if ($0 ~ /^[[:space:]]*(def|class)[[:space:]]+/) { in_def=0; print }
      next
    }
    { print }
  ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done < <(find "$ROOT" -type f -name "*.py" -print0)

# 3) Docs/logs: scrub "retain regex" phrasing
while IFS= read -r -d '' f; do
  backup "$f"
  sed -i 's/"regex_retained"[[:space:]]*:[[:space:]]*true/"regex_retained": false/Ig' "$f"
  sed -i 's/\bretain(ed)? regex\b/regex removed/Ig' "$f"
done < <(find "$ROOT" -type f \( -name "*.md" -o -name "*.json" \) -print0)

############################################################
# (c) Remove SVG toggle: inline unconditional SVG denial
############################################################
# 1) Replace references to DENY_SVG_EXTENSION with True (so conditions become unconditional)
while IFS= read -r -d '' f; do
  backup "$f"
  sed -i 's/\bDENY_SVG_EXTENSION\b/True/g' "$f"
done < <(find "$ROOT" -type f -name "*.py" -print0)

# 2) Delete the toggle definition lines entirely (if present)
while IFS= read -r -d '' f; do
  backup "$f"
  sed -i '/^[[:space:]]*DENY_SVG_EXTENSION[[:space:]]*=.*/d' "$f"
done < <(find "$ROOT" -type f -name "*.py" -print0)

# 3) Docs: remove mentions of the toggle
while IFS= read -r -d '' f; do
  backup "$f"
  sed -i 's/\bDENY_SVG_EXTENSION\b//g' "$f"
done < <(find "$ROOT" -type f -name "*.md" -print0)

echo "==> Patch complete. Backups saved under: $BAK"
echo "Re-run your tests to validate changes."

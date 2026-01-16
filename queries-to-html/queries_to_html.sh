#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  queries_to_html.sh -i INPUT.txt [-o OUTPUT.html] [-t ul|ol]

Options:
  -i  Input text file (one query per line)            (required)
  -o  Output HTML file (default: stdout)
  -t  List type: ul or ol (default: ul)
  -h  Show this help

Examples:
  ./queries_to_html.sh -i queries.txt > queries.html
  ./queries_to_html.sh -i queries.txt -t ol -o queries.html
USAGE
}

INPUT=""
OUTPUT=""
TYPE="ul"

while getopts ":i:o:t:h" opt; do
  case "$opt" in
    i) INPUT="$OPTARG";;
    o) OUTPUT="$OPTARG";;
    t) TYPE="$OPTARG";;
    h) usage; exit 0;;
    \?) echo "Error: unknown option -$OPTARG" >&2; usage; exit 2;;
    :) echo "Error: option -$OPTARG requires an argument" >&2; usage; exit 2;;
  esac
done

if [[ -z "$INPUT" ]]; then
  usage
  exit 2
fi

if [[ "$TYPE" != "ul" && "$TYPE" != "ol" ]]; then
  echo "Error: -t must be 'ul' or 'ol'" >&2
  usage
  exit 2
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Error: input file not found: $INPUT" >&2
  exit 2
fi

write_html() {
  echo '<!doctype html><meta charset="utf-8">'
  echo "<${TYPE}>"
  while IFS= read -r q || [[ -n "$q" ]]; do
    [[ -z "$q" ]] && continue

    enc=$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote_plus(sys.argv[1]))' "$q")
    # basic HTML escaping for &, <, >
    esc=$(printf '%s' "$q" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')

    printf '  <li><a href="https://www.google.com/search?q=%s" target="_blank" rel="noopener">%s</a></li>\n' "$enc" "$esc"
  done < "$INPUT"
  echo "</${TYPE}>"
}

if [[ -n "$OUTPUT" ]]; then
  write_html > "$OUTPUT"
else
  write_html
fi

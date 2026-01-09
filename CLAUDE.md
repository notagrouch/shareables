# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of shareable utilities. Currently contains:
- **evernote-converter**: Python utility for converting Evernote `.enex` export files to Markdown

## Evernote Converter

### Running the Script

```bash
# Basic usage
python3 evernote-converter/enex_to_markdown.py <input.enex>

# Specify custom output directory
python3 evernote-converter/enex_to_markdown.py <input.enex> /path/to/output
```

### Architecture

The converter is a single-file Python script (`evernote-converter/enex_to_markdown.py`) with no external dependencies (stdlib only).

**Core components:**

1. **ENMLToMarkdown (line 18)**: HTML parser that converts Evernote Markup Language to Markdown
   - Handles embedded media via `resources_map` (hash -> filename mapping)
   - Converts formatting: headers, bold, italic, lists, links
   - Embeds images using relative paths to `images/` directory

2. **extract_resources() (line 87)**: Extracts and decodes base64-encoded images/attachments
   - Creates `images/` subdirectory in output location
   - Calculates MD5 hash for each resource (used for referencing)
   - Determines file extensions from MIME types
   - Returns hash-to-filename mapping for use in conversion

3. **convert_note() (line 144)**: Main conversion logic per note
   - Extracts title, timestamps (created/updated)
   - Calls `extract_resources()` first to build resource map
   - Parses ENML content (handles CDATA sections)
   - Generates YAML frontmatter with metadata
   - Sanitizes filenames to be filesystem-safe

4. **convert_enex() (line 215)**: Entry point that processes entire `.enex` file
   - Parses XML structure
   - Creates output directory (defaults to `<filename>_markdown/`)
   - Iterates through all `<note>` elements
   - Handles errors gracefully per note (continues on failure)

**Data flow:**
1. Parse `.enex` XML file
2. For each note: extract resources → convert ENML to Markdown → write `.md` file
3. Resources are saved to `images/` subdirectory with MD5-based filenames
4. Markdown files reference images using relative paths

### Requirements

- Python 3.6+
- No external dependencies (uses only standard library modules)

### Output Structure

```
<filename>_markdown/
├── images/
│   ├── <md5hash>.png
│   └── <md5hash>.jpg
├── Note_Title_1.md
└── Note_Title_2.md
```

Each Markdown file includes YAML frontmatter:
```yaml
---
title: Note Title
created: 20240109T120000Z
updated: 20240109T150000Z
source: evernote
---
```

# Evernote to Markdown Converter

A Python script that converts Evernote `.enex` export files into clean Markdown documents with properly extracted images and attachments.

## Features

- 📝 **Markdown Conversion**: Converts Evernote's ENML (Evernote Markup Language) to standard Markdown
- 🖼️ **Image Extraction**: Automatically extracts and decodes base64-encoded images from notes
- 📂 **Organized Output**: Saves images to an `images/` subfolder with relative path references
- 🏷️ **Metadata Preservation**: Maintains note titles, creation dates, and update timestamps in YAML frontmatter
- 📎 **Attachment Support**: Handles images (PNG, JPG, GIF, BMP) and other attachments like PDFs
- ✨ **Formatting**: Preserves basic formatting (headers, bold, italic, lists)

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Usage

### Basic Usage

```bash
python3 enex_to_markdown.py <input.enex>
```

This creates an output directory named `<filename>_markdown/` containing:
- Individual `.md` files for each note
- An `images/` subfolder with all extracted media

### Specify Output Directory

```bash
python3 enex_to_markdown.py <input.enex> /path/to/output
```

### Example

```bash
# Convert your Evernote export
python3 enex_to_markdown.py my-notes.enex

# Result:
# my-notes_markdown/
# ├── images/
# │   ├── abc123.png
# │   └── def456.jpg
# ├── Note_Title_1.md
# ├── Note_Title_2.md
# └── ...
```

## Output Format

Each Markdown file includes YAML frontmatter with metadata:

```markdown
---
title: My Note Title
created: 20240109T120000Z
updated: 20240109T150000Z
source: evernote
---

# Note content here

![image](images/abc123.png)
```

## How It Works

1. **Parses XML**: Reads the `.enex` file as XML
2. **Extracts Resources**: Decodes base64-encoded images and attachments
3. **Converts ENML**: Transforms Evernote's markup to Markdown
4. **Creates Files**: Generates organized directory structure with relative paths

## Limitations

- EXIF data is not preserved in extracted images (timestamps are in frontmatter)
- Complex formatting may need manual adjustment
- Links in notes currently show as placeholder URLs

## Use Cases

- 🔄 Migrating from Evernote to other note-taking systems (Obsidian, Joplin, etc.)
- 📚 Creating a portable, text-based backup of your notes
- 🔍 Making notes searchable and versionable with git
- 🖥️ Self-hosting your note archive

## License

Free to use and modify.

## Contributing

Found a bug or want to add a feature? Feel free to submit issues or pull requests!

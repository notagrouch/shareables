# Evernote to HTML Converter

**Version 0.01.1**

A Python script that converts Evernote `.enex` export files into clean, browsable HTML documents with searchable index, image gallery, and optional Markdown output.

## Features

### Core Functionality
- 🌐 **HTML Export**: Converts notes to standalone HTML files with embedded CSS (mobile-responsive)
- 📝 **Optional Markdown**: Use `--markdown` flag to also generate Markdown files
- 🔍 **Searchable Index**: Auto-generated `index.html` with live search/filter functionality
- 🖼️ **Image Gallery**: Dedicated `gallery.html` with grid layout and lightbox viewer
- 📂 **Organized Structure**: Clean folder hierarchy with `notes/` and `attachments/images/`
- 🏷️ **Metadata Preservation**: Maintains note titles, creation dates, and update timestamps
- 📎 **Attachment Support**: Handles images (PNG, JPG, GIF, BMP) and PDFs
- ✨ **Formatting**: Preserves headers, bold, italic, lists, and links

### Advanced Features
- 🎯 **Multi-File Processing**: Process multiple `.enex` files in one command using wildcards
- 📱 **Mobile-Friendly**: Responsive design with CSS Grid, works on all devices
- 🌙 **Dark Mode**: Automatic dark mode support based on system preferences
- ⚡ **Self-Contained**: No external dependencies, works offline
- 🎨 **Modern UI**: Clean, modern design with smooth animations

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Installation

No installation needed! Just download `enex_to_markdown.py` and run it.

## Usage

### Basic Usage

```bash
# Convert single file to HTML
python3 enex_to_markdown.py notes.enex

# Convert multiple files using wildcard
python3 enex_to_markdown.py /path/to/exports/*.enex

# Convert with Markdown output
python3 enex_to_markdown.py notes.enex --markdown
```

### Advanced Usage

```bash
# Custom output directory (single file only)
python3 enex_to_markdown.py notes.enex -o /custom/output

# Process all .enex files in a directory
python3 enex_to_markdown.py ~/evernote-exports/*.enex --markdown

# View help
python3 enex_to_markdown.py --help
```

## Output Structure

Each conversion creates an organized export directory:

```
<filename>_export/
├── index.html              # Searchable note index with live filter
├── gallery.html            # Image gallery with lightbox viewer
├── notes/                  # All note HTML/Markdown files
│   ├── Note_Title_1.html
│   ├── Note_Title_2.html
│   └── Note_Title_1.md     # (if --markdown flag used)
└── attachments/
    └── images/             # All extracted images
        ├── abc123def456.png
        └── 789xyz012abc.jpg
```

### Index Page Features

- **Live Search**: Type to instantly filter notes by title or content
- **Note Cards**: Visual cards showing title, date, preview snippet, and image count
- **Sorted by Date**: Most recently updated notes appear first
- **Gallery Link**: Quick access to view all images

### Gallery Page Features

- **Responsive Grid**: Auto-fitting grid layout (1-5 columns depending on screen size)
- **Lightbox Viewer**: Click any image to view full-size
- **CSS Thumbnails**: Uniform image sizing without creating multiple files
- **Keyboard Support**: ESC key to close lightbox

## HTML Output Format

Each HTML note includes:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Note Title</title>
    <meta name="created" content="20240109T120000Z">
    <meta name="updated" content="20240109T150000Z">
    <!-- Embedded CSS for styling -->
</head>
<body>
    <header>
        <a href="../index.html">← Back to Index</a>
        <h1>Note Title</h1>
        <div class="metadata">Created: January 9, 2024 | Updated: January 9, 2024</div>
    </header>
    <main>
        <!-- Note content with images -->
        <img src="../attachments/images/abc123.png" alt="image" />
    </main>
</body>
</html>
```

## Markdown Output Format (Optional)

When using `--markdown` flag, notes are also saved as Markdown with YAML frontmatter:

```markdown
---
title: My Note Title
created: 20240109T120000Z
updated: 20240109T150000Z
source: evernote
---

# Note content here

![image](../attachments/images/abc123.png)
```

## Multi-File Processing

Process multiple exports in one command:

```bash
# Process all .enex files in a directory
python3 enex_to_markdown.py /path/to/exports/*.enex

# Example output:
# ============================================================
# Processing file 1 of 5: notebook1.enex
# ============================================================
# Output directory: /path/to/exports/notebook1_export
# ...
# ✓ Conversion complete!
#
# ============================================================
# Processing file 2 of 5: notebook2.enex
# ============================================================
# ...
# ============================================================
# ✓ All 5 files processed successfully!
# ============================================================
```

Each file gets its own independent export directory with separate index and gallery.

## Command-Line Options

```
usage: enex_to_markdown.py [-h] [--output-dir OUTPUT_DIR] [--markdown]
                           input_file [input_file ...]

positional arguments:
  input_file            Input .enex file(s) - supports wildcards like *.enex

options:
  -h, --help            Show help message and exit
  --output-dir, -o      Output directory (only for single file, default: <filename>_export)
  --markdown            Also generate Markdown files alongside HTML
```

## How It Works

1. **Parses XML**: Reads the `.enex` file as XML structure
2. **Extracts Resources**: Decodes base64-encoded images and attachments
3. **Converts ENML to HTML**: Transforms Evernote's markup to clean HTML5
4. **Generates Index**: Creates searchable index with metadata and snippets
5. **Creates Gallery**: Builds responsive image gallery with all extracted images
6. **Organizes Output**: Saves everything in a clean folder structure

## Browser Compatibility

The HTML output works in all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Use Cases

- 🔄 **Migrating from Evernote**: Move to other systems (Obsidian, Notion, etc.)
- 📚 **Portable Backup**: Create a browsable, offline backup of your notes
- 🔍 **Searchable Archive**: Browse and search notes without Evernote
- 🖥️ **Self-Hosting**: Host your notes on your own server or NAS
- 📱 **Mobile Access**: View notes on any device with a web browser
- 🎨 **Customization**: Edit the embedded CSS to match your style

## Version History

### v0.01.1 (2026-01-09)
- Added HTML export as default format
- Added searchable index.html with live filtering
- Added gallery.html with image grid and lightbox
- Added multi-file processing with wildcard support
- Reorganized output structure (notes/ and attachments/images/)
- Added mobile-responsive design with dark mode
- Made Markdown export optional (--markdown flag)

### v0.01.0 (2026-01-09)
- Initial release
- Basic Markdown conversion
- Image extraction

## Limitations

- EXIF data is not preserved in extracted images (timestamps are in metadata)
- Very complex formatting may need manual adjustment
- Tables and advanced layout elements may require cleanup

## License

Free to use and modify.

## Contributing

Found a bug or want to add a feature? Feel free to submit issues or pull requests!

## Credits

Built with Claude Code by Anthropic.

#!/usr/bin/env python3
"""
Convert Evernote .enex files to HTML with searchable index and image gallery.

Usage:
    python3 enex_to_markdown.py <input.enex> [options]
    python3 enex_to_markdown.py <file1.enex> <file2.enex> ... [options]
    python3 enex_to_markdown.py /path/to/*.enex [options]

Examples:
    # Convert single file to HTML (default)
    python3 enex_to_markdown.py notes.enex

    # Convert multiple files using wildcard
    python3 enex_to_markdown.py /path/to/exports/*.enex

    # Also generate Markdown files
    python3 enex_to_markdown.py notes.enex --markdown

    # Specify custom output directory (single file only)
    python3 enex_to_markdown.py notes.enex -o /path/to/output --markdown

Output structure:
    <filename>_export/
    ├── index.html              # Searchable note index
    ├── gallery.html            # Image gallery
    ├── notes/                  # All note HTML/MD files
    │   ├── Note_Title_1.html
    │   └── Note_Title_2.html
    └── attachments/
        └── images/             # All extracted images
            ├── <hash>.png
            └── <hash>.jpg
"""

import sys
import os
import base64
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser
import re
import argparse
from datetime import datetime
import glob as glob_module


def format_evernote_date(date_str):
    """Convert Evernote timestamp '20240109T120000Z' to readable format 'January 9, 2024'."""
    if not date_str:
        return ''
    try:
        dt = datetime.strptime(date_str, '%Y%m%dT%H%M%SZ')
        return dt.strftime('%B %d, %Y')
    except:
        return date_str


def extract_text_snippet(html_content, max_length=150):
    """Extract plain text snippet from HTML for preview."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Truncate with ellipsis
    if len(text) > max_length:
        return text[:max_length] + '...'
    return text


class NoteMetadata:
    """Store metadata for a converted note."""

    def __init__(self, title, created, updated, html_filename, md_filename=None):
        self.title = title
        self.created = created
        self.updated = updated
        self.html_filename = html_filename
        self.md_filename = md_filename
        self.snippet = ''
        self.image_count = 0

    def set_snippet(self, html_content, max_length=150):
        """Extract and store text snippet from HTML content."""
        self.snippet = extract_text_snippet(html_content, max_length)

    def get_formatted_date(self):
        """Get formatted update date."""
        return format_evernote_date(self.updated)


class ENMLToMarkdown(HTMLParser):
    """Convert Evernote Markup Language (ENML) to Markdown."""
    
    def __init__(self, resources_map):
        super().__init__()
        self.resources_map = resources_map  # hash -> filename mapping
        self.markdown = []
        self.in_list = False
        self.list_level = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'en-media':
            # Handle embedded images/attachments
            media_hash = attrs_dict.get('hash', '')
            if media_hash in self.resources_map:
                filename = self.resources_map[media_hash]
                self.markdown.append(f'\n![image]({filename})\n')
        elif tag == 'div':
            self.markdown.append('\n')
        elif tag == 'br':
            self.markdown.append('\n')
        elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.markdown.append('\n' + '#' * level + ' ')
        elif tag == 'strong' or tag == 'b':
            self.markdown.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown.append('*')
        elif tag == 'ul':
            self.in_list = True
            self.list_level += 1
        elif tag == 'li' and self.in_list:
            self.markdown.append('\n' + '  ' * (self.list_level - 1) + '- ')
        elif tag == 'a':
            self.markdown.append('[')
            
    def handle_endtag(self, tag):
        if tag in ['strong', 'b']:
            self.markdown.append('**')
        elif tag in ['em', 'i']:
            self.markdown.append('*')
        elif tag == 'ul':
            self.in_list = False
            self.list_level -= 1
        elif tag == 'a':
            self.markdown.append('](url)')  # Would need to track href
            
    def handle_data(self, data):
        # Clean up the text
        text = data.strip()
        if text:
            self.markdown.append(text)
    
    def get_markdown(self):
        return ''.join(self.markdown).strip()


class ENMLToHTML(HTMLParser):
    """Convert Evernote Markup Language (ENML) to clean HTML."""

    def __init__(self, resources_map):
        super().__init__()
        self.resources_map = resources_map  # hash -> filename mapping
        self.html = []
        self.current_link_href = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'en-media':
            # Handle embedded images/attachments
            media_hash = attrs_dict.get('hash', '')
            if media_hash in self.resources_map:
                filename = self.resources_map[media_hash]
                self.html.append(f'<img src="{filename}" alt="image" loading="lazy" />')
        elif tag == 'en-note':
            # Skip the en-note wrapper
            pass
        elif tag == 'a':
            # Preserve links
            href = attrs_dict.get('href', '#')
            self.current_link_href = href
            self.html.append(f'<a href="{href}">')
        else:
            # Preserve most HTML tags as-is
            attrs_str = ''
            if attrs:
                attrs_str = ' ' + ' '.join([f'{k}="{v}"' for k, v in attrs])
            self.html.append(f'<{tag}{attrs_str}>')

    def handle_endtag(self, tag):
        if tag == 'en-note':
            # Skip the en-note wrapper
            pass
        elif tag == 'a':
            self.html.append('</a>')
            self.current_link_href = None
        else:
            self.html.append(f'</{tag}>')

    def handle_data(self, data):
        # Preserve text content
        self.html.append(data)

    def get_html(self):
        return ''.join(self.html).strip()


def sanitize_filename(name):
    """Create a safe filename from note title."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    return name[:200] if name else 'untitled'


# HTML Templates
NOTE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="created" content="{created}">
    <meta name="updated" content="{updated}">
    <title>{title}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --hover: #f3f4f6;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #1f2937;
                --text: #f9fafb;
                --text-light: #9ca3af;
                --border: #374151;
                --hover: #374151;
            }}
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            padding: 2rem 1rem;
            max-width: 800px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        header a {{
            color: var(--primary);
            text-decoration: none;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            display: inline-block;
        }}
        header a:hover {{
            text-decoration: underline;
        }}
        h1 {{
            font-size: 2rem;
            margin: 0.5rem 0;
        }}
        .metadata {{
            color: var(--text-light);
            font-size: 0.9rem;
        }}
        main {{
            line-height: 1.8;
        }}
        main img {{
            max-width: 100%;
            height: auto;
            margin: 1.5rem 0;
            border-radius: 8px;
        }}
        main p {{
            margin: 1rem 0;
        }}
        main h1, main h2, main h3, main h4, main h5, main h6 {{
            margin: 1.5rem 0 1rem 0;
        }}
        main ul, main ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}
        main a {{
            color: var(--primary);
        }}
    </style>
</head>
<body>
    <header>
        <a href="../index.html">← Back to Index</a>
        <h1>{title}</h1>
        <div class="metadata">
            Created: {created_formatted} | Updated: {updated_formatted}
        </div>
    </header>
    <main>
        {content}
    </main>
</body>
</html>"""

INDEX_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evernote Notes Index</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --hover: #f3f4f6;
            --card-bg: #ffffff;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #111827;
                --text: #f9fafb;
                --text-light: #9ca3af;
                --border: #374151;
                --hover: #1f2937;
                --card-bg: #1f2937;
            }}
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }}
        nav {{
            margin: 1.5rem 0;
        }}
        nav a {{
            color: var(--primary);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border: 2px solid var(--primary);
            border-radius: 6px;
            display: inline-block;
        }}
        nav a:hover {{
            background: var(--primary);
            color: white;
        }}
        #search {{
            width: 100%;
            max-width: 600px;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            background: var(--card-bg);
            color: var(--text);
            margin: 1rem auto;
            display: block;
        }}
        #search:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        .notes-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
            margin-top: 2rem;
        }}
        @media (min-width: 640px) {{
            .notes-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        @media (min-width: 1024px) {{
            .notes-grid {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
        .note-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .note-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .note-card h3 {{
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }}
        .note-card h3 a {{
            color: var(--text);
            text-decoration: none;
        }}
        .note-card h3 a:hover {{
            color: var(--primary);
        }}
        .note-metadata {{
            color: var(--text-light);
            font-size: 0.875rem;
            margin-bottom: 0.75rem;
        }}
        .note-snippet {{
            color: var(--text-light);
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        .note-icons {{
            margin-top: 0.75rem;
            font-size: 0.875rem;
            color: var(--text-light);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>My Evernote Notes</h1>
            <nav>
                <a href="gallery.html">View Gallery</a>
            </nav>
            <input type="text" id="search" placeholder="Search notes..." />
        </header>
        <main id="notes-container" class="notes-grid">
            {notes_cards}
        </main>
    </div>
    <script>
        const searchInput = document.getElementById('search');
        const noteCards = document.querySelectorAll('.note-card');

        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value.toLowerCase();
            noteCards.forEach(card => {{
                const title = card.dataset.title.toLowerCase();
                const snippet = card.dataset.snippet.toLowerCase();
                const match = title.includes(query) || snippet.includes(query);
                card.style.display = match ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>"""

GALLERY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Gallery</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #ffffff;
            --text: #1f2937;
            --border: #e5e7eb;
            --modal-bg: rgba(0, 0, 0, 0.9);
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #111827;
                --text: #f9fafb;
                --border: #374151;
            }}
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: var(--text);
            background: var(--bg);
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 2rem;
            text-align: center;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 1rem;
        }}
        header a {{
            color: var(--primary);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border: 2px solid var(--primary);
            border-radius: 6px;
            display: inline-block;
        }}
        header a:hover {{
            background: var(--primary);
            color: white;
        }}
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        .gallery-item {{
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            cursor: pointer;
        }}
        .gallery-item img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            transition: transform 0.3s;
        }}
        .gallery-item:hover img {{
            transform: scale(1.05);
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: var(--modal-bg);
            justify-content: center;
            align-items: center;
        }}
        .modal.active {{
            display: flex;
        }}
        .modal-content {{
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        }}
        .modal-close {{
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        .modal-close:hover {{
            color: #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Image Gallery</h1>
            <a href="index.html">← Back to Index</a>
        </header>
        <div class="gallery-grid">
            {image_items}
        </div>
    </div>
    <div id="modal" class="modal" onclick="closeModal()">
        <span class="modal-close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modal-img" src="" alt="Full size image">
    </div>
    <script>
        function openModal(src) {{
            event.stopPropagation();
            const modal = document.getElementById('modal');
            const modalImg = document.getElementById('modal-img');
            modal.classList.add('active');
            modalImg.src = src;
        }}

        function closeModal() {{
            const modal = document.getElementById('modal');
            modal.classList.remove('active');
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>"""


def extract_resources(note_elem, output_dir):
    """Extract images and attachments from a note."""
    resources_map = {}  # hash -> filename
    attachments_dir = output_dir / 'attachments' / 'images'
    attachments_dir.mkdir(parents=True, exist_ok=True)

    for resource in note_elem.findall('.//resource'):
        # Get the data
        data_elem = resource.find('data')
        if data_elem is None:
            continue

        encoding = data_elem.get('encoding', '')
        data_b64 = data_elem.text

        if encoding != 'base64' or not data_b64:
            continue

        # Decode the data
        try:
            data_bytes = base64.b64decode(data_b64)
        except Exception as e:
            print(f"Warning: Failed to decode resource: {e}")
            continue

        # Get the hash (this is how resources are referenced)
        # Calculate hash from data
        data_hash = hashlib.md5(data_bytes).hexdigest()

        # Determine file extension from mime type
        mime_elem = resource.find('mime')
        mime_type = mime_elem.text if mime_elem is not None else 'application/octet-stream'

        ext = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'application/pdf': '.pdf',
        }.get(mime_type, '.bin')

        # Save the file
        filename = f'{data_hash}{ext}'
        filepath = attachments_dir / filename

        with open(filepath, 'wb') as f:
            f.write(data_bytes)

        # Store relative path from notes/ directory (where HTML files will be)
        resources_map[data_hash] = f'../attachments/images/{filename}'

        print(f"  Extracted: {filename} ({len(data_bytes)} bytes)")

    return resources_map


def generate_index_html(notes_metadata, output_dir):
    """Generate index.html with searchable list of all notes."""
    # Sort notes by updated date (newest first)
    sorted_notes = sorted(notes_metadata, key=lambda n: n.updated or '', reverse=True)

    # Generate note cards HTML
    cards_html = []
    for note in sorted_notes:
        # Create image icon if note has images
        image_icon = f'<div class="note-icons">📷 {note.image_count} images</div>' if note.image_count > 0 else ''

        card = f'''<div class="note-card" data-title="{note.title}" data-snippet="{note.snippet}">
            <h3><a href="notes/{note.html_filename}">{note.title}</a></h3>
            <div class="note-metadata">Updated: {note.get_formatted_date()}</div>
            <p class="note-snippet">{note.snippet}</p>
            {image_icon}
        </div>'''
        cards_html.append(card)

    notes_cards = '\n'.join(cards_html)

    # Generate the complete HTML
    index_html = INDEX_HTML_TEMPLATE.format(notes_cards=notes_cards)

    # Write to file
    index_path = output_dir / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"\n  Created index: {index_path}")


def generate_gallery_html(all_images, output_dir):
    """Generate gallery.html with grid of all images."""
    if not all_images:
        print("  No images found, skipping gallery generation")
        return

    # Generate image items HTML
    items_html = []
    for image_path in all_images:
        item = f'''<div class="gallery-item">
            <img src="{image_path}" alt="Gallery image" loading="lazy" onclick="openModal('{image_path}')">
        </div>'''
        items_html.append(item)

    image_items = '\n'.join(items_html)

    # Generate the complete HTML
    gallery_html = GALLERY_HTML_TEMPLATE.format(image_items=image_items)

    # Write to file
    gallery_path = output_dir / 'gallery.html'
    with open(gallery_path, 'w', encoding='utf-8') as f:
        f.write(gallery_html)

    print(f"  Created gallery: {gallery_path}")


def convert_note(note_elem, output_dir, export_markdown=False):
    """Convert a single note to HTML (and optionally Markdown)."""
    # Get note title
    title_elem = note_elem.find('title')
    title = title_elem.text if title_elem is not None else 'Untitled'

    # Get timestamps
    created_elem = note_elem.find('created')
    updated_elem = note_elem.find('updated')
    created = created_elem.text if created_elem is not None else ''
    updated = updated_elem.text if updated_elem is not None else ''

    print(f"\nProcessing: {title}")

    # Extract resources (images, attachments)
    resources_map = extract_resources(note_elem, output_dir)

    # Get note content (ENML)
    content_elem = note_elem.find('content')
    if content_elem is None or not content_elem.text:
        print(f"  Warning: No content found")
        content_raw = ""
    else:
        # Extract the CDATA content
        content_text = content_elem.text
        # Remove CDATA markers if present
        if content_text.startswith('<![CDATA['):
            content_text = content_text[9:]
        if content_text.endswith(']]>'):
            content_text = content_text[:-3]

        # Extract just the en-note content
        try:
            # Parse to get the inner content
            content_root = ET.fromstring(content_text)
            en_note = content_root if content_root.tag.endswith('en-note') else content_root.find('.//{*}en-note')
            if en_note is not None:
                content_raw = ET.tostring(en_note, encoding='unicode', method='html')
            else:
                content_raw = content_text
        except:
            content_raw = content_text

    # Convert ENML to HTML (default)
    html_converter = ENMLToHTML(resources_map)
    html_converter.feed(content_raw)
    html_content = html_converter.get_html()

    # Format dates for display
    created_formatted = format_evernote_date(created)
    updated_formatted = format_evernote_date(updated)

    # Create the HTML file in notes/ subdirectory
    notes_dir = output_dir / 'notes'
    notes_dir.mkdir(exist_ok=True)

    safe_title = sanitize_filename(title)
    html_filename = f'{safe_title}.html'
    html_filepath = notes_dir / html_filename

    # Generate full HTML document
    full_html = NOTE_HTML_TEMPLATE.format(
        title=title,
        created=created,
        updated=updated,
        created_formatted=created_formatted,
        updated_formatted=updated_formatted,
        content=html_content
    )

    # Write HTML file
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"  Created: {html_filepath}")

    # Optionally create Markdown file in notes/ directory
    md_filename = None
    if export_markdown:
        converter = ENMLToMarkdown(resources_map)
        converter.feed(content_raw)
        markdown_content = converter.get_markdown()

        md_filename = f'{safe_title}.md'
        md_filepath = notes_dir / md_filename

        # Add frontmatter
        frontmatter = f"""---
title: {title}
created: {created}
updated: {updated}
source: evernote
---

"""

        # Write Markdown file
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(markdown_content)
        print(f"  Created: {md_filepath}")

    # Create metadata object
    metadata = NoteMetadata(
        title=title,
        created=created,
        updated=updated,
        html_filename=html_filename,
        md_filename=md_filename
    )
    metadata.set_snippet(html_content)
    metadata.image_count = len(resources_map)

    return metadata


def convert_enex(enex_file, output_dir=None, export_markdown=False):
    """Convert an .enex file to HTML files with index and gallery."""
    enex_path = Path(enex_file)

    if not enex_path.exists():
        print(f"Error: File not found: {enex_file}")
        return

    # Create output directory
    if output_dir is None:
        output_dir = enex_path.parent / f'{enex_path.stem}_export'
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Parse the XML
    print(f"\nParsing {enex_path.name}...")
    try:
        tree = ET.parse(enex_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    # Process each note and collect metadata
    notes = root.findall('.//note')
    print(f"Found {len(notes)} notes")

    notes_metadata = []
    all_images = set()  # Use set to avoid duplicates

    for note in notes:
        try:
            metadata = convert_note(note, output_dir, export_markdown)
            notes_metadata.append(metadata)

            # Collect images for gallery (from resources in the note)
            # Images are already extracted, collect their paths
            for note_elem in [note]:
                for resource in note_elem.findall('.//resource'):
                    mime_elem = resource.find('mime')
                    if mime_elem is not None and mime_elem.text.startswith('image/'):
                        data_elem = resource.find('data')
                        if data_elem is not None and data_elem.text:
                            # Calculate hash to get filename
                            try:
                                data_bytes = base64.b64decode(data_elem.text)
                                data_hash = hashlib.md5(data_bytes).hexdigest()
                                ext = {
                                    'image/png': '.png',
                                    'image/jpeg': '.jpg',
                                    'image/jpg': '.jpg',
                                    'image/gif': '.gif',
                                    'image/bmp': '.bmp',
                                }.get(mime_elem.text, '.bin')
                                all_images.add(f'attachments/images/{data_hash}{ext}')
                            except:
                                pass

        except Exception as e:
            title_elem = note.find('title')
            title = title_elem.text if title_elem is not None else 'Unknown'
            print(f"  Error processing '{title}': {e}")

    # Generate index and gallery
    print("\nGenerating index and gallery...")
    generate_index_html(notes_metadata, output_dir)
    generate_gallery_html(list(all_images), output_dir)

    # Print summary
    print(f"\n✓ Conversion complete!")
    print(f"  📄 {len(notes_metadata)} notes converted")
    print(f"  🖼️  {len(all_images)} images extracted")
    if export_markdown:
        print(f"  📝 Markdown files also generated")
    print(f"  📂 Output: {output_dir}")
    print(f"  🌐 Open: {output_dir}/index.html")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert Evernote .enex files to HTML with searchable index and gallery'
    )
    parser.add_argument('input_files', nargs='+', metavar='input_file',
                       help='Input .enex file(s) - supports wildcards like *.enex')
    parser.add_argument('--output-dir', '-o', dest='output_dir', default=None,
                       help='Output directory (only for single file, default: <filename>_export)')
    parser.add_argument('--markdown', action='store_true',
                       help='Also generate Markdown files alongside HTML')

    args = parser.parse_args()

    # Process each input file
    total_files = len(args.input_files)
    for idx, input_file in enumerate(args.input_files, 1):
        if total_files > 1:
            print(f"\n{'='*60}")
            print(f"Processing file {idx} of {total_files}: {Path(input_file).name}")
            print(f"{'='*60}")
            # When processing multiple files, always use default output directories
            convert_enex(input_file, None, args.markdown)
        else:
            # Single file - allow custom output directory
            convert_enex(input_file, args.output_dir, args.markdown)

    if total_files > 1:
        print(f"\n{'='*60}")
        print(f"✓ All {total_files} files processed successfully!")
        print(f"{'='*60}")

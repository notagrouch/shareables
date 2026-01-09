#!/usr/bin/env python3
"""
Convert Evernote .enex files to Markdown with extracted images.

Usage: python3 enex_to_markdown.py <input.enex> [output_directory]
"""

import sys
import os
import base64
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser
import re


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


def sanitize_filename(name):
    """Create a safe filename from note title."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    return name[:200] if name else 'untitled'


def extract_resources(note_elem, output_dir):
    """Extract images and attachments from a note."""
    resources_map = {}  # hash -> filename
    images_dir = output_dir / 'images'
    images_dir.mkdir(exist_ok=True)
    
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
        filepath = images_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(data_bytes)
        
        # Store relative path for markdown
        resources_map[data_hash] = f'images/{filename}'
        
        print(f"  Extracted: {filename} ({len(data_bytes)} bytes)")
    
    return resources_map


def convert_note(note_elem, output_dir):
    """Convert a single note to Markdown."""
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
        content_html = ""
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
                content_html = ET.tostring(en_note, encoding='unicode', method='html')
            else:
                content_html = content_text
        except:
            content_html = content_text
    
    # Convert ENML/HTML to Markdown
    converter = ENMLToMarkdown(resources_map)
    converter.feed(content_html)
    markdown_content = converter.get_markdown()
    
    # Create the markdown file
    safe_title = sanitize_filename(title)
    md_filename = output_dir / f'{safe_title}.md'
    
    # Add frontmatter
    frontmatter = f"""---
title: {title}
created: {created}
updated: {updated}
source: evernote
---

"""
    
    # Write the file
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
        f.write(markdown_content)
    
    print(f"  Created: {md_filename}")
    return md_filename


def convert_enex(enex_file, output_dir=None):
    """Convert an .enex file to Markdown files."""
    enex_path = Path(enex_file)
    
    if not enex_path.exists():
        print(f"Error: File not found: {enex_file}")
        return
    
    # Create output directory
    if output_dir is None:
        output_dir = enex_path.parent / f'{enex_path.stem}_markdown'
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
    
    # Process each note
    notes = root.findall('.//note')
    print(f"Found {len(notes)} notes")
    
    for note in notes:
        try:
            convert_note(note, output_dir)
        except Exception as e:
            title_elem = note.find('title')
            title = title_elem.text if title_elem is not None else 'Unknown'
            print(f"  Error processing '{title}': {e}")
    
    print(f"\n✓ Conversion complete! Output in: {output_dir}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 enex_to_markdown.py <input.enex> [output_directory]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_enex(input_file, output_directory)

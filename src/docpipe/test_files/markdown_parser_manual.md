# MarkdownParserCore User Manual

A comprehensive guide to using the MarkdownParserCore library for secure markdown parsing and analysis.

## Table of Contents

1. [Overview](#overview)
2. [Security Profiles](#security-profiles)
3. [Basic Usage](#basic-usage)
4. [Validation and Security](#validation-and-security)
5. [Content Extraction](#content-extraction)
6. [Sanitization](#sanitization)
7. [Plugin System](#plugin-system)
8. [Configuration Options](#configuration-options)
9. [Error Handling](#error-handling)
10. [Advanced Examples](#advanced-examples)

## Overview

MarkdownParserCore is a secure, feature-rich markdown parser designed for RAG (Retrieval-Augmented Generation) systems and AI applications. It provides comprehensive parsing, security validation, and content extraction capabilities.

### Key Features

- **Security-first design** with multiple security profiles
- **Universal recursion engine** for efficient parsing
- **Comprehensive content extraction** (sections, tables, code blocks, etc.)
- **Plugin system** with security validation
- **YAML frontmatter support**
- **HTML sanitization** and security scanning
- **Unicode spoofing detection**
- **Prompt injection detection**
- **Content context awareness** (prose vs code)

## Security Profiles

The parser supports three security profiles that control feature availability and safety measures:

### Strict Profile
- Maximum security for untrusted content
- HTML completely disabled
- Limited plugins (table only)
- Small content size limits
- Aggressive prompt injection blocking

### Moderate Profile (Default)
- Balanced security and functionality
- HTML allowed with sanitization
- Basic plugins enabled
- Reasonable content limits
- Moderate injection detection

### Permissive Profile
- Maximum functionality
- All supported features enabled
- Large content limits
- Relaxed security (still safe for RAG)

## Basic Usage

### Simple Parsing

```python
from markdown_parser_core import MarkdownParserCore

# Basic parsing with default security profile
content = """
# My Document

This is a **sample** document with a [link](https://example.com).

```python
print("Hello, World!")
```
"""

parser = MarkdownParserCore(content)
result = parser.parse()

# Access parsed structure
print(f"Document has {len(result['structure']['sections'])} sections")
print(f"Found {len(result['structure']['code_blocks'])} code blocks")
```

### Security Profile Selection

```python
# Strict security for untrusted content
parser = MarkdownParserCore(content, security_profile='strict')

# Permissive for trusted internal content
parser = MarkdownParserCore(content, security_profile='permissive')

# Custom configuration with security profile
config = {
    'allows_html': True,
    'plugins': ['table', 'strikethrough'],
    'preset': 'gfm'
}
parser = MarkdownParserCore(content, config=config, security_profile='moderate')
```

## Validation and Security

### Content Validation

```python
# Quick validation without full parsing
validation = MarkdownParserCore.validate_content(content, 'strict')

if validation['valid']:
    print("Content is safe to parse")
else:
    print("Issues found:")
    for issue in validation['issues']:
        print(f"- {issue}")
```

### Check Available Features

```python
# Check what optional features are available
features = MarkdownParserCore.get_available_features()
print(f"YAML support: {features['yaml']}")
print(f"HTML sanitization: {features['bleach']}")
print(f"Footnotes plugin: {features['footnotes']}")
```

### Security Metadata

```python
result = parser.parse()
security = result['metadata']['security']

# Check for security warnings
if security['warnings']:
    print("Security warnings found:")
    for warning in security['warnings']:
        print(f"- {warning['type']}: {warning['message']}")

# Check statistics
stats = security['statistics']
print(f"Has scripts: {stats.get('has_script', False)}")
print(f"Ragged tables: {stats.get('ragged_tables_count', 0)}")
print(f"Unicode risk score: {stats.get('unicode_risk_score', 0)}")
```

## Content Extraction

### Sections and Headings

```python
result = parser.parse()

# Extract document sections
sections = result['structure']['sections']
for section in sections:
    print(f"Section: {section['title']} (Level {section['level']})")
    print(f"  Lines: {section['start_line']}-{section['end_line']}")
    print(f"  ID: {section['id']}")
    print(f"  Parent: {section['parent_id']}")

# Extract just headings
headings = result['structure']['headings']
for heading in headings:
    print(f"{'#' * heading['level']} {heading['text']}")
```

### Tables

```python
tables = result['structure']['tables']
for table in tables:
    print(f"Table at line {table['start_line']}:")
    print(f"  Headers: {table['headers']}")
    print(f"  Rows: {len(table['rows'])}")
    print(f"  Alignment: {table['align']}")
    
    # Check for issues
    if table.get('is_ragged'):
        print("  ⚠️  Ragged table detected (security concern)")
    
    # Display table data
    for i, row in enumerate(table['rows']):
        print(f"  Row {i}: {row}")
```

### Code Blocks

```python
code_blocks = result['structure']['code_blocks']
for block in code_blocks:
    print(f"Code block ({block['type']}) at line {block['start_line']}:")
    if block['language']:
        print(f"  Language: {block['language']}")
    print(f"  Content preview: {block['content'][:50]}...")
```

### Lists

```python
lists = result['structure']['lists']
for lst in lists:
    print(f"{lst['type'].title()} list at line {lst['start_line']}:")
    print(f"  Items: {lst['items_count']}")
    print(f"  Task items: {lst['task_items_count']}")
    
    for item in lst['items']:
        if item['checked'] is not None:
            status = "✓" if item['checked'] else "☐"
            print(f"  {status} {item['text']}")
        else:
            print(f"  • {item['text']}")
```

### Links and Images

```python
# Extract links
links = result['structure']['links']
for link in links:
    print(f"Link: {link['text']} -> {link['url']}")
    if not link.get('allowed', True):
        print("  ⚠️  Disallowed scheme detected")

# Extract images
images = result['structure']['images']
for img in images:
    print(f"Image: {img['alt']} ({img['src']})")
    print(f"  Kind: {img['image_kind']}, Format: {img['format']}")
    if img.get('bytes_approx'):
        print(f"  Size: ~{img['bytes_approx']} bytes")
```

### YAML Frontmatter

```python
metadata = result['metadata']
if metadata['has_frontmatter']:
    frontmatter = metadata['frontmatter']
    print("YAML Frontmatter:")
    for key, value in frontmatter.items():
        print(f"  {key}: {value}")
else:
    print("No frontmatter found")
```

## Sanitization

### Basic Sanitization

```python
# Sanitize content for RAG ingestion
sanitized = parser.sanitize()

print(f"Blocked: {sanitized['blocked']}")
print(f"Sanitized text: {sanitized['sanitized_text'][:200]}...")

if sanitized['reasons']:
    print("Sanitization actions:")
    for reason in sanitized['reasons']:
        print(f"  - {reason}")
```

### Custom Sanitization Policy

```python
# Custom sanitization settings
policy = {
    "allows_html": False,
    "drop_data_uri_images": True,
    "max_link_count": 50,
    "max_image_count": 20,
    "quarantine_on_injection": True
}

sanitized = parser.sanitize(policy=policy)

# Or use a security profile
sanitized = parser.sanitize(security_profile='strict')
```

## Plugin System

### Enable Plugins

```python
# Enable specific plugins
config = {
    'plugins': ['table', 'strikethrough', 'linkify'],
    'external_plugins': ['footnote', 'tasklists']
}

parser = MarkdownParserCore(content, config=config)

# Check what was actually enabled
print(f"Enabled plugins: {parser.enabled_plugins}")
print(f"Rejected plugins: {parser.rejected_plugins}")
print(f"Unavailable plugins: {parser.unavailable_plugins}")
```

### Extract Plugin-Specific Content

```python
result = parser.parse()

# Footnotes (if footnote plugin enabled)
if 'footnotes' in result['structure']:
    footnotes = result['structure']['footnotes']
    
    print("Footnote definitions:")
    for footnote in footnotes['definitions']:
        print(f"  [{footnote['label']}]: {footnote['content']}")
    
    print("Footnote references:")
    for ref in footnotes['references']:
        print(f"  Reference to [{ref['label']}] at line {ref['line']}")
```

## Configuration Options

### Complete Configuration Example

```python
config = {
    # Markdown-it preset
    'preset': 'gfm',  # 'commonmark', 'gfm', etc.
    
    # Plugin configuration
    'plugins': ['table', 'strikethrough', 'linkify'],
    'external_plugins': ['footnote', 'tasklists'],
    
    # HTML handling
    'allows_html': True,
}

# Security profile overrides
security_profile = 'moderate'

parser = MarkdownParserCore(
    content, 
    config=config, 
    security_profile=security_profile
)
```

### Security Profile Customization

```python
# Check available security limits
print("Security limits:")
for profile, limits in MarkdownParserCore.SECURITY_LIMITS.items():
    print(f"  {profile}:")
    for key, value in limits.items():
        print(f"    {key}: {value}")
```

## Error Handling

### Security Errors

```python
from markdown_parser_core import (
    MarkdownSecurityError, 
    MarkdownSizeError, 
    MarkdownPluginError
)

try:
    parser = MarkdownParserCore(very_large_content, security_profile='strict')
    result = parser.parse()
except MarkdownSizeError as e:
    print(f"Content too large: {e}")
    print(f"Security profile: {e.security_profile}")
    print(f"Content info: {e.content_info}")
except MarkdownSecurityError as e:
    print(f"Security violation: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Plugin Errors

```python
try:
    config = {'external_plugins': ['nonexistent_plugin']}
    parser = MarkdownParserCore(content, config=config)
except MarkdownPluginError as e:
    print(f"Plugin error: {e}")
```

## Advanced Examples

### RAG Document Processing Pipeline

```python
def process_document_for_rag(content: str, trusted: bool = False) -> dict:
    """Process a document for RAG ingestion with appropriate security."""
    
    # Choose security profile based on trust level
    profile = 'moderate' if trusted else 'strict'
    
    try:
        # Validate first
        validation = MarkdownParserCore.validate_content(content, profile)
        if not validation['valid']:
            return {
                'status': 'invalid',
                'issues': validation['issues']
            }
        
        # Parse with security profile
        parser = MarkdownParserCore(content, security_profile=profile)
        result = parser.parse()
        
        # Check for security issues
        security = result['metadata']['security']
        if security['warnings']:
            # Log warnings but continue
            print(f"Security warnings: {len(security['warnings'])}")
        
        # Sanitize for safe ingestion
        sanitized = parser.sanitize(security_profile=profile)
        
        if sanitized['blocked']:
            return {
                'status': 'blocked',
                'reasons': sanitized['reasons']
            }
        
        # Extract key content for RAG
        sections = result['structure']['sections']
        chunks = []
        
        for section in sections:
            chunks.append({
                'id': section['id'],
                'title': section['title'],
                'content': section['text_content'],
                'level': section['level'],
                'start_char': section['start_char'],
                'end_char': section['end_char']
            })
        
        return {
            'status': 'success',
            'chunks': chunks,
            'sanitized_text': sanitized['sanitized_text'],
            'metadata': {
                'has_code': result['metadata']['has_code'],
                'has_tables': result['metadata']['has_tables'],
                'total_chars': result['metadata']['total_chars'],
                'security_profile': profile
            }
        }
        
    except MarkdownSecurityError as e:
        return {
            'status': 'security_error',
            'error': str(e),
            'security_profile': e.security_profile
        }
```

### Content Analysis Pipeline

```python
def analyze_document_structure(content: str) -> dict:
    """Analyze document structure and provide insights."""
    
    parser = MarkdownParserCore(content, security_profile='moderate')
    result = parser.parse()
    
    structure = result['structure']
    metadata = result['metadata']
    
    analysis = {
        'document_stats': {
            'lines': metadata['total_lines'],
            'characters': metadata['total_chars'],
            'sections': len(structure['sections']),
            'headings': len(structure['headings'])
        },
        'content_types': {
            'paragraphs': len(structure['paragraphs']),
            'code_blocks': len(structure['code_blocks']),
            'tables': len(structure['tables']),
            'lists': len(structure['lists']),
            'images': len(structure['images']),
            'links': len(structure['links'])
        },
        'structure_analysis': {
            'max_heading_level': max((h['level'] for h in structure['headings']), default=0),
            'has_nested_lists': any(item['children'] for lst in structure['lists'] for item in lst['items']),
            'code_languages': list(set(block['language'] for block in structure['code_blocks'] if block['language'])),
            'external_links': len([link for link in structure['links'] if link.get('type') == 'external'])
        },
        'security_assessment': {
            'risk_score': metadata['security']['statistics'].get('unicode_risk_score', 0),
            'warnings_count': len(metadata['security']['warnings']),
            'has_html': metadata['security']['statistics'].get('has_html_block', False),
            'prompt_injection_risk': metadata['security']['statistics'].get('suspected_prompt_injection', False)
        }
    }
    
    return analysis
```

### Multi-Document Batch Processing

```python
def batch_process_documents(documents: list[str], security_profile: str = 'moderate') -> list[dict]:
    """Process multiple documents with consistent settings."""
    
    results = []
    
    for i, content in enumerate(documents):
        try:
            parser = MarkdownParserCore(content, security_profile=security_profile)
            result = parser.parse()
            
            # Extract summary information
            summary = {
                'document_id': i,
                'status': 'success',
                'sections': len(result['structure']['sections']),
                'word_count': sum(p['word_count'] for p in result['structure']['paragraphs']),
                'security_warnings': len(result['metadata']['security']['warnings']),
                'has_frontmatter': result['metadata']['has_frontmatter']
            }
            
            # Add full result if needed
            summary['full_result'] = result
            
        except MarkdownSecurityError as e:
            summary = {
                'document_id': i,
                'status': 'error',
                'error': str(e),
                'security_profile': e.security_profile
            }
        
        results.append(summary)
    
    return results
```

### Table Data Extraction

```python
def extract_table_data(content: str) -> list[dict]:
    """Extract structured data from markdown tables."""
    
    parser = MarkdownParserCore(content)
    result = parser.parse()
    
    table_data = []
    
    for table in result['structure']['tables']:
        # Convert to structured format
        headers = table['headers']
        rows = table['rows']
        
        # Create list of dictionaries
        structured_rows = []
        for row in rows:
            row_dict = {}
            for i, cell in enumerate(row):
                header = headers[i] if i < len(headers) else f'column_{i}'
                row_dict[header] = cell
            structured_rows.append(row_dict)
        
        table_info = {
            'table_id': table.get('id'),
            'location': {
                'start_line': table['start_line'],
                'end_line': table['end_line']
            },
            'headers': headers,
            'data': structured_rows,
            'metadata': {
                'column_count': table['column_count'],
                'row_count': table['row_count'],
                'is_ragged': table.get('is_ragged', False),
                'alignment': table['align']
            }
        }
        
        table_data.append(table_info)
    
    return table_data
```

## Best Practices

### Security
1. Always use appropriate security profiles for your use case
2. Validate content before parsing when dealing with untrusted input
3. Check security warnings in the results
4. Use sanitization for RAG ingestion
5. Monitor for prompt injection attempts

### Performance
1. Cache parser instances when processing similar content
2. Use content validation for quick checks
3. Leverage the universal recursion engine for custom processing
4. Consider using streaming for very large documents

### Error Handling
1. Always wrap parsing in try-catch blocks
2. Handle security errors appropriately
3. Check plugin availability before relying on features
4. Validate content size limits for your use case

This manual covers the core functionality of MarkdownParserCore. The library is designed to be both powerful and secure, making it ideal for AI applications that need to process markdown content safely.
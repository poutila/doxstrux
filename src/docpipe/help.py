"""
Interactive help system for docpipe.

This module provides comprehensive help functions for both human users and AI assistants
to understand and use docpipe's markdown enrichment capabilities.
"""

from typing import Any

# Version information
__version__ = "0.1.0"


class DocpipeHelpSystem:
    """Interactive help system for markdown enrichment."""

    def __init__(self) -> None:
        self.help_data = self._load_help_data()
        self.examples_data = self._load_examples_data()

    def _load_help_data(self) -> dict[str, Any]:
        """Load help metadata for docpipe."""
        return {
            "topics": {
                "basics": {
                    "title": "Getting Started",
                    "description": "Basic usage of docpipe for markdown enrichment",
                    "examples": ["basic_usage", "simple_analysis"],
                },
                "lists": {
                    "title": "Nested Lists",
                    "description": "Working with nested lists (up to 3 levels deep)",
                    "examples": ["nested_lists", "task_lists", "mixed_lists"],
                },
                "code_blocks": {
                    "title": "Code Block Extraction",
                    "description": "Extracting and processing code blocks with language detection",
                    "examples": ["extract_code", "language_detection"],
                },
                "tables": {
                    "title": "Table Processing",
                    "description": "Parsing complex markdown tables including GFM and HTML",
                    "examples": ["simple_tables", "complex_tables"],
                },
                "requirements": {
                    "title": "Requirements Detection",
                    "description": "Extracting MUST/SHOULD/MAY requirement patterns",
                    "examples": ["requirement_patterns", "rfc_keywords"],
                },
                "ai_integration": {
                    "title": "AI Integration",
                    "description": "Using docpipe with AI systems for preprocessing",
                    "examples": ["ai_preprocessing", "json_output"],
                },
                "performance": {
                    "title": "Performance",
                    "description": "Performance characteristics and optimization",
                    "examples": ["large_files", "batch_processing"],
                },
                "troubleshooting": {
                    "title": "Troubleshooting",
                    "description": "Common issues and their solutions",
                    "examples": ["common_errors", "debugging"],
                },
            },
            "capabilities": {
                "max_nesting_depth": 3,
                "supported_languages": [
                    "python",
                    "javascript",
                    "typescript",
                    "java",
                    "c++",
                    "go",
                    "rust",
                ],
                "table_formats": ["gfm", "pipe", "html"],
                "performance": {
                    "typical_speed": "< 1 second for 1000 lines",
                    "memory_usage": "< 10MB for typical documents",
                },
            },
            "api": {
                "classes": [
                    "MarkdownDocEnricher",
                    "MarkdownDocExtendedRich",
                    "CodeBlock",
                    "ListItem",
                    "MarkdownList",
                ],
                "functions": [
                    "extract_rich_doc",
                    "extract_code_blocks",
                    "validate_markdown",
                    "get_markdown_stats",
                ],
            },
        }

    def _load_examples_data(self) -> dict[str, str]:
        """Load code examples for docpipe usage."""
        return {
            "basic_usage": """
from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher

# Create enricher
enricher = MarkdownDocEnricher(Path("README.md"))

# Extract enriched document
doc = enricher.extract_rich_doc()

# Access structured data
print(f"Sections: {len(doc.sections)}")
print(f"Code blocks: {len(doc.code_blocks)}")
print(f"Max nesting: {doc.max_nesting_depth}")
""",
            "nested_lists": """
# Docpipe handles nested lists up to 3 levels deep

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher

enricher = MarkdownDocEnricher(Path("document.md"))
doc = enricher.extract_rich_doc()

# Access nested list structures
for section in doc.sections:
    if section.lists:
        for list_obj in section.lists:
            print(f"List type: {list_obj.type}")
            for item in list_obj.items:
                print(f"  Level {item.level}: {item.text}")
                if item.children:
                    # Process nested items
                    for child in item.children:
                        print(f"    Level {child.level}: {child.text}")
""",
            "extract_code": """
# Extract code blocks with metadata

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher

enricher = MarkdownDocEnricher(Path("technical_doc.md"))
doc = enricher.extract_rich_doc()

# Get all code blocks
for code_block in doc.code_blocks:
    print(f"Language: {code_block.language}")
    print(f"Section: {code_block.section_slug}")
    print(f"Line start: {code_block.line_start}")
    print(f"Content: {code_block.content[:100]}...")

# Filter by language
python_blocks = [cb for cb in doc.code_blocks if cb.language == "python"]
""",
            "ai_preprocessing": """
# Prepare markdown for AI consumption

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher
import json

enricher = MarkdownDocEnricher(Path("documentation.md"))
doc = enricher.extract_rich_doc()

# Convert to JSON for AI processing
json_output = doc.model_dump_json(indent=2)

# Or get specific structured data
ai_ready = {
    "content": doc.content,
    "structure": {
        "sections": len(doc.sections),
        "code_blocks": len(doc.code_blocks),
        "requirements": len(doc.requirements),
    },
    "code_samples": [
        {
            "language": cb.language,
            "content": cb.content
        }
        for cb in doc.code_blocks[:5]  # First 5 code blocks
    ],
    "metadata": doc.metadata,
}

# Save for AI processing
with open("ai_input.json", "w") as f:
    json.dump(ai_ready, f, indent=2)
""",
            "requirement_patterns": """
# Extract RFC-style requirements

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher

enricher = MarkdownDocEnricher(Path("specification.md"))
doc = enricher.extract_rich_doc()

# Get all requirements
for req in doc.requirements:
    print(f"{req.type}: {req.rule_text}")
    print(f"  Source: {req.source_block}")

# Filter by requirement level
must_requirements = [r for r in doc.requirements if r.type == "MUST"]
should_requirements = [r for r in doc.requirements if r.type == "SHOULD"]

print(f"MUST requirements: {len(must_requirements)}")
print(f"SHOULD requirements: {len(should_requirements)}")
""",
            "large_files": """
# Handle large markdown files efficiently

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher
import time

file_path = Path("large_document.md")
print(f"File size: {file_path.stat().st_size / 1024:.2f} KB")

start_time = time.time()
enricher = MarkdownDocEnricher(file_path)
doc = enricher.extract_rich_doc()
elapsed = time.time() - start_time

print(f"Processing time: {elapsed:.2f} seconds")
print(f"Lines processed: {doc.content.count(chr(10))}")
print(f"Speed: {doc.content.count(chr(10)) / elapsed:.0f} lines/second")
""",
            "batch_processing": '''
# Process multiple markdown files efficiently

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher
import concurrent.futures

def process_file(file_path):
    """Process a single markdown file."""
    try:
        enricher = MarkdownDocEnricher(file_path)
        doc = enricher.extract_rich_doc()
        return {
            "file": file_path.name,
            "sections": len(doc.sections),
            "code_blocks": len(doc.code_blocks),
        }
    except Exception as e:
        return {"file": file_path.name, "error": str(e)}

# Process directory of markdown files
md_files = list(Path("docs").glob("**/*.md"))

# Parallel processing
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(process_file, md_files))

for result in results:
    if "error" not in result:
        print(f"✅ {result['file']}: {result['sections']} sections")
''',
            "validation_example": """
# Validate markdown document structure

from pathlib import Path
from docpipe.diagnostics import diagnose_markdown

# Check document for issues
result = diagnose_markdown(Path("document.md"), verbose=True)

if result.status == "ok":
    print("✅ Document is valid")
elif result.status == "warning":
    print("⚠️ Warnings found:")
    for warning in result.potential_issues:
        print(f"  - {warning}")
else:
    print("❌ Document has errors")
""",
            "error_handling": '''
# Robust error handling with helpful messages

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher
from docpipe.help import help_for_error

def safe_process(file_path):
    """Process markdown with error handling."""
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        enricher = MarkdownDocEnricher(file_path)
        doc = enricher.extract_rich_doc()
        print(f"✅ Processed {file_path.name}")
        return doc
        
    except Exception as e:
        help_text = help_for_error(e)
        print(f"❌ Error: {e}")
        print(f"💡 Help: {help_text}")
        return None

doc = safe_process(Path("document.md"))
''',
            "parallel_execution": '''
# Parallel processing for better performance

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher
import concurrent.futures
import time

def time_sequential(files):
    """Process files sequentially."""
    start = time.time()
    results = []
    for f in files:
        enricher = MarkdownDocEnricher(f)
        results.append(enricher.extract_rich_doc())
    return time.time() - start

def time_parallel(files):
    """Process files in parallel."""
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(MarkdownDocEnricher(f).extract_rich_doc) 
                   for f in files]
        results = [f.result() for f in futures]
    return time.time() - start

files = list(Path("docs").glob("*.md"))[:10]
seq_time = time_sequential(files)
par_time = time_parallel(files)
print(f"Sequential: {seq_time:.2f}s")
print(f"Parallel: {par_time:.2f}s")
print(f"Speedup: {seq_time/par_time:.1f}x")
''',
            "structure_validation": """
# Validate document structure and hierarchy

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher

enricher = MarkdownDocEnricher(Path("document.md"))
doc = enricher.extract_rich_doc()

# Check heading structure
if doc.heading_structure_valid:
    print("✅ Heading hierarchy is valid")
else:
    print("❌ Invalid heading hierarchy detected")

# Check for empty sections
empty_sections = [s for s in doc.sections if not s.content.strip()]
if empty_sections:
    print(f"⚠️ Found {len(empty_sections)} empty sections")

# Check nesting depth
max_depth = 0
for section in doc.sections:
    if section.lists:
        for lst in section.lists:
            for item in lst.items:
                max_depth = max(max_depth, item.level)

if max_depth > 3:
    print(f"⚠️ Nesting depth {max_depth} exceeds recommended maximum of 3")
else:
    print(f"✅ Nesting depth ({max_depth}) is within limits")
""",
            "link_checking": """
# Check and validate links in markdown

from pathlib import Path
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher

enricher = MarkdownDocEnricher(Path("document.md"))
doc = enricher.extract_rich_doc()

# Check link validity
if doc.all_links_exist:
    print("✅ All file links are valid")
else:
    print("❌ Found invalid links:")
    for link in doc.invalid_file_links:
        print(f"  - {link}")

# Check for broken anchors
if doc.invalid_anchor_links:
    print("⚠️ Invalid anchor links:")
    for anchor in doc.invalid_anchor_links:
        print(f"  - {anchor}")

# Summary of all links
total_links = sum(len(v) for v in doc.links.values())
print(f"\nTotal links found: {total_links}")
for link_type, links in doc.links.items():
    if links:
        print(f"  {link_type}: {len(links)}")
""",
            "cli_commands": """
# Command-line usage examples

# Basic analysis
docpipe analyze README.md
docpipe analyze README.md --format json --output analysis.json

# Extract specific elements
docpipe extract code document.md --language python
docpipe extract requirements specs.md
docpipe extract lists nested_doc.md --max-depth 2
docpipe extract tables data.md --output tables.json

# Batch processing
docpipe batch "*.md" --recursive --format json
docpipe batch "*.md" --parallel --has-code
docpipe batch "docs/*.md" --filter-requirements MUST

# Diagnostics and validation
docpipe diagnose complex_doc.md --suggest-fixes
docpipe validate document.md --max-nesting 3 --quiet
docpipe stats docs/ --recursive --compare

# Get help and examples
docpipe help lists
docpipe examples nested_lists --run
docpipe metadata  # AI-friendly capability info
docpipe setup     # Validate environment
docpipe quickstart  # Show getting started guide
""",
        }


def help_docpipe(topic: str | None = None) -> None:
    """
    Show interactive help for docpipe.

    Args:
        topic: Specific help topic. If None, shows main help menu.

    Available topics: basics, lists, code_blocks, tables, requirements,
                     ai_integration, performance, troubleshooting
    """
    help_system = DocpipeHelpSystem()

    if topic is None:
        _show_main_help(help_system)
    elif topic in help_system.help_data["topics"]:
        _show_topic_help(help_system, topic)
    else:
        print(f"Unknown help topic: {topic}")
        print("Available topics:", ", ".join(help_system.help_data["topics"].keys()))


def _show_main_help(help_system: DocpipeHelpSystem) -> None:
    """Show main help menu."""
    print("📚 Docpipe Help System")
    print("=" * 50)
    print(f"Version: {__version__}")
    print("\nA comprehensive markdown enrichment tool for humans and AI systems")
    print()
    print("📖 Available Help Topics:")
    print()

    for topic, info in help_system.help_data["topics"].items():
        print(f"  {topic:18} - {info['description']}")

    print()
    print("💡 Usage:")
    print("  help_docpipe('topic')        # Get help on specific topic")
    print("  show_examples('topic')       # Show code examples")
    print("  diagnose_markdown('file')    # Analyze markdown file")
    print("  get_ai_metadata()           # Get capabilities for AI")
    print()
    print("🚀 Quick Start:")
    print("  from docpipe import MarkdownDocEnricher")
    print("  enricher = MarkdownDocEnricher(Path('README.md'))")
    print("  doc = enricher.extract_rich_doc()")
    print()
    print("📊 Capabilities:")
    caps = help_system.help_data["capabilities"]
    print(f"  Max nesting depth: {caps['max_nesting_depth']} levels")
    print(f"  Speed: {caps['performance']['typical_speed']}")
    print(f"  Memory: {caps['performance']['memory_usage']}")


def _show_topic_help(help_system: DocpipeHelpSystem, topic: str) -> None:
    """Show help for specific topic."""
    topic_info = help_system.help_data["topics"][topic]

    print(f"📖 {topic_info['title']}")
    print("=" * 50)
    print(topic_info["description"])
    print()

    if "examples" in topic_info:
        print("💡 Related Examples:")
        for example_key in topic_info["examples"]:
            if example_key in help_system.examples_data:
                print(f"\n--- {example_key.replace('_', ' ').title()} ---")
                code = help_system.examples_data[example_key].strip()
                print(code)
            else:
                print(f"  • {example_key} (run show_examples('{example_key}'))")

    print("\n🔗 For more: help_docpipe() or see USER_GUIDE.md")


def show_examples(topic: str | None = None) -> None:
    """
    Show code examples for docpipe usage.

    Args:
        topic: Specific example topic or None to list all
    """
    help_system = DocpipeHelpSystem()

    if topic is None:
        print("📝 Available Code Examples:")
        print("=" * 40)
        for key in help_system.examples_data:
            title = key.replace("_", " ").title()
            print(f"  • {key:20} - {title}")
        print("\n💡 Usage: show_examples('example_name')")
        return

    if topic in help_system.examples_data:
        print(f"📝 Example: {topic.replace('_', ' ').title()}")
        print("=" * 40)
        code = help_system.examples_data[topic].strip()
        print(code)
    else:
        print(f"Example '{topic}' not found.")
        print("Available:", ", ".join(help_system.examples_data.keys()))


def get_ai_metadata() -> dict[str, Any]:
    """
    Get machine-readable metadata for AI assistants.

    Returns:
        Complete docpipe capabilities and API information
    """
    help_system = DocpipeHelpSystem()
    return {
        "version": __version__,
        "description": "Markdown enrichment tool with 3-level nesting support",
        "capabilities": help_system.help_data["capabilities"],
        "api": help_system.help_data["api"],
        "topics": list(help_system.help_data["topics"].keys()),
        "examples": list(help_system.examples_data.keys()),
        "features": {
            "nested_lists": "3-level deep nesting for all list types",
            "code_extraction": "Language detection and metadata",
            "table_parsing": "GFM, pipe, and HTML table support",
            "requirements": "MUST/SHOULD/MAY pattern extraction",
            "performance": "< 1 second for 1000-line documents",
        },
    }


def help_for_error(error: Exception) -> str:
    """
    Provide context-specific help for errors.

    Args:
        error: Exception that occurred

    Returns:
        Help text for the error
    """
    error_type = type(error).__name__
    error_message = str(error)

    help_text = [f"🚨 Error: {error_type}"]
    help_text.append(f"Message: {error_message}")
    help_text.append("")

    if "ValidationError" in error_type or "validation" in error_message.lower():
        help_text.append("💡 This is a markdown validation error.")
        help_text.append("Common causes:")
        help_text.append("  • Invalid markdown syntax")
        help_text.append("  • Nesting depth exceeds 3 levels")
        help_text.append("  • Malformed tables or code blocks")
        help_text.append("  • Unclosed lists or quotes")
        help_text.append("")
        help_text.append("Solutions:")
        help_text.append("  1. Run: docpipe diagnose document.md --suggest-fixes")
        help_text.append("  2. Check: docpipe validate document.md --max-nesting 3")
        help_text.append("  3. Review heading hierarchy (no skipped levels)")
        help_text.append("  4. Ensure all code blocks have closing ```")
        help_text.append("")
        help_text.append("Example fix:")
        help_text.append("  from docpipe.diagnostics import diagnose_markdown")
        help_text.append("  result = diagnose_markdown(Path('document.md'))")
        help_text.append("  for issue in result.potential_issues:")
        help_text.append("      print(issue)")

    elif "FileNotFoundError" in error_type:
        help_text.append("💡 The markdown file was not found.")
        help_text.append("Solutions:")
        help_text.append("  1. Check the file path is correct")
        help_text.append("  2. Use Path.cwd() to verify working directory")
        help_text.append("  3. Use absolute paths for clarity")
        help_text.append("")
        help_text.append("Example fix:")
        help_text.append("  from pathlib import Path")
        help_text.append("  file_path = Path('document.md')")
        help_text.append("  if file_path.exists():")
        help_text.append("      enricher = MarkdownDocEnricher(file_path)")
        help_text.append("  else:")
        help_text.append("      print(f'File not found: {file_path.absolute()}')")

    elif "MemoryError" in error_type or "memory" in error_message.lower():
        help_text.append("💡 Document too large for available memory.")
        help_text.append("Solutions:")
        help_text.append("  1. Process file in chunks")
        help_text.append("  2. Use batch processing: docpipe batch '*.md' --parallel")
        help_text.append("  3. Check file size: ls -lh document.md")
        help_text.append("  4. Split large files into sections")
        help_text.append("")
        help_text.append("Performance tip: Files <1MB process in <0.1s")

    elif "encoding" in error_message.lower() or "decode" in error_message.lower():
        help_text.append("💡 File encoding issue detected.")
        help_text.append("Solutions:")
        help_text.append("  1. Check encoding: file -i document.md")
        help_text.append("  2. Convert to UTF-8:")
        help_text.append("     iconv -f ISO-8859-1 -t UTF-8 input.md > output.md")
        help_text.append("  3. Remove non-text content")
        help_text.append("  4. Check for binary data in file")

    elif "permission" in error_message.lower():
        help_text.append("💡 File permission issue.")
        help_text.append("Solutions:")
        help_text.append("  1. Check permissions: ls -la document.md")
        help_text.append("  2. Fix permissions: chmod 644 document.md")
        help_text.append("  3. Check ownership: chown $USER document.md")
        help_text.append("  4. Run with appropriate user permissions")

    elif "nesting" in error_message.lower() or "depth" in error_message.lower():
        help_text.append("💡 Nesting depth issue (max: 3 levels).")
        help_text.append("Solutions:")
        help_text.append("  1. Validate: docpipe validate document.md --max-nesting 3")
        help_text.append("  2. Flatten deeply nested lists")
        help_text.append("  3. Restructure content hierarchy")
        help_text.append("  4. Split into multiple sections")

    else:
        help_text.append("💡 General troubleshooting:")
        help_text.append("  1. Check input file is valid markdown")
        help_text.append("  2. Run: docpipe diagnose document.md")
        help_text.append("  3. Validate: docpipe validate document.md")
        help_text.append("  4. See: docpipe help troubleshooting")
        help_text.append("  5. Example: docpipe examples error_handling")

    return "\n".join(help_text)


def quick_start() -> None:
    """Display quick start guide."""
    print("🚀 Docpipe Quick Start")
    print("=" * 30)
    print("1. Install docpipe:")
    print("   pip install docpipe")
    print()
    print("2. Basic usage:")
    print("   from docpipe import MarkdownDocEnricher")
    print("   from pathlib import Path")
    print("   ")
    print("   enricher = MarkdownDocEnricher(Path('README.md'))")
    print("   doc = enricher.extract_rich_doc()")
    print()
    print("3. Extract specific elements:")
    print("   # Code blocks")
    print("   for code in doc.code_blocks:")
    print("       print(f'{code.language}: {code.content[:50]}...')")
    print()
    print("4. Get help:")
    print("   help_docpipe('basics')")
    print("   show_examples('nested_lists')")
    print()
    print("5. For AI integration:")
    print("   metadata = get_ai_metadata()")
    print("   json_output = doc.model_dump_json()")


if __name__ == "__main__":
    # Show main help when module is run
    help_docpipe()

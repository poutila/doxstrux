# Edge Cases Test Document

## Unicode and Special Characters

### Emoji in Requirements 
The system MUST support emoji 🚀 in text.
Users SHOULD be able to use 😊 emoticons.
The parser MAY handle 🎨🎭🎪 multiple emojis.

### Special Characters in Lists
- Item with special chars: <>&"'
- Math symbols: ∑ ∏ ∫ ∂ ∇
- Currency: $100, €50, £75, ¥1000
- Arrows: → ← ↑ ↓ ⇒ ⇐
  - Nested with more: α β γ δ ε
  - Chemical: H₂O, CO₂, Ca²⁺

### Code with Unicode
```python
def café():
    return "Zürich → München"
    
# Japanese comment: これはテストです
名前 = "田中"
```

## Malformed Markdown (Parser Resilience)

### Unclosed Code Block
```python
def broken():
    # This code block is never closed
    return None

### Mixed List Markers
- Bullet item
* Different bullet marker
+ Yet another marker
- Back to dash
  * Nested with star
  - Nested with dash

### Broken Table
| Col1 | Col2 | Col3
|------|------
| Data | Missing | Separator |
| Row2 
| Row3 | Has | Too | Many | Columns |

## Extreme Nesting Test

- Level 1
  - Level 2
    - Level 3 (our limit)
      - Level 4 (should be treated as text)
        - Level 5 (definitely text)
          - Level 6 (way too deep)
            - Level 7 (parser should not crash)

## Empty Elements Test

### Empty List Items
- 
- Item with content
- 
  - 
  - Nested with content
  - 

### Empty Code Block
```
```

### Empty Table
| | |
|-|-|
| | |

## Inline Code Stress Test

Here's `inline code` followed by more `inline code` and even more `inline code` all in one line with `special <> chars` and `quotes "inside"` plus `backslashes \\ too`.

### List with Inline Code
- Item with `code`
- Another `with` multiple `code` spans
  - Nested `code` with special chars: `<>&"`
  - More `inline` code `everywhere`

## Links and References Test

### Various Link Formats
- [Basic link](http://example.com)
- [Link with title](http://example.com "Title here")
- [Relative link](../docs/README.md)
- [Anchor link](#section-name)
- [Reference link][ref1]
- <http://direct-link.com>
- Plain URL: http://should-not-be-parsed.com

[ref1]: http://reference.com "Reference Title"

### Links in Lists
1. [Link in numbered](http://test.com)
   - [Nested link](../file.md)
     - [Deep nested](#anchor)
2. Multiple [link 1](url1) and [link 2](url2) same item

## Escaping Test

### Escaped Special Characters
- Escaped \* asterisk
- Escaped \# hash
- Escaped \[not a link\](not a url)
- Escaped \`not code\`

### Backslashes
- Single backslash: \
- Double backslash: \\
- Triple: \\\
- In code: `\n\t\r`

## HTML Entities and Raw HTML

### HTML Entities
- Less than: &lt;
- Greater than: &gt;
- Ampersand: &amp;
- Quote: &quot;
- Apos: &apos;
- Non-breaking space: &nbsp;
- Copyright: &copy;

### Raw HTML (if supported)
<div>
This is raw HTML that SHOULD be handled gracefully.
</div>

<script>
// This MUST NOT execute
alert("This should not run");
</script>

## Long Lines Test

This is an extremely long line that contains a requirement: The system MUST handle very long lines without breaking or causing performance issues even when the line goes on and on and on with multiple requirements like SHOULD support streaming and MAY optimize memory usage and MUST NOT crash on extremely long content that keeps going and going with more text and more requirements and potentially causing buffer or memory issues in poorly implemented parsers but our parser MUST handle this gracefully without any problems whatsoever even if the line is thousands of characters long.

## Repeated Pattern Test

MUST MUST MUST MUST MUST - multiple MUSTs in a row
SHOULD NOT SHOULD NOT SHOULD NOT - repeated SHOULD NOTs
MAY MAY MAY MAY - multiple MAYs

## Case Sensitivity Test

### Mixed Case Requirements
- The system must handle lowercase
- The system MUST handle uppercase
- The system Must handle mixed case
- The system MuSt handle weird case
- The system should HANDLE various cases
- The system SHOULD handle normal case
- The system SHOulD handle odd case

## Numbers and Requirements

### Requirements with Numbers
1. MUST support 100% uptime
2. SHOULD handle 1,000,000 requests
3. MAY cache for 3.14159 seconds
4. MUST NOT exceed 2^32 bytes
5. SHOULD process in <100ms

## Comments in Code Blocks

```python
# This comment has a requirement: MUST parse comments
def function():
    """
    Docstring with requirement: SHOULD document well
    """
    # TODO: MUST fix this later
    pass  # MUST NOT remove this
```

```javascript
// JavaScript comment: MUST support JS
/* 
   Multi-line comment
   SHOULD handle this too
*/
const x = 42; // Inline comment: MAY be useful
```

## Nested Blockquotes

> Level 1 quote
> > Level 2 quote with requirement: MUST nest
> > > Level 3 quote that SHOULD work
> > > > Level 4 quote MAY be too deep
> > > > > Level 5 definitely too deep but MUST NOT crash

## Mixed Indentation (Tabs vs Spaces)

	- Tab indented item
  - Space indented item
	  - Tab nested
    - Space nested
		- More tabs
      - More spaces

## Finally: Kitchen Sink

This final section has everything: **bold**, *italic*, ***both***, `code`, [links](http://test.com), requirements that MUST work, lists below:

- [ ] Task one
- [x] Task two with `code` and [link](url)
  > Quote in list
  ```python
  # Code in list after quote
  print("Complex MUST work")
  ```
  | Table | In | List |
  |-------|----|----|
  | With  | Data | SHOULD parse |
  
  1. Numbered in bullet
     - Bullet in numbered
       - Deep nesting MAY confuse
  2. But MUST NOT fail

---

The document ends with a horizontal rule and a final requirement: The parser MUST successfully process this entire edge cases document without errors!
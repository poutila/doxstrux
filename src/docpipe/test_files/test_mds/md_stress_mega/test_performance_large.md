# Large Document Performance Test

This document tests performance with many sections and repeated content.

## Section 1 of 100

This section contains various markdown elements to test parsing performance at scale.

### Requirements
- The system MUST handle large documents efficiently
- Processing SHOULD complete within reasonable time
- Memory usage MAY be optimized for large files

### Code Block
```python
def section_1():
    """Process section 1."""
    return "Section 1 processed"
```

### List
- Item 1
  - Nested 1.1
    - Nested 1.1.1
  - Nested 1.2
- Item 2

### Table
| Column A | Column B | Column C |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

---

## Section 2 of 100

Repeating similar content with variations.

### Requirements
- The parser MUST NOT slow down with repetitive content
- It SHOULD maintain consistent performance
- Caching MAY improve processing speed

### Code Block
```javascript
function section2() {
    // Process section 2
    return "Section 2 processed";
}
```

### List
- Different item A
  - Sub-item A.1
    - Deep item A.1.1
  - Sub-item A.2
- Different item B

---

## Section 3 of 100

### Task List
- [ ] Task for section 3
- [x] Completed task
  - [ ] Nested incomplete
  - [x] Nested complete

### Requirements
- Performance MUST scale linearly
- Memory SHOULD NOT grow exponentially
- The parser MAY use streaming

---

## Section 4 of 100

### Mixed Content
Here's a paragraph with **bold**, *italic*, and `inline code`. The system MUST handle mixed formatting efficiently even in large documents.

> Blockquote with a requirement: SHOULD parse quotes quickly

---

## Section 5 of 100

### Nested Lists Performance Test
1. Numbered item 1
   1. Nested 1.1
      1. Deep 1.1.1
      2. Deep 1.1.2
   2. Nested 1.2
2. Numbered item 2
   - Bullet in numbered
     - Nested bullet
   - Another bullet

---

## Section 6 of 100

### Large Table Test
| Header 1 | Header 2 | Header 3 | Header 4 | Header 5 |
|----------|----------|----------|----------|----------|
| Cell 1,1 | Cell 1,2 | Cell 1,3 | Cell 1,4 | Cell 1,5 |
| Cell 2,1 | Cell 2,2 | Cell 2,3 | Cell 2,4 | Cell 2,5 |
| Cell 3,1 | Cell 3,2 | Cell 3,3 | Cell 3,4 | Cell 3,5 |
| Cell 4,1 | Cell 4,2 | Cell 4,3 | Cell 4,4 | Cell 4,5 |
| Cell 5,1 | Cell 5,2 | Cell 5,3 | Cell 5,4 | Cell 5,5 |

---

## Section 7 of 100

### Multiple Code Blocks
```python
# First code block
def process_seven():
    pass
```

```javascript
// Second code block
function processSeven() {}
```

```bash
# Third code block
echo "Section 7"
```

---

## Section 8 of 100

### Complex Requirements
The system MUST handle multiple requirements in a single paragraph. It SHOULD also detect when there are many requirements close together. Furthermore, it MAY optimize the detection algorithm. However, it MUST NOT miss any valid requirements even in large documents.

---

## Section 9 of 100

### Deeply Nested Mixed Lists
- Level 1 bullet
  1. Level 2 numbered
     - Level 3 bullet
       - Beyond our limit but MUST NOT crash
  2. Level 2 numbered item 2
     - [ ] Level 3 task
     - [x] Level 3 completed task
- Level 1 bullet 2

---

## Section 10 of 100

This pattern continues for 100 sections to test performance.
Each section has similar but slightly different content.
The parser MUST handle all 100 sections efficiently.

---

## Section 11 through 50

[Simulating sections 11-50 with abbreviated content to keep file manageable while still being large]

### Section 11
Content with requirement: MUST process section 11
- List item
  - Nested item
```python
code_11 = True
```

### Section 12
Content with requirement: SHOULD handle section 12
| A | B |
|---|---|
| 1 | 2 |

### Section 13
- [ ] Task 13 MUST be tracked

### Section 14
> Quote 14 SHOULD be parsed

### Section 15
`inline_15` MAY appear

### Section 16
**Bold 16** MUST render

### Section 17
*Italic 17* SHOULD style

### Section 18
[Link 18](#) MUST work

### Section 19
```js
// Code 19
```

### Section 20
1. Numbered 20
2. MUST count

### Section 21-30
[Continuing pattern with variations including all element types:
- Lists (bullet, numbered, task)
- Code blocks (various languages)
- Tables
- Blockquotes
- Requirements
- Inline formatting]

### Section 31-40
[More content following the same pattern, ensuring the document is large enough to test performance while maintaining variety]

### Section 41-50
[Final set of repeated patterns before the conclusion]

---

## Sections 51-99: Bulk Test Data

For sections 51 through 99, we repeat a standard pattern to create document bulk:

### Standard Section Pattern
- The system MUST handle repetitive sections
- Performance SHOULD remain constant
- Memory usage MAY plateau

```python
def process_section(n):
    return f"Section {n} processed"
```

| Metric | Value |
|--------|-------|
| Time   | < 1s  |
| Memory | < 100MB |

- [ ] Process section
- [x] Validate output
  - [ ] Check performance
  - [x] Verify correctness

> Each section contributes to the overall document size and complexity.

[This pattern repeats with minor variations through section 99]

---

## Section 100: Performance Summary

### Final Requirements
- The entire document MUST parse successfully
- Processing time SHOULD be under 5 seconds
- Memory usage MUST NOT exceed reasonable limits
- All 100 sections MUST be accessible
- No data MUST be lost during parsing

### Performance Metrics Table
| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Parse Time | < 1s | < 5s | > 10s |
| Memory | < 50MB | < 200MB | > 500MB |
| Sections | 100 | 100 | < 100 |
| Requirements | All | > 95% | < 90% |

### Conclusion
This large document with 100 sections tests the parser's ability to handle:
1. Repetitive content efficiently
2. Large file sizes
3. Memory management
4. Consistent performance
5. Complete data extraction

The parser MUST successfully process this entire document, maintaining performance and correctness throughout!
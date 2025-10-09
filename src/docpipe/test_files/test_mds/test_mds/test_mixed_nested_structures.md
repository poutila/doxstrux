# Mixed Nested Structures Test

## Complex List with Code and Requirements

1. First item with a requirement: The system MUST handle nested structures
   - Sub-item with code:
     ```python
     def process_nested():
         # This code is inside a nested list
         return "nested"
     ```
   - Another sub-item that SHOULD be processed correctly
     - Third level with inline `code` and a MAY requirement
     - Third level with a table:
       | Header | Value |
       |--------|-------|
       | Data   | 123   |
   
2. Second numbered item
   - [ ] Unchecked task in numbered list
   - [x] Checked task that MUST be tracked
     - Nested under task with requirement: SHOULD NOT miss this
     
## Lists with Blockquotes

- Bullet item with blockquote:
  > This is a quote inside a list
  > The quote MUST be preserved with formatting
  
  - Nested item after blockquote
    > Another nested quote
    > With multiple lines that SHOULD stay together
    
- Another bullet with code after quote:
  > Quote first
  
  ```javascript
  // Code after quote in list
  const test = "complex";
  ```

## Tables with Complex Content

| Feature | Status | Requirement |
|---------|--------|-------------|
| Parsing | ✅ Done | MUST parse all markdown |
| Nesting | 🔄 WIP | SHOULD support 3 levels |
| Tables | ✅ Done | MAY include nested content |
| Code in table | `inline()` | MUST NOT break |

## Mixed Task Lists

### Project Tasks
- [x] Implement parser
  - [x] Basic parsing MUST work
  - [ ] Advanced features SHOULD be added
    - [ ] Feature A MAY be optional
    - [x] Feature B MUST be included
- [ ] Write documentation
  - [ ] User guide MUST be comprehensive
  - [x] API docs SHOULD be auto-generated

## Code Blocks with Different Languages

### Python with Requirements
```python
# This function MUST validate input
def validate(data):
    """The validator SHOULD check all fields."""
    if not data:
        raise ValueError("Data MUST NOT be empty")
    return True
```

### YAML Configuration
```yaml
# This config MUST be valid
version: "3.8"
requirements:
  - MUST: Support Docker
  - SHOULD: Use caching
  - MAY: Include monitoring
```

### SQL with Comments
```sql
-- This query MUST be optimized
SELECT * FROM users
WHERE status = 'active'  -- SHOULD filter properly
  AND created > '2024-01-01';  -- MAY need index
```

## Edge Case: Empty Sections

## 

## Section with Only Whitespace

   

## Requirements in Various Contexts

This paragraph has multiple requirements. First, the system MUST handle inline requirements. Second, it SHOULD detect multiple patterns in one block. Third, it MAY optimize for performance. Finally, it MUST NOT lose any data.

### Requirements in Headers MUST Be Detected

Even headers can contain requirements that SHOULD be found.

#### Deep Nesting MAY Contain Requirements

At any level, requirements MUST be extracted.

> Blockquotes also contain requirements:
> - The parser MUST handle quoted lists
> - It SHOULD preserve formatting
> - It MAY add metadata

**Bold text with requirement: MUST work**
*Italic text saying SHOULD process correctly*
***Bold italic claiming MAY be styled***

## Complex Numbered Lists

1. First level item
   1. Second level item 1.1
      1. Third level item 1.1.1 MUST be captured
      2. Third level item 1.1.2 SHOULD work
   2. Second level item 1.2
      1. Third level item 1.2.1
         - Mixing bullet in numbered list
         - Another bullet that MAY confuse parser
2. Back to first level
   a. Letter sub-item (if supported)
   b. Another letter item
      i. Roman numeral (edge case)
      ii. Another roman

## Final Test: Everything Combined

Here's a paragraph with a requirement: The enricher MUST handle this complex document.

- A list starts here
  ```python
  # Code in list
  def test():
      pass
  ```
  > Quote in list after code
  > MUST handle this
  
  | Table | In | List |
  |-------|----|----|
  | Yes   | It | SHOULD |
  
  - [ ] Task in same list
  - [x] Checked task MUST track
    - Nested continuation
      - Third level still going
        
And back to normal text with inline `code` and a final requirement: The parser MUST NOT fail on this document!
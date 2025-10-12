# tests_normalize_yaml_like_blocks.py
import pytest
from normalize_yaml_like_blocks import strip_front_matter_strict, normalize_yaml_like_blocks, prepare_content_raw

def test_strips_bof_front_matter_only():
    md = """---
title: x
---
# Heading
"""
    assert prepare_content_raw(md) == "# Heading\n"

def test_does_not_strip_whitespacey_fence_at_bof():
    md = """---   \n
# Heading
"""
    # Not exact '---\\n' at BOF, thus not stripped
    assert prepare_content_raw(md) == md.replace("\r\n","\n").replace("\r","\n")

def test_midfile_yaml_like_block_normalized():
    md = """# A

---
title: Example
---
Body
"""
    want = """# A

---
title: Example

---

Body
"""
    assert prepare_content_raw(md) == want

def test_midfile_yaml_like_block_with_code_fence_not_touched():
    md = """X

---
code: |
  ```sh
  echo hi
  ```
---
Y
"""
    # Detected as looks_like_code, not normalized
    assert prepare_content_raw(md) == md.replace("\r\n","\n").replace("\r","\n")

def test_multiple_blank_lines_collapsed_to_one():
    md = """P

---
a: b


---


Q
"""
    want = """P

---
a: b

---

Q
"""
    assert prepare_content_raw(md) == want

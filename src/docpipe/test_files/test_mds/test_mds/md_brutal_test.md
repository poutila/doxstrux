# 🧪 BRUTAL Markdown Parser Torture Test

A deliberately gnarly Markdown file to stress-test renderers and parsers.  
**Goal:** nest a wide variety of elements to **depth = 4** and mix syntaxes.  
> Note: CommonMark does **not** allow “paragraph inside paragraph”. We simulate via HTML containers (`<div><p>`…`</p></div>`).

---

## 0. Global Reference Links and Assets

This doc uses reference-style links and images:

- Link ref: [MD Spec][spec]
- Image ref: ![Ref Logo][logo]
- Autolink: <https://example.org>
- Escapes: \*not italic\* \_not italic\_ \`not code\`

[spec]: https://spec.commonmark.org/
[logo]: https://via.placeholder.com/80x40.png?text=MD

---

## 1) Depth‑4: Blockquote → List → Blockquote → Paragraph (+inline styles)

> **L1** Blockquote
> - **L2** List item with mixed _inline_ **markdown** and `code`
>   > **L3** Nested quote with a [link](https://example.com) and an image ![img](https://via.placeholder.com/30)
>   >
>   > - **L4** List item as deepest level — *emphasis* with `code` and ~~strikethrough~~
>   >
>   >   Paragraph at depth 4 that includes **_bold italic_**, `inline_code`, and a footnote marker[^deep1].
>
> Back to L1 paragraph.

[^deep1]: Footnote attached to a depth‑4 paragraph.


---

## 2) Depth‑4: List → List → Blockquote → Fenced Code

1. **L1** Ordered
   - **L2** Unordered
     > **L3** Quote wrapping code block below
     >
     > ```python
     > # L4 fenced code
     > def depth_four(a: int) -> int:
     >     return (a ** 2) // 3  # simulate work
     > ```
2. Continue list after deep structure.


---

## 3) Depth‑4: Quote → List → List → Task Checklist

> **L1** Quote
> - **L2** Bullet group
>   1. **L3** Numbered group
>      - [ ] **L4** task *unchecked*
>      - [x] **L4** task **checked**
>      - [ ] **L4** task with subtext  
>            Plain continuation line.


---

## 4) Depth‑4: Quote → List → Quote → Table (yes, inside a quote)

> **L1** Quote starts a table nest
> - **L2** Pre-table note
>   > **L3** Inner quote containing table:
>   >
>   > | **L4 Col A** | **L4 Col B** |
>   > |:------------:|:------------:|
>   > | `code`       | ~~strike~~    |
>   > | *italics*    | **bold**      |


---

## 5) Depth‑4: List → Quote → List → Fenced Code (tildes inside backticks test)

- **L1**
  > **L2** Quote
  > - **L3** Bullet
  >   ```
  >   ~~~
  >   L4 raw block fenced with tildes (shown inside triple‑backtick fence)
  >   ~~~
  >   ```


---

## 6) Depth‑4: HTML Containers to Simulate Paragraph‑in‑Paragraph

<div>
  <p><strong>L1 DIV→P.</strong> Contains a list nesting next.</p>
  <ul>
    <li><em>L2 UL→LI.</em>
      <blockquote>
        <p><code>L3 QUOTE→P</code> wrapping an inner container.</p>
        <div>
          <p><u>L4 DIV→P.</u> Final inline <a href="https://example.com">link</a> and <img src="https://via.placeholder.com/24" alt="img" />.</p>
        </div>
      </blockquote>
    </li>
  </ul>
</div>


---

## 7) Depth‑4: List → Task List → Quote → Indented Code Block

- **L1** Top
  - [ ] **L2** Task
    > **L3** Quote intro
    >
        # L4 indented code block (not fenced)
        for i in range(3):
            print(i)


---

## 8) Depth‑4: Blockquote → Heading → List → Blockquote (Headings in quotes)

> ### **L2** Heading inside quote (L1)
> - **L3** Bullet under heading
>   > **L4** Final quoted line with `inline_code`


---

## 9) Depth‑4: Complex Inline Mix + Table in List → Quote

- **L1** Start with inline: **bold** *italic* `code` [ref][spec]
  > **L2** Quote for context
  > - **L3** List hosting a table next:
  >
  >   | L4 A | L4 B |
  >   |------|------|
  >   | <sub>sub</sub> | <sup>sup</sup> |
  >   | <kbd>Esc</kbd> | <mark>mark</mark> |


---

## 10) Depth‑4: Details/Summary (HTML) → List → Quote → Code

<details>
  <summary><strong>L1</strong> details summary</summary>

  - <em>L2</em> list item inside details
    > <strong>L3</strong> quoted block explaining final code:
    >
    > ```json
    > {
    >   "level": 4,
    >   "message": "Deeply nested JSON block inside HTML → list → quote → code"
    > }
    > ```
</details>


---

## 11) Links, Images, Footnotes, Smart Punctuation, Entities

- Plain [link](https://example.com), reference link [spec], image ![inline](https://via.placeholder.com/20)
- Smart quotes: “curly”, dashes: en–dash, em—dash
- HTML entities: &copy; &amp; &lt; &gt; &nbsp;
- Footnote call[^a] and repeated call[^a].
- Definition list (HTML):
  <dl>
    <dt>Term</dt>
    <dd>Definition line 1<br/>Definition line 2</dd>
  </dl>

[^a]: A single footnote referenced twice.


---

## 12) Edge Cases: Tight/Loose Lists, HTML Comments, Escapes

- Tight item 1
- Tight item 2
  <!-- HTML comment between items -->
- Tight item 3

1. Loose ordered item 1

   Paragraph in between makes list **loose**.

2. Loose ordered item 2 with a blockquote:

   > Nested quote after blank line.

Backslash escape test: \\* \\_ \\` \\# \\[ \\] \\( \\)


---

## 13) Code Fences Within Lists and Quotes (language hints)

> - ```bash
>   # L3 fenced code inside quote / list
>   set -euo pipefail
>   printf '%s\n' "Depth 4 imminent"
>   ```


---

## 14) Table With Alignment, Inline Pipes, and Code

| Left align | Center | Right |
|:-----------|:------:|------:|
| `|` pipe   | `\|`   |  1234 |
| text \| more | **bold** |  -3.14 |


---

## 15) Raw HTML Block With Nested Markdown (often ignored)

<section>
  <h4>L1 HTML section</h4>
  <ul>
    <li>L2 item with <em>inline</em> markdown</li>
    <li>
      <blockquote>
        <p>L3 quoted HTML paragraph with <code>code</code>.</p>
        <pre><code>L4 pre/code — raw, not parsed as MD</code></pre>
      </blockquote>
    </li>
  </ul>
</section>


---

## 16) Para→List→Para Sandwich (renderer-dependent)

Paragraph before list.

- Bullet 1
  Continuation line as part of same list item paragraph.
- Bullet 2

Paragraph after list.


---

## 17) Math-ish (literal; let your renderer decide)

Inline: `$E = mc^2$` vs escaped: \$E = mc^2\$.

Block (fenced, not math-aware here):
```tex
% Depth-agnostic fenced block
\begin{align}
  a^2 + b^2 &= c^2 \\
  \alpha + \beta &= \gamma
\end{align}
```


---

## 18) The Kitchen Sink at Depth 4 (all-in-one)

> **L1**
> - **L2** bullet with [link][spec] and `code`
>   > **L3**
>   > 1. **L4** ordered item with a tiny table:
>   >
>   >    | k | v |
>   >    |---|---|
>   >    | a | 1 |
>   >
>   >    and a fenced block:
>   >
>   >    ```yaml
>   >    level: 4
>   >    ok: true
>   >    ```
>   >
>   >    plus a checklist:
>   >
>   >    - [x] done
>   >    - [ ] todo


---

## 19) Final Sanity: HRs, Thematic Breaks, & EOF

---
***
___

_EOF_

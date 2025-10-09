# 🧪 BRUTAL Markdown Parser Torture Test

A deliberately gnarly Markdown file to stress-test renderers and parsers.  
**Goal:** nest a wide variety of elements to **depth = 4** and mix syntaxes.  
> Note: CommonMark does **not** allow “paragraph inside paragraph”. We simulate via HTML containers (`<div><p>`…`</p></div>`).

---

## 0. Global Reference Links and Assets

This doc uses reference-style links and images:

- Link ref: [MD Spec][spec]
- Image ref: ![Ref Logo][logo]
- Autolink: 
- Escapes: \*not italic\* \_not italic\_ \`not code\`

[spec]: https://spec.commonmark.org/
[logo]: https://via.placeholder.com/80x40.png?text=MD

---

## 1) Depth‑4: Blockquote → List → Blockquote → Paragraph (+inline styles)

> **L1** Blockquote
> - **L2** List item with mixed _inline_ **markdown** and `code`
>   > **L3** Nested quote with a [link](https://example.com) and an image ![img](https://via.placeholder.com/30)
>   >
>   > - **L4** List item as deepest level — *emphasis* with `code` and strikethrough
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
>   > | `code`       | strike    |
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







  - <em>L2</em> list item inside details
    > <strong>L3</strong> quoted block explaining final code:
    >
    > ```json
    > {
    >   "level": 4,
    >   "message": "Deeply nested JSON block inside HTML → list → quote → code"
    > }
    > ```








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
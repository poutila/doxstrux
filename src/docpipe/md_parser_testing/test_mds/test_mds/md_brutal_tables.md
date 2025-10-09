# 🧪 BRUTAL Markdown Test — Nested Tables Edition

This file is designed to **break** Markdown table renderers by abusing **HTML tables inside Markdown tables**, nested blockquotes, lists, and code blocks — up to **depth 4**.  
If your renderer sanitizes HTML, many nested tables will be flattened or removed.

---

## 0) Reference Links & Assets
We’ll reuse refs: [CommonMark][cm], [GFM][gfm], logo: ![logo][logo]

[cm]: https://spec.commonmark.org/
[gfm]: https://github.github.com/gfm/
[logo]: https://via.placeholder.com/60x20?text=MD

---

## 1) Depth‑4: Quote → List → Quote → **Markdown Table** w/ **HTML nested table**

> **L1** Quote
> - **L2** List item leading to inner quote
>   > **L3** Quote wrapping an outer Markdown table:
>   >
>   > | Outer A | Outer B |
>   > |:-------:|:-------:|
>   > | plain   | <table>
>   >   <thead>
>   >     <tr><th>Nested A1</th><th>Nested A2</th></tr>
>   >   </thead>
>   >   <tbody>
>   >     <tr><td><strong>L4</strong> Cell 1</td><td><em>L4</em> Cell 2</td></tr>
>   >     <tr><td colspan="2">
>   >       <table>
>   >         <tr><td>Nested‑2 A</td><td>Nested‑2 B</td></tr>
>   >         <tr><td>
>   >           <table>
>   >             <tr><td>Nested‑3 X</td><td>Nested‑3 Y</td></tr>
>   >           </table>
>   >         </td><td>
>   >           <code>Inline code at nested‑2 depth</code>
>   >         </td></tr>
>   >       </table>
>   >     </td></tr>
>   >   </tbody>
>   > </table> |
>   >
>   > Row below nested table:
>   > | `code` | **bold** |


---

## 2) Depth‑4: **Markdown Table** → Cell contains **List → Quote → Code**

| Col A | Col B |
|------:|:------|
| 12345 | - **L1** bullet in table cell  
|       |   > **L2** quote in table cell  
|       |   > - **L3** list within quote  
|       |   >   ```js
|       |   >   // L4 fenced code inside the quoted list
|       |   >   export const deep = 4;
|       |   >   ``` |


---

## 3) Depth‑4: **Markdown Table** → Cell contains **HTML table** → Cell contains **Markdown table**

| Level | Content |
|:-----:|:--------|
| L1    | <table>
|       |   <tr>
|       |     <td>HTML‑L2
|       |       <table>
|       |         <tr><th>MD‑L3 A</th><th>MD‑L3 B</th></tr>
|       |         <tr><td>
|       |           
|       |           | L4 key | L4 val |
|       |           |:------:|:------:|
|       |           | a      | 1      |
|       |         
|       |         </td><td>
|       |           Nested paragraph with **bold**, *italic*, and `code`.
|       |         </td></tr>
|       |       </table>
|       |     </td>
|       |   </tr>
|       | </table> |


---

## 4) Depth‑4: Quote → **Markdown table** → Cell contains **Checklist** w/ continuation

> Outer context
>
> | Task         | Status |
> |--------------|--------|
> | Subtasks     | - [ ] L1 todo  
> |              |   - [x] L2 done  
> |              |   - [ ] L2 todo  
> |              |     - [ ] L3 deeper  
> |              |       - [x] **L4 deepest** (done)  |
>
> End of quote.


---

## 5) Depth‑4: **List → Markdown Table → HTML table → Fenced Code**

- **Phase 1 (L1)** intro paragraph.
  - **Phase 2 (L2)** we drop a table:
    | K | V |
    |---|---|
    | A | <table>
    |   |   <tr><td>HTML L3: value A</td></tr>
    |   |   <tr><td>
    |   |     <pre><code># L4 fenced block (inside HTML table)
    |   |     echo nested
    |   |     </code></pre>
    |   |   </td></tr>
    |   | </table> |
    | B | 2 |


---

## 6) Depth‑4: **Markdown Table** with **footnotes, links, images** inside cells

| Feature | Demo |
|:-------:|:-----|
| Footnote | Here is a note[^t1] inside a table cell (L1). |
| Links | [CommonMark spec][cm] and [GFM][gfm] referenced within table (L1). |
| Image | ![logo][logo] |
| Deep | - L1 bullet  
|      |   > L2 quote inside table  
|      |   > 1. L3 number  
|      |   >    - L4 bullet |

[^t1]: Footnote defined outside the table but referenced inside.

---

## 7) Depth‑4: **Code fence with pipes** embedded to test table parsing edge cases

| Pipe | Value |
|------|-------|
| show | ```bash
|      | echo "a|b|c"
|      | printf "1|2|3\n"
|      | ``` |


---

## 8) Depth‑4: **Table alignment, inline pipes, escapes** with nested quotes

| Left        | Center       | Right |
|:------------|:------------:|------:|
| `|`         | `\|`         |  1000 |
| text \| more | **bold**    |   -10 |
| > L1 quote  | > L1 quote   | > L1 quote |
| > - L2 li   | > - L2 li    | > - L2 li  |
| >   > L3    | >   > L3     | >   > L3   |
| >   >   1. L4 ordered | >   >   - L4 bullet | >   >   `L4 code` |


---

## 9) Depth‑4: **GFM table** inside **blockquote** inside **list** inside **blockquote** (max stress)

> Root quote (L1)
> - List level (L2)
>   > Inner quote (L3)
>   >
>   > | Head A | Head B |
>   > |:------:|:------:|
>   > | **L4** bold | `L4` code |
>   > | <sub>sub</sub> | <sup>sup</sup> |


---

## 10) Sanitization probe: raw tags inside cells (expect to be stripped by safe renderers)

| Field | Value |
|------:|:------|
| script | <script>console.log("XSS?")</script> |
| style  | <style>table{border:2px solid red}</style> |
| iframe | <iframe src="about:blank" width="100" height="20"></iframe> |

> If your pipeline strips the above, good. If not, your Markdown → HTML stage should add sanitization.

---

## Final HRs

---
***
___

_EOF_

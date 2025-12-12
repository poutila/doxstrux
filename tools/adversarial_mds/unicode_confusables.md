# Unicode Edge Cases - Confusables/Homoglyphs

This file tests parser robustness against confusable characters (homoglyphs).

## Cyrillic lookalikes

Pаypаl (contains Cyrillic а U+0430, not Latin a U+0061)

Gооgle (contains Cyrillic о U+043E, not Latin o U+006F)

Аpple (starts with Cyrillic А U+0410, not Latin A U+0041)

## Greek lookalikes

Ηello (starts with Greek Η U+0397, not Latin H U+0048)

## Mixed script in links

[Gооgle](https://gооgle.com)

## Confusables in code

```python
# This looks like valid Python but contains confusables
рrint("Hello")  # Cyrillic р instead of Latin p
```

## Zero-width characters

This​text​has​ZWSP​between​words (U+200B Zero Width Space)

This⁠text⁠has⁠ZWNBSP (U+2060 Word Joiner)

## Invisible formatting

Text with ​hidden​ zero-width characters that could hide malicious content.

# Unicode Edge Cases - BiDi Controls

This file tests parser robustness against BiDi (bidirectional) control characters.

## Right-to-Left Override

This text contains ‮EDOC NEDDIH‬ a hidden code using RLO (U+202E).

## Left-to-Right Override

Normal text ‭with LRO override‬ embedded.

## Mixed BiDi Controls

Start ‮backwards‭forwards‬back again‬ end.

## BiDi in Links

[Click ‮ereh‬ here](https://example.com)

## BiDi in Code

`let x = ‮edoc neddih‬;`

## Paragraph with multiple controls

This is a paragraph with ‮reversed text‬ and ‭forced LTR‬ and ‮more reversed‬ mixed together to test BiDi handling.

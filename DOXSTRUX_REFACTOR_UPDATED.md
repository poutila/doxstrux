# DOXSTRUX_REFACTOR_UPDATED

## 1. Context and goals

This document updates the original DOXSTRUX_REFACTOR plan with a minimal additional layer that addresses the key SOLID violations (SRP, OCP, ISP, DIP) without discarding the existing refactor design.

Existing refactor already introduced:
- A parser shim (MarkdownParserCore) that wraps markdown-it-py.
- A TokenWarehouse that owns token indices, topology, and text slicing.
- A collector model that walks tokens in a single pass and produces feature-level structures.

The new layer adds:
- Explicit protocol interfaces (WarehouseView, Collector, SecurityValidator, PluginManager).
- A collector registry (collector_registry.py) to decouple the parser from concrete collectors.
- Minimal constructor and type-level changes to TokenWarehouse and the parser shim, allowing dependency injection.

Goal: high-level code depends on stable abstractions (protocols + registry), and new collectors/services can be added without editing the parser core.

## 2. Target architecture after update

Layers, from high-level to low-level:

1) Public API / Parser shim
- doxstrux.markdown.parser.MarkdownParserCore
- Wires markdown-it, TokenWarehouse, collectors, and security into a single parse call.
- Depends on Collector, WarehouseView, SecurityValidator, PluginManager, and the collector registry.

2) Collector registry
- doxstrux.markdown.collector_registry
- Knows which collector implementations constitute the default feature set.
- Single place to add/remove collectors.

3) Warehouse and dispatch
- doxstrux.markdown.utils.token_warehouse.TokenWarehouse
- Implements WarehouseView (protocol).
- Provides indexing, parent/child relationships, text slicing, token ranges, and a single-pass dispatcher.

4) Collectors (feature extractors)
- doxstrux.markdown.collectors_phase8.*
- Implement the Collector protocol.
- Each collector focuses on one concern (sections, headings, lists, tables, links, images, math, HTML, etc.).

5) Optional services
- SecurityValidator (wraps existing security checks).
- PluginManager (wraps existing markdown-it plugin configuration).
- Introduced as protocols; initial implementation can call current functions.

## 3. New module: interfaces.py

Responsibilities:
- Define small, stable protocol interfaces used by both parser and collectors.
- Avoid circular imports by placing DispatchContext here.

Core elements:
- DispatchContext: dataclass with at least `stack: list[str]` and `line: int`.
- WarehouseView: protocol exposing tokens, find_close, find_parent, tokens_between, text_between, get_token_text, section_of.
- CollectorInterest: dataclass with types, tags, ignore_inside, predicate.
- Collector: protocol with attributes `name`, `interest`, and methods `should_process`, `on_token`, `finalize`.
- SecurityValidator: protocol with validate_content(content, profile) and apply_policy(metadata).
- PluginManager: protocol with configure_markdown_it(md, config).

## 4. New module: collector_registry.py

Create doxstrux.markdown.collector_registry as the single place that knows which collectors form the default feature set.

Key decisions:
- default_collectors() returns a tuple of collector instances (SectionsCollector, HeadingsCollector, ParagraphsCollector, ListsCollector, TasklistsCollector, CodeblocksCollector, TablesCollector, LinksCollector, ImagesCollector, FootnotesCollector, HtmlCollector, MathCollector).
- register_default_collectors(wh: WarehouseView) iterates default_collectors() and calls wh.register_collector for each.

Effects:
- The parser no longer imports concrete collector classes directly; it only calls register_default_collectors.
- Adding/removing a feature is done in collector_registry only.

## 5. TokenWarehouse changes

Update doxstrux.markdown.utils.token_warehouse.TokenWarehouse to:
- Implement WarehouseView.
- Use Collector, CollectorInterest, DispatchContext types for clarity and SOLID alignment.

Key points:
- Add imports from doxstrux.markdown.interfaces (Collector, CollectorInterest, WarehouseView, DispatchContext).
- Declare `class TokenWarehouse(WarehouseView):`.
- Ensure existing methods (find_close, find_parent, tokens_between, text_between, get_token_text, section_of) match the protocol.
- Implement register_collector(self, collector: Collector) that updates an internal routing dict keyed by token types and tag keys.
- dispatch_all() creates a DispatchContext once and walks all tokens, routing them to the appropriate collectors based on type/tag.
- finalize_all() calls finalize() on each collector and merges results into a flat dict.

Behaviour does not change; TokenWarehouse simply becomes the concrete implementation of WarehouseView used by collectors.

## 6. Parser shim changes

Update the skeleton MarkdownParserCore in doxstrux.markdown.parser:

- Import SecurityValidator, PluginManager from interfaces, and register_default_collectors from collector_registry.
- Extend __init__ to accept optional keyword-only parameters `security_validator` and `plugin_manager`.
- Use PluginManager (if provided) to configure markdown-it; otherwise, call a private _configure_default_plugins() which holds the existing plugin wiring.
- After constructing TokenWarehouse, call register_default_collectors(self.warehouse) instead of manually constructing and registering collectors.
- In parse(), optionally call security_validator.validate_content() before dispatch, and security_validator.apply_policy() after building metadata.
- Keep the external API (constructor and parse signature) compatible with the current src/doxstrux implementation.

## 7. Migration strategy

1) Add interfaces.py and collector_registry.py to the skeleton tree. No behavioural changes.
2) Update TokenWarehouse to implement WarehouseView and use Collector-related types. Keep all existing logic.
3) Update parser shim to use register_default_collectors and accept optional SecurityValidator and PluginManager.
4) Gradually refactor collectors to conform exactly to the Collector protocol (name, interest, should_process, on_token, finalize).
5) Later, introduce real SecurityValidator and PluginManager wrappers that delegate to the existing security and plugin configuration functions.

## 8. Testing and validation

Recommended additional tests:
- test_default_collectors_registration: verifies that register_default_collectors registers collectors and that dispatch_all + finalize_all return non-empty results for simple markdown.
- test_markdown_parser_core_uses_registry: monkeypatch register_default_collectors to record calls and assert it is invoked during parse.
- test_collectors_implement_protocol: use isinstance with the runtime-checkable Collector protocol to ensure all concrete collectors conform.
- test_security_validator_injection: use a dummy SecurityValidator to verify that validate_content and apply_policy are called and their results end up in metadata.

This updated plan keeps the existing refactor intact but adds a small, well-defined abstraction layer that significantly improves SRP, OCP, ISP, and DIP while remaining implementable in small, controlled steps.

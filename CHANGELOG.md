# Changelog

All notable changes to the Claude Agent SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-14

### Added
- **Metadata Enhancement Pattern**: Generic pattern for implementations to inject custom data via `Context.metadata`
  - Added `extract_metadata_from_contexts()` helper function in `interfaces.py`
  - Implementations can now inject reference assets, agent configuration, and custom data without changing SDK interfaces
  - Documentation: [docs/METADATA_PATTERN.md](docs/METADATA_PATTERN.md)

- **Enhanced Agent Archetypes**: All agent archetypes now consume metadata for improved behavior
  - **ContentCreatorAgent**: Uses `reference_assets` (brand guidelines, examples) and `agent_config` (tone, platform rules) to enhance content creation
  - **ResearchAgent**: Uses `agent_config` (watchlist topics, competitors, alert rules) for config-driven monitoring
  - **ReportingAgent**: Uses `reference_assets` (templates, style guides) and `agent_config` (formatting preferences, branding) for professional document generation

### Changed
- ContentCreatorAgent: Enhanced `create()` method to detect and use metadata if available
- ResearchAgent: Enhanced `monitor()` method to use config-driven parameters from metadata
- ReportingAgent: Enhanced `generate()` method to apply formatting preferences from metadata
- All enhancements are backward compatible and opt-in (graceful degradation if metadata not provided)

### Documentation
- Added comprehensive metadata pattern guide: [docs/METADATA_PATTERN.md](docs/METADATA_PATTERN.md)
- Updated README.md with "Enhanced Context via Metadata" section
- Added implementation examples and use cases for metadata pattern

### Notes
- **Backward Compatible**: All changes are backward compatible with v0.1.x
- **Generic Design**: Metadata pattern is implementation-agnostic and works with any provider
- **Opt-in Enhancement**: Agents work without metadata; enhancements apply only when metadata is available

## [0.1.0] - 2025-01-13

### Added
- Initial release of Claude Agent SDK
- **BaseAgent**: Generic foundation for building autonomous agents
- **Provider Interfaces**: Abstract interfaces for MemoryProvider, GovernanceProvider, TaskProvider
- **Session Management**: Agent identity and session tracking across executions
- **Lifecycle Hooks**: Extensibility mechanism for custom orchestration
  - `on_step_start`, `on_step_end` - Step lifecycle
  - `before_execute`, `after_execute` - Execution lifecycle
  - `on_checkpoint_opportunity` - Manual checkpoint handling
  - `on_interrupt_signal` - External interrupt handling
  - `on_error` - Error handling

- **Subagent System**: Delegation pattern for specialized sub-agents
  - SubagentDefinition and SubagentRegistry
  - Inspired by official Claude Agent SDK (TypeScript)

- **Agent Archetypes**: Three production-ready agent implementations
  - **ResearchAgent**: Continuous monitoring and deep-dive research with specialized subagents
  - **ContentCreatorAgent**: Multi-platform content creation with brand voice consistency
  - **ReportingAgent**: Professional document generation with template learning

- **Integrations**: Built-in provider implementations
  - **InMemoryProvider**: Simple in-memory storage (no dependencies)
  - **YarnnnMemory**: Persistent memory via YARNNN substrate
  - **YarnnnGovernance**: Proposal-based governance with approval workflows
  - **YarnnnClient**: HTTP client for YARNNN API

### Documentation
- Comprehensive README with quick start, examples, and philosophy
- Architecture documentation
- Lifecycle hooks guide
- YARNNN integration guide
- Building providers guide

### Philosophy
- **Generic, Not Opinionated**: Provides structure, not specifics
- **Agent Identity Over Tools**: Persistent agents that learn over time
- **Governance Enables Autonomy**: Human oversight enables autonomous operation
- **Extensibility First**: Clean interfaces and dependency injection

---

## Version Guide

- **Major (X.0.0)**: Breaking changes to core interfaces or APIs
- **Minor (0.X.0)**: New features, backward-compatible enhancements
- **Patch (0.0.X)**: Bug fixes, documentation updates, minor improvements

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-11-06

### Added
- Timeline merge mode (`m` key) — cross-file event timeline using `heapq.merge`
- Asynchronous timeline building via `asyncio.to_thread`
- `LogEntry.timestamp_dt` — parsed datetime field for precise sorting
- `LogParser.parse_timestamp()` — converts both loguru and logging datetime formats
- `LogParser._make_entry()` — factory that fills `timestamp_dt` on parse
- Source panel checkbox mode in merge mode with `Space` toggle, `←→` navigation
- Color-coded source names in SourcePanel matching LogList
- Source tag prefix (`[blue]app.log[/blue]`) in LogList merge mode messages
- Timsort-based live merge — `LogList` auto-sorts new entries in merge mode
- `LogSource.is_included` flag — selective file inclusion in timeline
- New version badge on README

### Changed
- `LogEntry` now carries `timestamp_dt: datetime | None` for O(1) comparison in merge
- `traceback` entries are no longer re-parsed — `heapq.merge` operates on already-assembled objects

## [1.0.0] - 2026-11-05

### Added
- Stable release with fully featured TUI debugger
- Three-panel interface with source panel, log list, and detail panel
- Color-coded log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log parsing for `loguru`, `standard logging`, and `simple` formats with auto-detection
- Navigation with arrow keys, hotkeys: F (filter), E (next error), T (theme), Q (quit)
- Multiple log file support with live monitoring
- Traceback display in detail panel
- Theme switching (light/dark)
- CLI interface with argparse
- Comprehensive test suite
- GitHub Actions CI/CD pipeline

## [0.1.0] - 2026-10-29

### Added
- Initial release
- Three-panel TUI interface (sources, logs, details)
- Log parsing for `loguru`, `standard logging`, and `simple` formats
- Auto-detection of log formats
- Color-coded log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Navigation with arrow keys
- Hotkeys: F (filter), E (next error), T (theme), Q (quit)
- Multiple log file support
- Traceback display in detail panel
- Custom tags for log entries
- Theme switching (light/dark)
- CLI interface with argparse
- Sample log files for testing
- Comprehensive test suite
- GitHub Actions CI/CD pipeline

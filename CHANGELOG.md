# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

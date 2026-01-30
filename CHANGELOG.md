# Changelog

## [v0.0.1] - 2026-01-29

### Added
- **Markdown Todo Support**: Use `# Headers`, `- [ ] Tasks`, and `**Bold**` in todo lists.
- **Print Logging**: All prints are automatically saved as `.txt` files in the `logs/` directory with timestamps and source URLs.
- **Global Font B**: Switched to compact "Font B" for all thermal prints.
- **Fraction Normalization**: Automatic conversion of Unicode fractions (½, ⅓, etc.) to ASCII (1/2, 1/3, etc.) for better readability.
- **Systemd Service**: Initial configuration for running the app as a service on boot using `uv run`.
- **Gitignore**: Comprehensive ignore list for Python, Logs, and IDE files.

### Changed
- Improved printer service robustness with safety checks for `Mock` mode.
- Optimized title and header formatting for font size hierarchy.

### Fixed
- Resolved `217/USER` and `203/EXEC` service errors by correcting user paths and using absolute script references.
- Fixed `AttributeError` in Mock mode for non-standard ESC/POS implementations.

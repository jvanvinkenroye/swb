# TODO - SWB API Client

## Potential Improvements

### 1. Expand Library Name Mapping

**Priority**: Low
**Effort**: Medium

The `LIBRARY_NAMES` dictionary currently contains only ~30-40 major universities. Consider:

- Expand dictionary with more library names from ISIL database
- Add automated script to fetch library names from https://sigel.staatsbibliothek-berlin.de/
- Cache library name lookups to avoid repeated unknown codes
- Consider making this an optional feature (download updated library database)

**Impact**: Better library name display in holdings information

### 2. Improve Type Checking

**Priority**: Medium
**Effort**: Low

Currently mypy is available but not enforced:

- Add mypy to pre-commit hooks
- Fix any type errors that emerge
- Add stricter mypy configuration in pyproject.toml
- Ensure all function signatures have proper type hints

**Impact**: Better code quality, fewer runtime errors

### 3. Increase Test Coverage

**Priority**: Medium
**Effort**: Medium

Current coverage is 63%, with gaps in:

- CLI module (48% coverage) - many display functions untested
- TUI module (3% coverage) - experimental feature, mostly untested
- Some API edge cases

Consider:
- Add tests for CLI display functions
- Add tests for error formatting
- Test TUI if it becomes a main feature
- Aim for 80%+ coverage

**Impact**: More robust codebase, catch edge case bugs

### 4. Performance Optimization

**Priority**: Low
**Effort**: Medium

Potential optimizations:

- Add caching layer for repeated queries
- Implement connection pooling for multiple requests
- Add async/await support for parallel requests
- Profile XML parsing performance
- Consider using lxml for faster parsing if needed

**Impact**: Faster response times, better user experience

### 5. Enhanced Error Messages

**Priority**: Low
**Effort**: Low

While error handling is good, could improve:

- Add suggestions for common errors (e.g., "Did you mean X?")
- Provide examples in error messages
- Add troubleshooting links to documentation
- Localize error messages (German support)

**Impact**: Better user experience, fewer support questions

### 6. Additional Features

**Priority**: Low
**Effort**: Varies

Possible feature additions:

- **Export functionality**: Save results to CSV, BibTeX, RIS formats
- **Batch operations**: Process multiple ISBNs from a file
- **Watch mode**: Monitor search results for changes
- **Citation formatting**: Generate citations in various styles
- **Advanced search builder**: Interactive CQL query builder
- **Bookmark/favorites**: Save frequently used queries
- **Diff tool**: Compare results between different catalogs

**Impact**: More versatile tool for researchers and librarians

### 7. TUI Enhancement

**Priority**: Low
**Effort**: High

The TUI is currently experimental (3% coverage):

- Complete the TUI implementation
- Add proper navigation and keyboard shortcuts
- Make it production-ready
- Add comprehensive tests
- Document TUI usage

**Impact**: Alternative interface for terminal-only users

### 8. API Client Features

**Priority**: Low
**Effort**: Medium

Additional API capabilities:

- **Sorting**: More sophisticated sorting options
- **Filtering**: Client-side filtering of results
- **Deduplication**: Identify and merge duplicate records
- **Language detection**: Identify and filter by language
- **Subject analysis**: Extract and analyze subject headings

**Impact**: More powerful search capabilities

### 9. Documentation Improvements

**Priority**: Low
**Effort**: Low

Documentation is good but could add:

- Video tutorials or screencasts
- More real-world usage examples
- Troubleshooting guide
- Best practices guide
- Contributing guide for developers
- API design decisions documentation

**Impact**: Easier onboarding for new users and contributors

### 10. Packaging and Distribution

**Priority**: Low
**Effort**: Low

Consider:

- Publish to PyPI for easier installation (`pip install swb-client`)
- Add to conda-forge
- Create pre-built binaries with PyInstaller
- Add to package managers (brew, apt)
- Create Docker image

**Impact**: Wider adoption, easier installation

### 11. Monitoring and Analytics

**Priority**: Low
**Effort**: Medium

Add optional telemetry:

- Track common queries (anonymized)
- Monitor error rates
- Performance metrics
- Usage patterns

**Impact**: Better understanding of how tool is used, prioritize improvements

### 12. Security Enhancements

**Priority**: Medium
**Effort**: Low

Security improvements:

- Add input sanitization audit
- Security scanning in CI/CD
- Dependency vulnerability scanning (already have this?)
- Rate limit per-user tracking
- API key support for authenticated catalogs

**Impact**: More secure application

## Non-Functional Improvements

### Code Quality
- Add more inline documentation
- Refactor large functions (e.g., `_parse_response` is 500+ lines)
- Extract common patterns into helper functions
- Improve variable naming consistency

### Developer Experience
- Add GitHub issue templates
- Add pull request template
- Improve pre-commit hooks
- Add code style guide
- Setup automated dependency updates (Dependabot)

### CI/CD
- Add more comprehensive CI tests
- Test on multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Add integration tests to CI (with rate limiting)
- Add performance benchmarks
- Add changelog generation

### 13. DNB-Profil reparieren

**Priority**: Medium
**Effort**: Low

Das dnb-Profil liefert immer "No results found": Die DNB-SRU-Schnittstelle erwartet
recordSchema=MARC21-xml (nicht marcxml) und eigene Indizes (WOE, dnb.num statt
pica.*). Verifiziert per curl gegen https://services.dnb.de/sru/dnb (funktioniert
mit korrekten Parametern). Fix: CatalogProfile um record_schema/Query-Syntax
erweitern oder DNB-spezifisches Mapping in SWBClient.

## Completed Items

✅ All 37 GitHub issues closed
✅ Custom exception hierarchy implemented
✅ Rate limiting added
✅ Test coverage improved (63%)
✅ Library holdings display fixed
✅ Integration tests added
✅ Documentation deployed to GitHub Pages
✅ CLI with rich output
✅ Multiple catalog support
✅ Holdings information display

## Priority Summary

**High Priority**: None currently - project is in good state

**Medium Priority**:
- Type checking enforcement
- Increase test coverage
- Security enhancements

**Low Priority**: Everything else - nice to have improvements

## Notes

- Project is feature-complete for core use cases
- All known bugs fixed
- Focus should be on code quality and expanding use cases
- Consider user feedback to prioritize future work

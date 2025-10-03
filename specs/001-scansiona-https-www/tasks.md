# Tasks: Scan and Extract Material Test Data from MyTechFun.com

**Input**: Design documents from `/specs/001-scansiona-https-www/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
2. Load optional design documents ✓
3. Generate tasks by category ✓
4. Apply task rules ✓
5. Number tasks sequentially (T001, T002...) ✓
6. Generate dependency graph ✓
7. Create parallel execution examples ✓
8. Validate task completeness ✓
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [ ] **T001** Create project directory structure (`src/`, `data/`, `config/`, `tests/`)
- [ ] **T002** Initialize Python project with requirements.txt (requests, beautifulsoup4, pandas, openpyxl, xlrd, tenacity, robotexclusionrulesparser, structlog)
- [ ] **T003** [P] Configure Python linting (flake8, black) and .gitignore
- [ ] **T004** [P] Create logging configuration in `config/logging.yaml` with structured JSON format per constitution

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [ ] **T005** [P] Create contract test for CrawlerService in `tests/test_crawler_service.py`
- [ ] **T006** [P] Create contract test for ParserService in `tests/test_parser_service.py`
- [ ] **T007** [P] Create contract test for NormalizerService in `tests/test_normalizer_service.py`
- [ ] **T008** [P] Create contract test for StorageService in `tests/test_storage_service.py`
- [ ] **T009** [P] Create integration test for full crawler workflow in `tests/test_integration.py`

## Phase 3.3: Core Models
- [ ] **T010** [P] Create Post model in `src/models/post.py` with validation and SHA-256 hashing
- [ ] **T011** [P] Create ValidFile model in `src/models/valid_file.py` with file type validation
- [ ] **T012** [P] Create MaterialData model in `src/models/material_data.py` with quality rating enum
- [ ] **T013** [P] Create Provenance model in `src/models/provenance.py` with constitutional compliance fields
- [ ] **T014** [P] Create JSONData model in `src/models/json_data.py` with complete output structure

## Phase 3.3: Core Services
- [ ] **T015** Implement CrawlerService in `src/services/crawler_service.py` (robots.txt, rate limiting, user-agent)
- [ ] **T016** Implement ParserService in `src/services/parser_service.py` (file extraction, download, filtering)
- [ ] **T017** Implement NormalizerService in `src/services/normalizer_service.py` (SI unit conversion, multi-material handling)
- [ ] **T018** Implement StorageService in `src/services/storage_service.py` (JSON serialization, provenance, CC BY 4.0 attribution)

## Phase 3.4: Utilities & Libraries
- [ ] **T019** [P] Create logging utilities in `src/lib/logging.py` using structlog with JSON formatter
- [ ] **T020** [P] Create file handling utilities in `src/lib/file_utils.py` (SHA-256, deduplication, directory management)
- [ ] **T021** [P] Create validation utilities in `src/lib/validation.py` (URL validation, constitutional compliance checks)
- [ ] **T022** [P] Create unit conversion mappings in `src/lib/units.py` (SI normalization rules per constitution)

## Phase 3.5: CLI Interface
- [ ] **T023** Create main CLI entry point in `src/cli/crawler.py` with argument parsing (--url parameter)
- [ ] **T024** Integrate all services in CLI orchestration with proper error handling and logging

## Phase 3.6: Integration & Polish
- [ ] **T025** [P] Create configuration management in `config/settings/default.py` (rate limits, user-agent, paths)
- [ ] **T026** [P] Add comprehensive error handling and retry logic with jitter per constitution
- [ ] **T027** Verify constitutional compliance in all components (gentle crawler, data quality, provenance, licensing)
- [ ] **T028** Run quickstart validation scenarios and verify JSON output structure

## Dependency Graph
```
T001,T002 → T003,T004 (Setup complete)
T005-T009 → T010-T014 (Tests before models)
T010-T014 → T015-T018 (Models before services)
T019-T022 → T023,T024 (Utils before CLI)
T015-T018,T023,T024 → T025-T028 (Core before integration)
```

## Parallel Execution Examples

### Phase 3.2 (All parallel - different test files):
```bash
# Run contract tests in parallel
/tasks T005 T006 T007 T008 T009
```

### Phase 3.3 (Models parallel, services sequential):
```bash
# Models can be created in parallel (different files)
/tasks T010 T011 T012 T013 T014

# Services must be sequential (may share imports/dependencies)
/tasks T015
/tasks T016  
/tasks T017
/tasks T018
```

### Phase 3.4 (All parallel - different utility files):
```bash
# Utility modules are independent
/tasks T019 T020 T021 T022
```

## Task Validation Checklist
- [x] All 4 contracts have test tasks (T005-T008)
- [x] All 5 entities have model tasks (T010-T014)  
- [x] All 4 services have implementation tasks (T015-T018)
- [x] CLI integration task included (T023-T024)
- [x] Constitutional compliance verification (T027)
- [x] Quickstart validation scenario (T028)
- [x] TDD enforced (tests before implementation)
- [x] Parallel execution identified where possible

## Success Criteria
✓ All contract tests pass after implementation  
✓ Full crawler workflow executes without errors  
✓ JSON output matches expected structure from quickstart.md  
✓ Constitutional compliance verified (robots.txt, rate limiting, attribution, provenance)  
✓ SI unit normalization working for supported properties  
✓ Multi-material handling functional  
✓ Deduplication prevents duplicate downloads

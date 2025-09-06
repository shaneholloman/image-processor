# Plan: Consolidate Image Processor Tools

## Overview

Move the `image_processor_name` tool into the main `src/` directory alongside `image_processor_meta`, unify the project structure, and standardize configuration naming.

## Current State

```tree
image-processor/
├── src/image_processor_meta/                        # Meta tool
├── image_processor_name/                            # Name tool (standalone)
├── config/app_config.yaml                           # Meta tool config (poorly named)
├── image_processor_name/config/rename_config.yaml   # Name tool config
└── pyproject.toml                                   # Main project file
```

## Target State

```tree
image-processor/
├── src/
│   ├── image_processor_meta/    # Meta tool
│   └── image_processor_name/    # Name tool (moved)
├── config/
│   ├── meta_config.yaml         # Meta tool config (renamed)
│   └── name_config.yaml         # Name tool config (renamed)
└── pyproject.toml               # Single unified project file
```

## Implementation Steps

### Phase 1: Move the Tool

1. **Move directory structure**

   ```bash
   mv image_processor_name/src/image_processor_name src/image_processor_name
   ```

2. **Update import paths**
   - Change all relative imports in `src/image_processor_name/` modules
   - Update any references to old path structure

3. **Test the move**
   - Verify `uv run image-processor-name` still works from project root
   - Ensure all modules can import correctly

### Phase 2: Consolidate Configuration

1. **Rename config files for consistency**
   - `config/app_config.yaml` → `config/meta_config.yaml`
   - `image_processor_name/config/rename_config.yaml` → `config/name_config.yaml`

2. **Update config path references**
   - Update `image_processor_meta` to use `config/meta_config.yaml`
   - Update `image_processor_name` to use `config/name_config.yaml`
   - Ensure both tools find configs in the unified `config/` directory

3. **Verify config loading**
   - Test both tools load their configs correctly
   - Test environment variable overrides still work

### Phase 3: Unify Project Management

1. **Consolidate pyproject.toml**
   - Remove `image_processor_name/pyproject.toml`
   - Ensure main `pyproject.toml` handles both tools correctly
   - Verify all dependencies are included

2. **Update CLI entry points**
   - Ensure `image-processor-meta` and `image-processor-name` commands both work
   - Verify paths point to correct modules in `src/`

3. **Clean up old structure**
   - Remove empty `image_processor_name/` directory
   - Remove any orphaned config files

### Phase 4: Testing and Validation

1. **Test both tools**

   ```bash
   uv run image-processor-meta --help
   uv run image-processor-name --help
   uv run image-processor-name --test-connection
   uv run image-processor-name rename test_images/
   ```

2. **Verify configurations**
   - Both tools load correct config files
   - Environment variables override correctly
   - All features work as expected

3. **Update documentation**
   - Update any README files
   - Fix any path references in docs

## Configuration Naming Standards

### Current Names (Inconsistent)

- `app_config.yaml` - Generic, doesn't match tool name
- `rename_config.yaml` - Better, but not consistent with tool name

### New Names (Consistent)

- `meta_config.yaml` - Matches `image_processor_meta` tool
- `name_config.yaml` - Matches `image_processor_name` tool

## Risk Mitigation

1. **Backup before changes**
   - Create git commit before starting
   - Document current working state

2. **Incremental testing**
   - Test after each phase
   - Don't proceed if previous phase fails

3. **Rollback plan**
   - Keep git history clean for easy revert
   - Document exact steps for rollback

## Expected Benefits

1. **Unified structure** - Both tools in `src/` directory
2. **Consistent configuration** - Clear naming that matches tool names
3. **Single project management** - One `pyproject.toml` for everything
4. **Easier maintenance** - All code in standard Python package structure
5. **Better development experience** - Standard layout, easier to navigate

## Success Criteria

- [ ] Both tools run correctly from project root
- [ ] Configuration files have consistent, descriptive names
- [ ] Single `pyproject.toml` manages both tools
- [ ] All existing functionality preserved
- [ ] Tests pass for both tools
- [ ] Documentation updated

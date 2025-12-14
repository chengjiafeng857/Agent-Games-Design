# Testing Guide

This directory contains comprehensive tests for the Agent Games Design system, with a focus on the new configuration system.

## Test Files

### 1. `test_configuration.py`
Comprehensive pytest-based tests for the configuration system.

**Coverage:**
- ✅ ModelConfig class functionality
- ✅ Settings class and configuration getters
- ✅ Tool getter functions
- ✅ Agent initialization with configurations
- ✅ Response API integration
- ✅ Thinking effort configuration
- ✅ Tool binding
- ✅ Backward compatibility

**Run with pytest:**
```bash
# Run all configuration tests
uv run python -m pytest tests/test_configuration.py -v

# Run specific test class
uv run python -m pytest tests/test_configuration.py::TestModelConfig -v

# Run with coverage
uv run python -m pytest tests/test_configuration.py --cov=agent_games_design.config
```

### 2. `verify_configuration.py`
Standalone verification script (no pytest required).

**What it tests:**
- ModelConfig initialization and methods
- Settings configuration getters
- Tool getter functions
- Common configuration scenarios
- Displays current configuration summary

**Run standalone:**
```bash
# Simple verification (no dependencies except project code)
uv run python tests/verify_configuration.py

# Or directly with python if dependencies are installed
python tests/verify_configuration.py
```

**Output:**
```
======================================================================
🧪 Configuration System Verification
======================================================================

✅ PASS - Default initialization
✅ PASS - Custom initialization
✅ PASS - GPT-5 is reasoning model
... (27 total tests)

✅ All verifications completed successfully!
```

### 3. `run_config_tests.py`
Test runner script with formatted output.

**Run tests:**
```bash
uv run python tests/run_config_tests.py
```

## Quick Test Commands

### Option 1: Quick Verification (Recommended)
```bash
# Fastest - standalone verification
uv run python tests/verify_configuration.py
```

### Option 2: Full Test Suite
```bash
# Complete pytest suite
uv run python -m pytest tests/test_configuration.py -v
```

### Option 3: All Tests
```bash
# Run all tests in the project
uv run python -m pytest tests/ -v
```

### Option 4: Specific Test Classes
```bash
# Test only ModelConfig
uv run python -m pytest tests/test_configuration.py::TestModelConfig -v

# Test only Settings
uv run python -m pytest tests/test_configuration.py::TestSettings -v

# Test only tool getters
uv run python -m pytest tests/test_configuration.py::TestToolGetters -v

# Test agent integration
uv run python -m pytest tests/test_configuration.py::TestPlanningAgentIntegration -v
```

## Test Coverage

### ModelConfig Class Tests
- ✅ Default initialization
- ✅ Custom initialization with all parameters
- ✅ Reasoning model detection (GPT-5, o-series)
- ✅ Standard model detection (GPT-4)
- ✅ Model kwargs generation for reasoning models
- ✅ Model kwargs generation for standard models
- ✅ Thinking effort handling
- ✅ Temperature handling
- ✅ Tool binding kwargs

### Settings Class Tests
- ✅ Settings singleton instance
- ✅ get_planning_config() method
- ✅ get_react_config() method
- ✅ get_evaluation_config() method
- ✅ Default values verification
- ✅ Thinking effort defaults

### Tool Getter Tests
- ✅ get_planning_tools() returns correct tools
- ✅ get_react_tools() returns all tools
- ✅ get_evaluation_tools() returns analysis tools

### Agent Integration Tests
- ✅ PlanningAgent default initialization
- ✅ PlanningAgent custom configuration
- ✅ PlanningAgent tool binding (enabled)
- ✅ PlanningAgent no tool binding (disabled)
- ✅ ReActExecutor default initialization
- ✅ ReActExecutor custom configuration
- ✅ ReActExecutor tool binding

### Response API Tests
- ✅ Response API v1 with reasoning models
- ✅ Response API v0 fallback
- ✅ Proper kwargs generation

### Backward Compatibility Tests
- ✅ Default initialization without parameters
- ✅ Existing code continues to work

## Test Results

As of the latest run, all 27 verification tests pass:

```
✅ ModelConfig Class: 7/7 tests passed
✅ Settings Class: 10/10 tests passed
✅ Tool Getters: 6/6 tests passed
✅ Configuration Scenarios: 4/4 tests passed
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pydantic_settings'"

**Solution:** Install dependencies using uv:
```bash
uv sync --extra dev
```

Then run tests with `uv run`:
```bash
uv run python tests/verify_configuration.py
```

### Issue: "pytest: command not found"

**Solution:** Use the verification script instead (no pytest required):
```bash
uv run python tests/verify_configuration.py
```

Or install pytest:
```bash
uv sync --extra dev
```

### Issue: Tests fail with import errors

**Solution:** Make sure you're in the project root and using `uv run`:
```bash
cd /path/to/agent-games-design
uv run python tests/verify_configuration.py
```

## Adding New Tests

When adding new configuration features:

1. **Add to `test_configuration.py`:**
   ```python
   class TestNewFeature:
       """Tests for new feature."""
       
       def test_new_feature_works(self):
           """Test that new feature works."""
           config = ModelConfig(new_param="value")
           assert config.new_param == "value"
   ```

2. **Add to `verify_configuration.py`:**
   ```python
   def test_new_feature():
       """Test new feature."""
       print("\nTesting New Feature")
       config = ModelConfig(new_param="value")
       print_test("New feature works", config.new_param == "value")
   ```

3. **Run tests to verify:**
   ```bash
   uv run python tests/verify_configuration.py
   uv run python -m pytest tests/test_configuration.py -v
   ```

## CI/CD Integration

For continuous integration, add to your workflow:

```yaml
- name: Run configuration tests
  run: |
    uv sync --extra dev
    uv run python -m pytest tests/test_configuration.py -v
```

## Next Steps

1. ✅ All configuration tests pass
2. 📖 Review [CONFIGURATION.md](../docs/CONFIGURATION.md) for usage
3. 🔧 Update your `.env` file with desired settings
4. 🚀 Run your application with new configuration

## References

- [Configuration Guide](../docs/CONFIGURATION.md)
- [Migration Guide](../docs/MIGRATION_TO_STANDARD_API.md)
- [Update Summary](../STANDARD_API_UPDATE_SUMMARY.md)


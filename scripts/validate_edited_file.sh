#!/bin/bash
# Real-time validation of edited files using full CLAUDE.md tool suite
# Usage: ./validate_edited_file.sh <filepath>

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the edited file path
FILEPATH="${1:-}"

# Debug: Log the arguments received
if [ -n "$DEBUG" ]; then
    echo "DEBUG: Script called with args: $@" >&2
    echo "DEBUG: FILEPATH='$FILEPATH'" >&2
fi

if [ -z "$FILEPATH" ]; then
    echo -e "${RED}Error: No file path provided${NC}" >&2
    echo "Usage: $0 <filepath>" >&2
    echo "Received arguments: $@" >&2
    exit 1
fi

if [ ! -f "$FILEPATH" ]; then
    echo -e "${RED}Error: File not found: $FILEPATH${NC}" >&2
    exit 1
fi

# Get absolute path
FILEPATH=$(realpath "$FILEPATH")
FILENAME=$(basename "$FILEPATH")
DIRNAME=$(dirname "$FILEPATH")

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 Validating: $FILEPATH${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Track if any check fails
FAILED=0

# Function to run a command and check result
run_check() {
    local name="$1"
    local cmd="$2"
    
    echo -e "\n${YELLOW}▶ Running $name...${NC}"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}" >&2
        FAILED=1
    fi
}

# Only run checks on Python files
if [[ "$FILEPATH" == *.py ]]; then
    
    # 1. Run mypy type checking
    if command -v mypy &> /dev/null; then
        run_check "mypy (type checking)" "mypy '$FILEPATH' --ignore-missing-imports"
    else
        echo -e "${YELLOW}⚠️  mypy not found, skipping type check${NC}"
    fi
    
    # 2. Run ruff linting
    if command -v ruff &> /dev/null; then
        run_check "ruff (linting)" "ruff check '$FILEPATH'"
    else
        echo -e "${YELLOW}⚠️  ruff not found, skipping lint check${NC}"
    fi
    
    # 3. Run ruff formatting check
    if command -v ruff &> /dev/null; then
        run_check "ruff format (formatting)" "ruff format --check '$FILEPATH'"
    else
        echo -e "${YELLOW}⚠️  ruff not found, skipping format check${NC}"
    fi
    
    # 4. Run black formatting check (additional strictness)
    if command -v black &> /dev/null; then
        run_check "black (formatting)" "black --check '$FILEPATH'"
    else
        echo -e "${YELLOW}⚠️  black not found, skipping black format check${NC}"
    fi
    
    # 5. Run bandit security check
    if command -v bandit &> /dev/null; then
        run_check "bandit (security)" "bandit -q '$FILEPATH'"
    else
        echo -e "${YELLOW}⚠️  bandit not found, skipping security check${NC}"
    fi
    
    # 6. Check for forbidden patterns from CLAUDE.md
    echo -e "\n${YELLOW}▶ Checking forbidden patterns...${NC}"
    PATTERNS_FOUND=0
    
    # Check each forbidden pattern
    declare -A FORBIDDEN_PATTERNS=(
        ["print("]="Use logging instead"
        ["eval("]="Security risk - dynamic code execution"
        ["exec("]="Security risk - arbitrary code execution"
        ["input("]="Use proper input validation"
        ["__import__("]="Use standard imports"
        ["# type: ignore"]="Fix typing errors properly"
        ["# noqa"]="Fix linting errors properly"
        ["# fmt: off"]="Fix formatting errors properly"
    )
    
    for pattern in "${!FORBIDDEN_PATTERNS[@]}"; do
        if grep -n "$pattern" "$FILEPATH" > /dev/null 2>&1; then
            echo -e "${RED}❌ Found forbidden pattern: $pattern - ${FORBIDDEN_PATTERNS[$pattern]}${NC}" >&2
            grep -n "$pattern" "$FILEPATH" | head -5 >&2
            PATTERNS_FOUND=1
        fi
    done
    
    if [ $PATTERNS_FOUND -eq 0 ]; then
        echo -e "${GREEN}✅ No forbidden patterns found${NC}"
    else
        FAILED=1
    fi
    
    # 7. Check if test file exists (for non-test files)
    if [[ ! "$FILENAME" =~ ^test_ ]] && [[ "$FILENAME" != "__init__.py" ]]; then
        echo -e "\n${YELLOW}▶ Checking for test file...${NC}"
        
        TEST_FILENAME="test_${FILENAME%.py}.py"
        TEST_FOUND=0
        
        # Check various test locations
        if [ -f "$DIRNAME/$TEST_FILENAME" ]; then
            echo -e "${GREEN}✅ Test file found: $DIRNAME/$TEST_FILENAME${NC}"
            TEST_FOUND=1
        elif [ -f "$DIRNAME/../tests/${DIRNAME##*/}/$TEST_FILENAME" ]; then
            echo -e "${GREEN}✅ Test file found: $DIRNAME/../tests/${DIRNAME##*/}/$TEST_FILENAME${NC}"
            TEST_FOUND=1
        elif [[ "$FILEPATH" == */src/* ]] && [ -f "${FILEPATH/\/src\//\/tests\/}" ]; then
            echo -e "${GREEN}✅ Test file found: ${FILEPATH/\/src\//\/tests\/}${NC}"
            TEST_FOUND=1
        fi
        
        if [ $TEST_FOUND -eq 0 ]; then
            echo -e "${RED}❌ No test file found for $FILENAME${NC}" >&2
            echo -e "${YELLOW}   Suggestion: Create test file at tests/.../$TEST_FILENAME${NC}" >&2
            FAILED=1
        fi
        
        # 8. Run tests for the specific module if test file exists
        if [ $TEST_FOUND -eq 1 ] && command -v pytest &> /dev/null; then
            echo -e "\n${YELLOW}▶ Running module tests...${NC}"
            
            # Find the test file and run it
            if [ -f "$DIRNAME/$TEST_FILENAME" ]; then
                run_check "pytest (unit tests)" "pytest '$DIRNAME/$TEST_FILENAME' -v"
            fi
        fi
    fi
    
    # 9. Run the original Python validator for additional CLAUDE.md checks
    VALIDATOR_SCRIPT="$(dirname "$0")/validate_edited_file.py"
    if [ -f "$VALIDATOR_SCRIPT" ]; then
        echo -e "\n${YELLOW}▶ Running CLAUDE.md specific checks...${NC}"
        if python "$VALIDATOR_SCRIPT" "$FILEPATH"; then
            echo -e "${GREEN}✅ CLAUDE.md checks passed${NC}"
        else
            echo -e "${RED}❌ CLAUDE.md checks failed${NC}" >&2
            FAILED=1
        fi
    fi
    
else
    echo -e "${YELLOW}ℹ️  Not a Python file, skipping Python-specific checks${NC}"
fi

# Summary
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
else
    echo -e "${RED}❌ Validation failed - please fix the issues above${NC}" >&2
fi
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

exit $FAILED
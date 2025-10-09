#!/bin/bash

# Required: path to the golden egg reference
GOLDEN_EGG="docs/standards/CLAUDE_MD_REQUIREMENTS.md"

# Path to the CLI
PYTHON_CMD=".venv/bin/python"
CLI_MODULE="src.docpipe.cli.main"

# List of folders to process
MD_FOLDERS=(
  "src/docpipe/quality_tests/test_false_positives"
  "src/docpipe/quality_tests/test_claude_semantic_test_variants"
  "src/docpipe/quality_tests/test_edit_regression_tests"
  "src/docpipe/quality_tests/test_foul_play"
  "src/docpipe/quality_tests/test_claudes"
  "src/docpipe/quality_tests/test_invalid_input"
  "src/docpipe/quality_tests/test_ambiguous"
  "src/docpipe/quality_tests/test_overengineered"
  "src/docpipe/quality_tests/test_minimal_valid"
  "src/docpipe/quality_tests/test_autogen_outputs"
)

# Special file
NIGHTMARE_MD="src/docpipe/quality_tests/TEST_CLAUDE_NIGHTMARE.md"

# Function to run validation
run_validation() {
  local md_file="$1"
  echo "🔍 Validating: $md_file"
  $PYTHON_CMD -m $CLI_MODULE "$md_file" "$GOLDEN_EGG"
  if [ $? -ne 0 ]; then
    echo "❌ Validation failed for: $md_file"
  else
    echo "✅ Passed: $md_file"
  fi
  echo
}

# Main loop
for folder in "${MD_FOLDERS[@]}"; do
  find "$folder" -type f -name "*.md" | while read -r file; do
    run_validation "$file"
  done
done

# Run for the special file
run_validation "$NIGHTMARE_MD"


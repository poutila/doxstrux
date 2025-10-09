#!/bin/bash

# create_new_tree_unique_names.sh - Create multiple git worktrees with unique names
# Usage: ./create_new_tree_unique_names.sh <name1> <name2> <name3> ...
# Example: ./create_new_tree_unique_names.sh database-mysql database-postgres auth-oauth

set -e  # Exit on any error

# Function to display usage
usage() {
    echo "Usage: $0 <name1> <name2> <name3> ..."
    echo ""
    echo "Creates multiple git worktrees with unique names for parallel development"
    echo ""
    echo "Arguments:"
    echo "  name1, name2, ...  Unique names for each worktree (at least 1 required)"
    echo ""
    echo "Examples:"
    echo "  $0 auth-jwt auth-oauth auth-saml"
    echo "  $0 db-mysql db-postgres db-mongo db-redis"
    echo ""
    echo "This will create:"
    echo "  • Branches: feature-<name1>, feature-<name2>, ..."
    echo "  • Directories: trees/<name1>/, trees/<name2>/, ..."
    exit 1
}

# Function to validate inputs
validate_inputs() {
    if [ $# -eq 0 ]; then
        echo "Error: At least one name is required"
        usage
    fi

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "Error: Not in a git repository"
        exit 1
    fi

    # Validate each name
    for name in "$@"; do
        if [ -z "$name" ]; then
            echo "Error: Empty name provided"
            usage
        fi
        
        # Check for invalid characters in names
        if [[ ! "$name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            echo "Error: Name '$name' contains invalid characters"
            echo "Only letters, numbers, hyphens, and underscores are allowed"
            exit 1
        fi
    done
}

# Function to create trees directory if it doesn't exist
create_trees_dir() {
    if [ ! -d "trees" ]; then
        echo "Creating trees/ directory..."
        mkdir -p trees
    fi
}

# Function to check for existing worktrees
check_existing_worktrees() {
    local has_conflicts=false
    
    for name in "$@"; do
        local branch_name="feature-${name}"
        local dir_path="./trees/${name}"

        # Check if branch already exists
        if git show-ref --verify --quiet "refs/heads/$branch_name"; then
            echo "Warning: Branch '$branch_name' already exists"
            has_conflicts=true
        fi

        # Check if directory already exists
        if [ -d "$dir_path" ]; then
            echo "Error: Directory '$dir_path' already exists"
            has_conflicts=true
        fi
    done
    
    if [ "$has_conflicts" = true ]; then
        read -p "Continue anyway? This may fail if branches are checked out elsewhere. (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted"
            exit 1
        fi
    fi
}

# Function to create worktrees
create_worktrees() {
    local total=$#
    local current=0
    local created_worktrees=()
    
    echo "Creating $total worktrees with unique names"
    echo "Base directory: $(pwd)/trees/"
    echo ""

    for name in "$@"; do
        current=$((current + 1))
        local branch_name="feature-${name}"
        local dir_path="./trees/${name}"

        echo "Creating worktree $current/$total:"
        echo "  Name: $name"
        echo "  Branch: $branch_name"
        echo "  Path: $dir_path"

        # Capture output and check exit code separately to handle git's stderr output
        output=$(git worktree add -b "$branch_name" "$dir_path" 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "  ✅ Created successfully"
            created_worktrees+=("$name")
        else
            echo "  ❌ Failed to create worktree"
            echo "  Cleaning up partial creation..."
            cleanup_on_failure "${created_worktrees[@]}"
            exit 1
        fi
        echo ""
    done
}

# Function to cleanup on failure
cleanup_on_failure() {
    for name in "$@"; do
        local branch_name="feature-${name}"
        local dir_path="./trees/${name}"

        if [ -d "$dir_path" ]; then
            echo "Removing: $dir_path"
            git worktree remove "$dir_path" 2>/dev/null || true
        fi

        if git show-ref --verify --quiet "refs/heads/$branch_name"; then
            echo "Removing branch: $branch_name"
            git branch -D "$branch_name" 2>/dev/null || true
        fi
    done
}

# Function to display success summary
display_summary() {
    local total=$#
    
    echo "🎉 Successfully created $total worktrees!"
    echo ""
    echo "Branches created:"
    for name in "$@"; do
        echo "  • feature-${name}"
    done
    echo ""
    echo "Directories created:"
    for name in "$@"; do
        echo "  • trees/${name}/"
    done
    echo ""
    echo "Next steps:"
    echo "  1. cd trees/$1"
    echo "  2. Start developing in this worktree"
    echo "  3. Use 'cd ../another-name' to switch between worktrees"
    echo ""
    echo "Useful commands:"
    echo "  git worktree list                    # List all worktrees"
    echo "  git worktree remove <path>           # Remove a worktree"
    echo "  git branch -d feature-<name>         # Delete branch after merge"
}

# Main function
main() {
    echo "Git Worktree Creator (Unique Names)"
    echo "==================================="
    echo ""

    validate_inputs "$@"
    create_trees_dir
    check_existing_worktrees "$@"
    create_worktrees "$@"
    display_summary "$@"
}

# Handle help flags
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    usage
fi

# Run main function with all arguments
main "$@"
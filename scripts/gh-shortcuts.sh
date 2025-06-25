#!/bin/bash
# GitHub CLI shortcuts for DiceBot development

# Configuration
REPO="ShakaTry/DiceBot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
check_auth() {
    if ! gh auth status >/dev/null 2>&1; then
        echo -e "${RED}❌ Not authenticated. Run: gh auth login${NC}"
        exit 1
    fi
}

# === ISSUE MANAGEMENT ===
create_bug() {
    local title="$1"
    local description="$2"
    
    check_auth
    echo -e "${BLUE}🐛 Creating bug report...${NC}"
    
    gh issue create \
        --title "🐛 $title" \
        --body "$description

## Environment
- Strategy: 
- Capital: 
- Parameters: 

## Expected Behavior
- 

## Actual Behavior
- 

## Steps to Reproduce
1. 
2. 
3. 

## Logs/Error Messages
\`\`\`
[Paste logs here]
\`\`\`" \
        --label "bug" \
        --assignee "@me"
}

create_feature() {
    local title="$1"
    local description="$2"
    
    check_auth
    echo -e "${BLUE}✨ Creating feature request...${NC}"
    
    gh issue create \
        --title "✨ $title" \
        --body "$description

## Feature Type
- [ ] New betting strategy
- [ ] Strategy enhancement
- [ ] Simulation improvement
- [ ] CLI feature
- [ ] Integration
- [ ] Other

## Use Case
Why this would improve DiceBot:

## Acceptance Criteria
- [ ] 
- [ ] 
- [ ] 

## Implementation Notes
-" \
        --label "enhancement" \
        --assignee "@me"
}

# === PULL REQUEST MANAGEMENT ===
create_pr() {
    local title="$1"
    local description="$2"
    
    check_auth
    echo -e "${BLUE}🔄 Creating pull request...${NC}"
    
    gh pr create \
        --title "$title" \
        --body "$description

## Changes
- 

## Testing
- [ ] Tests pass locally
- [ ] Added new tests if needed
- [ ] Linting passes
- [ ] Coverage maintained

## Performance Impact
- [ ] No performance regression
- [ ] Benchmarks run if needed

## Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes documented

## Related Issues
Fixes #" \
        --assignee "@me"
}

# === RELEASE MANAGEMENT ===
create_release() {
    local version="$1"
    local notes="$2"
    
    check_auth
    echo -e "${BLUE}🏷️ Creating release $version...${NC}"
    
    # Trigger release workflow
    gh workflow run release.yml \
        --field version_bump="$version"
    
    echo -e "${GREEN}✅ Release workflow triggered${NC}"
    echo "Monitor progress: gh run list"
}

# === WORKFLOW MANAGEMENT ===
trigger_simulation() {
    check_auth
    echo -e "${BLUE}🎲 Triggering daily simulation...${NC}"
    
    gh workflow run dicebot-production.yml
    echo -e "${GREEN}✅ Simulation workflow triggered${NC}"
}

check_workflows() {
    check_auth
    echo -e "${BLUE}🚀 Checking workflow status...${NC}"
    
    gh run list --limit 5
}

# === REPOSITORY STATUS ===
repo_status() {
    check_auth
    echo -e "${BLUE}📊 Repository Status${NC}"
    echo ""
    
    echo -e "${YELLOW}🔄 Recent Workflow Runs:${NC}"
    gh run list --limit 3
    echo ""
    
    echo -e "${YELLOW}📋 Open Issues:${NC}"
    gh issue list --limit 5
    echo ""
    
    echo -e "${YELLOW}🔄 Open PRs:${NC}"
    gh pr list --limit 5
    echo ""
    
    echo -e "${YELLOW}🏷️ Latest Releases:${NC}"
    gh release list --limit 3
}

# === MAIN FUNCTION ===
main() {
    case "$1" in
        "bug")
            create_bug "$2" "$3"
            ;;
        "feature")
            create_feature "$2" "$3"
            ;;
        "pr")
            create_pr "$2" "$3"
            ;;
        "release")
            create_release "$2" "$3"
            ;;
        "simulate")
            trigger_simulation
            ;;
        "status")
            repo_status
            ;;
        "workflows")
            check_workflows
            ;;
        *)
            echo -e "${BLUE}🐙 DiceBot GitHub CLI Shortcuts${NC}"
            echo ""
            echo "Usage: $0 <command> [args...]"
            echo ""
            echo "Commands:"
            echo "  bug <title> [description]       Create bug report"
            echo "  feature <title> [description]   Create feature request"
            echo "  pr <title> [description]        Create pull request"
            echo "  release <patch|minor|major>     Create release"
            echo "  simulate                        Trigger simulation"
            echo "  status                          Show repo status"
            echo "  workflows                       Check workflow runs"
            echo ""
            echo "Examples:"
            echo "  $0 bug 'Dice calculation error' 'Wrong probability'"
            echo "  $0 feature 'New strategy' 'Anti-martingale strategy'"
            echo "  $0 pr 'Fix simulation bug' 'Fixes issue #123'"
            echo "  $0 release patch"
            echo "  $0 status"
            ;;
    esac
}

# Run main function with all arguments
main "$@"

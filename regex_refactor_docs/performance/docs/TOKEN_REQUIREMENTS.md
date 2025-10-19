# GitHub Token Requirements

This document specifies the required GitHub token scopes for audit automation tools.

## Overview

The audit automation system uses GitHub API tokens to create issues, manage repositories, and check permissions. Different operations require different token scopes.

## Required Scopes by Operation

### Creating Issues in Central Backlog

**Required Scope**: `issues:write` OR `repo`

- **For public repos**: `issues:write` scope is sufficient
- **For private repos**: `repo` scope is required (includes `issues:write`)

**Rationale**: Creating issues requires write access to the repository's issues.

### Reading Repository Metadata

**Required Scope**: `repo:read` OR `public_repo`

- **For public repos**: `public_repo` scope is sufficient
- **For private repos**: `repo:read` or `repo` scope is required

**Rationale**: Checking repository permissions and metadata requires read access.

### Permission Checks

**Required Scope**: `repo` (includes all read/write permissions)

- The permission fallback system checks collaborator status via the `/repos/{owner}/{repo}/collaborators/{username}/permission` endpoint
- This requires authenticated access with repository read permissions

## Verifying Token Scopes

To verify your GitHub token has the required scopes:

```bash
# Check token scopes via API
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# The response includes X-OAuth-Scopes header showing active scopes
curl -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep X-OAuth-Scopes
```

**Example Response**:
```
X-OAuth-Scopes: repo, issues:write, read:org
```

## Token Setup

### For Local Development

```bash
# Create a GitHub Personal Access Token (PAT) with required scopes
# Go to: https://github.com/settings/tokens/new

# Set the token as an environment variable
export GITHUB_TOKEN=ghp_your_token_here

# Verify the token works
python tools/permission_fallback.py --repo security/audit-backlog --artifact test.json
```

### For CI/CD (GitHub Actions)

```yaml
# .github/workflows/audit.yml
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Run audit automation
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # Built-in token
          # OR use custom PAT:
          # GITHUB_TOKEN: ${{ secrets.AUDIT_BOT_TOKEN }}
        run: |
          python tools/create_issues_for_unregistered_hits.py --audit audit.json --confirm
```

**Note**: The built-in `GITHUB_TOKEN` in GitHub Actions has limited scopes. For cross-repository operations, use a custom Personal Access Token stored in repository secrets.

## Scope Inheritance

Token scopes are hierarchical:

- `repo` → includes `repo:read`, `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
- `public_repo` → limited to public repositories only
- `issues:write` → can create and update issues, but cannot read private repos

## Common Issues

### Permission Denied (403 Forbidden)

**Symptom**: API calls return 403 Forbidden

**Causes**:
1. Token lacks required scope
2. Token has expired
3. User is not a collaborator on the repository

**Solution**:
```bash
# Check token scopes
curl -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep X-OAuth-Scopes

# Regenerate token with correct scopes if needed
# Add user as collaborator to repository if needed
```

### Unauthorized (401 Unauthorized)

**Symptom**: API calls return 401 Unauthorized

**Causes**:
1. Token is missing or invalid
2. Token has been revoked

**Solution**:
```bash
# Verify token is set
echo $GITHUB_TOKEN

# Test token validity
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Generate new token if invalid
```

### Silent Failures

**Symptom**: Script runs but no issues are created

**Causes**:
1. Token lacks `issues:write` scope
2. Permission fallback is saving artifacts instead of creating issues

**Solution**:
```bash
# Check fallback artifacts
ls adversarial_reports/fallback_*.json

# Review fallback logs
grep "Permission fallback" issue_automation.log

# Add required scopes to token
```

## Security Best Practices

1. **Use Fine-Grained Personal Access Tokens** (beta)
   - Limit token to specific repositories
   - Set expiration dates
   - Use minimum required scopes

2. **Rotate Tokens Regularly**
   - Set up token expiration reminders
   - Rotate tokens every 90 days minimum

3. **Store Tokens Securely**
   - Use environment variables (not hardcoded)
   - Use secret managers for production (AWS Secrets Manager, HashiCorp Vault)
   - Never commit tokens to git

4. **Monitor Token Usage**
   - Check audit logs for unauthorized access
   - Review API rate limits
   - Monitor `audit_issue_create_failures_total` metric

## Rate Limits

GitHub API has rate limits that vary by authentication:

- **Authenticated requests**: 5,000 requests/hour
- **Unauthenticated requests**: 60 requests/hour

The audit system includes a rate-limit guard that:
- Checks remaining quota before creating issues
- Switches to digest mode when quota < 500
- Aborts if quota is exhausted

**Monitor quota usage**:
```bash
# Check current rate limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# View quota metrics
cat .metrics/github_api_quota_remaining.prom
```

## References

- [GitHub Token Scopes Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps)
- [Creating a Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [Permission Fallback System](tools/permission_fallback.py)

## Contact

For questions about token requirements or permission issues:
- File an issue in the audit automation repository
- Contact security@example.com
- Check `docs/CENTRAL_BACKLOG_README.md` for triage procedures

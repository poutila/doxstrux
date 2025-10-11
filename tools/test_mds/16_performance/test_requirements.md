# Test Requirements Document

## Section 1: Basic Requirements

The system MUST support user authentication.
Users SHOULD be able to reset their passwords.
The API MAY support webhooks for real-time updates.
The system MUST NOT store passwords in plain text.

## Section 2: Requirements in Lists

- The application MUST load within 3 seconds
- The database SHOULD support horizontal scaling
- The UI MAY include dark mode support
- Logs MUST NOT contain sensitive user data

## Section 3: Mixed Content

This paragraph contains a requirement: The system MUST validate all user inputs.

### Nested requirements

In nested sections, we still find requirements. The cache SHOULD expire after 1 hour.

> Even in blockquotes: The API MUST return proper HTTP status codes.

## Section 4: Complex Requirements

The authentication system MUST:
- Support multi-factor authentication
- Allow session management
- Integrate with OAuth providers

The logging system SHOULD NOT expose internal system details in production.
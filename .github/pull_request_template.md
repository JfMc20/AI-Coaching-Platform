## 📋 Description
Brief description of changes made and the problem they solve.

## 🔄 Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)  
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] 🧪 Tests (adding or updating tests)

## ✅ Pre-Implementation Checklist
- [ ] I have searched for similar functionality before creating new code
- [ ] I have followed the established patterns and naming conventions
- [ ] I have added type hints to all function parameters and return values
- [ ] I have used async/await for all I/O operations
- [ ] I have implemented proper error handling with appropriate HTTP status codes
- [ ] I have considered multi-tenant implications (if applicable)

## 🧪 Post-Implementation Checklist

### Code Quality
- [ ] Code follows the style guidelines (Black, isort, ruff)
- [ ] Self-review of code has been performed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] No code duplication exists
- [ ] Cyclomatic complexity is under 10 for all functions
- [ ] Functions are under 50 lines (or justified if longer)

### Testing & Documentation
- [ ] Unit tests have been added/updated and pass locally
- [ ] Test coverage is above 80% for new code
- [ ] Integration tests added/updated (if applicable)
- [ ] Corresponding changes to documentation have been made
- [ ] Manual testing performed

### Architecture & Performance
- [ ] Multi-tenant isolation has been verified (if applicable)
- [ ] Caching strategy implemented where appropriate
- [ ] Database queries are optimized
- [ ] Async patterns used correctly
- [ ] Resource cleanup implemented (connections, files, etc.)

## 🔒 Security Considerations
- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] Cross-tenant data access prevented
- [ ] Authentication/authorization properly implemented
- [ ] Security scan passes (bandit, safety)

## 🚀 API Changes (if applicable)
- [ ] OpenAPI documentation has been updated
- [ ] Breaking changes are documented with migration guide
- [ ] Backward compatibility is maintained or properly deprecated
- [ ] API versioning strategy followed
- [ ] Response schemas validated

## 🏗️ Database Changes (if applicable)
- [ ] Migration scripts created and tested
- [ ] Row Level Security policies updated (if needed)
- [ ] Indexes added for performance
- [ ] Backward compatibility maintained
- [ ] Rollback strategy documented

## 🤖 AI/ML Changes (if applicable)
- [ ] Model versioning implemented
- [ ] Embedding migration strategy defined
- [ ] Prompt templates versioned
- [ ] Fallback mechanisms implemented
- [ ] Performance impact assessed

## 🧪 Testing Strategy

### Unit Tests
- [ ] Business logic covered
- [ ] Edge cases tested
- [ ] Error conditions tested
- [ ] Mock external dependencies

### Integration Tests  
- [ ] API endpoints tested
- [ ] Database interactions tested
- [ ] External service integrations tested
- [ ] Multi-tenant scenarios tested

### Manual Testing
- [ ] Happy path verified
- [ ] Error scenarios tested
- [ ] Performance impact assessed
- [ ] UI/UX tested (if applicable)

## 📊 Performance Impact
- [ ] No significant performance degradation
- [ ] Database query performance analyzed
- [ ] Memory usage considered
- [ ] Caching effectiveness measured
- [ ] Load testing performed (if needed)

## 🚀 Deployment Notes
Any special deployment considerations, migration steps, or configuration changes required.

### Environment Variables
List any new environment variables or configuration changes:
- `NEW_VAR`: Description of what it does

### Migration Steps
1. Step 1
2. Step 2

### Rollback Plan
Describe how to rollback these changes if needed.

## 📸 Screenshots (if applicable)
Include screenshots for UI changes or visual features.

## 🔗 Related Issues
- Closes #[issue_number]
- Related to #[issue_number]

## 📝 Additional Notes
Any additional information that reviewers should know.

---

## 🔍 Reviewer Checklist
*For reviewers to complete:*

### Code Review
- [ ] Code follows project standards and patterns
- [ ] Logic is sound and efficient
- [ ] Error handling is appropriate
- [ ] Security considerations addressed
- [ ] Performance impact acceptable

### Testing Review
- [ ] Test coverage is adequate
- [ ] Tests are meaningful and not just for coverage
- [ ] Edge cases are covered
- [ ] Integration points tested

### Documentation Review
- [ ] Code is self-documenting or well-commented
- [ ] API documentation updated
- [ ] README or other docs updated if needed

### Architecture Review
- [ ] Changes align with system architecture
- [ ] Multi-tenancy preserved
- [ ] Scalability considerations addressed
- [ ] Dependencies are appropriate
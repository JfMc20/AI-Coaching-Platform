---
inclusion: always
---

# Spec Development Workflow Guide

## Overview

This document defines the complete specification development workflow for the multi-channel proactive coaching platform with AI. It establishes processes, roles, and tools to ensure high-quality deliveries.

## Project Context

### AI Coaching Platform MVP Status
**Current State**: Functional MVP with 4 implemented microservices
- ✅ Auth Service + Creator Hub + AI Engine + Channel Service
- ✅ FastAPI + PostgreSQL + Redis + Docker + Testing (85%+ coverage)
- ✅ Ollama + ChromaDB + Multi-tenancy with RLS

**Goal**: Scale from MVP to complete platform with 1,000+ creators and 50,000+ users

## Specification Workflow

### Phase 1: Requirements Analysis
**Input**: Business need, user story, or technical requirement  
**Output**: Requirements specification document  
**Agent**: `spec-requirements`  
**Duration**: 1-3 days  

**Process:**
1. **Stakeholder Consultation**: Gather information from product managers, users, and technical leads
2. **Business Analysis**: Understand business impact and value proposition
3. **Technical Constraints**: Review technical and architectural limitations
4. **Requirements Documentation**: Create detailed requirements specification

**Deliverables:**
- Requirements specification document
- User stories with acceptance criteria
- Business value assessment
- Preliminary risk analysis

**Quality Criteria:**
- Multi-tenant requirements clearly defined
- Performance targets specified (<2s API, <5s AI responses)
- Security requirements included (JWT, RLS, input validation)
- Integration points with existing services identified

### Phase 2: Design Specification
**Input**: Approved requirements specification  
**Output**: Technical design specification  
**Agent**: `spec-design`  
**Duration**: 2-5 days  

**Process:**
1. **Architecture Design**: Define components, interfaces, and data flows
2. **API Specification**: Design endpoints, models, and contracts
3. **Database Design**: Schemas, relationships, and optimizations
4. **Integration Planning**: Service-to-service communication
5. **Security Review**: Authentication, authorization, and data protection

**Deliverables:**
- Technical design document
- API specifications (OpenAPI)
- Database schemas and migrations
- Sequence diagrams and architecture diagrams
- Security implementation plan

**Architecture Requirements:**
- Follow existing microservices patterns (FastAPI + async/await)
- Implement RLS policies for all multi-tenant tables
- Use Pydantic models for all request/response validation
- Include Redis caching strategy for performance
- Define error handling with shared exception classes

### Phase 3: Task Breakdown
**Input**: Approved design specification  
**Output**: Detailed task list with estimates  
**Agent**: `spec-tasks`  
**Duration**: 1-2 days  

**Process:**
1. **Feature Decomposition**: Break down into implementable tasks
2. **Dependency Mapping**: Identify dependencies between tasks
3. **Effort Estimation**: Story points and time estimates
4. **Resource Assignment**: Match tasks with team skills
5. **Sprint Planning**: Organize tasks into sprints

**Deliverables:**
- Detailed task breakdown
- Sprint planning recommendations
- Resource allocation plan
- Risk assessment and mitigation strategies

**Task Standards:**
- Each task must specify multi-tenant implementation approach
- Include test coverage requirements (90%+ for new code)
- Define performance acceptance criteria
- Specify integration points with existing services

### Phase 4: Quality Review
**Input**: Requirements, design, and task specifications  
**Output**: Quality assessment and approval  
**Agent**: `spec-judge`  
**Duration**: 1 day  

**Process:**
1. **Technical Review**: Architecture, security, performance assessment
2. **Business Alignment**: Value delivery and market positioning
3. **Implementation Feasibility**: Resource and timeline viability
4. **Quality Standards**: Documentation and testing adequacy
5. **Risk Analysis**: Technical and business risk identification

**Deliverables:**
- Quality assessment report
- Approval/rejection recommendation
- Required improvements list
- Go/no-go decision

**Review Checklist:**
- Multi-tenant isolation properly implemented
- Security patterns follow established guidelines
- Performance targets achievable with current infrastructure
- Integration approach maintains service boundaries
- Error handling uses shared exception patterns

### Phase 5: Implementation
**Input**: Approved specifications and task breakdown  
**Output**: Working software implementation  
**Agent**: `spec-impl`  
**Duration**: Variable (based on task complexity)  

**Process:**
1. **Development Setup**: Environment and tooling preparation
2. **Code Implementation**: Following established patterns and standards
3. **Integration**: Service-to-service integration and testing
4. **Code Review**: Peer review and quality assurance
5. **Documentation**: Update technical documentation

**Deliverables:**
- Functional code implementation
- Unit and integration tests
- Updated documentation
- Deployment artifacts

**Implementation Standards:**
- Use async/await for all I/O operations
- Implement comprehensive type hints (95%+ coverage)
- Follow repository pattern for database operations
- Use shared models from `shared/models/` directory
- Implement proper error handling with structured exceptions

### Phase 6: Testing & Validation
**Input**: Implemented features  
**Output**: Tested and validated software  
**Agent**: `spec-test`  
**Duration**: 1-3 days (parallel with implementation)  

**Process:**
1. **Test Planning**: Define testing strategy and test cases
2. **Test Implementation**: Unit, integration, and E2E tests
3. **Test Execution**: Automated and manual testing
4. **Bug Reporting**: Issue identification and tracking
5. **Validation**: Acceptance criteria verification

**Deliverables:**
- Comprehensive test suite
- Test coverage reports
- Bug reports and resolutions
- Performance benchmarks
- User acceptance validation

**Testing Requirements:**
- Multi-tenant isolation verification (RLS policy testing)
- Performance testing (<2s API, <5s AI responses)
- Security testing (authentication, authorization, input validation)
- Integration testing with existing services
- Load testing for concurrent user scenarios

## Roles and Responsibilities

### Product Manager
- **Input Provision**: Business requirements and user needs
- **Stakeholder Coordination**: Alignment between business and technical teams
- **Priority Setting**: Feature prioritization and roadmap planning
- **Acceptance**: Final approval of deliverables

### Technical Lead/Architect
- **Architecture Guidance**: Technical direction and standards enforcement
- **Review Participation**: Design and implementation reviews
- **Risk Assessment**: Technical risk identification and mitigation
- **Mentorship**: Guidance for development team

### Development Team
- **Implementation**: Code development according to specifications
- **Code Review**: Peer review and quality assurance
- **Testing**: Unit and integration test development
- **Documentation**: Technical documentation maintenance

### QA Engineer
- **Test Strategy**: Testing approach and methodology
- **Test Implementation**: Automated and manual test development
- **Quality Assurance**: Quality gates and standards enforcement
- **Bug Tracking**: Issue management and resolution tracking

## Quality Gates

### Gate 1: Requirements Approval
**Criteria:**
- [ ] Business value clearly defined
- [ ] User stories complete with acceptance criteria
- [ ] Multi-tenant requirements specified
- [ ] Performance targets defined (<2s API, <5s AI)
- [ ] Security requirements included
- [ ] Technical feasibility validated
- [ ] Stakeholder sign-off obtained

### Gate 2: Design Approval
**Criteria:**
- [ ] Architecture aligns with existing microservices
- [ ] APIs follow OpenAPI standards
- [ ] Database design includes RLS policies
- [ ] Security patterns implemented (JWT, input validation)
- [ ] Performance requirements validated
- [ ] Integration points clearly defined

### Gate 3: Implementation Readiness
**Criteria:**
- [ ] Tasks include multi-tenant implementation
- [ ] Test coverage requirements specified (90%+)
- [ ] Dependencies identified and managed
- [ ] Resources allocated and available
- [ ] Risk mitigation plans in place

### Gate 4: Quality Validation
**Criteria:**
- [ ] Code follows established patterns (async/await, type hints)
- [ ] Multi-tenant isolation verified
- [ ] Security standards met
- [ ] Performance benchmarks achieved
- [ ] Documentation complete and clear

### Gate 5: Implementation Complete
**Criteria:**
- [ ] All acceptance criteria met
- [ ] Code reviews completed and approved
- [ ] Test coverage >90% with passing tests
- [ ] Multi-tenant RLS policies tested
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Gate 6: Production Ready
**Criteria:**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Security validation complete
- [ ] Performance validated under load
- [ ] Monitoring and alerts configured
- [ ] Deployment artifacts ready

## Tools and Templates

### Documentation Standards
- **Requirements Template**: Include multi-tenant considerations, performance targets, security requirements
- **Design Template**: Architecture diagrams, API specs (OpenAPI), database schemas with RLS
- **Task Template**: Implementation approach, test coverage requirements, integration points
- **Review Template**: Technical checklist, security validation, performance criteria

### Development Standards
- **Code Patterns**: Follow existing microservices structure (FastAPI + async/await)
- **Database**: Use repository pattern with RLS policies for all multi-tenant tables
- **Testing**: Achieve 90%+ coverage with multi-tenant isolation verification
- **Documentation**: Update shared models and API documentation

### Quality Assurance
- **Architecture Review**: Ensure alignment with existing patterns
- **Security Review**: JWT authentication, input validation, rate limiting
- **Performance Review**: <2s API response, <5s AI response targets
- **Multi-tenant Review**: RLS policy implementation and testing

## Metrics and KPIs

### Technical Quality Metrics
- **Code Coverage**: >90% for new features, >85% overall
- **Performance**: <2s API response (p95), <5s AI response (p95)
- **Security**: Zero critical vulnerabilities, proper multi-tenant isolation
- **Architecture**: Compliance with microservices patterns

### Process Metrics
- **Cycle Time**: Requirements to production deployment
- **Throughput**: Features delivered per sprint
- **Quality**: Defect rate and rework percentage
- **Predictability**: Estimation accuracy and on-time delivery

### Business Metrics
- **Time to Market**: Feature delivery speed
- **Development Efficiency**: Cost per feature delivered
- **Technical Debt**: Code maintainability scores
- **User Impact**: Feature adoption and satisfaction

## Implementation Guidelines for AI Assistants

### When Working on Specifications
1. **Multi-Tenant First**: Always consider creator_id isolation and RLS policies
2. **Performance Targets**: Include specific metrics (<2s API, <5s AI responses)
3. **Security Requirements**: JWT authentication, input validation, rate limiting
4. **Integration Points**: Clearly define service-to-service communication
5. **Testing Strategy**: Specify multi-tenant isolation testing approach

### Code Implementation Standards
1. **Architecture Patterns**: Follow existing microservices structure
2. **Database Operations**: Use repository pattern with async sessions
3. **Error Handling**: Implement shared exception classes
4. **Type Safety**: Comprehensive type hints and Pydantic models
5. **Performance**: Redis caching and async/await patterns

### Quality Validation Checklist
- [ ] Multi-tenant RLS policies implemented and tested
- [ ] Performance benchmarks met under load
- [ ] Security patterns properly implemented
- [ ] Integration with existing services verified
- [ ] Documentation updated with API changes
- [ ] Test coverage >90% with proper isolation testing

This workflow ensures all specifications are developed with high quality, delivered on time, and aligned with the platform's business objectives.
# AI Case Manager
## Software Requirements Specification (SRS)

**Version:** 1.0  
**Derived From:** AI Case Manager Final PRD  
**Product Stage:** College Project with Production-Ready Product Ambition  
**Primary Client:** Flutter Mobile Application  
**Backend:** Python FastAPI  
**Database:** PostgreSQL (Supabase)  
**ORM:** SQLAlchemy  
**Migrations:** Alembic

---

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification defines the functional, technical, security, integration, automation, testing, deployment, and operational requirements for the AI Case Manager application.

The system is an AI-assisted case-management platform that allows organizations to receive, understand, assign, investigate, communicate about, escalate, and resolve cases while maintaining complete ownership, history, auditability, and human control over important decisions.

## 1.2 Scope

The system shall support:

- Case creation and lifecycle management
- Multi-user collaboration
- Role-based access control
- Evidence and file management
- AI-assisted case understanding
- Assignment and ownership
- Investigation and tasks
- Communication and internal notes
- SLA and risk monitoring
- Escalation
- Notifications
- Resolution confirmation and reopening
- Complete timeline and audit history
- Managerial operational insights
- Administrative configuration
- Production-oriented deployment and testing

## 1.3 Primary Users

1. Requester
2. Case Operator
3. Team Lead
4. Manager
5. Administrator

## 1.4 Product Principle

The system shall preserve a clear case story, clear ownership, clear progress, and a clear next step. AI shall assist users while humans remain responsible for important decisions.

---

# 2. System Overview

## 2.1 High-Level Architecture

```text
Flutter Mobile Application
          |
          | HTTPS / REST API
          v
Python FastAPI Backend
          |
   +------+---------------------+------------------+
   |                            |                  |
   v                            v                  v
PostgreSQL / Supabase      AI Provider APIs   Notification/Email
   |
   +---- SQLAlchemy ORM
   +---- Alembic migrations

Additional services:
- Supabase/Object Storage for evidence files
- APScheduler for time-based SLA/risk/escalation checks
- Logging and application monitoring
```

## 2.2 Architecture Constraints

The first version shall NOT require:

- Dedicated Worker service
- Separate worker architecture
- Message queue such as RabbitMQ or Kafka
- n8n workflow engine
- Heavy long-running background workloads

The system does not assume heavy queued processing. Automation shall be implemented inside the FastAPI application using application services, asynchronous execution where useful, and an APScheduler-compatible scheduler for time-based operations.

A dedicated Worker, queue, or workflow engine may be introduced in a future version only when actual workload characteristics justify it.

## 2.3 Core Technology Requirements

| Area | Required Technology |
|---|---|
| Mobile | Flutter |
| Backend | Python + FastAPI |
| API | REST over HTTPS |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Managed Database | Supabase |
| Migrations | Alembic |
| Authentication | JWT-based authentication |
| Authorization | RBAC enforced by backend |
| File Storage | Supabase Storage or compatible object storage |
| AI | External AI API provider(s) |
| Scheduling | APScheduler or equivalent FastAPI-compatible scheduler |
| Testing | Pytest + FastAPI testing + Flutter tests |
| Containerization | Docker |
| Production Backend | Render or equivalent low-cost platform |
| Configuration | Environment variables/secrets |

---

# 3. User Roles and Authorization

## 3.1 Requester

The Requester shall be able to:

- Register and log in
- Create cases
- Upload evidence
- View their own cases
- View case status and updates
- Answer information requests
- View requester-visible communication
- Receive notifications
- Review proposed resolutions
- Confirm or reject resolution
- Reopen cases through resolution rejection where permitted

A Requester shall not be able to view another Requester's private case or internal notes.

## 3.2 Case Operator

The Operator shall be able to:

- View authorized new and assigned cases
- Review AI analysis
- Accept, edit, reject, or override AI recommendations where permitted
- Assign and reassign cases according to permissions
- Communicate with the Requester
- Add internal notes
- Create and manage investigation tasks
- Request missing information
- Update case states
- Record investigation findings
- Submit resolution

## 3.3 Team Lead

The Team Lead shall be able to:

- View team cases
- Monitor team workload
- View at-risk cases
- Review escalations
- Review operator workload
- Intervene through reassignment or case actions allowed by policy
- Monitor SLA conditions

## 3.4 Manager

The Manager shall be able to:

- View organization-level operational information
- Review trends
- Review SLA performance
- Review escalations
- Review workload and performance information
- Review important cases
- View AI-powered operational insights

## 3.5 Administrator

The Administrator shall be able to manage:

- Users
- Roles
- Teams
- Categories
- Organization settings
- Policies/configuration
- Audit history

Administrative privileges must not automatically be granted to other roles.

---

# 4. Functional Requirements

## FR-001 Authentication

The system shall provide secure registration and login functionality.

The backend shall issue authenticated access credentials using JWT-based authentication.

The system shall validate token expiration and reject unauthorized requests.

## FR-002 Role-Based Access Control

The system shall enforce role-based authorization on backend endpoints.

Authorization shall be enforced server-side and shall not rely only on Flutter UI restrictions.

## FR-003 Case Creation

The Requester shall be able to create a case with:

- Title or short description
- Detailed description
- Relevant category data when available
- Attachments/evidence where allowed
- Relevant location/context data

The system shall generate a unique case number.

## FR-004 Case Lifecycle

The system shall support the standard lifecycle:

**Reported → Understood → Assigned → Investigated → Action Taken → Resolution Proposed → Confirmed → Closed**

Temporary states shall include, as applicable:

- Waiting for Information
- Escalated
- Duplicate
- Reopened
- Cancelled

Only valid transitions shall be accepted by the backend.

## FR-005 Case Ownership

Every active case shall have clear ownership.

Assignment and reassignment shall record:

- Previous owner
- New owner
- Actor performing the change
- Timestamp
- Reason where required

## FR-006 Evidence and File Management

The system shall support attachments such as:

- Photos
- Screenshots
- Documents
- Videos where supported by the selected storage and application limits

Binary files shall be stored in object storage rather than as large binary fields in the relational database.

Database records shall store metadata and secure references to files.

## FR-007 AI Case Understanding

The system shall request AI analysis for newly created or materially updated cases.

AI analysis may produce:

- Likely category
- Likely subcategory
- Severity
- Priority
- Important details
- Missing information
- Potentially related cases
- Potential duplicates
- Suggested team
- Recommended next action

AI output shall be stored as recommendation data and shall not silently overwrite confirmed human-controlled case fields.

## FR-008 AI Case Summary

The system shall maintain an AI-generated case summary that can explain:

- Original report
- What has happened
- Confirmed findings
- Current unresolved items
- Current blockers

The summary should be refreshable when important case information changes.

## FR-009 Missing Information Detection

The AI service shall identify information that may materially help investigation.

The system shall allow the Operator to review and send a suggested question to the Requester.

## FR-010 Related/Duplicate Detection

The system shall compare new or updated cases with existing cases when appropriate.

The system shall display possible related or duplicate cases.

The system shall support human decisions such as:

- Link
- Mark as duplicate
- Keep separate
- Ignore suggestion

Cases shall not be automatically merged solely because AI suggests similarity.

## FR-011 Smart Assignment Recommendation

The system shall be able to recommend a team or person using available signals such as:

- Issue type
- Team responsibility
- Current workload
- Availability
- Location
- Relevant historical cases

Final assignment shall remain controlled by authorized users.

## FR-012 Communication

The system shall support case-linked communication between Requesters and Operators.

The system shall distinguish requester-visible communication from internal notes.

## FR-013 Internal Notes

Authorized staff shall be able to create private internal notes.

Internal notes must never be exposed to unauthorized Requesters.

## FR-014 Investigation

Authorized staff shall be able to record:

- Observations
- Actions taken
- Findings
- Evidence references
- Follow-up requirements

## FR-015 Tasks

A case shall support multiple tasks.

Each task should contain at minimum:

- Title
- Description where required
- Assignee
- Status
- Created timestamp
- Completion timestamp where applicable

## FR-016 SLA Management

The system shall support configurable response and resolution targets.

The system shall display useful SLA information, including remaining time and risk state.

## FR-017 Risk Detection

The system shall identify potentially risky cases using signals such as:

- Long inactivity
- Repeated follow-ups
- Multiple reassignments
- Missing information
- Increasing complexity
- Approaching deadlines
- Repeated reopening
- Unusually long resolution time

Risk warnings shall explain the underlying signals.

## FR-018 Escalation

The system shall support escalation due to conditions such as:

- Approaching deadline
- Missed deadline
- Serious issue
- Repeated unresolved complaint
- Operator-requested managerial assistance
- High-risk conditions

Escalations shall be traceable and visible to authorized users.

## FR-019 AI-Generated Communication Drafts

The system shall support AI-generated drafts for:

- Information requests
- Progress updates
- Resolution messages
- Escalation summaries

The Operator shall review and edit the draft before sending.

## FR-020 Notifications

The system shall support:

- In-app notifications
- Push notifications where supported
- Transactional email where configured

Examples:

- Case created
- Assignment
- Requester response
- New task
- SLA warning
- Escalation
- Resolution
- Reopening

Notification failures shall not invalidate the underlying case action.

## FR-021 Resolution

Authorized Operators shall be able to submit a resolution including:

- What was done
- What was found
- Supporting evidence
- Remaining limitations/issues where applicable

## FR-022 Resolution Confirmation

The Requester shall be able to:

- Confirm resolution
- Reject resolution

A rejected resolution shall reopen the case while preserving prior history.

## FR-023 Timeline

Every significant case event shall appear in chronological case history.

The timeline shall include system and user actions relevant to the case journey.

## FR-024 Audit Trail

The system shall retain audit events for important actions including:

- Creation
- Assignment/reassignment
- Priority changes
- Status changes
- AI recommendation generation
- AI recommendation override
- Information requests/responses
- Task actions
- SLA/risk events
- Escalation
- Resolution
- Reopening
- Closure

## FR-025 Search

Authorized users shall be able to search cases using available criteria such as:

- Case number
- Title
- Requester
- Category
- Status
- Team
- Assigned person
- Location

Natural-language search may be added as an enhancement.

## FR-026 Manager Operational Insights

The system shall provide organization-level insights such as:

- Case volume
- Active cases
- Resolution performance
- SLA performance
- Escalations
- Reopened cases
- Category trends
- Location trends
- Workload patterns
- Recurring operational issues

## FR-027 Administration

Administrators shall be able to manage the organizational data required by the case workflow, including users, teams, categories, policies, and configuration.

## FR-028 AI Availability Fallback

If the AI provider is unavailable:

- Case creation shall continue
- Case viewing shall continue
- Authorized assignment/update actions shall continue
- Case lifecycle shall continue
- AI-dependent results may be delayed/retried
- Failure shall be logged

AI availability shall not be the single point of failure for the core workflow.

---

# 5. Automation Requirements

## 5.1 Automatic AI Case Analysis

When a case is created, the backend shall initiate AI analysis through an application-level automation flow.

## 5.2 Automatic Case Summarization

The backend may refresh case summaries after meaningful case-history changes.

## 5.3 Automatic Missing Information Detection

The backend shall be able to analyze case context and produce missing-information recommendations.

## 5.4 Automatic Related/Duplicate Detection

The backend shall request similarity analysis against eligible existing cases.

## 5.5 Smart Assignment Recommendation

The backend shall generate assignment recommendations using available case and organizational data.

## 5.6 Automatic SLA and Risk Detection

The scheduler shall periodically evaluate applicable cases for SLA and risk conditions.

## 5.7 Escalation Automation

The scheduler/application services shall create or recommend escalation actions when configured conditions are met.

## 5.8 AI Communication Drafting

AI draft generation shall be performed on demand or as part of an application workflow and shall remain subject to human review before sending where required.

## 5.9 Automated Notifications

Case events shall invoke notification application services.

## 5.10 Automatic Timeline and Audit Logging

Important actions shall generate timeline/audit records as part of the same business operation wherever possible.

## 5.11 Operational Insights

Managers shall be able to request or view aggregated AI-assisted insights derived from multiple cases.

---

# 6. API Requirements

The exact URI naming can be finalized during implementation, but the API shall be organized by domain.

Suggested resource groups:

| Module | Example Endpoints |
|---|---|
| Auth | `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh` |
| Users | `/api/v1/users`, `/api/v1/users/{id}` |
| Teams | `/api/v1/teams`, `/api/v1/teams/{id}` |
| Categories | `/api/v1/categories`, `/api/v1/categories/{id}` |
| Cases | `/api/v1/cases`, `/api/v1/cases/{id}` |
| Assignments | `/api/v1/cases/{id}/assignment` |
| Messages | `/api/v1/cases/{id}/messages` |
| Notes | `/api/v1/cases/{id}/notes` |
| Tasks | `/api/v1/cases/{id}/tasks` |
| Investigation | `/api/v1/cases/{id}/investigations` |
| Attachments | `/api/v1/cases/{id}/attachments` |
| AI | `/api/v1/cases/{id}/ai-analysis`, `/api/v1/cases/{id}/summary` |
| SLA | `/api/v1/cases/{id}/sla` |
| Escalations | `/api/v1/cases/{id}/escalations` |
| Notifications | `/api/v1/notifications` |
| Audit | `/api/v1/cases/{id}/audit` |
| Dashboard | `/api/v1/dashboards/*` |
| Admin | `/api/v1/admin/*` |
| Health | `/health`, `/ready` |

The backend shall return consistent success/error response structures and HTTP status codes appropriate to the result.

---

# 7. Data Requirements

## 7.1 Core Entities

The minimum logical data model should include:

- User
- Role
- Permission
- Organization
- Team
- Category
- Case
- CaseAssignment
- CaseStatusHistory
- CaseMessage
- InternalNote
- Attachment
- Investigation
- Task
- SLARecord/Policy
- Escalation
- Resolution
- Notification
- AuditEvent
- AIAnalysis
- AIRecommendation
- RelatedCaseLink

## 7.2 Data Integrity

The backend shall enforce:

- Required fields
- Foreign-key consistency
- Valid case-state transitions
- Authorization boundaries
- Uniqueness where required
- Timestamp consistency

## 7.3 Migrations

All production schema changes shall be managed through Alembic migrations.

Database schema changes must not rely on manual production edits.

---

# 8. AI Requirements

## 8.1 Human-in-the-Loop

AI outputs shall be clearly distinguishable from confirmed system data.

Users shall be able to accept, edit, reject, or override AI recommendations where the workflow permits.

## 8.2 Uncertainty

The system shall communicate uncertainty where AI has inferred rather than confirmed information.

## 8.3 Explainability

Important AI recommendations should contain understandable reasoning/signals where practical, especially for risk, priority, and assignment suggestions.

## 8.4 AI Prompt/Input Safety

Sensitive organizational data sent to external AI providers shall be minimized and handled according to the selected provider's contractual and privacy requirements.

## 8.5 AI Failure Handling

AI timeouts, provider errors, malformed results, and validation failures shall be handled without breaking core case operations.

---

# 9. Security Requirements

## 9.1 Transport Security

Production API communication shall use HTTPS.

## 9.2 Authentication Security

- Passwords shall never be stored in plain text.
- Access tokens shall be validated server-side.
- Secrets shall not be committed to source control.
- JWT signing secrets/keys shall be environment-driven.

## 9.3 Authorization Security

Every protected endpoint shall enforce appropriate role and resource-level authorization.

## 9.4 File Security

Attachment access shall be authorized.

Publicly exposing sensitive case evidence by default shall be avoided.

## 9.5 Audit Security

Important security-sensitive and case-changing actions shall be auditable.

## 9.6 Input Validation

FastAPI/Pydantic validation and backend business rules shall validate incoming request data.

## 9.7 Secrets

The following must be environment-driven:

- Database URL/credentials
- JWT secrets/keys
- AI API keys
- Email provider credentials
- Push notification credentials
- Storage credentials
- Any external-service secrets

---

# 10. Non-Functional Requirements

## NFR-001 Performance

Normal CRUD/API operations should provide responsive user experience under expected student/demo and small production workloads.

AI operations may take longer than standard CRUD operations and shall expose appropriate loading/progress states.

## NFR-002 Availability

Core case operations should continue when an external AI or notification service is temporarily unavailable.

## NFR-003 Reliability

External integration failures shall be isolated and handled using retries where safe.

## NFR-004 Scalability

The first version shall be designed for modest workloads without introducing unnecessary distributed infrastructure.

The architecture shall allow future extraction of workers/queues if actual load requires them.

## NFR-005 Maintainability

The FastAPI backend should use clear separation of concerns between:

- Routers/API layer
- Schemas
- Services/business logic
- Data access/repositories where appropriate
- Models
- Integrations
- Security
- Configuration
- Background/scheduled automation

## NFR-006 Observability

The system shall provide:

- Structured application logs where practical
- Error logs
- Health checks
- Useful integration failure information
- Audit history for important business actions

## NFR-007 Usability

The Flutter application shall provide clear:

- Loading states
- Empty states
- Error states
- Success confirmations
- Permission-aware controls
- Consistent terminology

## NFR-008 Compatibility

The application shall target supported Flutter/Android environments selected during implementation and deployment.

## NFR-009 Data Persistence

Business-critical data shall be stored persistently in PostgreSQL/object storage rather than hardcoded in the client.

## NFR-010 Configuration

All environment-specific configuration shall be externalized through environment variables/secrets.

---

# 11. Error Handling and Retry Requirements

The backend shall return predictable error responses.

Errors should contain sufficient information for the client to display a useful message without exposing secrets or internal stack traces.

Retry behavior shall be considered for:

- AI provider calls
- Email delivery
- Push notification delivery
- External storage/API calls

Retries shall not create duplicate business actions. Idempotency or event-state checks shall be used where required.

The system shall log permanent failures after retry exhaustion.

---

# 12. Notification and Email Requirements

The system shall support transactional notifications for important case events.

Examples:

- Registration verification where applicable
- Password reset
- Case creation confirmation
- Assignment
- Requester information request
- Requester response
- SLA warning
- Escalation
- Resolution submission
- Reopening

The specific email provider is environment-specific. The production architecture shall not depend on an SMTP capability that is unavailable on the selected free hosting tier.

Notification/email failures shall not prevent the underlying case state transition.

---

# 13. Scheduling Requirements

The scheduler shall be lightweight and used only for time-based operations such as:

- SLA checks
- Risk checks
- Escalation checks
- Notification reminders where required
- Cleanup/maintenance jobs where justified

The scheduler shall not be used to simulate a heavy distributed queue.

Scheduled operations shall:

- Be idempotent where practical
- Record execution/failure information where useful
- Avoid duplicate escalations/notifications
- Be safe to recover after restart

---

# 14. Testing Requirements

## 14.1 Backend Unit Testing

Use Pytest for:

- Business rules
- Services
- Validation
- Permission logic
- Case-state transitions
- SLA calculations
- Escalation rules

## 14.2 API Integration Testing

Test:

- Authentication
- RBAC
- CRUD operations
- Case lifecycle
- File metadata handling
- Notifications
- AI integration boundaries
- SLA and escalation flows

## 14.3 Flutter Testing

Test:

- Core screens
- Navigation
- Form validation
- State handling
- Role-specific behavior
- API error states

## 14.4 End-to-End Testing

At minimum, a complete multi-user scenario shall cover:

1. Requester creates a case.
2. AI analysis is generated or safely skipped when unavailable.
3. Operator reviews the case.
4. Operator requests missing information.
5. Requester responds.
6. Operator creates/executes investigation tasks.
7. Team Lead reviews an at-risk/escalated condition.
8. Operator submits resolution.
9. Requester confirms or rejects resolution.
10. Manager reviews final operational information.

## 14.5 Regression Testing

Core workflow tests shall be executed after significant changes to backend, database, AI integrations, or role permissions.

---

# 15. Local Development Requirements

The project shall support local-first development before production deployment.

Minimum local setup:

- Flutter SDK
- Python environment
- FastAPI application
- PostgreSQL/Supabase development database
- Object storage configuration
- AI provider credentials for AI-enabled testing
- Email sandbox/test configuration where available

The project shall provide environment templates such as:

- `.env.example`

No secrets shall be committed to Git.

---

# 16. Deployment Requirements

## 16.1 Production Architecture

```text
Flutter Android App
        |
        v
 HTTPS API
        |
        v
FastAPI on Render
        |
        +---- PostgreSQL on Supabase
        +---- Supabase/Object Storage
        +---- External AI API
        +---- Transactional Email Provider
        +---- Push Notification Service
```

## 16.2 Deployment Rules

- Backend shall be deployable as a Dockerized FastAPI application.
- Database credentials shall be environment-driven.
- AI/email/push/storage credentials shall be environment-driven.
- Production shall use HTTPS.
- Database schema changes shall use Alembic.
- Health endpoints shall be available for deployment monitoring.

## 16.3 Free/Low-Cost Constraint

The first deployment should prefer free or low-cost services.

The architecture shall not depend on paid worker infrastructure or platform features unavailable on the selected free tier.

---

# 17. Logging and Monitoring

The backend shall provide logs for:

- Application startup/shutdown
- Authentication failures where appropriate
- Validation and application errors
- External-service failures
- AI failures
- Scheduler failures
- Important operational errors

The system shall expose health/readiness endpoints for basic monitoring.

Sensitive values such as passwords, JWT secrets, provider API keys, and full private credentials shall not be logged.

---

# 18. Production Quality Requirements

The implementation shall not be considered complete merely because screens exist.

A feature is complete only when it has:

- Backend business logic
- Persistent data where required
- Correct authorization
- Error handling
- Loading and empty states
- Validation
- Auditability where relevant
- Tests appropriate to its risk
- End-to-end integration with the rest of the system

The final application should feel like a real connected product rather than a collection of isolated screens.

---

# 19. Acceptance Criteria

The system will be considered ready for the first complete release when all of the following are demonstrated:

1. Multiple roles can authenticate securely.
2. Requester can create a case with evidence.
3. Case data is persisted in PostgreSQL.
4. Operator can view and manage authorized cases.
5. AI can provide meaningful recommendations when available.
6. Human users can override AI recommendations.
7. Requester and Operator can communicate within the case.
8. Internal notes remain private.
9. Tasks and investigations are persisted.
10. SLA and risk checks operate through the scheduler.
11. Escalations are traceable.
12. Notifications are generated for important events.
13. Resolution can be confirmed or rejected.
14. Rejected resolution reopens the case without losing history.
15. Timeline and audit history preserve important events.
16. Manager dashboards provide operational visibility.
17. Admin can manage core configuration required by the workflow.
18. Core workflow continues when the AI provider is unavailable.
19. Automated failures are logged and retried where appropriate.
20. Backend and mobile tests cover the critical workflow.
21. The system can be deployed with production configuration and environment variables.
22. A genuine multi-user end-to-end demonstration can be completed.

---

# 20. Future Scope

The following are not required for the first release unless later approved:

- Dedicated Worker architecture
- Message queues
- n8n/workflow engine
- Voice-based case creation
- Advanced document understanding
- Advanced semantic search
- Predictive workload management
- Organization-specific AI knowledge systems
- Advanced analytics
- Custom workflow builder
- Additional communication channels
- Mobile field-operations extensions
- Multi-organization SaaS
- Subscription and billing

Future infrastructure changes should be driven by actual product requirements and workload rather than introduced prematurely.

---

# 21. Traceability to PRD

This SRS converts the PRD's product principles and feature requirements into implementable system requirements.

Key traceability areas include:

| PRD Area | SRS Coverage |
|---|---|
| Multi-role experience | Sections 3, 4, 9 |
| Case lifecycle | FR-004, FR-021–FR-023 |
| AI triage | FR-007 |
| AI summary | FR-008 |
| Missing information | FR-009 |
| Related/duplicate detection | FR-010 |
| Smart assignment | FR-011 |
| SLA/risk | FR-016–FR-017 |
| Escalation | FR-018 |
| AI communication | FR-019 |
| Notifications | FR-020 |
| Resolution confirmation | FR-021–FR-022 |
| Timeline/audit | FR-023–FR-024 |
| Operational insights | FR-026 |
| Human override | Section 8 |
| AI fallback | FR-028 |
| Technical architecture | Sections 2, 16 |
| Automation | Section 5, Section 13 |
| Security | Section 9 |
| Testing | Section 14 |
| Production readiness | Sections 15–18 |

---

# 22. Final System Definition

AI Case Manager is a production-oriented, AI-assisted case management platform implemented as a **Flutter mobile application backed by a Python FastAPI REST API and PostgreSQL**, with AI, notification, email, and storage integrations.

The first release intentionally avoids unnecessary worker and queue infrastructure. Automation is implemented through FastAPI application services and a lightweight scheduler for time-based checks. The platform remains useful without AI, keeps humans responsible for important decisions, maintains a complete case story, and supports genuine multi-user end-to-end workflows.

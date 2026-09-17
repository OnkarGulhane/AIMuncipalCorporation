# AI Case Manager — AGENTS.md

## 1. Purpose

This file defines the engineering rules and execution workflow for building **AI Case Manager** according to:

- `PRD.md` / final PRD
- `SRS.md` / final SRS

Treat those documents as the source of truth for product scope and technical requirements.

The goal is to build a **real, production-oriented, multi-user application**, not a disconnected UI prototype.

---

## 2. Session Start Verification

At the beginning of every new agent session, output exactly:

> **Hello Omii — I have loaded the AI Case Manager PRD and SRS. I will follow them as the source of truth, verify my work before moving forward, and avoid inventing requirements or architecture.**

If the PRD or SRS is unavailable, stop and report that instead of guessing.

---

## 3. Source-of-Truth Rules

1. Read the PRD and SRS before implementing or changing architecture.
2. PRD defines product behavior, user journeys, features, roles, workflows, and scope.
3. SRS defines implementation-level functional and non-functional requirements.
4. Do not silently invent features, APIs, roles, workflows, or database behavior.
5. Do not remove a required feature merely because it is inconvenient to implement.
6. Keep implementation consistent across Flutter, FastAPI, database, AI, notifications, and deployment.
7. Do not change the approved architecture unless there is a genuine technical blocker; document the blocker and the proposed alternative first.

---

## 4. Final Technology Decisions

Use these technologies for the first release:

- Mobile: **Flutter**
- Backend/API: **Python + FastAPI**
- Database: **PostgreSQL**
- Managed PostgreSQL: **Supabase**
- ORM: **SQLAlchemy**
- Migrations: **Alembic**
- Authentication: **JWT-based authentication**
- Authorization: **Server-side RBAC**
- Roles:
  - Requester
  - Operator
  - Team Lead
  - Manager
  - Administrator
- File storage: **Supabase Storage or compatible object storage**
- AI: external AI provider APIs through a backend integration layer
- Scheduling: **APScheduler or an equivalent FastAPI-compatible scheduler**
- Testing: **Pytest + FastAPI testing + Flutter tests**
- Containerization: **Docker**
- Backend deployment target: **Render**
- Database/storage target: **Supabase**
- Configuration: **environment variables / `.env`**
- Production secrets: never hardcode

---

## 5. Explicit Architecture Constraints

For V1:

- **Do NOT create a dedicated Worker service.**
- **Do NOT create RabbitMQ/Kafka or another message queue.**
- **Do NOT introduce n8n.**
- **Do NOT create heavy background-processing infrastructure.**
- Do not assume long-running or high-volume queued workloads.
- Use FastAPI application services for normal automation.
- Use asynchronous execution where it is genuinely useful.
- Use APScheduler for time-based work such as SLA/risk/escalation checks.
- Keep the architecture simple and deployable on the intended low-cost/free-tier infrastructure.

A separate worker/queue architecture may be considered only in a future version when real workload characteristics justify it.

---

## 6. Core Product Principles

Always preserve these principles:

- AI assists; humans remain responsible for important decisions.
- AI recommendations must be distinguishable from confirmed facts.
- Users must be able to accept, edit, reject, or override important AI recommendations.
- AI must not become a single point of failure.
- Case creation and normal case management must continue when AI is temporarily unavailable.
- A Requester must not see another Requester's private case.
- Requesters must not see internal notes.
- Authorization must be enforced by the backend, not only by Flutter UI.
- Every important case action must be traceable.
- The complete case history must remain understandable.
- Closure is not enough; resolution confirmation matters.
- Features are not complete merely because a screen exists. The action must work end-to-end and persist correctly.

---

## 7. Required Case Lifecycle

Preserve the defined lifecycle:

**Reported → Understood → Assigned → Investigated → Action Taken → Resolution Proposed → Confirmed → Closed**

Temporary states may include:

- Waiting for Information
- Escalated
- Duplicate
- Reopened
- Cancelled

Do not invent alternative lifecycle rules without checking the PRD/SRS.

---

## 8. Implementation Order

Work in the following order unless a genuine dependency requires a small adjustment.

### Phase 0 — Repository and Requirements Audit

Before writing feature code:

1. Inspect the repository structure.
2. Read the final PRD and SRS.
3. Identify existing code, configuration, dependencies, and unfinished work.
4. Check whether any architecture already conflicts with the final requirements.
5. Produce a short implementation status report.
6. Do not rewrite working code without a reason.

### Phase 1 — Project Foundation

Set up:

- Flutter application
- FastAPI backend
- PostgreSQL/Supabase connection
- SQLAlchemy
- Alembic
- environment configuration
- Docker setup where required
- basic logging
- health endpoint
- clean folder structure

Verify that Flutter can reach FastAPI and FastAPI can reach PostgreSQL.

### Phase 2 — Database and Authentication

Implement:

- users
- roles
- authentication
- password handling
- JWT
- authorization dependencies
- profiles
- secure configuration

Create proper Alembic migrations.

Seed only safe development/demo data.

Never hardcode production credentials.

### Phase 3 — RBAC and Role-Based Experience

Implement backend permissions first.

Verify separately:

- Requester
- Operator
- Team Lead
- Manager
- Administrator

A UI restriction is never a substitute for backend authorization.

### Phase 4 — Core Case Management

Implement the case entity and complete basic lifecycle:

- create case
- case number
- category/status/priority
- ownership
- assignment
- case details
- attachments metadata
- timeline/history
- status transitions
- case listing/filtering/search
- persistent PostgreSQL storage

Use real API calls and real database persistence.

### Phase 5 — Communication, Notes, Tasks, Investigation

Implement:

- requester/operator communication
- internal notes
- tasks
- task ownership/status
- investigation observations
- findings
- evidence
- follow-up requirements

Ensure internal notes can never leak into requester-visible communication.

### Phase 6 — File Storage

Implement real file/object storage for case evidence.

Verify:

- upload
- metadata persistence
- authorized access
- download/view
- invalid-file/error handling

Do not store large files directly inside PostgreSQL unless explicitly required.

### Phase 7 — AI Integration

Implement AI as a backend integration layer.

Required AI capabilities include:

1. Case understanding/triage
2. Suggested category/subcategory
3. Severity/priority suggestion
4. Missing information detection
5. Related/duplicate case detection
6. Suggested team/assignment
7. Recommended next action
8. Case summary
9. AI-generated communication drafts
10. Risk insights
11. Operational insights where required

Rules:

- Never silently overwrite confirmed case data.
- Store AI recommendations separately from confirmed values where appropriate.
- Record important AI recommendations in audit history.
- Handle AI timeouts/failures gracefully.
- Never expose provider secrets to Flutter.

### Phase 8 — Automation, SLA, Risk, and Escalation

Implement automation using FastAPI application services.

Use APScheduler for time-based checks.

Implement:

- SLA/deadline calculation
- approaching-deadline detection
- inactivity/risk checks
- risk explanation
- escalation conditions
- escalation creation/visibility
- scheduled checks
- retry/error handling

Do not introduce a Worker or message queue to implement these requirements.

### Phase 9 — Notifications and Email

Implement:

- in-app notifications
- push notifications where supported
- transactional email
- notification preferences/meaningful event rules where required
- delivery failure handling
- retries where appropriate

Expected events include:

- new case
- assignment
- requester response
- task
- SLA warning
- escalation
- resolution
- reopening
- important status updates

Do not rely on platform infrastructure that is unavailable on the selected free tier.

### Phase 10 — Dashboards and Admin

Build separate role-aware experiences:

Requester:
- active cases
- waiting cases
- recent updates
- resolved cases
- notifications
- create case

Operator:
- new/assigned cases
- high priority
- at-risk
- waiting for information
- escalations
- pending tasks

Team Lead:
- team workload
- at-risk cases
- escalations
- unassigned work
- deadlines
- operator workload

Manager:
- total/active/resolved cases
- SLA performance
- average resolution time
- escalations
- reopened cases
- trends
- team/category performance
- operational insights

Administrator:
- users
- teams
- categories
- policies/rules
- organization settings
- audit history

### Phase 11 — Audit, Search, Reliability, and UX Hardening

Verify:

- complete audit trail
- useful case timeline
- search/filter behavior
- loading states
- empty states
- error states
- retry behavior
- validation messages
- permission errors
- network failure behavior
- AI failure behavior
- consistent terminology
- responsive/professional Flutter UI

### Phase 12 — Testing

Do not finish development before testing.

Backend:

- unit tests
- API tests
- authorization/RBAC tests
- validation tests
- database/integration tests where appropriate
- AI failure-path tests
- scheduler tests
- SLA/escalation tests

Flutter:

- widget tests where useful
- service/API tests
- role-access tests
- important user-flow tests

End-to-end:

- Requester creates case
- Operator reviews it
- AI analysis appears
- information is requested
- Requester responds
- Operator investigates
- Team Lead intervenes when required
- Operator submits resolution
- Requester confirms/rejects
- Manager reviews history

### Phase 13 — Production Readiness

Before deployment, verify:

- no hardcoded secrets
- production environment variables
- database migrations work
- logging works
- health endpoint works
- error responses are consistent
- critical failures are handled
- storage permissions are secure
- JWT configuration is production-safe
- CORS is configured appropriately
- Docker build works
- production Flutter build works
- Render deployment works
- Supabase connection works
- real multi-user testing works

### Phase 14 — Final Verification and Demo

Run the complete PRD demo scenario.

Use separate accounts for:

- Demo Requester
- Demo Operator
- Demo Team Lead
- Demo Manager
- Demo Administrator

Verify the complete connected workflow, not isolated screens.

---

## 9. Development Method

Use a vertical-slice approach.

For each major feature:

1. Define the backend model/rules.
2. Create/update migration.
3. Implement FastAPI schema.
4. Implement service/business logic.
5. Implement API endpoint.
6. Add authorization.
7. Add tests.
8. Connect Flutter.
9. Verify loading/error/empty states.
10. Test the complete user journey.
11. Only then move to the next dependent feature.

Do not build the entire UI first and postpone the backend.

---

## 10. Verification Gate

After every phase, verify:

- Does it satisfy the PRD/SRS?
- Does data persist correctly?
- Does the correct role have access?
- Does another role incorrectly gain access?
- Do errors fail safely?
- Are there tests?
- Is the implementation connected end-to-end?
- Did the change accidentally break another workflow?

Do not claim a feature is complete until it is actually tested.

---

## 11. Code Quality Rules

- Keep clear separation of concerns.
- Keep business logic out of Flutter widgets.
- Keep business rules out of API route handlers where practical.
- Use typed request/response schemas.
- Validate inputs.
- Use database transactions where necessary.
- Avoid duplicated business logic.
- Keep naming consistent with PRD/SRS terminology.
- Prefer simple architecture over unnecessary infrastructure.
- Do not add dependencies without a real reason.
- Keep configuration environment-driven.
- Never commit secrets.

---

## 12. AI Safety and Trust Rules

AI output is advisory.

The implementation must:

- clearly label AI recommendations
- preserve uncertainty where relevant
- prevent unsupported assumptions from being presented as facts
- allow human override
- record important overrides when required
- handle provider failures and timeouts
- avoid making AI a mandatory dependency for ordinary case operations

Do not fabricate AI results merely to make a UI appear complete.

---

## 13. Communication to the User

After completing a meaningful phase, report:

- what was implemented
- important files/modules changed
- what was tested
- test result
- any remaining blocker

Do not give false completion statements.

If a requirement is genuinely blocked, state:

**BLOCKED — [specific reason]**

and identify the smallest practical solution.

Do not repeatedly ask for confirmation for routine implementation decisions that are already defined by the PRD/SRS.

---

## 14. Forbidden Changes Without Explicit Requirement

Do not introduce these into V1:

- Spring Boot
- Node.js backend
- a dedicated worker service
- RabbitMQ
- Kafka
- n8n
- unnecessary microservices
- heavy distributed job infrastructure
- fake/mock production data as the actual implementation
- client-only authentication
- hardcoded credentials
- fake AI responses presented as real AI
- fake notifications presented as delivered notifications

---

## 15. Definition of Done

A feature is **Done** only when:

- backend logic exists
- database persistence exists where required
- API works
- authorization is enforced
- Flutter UI is connected
- errors/loading/empty states are handled
- tests exist and pass
- audit/timeline behavior is implemented where applicable
- the complete user action produces the expected system-wide result

A screen alone is never considered Done.

---

## 16. Final Principle

Build this project as one connected product:

**People → Cases → Evidence → Communication → Tasks → AI Insights → Deadlines → Escalations → Resolution**

Keep the implementation simple enough for the intended low-cost deployment, but strong enough to demonstrate real production-oriented engineering.

**Follow the PRD and SRS. Build incrementally. Verify every step. Do not hallucinate requirements.**

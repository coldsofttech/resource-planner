# Repository Structure Guide

## Purpose

This document outlines the standard repository structure, architectural boundaries, ownership rules, and engineering conventions for the platform.

The repository is designed to support:

- A modular Django application
- Background jobs and serverless workloads
- Future separation of API and UI runtimes
- Shared reusable Python packages
- Infrastructure as code
- Scalable CI/CD pipelines
- Multi-team development
- Long-term maintainability

This repository follows a **modular monolith** architecture today, while remaining structured for future service extraction if required.

## High-Level Repository Layout

```
repo-root/
|
|--- apps/
|    |--- web/                  # Current Django monolith
|    |    |--- manage.py
|    |    |--- requirements.txt
|    |    |
|    |    |--- config/          # Django settings/project config
|    |    |    |--- settings/
|    |    |    |--- urls.py
|    |    |    |--- asgi.py
|    |    |    |--- wsgi.py
|    |    |
|    |    |--- apps/            # Django domain apps
|    |    |    |--- users/
|    |    |    |    |--- admin.py
|    |    |    |    |--- api_urls.py
|    |    |    |    |--- api_views.py
|    |    |    |    |--- apps.py
|    |    |    |    |--- models.py
|    |    |    |    |--- serializers.py
|    |    |    |    |--- selectors.py
|    |    |    |    |--- services.py
|    |    |    |    |--- signals.py
|    |    |    |    |--- urls.py
|    |    |    |    |--- views.py
|    |    |    |    |--- engine.py
|    |    |    |    |--- tests/
|    |    |    |    |    |--- tests_api.py
|    |    |    |    |    |--- tests_services.py
|    |    |    |
|    |    |    |--- projects/
|    |    |    |--- ...
|    |    |
|    |    |--- static/
|    |    |    |--- css/
|    |    |    |--- js/
|    |    |
|    |    |--- templates/
|    |
|    |--- jobs/
|    |    |--- daily_reports/
|    |    |    |--- handler.py
|    |    |    |--- requirements.txt
|    |    |    |--- tests/
|    |    |    |--- serverless.yml
|    |    |
|    |    |--- cleanup/
|    |
|    |--- ui/                   # Future Node/React frontend
|
|--- packages/                  # Shared reusable libraries
|    |--- logging/
|    |    |--- pyproject.toml
|    |    |--- logging/
|    |    |    |--- __init__.py
|    |    |--- tests/
|    |
|    |--- utils/
|
|--- infrastructure/
|    |--- terraform/
|    |--- scripts/
|
|--- docs/
|    |--- architecture/
|    |--- deployment/
|    |--- api/
|
|--- .github/
|    |--- workflows/
|    |    |--- web-ci.yml
|    |    |--- jobs-ci.yml
|    |    |--- deploy.yml
|    |    |--- codeql.yml
|    |    |--- security.yml
|    |
|    |--- dependabot.yml
|
|--- .env.example
|--- .gitignore
|--- Makefile
|--- README.md
|--- pyproject.toml
```

## Architectural Philosophy

The repository follows several important architectural principles.

### 1. Domain-Oriented Design

Code is grouped primarily by business domain rather than technical layer.

Example:

Good:

```
apps/web/apps/users/
apps/web/apps/projects/
apps/web/apps/resource-plans/
```

Avoid:

```
api/users/
services/users/
models/users/
```

The goal is to keep all functionality related to a domain co-located.

This improves:

- discoverability
- ownership
- modularity
- onboarding
- future extraction
- testing

### 2. Thin Transport Layers

API and UI layers should remain thin.

Business logic must NOT live in:

- views
- serializers
- signals
- forms
- controllers

Business logic belongs in:

```
services.py
```

### 3. Explicit Boundaries

The repository separates:

- deployable applications
- reusable shared packages
- infrastructure code
- documentation
- operational workflows

This reduces coupling and improves maintainability.

### 4. Shared Code Must Be Intentional

Shared code belongs in:

```
packages/
```

Only code that is genuinely reusable across multiple systems should be placed there.

Domain-specific business logic should remain within the owning application.

## Top-Level Directories

### `/apps`

Contains deployable applications and runtime systems.

Each application may:

- have independent deployment pipelines
- own runtime configuration
- have independent dependencies
- evolve separately over time

Structure:

```
apps/
|--- web/
|--- jobs/
|--- api/
|--- ui/
```

### `/apps/web`

Primary Django application.

Currently contains:

- Django admin
- Django templates/UI
- Django REST API
- domain models
- business services
- authentication
- authorization
- background tasks

Future evolution:

- API may move into `/apps/api`
- Frontend may move into `/apps/ui`
- Web app may become an internal/admin application only

### `apps/web/` Structure

```
apps/web/
|--- manage.py
|--- requirements.txt
|
|--- config/
|    |--- settings/
|    |--- urls.py
|    |--- asgi.py
|    |--- wsgi.py
|
|--- apps/
|    |--- users/
|    |--- projects/
|    |--- ...
|
|--- static/
|    |--- css/
|    |--- js/
|
|--- templates/
```

### `apps/web/config`

Contains Django project-level configuration.

Example:

```
config/
|--- settings/
|    |--- base.py
|    |--- dev.py
|    |--- prod.py
|
|--- urls.py
|--- asgi.py
|--- wsgi.py
```

Responsibilities:

- Django settings
- middleware configuration
- installed apps
- root routing
- WSGI/ASGI setup
- environment-specific configuration

Rules:

- Do not place business logic here
- Keep settings environment-driven
- Use environment variables for secrets
- Avoid importing application models into settings

### `/apps/web/apps`

Contains domain-oriented Django applications.

Each domain app owns:

- models
- API endpoints
- UI components
- business logic
- permissions
- tests
- tasks
- admin configuration

Example:

```
apps/
|--- users/
|--- projects/
|--- notifications/
|--- resource-plans/
```

Each domain should represent a business capability.

## Domain App Structure

Each Django admin app follows a flat, domain-oriented structure.

Example:

```
apps/users/
|--- admin.py
|--- api_urls.py
|--- api_views.py
|--- apps.py
|--- models.py
|--- serializers.py
|--- selectors.py
|--- services.py
|--- signals.py
|--- urls.py
|--- views.py
|--- engine.py
|--- tests/
|    |--- tests_api.py
|    |--- tests_services.py
```

The objective is to keep all functionality related to a business domain co-located inside a single Django app.

This improves:

- discoverability
- ownership
- modularity
- onboarding
- maintainability
- future extraction capability

### `api_views.py` and `api_urls.py`

Contains REST API transport logic for the domain.

Example:

```
api_views.py
api_urls.py
serializers.py
```

Responsibilities:

- request validation
- serialization
- authentication integration
- API permissions
- response formatting
- API routing

Rules:

- Keep API views thin
- Delegate business logic to services
- Avoid complex ORM logic directly inside API views
- Avoid side effects inside serializers
- Avoid large view classes

Example:

```python
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        user = UserService.create_user(request.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        UserService.deactivate_user(user)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

The preferred API architecture uses DRF `ViewSet` and router-based routing.

Guidelines:

- Use standard ViewSet methods for CRUD operations
- Override default methods only when business workflows require customization
- Use `@action` for domain-specific operations
- Keep ViewSets thin
- Delegate workflows to services
- Avoid embedding business logic directly in ViewSets
- Prefer explicit service calls over serializer side effects

### `views.py` and `urls.py`

Contains Django-rendered UI logic.

The current architectural direction is intentionally minimal server-rendered UI.

Django views hould primarily:

- render initial HTML pages
- serve authenticated entry points
- provide layout/template composition
- support lightweight SSR where necessary

Most user interactions should be:

- JavaScript-driven
- API-driven
- progressively decoupled from Django templates

This approach simplifies the future migration toward:

- React
- Next.js
- Node.js frontend applications

without major backend restructuring.

Recommended pattern:

```python
class DashboardView(View):
    def get(self, request):
        return render(request, "dashboard/index.html")
```

Frontend behavior should primarily interact with:

- DRF ViewSets
- REST endpoints
- asynchronous API requests

Rules:

- Keep Django views minimal
- Prefer GET-only page rendering views
- Avoid embedding business logic in views
- Avoid heavy form-processing workflows
- Avoid tightly coupling templates to backend state
- Prefer APIs for mutations and dynamic interactions

The current Django monolith supports both:

- lightweight server-rendered UI
- REST APIs

within the same domain app while remaining migration-friendly for future frontend separation.

### `models.py`

Contains Django ORM models for the domain.

Responsibilities:

- persistence structure
- ORM relationships
- database constraints
- lightweight model methods

Rules:

- Avoid heavy business logic
- Avoid orchestration logic
- Avoid network calls
- Avoid cross-domain side effects
- Prefer services for workflows

### `services.py`

Contains business logic and workflows.

This is one of the most important architectural layers.

Example responsibilities:

- orchestration
- business rules
- workflows
- transactional operations
- coordination between models
- external integrations

Example:

```python
class UserService:
    @staticmethod
    def create_user(data):
        ...
```

Rules:

- Most business logic belongs here
- Services may call selectors
- Services may call repositories
- Services may emit events
- Services should remain testable
- Services should avoid HTTP concerns

### `selectors.py`

Contains read/query logic.

Selectors centralize ORM access patterns.

Example:

```python
def get_active_users():
    return User.objects.filter(is_active=True)
```

Benefits:

- reusable queries
- easier optimization
- centralized filtering logic
- reduced ORM duplication
- easier caching

Rules:

- Selectors should not mutate state
- Keep selectors query-focused
- Avoid business workflows in selectors

### `admin.py`

Contains lightweight Django admin registrations and configuration.

The admin layer should remain intentionally thin.

Primary responsibilities:

- model registration
- list display configuration
- filtering
- search configuration
- readonly field setup
- lightweight operational tooling

Example:

```python
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "is_active"]
    search_fields = ["email"]
```

Architectural direction:

The platform should NOT rely heavily on Django Admin as a primary business application.

Instead:

- product workflows should live in the main application UI
- APIs should power operational workflows
- admin should remain operational/support-focused

Rules:

- Keep admin lightweight
- Avoid embedding business workflows in admin actions
- Avoid large custom admin applications
- Avoid placing critical business operations only in admin
- Prefer services for orchestration
- Admin actions should delegate to services

Django Admin should primarily function as:

- operational tooling
- support tooling
- data inspection interface
- emergency maintenance interface

rather than the primary product experience.

### `apps.py`

Contains Django application configuration.

Responsibilities:

- app metadata
- application startup hooks
- signal registration
- lightweight initialization

Example:

```python
class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self):
        import apps.users.signals
```

Rules:

- Keep startup lightweight
- Avoid heavy initialization logic
- Avoid network calls during startup
- Avoid database queries during startup
- Use primarily for application wiring

The application startup path should remain fast and predictable.

### `signals.py`

Contains Django signal handlers.

Signals should be used sparingly and intentionally.

Good use cases:

- audit logging
- metrics
- lightweight side effects
- decoupled notifications

Avoid using signals for:

- core business workflows
- transactional orchestration
- hidden side effects
- critical application behavior

Example:

```python
@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        metrics.increment("user.created")
```

Architectural guidance:

Prefer:

```
explicit service calls
```

over:

```
implicit signal chains
```

Rules:

- Keep signals lightweight
- Avoid cascading signal behavior
- Avoid complex dependency chains
- Avoid business-critical workflows in signals
- Prefer explicit orchestration in services.py

Heavy signal usage often creates:

- debugging difficulty
- hidden side effects
- circular dependencies
- unpredictable execution flow

### `engine.py`

Contains heavy domain-specific business engines and orchestration logic.

This layer is reserved for:

- complex business rules
- workflow engines
- calculation engines
- rule processing
- state machines
- domain orchestration
- large decision trees
- AI/ML orchestration
- advanced processing pipelines

The purpose of engine.py is to isolate highly complex domain behavior from:

- API layers
- services.py
- Django models
- UI concerns

Example responsibilities:

- pricing engine
- recommendation engine
- workflow engine
- rules evaluation
- approval processing
- automation orchestration

Example:

```python
class PricingEngine:
    def calculate_quote(self, customer, products):
        ...
```

Architectural distinction:

`services.py` coordinates workflows
`engine.py` performs heavy domain computation and processing

Rules:

- Engines should remain highly testable
- Engines should remain deterministic where possible
- Avoid HTTP concerns
- Avoid framework coupling
- Avoid UI concerns
- Prefer pure business/domain logic

The engine layer should evolve independently from transport and framework concerns.

### `tests/`

Contains tests owned by the domain app.

Example:

```
tests/
|--- tests_api.py
|--- tests_services.py
|--- tests_selectors.py
|--- tests_permissions.py
|--- tests_engine.py
```

Responsibilities:

- API testing
- service testing
- engine testing
- authorization testing
- regression testing
- workflow validation
- integration testing

Testing philosophy:

The platform prioritizes:

- service-level testing
- engine testing
- authorization testing
- integration testing
- regression protection

Recommended test pyramid:

- many service/engine tests
- moderate integration tests
- fewer end-to-end tests

Rules:

- Keep tests close to implementation
- Prefer domain ownership of tests
- Test business rules heavily
- Test authorization explicitly
- Test failure scenarios
- Test edge cases
- Prefer deterministic tests
- Avoid unnecessary mocking

Critical business workflows should always have:

- happy path coverage
- failure path coverage
- authorization coverage
- edge case coverage

### `/apps/jobs`

Contains scheduled jobs and serverless workloads.

Examples:

- cron jobs
- Lambda handlers
- synchronization tasks
- reporting
- cleanup jobs
- ETL workflows

Structure:

```
apps/jobs/
|--- daily_reports/
|--- cleanup/
```

Each job should be independently deployable.

### Job Structure

Example:

```
daily_reports/
|--- handler.py
|--- services.py
|--- tests/
|--- requirements.txt
|--- README.md
```

Rules:

- Jobs should remain isolated
- Jobs should avoid coupling to Django internals
- Shared logic should move into packages
- Jobs should remain idempotent where possible
- Avoid giant shared job runtimes

### `/apps/api`

Reserved for future standalone API runtime.

Potential future implementations:

- Django API-only service
- FastAPI
- GraphQL gateway
- internal platform APIs

This directory may eventually absorb API responsibilities currently inside `/apps/web`.

### `/apps/ui`

Reserved for future standalone frontend runtime.

Potential implementations:

- React
- Next.js
- Vue
- mobile web

This allows future frontend separation without major repository restructuring.

### `/packages`

Contains reusable shared Python packages.

Purpose:

- reduce duplication
- share infrastructure code
- share utilities
- share contracts
- standardize cross-system behavior

Structure:

```
packages/
|--- logging/
|--- events/
```

## Shared Package Principles

Good candidates:

- authentication helpers
- logging utilities
- database utilities
- event contracts
- SDK wrappers
- shared infrastructure
- common serializers

Avoid placing:

- domain business logic
- app-specific workflows
- tightly coupled Django code

inside shared packages.

Packages should remain:

- framework-light
- reusable
- independently testable

### Example Shared Package

```
packages/auth/
|--- pyproject.toml
|--- auth/
|    |--- jwt.py
|    |--- permissions.py
|    |--- middleware.py
|--- tests/
```

Usage:

```python
from auth.jwt import validate_token
```

### `/infrastructure`

Contains infrastructure and deployment code.

Examples:

```
infrastructure/
|--- terraform/
|--- scripts/
```

Responsibilities:

- infrastructure as code
- deployment configuration
- observability
- environment setup
- containerization
- CI/CD helpers

Rules:

- Infrastructure should not be scattered across apps
- Reusable deployment patterns should be centralized
- Environment configuration should remain explicit

### `/docs`

Contains engineering documentation.

Structure:

```
docs/
|--- architecture/
|--- deployment/
|--- api/
```

### `/docs/architecture`

Contains system architecture documentation.

Examples:

```
architecture/
|--- repo-structure.md
|--- auth.md
|--- api-design.md
|--- deployment.md
|--- jobs-architecture.md
|--- frontend-strategy.md
```

Purpose:

- explain architectural decisions
- define conventions
- describe system boundaries
- improve onboarding

### `/docs/deployment`

Contains deployment and operational how-to documentation.

This directory should contain practical operational guidance for:

- local development
- production deployments
- rollback procedures
- infrastructure operations
- CI/CD workflows
- debugging operational issues
- environment management

Examples:

```
deployment/
|--- local-development.md
|--- environment-variables.md
|--- database-migrations.md
|--- deployment-process.md
|--- rollback-procedures.md
|--- lambda-deployments.md
|--- infrastructure-setup.md
|--- application-setup.md
|--- ci-cd.md
|--- monitoring.md
|--- troubleshooting.md
```

The deployment documentation should prioritize:

- operational clarity
- reproducibility
- step-by-step instructions
- incident reduction
- onboarding efficiency

Documentation should answer:

- how to run locally
- how to deploy safely
- how to rollback safely
- how to debug failures
- how environments are configured
- how secrets are managed
- how CI/CD works
- how infrastructure is provisioned

### `/docs/api`

Contains API documentation and API integration guidance.

This directory should focus on:

- API standards
- authentication
- request/response conventions
- versioning
- integration examples
- error handling
- frontend integration guidance
- third-party integration guidance

Examples:

```
api/
|--- authentication.md
|--- conventions.md
|--- error-handling.md
|--- pagination.md
|--- filtering.md
|--- versioning.md
|--- rate-limiting.md
|--- examples.md
|--- webhooks.md
|--- openapi.md
```

The API documentation should answer:

- how to authenticate
- how APIs are structured
- how pagination works
- how filtering works
- how errors are returned
- how rate limits work
- how versioning works
- how integrations should be built

### `/.github`

Contains repository automation and workflows.

Structure:

```
.github/
|--- workflows/
|--- dependabot.yml
```

### `/workflows`

Contains CI/CD pipelines.

Examples:

```
workflows/
|--- web-ci.yml
|--- jobs-ci.yml
|--- deploy.yml
|--- security.yml
|--- codeql.yml
```

Responsibilities:

- testing
- linting
- security scanning
- deployment
- package publishing

Rules:

- Pipelines should remain focused
- Use path-based workflow triggers where possible
- Security checks are mandatory

### Security Standards

The repository should enforce:

- OWASP ASVS guidance
- secure dependency management
- automated vulnerability scanning
- secret scanning
- branch protection
- code review requirements

Recommended tooling:

- CodeQL
- Dependabot
- pip-audit
- Bandit
- Pytest

### Dependency Management

The repository uses:

```
pyproject.toml
```

as the primary Python tooling configuration.

This centralizes:

- formatting
- linting
- type checking
- packaging
- testing

### Testing Philosophy

The system should prioritize:

- service-level testing
- authorization testing
- integration testing
- API contract testing
- regression testing

Recommended test pyramid:

- many unit/service tests
- moderate integration tests
- fewer end-to-end tests

### Logging Standards

All systems should implement:

- structured logging
- correlation IDs
- audit logging
- standardized error logging

Sensitive information must NEVER be logged.

Examples:

- passwords
- tokens
- secrets
- session cookies
- API credentials

### API Standards

REST APIs should:

- use Bearer authentication
- use versioned endpoints
- implement rate limiting
- validate all input
- return structured errors
- support observability

Example:

```
Authorization: Bearer <token>
```

### Authentication Standards

Preferred standards:

- OAuth2 conventions
- OpenID Connect compatibility
- short-lived access tokens
- refresh tokens
- HTTPS-only communication

## Repository Rules

### Allowed

- Thin views
- Explicit services
- Centralized query logic
- Explicit permissions
- Domain ownership
- Reusable infrastructure packages

### Avoid

- Fat models
- Business logic in serializers
- Heavy signal usage
- Massive utils.py files
- Circular dependencies
- Cross-domain ORM leakage
- Hidden side effects

## Long-Term Evolution Strategy

The repository is intentionally structured to support future scaling.

Potential future evolution:

```
Today:
apps/web
apps/jobs

Future:
apps/api
apps/ui
```

without requiring major repository reorganization.

The architecture prioritizes:

- modularity
- explicit boundaries
- maintainability
- operational scalability
- team scalability
- future extraction flexibility

## Summary

This repository structure is designed to:

- support rapid development
- reduce architectural drift
- improve maintainability
- enable multi-team collaboration
- support future service separation
- centralize engineering standards
- improve operational consistency

The most important architectural principles are:

1. Domain-oriented organization
2. Thin transport layers
3. Explicit business services
4. Reusable shared infrastructure
5. Strong documentation
6. Explicit ownership boundaries
7. Long-term scalability

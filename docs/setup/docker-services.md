# Local Docker Services

The development environment uses Docker Compose to run optional backing services.
All services are **profile-gated** — nothing starts automatically unless the relevant configuration is in place.
The dev control panel (`scripts/dev/dev.py`) detects which services are needed and starts the appropriate containers when you run the server.

---

## Quick Reference

| Service    | Purpose                                  | Trigger                            | Port | Container name                    |
| ---------- | ---------------------------------------- | ---------------------------------- | ---- | --------------------------------- |
| PostgreSQL | Relational database                      | `DB_ENGINE=postgresql` in `.env`   | 5432 | `resource-planner-dev-pg`         |
| Mailpit    | Local SMTP / email capture               | `EMAIL_TYPE=smtp` in DB config     | 1025 | `resource-planner-dev-mailpit`    |
| LocalStack | Local AWS (Secrets Manager, S3, etc)     | `DEPLOYMENT_TYPE=aws` in DB config | 4566 | `resource-planner-dev-localstack` |
| Keycloak   | Local OAuth 2.0 / SAML identity provider | `DEV_KEYCLOAK=true` in `.env`      | 8080 | `resource-planner-dev-keycloak`   |

Services are started at the beginning of `Run Server` and stopped cleanly when the server exits.
If a container is already running when the dev script starts, it is left untouched and will **not** be stopped on exit.

---

## PostgreSQL

### What it is

A containerised PostgreSQL database for local development.
By default the application uses SQLite, which requires no configuration.
Switch to PostgreSQL when you need to validate behaviour that only manifests against a real Postgres engine — migrations with constraints, JSON queries, full-text search, etc.

### How to enable

Set `DB_ENGINE` in `apps/web/.env`:

```env
DB_ENGINE=django.db.backends.postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=resourceplanner
DB_USER=postgres
DB_PASSWORD=yourpassword
```

The `DB_ENGINE` value must contain the string `postgresql` for the dev script to detect it.

### What the dev script does

1. Reads `DB_ENGINE`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` from `apps/web/.env`.
2. Checks whether the container is already running.
3. If not, starts the `postgres` Docker Compose profile, which maps `$DB_PORT` → `5432` inside the container.
4. Stops and removes the container when the dev server exits (unless it was already running before).

### Configuration reference

| `.env` key    | Default           | Description                                |
| ------------- | ----------------- | ------------------------------------------ |
| `DB_ENGINE`   | _(SQLite)_        | Must contain `postgresql` to enable Docker |
| `DB_HOST`     | `127.0.0.1`       | Hostname the Django app connects to        |
| `DB_PORT`     | `5432`            | Host port mapped to the container          |
| `DB_NAME`     | `resourceplanner` | Database name created inside PostgreSQL    |
| `DB_USER`     | `postgres`        | PostgreSQL user                            |
| `DB_PASSWORD` | _(empty)_         | PostgreSQL password                        |

### Connecting manually

Use the **SQL Query Runner** inside the dev control panel:

```
python scripts/dev/dev.py → Django Tools → SQL Query Runner → PostgreSQL
```

Or connect with any PostgreSQL client using the values from `.env`.

### Notes

- Data persists between server restarts because Docker Compose does not use an anonymous volume with `--rm` — the container is simply stopped, not deleted.
- Run migrations after switching from SQLite: **Django Tools → Migrate**.
- The Reset Setup script removes all `DB_*` keys from `.env` when triggered with `--full-clean`.

---

## Mailpit (Email)

### What it is

[Mailpit](https://mailpit.axllent.org/) is a lightweight SMTP server that captures all outgoing email and exposes them through a web UI.
No emails are delivered to real recipients — everything is intercepted locally.
It is the recommended tool for testing password resets, notifications, and any other email flow during development.

### How to enable

Email behaviour is controlled by the **Email Type** configuration in the application's setup wizard (stored in the database, not in `.env`).

Set **Email Type** to `smtp` via the setup wizard or directly in the database:

| Config code  | Required value |
| ------------ | -------------- |
| `EMAIL_TYPE` | `smtp`         |

The dev script reads this value from the database at startup.
No changes to `.env` are needed.

### SMTP authentication (optional)

If the **SMTP Authentication Enabled** config is set to `true` in the database, the dev script reads `EMAIL_SMTP_USERNAME` and `EMAIL_SMTP_PASSWORD` (decrypting the password with Fernet if stored encrypted) and passes them to Mailpit via two transient `.env` keys:

| `.env` key (set automatically) | Value               |
| ------------------------------ | ------------------- |
| `MP_SMTP_AUTH`                 | `username:password` |
| `MP_SMTP_AUTH_ALLOW_INSECURE`  | `true`              |

These keys are written at server start and removed at server exit.

### SMTP port

The container maps `$EMAIL_SMTP_PORT` (from the database config) to Mailpit's internal port `1025`.
Configure the port in the setup wizard under **SMTP Port** (config code `EMAIL_SMTP_PORT`); the default is `587`.

### What the dev script does

1. Reads `EMAIL_TYPE`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_AUTH_ENABLED`, `EMAIL_SMTP_USERNAME`, and `EMAIL_SMTP_PASSWORD` from the database.
2. If `EMAIL_TYPE=smtp`, starts the `smtp` Docker Compose profile.
3. Optionally writes `MP_SMTP_AUTH` and `MP_SMTP_AUTH_ALLOW_INSECURE` to `.env` when auth is configured.
4. Stops the container and removes the transient `.env` keys on server exit.

### Access

| Interface      | URL                           |
| -------------- | ----------------------------- |
| Web UI (inbox) | http://localhost:8025         |
| SMTP endpoint  | `localhost:<EMAIL_SMTP_PORT>` |

Open the web UI to browse captured emails, inspect headers, and view HTML/text bodies.

### Django email settings

The application sends mail through the SMTP host and port configured in the database (`EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`).
For local Mailpit, set **SMTP Host** to `127.0.0.1` and **SMTP Port** to the same port Mailpit listens on (default `1025`).

### Notes

- Mailpit does not forward emails externally. All email is captured regardless of the recipient address.
- The web UI auto-refreshes. There is no need to reload the page when new emails arrive.
- If no email appears after an action, check the Django console for SMTP connection errors — the most common cause is a port mismatch between `EMAIL_SMTP_PORT` in the database and the port Mailpit is bound to.

---

## LocalStack (AWS)

### What it is

[LocalStack](https://localstack.github.io/) emulates AWS services locally.
The application uses it when the deployment type is set to `aws`, which enables:

- **AWS Secrets Manager** — for storing OAuth client secrets, SAML certificates, and other sensitive values instead of encrypting them in the database.
- **S3** — for file storage.
- **CloudWatch Logs** — for log streaming.

In `local` deployment mode these services are replaced by Fernet-encrypted database storage, so LocalStack is not needed.

### How to enable

Set **Deployment Type** to `aws` in the setup wizard or directly in the database:

| Config code       | Required value |
| ----------------- | -------------- |
| `DEPLOYMENT_TYPE` | `aws`          |

The dev script reads this value from the database at startup.

### What the dev script does

1. Reads `DEPLOYMENT_TYPE` from the database.
2. If `aws`, starts the `aws` Docker Compose profile which exposes LocalStack on port `4566`.
3. Writes `AWS_ENDPOINT=http://localhost:4566` to `apps/web/.env` so Django routes AWS SDK calls to LocalStack instead of real AWS.
4. On server exit, stops the container and removes `AWS_ENDPOINT` from `.env`.

### Configuration reference

| Setting             | Value                                |
| ------------------- | ------------------------------------ |
| LocalStack endpoint | `http://localhost:4566`              |
| Services available  | `secretsmanager`, `s3`, `logs`       |
| `.env` key written  | `AWS_ENDPOINT=http://localhost:4566` |

### AWS credentials

LocalStack does not validate real AWS credentials.
The application's AWS SDK calls require credential keys to be present but their values are arbitrary.
Add dummy values to `apps/web/.env` if the SDK complains:

```env
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
```

### Accessing LocalStack

You can inspect LocalStack resources using the AWS CLI pointed at the local endpoint:

```bash
aws --endpoint-url http://localhost:4566 secretsmanager list-secrets
aws --endpoint-url http://localhost:4566 s3 ls
```

Or install the LocalStack CLI for a richer experience:

```bash
pip install localstack
localstack status services
```

### Notes

- LocalStack data is **not persisted** between container restarts. Secrets created in one session are lost when the container is stopped.
- If secrets are missing after a restart, re-run setup or recreate them through the application.
- Switch back to `local` deployment type to use Fernet-encrypted database storage without needing LocalStack.

---

## Keycloak (OAuth 2.0 / SAML)

### What it is

[Keycloak](https://www.keycloak.org/) is an open-source identity and access management server.
In this project it serves as a **local Identity Provider (IdP)** for testing OAuth 2.0 and SAML 2.0 single sign-on flows without needing an external service like Google, Okta, or Azure AD.

When the container starts it automatically imports a pre-configured realm (`resource-planner`) that includes:

| Resource    | Details                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------ |
| OIDC client | `resource-planner-oauth`, secret `dev-oauth-secret`                                        |
| SAML client | SP entity ID `http://localhost:8000/sp`, ACS `http://localhost:8000/api/v1/auth/saml/acs/` |
| Test user   | `sso@example.com` / `Test1234!`                                                            |

### How to enable

Add `DEV_KEYCLOAK=true` to `apps/web/.env`:

```env
DEV_KEYCLOAK=true
```

This is the only change needed. The container, realm, and test user are all created automatically.

### What the dev script does

1. Reads `DEV_KEYCLOAK` from `apps/web/.env`.
2. If `true`, starts the `keycloak` Docker Compose profile.
3. Keycloak starts in **dev mode** (`start-dev`) with the realm JSON mounted and imported on first boot.
4. Prints a reminder to use **Keycloak Dev Config** from the menu once Keycloak is ready.
5. Stops the container when the dev server exits.

Keycloak takes approximately 30–60 seconds to become available after the container starts.

### Realm details

The pre-configured realm is defined in [`scripts/dev/keycloak/realm-export.json`](../../scripts/dev/keycloak/realm-export.json).

#### OIDC client (`resource-planner-oauth`)

| Field                 | Value                                                                            |
| --------------------- | -------------------------------------------------------------------------------- |
| Client ID             | `resource-planner-oauth`                                                         |
| Client secret         | `dev-oauth-secret`                                                               |
| Auth endpoint         | `http://localhost:8080/realms/resource-planner/protocol/openid-connect/auth`     |
| Token endpoint        | `http://localhost:8080/realms/resource-planner/protocol/openid-connect/token`    |
| Userinfo endpoint     | `http://localhost:8080/realms/resource-planner/protocol/openid-connect/userinfo` |
| Scope                 | `openid email profile`                                                           |
| Allowed redirect URIs | `http://localhost:8000/*`, `http://localhost:3000/*`                             |

#### SAML client (`http://localhost:8000/sp`)

| Field             | Value                                                         |
| ----------------- | ------------------------------------------------------------- |
| SP entity ID      | `http://localhost:8000/sp`                                    |
| ACS URL (POST)    | `http://localhost:8000/api/v1/auth/saml/acs/`                 |
| IdP entity ID     | `http://localhost:8080/realms/resource-planner`               |
| IdP SSO URL       | `http://localhost:8080/realms/resource-planner/protocol/saml` |
| NameID format     | `emailAddress`                                                |
| Signature         | Assertion signed with Keycloak's realm key                    |
| Attribute mappers | `email`, `first_name`, `last_name`                            |

The IdP signing certificate is generated by Keycloak at first boot and is unique per container instance.
Use **Keycloak Dev Config** (see below) to retrieve the live certificate.

### Getting OAuth and SAML configuration values

After Keycloak has started (allow ~60 seconds), use the dev control panel to fetch all ready-to-paste values:

```
python scripts/dev/dev.py → Django Tools → Keycloak Dev Config
```

This reads Keycloak's live OIDC discovery document and SAML metadata, then prints:

- All OAuth 2.0 field values for the provider registration form
- All SAML field values including the full IdP certificate in PEM format

Copy these values directly into the application's OAuth or SAML setup screens.

### Access

| Interface         | URL                                                                            |
| ----------------- | ------------------------------------------------------------------------------ |
| Admin console     | http://localhost:8080/admin                                                    |
| Admin credentials | `admin` / `admin`                                                              |
| Realm             | `resource-planner`                                                             |
| OIDC discovery    | http://localhost:8080/realms/resource-planner/.well-known/openid-configuration |
| SAML metadata     | http://localhost:8080/realms/resource-planner/protocol/saml/descriptor         |

### End-to-end OAuth 2.0 login flow

1. Register the OIDC provider in the application using values from **Keycloak Dev Config**.
2. Set **Auth Mode** to `oauth` in the application settings.
3. Initiate login. The application redirects to Keycloak.
4. Log in with `sso@example.com` / `Test1234!`.
5. Keycloak redirects back to the application callback.
6. The application creates or links the local user and establishes a session.

### End-to-end SAML 2.0 login flow

1. Run **Keycloak Dev Config** and copy the IdP certificate.
2. Register the SAML provider in the application with the IdP entity ID, SSO URL, certificate, and the SP values shown above.
3. Set **Auth Mode** to `saml` in the application settings.
4. Initiate login. The application redirects to Keycloak with a SAML AuthnRequest.
5. Log in with `sso@example.com` / `Test1234!`.
6. Keycloak posts a signed SAMLResponse to the ACS URL.
7. The application validates the signature, extracts the identity, and establishes a session.

### Notes

- Keycloak runs in **dev mode** (`start-dev`) which uses an in-memory H2 database. All user and session data is lost when the container stops. Only the imported realm configuration persists via the JSON file.
- The IdP signing certificate changes each time the container is recreated. Always re-run **Keycloak Dev Config** after a fresh container start to get the updated certificate and re-register the SAML provider.
- The OAuth client secret (`dev-oauth-secret`) and OIDC client ID are fixed in the realm export and do not change between restarts.
- Port `8080` is reserved for Keycloak. Ensure nothing else is bound to that port before enabling `DEV_KEYCLOAK=true`.
- To add more test users, log in to the admin console at http://localhost:8080/admin and create them in the `resource-planner` realm. Changes are lost on container restart unless added to the realm export file.

---

## Manual Docker Compose commands

The dev script manages containers automatically, but you can also control them directly:

```bash
# Start a single service
docker compose --env-file apps/web/.env --profile postgres up -d
docker compose --env-file apps/web/.env --profile smtp up -d
docker compose --env-file apps/web/.env --profile aws up -d
docker compose --env-file apps/web/.env --profile keycloak up -d

# Stop a single service
docker compose --env-file apps/web/.env --profile postgres down
docker compose --env-file apps/web/.env --profile smtp down
docker compose --env-file apps/web/.env --profile aws down
docker compose --env-file apps/web/.env --profile keycloak down

# View logs
docker logs resource-planner-dev-keycloak -f
docker logs resource-planner-dev-pg -f
docker logs resource-planner-dev-mailpit -f
docker logs resource-planner-dev-localstack -f
```

---

## Troubleshooting

### Container fails to start

Run the compose command manually (see above) and inspect the output.
Common causes: port already in use, Docker daemon not running, insufficient memory.

### Keycloak not reachable after starting

Keycloak can take 30–60 seconds to initialise.
Wait and re-run **Keycloak Dev Config** from the menu.
If it still fails, check the logs: `docker logs resource-planner-dev-keycloak`.

### SAML signature verification fails after container restart

The Keycloak realm signing key changes when the container is recreated.
Re-run **Keycloak Dev Config**, copy the new certificate, and update the SAML provider registration in the application.

### Emails not appearing in Mailpit

Ensure **SMTP Host** in the application config is set to `127.0.0.1` and **SMTP Port** matches `EMAIL_SMTP_PORT`.
Check `docker logs resource-planner-dev-mailpit` for connection errors.

### LocalStack secrets not found after restart

LocalStack does not persist state between container restarts.
Re-run application setup or manually recreate secrets via the AWS CLI pointed at `http://localhost:4566`.

### PostgreSQL connection refused

Verify the container is running: `docker ps | grep resource-planner-dev-pg`.
Confirm `DB_HOST=127.0.0.1` and `DB_PORT` in `.env` match the port the container is bound to.

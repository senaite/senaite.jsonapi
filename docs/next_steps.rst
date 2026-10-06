Next Steps: AI-Driven SENAITE Automation
========================================

Strategy: extend `senaite.jsonapi` in place, borrowing endpoint shapes
and patterns from `plone.restapi` (`/@workflow`, `/@types`,
`/@vocabularies`, `/@registry`, JWT auth). No new package — all
changes land in
`src/senaite/jsonapi/v1/routes/` plus a few new adapters.

Each phase ends with a verifiable artifact (curl call, doctest, or
working Claude tool).


Phase 1 — JWT auth + CORS (foundation)
--------------------------------------

Goal: a Claude session can authenticate once and call the API without
cookies.

Status: **partial.** JWT authentication shipped in PR #88; CORS and
token refresh are still outstanding.

Done
~~~~

- JWT issuance via the existing `/login` route (Bearer header, HttpOnly
  cookie, `X-JWT-Auth-Token` fallback).
- `JWTAuthenticationPlugin` PAS plugin with per-user signing secrets
  and `rotate_secret(userid)` for server-side revocation.
- GenericSetup install/uninstall profile, `INonInstallable` adapter,
  doctests for the full bearer flow.
- **Verified:** `curl /login` returns a token; subsequent calls with
  `Authorization: Bearer` succeed.

Pending
~~~~~~~

- `POST /@login-renew` (token refresh). Without it, long-running
  clients must re-authenticate with credentials every hour. Small:
  new route that issues a fresh token for the already-authenticated
  user, optionally guarded by a `JWT_RENEW_WINDOW` so a brand-new
  token cannot immediately be refreshed.
- **CORS headers** on the `senaite/v1` traverser. Blocks browser-based
  clients on a different origin (dashboards, the future configlet
  test panel, third-party web UIs). Should reuse the same allow-list
  pattern as `plone.restapi`.


Phase 2 — Type & workflow introspection
---------------------------------------

Goal: Claude can discover what is creatable and what transitions are
legal without prior schema knowledge.

- `GET /@types` → list of portal types (filtered to SENAITE-relevant:
  AnalysisRequest, Analysis, Client, Contact, SampleType,
  AnalysisService, AnalysisProfile, ARTemplate, Calculation, Method,
  Instrument, Worksheet, Batch).
- `GET /@types/{portal_type}` → field schema (name, type, required,
  vocabulary ref, default).
- `GET /@workflow/{uid}` → current state + available transitions +
  full history (replaces `?workflow=yes`).
- `POST /@workflow/{uid}/{transition_id}` with
  `{comment, include_children}` — borrow `include_children`
  semantics directly from plone.restapi to cascade
  Sample → Analyses.
- **Verify:** doctest creates a sample, lists transitions, calls
  `/@workflow/{uid}/receive`, asserts state.


Phase 3 — Vocabularies & registry
---------------------------------

Goal: Claude can resolve dropdowns (sample types, containers, methods,
departments) and read setup settings.

- `GET /@vocabularies` and `GET /@vocabularies/{name}` (wrap
  zope.schema vocabularies + SENAITE-specific catalogs like
  `bika_setup_catalog`).
- `GET /@registry/{key}` + `PATCH /@registry` for `senaite.*`
  registry settings.
- **Verify:** `/@vocabularies/senaite.core.vocabularies.sampletypes`
  lists all sample types with UID + title.


Phase 4 — Batch operations
--------------------------

Goal: one HTTP call creates N samples with M analyses each.

- `POST /@batch` accepting
  `{operations: [{method, path, body}, ...]}` — plone.restapi-style.
  All-or-nothing transaction via Zope transaction manager.
- Convenience: `POST /AnalysisRequest/create` already exists; add
  support for nested `analyses: [...]` and `contained_analyses` so
  one POST = one Sample + its Analyses.
- **Verify:** create 5 samples × 3 analyses in a single request;
  rollback on failure.


Phase 5 — Analysis results submission
-------------------------------------

Goal: Claude can submit/verify/publish analytical results end-to-end.

- `POST /@results/{analysis_uid}` with
  `{Result, ResultCaptureDate, Remarks, InterimFields, Uncertainty}`
  — wraps SENAITE result-setting (which differs from plain field update
  because of interim calcs and dependent services).
- `POST /@results/{ar_uid}/bulk` for whole-sample submission.
- Chain: submit → transition `submit` → `verify` → `publish` via
  `/@workflow` `include_children=true`.
- **Verify:** doctest covers receive → submit results → verify →
  publish; resulting PDF report registered.


Phase 6 — Setup configuration endpoints
---------------------------------------

Goal: Claude can configure a SENAITE instance (the "setup" Odoo-style).

- Generic CRUD already exists; add discovery: `GET /@setup` → maps
  each setup folder (`/bika_setup/bika_analysisservices`,
  `/bika_setup/laboratory`, etc.) to a portal_type + create URL.
- Targeted helpers as push consumers (clean Python, no new route
  plumbing per object):

  - `analysisservice.create_with_calculation`
  - `analysisprofile.attach_services`
  - `artemplate.from_profile`
  - `client.create_with_contacts`

- **Verify:** script provisions Lab, 1 Client, 1 SampleType,
  3 Services, 1 Profile, 1 Template via API.


Phase 7 — Search hardening
--------------------------

Goal: rich querying for AI reasoning.

- Extend existing `/search` with plone.restapi `@search` features:
  `metadata_fields=_all`, `fullobjects`, `path.depth`,
  `sort_on` indices.
- `GET /@querystring-search` for Collection-style queries against
  `senaite_catalog_analysisrequest`.
- **Verify:** query "all AR in `to_be_verified` for client X in last
  7d" returns expected set.


Phase 8 — Claude tooling layer
------------------------------

Goal: a Claude Code MCP server (thin) that wraps the above into typed
tools.

- Tools: `senaite_login`, `senaite_list_types`,
  `senaite_get_schema`, `senaite_search`, `senaite_create_sample`,
  `senaite_submit_results`, `senaite_transition`,
  `senaite_configure_service`.
- Each tool = one HTTP call to senaite.jsonapi. Token cached in
  session.
- **Verify:** in a Claude session: "Create a water sample for client
  Acme with pH and conductivity, receive it, submit results 7.2 and
  450, verify, publish" — completes end-to-end.


Cross-cutting concerns
----------------------

- Tests: each phase ships doctests in `senaite.jsonapi/docs/`
  (matches existing pattern).
- Backwards compat: all new endpoints prefixed with `@`
  (plone.restapi convention); existing `/create`, `/update`,
  `/delete`, `/push` untouched.
- Permissions: every service checks SENAITE permissions explicitly; no
  implicit elevation.
- Errors: standard JSON `{type, message, traceback?}` shape borrowed
  from `plone.restapi.exceptions`.


Suggested order of value
------------------------

Phases 1, 2, 4, 5 deliver the lion's share (auth + discoverability +
bulk + results) — at that point Claude can already run a full sample
lifecycle. Phases 3, 6, 7, 8 are amplifiers.

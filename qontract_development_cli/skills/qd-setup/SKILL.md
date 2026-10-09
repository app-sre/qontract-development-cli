---
name: qd-setup
description: Help users initialize, understand, or update Qontract Development CLI (qd) configuration, environments, defaults, and integration profiles. Use when someone asks to set up qd, add an environment or profile, configure local reconcile/API development, or troubleshoot setup and settings precedence. Do not run integrations automatically.
---

# Set up qd

`qd` (Qontract Development CLI) runs qontract-reconcile integrations and their
supporting services in local Docker Compose environments. Use this skill to help
a user turn their existing checkouts and integration requirements into a working
setup—not to reconcile infrastructure or run production checks.

## Explain the settings

| Settings                      | Purpose                                                                                                              |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Global `config.yaml`          | Editor, environment/profile directories, defaults-profile name, worktree directory, and Compose project name.        |
| Environment `<name>.yml`      | App-Interface path, reconcile TOML configuration, platform, and which services run.                                  |
| Defaults/profile `<name>.yml` | Shared checkout paths and per-integration command, arguments, images/build settings, debugger, and dry-run behavior. |

The environment's `config` points to a separate `config.<environment>.toml` in
the **qontract-reconcile working copy**. It configures reconcile connections and
can contain Vault and qontract-api credentials; qd's YAML files do not replace it.

Profiles inherit the configured defaults profile, normally `defaults.yml`.
Profile settings override defaults; a profile's App-Interface path overrides the
environment path. Global `QONTRACT_DEVELOPMENT_` variables override global YAML;
qd does not load a project `.env` for those settings. API services can separately
mount their own `.env` file.

## Discover before changing anything

1. Check `qd --version` and the installed CLI's `config`, `env`, and `profile`
   help. If qd is missing, offer `uv tool install qontract-development-cli`;
   obtain approval before installing.
2. Read applicable repository instructions. Inspect existing global settings,
   defaults, environments, and relevant profiles privately. Use `qd env ls` and
   `qd profile ls` to locate directories; resolve global config through qd's
   installed `config.py`/AppDirs rather than assuming a platform-specific path.
   Never read credential-bearing reconcile `config*.toml` or API `.env` files.
   Check their path and existence only. Do not display, grep, parse, diff, upload,
   or stage them; ask the user to confirm non-secret setup details privately.
3. Use the user's stored workspace layout and fork checkouts before asking for
   repository paths; upstream project names are not local directory names.
   Inspect available checkouts and relevant CLI registration. Establish which
   environment, integration, real CLI name, arguments, and local supporting
   services the user needs. Ask only for missing decisions; do not guess paths,
   profile names, required arguments, credentials, or a production environment.
4. Show the smallest proposed changes, exact target files, inherited settings,
   and unresolved prerequisites. Obtain approval before creating or modifying
   saved configuration. Never silently change an existing profile's checkout,
   production endpoint, dry-run setting, or Compose project name.

## Apply the approved setup

- **Prepare reconcile TOML privately.** In the qontract-reconcile working copy,
  guide the user to create `config.<environment>.toml` from the repository's
  example template or their approved configuration. For example, the user can
  run `cp config.toml.example config.dev-local.toml` in their own terminal.
  The user must edit connections, Vault access, and qontract-api authentication
  privately; never request credential values or file contents. Confirm only that
  the file exists and that the user has configured the intended endpoints.
  Set the qd environment YAML's `config` field to that exact file path. Do not
  commit credential files or automatically copy an existing credential-bearing
  configuration.
- For a genuinely new setup, guide the user through `qd config init` in their
  terminal. It writes global config, `dev.yml`, and the defaults profile; do not
  rerun it blindly on an existing setup. Do not simulate terminal input.
- **Edit qd environment and profile YAML directly** after approval, for both new
  files and updates. Resolve the real directories from qd's global settings;
  preserve unrelated fields, defaults, comments, and user changes. Apply only the
  agreed values and show a minimal, credential-free summary of the changes.
  The global qd YAML may also be edited when approved. This permission does not
  extend to reconcile TOML or API `.env` contents. The `qd ... edit` commands are
  optional human editor workflows, not a requirement for agent-driven setup.
- Create an integration profile with the supported CLI, supplying both values
  to avoid its integration-name/argument prompts:

  ```shell
  qd profile create PROFILE --integration-name REAL-CLI-NAME --integration-extra-args 'VERIFIED-ARGS'
  ```

  Use `--integration-extra-args ''` only when no extra arguments are needed.
  Inspect `qd profile create --help` for supported checkout/PR overrides. An
  existing name is not permission to replace it.

- Default to `dry_run: true`. Keep integration-specific settings in profiles
  and shared checkout paths in defaults where appropriate. Do not copy complete
  inherited settings into every profile or silently switch to published images.
- For local API development, verify actual source mounts and `app.sh`; check
  API `.env` existence without reading it. Have the user privately confirm TOML
  API endpoints and credentials. Enabled API/worker/subscriber services require cache;
  OPA depends on the intended authorization setup, not a universal preset.

## AppSRE developer credentials (user-only)

For AppSRE environments, read the developer instructions in the user's actual
app-interface checkout at
`docs/app-sre/sops/general/app-interface-development-environment-setup.md`.
Prefer development data and credentials; do not copy the guide's example clone
layout or old Python versions over the user's verified workspace/current manifests.
These references document the credential handoff, not permission for the agent
to authenticate, fetch secrets, generate tokens, or read the resulting files:

https://gitlab.cee.redhat.com/service/app-interface/-/blob/master/docs/app-sre/sops/general/app-interface-development-environment-setup.md
https://gitlab.cee.redhat.com/service/app-interface/-/blob/master/docs/app-sre/app-interface/qontract-api/qontract-api-bootstrap.md

1. **Vault access:** have the user sign in privately, using OIDC:

   ```shell
   vault login -method=oidc -address=https://vault.devshift.net
   ```

2. **Development TOML:** the guide directs the user to copy the contents of this
   Vault secret into `config.dev.toml` in their reconcile checkout:

   https://vault.devshift.net/ui/vault/secrets/app-sre/show/creds/app-interface-dev-config-toml

   If they lack access, follow the guide's credentials-request process; do not
   switch to privileged debugging credentials to bypass the blocker.

3. **Stage/production debugging only:** when explicitly needed and authorized,
   the guide documents this command for the user to run privately in their
   reconcile checkout:

   ```shell
   vault kv get -field=data -address=https://vault.devshift.net \
     app-sre/creds/app-interface-debug-config-toml > config.debug.toml
   ```

   These are privileged developer credentials. Confirm the destination is new
   or that the user explicitly approves replacing it; never execute this command
   through agent tools or read its output/file.

4. **Local qontract-api JWT:** have the user privately configure the token
   generator with the same `QAPI_JWT_SECRET_KEY` as their local API's settings.
   Do not retrieve a production signing key for a local development API.
   Verify the installed checkout's non-secret Makefile/token-generator source;
   the current target requires both parameters:

   ```shell
   make -C <qontract-reconcile>/qontract_api generate-token \
     SUBJECT=<approved-local-subject> EXPIRES_DAYS=<chosen-duration>
   ```

   This command prints the credential: the user runs it in their private
   terminal and places the token into their TOML themselves. Never capture or
   request the token. The generator appends today's date to the subject; confirm
   the resulting subject is allowed by the intended local OPA policy if enabled.
   Older README examples using unprefixed `JWT_SECRET_KEY` or `DAYS` are stale;
   use the current implementation, not those examples.

After this handoff, edit only the approved qd YAML paths/service settings and
verify file existence. Do not inspect private TOML or API `.env` contents.

## Verify and hand over

Use `qd env show ENV` and `qd profile show PROFILE` to check loading, but remember
that displayed YAML is the saved file, not an effective merged-settings report.
Recheck defaults, paths, service dependencies, and the installed models for
current fields. Check Docker/Compose prerequisites if the intended workflow needs
them. Report what changed and every remaining blocker without claiming a run
passed.

Do not use `qd profile run` as a harmless configuration check: it builds images
or bundles, can fetch PR worktrees, and interactive mode can stop an existing
development stack. Offer a separately approved dry-run through
`qd-integration-dry-run` when setup is ready; no production calls, wet-runs,
credential rotation, or infrastructure changes are part of this skill.

## Examples and evaluation scenarios

- **First setup:** explain the three settings layers, verify real checkouts, ask
  for missing paths, then obtain approval before initialization.
- **Add a profile:** resolve the real integration name and required arguments;
  create only the approved profile and preserve existing defaults/environments.
- **Existing production setup:** propose a minimal diff; never reset it with
  `config init` or run an integration just to validate YAML.
- **Local API setup:** identify missing cache, mounts, or endpoint configuration;
  report blockers rather than substituting an image or inventing credentials.
- **Private TOML setup:** guide the user to prepare the environment-specific
  file using the appropriate documented development/debugging workflow, link its
  path from qd YAML, and verify existence without reading secrets or running Vault.
- **Malformed settings:** identify the affected file, preserve unrelated user
  work, and propose a targeted repair without silently overwriting configuration.

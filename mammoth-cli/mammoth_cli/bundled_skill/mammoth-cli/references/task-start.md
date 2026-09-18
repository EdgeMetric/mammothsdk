# Portable task-start playbook

Use this playbook when a shell-capable agent receives a new Mammoth business
task and has no repository or prior chat context. The user supplies the intent,
authorized scope, and (when needed) a protected profile. Never put credentials
or secrets in an argument, prompt, transcript, or checkpoint.

1. Check whether `mammoth` is available. If it is absent, install the CLI
   from PyPI into a fresh environment and verify it:

   ```bash
   python3 -m venv .mammoth && .mammoth/bin/python -m pip install --upgrade mammoth-cli
   .mammoth/bin/mammoth --version      # or: uv tool install mammoth-cli
   ```

   Pin `mammoth-cli==X.Y.Z` when the task names an approved release. Use the
   host installer script (`installers/mammoth-install.sh` in the repository)
   only when the operator names it; do not pipe a remote script to a shell on
   your own initiative. The SDK (`mammoth-io`) comes with the CLI.
2. Locate the installed guidance with `mammoth skill path --output json
   --no-input` and read `SKILL.md`; open a reference only when the routing
   table sends you there. `references/commands/*.md` are per-command lookups,
   not upfront reading. If a skill install is required for the agent host,
   run `mammoth skill install --output json --no-input` and verify ownership
   with `mammoth skill list --output json --no-input`.
3. Establish authentication before any remote read or write. Determine the
   intended environment from the task first: production defaults to the `app` endpoint;
   use `release` only when the task explicitly names release. Then inspect the
   selected profile without attempting business work:

   ```bash
   mammoth auth status --output json --no-input
   ```

   Compare the status response's `endpoint` with the intended environment. If
   the profile or credentials are missing, or the endpoint is for another
   environment, stop and follow the credential rule in
   [authentication](auth.md) (the operator logs in from their own terminal;
   you never handle the key or secret). Then run the connectivity and
   configuration check and require success:

   ```bash
   mammoth doctor --profile PROFILE --output json --no-input
   ```

   Do not print, echo, or copy secret-bearing inputs. A failed status, login,
   or doctor check stops the task before discovery and business commands.
4. Discover instead of guessing. Run `mammoth schema list/find/get --output
   json --no-input` for local CLI routes; `mammoth capability list --output
   json --no-input` is an API-binding inventory and can omit typed/local
   routes. Check [capabilities](capabilities.md) for whether a route is
   proven, not supported, or untried on release before building a plan on
   it. Then resolve workspace/project/dataset/view
   parents with reads. Use display names returned by the exact view schema.
5. Translate the business intent into a plan the agent chooses. Submit only
   supported operations with explicit `--project` (and other returned parents),
   structured `--input`, `--output json`, and `--no-input`. Do not use private
   HTTP/SDK escape hatches or local data processing as a substitute.
   For pipeline transformations, prefer the typed `mammoth view transform
   <operation>` commands. Useful typed alternatives include
   `view.transform.filter`, `view.transform.math`, and
   `view.transform.substring`; inspect one with
   `mammoth schema get view.transform.filter --output json --no-input` before
   composing its input. The generic `view task add`, `view task preview`, and
   `view task update` routes expose an opaque `task_spec` object in the current
   schema. Prefer typed `view transform <operation>` routes. Use a low-level
   task route only when an independently documented task specification is
   supplied for the target backend; never infer fields or a union from
   `schema get` or an illustrative example. Otherwise report it as
   unsupported/ambiguous and stop. See
   [operations](operations.md) for task/pipeline, workflow, and export
   read-back guidance.
6. Verify each mutation from remote reads and exported content. A job status
   or pipeline/task definition only proves the task ran, not that it changed
   what you meant; for any value-changing step the proof is `view data get`
   row read-back. On timeout or unknown outcome, reconcile the observed
   job/resource before retrying; never blindly replay a mutation.
7. Record only nonsecret IDs, parents, job handles, evidence hashes, and the
   remaining objective in the portable handoff. Clean up only resources created
   by this task, with required confirmations, and verify they are gone.

If the requested operation is unavailable, ambiguous, unauthorized, or cannot
be verified, stop safely with the structured error and the next supported read
or recovery action. This playbook is onboarding guidance, not proof that a
particular business task or provider is available.

# Portable task-start playbook

Use this playbook when a shell-capable agent receives a new Mammoth business
task and has no repository or prior chat context. The user supplies the intent,
authorized scope, and (when needed) a protected profile. Never put credentials
or secrets in an argument, prompt, transcript, or checkpoint.

For an evaluated or isolated agent, follow the controller-provided credential
broker/sidecar instead of using a saved profile. Never mount or read the saved
profile in that shell. If the broker/sidecar is not provided, stop before any
authenticated action. The profile workflow below remains for ordinary,
non-evaluated operator use.

1. Check whether `mammoth` is available. If it is absent, install the CLI and
   bundled skill with the supported host installer:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash
   ```

   For an evaluation or deployment that names an exact approved release, append
   `--version X.Y.Z`. Verify the installed result with `mammoth --version`.
   Do not substitute a manual pip/uv install for this
   CLI path; Python applications install the SDK separately.
2. Locate the installed guidance with `mammoth skill path --output json
   --no-input` and read the canonical skill plus its references. If a skill
   install is required for the agent host, run `mammoth skill install
   --output json --no-input` and verify ownership with `mammoth skill list
   --output json --no-input`.
3. Establish authentication before any remote read or write. In an evaluated
   or isolated run, do not inspect a saved profile and do not run `auth login`:
   use the controller-provided credential broker/sidecar check. If it is not
   provided, stop before authenticated actions. The remaining instructions in
   this step are for ordinary operator runs only. Determine the intended
   environment from the task first: production defaults to the `app` endpoint;
   use `release` only when the task explicitly names release. Then inspect the
   selected profile without attempting business work:

   ```bash
   mammoth auth status --output json --no-input
   ```

   Compare the status response's `endpoint` with the intended environment. If
   the profile or credentials are missing, or the endpoint is for another
   environment, stop and follow [authentication](auth.md) to select or log in
   to the explicitly intended profile. Never silently reuse or rewrite a
   mismatched profile, invent a profile, put credentials in chat, or put
   secrets in argv. After login (or when an existing, matching profile is
   present), run the connectivity and configuration check and require success:

   ```bash
   mammoth doctor --profile PROFILE --output json --no-input
   ```

   Do not print, echo, or copy secret-bearing inputs. A failed status, login,
   or doctor check stops the task before discovery and business commands. A
   broker check is the equivalent precondition in evaluated mode; do not add a
   profile or `--profile` flag to broker-invoked commands.
4. Discover instead of guessing. Run `mammoth schema list/find/get --output
   json --no-input` for local CLI routes; `mammoth capability list --output
   json --no-input` is an API-binding inventory and can omit typed/local
   routes. Then resolve workspace/project/dataset/view
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
6. Verify each mutation from remote reads, schemas, jobs, pipeline/task
   definitions, and exported content. On timeout or unknown outcome, reconcile
   the observed job/resource before retrying; never blindly replay a mutation.
7. Record only nonsecret IDs, parents, job handles, evidence hashes, and the
   remaining objective in the portable handoff. Clean up only resources created
   by this task, with required confirmations, and verify they are gone.

If the requested operation is unavailable, ambiguous, unauthorized, or cannot
be verified, stop safely with the structured error and the next supported read
or recovery action. This playbook is onboarding guidance, not proof that a
particular business task or provider is available.

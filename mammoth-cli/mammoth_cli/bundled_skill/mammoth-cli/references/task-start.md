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

1. Check whether `mammoth` is available. If it is absent, create and activate a
   dedicated virtual environment, then install either the exact wheel file
   authorized by the task/release record or an actually published pinned
   release:

   ```bash
   python -m venv .mammoth-cli-env
   . .mammoth-cli-env/bin/activate
   python -m pip install "/path/to/authorized/mammoth_cli-PINNED_VERSION-py3-none-any.whl"
   # Or, only when that exact release is published and authorized:
   python -m pip install "mammoth-cli==PINNED_VERSION"
   ```

   Replace `PINNED_VERSION` and the wheel path only with authorized values; do
   not install an unpinned latest version. If a SHA-256 is supplied with the
   authorized wheel, verify it before installation (for example with
   `sha256sum`) and stop on mismatch. Then run `mammoth --version`.
2. Locate the installed guidance with `mammoth skill path --output json
   --no-input` and read the canonical skill plus its references. If a skill
   install is required for the agent host, run `mammoth skill install
   --output json --no-input` and verify ownership with `mammoth skill list
   --output json --no-input`.
3. Use the protected profile/configuration supplied by the user or environment.
   Run `mammoth doctor --profile PROFILE --output json --no-input`; do not print,
   echo, or copy its secret-bearing inputs.
4. Discover instead of guessing. Run `mammoth capability list --output json
   --no-input` and the relevant `mammoth schema get COMMAND.ID --output json
   --no-input`, then resolve workspace/project/dataset/view
   parents with reads. Use display names returned by the exact view schema.
5. Translate the business intent into a plan the agent chooses. Submit only
   supported operations with explicit `--project` (and other returned parents),
   structured `--input`, `--output json`, and `--no-input`. Do not use private
   HTTP/SDK escape hatches or local data processing as a substitute.
   For pipeline transformations, prefer the typed `mammoth view transform
   <operation>` commands. The generic `view task add`, `view task preview`, and
   `view task update` routes are low-level expert envelopes: `task_spec` is not
   a fully discoverable task union in the installed schema, so do not invent
   fields from its opaque object shape.
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

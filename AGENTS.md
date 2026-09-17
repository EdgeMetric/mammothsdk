# Working rule for this project

For Mammoth CLI/SDK readiness and release work, the primary agent acts as the
orchestrator. Delegate bounded implementation, documentation, test-case
preparation, and other grunt work to available subagents (prefer Luna for
routine work). The primary agent owns scope and critical decisions, reviews
their diffs, independently verifies the relevant behavior and release
artifacts, and reports evidence and remaining limitations. Do not spend the
primary agent's time making edits that can be safely delegated. Keep parallel
workstreams moving when independent, and avoid repeatedly running full suites
when targeted checks suffice.

This rule does not relax safety, honesty, authorization, or release
verification requirements. Do not claim unsupported capabilities or autonomous
qualification without the required evidence.

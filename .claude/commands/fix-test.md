Read `docs/test-report.txt`. If the file doesn't exist, tell the user to run `./scripts/run-tests.sh` first and stop. If all tests passed, say so and stop.

Count the failures and tell the user how many there are before starting. Work through them one at a time in the order they appear in the report.

For each failure:

Show the test name and the full error message and traceback — do not truncate it.

Read the failing test function from its test file. Also read the router or source function it exercises — find it by tracing the HTTP path the test calls (e.g. `POST /items` → `app/routers/items.py`).

Diagnose which of these four failure modes applies:
- **Source bug**: the source code does not implement what the test expects. Fix the source.
- **Test bug**: the test asserts something wrong (wrong status code, wrong field name, wrong logic). Fix the test.
- **Fixture bug**: a shared fixture in `conftest.py` produces unexpected state. Fix the fixture.
- **Structural error**: import failure, missing dependency, schema mismatch. Name the root cause explicitly before proposing anything.

If the diagnosis is ambiguous between two modes, say which two and ask the user before touching anything.

For source bugs and test bugs: propose the exact change and state why you're confident in the diagnosis. Wait for the user to confirm before writing.

For fixture bugs: do the same, but name every test that uses the fixture so the user knows the blast radius.

For structural errors: do not propose a fix until the root cause is certain. Describe what you'd need to verify and ask whether to proceed.

After each fix, ask the user to re-run `./scripts/run-tests.sh` and confirm before continuing.

Do not commit. The user handles all commits.

When all failures are done, list every file changed and what was changed in each. List any failure you skipped and why.

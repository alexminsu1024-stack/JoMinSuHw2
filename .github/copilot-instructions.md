# Copilot instructions

## Project constraints

- Read `SPEC.md` before changing implementation code.
- In `src/`, do not use Python's built-in `dict` or `set` containers, their constructors, or the built-in `hash()` function. Use the project's `HashTable` instead. Its `.set(key, value)` method is allowed; it is not Python's built-in `set`.
- Generate short codes from incrementing integer IDs with the base62 helpers. Never derive a short code from a hash value.
- Add or update tests before implementing behavior. Do not weaken tests to make an implementation pass.
- Use only the Python standard library and run `make test` after behavior changes.
- Keep server behavior aligned with `SPEC.md`; do not change port visibility or network exposure as part of application code.

## Git workflow

- For each issue, branch from `develop` using `feature/<issue-number>-<short-name>`.
- Post progress updates as comments on the issue.
- When the work is complete, commit the changes, merge the feature branch into `develop`, push the updated branch, and close the issue.

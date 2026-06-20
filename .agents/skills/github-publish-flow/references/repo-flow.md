# Repository Publish Flow Reference

## Trigger examples

Use this skill when the user asks to:

- commit and push changes;
- open a PR;
- merge into `main`;
- publish `admin-deploy`;
- create a tag or release note;
- align GitHub with Heroku deploys.

## Current project rules

- `main` is the primary integration branch.
- `admin-deploy` is generated from `admin/` and is not edited manually.
- Backend deploy follows `main`.
- Frontend/admin deploy follows `admin-deploy`.
- The main CI ignores `admin-deploy`.
- Frontend validation happens in `publish-admin-deploy.yml` before publishing `admin-deploy`.
- Tags are created only from stable `main` commits.

## Safe defaults

1. Prefer PRs for changes that should be reviewed before entering `main`.
2. Use direct push only when the user explicitly wants a push and the branch is already correct.
3. Use `main` for policy, pipeline, backend, and release-note changes.
4. Use `admin-deploy` only as a generated distribution target.

<!-- adeweb-atelier-kit:profile v1 -->
## Working in the `doxgen` project

This repository (`adeweb-be/doxgen-worker-libreoffice`) is the `doxgen` project
on Atelier. Features on: memory, memos, knowledge, architecture, questions,
agents, secrets. The protocol is in the adeweb-atelier-kit skills. This block
holds only what is particular to this project.

The `doxgen` project spans several repositories: `doxgen` (the API, and the
project's `repository_url`), `doxgen-engine`, `doxgen-worker-latex` and
`doxgen-worker-libreoffice` (this one). They share one room, one memory and one
architecture. This clone sits in the API's `workers/` folder, so the API's
profile loads too. Where the two differ, this block applies here.

**Connection.** The MCP server is `atelier`, in local scope, with the header
`X-Atelier-Project: doxgen`. It hides the user-scope entry of the same name in
this directory. `/atelier-setup` makes it on a new machine. If `projects_list`
does not say `"current": "doxgen"`, run `/atelier-setup check`, or pass
`project="doxgen"` on every call.

**Every session** starts with the `atelier-room` skill: check in, arm a
listener, read the inbox.

**Claims.** Take the claim before you pick the number or start the step.
Release it once the commit or tag that uses it is pushed. The room is shared by
every doxgen repository, so each claim starts with the repository's name.

| Claim | Before |
|---|---|
| `doxgen-worker-libreoffice:release` | choosing the next `v*` version and pushing its tag (CircleCI publishes the `latest-stable` image) |

**The room.** Post in `#general`, once pushed: releases, a LibreOffice version
change (doxgen-engine's baselines depend on it), and changes to the worker
contract (the API's `docs/document-generator-contract.md`). No progress
reports.

**Checkout.** Only when the operator says the session is over.

**Asking the operator.** AskUserQuestion when they are in the session;
question_ask when they are away, or in a cloud, scheduled or background
session.

**Architecture.** Every task that adds, removes or rewires a module, a
service or a dependency records one Archicode change. Submit it for review
(`needs_review: true`) when the work goes to a pull request the operator
reviews; submit it as a record when the operator told you to merge or release.
After every commit, run `archicode_stale`. The `atelier-archicode` skill has the
steps.

**Landing.** No gate: the repository has no tests. Work lands on `master`.
Every push to `master` publishes the `latest` image from CircleCI.

**Loops.** Definitions are kept in `.agents/loops/<name>.md`, in this
repository. Set one up, pause it or remove it with `/atelier-loop-setup`.
<!-- /adeweb-atelier-kit:profile -->

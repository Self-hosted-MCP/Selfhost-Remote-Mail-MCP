# Contributing

Thanks for wanting to help. Bug reports, fixes, new providers and clearer docs are all welcome.

## Reporting a problem

Click **New issue** on GitHub and pick a form:

| Form | Use it when |
|---|---|
| **Something doesn't work** | You hit a bug or an error message |
| **My email provider doesn't work** | Your provider won't connect, or isn't on the list |
| **Question** | You want to know how to do something, or have an idea |
| **Share an add-on** | You built an add-on, or have an idea for one. Good ones can join the official version |
| **Report a security problem (private)** | Someone could misuse the server. Only the maintainer sees it |

Each form asks for what's needed to help you, such as how you run the server and which AI app you use. There's no email contact: the forms and private reporting cover everything, and they keep the conversation in one place.

**Remove passwords, passphrases, email addresses and email content** before posting. For security problems, don't open an issue: follow [SECURITY.md](SECURITY.md).

## Changing the code

1. Read [AGENTS.md](AGENTS.md). It explains the code and the rules that must never break, such as "only two tools can send".
2. Install the tools: `uv sync`.
3. Make your change, with a test in `tests/`. The tests use a fake mailbox; never use a real one.
4. Run `uv run pytest -q`. Everything must pass.
5. If people will notice the change, update the matching page in `docs/` and add a line to [CHANGELOG.md](CHANGELOG.md).
6. Open a pull request saying what changed and why.

## Releases (maintainers)

`main` always matches the newest release; work happens on branches and is merged when it's released. To release:

1. Move the "unreleased" notes in [CHANGELOG.md](CHANGELOG.md) under the new version number and date, and set the same version in `pyproject.toml` and `CITATION.cff`.
2. Merge to `main`, tag it `vX.Y.Z`, and publish a GitHub Release with the changelog notes.

Every update path (the `update` command, the fork action, `scripts/update.sh`) only follows published releases, so nothing reaches users until step 2.

## Writing docs

The docs are for people who have never used a terminal. Use short sentences and everyday words, explain any technical word the first time, and show what the reader should see when a step works. No em dashes.

## Adding an email provider

Add it to the table in [docs/email-providers.md](docs/email-providers.md) with a link to the provider's own help page. If `setup` should fill it in, add it to `PROVIDERS` in `server.py` too.

## Credit

By contributing you agree that your work is shared under the MIT license. Keep the original credit (`LICENSE`, `NOTICE`, `CITATION.cff`, the login page footer) and add yourself to the changelog entry if you like.

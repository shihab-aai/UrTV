# Contributing

Thank you. Small, safe changes are the best ones: a fix, a test, a clearer line of text.

## How

1. Fork the repository and make a branch.
2. Open the pull request against **`next`**, never against the release branch.
3. Run the tests before you push (about 15 minutes):

       export CHROMIUM=/opt/pw-browsers/chromium
       bash tests/run.sh

   While you work, run just the test of the file you touched, for example `python3 tests/share_test.py`.

## Releases for this fork

The launcher and screensaver built here read APK updates and the screensaver page from this fork.

- CI fetches pinned Noto Sans Arabic from its public release (SIL Open Font License 1.1). For local tests, install `fonttools` and `brotli`, then run `python3 .github/tools/install_open_fonts.py`. The generated files use the existing asset names for compatibility.
- For the first fork release, prepare and keep a dedicated key with `python3 .github/tools/make_signing_key.py` (requires `cryptography`). To upload it with an authenticated GitHub CLI, add `--repo shihab-aai/UrTV`. The workflow uses the `ANDROID_KEYSTORE_B64` and `ANDROID_KEYSTORE_PASSWORD` secrets to sign both apps.
- An in-place migration requires the key of the installed apps and a higher build number. The optional Actions variable `URTV_BUILD_OFFSET` adds a fixed offset to the workflow run number for both APKs and `version.txt`. For a clean install, the fork can use its dedicated key and its own build numbers.
- Once the signed `apk-latest` release is ready, follow the TV setup instructions with `URTV_RELEASE_REPO=shihab-aai/UrTV`. The new apps take subsequent updates from the fork.

## Rules

- Read [AGENTS.md](AGENTS.md); it applies to people and to AI agents alike. In short: never build or install your own APK,
  never turn auto-update off, never skip or disable a test to make it pass, never override a `!!` guard.
- Keep the generated font files out of Git.
- No personal data anywhere (code, docs, tests, reports): no IP address, serial, Wi-Fi name, user name or file path.
  Tests use obvious placeholders (`2001:db8::`, `192.0.2.x`, `Example Name`).
- Defaults stay as they are unless it is a bug. Nothing that can break a setup in progress or a TV already set up.
- A problem with someone's TV is reported through the form, not as an issue: see [SECURITY.md](SECURITY.md).

## Arabic text

The screens and docs are in plain Saudi-leaning Arabic, short and warm, the way [docs/FEATURES.md](docs/FEATURES.md) is written:
what it is, where to change it, what to tell the agent. Keep the same voice. Religious texts (verses, hadith, adhkar) are never
typed by hand; they come from the checked sources described in [notes/CONTENT-REVIEW.md](notes/CONTENT-REVIEW.md).

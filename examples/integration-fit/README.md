# Integration-Fit Fixtures

These fixtures are not full OpenNort runs. They are small external-input samples used to test whether
an integration can map into existing OpenNort artifacts before source-level adapter work begins.

Run the package-level metadata check from the repository root:

```bash
python skills/research-codex-workflow/scripts/validate_extension_package.py
```

Each fixture declares:

- the external input type;
- the source/version identifier and validation command;
- the minimum OpenNort artifacts it must map to;
- pass criteria;
- fail criteria;
- negative controls for the future semantic runner.

Passing this check does not prove that an adapter works. It only proves that the package surface and
fixture metadata are present enough for a real schema-fit runner to consume.

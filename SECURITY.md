# Security and disclosure

Do not submit any real trading account records, private trading data, private strategy code, exchange credentials, production logs, SSH keys, or licensed datasets in a public issue or PR. Use the synthetic fixtures in `examples/` to reproduce failures.

The application processes local CSV files and generates aggregate reports; it does not call network endpoints, transmit telemetry, connect to a brokerage, or execute strategy files. It is not a general-purpose sandbox for hostile file input or malicious filesystem races. It has explicit file limits and minimizes the output surface but does not guarantee anonymity.

When reporting a security issue, use GitHub's private vulnerability reporting (if enabled), or contact the repository owner through an established private channel. Do not post exploit material or credentials in public issues.

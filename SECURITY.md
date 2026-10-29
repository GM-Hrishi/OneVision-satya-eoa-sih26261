# Security policy

SATYA-EoA is a prototype that runs against a mock approval portal on synthetic data. It is not connected to AICTE or any issuer and is not deployed anywhere by this repository.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub private vulnerability reporting: open the **Security** tab of this repository and choose **Report a vulnerability**. Do not open a public issue or pull request for a security problem.

Please include what you found, where (file or endpoint), how to reproduce it, and what you think the impact is. We will acknowledge the report and keep you informed as we look into it. This is a student prototype maintained by volunteers, so we cannot promise a fixed response time.

## Synthetic data only

Do not include real documents, personal data or real credentials in a report, a test case or an attachment. Use the synthetic data in `data/synthetic/` or invent obviously synthetic values. If you believe you found a real credential or real personal data committed to this repository, say so in a private report without pasting the value.

## Scope

In scope: the code, configuration and documentation in this repository (workbench, mock portal, gateway, worker, packages, compose stack). Out of scope: any real AICTE system, portal or data, which this project does not touch.

# IAM Configuration for n8n Workflows on AWS

This directory includes all the n8n workflows that are in progress or running in production, along with their necessary IAM (Identity and Access Management) configuration files. These configurations help ensure that [n8n](https://n8n.io/) automations operate securely and reliably on AWS.

Below is an overview of the relevant project structure, starting from the `n8n-workflows` directory:

```
n8n-workflows/
└── pratejra-n8n/
    ├── .gitignore
    ├── infra/
    │   └── IAM/
    │       ├── README.md                # (This file)
    │       ├── github-n8n-actions-iam.json
    │       └── github-n8n-backup.json
    └── ...                             # Other project directories and files
```

## Structure

- **`infra/IAM/github-n8n-actions-iam.json`**  
  Trust policy that enables GitHub Actions to assume AWS roles securely via OIDC, supporting CI/CD for active and production n8n workflows.

- **`infra/IAM/github-n8n-backup.json`**  
  Permission policy for n8n to read from and write backups to the designated S3 storage, covering all workflows currently running or in progress.

- **`.gitignore`**  
  Prevents sensitive (e.g., environment variables) and unnecessary files from being tracked in version control.

## Usage

1. **Deployment Integration:**  
   Attach the trust policy (`github-n8n-actions-iam.json`) to IAM roles assumed by GitHub Actions. This allows automated pipelines to deploy or update any in-progress or production n8n workflow securely.

2. **Backup Permissions:**  
   Attach the S3 backup policy (`github-n8n-backup.json`) to IAM roles used by n8n for storing or restoring backups, ensuring all relevant workflows can back up state and data.

This structure supports best security practices and maintainability for both running and in-progress n8n workflows on AWS, with GitHub Actions integration for automation and safe operations.

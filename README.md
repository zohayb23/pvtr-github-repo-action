# pvtr-github-repo-action

GitHub Action for running OSPS (Open Source Project Security) Baseline assessments on your GitHub repository. This action evaluates your repository against security controls defined in the [Open Source Project Security Baseline](https://baseline.openssf.org) and can optionally upload results to GitHub's Security tab as SARIF files.

## Features

- 🔒 Automated security assessments against OSPS Baseline controls
- 📊 Multiple output formats: YAML, JSON, or SARIF
- 🔍 Direct integration with GitHub Security tab via SARIF upload
- 🎯 Configurable catalog selection (default: `osps-baseline`)
- 📦 Artifact uploads for assessment results

## Results

<img width="720" height="512" alt="image" src="https://github.com/user-attachments/assets/1c5c0f6e-9f06-40cc-8fc9-a72b3f01d3a7" />

## Usage

### Basic Example

```yaml
name: OSPS Security Assessment

on:
  schedule:
    - cron: "0 9 * * 1"  # Weekly on Mondays at 9 AM UTC
  workflow_dispatch:  # Allow manual triggering

jobs:
  osps-assessment:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      security-events: write  # Required for SARIF upload
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Run OSPS Security Assessment
        uses: revanite-io/pvtr-github-repo-action@main
        with:
          owner: ${{ github.repository_owner }}
          repo: ${{ github.event.repository.name }}
          token: ${{ secrets.GITHUB_TOKEN }}
          catalog: "osps-baseline"
          upload-sarif: "true"
      
      - name: Upload Assessment Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: osps-assessment-results-${{ github.run_number }}
          path: evaluation_results/
          retention-days: 30
```

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `owner` | Repository owner (organization or user) | Yes | - |
| `repo` | Repository name | Yes | - |
| `token` | GitHub Personal Access Token with repo read permissions | Yes | - |
| `catalog` | OSPS catalog to assess against | No | `osps-baseline` |
| `output-format` | Output format (`yaml`, `json`, or `sarif`) | No | `yaml` |
| `upload-sarif` | Upload results as SARIF to GitHub Security tab. When `true`, `output-format` is automatically set to `sarif` | No | `false` |

### Outputs

| Output | Description |
|--------|-------------|
| `results-path` | Path to the evaluation results directory (`evaluation_results`) |

## Requirements

### GitHub Token Setup

You need a GitHub Personal Access Token (PAT) with the following permissions:
- **Repository read access** - Required to read repository metadata, files, and settings

**Creating a PAT:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` scope (or `public_repo` for public repositories)
3. Add the token as a secret in your repository (Settings → Secrets and variables → Actions)
4. Reference it in your workflow as `${{ secrets.YOUR_TOKEN_NAME }}`

**Note:** For public repositories, you can use `${{ secrets.GITHUB_TOKEN }}` which is automatically provided by GitHub Actions, but it has limited permissions. For private repositories or more comprehensive assessments, use a PAT.

### Permissions

When using `upload-sarif: true`, your workflow must include the `security-events: write` permission:

```yaml
permissions:
  contents: read
  security-events: write  # Required for SARIF upload
```

## Output Formats

### YAML (Default)
Human-readable format, suitable for local review and CI/CD pipelines.

### JSON
Machine-readable format, useful for programmatic processing and integration with other tools.

### SARIF
Static Analysis Results Interchange Format, designed for upload to GitHub's Security tab. Automatically selected when `upload-sarif: true`.

## Results Location

All assessment results are written to the `evaluation_results/` directory in your workspace. This directory contains:
- Assessment results in the selected format
- Detailed evaluation logs
- Control evaluation outcomes

## FAQ

### Q: What permissions does my GitHub token need?

**A:** Your GitHub Personal Access Token needs **repository read permissions**. For public repositories, you can use the `repo` scope (or `public_repo` for public repos only). For private repositories, you'll need the full `repo` scope. The token is used to:
- Read repository metadata
- Access repository files and settings
- Query GitHub's API for security-related information

### Q: Can I use `GITHUB_TOKEN` instead of a Personal Access Token?

**A:** Yes, for public repositories, `${{ secrets.GITHUB_TOKEN }}` works and is automatically provided by GitHub Actions. However, it has limited permissions and may not have access to all repository data needed for comprehensive assessments. For private repositories or more thorough assessments, use a Personal Access Token with appropriate scopes.

### Q: Why isn't my SARIF file uploading to the Security tab?

**A:** There are several common reasons:

1. **Missing permissions**: Ensure your workflow includes `security-events: write` permission
2. **Empty SARIF file**: GitHub Code Scanning requires at least one result in the SARIF file. If all controls pass, the file may be empty and won't upload
3. **Invalid SARIF format**: The action validates the SARIF file before upload. Check the workflow logs for validation messages
4. **Workflow permissions**: Organization-level settings may restrict security event uploads. Check your organization's security settings

The action will log warnings if the SARIF file cannot be uploaded, and the upload step uses `continue-on-error: true` to prevent workflow failures.

### Q: What happens if the assessment finds no issues?

**A:** If all controls pass, the SARIF file may contain no results. GitHub Code Scanning requires at least one result in the SARIF file to upload successfully. In this case:
- The action will detect the empty SARIF file
- A warning will be logged
- The SARIF upload step will be skipped
- Other output formats (YAML/JSON) will still contain the full assessment results

### Q: How do I choose which catalog to assess against?

**A:** Use the `catalog` input parameter. The default is `osps-baseline`, which assesses against the Open Source Project Security Baseline. You can specify other catalogs if available. Check the [OSPS Baseline documentation](https://baseline.openssf.org) for available catalogs.

### Q: Can I assess multiple repositories with one workflow?

**A:** Yes, you can create a matrix strategy to assess multiple repositories:

```yaml
jobs:
  assess-repos:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        repo: [repo1, repo2, repo3]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Run OSPS Security Assessment
        uses: revanite-io/pvtr-github-repo-action@main
        with:
          owner: ${{ github.repository_owner }}
          repo: ${{ matrix.repo }}
          token: ${{ secrets.GITHUB_TOKEN }}
```

### Q: What if I get permission errors when accessing files?

**A:** The action automatically fixes file permissions after the Docker container runs. If you still encounter permission issues:
- Ensure the workflow has write access to the workspace
- Check that the `evaluation_results` directory is created and writable
- Review the workflow logs for specific permission error messages

### Q: How long do assessment results take to process?

**A:** Assessment time varies based on:
- Repository size and complexity
- Number of controls being evaluated
- GitHub API rate limits

Typically, assessments complete in 1-5 minutes. The action includes `wait-for-processing: true` for SARIF uploads, which waits for GitHub to process the results before completing.

### Q: Can I customize the maturity level being assessed?

**A:** Currently, the action assesses against "Maturity Level 1" by default. This is hardcoded in the action configuration. For different maturity levels, you would need to modify the action or use the underlying Docker image directly with a custom configuration file.

### Q: Where can I find example workflows?

**A:** Check out these examples:
- [OSPS Security Assessment Workflow](https://github.com/privateerproj/.github/blob/main/.github/workflows/osps-baseline.yml)
- [Example Configuration](https://github.com/privateerproj/.github/blob/main/.github/pvtr-config.yml)

### Q: What Docker image does this action use?

**A:** The action uses the `eddieknight/pvtr-github-repo:latest` Docker image, which contains the Privateer plugin for GitHub repository assessments.

### Q: How do I troubleshoot a failed assessment?

**A:** Follow these steps:

1. **Check workflow logs**: Review the full workflow output for error messages
2. **Verify token permissions**: Ensure your token has the required repository read access
3. **Check repository accessibility**: Confirm the repository exists and is accessible with the provided token
4. **Review artifact uploads**: Download and inspect the `evaluation_results` artifact for detailed logs
5. **Validate configuration**: Ensure all required inputs are provided correctly

### Q: Can I run this action on a schedule?

**A:** Yes! Use GitHub Actions' `schedule` trigger:

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"  # Every Monday at 9 AM UTC
```

This allows you to run regular security assessments automatically.

### Q: What's the difference between `output-format` and `upload-sarif`?

**A:** 
- `output-format` controls the format of files written to `evaluation_results/` (yaml, json, or sarif)
- `upload-sarif` is a boolean that, when `true`, automatically sets the output format to `sarif` AND uploads the SARIF file to GitHub's Security tab

If you set `upload-sarif: true`, you don't need to also set `output-format: sarif` - it's handled automatically.

## Contributing

Contributions are welcome! Please see our contributing guidelines for more information.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Privateer](https://github.com/privateerproj/privateer) - The core assessment engine
- [Gemara](https://github.com/ossf/gemara) - OSPS Baseline control definitions
- [OSPS Baseline](https://baseline.openssf.org) - Open Source Project Security Baseline specification

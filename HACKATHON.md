# Hacktoberfest 2026 — Hack Day Sonipat

## Team Details

- **Team Name:** Team Async
- **Team Members:**
  - Kamlesh Patade
  - Amit Pal
  - Shivans Gupta

## Selected Problem Statement

**Problem 05: Automated Documentation Drift Detection**

## Project Name

**DocGuard — Automated Documentation Accuracy Checker**

## Project Overview

DocGuard is an open-source developer tool designed to detect outdated or inconsistent documentation by comparing documentation files with source code and code changes.

The tool aims to identify potentially outdated API references, configuration options, default values, and other documentation inconsistencies. It will highlight relevant documentation passages, provide supporting evidence from source code or code changes, and suggest possible corrections.

Our goal is to help developers maintain accurate documentation and reduce the manual effort required to keep documentation synchronized with evolving codebases.

## AI Models Used

- **Model Name:** Qwen2.5-Coder-7B-Instruct (proposed)
- **Reason for Selection:** This open-weight language model is designed for code-related tasks. It is a suitable candidate for analyzing source code and documentation, identifying potential inconsistencies, and generating correction suggestions. Its suitability will be evaluated during implementation.
- **Role of AI:** The model will be integrated into DocGuard to assist in analyzing relevant code changes and documentation, identifying potential documentation drift, and generating evidence-based correction suggestions. Findings will be supported by references to the relevant code or documentation.

## Planned Technology Stack

- **Frontend:** React
- **Backend:** Python with FastAPI
- **Documentation Analysis:** Python-based parsing and comparison
- **AI Integration:** Qwen2.5-Coder-7B-Instruct (proposed open-weight model)
- **Testing:** pytest
- **Continuous Integration:** GitHub Actions
- **Version Control:** Git and GitHub

## Planned Features

1. Analyze Markdown documentation files.
2. Compare documented API names, configuration options, and default values with source code.
3. Analyze code changes to identify documentation that may need updating.
4. Highlight potentially outdated documentation passages.
5. Provide supporting evidence linking findings to relevant source code or code changes.
6. Generate AI-assisted documentation correction suggestions.
7. Include representative example inputs, expected outputs, and automated tests.
8. Run automated checks through GitHub Actions.

## Open-Source Information

- **Repository Visibility:** Public
- **License:** MIT License
- **Selected Problem:** Problem 05 — Automated Documentation Drift Detection

## Repository URL

https://github.com/kamleshpatade1/DocGuard

## Development Approach

DocGuard will begin with a simple, testable documentation analysis pipeline. Rule-based checks will identify straightforward inconsistencies, while the integrated AI model will assist with more contextual analysis and correction suggestions.

The project will prioritize clear evidence, explainable findings, and developer review rather than automatically modifying documentation without approval.
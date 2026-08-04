name: "🐛 Bug Report"
description: "File a bug report to help us improve MailSentry"
title: "[BUG]: "
labels: ["bug"]
assignees:
  - "khushal910"
body:
  - type: markdown
    attributes:
      value: "Thank you for taking the time to report an issue in MailSentry!"
  - type: textarea
    id: summary
    attributes:
      label: "Bug Summary"
      description: "A clear and concise description of what the bug is."
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: "Steps to Reproduce"
      description: "Steps to reproduce the behavior."
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. Scroll down to '....'
        4. See error
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: "Expected Behavior"
      description: "A clear description of what you expected to happen."
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: "Relevant Logs or Stack Trace"
      description: "Paste any relevant backend/frontend console logs or tracebacks here."
      render: shell

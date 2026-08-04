name: "✨ Feature Request"
description: "Suggest an idea or improvement for MailSentry"
title: "[FEATURE]: "
labels: ["enhancement"]
assignees:
  - "khushal910"
body:
  - type: markdown
    attributes:
      value: "Have an idea to make MailSentry faster, safer, or smarter? Let us know!"
  - type: textarea
    id: problem
    attributes:
      label: "Problem or Use Case"
      description: "Is your feature request related to a problem or user workflow? Please describe."
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: "Proposed Solution"
      description: "A clear description of what you want to happen."
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: "Alternatives Considered"
      description: "Any alternative solutions or features you've considered."

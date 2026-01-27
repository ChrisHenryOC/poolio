---
description: Send code or a prompt to Gemini for independent evaluation
allowed-tools: Bash(gemini*),Read
---

Send $ARGUMENTS to Gemini for evaluation.

## Usage

- `/gemini-eval <file-path>` - Evaluate a specific file
- `/gemini-eval <question or prompt>` - Ask Gemini a question

## Step 1: Determine Input Type

Check if $ARGUMENTS is a file path or a free-form prompt.

If it's a file path, read the file content.

## Step 2: Formulate Prompt

Build a prompt that includes:
- The code or question from the user
- Request for analysis/evaluation

## Step 3: Execute Gemini

Run Gemini with the prompt:

```bash
gemini <<'EOF'
Please review and evaluate the following:

[CODE OR QUESTION HERE]

Provide:
1. Your analysis
2. Any issues or concerns
3. Suggestions for improvement (if applicable)
EOF
```

## Step 4: Report Results

Display Gemini's response to the user.

If Gemini fails with an auth error, tell the user:
```
Please ensure GEMINI_API_KEY is set:
  export GEMINI_API_KEY="your-key"
```

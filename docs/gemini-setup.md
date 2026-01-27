# Gemini CLI Setup

This document describes how to set up the Gemini CLI for use with the `/gemini-eval` and `/gemini-review` commands.

## Installation

Install the Gemini CLI using npm:

```bash
npm install -g @google/generative-ai-cli
```

Or using Homebrew:

```bash
brew install gemini
```

Verify installation:

```bash
gemini --version
```

## API Key Configuration

1. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey)

2. Set the environment variable (choose one method):

**Option A: Shell profile (persistent)**

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Then reload: `source ~/.zshrc`

**Option B: direnv (per-project, recommended)**

Create `.envrc` in the project root:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Then run: `direnv allow`

Note: Ensure `.envrc` is in `.gitignore` to avoid committing credentials.

**Option C: Secrets manager**

For teams, consider using 1Password CLI or similar:

```bash
export GEMINI_API_KEY=$(op read "op://Private/Gemini API Key/credential")
```

## Security Notes

- Never commit API keys to version control
- Avoid setting keys inline in commands (exposes in shell history)
- Use environment variables or secrets managers
- Rotate keys periodically

## Verification

Test that the CLI is working:

```bash
echo "Hello, what is 2+2?" | gemini -p "Answer briefly:"
```

Expected output: A response containing "4".

## Troubleshooting

### "GEMINI_API_KEY not set"

Ensure the environment variable is exported and available in your current shell.

### "Permission denied" or "Command not found"

Verify the CLI is installed and in your PATH:

```bash
which gemini
```

### Rate limiting

The free tier has usage limits. If you hit rate limits, wait a few minutes or upgrade your API plan.

## See Also

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)

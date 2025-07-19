# 🪄 promptify

_Gather your codebase into a single, LLM-ready prompt in seconds!_

Install with:
```bash
pip install promptify-ai
```

**promptify** is a command-line tool that collects files from your project into a single prompt file. With one command you can include your whole codebase or selected files with clear headers.

## How to Use

```bash
# Collect files from 'myapp/' and output to 'llm_context.txt'
promptify -s myapp -o llm_context.txt -p '*.md' '*.js' -e 'docs'

# Include files under 'app/src' and add a project tree from its parent directory
promptify -s app/src -o prompt.llm -t app

# See all available options
promptify -h
```

## Features

- Combine your project or chosen files using patterns
- Exclude files or directories as needed
- Adds file headers and an optional project tree
- Copies results to your clipboard

## How it Works

- Recursively scans directories for your patterns
- Concatenates files with clear boundaries
- Optionally saves to a file and copies the prompt

## License

MIT License.

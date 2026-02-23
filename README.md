# Modulattice

**Generate Unity game modules from a single description.** An AI‑powered module factory that designs and writes self‑contained C# systems (code, config, docs) so you can stop fighting boilerplate and focus on game design.

<p align="center">
<strong>Type a prompt → Get a complete Unity module folder → Drag it into your project.</strong>
</p>

***

## Quickstart

```bash
pip install fastapi uvicorn[standard] aiofiles ollama websockets modulattice
```

```bash
# In the repo folder
start.bat
```

Then:

1. Open the web UI.
2. Enter a prompt like: `A player controller for a top‑down shooter`.
3. Review the generated design + code.
4. Copy the module folder into your Unity project once you’re happy with it.

***

## What Modulattice generates

Example:

> “A player health module that will handle players taking damage and dying”

Outputs a self‑contained module folder:

```text
MyPlayerHealthModule/
├── audit.jsonl    # What the system was thinking during generation
├── design.txt     # Design document for the module
├── Config.cs      # Data class for configuration
├── PlayerHealth.cs# Main module code
└── README.md      # How to use this module in Unity
```

Each module lives in its own folder, so Modulattice never touches your existing Unity project or IDE; you decide what to import.

***

## Installation

From PyPI:

```bash
pip install modulattice
```

**Supported / planned LLMs:**

- `llama3` (current default)
- `deepseek-coder`
- Bring‑your‑own via Ollama (planned)

***

## Contributing

1. Fork → Clone → Create a branch (`feat/amazing-feature`).
2. Implement your changes and add/update tests or examples.
3. Open a PR (squash merge preferred).
4. Star the repo if Modulattice helps you – it really boosts visibility.

```bash
git clone https://github.com/remelic/modulattice.git
cd modulattice
pip install -r requirements-dev.txt
start.bat
```

Discussions and ideas: [GitHub Discussions](https://github.com/remelic/modulattice/discussions)

***

## Sponsor the Lattice

Help fuel more Unity templates, better tooling, and faster code generation.

***

## Connect

- 🌐 [modulattice.com](https://modulattice.com)
- 🐦 [@remelic](https://x.com/remelic)
- 📧 [info@modulattice.com](mailto:info@modulattice.com)
- 💬 Discord – coming soon

***

## License

MIT © [remelic](https://github.com/remelic)

<div align="center">
*** Smart – Fast – Helpful ***
</div>

**Made with Modulattice**

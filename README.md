# Resist

**Resist** is a modular **Research Assistant** designed to help manage and organize research projects efficiently.
It provides tools for experimenting, analyzing, and documenting your research process with multilingual support.

## ✨ Features

* **Modular architecture** with `core/` for the main engine (config, database, and app manager).
* **Dashboard module (`modules/dashboard/`)** for handling:

  * Search
  * Analysis
  * Articles
  * Research
* **Experimental Research Assistant** – a space for trying new approaches and storing experiment results.
* **Multilingual support** with `locales/` (currently supports `fa.json` for Persian and `en.json` for English).
* **SQLite database integration** for lightweight and portable data storage.

## 📂 Project Structure

```
Resist/
│── core/               # Core engine (config, database, app)
│── locales/            # Translations (fa.json, en.json, ...)
│── modules/
│   └── dashboard/      # Dashboard module (articles, analysis, etc.)
│── main.py             # Entry point
│── requirements.txt    # Dependencies
```

## 🚀 Getting Started

1. Clone the project:

   ```bash
   git clone https://github.com/AbbasLashani/Resist.git
   cd Resist
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python main.py
   ```

## 🤝 Contributing

We welcome contributions! 🎉
If you'd like to add features, fix bugs, or improve documentation:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

## 📌 Roadmap

* Add more dashboard tools
* Extend experimental assistant features
* Improve multilingual support
* Enhance database integrations

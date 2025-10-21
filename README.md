# Carousel Crew 🎠

Welcome to Carousel Crew, a sophisticated multi-agent AI system designed to automate the entire pipeline of producing high-end, print-ready digital reports. From a single topic, this crew performs deep research, generates multi-modal visuals (data charts and illustrations), and designs a professional HTML presentation ready for PDF conversion.

This project showcases a unique architecture where a team of specialized AI agents, powered by Google's Gemini models, collaborates to deliver a polished final product.

## Key Features & Technical Innovations

-   **Deep Research with Grounding**: The `researcher` agent leverages the built-in Google Search grounding of the Gemini API to ensure all information is up-to-date, factual, and directly sourced from the web.

-   **Custom High-Quality Image Generation**: A custom `Imagen4Tool` was developed to give the `visual_designer` agent the ability to generate stunning, high-resolution (up to 2K) photos and illustrations using Google's state-of-the-art Imagen 4 model.

-   **Advanced Data Visualization**: The `visual_designer` can research the best chart types for a given dataset by scraping the Plotly documentation, and then write and execute Python code via the `CodeInterpreterTool` to generate precise, publication-quality data visualizations.

-   **Automated HTML & PDF Pipeline**: The crew culminates in a `html_designer` agent that builds a modern, print-ready HTML file, which is then passed to a `pdf_converter` agent. This final agent uses a custom tool that interacts with a dedicated PDF conversion API.
-   **Desktop Research Studio UI**: A PySide6-powered control room (`carousel.ui`) delivers a cinematic interface with live logs, slide previews, optional human approvals, and safe cancellation. It automatically clears old artifacts so every run produces a fresh `report.html` / `report.pdf`.

## The HTML-to-PDF Challenge & Solution

A significant challenge in this Python-based `crewAI` project was converting the final, complex HTML file into a pixel-perfect PDF. Standard Python libraries often struggle with modern CSS and JavaScript, leading to rendering issues.

**The Solution**: Instead of a direct Python implementation, we built a robust, external **HTML-to-PDF conversion service** hosted as an API on Hugging Face Spaces.

-   **API Endpoint**: `https://abdallalswaiti-htmlpdfs.hf.space/convert`
-   **Technology**: The service uses **Puppeteer**, a headless browser automation library, ensuring that the HTML is rendered exactly as it would appear in a modern web browser.
-   **Workflow**: The `PDFConversionTool` in this project intelligently packages the `report.html` file along with all its referenced images (`images/*.png`) into a single multipart request to the API. The API then renders the page and returns a high-fidelity PDF.

This architectural decision decouples the rendering logic from the agent framework, providing a scalable and reliable solution for high-quality document generation.

## How It Works: The Agent Workflow

1.  **Research**: The `researcher` agent investigates the topic and produces a structured list of key findings with supporting data.
2.  **Visual Design**: The `visual_designer` receives the research, creates a stunning cover image, and then decides which findings need a data chart (via Plotly) or a conceptual illustration (via Imagen4). It outputs a map of findings to their corresponding image file paths.
3.  **Content Strategy**: The `content_strategist` acts as an editor, taking the research and visual map to create a final JSON structure for the report, defining the narrative flow and layout for each slide.
4.  **HTML Design**: The `html_designer` takes the final JSON brief and uses its expertise in modern web design to generate a single, self-contained, and print-ready `report.html` file.
5.  **PDF Conversion**: The `pdf_converter` takes the `report.html`, gathers all associated images, and sends them to the external Puppeteer-based API to produce the final `report.pdf`.

## Getting Started

### Installation

This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

1.  **Install `uv`:**
    ```bash
    pip install uv
    ```
2.  **Install Dependencies:**
    ```bash
    crewai install
    ```

### Configuration

1.  Rename `example.env` to `.env`.
2.  Add your Gemini key to the `.env` file. Carousel currently targets the Gemini 2.5 Flash model exclusively.

    ```
    # .env file
    MODEL=gemini/gemini-2.5-flash
    GEMINI_API_KEY=YOUR_GEMINI_FLASH_API_KEY
    ```

### Running the Project

Execute the crew from the root directory:

```bash
crewai run
```

The process still supports human-in-the-loop approvals, but they are now optional. You can run end-to-end without pausing by replying with the suggested keyword (e.g., “continue”) or, when using the UI, unchecking the *Require human approvals during run* toggle. The final artifacts land in the project root: `report.html`, `report.pdf`, plus any new visuals inside `images/`.

### Visual Best-Practice Explorer

Prefer a cinematic GUI to explore the research agent with live approvals, console feed, and HTML/PDF previews? Launch the PySide6 interface:

```bash
uv run carousel_ui
```

or, if you are inside an active environment:

```bash
python -m carousel.ui
```

Provide a topic, choose how many insights you need, and the interface will orchestrate the full crew. Highlights of the Research Studio:

- Toggle human approvals on/off at launch. When disabled, prompts are auto-approved with the correct keywords.
- Built-in “Force Stop Run” button safely terminates a stuck crew and resets the UI.
- Automatic cleanup of prior `report.html` / `report.pdf` before each execution to avoid stale artifacts.
- Live console stream, slide timeline, and embedded HTML/PDF previews refresh as soon as each phase finishes.

> **Heads up:** the interface uses PySide6. If you have not yet synced dependencies run `uv sync` (or `pip install PySide6` inside your environment) before launching.

### Programmatic Research Only

Need fast, reusable insights without running the full design pipeline? Import the lightweight helper:

```python
from carousel.best_practices import fetch_best_practices

insights = fetch_best_practices(
    topic="Future of sustainable aviation fuel",
    slides=5,
    aspect_ratio="16:9",
    audience_persona="General executive audience",
)
```

The helper executes only the research task (no visuals, HTML, or PDF) and returns a list of dictionaries ready for downstream use.

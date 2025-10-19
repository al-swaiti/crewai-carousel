# Carousel Crew 🎠

Welcome to Carousel Crew, a sophisticated multi-agent AI system designed to automate the entire pipeline of producing high-end, print-ready digital reports. From a single topic, this crew performs deep research, generates multi-modal visuals (data charts and illustrations), and designs a professional HTML presentation ready for PDF conversion.

This project showcases a unique architecture where a team of specialized AI agents, powered by Google's Gemini models, collaborates to deliver a polished final product.

## Key Features & Technical Innovations

-   **Deep Research with Grounding**: The `researcher` agent leverages the built-in Google Search grounding of the Gemini API to ensure all information is up-to-date, factual, and directly sourced from the web.

-   **Custom High-Quality Image Generation**: A custom `Imagen4Tool` was developed to give the `visual_designer` agent the ability to generate stunning, high-resolution (up to 2K) photos and illustrations using Google's state-of-the-art Imagen 4 model.

-   **Advanced Data Visualization**: The `visual_designer` can research the best chart types for a given dataset by scraping the Plotly documentation, and then write and execute Python code via the `CodeInterpreterTool` to generate precise, publication-quality data visualizations.

-   **Automated HTML & PDF Pipeline**: The crew culminates in a `html_designer` agent that builds a modern, print-ready HTML file, which is then passed to a `pdf_converter` agent. This final agent uses a custom tool that interacts with a dedicated PDF conversion API.

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
2.  Add your API keys to the `.env` file. This project requires keys for Google Gemini and Serper (for search).

    ```
    # .env file
    MODEL=gemini-1.5-pro-latest
    GEMINI_API_KEY=YOUR_GOOGLE_AI_API_KEY
    SERPER_API_KEY=YOUR_SERPER_API_KEY
    ```

### Running the Project

Execute the crew from the root directory:

```bash
crewai run
```

The process will prompt for human input to approve the research plan and the final HTML design before conversion. The final outputs will be `report.html`, `report.pdf`, and the `images/` directory.
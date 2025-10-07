# Carousel Crew 🎠

Welcome to Carousel Crew, a project that demonstrates the power of a multi-agent AI system to generate professional, print-ready presentation carousels from a single prompt.

This entire project is powered by a **single API: Google's Gemini**. From deep research and data analysis to generating stunning visuals and designing the final HTML report, every step is handled by specialized AI agents all leveraging the multi-modal capabilities of the Gemini model family.

## The Power of One API

This project showcases how a single, powerful, multi-modal API can handle a complex workflow that traditionally required multiple services:

-   **Deep Research**: The researcher agent uses the built-in search grounding of Gemini for up-to-date, factual information.
-   **Multi-Modal Visual Generation**: The visual designer agent generates both data-driven charts (via code execution) and creative illustrations (via Imagen) through the Gemini API.
-   **Content Strategy & Design**: Agents analyze the research and visuals to structure a compelling narrative and then build a professional HTML presentation to display the results.

## Installation

This project uses [UV](https://docs.astral.sh/uv/) for fast and reliable dependency management.

1.  **Install `uv`:**
    ```bash
    pip install uv
    ```
2.  **Install Dependencies:**
    ```bash
    crewai install
    ```

## Configuration

Before running, configure your Gemini API key in the `.env` file.

1.  Rename the `example.env` file to `.env`.
2.  Add your `GEMINI_API_KEY` to the `.env` file. This project defaults to `gemini-2.5-flash` for a fast and cost-effective experience. For the highest quality results, you can change the model to `gemini-2.5-pro`.

**Note on API Costs:** While the Gemini API has a free tier for text generation, this project uses the advanced **Imagen 4** model for high-quality image generation, which is a paid feature available on the Google AI Platform. Please be aware of the associated costs.
    ```
    # .env file
    MODEL=gemini-2.5-flash
    GEMINI_API_KEY=YOUR_GOOGLE_AI_API_KEY
    ```

## Running the Project

To generate a new carousel, run the project from the root directory:

```bash
crewai run
```

This command will kick off the crew. After a few minutes, you will find a final `report.html` file and an `images/` directory containing all the generated visuals.

## Customizing Your Crew

You can easily customize the agents, tasks, and tools to fit your needs:

-   **Agents**: Modify `src/carousel/config/agents.yaml` to define your agents' roles and goals.
-   **Tasks**: Modify `src/carousel/config/tasks.yaml` to set up the workflow and agent assignments.
-   **Crew Logic**: Modify `src/carousel/crew.py` to add new tools or change the collaboration process.
-   **Inputs**: Modify `src/carousel/main.py` to change the initial topic or inputs for your crew.

## Agent Breakdown

This project is composed of four specialized AI agents, each with a unique role in the content creation pipeline.

### 1. Researcher
The **Researcher** agent is the foundation of the crew. Its primary role is to gather, analyze, and structure up-to-date information on a given topic.

-   **Core LLM**: `GeminiWithGoogleSearch`
-   **Key Capability**: This agent uses the built-in **Google Search grounding** of its LLM. This allows it to perform real-time web searches to ensure the information it provides is current and factual, directly citing its sources.

### 2. Visual Designer
The **Visual Designer** is a powerful multi-modal agent responsible for creating all the imagery for the presentation. It can generate both data-driven charts and creative illustrations.

-   **Core LLM**: Standard Gemini
-   **Tools Used**:
    -   **`CodeInterpreterTool`**: Gives the agent the ability to write and execute Python code to generate data-driven visualizations (e.g., bar charts, line graphs) using libraries like Matplotlib.
    -   **`Imagen4Tool`**: A custom tool that connects to Google's Imagen 4 model via the Gemini API, used to generate high-quality, original photos and illustrations.
    -   **`ScrapeWebsiteTool`**: Pre-configured to scrape the Plotly documentation, allowing the agent to look up examples for creating complex charts.

### 3. Content Strategist
The **Content Strategist** acts as the editor and project manager. It takes the structured research and the generated visuals and weaves them into a coherent narrative.

-   **Core LLM**: Standard Gemini
-   **Key Capability**: This agent's primary function is reasoning and data organization. It processes the outputs from the previous agents and structures them into a final JSON brief that the HTML Designer can easily parse. It does not require any external tools.

### 4. HTML Designer
The **HTML Designer** is the final specialist in the pipeline. It takes the structured JSON brief and is responsible for designing and building the final, polished `report.html` file.

-   **Core LLM**: `GeminiWithGoogleSearch`
-   **Tools Used**:
    -   **`CodeInterpreterTool`**: This is the agent's most critical tool. After generating the complete HTML and CSS code, it uses this tool to execute a Python script that **writes the code to the `report.html` file**.
    -   **Google Search Grounding**: The agent uses its search-enabled LLM to look up modern web design trends, find the best CSS libraries, or discover JavaScript libraries for interactive elements.

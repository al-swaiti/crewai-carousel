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
2.  Add your `GEMINI_API_KEY` to the `.env` file:
    ```
    MODEL=gemini-1.5-pro-latest
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
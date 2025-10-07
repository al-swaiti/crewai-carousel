# Carousel Crew Knowledge Base

This document provides a comprehensive guide to the Carousel Crew project, a `crewAI` application that performs deep research, generates visuals, and designs professional, print-ready HTML presentation reports.

## Table of Contents
1.  [Introduction & Core Concepts](#1-introduction--core-concepts)
    -   [What is Carousel Crew?](#what-is-carousel-crew)
    -   [Agents](#agents)
    -   [Crews](#crews)
    -   [Tasks](#tasks)
2.  [Key Features](#2-key-features)
    -   [Deep Research](#deep-research)
    -   [Multi-Modal Visual Generation](#multi-modal-visual-generation)
    -   [Professional HTML Presentation](#professional-html-presentation)
3.  [Getting Started & Guides](#3-getting-started--guides)
    -   [Installation](#installation)
    -   [Configuration](#configuration)
    -   [Running the Project](#running-the-project)
4.  [Project-Specific Knowledge: `carousel`](#4-project-specific-knowledge-carousel)
    -   [Agents](#agents-1)
    -   [Tasks](#tasks-1)
    -   [Workflow](#workflow)
    -   [Debugging HTML Generation](#debugging-html-generation)

---

## 1. Introduction & Core Concepts

### What is Carousel Crew?
Carousel Crew is a sophisticated multi-agent AI system that automates the entire pipeline for producing high-end digital reports. It researches topics, generates both data-driven charts and conceptual illustrations, and then designs a professional, print-ready HTML presentation to display the results.

### Agents
Agents are autonomous units with specific roles, defined in `src/carousel/config/agents.yaml`.

### Crews
A Crew is a group of agents working together, defined in `src/carousel/crew.py`.

### Tasks
Tasks are specific assignments for agents, defined in `src/carousel/config/tasks.yaml`.

---

## 2. Key Features

### Deep Research
The `researcher` agent uses the built-in **search grounding** of Google's Gemini models for up-to-date, factual information.

### Multi-Modal Visual Generation
The `visual_designer` agent is a powerful creative engine with two tools:
-   **`CodeInterpreterTool`**: Generates data-driven visuals like charts and plots by writing and executing Python code.
-   **`Imagen4Tool`**: Generates high-quality, original photos and illustrations for conceptual points.

### Professional HTML Presentation
A dedicated `html_designer` agent acts as a "Visual Data Architect." It takes the final content and uses its knowledge of advanced HTML, CSS, and web design principles to generate a polished, print-ready `report.html` file. It can use a web search tool to find the best libraries and techniques for the job.

---

## 3. Getting Started & Guides

### Installation
```bash
pip install uv
crewai install
```

### Configuration
Configure your Gemini model and API keys in a `.env` file:
```
MODEL=gemini-1.5-pro-latest
GEMINI_API_KEY=YOUR_GOOGLE_AI_API_KEY
SERPER_API_KEY=YOUR_SERPER_API_KEY
```

### Running the Project
```bash
crewai run
```
This command will generate a final `report.html` file and an `images/` directory containing all the generated visuals.

---

## 4. Project-Specific Knowledge: `carousel`

### Agents
-   **`researcher`**: Researches the topic and provides structured data.
-   **`visual_designer`**: The "Creative Visuals Director" that generates both charts (with code) and illustrations (with Imagen4).
-   **`reporting_analyst`**: The "Content Strategist" that organizes the research and visuals into a JSON brief.
-   **`html_designer`**: The "Elite Visual Data Architect" that uses the JSON brief to design and build the final `report.html`.

### Tasks
-   **`research_task`**: Conducts research and outputs structured findings with data.
-   **`visual_design_task`**: Generates all necessary visuals and outputs their file paths.
-   **`reporting_task`**: Creates a structured JSON brief of the final content.
-   **`html_design_task`**: Takes the JSON brief and produces the final `report.html`.

### Workflow
1.  The `researcher` performs deep research and identifies top points, passing structured data.
2.  The `visual_designer` receives the research and generates a complete set of visuals, saving them to the `images/` directory.
3.  The `reporting_analyst` receives the research and image paths and creates a clean JSON content brief.
4.  The `html_designer` receives the JSON brief and uses its web design expertise to build the final, professional `report.html`.

### Debugging HTML Generation
-   **Problem**: The `html_designer` agent completed its task without errors, but the final `report.html` file was not created.
-   **Root Cause**: The agent's task description in `src/carousel/config/tasks.yaml` was insufficiently specific. It described the desired HTML content in detail but was missing an explicit, imperative command for the agent to **use its tool to write the generated code to a file**.
-   **Solution**: The `html_design_task` description was modified to include a final, critical instruction: `After generating the complete HTML and CSS as a single string, you MUST use your tool to write this string to a file named 'report.html'`.
-   **Key Takeaway**: For agents that need to produce a file artifact, the task's instructions must not only describe the content but also explicitly command the agent to perform the final file-writing action. An agent will not automatically assume it should save its output unless told to do so.
-   **Image Data Flow**: The image content (pixels) is never sent to the LLM. The `visual_designer` saves the image to a file and passes only the text-based **file path** to subsequent agents. The `html_designer` then uses this text path to write the `<img src="...">` tag in the final HTML.
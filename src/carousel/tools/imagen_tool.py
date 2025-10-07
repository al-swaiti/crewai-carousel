from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from typing import Type, Literal
import os
from datetime import datetime
import traceback

class Imagen4Input(BaseModel):
    """Input schema for the Imagen4 Ultra Tool."""
    prompt: str = Field(..., description="Text prompt for image generation (max 480 tokens)")
    number_of_images: int = Field(default=1, description="Number of images to generate (1-4)")
    aspect_ratio: Literal["1:1", "3:4", "4:3", "9:16", "16:9"] = Field(default="1:1")
    image_size: Literal["1K", "2K"] = Field(default="1K", description="Image resolution")
    person_generation: Literal["dont_allow", "allow_adult", "allow_all"] = Field(default="allow_all")

class Imagen4Tool(BaseTool):
    name: str = "Imagen 4 Ultra Image Generator"
    description: str = "Generates high-quality images using Google's Imagen 4 Ultra model"
    args_schema: Type[BaseModel] = Imagen4Input

    def _run(self, prompt: str, number_of_images: int = 1, aspect_ratio: str = "1:1",
             image_size: str = "1K", person_generation: str = "allow_all") -> str:
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return "❌ Error: GEMINI_API_KEY environment variable not set"

            # Initialize client
            client = genai.Client(api_key=api_key)

            response = client.models.generate_images(
                model="imagen-4.0-ultra-generate-001",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=number_of_images,
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,

                )
            )

            if not hasattr(response, "generated_images") or not response.generated_images:
                return f"❌ Error: No images generated. Full response: {response}"

            output_dir = os.path.join(os.getcwd(), "images")
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results = []

            for i, generated_image in enumerate(response.generated_images):
                filename = os.path.join(output_dir, f"imagen4_ultra_{timestamp}_{i+1}.png")
                generated_image.image.save(filename)
                results.append(filename)

            return f"✅ Successfully generated {len(results)} images: {', '.join(results)}"

        except Exception as e:
            error_details = traceback.format_exc()
            return f"❌ Error generating images: {str(e)}\nTraceback:\n{error_details}"

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os

class FileExistenceCheckerInput(BaseModel):
    """Input schema for FileExistenceCheckerTool."""
    file_name: str = Field(..., description="The name of the file to check for existence.")

class FileExistenceCheckerTool(BaseTool):
    name: str = "File Existence Checker"
    description: str = "Checks if a specific file exists in the project's root directory. Use this to check for completed work before starting a task."
    args_schema: Type[BaseModel] = FileExistenceCheckerInput

    def _run(self, file_name: str) -> str:
        """Checks if the file exists and returns a confirmation or error message."""
        file_path = os.path.join(os.getcwd(), file_name)
        if os.path.exists(file_path):
            return f"Confirmed: The file '{file_name}' already exists. You can proceed to the next step."
        else:
            return f"Action Required: The file '{file_name}' does not exist. The relevant task must be executed."

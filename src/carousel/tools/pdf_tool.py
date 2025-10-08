from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os
from weasyprint import HTML, CSS

class PDFConversionInput(BaseModel):
    """Input schema for PDFConversionTool."""
    html_file_path: str = Field(..., description="Path to the HTML file to convert")
    aspect_ratio: str = Field(..., description="Aspect ratio: '16:9', '9:16', or '1:1'")

class PDFConversionTool(BaseTool):
    name: str = "PDF Conversion Tool"
    description: str = "Converts a local HTML file to a PDF document, respecting the specified aspect ratio."
    args_schema: Type[BaseModel] = PDFConversionInput
    
    def _run(self, html_file_path: str, aspect_ratio: str) -> str:
        if not os.path.exists(html_file_path):
            return f"Error: HTML file not found at {html_file_path}"
        
        try:
            pdf_path = html_file_path.replace('.html', '.pdf')
            
            # Define CSS for page size based on aspect ratio
            if aspect_ratio == '16:9':
                page_style = '@page { size: A4 landscape; margin: 0; }'
            elif aspect_ratio == '1:1':
                page_style = '@page { size: 21cm 21cm; margin: 0; }'
            else: # Default to 9:16 portrait
                page_style = '@page { size: A4 portrait; margin: 0; }'

            css = CSS(string=page_style)
            HTML(filename=html_file_path).write_pdf(pdf_path, stylesheets=[css])
            
            return f"Successfully converted {html_file_path} to {pdf_path}"
        except Exception as e:
            return f"An error occurred during PDF conversion with WeasyPrint: {e}"
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List
import os
import requests
import re
import mimetypes

class PDFConversionInput(BaseModel):
    """Input schema for PDFConversionTool."""
    html_file_path: str = Field(..., description="Path to the HTML file to convert")
    aspect_ratio: str = Field(..., description="Aspect ratio: '16:9', '9:16', or '1:1'")

class PDFConversionTool(BaseTool):
    name: str = "PDF Conversion Tool"
    description: str = "Converts a local HTML file to a PDF document using an external API, handling image uploads automatically."
    args_schema: Type[BaseModel] = PDFConversionInput

    def _run(self, html_file_path: str, aspect_ratio: str) -> str:
        api_url = "https://abdallalswaiti-htmlpdfs.hf.space/convert"

        if not os.path.exists(html_file_path):
            return f"Error: HTML file not found at {html_file_path}"

        try:
            # 1. Read HTML content
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 2. Find all unique image paths in the HTML (more robustly)
            img_src_paths = re.findall(r'src=[\'"]([^\'"]+)[\'"]', html_content)
            css_url_paths = re.findall(r'url\([\'"]?([^\'"\)]+)[\'"]?\)', html_content)
            image_paths = img_src_paths + css_url_paths
            unique_images = sorted(list(set(image_paths)))

            # 3. Prepare files for multipart upload
            files = [('html_file', (os.path.basename(html_file_path), open(html_file_path, 'rb'), 'text/html'))]
            
            print(f"Found {len(unique_images)} unique images to upload.")
            
            for image_path in unique_images:
                if os.path.exists(image_path):
                    mimetype, _ = mimetypes.guess_type(image_path)
                    if not mimetype:
                        mimetype = 'application/octet-stream'
                    files.append(('images', (os.path.basename(image_path), open(image_path, 'rb'), mimetype)))
                else:
                    print(f"Warning: Image file not found, skipping: {image_path}")


            # 4. Prepare data payload
            data = {
                'aspect_ratio': aspect_ratio,
                'auto_detect': 'false'
            }

            # 5. Make the request to the API
            print(f"Sending request to API with {len(files) - 1} images...")
            response = requests.post(api_url, files=files, data=data, timeout=120)

            # Close all opened files
            for _, file_tuple in files:
                file_tuple[1].close()

            # 6. Handle the response
            if response.status_code == 200:
                pdf_path = html_file_path.replace('.html', '.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                return f"✅ Successfully converted to PDF: {pdf_path}"
            else:
                return f"PDF conversion failed with status {response.status_code}: {response.text}"

        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

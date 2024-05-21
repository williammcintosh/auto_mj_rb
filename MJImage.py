import openai
import requests
from PIL import Image
from io import BytesIO
import math

class MJImage:
    def __init__(self, image_url):
        self.api_key = self.get_openai_api_key()
        self.client = openai.OpenAI(api_key=self.api_key)
        self.image_url = image_url

    def get_openai_api_key(self):
        """Retrieve the OpenAI API key from a file."""
        with open('gptapi_key.txt', 'r') as file:
            return file.read().strip()

    def describe(self):
        """Describe the image using OpenAI's GPT model with a form-filling prompt."""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are about to describe an image. Please fill out the following sections:"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Title - Use a descriptive title that explains the image in 4-8 words that is family friendly."
                        },
                        {
                            "type": "text",
                            "text": "Tags - Write up to 15 tags (50 character limit per tag) separated by commas, that describe the content of the image."
                        },
                        {
                            "type": "text",
                            "text": "Description - Share the story or meaning behind the image as if it were your own work from the first person using ('I') as if you created it from the perspective of the artist or photographer."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self.image_url
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        try:
            # Extracting title, tags, and description from the response
            content = response.choices[0].message.content
            title = content.split("\n")[0].split("Title: ")[1].strip()
            tags = content.split("\n")[2].split("Tags: ")[1].strip()
            description = content.split("\n")[4].split("Description: ")[1].strip()
            
            return {"title": title, "tags": tags, "description": description}
        except Exception as e:
            print(f"Failed to parse response: {str(e)}")
            return {"title": "", "tags": "", "description": ""}


    def download_image(self):
        """Download an image from the URL and return a PIL Image object."""
        response = requests.get(self.image_url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))

    def calculate_scale_factor(self, initial_size, target_size):
        """Calculate the scale factor needed to reach the target size."""
        return math.sqrt(target_size / initial_size)

    def enlarge(self, target_size_mb=200):
        """Enlarge the image by a calculated scale factor to reach the target size."""
        image = self.download_image()
        
        # Calculate the current file size in bytes
        with BytesIO() as buf:
            image.save(buf, format='PNG')
            initial_size_mb = len(buf.getvalue()) / (1024 * 1024)
        
        # Calculate the desired scale factor to reach the target size
        scale_factor = self.calculate_scale_factor(initial_size_mb, target_size_mb)
        
        # Calculate new dimensions
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        
        # Resize the image
        enlarged_image = image.resize((new_width, new_height), Image.LANCZOS)
        
        return enlarged_image

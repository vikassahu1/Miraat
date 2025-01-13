import google.generativeai as genai
from dotenv import load_dotenv
from accessories.exception import CustomException
from accessories.logger import logging
import sys
import os
import re

# Load API key from environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY 


class LLMSetup:
    def __init__(self):
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')



    def format_input(self, user_input: str) -> str:
        """
        Formats the input text using a template.
        """
        input_template = (
            "User Query:\n"
            "{user_input}\n"
            "Please provide a detailed, well-structured response."
        )
        return input_template.format(user_input=user_input)



    def format_to_text(self,text):
        # Replace **...** with a new section header, followed by a line break
        text = re.sub(r"\*\*(.*?)\*\*", r"\n\1\n", text)

        # Replace * with an indented line, adding a newline at the start
        text = re.sub(r"\* (.*?)\n", r"\1\n", text)
        
        # Ensure there are no extra leading/trailing newlines
        text = text.strip()
         
        return text



    def format_to_html(self, text: str) -> str:
        """
        Converts the raw response text into well-formatted HTML.
        """
        # Replace **...** with section headers
        text = re.sub(r"\*\*(.*?)\*\*", r"<h2>\1</h2>", text)

        # Replace lists starting with * with bullet points
        text = re.sub(r"\* (.*?)\n", r"<li>\1</li>", text)

        # Wrap bullet points in a <ul>
        text = re.sub(r"(?:<li>.*?</li>\n)+", lambda match: f"<ul>{match.group(0)}</ul>", text, flags=re.S)

        # Add paragraph tags for standalone text
        text = re.sub(r"(?<!</h2>|</ul>)\n", r"<br>", text)

        # Ensure no extra leading/trailing tags
        text = text.strip()

        return text



    # Adding name, age and gender to the context. 
    def get_result(self, user_text: str,name: str, age: int, gender: str) -> str:
        try:
            formatted_input = (
                "Context: You are mental health assessment AI (your name is Mirat). "
                "You are given a text in which the user is describing their mental health issue. "
                "Based on the text, detect some disorders. They also gave some tests to assess further. "
                "Inference of tests is also given. In some cases, tests or inferences may not be available. "
                "Your task is to give a full systematic solution to the user based on the data given. "
                "You may use the context of the text to make it more personalized.\n\n"
                "Note: Its not two sided conversion so don't ask questions.\n\n"
                "User Information:\n"
                f"Name: {name}\n"
                f"Age: {age}\n"
                f"Gender: {gender}\n\n"
                "Data:\n"
            )

            formatted_input += self.format_input(user_text)
            response = self.model.generate_content(formatted_input)

            formatted_output = "<p>Sorry, no valid response could be generated.</p>"

            if hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    if len(candidate.content.parts) > 0 and hasattr(candidate.content.parts[0], 'text'):
                        raw_output = candidate.content.parts[0].text
                        formatted_output = self.format_to_html(raw_output)
            
            return formatted_output
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            raise CustomException(e, sys)




# Note:
# LLM part is perfectly working . 
if __name__ == '__main__':
    llm = LLMSetup()
    user_text = "The user feels anxious about their exam results."
    result = llm.get_result(user_text,"Vikas",22,"Male")
    print(result)





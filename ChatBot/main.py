import os
import warnings
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import trim_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

# Suppress warnings
warnings.filterwarnings("ignore")

class Chatbot:
    def __init__(self, session_id):
        self.session_id = session_id
        self.history = self.get_session_history(session_id)

        # Set environment variables
        os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

        # Initialize the model
        self.model = ChatGoogleGenerativeAI(
            model="gemini-pro",
            convert_system_message_to_human=True,
            temperature=0.7,
            max_output_tokens=2048
        )

        # Define the system message
        SYSTEM_MESSAGE = """You are Miraat, a mental health assistant chatbot. Your role is to be a supportive friend and guide, 
        offering compassionate, helpful responses. You should maintain a friendly and empathetic tone while assisting the user."""

        # Define the prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_MESSAGE),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # Create the chain
        self.chain = self.prompt | self.model

    @staticmethod
    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session."""
        if not hasattr(Chatbot, "store"):
            Chatbot.store = {}
        if session_id not in Chatbot.store:
            Chatbot.store[session_id] = InMemoryChatMessageHistory()
        return Chatbot.store[session_id]

    def __str__(self):
        return "Miraat, the mental health assistant"

    def chat(self, user_input: str) -> str:
        """Process user input and return chatbot response."""
        try:
            # Trim history to ensure it fits within model limits
            trimmed_history = trim_messages(
                self.history.messages,
                max_tokens=1500,
                token_counter=lambda msgs: sum(len(msg.content.split()) for msg in msgs)  # Ensure callable
            )

            # Generate response
            response = self.chain.invoke({
                "history": trimmed_history,
                "input": user_input
            })
            
            # Check and handle empty or inappropriate responses
            if not response or not response.content.strip():
                fallback = "I'm here to support you, but I might not have the right words for this topic. Can I assist in another way?"
                self.history.add_ai_message(fallback)
                return fallback

            # Add messages to history
            self.history.add_user_message(user_input)
            self.history.add_ai_message(response.content)
            
            return response.content
        
        except Exception as e:
            print(f"Debug - Error details: {str(e)}")
            return f"An error occurred: {str(e)}"

    def get_chat_history(self):
        """Retrieve chat history for the current session."""
        return self.history.messages









if __name__ == "__main__":
    try:
        # Create a chatbot instance with a session ID
        bot = Chatbot("user123")
        print("Miraat Mental Health Assistant (Type 'exit' to end the conversation)")
        print("-" * 50)
        
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nBot: Goodbye! Take care of yourself. Remember, I'm here if you need to talk again.")
                
                # Print final chat history
                print("\nChat History:")
                history = bot.get_chat_history()
                for msg in history:
                    sender = "Bot" if isinstance(msg, AIMessage) else "You"
                    print(f"{sender}: {msg.content}")
                break
            
            # Get bot response
            response = bot.chat(user_input)
            print("\nBot:", response)
            print("-" * 50)
    
    except Exception as e:
        print(f"Main execution error: {str(e)}")

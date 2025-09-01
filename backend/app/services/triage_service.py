
from transformers import pipeline

class TriageService:
    def __init__(self, categories: list[str]):
        """
        Initializes the Triage Service.
        
        Args:
            categories: The list of your 13 broad category names.
        """
        self.candidate_labels = categories
        try:
            # This model will be downloaded from Hugging Face the first time.
            self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            print("TriageService: Zero-Shot model loaded successfully.")
        except Exception as e:
            self.classifier = None
            print(f"TriageService: FAILED to load Zero-Shot model. Error: {e}")


    def get_initial_hypotheses(self, text: str, num_hypotheses: int = 3) -> list[dict]:
        """
        Args:
            text: The concatenated text from the priming conversation.
            num_hypotheses: The number of top categories to return.
            
        Returns:
            A list of dictionaries, e.g., [{'category': 'Anxiety Disorders', 'score': 0.92}, ...]
        """
        if not self.classifier:
            # Fallback if the model failed to load
            return []

        print(f"TriageService: Classifying text: '{text[:100]}...'")
        results = self.classifier(text, self.candidate_labels, multi_label=True)
        
        # Combine labels and scores into a list of dictionaries
        hypotheses = [
            {"category": label, "score": score}
            for label, score in zip(results['labels'], results['scores'])
        ]
        
        # Return the top N hypotheses
        return hypotheses[:num_hypotheses]






if __name__ == "__main__":
    # Example usage
    categories = [
        "Mood Disorders", 
        "Anxiety Disorders", 
        "Trauma and Stressor-Related Disorders", 
        "Obsessive-Compulsive Disorder (OCD)", 
        "Personality Disorders", 
        "Eating Disorders", 
        "Substance Use Disorders", 
        "Psychotic Disorders", 
        "Neurodevelopmental Disorders", 
        "Impulse Control Disorders", 
        "Social and Emotional Well-being",
        "Suicidal Tendencies"
    ]
    
    triage_service = TriageService(categories)
    sample_text = "I have been feeling very anxious lately, with constant worry and restlessness."
    hypotheses = triage_service.get_initial_hypotheses(sample_text)
    print("Initial Hypotheses:", hypotheses)

    x = {h['category']: h['score'] for h in hypotheses}
    print(x)

from transformers import pipeline
import json

# Define possible mental health disorder labels
candidate_labels = [
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

relevance_labels = ["Mental Health Symptom or Emotion", "Neutral Statement"]


class Assess:
    def __init__(self,text):
        # Initialize the zero-shot classification pipeline
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.symptom_text = text


    
    def classify_dual(self)->list:
        # Run classification
        relevance_result = self.classifier(self.symptom_text, relevance_labels, multi_label=True)
        return relevance_result['labels'][0]


    def dignose(self)->list:
        # Perform zero-shot classification
        result = self.classifier(self.symptom_text, candidate_labels)
        disorders  = []

        # Output the results
        for label, score in zip(result['labels'], result['scores']):
            if(score>0.15):
                # print(label,"  ",score)
                disorders.append(label)

        sorted(disorders)
        n  = len(disorders)
        if(n==0):
            return ["No disorder found"]
        if(n>3):
            disorders = disorders[:3]

        return disorders

    






    


    


        

if __name__ == '__main__':
    symptom_text = "my name is khan"
    assess = Assess(symptom_text)
    print(type(assess.classify_dual()))
    print("Mental Health Disorders:", assess.dignose())
    print("Mental Health Symptom or Emotion:", assess.classify_dual())

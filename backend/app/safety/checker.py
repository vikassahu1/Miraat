
HIGH_RISK_KEYWORDS = [
    "kill myself", "suicide", "suicidal", "end my life", "want to die",
    "no reason to live", "can't go on", "i am hopeless", "self-harm",
    "ending it all", "take my own life","i quit my life"
]

def check_for_crisis(text: str) -> bool:
    lower_text = text.lower()
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in lower_text:
            print(f"CRISIS ALERT: High-risk keyword '{keyword}' detected.")
            return True 
    return False 

if __name__ == "__main__":
    test_texts = [
        "I feel hopeless and want to die.",
        "I am just having a bad day.",
        "Sometimes I think about ending it all.",
        "Life is beautiful."
    ]
    
    for text in test_texts:
        if check_for_crisis(text):
            print(f"Alert triggered for text: {text}")
        else:
            print(f"No alert for text: {text}")
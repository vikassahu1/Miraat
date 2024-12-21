from schemas import TestRequest,TestAndAnswer
from typing import Dict
from accessories.exception import CustomException
import sys
from accessories.logger import logging



#We are gettign test and ans dict[str,str] form 
class Tests:
    def __init__(self):
        pass

    def phq9(self,ans):
        score = 0
        for question_id, answer in ans.items():
            score+= (answer-1)
        if score>=1 and score<=4:
            return score, "Minimal symptoms"
        elif score>=5 and score<=9:
            return score, "Mild symptoms"
        elif score>=10 and score<=14:
            return score, "Moderate symptoms"
        elif score>=15 and score<=19:
            return score, "Moderately severe symptoms"
        elif score>=20 and score<=27:
            return score, "Severe symptoms"



    
    def mdq(self,ans):
        counter = 1
        score = 0
        one,two = False,False
        for question_id, answer in ans.items():
            if counter<=13 and answer == 1:
                score+=1
            
            elif counter==14 and answer == 1 and score>=7:
                one = True
            
            elif counter==15 and answer >= 1 :
                two = True
            counter += 1

        if one and two:
            return score,"Result suggest illness"
        else:
            return score,"Result suggest no illness"
        





    def gad7(self,ans):
        score = 0
        # Calculate the total score by summing up answers
        for question_id, answer in ans.items():
            score += (answer - 1)  # Adjusting as per scoring (0-based)

        # Determine anxiety severity based on total score
        if score >= 0 and score <= 4:
            return score, "Minimal anxiety"
        elif score >= 5 and score <= 9:
            return score, "Mild anxiety"
        elif score >= 10 and score <= 14:
            return score, "Moderate anxiety"
        elif score >= 15 and score <= 21:
            return score, "Severe anxiety"




    

    def pcl5_evaluation(self,ans):
        """
        Evaluates the PCL-5 score based on the provided answers.
        Args:
            ans (dict): A dictionary where keys are question IDs and values are selected option IDs (0 to 4).
        Returns:
            tuple: A tuple containing the total score and the symptom severity description.
        """
        total_score = 0

        # Calculate total score by summing option_id values for each question
        for question_id, answer in ans.items():
            total_score += (answer-1)  # No adjustment needed, options are 0–4 directly

        # Determine symptom severity based on the clinical cutoff of 33
        if total_score >= 33:
            symptom_severity = "High PTSD Symptoms"
        else:
            symptom_severity = "Low PTSD Symptoms"

        return total_score, symptom_severity


        


    def y_bocs_evaluation(self,ans):
        total_score = 0
        
        for question_id, answer in ans.items():
            total_score += (answer -1)

        if 0 <= total_score <= 7:
            severity = "Subclinical"
        elif 8 <= total_score <= 15:
            severity = "Mild"
        elif 16 <= total_score <= 23:
            severity = "Moderate"
        elif 24 <= total_score <= 31:
            severity = "Severe"
        elif 32 <= total_score <= 40:
            severity = "Extreme"
        else:
            severity = "Invalid score"

        return total_score, severity





    def evaluate_lsas_responses(self,responses):
        """
        Evaluate LSAS questionnaire responses.

        Parameters:
        - responses: A list of integers, where each integer corresponds to the selected
        option_id (0-4) for a question.

        Returns:
        - A dictionary with:
            - total_score: The sum of the responses.
            - evaluation: A string indicating the severity level.
        """
        # Clinical thresholds based on LSAS scoring
        thresholds = {
            "None": 0,
            "Mild Social Anxiety": 30,
            "Moderate Social Anxiety": 60,
            "Marked Social Anxiety": 90,
            "Severe Social Anxiety": 120,
        }

        total_score = 0
        # Calculate total score
        for question_id, answer in ans.items():
            total_score += (answer -1)
        

        # Determine severity based on thresholds
        if total_score < thresholds["Mild Social Anxiety"]:
            evaluation = "None or minimal social anxiety."
        elif total_score < thresholds["Moderate Social Anxiety"]:
            evaluation = "Mild social anxiety."
        elif total_score < thresholds["Marked Social Anxiety"]:
            evaluation = "Moderate social anxiety."
        elif total_score < thresholds["Severe Social Anxiety"]:
            evaluation = "Marked social anxiety."
        else:
            evaluation = "Severe social anxiety."

        return total_score, evaluation


            





    def evaluate_msi_bpd(self,responses):
        """
        Evaluates the McLean Screening Instrument for Borderline Personality Disorder (MSI-BPD).
        
        Args:
            responses (dict): A dictionary where the key is the question_id (1-10), and the value is the option_id (1 for "No", 2 for "Yes").
        
        Returns:
            dict: A tuple containing the total score and a professional assessment of the result.
        """
        # Scoring: Yes (option_id 2) is 1 point, No (option_id 1) is 0 points.
        score = sum(1 for answer in responses.values() if answer == 2)
        
        # Threshold for clinical concern: Usually 7 or higher is indicative of possible BPD.
        threshold = 7
        
        # Assessment based on the score
        if score >= threshold:
            assessment = "The respondent's score is indicative of a potential Borderline Personality Disorder (BPD). \nFurther clinical evaluation by a mental health professional is recommended."
            
        else:
            assessment = "The respondent's score does not suggest significant concerns related to Borderline Personality Disorder (BPD).\nHowever, this is a screening tool and not a diagnostic measure. If there are concerns, consulting a mental health professional is advised."
        return score, assessment








    def eat_26_evaluation(self,ans):
        """
        Evaluate EAT-26 scores based on the standard criteria.

        Parameters:
            ans (dict): A dictionary where keys are question IDs and values are user responses (1–6 scale).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the level of concern.
        """
        total_score = 0

        # Calculate the total score
        for question_id, answer in ans.items():
            # Subtract 1 because EAT-26 scoring starts from 0 for "Never"
            total_score += (answer - 1)

        # Determine the severity level
        if total_score < 20:
            severity = "No clinical concern (Normal)"
        else:
            severity = "Clinical concern (Further evaluation recommended)"

        return total_score, severity









    def audit_evaluation(self,ans):
        """
        Evaluate AUDIT scores based on standard criteria with options starting from 1.

        Parameters:
            ans (dict): A dictionary where keys are question IDs (1-10) and values are user responses (option IDs 1, 2, ...).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the risk category.
        """
        total_score = 0

        # Score questions 1-8 (options range from 1-5, adjusted to 0-4 by subtracting 1)
        for question_id in range(1, 9):
            if question_id in ans:
                total_score += ans[question_id] - 1

        # Score questions 9-10 (options range from 1-3, adjusted to 0-2 by subtracting 1)
        for question_id in range(9, 11):
            if question_id in ans:
                total_score += ans[question_id] - 1

        # Determine risk category
        if 10 <= total_score <= 16:
            severity = "Low Risk"
        elif 17 <= total_score <= 24:
            severity = "Hazardous Drinking"
        elif 25 <= total_score <= 32:
            severity = "Harmful Drinking"
        elif total_score >= 33:
            severity = "Likely Alcohol Dependence"
        else:
            severity = "Invalid score"

        return total_score, severity








    def dast10_evaluation(self,ans):
        """
        Evaluate DAST-10 scores based on answers valued 1 (No) and 2 (Yes).
        
        Parameters:
            ans (dict): A dictionary where keys are question IDs (1-10) and values are user responses (1 or 2).
            
        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the risk category.
        """
        total_score = 0


        # Score questions 1-10, options range from 1-7
        for question_id, answer in ans.items():
            total_score += (answer) 

        # Determine risk category based on total score
        if 10 <= total_score <= 14:
            severity = "Low Risk"
        elif 15 <= total_score <= 19:
            severity = "Moderate Risk"
        elif 20 <= total_score <= 24:
            severity = "High Risk"
        elif 25 <= total_score <= 40:
            severity = "Severe Risk"
        else:
            severity = "Invalid score"

        return total_score, severity








    def panss_evaluation(self,ans):
        """
        Evaluate PANSS scores based on user responses for 10 questions.

        Parameters:
            ans (dict): A dictionary where keys are question IDs (1-10) and values are user responses (option IDs 1-7).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the severity category.
        """
        total_score = 0

        # Score questions 1-10, options range from 1-7
        for question_id, answer in ans.items():
            total_score += (answer) 
        # Determine severity category based on total score
        if total_score <= 30:
            severity = "Low Severity"
        elif 31 <= total_score <= 60:
            severity = "Moderate Severity"
        elif 61 <= total_score <= 90:
            severity = "High Severity"
        elif total_score > 90:
            severity = "Very High Severity"
        else:
            severity = "Invalid score"

        return total_score, severity









    def asrs_evaluation(self,ans):
        """
        Evaluate ASRS (Autism Spectrum Rating Scale) scores based on user responses.

        Parameters:
            ans (dict): A dictionary where keys are question IDs (SC1, SC2, ..., ER3) and values are user responses (option IDs 1-4).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the severity category.
        """
        total_score = 0

        # Define the questions and their respective option values (1-4)
        questions = [
            "SC1", "SC2", "SC3",  # Social Communication questions
            "RRB1", "RRB2", "RRB3",  # Repetitive Behaviors questions
            "ER1", "ER2", "ER3"  # Emotional Regulation questions
        ]

        # Score each question based on the user's answer (values range from 1 to 4)
        for question_id in questions:
            if question_id in ans:
                total_score += ans[question_id]

        # Determine severity category based on total score
        if total_score <= 10:
            severity = "Low Severity"
        elif 11 <= total_score <= 20:
            severity = "Mild Severity"
        elif 21 <= total_score <= 30:
            severity = "Moderate Severity"
        elif 31 <= total_score <= 40:
            severity = "High Severity"
        else:
            severity = "Very High Severity"

        return total_score, severity







    def wemwbs_evaluation(self, ans):
            # Your existing code for evaluating the WEMWBS
            total_score = 0

            for question_id, answer in ans.items():
                total_score += (answer - 1)  # Make sure answers are converted to numerical values

            # Provide an inference based on the score
            if total_score <= 28:
                inference = "Low well-being: You may be experiencing low levels of well-being. It could be helpful to seek support or engage in activities that promote positive mental health."
            elif 29 <= total_score <= 42:
                inference = "Moderate well-being: Your well-being is average. Consider exploring ways to improve your mental health through self-care or professional guidance."
            elif 43 <= total_score <= 56:
                inference = "Good well-being: You are experiencing good levels of well-being. Continue engaging in activities that support your mental and emotional health."
            elif total_score > 56:
                inference = "Excellent well-being: You have high well-being. Keep up the great work maintaining a positive outlook and engaging in healthy practices."

            return total_score, inference



def get_inference(test:str,ans):
    try:
        testing = Tests()
        logging.info("Test Inference Started")
        logging.info("Test:",test,"Ans",ans) 
        if(test == "Patient Health Questionnaire (PHQ-9)"):
            return testing.phq9(ans)
        elif (test == "Mood Disorder Questionnaire (MDQ)"):
            return testing.mdq(ans)
        elif (test == "Generalized Anxiety Disorder 7 (GAD-7)"):
            return testing.gad7(ans)
        elif(test == "Liebowitz Social Anxiety Scale (LSAS)"):
            return testing.evaluate_lsas_responses(ans)
        elif (test == "PTSD Checklist for DSM-5 (PCL-5)"):
            return testing.pcl5_evaluation(ans)
        elif (test == "Yale-Brown Obsessive-Compulsive Scale (Y-BOCS)"):
            return testing.y_bocs_evaluation(ans)
        elif (test == "McLean Screening Instrument for Borderline Personality Disorder (MSI-BPD)"):
            return testing.evaluate_msi_bpd(ans)
        elif (test == "Eating Attitudes Test (EAT-26)"):
            return testing.eat_26_evaluation(ans)    
        elif (test == "Alcohol Use Disorders Identification Test (AUDIT)"):
            return testing.audit_evaluation(ans)
        elif (test == "Drug Abuse Screening Test (DAST-10)"):
            return testing.dast10_evaluation(ans)
        elif (test == "Positive and Negative Syndrome Scale (PANSS - Shortened Version)"):
            return testing.panss_evaluation(ans)
        elif (test == "Autism Spectrum Rating Scales (ASRS - Short Version)"):
            return testing.asrs_evaluation(ans)
        elif (test == "Warwick-Edinburgh Mental Well-being Scale (WEMWBS)"):
            return testing.wemwbs_evaluation(ans)
        else:
            return (0,"Evaluation not available as for now !, Please evaluate yourself on test from outer sources")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise CustomException(e, sys)


        
'''


# For testing purpose 
if __name__ == "__main__":
    logging.info("Logger working ")
    test = {
    "Q1": 2,
    "Q2": 1,
    "Q3": 1,
    "Q4": 1,
    "Q5": 1,
    "Q6": 3,
    "Q7": 1,
    "Q8": 2,
    "Q9": 1,
    "Q10": 1,
    # "Q11": 0,
    # "Q12": 0,
    # "Q13": 1,
    # "Q14": 2
  }
    ans = get_inference("Positive and Negative Syndrome Scale (PANSS - Shortened Version)",test)
    print(ans)

'''

'''
Notes for the developer:
1. Answers are in format {question_id: answer} where answer is an integer(1,2,3,4..).

'''

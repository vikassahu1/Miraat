from core_logic.Data.schemas import TestRequest,TestAndAnswer
from typing import Dict, Tuple, Any, Optional
from core_logic.Accessories.exception import CustomException
import sys
from core_logic.Accessories.logger import logging



#We are getting test and ans dict[str,str] form 
class Tests:
    def __init__(self):
        logging.info("Tests class initialized")

    def phq9(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """Evaluate PHQ-9 depression screening test"""
        try:
            logging.info(f"PHQ-9 evaluation started with {len(ans)} answers")
            score = 0
            for question_id, answer in ans.items():
                score += (answer-1)
                logging.debug(f"PHQ-9 Q{question_id}: {answer}, running score: {score}")
            
            if score>=1 and score<=4:
                inference = "Minimal symptoms"
            elif score>=5 and score<=9:
                inference = "Mild symptoms"
            elif score>=10 and score<=14:
                inference = "Moderate symptoms"
            elif score>=15 and score<=19:
                inference = "Moderately severe symptoms"
            elif score>=20 and score<=27:
                inference = "Severe symptoms"
            else:
                inference = "Score outside expected range"
                
            logging.info(f"PHQ-9 evaluation complete. Score: {score}, Inference: {inference}")
            return score, inference
        except Exception as e:
            logging.error(f"Error in PHQ-9 evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"



    def mdq(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """Evaluate Mood Disorder Questionnaire"""
        try:
            logging.info(f"MDQ evaluation started with {len(ans)} answers")
            counter = 1
            score = 0
            one, two = False, False
            
            for question_id, answer in ans.items():
                logging.debug(f"MDQ Q{question_id}: {answer}")
                if counter <= 13 and answer == 1:
                    score += 1
                elif counter == 14 and answer == 1 and score >= 7:
                    one = True
                    logging.debug("MDQ criterion one met")
                elif counter == 15 and answer >= 1:
                    two = True
                    logging.debug("MDQ criterion two met")
                counter += 1

            if one and two:
                inference = "Result suggest illness"
            else:
                inference = "Result suggest no illness"
            
            logging.info(f"MDQ evaluation complete. Score: {score}, Inference: {inference}")
            return score, inference
        except Exception as e:
            logging.error(f"Error in MDQ evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"
        





    def gad7(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """Evaluate Generalized Anxiety Disorder-7 screening test"""
        try:
            logging.info(f"GAD-7 evaluation started with {len(ans)} answers")
            score = 0
            # Calculate the total score by summing up answers
            for question_id, answer in ans.items():
                adjusted_score = answer - 1  # Adjusting as per scoring (0-based)
                score += adjusted_score
                logging.debug(f"GAD-7 Q{question_id}: {answer} (adjusted: {adjusted_score}), running score: {score}")

            # Determine anxiety severity based on total score
            if score >= 0 and score <= 4:
                inference = "Minimal anxiety"
            elif score >= 5 and score <= 9:
                inference = "Mild anxiety"
            elif score >= 10 and score <= 14:
                inference = "Moderate anxiety"
            elif score >= 15 and score <= 21:
                inference = "Severe anxiety"
            else:
                inference = "Score outside expected range"
            
            logging.info(f"GAD-7 evaluation complete. Score: {score}, Inference: {inference}")
            return score, inference
        except Exception as e:
            logging.error(f"Error in GAD-7 evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"




    

    def pcl5_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluates the PCL-5 score based on the provided answers.
        Args:
            ans (dict): A dictionary where keys are question IDs and values are selected option IDs (1 to 5).
        Returns:
            tuple: A tuple containing the total score and the symptom severity description.
        """
        try:
            logging.info(f"PCL-5 evaluation started with {len(ans)} answers")
            total_score = 0

            # Calculate total score by summing option_id values for each question
            for question_id, answer in ans.items():
                adjusted_score = answer - 1  # Adjustment for 0-4 scale
                total_score += adjusted_score
                logging.debug(f"PCL-5 Q{question_id}: {answer} (adjusted: {adjusted_score}), running score: {total_score}")

            # Determine symptom severity based on the clinical cutoff of 33
            if total_score >= 33:
                symptom_severity = "High PTSD Symptoms"
            else:
                symptom_severity = "Low PTSD Symptoms"

            logging.info(f"PCL-5 evaluation complete. Score: {total_score}, Inference: {symptom_severity}")
            return total_score, symptom_severity
        except Exception as e:
            logging.error(f"Error in PCL-5 evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"


        


    def y_bocs_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluates the Y-BOCS score for obsessive-compulsive symptoms.
        Args:
            ans (dict): A dictionary where keys are question IDs and values are selected option IDs.
        Returns:
            tuple: A tuple containing the total score and severity description.
        """
        try:
            logging.info(f"Y-BOCS evaluation started with {len(ans)} answers")
            total_score = 0
            
            for question_id, answer in ans.items():
                adjusted_score = answer - 1
                total_score += adjusted_score
                logging.debug(f"Y-BOCS Q{question_id}: {answer} (adjusted: {adjusted_score}), running score: {total_score}")

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

            logging.info(f"Y-BOCS evaluation complete. Score: {total_score}, Inference: {severity}")
            return total_score, severity
        except Exception as e:
            logging.error(f"Error in Y-BOCS evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"





    def evaluate_lsas_responses(self, responses: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate LSAS questionnaire responses.

        Parameters:
        - responses: A dictionary where keys are question IDs and values are selected option IDs.

        Returns:
        - A tuple containing total score and evaluation string.
        """
        try:
            logging.info(f"LSAS evaluation started with {len(responses)} answers")
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
            for question_id, answer in responses.items():
                adjusted_score = answer - 1
                total_score += adjusted_score
                logging.debug(f"LSAS Q{question_id}: {answer} (adjusted: {adjusted_score}), running score: {total_score}")

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

            logging.info(f"LSAS evaluation complete. Score: {total_score}, Inference: {evaluation}")
            return total_score, evaluation
        except Exception as e:
            logging.error(f"Error in LSAS evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"


            





    def evaluate_msi_bpd(self, responses: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluates the McLean Screening Instrument for Borderline Personality Disorder (MSI-BPD).
        
        Args:
            responses (dict): A dictionary where the key is the question_id (1-10), and the value is the option_id (1 for "No", 2 for "Yes").
        
        Returns:
            tuple: A tuple containing the total score and a professional assessment of the result.
        """
        try:
            logging.info(f"MSI-BPD evaluation started with {len(responses)} answers")
            # Scoring: Yes (option_id 2) is 1 point, No (option_id 1) is 0 points.
            score = 0
            for question_id, answer in responses.items():
                point = 1 if answer == 2 else 0
                score += point
                logging.debug(f"MSI-BPD Q{question_id}: {answer} (point: {point}), running score: {score}")
            
            # Threshold for clinical concern: Usually 7 or higher is indicative of possible BPD.
            threshold = 7
            
            # Assessment based on the score
            if score >= threshold:
                assessment = "The respondent's score is indicative of a potential Borderline Personality Disorder (BPD). \nFurther clinical evaluation by a mental health professional is recommended."
            else:
                assessment = "The respondent's score does not suggest significant concerns related to Borderline Personality Disorder (BPD).\nHowever, this is a screening tool and not a diagnostic measure. If there are concerns, consulting a mental health professional is advised."
            
            logging.info(f"MSI-BPD evaluation complete. Score: {score}, Inference: {assessment[:30]}...")
            return score, assessment
        except Exception as e:
            logging.error(f"Error in MSI-BPD evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"








    def eat_26_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate EAT-26 scores based on the standard criteria.

        Parameters:
            ans (dict): A dictionary where keys are question IDs and values are user responses (1–6 scale).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the level of concern.
        """
        try:
            logging.info(f"EAT-26 evaluation started with {len(ans)} answers")
            total_score = 0

            # Calculate the total score
            for question_id, answer in ans.items():
                # Subtract 1 because EAT-26 scoring starts from 0 for "Never"
                adjusted_score = answer - 1
                total_score += adjusted_score
                logging.debug(f"EAT-26 Q{question_id}: {answer} (adjusted: {adjusted_score}), running score: {total_score}")

            # Determine the severity level
            if total_score < 20:
                severity = "No clinical concern (Normal)"
            else:
                severity = "Clinical concern (Further evaluation recommended)"

            logging.info(f"EAT-26 evaluation complete. Score: {total_score}, Inference: {severity}")
            return total_score, severity
        except Exception as e:
            logging.error(f"Error in EAT-26 evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"









    def audit_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate AUDIT scores based on standard criteria with options starting from 1.

        Parameters:
            ans (dict): A dictionary where keys are question IDs (1-10) and values are user responses (option IDs 1, 2, ...).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the risk category.
        """
        try:
            logging.info(f"AUDIT evaluation started with {len(ans)} answers")
            total_score = 0

            # Score questions 1-8 (options range from 1-5, adjusted to 0-4 by subtracting 1)
            for question_id in range(1, 9):
                if question_id in ans:
                    adjusted_score = ans[question_id] - 1
                    total_score += adjusted_score
                    logging.debug(f"AUDIT Q{question_id}: {ans[question_id]} (adjusted: {adjusted_score}), running score: {total_score}")
                else:
                    logging.warning(f"AUDIT Q{question_id} missing from answers")

            # Score questions 9-10 (options range from 1-3, adjusted to 0-2 by subtracting 1)
            for question_id in range(9, 11):
                if question_id in ans:
                    adjusted_score = ans[question_id] - 1
                    total_score += adjusted_score
                    logging.debug(f"AUDIT Q{question_id}: {ans[question_id]} (adjusted: {adjusted_score}), running score: {total_score}")
                else:
                    logging.warning(f"AUDIT Q{question_id} missing from answers")

            # Determine risk category
            if total_score < 10:
                severity = "Low Risk or Abstinence"
            elif 10 <= total_score <= 16:
                severity = "Low Risk"
            elif 17 <= total_score <= 24:
                severity = "Hazardous Drinking"
            elif 25 <= total_score <= 32:
                severity = "Harmful Drinking"
            elif total_score >= 33:
                severity = "Likely Alcohol Dependence"
            else:
                severity = "Invalid score"

            logging.info(f"AUDIT evaluation complete. Score: {total_score}, Inference: {severity}")
            return total_score, severity
        except Exception as e:
            logging.error(f"Error in AUDIT evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"








    def dast10_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate DAST-10 scores based on answers valued 1 (No) and 2 (Yes).
        
        Parameters:
            ans (dict): A dictionary where keys are question IDs (1-10) and values are user responses (1 or 2).
            
        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the risk category.
        """
        try:
            logging.info(f"DAST-10 evaluation started with {len(ans)} answers")
            total_score = 0

            # Score questions 1-10
            for question_id, answer in ans.items():
                total_score += answer
                logging.debug(f"DAST-10 Q{question_id}: {answer}, running score: {total_score}")

            # Determine risk category based on total score
            if total_score < 10:
                severity = "No Risk"
            elif 10 <= total_score <= 14:
                severity = "Low Risk"
            elif 15 <= total_score <= 19:
                severity = "Moderate Risk"
            elif 20 <= total_score <= 24:
                severity = "High Risk"
            elif 25 <= total_score <= 40:
                severity = "Severe Risk"
            else:
                severity = "Invalid score"

            logging.info(f"DAST-10 evaluation complete. Score: {total_score}, Inference: {severity}")
            return total_score, severity
        except Exception as e:
            logging.error(f"Error in DAST-10 evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"








    def panss_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate PANSS scores based on user responses for 10 questions.

        Parameters:
            ans (dict): A dictionary where keys are question IDs (1-10) and values are user responses (option IDs 1-7).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the severity category.
        """
        try:
            logging.info(f"PANSS evaluation started with {len(ans)} answers")
            total_score = 0

            # Score questions 1-10, options range from 1-7
            for question_id, answer in ans.items():
                total_score += answer
                logging.debug(f"PANSS Q{question_id}: {answer}, running score: {total_score}")
                
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

            logging.info(f"PANSS evaluation complete. Score: {total_score}, Inference: {severity}")
            return total_score, severity
        except Exception as e:
            logging.error(f"Error in PANSS evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"









    def asrs_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate ASRS (Autism Spectrum Rating Scale) scores based on user responses.

        Parameters:
            ans (dict): A dictionary where keys are question IDs (SC1, SC2, ..., ER3) and values are user responses (option IDs 1-4).

        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the severity category.
        """
        try:
            logging.info(f"ASRS evaluation started with {len(ans)} answers")
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
                    logging.debug(f"ASRS {question_id}: {ans[question_id]}, running score: {total_score}")
                else:
                    logging.warning(f"ASRS {question_id} missing from answers")

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

            logging.info(f"ASRS evaluation complete. Score: {total_score}, Inference: {severity}")
            return total_score, severity
        except Exception as e:
            logging.error(f"Error in ASRS evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"







    def wemwbs_evaluation(self, ans: Dict[str, int]) -> Tuple[int, str]:
        """
        Evaluate WEMWBS (Warwick-Edinburgh Mental Well-being Scale) scores.
        
        Parameters:
            ans (dict): A dictionary where keys are question IDs and values are user responses.
            
        Returns:
            tuple: A tuple containing the total score (int) and a string indicating the well-being category.
        """
        try:
            logging.info(f"WEMWBS evaluation started with {len(ans)} answers")
            total_score = 0

            for question_id, answer in ans.items():
                adjusted_score = answer - 1  # Make sure answers are converted to numerical values
                total_score += adjusted_score
                logging.debug(f"WEMWBS Q{question_id}: {answer} (adjusted: {adjusted_score}), running score: {total_score}")

            # Provide an inference based on the score
            if total_score <= 28:
                inference = "Low well-being: You may be experiencing low levels of well-being. It could be helpful to seek support or engage in activities that promote positive mental health."
            elif 29 <= total_score <= 42:
                inference = "Moderate well-being: Your well-being is average. Consider exploring ways to improve your mental health through self-care or professional guidance."
            elif 43 <= total_score <= 56:
                inference = "Good well-being: You are experiencing good levels of well-being. Continue engaging in activities that support your mental and emotional health."
            elif total_score > 56:
                inference = "Excellent well-being: You have high well-being. Keep up the great work maintaining a positive outlook and engaging in healthy practices."
            else:
                inference = "Score outside expected range"

            logging.info(f"WEMWBS evaluation complete. Score: {total_score}, Inference: {inference[:30]}...")
            return total_score, inference
        except Exception as e:
            logging.error(f"Error in WEMWBS evaluation: {str(e)}")
            return 0, "Error in evaluation, please consult a healthcare professional"



def get_inference(test: str, ans: Dict[str, int]) -> Tuple[int, str]:
    """
    Main function to evaluate a test based on the provided answers.
    
    Args:
        test (str): The name of the test to be evaluated.
        ans (Dict[str, int]): A dictionary of answers where keys are question IDs and values are responses.
        
    Returns:
        Tuple[int, str]: A tuple containing the score and an inference/interpretation.
    """
    try:
        testing = Tests()
        logging.info(f"Test Inference Started for: {test}")
        logging.info(f"Answer data received: {len(ans)} responses")
        
        if not ans:
            logging.error("No answers provided for evaluation")
            return 0, "Error: No answers provided for evaluation"
            
        if test == "Patient Health Questionnaire (PHQ-9)":
            result = testing.phq9(ans)
        elif test == "Mood Disorder Questionnaire (MDQ)":
            result = testing.mdq(ans)
        elif test == "Generalized Anxiety Disorder 7 (GAD-7)":
            result = testing.gad7(ans)
        elif test == "Liebowitz Social Anxiety Scale (LSAS)":
            result = testing.evaluate_lsas_responses(ans)
        elif test == "PTSD Checklist for DSM-5 (PCL-5)":
            result = testing.pcl5_evaluation(ans)
        elif test == "Yale-Brown Obsessive-Compulsive Scale (Y-BOCS)":
            result = testing.y_bocs_evaluation(ans)
        elif test == "McLean Screening Instrument for Borderline Personality Disorder (MSI-BPD)":
            result = testing.evaluate_msi_bpd(ans)
        elif test == "Eating Attitudes Test (EAT-26)":
            result = testing.eat_26_evaluation(ans)    
        elif test == "Alcohol Use Disorders Identification Test (AUDIT)":
            result = testing.audit_evaluation(ans)
        elif test == "Drug Abuse Screening Test (DAST-10)":
            result = testing.dast10_evaluation(ans)
        elif test == "Positive and Negative Syndrome Scale (PANSS - Shortened Version)":
            result = testing.panss_evaluation(ans)
        elif test == "Autism Spectrum Rating Scales (ASRS - Short Version)":
            result = testing.asrs_evaluation(ans)
        elif test == "Warwick-Edinburgh Mental Well-being Scale (WEMWBS)":
            result = testing.wemwbs_evaluation(ans)
        else:
            logging.warning(f"Unknown test type requested: {test}")
            result = (0, "Evaluation not available as for now! Please evaluate yourself on test from outer sources")
        
        logging.info(f"Test Inference Completed for {test}. Score: {result[0]}, Inference: {result[1][:30]}...")
        return result
    except Exception as e:
        logging.error(f"Critical error in get_inference: {str(e)}")
        # Return a safe fallback rather than raising an exception
        return 0, "Error in evaluation. Please consult a healthcare professional."


        


# For testing purpose 
if __name__ == "__main__":
    logging.info("Logger working - Starting comprehensive test of all assessment functions")

    test_data =  {'1': 2, '2': 4, '3': 2, '4': 2, '5': 2, '6': 3, '7': 2, '8': 2, '9': 2, '10': 2, '11': 3, '12': 4, '13': 3, '14': 3, '15': 2, '16': 2, '17': 2, '18': 2, '19': 1, '20': 1, '21': 2, '22': 3, '23': 3, '24': 3}
    test_name = "Liebowitz Social Anxiety Scale (LSAS)"
    try:
        score, interpretation = get_inference(test_name, test_data)
        print(f"Test: {test_name}, Score: {score}, Interpretation: {interpretation}")
    except Exception as e:
        logging.error(f"Error during testing: {str(e)}")



    exit()
    
    # Create test data for each assessment
    test_data = {
        "Patient Health Questionnaire (PHQ-9)": {
            1: 2,  # Several days
            2: 3,  # More than half the days
            3: 3,  # More than half the days
            4: 2,  # Several days
            5: 2,  # Several days
            6: 3,  # More than half the days
            7: 2,  # Several days
            8: 1,  # Several days
            9: 1   # Several days
        },
        "Mood Disorder Questionnaire (MDQ)": {
            1: 1,  # Yes
            2: 1,  # Yes
            3: 1,  # Yes
            4: 1,  # Yes
            5: 1,  # Yes
            6: 1,  # Yes
            7: 1,  # Yes
            8: 1,  # Yes
            9: 0,  # No
            10: 0,  # No
            11: 0,  # No
            12: 0,  # No
            13: 0,  # No
            14: 1,  # Yes
            15: 2   # Yes, moderately
        },
        "Generalized Anxiety Disorder 7 (GAD-7)": {
            1: 3,  # Nearly every day
            2: 2,  # More than half the days
            3: 3,  # Nearly every day
            4: 2,  # More than half the days
            5: 2,  # More than half the days
            6: 2,  # More than half the days
            7: 1   # Several days
        },



        "Liebowitz Social Anxiety Scale (LSAS)": {'1': 2, '2': 4, '3': 2, '4': 2, '5': 2, '6': 3, '7': 2, '8': 2, '9': 2, '10': 2, '11': 3, '12': 4, '13': 3, '14': 3, '15': 2, '16': 2, '17': 2, '18': 2, '19': 1, '20': 1, '21': 2, '22': 3, '23': 3, '24': 3},





        "PTSD Checklist for DSM-5 (PCL-5)": {
            # 20 PCL-5 questions
            1: 4,  # Extremely
            2: 3,  # Quite a bit
            3: 4,  # Extremely
            4: 3,  # Quite a bit
            5: 4,  # Extremely
            6: 3,  # Quite a bit
            7: 3,  # Quite a bit
            8: 2,  # Moderately
            9: 4,  # Extremely
            10: 3,  # Quite a bit
            11: 4,  # Extremely
            12: 3,  # Quite a bit
            13: 4,  # Extremely
            14: 3,  # Quite a bit
            15: 2,  # Moderately
            16: 3,  # Quite a bit
            17: 2,  # Moderately
            18: 3,  # Quite a bit
            19: 4,  # Extremely
            20: 3   # Quite a bit
        },
        "Yale-Brown Obsessive-Compulsive Scale (Y-BOCS)": {
            1: 3,  # Moderate
            2: 4,  # Severe
            3: 3,  # Moderate
            4: 2,  # Mild
            5: 3,  # Moderate
            6: 4,  # Severe
            7: 3,  # Moderate
            8: 3,  # Moderate
            9: 4,  # Severe
            10: 3   # Moderate
        },
        "McLean Screening Instrument for Borderline Personality Disorder (MSI-BPD)": {
            1: 2,  # Yes
            2: 2,  # Yes
            3: 2,  # Yes
            4: 2,  # Yes
            5: 2,  # Yes
            6: 2,  # Yes
            7: 2,  # Yes
            8: 1,  # No
            9: 1,  # No
            10: 1   # No
        },
        "Eating Attitudes Test (EAT-26)": {
            # 26 EAT-26 questions
            1: 4,  # Often
            2: 3,  # Sometimes
            3: 5,  # Usually
            4: 2,  # Rarely
            5: 3,  # Sometimes
            6: 4,  # Often
            7: 3,  # Sometimes
            8: 4,  # Often
            9: 2,  # Rarely
            10: 3,  # Sometimes
            11: 4,  # Often
            12: 3,  # Sometimes
            13: 2,  # Rarely
            14: 1,  # Never
            15: 3,  # Sometimes
            16: 2,  # Rarely
            17: 3,  # Sometimes
            18: 4,  # Often
            19: 5,  # Usually
            20: 3,  # Sometimes
            21: 2,  # Rarely
            22: 3,  # Sometimes
            23: 4,  # Often
            24: 3,  # Sometimes
            25: 2,  # Rarely
            26: 3   # Sometimes
        },
        "Alcohol Use Disorders Identification Test (AUDIT)": {
            1: 3,  # 2-3 times a week
            2: 2,  # 3-4 drinks
            3: 3,  # 5-6 drinks
            4: 2,  # Monthly
            5: 2,  # Monthly
            6: 2,  # Monthly
            7: 2,  # Monthly
            8: 1,  # Less than monthly
            9: 1,  # Yes, but not in the last year
            10: 2   # Yes, during the last year
        },
        "Drug Abuse Screening Test (DAST-10)": {
            1: 2,  # Yes
            2: 1,  # No
            3: 2,  # Yes
            4: 1,  # No
            5: 2,  # Yes
            6: 1,  # No
            7: 2,  # Yes
            8: 1,  # No
            9: 2,  # Yes
            10: 1   # No
        },
        "Positive and Negative Syndrome Scale (PANSS - Shortened Version)": {
            1: 3,  # Moderate
            2: 4,  # Moderately severe
            3: 3,  # Moderate
            4: 2,  # Minimal
            5: 3,  # Moderate
            6: 2,  # Minimal
            7: 4,  # Moderately severe
            8: 3,  # Moderate
            9: 3,  # Moderate
            10: 2   # Minimal
        },
        "Autism Spectrum Rating Scales (ASRS - Short Version)": {
            "SC1": 3,  # Often
            "SC2": 2,  # Sometimes
            "SC3": 3,  # Often
            "RRB1": 2,  # Sometimes
            "RRB2": 3,  # Often
            "RRB3": 2,  # Sometimes
            "ER1": 3,  # Often
            "ER2": 2,  # Sometimes
            "ER3": 3   # Often
        },
        "Warwick-Edinburgh Mental Well-being Scale (WEMWBS)": {
            1: 4,  # Often
            2: 3,  # Some of the time
            3: 3,  # Some of the time
            4: 4,  # Often
            5: 3,  # Some of the time
            6: 4,  # Often
            7: 3,  # Some of the time
            8: 2,  # Rarely
            9: 3,  # Some of the time
            10: 4,  # Often
            11: 3,  # Some of the time
            12: 4,  # Often
            13: 3,  # Some of the time
            14: 4   # Often
        }
    }
    
    # Test each assessment function and print results
    print("\n===== COMPREHENSIVE ASSESSMENT TEST RESULTS =====\n")
    
    for test_name, answers in test_data.items():
        try:
            result = get_inference(test_name, answers)
            print(f"\n{test_name}:")
            print(f"  Score: {result[0]}")
            print(f"  Inference: {result[1]}")
            print(f"  Raw data: {answers}")
            print("-" * 70)
        except Exception as e:
            print(f"\n{test_name}: ERROR - {str(e)}")
            print("-" * 70)
    
    # Test edge cases
    print("\n===== EDGE CASE TESTS =====\n")
    
    # Empty data test
    empty_test = {}
    for test_name in ["Patient Health Questionnaire (PHQ-9)", "Generalized Anxiety Disorder 7 (GAD-7)"]:
        empty_result = get_inference(test_name, empty_test)
        print(f"{test_name} (Empty Input):")
        print(f"  Score: {empty_result[0]}")
        print(f"  Inference: {empty_result[1]}")
        print("-" * 70)
    
    # Invalid test name
    invalid_test = get_inference("Non-existent Test", {1: 2, 2: 3})
    print(f"Invalid Test Name:")
    print(f"  Score: {invalid_test[0]}")
    print(f"  Inference: {invalid_test[1]}")
    print("-" * 70)
    
    print("\nAll tests completed.")

'''
Notes for the developer:
1. Answers are in format {question_id: answer} where answer is an integer(1,2,3,4..).
2. Each assessment function now includes comprehensive error handling and logging.
3. All functions consistently return a (score, inference) tuple even in error cases.
4. Debug logs provide detailed tracking of scores for each question.
5. Type hints improve code readability and maintainability.
'''

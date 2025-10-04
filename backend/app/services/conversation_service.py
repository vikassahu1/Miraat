from core_logic.LLM.llm_endpoint import llm
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging
from core_logic.Accessories.logger import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from app.services.config import BROAD_CATERGORY_THRESHOLD, SUBCATEGORY_THRESHOLD


from app.services.schemas import Verdict, QuestionGenerationPlan
import os
import json
import sys


class ConversationService:
    def __init__(self, knowledge_base: dict):
        self.knowledge_base = knowledge_base
        try:
            self.llm_client = llm
            self.parser = PydanticOutputParser(pydantic_object=Verdict)
            self.structured_llm_verdict = self.llm_client.with_structured_output(Verdict)
            self.structured_llm_plan = self.llm_client.with_structured_output(QuestionGenerationPlan) 
            logging.info("ConversationService: Gemini LLM client initialized.")
        except Exception:
            self.llm_client = None
            self.parser = None
            self.structured_llm_verdict = None
            self.structured_llm_plan = None
            logging.info("ConversationService: Could not initialize Gemini LLM client.")


    def _make_llm_call(self, system_prompt: str, user_prompt: str) -> str:
        if not self.llm_client:
            return "Error: LLM not available."
        try:
            # Compose the prompt for Gemini
            prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.llm_client.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM call failed: {e}")
            logging.error(f"Error occurred: {e}")
            raise CustomException(e, sys)



    def generate_probing_question(self, initial_text: str) -> str:
        """
        Generates a simple, open-ended question to encourage the user to elaborate.
        This is the first step in the priming conversation.
        """
        system_prompt = (
            "You are an empathetic AI assistant. A user has just shared their initial feeling. "
            "Your ONLY job is to ask one simple, open-ended question to encourage them to elaborate on the IMPACT this feeling is having on their daily life. "
            "Do not give advice. Do not analyze. "
            "Ask the question directly, but make it warm, and empathetic. "
            "NOTE: Some words in the text will appear in square brackets like [this]; these are placeholders for sensitive information that has been redacted for privacy. Do not ask about or reference these placeholders."
            "VERY CRITICAL:Also even if by accidently the text contains PII information like Names, Phone numbers, Emails, Credit Card numbers etc, do not ask about or reference these details. NEVER USE THESE INFO IN REPLY ANYHOW (Person Names, Phone numbers, Emails, Credit Card numbers)"
        )
        user_prompt = f"User's initial feeling: \"{initial_text}\"\n\nGenerate the probing question:"
        
        fallback_question = "Thank you for sharing. Could you tell me a bit more about how this has been affecting your day-to-day life?"
        
        try:
            question = self._make_llm_call(system_prompt, user_prompt)
            logging.info(f"LLM generated probing question: {question}")
            # Basic cleanup of the LLM output
            return question.strip().strip('"') if question and "Error" not in question else fallback_question
        except Exception:
            return fallback_question



    def _get_description(self, category: str) -> str:
        description = self.knowledge_base.get(category)
        if not description:
            raise Exception(f"Trying to get discription of Category: '{category}' not found in knowledge base.")
        return description['description']


    def _get_subcategory_description(self, subcategory: str, broad_category: str) -> str:
        category_info = self.knowledge_base.get(broad_category)
        if not category_info:
            raise Exception(f"Trying to get subcategory '{subcategory}' of Broad Category '{broad_category}' not found in knowledge base.")
        subcat_info = category_info.get('Subcategories', {}).get(subcategory)
        if not subcat_info:
            raise Exception(f"Trying to get discription of Subcategory: '{subcategory}' not found in knowledge base under Broad Category '{broad_category}'.")
        return subcat_info['description']




    def _get_subcategories(self, category: str) -> list:
        category_info = self.knowledge_base.get(category)
        if not category_info:
            raise Exception(f"Trying to get subcategories of Category '{category}' not found in knowledge base.")
        return list(category_info.get('Subcategories', {}).keys())
    



    def evaluate_user_answer(self, session_data: dict) -> dict:
        if not self.llm_client or not self.parser:
            print("ERROR: LLM or Parser not available for evaluation.")
            return {}

        # Get the belief and conversation history from the session data 
        belief_state = session_data.get('belief_state') or {}
        conversation_history = session_data.get('conversation_history', [])
        
        # TODO: If belief is more less than 2 
        if len(belief_state) < 1 or len(conversation_history) < 2: return {}

        candidates = list(belief_state.keys())
        last_question = next((turn['content'] for turn in reversed(conversation_history) if turn['role'] == 'assistant'), None)
        last_answer = conversation_history[-1]['content']
        current_status = session_data.get('status')

        if not last_question: return {}

        context_definitions = ""

        if current_status == "refining_sub":
            broad_category  = session_data.get('final_category')
            for subcat in candidates:
                description = self._get_subcategory_description(subcat,broad_category)
                context_definitions += f"Possibility: '{subcat}'\nDescription: \"{description}\"\n\n"
        else:
            for category in candidates:
                description = self._get_description(category)
                context_definitions += f"Possibility: '{category}'\nDescription: \"{description}\"\n\n"

        # --- The Prompt now explicitly includes formatting instructions from the parser ---
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a logical analyst. Your task is to determine which of several possibilities a user's statement supports. "
             "You must provide your answer in the specified JSON format.\n"
             "{format_instructions}"), # <-- The magic instruction is injected here
            ("human", 
             "Analyze the conversation and context below. Then, format your response according to the instructions.\n\n"
             "---CONTEXT---\n{definitions}\n\n"
             "---CONVERSATION---\n"
             "Question Asked: \"{question}\"\n"
             "User's Answer: \"{answer}\"")
        ])
        
        # The chain now pipes the LLM output directly into the parser
        chain = prompt | self.llm_client | self.parser

        try:
            print("Invoking LangChain PydanticOutputParser chain...")
            # The parser gets the format instructions and injects them into the prompt
            verdict_object: Verdict = chain.invoke({
                "definitions": context_definitions,
                "question": last_question,
                "answer": last_answer,
                "format_instructions": self.parser.get_format_instructions(),
            })
            
            print(f"LangChain evaluation successful. Verdict: {verdict_object.model_dump()}")
            return verdict_object.model_dump()

        except Exception as e:
            # This will catch LangChain's OutputParserException if Gemini still fails
            print(f"LangChain evaluation with parser failed: {e}")
            return {}






    def update_belief_state(self, session_data: dict, evaluation: dict) -> dict:

        # Extracted data from the evaluated verdict 
        supported_category = evaluation.get("supported_category")
        confidence = evaluation.get("confidence_score", 0.5) # Default to neutral confidence
        current_candidates = session_data.get('belief_state') or {}

        # Validate that the returned category is one we are actually considering
        if not supported_category or supported_category not in current_candidates:
            print(f"Warning: Evaluation returned a category not in the current belief state: {supported_category}")
            return session_data # Make no changes if the verdict is invalid

        new_scores = {}
        # Apply a weighted update. A higher confidence verdict has a stronger effect.

        #  TODO: Need to tune these multipliers based on real-world testing.
        for category, score in current_candidates.items():
            if category == supported_category:
                # Boost the winner
                new_scores[category] = score * (1 + confidence) 
            else:
                # Penalize the losers, but less harshly
                new_scores[category] = score * (1 - (confidence * 0.5))

        # Normalize the scores so they sum to 1.0
        total_new_score = sum(new_scores.values())
        if total_new_score > 0:
            normalized_scores = {cat: score / total_new_score for cat, score in new_scores.items()}
            session_data['belief_state'] = dict(sorted(
                normalized_scores.items(), key=lambda item: item[1], reverse=True
            ))
        
        reasoning = evaluation.get('reasoning', 'No reasoning provided.')
        print(f"Belief State Updated. Reason: '{reasoning}'. New Belief: {session_data['belief_state']}")
        
        return session_data

    def check_funnel_completion(self, session_data: dict) -> str | None:
        candidates = session_data.get('belief_state') or {}
        status = session_data.get('status') 

        if not candidates:
            logging.info("No candidates in belief state.")
            return None

        sorted_candidates = list(candidates.items())
        top_candidate_name, top_candidate_score = sorted_candidates[0]
        
        if (
            (status == "refining_broad" and top_candidate_score >= BROAD_CATERGORY_THRESHOLD) or
            (status == "refining_sub" and top_candidate_score >= SUBCATEGORY_THRESHOLD)
        ):
            return top_candidate_name

        return None

    def generate_differentiating_question(self, session_data: dict) -> str:
        """
        "CHAIN OF THOUGHT" IMPLEMENTATION: The heart of the diagnostic funnel.
        Forces the LLM to first reason about a strategy and then generate a question,
        ensuring the highest possible relevance and accuracy.
        """
        logging.info(f"1. Session Data for Question Generation: {session_data}")
        

        # --- 1. Extract Context ---
        belief_state = session_data.get('belief_state') or {}
        conversation_history = session_data.get('conversation_history', [])
        current_status = session_data.get('status')
        
        # We may proceed to render test for final assessment if just one
        if not belief_state or len(belief_state) < 2:
            return "Thank you for your responses. Let's move on to the final part of the assessment."

        # Top 2 candidates
        top_candidates = sorted(belief_state.keys(), key=lambda k: belief_state[k], reverse=True)[:2]
        
        #* FOR BROAD CATEGORY: Preparing the context definitions (Disorder : Discription) of disorder for the prompt 
        context_definitions = ""
        if current_status == "refining_sub":
            broad_category  = session_data.get('final_category')
            for subcat in top_candidates:
                description = self._get_subcategory_description(subcat,broad_category)
                context_definitions += f"Theme: '{subcat}'\nDescription: \"{description}\"\n\n"
        else:
            for category in top_candidates:
                description = self._get_description(category)
                context_definitions += f"Theme: '{category}'\nDescription: \"{description}\"\n\n"
        
        # Preparing the formatted conversation for the prompt
        formatted_history = ""
        recent_turns = conversation_history[-6:] # Use more history for better context
        for turn in recent_turns:
            role = "User" if turn.get('role') == 'user' else "AI Assistant"
            content = turn.get('content', '')
            formatted_history += f"{role}: {content}\n"

        # --- 2. The Chain of Thought Prompt & Structured Output ---
        # Make sure you have self.structured_llm_plan = self.llm.with_structured_output(QuestionGenerationPlan)
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a master clinical intake strategist. Your goal is to determine the most effective question to ask next to clarify a user's situation. "
             "You will first form an internal 'reasoning' of what to probe, and then formulate the question. "
             "Your response MUST use the 'QuestionGenerationPlan' tool."),
            ("human",
             "---CONVERSATION HISTORY---\n{history}\n\n"
             "---CANDIDATE THEMES TO DIFFERENTIATE---\n{definitions}\n\n"
             "---YOUR TASK---\n"
             "1. **Reasoning:** Look at the user's last statement. What is the most important piece of information to get next to tell the two themes apart? Is it about timing, triggers, physical vs. emotional feelings, etc.? Write this down as your internal reasoning.\n"
             "2. **Next Question:** Based on your reasoning, formulate the single best, empathetic, open-ended question to ask the user.")
        ])
        
        chain = prompt | self.structured_llm_plan # Assume self.structured_llm_plan is defined in __init__

        # --- 3. The LLM Call with a Robust Fallback ---
        fallback_question = "Thank you for sharing that. Could you tell me a bit more about a specific time you felt this way recently?"

        try:
            plan: QuestionGenerationPlan = chain.invoke({
                "history": formatted_history,
                "definitions": context_definitions
            })
            
            # --- 4. Log the AI's "Thought Process" ---
            # Valuable for debugging and demonstrating your system's intelligence.
            print("--- AI Thought Process ---")
            print(f"Reasoning: {plan.reasoning}")
            print(f"Question Generated: {plan.next_question}")
            print("--------------------------")

            return plan.next_question

        except Exception as e:
            print(f"Chain of Thought question generation failed: {e}")
            return fallback_question





if __name__ == "__main__":

    knowledge_base = {"Mood Disorders": {
    "description": "Characterized by significant and persistent disturbances in mood and emotional state, ranging from extreme sadness (depression) to extreme elation (mania).",
    "Subcategories": {
    "Major_Depressive_Disorder": {
        "description": "Involves a constant sense of hopelessness and despair, with a loss of interest or pleasure in most activities.",
        "Tests": ["Patient Health Questionnaire (PHQ-9)"]
    },
    "Bipolar_Disorder": {
        "description": "Involves extreme mood swings that include emotional highs (mania or hypomania) and lows (depression).",
        "Tests": ["Mood Disorder Questionnaire (MDQ)"]
    }
        }
    },
    "Anxiety Disorders": {
        "description": "Characterized by intense, excessive, and persistent worry and fear about everyday situations, often involving repeated episodes of sudden intense anxiety and terror (panic attacks).",
        "Subcategories": {
        "Generalized_Anxiety_Disorder": {
            "description": "Marked by persistent and excessive worry about a number of different things, often anticipating disaster and being overly concerned about money, health, family, or work.",
            "Tests": ["Generalized Anxiety Disorder 7 (GAD-7)"]
        },
        "Social_Anxiety_Disorder": {
            "description": "Involves a significant amount of fear, anxiety, and avoidance of social situations due to feelings of embarrassment, self-consciousness, and concern about being judged by others.",
            "Tests": ["Liebowitz Social Anxiety Scale (LSAS)"]
        }
        }
    },
    "Trauma and Stressor-Related Disorders": {
        "description": "Involves exposure to a traumatic or stressful event. Symptoms include intrusive memories, avoidance, negative changes in mood and thinking, and altered arousal and reactivity.",
        "Subcategories": {
        "Post_Traumatic_Stress_Disorder": {
            "description": "A disorder that develops in some people who have experienced a shocking, scary, or dangerous event. Symptoms include flashbacks, nightmares, and severe anxiety.",
            "Tests": ["PTSD Checklist for DSM-5 (PCL-5)"]
        }
        }
    },
    "Obsessive-Compulsive Disorder (OCD)": {
        "description": "Characterized by a pattern of unwanted thoughts and fears (obsessions) that lead you to do repetitive behaviors (compulsions).",
        "Subcategories": {
        "Obsessive_Compulsive_Disorder": {
            "description": "Features recurring, unwanted thoughts, ideas, or sensations (obsessions) that make a person feel driven to do something repetitively (compulsions).",
            "Tests": ["Yale-Brown Obsessive-Compulsive Scale (Y-BOCS)"]
        }
        }
    },
    "Personality Disorders": {
        "description": "Involves a rigid and unhealthy pattern of thinking, functioning, and behaving, causing significant problems and limitations in relationships, social activities, work, and school.",
        "Subcategories": {
        "Borderline_Personality_Disorder": {
            "description": "Marked by a pattern of ongoing instability in moods, behavior, self-image, and functioning. This often results in impulsive actions and unstable relationships.",
            "Tests": ["McLean Screening Instrument for Borderline Personality Disorder (MSI-BPD)"]
        }
        }
    },
    "Eating Disorders": {
        "description": "Serious conditions related to persistent eating behaviors that negatively impact health, emotions, and the ability to function in important areas of life.",
        "Subcategories": {
        "Eating_Disorders": {
            "description": "Characterized by severe disturbances in eating behavior and related thoughts and emotions, such as an unhealthy preoccupation with body weight and food.",
            "Tests": ["Eating Attitudes Test (EAT-26)"]
        }
        }
    },
    "Substance Use Disorders": {
        "description": "A disease that affects a person's brain and behavior and leads to an inability to control the use of a legal or illegal drug or medicine.",
        "Subcategories": {
        "Alcohol_Use_Disorder": {
            "description": "A medical condition characterized by an impaired ability to stop or control alcohol use despite adverse social, occupational, or health consequences.",
            "Tests": ["Alcohol Use Disorders Identification Test (AUDIT)"]
        },
        "Drug_Use_Disorders": {
            "description": "Involves the compulsive seeking and use of drugs despite harmful consequences. It is considered a brain disorder because it involves functional changes to brain circuits involved in reward, stress, and self-control.",
            "Tests": ["Drug Abuse Screening Test (DAST-10)"]
        }
        }
    },
    "Psychotic Disorders": {
        "description": "Severe mental disorders that cause abnormal thinking and perceptions. People with psychoses lose touch with reality. Two of the main symptoms are delusions and hallucinations.",
        "Subcategories": {
        "Schizophrenia": {
            "description": "A serious mental disorder in which people interpret reality abnormally. It may result in hallucinations, delusions, and extremely disordered thinking and behavior that impairs daily functioning.",
            "Tests": ["Positive and Negative Syndrome Scale (PANSS - Shortened Version)"]
        }
        }
    },
    "Neurodevelopmental Disorders": {
        "description": "A group of conditions with onset in the developmental period. They typically manifest early in development, often before the child enters grade school, and are characterized by developmental deficits that produce impairments of personal, social, academic, or occupational functioning.",
        "Subcategories": {
        "Autism_Spectrum_Disorder": {
            "description": "A complex developmental condition involving persistent challenges in social interaction, speech and nonverbal communication, and restricted/repetitive behaviors.",
            "Tests": ["Autism Spectrum Rating Scales (ASRS - Short Version)"]
        },
        "Attention_Deficit_Hyperactivity_Disorder": {
            "description": "A chronic condition including attention difficulty, hyperactivity, and impulsiveness.",
            "Tests": ["Vanderbilt ADHD Diagnostic Rating Scale (VADRS)"]
        }
        }
    },
    "Impulse Control Disorders": {
        "description": "Conditions in which a person has trouble controlling emotions or behaviors. Often, the behaviors are impulsive and can be harmful to oneself or others.",
        "Subcategories": {
        "Intermittent_Explosive_Disorder": {
            "description": "Involves repeated, sudden episodes of impulsive, aggressive, violent behavior or angry verbal outbursts in which you react grossly out of proportion to the situation.",
            "Tests": ["Intermittent Explosive Disorder Scale (IEDS)"]
        }
        }
    },
    "Social and Emotional Well-being": {
        "description": "Refers to a person's overall psychological state, including their ability to feel, think, and act in ways that create a positive impact on their functioning and quality of life.",
        "Subcategories": {
        "General_Emotional_Well_being": {
            "description": "Encompasses a person's ability to manage feelings, cope with stress, and maintain a positive outlook on life.",
            "Tests": ["Warwick-Edinburgh Mental Well-being Scale (WEMWBS)"]
        }
        }
    },
    "Suicidal Tendencies": {
        "description": "Refers to thoughts, plans, or actions related to intentionally ending one's own life. This is a serious psychiatric emergency.",
        "Subcategories": {
        "Suicidal_Tendencies": {
            "description": "Involves thinking about or planning suicide. It can range from a fleeting thought to a detailed plan.",
            "Tests": ["Columbia-Suicide Severity Rating Scale (C-SSRS)"]
        }
        }
    }
    }

    ob = ConversationService(knowledge_base)

    # # print(ob._get_description("Suicidal Tendencies"))



    dic = {
    "user_answer": "i am always depressed and anxious around people",
    "session_data": {
        "session_id": "8104b085-5ced-4404-a70f-db6e12d7c96d",
        "status": "priming",
        "ai_question_to_ask_user": "null",
        "conversation_history": [
        {
            "role": "user",
            "content": "Hi, I am very depessessed , i feel anxiety in front of people what to do"
        },
        {
            "role": "assistant",
            "content": "I'm so sorry to hear you're feeling this way. Could you share a bit about how these feelings are affecting your daily life right now?"
        },
                {
            "role": "user",
            "content": "when i see group of people I start trembling specially girls"
        },
        ],
        "belief_state": {'Anxiety Disorders':0.8, 'Trauma and Stressor-Related Disorders':0.2},
        "final_category": None,
        "assessment_data": None
    }
    }



    demo_session  = {
        "session_id": "8104b085-5ced-4404-a70f-db6e12d7c96d",
        "status": "priming",
        "ai_question_to_ask_user": "null",
        "conversation_history": [
        {
            "role": "user",
            "content": "Hi, I am very depessessed , i feel anxiety in front of people what to do"
        },
        {
            "role": "assistant",
            "content": "I'm so sorry to hear you're feeling this way. Could you share a bit about how these feelings are affecting your daily life right now?"
        },
            {
            "role": "user",
            "content": "when i see group of people I start trembling specially girls"
        }
        ],
        "belief_state": {'Anxiety Disorders':0.8, 'Trauma and Stressor-Related Disorders':0.2},
        "final_category": None,
        "assessment_data": None
    }




    print(ob._get_subcategory_description('Generalized_Anxiety_Disorder', 'Anxiety Disorders'))




    # # Example session_data and evaluation for testing update_belief_state
    # test_session_data = {
    #     "belief_state": {"Anxiety Disorders": 0.9, "Mood Disorders": 0.1},
    #     "conversation_history": [],
    #     "status": "refining_broad",
    #     "final_category": None,
    #     "assessment_data": None
    # }
    # test_evaluation = {
    #     "supported_category": "Anxiety Disorders",
    #     "confidence_score": 0.8,
    #     "reasoning": "User's answer strongly supports Anxiety Disorders."
    # }

    # updated = ob.update_belief_state(test_session_data, test_evaluation)
    # print("Updated session_data:", updated)



from app.services.llm_service import call_llm
from app.prompts.clinical_prompt import ROUTER_PROMPT

def classify_intent(user_input: str) -> str:
    """
    Classify user input intent using Nemotron router.
    
    Args:
        user_input: User's input message
    
    Returns:
        Intent classification
    """
    prompt = ROUTER_PROMPT.format(input=user_input)
    
    result = call_llm(prompt)
    
    # Normalize result
    result = result.strip().lower()
    
    # Validate against known intents
    valid_intents = [
        "lab_report",
        "prescription",
        "imaging",
        "symptom_query",
        "general_chat"
    ]
    
    # Check if result matches known intent
    for intent in valid_intents:
        if intent in result:
            return intent
    
    # Default to general_chat if no match
    return "general_chat"

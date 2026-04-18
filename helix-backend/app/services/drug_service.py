from typing import Dict, Any

# Mock drug database - in production connect to real database
DRUG_DATABASE = {
    "aspirin": {
        "name": "Aspirin",
        "use": ["Pain relief", "Fever reduction", "Anti-inflammatory"],
        "side_effects": ["Nausea", "Upset stomach", "Bleeding risk"],
        "interactions": ["Warfarin", "Ibuprofen"],
        "contraindications": ["Bleeding disorders", "Pregnancy third trimester"]
    },
    "metformin": {
        "name": "Metformin",
        "use": ["Type 2 Diabetes management", "PCOS treatment"],
        "side_effects": ["Diarrhea", "Nausea", "Metallic taste"],
        "interactions": ["Contrast dyes", "Alcohol"],
        "contraindications": ["Renal impairment", "Hepatic disease"]
    },
    "lisinopril": {
        "name": "Lisinopril",
        "use": ["Hypertension", "Heart failure"],
        "side_effects": ["Dry cough", "Dizziness", "Hyperkalemia"],
        "interactions": ["NSAIDs", "ACE inhibitors"],
        "contraindications": ["Pregnancy", "Angioedema history"]
    }
}

def get_drug_info(drug_name: str) -> Dict[str, Any]:
    """
    Retrieve drug information from database.
    
    Args:
        drug_name: Name of the drug
    
    Returns:
        Drug information dictionary
    """
    drug_key = drug_name.lower().strip()
    
    if drug_key in DRUG_DATABASE:
        return {
            "found": True,
            "data": DRUG_DATABASE[drug_key]
        }
    else:
        return {
            "found": False,
            "message": f"Drug '{drug_name}' not found in database",
            "suggestion": "Consult healthcare provider for accurate drug information"
        }

def check_drug_interactions(drugs: list) -> Dict[str, Any]:
    """
    Check for interactions between multiple drugs.
    
    Args:
        drugs: List of drug names
    
    Returns:
        Interaction analysis
    """
    interactions = []
    
    for i, drug1 in enumerate(drugs):
        drug1_key = drug1.lower().strip()
        
        if drug1_key in DRUG_DATABASE:
            drug1_data = DRUG_DATABASE[drug1_key]
            
            for drug2 in drugs[i+1:]:
                drug2_key = drug2.lower().strip()
                
                if drug2_key in DRUG_DATABASE:
                    # Check if there's an interaction
                    if drug2 in drug1_data.get("interactions", []) or \
                       drug1 in DRUG_DATABASE[drug2_key].get("interactions", []):
                        
                        interactions.append({
                            "drug1": drug1,
                            "drug2": drug2,
                            "severity": "Medium",
                            "recommendation": "Consult pharmacist or doctor"
                        })
    
    return {
        "interactions_found": len(interactions) > 0,
        "interactions": interactions,
        "safe": len(interactions) == 0
    }

def get_drug_contraindications(drug_name: str, conditions: list) -> Dict[str, Any]:
    """
    Check if drug is contraindicated for given conditions.
    
    Args:
        drug_name: Name of drug
        conditions: Patient conditions/diagnoses
    
    Returns:
        Contraindication check results
    """
    drug_key = drug_name.lower().strip()
    
    if drug_key not in DRUG_DATABASE:
        return {"found": False}
    
    drug_data = DRUG_DATABASE[drug_key]
    contraindications = []
    
    for condition in conditions:
        for contra in drug_data.get("contraindications", []):
            if condition.lower() in contra.lower():
                contraindications.append({
                    "condition": condition,
                    "contraindication": contra,
                    "severity": "High"
                })
    
    return {
        "drug": drug_name,
        "contraindications": contraindications,
        "safe": len(contraindications) == 0
    }

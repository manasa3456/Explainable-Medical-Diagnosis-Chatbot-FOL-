class Fact:
    def __init__(self, predicate, argument):
        self.predicate = predicate
        self.argument = argument
    def __repr__(self):
        return f"{self.predicate}({self.argument})"

class InferenceEngine:
    def __init__(self, kb_data):
        self.kb = kb_data
        self.diseases = kb_data['diseases']
        self.synonyms = kb_data['synonyms']

    def normalize_symptoms(self, user_symptoms):
        normalized = []
        for s in user_symptoms:
            s = s.lower().strip()
            normalized.append(self.synonyms.get(s, s).replace(" ", "_"))
        return list(set(normalized))

    def evaluate_match(self, disease, user_facts):
        """Calculates a match score and checks for exclusions."""
        user_symptom_names = [f.argument for f in user_facts]
        
        # Check Exclusions (Hard constraint)
        for exclusion in disease['exclusions']:
            if exclusion in user_symptom_names:
                return None, f"Excluded because user has {exclusion}."

        # Check Required Symptoms
        req_met = [s for s in disease['required'] if s in user_symptom_names]
        opt_met = [s for s in disease.get('optional', []) if s in user_symptom_names]
        
        # Scoring logic for ranking
        score = (len(req_met) + 0.5 * len(opt_met)) / (len(disease['required']) + 0.5 * len(disease.get('optional', [])))
        
        reasoning = {
            "met_required": req_met,
            "missing_required": [s for s in disease['required'] if s not in user_symptom_names],
            "met_optional": opt_met,
            "score": round(score * 100, 2)
        }
        
        return score, reasoning

    def forward_chaining(self, user_symptoms):
        """Data-driven: From symptoms to all possible diseases."""
        user_facts = [Fact("HasSymptom", s) for s in self.normalize_symptoms(user_symptoms)]
        results = []
        
        for disease in self.diseases:
            score, trace = self.evaluate_match(disease, user_facts)
            if score is not None and score > 0:
                results.append({
                    "disease": disease['name'],
                    "score": score,
                    "trace": trace,
                    "method": "Forward Chaining"
                })
        return sorted(results, key=lambda x: x['score'], reverse=True)

    def backward_chaining(self, user_symptoms, target_disease_name):
        """Goal-driven: Proves if a specific disease is likely."""
        user_facts = [Fact("HasSymptom", s) for s in self.normalize_symptoms(user_symptoms)]
        disease = next((d for d in self.diseases if d['name'] == target_disease_name), None)
        
        if not disease:
            return {"error": "Disease not in KB"}

        score, trace = self.evaluate_match(disease, user_facts)
        return {
            "disease": disease['name'],
            "is_possible": score is not None and score >= 0.5, # Threshold
            "trace": trace,
            "method": "Backward Chaining (Goal: " + target_disease_name + ")"
        }
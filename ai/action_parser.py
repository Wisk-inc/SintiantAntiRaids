import json

class Action:
    def __init__(self, type, **kwargs):
        self.type = type
        self.params = kwargs

    def __repr__(self):
        return f"Action(type={self.type}, params={self.params})"

def parse_ai_response(response_text):
    """
    Parses AI response → Action objects
    """
    try:
        # AI might wrap JSON in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        data = json.loads(response_text)
        verdict = data.get("verdict")
        explanation = data.get("explanation")
        threat_level = data.get("threat_level")
        actions_data = data.get("actions", [])

        actions = []
        for action_data in actions_data:
            a_type = action_data.pop("type")
            actions.append(Action(a_type, **action_data))

        return {
            "verdict": verdict,
            "explanation": explanation,
            "threat_level": threat_level,
            "actions": actions
        }
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        return None

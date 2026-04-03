import unittest
import json
from ai.action_parser import parse_ai_response, Action

class TestActionParser(unittest.TestCase):
    def test_parse_json(self):
        json_data = {
            "verdict": "RAID_DETECTED",
            "threat_level": 10,
            "explanation": "Mass deletion",
            "actions": [
                {"type": "BAN", "target": "123", "reason": "Raiding"}
            ]
        }
        response = json.dumps(json_data)
        result = parse_ai_response(response)
        self.assertEqual(result["verdict"], "RAID_DETECTED")
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0].type, "BAN")
        self.assertEqual(result["actions"][0].params["target"], "123")

    def test_parse_markdown_json(self):
        response = "```json\n{\"verdict\": \"CLEAN\", \"actions\": []}\n```"
        result = parse_ai_response(response)
        self.assertEqual(result["verdict"], "CLEAN")

if __name__ == "__main__":
    unittest.main()

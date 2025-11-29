import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.general.error_texts import APIError, ErrorCode
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import EnvelopeApi, AnswerSource, AnswerType, TextResult

class TestErrorFeedbackRecursive(unittest.TestCase):

    @patch("ApartmentManager.backend.AI_API.general.conversation_client.write_action_to_entity")
    @patch("ApartmentManager.backend.AI_API.general.conversation_client.GeminiClient")
    @patch("ApartmentManager.backend.AI_API.general.conversation_client.os.getenv")
    def test_backend_error_feedback_recursion(self, mock_getenv, mock_gemini_cls, mock_write_action):
        # Setup
        mock_getenv.return_value = "gemini-2.5-flash"
        client = ConversationClient("gemini-2.5-flash")
        
        # Mock LLM client and assistants
        mock_llm_client = MagicMock()
        client.llm_client = mock_llm_client
        
        # Mock CRUD intent to be CREATE
        mock_crud_intent = MagicMock()
        mock_crud_intent.create.value = True
        mock_crud_intent.create.operation_id = "NEW"
        mock_crud_intent.update.value = False
        mock_crud_intent.delete.value = False
        mock_crud_intent.show.value = False
        mock_llm_client.crud_intent_assistant.get_crud_llm_response.return_value = mock_crud_intent

        # Mock write_action_to_entity behavior
        # First call raises APIError
        error_code = ErrorCode.SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON
        
        # Second call succeeds
        success_envelope = EnvelopeApi(
            type=AnswerType.TEXT,
            result=TextResult(message="Success"),
            llm_model="gemini-2.5-flash",
            answer_source=AnswerSource.BACKEND
        )
        
        mock_write_action.side_effect = [
            APIError(error_code),
            (success_envelope, True)
        ]

        # Execute
        result = client.get_llm_answer("Create person")

        # Verify
        # 1. Check if write_action_to_entity was called twice
        self.assertEqual(mock_write_action.call_count, 2)

        # 2. Check if the second call to get_llm_answer (via recursion) had the error message
        # We can't directly check the recursive call arguments easily without mocking get_llm_answer itself,
        # but we can check if the second write_action call happened, which implies recursion worked.
        # Also, we can check if user_question was updated in the process (since it's an instance var)
        # However, since we are recursing, the `user_question` argument to the *inner* call is what matters.
        # The `self.user_question` attribute is updated at the start of `get_llm_answer`.
        
        # Let's verify that `self.user_question` currently holds the error message (from the last recursive call)
        # OR holds the original question if the recursion finished and popped back? 
        # Actually, `self.user_question = user_question` happens at start of method.
        # So in the inner call, `self.user_question` becomes the error message.
        # When inner call returns, `self.user_question` is still that error message (unless reset, which it isn't).
        self.assertIn("Backend Error:", client.user_question)
        self.assertIn(error_code.value[1], client.user_question)

        # 3. Check final result
        self.assertEqual(result, success_envelope)

    @patch("ApartmentManager.backend.AI_API.general.conversation_client.write_action_to_entity")
    @patch("ApartmentManager.backend.AI_API.general.conversation_client.GeminiClient")
    @patch("ApartmentManager.backend.AI_API.general.conversation_client.os.getenv")
    def test_infinite_recursion_prevention(self, mock_getenv, mock_gemini_cls, mock_write_action):
        # Setup
        mock_getenv.return_value = "gemini-2.5-flash"
        client = ConversationClient("gemini-2.5-flash")
        
        mock_llm_client = MagicMock()
        client.llm_client = mock_llm_client
        
        mock_crud_intent = MagicMock()
        mock_crud_intent.create.value = True
        mock_crud_intent.create.operation_id = "NEW"
        mock_llm_client.crud_intent_assistant.get_crud_llm_response.return_value = mock_crud_intent

        # Always raise error
        error_code = ErrorCode.SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON
        mock_write_action.side_effect = APIError(error_code)

        # Execute & Verify
        # Should raise APIError after one recursion attempt (because user_question will contain "Backend Error")
        with self.assertRaises(APIError):
            client.get_llm_answer("Create person")
        
        # Should be called twice: 1st time (original), 2nd time (recursive with error msg)
        # Then 2nd time fails, checks "Backend Error" in user_question, and raises.
        self.assertEqual(mock_write_action.call_count, 2)

if __name__ == "__main__":
    unittest.main()

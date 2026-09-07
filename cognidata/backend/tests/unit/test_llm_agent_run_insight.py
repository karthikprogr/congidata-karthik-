"""
Unit tests for the enhanced run_insight() function in llm_agent.py

Tests the integration of query classification, prompt building, response validation,
and performance monitoring in the main run_insight function according to the 
AI Chat Direct Answers specification.

Requirements tested: 8.1, 8.2, 8.4, 5.4
"""
import pytest
import pandas as pd
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from services.agents.llm_agent import run_insight, QueryType


class TestRunInsightFunctionSignature:
    """Test function signature preservation (Requirement 8.1)"""
    
    def test_function_signature_preserved(self):
        """Test that run_insight maintains expected function signature"""
        import inspect
        sig = inspect.signature(run_insight)
        params = list(sig.parameters.keys())
        
        # Verify parameter names and order
        assert params[0] == 'df', "First parameter should be 'df'"
        assert params[1] == 'api_key', "Second parameter should be 'api_key'"
        assert params[2] == 'history', "Third parameter should be 'history'"
        assert params[3] == 'question', "Fourth parameter should be 'question'"
        
        # Verify parameter defaults
        assert sig.parameters['history'].default is None, "history should default to None"
        assert sig.parameters['question'].default == "", "question should default to empty string"
    
    def test_function_returns_string(self):
        """Test that run_insight returns a string"""
        # Test with None df (simplest case)
        result = run_insight(df=None, api_key="test_key")
        assert isinstance(result, str), "run_insight should return a string"
    
    def test_function_accepts_optional_parameters(self):
        """Test that function accepts calls with minimal parameters"""
        # Should work with just df and api_key
        result = run_insight(df=None, api_key="test_key")
        assert isinstance(result, str), "Should work with minimal parameters"
        
        # Should work with all parameters
        df = pd.DataFrame({'A': [1, 2, 3]})
        history = []
        question = "test"
        
        with patch('services.agents.llm_agent._get_gemini_client') as mock_gemini:
            mock_client = Mock()
            mock_client.generate_text = AsyncMock(return_value="test response")
            mock_gemini.return_value = mock_client
            
            result = run_insight(df=df, api_key="key", history=history, question=question)
            assert isinstance(result, str), "Should work with all parameters"


class TestRunInsightNoneHandling:
    """Test None df handling (Requirement 8.1, 8.4)"""
    
    def test_none_df_returns_error_message(self):
        """Test that None df returns appropriate error message"""
        result = run_insight(df=None, api_key="test_key")
        assert isinstance(result, str), "Should return a string"
        assert "No dataset loaded" in result or "Upload a file" in result, \
            "Should indicate no dataset is loaded"
    
    def test_none_df_does_not_raise_exception(self):
        """Test that None df does not raise an exception"""
        try:
            result = run_insight(df=None, api_key="test_key")
            assert isinstance(result, str), "Should return error message string"
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
    
    def test_none_df_message_is_user_friendly(self):
        """Test that None df message is user-friendly"""
        result = run_insight(df=None, api_key="test_key")
        assert len(result) < 100, "Error message should be concise"
        assert not result.startswith("Error:"), "Should not be technical error format"


class TestRunInsightQueryClassificationIntegration:
    """Test query classification integration (Requirement 8.1, 1.3)"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._classify_query')
    def test_classify_query_called_for_question(self, mock_classify, mock_gemini):
        """Test that _classify_query is called when question is provided"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        mock_classify.return_value = QueryType.SIMPLE
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question="Which category?")
        
        # Verify
        mock_classify.assert_called_once()
        assert mock_classify.call_args[0][0] == "Which category?", \
            "Should call _classify_query with the question"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._classify_query')
    def test_complex_default_for_general_insights(self, mock_classify, mock_gemini):
        """Test that empty question defaults to COMPLEX classification"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute with empty question
        run_insight(df=df, api_key="key", question="")
        
        # Verify _classify_query was NOT called for empty question
        mock_classify.assert_not_called()
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._build_enhanced_prompt')
    def test_query_type_passed_to_prompt_builder(self, mock_build_prompt, mock_gemini):
        """Test that classified query type is passed to prompt builder"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        mock_build_prompt.return_value = "test prompt"
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute with simple query
        with patch('services.agents.llm_agent._classify_query') as mock_classify:
            mock_classify.return_value = QueryType.SIMPLE
            run_insight(df=df, api_key="key", question="Which?")
        
        # Verify query_type was passed to prompt builder
        mock_build_prompt.assert_called_once()
        call_kwargs = mock_build_prompt.call_args[1]
        assert call_kwargs['query_type'] == QueryType.SIMPLE, \
            "Should pass query_type to prompt builder"


class TestRunInsightPromptBuildingIntegration:
    """Test prompt building integration (Requirement 8.1, 6.1-6.4)"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._build_enhanced_prompt')
    def test_build_prompt_called_with_correct_parameters(self, mock_build_prompt, mock_gemini):
        """Test that _build_enhanced_prompt is called with all required parameters"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        history = [{"role": "user", "content": "test"}]
        question = "Which category?"
        
        mock_build_prompt.return_value = "test prompt"
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", history=history, question=question)
        
        # Verify
        mock_build_prompt.assert_called_once()
        call_kwargs = mock_build_prompt.call_args[1]
        
        assert 'df' in call_kwargs, "Should pass df to prompt builder"
        assert 'question' in call_kwargs, "Should pass question to prompt builder"
        assert 'history' in call_kwargs, "Should pass history to prompt builder"
        assert 'query_type' in call_kwargs, "Should pass query_type to prompt builder"
        assert 'dataset_ctx' in call_kwargs, "Should pass dataset_ctx to prompt builder"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._format_dataset_context')
    def test_dataset_context_formatted_and_passed(self, mock_format_ctx, mock_gemini):
        """Test that dataset context is formatted and passed to prompt builder"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        expected_ctx = {
            'record_count': 3,
            'record_count_formatted': '3',
            'num_columns': 1
        }
        mock_format_ctx.return_value = expected_ctx
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        with patch('services.agents.llm_agent._build_enhanced_prompt') as mock_build:
            mock_build.return_value = "test prompt"
            run_insight(df=df, api_key="key", question="test")
        
        # Verify
        mock_format_ctx.assert_called_once()
        mock_build.assert_called_once()
        call_kwargs = mock_build.call_args[1]
        assert call_kwargs['dataset_ctx'] == expected_ctx, \
            "Should pass formatted dataset context to prompt builder"


class TestRunInsightResponseValidationIntegration:
    """Test response validation integration (Requirement 8.1, 1.1, 1.2)"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._validate_response_format')
    def test_validate_response_called_after_generation(self, mock_validate, mock_gemini):
        """Test that _validate_response_format is called after response generation"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        generated_response = "Test response from Gemini"
        
        mock_validate.return_value = (True, "")
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value=generated_response)
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question="Which?")
        
        # Verify
        mock_validate.assert_called_once()
        call_args = mock_validate.call_args[0]
        assert call_args[0] == generated_response, \
            "Should validate the generated response"
        assert call_args[1] in [QueryType.SIMPLE, QueryType.COMPLEX], \
            "Should pass query type to validator"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._validate_response_format')
    @patch('services.agents.llm_agent.logger')
    def test_validation_warning_logged_on_invalid_response(
        self, mock_logger, mock_validate, mock_gemini
    ):
        """Test that validation warnings are logged but response is still returned"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        generated_response = "Test response"
        
        # Simulate validation failure
        mock_validate.return_value = (False, "Too many sentences")
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value=generated_response)
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question="test")
        
        # Verify warning was logged
        mock_logger.debug.assert_called()
        debug_call_args = str(mock_logger.debug.call_args)
        assert "validation" in debug_call_args.lower(), \
            "Should log validation warning"
        
        # Verify response is still returned despite validation failure
        assert result == generated_response, \
            "Should return response even if validation fails (soft validation)"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent._validate_response_format')
    def test_valid_response_returned_without_warning(self, mock_validate, mock_gemini):
        """Test that valid responses are returned without warnings"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        generated_response = "Valid response"
        
        # Simulate validation success
        mock_validate.return_value = (True, "")
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value=generated_response)
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question="test")
        
        # Verify
        assert result == generated_response, "Should return valid response"


class TestRunInsightPerformanceMonitoring:
    """Test performance monitoring integration (Requirement 5.4)"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent.logger')
    @patch('services.agents.llm_agent.time')
    def test_performance_warning_logged_when_slow(self, mock_time, mock_logger, mock_gemini):
        """Test that performance warning is logged when response takes >2 seconds"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        question = "Which category sells more?"
        
        # Simulate slow response (>2 seconds)
        mock_time.time.side_effect = [0.0, 2.5]  # Start time, end time
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question=question)
        
        # Verify warning was logged
        mock_logger.warning.assert_called()
        warning_message = str(mock_logger.warning.call_args)
        assert "slow" in warning_message.lower(), "Should mention slow performance"
        assert "2.5" in warning_message or "2.50" in warning_message, \
            "Should include the duration"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent.logger')
    @patch('services.agents.llm_agent.time')
    def test_no_warning_when_fast(self, mock_time, mock_logger, mock_gemini):
        """Test that no performance warning is logged for fast responses (<2 seconds)"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Simulate fast response (<2 seconds)
        mock_time.time.side_effect = [0.0, 1.5]  # Start time, end time
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question="test")
        
        # Verify no warning was logged
        mock_logger.warning.assert_not_called()
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent.logger')
    def test_performance_warning_includes_query_text(self, mock_logger, mock_gemini):
        """Test that performance warning includes truncated query text"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        long_question = "Which category " + "x" * 200  # Long question
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Force slow execution by mocking time
        with patch('services.agents.llm_agent.time') as mock_time:
            mock_time.time.side_effect = [0.0, 3.0]  # 3 second duration
            run_insight(df=df, api_key="key", question=long_question)
        
        # Verify warning includes truncated query
        mock_logger.warning.assert_called()
        warning_message = str(mock_logger.warning.call_args)
        # Should truncate to 100 chars per design
        assert len(long_question[:100]) <= 100, "Query should be truncated in warning"


class TestRunInsightErrorHandling:
    """Test error handling preservation (Requirement 8.4)"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_exception_returns_error_message_not_raises(self, mock_gemini):
        """Test that exceptions are caught and returned as error message strings"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Simulate exception in Gemini client
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(side_effect=Exception("API Error"))
        mock_gemini.return_value = mock_client
        
        # Execute - should not raise exception
        try:
            result = run_insight(df=df, api_key="key", question="test")
            assert isinstance(result, str), "Should return error message as string"
            assert "error" in result.lower() or "could not" in result.lower(), \
                "Error message should indicate failure"
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
    
    @patch('services.agents.llm_agent._get_gemini_client')
    @patch('services.agents.llm_agent.logger')
    def test_exception_logged_with_details(self, mock_logger, mock_gemini):
        """Test that exceptions are logged with error details"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        error_message = "Gemini API timeout"
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(side_effect=Exception(error_message))
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question="test")
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_log = str(mock_logger.error.call_args)
        assert "error" in error_log.lower(), "Should log error"
    
    @patch('services.agents.llm_agent._format_dataset_context')
    def test_error_in_formatting_handled_gracefully(self, mock_format):
        """Test that errors in dataset context formatting are handled"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        mock_format.side_effect = Exception("Formatting error")
        
        # Execute - should not raise exception
        try:
            result = run_insight(df=df, api_key="key", question="test")
            assert isinstance(result, str), "Should return error message as string"
        except Exception as e:
            pytest.fail(f"Should handle formatting errors gracefully, but raised: {e}")
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_error_message_format_is_user_friendly(self, mock_gemini):
        """Test that error messages are user-friendly"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(side_effect=Exception("Internal error"))
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question="test")
        
        # Verify message is user-friendly
        assert isinstance(result, str), "Should return string"
        assert len(result) < 200, "Error message should be concise"
        # Should not expose raw exception traces to user
        assert "traceback" not in result.lower(), "Should not expose traceback"


class TestRunInsightGeminiIntegration:
    """Test Gemini client integration and token limits"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_gemini_client_called_with_prompt(self, mock_gemini):
        """Test that Gemini client is called with the generated prompt"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question="test")
        
        # Verify
        mock_client.generate_text.assert_called_once()
        call_args = mock_client.generate_text.call_args
        
        # First positional argument should be the prompt
        assert len(call_args[0]) > 0, "Should pass prompt to Gemini"
        assert isinstance(call_args[0][0], str), "Prompt should be a string"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_token_limit_for_simple_query(self, mock_gemini):
        """Test that SIMPLE queries use 150 max_tokens"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute with simple query
        with patch('services.agents.llm_agent._classify_query') as mock_classify:
            mock_classify.return_value = QueryType.SIMPLE
            run_insight(df=df, api_key="key", question="Which?")
        
        # Verify max_tokens
        call_kwargs = mock_client.generate_text.call_args[1]
        assert call_kwargs['max_tokens'] == 150, \
            "Simple queries should use 150 max_tokens"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_token_limit_for_complex_query(self, mock_gemini):
        """Test that COMPLEX queries use 300 max_tokens"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute with complex query
        with patch('services.agents.llm_agent._classify_query') as mock_classify:
            mock_classify.return_value = QueryType.COMPLEX
            run_insight(df=df, api_key="key", question="What are the trends?")
        
        # Verify max_tokens
        call_kwargs = mock_client.generate_text.call_args[1]
        assert call_kwargs['max_tokens'] == 300, \
            "Complex queries should use 300 max_tokens"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_token_limit_for_general_insights(self, mock_gemini):
        """Test that general insights (no question) use 400 max_tokens"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute with no question (general insights)
        run_insight(df=df, api_key="key", question="")
        
        # Verify max_tokens
        call_kwargs = mock_client.generate_text.call_args[1]
        assert call_kwargs['max_tokens'] == 400, \
            "General insights should use 400 max_tokens"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_temperature_set_to_low_value(self, mock_gemini):
        """Test that temperature is set to 0.2 for consistency"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value="Test response")
        mock_gemini.return_value = mock_client
        
        # Execute
        run_insight(df=df, api_key="key", question="test")
        
        # Verify temperature
        call_kwargs = mock_client.generate_text.call_args[1]
        assert call_kwargs['temperature'] == 0.2, \
            "Should use temperature 0.2 for consistent formatting"


class TestRunInsightResponseProcessing:
    """Test response processing and cleanup"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_response_stripped_of_whitespace(self, mock_gemini):
        """Test that response is stripped of leading/trailing whitespace"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        response_with_whitespace = "  Test response with whitespace  \n"
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value=response_with_whitespace)
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question="test")
        
        # Verify whitespace is stripped
        assert result == "Test response with whitespace", \
            "Response should be stripped of whitespace"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_response_returned_unchanged_if_valid(self, mock_gemini):
        """Test that valid responses are returned without modification"""
        # Setup
        df = pd.DataFrame({'A': [1, 2, 3]})
        expected_response = "Technology sells more in your 3 records."
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(return_value=expected_response)
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question="Which?")
        
        # Verify response is unchanged
        assert result == expected_response, \
            "Valid response should be returned unchanged"


class TestRunInsightEndToEnd:
    """End-to-end integration tests with real data flow"""
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_simple_query_end_to_end(self, mock_gemini):
        """Test complete flow for a simple query"""
        # Setup realistic scenario
        df = pd.DataFrame({
            'Category': ['Tech', 'Office', 'Tech', 'Office'],
            'Sales': [100, 50, 150, 75]
        })
        question = "Which category sells more?"
        history = []
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(
            return_value="Tech sells more in your 4 records."
        )
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", history=history, question=question)
        
        # Verify
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return non-empty response"
        # Gemini client should have been called
        mock_client.generate_text.assert_called_once()
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_complex_query_end_to_end(self, mock_gemini):
        """Test complete flow for a complex query"""
        # Setup realistic scenario
        df = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'Sales': [100, 120, 140, 160]
        })
        question = "What are the sales trends?"
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(
            return_value="Your 4 records show steady growth from Jan to Apr."
        )
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question=question)
        
        # Verify
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return non-empty response"
    
    @patch('services.agents.llm_agent._get_gemini_client')
    def test_general_insights_end_to_end(self, mock_gemini):
        """Test complete flow for general insights (no question)"""
        # Setup realistic scenario
        df = pd.DataFrame({
            'Product': ['A', 'B', 'C'],
            'Sales': [100, 200, 150]
        })
        
        mock_client = Mock()
        mock_client.generate_text = AsyncMock(
            return_value="Your dataset contains 3 products with varying sales."
        )
        mock_gemini.return_value = mock_client
        
        # Execute
        result = run_insight(df=df, api_key="key", question="")
        
        # Verify
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return non-empty response"

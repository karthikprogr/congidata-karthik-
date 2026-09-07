"""
Integration tests for LLM Agent model verification.
Tests that Gemini Flash model is instantiated correctly with proper configuration.
**Validates: Requirements 5.2**
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
from services.agents.llm_agent import run_insight, _get_gemini_client, QueryType
from app.ai.gemini_provider import GeminiProvider


class TestGeminiModelConfiguration:
    """Test that Gemini Flash model is instantiated correctly."""
    
    def test_gemini_flash_model_is_used(self):
        """
        Test that the Gemini provider uses gemini-2.5-flash model.
        **Validates: Requirements 5.2**
        """
        gemini_client = _get_gemini_client()
        
        # Verify the client is a GeminiProvider instance
        assert isinstance(gemini_client, GeminiProvider)
        
        # Verify the model name is gemini-2.5-flash (optimized for speed)
        assert gemini_client.model_name == "gemini-2.5-flash"
    
    def test_temperature_is_set_to_point_two(self):
        """
        Test that temperature is set to 0.2 for consistent formatting.
        **Validates: Requirements 5.2**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['Technology', 'Furniture', 'Office Supplies'],
            'Sales': [125000, 78000, 45000]
        })
        
        # Mock the Gemini client to capture the temperature parameter
        with patch('services.agents.llm_agent._get_gemini_client') as mock_get_client:
            mock_gemini = MagicMock(spec=GeminiProvider)
            mock_gemini.generate_text = AsyncMock(return_value="Technology sells more in your 3 records.")
            mock_get_client.return_value = mock_gemini
            
            # Call run_insight with a simple query
            result = run_insight(df, api_key="test_key", history=[], question="Which category sells more?")
            
            # Verify generate_text was called with temperature=0.2
            mock_gemini.generate_text.assert_called_once()
            call_args = mock_gemini.generate_text.call_args
            
            # Check that temperature parameter is 0.2
            assert 'temperature' in call_args.kwargs
            assert call_args.kwargs['temperature'] == 0.2
    
    def test_max_tokens_configured_for_simple_query(self):
        """
        Test that max_tokens is set to 150 for Simple queries.
        **Validates: Requirements 5.2**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['Technology', 'Furniture'],
            'Sales': [125000, 78000]
        })
        
        # Mock the Gemini client
        with patch('services.agents.llm_agent._get_gemini_client') as mock_get_client:
            mock_gemini = MagicMock(spec=GeminiProvider)
            mock_gemini.generate_text = AsyncMock(return_value="Technology sells more in your 2 records.")
            mock_get_client.return_value = mock_gemini
            
            # Call run_insight with a simple query (should be classified as SIMPLE)
            result = run_insight(df, api_key="test_key", history=[], question="Which category sells more?")
            
            # Verify max_tokens is 150 for Simple query
            call_args = mock_gemini.generate_text.call_args
            assert 'max_tokens' in call_args.kwargs
            assert call_args.kwargs['max_tokens'] == 150
    
    def test_max_tokens_configured_for_complex_query(self):
        """
        Test that max_tokens is set to 300 for Complex queries.
        **Validates: Requirements 5.2**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['Technology', 'Furniture', 'Office Supplies'],
            'Sales': [125000, 78000, 45000],
            'Profit': [25000, 15000, 10000]
        })
        
        # Mock the Gemini client
        with patch('services.agents.llm_agent._get_gemini_client') as mock_get_client:
            mock_gemini = MagicMock(spec=GeminiProvider)
            mock_gemini.generate_text = AsyncMock(
                return_value="Your 3 records show Technology leading with $125,000 in sales. "
                             "Furniture follows at $78,000, while Office Supplies trails at $45,000."
            )
            mock_get_client.return_value = mock_gemini
            
            # Call run_insight with a complex query (contains "trend" keyword)
            result = run_insight(df, api_key="test_key", history=[], question="What are the sales trends?")
            
            # Verify max_tokens is 300 for Complex query
            call_args = mock_gemini.generate_text.call_args
            assert 'max_tokens' in call_args.kwargs
            assert call_args.kwargs['max_tokens'] == 300
    
    def test_max_tokens_configured_for_general_insights(self):
        """
        Test that max_tokens is set to 400 for general insights (no question).
        **Validates: Requirements 5.2**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['Technology', 'Furniture', 'Office Supplies'],
            'Sales': [125000, 78000, 45000],
            'Profit': [25000, 15000, 10000]
        })
        
        # Mock the Gemini client
        with patch('services.agents.llm_agent._get_gemini_client') as mock_get_client:
            mock_gemini = MagicMock(spec=GeminiProvider)
            mock_gemini.generate_text = AsyncMock(
                return_value="Your 3 records show strong performance in Technology. "
                             "Sales total $248,000 with Technology driving 50% of revenue. "
                             "Profit margins are healthy at 20% overall."
            )
            mock_get_client.return_value = mock_gemini
            
            # Call run_insight without a question (general insights)
            result = run_insight(df, api_key="test_key", history=[], question="")
            
            # Verify max_tokens is 400 for general insights
            call_args = mock_gemini.generate_text.call_args
            assert 'max_tokens' in call_args.kwargs
            assert call_args.kwargs['max_tokens'] == 400
    
    def test_gemini_provider_initialization(self):
        """
        Test that GeminiProvider is properly initialized with correct model.
        **Validates: Requirements 5.2**
        """
        from app.ai.gemini_provider import gemini_flash
        
        # Verify gemini_flash instance exists
        assert gemini_flash is not None
        assert isinstance(gemini_flash, GeminiProvider)
        
        # Verify it's configured with the flash model
        assert gemini_flash.model_name == "gemini-2.5-flash"


class TestModelConfigurationIntegration:
    """Integration tests verifying model configuration in full workflow."""
    
    def test_full_workflow_uses_correct_model_and_settings(self):
        """
        Test that the full run_insight workflow uses correct model with proper settings.
        **Validates: Requirements 5.2**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Product': ['Laptop', 'Mouse', 'Keyboard'],
            'Sales': [1200, 450, 380]
        })
        
        # Mock the Gemini client to verify all parameters
        with patch('services.agents.llm_agent._get_gemini_client') as mock_get_client:
            mock_gemini = MagicMock(spec=GeminiProvider)
            mock_gemini.model_name = "gemini-2.5-flash"
            mock_gemini.generate_text = AsyncMock(return_value="Laptop sells more in your 3 records.")
            mock_get_client.return_value = mock_gemini
            
            # Run insight generation
            result = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="Which product sells more?"
            )
            
            # Verify the correct client was obtained
            mock_get_client.assert_called_once()
            
            # Verify generate_text was called with correct parameters
            mock_gemini.generate_text.assert_called_once()
            call_args = mock_gemini.generate_text.call_args
            
            # Verify all key parameters
            assert call_args.kwargs['temperature'] == 0.2
            assert call_args.kwargs['max_tokens'] == 150  # Simple query
            assert isinstance(call_args.args[0], str)  # Prompt is a string
            
            # Verify result is returned
            assert result == "Laptop sells more in your 3 records."
    
    def test_model_settings_vary_by_query_type(self):
        """
        Test that max_tokens changes based on query classification.
        **Validates: Requirements 5.2**
        """
        df = pd.DataFrame({
            'Category': ['A', 'B'],
            'Sales': [100, 200]
        })
        
        with patch('services.agents.llm_agent._get_gemini_client') as mock_get_client:
            mock_gemini = MagicMock(spec=GeminiProvider)
            mock_gemini.generate_text = AsyncMock(return_value="Response")
            mock_get_client.return_value = mock_gemini
            
            # Test 1: Simple query
            run_insight(df, "key", [], "Which sells more?")
            assert mock_gemini.generate_text.call_args.kwargs['max_tokens'] == 150
            
            # Reset mock
            mock_gemini.reset_mock()
            
            # Test 2: Complex query
            run_insight(df, "key", [], "What are the trends over time?")
            assert mock_gemini.generate_text.call_args.kwargs['max_tokens'] == 300
            
            # Reset mock
            mock_gemini.reset_mock()
            
            # Test 3: General insights (no question)
            run_insight(df, "key", [], "")
            assert mock_gemini.generate_text.call_args.kwargs['max_tokens'] == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

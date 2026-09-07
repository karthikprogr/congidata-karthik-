"""
Unit tests for _build_enhanced_prompt() helper function in llm_agent.py

Tests the prompt building functionality according to the AI Chat Direct Answers specification.
Tests verify:
- System instructions with role, length constraints, tone guidelines
- Response length based on query_type (1 sentence for SIMPLE, 3 for COMPLEX)
- Examples for both simple and complex queries
- Conversation history formatting (last 4 exchanges, truncate to 500 chars each)
- Compact dataset context summary (record count, columns, top 3 numeric stats)
- Final prompt construction with current question
- Token optimization (target <800 tokens)
"""
import pytest
import pandas as pd
import numpy as np
from services.agents.llm_agent import _build_enhanced_prompt, _format_dataset_context, QueryType


class TestBuildEnhancedPrompt:
    """Test suite for _build_enhanced_prompt() function"""
    
    def test_system_instructions_include_length_constraints(self):
        """Test that system instructions include length constraints based on query type"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        # Test SIMPLE query - should say "one sentence"
        prompt_simple = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        assert "one sentence" in prompt_simple.lower()
        
        # Test COMPLEX query - should say "up to three sentences"
        prompt_complex = _build_enhanced_prompt(df, "What are the trends?", None, QueryType.COMPLEX, ctx)
        assert "up to three sentences" in prompt_complex.lower()
    
    def test_system_instructions_include_tone_guidelines(self):
        """Test that system instructions include tone guidelines"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        
        # Should include conversational business language guidance
        assert "conversational business language" in prompt.lower()
        assert "casual" in prompt.lower()
        
        # Should include preamble avoidance
        assert "no preambles" in prompt.lower() or "start your answer immediately" in prompt.lower()
        
        # Should include casual comparatives guidance
        assert "sells more" in prompt.lower() or "casual comparatives" in prompt.lower()
        
        # Should include jargon avoidance
        assert "avoid technical jargon" in prompt.lower() or "jargon" in prompt.lower()
        
        # Should include academic phrase avoidance
        assert "avoid academic" in prompt.lower() or "therefore" in prompt.lower() or "thus" in prompt.lower()
    
    def test_examples_included_for_simple_queries(self):
        """Test that examples are included for SIMPLE query type"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        
        # Should include "Examples:" section
        assert "Examples:" in prompt or "examples:" in prompt.lower()
        
        # Should include Q: and A: format examples
        assert "Q:" in prompt
        assert "A:" in prompt
        
        # Should include example about categories or top customer
        prompt_lower = prompt.lower()
        assert "category" in prompt_lower or "customer" in prompt_lower
    
    def test_examples_included_for_complex_queries(self):
        """Test that examples are included for COMPLEX query type"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "What are the sales trends?", None, QueryType.COMPLEX, ctx)
        
        # Should include "Examples:" section
        assert "Examples:" in prompt or "examples:" in prompt.lower()
        
        # Should include Q: and A: format examples
        assert "Q:" in prompt
        assert "A:" in prompt
        
        # Should include example with numbers and multiple sentences
        prompt_lower = prompt.lower()
        assert "trends" in prompt_lower or "compare" in prompt_lower or "region" in prompt_lower
        
        # Complex examples should have numbers
        assert any(char.isdigit() for char in prompt)
    
    def test_conversation_history_limited_to_last_4_exchanges(self):
        """Test that conversation history is limited to last 4 exchanges"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        # Create 6 history messages
        history = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
            {"role": "assistant", "content": "Response 3"},
        ]
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", history, QueryType.SIMPLE, ctx)
        
        # Should include "Previous conversation:" section
        assert "Previous conversation:" in prompt or "previous conversation:" in prompt.lower()
        
        # Should only include last 4 messages (Message 2, Response 2, Message 3, Response 3)
        assert "Message 1" not in prompt
        assert "Response 1" not in prompt
        assert "Message 2" in prompt
        assert "Response 2" in prompt
        assert "Message 3" in prompt
        assert "Response 3" in prompt
    
    def test_conversation_history_truncates_long_messages(self):
        """Test that conversation history messages are truncated to 500 chars"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        # Create a message longer than 500 chars
        long_message = "A" * 600
        history = [
            {"role": "user", "content": long_message},
            {"role": "assistant", "content": "Short response"},
        ]
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", history, QueryType.SIMPLE, ctx)
        
        # The long message should be truncated
        # Count how many 'A's appear in the prompt
        a_count = prompt.count('A')
        
        # Should have roughly 500 A's (plus maybe ellipsis), not 600
        assert a_count < 550, f"Expected ~500 chars, but found {a_count} 'A' characters"
        assert a_count >= 400, f"Expected at least 400 chars after truncation, found {a_count}"
        
        # Should have ellipsis if truncated
        if a_count < 600:
            assert "..." in prompt
    
    def test_dataset_context_includes_record_count(self):
        """Test that dataset context includes formatted record count"""
        df = pd.DataFrame({'Sales': [100, 200, 300], 'Category': ['A', 'B', 'C']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        
        # Should include "Dataset:" section with record count
        assert "Dataset:" in prompt or "dataset:" in prompt.lower()
        assert "3 records" in prompt or ctx['record_count_formatted'] in prompt
    
    def test_dataset_context_includes_column_names(self):
        """Test that dataset context includes column names (first 5)"""
        df = pd.DataFrame({
            'Col1': [1, 2],
            'Col2': [3, 4],
            'Col3': [5, 6],
            'Col4': [7, 8],
            'Col5': [9, 10],
            'Col6': [11, 12],
            'Col7': [13, 14],
        })
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "Show trends", None, QueryType.COMPLEX, ctx)
        
        # Should include first 5 column names
        assert "Col1" in prompt
        assert "Col2" in prompt
        assert "Col3" in prompt
        assert "Col4" in prompt
        assert "Col5" in prompt
        
        # Should indicate there are more columns
        assert "+2 more" in prompt or "7 columns" in prompt
    
    def test_dataset_context_includes_top_3_numeric_stats(self):
        """Test that dataset context includes stats for top 3 numeric columns"""
        df = pd.DataFrame({
            'Sales': [100, 200, 300],
            'Profit': [10, 20, 30],
            'Quantity': [1, 2, 3],
            'ExtraNum': [4, 5, 6],
            'Category': ['A', 'B', 'C']
        })
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "What are trends?", None, QueryType.COMPLEX, ctx)
        
        # Should include stats for first 3 numeric columns (Sales, Profit, Quantity)
        assert "Sales:" in prompt
        assert "Profit:" in prompt
        assert "Quantity:" in prompt
        
        # Stats should include mean and range
        assert "mean=" in prompt
        assert "range=" in prompt
        
        # Should NOT include stats for 4th numeric column (token optimization)
        assert "ExtraNum:" not in prompt or prompt.count("mean=") <= 3
    
    def test_prompt_includes_current_question(self):
        """Test that prompt includes the current user question"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        question = "Which category has higher sales?"
        prompt = _build_enhanced_prompt(df, question, None, QueryType.SIMPLE, ctx)
        
        # Should include the question
        assert question in prompt
        
        # Should be formatted as "Client: <question>"
        assert f"Client: {question}" in prompt
        
        # Should have a response prompt
        assert "You:" in prompt
    
    def test_prompt_for_general_insights_without_question(self):
        """Test prompt construction when question is empty (general insights)"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "", None, QueryType.COMPLEX, ctx)
        
        # Should have general insights instruction
        assert "insights" in prompt.lower()
        assert "Your insights:" in prompt or "key insights" in prompt.lower()
    
    def test_simple_query_number_formatting_guidance(self):
        """Test that SIMPLE queries include guidance to avoid numbers"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        
        # Should tell model not to include numbers
        assert "don't include numbers" in prompt.lower() or "without numbers" in prompt.lower()
    
    def test_complex_query_number_formatting_guidance(self):
        """Test that COMPLEX queries include guidance for number formatting"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "What are trends?", None, QueryType.COMPLEX, ctx)
        
        # Should include number formatting guidance
        prompt_lower = prompt.lower()
        assert "formatting" in prompt_lower or "1,234" in prompt
        
        # Should mention rounding
        assert "round" in prompt_lower
        assert "decimal" in prompt_lower or "whole number" in prompt_lower
    
    def test_prompt_structure_is_complete(self):
        """Test that prompt has all required sections in correct order"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        history = [{"role": "user", "content": "Previous question"}]
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", history, QueryType.SIMPLE, ctx)
        
        # Find positions of key sections
        sections = []
        if "business analyst" in prompt.lower():
            sections.append(("system", prompt.lower().find("business analyst")))
        if "examples:" in prompt.lower():
            sections.append(("examples", prompt.lower().find("examples:")))
        if "previous conversation:" in prompt.lower():
            sections.append(("history", prompt.lower().find("previous conversation:")))
        if "dataset:" in prompt.lower():
            sections.append(("dataset", prompt.lower().find("dataset:")))
        if "client:" in prompt.lower():
            sections.append(("question", prompt.lower().find("client:")))
        
        # Verify sections appear in expected order
        # Sort by position
        sections_sorted = sorted(sections, key=lambda x: x[1])
        section_names = [s[0] for s in sections_sorted]
        
        # System should come first, examples second, then history/dataset/question
        assert section_names[0] == "system"
        assert section_names[1] == "examples"
        assert "question" in section_names  # Question should be last
    
    def test_empty_history_does_not_break_prompt(self):
        """Test that empty history list doesn't break prompt generation"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        # Test with None history
        prompt_none = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        assert len(prompt_none) > 0
        assert "Client:" in prompt_none
        
        # Test with empty list
        prompt_empty = _build_enhanced_prompt(df, "Which sells more?", [], QueryType.SIMPLE, ctx)
        assert len(prompt_empty) > 0
        assert "Client:" in prompt_empty
    
    def test_prompt_token_optimization(self):
        """Test that prompt is reasonably sized (target <800 tokens, rough check)"""
        df = pd.DataFrame({
            'Sales': list(range(100)),
            'Profit': list(range(100, 200)),
            'Quantity': list(range(200, 300)),
            'Category': ['A'] * 100
        })
        ctx = _format_dataset_context(df)
        
        history = [
            {"role": "user", "content": "Message 1 " * 50},
            {"role": "assistant", "content": "Response 1 " * 50},
            {"role": "user", "content": "Message 2 " * 50},
            {"role": "assistant", "content": "Response 2 " * 50},
        ]
        
        prompt = _build_enhanced_prompt(df, "What are the sales trends?", history, QueryType.COMPLEX, ctx)
        
        # Rough token estimation: ~4 chars per token
        # Target is <800 tokens = ~3200 chars
        char_count = len(prompt)
        estimated_tokens = char_count / 4
        
        # Allow some buffer (1000 tokens = 4000 chars)
        assert char_count < 4000, f"Prompt too long: {char_count} chars (~{estimated_tokens:.0f} tokens), target <800 tokens"
    
    def test_dataset_context_none_does_not_break_prompt(self):
        """Test that None dataset_ctx doesn't break prompt generation"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, None)
        
        assert len(prompt) > 0
        assert "Client:" in prompt
        # Should still have system instructions and examples
        assert "business analyst" in prompt.lower()
        assert "Examples:" in prompt
    
    def test_role_definition_in_system_instructions(self):
        """Test that system instructions define the expert business analyst role"""
        df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        ctx = _format_dataset_context(df)
        
        prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        
        # Should define role as expert business analyst
        assert "expert business analyst" in prompt.lower() or "business analyst" in prompt.lower()
        assert "client" in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

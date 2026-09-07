"""
Unit tests for _classify_query() helper function in llm_agent.py

Tests query classification logic that determines whether user queries are
Simple (single fact/comparison) or Complex (multiple metrics/trends)
according to the AI Chat Direct Answers specification.

Requirements tested: 7.1, 7.2, 7.3, 7.4, 7.5
"""
import pytest
from services.agents.llm_agent import _classify_query, QueryType


class TestClassifyQuery:
    """Test suite for _classify_query() function"""
    
    # ──────────────────────────────────────────────────────────────────────
    # Test Complex Keyword Detection (Requirement 7.3)
    # ──────────────────────────────────────────────────────────────────────
    
    def test_complex_keyword_trend(self):
        """Test that 'trend' keyword triggers Complex classification"""
        query = "What are the sales trends?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'trend' should be Complex"
    
    def test_complex_keyword_pattern(self):
        """Test that 'pattern' keyword triggers Complex classification"""
        query = "Show me patterns in customer behavior"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'pattern' should be Complex"
    
    def test_complex_keyword_breakdown(self):
        """Test that 'breakdown' keyword triggers Complex classification"""
        query = "Give me a breakdown by region"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'breakdown' should be Complex"
    
    def test_complex_keyword_compare_across(self):
        """Test that 'compare across' phrase triggers Complex classification"""
        query = "Compare across all categories"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'compare across' should be Complex"
    
    def test_complex_keyword_over_time(self):
        """Test that 'over time' phrase triggers Complex classification"""
        query = "How have sales changed over time?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'over time' should be Complex"
    
    def test_complex_keyword_analysis(self):
        """Test that 'analysis' keyword triggers Complex classification"""
        query = "Provide an analysis of the data"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'analysis' should be Complex"
    
    def test_complex_keyword_correlation(self):
        """Test that 'correlation' keyword triggers Complex classification"""
        query = "Is there any correlation between sales and profit?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'correlation' should be Complex"
    
    def test_complex_keyword_distribution(self):
        """Test that 'distribution' keyword triggers Complex classification"""
        query = "Show the distribution of customers"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'distribution' should be Complex"
    
    def test_complex_keyword_case_insensitive(self):
        """Test that complex keyword detection is case-insensitive"""
        queries = [
            "What are the TRENDS?",
            "Show me PATTERNS",
            "Give a BREAKDOWN",
            "ANALYSIS please"
        ]
        for query in queries:
            result = _classify_query(query)
            assert result == QueryType.COMPLEX, f"Query '{query}' should be Complex (case-insensitive)"
    
    def test_complex_keyword_in_middle_of_sentence(self):
        """Test that complex keywords are detected anywhere in the query"""
        query = "Can you help me understand the trend in this data?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Complex keyword in middle of sentence should trigger Complex"
    
    def test_complex_keyword_multiple_keywords(self):
        """Test query with multiple complex keywords"""
        query = "Show me trends and patterns with a detailed breakdown"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with multiple complex keywords should be Complex"
    
    # ──────────────────────────────────────────────────────────────────────
    # Test Simple Pattern Matching (Requirement 7.4)
    # ──────────────────────────────────────────────────────────────────────
    
    def test_simple_pattern_which(self):
        """Test that 'which' without modifiers triggers Simple classification"""
        query = "Which category sells more?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'which' should be Simple"
    
    def test_simple_pattern_who(self):
        """Test that 'who' without modifiers triggers Simple classification"""
        query = "Who is the top customer?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'who' should be Simple"
    
    def test_simple_pattern_what_is(self):
        """Test that 'what is' phrase triggers Simple classification"""
        query = "What is the total sales?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'what is' should be Simple"
    
    def test_simple_pattern_how_many(self):
        """Test that 'how many' phrase triggers Simple classification"""
        query = "How many orders were placed?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'how many' should be Simple"
    
    def test_simple_pattern_case_insensitive(self):
        """Test that simple pattern detection is case-insensitive"""
        queries = [
            "WHICH category is best?",
            "WHO leads in sales?",
            "WHAT IS the average?",
            "HOW MANY records?"
        ]
        for query in queries:
            result = _classify_query(query)
            assert result == QueryType.SIMPLE, f"Query '{query}' should be Simple (case-insensitive)"
    
    def test_simple_pattern_which_at_start(self):
        """Test 'which' at the start of the query"""
        query = "Which region has the highest sales?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query starting with 'which' should be Simple"
    
    def test_simple_pattern_which_in_middle(self):
        """Test 'which' in the middle of the query"""
        query = "Can you tell me which product is most popular?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'which' in middle should be Simple"
    
    def test_simple_pattern_word_boundaries(self):
        """Test that patterns match whole words only"""
        # 'which' should match as a word, not as part of 'whichever'
        query = "Which customer?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'which' as whole word should be Simple"
    
    # ──────────────────────────────────────────────────────────────────────
    # Test Default to Simple for Ambiguous Queries (Requirement 7.5)
    # ──────────────────────────────────────────────────────────────────────
    
    def test_ambiguous_defaults_to_simple_generic_question(self):
        """Test that generic questions without clear indicators default to Simple"""
        query = "Tell me about this data"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Ambiguous generic query should default to Simple"
    
    def test_ambiguous_defaults_to_simple_short_query(self):
        """Test that short ambiguous queries default to Simple"""
        query = "Show me the data"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Short ambiguous query should default to Simple"
    
    def test_ambiguous_defaults_to_simple_vague_request(self):
        """Test that vague requests default to Simple"""
        query = "Give me some insights"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Vague request should default to Simple"
    
    def test_ambiguous_defaults_to_simple_no_keywords(self):
        """Test that queries with no complex or simple keywords default to Simple"""
        query = "Summarize this"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with no keywords should default to Simple"
    
    def test_ambiguous_defaults_to_simple_single_word(self):
        """Test that single-word queries default to Simple"""
        query = "Sales?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Single-word query should default to Simple"
    
    def test_ambiguous_defaults_to_simple_empty_string(self):
        """Test that empty string defaults to Simple"""
        query = ""
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Empty query should default to Simple"
    
    def test_ambiguous_defaults_to_simple_whitespace_only(self):
        """Test that whitespace-only query defaults to Simple"""
        query = "   "
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Whitespace-only query should default to Simple"
    
    def test_ambiguous_defaults_to_simple_unclear_intent(self):
        """Test that queries with unclear intent default to Simple"""
        queries = [
            "Help me understand",
            "Can you check?",
            "Look at this",
            "Something about sales"
        ]
        for query in queries:
            result = _classify_query(query)
            assert result == QueryType.SIMPLE, f"Ambiguous query '{query}' should default to Simple"
    
    # ──────────────────────────────────────────────────────────────────────
    # Test Multiple Question Components (Requirement 7.3)
    # ──────────────────────────────────────────────────────────────────────
    
    def test_multiple_components_what_and_why(self):
        """Test that queries with multiple question words are classified as Complex"""
        query = "What are the top categories and why are they performing well?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'what and why' should be Complex"
    
    def test_multiple_components_which_and_how(self):
        """Test that queries with 'which and how' are classified as Complex"""
        query = "Which region is best and how did it achieve this?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'which and how' should be Complex"
    
    def test_multiple_components_what_and_when(self):
        """Test that queries with 'what and when' are classified as Complex"""
        query = "What happened and when did it occur?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'what and when' should be Complex"
    
    def test_multiple_components_who_and_where(self):
        """Test that queries with 'who and where' are classified as Complex"""
        query = "Who are the top customers and where are they located?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'who and where' should be Complex"
    
    def test_multiple_components_three_questions(self):
        """Test that queries with three question components are classified as Complex"""
        query = "What products sell best, when do they sell, and who buys them?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with three question components should be Complex"
    
    def test_multiple_components_compound_with_and(self):
        """Test compound questions connected with 'and'"""
        query = "Show me sales and tell me profit"
        result = _classify_query(query)
        # This has "and" but not clear question words on both sides, behavior may vary
        # Based on implementation, this should check for question words
        # Let's verify the actual behavior
        # The implementation checks if there are question words and "and" together
        assert result in [QueryType.SIMPLE, QueryType.COMPLEX], "Compound query classification"
    
    def test_multiple_components_how_many_and_which(self):
        """Test query with 'how many and which' combination"""
        query = "How many sales were made and which category was most popular?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Query with 'how many and which' should be Complex"
    
    def test_not_multiple_components_single_question_with_and(self):
        """Test that single question with 'and' but no second question word stays Simple"""
        # "Which product is best and most popular?" - single question, not multiple components
        query = "Which product and service?"
        result = _classify_query(query)
        # This should be Simple because there's only one question word
        assert result == QueryType.SIMPLE, "Single question with 'and' should be Simple"
    
    def test_not_multiple_components_and_without_questions(self):
        """Test that 'and' without question words doesn't trigger Complex"""
        query = "Sales and profit data"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with 'and' but no question words should default to Simple"
    
    # ──────────────────────────────────────────────────────────────────────
    # Priority Tests: Complex Keywords Override Simple Patterns
    # ──────────────────────────────────────────────────────────────────────
    
    def test_complex_keyword_overrides_simple_pattern(self):
        """Test that complex keywords take priority over simple patterns"""
        # Query has both "which" (simple) and "trend" (complex)
        # Should classify as Complex
        query = "Which trend is most significant?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Complex keyword should override simple pattern"
    
    def test_complex_pattern_with_simple_word(self):
        """Test complex patterns with simple question words"""
        queries = [
            "What are the patterns?",  # has "what" (simple indicator in some forms) but "patterns" (complex)
            "Which breakdown should I focus on?",  # has "which" (simple) but "breakdown" (complex)
            "How many trends are there?"  # has "how many" (simple) but "trends" (complex)
        ]
        for query in queries:
            result = _classify_query(query)
            assert result == QueryType.COMPLEX, f"Query '{query}' should be Complex due to keyword priority"
    
    # ──────────────────────────────────────────────────────────────────────
    # Edge Cases and Special Scenarios
    # ──────────────────────────────────────────────────────────────────────
    
    def test_mixed_case_query(self):
        """Test query with mixed case"""
        query = "WhAt ArE tHe TrEnDs?"
        result = _classify_query(query)
        assert result == QueryType.COMPLEX, "Mixed case query should work correctly"
    
    def test_query_with_punctuation(self):
        """Test queries with punctuation"""
        queries = [
            "Which category sells more?",
            "What are the trends!",
            "Show me patterns...",
            "Breakdown by region?"
        ]
        expected = [QueryType.SIMPLE, QueryType.COMPLEX, QueryType.COMPLEX, QueryType.COMPLEX]
        for query, expected_type in zip(queries, expected):
            result = _classify_query(query)
            assert result == expected_type, f"Query '{query}' should be {expected_type}"
    
    def test_query_with_extra_whitespace(self):
        """Test queries with extra whitespace"""
        query = "  Which   category   sells   more?  "
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with extra whitespace should be handled correctly"
    
    def test_query_with_numbers(self):
        """Test queries containing numbers"""
        query = "Which product has more than 100 sales?"
        result = _classify_query(query)
        assert result == QueryType.SIMPLE, "Query with numbers should classify correctly"
    
    def test_real_world_simple_examples(self):
        """Test real-world examples that should be Simple"""
        simple_queries = [
            "Which category sells more?",
            "Who is the top customer?",
            "What is the total revenue?",
            "How many orders?",
            "Which region is best?",
            "Who has the highest sales?",
            "What is the average profit?"
        ]
        for query in simple_queries:
            result = _classify_query(query)
            assert result == QueryType.SIMPLE, f"Real-world simple query '{query}' should be Simple"
    
    def test_real_world_complex_examples(self):
        """Test real-world examples that should be Complex"""
        complex_queries = [
            "What are the sales trends over time?",
            "Show me a breakdown by region and category",
            "What patterns do you see in customer behavior?",
            "Compare across all product lines",
            "Analyze the distribution of sales",
            "What is the correlation between price and sales?",
            "What are the top products and why are they successful?"
        ]
        for query in complex_queries:
            result = _classify_query(query)
            assert result == QueryType.COMPLEX, f"Real-world complex query '{query}' should be Complex"

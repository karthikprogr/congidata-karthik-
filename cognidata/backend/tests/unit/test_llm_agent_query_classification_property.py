"""
Property-based tests for query classification in llm_agent.py

This module tests Property 2: Query classification correctness
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

Property 2: Query classification correctness
- For any query containing complexity keywords ("trend", "pattern", "breakdown", 
  "compare across", "over time", "analysis", "correlation", "distribution"), 
  classification SHALL be Complex
- For any query containing only simple comparison words ("which", "who", "what") 
  without modifiers, classification SHALL be Simple
- For any query with multiple question components (e.g., "what and why"), 
  classification SHALL be Complex
- For any ambiguous query, classification SHALL default to Simple
"""
import pytest
from hypothesis import given, strategies as st, assume, example
from services.agents.llm_agent import _classify_query, QueryType


class TestQueryClassificationProperty:
    """Property-based tests for query classification"""
    
    # ── Property 2.1: Complex keyword detection ───────────────────────────────
    
    @given(
        keyword=st.sampled_from([
            "trend", "pattern", "breakdown", "compare across",
            "over time", "analysis", "correlation", "distribution"
        ]),
        prefix=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", 
                      min_size=0, max_size=20),
        suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ?!.", 
                      min_size=0, max_size=20)
    )
    @example(keyword="trend", prefix="What is the sales ", suffix=" over time?")
    @example(keyword="pattern", prefix="Show me ", suffix=" in the data")
    @example(keyword="breakdown", prefix="Give me a ", suffix=" by region")
    def test_property_complex_keyword_detection(self, keyword, prefix, suffix):
        """
        Property 2.1: Query classification correctness - Complex keywords
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any query containing complexity keywords ("trend", "pattern", 
        "breakdown", "compare across", "over time", "analysis", "correlation", 
        "distribution"), classification SHALL be Complex.
        """
        query = f"{prefix}{keyword}{suffix}"
        
        # Skip empty or whitespace-only queries
        assume(query.strip() != "")
        
        result = _classify_query(query)
        
        assert result == QueryType.COMPLEX, (
            f"Query containing complex keyword '{keyword}' should be classified as COMPLEX. "
            f"Query: '{query}', Result: {result}"
        )
    
    # ── Property 2.2: Simple comparison word detection ────────────────────────
    
    @given(
        comparison_word=st.sampled_from(["which", "who", "what is", "how many"]),
        context=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", 
                       min_size=0, max_size=30)
    )
    @example(comparison_word="which", context="category sells more")
    @example(comparison_word="who", context="is the top customer")
    @example(comparison_word="what is", context="the total sales")
    @example(comparison_word="how many", context="orders are there")
    def test_property_simple_comparison_detection(self, comparison_word, context):
        """
        Property 2.2: Query classification correctness - Simple comparisons
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any query containing only simple comparison words ("which", "who", 
        "what is", "how many") without modifiers or complexity keywords, 
        classification SHALL be Simple.
        """
        query = f"{comparison_word} {context}"
        
        # Skip empty contexts
        assume(context.strip() != "")
        
        # Ensure query doesn't contain complex keywords
        complex_keywords = [
            "trend", "pattern", "breakdown", "compare across",
            "over time", "analysis", "correlation", "distribution"
        ]
        assume(not any(kw in query.lower() for kw in complex_keywords))
        
        # Ensure query doesn't have multiple question components
        q_lower = query.lower()
        if " and " in q_lower:
            question_words = ["what", "which", "how", "why", "where", "who", "when"]
            parts = q_lower.split(" and ")
            if len(parts) >= 2:
                has_question_before = any(word in parts[0] for word in question_words)
                has_question_after = any(word in " and ".join(parts[1:]) for word in question_words)
                assume(not (has_question_before and has_question_after))
        
        result = _classify_query(query)
        
        assert result == QueryType.SIMPLE, (
            f"Query with simple comparison word '{comparison_word}' should be classified as SIMPLE. "
            f"Query: '{query}', Result: {result}"
        )
    
    # ── Property 2.3: Multiple question components detection ──────────────────
    
    @given(
        first_question=st.sampled_from([
            "what is the total", "which category", "how many orders", 
            "who is the customer", "where are the sales"
        ]),
        second_question=st.sampled_from([
            "why is it high", "what is the reason", "which region", 
            "how does it compare", "when did it happen"
        ])
    )
    @example(first_question="what is the total", second_question="why is it high")
    @example(first_question="which category", second_question="what is the reason")
    def test_property_multiple_question_components(self, first_question, second_question):
        """
        Property 2.3: Query classification correctness - Multiple components
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any query containing multiple question components connected by "and"
        with question words on both sides, classification SHALL be Complex.
        """
        query = f"{first_question} and {second_question}"
        
        result = _classify_query(query)
        
        assert result == QueryType.COMPLEX, (
            f"Query with multiple question components should be classified as COMPLEX. "
            f"Query: '{query}', Result: {result}"
        )
    
    # ── Property 2.4: Default to Simple for ambiguous queries ─────────────────
    
    @given(
        query_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ?!.", 
            min_size=5, 
            max_size=50
        )
    )
    @example(query_text="tell me something")
    @example(query_text="show data")
    @example(query_text="I want to see info")
    def test_property_default_to_simple_for_ambiguous(self, query_text):
        """
        Property 2.4: Query classification correctness - Default behavior
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
        
        For any ambiguous query that doesn't contain complex keywords, simple
        comparison words, or multiple question components, classification SHALL
        default to Simple.
        """
        # Ensure query doesn't contain complex keywords
        complex_keywords = [
            "trend", "pattern", "breakdown", "compare across",
            "over time", "analysis", "correlation", "distribution"
        ]
        assume(not any(kw in query_text.lower() for kw in complex_keywords))
        
        # Ensure query doesn't contain simple comparison patterns
        simple_patterns = [r'\bwhich\b', r'\bwho\b', r'\bwhat is\b', r'\bhow many\b']
        import re
        assume(not any(re.search(pattern, query_text.lower()) for pattern in simple_patterns))
        
        # Ensure query doesn't have multiple question components
        q_lower = query_text.lower()
        if " and " in q_lower:
            question_words = ["what", "which", "how", "why", "where", "who", "when"]
            parts = q_lower.split(" and ")
            if len(parts) >= 2:
                has_question_before = any(word in parts[0] for word in question_words)
                has_question_after = any(word in " and ".join(parts[1:]) for word in question_words)
                assume(not (has_question_before and has_question_after))
        
        # Skip empty queries
        assume(query_text.strip() != "")
        
        result = _classify_query(query_text)
        
        assert result == QueryType.SIMPLE, (
            f"Ambiguous query should default to SIMPLE. "
            f"Query: '{query_text}', Result: {result}"
        )
    
    # ── Property 2.5: Case insensitivity ──────────────────────────────────────
    
    @given(
        keyword=st.sampled_from([
            "trend", "pattern", "breakdown", "compare across",
            "over time", "analysis", "correlation", "distribution"
        ]),
        case_variant=st.sampled_from([str.upper, str.lower, str.title, str.swapcase])
    )
    @example(keyword="trend", case_variant=str.upper)
    @example(keyword="pattern", case_variant=str.title)
    def test_property_case_insensitive_classification(self, keyword, case_variant):
        """
        Property 2.5: Query classification correctness - Case insensitivity
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any complex keyword in any case variation (UPPER, lower, Title, etc.),
        classification SHALL correctly identify it as Complex.
        """
        query = f"What is the {case_variant(keyword)} here?"
        
        result = _classify_query(query)
        
        assert result == QueryType.COMPLEX, (
            f"Query with complex keyword '{case_variant(keyword)}' should be classified as COMPLEX "
            f"regardless of case. Query: '{query}', Result: {result}"
        )
    
    # ── Property 2.6: Keyword position independence ───────────────────────────
    
    @given(
        keyword=st.sampled_from(["trend", "pattern", "breakdown", "analysis"]),
        position=st.sampled_from(["start", "middle", "end"])
    )
    @example(keyword="trend", position="start")
    @example(keyword="pattern", position="middle")
    @example(keyword="breakdown", position="end")
    def test_property_keyword_position_independence(self, keyword, position):
        """
        Property 2.6: Query classification correctness - Position independence
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any complex keyword appearing at any position in the query (start,
        middle, or end), classification SHALL correctly identify it as Complex.
        """
        if position == "start":
            query = f"{keyword} of sales data"
        elif position == "middle":
            query = f"Show me the {keyword} of sales"
        else:  # end
            query = f"I want to see the {keyword}"
        
        result = _classify_query(query)
        
        assert result == QueryType.COMPLEX, (
            f"Query with complex keyword '{keyword}' at {position} should be classified as COMPLEX. "
            f"Query: '{query}', Result: {result}"
        )
    
    # ── Property 2.7: Simple query without modifiers ──────────────────────────
    
    @given(
        simple_word=st.sampled_from(["which", "who"]),
        noun=st.sampled_from(["category", "product", "customer", "region", "seller"])
    )
    @example(simple_word="which", noun="category")
    @example(simple_word="who", noun="customer")
    def test_property_simple_word_without_modifiers(self, simple_word, noun):
        """
        Property 2.7: Query classification correctness - Simple words unmodified
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any query with simple comparison words (which, who) followed by a
        simple noun without complexity keywords, classification SHALL be Simple.
        """
        query = f"{simple_word} {noun}"
        
        result = _classify_query(query)
        
        assert result == QueryType.SIMPLE, (
            f"Simple query '{query}' should be classified as SIMPLE. Result: {result}"
        )
    
    # ── Property 2.8: Conjunction without multiple questions ──────────────────
    
    @given(
        base_query=st.sampled_from([
            "which category", "who is top", "what is total", "how many items"
        ]),
        conjunction_part=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", 
            min_size=3, 
            max_size=15
        )
    )
    @example(base_query="which category", conjunction_part="sells products")
    def test_property_conjunction_without_multiple_questions(self, base_query, conjunction_part):
        """
        Property 2.8: Query classification correctness - Conjunction handling
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any query with "and" that does NOT have question words on both sides,
        classification SHALL follow the primary query pattern (Simple if it 
        contains simple comparison words).
        """
        # Ensure conjunction part doesn't contain question words
        question_words = ["what", "which", "how", "why", "where", "who", "when"]
        assume(not any(word in conjunction_part.lower() for word in question_words))
        
        # Ensure no complex keywords
        complex_keywords = [
            "trend", "pattern", "breakdown", "compare across",
            "over time", "analysis", "correlation", "distribution"
        ]
        assume(not any(kw in conjunction_part.lower() for kw in complex_keywords))
        
        query = f"{base_query} and {conjunction_part}"
        
        result = _classify_query(query)
        
        assert result == QueryType.SIMPLE, (
            f"Query with single question component should be classified as SIMPLE. "
            f"Query: '{query}', Result: {result}"
        )


# ── Specific edge case tests ─────────────────────────────────────────────────

class TestQueryClassificationEdgeCases:
    """Edge case tests for query classification"""
    
    def test_empty_string(self):
        """Empty string should default to SIMPLE"""
        result = _classify_query("")
        assert result == QueryType.SIMPLE
    
    def test_whitespace_only(self):
        """Whitespace-only query should default to SIMPLE"""
        result = _classify_query("   \t\n  ")
        assert result == QueryType.SIMPLE
    
    def test_complex_keyword_as_substring(self):
        """Complex keyword as part of larger word should still trigger COMPLEX"""
        # "trend" appears in "trending"
        result = _classify_query("What is trending")
        assert result == QueryType.COMPLEX
    
    def test_simple_with_punctuation(self):
        """Simple query with punctuation should remain SIMPLE"""
        result = _classify_query("Which category?")
        assert result == QueryType.SIMPLE
    
    def test_complex_with_multiple_keywords(self):
        """Query with multiple complex keywords should be COMPLEX"""
        result = _classify_query("Show me the trend and pattern analysis")
        assert result == QueryType.COMPLEX
    
    def test_numeric_content(self):
        """Query with numbers should be classified based on other criteria"""
        result = _classify_query("which 5 categories")
        assert result == QueryType.SIMPLE
        
        result = _classify_query("trend over 5 years")
        assert result == QueryType.COMPLEX

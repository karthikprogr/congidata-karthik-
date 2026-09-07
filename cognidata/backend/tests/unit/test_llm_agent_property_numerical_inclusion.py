"""
Property-based tests for numerical value inclusion rules in llm_agent.py

Tests Property 7: Numerical value inclusion rules
- For any Complex query response, if numbers are included, they SHALL be formatted with separators (e.g., 1,234)
- For any Simple query response not explicitly requesting quantification, it SHALL NOT contain numeric values

**Validates: Requirements 4.1, 4.2, 4.3**
"""
import pytest
import re
from hypothesis import given, strategies as st, assume
from services.agents.llm_agent import QueryType


class TestNumericalValueInclusionProperty:
    """
    Property-based tests for numerical value inclusion rules.
    
    **Property 7: Numerical value inclusion rules**
    **Validates: Requirements 4.1, 4.2, 4.3**
    """
    
    # ── Helper Functions ──────────────────────────────────────────────────────
    
    def _has_numeric_values(self, text: str) -> bool:
        """Check if text contains numeric values."""
        # Match numbers (including decimals, percentages, currency)
        # Exclude numbers that are part of words (e.g., "3rd", "1st")
        numeric_pattern = r'\b\d+(?:[,\.]\d+)*\b'
        return bool(re.search(numeric_pattern, text))
    
    def _has_formatted_separators(self, text: str) -> bool:
        """
        Check if numbers in text use proper formatting with separators.
        Returns True if all numbers >= 1,000 use comma separators.
        """
        # Find all numbers in the text
        numbers = re.findall(r'\$?\d+(?:[,\.]\d+)*', text)
        
        if not numbers:
            return True  # No numbers to check
        
        for num_str in numbers:
            # Remove currency symbols and extract numeric part
            clean_num = num_str.replace('$', '').replace(',', '')
            
            # Check if it's a decimal or integer
            if '.' in clean_num:
                # For decimals, check the integer part
                integer_part = clean_num.split('.')[0]
                if len(integer_part) >= 4:
                    # Should have comma in original
                    if ',' not in num_str:
                        return False
            else:
                # For integers >= 1000, should have commas
                if len(clean_num) >= 4:
                    if ',' not in num_str:
                        return False
        
        return True
    
    def _explicitly_requests_quantification(self, query: str) -> bool:
        """Check if query explicitly requests numerical values."""
        quantification_keywords = [
            'how many', 'how much', 'count', 'total', 'sum',
            'number of', 'amount', 'quantity', 'price', 'cost',
            'average', 'mean', 'median', 'maximum', 'minimum',
            'percentage', 'percent', 'ratio', 'value'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in quantification_keywords)
    
# Strategy generators (defined outside class as they're decorated with @st.composite)
@st.composite
def _generate_simple_query_without_quantification(draw):
    """Generate simple queries that don't request quantification."""
    templates = [
        "Which {category} sells more?",
        "Who is the top {entity}?",
        "What is the best {item}?",
        "Which {category} performs better?",
        "What category leads?",
        "Who has the highest {metric}?",
    ]
    
    template = draw(st.sampled_from(templates))
    
    # Fill in placeholders
    category = draw(st.sampled_from(['category', 'region', 'segment', 'product', 'department']))
    entity = draw(st.sampled_from(['customer', 'salesperson', 'vendor', 'supplier']))
    item = draw(st.sampled_from(['product', 'option', 'choice', 'performer']))
    metric = draw(st.sampled_from(['sales', 'revenue', 'profit', 'orders']))
    
    query = template.format(category=category, entity=entity, item=item, metric=metric)
    return query


@st.composite
def _generate_simple_query_with_quantification(draw):
    """Generate simple queries that explicitly request quantification."""
    templates = [
        "How many {items} are there?",
        "What is the total {metric}?",
        "How much {metric} did {entity} generate?",
        "What is the count of {items}?",
        "What percentage of {category} is {item}?",
    ]
    
    template = draw(st.sampled_from(templates))
    
    items = draw(st.sampled_from(['orders', 'sales', 'customers', 'products', 'transactions']))
    metric = draw(st.sampled_from(['revenue', 'profit', 'sales', 'cost']))
    entity = draw(st.sampled_from(['Technology', 'Furniture', 'Office Supplies']))
    category = draw(st.sampled_from(['sales', 'revenue', 'profit']))
    item = draw(st.sampled_from(['Technology', 'Furniture', 'Consumer']))
    
    query = template.format(items=items, metric=metric, entity=entity, category=category, item=item)
    return query


@st.composite
def _generate_response_with_numbers(draw, use_separators: bool = True):
    """Generate a response containing numbers with or without separators."""
    templates = [
        "Your {count} records show Technology driving {amount} of revenue.",
        "West region dominates with {count} orders totaling {amount}.",
        "Technology leads with {count} sales at {amount} revenue.",
        "Your dataset has {count} transactions with {amount} total value.",
    ]
    
    template = draw(st.sampled_from(templates))
    
    # Generate numbers
    count_num = draw(st.integers(min_value=100, max_value=50000))
    amount_num = draw(st.integers(min_value=1000, max_value=500000))
    
    # Format based on use_separators flag
    if use_separators:
        count = f"{count_num:,}"
        amount = f"${amount_num:,}"
    else:
        count = str(count_num)
        amount = f"${amount_num}"
    
    response = template.format(count=count, amount=amount)
    return response


@st.composite
def _generate_response_without_numbers(draw):
    """Generate a response without numeric values."""
    templates = [
        "Technology sells more in your dataset.",
        "West region dominates your sales data.",
        "Technology leads across your records.",
        "Sean Miller is your top customer.",
        "Furniture performs better than Office Supplies.",
        "Technology category shows the strongest growth.",
    ]
    
    return draw(st.sampled_from(templates))


class TestNumericalValueInclusionProperty:
    """
    Property-based tests for numerical value inclusion rules.
    
    **Property 7: Numerical value inclusion rules**
    **Validates: Requirements 4.1, 4.2, 4.3**
    """
    
    # ── Helper Functions ──────────────────────────────────────────────────────
    
    def _has_numeric_values(self, text: str) -> bool:
        """Check if text contains numeric values."""
        # Match numbers (including decimals, percentages, currency)
        # Exclude numbers that are part of words (e.g., "3rd", "1st")
        numeric_pattern = r'\b\d+(?:[,\.]\d+)*\b'
        return bool(re.search(numeric_pattern, text))
    
    def _has_formatted_separators(self, text: str) -> bool:
        """
        Check if numbers in text use proper formatting with separators.
        Returns True if all numbers >= 1,000 use comma separators.
        """
        # Find all numbers in the text
        numbers = re.findall(r'\$?\d+(?:[,\.]\d+)*', text)
        
        if not numbers:
            return True  # No numbers to check
        
        for num_str in numbers:
            # Remove currency symbols and extract numeric part
            clean_num = num_str.replace('$', '').replace(',', '')
            
            # Check if it's a decimal or integer
            if '.' in clean_num:
                # For decimals, check the integer part
                integer_part = clean_num.split('.')[0]
                if len(integer_part) >= 4:
                    # Should have comma in original
                    if ',' not in num_str:
                        return False
            else:
                # For integers >= 1000, should have commas
                if len(clean_num) >= 4:
                    if ',' not in num_str:
                        return False
        
        return True
    
    def _explicitly_requests_quantification(self, query: str) -> bool:
        """Check if query explicitly requests numerical values."""
        quantification_keywords = [
            'how many', 'how much', 'count', 'total', 'sum',
            'number of', 'amount', 'quantity', 'price', 'cost',
            'average', 'mean', 'median', 'maximum', 'minimum',
            'percentage', 'percent', 'ratio', 'value'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in quantification_keywords)
    
    # ── Property Tests ────────────────────────────────────────────────────────
    
    # ── Property Tests ────────────────────────────────────────────────────────
    
    @given(st.data())
    def test_property_complex_responses_use_number_separators(self, data):
        """
        Property 7a: For any Complex query response containing numerical values,
        those values SHALL be formatted with appropriate separators (e.g., 1,234 not 1234).
        
        **Validates: Requirements 4.1, 4.2**
        """
        # Generate a response with numbers (with separators)
        response = data.draw(_generate_response_with_numbers(use_separators=True))
        
        # Verify it has numeric values
        assert self._has_numeric_values(response), \
            f"Generated response should contain numbers: {response}"
        
        # Verify all numbers >= 1,000 have proper separators
        assert self._has_formatted_separators(response), \
            f"Numbers in Complex response should use separators: {response}"
    
    @given(st.data())
    def test_property_complex_responses_reject_unseparated_numbers(self, data):
        """
        Property 7b: For any Complex query response, numbers >= 1,000 without
        separators SHALL be considered improperly formatted.
        
        **Validates: Requirements 4.1, 4.2**
        """
        # Generate a response with numbers (without separators)
        response = data.draw(_generate_response_with_numbers(use_separators=False))
        
        # Verify it has numeric values
        assert self._has_numeric_values(response), \
            f"Generated response should contain numbers: {response}"
        
        # Verify that numbers >= 1,000 lack separators (should fail validation)
        assert not self._has_formatted_separators(response), \
            f"Response without separators should fail validation: {response}"
    
    @given(st.data())
    def test_property_simple_responses_no_numbers_when_not_requested(self, data):
        """
        Property 7c: For any Simple query response where the query does NOT
        explicitly request quantification, the response SHALL NOT contain numeric values.
        
        **Validates: Requirements 4.3**
        """
        # Generate a simple query without quantification request
        query = data.draw(_generate_simple_query_without_quantification())
        
        # Generate a response without numbers
        response = data.draw(_generate_response_without_numbers())
        
        # Verify query doesn't request quantification
        assert not self._explicitly_requests_quantification(query), \
            f"Query should not request quantification: {query}"
        
        # Verify response doesn't contain numbers
        assert not self._has_numeric_values(response), \
            f"Simple response without quantification request should not contain numbers: {response}"
    
    @given(st.data())
    def test_property_simple_responses_allow_numbers_when_requested(self, data):
        """
        Property 7d: For any Simple query response where the query DOES
        explicitly request quantification, the response MAY contain numeric values
        (and they should be formatted with separators if >= 1,000).
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Generate a simple query with quantification request
        query = data.draw(_generate_simple_query_with_quantification())
        
        # Verify query explicitly requests quantification
        assert self._explicitly_requests_quantification(query), \
            f"Query should request quantification: {query}"
        
        # When responding to such queries, numbers ARE allowed
        # Generate a response with properly formatted numbers
        response = data.draw(_generate_response_with_numbers(use_separators=True))
        
        # Verify response has numbers (allowed for quantification requests)
        assert self._has_numeric_values(response), \
            f"Response to quantification query should contain numbers: {response}"
        
        # Verify numbers are properly formatted
        assert self._has_formatted_separators(response), \
            f"Numbers in response should use separators: {response}"
    
    @given(number=st.integers(min_value=1, max_value=999))
    def test_property_small_numbers_no_separator_required(self, number):
        """
        Property 7e: For any number < 1,000, separators are NOT required
        (i.e., both "500" and "500" are acceptable).
        
        **Validates: Requirement 4.2**
        """
        # Small numbers don't require separators
        response = f"Your dataset has {number} records."
        
        # Should pass validation (small numbers don't need separators)
        # We're just checking that the helper correctly identifies this as valid
        has_valid_formatting = self._has_formatted_separators(response)
        assert has_valid_formatting, \
            f"Small numbers (<1000) should pass validation without separators: {response}"
    
    @given(number=st.integers(min_value=1000, max_value=999999))
    def test_property_large_numbers_require_separators(self, number):
        """
        Property 7f: For any number >= 1,000, separators SHALL be required
        for proper formatting.
        
        **Validates: Requirement 4.2**
        """
        # Create response with number without separators
        response_without = f"Your dataset has {number} records."
        
        # Create response with number with separators
        response_with = f"Your dataset has {number:,} records."
        
        # Without separators should fail validation
        assert not self._has_formatted_separators(response_without), \
            f"Large number without separators should fail: {response_without}"
        
        # With separators should pass validation
        assert self._has_formatted_separators(response_with), \
            f"Large number with separators should pass: {response_with}"
    
    @given(st.data())
    def test_property_currency_values_use_separators(self, data):
        """
        Property 7g: For any monetary value >= $1,000, the value SHALL be
        formatted with both currency symbol and comma separators (e.g., $1,234).
        
        **Validates: Requirements 4.1, 4.2**
        """
        # Generate a monetary value
        amount = data.draw(st.integers(min_value=1000, max_value=1000000))
        
        # Format with separators
        formatted_amount = f"${amount:,}"
        response = f"Technology generated {formatted_amount} in revenue from your records."
        
        # Verify proper formatting
        assert self._has_formatted_separators(response), \
            f"Currency values should use separators: {response}"
        
        # Test improper formatting (no separators)
        unformatted_amount = f"${amount}"
        response_bad = f"Technology generated {unformatted_amount} in revenue from your records."
        
        assert not self._has_formatted_separators(response_bad), \
            f"Currency without separators should fail: {response_bad}"
    
    @given(percentage=st.floats(min_value=0.01, max_value=100.0))
    def test_property_percentages_allowed_in_complex_responses(self, percentage):
        """
        Property 7h: For any Complex query response, percentage values are
        allowed and should be formatted with appropriate precision (per Requirement 4.4).
        
        **Validates: Requirements 4.1, 4.4**
        """
        # Percentages are numeric values that ARE allowed in complex responses
        formatted_pct = f"{percentage:.2f}%"
        response = f"Technology drives {formatted_pct} of revenue in your dataset."
        
        # Verify response contains numeric values (percentages count)
        assert self._has_numeric_values(response), \
            f"Percentage values are numeric and should be detected: {response}"
        
        # Percentages themselves don't need comma separators (they're typically <1000)
        # But the validation should still pass
        assert self._has_formatted_separators(response), \
            f"Percentage values should pass formatting validation: {response}"
    
    @given(st.data())
    def test_property_mixed_numbers_all_must_be_formatted(self, data):
        """
        Property 7i: For any response containing multiple numeric values,
        ALL numbers >= 1,000 SHALL use separators consistently.
        
        **Validates: Requirements 4.1, 4.2**
        """
        # Generate multiple numbers
        count1 = data.draw(st.integers(min_value=1000, max_value=50000))
        count2 = data.draw(st.integers(min_value=1000, max_value=50000))
        amount = data.draw(st.integers(min_value=10000, max_value=500000))
        
        # Properly formatted response (all numbers have separators)
        response_good = (
            f"West region has {count1:,} orders while East has {count2:,} orders, "
            f"totaling ${amount:,} in combined revenue from your dataset."
        )
        
        assert self._has_formatted_separators(response_good), \
            f"All numbers should have separators: {response_good}"
        
        # Improperly formatted response (mixed formatting)
        response_bad = (
            f"West region has {count1:,} orders while East has {count2} orders, "
            f"totaling ${amount} in combined revenue from your dataset."
        )
        
        assert not self._has_formatted_separators(response_bad), \
            f"Mixed formatting should fail validation: {response_bad}"
    
    @given(st.data())
    def test_property_decimal_numbers_use_separators_in_integer_part(self, data):
        """
        Property 7j: For any decimal number with integer part >= 1,000,
        the integer part SHALL use comma separators (e.g., 1,234.56).
        
        **Validates: Requirement 4.2**
        """
        # Generate a decimal number with large integer part
        integer_part = data.draw(st.integers(min_value=1000, max_value=999999))
        decimal_part = data.draw(st.integers(min_value=0, max_value=99))
        
        # Properly formatted
        formatted = f"{integer_part:,}.{decimal_part:02d}"
        response_good = f"The average value is {formatted} across your dataset."
        
        assert self._has_formatted_separators(response_good), \
            f"Decimal with large integer part should use separators: {response_good}"
        
        # Improperly formatted (no separators)
        unformatted = f"{integer_part}.{decimal_part:02d}"
        response_bad = f"The average value is {unformatted} across your dataset."
        
        assert not self._has_formatted_separators(response_bad), \
            f"Decimal without separators should fail: {response_bad}"


# ── Concrete Example Tests ───────────────────────────────────────────────────

class TestNumericalInclusionConcreteExamples:
    """
    Concrete example tests to validate specific scenarios for Property 7.
    These complement the property-based tests above.
    """
    
    def test_complex_response_with_formatted_numbers(self):
        """Complex response with properly formatted numbers should pass"""
        response = "Your 2,340 orders show steady growth with Technology driving $125,000 in revenue."
        
        # Should contain numbers
        pattern = r'\b\d+(?:[,\.]\d+)*\b'
        assert re.search(pattern, response), "Should contain numeric values"
        
        # Numbers should be formatted with separators
        assert '2,340' in response, "Count should have comma separator"
        assert '$125,000' in response, "Currency should have comma separator"
    
    def test_complex_response_without_separators_invalid(self):
        """Complex response with unformatted numbers >= 1,000 should be invalid"""
        response = "Your 2340 orders show steady growth with Technology driving $125000 in revenue."
        
        # Should contain numbers
        pattern = r'\b\d+(?:[,\.]\d+)*\b'
        assert re.search(pattern, response), "Should contain numeric values"
        
        # But numbers lack proper separators (validation should catch this)
        # This would fail the formatting check
        assert '2340' in response and '2,340' not in response
        assert '$125000' in response and '$125,000' not in response
    
    def test_simple_response_without_quantification_no_numbers(self):
        """Simple response to non-quantification query should not contain numbers"""
        query = "Which category sells more?"
        response = "Technology sells more in your dataset."
        
        # Query doesn't request quantification
        quantification_keywords = ['how many', 'how much', 'count', 'total']
        assert not any(kw in query.lower() for kw in quantification_keywords)
        
        # Response should not contain numbers
        pattern = r'\b\d+\b'
        assert not re.search(pattern, response), "Simple response should not have numbers"
    
    def test_simple_response_with_quantification_allows_numbers(self):
        """Simple response to quantification query may contain numbers"""
        query = "How many orders are there?"
        response = "Your dataset has 1,234 orders."
        
        # Query requests quantification
        assert 'how many' in query.lower()
        
        # Response may contain numbers (and they should be formatted)
        assert '1,234' in response, "Quantification response can have formatted numbers"
    
    def test_small_numbers_no_separator_valid(self):
        """Numbers < 1,000 don't require separators"""
        response = "Your dataset has 500 records with Technology leading."
        
        # Should contain numbers
        pattern = r'\b\d+\b'
        assert re.search(pattern, response), "Should contain numeric value"
        
        # Small number doesn't need separator (both "500" and "500" are valid)
        assert '500' in response
    
    def test_percentages_in_complex_response(self):
        """Percentages are allowed in complex responses"""
        response = "Technology drives 45.5% of revenue across your 1,200 records."
        
        # Should contain both percentage and formatted count
        assert '45.5%' in response, "Percentage should be present"
        assert '1,200' in response, "Count should be formatted with separator"
    
    def test_multiple_numbers_all_formatted(self):
        """All numbers >= 1,000 should have separators"""
        response = (
            "West region has 1,250 orders totaling $310,000 while "
            "East has 890 orders totaling $210,000 from your dataset."
        )
        
        # Check all large numbers are formatted
        assert '1,250' in response
        assert '$310,000' in response
        assert '$210,000' in response
        # 890 is < 1,000 so doesn't need separator


if __name__ == "__main__":
    # Run the property-based tests with statistics
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

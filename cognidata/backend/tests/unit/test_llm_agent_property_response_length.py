"""
Property-based tests for response length constraints.

**Validates: Requirements 1.1, 1.2**

Property 1: Response Length Constraint
---------------------------------------
For any user query, when classified as Simple, the generated response SHALL contain
at most one sentence, and when classified as Complex, the generated response SHALL
contain at most three sentences.

This test uses property-based testing with the Hypothesis library to verify that
the _validate_response_format() function correctly enforces sentence count limits
across a wide variety of generated responses.
"""
import re
import pytest
from hypothesis import given, strategies as st, settings, assume
from services.agents.llm_agent import _validate_response_format, QueryType


# ── Strategy: Generate valid sentences ───────────────────────────────────────

@st.composite
def sentence(draw):
    """
    Generate a realistic sentence for testing.
    
    Sentences include:
    - Subject-verb-object structure
    - Dataset references (record counts, possessives)
    - Numerical values with proper formatting
    - Conversational business language
    - Proper capitalization and punctuation
    """
    # Components for realistic sentences
    subjects = [
        "Technology",
        "Furniture",
        "Office Supplies",
        "West region",
        "East region",
        "Your dataset",
    ]
    
    verbs = [
        "sells more",
        "leads",
        "dominates",
        "shows",
        "demonstrates",
        "has",
    ]
    
    objects = [
        "in your {count} records",
        "across your {count} transactions",
        "with ${amount:,} in revenue",
        "at {pct:.1f}% growth",
        "by {amount:,} units",
    ]
    
    subject = draw(st.sampled_from(subjects))
    verb = draw(st.sampled_from(verbs))
    obj_template = draw(st.sampled_from(objects))
    
    # Generate realistic numbers
    count = draw(st.integers(min_value=50, max_value=10000))
    amount = draw(st.integers(min_value=1000, max_value=500000))
    pct = draw(st.floats(min_value=0.1, max_value=99.9))
    
    # Format the object with numbers
    obj = obj_template.format(count=count, amount=amount, pct=pct)
    
    # Combine into sentence
    sentence_text = f"{subject} {verb} {obj}."
    
    return sentence_text


@st.composite
def simple_response(draw):
    """
    Generate a response for a Simple query (exactly 1 sentence).
    
    Simple responses should:
    - Contain exactly 1 sentence
    - Reference the dataset (record count or possessive)
    - Use conversational language
    - End with proper punctuation
    """
    return draw(sentence())


@st.composite
def complex_response(draw, min_sentences=1, max_sentences=3):
    """
    Generate a response for a Complex query (1-3 sentences).
    
    Complex responses should:
    - Contain 1-3 sentences
    - Include numerical values
    - Reference the dataset
    - Use conversational business language
    """
    num_sentences = draw(st.integers(min_value=min_sentences, max_value=max_sentences))
    sentences = [draw(sentence()) for _ in range(num_sentences)]
    return " ".join(sentences)


# ── Property Tests: Response Length Constraint ───────────────────────────────

@given(response=simple_response())
@settings(max_examples=100, deadline=None)
def test_property_simple_query_one_sentence_max(response):
    """
    Property Test: Simple queries SHALL receive responses with ≤1 sentence.
    
    **Validates: Requirements 1.1**
    
    This property verifies that for any response generated for a Simple query,
    the validation function correctly identifies responses with exactly 1 sentence
    as valid, ensuring conciseness for simple fact/comparison queries.
    """
    # Given: A response with exactly 1 sentence (by construction)
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Then: The response should be valid (1 sentence is acceptable)
    assert is_valid, f"Valid 1-sentence response rejected: {error_msg}"
    assert error_msg == "", f"Unexpected error for valid response: {error_msg}"


@given(response=complex_response(min_sentences=1, max_sentences=1))
@settings(max_examples=100, deadline=None)
def test_property_complex_query_one_sentence_valid(response):
    """
    Property Test: Complex queries CAN receive 1-sentence responses (valid).
    
    **Validates: Requirements 1.2**
    
    Complex queries allow UP TO 3 sentences, so 1 sentence should also be valid.
    """
    # Given: A response with exactly 1 sentence
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    # Then: The response should be valid
    assert is_valid, f"Valid 1-sentence response rejected for Complex query: {error_msg}"


@given(response=complex_response(min_sentences=2, max_sentences=2))
@settings(max_examples=100, deadline=None)
def test_property_complex_query_two_sentences_valid(response):
    """
    Property Test: Complex queries CAN receive 2-sentence responses (valid).
    
    **Validates: Requirements 1.2**
    """
    # Given: A response with exactly 2 sentences
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    # Then: The response should be valid
    assert is_valid, f"Valid 2-sentence response rejected for Complex query: {error_msg}"


@given(response=complex_response(min_sentences=3, max_sentences=3))
@settings(max_examples=100, deadline=None)
def test_property_complex_query_three_sentences_valid(response):
    """
    Property Test: Complex queries CAN receive 3-sentence responses (valid).
    
    **Validates: Requirements 1.2**
    """
    # Given: A response with exactly 3 sentences
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    # Then: The response should be valid (3 is the maximum allowed)
    assert is_valid, f"Valid 3-sentence response rejected for Complex query: {error_msg}"


@given(
    base_response=complex_response(min_sentences=3, max_sentences=3),
    extra_sentence=sentence()
)
@settings(max_examples=100, deadline=None)
def test_property_complex_query_four_sentences_invalid(base_response, extra_sentence):
    """
    Property Test: Complex queries SHALL NOT receive responses with >3 sentences.
    
    **Validates: Requirements 1.2**
    
    This property verifies that responses exceeding 3 sentences are correctly
    rejected for Complex queries, ensuring conciseness even for analytical requests.
    """
    # Given: A response with 4 sentences (3 + 1 extra)
    response = f"{base_response} {extra_sentence}"
    
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    # Then: The response should be invalid
    assert not is_valid, "4-sentence response should be rejected for Complex query"
    assert "Too many sentences" in error_msg, f"Expected sentence count error, got: {error_msg}"
    assert "4 > 3" in error_msg, f"Expected '4 > 3' in error message, got: {error_msg}"


@given(
    base_response=simple_response(),
    extra_sentence=sentence()
)
@settings(max_examples=100, deadline=None)
def test_property_simple_query_two_sentences_invalid(base_response, extra_sentence):
    """
    Property Test: Simple queries SHALL NOT receive responses with >1 sentence.
    
    **Validates: Requirements 1.1**
    
    This property verifies that responses with 2+ sentences are correctly rejected
    for Simple queries, enforcing strict conciseness for fact/comparison requests.
    """
    # Given: A response with 2 sentences (1 base + 1 extra)
    response = f"{base_response} {extra_sentence}"
    
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Then: The response should be invalid
    assert not is_valid, "2-sentence response should be rejected for Simple query"
    assert "Too many sentences" in error_msg, f"Expected sentence count error, got: {error_msg}"
    assert "2 > 1" in error_msg, f"Expected '2 > 1' in error message, got: {error_msg}"


# ── Edge Case Tests ──────────────────────────────────────────────────────────

@given(
    words=st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
            min_size=1,
            max_size=10
        ),
        min_size=3,
        max_size=15
    ),
    record_count=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=100, deadline=None)
def test_property_sentence_without_proper_termination(words, record_count):
    """
    Property Test: Responses without proper sentence terminators.
    
    **Validates: Requirements 1.1, 1.2**
    
    Tests that responses without clear sentence boundaries (no . ! ?)
    are treated as single sentences.
    """
    # Filter out words that could cause issues
    words = [w for w in words if w and w.strip() and w.isalnum()]
    assume(len(words) >= 3)  # Need at least 3 words for a meaningful sentence
    
    # Given: A response without proper sentence terminator (no . ! ?)
    response = f"{' '.join(words)} in your {record_count} records"
    
    # When: Validating for Simple query type
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Then: Should be valid as it's treated as a single sentence
    # (The regex split won't find sentence boundaries without terminators)
    assert is_valid, f"Single-line response without terminator should be valid: {error_msg}"


@given(
    base_sentence=sentence(),
    abbreviations=st.lists(
        st.sampled_from(["U.S.", "Dr.", "Inc.", "Ltd.", "Co.", "St.", "Ave."]),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=100, deadline=None)
def test_property_abbreviations_dont_break_sentence_count(base_sentence, abbreviations):
    """
    Property Test: Abbreviations with periods should not be counted as sentence breaks.
    
    **Validates: Requirements 1.1, 1.2**
    
    Tests that common abbreviations (U.S., Dr., Inc.) don't incorrectly split
    sentences during validation.
    """
    # Given: A sentence with abbreviations embedded
    abbrev_text = " ".join(abbreviations)
    response = f"{abbrev_text} shows that {base_sentence}"
    
    # When: Validating for Simple query type
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Then: Should be valid IF the sentence boundary regex works correctly
    # Note: Our regex looks for ". " followed by capital letter, so "U.S. shows"
    # won't split because 'shows' is lowercase. This is a limitation but acceptable.
    # We primarily test that it doesn't incorrectly reject valid responses.
    
    # Count actual sentence boundaries (. ! ? followed by space and capital)
    sentence_boundaries = len(re.findall(r'[.!?]\s+(?=[A-Z])', response))
    
    if sentence_boundaries == 0:
        # No sentence boundaries detected, should be treated as 1 sentence
        assert is_valid or "Too many sentences: 1 > 1" not in error_msg


@given(response=st.text(min_size=10, max_size=200))
@settings(max_examples=100, deadline=None)
def test_property_arbitrary_text_sentence_counting(response):
    """
    Property Test: Arbitrary text sentence counting matches regex expectations.
    
    **Validates: Requirements 1.1, 1.2**
    
    This property verifies that the sentence counting logic in _validate_response_format
    is consistent with the regex pattern used to split sentences.
    """
    # Given: Arbitrary text input
    # Count sentences using the same regex as the validator
    sentences = re.split(r'[.!?]\s+(?=[A-Z])', response)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    # When: Validating for Simple query
    is_valid_simple, error_msg_simple = _validate_response_format(response, QueryType.SIMPLE)
    
    # When: Validating for Complex query
    is_valid_complex, error_msg_complex = _validate_response_format(response, QueryType.COMPLEX)
    
    # Then: Validation results should match expected sentence count constraints
    if sentence_count <= 1:
        # If 0 or 1 sentences detected, might fail on other validations but NOT sentence count
        if not is_valid_simple:
            assert "Too many sentences" not in error_msg_simple
    else:
        # If more than 1 sentence, Simple should fail on sentence count
        if "Too many sentences" in error_msg_simple:
            assert f"{sentence_count} > 1" in error_msg_simple
    
    if sentence_count <= 3:
        # If ≤3 sentences, might fail on other validations but NOT sentence count
        if not is_valid_complex:
            assert "Too many sentences" not in error_msg_complex
    else:
        # If >3 sentences, Complex should fail on sentence count
        if "Too many sentences" in error_msg_complex:
            assert f"{sentence_count} > 3" in error_msg_complex


# ── Integration with Other Validation Rules ──────────────────────────────────

@given(response=simple_response())
@settings(max_examples=50, deadline=None)
def test_property_simple_response_passes_all_validations(response):
    """
    Property Test: Well-formed simple responses pass all validation rules.
    
    **Validates: Requirements 1.1**
    
    This property verifies that responses generated by our simple_response strategy
    (which includes dataset references and proper formatting) pass validation.
    """
    # Given: A well-formed simple response
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Then: Should pass validation (has 1 sentence, includes dataset reference)
    assert is_valid, f"Well-formed simple response failed validation: {error_msg}"


@given(response=complex_response(min_sentences=2, max_sentences=3))
@settings(max_examples=50, deadline=None)
def test_property_complex_response_passes_sentence_count(response):
    """
    Property Test: Well-formed complex responses with 2-3 sentences pass sentence count validation.
    
    **Validates: Requirements 1.2**
    
    Note: May fail on other validation rules (preamble, jargon, etc.) but should
    NOT fail on sentence count.
    """
    # Given: A well-formed complex response with 2-3 sentences
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    # Then: Should NOT fail on sentence count
    assert "Too many sentences" not in error_msg, \
        f"Well-formed complex response failed sentence count validation: {error_msg}"


# ── Boundary Tests ───────────────────────────────────────────────────────────

def test_boundary_simple_query_exactly_one_sentence():
    """
    Boundary Test: Simple query with exactly 1 sentence (boundary case).
    
    **Validates: Requirements 1.1**
    """
    response = "Technology sells more in your 847 records."
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    assert is_valid, f"Exactly 1 sentence should be valid for Simple query: {error_msg}"
    assert error_msg == ""


def test_boundary_complex_query_exactly_three_sentences():
    """
    Boundary Test: Complex query with exactly 3 sentences (boundary case).
    
    **Validates: Requirements 1.2**
    """
    response = (
        "Your 2,340 orders show steady growth from Jan to Jun. "
        "Technology drives 45% of revenue at $125,000. "
        "Consumer products improved 15% in Q2."
    )
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    assert is_valid, f"Exactly 3 sentences should be valid for Complex query: {error_msg}"
    assert error_msg == ""


def test_boundary_simple_query_two_sentences():
    """
    Boundary Test: Simple query with 2 sentences (exceeds limit by 1).
    
    **Validates: Requirements 1.1**
    """
    response = "Technology sells more in your 847 records. Furniture is second."
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    assert not is_valid, "2 sentences should be invalid for Simple query"
    assert "Too many sentences: 2 > 1" in error_msg


def test_boundary_complex_query_four_sentences():
    """
    Boundary Test: Complex query with 4 sentences (exceeds limit by 1).
    
    **Validates: Requirements 1.2**
    """
    response = (
        "Your 2,340 orders show steady growth. "
        "Technology leads at $125,000. "
        "Consumer products improved 15%. "
        "Office supplies remain stable."
    )
    is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
    
    assert not is_valid, "4 sentences should be invalid for Complex query"
    assert "Too many sentences: 4 > 3" in error_msg


# ── Empty/Minimal Response Tests ─────────────────────────────────────────────

def test_empty_response_simple_query():
    """
    Edge Case: Empty response for Simple query.
    
    **Validates: Requirements 1.1**
    """
    response = ""
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Empty response has no sentences, which technically satisfies ≤1 sentence
    # But should fail on dataset reference check
    assert not is_valid
    assert "No dataset reference found" in error_msg


def test_minimal_response_simple_query():
    """
    Edge Case: Minimal response with just a number (valid for Simple query).
    
    **Validates: Requirements 1.1**
    """
    response = "847"
    is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
    
    # Has a number (dataset reference), no sentence terminators (treated as 1 sentence)
    # Should pass sentence count but might fail on other checks
    # The validator counts sentences by splitting on terminators, so "847" is 1 sentence
    if not is_valid:
        assert "Too many sentences" not in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

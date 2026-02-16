from inference.models.classification import ClassificationResult


def test_classification_result_exposes_only_category_centric_fields():
    result = ClassificationResult(
        category_id="simple",
        category_name="Simple",
        reasoning="quick factual lookup",
        confidence=0.8,
    )

    payload = result.model_dump()
    assert payload["category_id"] == "simple"
    assert payload["category_name"] == "Simple"
    assert "complexity" not in payload
    assert "suggested_model_tier" not in payload

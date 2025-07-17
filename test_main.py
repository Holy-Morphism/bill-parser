from fastapi.testclient import TestClient
from main import app
import os
import json
from fuzzywuzzy import fuzz


client: TestClient = TestClient(app)


def test_extract_bills():

    with open("tests/expected_results.json") as f:
        expected_results = json.load(f)

    test_files = []
    for i in range(14):
        file_name = f"tests/data/test{i+1}.pdf"
        file = open(file_name, "rb")
        test_files.append(("bills", (file_name, file, "application/pdf")))

    response = client.post("/extract-bills", files=test_files)

    for _, (name, f, _) in test_files:
        f.close()

    # Check response
    assert response.status_code == 200

    response_data = response.json()

    results = response_data["results"]

    assert len(results) == 14

    for i, (actual, predicted) in enumerate(zip(expected_results["results"], results)):
        print(f"\n--- Item {i+1} ---")
        print(f"Predicted: {json.dumps(predicted, indent=2)}")
        print(f"Actual: {json.dumps(actual, indent=2)}")

        predicted_json = json.loads(predicted)

        # Extract date components (they're already dictionaries, not strings)
        predicted_prev = predicted_json["previous_date"]
        predicted_curr = predicted_json["current_date"]

        # Extract expected date components
        expected_prev = actual["previous_date"]
        expected_curr = actual["current_date"]

        # Assert date comparisons
        assert (
            predicted_prev["month"] == expected_prev["month"]
        ), f"Previous month mismatch: {predicted_prev['month']} != {expected_prev['month']}"
        assert (
            predicted_prev["day"] == expected_prev["day"]
        ), f"Previous day mismatch: {predicted_prev['day']} != {expected_prev['day']}"
        assert (
            predicted_prev["year"] == expected_prev["year"]
        ), f"Previous year mismatch: {predicted_prev['year']} != {expected_prev['year']}"

        assert (
            predicted_curr["month"] == expected_curr["month"]
        ), f"Current month mismatch: {predicted_curr['month']} != {expected_curr['month']}"
        assert (
            predicted_curr["day"] == expected_curr["day"]
        ), f"Current day mismatch: {predicted_curr['day']} != {expected_curr['day']}"
        assert (
            predicted_curr["year"] == expected_curr["year"]
        ), f"Current year mismatch: {predicted_curr['year']} != {expected_curr['year']}"

        # Compare consumption (with some tolerance for floating point differences)
        assert (
            abs(predicted_json["consumption"] - actual["consumption"]) < 0.01
        ), f"Consumption mismatch: {predicted_json['consumption']} != {actual['consumption']}"

        # Compare bill amount (check both 'total_bill' and 'current_bill' fields)
        predicted_bill = predicted_json.get(
            "total_bill", predicted_json.get("current_bill", 0)
        )
        assert (
            abs(predicted_bill - actual["current_bill"]) < 0.01
        ), f"Bill amount mismatch: {predicted_bill} != {actual['current_bill']}"

        print(f"✓ Item {i+1} passed all assertions")

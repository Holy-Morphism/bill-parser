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

    response = client.post(
        "/extract-bills", files=test_files
    )

    for _, (name, f, _) in test_files:
        f.close()

    # Check response
    assert response.status_code == 200
    
    # Debug: Print the entire response to see the structure
    print("Full response:")
    print(response.json())
    
    response_data = response.json()
    
    # Check if 'results' key exists
    if "results" in response_data:
        results = response_data["results"]
    else:
        print("Available keys in response:", list(response_data.keys()))
        # Maybe the results are directly in the response or under a different key
        results = response_data  # Try this if results are directly returned
    
    print(f"Results type: {type(results)}")
    print(f"Results length: {len(results) if isinstance(results, list) else 'Not a list'}")
    
    if isinstance(results, list) and len(results) > 0:
        print(f"First result type: {type(results[0])}")
        print(f"First result: {results[0]}")

    assert len(results) == 14
    for i, (expected,actual) in enumerate(zip(results, expected_results["results"])):
        print(f"\n--- Item {i+1} ---")
        print(f"Expected: {expected}")
        print(f"Actual: {actual}")  # Change this line - was using undefined actual_str
        print(f"Actual type: {type(actual)}")
        
        actual = json.loads(actual)  # Parse the JSON string
        assert fuzz.ratio(actual["previous_date"], expected["start_date"]) >= 80
        assert fuzz.ratio(actual["current_date"], expected["end_date"]) >= 80
   
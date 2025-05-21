import requests
import json
from typing import Dict, Any

def test_code_execution(url: str, code: str, tests: list, timeout: int = 5) -> Dict[str, Any]:
    """
    Test code execution with given tests
    """
    payload = {
        "code": code,
        "tests": tests,
        "timeout": timeout
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def print_result(result: Dict[str, Any]) -> None:
    """
    Pretty print the test results
    """
    if not result:
        return
    
    print("\n=== Test Results ===")
    print(f"Verdict: {result['verdict']}")
    print("\nDetails:")
    for detail in result['details']:
        print(f"\nTest: {detail['test']}")
        print(f"Status: {detail['status']}")
        if detail['error_type']:
            print(f"Error Type: {detail['error_type']}")
        if detail['traceback']:
            print(f"Traceback:\n{detail['traceback']}")
    print("\n==================\n")

def main():
    url = "http://localhost:1337/execute"
    
    # Test Case 1: All tests pass
    print("Test Case 1: All tests should pass")
    code1 = """
def add(a, b):
    return a + b
"""
    tests1 = [
        "assert add(1, 2) == 3",
        "assert add(-1, 1) == 0",
        "assert add(0, 0) == 0"
    ]
    result1 = test_code_execution(url, code1, tests1)
    print_result(result1)
    
    # Test Case 2: Some tests fail
    print("Test Case 2: Some tests should fail")
    code2 = """
def multiply(a, b):
    return a * b
"""
    tests2 = [
        "assert multiply(2, 3) == 6",  # Should pass
        "assert multiply(2, 3) == 5",  # Should fail
        "assert multiply(0, 5) == 0"   # Should pass
    ]
    result2 = test_code_execution(url, code2, tests2)
    print_result(result2)
    
    # Test Case 3: Compilation error
    print("Test Case 3: Should have compilation error")
    code3 = """
def broken_function(
    return 42  # Missing closing parenthesis
"""
    tests3 = ["assert broken_function() == 42"]
    result3 = test_code_execution(url, code3, tests3)
    print_result(result3)
    
    # Test Case 4: Runtime error
    print("Test Case 4: Should have runtime error")
    code4 = """
def divide(a, b):
    return a / b
"""
    tests4 = ["assert divide(1, 0) == 0"]  # Division by zero
    result4 = test_code_execution(url, code4, tests4)
    print_result(result4)

if __name__ == "__main__":
    main()
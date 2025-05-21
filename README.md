# Code Execution Environment

A Docker-based code execution environment for evaluating Python code against test cases, with support for HumanEval and MBPP benchmarks evaluation.

## Components

### 1. Code Execution API (`docker_api.py`)
- FastAPI-based service for executing Python code
- Supports timeout enforcement
- Provides detailed error reporting
- Runs in a Docker container for isolation



### 3. MBPP Evaluator (`evaluate_mbpp.py`)
- Evaluates code solutions against MBPP (Mostly Basic Python Problems) benchmark
- Supports test cases in assert format
- Provides detailed metrics and error analysis
- Generates comprehensive evaluation reports

### 4. HumanEvalPlus Evaluator (`evaluate_humanevalplus.py`)
- Evaluates code solutions against the HumanEvalPlus benchmark
- Supports execution of full test scripts
- Provides detailed metrics and error analysis
- Generates comprehensive evaluation reports

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build and run the Docker container:
```bash
cd docker
./build_and_run.sh
```

## Usage

### Basic Code Execution

```python
import requests

response = requests.post(
    "http://localhost:1337/execute",
    json={
        "code": "def add(a, b): return a + b",
        "tests": ["assert add(1, 2) == 3"],
        "timeout": 5
    }
)
print(response.json())
```

### MBPP Evaluation

```python
from evaluate_mbpp import MBPPEvaluator

# Initialize evaluator
evaluator = MBPPEvaluator()

# Your predictions (task_id -> code)
predictions = {
    "mbpp/1": """
def max_chain_length(pairs, n):
    pairs.sort(key=lambda x: x[1])
    count = 0
    last_end = float('-inf')
    for pair in pairs:
        if pair[0] > last_end:
            count += 1
            last_end = pair[1]
    return count
"""
}

# Evaluate predictions
results = evaluator.evaluate_predictions(predictions)

# Save detailed report
evaluator.save_report(results, "mbpp_evaluation_report.json")
```

### HumanEvalPlus Evaluation

```python
from evaluators.humaneval import HumanEvalPlusEvaluator

# Initialize evaluator
evaluator = HumanEvalPlusEvaluator()

# Your predictions (task_id -> code)
predictions = {
    "HumanEvalPlus/0": """
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False
"""
}

# Evaluate predictions
results = evaluator.evaluate_predictions(predictions)

# Save detailed report
evaluator.save_report(results, "humanevalplus_evaluation_report.json")
```

## Output Format

### Code Execution Response
```json
{
    "verdict": "All tests passed" | "At least one test error",
    "details": [
        {
            "test": "assert foo(1) == 2",
            "status": "passed" | "failed",
            "error_type": "AssertionError" | "Timeout" | "CompilationError" | "RuntimeError",
            "traceback": "..."
        }
    ]
}
```

### Evaluation Report Format
```json
{
    "total_tasks": 164,
    "passed_tasks": 120,
    "failed_tasks": 44,
    "error_types": {
        "AssertionError": 30,
        "CompilationError": 5,
        "RuntimeError": 9
    },
    "task_reports": {
        "task_id": {
            "task_id": "task_id",
            "verdict": "All tests passed",
            "test_results": [...],
            "passed": true
        }
    },
    "summary": {
        "pass_rate": 0.7317,
        "error_distribution": {...},
        "total_tasks": 164,
        "passed_tasks": 120,
        "failed_tasks": 44
    }
}
```

## Error Types

The system distinguishes between several types of errors:
- `CompilationError`: Syntax errors in the code
- `AssertionError`: Test assertions failed
- `RuntimeError`: Errors during code execution
- `TimeLimit`: Execution exceeded timeout
- `EvaluationError`: Errors during evaluation process

## Contributing

Feel free to submit issues and enhancement requests!

## Datasets

- **MBPP (Mostly Basic Python Problems)**: `google-research-datasets/mbpp`
- **HumanEvalPlus**: `evalplus/humanevalplus` 
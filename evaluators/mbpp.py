import json
import ast
import io
import sys
from typing import Dict, List, Any, Tuple
from datasets import load_dataset
import requests
from collections import defaultdict
import time
from tqdm import tqdm
import re
import ast
import numpy as np
import re

def extract_prefix_before_solution(code: str) -> str:
    lines = code.strip().split('\n')
    result_lines = []
    found_main_func = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Match top-level function definitions
        if re.match(r'^def\s+\w+\s*\(.*\)\s*:', line):
            result_lines.append(line)
            break

        # Match import lines or class definitions or docstrings
        if (stripped.startswith("import") or
            stripped.startswith("from") or
            stripped.startswith("class") or
            stripped.startswith("def") or
            stripped.startswith('"""') or
            stripped.startswith("'''") or
            len(result_lines) > 0):  # capture body of classes/functions

            result_lines.append(line)

    return '\n'.join(result_lines)

class MBPPEvaluator:
    def __init__(self, api_url: str = "http://localhost:1337/execute"):
        self.api_url = api_url
        self.dataset = load_dataset("google-research-datasets/mbpp")
        self.test_cases = self._prepare_test_cases()
        
    def _prepare_test_cases(self) -> Dict[str, Dict[str, Any]]:
        """Extract test cases and setup code from the dataset."""
        test_cases = {}
        for item in self.dataset['test']:
            test_cases[item['task_id']] = {
                'test_list': item['test_list'],
                'test_setup_code': item.get('test_setup_code', '')
            }
        return test_cases

    def evaluate_predictions(self, predictions: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluate predictions against MBPP test cases.
        
        Args:
            predictions: Dict mapping task_id to predicted code
            
        Returns:
            Dict containing evaluation metrics and detailed reports
        """
        results = {
            'total_tasks': len(predictions),
            'passed_tasks': 0,
            'failed_tasks': 0,
            'error_types': defaultdict(int),
            'task_reports': {},
            'summary': {}
        }
        
        for task_id, code in tqdm(predictions.items(), desc="Evaluating tasks"):
            if task_id not in self.test_cases:
                print(f"Warning: Task {task_id} not found in dataset")
                continue
                
            task_data = self.test_cases[task_id]
            task_tests = task_data['test_list']
            setup_code = task_data['test_setup_code']
            task_results = []
            all_passed = True
            
            for test_case in task_tests:
                try:
                    # Combine solution code and setup code
                    full_code = f"{code}\n\n{setup_code}"
                    
                    response = requests.post(
                        self.api_url,
                        json={
                            "code": full_code,
                            "tests": [test_case],
                            "timeout": 5
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    test_result = {
                        'test_case': test_case,
                        'passed': result['verdict'] == "All tests passed",
                        'error': None if result['verdict'] == "All tests passed" else result['details'][0]['traceback']
                    }
                    
                    if not test_result['passed']:
                        all_passed = False
                        results['error_types'][result['details'][0]['error_type']] += 1
                    
                    task_results.append(test_result)
                    
                except Exception as e:
                    print(f"Error evaluating test case for task {task_id}: {str(e)}")
                    results['error_types']['EvaluationError'] += 1
                    all_passed = False
                    task_results.append({
                        'test_case': test_case,
                        'passed': False,
                        'error': str(e)
                    })
            
            # Update task report
            if all_passed:
                results['passed_tasks'] += 1
            else:
                results['failed_tasks'] += 1
                
            results['task_reports'][task_id] = {
                'task_id': task_id,
                'verdict': "All tests passed" if all_passed else "At least one test failed",
                'test_results': task_results,
                'passed': all_passed
            }
        
        # Calculate summary statistics
        results['summary'] = {
            'total_tasks': results['total_tasks'],
            'passed_tasks': results['passed_tasks'],
            'failed_tasks': results['failed_tasks'],
            'pass_rate': results['passed_tasks'] / results['total_tasks'] if results['total_tasks'] > 0 else 0,
            'error_distribution': dict(results['error_types'])
        }
        
        return results

    def save_report(self, results: Dict[str, Any], output_file: str):
        """Save the evaluation results to a JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

    def get_problem_descriptions(self) -> Dict[str, str]:
        """Retrieve problem descriptions from the dataset."""
        descriptions = {}
        for item in self.dataset['test']:
            item_description = {}
            item_description['problem_description'] = item['text']
            item_description['starter_code'] = extract_prefix_before_solution(item['code'])
            descriptions[item['task_id']] = item_description
        return descriptions 
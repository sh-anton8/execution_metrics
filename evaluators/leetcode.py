import json
import requests
from typing import Dict, Any
from datasets import load_dataset
from collections import defaultdict
from tqdm import tqdm
from requests.exceptions import ConnectionError
import time

class LeetCodeEvaluator:
    def __init__(self, api_url: str = "http://localhost:1337/execute"):
        self.api_url = api_url
        self.dataset = load_dataset("newfacade/LeetCodeDataset")
        self.test_cases = self._prepare_test_cases()
        
    def _prepare_test_cases(self) -> Dict[str, Dict[str, Any]]:
        """Extract test cases and setup code from the dataset."""
        test_cases = {}
        for item in self.dataset['test']:
            test_cases[item['task_id']] = {
                'entry_point': item['entry_point'],
                'test_code': f"{item['test']}",
                'prompt': item['prompt']
            }
        return test_cases

    def evaluate_predictions(self, predictions: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluate predictions against LeetCode test cases.
        
        Args:
            predictions: Dict mapping task-id to predicted code
            
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
            entry_point = task_data['entry_point']
            test_code = task_data['test_code']
            prompt = task_data['prompt']
            task_results = []
            all_passed = True
            
            retries = 3
            while retries > 0:
                try:
                    # Construct the full test script
                    full_code = f"{prompt}\n\n{code}\n\n{test_code}\n"
                    
                    response = requests.post(
                        self.api_url,
                        json={
                            "code": full_code,
                            "tests": [f"check({entry_point})"],
                            "timeout": 80
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    test_result = {
                        'task_id': task_id,
                        'verdict': "All tests passed" if result['verdict'] == "All tests passed" else "At least one test failed",
                        'error': None if result['verdict'] == "All tests passed" else result['details'][0]['traceback']
                    }
                    
                    if not test_result['verdict'] == "All tests passed":
                        all_passed = False
                        results['error_types'][result['details'][0]['error_type']] += 1
                    
                    task_results.append(test_result)
                    break  # Exit the retry loop if successful
                except ConnectionError:
                    retries -= 1
                    if retries == 0:
                        print(f"Error: Unable to connect to the server for task {task_id} after 3 attempts.")
                        results['error_types']['ConnectionError'] += 1
                        task_results.append({
                            'task_id': task_id,
                            'verdict': "ConnectionError",
                            'error': 'ConnectionError: Unable to connect to the server after 3 attempts.'
                        })
                    else:
                        print(f"Connection error for task {task_id}. Retrying in 10 seconds...")
                        time.sleep(10)
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        print(f"Error evaluating test case for task {task_id}: {str(e)}")
                        results['error_types']['EvaluationError'] += 1
                        all_passed = False
                        task_results.append({
                            'task_id': task_id,
                            'verdict': "EvaluationError",
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
        results['summary']['pass_rate'] = results['passed_tasks'] / results['total_tasks'] if results['total_tasks'] > 0 else 0
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

    def get_problem_descriptions(self) -> Dict[str, str]:
        """Retrieve problem descriptions from the dataset."""
        descriptions = {}
        for item in self.dataset['test']:
            item_description = {}
            item_description['problem_description'] = item['problem_description']
            item_description['starter_code'] = item['starter_code']
            descriptions[item['task_id']] = item_description
        return descriptions 
from typing import Dict, List, Any
from datasets import load_dataset
from collections import defaultdict
from tqdm import tqdm
from evaluators.mbpp import MBPPEvaluator

def main():
    # Example usage
    evaluator = MBPPEvaluator()
    
    dataset = load_dataset("google-research-datasets/mbpp")
    # Example predictions (replace with your actual predictions)
    predictions = {
        el['task_id']: el['code'] for el in dataset['test']
    }
    
    # Evaluate predictions
    results = evaluator.evaluate_predictions(predictions)
    
    # Print summary
    print("\n=== Evaluation Summary ===")
    print(f"Total Tasks: {results['summary']['total_tasks']}")
    print(f"Passed Tasks: {results['summary']['passed_tasks']}")
    print(f"Failed Tasks: {results['summary']['failed_tasks']}")
    print(f"Pass Rate: {results['summary']['pass_rate']:.2%}")
    
    print("\nError Distribution:")
    for error_type, count in results['summary']['error_distribution'].items():
        print(f"- {error_type}: {count}")
    
    # Save detailed report
    evaluator.save_report(results, "mbpp_evaluation_report.json")
    print("\nDetailed report saved to mbpp_evaluation_report.json")

if __name__ == "__main__":
    main() 
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from multiprocessing import Process, Manager
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import ast

app = FastAPI(
    title="Code Execution API",
    description="API for executing generated code against provided tests with detailed verdicts.",
    version="2.0.0"
)

class TestCaseResult(BaseModel):
    test: str
    status: str  # 'passed' or 'failed'
    error_type: Optional[str] = None
    traceback: Optional[str] = None
    output: Optional[str] = None
    input_args: Optional[Any] = None  # Add input arguments
    expected_output: Optional[Any] = None  # Add expected output
    actual_output: Optional[Any] = None  # Add actual output

class ExecutionResponse(BaseModel):
    verdict: str  # 'All tests passed' or 'At least one test error'
    details: List[TestCaseResult]

class CodeExecutionRequest(BaseModel):
    code: str
    tests: List[str]
    timeout: int = Field(default=20, ge=1, le=30)

def run_code_and_tests(code: str, tests: List[str], shared_dict, timeout: int):
    results = []
    verdict = "All tests passed"
    start_time = time.time()
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    
    try:
        local_namespace = {'__builtins__': __builtins__}
        # Try to compile the code first
        try:
            compiled = compile(code, '<string>', 'exec')
        except Exception as e:
            verdict = "At least one test error"
            results = [TestCaseResult(
                test="<code compilation>",
                status="failed",
                error_type="CompilationError",
                traceback=traceback.format_exc(),
                output=stderr_buffer.getvalue()
            ).dict()]
            shared_dict['verdict'] = verdict
            shared_dict['details'] = results
            return
            
        # Execute the code
        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(compiled, local_namespace)
                # Print the namespace for debugging
                print("Available functions:", [name for name in local_namespace if not name.startswith('__')])
        except Exception as e:
            verdict = "At least one test error"
            error_msg = f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}\nStderr:\n{stderr_buffer.getvalue()}"
            results = [TestCaseResult(
                test="<code execution>",
                status="failed",
                error_type="RuntimeError",
                traceback=error_msg,
                output=stdout_buffer.getvalue()
            ).dict()]
            shared_dict['verdict'] = verdict
            shared_dict['details'] = results
            return
            
        # Run each test
        for test in tests:
            try:
                # Extract input arguments and expected output from test
                input_args = None
                expected_output = None
                actual_output = None
                
                # Try to extract input arguments and expected output
                if "assert" in test:
                    # Extract the function call and expected result
                    parts = test.split("assert")[1].strip()
                    if "==" in parts:
                        func_call, expected = parts.split("==")
                        try:
                            # Try to evaluate the expected output
                            expected_output = ast.literal_eval(expected.strip())
                            # Try to extract input arguments from function call
                            func_name = func_call.split("(")[0].strip()
                            args_str = func_call.split("(")[1].split(")")[0]
                            try:
                                input_args = ast.literal_eval(args_str)
                            except:
                                input_args = args_str
                        except:
                            pass
                
                # Execute the test and capture output
                with redirect_stdout(StringIO()) as test_stdout, redirect_stderr(StringIO()) as test_stderr:
                    exec(test, local_namespace)
                    actual_output = test_stdout.getvalue().strip()
                
                results.append(TestCaseResult(
                    test=test,
                    status="passed",
                    output=stdout_buffer.getvalue(),
                    input_args=input_args,
                    expected_output=expected_output,
                    actual_output=actual_output
                ).dict())
            except AssertionError as e:
                verdict = "At least one test error"
                error_msg = f"AssertionError: {str(e)}\nTraceback:\n{traceback.format_exc()}\nStderr:\n{stderr_buffer.getvalue()}"
                results.append(TestCaseResult(
                    test=test,
                    status="failed",
                    error_type="AssertionError",
                    traceback=error_msg,
                    output=stdout_buffer.getvalue(),
                    input_args=input_args,
                    expected_output=expected_output,
                    actual_output=actual_output
                ).dict())
            except Exception as e:
                verdict = "At least one test error"
                error_msg = f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}\nStderr:\n{stderr_buffer.getvalue()}"
                error_type = type(e).__name__
                results.append(TestCaseResult(
                    test=test,
                    status="failed",
                    error_type=error_type,
                    traceback=error_msg,
                    output=stdout_buffer.getvalue(),
                    input_args=input_args,
                    expected_output=expected_output,
                    actual_output=actual_output
                ).dict())
    except Exception as e:
        verdict = "At least one test error"
        error_msg = f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}\nStderr:\n{stderr_buffer.getvalue()}"
        results.append(TestCaseResult(
            test="<unknown>",
            status="failed",
            error_type="UnknownError",
            traceback=error_msg,
            output=stdout_buffer.getvalue()
        ).dict())
    finally:
        elapsed = time.time() - start_time
        shared_dict['verdict'] = verdict
        shared_dict['details'] = results
        shared_dict['elapsed'] = elapsed

def execute_with_timeout(code: str, tests: List[str], timeout: int) -> ExecutionResponse:
    with Manager() as manager:
        shared_dict = manager.dict()
        p = Process(target=run_code_and_tests, args=(code, tests, shared_dict, timeout))
        p.start()
        p.join(timeout)
        if p.is_alive():
            p.terminate()
            p.join()
            # Timeout occurred
            details = [TestCaseResult(
                test="<timeout>",
                status="failed",
                error_type="TimeLimit",
                traceback=f"Execution exceeded time limit of {timeout} seconds."
            ).dict()]
            return ExecutionResponse(verdict="At least one test error", details=details)
        # Normal case
        verdict = shared_dict.get('verdict', 'At least one test error')
        details = shared_dict.get('details', [])
        return ExecutionResponse(verdict=verdict, details=details)

@app.post("/execute", response_model=ExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")
    if not request.tests:
        raise HTTPException(status_code=400, detail="No tests provided")
    return execute_with_timeout(request.code, request.tests, request.timeout)
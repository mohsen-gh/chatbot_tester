import time
from collections import defaultdict

import utils.log_manager as log_manager
from schemas import (
    TestQuery,
    TestResult,
    TurnResult,
    UserQuery,
    UserResponse,
)
from utils.chat_client import ChatClient
from utils.json_utils import append_to_jsonl, stream_json_file, write_json_file
from utils.text.intent_matcher import IntentMatcher as intent_matcher
from utils.text.response_matcher import ResponseMatcher

logger = log_manager.get_logger(__name__)

class TestEngine:
    """
    TestEngine - A test execution engine for chatbot API testing.
    This class manages the execution of multiple test runs against a chat service,
    collects results, and generates summary reports with statistics.
    Attributes:
        _test_case_json_file_path (str): Path to the JSON file containing test cases.
        _runs (int): Number of times to run each test case.
        _chat_client (ChatClient): Client for communicating with the chat API.
        _fuzzy_threshold (float): Threshold for the fuzzy matcher used in response validation.
        _summary_file_path (str): Path where the summary report will be written.
        _raw_results_path (str): Path where raw results are written.
        _results_list (list[TurnResult]): List storing results for each turn across all runs.
        _response_validator (ResponseMatcher): Validator for response matching with semantic similarity.
    Methods:
        __init__(test_case_json_file_path, runs, summary_file_path, chat_client, fuzzy_threshold=0.6):
            Initializes the TestEngine with configuration parameters and dependencies.
        _run_single_turn(query, test_case_id, run_idx) -> TurnResult:
            Executes a single turn of the conversation by sending the user query to the chat service,
            collecting responses, matching intent, validating response, and measuring latency.
        run_tests():
            Executes all test cases for the specified number of runs, collects results including
            intent matching, response validation, and latency metrics, writes raw results to a
            JSONL file and generates a summary report.
        get_results() -> TestResult:
            Processes collected results and returns aggregated statistics including total tests,
            intent accuracy, response pass rate, average latency, and summary of failed test cases.
    """
    
    def __init__(self, 
                 test_case_json_file_path: str, 
                 runs: int, 
                 summary_file_path: str,
                 chat_client: ChatClient,
                 fuzzy_threshold: float = 0.6):
        
        self._test_case_json_file_path = test_case_json_file_path
        self._runs = runs
        self._chat_client = chat_client
        self._fuzzy_threshold = fuzzy_threshold
        self._summary_file_path = summary_file_path
        
        import os
        self._raw_results_path =  self._summary_file_path.replace(".json", "_raw.jsonl")
        report_dir = os.path.dirname(self._raw_results_path)
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        if os.path.exists(self._raw_results_path):
            os.remove(self._raw_results_path)

        self._results_list: list[TurnResult] = [] 
        self._response_validator = ResponseMatcher(fuzzy_threshold=self._fuzzy_threshold) # can be parameterized as needed

    def _run_single_turn(self, query: TestQuery, test_case_id:str, run_idx: int) -> TurnResult:
        ''' Executes a single turn of the conversation by sending the user query to the chat service,'''

        start = time.perf_counter()
        turn_result = TurnResult(run_idx=run_idx, test_case_id=test_case_id)
        user_id = f"{test_case_id}_{run_idx}"
        try:
            user_query = UserQuery(user_id=user_id, message=query.message)
            turn_result.query = user_query
            
            resp:UserResponse = self._chat_client.chat_sync(user_query)
            turn_result.response = resp

            turn_result.intent_match = intent_matcher.match(resp.intent, query.expected_intents)
            turn_result.response_match = self._response_validator.match(resp.response, query.expected_keywords)

        except Exception as e:
            error = str(e)
            turn_result.error = error

        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            turn_result.latency_ms = latency_ms

        return turn_result
    
    def _save_results_on_file(self, summary: TestResult = None):
        ''' Writes the raw results map to a JSON file for record-keeping and further analysis.'''

        logger.info("Saving results to file...")
        # After all runs, write the results to the output report file exactly as they are in the results map both keys and values
        write_json_file(self._summary_file_path, summary.model_dump())
        
        logger.info(f"Raw results written to {self._raw_results_path}")
        logger.info(f"Summary written to {self._summary_file_path}")


    def run_tests(self)->TestResult:
        logger.info("Running tests...")

        for run_idx in range(1, self._runs + 1):

            logger.debug(f"Starting run {run_idx}/{self._runs}...")

            for test_case in stream_json_file(self._test_case_json_file_path):
                
                logger.debug(f"Processing test case {test_case.test_id} for run {run_idx}...")

                for test_query in test_case.conversation:

                    turn_result = self._run_single_turn(test_query, test_case.test_id, run_idx)
                    # append to raw output
                    append_to_jsonl(self._raw_results_path, turn_result)
                    self._results_list.append(turn_result)

                    # log every 10 turns for visibility into ongoing results
                    total_turns = len(self._results_list)
                    logger.debug(f"Completed turn {total_turns} for message '{test_query.message}' for test case {test_case.test_id} in run {run_idx}")
                    if total_turns % 10 == 0:
                        logger.info(f"Processed {total_turns} turns so far...")

        # log the remaining processed turns and final statistics
        logger.info(f"Processed (all) {total_turns} turns")
        # generate summary statistics and save alongside raw results
        summary = self._prepare_results()
        self._save_results_on_file(summary)
        return summary
        

    def _prepare_results(self)-> TestResult:
        ''' Processes the collected results to compute summary statistics such as total tests executed, intent accuracy, 
            response pass rate, average latency, and identifies tests that failed in a majority of runs. Returns a TestResult 
            object containing these aggregated metrics.
        '''
        logger.info("Preparing summary results...")
        result = TestResult()
        # process the self._results_map to calculate total_tests, intent_accuracy, response_pass_rate, average_latency
        intent_matches = 0
        response_matches = 0
        total_success_turns = 0
        total_success_latency = 0.0
        timeout_count = 0
        server_error_count = 0

        # track tests that fail in a majority of runs
        failed_ids: set[str] = set()
        test_cases: set[str] = set()
        failed_tests: defaultdict[str, list] = defaultdict(set)

        for turn_result in self._results_list:

            test_cases.add(turn_result.test_case_id)
            if turn_result.intent_match:
                intent_matches += 1
            else:
                failed_tests[turn_result.test_case_id].add(turn_result.run_idx)
            if turn_result.response_match:
                response_matches += 1
            else:
                failed_tests[turn_result.test_case_id].add(turn_result.run_idx)
            
            # accumulate latency for every turn
            if turn_result.error is None:
                total_success_latency += turn_result.latency_ms
                total_success_turns += 1
            else:
                if "timed out" in turn_result.error.lower() or "504" in turn_result.error or "timeout" in turn_result.error.lower():
                    timeout_count += 1
                else:
                    server_error_count += 1

        # determine majority: more than half of executed runs must have failure
        print(failed_tests)
        for test_case_id, failed_runs_list in failed_tests.items():
            if len(failed_runs_list) > self._runs / 2:
                failed_ids.add(test_case_id)

        total_tests = len(test_cases)
        total_turns = len(self._results_list)

        if total_tests > 0:
            result.total_tests = total_tests
            result.intent_accuracy = intent_matches / total_turns if total_turns > 0 else 0.0
            result.response_pass_rate = response_matches / total_turns if total_turns > 0 else 0.0
            result.average_latency = total_success_latency / total_success_turns if total_turns > 0 else 0.0
            result.api_errors = f"{server_error_count + timeout_count} ({timeout_count} Timeouts, {server_error_count} Server Errors)"
            result.failed_test_ids = sorted(failed_ids)

        return result
import argparse
import logging

import utils.log_manager as log_manager
from test_engine import TestEngine
from utils.chat_client import ChatClient
from utils.text.intent_matcher import ExactIntentMatcher
from utils.text.response_matcher import DynamicResponseMatcher

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run chatbot tests")
    parser.add_argument("--dataset", default="tester/data/test_cases.json", help="Path to test data file")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL for the API")
    parser.add_argument("--runs", type=int, default=1, help="Number of test runs")
    parser.add_argument("--output", default="tester/data/report/report.json", help="Output report file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--fuzzy-thresh", type=float, default=0.6, help="Fuzzy matching threshold for response matching")
    args = parser.parse_args()

    # Setup logging based on verbosity flag
    log_manager.setup_logging(
        app_level=logging.DEBUG if args.verbose else logging.INFO,
        root_level=logging.WARNING
    )
    logger = log_manager.get_logger(__name__)
    
    logger.info(f"Initiating test engine with args: {args}")
    # Initialize and run the test engine
    test_engine = TestEngine(
        test_case_json_file_path=args.dataset, 
        runs=args.runs, 
        chat_client=ChatClient(base_url=args.base_url),
        summary_file_path=args.output,
        intent_matcher=ExactIntentMatcher(),
        response_matcher=DynamicResponseMatcher(fuzzy_threshold=args.fuzzy_thresh)
    )
    results = test_engine.run_tests()
    logger.info(results)
    
    
    
    
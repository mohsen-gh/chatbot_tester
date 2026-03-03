
from dataclasses import dataclass

from pydantic import BaseModel, Field


################################################
# Schemas for interacting with the chat service
################################################
@dataclass
class UserQuery:
    user_id: str
    message: str

@dataclass
class UserResponse:
    response: str
    intent: str
    confidence: float

    def __str__(self):
        return f"Response: {self.response}, Intent: {self.intent}, Confidence: {self.confidence}"



################################################
# schemas for parsing test cases into structured format
################################################
class TestQuery(BaseModel):
    message:str
    expected_intents: list[str]
    expected_keywords: list[str]

class TestCase(BaseModel):
    test_id: str
    conversation: list[TestQuery]


################################################
# Schemas for storing test results
################################################
class TurnResult(BaseModel):
    # turn_id: str = Field(default_factory=lambda: str(uuid4())) # Added for flattening
    test_case_id: str                   # Added for flattening
    run_idx: int                   # Added for flattening
    query: UserQuery | None = None
    response: UserResponse | None = None
    intent_match: bool = False
    response_match: bool = False
    latency_ms: float | None = None
    error: str | None = None


class TestResult(BaseModel):
    total_tests: int = 0
    intent_accuracy: float = 0.0
    response_pass_rate: float = 0.0
    average_latency: float = 0.0
    api_errors: str | None = None
    failed_test_ids: list[str] = Field(default_factory=list)

    def model_dump(self, **kwargs):
        """
        Convert the model instance to a dictionary with formatted string representations.
        Formats specific numeric fields for better readability:
        - intent_accuracy: Converted to percentage format (e.g., "95.50%")
        - response_pass_rate: Converted to percentage format (e.g., "87.25%")
        - average_latency: Converted to milliseconds format with 2 decimal places (e.g., "125.34 ms")
        Args:
            **kwargs: Additional keyword arguments to pass to the parent model_dump method.
        Returns:
            dict: A dictionary representation of the model with formatted string values
                  for intent_accuracy, response_pass_rate, and average_latency fields.
        """

        data = super().model_dump(**kwargs)
        data['intent_accuracy'] = f"{data['intent_accuracy']:.2%}"
        data['response_pass_rate'] = f"{data['response_pass_rate']:.2%}"
        data['average_latency'] = f"{data['average_latency']:.2f} ms"
        return data

    def __str__(self):
        base = (
            f"Total Tests: {self.total_tests}, Intent Accuracy: {self.intent_accuracy:.2%}, "
            f"Response Pass Rate: {self.response_pass_rate:.2%}, Average Latency: {self.average_latency:.2f} ms"
        )
        if self.failed_test_ids:
            base += f", Failed Test IDs: {', '.join(self.failed_test_ids)}"
        return base
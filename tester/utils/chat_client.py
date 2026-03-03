import httpx
import utils.log_manager as log_manager
from schemas import UserQuery, UserResponse

logger = log_manager.get_logger(__name__)

class ChatClient:
    def __init__(self, base_url: str):
        self.api_url = base_url + "/chat"
    
    def _post_call_sync(self, data) -> UserResponse:
        try:
            with httpx.Client() as client:
                response = client.post(self.api_url, json=data)
                if response.status_code != 200:
                    logger.error(f"API call ({self.api_url}) failed. Error Response is: {response.status_code} - {response.text}")
                    raise Exception(f"API call failed with status code {response.status_code}")
                logger.debug(f"API call ({self.api_url}) was successful.")
                return UserResponse(**response.json())
            
        except httpx.RequestError as e:
            logger.error(f"An error occurred while making the API call to {self.api_url}: {e}")
            raise Exception(f"An error occurred while making the API call: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred during API call to {self.api_url}: {e}")
            raise Exception(f"HTTP error occurred during API call: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during API call to {self.api_url}: {e}")
            raise Exception(f"An unexpected error occurred during API call: {e}")
        
    def chat_sync(self, query: UserQuery) -> UserResponse:
        return self._post_call_sync(query.__dict__)
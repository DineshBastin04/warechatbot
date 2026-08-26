import json
import re
import sqlparse
from sqlparse.sql import Token
from sqlparse.tokens import Keyword, DML
from httpx import Timeout
import logging 
from ..base import VannaBase
from ..exceptions import DependencyError
import queue  # NEW: For potential serialization if needed
from concurrent.futures import ThreadPoolExecutor, as_completed  # NEW: For pooling
from functools import wraps
import threading  # NEW: For thread names in logs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # NEW: Dedicated logger

class Ollama(VannaBase):
  def __init__(self, config=None, max_workers=10):  # NEW: Add max_workers param

    try:
      ollama = __import__("ollama")
    except ImportError:
      raise DependencyError(
        "You need to install required dependencies to execute this method, run command:"
        " \npip install ollama"
      )

    if not config:
      raise ValueError("config must contain at least Ollama model")
    if 'model' not in config.keys():
      raise ValueError("config must contain at least Ollama model")
    self.host = config.get("ollama_host", "http://localhost:11434")
    self.model = config["model"]
    if ":" not in self.model:
      self.model += ":latest"

    self.ollama_timeout = config.get("ollama_timeout", 3000.0)

    self.ollama_client = ollama.Client(self.host, timeout=Timeout(self.ollama_timeout))
    self.keep_alive = config.get('keep_alive', None)
    self.ollama_options = config.get('options', {})
    self.num_ctx = self.ollama_options.get('num_ctx', 2048)
    self.__pull_model_if_ne(self.ollama_client, self.model)
    
    # NEW: Thread pool for parallel Ollama requests (I/O-bound)
    self.executor = ThreadPoolExecutor(max_workers=max_workers)
    logger.info(f"Initialized Ollama with ThreadPoolExecutor (max_workers={max_workers}) in thread {threading.current_thread().name}")  # NEW

  def log_pool_stats(self):  # NEW: Utility for monitoring (can be called externally if needed)
      """Log current pool stats for debugging."""
      active_threads = len(self.executor._threads) if hasattr(self.executor, '_threads') else 0
      pending_tasks = self.executor._work_queue.qsize() if hasattr(self.executor, '_work_queue') else 0
      logger.info(f"Ollama Pool Stats - Active Threads: {active_threads}, Pending Tasks: {pending_tasks} (thread: {threading.current_thread().name})")  # NEW

  @staticmethod
  def __pull_model_if_ne(ollama_client, model):
    model_response = ollama_client.list()
    model_lists = [model_element['model'] for model_element in
                   model_response.get('models', [])]
    if model not in model_lists:
      ollama_client.pull(model)

  def system_message(self, message: str) -> any:
    return {"role": "system", "content": message}

  def user_message(self, message: str) -> any:
    return {"role": "user", "content": message}

  def assistant_message(self, message: str) -> any:
    return {"role": "assistant", "content": message}

  def extract_sql(self, llm_response):
      """
      Extracts the complete SQL query from an LLM response, handling nested blocks and distinguishing `END` within `CASE` statements.

      Args:
      - llm_response (str): The LLM response containing the SQL query.

      Returns:
      - str: The fully extracted SQL query.
      """
      thread_name = threading.current_thread().name  # NEW: For logging
      logger.info(f"extract_sql called from {thread_name}: Response len={len(llm_response)}")  # NEW

      # Clean the LLM response
      llm_response = llm_response.replace("\\_", "_").replace("\\", "")

      # Tokenize the response into words
      tokens = llm_response.split()
      stack = []  # Track nested BEGIN...END blocks
      extracted_sql = []  # Build the query dynamically
      inside_case = False  # Flag to track if inside a CASE...END block
      case_stack = []
      for token in tokens:
          extracted_sql.append(token)  # Add the current token to the result

          # Handle CASE...END blocks
          if token.upper() == "CASE":
              case_stack.append("CASE")
          elif token.upper() == "END" and case_stack:
              case_stack.pop()

          # Handle BEGIN...END or IF...END blocks
          if token.upper() in {"BEGIN", "IF"} and not case_stack:
              stack.append(token.upper())
          elif token.upper() == "END" and not case_stack:
              if stack:
                  stack.pop()

          # Stop only when all stacks are empty and parsing the last `END`
          if not stack and not case_stack and token.upper() == "END":
              continue

      # Join the tokens to reconstruct the full query
      full_query = " ".join(extracted_sql).strip()

      # Log and return the result
      self.log(f"Extracted SQL: {full_query}")
      logger.info(f"extract_sql returning query len={len(full_query)} from {thread_name}")  # NEW
      return full_query if full_query else llm_response

  def _submit_to_pool(self, func, *args, **kwargs):  # NEW: Helper for pooling
      """Helper to submit a task to the thread pool and return result."""
      thread_name = threading.current_thread().name
      logger.info(f"Submitting task '{func.__name__}' to pool from thread {thread_name} with args: {args[:1]}...")  # NEW: Log submission
      future = self.executor.submit(func, *args, **kwargs)
      try:
          result = future.result(timeout=self.ollama_timeout / 1000)  # Block with timeout (convert ms to s)
          logger.info(f"Task '{func.__name__}' completed successfully from thread {thread_name} (result type: {type(result)})")  # NEW
          return result
      except Exception as e:
          logger.error(f"Task '{func.__name__}' failed from thread {thread_name}: {e}", exc_info=True)  # NEW: Error with trace
          raise

  def _async_ollama_chat(self, model, messages, stream, options, keep_alive):  # NEW: Async wrapper for chat
      """Async wrapper for ollama_client.chat (for pooling)."""
      thread_name = threading.current_thread().name
      logger.debug(f"Executing ollama.chat in thread {thread_name}: model={model}, messages len={len(messages)}")  # NEW
      response = self.ollama_client.chat(
          model=model,
          messages=messages,
          stream=stream,
          options=options,
          keep_alive=keep_alive
      )
      logger.debug(f"ollama.chat completed in {thread_name}: response keys={list(response.keys())}")  # NEW
      return response

  def submit_prompt(self, prompt, **kwargs) -> str:
      thread_name = threading.current_thread().name  # NEW
      self.log(
          f"Ollama parameters:\n"
          f"model={self.model},\n"
          f"options={self.ollama_options},\n"
          f"keep_alive={self.keep_alive}")
      self.log(f"Prompt Content:\n{json.dumps(prompt)}")
      logging.info(f"Prompt Content:\n{json.dumps(prompt)}")
      
      # NEW: Offload the actual chat call to the thread pool for parallelism
      logger.info(f"submit_prompt called from {thread_name}: Submitting to pool for model '{self.model}'")  # NEW
      response_dict = self._submit_to_pool(
          self._async_ollama_chat,
          self.model,
          prompt,
          False,  # stream=False as per original
          self.ollama_options,
          self.keep_alive
      )
      
      self.log(f"Ollama Response:\n{str(response_dict)}")
      logging.info(f"Ollama Response:\n{str(response_dict)}")
      logger.info(f"submit_prompt returning response len={len(response_dict['message']['content'])} from {thread_name}")  # NEW
      return response_dict['message']['content']

  def pooled(self, func):  # NEW: Decorator for easy pooling on other methods if needed
      @wraps(func)
      def wrapper(*args, **kwargs):
          thread_name = threading.current_thread().name
          logger.debug(f"Using pooled decorator for '{func.__name__}' from {thread_name}")  # NEW
          return self._submit_to_pool(func, *args, **kwargs)
      return wrapper

  # NEW: Shutdown method for cleanup (can be called externally if needed, e.g., on app shutdown)
  def shutdown(self):
      """Shutdown the executor (call on app shutdown)."""
      logger.info("Shutting down Ollama thread pool")  # NEW
      self.executor.shutdown(wait=True)
      logger.info("Ollama thread pool shutdown complete")  # NEW
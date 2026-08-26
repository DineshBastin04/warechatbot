import json
from typing import List
import logging
import chromadb
import pandas as pd
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from ..base import VannaBase
from ..utils import deterministic_uuid
import re
import hashlib
import math
import logging
import json
import os
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed  # For pooling
from functools import wraps
import threading  # NEW: For thread names in logs
import logging
import math
from fuzzywuzzy import fuzz
import json
import os






logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # NEW: Dedicated logger
# Assuming your JSON is in config folder next to your main.py
CONFIG_DIR = os.path.join(os.path.dirname(__file__))

with open(os.path.join(CONFIG_DIR, "domain_mapping.json"), "r") as f:
    domain_mappings = json.load(f)

with open(os.path.join(CONFIG_DIR, "glossary.json"), "r") as f:
    glossary = json.load(f)

with open(os.path.join(CONFIG_DIR, "query_mapping.json"), "r") as f:
    query_mapping = json.load(f)

# Write whitelist: {table_name: {"db": alias, "allowed_operations": [...], "allowed_columns": [...]}}.
# Empty by default — no table is writable until this is explicitly populated. See
# get_write_sql_prompt / is_write_sql_valid in base.py for how this is enforced.
with open(os.path.join(CONFIG_DIR, "write_whitelist.json"), "r") as f:
    write_whitelist_config = json.load(f)



with open(os.path.join(CONFIG_DIR, "table_relevance.json"), "r") as f:
    raw_table_relevance = json.load(f)

cleaned_table_relevance = {}

# ----------------------------------------
# CLEAN EACH KEYWORD GROUP
# ----------------------------------------
for k, v in raw_table_relevance.items():

    # -----------------------------
    # STEP 1: Safely load JSON list
    # -----------------------------
    try:
        kws = json.loads(k)        # expected → ["zone", "zone01", ...]
        if not isinstance(kws, list):
            kws = [kws]
    except Exception:
        # Fallback for malformed JSON
        kws = [
            token.strip().strip('"').strip("'")
            for token in k.strip("[]").split(",")
        ]

    # -----------------------------
    # STEP 2: Clean & normalize
    # -----------------------------
    cleaned = []
    for kw in kws:
        kw = kw.strip().lower()

        # skip empty
        if not kw:
            continue

        # skip corrupted long keywords
        if len(kw) > 60:
            continue

        cleaned.append(kw)

    # -----------------------------
    # STEP 3: Remove duplicates
    # -----------------------------
    cleaned = list(dict.fromkeys(cleaned))

    # -----------------------------
    # STEP 3.5: Normalize value shape — supports the original plain
    # "table_name" string (single-DB, backward compatible) as well as
    # {"table": "table_name", "db": "SECONDARY"} for dual-DB workspaces.
    # "db" of None means "primary DB" (resolved against vn.primary_db_alias
    # at retrieval time).
    # -----------------------------
    if isinstance(v, dict):
        table_name = v.get("table", "")
        table_db = v.get("db") or None
    else:
        table_name = v
        table_db = None

    # -----------------------------
    # STEP 4: IMPORTANT — avoid empty keys
    # -----------------------------
    if not cleaned:
        cleaned = ["placeholder_keyword_for_" + table_name.lower()]


    # -----------------------------
    # STEP 5: Store using tuple key
    # -----------------------------
    cleaned_table_relevance[tuple(cleaned)] = {"table": table_name, "db": table_db}


# ----------------------------------------
# STEP 6: Prevent accidental overwriting
# ----------------------------------------
# seen_tables = set()
# final_table_relevance = {}

# for kws, table in cleaned_table_relevance.items():

#     # ensure only one mapping per table
#     if table in seen_tables:
#         continue

#     seen_tables.add(table)
#     final_table_relevance[kws] = table


# ----------------------------------------
# FINAL: Assign cleaned & safe dictionary
# ----------------------------------------
table_relevance = cleaned_table_relevance


default_ef = embedding_functions.DefaultEmbeddingFunction()
# Thread-local storage for each request thread
thread_local = threading.local()

# Single-threaded pool for queued write operations
chroma_write_pool = ThreadPoolExecutor(max_workers=1)

def get_chroma_client():
    """Ensure each thread has its own Chroma client."""
    if not hasattr(thread_local, "client"):
        thread_local.client = chromadb.PersistentClient(path="./chromadb_store")
    return thread_local.client

class ChromaDB_VectorStore(VannaBase):
    def __init__(self, config=None, max_workers=10):
        VannaBase.__init__(self, config=config)
        if config is None:
            config = {}

        path = config.get("path", ".")
        self.embedding_function = config.get("embedding_function", default_ef)
        curr_client = config.get("client", "persistent")
        collection_metadata = config.get("collection_metadata", None)
        self.n_results_sql = config.get("n_results_sql", config.get("n_results", 10))
        self.n_results_documentation = config.get("n_results_documentation", config.get("n_results", 5))
        self.n_results_ddl = config.get("n_results_ddl", config.get("n_results", 10))

        # Enable WAL mode for better SQLite concurrency
        settings = Settings(anonymized_telemetry=False, allow_reset=True)

        if curr_client == "persistent":
            self.chroma_client = chromadb.PersistentClient(
                path=path, settings=Settings(anonymized_telemetry=False)
            )
        # elif curr_client == "in-memory":
        #     self.chroma_client = chromadb.EphemeralClient(
        #         settings=Settings(anonymized_telemetry=False)
        #     )

        elif curr_client == "in-memory":
            self.chroma_client = chromadb.EphemeralClient(settings=settings)
            logger.info("Initialized EphemeralClient (in-memory)")  # NEW
        elif isinstance(curr_client, chromadb.api.client.Client):
            self.chroma_client = curr_client
            logger.info("Initialized with provided ChromaDB client")  # NEW
        else:
            raise ValueError(f"Unsupported client was set in config: {curr_client}")
        
        # ... (keep existing collection init: documentation_collection, ddl_collection, sql_collection)
        logger.info("Initialized standard collections: documentation, ddl, sql")  # NEW

        # Initialize standard collections
        self.documentation_collection = self.chroma_client.get_or_create_collection(
            name="documentation",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        # Remove hardcoded 'suriyan' workspace; we'll handle workspaces dynamically


        # Thread pool for parallel reads (embedding + queries)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"Initialized ThreadPoolExecutor with max_workers={max_workers} (current thread: {threading.current_thread().name})")  # NEW

        # Queue for serializing writes (to avoid SQLite conflicts)
        self.write_queue = queue.Queue(maxsize=100)  # Limit queue size to prevent memory buildup
        self.write_thread = None  # Will start a background thread for processing writes


    def log_pool_stats(self):  # NEW: Utility for monitoring (call in tests or timers)
        """Log current pool and queue stats for debugging."""
        active_threads = len(self.executor._threads) if hasattr(self.executor, '_threads') else 0
        pending_tasks = self.executor._work_queue.qsize() if hasattr(self.executor, '_work_queue') else 0
        queue_size = self.write_queue.qsize()
        logger.info(f"Pool Stats - Active Threads: {active_threads}, Pending Tasks: {pending_tasks}, Write Queue: {queue_size}/{self.write_queue.maxsize} (thread: {threading.current_thread().name})")


    # def _submit_to_pool(self, func, *args, **kwargs):
    #     """Helper to submit a task to the thread pool and return future."""
    #     future = self.executor.submit(func, *args, **kwargs)
    #     return future.result()  # Block until done (synchronous API for Vanna compatibility)

    def _submit_to_pool(self, func, *args, **kwargs):
        """Helper to submit a task to the thread pool and return future."""
        thread_name = threading.current_thread().name
        logger.info(f"Submitting task '{func.__name__}' to pool from thread {thread_name} with args: {args[:2]}...")  # NEW: Log submission
        future = self.executor.submit(func, *args, **kwargs)
        try:
            result = future.result(timeout=30)  # Block with timeout to prevent hangs
            logger.info(f"Task '{func.__name__}' completed successfully from thread {thread_name} (result type: {type(result)})")  # NEW
            return result
        except Exception as e:
            logger.error(f"Task '{func.__name__}' failed from thread {thread_name}: {e}", exc_info=True)  # NEW: Error with trace
            raise
    
    # def _async_add_to_collection(self, collection, documents, embeddings, ids):
    #     """Async wrapper for collection.add (for pooling)."""
    #     collection.add(documents=documents, embeddings=embeddings, ids=ids)

    # def _async_query_collection(self, collection, query_texts, n_results, **kwargs):
    #     """Async wrapper for collection.query (for pooling)."""
    #     return collection.query(query_texts=query_texts, n_results=n_results, **kwargs)


    def _async_add_to_collection(self, collection, documents, embeddings, ids):
        """Async wrapper for collection.add (for pooling)."""
        thread_name = threading.current_thread().name
        logger.debug(f"Adding to collection '{collection.name}' in thread {thread_name}: {len(documents)} docs")  # NEW
        collection.add(documents=documents, embeddings=embeddings, ids=ids)
        logger.debug(f"Add completed to '{collection.name}' in thread {thread_name}")  # NEW
    #commented on 24/10/2025
    # def _async_query_collection(self, collection, query_texts, n_results, **kwargs):
    #     """Async wrapper for collection.query (for pooling)."""
    #     thread_name = threading.current_thread().name
    #     logger.debug(f"Querying collection '{collection.name}' in thread {thread_name}: texts='{query_texts[0][:50]}...', n_results={n_results}")  # NEW
    #     result = collection.query(query_texts=query_texts, n_results=n_results, **kwargs)
    #     logger.debug(f"Query completed on '{collection.name}' in thread {thread_name}: {len(result.get('documents', []))} results")  # NEW
    #     return result
    def _async_query_collection(self, collection, query_texts, n_results, **kwargs):
        """Async wrapper for collection.query with None handling"""
        thread_name = threading.current_thread().name
        logger.debug(f"Querying collection '{collection.name}' in thread {thread_name}: texts='{query_texts[0][:50]}...', n_results={n_results}")
        
        try:
            result = collection.query(query_texts=query_texts, n_results=n_results, **kwargs)
            
            # Ensure result is not None
            if result is None:
                logger.warning(f"Collection query returned None for collection '{collection.name}'")
                return {"documents": []}  # Return empty result
            
            logger.debug(f"Query completed on '{collection.name}' in thread {thread_name}: {len(result.get('documents', []))} results")
            return result
            
        except Exception as e:
            logger.error(f"Query failed on collection '{collection.name}': {e}")
            return {"documents": []}  # Return empty result on error

    def _process_write_queue(self):
        """Background thread to process serialized writes."""
        while True:
            try:
                task = self.write_queue.get(timeout=1)  # Non-blocking get
                if task is None:  # Sentinel to stop
                    break
                collection_name, documents, embeddings, ids = task
                collection = self.chroma_client.get_or_create_collection(
                    name=collection_name, embedding_function=self.embedding_function
                )
                self._async_add_to_collection(collection, documents, embeddings, ids)  # Even writes can be pooled if low contention
                self.write_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Write queue error: {e}")

    def start_write_processor(self):
        """Start the background write processor thread."""
        if self.write_thread is None or not self.write_thread.is_alive():
            self.write_thread = self.executor.submit(self._process_write_queue)

    def stop_write_processor(self):
        """Stop the write processor (call on shutdown)."""
        self.write_queue.put(None)  # Sentinel
        if self.write_thread:
            self.write_thread.result()  # Wait for completion

    # def generate_embedding(self, data: str, **kwargs) -> List[float]:
    #     # Offload embedding to pool (CPU-bound)
    #     return self._submit_to_pool(self.embedding_function, [data])[0]  # DefaultEmbeddingFunction takes list

    # def generate_embedding(self, data: str, **kwargs) -> List[float]:
    #     # Offload embedding to pool (CPU-bound)
    #     thread_name = threading.current_thread().name
    #     logger.debug(f"Generating embedding for data len={len(data)} from {thread_name}")  # NEW
    #     embedding_list = self._submit_to_pool(self.embedding_function, [data])  # DefaultEmbeddingFunction takes list
    #     result = embedding_list[0]
    #     logger.debug(f"Embedding generated (len={len(result)}) from {thread_name}")  # NEW
    #     return result
    

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding = self.embedding_function([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    # def add_question_sql(self, question: str, sql: str, workspace: str, **kwargs) -> str:
    #     """
    #     Add a question-SQL pair to the specified workspace collection in ChromaDB.
    #     """
    #     logging.info(f"Fetching training data for add training data: {workspace}")
    #     if not workspace:
    #         raise ValueError("Workspace name is required")

    #     # Create or retrieve collection dynamically based on workspace name
    #     collection = self.chroma_client.get_or_create_collection(
    #         name=workspace,
    #         embedding_function=self.embedding_function,
    #     )

    #     # Prepare the question-SQL pair
    #     question_sql_json = json.dumps({"question": question, "sql": sql}, ensure_ascii=False)
    #     unique_id = deterministic_uuid(question_sql_json) + "-sql"
    #     embeddings=[self.generate_embedding(question_sql_json)],

    #     # Add to the collection
    #     collection.add(
    #         documents=[question_sql_json],
    #         embeddings=[self.generate_embedding(question_sql_json)],
    #         ids=[unique_id],
            
    #     )
    #     self.write_queue.put((workspace, [question_sql_json], [embeddings], [unique_id])),
    #     self.start_write_processor()  # Ensure processor is running

    #     return unique_id


    def add_question_sql(self, question: str, sql: str, workspace: str, db: str = None, **kwargs) -> str:
        """
        Add a question-SQL pair to the specified workspace collection in ChromaDB.
        """
        logging.info(f"Fetching training data for add training data: {workspace} (db={db or 'primary'})")
        if not workspace:
            raise ValueError("Workspace name is required")

        # Create or retrieve collection dynamically based on workspace name
        collection = self.chroma_client.get_or_create_collection(
            name=workspace,
            embedding_function=self.embedding_function,
        )

        resolved_db = db or getattr(self, "primary_db_alias", None) or "PRIMARY"

        # Prepare the question-SQL pair
        question_sql_json = json.dumps({"question": question, "sql": sql}, ensure_ascii=False)
        unique_id = deterministic_uuid(question_sql_json) + "-sql"

        # Add to the collection. Embed the question alone (not the JSON blob, which
        # would dilute the intent embedding with SQL/JSON syntax noise) — the stored
        # `documents` text keeps the full JSON for retrieval display. "type"/"db" go
        # into real Chroma metadata so retrieval can use `where` filters natively
        # instead of parsing them back out of the JSON text.
        collection.add(
            documents=[question_sql_json],
            embeddings=[self.generate_embedding(question)],
            metadatas=[{"type": "sql", "db": resolved_db}],
            ids=[unique_id],
        )

        return unique_id


    def get_training_data_module(self, collection_name: str, **kwargs) -> pd.DataFrame:
        logging.info(f"Fetching training data for collection: {collection_name}")

        df = pd.DataFrame()
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )
        data = collection.get()
        if data and "documents" in data:
            try:
                documents = [json.loads(doc) for doc in data["documents"]]
                ids = data["ids"]
                records = []
                for i, doc in enumerate(documents):
                    if doc.get("type") == "documentation":
                        records.append({
                            "id": ids[i],
                            "question": "",
                            "content": doc.get("content", ""),
                            "training_data_type": "documentation"
                        })
                    else:  # assume it's a SQL entry
                        records.append({
                            "id": ids[i],
                            "question": doc.get("question", ""),
                            "content": doc.get("sql", ""),
                            "training_data_type": "sql"
                        })
                df = pd.DataFrame(records)
            except Exception as e:
                logging.error(f"Error parsing documents in collection '{collection_name}': {e}")

        logging.info(f"Final training data for workspace '{collection_name}':\n{df}")
        return df






    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = deterministic_uuid(ddl) + "-ddl"
        self.ddl_collection.add(
            documents=ddl,
            embeddings=self.generate_embedding(ddl),
            ids=id,
        )
        return id

    def add_documentation(self, documentation: str, workspace: str, db: str = None, table: str = None, **kwargs) -> str:
        resolved_db = db or getattr(self, "primary_db_alias", None) or "PRIMARY"
        logging.info(f"Adding documentation to workspace: {workspace} (db={resolved_db})")
        if not workspace:
            raise ValueError("Workspace name is required")
        if not documentation:
            raise ValueError("Documentation content is required")

        collection = self.chroma_client.get_or_create_collection(
            name=workspace,
            embedding_function=self.embedding_function,
        )

        # Best-effort table name so retrieval can filter by (table, db) as real
        # Chroma metadata instead of regexing it back out of the content later.
        resolved_table = (table or self.extract_table_from_content(documentation) or "").lower() or None

        # Store documentation in structured JSON format. "db"/"table" also go into
        # real Chroma metadata (below) so retrieval can use `where` filters natively —
        # kept in the JSON too for backward compatibility with the regex-based fallback.
        doc_json = json.dumps({
            "content": documentation,
            "type": "documentation",
            "db": resolved_db,
            "table": resolved_table
        })

        doc_id = deterministic_uuid(documentation) + "-doc"
        collection.add(
            documents=[doc_json],
            embeddings=[self.generate_embedding(documentation)],
            metadatas=[{"type": "documentation", "db": resolved_db, "table": resolved_table or ""}],
            ids=[doc_id]
        )
        return doc_id

    # def get_training_data(self, **kwargs) -> pd.DataFrame:
    #     sql_data = self.sql_collection.get()
    #     df = pd.DataFrame()

    #     if sql_data is not None and "documents" in sql_data and sql_data["documents"]:
    #         documents = [json.loads(doc) for doc in sql_data["documents"]]
    #         ids = sql_data["ids"]
    #         df_sql = pd.DataFrame(
    #             {
    #                 "id": ids,
    #                 "question": [doc["question"] for doc in documents],
    #                 "content": [doc["sql"] for doc in documents],
    #             }
    #         )
    #         df_sql["training_data_type"] = "sql"
    #         df = pd.concat([df, df_sql])

    #     ddl_data = self.ddl_collection.get()
    #     if ddl_data is not None and "documents" in ddl_data and ddl_data["documents"]:
    #         documents = [doc for doc in ddl_data["documents"]]
    #         ids = ddl_data["ids"]
    #         df_ddl = pd.DataFrame(
    #             {
    #                 "id": ids,
    #                 "question": [None for _ in documents],
    #                 "content": [doc for doc in documents],
    #             }
    #         )
    #         df_ddl["training_data_type"] = "ddl"
    #         df = pd.concat([df, df_ddl])

    #     doc_data = self.documentation_collection.get()
    #     if doc_data is not None and "documents" in doc_data and doc_data["documents"]:
    #         documents = [doc for doc in doc_data["documents"]]
    #         ids = doc_data["ids"]
    #         df_doc = pd.DataFrame(
    #             {
    #                 "id": ids,
    #                 "question": [None for _ in documents],
    #                 "content": [doc for doc in documents],
    #             }
    #         )
    #         df_doc["training_data_type"] = "documentation"
    #         df = pd.concat([df, df_doc])

    #     return df
    def get_training_data(self, workspace: str = None, **kwargs) -> pd.DataFrame:
        df = pd.DataFrame()

        # Fetch SQL question data using get_similar_question_sql
        sql_results = self.get_similar_question_sql(
            question="",  # Empty question to retrieve all SQL entries
            workspace=workspace,  # Pass workspace parameter
            training_data_type="sql",
            **kwargs
        )

        if sql_results:
            sql_data = [
                {
                    "id": result["content"].get("id", f"sql_{i}"),
                    "question": result["content"].get("question"),
                    "content": result["content"].get("sql"),
                    "training_data_type": "sql"
                }
                for i, result in enumerate(sql_results)
                if result["type"] == "sql" and "question" in result["content"] and "sql" in result["content"]
            ]
            df_sql = pd.DataFrame(sql_data)
            df = pd.concat([df, df_sql])
            
        return df

    def edit_training_data(self, id: str, new_question: str = None, new_content: str = None, new_ddl: str = None, workspace: str = None, **kwargs) -> tuple[bool, str]:
        if not workspace:
            print("⚠️ Workspace name is required for editing training data")
            return False, None

        # Use workspace-specific collection
        workspace_collection = self.chroma_client.get_or_create_collection(
            name=workspace,
            embedding_function=self.embedding_function,
        )

        # Fetch existing data
        existing_data = workspace_collection.get(ids=[id])
        if not existing_data["documents"]:
            print(f"⚠️ No document found for ID: {id} in workspace: {workspace}")
            return False, None

        try:
            workspace_collection.delete(ids=[id])
            print(f"🗑️ Deleted old embedding: {id} from workspace: {workspace}")
        except Exception as e:
            print(f"❌ Error deleting embedding {id} from workspace {workspace}: {e}")
            return False, None

        old_data = json.loads(existing_data["documents"][0])

        if id.endswith("-sql"):
            # Handle SQL training data
            updated_question = new_question if new_question is not None else old_data.get("question", "")
            updated_sql = new_content if new_content is not None else old_data.get("sql", "")
            updated_json = json.dumps({"question": updated_question, "sql": updated_sql}, ensure_ascii=False)
            new_id = deterministic_uuid(updated_json) + "-sql"
        elif id.endswith("-doc"):
            # Handle documentation training data
            updated_content = new_content if new_content is not None else old_data.get("content", "")
            updated_json = json.dumps({"type": "documentation", "content": updated_content}, ensure_ascii=False)
            new_id = deterministic_uuid(updated_json) + "-doc"
        else:
            print(f"⚠️ Unsupported training data type for ID: {id}")
            return False, None

        # Check for ID conflicts
        existing_ids = workspace_collection.get(ids=[new_id])
        if existing_ids["documents"]:
            print(f"⚠️ Generated ID already exists: {new_id} in workspace: {workspace}")
            return False, None

        # Add updated data
        workspace_collection.add(
            documents=[updated_json],
            embeddings=[self.generate_embedding(updated_json)],
            ids=[new_id],
        )
        print(f"✅ Updated Training Data with New ID: {new_id} in workspace: {workspace}")
        return True, new_id
    

    
    def remove_training_data_module(self, id: str, workspace_name: str) -> bool:

        """

        Remove training data from the specified workspace collection in ChromaDB.

        

        Args:

            id (str): The unique ID of the training data to remove.

            workspace_name (str): The name of the workspace (ChromaDB collection) to operate on.

        

        Returns:

            bool: True if deletion was successful, False otherwise.

        """

        try:

            if not id or not workspace_name:

                logging.error(f"Missing id or workspace_name: id={id}, workspace_name={workspace_name}")

                return False



            # Get or create the workspace-specific collection

            workspace_collection = self.chroma_client.get_or_create_collection(

                name=workspace_name,

                embedding_function=self.embedding_function,

            )

            logging.info(f"inside chromadb workspace={workspace_name}")

            # Check if the ID exists in the collection

            existing_data = workspace_collection.get(ids=[id])

            if not existing_data or not existing_data["ids"] or id not in existing_data["ids"]:

                logging.info(f"No training data found with id={id} in workspace={workspace_name}")

                return False



            # Delete the training data by ID

            workspace_collection.delete(ids=[id])

            logging.info(f"Successfully deleted training data with id={id} from workspace={workspace_name}")

            return True



        except Exception as e:

            logging.error(f"Error deleting training data with id={id} from workspace={workspace_name}: {e}")

            return False


    def remove_training_data(self, id: str, **kwargs) -> bool:
        # SQL and documentation entries live in the per-workspace collection (see
        # add_question_sql/add_documentation), not the legacy global sql_collection/
        # documentation_collection — deleting from the wrong collection silently
        # no-ops (Chroma doesn't error on deleting a nonexistent id) while still
        # returning True, so this must target the same collection they were added to.
        workspace = kwargs.get("workspace")
        if (id.endswith("-sql") or id.endswith("-doc")) and workspace:
            collection = self.chroma_client.get_or_create_collection(
                name=workspace, embedding_function=self.embedding_function
            )
            collection.delete(ids=[id])
            return True
        elif id.endswith("-ddl"):
            # add_ddl still writes to the legacy global ddl_collection (not yet
            # workspace-scoped), so that's the correct target here.
            self.ddl_collection.delete(ids=[id])
            return True
        elif id.endswith("-sql") or id.endswith("-doc"):
            logging.error(f"remove_training_data: 'workspace' is required to delete {id}")
            return False
        return False

    def remove_collection(self, collection_name: str) -> bool:
        if collection_name == "sql":
            logging.info(f"Reached sql in remove collection {collection_name}")
            self.chroma_client.delete_collection(name="sql")
            self.sql_collection = self.chroma_client.get_or_create_collection(
                name="sql", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "ddl":
            logging.info(f"Reached ddl in remove collection {collection_name}")
            self.chroma_client.delete_collection(name="ddl")
            self.ddl_collection = self.chroma_client.get_or_create_collection(
                name="ddl", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "documentation":
            logging.info(f"Reached documentation in remove collection {collection_name}")
            self.chroma_client.delete_collection(name="documentation")
            self.documentation_collection = self.chroma_client.get_or_create_collection(
                name="documentation", embedding_function=self.embedding_function
            )
            return True
        else:
            logging.info(f"Reached else in remove collection {collection_name}")
            self.chroma_client.delete_collection(name=collection_name)
            return True

    @staticmethod
    def _extract_documents(query_results) -> list:
        if query_results is None:
            return []
        if "documents" in query_results:
            documents = query_results["documents"]
            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    return documents[0]
            return documents
        return []

    
    def get_related_ddl(self, question: str, **kwargs) -> list:
            return ChromaDB_VectorStore._extract_documents(
                self.ddl_collection.query(
                    query_texts=[question],
                    n_results=self.n_results_ddl,
                )
            )

    def get_write_whitelist(self, workspace: str = None, **kwargs) -> dict:
        """
        Currently a single global config (write_whitelist.json, loaded at module
        import), consistent with how glossary/table_relevance/query_mapping are
        loaded — swap the file per deployment if different workspaces need
        different write policies. Empty by default: no table is writable until
        this file is explicitly populated.
        """
        return write_whitelist_config


    def extract_table_from_content(self, content: str) -> str:
        """
        Robust extraction of table name from documentation text.
        Handles case-insensitive matches, backticks, quotes, and spacing variations.
        """
        import re, json

        if not content:
            return None

        text = content.strip()

        # Normalize case for detection while keeping original text intact
        lowered = text.lower()

        # Look for the phrase in any casing
        # Examples handled:
        # our definition of `t_table` is:
        # Our Definition Of 't_table' is:
        # OUR DEFINITION OF t_table IS :
        match = re.search(
            r"definition\s+of\s+[`'\"]?([a-zA-Z0-9_]+)[`'\"]?\s+is",
            lowered,
            flags=re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        # Try JSON style fallback
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "table" in data:
                return data["table"]
        except:
            pass

        return None

    def fetch_all_documentation(self, workspace: str) -> list:
        """
        Fetch all documentation data from the specified workspace collection in ChromaDB.

        Args:
            workspace (str): The name of the workspace (ChromaDB collection) to fetch data from.

        Returns:
            list: A list of dictionaries containing documentation entries (with "type": "documentation").
        """
        
        
        if not workspace:
            logging.error("Workspace name is required")
            return []

        try:
            # Get or create the workspace-specific collection
            collection = self.chroma_client.get_or_create_collection(
                name=workspace,
                embedding_function=self.embedding_function,
            )

            # Fetch all documents
            raw_docs = collection.get()
            if not raw_docs or "documents" not in raw_docs:
                logging.info(f"No documents found in workspace: {workspace}")
                return []

            # Process documents using _extract_documents
            results = ChromaDB_VectorStore._extract_documents(raw_docs)
            

            # Parse results to ensure all entries are dictionaries
            processed_docs = []
            for doc in results:
                if isinstance(doc, dict):
                    # Already a dictionary (parsed JSON)
                    processed_docs.append(doc)
                elif isinstance(doc, str):
                    try:
                        # Try parsing as JSON
                        parsed_doc = json.loads(doc)
                        processed_docs.append(parsed_doc)
                    except json.JSONDecodeError:
                        # Plain string, wrap in a dictionary
                        processed_docs.append({
                            "content": doc,
                            "type": "documentation",  # Default type for plain strings
                            "metadata": {},
                            "id": None,
                            "distance": None
                        })
                else:
                    logging.warning(f"Skipping document of unexpected type: {type(doc)}")

            # Filter for documentation-type entries
            documentation_results = [
                doc for doc in processed_docs
                if isinstance(doc, dict) and doc.get("type") == "documentation"
            ]
            

            return documentation_results

        except Exception as e:
            logging.error(f"Failed to fetch documentation data for workspace {workspace}: {e}")
            return []
    def hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()
 


    def normalize_keyword(self, text: str) -> str:
        """
        SIMPLE normalization for exact matching - preserves original word structure
        """
        if not text:
            return ""
        
        # Convert to lowercase only
        normalized = text.lower()
        
        # Remove extra whitespace only
        normalized = ' '.join(normalized.split())
        
        # Remove ONLY trailing punctuation (preserves internal punctuation)
        normalized = re.sub(r'[?.!,;]*$', '', normalized).strip()
        
        return normalized

  
   

   

    # def _enrich_table_documentation(self, doc_results: list, matched_tables: list, table_scores: dict, workspace: str, collection) -> list:
    #     """
    #     Helper function to enrich documentation by combining vector search results 
    #     with table relevance matches. Fetches missing table documentation from ChromaDB.
        
    #     Args:
    #         doc_results: Documentation from vector search
    #         matched_tables: Tables from table_relevance keyword matching
    #         table_scores: Relevance scores for matched tables
    #         workspace: Workspace name
    #         collection: ChromaDB collection object
        
    #     Returns:
    #         list: Enriched documentation list (max 5 tables)
    #     """
    #     import logging
        
    #     logger.info(
    #         f"[_enrich_table_documentation] BEGIN | DocResults={len(doc_results)} | MatchedTables={matched_tables}",
    #         extra={"admin": True}
    #     )
        
    #     # === STEP 1: Extract tables from vector search results ===
    #     tables_from_docs = set()
    #     for doc in doc_results:
    #         content = doc.get("content", "")
    #         table_name = self.extract_table_from_content(content)
    #         if table_name:
    #             tables_from_docs.add(table_name)
    #             logger.info(f"[_enrich_table_documentation] Extracted table '{table_name}' from doc result")
        
    #     # === STEP 2: Merge with matched_tables (Priority: docs > table_relevance) ===
    #     # Sort matched_tables by their relevance scores (highest first)
    #     sorted_matched = sorted(
    #         [(table, table_scores.get(table, 0)) for table in matched_tables],
    #         key=lambda x: x[1],
    #         reverse=True
    #     )
        
    #     # Build final table list with priority
    #     final_tables = []
        
    #     # Priority 1: Tables from doc_results (vector search)
    #     for table in tables_from_docs:
    #         if len(final_tables) < 5:
    #             final_tables.append(table)
        
    #     # Priority 2: Tables from table_relevance (by score)
    #     for table, score in sorted_matched:
    #         if len(final_tables) >= 5:
    #             break
    #         if table not in final_tables:
    #             final_tables.append(table)
        
    #     logger.info(
    #         f"[_enrich_table_documentation] Final merged tables (max 5): {final_tables}",
    #         extra={"admin": True}
    #     )
        
    #     # === STEP 3: Fetch missing table documentation ===
    #     # Tables that need documentation fetched
    #     tables_needing_docs = [t for t in final_tables if t not in tables_from_docs]
        
    #     if not tables_needing_docs:
    #         logger.info(
    #             f"[_enrich_table_documentation] All tables already have docs from vector search. Returning {len(doc_results)} docs.",
    #             extra={"admin": True}
    #         )
    #         return doc_results
        
    #     logger.info(
    #         f"[_enrich_table_documentation] Fetching docs for missing tables: {tables_needing_docs}",
    #         extra={"admin": True}
    #     )
        
    #     # Fetch all documentation from workspace
    #     try:
    #         all_docs = self.fetch_all_documentation(workspace)
    #     except Exception as e:
    #         logger.error(f"[_enrich_table_documentation] Failed to fetch all docs: {e}", extra={"admin": True})
    #         return doc_results
        
    #     # Find documentation for missing tables
    #     additional_docs = []
    #     for doc in all_docs:
    #         content = doc.get("content", "")
    #         table_name = self.extract_table_from_content(content)
            
    #         if table_name in tables_needing_docs:
    #             # Check if not already in doc_results (avoid duplicates)
    #             content_hash = self.hash_content(content)
    #             if not any(self.hash_content(d.get("content", "")) == content_hash for d in doc_results):
    #                 additional_docs.append(doc)
    #                 logger.info(
    #                     f"[_enrich_table_documentation] Added doc for table '{table_name}' from table_relevance",
    #                     extra={"admin": True}
    #                 )
        
    #     # === STEP 4: Combine and deduplicate ===
    #     combined_docs = doc_results + additional_docs
        
    #     # Deduplicate by content hash
    #     seen_hashes = set()
    #     unique_docs = []
    #     for doc in combined_docs:
    #         content_hash = self.hash_content(doc.get("content", ""))
    #         if content_hash not in seen_hashes:
    #             unique_docs.append(doc)
    #             seen_hashes.add(content_hash)
        
    #     logger.info(
    #         f"[_enrich_table_documentation] COMPLETE | Original={len(doc_results)} | Added={len(additional_docs)} | Final={len(unique_docs)}",
    #         extra={"admin": True}
    #     )
        
    #     return unique_docs
    


    # def get_similar_question_sql(self, question: str, workspace: str = None, training_data_type: str = None, **kwargs) -> dict | list:
    #     """
    #     Unified retrieval for SQL + Documentation, including domain context.
    #     Returns both embeddings and domain context (glossary, tables, query_mapping).
    #     NOW WITH TABLE DOCUMENTATION ENRICHMENT!
    #     """
    #     import re, ast, asyncio, traceback
    #     from fuzzywuzzy import fuzz

    #     thread_name = threading.current_thread().name
    #     training_data_type = (training_data_type or "").strip().lower()

    #     logger.info(
    #         f"[get_similar_question_sql] BEGIN | Thread={thread_name} | Type={training_data_type or 'none'} | Workspace={workspace or 'none'} | Question='{(question or '').strip()}'",
    #         extra={"admin": True},
    #     )

    #     # === PREVENT EMPTY INPUTS ===
    #     if not question or not question.strip():
    #         logger.warning(
    #             "[get_similar_question_sql] Skipping embedding generation because question is empty.",
    #             extra={"admin": True},
    #         )
    #         return []

    #     try:
    #         # === STEP 1: EXACT MATCH FIRST (SQL only) ===
    #         if training_data_type in ("sql", "all"):
    #             exact_matches = self._find_exact_matches_first(question, workspace)
    #             if exact_matches:
    #                 logger.info(
    #                     f"[get_similar_question_sql] Exact SQL match FOUND | Count={len(exact_matches)} | Returning immediately",
    #                     extra={"admin": True},
    #                 )
    #                 if training_data_type == "all":
    #                     return {
    #                         "sql": exact_matches,
    #                         "documentation": [],
    #                         "context": {"glossary": [], "tables": [], "query_mapping": []},
    #                     }
    #                 return exact_matches
    #             else:
    #                 logger.info(
    #                     f"[get_similar_question_sql] No exact SQL match for '{question.strip()}' - proceeding to similarity search",
    #                     extra={"admin": True},
    #                 )

    #         # === STEP 2: NORMALIZE + TOKENIZE ===
    #         normalized_question = self.normalize_keyword(question)
    #         tokens = re.findall(r"\w+", normalized_question)
    #         token_set = set(tokens)
    #         bigrams = {" ".join(tokens[i:i+2]) for i in range(len(tokens) - 1)}

    #         collection = (
    #             self.chroma_client.get_or_create_collection(
    #                 name=workspace, embedding_function=self.embedding_function
    #             )
    #             if workspace
    #             else self.sql_collection
    #         )

    #         query_kwargs = {k: v for k, v in kwargs.items() if k not in ["allow_llm_to_see_data", "followup_sql"]}

    #         # === STEP 3: GLOSSARY MATCHING ===
    #         matched_glossary_keys, matched_keywords = [], []
    #         for key, entry in glossary.items():
    #             for term in entry.get("terms", []):
    #                 nt = self.normalize_keyword(term)
    #                 if (
    #                     nt in normalized_question
    #                     or nt in token_set
    #                     or nt in bigrams
    #                     or fuzz.partial_ratio(nt, normalized_question) > 80
    #                 ):
    #                     matched_glossary_keys.append(key)
    #                     matched_keywords.append(term)
    #                     break

    #         # === STEP 4: TABLE RELEVANCE MATCH ===
    #         matched_tables, table_scores = [], {}
    #         for kw_tuple, table in table_relevance.items():
    #             try:
    #                 kws = ast.literal_eval(kw_tuple) if isinstance(kw_tuple, str) else kw_tuple
    #                 if not isinstance(kws, (list, tuple)):
    #                     kws = [kws]
    #             except Exception:
    #                 kws = [kw_tuple]
    #             score = sum(1 for kw in kws if self.normalize_keyword(kw) in normalized_question or self.normalize_keyword(kw) in token_set)
    #             if score > 0:
    #                 table_scores[table] = score
    #         if table_scores:
    #             matched_tables = [t[0] for t in sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[:3]]

    #         # === STEP 5: QUERY MAPPING MATCH ===
    #         matched_query_mapping_keys = []
    #         for key, mapping in query_mapping.items():
    #             hit = False
    #             if isinstance(mapping, dict):
    #                 table_name = mapping.get("table")
    #                 if table_name and (
    #                     self.normalize_keyword(table_name) in normalized_question
    #                     or self.normalize_keyword(table_name) in token_set
    #                     or self.normalize_keyword(table_name) in bigrams
    #                 ):
    #                     hit = True
    #                 for col in mapping.get("columns", []):
    #                     if self.normalize_keyword(col) in normalized_question or self.normalize_keyword(col) in token_set:
    #                         hit = True
    #                         break
    #             if hit or (self.normalize_keyword(key) in normalized_question or self.normalize_keyword(key) in token_set):
    #                 matched_query_mapping_keys.append(key)

    #         # === STEP 6: LOG SUMMARY ===
    #         logger.info(
    #             f"[get_similar_question_sql] Context matches -> Glossary={matched_glossary_keys or 'None'} | Tables={matched_tables or 'None'} | QueryMapping={matched_query_mapping_keys or 'None'}",
    #             extra={"admin": True},
    #         )

    #         # === STEP 7: BUILD ENRICHED QUERY TEXT ===
    #         query_tables = set(matched_tables)
    #         for k in matched_glossary_keys + matched_query_mapping_keys:
    #             mapping = query_mapping.get(k, {})
    #             if isinstance(mapping, dict):
    #                 tname = mapping.get("table")
    #                 if tname:
    #                     query_tables.add(tname)

    #         query_text = f"{question} {' '.join(query_tables)} {' '.join(matched_keywords * 2)}".strip()

    #         # === STEP 8: RUN BOTH SQL & DOC RETRIEVAL ASYNC ===
    #         async def async_retrieve():
    #             sql_task = asyncio.to_thread(
    #                 self._submit_to_pool, self._async_query_collection, collection, [query_text], self.n_results_sql, **query_kwargs
    #             )
    #             doc_task = asyncio.to_thread(
    #                 self._submit_to_pool, self._async_query_collection, collection, [query_text], self.n_results_documentation, **query_kwargs
    #             )
    #             return await asyncio.gather(sql_task, doc_task)

    #         sql_results, doc_results = [], []
    #         try:
    #             sql_raw, doc_raw = asyncio.run(async_retrieve())
    #             sql_extracted = ChromaDB_VectorStore._extract_documents(sql_raw)
    #             doc_extracted = ChromaDB_VectorStore._extract_documents(doc_raw)
    #             sql_results = [r for r in sql_extracted if isinstance(r, dict) and "question" in r and r.get("sql")]
    #             doc_results = [r for r in doc_extracted if isinstance(r, dict) and r.get("type") == "documentation"]
    #         except Exception as e:
    #             logger.error(f"[get_similar_question_sql] Async embedding retrieval failed: {e}", extra={"admin": True})

    #         # === STEP 8.5: 🆕 ENRICH DOCUMENTATION WITH TABLE RELEVANCE ===
    #         doc_results = self._enrich_table_documentation(
    #             doc_results=doc_results,
    #             matched_tables=matched_tables,
    #             table_scores=table_scores,
    #             workspace=workspace,
    #             collection=collection
    #         )

    #         logger.info(
    #             f"[get_similar_question_sql] Final combined results -> SQL={len(sql_results)} | DOC={len(doc_results)} | Glossary={len(matched_glossary_keys)}",
    #             extra={"admin": True},
    #         )

    #         # === STEP 9: RETURN ENRICHED CONTEXT ===
    #         return {
    #             "sql": sql_results,
    #             "documentation": doc_results,
    #             "context": {
    #                 "glossary": matched_glossary_keys,
    #                 "tables": matched_tables,
    #                 "query_mapping": matched_query_mapping_keys,
    #             },
    #         }

    #     except Exception as e:
    #         tb = traceback.format_exc()
    #         logger.error(f"[get_similar_question_sql] Exception for '{question.strip()}': {e}\n{tb}", extra={"admin": True})
    #         return {"sql": [], "documentation": [], "context": {"glossary": [], "tables": [], "query_mapping": []}}


    #lasted updated on 5/11/2025
    # def get_similar_question_sql(self, question: str, workspace: str = None, training_data_type: str = None, **kwargs) -> dict | list:
    #     """
    #     Unified retrieval for SQL + Documentation, including domain context.
    #     Returns both embeddings and domain context (glossary, tables, query_mapping).
    #     """
    #     import re, ast, asyncio, traceback
    #     from fuzzywuzzy import fuzz

    #     thread_name = threading.current_thread().name
    #     training_data_type = (training_data_type or "").strip().lower()

    #     logger.info(
    #         f"[get_similar_question_sql] BEGIN | Thread={thread_name} | Type={training_data_type or 'none'} | Workspace={workspace or 'none'} | Question='{(question or '').strip()}'",
    #         extra={"admin": True},
    #     )

    #    # === PREVENT EMPTY INPUTS ===
    #         if not question or not question.strip():
    #             logger.warning(
    #                 "[get_similar_question_sql] Skipping embedding generation because question is empty.",
    #                 extra={"admin": True},
    #             )
    #             return []

    #     try:
    #         # === STEP 1: EXACT MATCH FIRST (SQL only) ===
    #         if training_data_type in ("sql", "all"):
    #             exact_matches = self._find_exact_matches_first(question, workspace)
    #             if exact_matches:
    #                 logger.info(
    #                     f"[get_similar_question_sql] Exact SQL match FOUND | Count={len(exact_matches)} | Returning immediately",
    #                     extra={"admin": True},
    #                 )
    #                 if training_data_type == "all":
    #                     return {
    #                         "sql": exact_matches,
    #                         "documentation": [],
    #                         "context": {"glossary": [], "tables": [], "query_mapping": []},
    #                     }
    #                 return exact_matches
    #             else:
    #                 logger.info(
    #                     f"[get_similar_question_sql] No exact SQL match for '{question.strip()}' - proceeding to similarity search",
    #                     extra={"admin": True},
    #                 )

    #         # === STEP 2: NORMALIZE + TOKENIZE ===
    #         normalized_question = self.normalize_keyword(question)
    #         tokens = re.findall(r"\w+", normalized_question)
    #         token_set = set(tokens)
    #         bigrams = {" ".join(tokens[i:i+2]) for i in range(len(tokens) - 1)}

    #         collection = (
    #             self.chroma_client.get_or_create_collection(
    #                 name=workspace, embedding_function=self.embedding_function
    #             )
    #             if workspace
    #             else self.sql_collection
    #         )

    #         query_kwargs = {k: v for k, v in kwargs.items() if k not in ["allow_llm_to_see_data", "followup_sql"]}

    #         # === STEP 3: GLOSSARY MATCHING ===
    #         matched_glossary_keys, matched_keywords = [], []
    #         for key, entry in glossary.items():
    #             for term in entry.get("terms", []):
    #                 nt = self.normalize_keyword(term)
    #                 if (
    #                     nt in normalized_question
    #                     or nt in token_set
    #                     or nt in bigrams
    #                     or fuzz.partial_ratio(nt, normalized_question) > 80
    #                 ):
    #                     matched_glossary_keys.append(key)
    #                     matched_keywords.append(term)
    #                     break

    #         # === STEP 4: TABLE RELEVANCE MATCH ===
    #         matched_tables, table_scores = [], {}
    #         for kw_tuple, table in table_relevance.items():
    #             try:
    #                 kws = ast.literal_eval(kw_tuple) if isinstance(kw_tuple, str) else kw_tuple
    #                 if not isinstance(kws, (list, tuple)):
    #                     kws = [kws]
    #             except Exception:
    #                 kws = [kw_tuple]
    #             score = sum(1 for kw in kws if self.normalize_keyword(kw) in normalized_question or self.normalize_keyword(kw) in token_set)
    #             if score > 0:
    #                 table_scores[table] = score
    #         if table_scores:
    #             matched_tables = [t[0] for t in sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[:3]]

    #         # === STEP 5: QUERY MAPPING MATCH ===
    #         matched_query_mapping_keys = []
    #         for key, mapping in query_mapping.items():
    #             hit = False
    #             if isinstance(mapping, dict):
    #                 table_name = mapping.get("table")
    #                 if table_name and (
    #                     self.normalize_keyword(table_name) in normalized_question
    #                     or self.normalize_keyword(table_name) in token_set
    #                     or self.normalize_keyword(table_name) in bigrams
    #                 ):
    #                     hit = True
    #                 for col in mapping.get("columns", []):
    #                     if self.normalize_keyword(col) in normalized_question or self.normalize_keyword(col) in token_set:
    #                         hit = True
    #                         break
    #             if hit or (self.normalize_keyword(key) in normalized_question or self.normalize_keyword(key) in token_set):
    #                 matched_query_mapping_keys.append(key)

    #         # === STEP 6: LOG SUMMARY ===
    #         logger.info(
    #             f"[get_similar_question_sql] Context matches -> Glossary={matched_glossary_keys or 'None'} | Tables={matched_tables or 'None'} | QueryMapping={matched_query_mapping_keys or 'None'}",
    #             extra={"admin": True},
    #         )

    #         # === STEP 7: BUILD ENRICHED QUERY TEXT ===
    #         query_tables = set(matched_tables)
    #         for k in matched_glossary_keys + matched_query_mapping_keys:
    #             mapping = query_mapping.get(k, {})
    #             if isinstance(mapping, dict):
    #                 tname = mapping.get("table")
    #                 if tname:
    #                     query_tables.add(tname)

    #         query_text = f"{question} {' '.join(query_tables)} {' '.join(matched_keywords * 2)}".strip()

    #         # === STEP 8: RUN BOTH SQL & DOC RETRIEVAL ASYNC ===
    #         async def async_retrieve():
    #             sql_task = asyncio.to_thread(
    #                 self._submit_to_pool, self._async_query_collection, collection, [query_text], self.n_results_sql, **query_kwargs
    #             )
    #             doc_task = asyncio.to_thread(
    #                 self._submit_to_pool, self._async_query_collection, collection, [query_text], self.n_results_documentation, **query_kwargs
    #             )
    #             return await asyncio.gather(sql_task, doc_task)

    #         sql_results, doc_results = [], []
    #         try:
    #             sql_raw, doc_raw = asyncio.run(async_retrieve())
    #             sql_extracted = ChromaDB_VectorStore._extract_documents(sql_raw)
    #             doc_extracted = ChromaDB_VectorStore._extract_documents(doc_raw)
    #             sql_results = [r for r in sql_extracted if isinstance(r, dict) and "question" in r and r.get("sql")]
    #             doc_results = [r for r in doc_extracted if isinstance(r, dict) and r.get("type") == "documentation"]
    #         except Exception as e:
    #             logger.error(f"[get_similar_question_sql] Async embedding retrieval failed: {e}", extra={"admin": True})

    #         logger.info(
    #             f"[get_similar_question_sql] Final combined results -> SQL={len(sql_results)} | DOC={len(doc_results)} | Glossary={len(matched_glossary_keys)}",
    #             extra={"admin": True},
    #         )



    #         # === STEP 9: RETURN ENRICHED CONTEXT ===
    #         return {
    #             "sql": sql_results,
    #             "documentation": doc_results,
    #             "context": {
    #                 "glossary": matched_glossary_keys,
    #                 "tables": matched_tables,
    #                 "query_mapping": matched_query_mapping_keys,
    #             },
    #         }

    #     except Exception as e:
    #         tb = traceback.format_exc()
    #         logger.error(f"[get_similar_question_sql] Exception for '{question.strip()}': {e}\n{tb}", extra={"admin": True})
    #         return {"sql": [], "documentation": [], "context": {"glossary": [], "tables": [], "query_mapping": []}}



    #new code for tables relevecn documatation adndoc retraivel adds as totla 5 
    #commented out december 
    # def get_similar_question_sql(self, question: str, workspace: str = None, training_data_type: str = None, **kwargs) -> dict | list:
    #     """
    #     Unified retrieval for SQL + Documentation, including domain context.
    #     Returns both embeddings and domain context (glossary, tables, query_mapping).
    #     Now includes enriched documentation (up to 5 total across vector + table relevance),
    #     and logs exactly which table documentations are being sent to the LLM.
    #     """
    #     import re, ast, asyncio, traceback
    #     from fuzzywuzzy import fuzz
    #     import threading

    #     thread_name = threading.current_thread().name
    #     training_data_type = (training_data_type or "").strip().lower()

    #     logger.info(
    #         f"[get_similar_question_sql] BEGIN | Thread={thread_name} | Type={training_data_type or 'none'} | Workspace={workspace or 'none'} | Question='{(question or '').strip()}'",
    #         extra={"admin": True},
    #     )

    #     # === PREVENT EMPTY INPUTS ===
    #     if not question or not question.strip():
    #         logger.warning(
    #             "[get_similar_question_sql] Skipping embedding generation because question is empty.",
    #             extra={"admin": True},
    #         )
    #         return []

    #     try:
    #         # === STEP 1: EXACT MATCH FIRST (SQL only) ===
    #         if training_data_type in ("sql", "all"):
    #             exact_matches = self._find_exact_matches_first(question, workspace)
    #             if exact_matches:
    #                 logger.info(
    #                     f"[get_similar_question_sql] Exact SQL match FOUND | Count={len(exact_matches)} | Returning immediately",
    #                     extra={"admin": True},
    #                 )
    #                 if training_data_type == "all":
    #                     return {
    #                         "sql": exact_matches,
    #                         "documentation": [],
    #                         "context": {"glossary": [], "tables": [], "query_mapping": []},
    #                     }
    #                 return exact_matches
    #             else:
    #                 logger.info(
    #                     f"[get_similar_question_sql] No exact SQL match for '{question.strip()}' - proceeding to similarity search",
    #                     extra={"admin": True},
    #                 )

    #         # === STEP 2: NORMALIZE + TOKENIZE ===
    #         normalized_question = self.normalize_keyword(question)
    #         tokens = re.findall(r"\w+", normalized_question)
    #         token_set = set(tokens)
    #         bigrams = {" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)}

    #         collection = (
    #             self.chroma_client.get_or_create_collection(
    #                 name=workspace, embedding_function=self.embedding_function
    #             )
    #             if workspace
    #             else self.sql_collection
    #         )

    #         query_kwargs = {k: v for k, v in kwargs.items() if k not in ["allow_llm_to_see_data", "followup_sql"]}

    #         # === STEP 3: GLOSSARY MATCHING ===
    #         matched_glossary_keys, matched_keywords = [], []
    #         for key, entry in glossary.items():
    #             for term in entry.get("terms", []):
    #                 nt = self.normalize_keyword(term)
    #                 if (
    #                     nt in normalized_question
    #                     or nt in token_set
    #                     or nt in bigrams
    #                     or fuzz.partial_ratio(nt, normalized_question) > 80
    #                 ):
    #                     matched_glossary_keys.append(key)
    #                     matched_keywords.append(term)
    #                     break


    #         # === STEP 4: TABLE RELEVANCE MATCH ===
    #         matched_tables, table_scores = [], {}

    #         # Precompute embedding for question only once
    #         try:
    #             q_vec = self.embedding_function.embed_query(question)
    #         except:
    #             q_vec = None

    #         for kw_tuple, table in table_relevance.items():

    #             # ---- Existing rule-based keyword scoring (KEEP THIS) ----
    #             try:
    #                 kws = ast.literal_eval(kw_tuple) if isinstance(kw_tuple, str) else kw_tuple
    #                 if not isinstance(kws, (list, tuple)):
    #                     kws = [kws]
    #             except:
    #                 kws = [kw_tuple]

    #             rule_score = 0
    #             for kw in kws:
    #                 norm_kw = self.normalize_keyword(kw)
    #                 kw_tokens = [t for t in norm_kw.split() if len(t) > 2]

    #                 if any(t in token_set for t in kw_tokens):
    #                     rule_score += 1
    #                     continue

    #                 if any(f" {t} " in f" {normalized_question} " for t in kw_tokens):
    #                     rule_score += 1
    #                     continue

    #                 if any(fuzz.partial_ratio(t, normalized_question) > 85 for t in kw_tokens if len(t) > 4):
    #                     rule_score += 1
    #                     continue

    #             # ---- NEW semantic scoring (NO new library, uses your existing embeddings) ----
    #             semantic_score = 0
    #             if q_vec:
    #                 kw_text = " ".join(kws)
    #                 try:
    #                     kw_vec = self.embedding_function.embed_query(kw_text)
    #                     # manual cosine similarity (no external dependency)
    #                     dot = sum(a * b for a, b in zip(q_vec, kw_vec))
    #                     norm_q = sum(a * a for a in q_vec) ** 0.5
    #                     norm_kw = sum(a * a for a in kw_vec) ** 0.5
    #                     semantic_score = dot / (norm_q * norm_kw + 1e-9)
    #                 except:
    #                     semantic_score = 0

    #             # ---- final score combining rule + semantic (lightweight and powerful) ----
    #             #final_score = (0.3 * rule_score) + (0.7 * semantic_score)
    #             final_score = semantic_score + (0.1 * rule_score)

    #             if final_score > 0:
    #                 table_scores[table] = final_score

    #         # Sort based on final_score
    #         if table_scores:
    #             matched_tables = [
    #                 t[0] for t in sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    #             ]



    #         # === STEP 5: QUERY MAPPING MATCH ===
    #         matched_query_mapping_keys = []
    #         for key, mapping in query_mapping.items():
    #             hit = False
    #             if isinstance(mapping, dict):
    #                 table_name = mapping.get("table")
    #                 if table_name and (
    #                     self.normalize_keyword(table_name) in normalized_question
    #                     or self.normalize_keyword(table_name) in token_set
    #                     or self.normalize_keyword(table_name) in bigrams
    #                 ):
    #                     hit = True
    #                 for col in mapping.get("columns", []):
    #                     if self.normalize_keyword(col) in normalized_question or self.normalize_keyword(col) in token_set:
    #                         hit = True
    #                         break
    #             if hit or (self.normalize_keyword(key) in normalized_question or self.normalize_keyword(key) in token_set):
    #                 matched_query_mapping_keys.append(key)

    #         # === STEP 6: LOG SUMMARY ===
    #         logger.info(
    #             f"[get_similar_question_sql] Context matches -> Glossary={matched_glossary_keys or 'None'} | Tables={matched_tables or 'None'} | QueryMapping={matched_query_mapping_keys or 'None'}",
    #             extra={"admin": True},
    #         )

    #         # === STEP 7: BUILD ENRICHED QUERY TEXT ===
    #         query_tables = set(matched_tables)
    #         for k in matched_glossary_keys + matched_query_mapping_keys:
    #             mapping = query_mapping.get(k, {})
    #             if isinstance(mapping, dict):
    #                 tname = mapping.get("table")
    #                 if tname:
    #                     query_tables.add(tname)

    #         query_text = f"{question} {' '.join(query_tables)} {' '.join(matched_keywords * 2)}".strip()

    #         # === STEP 8: RUN BOTH SQL & DOC RETRIEVAL ASYNC ===
    #         async def async_retrieve():
    #             sql_task = asyncio.to_thread(
    #                 self._submit_to_pool,
    #                 self._async_query_collection,
    #                 collection,
    #                 [query_text],
    #                 self.n_results_sql,
    #                 **query_kwargs,
    #             )
    #             doc_task = asyncio.to_thread(
    #                 self._submit_to_pool,
    #                 self._async_query_collection,
    #                 collection,
    #                 [query_text],
    #                 self.n_results_documentation,
    #                 **query_kwargs,
    #             )
    #             return await asyncio.gather(sql_task, doc_task)

    #         sql_results, doc_results = [], []
    #         try:
    #             sql_raw, doc_raw = asyncio.run(async_retrieve())
    #             sql_extracted = ChromaDB_VectorStore._extract_documents(sql_raw)
    #             doc_extracted = ChromaDB_VectorStore._extract_documents(doc_raw)
    #             sql_results = [r for r in sql_extracted if isinstance(r, dict) and "question" in r and r.get("sql")]
    #             doc_results = [r for r in doc_extracted if isinstance(r, dict) and r.get("type") == "documentation"]
    #         except Exception as e:
    #             logger.error(f"[get_similar_question_sql] Async embedding retrieval failed: {e}", extra={"admin": True})

    #         # === STEP 8.5: ENRICH DOCUMENTATION (LIMIT 5 TOTAL) ===
    #         try:
    #             doc_results = self._enrich_table_documentation(
    #                 doc_results=doc_results,
    #                 matched_tables=matched_tables,
    #                 table_scores=table_scores,
    #                 workspace=workspace,
    #                 collection=collection
    #             )
    #         except Exception as e:
    #             logger.error(f"[get_similar_question_sql] _enrich_table_documentation failed: {e}", extra={"admin": True})


    #         # NEW LOGGING ENHANCEMENT HERE
    #         try:
    #             # Extract table names from final docs
    #             final_doc_tables = []
    #             for d in doc_results:
    #                 content = d.get("content", "")
    #                 table_name = self.extract_table_from_content(content)
    #                 if table_name:
    #                     final_doc_tables.append(table_name)

    #             logger.info(
    #                 f"[get_similar_question_sql] Documentation sent to LLM -> {final_doc_tables or 'None'}",
    #                 extra={"admin": True},
    #             )
    #         except Exception as e:
    #             logger.warning(f"[get_similar_question_sql] Failed to extract doc table names for logging: {e}")

    #         # === STEP 9: FINAL SUMMARY ===
    #         logger.info(
    #             f"[get_similar_question_sql] Final combined results -> SQL={len(sql_results)} | DOC={len(doc_results)} | Glossary={len(matched_glossary_keys)}",
    #             extra={"admin": True},
    #         )

    #         # === STEP 10: RETURN ENRICHED CONTEXT ===
    #         return {
    #             "sql": sql_results,
    #             "documentation": doc_results[:5],  # enforce final doc cap at 5
    #             "context": {
    #                 "glossary": matched_glossary_keys,
    #                 "tables": matched_tables,
    #                 "query_mapping": matched_query_mapping_keys,
    #             },
    #         }

    #     except Exception as e:
    #         tb = traceback.format_exc()
    #         logger.error(f"[get_similar_question_sql] Exception for '{question.strip()}': {e}\n{tb}", extra={"admin": True})
    #         return {"sql": [], "documentation": [], "context": {"glossary": [], "tables": [], "query_mapping": []}}

    def get_similar_question_sql(
        self,
        question: str,
        workspace: str = None,
        training_data_type: str = None,
        **kwargs,
    ) -> dict | list:
        """
        Unified retrieval for SQL + Documentation, including domain context.

        Uses:
        - Exact match on SQL dataset (if available)
        - Glossary.json
        - table_relevance.json (pre-cleaned into `table_relevance`)
        - query_mapping.json
        - ChromaDB vector search for SQL + documentation

        Returns (when training_data_type == "all"):
            {
                "sql": [ ... ],
                "documentation": [ ... up to 5 ... ],
                "context": {
                    "glossary": [...matched glossary keys...],
                    "tables": [...top-5 tables...],
                    "query_mapping": [...matched query mapping keys...],
                },
            }

        Returns SQL list when training_data_type == "sql".
        """

        import re, ast, asyncio, traceback
        from fuzzywuzzy import fuzz
        import threading

        thread_name = threading.current_thread().name
        training_data_type = (training_data_type or "").strip().lower()

        logger.info(
            f"[get_similar_question_sql] BEGIN | Thread={thread_name} | "
            f"Type={training_data_type or 'none'} | "
            f"Workspace={workspace or 'none'} | "
            f"Question='{(question or '').strip()}'",
            extra={"admin": True},
        )

        # === PREVENT EMPTY INPUTS ===
        if not question or not question.strip():
            logger.warning(
                "[get_similar_question_sql] Skipping embedding generation because question is empty.",
                extra={"admin": True},
            )
            return []

        try:
            # === STEP 1: EXACT MATCH FIRST (SQL only) ===
            if training_data_type in ("sql", "all"):
                exact_matches = self._find_exact_matches_first(question, workspace)
                if exact_matches:
                    logger.info(
                        f"[get_similar_question_sql] Exact SQL match FOUND | Count={len(exact_matches)} | Returning immediately",
                        extra={"admin": True},
                    )
                    if training_data_type == "all":
                        return {
                            "sql": exact_matches,
                            "documentation": [],
                            "context": {"glossary": [], "tables": [], "query_mapping": []},
                        }
                    return exact_matches
                else:
                    logger.info(
                        f"[get_similar_question_sql] No exact SQL match for '{question.strip()}' - proceeding to similarity search",
                        extra={"admin": True},
                    )

            # === STEP 2: NORMALIZE + TOKENIZE ===
            normalized_question = self.normalize_keyword(question)
            tokens = re.findall(r"\w+", normalized_question)
            token_set = set(tokens)
            bigrams = {" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)}

            collection = (
                self.chroma_client.get_or_create_collection(
                    name=workspace, embedding_function=self.embedding_function
                )
                if workspace
                else self.sql_collection
            )

            # strip internal flags
            query_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k not in ["allow_llm_to_see_data", "followup_sql"]
            }

            # === STEP 3: GLOSSARY MATCHING ===
            matched_glossary_keys, matched_keywords = [], []
            for key, entry in glossary.items():
                for term in entry.get("terms", []):
                    nt = self.normalize_keyword(term)
                    if (
                        nt in normalized_question
                        or nt in token_set
                        or nt in bigrams
                        or fuzz.partial_ratio(nt, normalized_question) > 80
                    ):
                        matched_glossary_keys.append(key)
                        matched_keywords.append(term)
                        break  # move to next glossary key

            # === STEP 4: TABLE RELEVANCE MATCH (keyword + semantic) ===
            matched_tables, table_scores = [], {}

            # Resolve which physical DB each matched table belongs to. table_relevance
            # entries carry an optional "db" tag (see loader above) — None means the
            # table lives on the primary DB. table_scores is keyed by (table, db) so
            # a same-named table on each DB never collides.
            primary_db_alias = getattr(self, "primary_db_alias", None) or "PRIMARY"
            secondary_db_alias = getattr(self, "secondary_db_alias", None)

            # Precompute embedding for question only once
            try:
                q_vec = self.embedding_function.embed_query(question)
            except Exception:
                q_vec = None

            def _normalize_token(t: str) -> str:
                t = self.normalize_keyword(t)
                if t.endswith("s"):
                    return t[:-1]
                return t

            for kw_tuple, table_entry in table_relevance.items():
                table = table_entry["table"]
                resolved_db = table_entry.get("db") or primary_db_alias
                # kw_tuple is already a tuple/list of cleaned keywords from your loader
                if isinstance(kw_tuple, str):
                    # safety fallback if something slipped through
                    try:
                        kws = ast.literal_eval(kw_tuple)
                        if not isinstance(kws, (list, tuple)):
                            kws = [kws]
                    except Exception:
                        kws = [kw_tuple]
                else:
                    kws = list(kw_tuple)

                rule_score = 0.0
                kw_count = max(len(kws), 1)

                for kw in kws:
                    norm_kw = self.normalize_keyword(kw)
                    if not norm_kw:
                        continue

                    # ----------------------------------------------------
                    # 1) Direct phrase match = strongest
                    # ----------------------------------------------------
                    if norm_kw in normalized_question:
                        rule_score += 6
                        continue

                    # ----------------------------------------------------
                    # 2) Token-level match (plural normalized)
                    # ----------------------------------------------------
                    kw_tokens = [t for t in norm_kw.split() if len(t) > 2]
                    token_hits = 0

                    for t in kw_tokens:
                        base = _normalize_token(t)
                        if any(_normalize_token(qt) == base for qt in token_set):
                            token_hits += 1

                    if token_hits > 1:
                        rule_score += 4      # multi-token match
                    elif token_hits == 1:
                        rule_score += 2      # single token hit

                    # ----------------------------------------------------
                    # 3) Fuzzy match for full phrase
                    # ----------------------------------------------------
                    fz = fuzz.partial_ratio(norm_kw, normalized_question)
                    if fz > 85:
                        rule_score += 4
                    elif fz > 70:
                        rule_score += 2

                # --------------------------------------------------------
                # 4) Semantic similarity weight (no domain special boost)
                # --------------------------------------------------------
                semantic_score = 0.0
                if q_vec:
                    candidate_kws = []
                    for kw in kws:
                        norm_kw = self.normalize_keyword(kw)
                        if fuzz.partial_ratio(norm_kw, normalized_question) > 60:
                            candidate_kws.append(norm_kw)

                    if not candidate_kws:
                        candidate_kws = [
                            self.normalize_keyword(k) for k in kws[:10] if k
                        ]

                    if candidate_kws:
                        try:
                            kw_vec = self.embedding_function.embed_query(
                                " ".join(candidate_kws)
                            )
                            dot = sum(a * b for a, b in zip(q_vec, kw_vec))
                            norm_q = sum(a * a for a in q_vec) ** 0.5
                            norm_kwv = sum(a * a for a in kw_vec) ** 0.5
                            semantic_score = dot / (norm_q * norm_kwv + 1e-9)
                        except Exception:
                            semantic_score = 0.0

                # --------------------------------------------------------
                # 5) Normalize by keyword group size
                # --------------------------------------------------------
                normalized_rule = rule_score / kw_count
                final_score = (0.7 * normalized_rule) + (0.3 * semantic_score)

                if final_score > 0:
                    score_key = (table, resolved_db)
                    table_scores[score_key] = table_scores.get(score_key, 0.0) + final_score

            # ------------------------------------------------------------
            # TOP 5 tables by score
            # ------------------------------------------------------------
            # matched_tables stays a flat list of table-name strings (unchanged
            # contract for all existing downstream consumers). matched_table_dbs
            # carries the db each one resolved to, used below to detect whether
            # this question needs a cross-DB (linked-server) join.
            if table_scores:
                top_entries = sorted(
                    table_scores.items(), key=lambda x: x[1], reverse=True
                )[:5]
                matched_tables = [key[0] for key, _ in top_entries]
                matched_table_dbs = {key[0]: key[1] for key, _ in top_entries}
            else:
                matched_tables = []
                matched_table_dbs = {}

            dbs_present = set(matched_table_dbs.values())
            cross_db = bool(secondary_db_alias) and secondary_db_alias in dbs_present and len(dbs_present) > 1

            # === STEP 5: QUERY MAPPING MATCH ===
            matched_query_mapping_keys = []
            for key, mapping in query_mapping.items():
                hit = False
                if isinstance(mapping, dict):
                    table_name = mapping.get("table")
                    if table_name and (
                        self.normalize_keyword(table_name) in normalized_question
                        or self.normalize_keyword(table_name) in token_set
                        or self.normalize_keyword(table_name) in bigrams
                    ):
                        hit = True
                    for col in mapping.get("columns", []):
                        if (
                            self.normalize_keyword(col) in normalized_question
                            or self.normalize_keyword(col) in token_set
                        ):
                            hit = True
                            break
                if hit or (
                    self.normalize_keyword(key) in normalized_question
                    or self.normalize_keyword(key) in token_set
                ):
                    matched_query_mapping_keys.append(key)
                    # Fold this mapping's table into the same (table, db) tracking
                    # used for table_relevance, so a query_mapping-only hit on a
                    # secondary-DB table still triggers cross_db detection.
                    if isinstance(mapping, dict) and mapping.get("table"):
                        mt = mapping["table"]
                        matched_table_dbs.setdefault(mt, mapping.get("db") or primary_db_alias)

            dbs_present = set(matched_table_dbs.values())
            cross_db = bool(secondary_db_alias) and secondary_db_alias in dbs_present and len(dbs_present) > 1

            logger.info(
                f"[get_similar_question_sql] Context matches -> "
                f"Glossary={matched_glossary_keys or 'None'} | "
                f"Tables={matched_tables or 'None'} | "
                f"QueryMapping={matched_query_mapping_keys or 'None'}",
                extra={"admin": True},
            )

            # === STEP 6: BUILD ENRICHED QUERY TEXT ===
            query_tables = set(matched_tables)
            for k in matched_glossary_keys + matched_query_mapping_keys:
                mapping = query_mapping.get(k, {})
                if isinstance(mapping, dict):
                    tname = mapping.get("table")
                    if tname:
                        query_tables.add(tname)

            # duplicate glossary terms to give them more weight in embedding
            query_text = f"{question} {' '.join(query_tables)} {' '.join(matched_keywords * 2)}".strip()

            # === STEP 7: RUN BOTH SQL & DOC RETRIEVAL ASYNC ===
            # Push a native Chroma `where` filter down into the documentation vector
            # search, but ONLY when every matched table resolved exclusively to the
            # secondary DB. Documentation trained before the "db" metadata field
            # existed has no "db" key at all, so a where={"db": primary_alias} filter
            # would wrongly exclude it — that case (and the cross_db / no-match case)
            # is left unfiltered and still handled by the Python-side filtering below.
            doc_query_kwargs = dict(query_kwargs)
            if dbs_present == {secondary_db_alias} and secondary_db_alias:
                doc_query_kwargs["where"] = {"db": secondary_db_alias}

            async def async_retrieve():
                sql_task = asyncio.to_thread(
                    self._submit_to_pool,
                    self._async_query_collection,
                    collection,
                    [query_text],
                    self.n_results_sql,
                    **query_kwargs,
                )
                doc_task = asyncio.to_thread(
                    self._submit_to_pool,
                    self._async_query_collection,
                    collection,
                    [query_text],
                    self.n_results_documentation,
                    **doc_query_kwargs,
                )
                return await asyncio.gather(sql_task, doc_task)

            sql_results, doc_results = [], []
            try:
                sql_raw, doc_raw = asyncio.run(async_retrieve())
                sql_extracted = ChromaDB_VectorStore._extract_documents(sql_raw)
                doc_extracted = ChromaDB_VectorStore._extract_documents(doc_raw)
                sql_results = [
                    r
                    for r in sql_extracted
                    if isinstance(r, dict) and "question" in r and r.get("sql")
                ]
                doc_results = [
                    r
                    for r in doc_extracted
                    if isinstance(r, dict) and r.get("type") == "documentation"
                ]
            except Exception as e:
                logger.error(
                    f"[get_similar_question_sql] Async embedding retrieval failed: {e}",
                    extra={"admin": True},
                )

            # === STEP 8: ENFORCE TABLE-BASED DOC SELECTION ===

            def extract_table_name(doc: dict) -> str | None:
                """
                Robust table name extractor.
                Works even if:
                - documentation does NOT start with "our definition of"
                - table name is not in quotes
                - pattern changes
                - markdown or formatting is different
                """
                import re as _re

                # Prefer the "table" field set by add_documentation (native Chroma
                # metadata, or its JSON-embedded copy for older entries) — the regex
                # scan below is a fallback for documentation trained before that field
                # existed.
                doc_table = doc.get("table")
                if doc_table:
                    return doc_table

                try:
                    content = (doc.get("content") or "").lower()

                    # 1. Try: our definition of 't_table_name'
                    match = _re.search(
                        r"our definition of ['\"](t_[a-z0-9_]+)['\"]", content
                    )
                    if match:
                        return match.group(1)

                    # 2. Try: any 't_table_name' in quotes
                    match = _re.search(r"['\"](t_[a-z0-9_]+)['\"]", content)
                    if match:
                        return match.group(1)

                    # 3. Try: first t_table_name appearing anywhere
                    match = _re.search(r"\b(t_[a-z0-9_]+)\b", content)
                    if match:
                        return match.group(1)

                except Exception:
                    return None

                return None

            def fetch_doc_for_table(table_name: str):
                """
                Backfill documentation for a specific table name
                by directly querying the collection.
                """
                try:
                    results = collection.query(
                        query_texts=[table_name],
                        n_results=5,
                    )
                    extracted = ChromaDB_VectorStore._extract_documents(results)
                    for d in extracted:
                        if d.get("type") == "documentation":
                            content = (d.get("content") or "").lower()
                            if table_name.lower() in content:
                                return d
                except Exception:
                    return None
                return None

            # If we have matched tables, filter docs to only those tables
            if matched_tables:
                matched_lower = [t.lower() for t in matched_tables]
                # Lowercased (table -> db) so a same-named table on the other DB
                # doesn't pick up this DB's documentation in dual-DB workspaces.
                matched_table_dbs_lower = {t.lower(): db for t, db in matched_table_dbs.items()}
                filtered_docs = []

                # Keep only docs for matched top-5 tables (and, when the table exists
                # on both DBs, only the doc tagged for the DB it actually resolved to)
                for d in doc_results:
                    tname = extract_table_name(d)
                    if not tname or tname not in matched_lower:
                        continue
                    doc_db = d.get("db") or primary_db_alias
                    expected_db = matched_table_dbs_lower.get(tname, primary_db_alias)
                    if doc_db == expected_db:
                        filtered_docs.append(d)

                # Identify which tables are missing documentation
                existing_tables = set(
                    extract_table_name(d)
                    for d in filtered_docs
                    if extract_table_name(d)
                )

                missing_tables = [
                    t for t in matched_tables if t.lower() not in existing_tables
                ]

                # Backfill missing documentation
                for t in missing_tables:
                    back_doc = fetch_doc_for_table(t)
                    if back_doc:
                        filtered_docs.append(back_doc)

                # FINAL: Limit to 5 docs for the LLM prompt
                doc_results = filtered_docs[:5]
            else:
                # No matched_tables: just cap what we have
                doc_results = doc_results[:5]

            # === NEW LOGGING: WHICH TABLE DOCS ARE SENT ===
            try:
                final_doc_tables = []
                for d in doc_results:
                    tname = extract_table_name(d)
                    if tname:
                        final_doc_tables.append(tname)
                logger.info(
                    f"[get_similar_question_sql] Documentation sent to LLM -> {final_doc_tables or 'None'}",
                    extra={"admin": True},
                )
            except Exception as e:
                logger.warning(
                    f"[get_similar_question_sql] Failed to extract doc table names for logging: {e}"
                )

            # === FINAL SUMMARY ===
            logger.info(
                f"[get_similar_question_sql] Final combined results -> "
                f"SQL={len(sql_results)} | DOC={len(doc_results)} | "
                f"Glossary={len(matched_glossary_keys)}",
                extra={"admin": True},
            )

            # === RETURN ENRICHED CONTEXT (DOCS CAPPED TO 5) ===
            return {
                "sql": sql_results,
                "documentation": doc_results[:5],
                "context": {
                    "glossary": matched_glossary_keys,
                    "tables": matched_tables,
                    "query_mapping": matched_query_mapping_keys,
                    # Dual-DB info: which DB each matched table resolved to, whether
                    # this question needs tables from both (cross_db), and the two
                    # aliases so get_sql_prompt can qualify only the secondary DB's
                    # tables with linked-server three-part names.
                    "table_dbs": matched_table_dbs,
                    "cross_db": cross_db,
                    "primary_db_alias": primary_db_alias,
                    "secondary_db_alias": secondary_db_alias,
                    "same_instance": getattr(self, "same_instance", False),
                },
            }

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(
                f"[get_similar_question_sql] Exception for '{question.strip()}': {e}\n{tb}",
                extra={"admin": True},
            )
            return {
                "sql": [],
                "documentation": [],
                "context": {
                    "glossary": [], "tables": [], "query_mapping": [],
                    "table_dbs": {}, "cross_db": False,
                    "primary_db_alias": getattr(self, "primary_db_alias", None) or "PRIMARY",
                    "secondary_db_alias": getattr(self, "secondary_db_alias", None),
                    "same_instance": getattr(self, "same_instance", False),
                },
            }



    def _enrich_table_documentation(self, doc_results: list, matched_tables: list, table_scores: dict,workspace: str, collection) -> list:
        """
        Enrich documentation results with table relevance-based documentation.
        Combines existing doc_results with any table-specific docs found in the workspace.
        """
        logger.info(f"[_enrich_table_documentation] BEGIN | DocResults={len(doc_results)} | MatchedTables={matched_tables}")

        added_docs = []
        missing_tables = []
        seen_hashes = set()

        try:
            # === STEP 1: Fetch all documentation for the workspace ===
            all_docs = self.fetch_all_documentation(workspace)
            logger.info(f"[_enrich_table_documentation] Retrieved {len(all_docs)} total documentation entries from workspace '{workspace}'")

            if not all_docs:
                logger.warning(f"[_enrich_table_documentation] No documentation found in workspace '{workspace}'")
                return doc_results

            # === STEP 2: Filter docs matching relevant tables ===
            for table in matched_tables:
                matched = []
                for doc in all_docs:
                    content = doc.get("content", "")
                    extracted_table = self.extract_table_from_content(content)

                    # Match normalized names
                    if extracted_table and extracted_table.lower().strip() == table.lower().strip():
                        matched.append(doc)

                if matched:
                    added_docs.extend(matched)
                    logger.info(f"[_enrich_table_documentation] ✅ Found {len(matched)} documentation entries for table '{table}'")
                else:
                    missing_tables.append(table)
                    logger.warning(f"[_enrich_table_documentation] ⚠️ No documentation found for table '{table}'")

            # === STEP 3: Merge, deduplicate, and limit ===
            merged_docs = doc_results + added_docs

            # Deduplicate by hash of content
            unique_docs = []
            for d in merged_docs:
                content = d.get("content", "")
                h = self.hash_content(content)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    unique_docs.append(d)

            # Limit to max 5
            if len(unique_docs) > 5:
                unique_docs = unique_docs[:5]

            logger.info(
                f"[_enrich_table_documentation] COMPLETE | Original={len(doc_results)} | Added={len(added_docs)} "
                f"| Missing={len(missing_tables)} | Final={len(unique_docs)}"
            )

            if missing_tables:
                logger.warning(f"[_enrich_table_documentation] Missing documentation for tables: {missing_tables}")

            return unique_docs

        except Exception as e:
            logger.error(f"[_enrich_table_documentation] Exception during enrichment: {e}", exc_info=True)
            return doc_results


        
    #workes but take time
    # def _enrich_table_documentation(self, doc_results: list, matched_tables: list, table_scores: dict,workspace: str, collection) -> list:
    #     """
    #     Enrich documentation by merging retrieved docs with relevant table docs.
    #     Uses same retrieval pipeline as documentation retrieval,
    #     but prevents recursive loops using a guard flag.
    #     """
    #     import logging
    #     logger = logging.getLogger("vanna.chromadb.chromadb_vector")

    #     logger.info(
    #         f"[_enrich_table_documentation] BEGIN | DocResults={len(doc_results)} | MatchedTables={matched_tables}",
    #         extra={"admin": True}
    #     )

    #     # === STEP 1: Extract already documented tables ===
    #     tables_from_docs = set()
    #     for d in doc_results:
    #         t = self.extract_table_from_content(d.get("content", ""))
    #         if t:
    #             tables_from_docs.add(t)

    #     # === STEP 2: Merge with matched_tables (limit 5 total) ===
    #     sorted_matched = sorted(
    #         [(t, table_scores.get(t, 0)) for t in matched_tables],
    #         key=lambda x: x[1],
    #         reverse=True,
    #     )
    #     final_tables = list(tables_from_docs)
    #     for t, _ in sorted_matched:
    #         if len(final_tables) >= 5:
    #             break
    #         if t not in final_tables:
    #             final_tables.append(t)

    #     logger.info(f"[_enrich_table_documentation] Final merged tables (≤5): {final_tables}",
    #                 extra={"admin": True})

    #     # === STEP 3: Retrieve missing docs safely ===
    #     tables_needing_docs = [t for t in final_tables if t not in tables_from_docs]
    #     added_docs, missing_docs = [], []

    #     for t in tables_needing_docs:
    #         try:
    #             logger.info(
    #                 f"[_enrich_table_documentation] Attempting unified doc retrieval for table '{t}'",
    #                 extra={"admin": True},
    #             )

    #             # ✅ Use a recursion guard
    #             if getattr(self, "_doc_enrichment_in_progress", False):
    #                 logger.debug(f"[_enrich_table_documentation] Skipping recursion for table '{t}' (guard active).",
    #                             extra={"admin": True})
    #                 continue

    #             # Activate guard flag
    #             self._doc_enrichment_in_progress = True

    #             # ✅ Unified retrieval using same logic as main documentation pipeline
    #             result = self.get_similar_question_sql(
    #                 question=f"documentation for table {t}",
    #                 workspace=workspace,
    #                 training_data_type="documentation"
    #             )

    #             # Reset guard flag after call
    #             self._doc_enrichment_in_progress = False

    #             docs = result.get("documentation", [])
    #             if docs:
    #                 for d in docs:
    #                     d["table_name"] = t
    #                 added_docs.extend(docs)
    #                 logger.info(
    #                     f"[_enrich_table_documentation] Found {len(docs)} docs for '{t}' (unified retrieval).",
    #                     extra={"admin": True},
    #                 )
    #             else:
    #                 missing_docs.append(t)
    #                 logger.warning(
    #                     f"[_enrich_table_documentation] No documentation found for '{t}' (unified retrieval).",
    #                     extra={"admin": True},
    #                 )

    #         except Exception as e:
    #             # Always reset guard to avoid getting stuck
    #             self._doc_enrichment_in_progress = False
    #             logger.error(
    #                 f"[_enrich_table_documentation] Error fetching documentation for '{t}': {e}",
    #                 extra={"admin": True},
    #             )
    #             missing_docs.append(t)

    #     # === STEP 4: Add placeholders for missing docs ===
    #     for t in missing_docs:
    #         placeholder = {
    #             "content": f"⚠️ Documentation missing for table `{t}`. "
    #                     f"This table was matched via table relevance but no documentation entry was found.",
    #             "type": "documentation",
    #             "source": "placeholder",
    #             "table_name": t
    #         }
    #         added_docs.append(placeholder)
    #         logger.warning(
    #             f"[_enrich_table_documentation] No documentation found for '{t}' — using placeholder.",
    #             extra={"admin": True},
    #         )

    #     # === STEP 5: Merge & deduplicate (limit to 5) ===
    #     combined = doc_results + added_docs
    #     seen, unique_docs = set(), []
    #     for d in combined:
    #         h = self.hash_content(d.get("content", ""))
    #         if h not in seen:
    #             unique_docs.append(d)
    #             seen.add(h)

    #     unique_docs = unique_docs[:5]

    #     # === STEP 6: Final summary ===
    #     logger.info(
    #         f"[_enrich_table_documentation] COMPLETE | Original={len(doc_results)} | Added={len(added_docs)} | "
    #         f"Missing={len(missing_docs)} | Final={len(unique_docs)}",
    #         extra={"admin": True},
    #     )

    #     if missing_docs:
    #         logger.info(f"[_enrich_table_documentation] Missing documentation: {missing_docs}",
    #                     extra={"admin": True})

    #     return unique_docs




    def _find_exact_matches_first(self, question: str, workspace: str) -> list:
        """
        Find 100% exact matches — not case-insensitive, not normalized.
        Must match character-for-character, including spaces and case.
        """
        logger.info(f"STEP 1: Searching for exact matches for: '{question}'")

        try:
            if not workspace:
                logger.warning(" Workspace not provided, skipping exact match search.")
                return []

            collection = self.chroma_client.get_or_create_collection(
                name=workspace,
                embedding_function=self.embedding_function,
            )

            all_records = collection.get()
            total_records = len(all_records.get("ids", []))
            logger.info(f" Scanning {total_records} records for exact matches...")

            exact_matches = []

            # Scope guard: a query may only touch the database(s)/linked server(s)
            # actually saved in this workspace's config. Nothing else, ever, even if
            # some other database happens to exist and resolve successfully on the
            # same server. Trained SQL is frozen literal text and doesn't
            # automatically track config changes the way fresh LLM generation does,
            # so re-validate it here every time via the same check generation uses
            # (validate_db_scope, defined on VannaBase) rather than trusting it was
            # still correct after it was saved.

            for i, document in enumerate(all_records.get("documents", [])):
                try:
                    if not document:
                        continue

                    if document.strip().startswith("{"):
                        parsed_data = json.loads(document)

                        if "question" in parsed_data and "sql" in parsed_data:
                            stored_question = parsed_data["question"]

                            #  PURE CHARACTER-FOR-CHARACTER MATCH
                            if stored_question == question:
                                sql_text = parsed_data.get("sql", "") or ""
                                scope_ok, scope_err = self.validate_db_scope(sql_text)
                                if not scope_ok:
                                    logger.warning(
                                        f" Skipping exact match for '{stored_question}' — {scope_err}. "
                                        f"Falling back to fresh generation."
                                    )
                                    continue
                                logger.info(f" EXACT MATCH FOUND: '{stored_question}'")
                                exact_matches.append({
                                    "type": "sql",
                                    "content": parsed_data,
                                    "domain_mappings": [],
                                    "match_score": 1.0,
                                    "match_type": "exact",
                                    "id": all_records["ids"][i]
                                })
                            else:
                                logger.debug(f" NO MATCH: '{stored_question}' != '{question}'")

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f" Error checking record {i}: {e}")
                    continue

            logger.info(f" Exact match search completed: {len(exact_matches)} matches found")
            return exact_matches

        except Exception as e:
            logger.error(f" Exact match search failed: {e}")
            return []
        

        
    def _get_table_documentation(self, table_name, workspace=None, collection=None):
        """
        Fetches documentation for a specific table from ChromaDB or cache.
        """
        try:
            query_text = f"documentation for table {table_name}"
            results = self._async_query_collection(
                collection=collection,
                query_texts=[query_text],
                n_results=1,
                where={"type": "documentation"},
            )
            extracted = ChromaDB_VectorStore._extract_documents(results)
            if extracted:
                return extracted[0].get("content")
        except Exception as e:
            logger.warning(f"[_get_table_documentation] Could not retrieve documentation for '{table_name}': {e}")
        return None




    def _extract_documents(query_results) -> list:
        """
        FIXED: Enhanced document extraction with proper None handling.
        Also merges Chroma's native metadata (type/db/table, set by add_question_sql/
        add_documentation) onto each parsed dict result when present, so callers can
        rely on real Chroma metadata rather than only the JSON-embedded copies.
        """
        if query_results is None:
            logger.warning("Query results is None, returning empty list")
            return []

        if "documents" not in query_results:
            logger.warning("No 'documents' key in query results, returning empty list")
            return []

        documents = query_results["documents"]

        if documents is None:
            logger.warning("Documents is None in query results, returning empty list")
            return []

        if len(documents) == 0:
            logger.info("No documents found in query results")
            return []

        raw_metadatas = query_results.get("metadatas")

        def _merge_metadata(parsed_list, doc_list):
            if not raw_metadatas:
                return parsed_list
            # metadatas mirrors documents' shape: nested ([[...]]) for query(), flat for get()
            flat_meta = raw_metadatas[0] if (len(raw_metadatas) == 1 and isinstance(raw_metadatas[0], list)) else raw_metadatas
            if not flat_meta or len(flat_meta) != len(doc_list):
                return parsed_list
            for item, meta in zip(parsed_list, flat_meta):
                if isinstance(item, dict) and isinstance(meta, dict):
                    for k in ("type", "db", "table"):
                        if meta.get(k) not in (None, ""):
                            item[k] = meta[k]
            return parsed_list

        # Handle nested list structure
        if len(documents) == 1 and isinstance(documents[0], list):
            try:
                # Try to parse JSON documents
                parsed_docs = []
                for doc in documents[0]:
                    if isinstance(doc, str) and doc.strip().startswith('{'):
                        try:
                            parsed_docs.append(json.loads(doc))
                        except json.JSONDecodeError:
                            parsed_docs.append(doc)  # Keep as string if not JSON
                    else:
                        parsed_docs.append(doc)
                return _merge_metadata(parsed_docs, documents[0])
            except Exception as e:
                logger.warning(f"Error parsing nested documents: {e}, returning raw documents")
                return documents[0]

        return documents
    

    

    #commented on 23/10/2-25

    # def get_similar_question_sql(self, question: str, workspace: str = None, training_data_type: str = None, **kwargs) -> list:
    

    #     thread_name = threading.current_thread().name
    #     logger.info(f"get_similar_question_sql called from {thread_name}: question='{question[:50]}...', type='{training_data_type}', workspace='{workspace}'")  # NEW

    #     # Normalize query text
    #     normalized_question = self.normalize_keyword(question)

    #     # Determine which collection to query
    #     if workspace:
    #         collection = self.chroma_client.get_or_create_collection(
    #             name=workspace,
    #             embedding_function=self.embedding_function,
    #         )
    #     else:
    #         collection = self.sql_collection

    #     # Filter out 'allow_llm_to_see_data' from kwargs
    #     query_kwargs = {k: v for k, v in kwargs.items() if k not in ["allow_llm_to_see_data", "followup_sql"]}

    #     # Load glossary and query mapping (table_relevance already loaded globally)
    #     # CONFIG_DIR = getattr(self, 'CONFIG_DIR', '.')  # Assume CONFIG_DIR is set globally or as an attribute
    #     # with open(os.path.join(CONFIG_DIR, "glossary.json"), "r") as f:
    #     #     glossary = json.load(f)
    #     # with open(os.path.join(CONFIG_DIR, "query_mapping.json"), "r") as f:
    #     #     query_mapping = json.load(f)

    #     # # Assume table_relevance is already loaded as {tuple(keywords): table}
    #     # table_relevance = getattr(self, 'table_relevance', {})  # Access preprocessed table_relevance

    #     # === Step 1: Match glossary terms for intent ===
    #     matched_glossary_keys = []
    #     matched_keywords = []

    #     for key, entry in glossary.items():
    #         terms = entry["terms"]
    #         for term in terms:
    #             normalized_term = self.normalize_keyword(term)
    #             if normalized_term in normalized_question or fuzz.partial_ratio(normalized_term, normalized_question) > 80:
    #                 matched_glossary_keys.append(key)
    #                 if term not in matched_keywords:
    #                     matched_keywords.append(term)
    #                 break  # Move to next key after first match

    #     # === Step 2: Enhance with table_relevance for table matching ===
    #     table_scores = {}
    #     for keywords_tuple, table in table_relevance.items():
    #         score = 0
    #         for keyword in keywords_tuple:  # Use the tuple of keywords directly
    #             normalized_keyword = self.normalize_keyword(keyword)
    #             if normalized_keyword in normalized_question:
    #                 score += 1  # Basic scoring; can add IDF later
    #                 if keyword not in matched_keywords:
    #                     matched_keywords.append(keyword)
    #         if score > 0:
    #             table_scores[table] = score

    #     # Select top tables and align with glossary if possible
    #     matched_tables = [t[0] for t in sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[:3]]
    #     if not matched_glossary_keys and matched_tables:
    #         for table in matched_tables:
    #             for key, mapping in query_mapping.items():
    #                 if mapping.get("table") == table:
    #                     matched_glossary_keys.append(key)
    #                     break

    #     # if not matched_glossary_keys:
    #     #     logging.info(f"No glossary or table relevance matched for question: {question}")
    #     #     # Return empty if no matches, to avoid proceeding with invalid data
    #     #     return []

    #     if not matched_glossary_keys:
    #         logging.info(f"No glossary or table relevance matched for question: {question}. Falling back to direct ChromaDB similarity search.")
    #         try:
    #             query_results = self._submit_to_pool(
    #                 self._async_query_collection, collection, [question], self.n_results_sql, **query_kwargs
    #             )

    #             # Safely extract documents
    #             results = ChromaDB_VectorStore._extract_documents(query_results)

    #             if not results or not isinstance(results, list):
    #                 logging.warning(f"Fallback query returned no valid documents for workspace '{workspace}'")
    #                 return []

    #             valid_results = []
    #             for r in results:
    #                 if not isinstance(r, dict):
    #                     continue
    #                 if "question" in r and "sql" in r:
    #                     valid_results.append({"type": "sql", "content": r, "domain_mappings": []})
    #                 else:
    #                     logging.debug(f"Skipping malformed fallback result: {r}")

    #             if not valid_results:
    #                 logging.warning(f"Fallback ChromaDB query for workspace '{workspace}' returned empty or invalid results.")
    #                 return []

    #             logging.info(f"Fallback ChromaDB query for workspace '{workspace}' returned {len(valid_results)} valid result(s).")
    #             return valid_results

    #         except Exception as e:
    #             logging.error(f"Fallback ChromaDB query failed safely: {e}", exc_info=True)
    #             return []


    #     # === Step 3: Build enriched query context ===
    #     # query_tables = set([query_mapping[k].get("table", "") for k in matched_glossary_keys] + matched_tables)
    #     query_tables = set([
    #         query_mapping.get(k, {}).get("table", "") 
    #         for k in matched_glossary_keys 
    #         if k in query_mapping
    #     ] + matched_tables)

    #     query_text = f"{question} {' '.join(query_tables)} {' '.join(matched_keywords * 2)}"

    #     # === Step 4: Documentation or SQL processing ===
    #     combined_results = []

    #     if training_data_type == "documentation":
    #         try:
    #             # documentation_results = ChromaDB_VectorStore._extract_documents(
    #             #     collection.query(
    #             #         query_texts=[query_text],
    #             #         n_results=self.n_results_documentation,
    #             #         **query_kwargs
    #             #     )
    #             # )

    #             logger.debug(f"Submitting documentation query to pool from {thread_name}")  # NEW
    #             query_results = self._submit_to_pool(
    #                 self._async_query_collection, collection, [query_text], self.n_results_documentation, **query_kwargs
    #             )
    #             documentation_results = ChromaDB_VectorStore._extract_documents(query_results)
    #         except Exception as e:
    #             logging.error(f"ChromaDB similarity search failed: {e}")
    #             documentation_results = []

    #         documentation_results = [r for r in documentation_results if r.get("type") == "documentation"]

    #         try:
    #             filtered_raw_docs = self.fetch_all_documentation(workspace)
    #             keyword_based_results = []
    #             for doc in filtered_raw_docs:
    #                 table_name = self.extract_table_from_content(doc.get("content", ""))
    #                 if table_name:
    #                     if table_name in query_tables or any(table_name == query_mapping.get(k, {}).get("table") for k in matched_glossary_keys):
    #                         keyword_based_results.append(doc)
    #                         logging.info(f"Matched table '{table_name}' in document: {doc.get('content')[:100]}...")
    #                 else:
    #                     logging.debug(f"No table extracted from document: {doc.get('content')[:100]}...")
    #                     keyword_based_results.append(doc)  # Include doc even without table match
    #         except Exception as e:
    #             logging.error(f"Failed to fetch all documentation: {e}")
    #             keyword_based_results = []

    #         combined_docs = keyword_based_results + documentation_results
    #         seen_hashes = set()
    #         unique_results = []
    #         for doc in combined_docs:
    #             content_hash = self.hash_content(doc.get("content", ""))
    #             if content_hash not in seen_hashes:
    #                 unique_results.append(doc)
    #                 seen_hashes.add(content_hash)

    #         # Flexible sorting: Handle cases where no table is extracted
    #         # Extract table_name in the lambda scope (use a default variable)
    #         sorted_results = sorted(
    #             unique_results,
    #             key=lambda x: x.get("distance", float("inf")) * (0.5 if (table_name := self.extract_table_from_content(x.get("content", ""))) and table_name in query_tables else 1.0)
    #         )

    #         top_3_results = sorted_results[:3]

    #         if top_3_results:
    #             combined_results.append({
    #                 "type": "documentation",
    #                 "content": top_3_results,
    #                 "domain_mappings": [{k: glossary[k]} for k in matched_glossary_keys if k in glossary]
    #             })

    #     elif training_data_type == "sql":
    #         try:
    #             # results = ChromaDB_VectorStore._extract_documents(
    #             #     collection.query(
    #             #         query_texts=[query_text],
    #             #         n_results=self.n_results_sql,
    #             #         **query_kwargs
    #             #     )
    #             # )

    #             logger.debug(f"Submitting SQL query to pool from {thread_name}")  # NEW
    #             query_results = self._submit_to_pool(
    #                 self._async_query_collection, collection, [query_text], self.n_results_sql, **query_kwargs
    #             )
    #             results = ChromaDB_VectorStore._extract_documents(query_results)
    #         except Exception as e:
    #             logging.error(f"Failed to query ChromaDB for SQL questions: {e}")
    #             results = []

    #         filtered_results = [r for r in results if "question" in r and "sql" in r]

    #         for result in filtered_results:
    #             # Check for exact match and skip enhancement if found
    #             if result.get("question", "").strip().lower() == question.strip().lower():
    #                 logging.info(f"Exact trained match found for question; skipping enhancement")
    #                 combined_results.append({
    #                     "type": "sql",
    #                     "content": result,
    #                     "domain_mappings": []
    #                 })
    #                 continue  # Skip to next result

    #             enhanced = False
    #             for key in matched_glossary_keys:
    #                 mapping = query_mapping.get(key)  # Safe get
    #                 if mapping and isinstance(mapping, dict) and "table" in mapping:
    #                     table = mapping["table"]
    #                     if table in query_tables:
    #                         try:
    #                             result["suggested_query"] = self.generate_sql_from_mapping(mapping)
    #                             enhanced = True
    #                             logging.info(f"Enhanced SQL result with mapping for key '{key}' and table '{table}'")
    #                             break
    #                         except Exception as e:
    #                             logging.error(f"Failed to generate suggested query for key '{key}': {e}")
    #                 else:
    #                     logging.warning(f"Skipping enhancement for glossary key '{key}': No valid mapping or 'table' field in query_mapping.json")
                
    #             if not enhanced:
    #                 logging.info(f"No valid query mapping found for result; using raw result")

    #             combined_results.append({
    #                 "type": "sql",
    #                 "content": result,
    #                 "domain_mappings": []
    #             })

    #     else:
    #         logging.info("Invalid training_data_type; returning empty list")
    #         return []

    #     logging.info(f"Returning combined results: {combined_results}")
    #     return combined_results





    # Helper method to generate SQL (placeholder)
    def generate_sql_from_mapping(self, mapping):
        columns = ", ".join(mapping["columns"])
        conditions = mapping.get("conditions", {})
        where_clause = f" WHERE {conditions.get('WHERE', '1=1')}"
        group_by = f" GROUP BY {conditions.get('group_by', '')}" if conditions.get("group_by") else ""
        order_by = f" ORDER BY {conditions.get('order_by', '')}" if conditions.get("order_by") else ""
        agg_clause = f" {conditions.get('count', '')}, {conditions.get('sum', '')}" if conditions.get("count") or conditions.get("sum") else ""
        return f"SELECT {columns} {agg_clause} FROM {mapping['table']} {where_clause} {group_by} {order_by}"

    # Placeholder for extract_table_from_content (to be implemented or fixed)
    # def extract_table_from_content(self, content):
    #     # This method should return a string (e.g., "t_zone") or None if no table is found
    #     import re
    #     match = re.search(r"`t_[a-zA-Z_]+`", content)  # Example regex to match table names like `t_zone`
    #     return match.group(0).replace("`", "") if match else None



    def get_table_documentation(self, table_names, **kwargs) -> dict:
        """
        Retrieve documentation entries for one or more tables from the specified workspace.

        Args:
            table_names (str or list): A single table name (str), a comma-separated string of names, or list of table names.
            **kwargs: Additional keyword arguments, including 'workspace' (required).

        Returns:
            dict: A dictionary mapping each table name to a list of matched documentation entries.
        """
        workspace = kwargs.get("workspace")
        if not table_names or not workspace:
            logging.error("Table name(s) and workspace are required")
            return {}

        # Normalize table_names into a list of clean individual table names
        if isinstance(table_names, str):
            table_names = [name.strip() for name in table_names.split(",") if name.strip()]

        try:
            all_docs = self.fetch_all_documentation(workspace)
            if not all_docs:
                logging.info(f"No documentation found in workspace: {workspace}")
                return {}

            # Create a map of normalized names to original names for comparison
            normalized_targets = {self.normalize_keyword(name): name for name in table_names}
            table_doc_map = {name: [] for name in table_names}

            # Loop through all docs and match by normalized table name
            for doc in all_docs:
                content = doc.get("content", "")
                extracted_table = self.extract_table_from_content(content)
                if extracted_table:
                    normalized_extracted = self.normalize_keyword(extracted_table)
                    if normalized_extracted in normalized_targets:
                        original_name = normalized_targets[normalized_extracted]
                        table_doc_map[original_name].append(doc)
                        logging.info(f"Matched table '{extracted_table}' in document: {content[:100]}...")

            # Remove tables with no matches
            result = {k: v for k, v in table_doc_map.items() if v}
            if not result:
                logging.info(f"No documentation matched any of the requested tables in workspace: {workspace}")
            else:
                logging.info(f"Documentation fetched for tables: {list(result.keys())}")

            return result

        except Exception as e:
            logging.error(f"Failed to fetch documentation for tables in workspace {workspace}: {e}")
            return {}




    def get_related_documentation(self, question: str, workspace: str = None, training_data_type: str = "documentation", **kwargs) -> list:
        # Define table relevance as a dictionary with lists of keywords as keys
        table_relevance = {
            ('order detail', 'order line', 'item number', 'order number', 'quantity shipped', 'backorder qty', 'unit of measure', 'warehouse id', 'fulfillment details', 'hazardous material', 'lot number', 'planned qty', 'order processing', 'shipping qty', 'item-specific order', 'customer order line', 'order allocation', 'wave planning', 'UOM EA', 'order items', 'order execution', 'picked items', 'order tracking', 'detailed order', 'BOL reference', 'client-specific order', 'item master join', 'order qty', 'shipped items', 'order fulfillment'): "t_order_detail",
            (
                'stored item', 'inventory tracking', 'item number', 'location id', 'warehouse id', 
                'actual quantity', 'status available', 'status hold', 'status unavailable', 
                'unavailable quantity', 'stock status', 'inventory quantity', 'lot number', 
                'stored attribute', 'partial location', 'ready to pick', 'item storage', 
                'stock levels', 'inventory condition', 'out of stock', 'high in stock', 'need refill', 
                'stock maintained', 'handling unit id', 'location-based stock', 'inventory audit', 
                'fork location items', 'real-time stock', 'warehouse stock', 'item availability', 
                'stock update', 'pickable items', 'status', 'fifo date', 'expiration date', 
                'reserved for', 'inspection code', 'serial number', 'type', 'put away location', 
                'shipment number', 'hu id', 'license plate', 'storage type'
            ) : "t_stored_item",

            (
                'item master', 'item number', 'warehouse id', 'item description', 'unit of measure',
                'inventory type', 'shelf life', 'alternate item', 'upc code', 'class id', 'pick put profile',
                'cross-dock profile', 'attribute collection', 'client code', 'serial control', 'lot control',
                'item pricing', 'hazardous material', 'country of manufacture', 'harmonized tariff',
                'inventory management', 'item attributes', 'warehouse items', 'freight class', 'reorder point',
                'reorder quantity', 'cycle count date', 'pick location', 'inventory category', 'inventory class',
                'audit requirement', 'expiration date control', 'client item number', 'international shipping',
                'TMS integration', '3PL support', 'dynamic attributes', 'commodity code', 'NAFTA compliance',
                'comment flag', 'missing UPC', 'missing description', 'forward pick', 'NAFTA producer',
                'NAFTA net cost', 'MSDS URL', 'auto adjustment', 'inbound lot tracking', 'outbound serial tracking',
                'cycle count overdue', 'item count', 'inventory grouping', 'non-hazardous items', 'price availability',
                'country import', 'freight class assignment','item weight', 'unit weight', 'item volume', 'space', 'item size', 'length', 'width', 'height', 'item style', 'item color', 'standard handling quantity', 'std_hand_qty', 'item details'
            ): 't_item_master',

            ('customer order', 'order number', 'shipping info', 'carrier name', 'freight terms', 'backorder status', 'order status', 'warehouse id', 'ship to city', 'Toronto orders', 'order weight', 'order qty', 'rush order', 'packing process', 'order tracking', 'delivery scheduling', 'BOL number', 'customer name', 'Costco orders', 'order creation date', '2021-2022 orders', 'order priority', 'shipping manifest', 'order fulfillment', 'pick-and-pack', 'invoice generation', 'order urgency', 'wave execution', 'appointment scheduling', 'client code'): "t_order",

            ('handling unit', 'license plate', 'hu id', 'location id', 'warehouse id', 'unit status', 'container type', 'load id', 'parent hu id', 'staged order', 'received inventory', 'DATEXLP location', 'pallet management', 'shipment unit', 'inventory grouping', 'movement tracking', 'consolidated items', 'RFID tagging', 'barcode unit', 'load assignment', 'warehouse tracking', 'nested units', 'handling status', 'container tracking', 'multi-item unit', 'shipping prep', 'receiving prep', 'PO license plate', 'CHR.1201 LP', 'unitized inventory'): "t_hu_master",

            (
                'warehouse location', 'location status', 'location type', 'warehouse id', 'zone',
                'capacity quantity', 'volume capacity', 'maintenance interval', 'cycle count frequency',
                'bulk picking', 'slotting rank', 'inventory control type', 'equipment type',
                'control tower groups', 'picking flow order', 'replenishment location',
                'location dimensions', 'aisle location', 'staging location', 'cross-dock location',
                'forward pick location', 'single item storage', 'forklift location', 'full location',
                'inactive location', 'partial location', 'empty location', 'user assignment',
                'putaway rules', 'location coordinates', 'storage device', 'license plate control',
                'cycle count classes', 'cubing rules', 'labor advantage', 'slotting advantage',
                'capacity management', 'location validation', 'equipment audit', 'last maintained date',
                'location groups', 'status constraints', 'location group assignment', 'maintenance threshold',
                'cycle count overdue', 'partial location status', 'bulk picking zone', 'door location status',
                'VAS location', 'average slot rank', 'forklift user assignment', 'maintenance due',
                'aisle status', 'slotting status', 'pickup and delivery location', 'total volume capacity',
                'location status inquiry', 'cycle count class type', 'maintenance overdue',
                'location type variety', 'slot rank ranking', 'short location id',
                'storage location', 'bin location', 'rack location', 'dock door', 'pick face',
                'reserve location', 'temperature control', 'hazard handling', 'inventory placement',
                'task routing', 'warehouse map', 'exception dashboard', 'location sequencing',
                'space optimization', 'routing failure', 'space violation', 'task execution',
                'inventory movement', 'putaway activity', 'picking activity', 'replenishment activity',
                'cycle count activity', 'audit activity', 'location-based inventory', 'zone sequencing'
            ): 't_location',

            ('work queue', 'task priority', 'work status', 'warehouse id', 'cycle count', 'directed pickup', 'task description', 'workers required', 'work type', 'completed tasks', 'task assignment', 'pick requests', 'audit request', 'task scheduling', 'workload balancing', 'task tracking', 'replenishment job', 'picking efficiency', 'task execution', 'workflow management', 'task urgency', 'worker productivity', 'real-time tasks', 'shift management', 'job dispatch', 'task optimization', 'warehouse execution', 'mobile workflow', 'priority override', 'system tasking'): "t_work_q",

            ('inbound receipt', 'receipt date', 'item number', 'po number', 'vendor code', 'qty received', 'qty damaged', 'receipt status', 'handling unit id', 'warehouse id', 'receiving process', 'damaged count', 'ASN tracking', 'GRN processing', 'quality control', 'vendor shipment', 'receipt validation', 'over-delivery', 'under-delivery', 'putaway trigger', 'supplier receipt', 'receiving audit', 'receipt confirmation', 'inventory intake', 'dock receiving', 'freight inspection', 'item acceptance', 'receipt logging', 'VND001 items', 'CHR.1201 receipt'): "t_receipt",

            ('purchase order', 'po number', 'vendor code', 'order status', 'warehouse id', 'client code', 'closed PO', 'freight terms', 'inbound order', 'procurement process', 'supplier order', 'order tracking', 'goods receipt note', 'open PO', 'closed status', 'fulfillment scheduling', 'stock replenishment', 'bulk order', 'PO validation', 'supplier performance', 'receiving plan', 'warehouse procurement', 'order lifecycle', 'TMS integration', 'residential delivery', 'vendor management', 'invoice reconciliation', 'payment scheduling', 'return order', 'transportation logistics'): "t_po_master",

            ('pick detail', 'picking task', 'order number', 'item number', 'planned qty', 'shipped status', 'warehouse id', 'pick area', 'staging location', 'pick status', 'cancelled orders', 'wave picking', 'picker assignment', 'batch processing', 'zone-based picking', 'pick confirmation', 'shortage handling', 'picking accuracy', 'pick optimization', 'pick location', 'automated picks', 'picking workflow', 'RF scanning', 'order consolidation', 'pick sequencing', 'path efficiency', 'pick completion', 'task creation', 'inventory pick', 'client code PVH'): "t_pick_detail",

            ('putaway class', 'warehouse class', 'item classification', 'storage rules', 'overflow class', 'putaway cube', 'height check', 'storage mix', 'inventory organization', 'class id', 'space optimization', 'warehouse zoning', 'item grouping', 'putaway strategy', 'capacity planning', 'storage type', 'hazardous storage', 'perishable goods', 'bulk storage', 'location assignment', 'cubing rules', 'class description', 'target capacity', 'mix group', 'warehouse configuration', 'storage hierarchy', 'item segregation', 'putaway logic'): "t_class",

            ('pick-put profile', 'picking rules', 'putaway rules', 'warehouse operations', 'override profile', 'profile id', 'hierarchical rules', 'pick-put strategy', 'operational workflow', 'special handling', 'peak season rules', 'profile description', 'task hierarchy', 'picking optimization', 'putaway optimization', 'rule override', 'warehouse efficiency', 'process customization', 'handling priority', 'inventory flow', 'rule-based picking', 'rule-based putaway', 'task customization', 'profile management', 'operational rules'): "t_pick_put_master",

            ('lookup table', 'status codes', 'localization', 'standardization', 'lookup id', 'source table', 'sequence order', 'locale support', 'lookup text', 'description field', 'lookup type', 'system reference', 'multi-language', 'status definition', 'process standardization', 'data mapping', 'reference data', 'code translation', 'warehouse terminology', 'dynamic lookup', 'configuration table', 'lookup management', 'text localization', 'system codes', 'lookup validation'): "t_lookup",

            ('warehouse', 'warehouse id', 'warehouse code', 'warehouse name', 'warehouse address', 'contact details', 'country info', 'facility management', 'logistics network', 'multi-warehouse', 'warehouse location', 'operational hub', 'warehouse directory', 'communication channels', 'web presence', 'regional warehouse', 'global operations', 'warehouse profile', 'site details', 'facility tracking', 'warehouse operations', 'location hub', 'network facility', 'warehouse 1', 'warehouse 2'): "t_whse",

            ('client', '3PL client', 'client code', 'warehouse id', 'client name', 'client address', 'contact info', 'client management', 'client operations', 'customer data', 'client tracking', 'warehouse linkage', 'shipping details', 'billing info', 'client contact', 'service provider', 'client profile', 'logistics partner', 'client communication', 'client-specific rules', 'client logistics', 'warehouse partner', 'client support', 'PVH client', 'Costco client'): "t_client"
        }
       
        # Determine the most relevant table
        relevant_table = None
        for keywords, table in table_relevance.items():
            if any(keyword in question.lower() for keyword in keywords):
                relevant_table = table
                break
       
        if not workspace or not relevant_table:
            return []

        # Use workspace-specific documentation collection
        collection_name = workspace
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

        

        # results = ChromaDB_VectorStore._extract_documents(
        #     collection.query(
        #         query_texts=[question],
        #         n_results=self.n_results_sql,
        #     )
        # )

        thread_name = threading.current_thread().name

        logger.debug(f"Submitting SQL query to pool from {thread_name}")  # NEW

        query_results = self._submit_to_pool(
            self._async_query_collection, collection, query_texts=[question], n_results=self.n_results_sql, **kwargs
        )
        results = ChromaDB_VectorStore._extract_documents(query_results)
        logging.info(f"documentation results without filter -{results}")
        if training_data_type == "documentation":
            results = [r for r in results if "content" in r]
        return results
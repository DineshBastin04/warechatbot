r"""

# Nomenclature

| Prefix | Definition | Examples |
| --- | --- | --- |
| `vn.get_` | Fetch some data | [`vn.get_related_ddl(...)`][vanna.base.base.VannaBase.get_related_ddl] |
| `vn.add_` | Adds something to the retrieval layer | [`vn.add_question_sql(...)`][vanna.base.base.VannaBase.add_question_sql] <br> [`vn.add_ddl(...)`][vanna.base.base.VannaBase.add_ddl] |
| `vn.generate_` | Generates something using AI based on the information in the model | [`vn.generate_sql(...)`][vanna.base.base.VannaBase.generate_sql] <br> [`vn.generate_explanation()`][vanna.base.base.VannaBase.generate_explanation] |
| `vn.run_` | Runs code (SQL) | [`vn.run_sql`][vanna.base.base.VannaBase.run_sql] |
| `vn.remove_` | Removes something from the retrieval layer | [`vn.remove_training_data`][vanna.base.base.VannaBase.remove_training_data] |
| `vn.connect_` | Connects to a database | [`vn.connect_to_snowflake(...)`][vanna.base.base.VannaBase.connect_to_snowflake] |
| `vn.update_` | Updates something | N/A -- unused |
| `vn.set_` | Sets something | N/A -- unused  |

# Open-Source and Extending

Vanna.AI is open-source and extensible. If you'd like to use Vanna without the servers, see an example [here](https://vanna.ai/docs/postgres-ollama-chromadb/).

The following is an example of where various functions are implemented in the codebase when using the default "local" version of Vanna. `vanna.base.VannaBase` is the base class which provides a `vanna.base.VannaBase.ask` and `vanna.base.VannaBase.train` function. Those rely on abstract methods which are implemented in the subclasses `vanna.openai_chat.OpenAI_Chat` and `vanna.chromadb_vector.ChromaDB_VectorStore`. `vanna.openai_chat.OpenAI_Chat` uses the OpenAI API to generate SQL and Plotly code. `vanna.chromadb_vector.ChromaDB_VectorStore` uses ChromaDB to store training data and generate embeddings.

If you want to use Vanna with other LLMs or databases, you can create your own subclass of `vanna.base.VannaBase` and implement the abstract methods.

```mermaid
flowchart
    subgraph VannaBase
        ask
        train
    end

    subgraph OpenAI_Chat
        get_sql_prompt
        submit_prompt
        generate_question
        generate_plotly_code
    end

    subgraph ChromaDB_VectorStore
        generate_embedding
        add_question_sql
        add_ddl
        add_documentation
        get_similar_question_sql
        get_related_ddl
        get_related_documentation
    end
```

"""
from typing import Dict, List, Optional
import json
import os
import re
import sqlite3
import traceback
from abc import ABC, abstractmethod
from typing import List, Tuple, Union
from urllib.parse import urlparse
import logging
from fuzzywuzzy import fuzz
#import spacy
import tiktoken
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import requests
import sqlparse
import string

from sqlalchemy import event  

import re
from ..exceptions import DependencyError, ImproperlyConfigured, ValidationError
from ..types import TrainingPlan, TrainingPlanItem
from ..utils import validate_config_path
# Load spaCy NER model
#nlp = spacy.load("en_core_web_sm")  

logger = logging.getLogger(__name__)
class VannaBase(ABC):
    def __init__(self, config=None):
        if config is None:
            config = {}

        self.config = config
        self.run_sql_is_set = False
        self.static_documentation = ""
        self.dialect = self.config.get("dialect", "SQL")
        self.language = self.config.get("language", None)
        self.max_tokens = self.config.get("max_tokens", 14000)

    def log(self, message: str, title: str = "Info"):
        print(f"{title}: {message}")

    def _response_language(self) -> str:
        if self.language is None:
            return ""

        return f"Respond in the {self.language} language."



    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracts key entities dynamically with broader pattern matching tailored to the dataset."""
        extracted_values: Dict[str, List[str]] = {}

        # Order number pattern: e.g., CO.224684, KL.KTT021221, PVH.052607506
        # order_number_pattern = r'\b[A-Z0-9]+\.[A-Z0-9.]+\b'
        order_number_pattern = r'\b[A-Z0-9]+\.[A-Z0-9.-]+\b'
        order_numbers = re.findall(order_number_pattern, text)
        if order_numbers:
            extracted_values["order_number"] = order_numbers

        # po_number_pattern = r'\b[A-Z0-9]+\.[A-Z0-9.]+\b'
        po_number_pattern = r'\b[A-Z0-9]+\.[A-Z0-9..]+\b'
        po_numbers = re.findall(po_number_pattern, text)
        if po_numbers:
            extracted_values["po_number"] = po_numbers

        # Warehouse ID pattern: single digits like '1', '2', '3'
        warehouse_pattern = r'\b(?:warehouse|wh_id|Warehouse)\s*(\d)\b'
        warehouses = re.findall(warehouse_pattern, text)
        if warehouses:
            extracted_values["warehouse_id"] = warehouses

        # Product categories or vendor codes (e.g., MENS, WOMENS, VND001)
        category_pattern = r'\b[A-Z0-9]{4,}\b' # Matches MENS, WOMENS, etc.
        all_categories = re.findall(category_pattern, text)
        categories = [cat for cat in all_categories if cat not in order_numbers]
        if categories:
            extracted_values["category"] = categories
       
        # Location ID pattern: e.g., AA2302, DATEXLP, ACHAN
        location_pattern = r'\b[A-Z]{2,}\d*\b'
        all_locations = re.findall(location_pattern, text)
        locations = [loc for loc in all_locations if loc not in order_numbers and loc not in categories]
        if locations:
            extracted_values["location_id"] = locations

        # City names (e.g., Toronto, Calgary)
        city_pattern = r'\b(?:to|in)\s*([A-Z][a-z]+)\b'
        cities = re.findall(city_pattern, text)
        if cities:
            extracted_values["city"] = cities
        logging.info(f"categories: {categories}")
        print("Extracted Values:", extracted_values)
        return extracted_values

    def extract_dynamic_values(self, sql: str) -> List[str]:
        """Identify all dynamic placeholders in the SQL query."""
        quoted_values = re.findall(r"'([^']+)'", sql)
        numbers = re.findall(r'\b\d+\b', sql)
        return quoted_values + [num for num in numbers if num not in quoted_values]
    
    def replace_dynamic_values(self, sql: str, dynamic_values: List[str], entities: Dict[str, List[str]]) -> str:
        """Dynamically replace placeholders with context-aware entity matching, maximizing flexibility."""
        order_numbers = entities.get("order_number", [])
        po_numbers = entities.get("po_number", [])
        warehouses = entities.get("warehouse_id", [])
        categories = entities.get("category", [])
        locations = entities.get("location_id", [])
        cities = entities.get("city", [])
        vendors = entities.get("vendor_code", [])

        used_indices = {
            "order_number": 0,
            "po_number": 0,
            "warehouse_id": 0,
            "category": 0,
            "location_id": 0,
            "city": 0,
            "vendor_code": 0
        }

        for value in dynamic_values:
            replacement = None

            # Order number replacement
            if "order_number" in sql.lower():
                if order_numbers and used_indices["order_number"] < len(order_numbers):
                    replacement = order_numbers[used_indices["order_number"]]
                    used_indices["order_number"] += 1
                else:
                    logging.warning(f"No valid order_number in entities to replace '{value}'. Entities: {entities}")
            # po number replacement
            elif "po_number" in sql.lower():
                if po_numbers and used_indices["po_number"] < len(po_numbers):
                    replacement = order_numbers[used_indices["po_number"]]
                    used_indices["po_number"] += 1
                else:
                    logging.warning(f"No valid po_number in entities to replace '{value}'. Entities: {entities}")                    

            # Warehouse ID replacement
            elif "wh_id" in sql.lower() and value.isdigit():
                if warehouses and used_indices["warehouse_id"] < len(warehouses):
                    replacement = warehouses[used_indices["warehouse_id"]]
                    used_indices["warehouse_id"] += 1
                else:
                    logging.warning(f"No warehouse_id in entities to replace '{value}'. Entities: {entities}")


            elif "vendor_code" in sql.lower():
                if vendors and used_indices["vendor_code"] < len(vendors):
                    replacement = vendors[used_indices["vendor_code"]]
                    used_indices["vendor_code"] += 1
                elif "category" in entities and used_indices["category"] < len(entities["category"]):
                    replacement = entities["category"][used_indices["category"]]
                    used_indices["category"] += 1
                else:
                    logging.warning(f"No vendor_code or category in entities to replace '{value}'. Entities: {entities}")
            # Category replacement
            elif "product_category" in sql.lower():
                if categories and used_indices["category"] < len(categories):
                    replacement = categories[used_indices["category"]]
                    used_indices["category"] += 1

            # Location ID replacement
            elif "location_id" in sql.lower():
                if locations and used_indices["location_id"] < len(locations):
                    replacement = locations[used_indices["location_id"]]
                    used_indices["location_id"] += 1

            # City replacement
            elif "ship_to_city" in sql.lower():
                if cities and used_indices["city"] < len(cities):
                    replacement = cities[used_indices["city"]].upper()
                    used_indices["city"] += 1

            if replacement:
                logging.info(f"Before replacement - Value: '{value}', Replacement: '{replacement}', SQL: '{sql}'")
                sql = sql.replace(f"'{value}'", f"'{replacement}'")
                logging.info(f"After replacing '{value}' with '{replacement}' - SQL: '{sql}'")
            else:
                logging.warning(f"No replacement found for value: '{value}' in context: {sql.lower()}. Entities: {entities}")

        return sql

    # def generate_sql(self, question: str, **kwargs) -> str:
    #     """Generates SQL dynamically using unified retrieval (SQL + Documentation)."""
    #     import re
    #     import json
    #     logger.info(f"[generate_sql] START | Question='{question}'")

    #     initial_prompt = kwargs.get("initial_prompt", "")
    #     followup_sql = kwargs.get("followup_sql")
    #     logger.info(f"[generate_sql] initial_prompt  '{initial_prompt}'")

    #     # === STEP 1: Handle follow-up 'rewritten' SQLs ===
    #     if followup_sql:
    #         followup_sql = ' '.join(question.replace('\n', ' ').replace('\r', '').split())
    #         logging.info(f"[generate_sql] Flattened followup_sql: {followup_sql}")
    #         if 'rewritten' in followup_sql:
    #             followup_sql = followup_sql.replace("'''rewritten'''", "```rewritten").replace("'''", "```")
    #             rewritten_match = re.search(r'```rewritten\s*(.*?)\s*```', followup_sql, re.DOTALL)
    #             if rewritten_match:
    #                 sql_content = rewritten_match.group(1).strip()
    #                 final_question = f"```sql\n{sql_content}\n```"
    #                 logging.info(f"[generate_sql] Extracted rewritten SQL → returning early.")
    #                 return self.extract_sql(final_question)

    #     # === STEP 2: Unified retrieval (SQL + Docs + Domain Context) ===
    #     context = self.get_similar_question_sql(question, training_data_type="all", **kwargs)
    #     question_sql_list = context.get("sql", [])
    #     doc_list = context.get("documentation", [])
    #     domain_context = context.get("context", {}) or {}
    #     glossary = domain_context.get("glossary", [])
    #     tables = domain_context.get("tables", [])
    #     query_mapping = domain_context.get("query_mapping", [])

    #     logger.info(f"Document found {doc_list}", extra={"admin": True})
    #     logger.info(f"Dataset found {question_sql_list}", extra={"admin": True})
    #     logger.info(f"[generate_sql] Unified context retrieved -> ", extra={"admin": True})
    #     logger.info(f"Number of SQL={len(question_sql_list)} | SQL={(question_sql_list)}  | Number of DOC={len(doc_list)} |  DOC={(doc_list)}  | ", extra={"admin": True})
    #     logger.info(f"Number of Glossary={len(glossary)} | Glossary={(glossary)}  | Number of Tables={len(tables)} |  Tables={(tables)}  | Number of QueryMapping={len(query_mapping)} |  QueryMapping={(query_mapping)}  | ", extra={"admin": True})
    #     logger.info(f"Number of SQL={len(question_sql_list)} | SQL={(question_sql_list)}  | Number of DOC={len(doc_list)} |  DOC={(doc_list)}  | ", extra={"document": True})
    #     logger.info(f"Number of Glossary={len(glossary)} | Glossary={(glossary)}  | Number of Tables={len(tables)} |  Tables={(tables)}  | Number of QueryMapping={len(query_mapping)} |  QueryMapping={(query_mapping)}  | ", extra={"document": True})
    #     logger.info(f"Question='{question}'", extra={"admin": True})

    #     # === STEP 3: Return only on 100% exact match ===
    #     if question_sql_list:
    #         top_match = question_sql_list[0]
    #         match_type = top_match.get("match_type", "").lower()
    #         sql_text = top_match.get("sql") or top_match.get("content", {}).get("sql")

    #         if match_type == "exact" and sql_text:
    #             logger.info("[generate_sql]  Returning SQL directly from exact dataset match.", extra={"admin": True})
    #             return self.extract_sql(f"```sql\n{sql_text}\n```")
    #         else:
    #             logger.info("[generate_sql]  Similar match found but not exact - LLM will refine.", extra={"admin": True})

    #     # === STEP 4: Fallback to LLM SQL generation ===
    #     ddl_list = self.get_related_ddl(question, **kwargs)
    #     query = f"The follow-up SQL: {followup_sql}\nPrevious question: {question}" if followup_sql else question



    #     prompt = self.get_sql_prompt(
    #         initial_prompt=initial_prompt,
    #         question=question,
    #         question_sql_list=question_sql_list,
    #         ddl_list=ddl_list,
    #         doc_list=doc_list,
    #         domain_context=domain_context,
    #         **kwargs,
    #     )

    #     self.log(title="SQL Prompt", message=prompt)
    #     logger.info(f"Final prompt {prompt}", extra={"admin": True})
    #     llm_response = self.submit_prompt(prompt, **kwargs)
    #     self.log(title="LLM Response", message=llm_response)

    #     # === STEP 6: Handle Intermediate SQL (if any) ===
    #     if 'intermediate_sql' in llm_response:
    #         if not kwargs.get("allow_llm_to_see_data", False):
    #             return "The LLM is not allowed to see database data. Enable `allow_llm_to_see_data=True`."

    #         intermediate_sql = self.extract_sql(llm_response)
    #         try:
    #             self.log(title="Running Intermediate SQL", message=intermediate_sql)
    #             df = self.run_sql(intermediate_sql)
    #             prompt = self.get_sql_prompt(
    #                 initial_prompt=initial_prompt,
    #                 question=question,
    #                 question_sql_list=question_sql_list,
    #                 ddl_list=ddl_list,
    #                 doc_list=doc_list + [f"DataFrame from {intermediate_sql}:\n{df.to_markdown()}"],
    #                 domain_context=domain_context,
    #                 **kwargs,
    #             )
    #             logger.info(f"Intermediate prompt {prompt}", extra={"admin": True})
    #             llm_response = self.submit_prompt(prompt, **kwargs)
    #         except Exception as e:
    #             return f"Error running intermediate SQL: {e}"

    #     final_sql = self.extract_sql(llm_response)
    #     logger.info(f"[generate_sql] END | SQL generated successfully for '{question}'", extra={"admin": True})
    #     return final_sql










    def generate_sql(self, question: str, **kwargs) -> tuple[str, int, int, int, str]:
        """
        Returns: (sql: str, total_tokens: int, input_tokens: int, output_tokens: int, model_name: str)
        """
        followup_sql = kwargs.get("followup_sql")

        # A. Follow-up handling
        if followup_sql:
            prev_sql = question
            new_q = followup_sql.strip()

            rewritten_match = re.search(r"'''rewritten'''\s*(.*?)\s*'''rewritten'''", new_q, re.DOTALL)
            if rewritten_match:
                new_q = rewritten_match.group(1).strip()

            question = f"{new_q}\n\nPrevious SQL:\n{prev_sql}"

        # B. Retrieval
        context = self.get_similar_question_sql(question, training_data_type="all", **kwargs)
        question_sql_list = context.get("sql", [])
        doc_list         = context.get("documentation", [])
        domain_context   = context.get("context", {}) or {}

        logger.info(f"Retrieval → SQL:{len(question_sql_list)} | DOC:{len(doc_list)}", extra={"admin": True})

        # Exact match short-circuit
        if question_sql_list:
            top = question_sql_list[0]
            if top.get("match_type", "").lower() == "exact":
                sql_text = top.get("sql") or top.get("content", {}).get("sql", "")
                if sql_text:
                    logger.info("Exact match hit → returning directly", extra={"admin": True})
                    return self.extract_sql(f"```sql\n{sql_text}\n```"), 0, 0, 0, "exact_match"

        # C. LLM generation path
        ddl_list = self.get_related_ddl(question, **kwargs)

        # ────────────────────────────────────────────────
        #  ← This is the important change →
        # ────────────────────────────────────────────────
        system_prompt = self.get_sql_prompt(
            initial_prompt=kwargs.get("initial_prompt", ""),   # ← add this if your signature requires it
            question=question,
            question_sql_list=question_sql_list,
            ddl_list=ddl_list,
            doc_list=doc_list,
            domain_context=domain_context,
            **kwargs,
        )

        # Convert string prompt → OpenAI-compatible message list
        messages = [
            self.system_message(system_prompt),
            self.user_message(question),           # or a shorter version if preferred
        ]

        self.log(title="SQL Prompt", message=system_prompt)
        llm_response_tuple = self.submit_prompt(messages, **kwargs)

        # Normalize different return shapes
        if isinstance(llm_response_tuple, tuple) and len(llm_response_tuple) == 5:
            response_text, total, inp, out, model = llm_response_tuple
        elif isinstance(llm_response_tuple, tuple) and len(llm_response_tuple) == 2:
            response_text, total = llm_response_tuple
            inp = out = 0
            model = "unknown"
        else:
            response_text = str(llm_response_tuple)
            total = inp = out = 0
            model = "unknown"

        self.log(title="LLM Response", message=response_text)

        # Optional intermediate SQL step
        if 'intermediate_sql' in response_text and kwargs.get("allow_llm_to_see_data", False):
            intermediate_sql = self.extract_sql(response_text)
            try:
                df = self.run_sql(intermediate_sql)

                # Reuse the same pattern: string → messages
                system_prompt_inter = self.get_sql_prompt(
                    initial_prompt=kwargs.get("initial_prompt", ""),
                    question=question,
                    question_sql_list=question_sql_list,
                    ddl_list=ddl_list,
                    doc_list=doc_list + [f"DataFrame from {intermediate_sql}:\n{df.to_markdown()}"],
                    domain_context=domain_context,
                    **kwargs,
                )

                messages_inter = [
                    self.system_message(system_prompt_inter),
                    self.user_message(question),
                ]

                llm_response_tuple = self.submit_prompt(messages_inter, **kwargs)

                # Re-normalize
                if isinstance(llm_response_tuple, tuple) and len(llm_response_tuple) == 5:
                    response_text, total, inp, out, model = llm_response_tuple
                elif isinstance(llm_response_tuple, tuple) and len(llm_response_tuple) == 2:
                    response_text, total = llm_response_tuple
                    inp = out = 0
                    model = "unknown"

            except Exception as e:
                logger.error(f"Intermediate SQL failed: {e}")
                response_text = f"/* Intermediate SQL failed: {e} */\n{response_text}"

        final_sql = self.extract_sql(response_text)

        # Cross-DB queries route through OPENQUERY (see get_sql_prompt) — reject before
        # execution if any OPENQUERY literal is malformed/unescaped. No-op for SQL with
        # no OPENQUERY call (the vast majority of single-DB questions).
        openquery_ok, openquery_err = self.validate_openquery_literals(final_sql)
        if not openquery_ok:
            logger.error(
                f"[generate_sql] Rejected generated SQL with malformed OPENQUERY literal: {openquery_err}",
                extra={"admin": True},
            )
            return (
                f"Insufficient data for query. (rejected: {openquery_err})",
                int(total or 0), int(inp or 0), int(out or 0), "rejected_openquery",
            )

        # Only the database(s) actually configured for this workspace may be queried —
        # reject anything else, even if it would resolve successfully on the server.
        scope_ok, scope_err = self.validate_db_scope(final_sql)
        if not scope_ok:
            logger.error(
                f"[generate_sql] Rejected generated SQL out of workspace scope: {scope_err}",
                extra={"admin": True},
            )
            return (
                f"Insufficient data for query. (rejected: {scope_err})",
                int(total or 0), int(inp or 0), int(out or 0), "rejected_out_of_scope",
            )

        return final_sql, int(total or 0), int(inp or 0), int(out or 0), model or "unknown"

    def generate_write_sql(self, question: str, workspace: str = None, **kwargs) -> Tuple[str, int, int, int, str]:
        """
        Generates a write (UPDATE/INSERT/DELETE) statement for a natural-language
        request, constrained to the workspace's write whitelist (get_write_whitelist).

        This does NOT execute the statement — callers must get explicit user
        confirmation before running it (see the /api/v0/generate_write_sql and
        /api/v0/execute_write_sql Flask routes, which re-validate independently
        rather than trusting this call's result unconditionally).

        Returns: (sql: str, total_tokens: int, input_tokens: int, output_tokens: int, model_name: str)
        """
        whitelist = self.get_write_whitelist(workspace=workspace, **kwargs)

        system_prompt = self.get_write_sql_prompt(question=question, whitelist=whitelist, workspace=workspace, **kwargs)
        messages = [
            self.system_message(system_prompt),
            self.user_message(question),
        ]

        self.log(title="Write SQL Prompt", message=system_prompt)
        llm_response_tuple = self.submit_prompt(messages, **kwargs)

        if isinstance(llm_response_tuple, tuple) and len(llm_response_tuple) == 5:
            response_text, total, inp, out, model = llm_response_tuple
        elif isinstance(llm_response_tuple, tuple) and len(llm_response_tuple) == 2:
            response_text, total = llm_response_tuple
            inp = out = 0
            model = "unknown"
        else:
            response_text = str(llm_response_tuple)
            total = inp = out = 0
            model = "unknown"

        self.log(title="Write SQL Response", message=response_text)
        final_sql = self.extract_sql(response_text)

        valid, reason = self.is_write_sql_valid(final_sql, whitelist)
        if not valid:
            logger.warning(f"[generate_write_sql] Rejected generated write SQL: {reason}", extra={"admin": True})
            return (
                f"Insufficient data for query. (rejected: {reason})",
                int(total or 0), int(inp or 0), int(out or 0), "rejected_write",
            )

        scope_ok, scope_err = self.validate_db_scope(final_sql)
        if not scope_ok:
            logger.warning(f"[generate_write_sql] Rejected write SQL out of workspace scope: {scope_err}", extra={"admin": True})
            return (
                f"Insufficient data for query. (rejected: {scope_err})",
                int(total or 0), int(inp or 0), int(out or 0), "rejected_out_of_scope",
            )

        return final_sql, int(total or 0), int(inp or 0), int(out or 0), model or "unknown"


    def extract_sql(self, llm_response: str) -> str:
        """
        Example:
        ```python
        vn.extract_sql("Here's the SQL query in a code block: ```sql\nSELECT * FROM customers\n```")
        ```

        Extracts the SQL query from the LLM response. This is useful in case the LLM response contains other information besides the SQL query.
        Override this function if your LLM responses need custom extraction logic.

        Args:
            llm_response (str): The LLM response.

        Returns:
            str: The extracted SQL query.
        """
        ddl_keywords = r"\b(CREATE|ALTER|DROP|TRUNCATE|RENAME|COMMENT)\b"

        # Extract SQL queries from markdown code blocks labeled as SQL
        sqls = re.findall(r"```sql\s+(.*?)```", llm_response, re.DOTALL | re.IGNORECASE)
        if sqls:
            sql = sqls[-1].strip()
            if re.search(ddl_keywords, sql, re.IGNORECASE):
                return "I am unable to perform any Data Definition Language (DDL) functions."
            self.log(title="Extracted SQL from labeled code block", message=sql)
            sql_single_line = " ".join(line.strip() for line in sql.splitlines() if line.strip())
            return sql_single_line

        # Extract SQL queries from generic markdown code blocks
        sqls = re.findall(r"```\s*(.*?)```", llm_response, re.DOTALL | re.IGNORECASE)
        if sqls:
            sql = sqls[-1].strip()
            if re.search(ddl_keywords, sql, re.IGNORECASE):
                return "I am unable to perform any Data Definition Language (DDL) functions."
            self.log(title="Extracted SQL from generic code block", message=sql)
            return sql
        # If the llm_response contains a CTE (with clause), extract the last sql between WITH and ;
        # sqls = re.findall(r"\bWITH\b .*?;", llm_response, re.DOTALL)
        sqls=re.findall(r"\bWITH\s+[a-zA-Z0-9_]+\s+AS\s*\(.*?\)\s*SELECT.*?;",llm_response,re.DOTALL | re.IGNORECASE,)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        # If the llm_response is not markdown formatted, extract last sql by finding select and ; in the response
        sqls = re.findall(r"SELECT.*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        # If the llm_response contains a markdown code block, with or without the sql tag, extract the last sql from it
        sqls = re.findall(r"```sql\n(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        sqls = re.findall(r"```(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        return llm_response

    def is_sql_valid(self, sql: str) -> bool:
        """
        Example:
        ```python
        vn.is_sql_valid("SELECT * FROM customers")
        ```
        Checks if the SQL query is valid. This is usually used to check if we should run the SQL query or not.
        By default it checks if the SQL query is a SELECT statement. You can override this method to enable running other types of SQL queries.

        Args:
            sql (str): The SQL query to check.

        Returns:
            bool: True if the SQL query is valid, False otherwise.
        """

        parsed = sqlparse.parse(sql)

        for statement in parsed:
            if statement.get_type() == 'SELECT':
                return True

        return False

    def validate_openquery_literals(self, sql: str) -> Tuple[bool, str]:
        """
        Cross-DB queries push filters into OPENQUERY(...) string literals (see the
        cross-DB instruction block in get_sql_prompt). The LLM writes this SQL text
        directly, so this walks every OPENQUERY call's embedded literal and confirms
        each single quote is either a properly doubled escape ('') or the literal's
        true closing quote — catching a stray/unescaped quote (e.g. echoed from the
        user's question) before it reaches the database. A no-op (returns True) for
        SQL that contains no OPENQUERY call.

        Returns:
            (True, "") if valid or no OPENQUERY present; (False, reason) otherwise.
        """
        upper_sql = sql.upper()
        idx = 0
        while True:
            start = upper_sql.find("OPENQUERY", idx)
            if start == -1:
                return True, ""

            paren = upper_sql.find("(", start)
            if paren == -1:
                return False, "OPENQUERY call missing opening parenthesis"

            comma = upper_sql.find(",", paren)
            if comma == -1:
                return False, "OPENQUERY call missing linked-server argument"

            quote_start = sql.find("'", comma)
            if quote_start == -1:
                return False, "OPENQUERY call missing query string literal"

            i = quote_start + 1
            closed = False
            while i < len(sql):
                if sql[i] == "'":
                    if i + 1 < len(sql) and sql[i + 1] == "'":
                        i += 2  # doubled escape — part of the literal, keep scanning
                        continue
                    closed = True
                    i += 1
                    break
                i += 1

            if not closed:
                return False, "OPENQUERY string literal is not properly closed or has an unescaped quote"

            j = i
            while j < len(sql) and sql[j].isspace():
                j += 1
            if j >= len(sql) or sql[j] != ")":
                return False, "OPENQUERY call missing closing parenthesis after its string literal"

            idx = j + 1

    def validate_db_scope(self, sql: str) -> Tuple[bool, str]:
        """
        Scope guard: a generated query may only reference the database(s) actually
        configured for this workspace — the primary (self.primary_db_name), and the
        secondary (self.secondary_db_name) if one is configured. Nothing else, ever,
        even if some other database happens to exist and would resolve successfully
        on the same server. Catches the LLM referencing a database it picked up from
        documentation/training noise rather than the workspace's real configuration.

        Checks both forms a cross-DB reference can take: a plain three-part name
        (same-instance topology) and an OPENQUERY(...) linked-server alias
        (separate-server topology) — a query can't reach any database or any
        linked server other than what's actually configured, regardless of which
        form it uses.

        Returns:
            (True, "") if every reference is in scope, else (False, reason).
            A no-op (returns True) for SQL with no cross-DB references at all.
        """
        primary_db_name = (getattr(self, "primary_db_name", None) or "").lower()
        secondary_db_name = (getattr(self, "secondary_db_name", None) or "").lower()
        same_instance = getattr(self, "same_instance", False)
        allowed_dbs = {d for d in (primary_db_name, secondary_db_name) if d}

        referenced_dbs = {
            m.lower() for m in re.findall(r"\b([a-zA-Z0-9_]+)\.dbo\.[a-zA-Z0-9_]+\b", sql)
        }
        out_of_scope = referenced_dbs - allowed_dbs
        if out_of_scope:
            return False, f"references database(s) {out_of_scope} not configured for this workspace (allowed: {allowed_dbs or 'none'})"

        # Even a reference to the correctly-configured secondary database is
        # invalid if it uses plain three-part naming while the two databases are
        # on separate servers (same_instance=False) — that naming form can only
        # resolve databases on the SAME instance as this connection. Whether it
        # came from the LLM or a stale trained example, it must go through
        # OPENQUERY instead, or it's guaranteed to fail with "Invalid object name".
        if not same_instance and secondary_db_name and secondary_db_name in referenced_dbs:
            secondary_db_alias = getattr(self, "secondary_db_alias", None) or "SECONDARY"
            return False, (
                f"references secondary database '{secondary_db_name}' via plain three-part naming, "
                f"but the databases are on separate servers — it can only be reached via "
                f"OPENQUERY([{secondary_db_alias}], ...), not db.schema.table"
            )

        secondary_db_alias = (getattr(self, "secondary_db_alias", None) or "").lower()
        allowed_aliases = {secondary_db_alias} if secondary_db_alias else set()
        openquery_aliases = {
            m.strip("[] ").lower()
            for m in re.findall(r"OPENQUERY\s*\(\s*(\[?[a-zA-Z0-9_ ]+\]?)\s*,", sql, re.IGNORECASE)
        }
        unknown_aliases = openquery_aliases - allowed_aliases
        if unknown_aliases:
            return False, f"OPENQUERY references linked server(s) {unknown_aliases} not configured for this workspace (allowed: {allowed_aliases or 'none'})"

        return True, ""

    def classify_intent(self, question: str, **kwargs) -> str:
        """
        Cheap heuristic read/write router: decides whether a question should go
        through generate_sql (read) or generate_write_sql (write).

        This is a UX router, NOT a security boundary — is_write_sql_valid plus the
        write whitelist are the actual enforcement. A misclassification is harmless
        either way: a write question routed to "read" just fails to produce valid
        SQL under the read-only prompt and the user is asked to rephrase; a read
        question routed to "write" only costs an unnecessary confirmation step.
        Defaults to "read" whenever it's ambiguous.

        Returns:
            "write" if the question clearly asks for a data change, else "read".
        """
        if not question or not question.strip():
            return "read"

        q = question.lower()

        write_verbs = [
            "update", "change", "set", "modify", "correct", "fix",
            "mark", "cancel", "delete", "remove", "add", "create",
            "insert", "assign", "reassign", "move", "relocate",
            "close", "reopen", "approve", "reject",
        ]
        # Guard against read phrasing that happens to contain a write-ish word,
        # e.g. "show me items that need updating" or "which orders were cancelled".
        read_guards = [
            "show", "list", "how many", "what", "which", "who", "when",
            "where", "count", "find", "get", "display", "report",
            "compare", "summary", "summarize",
        ]

        has_write_verb = any(re.search(rf"\b{re.escape(v)}\b", q) for v in write_verbs)
        has_read_guard = any(re.search(rf"\b{re.escape(g)}\b", q) for g in read_guards)

        return "write" if (has_write_verb and not has_read_guard) else "read"

    def is_write_sql_valid(self, sql: str, whitelist: dict) -> Tuple[bool, str]:
        """
        Validates a generated write statement (UPDATE/INSERT/DELETE) against the
        workspace's write whitelist before it is ever shown for confirmation or
        executed. This is the actual safety boundary for the write path — checks:
        exactly one statement, type is UPDATE/INSERT/DELETE only (no DDL bypass),
        the target table + every referenced column is on the whitelist for that
        operation, and UPDATE/DELETE carry a WHERE clause (no whole-table writes).

        Returns:
            (True, "") if valid, else (False, reason).
        """
        if not sql or not sql.strip():
            return False, "Empty SQL"

        ddl_keywords = r"\b(CREATE|ALTER|DROP|TRUNCATE|RENAME|COMMENT|GRANT|REVOKE|EXEC|EXECUTE)\b"
        if re.search(ddl_keywords, sql, re.IGNORECASE):
            return False, "DDL/administrative statements are not permitted"

        parsed = sqlparse.parse(sql)
        if len(parsed) != 1:
            return False, "Exactly one SQL statement is required per write"

        stmt_type = parsed[0].get_type()
        if stmt_type not in ("UPDATE", "INSERT", "DELETE"):
            return False, f"Only UPDATE/INSERT/DELETE are permitted for writes (got {stmt_type})"

        if stmt_type == "UPDATE":
            table_match = re.search(r"UPDATE\s+([a-zA-Z0-9_.\[\]]+)", sql, re.IGNORECASE)
        elif stmt_type == "INSERT":
            table_match = re.search(r"INSERT\s+INTO\s+([a-zA-Z0-9_.\[\]]+)", sql, re.IGNORECASE)
        else:
            table_match = re.search(r"DELETE\s+FROM\s+([a-zA-Z0-9_.\[\]]+)", sql, re.IGNORECASE)

        if not table_match:
            return False, "Could not determine the target table"

        table_name = table_match.group(1).strip("[]").split(".")[-1].lower()

        whitelist_lower = {k.lower(): v for k, v in (whitelist or {}).items()}
        rule = whitelist_lower.get(table_name)
        if not rule:
            return False, f"Table '{table_name}' is not on the write whitelist"

        allowed_ops = {op.upper() for op in rule.get("allowed_operations", [])}
        if stmt_type not in allowed_ops:
            return False, f"'{stmt_type}' is not a permitted operation on '{table_name}'"

        allowed_columns = {c.lower() for c in rule.get("allowed_columns", [])}

        if stmt_type == "UPDATE":
            set_match = re.search(r"\bSET\b(.*?)\bWHERE\b", sql, re.IGNORECASE | re.DOTALL)
            if not set_match:
                return False, "UPDATE must include a WHERE clause (no whole-table updates)"
            columns = re.findall(r"([a-zA-Z0-9_.\[\]]+)\s*=", set_match.group(1))
        elif stmt_type == "DELETE":
            if not re.search(r"\bWHERE\b", sql, re.IGNORECASE):
                return False, "DELETE must include a WHERE clause (no whole-table deletes)"
            columns = []
        else:  # INSERT
            col_list_match = re.search(r"\(([^)]+)\)\s*VALUES", sql, re.IGNORECASE)
            columns = [c.strip() for c in col_list_match.group(1).split(",")] if col_list_match else []

        for col in columns:
            col_clean = col.strip("[]").split(".")[-1].lower()
            if col_clean and col_clean not in allowed_columns:
                return False, f"Column '{col_clean}' is not whitelisted for writes on '{table_name}'"

        return True, ""

    def should_generate_chart(self, df: pd.DataFrame) -> bool:
        """
        Example:
        ```python
        vn.should_generate_chart(df)
        ```

        Checks if a chart should be generated for the given DataFrame. By default, it checks if the DataFrame has more than one row and has numerical columns.
        You can override this method to customize the logic for generating charts.

        Args:
            df (pd.DataFrame): The DataFrame to check.

        Returns:
            bool: True if a chart should be generated, False otherwise.
        """

        if len(df) > 1 and df.select_dtypes(include=['number']).shape[1] > 0:
            return True

        return False


    def generate_rewritten_question(self, last_question: str, new_question: str, schema: dict = None, sql: str = None, **kwargs) -> str:
        """
        Generate a T-SQL query for a follow-up question, preserving context from the previous question if related and using specified views for six key tables.

        Args:
            last_question (str): The previous question asked.
            new_question (str): The new follow-up question.
            schema (dict, optional): The database schema.
            sql (str, optional): The SQL query from the previous question.
            **kwargs: Additional arguments.

        Returns:
            str: The generated SQL query or an error message.
        """
        last_question = re.sub(r"'''|\\n", '', last_question)  # Clean input
        question_query = f"The followup question {new_question}, previous question {last_question} and it's sql {schema}"
        logging.info(f"rewritten question {question_query}")
        doc_list = self.get_similar_question_sql(question_query, training_data_type="documentation", **kwargs)
        logging.info(f"rewritten documentation {doc_list}")
        if doc_list is not None:
            prompt = [
            {
                "role": "user",
                "content": (
                f"**Previous Question:** {last_question}\n\n"
                f"**Previous SQL Query:**\n"
                f"```sql\n{schema}\n```\n\n"
                f"**Table Documentation:**\n"
                f"```\n{doc_list}\n```\n\n"
                f"**Instructions:**\n"
                f"1. **Context Awareness:** If the new question refers back (e.g. 'them', 'their'), reuse relevant filters or subqueries from prior SQL.\n"
                f"2. **Schema Only:** Use only tables, columns, and values in the documentation-no inventions.\n"
                f"3. **Use Views When Specified:** Otherwise use base tables.\n"
                f"4. **Standalone When Needed:** If unrelated, generate an independent SELECT query.\n"
                f"5. **Missing Info:** If documentation lacks necessary info, respond exactly:\n"
                f"```\nInsufficient data to generate query.\n```\n"
                f"6. **T‑SQL Only:** No LIMIT; use TOP or OFFSET…FETCH. Joins only via documented relationships.\n"
                f"7. **No DDL/DML:** If user asks for CREATE, UPDATE, DELETE, respond exactly:\n"
                f"```\nCannot perform DDL or DML functions.\n```\n"
                f"8. **Fix Syntax Only:** The user needs a corrected MS SQL query-not an explanation or commentary.\n"
                f"9. **LOB‑safe STRING_AGG:** Whenever using `STRING_AGG`, cast the expression to `VARCHAR(MAX)` or `NVARCHAR(MAX)` to prevent the 8000‑byte limit error.\n"
                f"10. **Strict Output:** Output only the final SQL query, enclosed in:\n"
                f"```sql\n...\n```\n\n"
                f"**New Question:** {new_question}"
                )
            }
            ]



        else:
            prompt = [
                {
                    "role": "user",
                    "content": (
                        f"Create a MS SQL query for the following question, enclosed in ```sql```:\n"
                        f"{new_question}\n\n"
                        f"For tables t_location, t_order, t_item_master, t_employee, t_po_detail, t_asn_detail, use their respective views "
                        f"(v_location_explained, v_order_explained, v_item_master_explained, v_employee_explained, v_po_detail_explained, v_asn_detail_explained) "
                        f"and include both code and description columns in SELECT."
                    )
                }
            ]

        logging.info(f"Follow-up prompt: {prompt}")
        return self.submit_prompt(prompt=prompt, **kwargs)

    def generate_followup_questions(
        self, question: str, sql: str, df: pd.DataFrame, schema: dict = None, n_questions: int = 5, **kwargs
    ) -> list:
        """
        **Example:**
        ```python
        vn.generate_followup_questions("What are the top 10 customers by sales?", sql, df)
        ```

        Generate a list of followup questions that you can ask Vanna.AI.

        Args:
            question (str): The question that was asked.
            sql (str): The LLM-generated SQL query.
            df (pd.DataFrame): The results of the SQL query.
            n_questions (int): Number of follow-up questions to generate.

        Returns:
            list: A list of followup questions that you can ask Vanna.AI.
        """

        '''message_log = [
            self.system_message(
                f"You are a helpful data assistant. The user asked the question: '{question}'\n\nThe SQL query for this question was: {sql}\n\nThe following is a pandas DataFrame with the results of the query: \n{df.head(25).to_markdown()}\n\n"
            ),
            self.user_message(
                f"Generate a list of {n_questions} followup questions that the user might ask about this data. Respond with a list of questions, one per line. Do not answer with any explanations -- just the questions. Remember that there should be an unambiguous SQL query that can be generated from the question. Prefer questions that are answerable outside of the context of this conversation. Prefer questions that are slight modifications of the SQL query that was generated that allow digging deeper into the data. Each question will be turned into a button that the user can click to generate a new SQL query so don't use 'example' type questions. Each question must have a one-to-one correspondence with an instantiated SQL query." +
                self._response_language()
            ),
        ]'''
        system_message_content = (
                f"You are a helpful data assistant. The user asked the question: '{question}'\n\n"
                f"The SQL query for this question was: {sql}\n\n"
                f"The schema of the relevant table(s) is as follows:\n{schema}\n\n"
                f"The following is a pandas DataFrame with the results of the query: \n{df.head(25).to_markdown()}\n\n"
            )

        user_message_content = (
                f"Generate a list of {n_questions} follow-up questions that the user might ask about this data. "
                f"Ensure that all questions are relevant to the provided schema and do not reference unknown columns or tables. "
                f"Each follow-up question should allow deeper exploration of the same dataset. "
                f"Respond with a list of questions, one per line, without explanations. "
                f"Each question must have a one-to-one correspondence with an SQL query that can be generated using the given schema." +
                self._response_language()
            )

        message_log = [
            self.system_message(system_message_content),
            self.user_message(user_message_content),
        ]
        logging.info(f"followup message log {message_log}")
        # llm_response = self.submit_prompt(message_log, **kwargs)

        # numbers_removed = re.sub(r"^\d+\.\s*", "", llm_response, flags=re.MULTILINE)
        # return numbers_removed.split("\n")

        llm_response = self.submit_prompt(message_log, **kwargs)

        # Normalize submit_prompt output
        if isinstance(llm_response, tuple):
            llm_text = llm_response[0]
        else:
            llm_text = llm_response

        if not isinstance(llm_text, str):
            llm_text = str(llm_text)

        numbers_removed = re.sub(
            r"^\d+\.\s*", "", llm_text, flags=re.MULTILINE
        )

        return [q.strip() for q in numbers_removed.split("\n") if q.strip()]


    def generate_questions(self, **kwargs) -> List[str]:
        """
        **Example:**
        ```python
        vn.generate_questions()
        ```

        Generate a list of questions that you can ask Vanna.AI.
        """
        question_sql = self.get_similar_question_sql(question="", **kwargs)

        logging.info(f"Genrate quesitons {question_sql}")

        return [q["question"] for q in question_sql]

    # def generate_summary(self, question: str, df: pd.DataFrame, schema: dict = None, sql: str = None, **kwargs) -> str:
    #     """
    #     **Example:**
    #     ```python
    #     vn.generate_summary("What are the top 10 customers by sales?", df)
    #     ```

    #     Generate a summary of the results of a SQL query.

    #     Args:
    #         question (str): The question that was asked.
    #         df (pd.DataFrame): The results of the SQL query.

    #     Returns:
    #         str: The summary of the results of the SQL query.
    #     """

    #     '''message_log = [
    #         self.system_message(
    #             f"You are a helpful data assistant. The user asked the question: '{question}'\n\nThe following is a pandas DataFrame with the results of the query: \n{df.head(50).to_markdown()}\n\n"
    #         ),
    #         self.user_message(
    #             "Briefly summarize the data based on the question that was asked. Do not respond with any additional explanation beyond the summary." +
    #             self._response_language()
    #         ),
    #     ]'''

    #     logging.info(f"starting of summary in base {question}, schema {schema}, sql {sql}")
    #     # Calculate key statistics
    #     '''stats_dict = {
    #         "row_count": len(df),
    #         "column_names": list(df.columns),
    #         "numeric_means": df.select_dtypes(include='number').mean().to_dict() if df.select_dtypes(include='number').columns.any() else "No numeric columns",
    #         "top_categories": df.select_dtypes(include='object').mode().iloc[0].to_dict() if df.select_dtypes(include='object').columns.any() else "No categorical columns",
    #         "unique_count": {col: df[col].nunique() for col in df.columns}  # Add unique counts for columns
    #     }'''
    #     logging.info(f"starting of summary in base {question}, schema {schema}, sql {sql}")
        
    #     # Construct the system message with sql, schema, and DataFrame preview
    #     system_message_content = (
    #         f"You are a helpful data assistant. The user asked the question: '{question}'\n\n"
    #     )
    #     if sql:
    #         system_message_content += (
    #             f"The data is fetched using the query: '{sql}'\n"
    #             f"Note: The query filters the data based on its conditions (e.g., any WHERE clauses). "
    #             f"The DataFrame contains only the rows that satisfy these conditions.\n"
    #         )
    #     if schema:
    #         system_message_content += f"Schema (table or column: data type): {schema}\n"
    #     system_message_content += (
    #         f"Data preview (top 50 rows): \n{df.head(25).to_markdown()}\n\n"
    #     )

    #     # Check if the DataFrame is empty
    #     if df.empty:
    #         summary = "There is no data to summarize."
    #     else:
    #         message_log = [
    #             self.system_message(system_message_content),
    #             self.user_message(
    #                 "Summarize the data in a simple and natural way, as if explaining it to someone who isn't technical, like a high school dropout. "
    #                 "Focus on what the data means in a practical sense (e.g., what it tells us about customers, orders, or sales) rather than technical details like formats or patterns in the numbers. "
    #                 "Avoid using jargon, mentioning specific values like codes or IDs, and do not reference table names or column names. "
    #                 "Include basic insights like counts or general trends if they're relevant, and make the tone conversational. "
    #                 "Do not respond with any additional explanation beyond the summary." + self._response_language()
    #             ),
    #         ]
    #         logging.info(f"inside base generate summary {message_log}")
    #         summary = self.submit_prompt(message_log, **kwargs)

    #     return summary
    def generate_summary(self, question: str, df: pd.DataFrame, schema: dict = None, sql: str = None, **kwargs) -> tuple:
        """
        Returns: (summary_text: str, total_tokens: int, input_tokens: int, output_tokens: int, model_name: str)
        """
        if df is None or df.empty:
            return "There is no data to summarize.", 0, 0, 0, "none"

        # Retrieval of relevant documentation
        question_query = f"{question} and its query {sql}" if sql else question
        doc_list = self.get_similar_question_sql(question_query, training_data_type="documentation", **kwargs)
        logger.info(f"Documentation retrieved for summary: {len(doc_list)} items")

        # ────────────────────────────────────────────────
        # Data characteristics
        # ────────────────────────────────────────────────
        num_rows    = len(df)
        num_columns = len(df.columns)
        has_numeric    = df.select_dtypes(include='number').columns.any()
        has_categorical = df.select_dtypes(include='object').columns.any()

        # ────────────────────────────────────────────────
        # Smart preview + token budgeting
        # ────────────────────────────────────────────────
        MAX_TOKENS = 8000
        RESERVED   = 2000
        BUDGET     = MAX_TOKENS - RESERVED

        max_rows = min(10, num_rows)
        max_cols = min(10, num_columns)
        if num_rows > 50 or num_columns > 5:
            max_rows = min(5, num_rows)
            max_cols = min(5, num_columns)

        preview_cols = list(df.columns[:max_cols])
        if has_numeric and has_categorical:
            num_cols   = list(df.select_dtypes('number').columns)
            cat_cols   = list(df.select_dtypes('object').columns)
            priority   = (num_cols[:1] if num_cols else []) + (cat_cols[:1] if cat_cols else [])
            rest       = [c for c in df.columns if c not in priority][:max_cols - len(priority)]
            preview_cols = list(dict.fromkeys(priority + rest))[:max_cols]

        preview_df = df[preview_cols].head(max_rows)
        preview_md = preview_df.to_markdown(index=False)

        preview_tokens_est = len(preview_md) // 4
        if preview_tokens_est > BUDGET // 2:
            max_rows = max(1, max_rows // 2)
            preview_df = df[preview_cols].head(max_rows)
            preview_md = preview_df.to_markdown(index=False)

        # Truncate large SQL
        sql_display = (sql[:500] + "... (truncated)") if sql and len(sql) > 500 else (sql or "No SQL provided")

        # ────────────────────────────────────────────────
        # System prompt construction
        # ────────────────────────────────────────────────
        system = f"You are a helpful data assistant. The user asked: '{question}'\n\n"

        if sql:
            system += f"Data comes from this query: {sql_display}\n"
            system += "The query filters the data — only matching rows are present.\n"

        if doc_list:
            system += "Table Documentation:\n" + str(doc_list) + "\n\n"
            system += (
                "Instructions:\n"
                "- Use documentation to interpret tables, columns, IDs/codes\n"
                "- Explain business meaning when relevant\n"
                "- Describe query intent in plain business language\n"
                "- Do NOT change or suggest modifications to the SQL\n"
            )

        system += f"Data shape: {num_rows} rows, {num_columns} columns\n"

        # Add stats when helpful
        if num_rows > 10 or num_columns > 5:
            stats = []
            if has_numeric:
                num_c = df.select_dtypes('number').columns
                try:
                    stats.append(f"Avg: {df[num_c].mean().to_dict()}")
                    stats.append(f"Min: {df[num_c].min().to_dict()}")
                    stats.append(f"Max: {df[num_c].max().to_dict()}")
                except:
                    pass
            if has_categorical:
                cat_c = df.select_dtypes('object').columns
                try:
                    stats.append(f"Unique counts: {{c: {df[c].nunique()} for c in cat_c}}")
                except:
                    pass
            if stats:
                system += "Quick statistics:\n" + "; ".join(stats) + "\n"

        system += f"Data preview (top {len(preview_df)} rows, {len(preview_cols)} cols):\n{preview_md}\n\n"

        # ────────────────────────────────────────────────
        # User prompt – tailored by data size
        # ────────────────────────────────────────────────
        user_p = (
            "Summarize what the data shows in clear, simple language — as if explaining to a non-technical colleague. "
            "Focus only on the meaningful business/story insight related to the original question. "
            "Do not mention column names, table names, IDs, technical terms, 'query', 'DataFrame', etc. "
            "No generic openers like 'The data shows' or 'Sure'. Be direct and conversational."
        )

        if num_columns <= 2 and num_rows <= 10:
            user_p += " Data is small → describe values and patterns concisely."
        else:
            user_p += " Data is larger → highlight key totals, rankings, trends or surprises that answer the question."

        if num_rows <= 5:
            user_p += " Very few rows — describe everything without generalizing."
        if has_numeric and has_categorical:
            user_p += " Mention important high/low values or common categories when relevant."
        elif has_numeric:
            user_p += " Mention totals, high/low values or direction of change when relevant."
        elif has_categorical:
            user_p += " Mention most common categories and counts when relevant."

        user_p += self._response_language()   # ← presumably adds language instruction if needed

        # ────────────────────────────────────────────────
        # Submit to LLM
        # ────────────────────────────────────────────────
        messages = [
            self.system_message(system),
            self.user_message(user_p),
        ]

        try:
            result = self.submit_prompt(messages, **kwargs)
            if isinstance(result, tuple) and len(result) == 5:
                text, total, inp, out, model = result
            else:
                text = str(result)
                total = inp = out = 0
                model = "unknown"
        except Exception as e:
            text = f"Summary generation failed: {str(e)}"
            total = inp = out = 0
            model = "error"

        return text, int(total or 0), int(inp or 0), int(out or 0), model or "unknown"




    def get_prediction_suggestions(self, table: list[str],user_query: str, **kwargs) -> str:
        """
        Generate prediction configuration suggestions vital for warehouse personas based on table documentation,
        with ready-to-execute SQL queries that do not require user-defined variables.

        Args:
            table (str): The name of the table to generate predictions for.
            **kwargs: Additional keyword arguments, including 'workspace' (required).

        Returns:
            str: A JSON string containing a list of prediction configurations.
        """
        # Fetch table documentation
        doc_list = self.get_table_documentation(table, **kwargs)
        logger.info(f"Prediction documentations: Tables: {table} and their {doc_list}")
        system_message_content = (
            f"You are a precise and reliable data assistant tasked with generating prediction configurations for a given table, tailored for warehouse personas (employees, operators, managers)."
            f"\n\nThe user asked: '{user_query}'\n\n"
            f"You are provided with:\n"
            f"- A table name: {table}\n"
            f"- Table documentation: {doc_list}\n\n"
            f"The documentation provides technical descriptions, business usage, relationships, and other relevant details strictly related to the specified table(s). You **must**:\n"
            f"- Use **only** the columns, relationships, and details explicitly listed in the provided documentation for {table}.\n"
            f"- **Do not** assume or invent any columns, relationships, or attributes not explicitly mentioned in the documentation.\n"
            f"- Validate that all referenced columns in your SQL queries and parameters exist in the documented schema of {table} or related tables as per the documentation.\n"
            f"- If the documentation is insufficient or unclear, include a note in the justification explaining any limitations and propose solutions based only on available information.\n\n"
            f"Your task is to:\n"
            f"1. Based on the user query and table documentation, identify one or more (up to 5) vital prediction use cases for {table} that can be utilized by warehouse employees, operators, or managers. Focus on predictions that enhance warehouse operations, such as inventory management, order fulfillment, or resource allocation.\n"
            f"2. For each use case, select the most appropriate algorithm from the following list:\n"
            f"   - mean\n"
            f"   - standard_deviation\n"
            f"   - linear_regression\n"
            f"   - logistic_regression\n"
            f"   - custom\n"
            f"3. For each use case, generate:\n"
            f"   - A concise and meaningful prediction name relevant to warehouse operations.\n"
            f"   - The selected algorithm.\n"
            f"   - A valid MS SQL query to fetch training data, using only columns and tables explicitly mentioned in the documentation. The query **must be ready-to-execute** without requiring user-defined variables or parameters (e.g., avoid using @variable placeholders). Use aggregations, static filters, or joins based on the documentation to ensure the query is self-contained.\n"
            f"   - Parameters required for the algorithm, e.g.:\n"
            f"       - For 'mean' or 'standard_deviation': target, inflation_rate\n"
            f"       - For regression: target and features (only documented columns)\n"
            f"       - For custom: any custom fields inside a dictionary (only documented fields)\n"
            f"   - A clear justification explaining why the prediction is vital for warehouse personas, referencing specific details from the documentation and aligning with the user's query.\n\n"
            f"Return your answer in **valid JSON** as a list of prediction configurations, each with the following structure:\n\n"
            f"["
            f"  {{\n"
            f"    \"table_names\": \"{table}\",\n"
            f"    \"prediction_name\": \"<short meaningful name>\",\n"
            f"    \"algorithm\": \"<one of the listed algorithms>\",\n"
            f"    \"sql_query\": \"<valid MS SQL query using only documented columns and tables, no user-defined variables>\",\n"
            f"    \"parameters\": {{\n"
            f"      // parameters depend on algorithm, using only documented columns\n"
            f"    }},\n"
            f"    \"justification\": \"<why this prediction is vital for warehouse personas based on documentation and the user query>\"\n"
            f"  }},"
            f"  ..."
            f"]"
        )


        messages = [
            {"role": "system", "content": system_message_content}
        ]

        # Submit prompt and get suggestions
        #suggestions, token_count = self.submit_prompt(messages, **kwargs)
        (suggestions, token_count, input_tokens, output_tokens, model_name) = \
            self.submit_prompt(messages, **kwargs)

        try:
            parsed_suggestions = json.loads(suggestions)
            if not isinstance(parsed_suggestions, list):
                parsed_suggestions = [parsed_suggestions]

            return (
                json.dumps(parsed_suggestions),
                token_count,
                input_tokens,
                output_tokens,
                model_name,
            )

        except json.JSONDecodeError:
            logging.warning("Failed to parse suggestions as JSON; generating fallback predictions")
            fallback_suggestions = self._generate_fallback_predictions(table, doc_list)

            return (
                json.dumps(fallback_suggestions),
                token_count,
                input_tokens,
                output_tokens,
                model_name,
            )


    def get_anomaly_suggestions(self, table: str, user_query: str, **kwargs) -> str:
        """
        Generate anomaly detection configuration suggestions for warehouse personas based on table documentation,
        with ready-to-execute SQL queries that do not require user-defined variables.

        Args:
            table (str): The name of the table to generate anomaly detection configurations for.
            **kwargs: Additional keyword arguments, including 'workspace' (required).

        Returns:
            str: A JSON string containing a list of anomaly detection configurations.
        """
        # Fetch table documentation
        doc_list = self.get_table_documentation(table, **kwargs)

        system_message_content = (
            f"You are a precise and reliable data assistant tasked with generating anomaly detection configurations for a given table, tailored for warehouse personas (employees, operators, managers). The user asked: 'Given a table name and its complete documentation, "
            f"suggest anomaly detection configurations vital for warehouse operations.'\n\n"
            f"\n\nThe user asked: '{user_query}'\n\n"
            f"You are provided with:\n"
            f"- A table name: {table}\n"
            f"- Table documentation: {doc_list}\n\n"
            f"The documentation provides technical descriptions, business usage, relationships, and other relevant details strictly related to the specified table(s). You **must**:\n"
            f"- Use **only** the columns, relationships, and details explicitly listed in the provided documentation for {table}.\n"
            f"- **Do not** assume or invent any columns, relationships, or attributes not explicitly mentioned in the documentation.\n"
            f"- Validate that all referenced columns in your SQL queries and parameters exist in the documented schema of {table} or related tables as per the documentation.\n"
            f"- If the documentation is insufficient or unclear, include a note in the justification explaining any limitations and propose solutions based only on available information.\n\n"
            f"Your task is to:\n"
            f"1. Identify one or more (up to 5) vital anomaly detection use cases for {table} that can be utilized by warehouse employees, operators, or managers, based solely on its documented purpose and attributes. Focus on detecting anomalies in warehouse operations, such as unusual inventory levels, order delays, or customer order patterns.\n"
            f"2. For each use case, select the most appropriate algorithm from the following list:\n"
            f"   - z_score\n"
            f"   - isolation_forest\n"
            f"   - dbscan\n"
            f"   - custom\n"
            f"3. For each use case, generate:\n"
            f"   - A concise and meaningful anomaly detection name relevant to warehouse operations.\n"
            f"   - The selected algorithm.\n"
            f"   - A valid MS SQL query to fetch data for anomaly detection, using only columns and tables explicitly mentioned in the documentation. The query **must be ready-to-execute** without requiring user-defined variables or parameters (e.g., avoid using @variable placeholders). Use aggregations, static filters, or joins based on the documentation to ensure the query is self-contained.\n"
            f"   - Parameters required for the algorithm, e.g.:\n"
            f"       - For 'z_score': target (documented column), threshold\n"
            f"       - For 'isolation_forest': features (list of documented columns), contamination\n"
            f"       - For 'dbscan': features (list of documented columns), eps, min_samples\n"
            f"       - For 'custom': any custom fields inside a dictionary (only documented fields)\n"
            f"   - A clear justification explaining why detecting this anomaly is vital for warehouse personas, referencing specific details from the documentation.\n\n"
            f"Return your answer in **valid JSON** as a list of anomaly detection configurations, each with the following structure:\n\n"
            f"["
            f"  {{\n"
            f"    \"table_name\": \"{table}\",\n"
            f"    \"anomaly_name\": \"<short meaningful name>\",\n"
            f"    \"algorithm\": \"<one of the listed algorithms>\",\n"
            f"    \"sql_query\": \"<valid MS SQL query using only documented columns and tables, no user-defined variables>\",\n"
            f"    \"parameters\": {{\n"
            f"      // parameters depend on algorithm, using only documented columns\n"
            f"    }},\n"
            f"    \"justification\": \"<why detecting this anomaly is vital for warehouse personas based on documentation>\"\n"
            f"  }},"
            f"  ..."
            f"]"
        )

        messages = [
            {"role": "system", "content": system_message_content}
        ]

        # ---- UPDATED UNPACKING (no functional change) ----
        (suggestions, token_count, input_tokens, output_tokens, model_name) = \
            self.submit_prompt(messages, **kwargs)
        
        logger.info(
            f"Anomaly suggestion billing | "
            f"Model: {model_name} | "
            f"Input Tokens: {input_tokens} | "
            f"Output Tokens: {output_tokens} | "
            f"Total Tokens: {token_count}",
            extra={"token_calculation": True},
        )

        # Ensure suggestions is a JSON string containing a list
        try:
            parsed_suggestions = json.loads(suggestions)
            if not isinstance(parsed_suggestions, list):
                parsed_suggestions = [parsed_suggestions]

            return (
                json.dumps(parsed_suggestions),
                token_count,
                input_tokens,
                output_tokens,
                model_name,
            )

        except json.JSONDecodeError:
            logging.warning(
                "Failed to parse suggestions as JSON; generating fallback anomaly detection configurations"
            )
            fallback_suggestions = self._generate_fallback_anomaly_configurations(table, doc_list)

            return (
                json.dumps(fallback_suggestions),
                token_count,
                input_tokens,
                output_tokens,
                model_name,
            )

    def _generate_fallback_anomaly_configurations(self, table: str, doc_list: list) -> list:
        """
        Generate fallback anomaly detection configurations for warehouse personas if the prompt fails.

        Args:
            table (str): The table name.
            doc_list (list): List of documentation entries for the table.

        Returns:
            list: List of anomaly detection configuration dictionaries.
        """
        # Extract columns and relationships from documentation
        columns = []
        related_tables = []
        for doc in doc_list:
            content = doc.get("content", "")
            if "columns" in content.lower():
                try:
                    parsed = json.loads(content) if content.startswith("{") else {"columns": [], "relationships": []}
                    columns.extend(parsed.get("columns", []))
                    related_tables.extend([rel.get("table") for rel in parsed.get("relationships", [])])
                except json.JSONDecodeError:
                    if "columns:" in content.lower():
                        cols = content.lower().split("columns:")[1].split(", ")
                        columns.extend([c.strip() for c in cols if c.strip()])

        if not columns:
            columns = ["id", "quantity"]  # Default for warehouse context

        # Generate fallback anomaly detection configurations for warehouse personas
        configurations = [
            {
                "table_name": table,
                "anomaly_name": f"Unusual_{table}_Quantity",
                "algorithm": "z_score",
                "sql_query": f"SELECT id, quantity FROM {table} WHERE quantity IS NOT NULL",
                "parameters": {
                    "target": "quantity",
                    "threshold": 2.0
                },
                "justification": f"Detecting unusual quantity values in {table} helps warehouse employees identify potential inventory errors or stock outliers, based on the documented 'quantity' column."
            },
            {
                "table_name": table,
                "anomaly_name": f"{table}_Quantity_Clusters",
                "algorithm": "dbscan",
                "sql_query": f"SELECT id, quantity FROM {table} WHERE quantity IS NOT NULL",
                "parameters": {
                    "features": ["quantity"],
                    "eps": 0.5,
                    "min_samples": 5
                },
                "justification": f"Identifying clusters of quantity values in {table} helps managers detect abnormal inventory patterns, using the documented 'quantity' column."
            }
        ]

        # Add a third configuration if status or customer_id exists
        if "status" in columns:
            configurations.append({
                "table_name": table,
                "anomaly_name": f"{table}_Pending_Orders_Anomaly",
                "algorithm": "custom",
                "sql_query": f"SELECT COUNT(*) as pending_orders FROM {table} WHERE status = 'pending' GROUP BY CONVERT(DATE, created_at)",
                "parameters": {
                    "aggregate": "COUNT(*)",
                    "filter": "status = 'pending'",
                    "group_by": "CONVERT(DATE, created_at)"
                },
                "justification": f"Detecting anomalies in the count of pending orders per day in {table} helps operators identify unusual delays in order processing, using the documented 'status' and 'created_at' columns."
            })
        elif related_tables and "customer_id" in columns:
            configurations.append({
                "table_name": table,
                "anomaly_name": f"{table}_Customer_Order_Anomaly",
                "algorithm": "isolation_forest",
                "sql_query": f"SELECT customer_id, COUNT(*) as order_count FROM {table} GROUP BY customer_id",
                "parameters": {
                    "features": ["order_count"],
                    "contamination": 0.1
                },
                "justification": f"Detecting unusual order frequencies per customer in {table} helps operators identify atypical customer behavior, leveraging the 'customer_id' column and its relationship to {related_tables[0]}."
            })

        return configurations
        
    def _generate_fallback_predictions(self, table: str, doc_list: list) -> list:
        """
        Generate fallback prediction configurations for warehouse personas if the prompt fails.

        Args:
            table (str): The table name.
            doc_list (list): List of documentation entries for the table.

        Returns:
            list: List of prediction configuration dictionaries.
        """
        # Extract columns and relationships from documentation
        columns = []
        related_tables = []
        for doc in doc_list:
            content = doc.get("content", "")
            if "columns" in content.lower():
                try:
                    parsed = json.loads(content) if content.startswith("{") else {"columns": [], "relationships": []}
                    columns.extend(parsed.get("columns", []))
                    related_tables.extend([rel.get("table") for rel in parsed.get("relationships", [])])
                except json.JSONDecodeError:
                    if "columns:" in content.lower():
                        cols = content.lower().split("columns:")[1].split(", ")
                        columns.extend([c.strip() for c in cols if c.strip()])

        if not columns:
            columns = ["id", "quantity"]  # Default for warehouse context

        # Generate fallback predictions for warehouse personas
        predictions = [
            {
                "table_name": table,
                "prediction_name": f"Average_{table}_Quantity",
                "algorithm": "mean",
                "sql_query": f"SELECT AVG(quantity) as avg_quantity FROM {table} WHERE quantity IS NOT NULL",
                "parameters": {
                    "target": "quantity",
                    "inflation_rate": 0.02
                },
                "justification": f"Predicting the average quantity in {table} helps warehouse employees manage inventory levels, ensuring stock availability, based on the documented 'quantity' column."
            },
            {
                "table_name": table,
                "prediction_name": f"{table}_Stock_Variability",
                "algorithm": "standard_deviation",
                "sql_query": f"SELECT STDEV(quantity) as std_quantity FROM {table} WHERE quantity IS NOT NULL",
                "parameters": {
                    "target": "quantity",
                    "inflation_rate": 0.02
                },
                "justification": f"Calculating the variability of quantity in {table} assists managers in understanding stock fluctuations, aiding in resource planning."
            }
        ]

        # Add a third prediction if status or customer_id exists
        if "status" in columns:
            predictions.append({
                "table_name": table,
                "prediction_name": f"{table}_Pending_Orders",
                "algorithm": "custom",
                "sql_query": f"SELECT COUNT(*) as pending_orders FROM {table} WHERE status = 'pending'",
                "parameters": {
                    "aggregate": "COUNT(*)",
                    "filter": "status = 'pending'"
                },
                "justification": f"Counting pending orders in {table} helps operators prioritize order processing, using the documented 'status' column."
            })
        elif related_tables and "customer_id" in columns:
            predictions.append({
                "table_name": table,
                "prediction_name": f"{table}_Customer_Order_Frequency",
                "algorithm": "custom",
                "sql_query": f"SELECT customer_id, COUNT(*) as order_count FROM {table} GROUP BY customer_id",
                "parameters": {
                    "group_by": "customer_id",
                    "aggregate": "COUNT(*)"
                },
                "justification": f"Counting orders per customer in {table} helps operators prioritize high-frequency customers, leveraging the 'customer_id' column and its relationship to {related_tables[0]}."
            })

        return predictions


    # ----------------- Use Any Embeddings API ----------------- #
    @abstractmethod
    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        pass

    # ----------------- Use Any Database to Store and Retrieve Context ----------------- #
    @abstractmethod
    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        """
        This method is used to get similar questions and their corresponding SQL statements.

        Args:
            question (str): The question to get similar questions and their corresponding SQL statements for.

        Returns:
            list: A list of similar questions and their corresponding SQL statements.
        """
        pass
    @abstractmethod
    def get_table_documentation(self, table: str, **kwargs) -> list:
        """
        This method is used to get similar questions and their corresponding SQL statements.

        Args:
            question (str): The question to get similar questions and their corresponding SQL statements for.

        Returns:
            list: A list of similar questions and their corresponding SQL statements.
        """
        pass
    @abstractmethod
    def get_related_ddl(self, question: str, **kwargs) -> list:
        """
        This method is used to get related DDL statements to a question.

        Args:
            question (str): The question to get related DDL statements for.

        Returns:
            list: A list of related DDL statements.
        """
        pass

    @abstractmethod
    def get_write_whitelist(self, workspace: str = None, **kwargs) -> dict:
        """
        Returns the write whitelist that constrains chat-driven data modification.

        Returns:
            dict: keyed by table name (lowercase), each value shaped like
            {"db": <db alias>, "allowed_operations": ["UPDATE", ...], "allowed_columns": [...]}.
            A table absent from this dict is not writable. An empty dict disables
            writes entirely for the workspace.
        """
        pass

    @abstractmethod
    def get_related_documentation(self, question: str, **kwargs) -> list:
        """
        This method is used to get related documentation to a question.

        Args:
            question (str): The question to get related documentation for.

        Returns:
            list: A list of related documentation.
        """
        pass

    @abstractmethod
    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        """
        This method is used to add a question and its corresponding SQL query to the training data.

        Args:
            question (str): The question to add.
            sql (str): The SQL query to add.

        Returns:
            str: The ID of the training data that was added.
        """
        pass

    @abstractmethod
    def add_ddl(self, ddl: str, **kwargs) -> str:
        """
        This method is used to add a DDL statement to the training data.

        Args:
            ddl (str): The DDL statement to add.

        Returns:
            str: The ID of the training data that was added.
        """
        pass

    @abstractmethod
    def add_documentation(self, documentation: str, **kwargs) -> str:
        """
        This method is used to add documentation to the training data.

        Args:
            documentation (str): The documentation to add.

        Returns:
            str: The ID of the training data that was added.
        """
        pass

    @abstractmethod
    def get_training_data(self, workspace: str = None, **kwargs) -> pd.DataFrame:
        """
        Example:
        ```python
        vn.get_training_data()
        ```

        This method is used to get all the training data from the retrieval layer.

        Returns:
            pd.DataFrame: The training data.
        """
        pass

    @abstractmethod
    def remove_training_data(self, id: str, **kwargs) -> bool:
        """
        Example:
        ```python
        vn.remove_training_data(id="123-ddl")
        ```

        This method is used to remove training data from the retrieval layer.

        Args:
            id (str): The ID of the training data to remove.

        Returns:
            bool: True if the training data was removed, False otherwise.
        """
        pass

    # ----------------- Use Any Language Model API ----------------- #

    @abstractmethod
    def system_message(self, message: str) -> any:
        pass

    @abstractmethod
    def user_message(self, message: str) -> any:
        pass

    @abstractmethod
    def assistant_message(self, message: str) -> any:
        pass

    def str_to_approx_token_count(self, string: str) -> int:
        return len(string) / 4

    def add_ddl_to_prompt(
        self, initial_prompt: str, ddl_list: list[str], max_tokens: int = 14000
    ) -> str:
        if len(ddl_list) > 0:
            initial_prompt += "\n===Tables \n"

            for ddl in ddl_list:
                if (
                    self.str_to_approx_token_count(initial_prompt)
                    + self.str_to_approx_token_count(ddl)
                    < max_tokens
                ):
                    initial_prompt += f"{ddl}\n\n"

        return initial_prompt

    '''def add_documentation_to_prompt(
        self,
        initial_prompt: str,
        documentation_list: list[str],
        max_tokens: int = 14000,
    ) -> str:
        if len(documentation_list) > 0:
            initial_prompt += "\n===Prioritize Documentation: If schema/documentation is provided (up to five documents), deeply analyze and select the single most relevant document based on the user's question to construct a new query. Fallback to Dataset if No Documentation: If no documentation is provided, check the dataset for a relevant query that matches the user's request and use it directly. \nIf using documentation, ensure the query aligns with the table structure, respects constraints, and leverages appropriate columns, foreign keys, and indexes for efficiency. \n\n"

            for documentation in documentation_list:
                if (
                    self.str_to_approx_token_count(initial_prompt)
                    + self.str_to_approx_token_count(documentation)
                    < max_tokens
                ):
                    initial_prompt += f"{documentation}\n\n"


        return initial_prompt'''

    def add_documentation_to_prompt(
        self,
        initial_prompt: str,
        documentation_list: list[str],
        max_tokens: int = 14000,
    ) -> str:
        """
        Append documentation-related instructions + the docs themselves
        to the existing initial_prompt without overwriting it.
        """
        if documentation_list:
            initial_prompt += (
                "\n\n=== Documentation Check ===\n"
                "- You are given warehouse table documentation that describes schema, "
                "relationships, technical details, and business usage.\n"
                "- Treat this documentation as an authoritative description of the tables.\n"
                "- Use only tables and columns that appear in:\n"
                "  - The documentation, OR\n"
                "  - The example Question-SQL pairs (dataset), OR\n"
                "  - Explicit domain mappings (query_mapping).\n"
                "- Do NOT invent new tables or columns.\n"
                "- If a required table or column does not appear in ANY of these sources, respond with:\n"
                "  Insufficient data for query.\n"
                "- When documentation provides technical vs business descriptions, you should still generate "
                "SQL only from the actual schema-level elements (tables, columns, relationships).\n"
            )

            for documentation in documentation_list:
                if (
                    self.str_to_approx_token_count(initial_prompt)
                    + self.str_to_approx_token_count(documentation)
                    < max_tokens
                ):
                    initial_prompt += f"\n{documentation}\n"

        else:
            initial_prompt += (
                "\n\n=== Documentation Check ===\n"
                "- No table documentation was provided. Rely on dataset Question–SQL pairs and any domain mappings.\n"
            )

        return initial_prompt



    def add_sql_to_prompt(
        self, initial_prompt: str, sql_list: list[str], max_tokens: int = 14000
    ) -> str:
        if len(sql_list) > 0:
            initial_prompt += "\n===1. Dataset Lookup (Highest Priority):\n- First, check if the provided dataset contains an existing SQL query that exactly answers or closely matches the question using text similarity.\n- If an exact match is found, reuse it without modification.\n- If a similar query exists but requires minor adjustments (e.g., column name changes, minor filtering), modify it accordingly.\n-Do not generate a new query if the dataset contains a suitable one.  \n\n"


            for question in sql_list:
                if (
                    self.str_to_approx_token_count(initial_prompt)
                    + self.str_to_approx_token_count(question["sql"])
                    < max_tokens
                ):
                    initial_prompt += f"{question['question']}\n{question['sql']}\n\n"

        return initial_prompt

    '''def get_sql_prompt(
        self,
        initial_prompt : str,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        # """
        # Example:
        # ```python
        # vn.get_sql_prompt(
        #     question="What are the top 10 customers by sales?",
        #     question_sql_list=[{"question": "What are the top 10 customers by sales?", "sql": "SELECT * FROM customers ORDER BY sales DESC LIMIT 10"}],
        #     ddl_list=["CREATE TABLE customers (id INT, name TEXT, sales DECIMAL)"],
        #     doc_list=["The customers table contains information about customers and their sales."],
        # )

        # ```

        # This method is used to generate a prompt for the LLM to generate SQL.

        # Args:
        #     question (str): The question to generate SQL for.
        #     question_sql_list (list): A list of questions and their corresponding SQL statements.
        #     ddl_list (list): A list of DDL statements.
        #     doc_list (list): A list of documentation.

        # Returns:
        #     any: The prompt for the LLM to generate SQL.
        # """

        if initial_prompt is None:
            initial_prompt = f"You are a warehouse {self.dialect} expert. " + \
            "Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context (dataset and document) and follow the response guidelines and format instructions. Do not generate queries based on external knowledge or assumptions. \n\n===Additional Context \n1. Dataset: A collection of pre-defined SQL queries and their corresponding questions. If the user's question matches a question in the dataset, use the corresponding query from the dataset without modification. \n2. Schema: Schema of the table(s) that matched the question using text similarity. \n3. Documentation: Detailed explanation of the table(s) and columns that matched the question using text similarity."


        initial_prompt = self.add_ddl_to_prompt(
            initial_prompt, ddl_list, max_tokens=self.max_tokens
        )
        # for example in question_sql_list:
        #     sql=[]
        #     question = []
        #     if example is None:
        #         print("example is None")
        #     else:
        #         if example is not None and "question" in example and "sql" in example:
        #             question.append(self.user_message(example["question"]))
        #             sql.append(self.assistant_message(example["sql"]))
        #             initial_prompt+=f"question-{question} related sql-{sql}"

        # initial_prompt = self.add_sql_to_prompt(
        #     initial_prompt, question_sql_list, max_tokens=self.max_tokens
        # )




        # initial_prompt += (
        #     "\n\n===Response Guidelines"
            
        #     "\n\n1. Step-by-Step Reasoning: \nnStep 1: Understand the User Query:\nIdentify the intent of the question and the key details (e.g., filters, columns, tables). \nnStep 2: Check the Dataset: \nLook for a matching or highly similar query in the provided dataset.\n If a match is found, use the corresponding SQL query exactly as it is. Do not modify it. \n\nStep 3: Use Schema and Documentation: \nIf no match is found in the dataset, use the provided schema and documentation to generate a valid SQL query. \nSelect the relevant tables and columns based on the query. \nDetermine if joins are needed and specify the join conditions. \nApply filters (WHERE clauses) based on the query requirements. \n\nStep 4: Validate the Query: \nEnsure the query aligns with schema constraints and is executable in T-SQL / Microsoft SQL Server. \n\nStep 5: Handle Intermediate Queries: \nIf the context is almost sufficient but requires knowledge of specific values in a column, generate an intermediate query to find distinct values in that column. \n\n2. Priority Order: \nAlways prioritize using the dataset query if a match is found. \nOnly generate a new query if the dataset does not contain a matching query. \n\n3. Query Requirements: \nEnsure the SQL query is T-SQL / Microsoft SQL Server-compliant and executable. \nDo not generate queries for Data Definition Language (DDL) operations (e.g., CREATE, ALTER, DROP, TRUNCATE). \nInstead, respond with: 'I am unable to perform any Data Definition Language (DDL) functions.'  \nDo not include explanations unless the query cannot be generated. \n\n4. Intermediate Queries: \nIf the context is almost sufficient but requires knowledge of specific values in a column, generate an intermediate query to find distinct values in that column. \nPlease enclose the SQL query inside triple backticks like this:\n```sql\nSELECT * FROM table;\n```"
        #     "\n\n===Examples"
           
        # )

        initial_prompt = (
            "\n\n=== T-SQL Query Generation Guidelines ===\n"
            "You are tasked with generating T-SQL queries for a Warehouse Management System (WMS) database using MS SQL Server. "
            "Adhere strictly to the provided schema and documentation.\n\n"
            " **Understand the Request:**\n"
            "   - Read the user's query and identify entities, attributes, and conditions.\n\n"
            " **Schema Validation:**\n"
            "   - Use only the tables and columns explicitly defined in the schema.\n"
            "   - If schema info is missing, output:\n"
            "     ```\n"
            "     Insufficient data for query.\n"
            "     ```\n\n"
            " **Operation Constraints:**\n"
            "   - Disallow DDL (CREATE, ALTER, DROP, TRUNCATE, UPDATE). If requested, output:\n"
            "     ```\n"
            "     Cannot perform DDL functions.\n"
            "     ```\n\n"
            " **Unknown Values:**\n"
            "   - To list possible values for an unspecified column, output a DISTINCT query:\n"
            "     ```sql\n"
            "     SELECT DISTINCT column_name FROM table_name;\n"
            "     ```\n\n"
            " **Result Limits:**\n"
            "   - Use `TOP` or `OFFSET … FETCH`. Do **not** use `LIMIT`.\n\n"
            " **Joins:**\n"
            "   - Join tables only on schema-defined keys.\n\n"

            " **Output Requirements:**\n"
            "   - **Only** output the final T-SQL query wrapped in triple backticks with `sql` with no comments:\n"
            "     ```sql\n"
            "     -- Your query here\n"
            "     ```\n"
            "   - **No** additional explanation, comments, or step-by-step reasoning.\n\n"
            "By following these rules, respond with exactly the T-SQL query that fulfills the user's request."
        )

        if self.static_documentation != "":
            doc_list.append(self.static_documentation)
        initial_prompt = self.add_documentation_to_prompt(
            initial_prompt, doc_list, max_tokens=self.max_tokens
        )
        initial_prompt += "====Dataset Example: \n\n Contains example queries. Select the most relevant query from the dataset examples that closely matches the user's question. \nDo not create any new columns or tables that are not present in the dataset. \nForm the SQL query strictly using the known columns provided in the dataset. \nEnsure the query is precise, syntactically correct SQL, and aligned with the user's intent as closely as possible based on available dataset examples."
        message_log = [self.system_message(initial_prompt)]
        for example in question_sql_list:
            if example is None:
                print("example is None")
            else:
                if example is not None and "question" in example and "sql" in example:
                    message_log.append(self.user_message(example["question"]))
                    message_log.append(self.assistant_message(example["sql"]))      

        message_log.append(self.user_message(question))

        return message_log'''
    


    def get_sql_prompt(
        self,
        initial_prompt: str = "",
        question: str = "",
        question_sql_list: list = None,
        ddl_list: list = None,
        doc_list: list = None,
        domain_context: dict = None,
        **kwargs,
    ) -> str:
        """
        Builds a single, well-structured prompt string for SQL generation.
        Returns plain text (not message list) — compatible with most LLM backends.
        """

        if question_sql_list is None:
            question_sql_list = []
        if ddl_list is None:
            ddl_list = []
        if doc_list is None:
            doc_list = []
        if domain_context is None:
            domain_context = {}

        # ────────────────────────────────────────────────
        # 1. Base / fallback system prompt (only if nothing provided)
        # ────────────────────────────────────────────────
        if not initial_prompt:
            initial_prompt = (
                "You are an expert T-SQL query generator for Microsoft SQL Server 2022.\n\n"
                "STRICT RULES:\n"
                "- Generate ONLY clean SELECT statements — no comments (--, /* */), no explanations.\n"
                "- Use ONLY tables and columns that appear in the provided documentation, examples, or mappings.\n"
                "- Never invent tables, columns, joins, filters or business logic.\n"
                "- If any required element is missing → respond exactly: 'Insufficient data for query.'\n"
                "**No DDL/DML:** If user asks for CREATE, UPDATE, DELETE, respond exactly:\n"
                "```\nCannot perform DDL or DML functions.\n```\n"
                "- Use single quotes for string literals.\n"
                "- Use TOP n or OFFSET ... FETCH — never LIMIT.\n"
                "- Return ONLY the query inside ```sql ... ``` block — nothing else.\n"

            )

        prompt = initial_prompt.strip() + "\n\n"

        # ────────────────────────────────────────────────
        # 2. Add DDL (schema) context
        # ────────────────────────────────────────────────
        prompt = self.add_ddl_to_prompt(prompt, ddl_list, max_tokens=self.max_tokens or 8000)

        # Add static documentation if exists
        if hasattr(self, 'static_documentation') and self.static_documentation:
            doc_list = doc_list + [self.static_documentation]

        prompt = self.add_documentation_to_prompt(prompt, doc_list, max_tokens=self.max_tokens or 8000)

        # ────────────────────────────────────────────────
        # 3. Domain context (glossary, tables, mappings)
        # ────────────────────────────────────────────────
        glossary = domain_context.get("glossary", [])
        tables = domain_context.get("tables", [])
        query_mapping = domain_context.get("query_mapping", [])

        if glossary or tables or query_mapping:
            prompt += "=== Business / Domain Context ===\n"
            if glossary:
                prompt += f"Glossary: {', '.join(glossary[:15])}\n"  # limit to avoid token explosion
            if tables:
                prompt += f"Relevant tables: {', '.join(tables)}\n"
            if query_mapping:
                prompt += f"Query mappings: {', '.join(str(m) for m in query_mapping[:10])}\n"
            prompt += (
                "Use this context only to interpret intent — "
                "NEVER invent schema or joins not supported by examples/documentation.\n\n"
            )

        # ────────────────────────────────────────────────
        # 3.5. Cross-database qualification (dual-DB workspaces only)
        # Only fires when retrieval found relevant tables on both the primary and
        # a configured secondary DB (see ChromaDB_VectorStore.get_similar_question_sql).
        # Single-DB workspaces have no secondary_db_alias, so this is a no-op for them.
        # ────────────────────────────────────────────────
        table_dbs = domain_context.get("table_dbs", {}) or {}
        cross_db = domain_context.get("cross_db", False)
        secondary_db_alias = domain_context.get("secondary_db_alias") or getattr(self, "secondary_db_alias", None)
        secondary_db_name = getattr(self, "secondary_db_name", None)
        same_instance = domain_context.get("same_instance", getattr(self, "same_instance", False))

        if cross_db and secondary_db_alias and secondary_db_name:
            secondary_tables = [t for t in tables if table_dbs.get(t) == secondary_db_alias]
            primary_tables = [t for t in tables if t not in secondary_tables]

            if same_instance:
                # Both databases live on the same SQL Server instance — no linked server
                # involved, so plain three-part naming works directly and is strictly
                # simpler/faster than OPENQUERY. No new infrastructure needed.
                prompt += (
                    "=== Cross-Database Query ===\n"
                    "This question needs tables from two databases on the SAME SQL Server instance "
                    f"(this connection reaches both — no linked server involved).\n"
                    f"- Primary-database tables (reference normally, no prefix): {', '.join(primary_tables) or 'none of the relevant tables'}\n"
                    f"- Secondary-database tables (database '{secondary_db_name}'): {', '.join(secondary_tables) or 'none'}\n\n"
                    f"Qualify EVERY secondary-database table with its three-part name: {secondary_db_name}.dbo.<table_name> "
                    "('dbo' is the default schema — use the schema documentation actually specifies if it differs). "
                    "Join it to primary-database tables normally, using the documented key columns — exactly as you "
                    "would join any other table. Never qualify a primary-database table with any prefix.\n\n"
                )
            else:
                prompt += (
                    "=== Cross-Database Query ===\n"
                    "This question needs tables from two databases, reached through a SQL Server linked server "
                    "configured from this connection.\n"
                    f"- Primary-database tables (reference normally, no prefix): {', '.join(primary_tables) or 'none of the relevant tables'}\n"
                    f"- Secondary-database tables (alias '{secondary_db_alias}'): {', '.join(secondary_tables) or 'none'}\n\n"
                    "Do NOT reference secondary-database tables with a plain four-part name (e.g. "
                    f"[{secondary_db_alias}].{secondary_db_name}.dbo.table) — SQL Server's optimizer frequently fails "
                    "to push filters across a linked server that way and pulls the entire remote table locally, which "
                    "is a serious production performance risk on large warehouse tables. Instead, for EVERY secondary-database "
                    "table reference:\n"
                    f"1. Wrap it in OPENQUERY, pushing every filter you can determine from the question (constants, "
                    f"dates, IDs, statuses — anything that is NOT dependent on a primary-table row) into the remote "
                    f"query text, e.g.:\n"
                    f"   OPENQUERY([{secondary_db_alias}], 'SELECT col1, col2 FROM dbo.table WHERE known_filter = ''value''')\n"
                    "   ('dbo' is the default schema — use the schema documentation actually specifies if it differs.)\n"
                    "2. OPENQUERY's query text cannot reference primary-table columns (no per-row correlation is possible "
                    "— it is a single static query executed entirely on the remote server). Push down only filters whose "
                    "values are already known from the question itself.\n"
                    "3. Then JOIN the OPENQUERY(...) result to the primary-database table normally, in the outer query, "
                    "using the documented key columns — exactly as you would join to any other table or subquery.\n"
                    "4. Inside the OPENQUERY string literal, every single quote belonging to a value (not the literal's "
                    "own boundary quotes) MUST be doubled (e.g. 'O''Brien' not 'O'Brien'). An unescaped quote will "
                    "break the query and is rejected before execution.\n"
                    "5. Never qualify a primary-database table with any prefix.\n"
                    "6. The two databases may have different default collations. If the JOIN condition compares a "
                    "string/varchar column from the OPENQUERY(...) result against a primary-database column, add "
                    "COLLATE SQL_Latin1_General_CP1_CI_AS to that side of the comparison (e.g. "
                    "ON I.col = T.col COLLATE SQL_Latin1_General_CP1_CI_AS) to avoid a collation-conflict error — "
                    "purely numeric join keys don't need this.\n\n"
                )

        # ────────────────────────────────────────────────
        # 4. Example Question → SQL pairs (few-shot learning)
        # ────────────────────────────────────────────────
        if question_sql_list:
            prompt += "=== Relevant Example Queries ===\n"
            prompt += "Use patterns, tables and columns from the most similar examples below.\n\n"

            for i, ex in enumerate(question_sql_list[:6], 1):  # limit to 6 to save tokens
                q = ""
                s = ""
                if isinstance(ex, dict):
                    if "question" in ex and "sql" in ex:
                        q = ex["question"].strip()
                        s = ex["sql"].strip()
                    elif "content" in ex:
                        content = ex["content"]
                        q = content.get("question", "").strip()
                        s = content.get("sql", "").strip()

                if q and s:
                    prompt += f"Example {i}:\nQuestion: {q}\nSQL:\n{s}\n\n"

            prompt += (
                "Prefer the example that best matches the intent.\n"
                "Reuse table/column names and join patterns exactly as shown.\n"
                "If no example is reasonably similar → 'Insufficient data for query.'\n\n"
            )

        # ────────────────────────────────────────────────
        # 5. Anti-hallucination & validation rules (reinforced)
        # ────────────────────────────────────────────────
        prompt += (
            "=== FINAL VALIDATION RULES (must follow) ===\n"
            "1. Every table and column MUST appear in documentation, examples or mappings.\n"
            "2. No cross-table column transfer.\n"
            "3. No invented joins unless explicitly present in an example.\n"
            "4. Case-insensitive string compares: use LOWER() on both sides.\n"
            "5. If validation fails at any point → return exactly:\n"
            "   Insufficient data for query.\n"
            "6. Output format: ONLY the code block — nothing else.\n\n"
        )

        # ────────────────────────────────────────────────
        # 6. The actual user question (placed at the end)
        # ────────────────────────────────────────────────
        prompt += f"Generate T-SQL for this question:\n{question.strip()}\n\n"

        return prompt

    def get_write_sql_prompt(self, question: str, whitelist: dict, workspace: str = None, **kwargs) -> str:
        """
        Builds the system prompt for write (UPDATE/INSERT/DELETE) SQL generation.

        Unlike get_sql_prompt, this is constrained to an explicit whitelist of
        tables/columns/operations rather than whatever the retrieval layer surfaces
        — a write must never touch anything the workspace hasn't explicitly approved.
        The whitelist is the real enforcement (see is_write_sql_valid); this prompt
        is the first line of defense, not the only one.
        """
        if not whitelist:
            return (
                "Writes are not enabled for this workspace (no write whitelist is configured).\n"
                "Respond exactly:\n```\nWrites are not enabled for this workspace.\n```\n"
            )

        lines = []
        for table, rule in whitelist.items():
            ops = ", ".join(rule.get("allowed_operations", []))
            cols = ", ".join(rule.get("allowed_columns", []))
            lines.append(f"- {table}: operations=[{ops}], columns=[{cols}]")
        whitelist_text = "\n".join(lines)

        return (
            "You are an expert T-SQL query generator for Microsoft SQL Server 2022, generating a "
            "DATA-MODIFYING statement (UPDATE, INSERT, or DELETE) requested by a warehouse user.\n\n"
            "STRICT RULES:\n"
            "1. You may ONLY write to the tables, columns and operations listed below. Nothing else is "
            "permitted — if the request needs a table, column or operation not listed, respond exactly:\n"
            "   ```\n   Insufficient data for query.\n   ```\n"
            f"{whitelist_text}\n\n"
            "2. UPDATE and DELETE statements MUST include a WHERE clause that targets specific row(s) — "
            "never a whole-table write.\n"
            "3. Write to exactly one table in a single statement — never combine tables and never write "
            "across two databases.\n"
            "4. No DDL (CREATE, ALTER, DROP, TRUNCATE) under any circumstance.\n"
            "5. Use single quotes for string literals; double any single quote that is part of a value "
            "itself (e.g. 'O''Brien').\n"
            "6. Return ONLY the statement inside a ```sql ... ``` block — no explanation, no comments.\n\n"
            f"Generate the T-SQL statement for this request:\n{question.strip()}\n"
        )

    def get_followup_questions_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ) -> list:
        initial_prompt = f"The user initially asked the question: '{question}': \n\n"

        initial_prompt = self.add_ddl_to_prompt(
            initial_prompt, ddl_list, max_tokens=self.max_tokens
        )

        initial_prompt = self.add_documentation_to_prompt(
            initial_prompt, doc_list, max_tokens=self.max_tokens
        )

        initial_prompt = self.add_sql_to_prompt(
            initial_prompt, question_sql_list, max_tokens=self.max_tokens
        )

        message_log = [self.system_message(initial_prompt)]
        message_log.append(
            self.user_message(
                "Generate a list of followup questions that the user might ask about this data. Respond with a list of questions, one per line. Do not answer with any explanations -- just the questions."
            )
        )

        return message_log

    @abstractmethod
    def submit_prompt(self, prompt, **kwargs) -> str:
        """
        Example:
        ```python
        vn.submit_prompt(
            [
                vn.system_message("The user will give you SQL and you will try to guess what the business question this query is answering. Return just the question without any additional explanation. Do not reference the table name in the question."),
                vn.user_message("What are the top 10 customers by sales?"),
            ]
        )
        ```

        This method is used to submit a prompt to the LLM.

        Args:
            prompt (any): The prompt to submit to the LLM.

        Returns:
            str: The response from the LLM.
        """
        pass

    def generate_question(self, sql: str, **kwargs) -> str:
        response = self.submit_prompt(
            [
                self.system_message(
                    "The user will give you SQL and you will try to guess what the business question this query is answering. Return just the question without any additional explanation. Do not reference the table name in the question."
                ),
                self.user_message(sql),
            ],
            **kwargs,
        )

        return response

    def _extract_python_code(self, markdown_string: str) -> str:
        # Strip whitespace to avoid indentation errors in LLM-generated code
        markdown_string = markdown_string.strip()

        # Regex pattern to match Python code blocks
        pattern = r"```[\w\s]*python\n([\s\S]*?)```|```([\s\S]*?)```"

        # Find all matches in the markdown string
        matches = re.findall(pattern, markdown_string, re.IGNORECASE)

        # Extract the Python code from the matches
        python_code = []
        for match in matches:
            python = match[0] if match[0] else match[1]
            python_code.append(python.strip())

        if len(python_code) == 0:
            return markdown_string

        return python_code[0]

    def _sanitize_plotly_code(self, raw_plotly_code: str) -> str:
        # Remove the fig.show() statement from the plotly code
        plotly_code = raw_plotly_code.replace("fig.show()", "")

        return plotly_code

    # def generate_plotly_code(
    #     self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs
    # ) -> str:
    #     if question is not None:
    #         system_msg = f"The following is a pandas DataFrame that contains the results of the query that answers the question the user asked: '{question}'"
    #     else:
    #         system_msg = "The following is a pandas DataFrame "

    #     if sql is not None:
    #         system_msg += f"\n\nThe DataFrame was produced using this query: {sql}\n\n"

    #     system_msg += f"The following is information about the resulting pandas DataFrame 'df': \n{df_metadata}"

    #     message_log = [
    #         self.system_message(system_msg),
    #         self.user_message(
    #             "Can you generate the Python plotly code to chart the results of the dataframe? Assume the data is in a pandas dataframe called 'df'. If there is only one value in the dataframe, use an Indicator. Respond with only Python code. Do not answer with any explanations -- just the code."
    #         ),
    #     ]

    #     plotly_code = self.submit_prompt(message_log, kwargs=kwargs)

    #     return self._sanitize_plotly_code(self._extract_python_code(plotly_code))


    def generate_plotly_code(self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs) -> str:
        if question is not None:
            system_msg = (
                f"The following is a pandas DataFrame that contains the results of the query "
                f"that answers the question the user asked: '{question}'"
            )
        else:
            system_msg = "The following is a pandas DataFrame "

        if sql is not None:
            system_msg += (
                f"\n\nThe DataFrame was produced using this query: {sql}\n\n"
            )

        system_msg += (
            f"The following is information about the resulting pandas DataFrame 'df': \n"
            f"{df_metadata}"
        )

        message_log = [
            self.system_message(system_msg),
            self.user_message(
                "Can you generate the Python plotly code to chart the results of the dataframe? "
                "Assume the data is in a pandas dataframe called 'df'. "
                "If there is only one value in the dataframe, use an Indicator. "
                "Respond with only Python code. Do not answer with any explanations -- just the code."
            ),
        ]

        plotly_code = self.submit_prompt(message_log, kwargs=kwargs)

    
        # If submit_prompt returns (response_text, usage) tuple
        if isinstance(plotly_code, tuple):
            plotly_code = plotly_code[0]

        # Ensure it's always a string
        if not isinstance(plotly_code, str):
            plotly_code = str(plotly_code)
    

        return self._sanitize_plotly_code(
            self._extract_python_code(plotly_code)
        )

    # ----------------- Connect to Any Database to run the Generated SQL ----------------- #

    def connect_to_snowflake(
        self,
        account: str,
        username: str,
        password: str,
        database: str,
        role: Union[str, None] = None,
        warehouse: Union[str, None] = None,
        **kwargs
    ):
        try:
            snowflake = __import__("snowflake.connector")
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method, run command:"
                " \npip install vanna[snowflake]"
            )

        if username == "my-username":
            username_env = os.getenv("SNOWFLAKE_USERNAME")

            if username_env is not None:
                username = username_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake username.")

        if password == "mypassword":
            password_env = os.getenv("SNOWFLAKE_PASSWORD")

            if password_env is not None:
                password = password_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake password.")

        if account == "my-account":
            account_env = os.getenv("SNOWFLAKE_ACCOUNT")

            if account_env is not None:
                account = account_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake account.")

        if database == "my-database":
            database_env = os.getenv("SNOWFLAKE_DATABASE")

            if database_env is not None:
                database = database_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake database.")

        conn = snowflake.connector.connect(
            user=username,
            password=password,
            account=account,
            database=database,
            client_session_keep_alive=True,
            **kwargs
        )

        def run_sql_snowflake(sql: str) -> pd.DataFrame:
            cs = conn.cursor()

            if role is not None:
                cs.execute(f"USE ROLE {role}")

            if warehouse is not None:
                cs.execute(f"USE WAREHOUSE {warehouse}")
            cs.execute(f"USE DATABASE {database}")

            cur = cs.execute(sql)

            results = cur.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(results, columns=[desc[0] for desc in cur.description])

            return df

        self.dialect = "Snowflake SQL"
        self.run_sql = run_sql_snowflake
        self.run_sql_is_set = True

    def connect_to_sqlite(self, url: str, check_same_thread: bool = False,  **kwargs):
        """
        Connect to a SQLite database. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]

        Args:
            url (str): The URL of the database to connect to.
            check_same_thread (str): Allow the connection may be accessed in multiple threads.
        Returns:
            None
        """

        # URL of the database to download

        # Path to save the downloaded database
        path = os.path.basename(urlparse(url).path)

        # Download the database if it doesn't exist
        if not os.path.exists(url):
            response = requests.get(url)
            response.raise_for_status()  # Check that the request was successful
            with open(path, "wb") as f:
                f.write(response.content)
            url = path

        # Connect to the database
        conn = sqlite3.connect(
            url,
            check_same_thread=check_same_thread,
            **kwargs
        )

        def run_sql_sqlite(sql: str):
            return pd.read_sql_query(sql, conn)

        self.dialect = "SQLite"
        self.run_sql = run_sql_sqlite
        self.run_sql_is_set = True

    def connect_to_postgres(
        self,
        host: str = None,
        dbname: str = None,
        user: str = None,
        password: str = None,
        port: int = None,
        **kwargs
    ):

        """
        Connect to postgres using the psycopg2 connector. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]
        **Example:**
        ```python
        vn.connect_to_postgres(
            host="myhost",
            dbname="mydatabase",
            user="myuser",
            password="mypassword",
            port=5432
        )
        ```
        Args:
            host (str): The postgres host.
            dbname (str): The postgres database name.
            user (str): The postgres user.
            password (str): The postgres password.
            port (int): The postgres Port.
        """

        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: \npip install vanna[postgres]"
            )

        if not host:
            host = os.getenv("HOST")

        if not host:
            raise ImproperlyConfigured("Please set your postgres host")

        if not dbname:
            dbname = os.getenv("DATABASE")

        if not dbname:
            raise ImproperlyConfigured("Please set your postgres database")

        if not user:
            user = os.getenv("PG_USER")

        if not user:
            raise ImproperlyConfigured("Please set your postgres user")

        if not password:
            password = os.getenv("PASSWORD")

        if not password:
            raise ImproperlyConfigured("Please set your postgres password")

        if not port:
            port = os.getenv("PORT")

        if not port:
            raise ImproperlyConfigured("Please set your postgres port")

        conn = None

        try:
            conn = psycopg2.connect(
                host=host,
                dbname=dbname,
                user=user,
                password=password,
                port=port,
                **kwargs
            )
        except psycopg2.Error as e:
            raise ValidationError(e)

        def connect_to_db():
            return psycopg2.connect(host=host, dbname=dbname,
                        user=user, password=password, port=port, **kwargs)


        def run_sql_postgres(sql: str) -> Union[pd.DataFrame, None]:
            conn = None
            try:
                conn = connect_to_db()  # Initial connection attempt
                cs = conn.cursor()
                cs.execute(sql)
                results = cs.fetchall()

                # Create a pandas dataframe from the results
                df = pd.DataFrame(results, columns=[desc[0] for desc in cs.description])
                return df

            except psycopg2.InterfaceError as e:
                # Attempt to reconnect and retry the operation
                if conn:
                    conn.close()  # Ensure any existing connection is closed
                conn = connect_to_db()
                cs = conn.cursor()
                cs.execute(sql)
                results = cs.fetchall()

                # Create a pandas dataframe from the results
                df = pd.DataFrame(results, columns=[desc[0] for desc in cs.description])
                return df

            except psycopg2.Error as e:
                if conn:
                    conn.rollback()
                    raise ValidationError(e)

            except Exception as e:
                        conn.rollback()
                        raise e

        self.dialect = "PostgreSQL"
        self.run_sql_is_set = True
        self.run_sql = run_sql_postgres


    def connect_to_mysql(
        self,
        host: str = None,
        dbname: str = None,
        user: str = None,
        password: str = None,
        port: int = None,
        **kwargs
    ):

        try:
            import pymysql.cursors
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: \npip install PyMySQL"
            )

        if not host:
            host = os.getenv("HOST")

        if not host:
            raise ImproperlyConfigured("Please set your MySQL host")

        if not dbname:
            dbname = os.getenv("DATABASE")

        if not dbname:
            raise ImproperlyConfigured("Please set your MySQL database")

        if not user:
            user = os.getenv("USER")

        if not user:
            raise ImproperlyConfigured("Please set your MySQL user")

        if not password:
            password = os.getenv("PASSWORD")

        if not password:
            raise ImproperlyConfigured("Please set your MySQL password")

        if not port:
            port = os.getenv("PORT")

        if not port:
            raise ImproperlyConfigured("Please set your MySQL port")

        conn = None

        try:
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=dbname,
                port=port,
                cursorclass=pymysql.cursors.DictCursor,
                **kwargs
            )
        except pymysql.Error as e:
            raise ValidationError(e)

        def run_sql_mysql(sql: str) -> Union[pd.DataFrame, None]:
            if conn:
                try:
                    conn.ping(reconnect=True)
                    cs = conn.cursor()
                    cs.execute(sql)
                    results = cs.fetchall()

                    # Create a pandas dataframe from the results
                    df = pd.DataFrame(
                        results, columns=[desc[0] for desc in cs.description]
                    )
                    return df

                except pymysql.Error as e:
                    conn.rollback()
                    raise ValidationError(e)

                except Exception as e:
                    conn.rollback()
                    raise e

        self.run_sql_is_set = True
        self.run_sql = run_sql_mysql

    def connect_to_clickhouse(
        self,
        host: str = None,
        dbname: str = None,
        user: str = None,
        password: str = None,
        port: int = None,
        **kwargs
    ):

        try:
            import clickhouse_connect
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: \npip install clickhouse_connect"
            )

        if not host:
            host = os.getenv("HOST")

        if not host:
            raise ImproperlyConfigured("Please set your ClickHouse host")

        if not dbname:
            dbname = os.getenv("DATABASE")

        if not dbname:
            raise ImproperlyConfigured("Please set your ClickHouse database")

        if not user:
            user = os.getenv("USER")

        if not user:
            raise ImproperlyConfigured("Please set your ClickHouse user")

        if not password:
            password = os.getenv("PASSWORD")

        if not password:
            raise ImproperlyConfigured("Please set your ClickHouse password")

        if not port:
            port = os.getenv("PORT")

        if not port:
            raise ImproperlyConfigured("Please set your ClickHouse port")

        conn = None

        try:
            conn = clickhouse_connect.get_client(
                host=host,
                port=port,
                username=user,
                password=password,
                database=dbname,
                **kwargs
            )
            print(conn)
        except Exception as e:
            raise ValidationError(e)

        def run_sql_clickhouse(sql: str) -> Union[pd.DataFrame, None]:
            if conn:
                try:
                    result = conn.query(sql)
                    results = result.result_rows

                    # Create a pandas dataframe from the results
                    df = pd.DataFrame(results, columns=result.column_names)
                    return df

                except Exception as e:
                    raise e

        self.run_sql_is_set = True
        self.run_sql = run_sql_clickhouse

    def connect_to_oracle(
        self,
        user: str = None,
        password: str = None,
        dsn: str = None,
        **kwargs
    ):

        """
        Connect to an Oracle db using oracledb package. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]
        **Example:**
        ```python
        vn.connect_to_oracle(
        user="username",
        password="password",
        dsn="host:port/sid",
        )
        ```
        Args:
            USER (str): Oracle db user name.
            PASSWORD (str): Oracle db user password.
            DSN (str): Oracle db host ip - host:port/sid.
        """

        try:
            import oracledb
        except ImportError:

            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: \npip install oracledb"
            )

        if not dsn:
            dsn = os.getenv("DSN")

        if not dsn:
            raise ImproperlyConfigured("Please set your Oracle dsn which should include host:port/sid")

        if not user:
            user = os.getenv("USER")

        if not user:
            raise ImproperlyConfigured("Please set your Oracle db user")

        if not password:
            password = os.getenv("PASSWORD")

        if not password:
            raise ImproperlyConfigured("Please set your Oracle db password")

        conn = None

        try:
            conn = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn,
                **kwargs
            )
        except oracledb.Error as e:
            raise ValidationError(e)

        def run_sql_oracle(sql: str) -> Union[pd.DataFrame, None]:
            if conn:
                try:
                    sql = sql.rstrip()
                    if sql.endswith(';'): #fix for a known problem with Oracle db where an extra ; will cause an error.
                        sql = sql[:-1]

                    cs = conn.cursor()
                    cs.execute(sql)
                    results = cs.fetchall()

                    # Create a pandas dataframe from the results
                    df = pd.DataFrame(
                        results, columns=[desc[0] for desc in cs.description]
                    )
                    return df

                except oracledb.Error as e:
                    conn.rollback()
                    raise ValidationError(e)

                except Exception as e:
                    conn.rollback()
                    raise e

        self.run_sql_is_set = True
        self.run_sql = run_sql_oracle

    def connect_to_bigquery(
        self,
        cred_file_path: str = None,
        project_id: str = None,
        **kwargs
    ):
        """
        Connect to gcs using the bigquery connector. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]
        **Example:**
        ```python
        vn.connect_to_bigquery(
            project_id="myprojectid",
            cred_file_path="path/to/credentials.json",
        )
        ```
        Args:
            project_id (str): The gcs project id.
            cred_file_path (str): The gcs credential file path
        """

        try:
            from google.api_core.exceptions import GoogleAPIError
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method, run command:"
                " \npip install vanna[bigquery]"
            )

        if not project_id:
            project_id = os.getenv("PROJECT_ID")

        if not project_id:
            raise ImproperlyConfigured("Please set your Google Cloud Project ID.")

        import sys

        if "google.colab" in sys.modules:
            try:
                from google.colab import auth

                auth.authenticate_user()
            except Exception as e:
                raise ImproperlyConfigured(e)
        else:
            print("Not using Google Colab.")

        conn = None

        if not cred_file_path:
            try:
                conn = bigquery.Client(project=project_id)
            except:
                print("Could not found any google cloud implicit credentials")
        else:
            # Validate file path and pemissions
            validate_config_path(cred_file_path)

        if not conn:
            with open(cred_file_path, "r") as f:
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(f.read()),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )

            try:
                conn = bigquery.Client(
                    project=project_id,
                    credentials=credentials,
                    **kwargs
                )
            except:
                raise ImproperlyConfigured(
                    "Could not connect to bigquery please correct credentials"
                )

        def run_sql_bigquery(sql: str) -> Union[pd.DataFrame, None]:
            if conn:
                job = conn.query(sql)
                df = job.result().to_dataframe()
                return df
            return None

        self.dialect = "BigQuery SQL"
        self.run_sql_is_set = True
        self.run_sql = run_sql_bigquery

    def connect_to_duckdb(self, url: str, init_sql: str = None, **kwargs):
        """
        Connect to a DuckDB database. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]

        Args:
            url (str): The URL of the database to connect to. Use :memory: to create an in-memory database. Use md: or motherduck: to use the MotherDuck database.
            init_sql (str, optional): SQL to run when connecting to the database. Defaults to None.

        Returns:
            None
        """
        try:
            import duckdb
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: \npip install vanna[duckdb]"
            )
        # URL of the database to download
        if url == ":memory:" or url == "":
            path = ":memory:"
        else:
            # Path to save the downloaded database
            print(os.path.exists(url))
            if os.path.exists(url):
                path = url
            elif url.startswith("md") or url.startswith("motherduck"):
                path = url
            else:
                path = os.path.basename(urlparse(url).path)
                # Download the database if it doesn't exist
                if not os.path.exists(path):
                    response = requests.get(url)
                    response.raise_for_status()  # Check that the request was successful
                    with open(path, "wb") as f:
                        f.write(response.content)

        # Connect to the database
        conn = duckdb.connect(path, **kwargs)
        if init_sql:
            conn.query(init_sql)

        def run_sql_duckdb(sql: str):
            return conn.query(sql).to_df()

        self.dialect = "DuckDB SQL"
        self.run_sql = run_sql_duckdb
        self.run_sql_is_set = True

    # def connect_to_mssql(self, odbc_conn_str: str, **kwargs):
    #     """
    #     Connect to a Microsoft SQL Server database. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]

    #     Args:
    #         odbc_conn_str (str): The ODBC connection string.

    #     Returns:
    #         None
    #     """
    #     try:
    #         import pyodbc
    #     except ImportError:
    #         raise DependencyError(
    #             "You need to install required dependencies to execute this method,"
    #             " run command: pip install pyodbc"
    #         )

    #     try:
    #         import sqlalchemy as sa
    #         from sqlalchemy.engine import URL
    #     except ImportError:
    #         raise DependencyError(
    #             "You need to install required dependencies to execute this method,"
    #             " run command: pip install sqlalchemy"
    #         )

    #     connection_url = URL.create(
    #         "mssql+pyodbc", query={"odbc_connect": odbc_conn_str}
    #     )

    #     from sqlalchemy import create_engine

    #     engine = create_engine(connection_url, **kwargs)

    #     def run_sql_mssql(sql: str):
    #         # Execute the SQL statement and return the result as a pandas DataFrame
    #         with engine.begin() as conn:
    #             df = pd.read_sql_query(sa.text(sql), conn)
    #             conn.close()
    #             return df

    #         raise Exception("Couldn't run sql")

    #     self.dialect = "T-SQL / Microsoft SQL Server"
    #     self.run_sql = run_sql_mssql
    #     self.run_sql_is_set = True









    #without any 15 sec time constrain on exectuing the query
    # def connect_to_mssql(self, odbc_conn_str: str, pool_size: int = 10, max_overflow: int = 5, **kwargs):
    #     # Convert pool_size and max_overflow to integers if they’re strings
    #     try:
    #         pool_size = int(pool_size)
    #         max_overflow = int(max_overflow)
    #     except (ValueError, TypeError) as e:
    #         raise ValueError(f"pool_size and max_overflow must be integers or convertible to integers. Got: pool_size={pool_size}, max_overflow={max_overflow}")
 
    #     try:
    #         import pyodbc
    #     except ImportError:
    #         raise DependencyError(
    #             "You need to install required dependencies to execute this method,"
    #             " run command: pip install pyodbc"
    #         )
 
    #     try:
    #         import sqlalchemy as sa
    #         from sqlalchemy.engine import URL
    #     except ImportError:
    #         raise DependencyError(
    #             "You need to install required dependencies to execute this method,"
    #             " run command: pip install sqlalchemy"
    #         )
 
    #     connection_url = URL.create(
    #         "mssql+pyodbc", query={"odbc_connect": odbc_conn_str}
    #     )
 
    #     from sqlalchemy import create_engine
 
    #     engine = create_engine(
    #         connection_url,
    #         pool_size=pool_size,
    #         max_overflow=max_overflow,
    #         pool_pre_ping=True,
    #         **kwargs
    #     )
    #     logging.info(engine)
       
    #     def run_sql_mssql(sql: str):
    #         with engine.begin() as conn:
    #             df = pd.read_sql_query(sa.text(sql), conn)
    #             return df
 
    #     self.dialect = "T-SQL / Microsoft SQL Server"
    #     self.run_sql = run_sql_mssql
    #     self.run_sql_is_set = True


    def connect_to_mssql(self, odbc_conn_str: str, pool_size: int = 10, max_overflow: int = 5, query_timeout: int = 15, **kwargs):
        # Convert pool_size and max_overflow to integers if they're strings
        try:
            pool_size = int(pool_size)
            max_overflow = int(max_overflow)
        except (ValueError, TypeError) as e:
            raise ValueError(f"pool_size and max_overflow must be integers or convertible to integers. Got: pool_size={pool_size}, max_overflow={max_overflow}")

        try:
            import pyodbc
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: pip install pyodbc"
            )

        try:
            import sqlalchemy as sa
            from sqlalchemy.engine import URL
            from sqlalchemy import event
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: pip install sqlalchemy"
            )

        connection_url = URL.create(
            "mssql+pyodbc", query={"odbc_connect": odbc_conn_str}
        )

        from sqlalchemy import create_engine

        engine = create_engine(
            connection_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            **kwargs
        )
        
        # Set query timeout for all connections from the pool
        @event.listens_for(engine, "connect")
        def set_connection_timeout(dbapi_conn, connection_record):
            """Set timeout on the raw pyodbc connection"""
            dbapi_conn.timeout = query_timeout
        
        logger.info(f"   MS SQL connection established with {query_timeout}s query timeout", extra={"user": True})
    
        def run_sql_mssql(sql: str):
            try:
                logger.info(f"   Executing SQL query with {query_timeout}s timeout", extra={"user": True})
                with engine.begin() as conn:
                    # Execute with timeout using execution_options
                    result = conn.execution_options(timeout=query_timeout).execute(sa.text(sql))
                    columns = list(result.keys())
                    if len(columns) != len(set(columns)):
                        # A join can legitimately return two columns with the same name
                        # (e.g. two tables both having a "pick_put_id" column with no
                        # alias to disambiguate). pandas allows that in a DataFrame but
                        # refuses to serialize it to JSON records downstream — rename
                        # duplicates here so every caller gets a usable, unique-column
                        # DataFrame instead of a crash several layers away.
                        seen = {}
                        deduped = []
                        for col in columns:
                            if col not in seen:
                                seen[col] = 0
                                deduped.append(col)
                            else:
                                seen[col] += 1
                                deduped.append(f"{col}_{seen[col]}")
                        columns = deduped
                    df = pd.DataFrame(result.fetchall(), columns=columns)
                    logger.info(f"   Query executed successfully, returned {len(df)} rows", extra={"user": True})
                    return df
            except sa.exc.DBAPIError as e:
                # Check if it's a timeout error
                if "timeout" in str(e).lower() or "query timeout" in str(e).lower():
                    logger.error(f"   Query exceeded {query_timeout}s timeout limit and was terminated", extra={"user": True})
                    raise TimeoutError(f"Query execution exceeded {query_timeout} seconds and was terminated to protect database performance")
                else:
                    logger.error(f"   Database error: {e}", extra={"user": True})
                    raise
            except Exception as e:
                logger.error(f"   Unexpected error executing SQL: {e}", extra={"user": True})
                raise

        self.dialect = "T-SQL / Microsoft SQL Server"
        self.run_sql = run_sql_mssql
        self.run_sql_is_set = True














    def connect_to_presto(
        self,
        host: str,
        catalog: str = 'hive',
        schema: str = 'default',
        user: str = None,
        password: str = None,
        port: int = None,
        combined_pem_path: str = None,
        protocol: str = 'https',
        requests_kwargs: dict = None,
        **kwargs
    ):
      """
        Connect to a Presto database using the specified parameters.

        Args:
            host (str): The host address of the Presto database.
            catalog (str): The catalog to use in the Presto environment.
            schema (str): The schema to use in the Presto environment.
            user (str): The username for authentication.
            password (str): The password for authentication.
            port (int): The port number for the Presto connection.
            combined_pem_path (str): The path to the combined pem file for SSL connection.
            protocol (str): The protocol to use for the connection (default is 'https').
            requests_kwargs (dict): Additional keyword arguments for requests.

        Raises:
            DependencyError: If required dependencies are not installed.
            ImproperlyConfigured: If essential configuration settings are missing.

        Returns:
            None
      """
      try:
        from pyhive import presto
      except ImportError:
        raise DependencyError(
          "You need to install required dependencies to execute this method,"
          " run command: \npip install pyhive"
        )

      if not host:
        host = os.getenv("PRESTO_HOST")

      if not host:
        raise ImproperlyConfigured("Please set your presto host")

      if not catalog:
        catalog = os.getenv("PRESTO_CATALOG")

      if not catalog:
        raise ImproperlyConfigured("Please set your presto catalog")

      if not user:
        user = os.getenv("PRESTO_USER")

      if not user:
        raise ImproperlyConfigured("Please set your presto user")

      if not password:
        password = os.getenv("PRESTO_PASSWORD")

      if not port:
        port = os.getenv("PRESTO_PORT")

      if not port:
        raise ImproperlyConfigured("Please set your presto port")

      conn = None

      try:
        if requests_kwargs is None and combined_pem_path is not None:
          # use the combined pem file to verify the SSL connection
          requests_kwargs = {
            'verify': combined_pem_path,  # 使用转换后得到的 PEM 文件进行 SSL 验证
          }
        conn = presto.Connection(host=host,
                                 username=user,
                                 password=password,
                                 catalog=catalog,
                                 schema=schema,
                                 port=port,
                                 protocol=protocol,
                                 requests_kwargs=requests_kwargs,
                                 **kwargs)
      except presto.Error as e:
        raise ValidationError(e)

      def run_sql_presto(sql: str) -> Union[pd.DataFrame, None]:
        if conn:
          try:
            sql = sql.rstrip()
            # fix for a known problem with presto db where an extra ; will cause an error.
            if sql.endswith(';'):
                sql = sql[:-1]
            cs = conn.cursor()
            cs.execute(sql)
            results = cs.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(
              results, columns=[desc[0] for desc in cs.description]
            )
            return df

          except presto.Error as e:
            print(e)
            raise ValidationError(e)

          except Exception as e:
            print(e)
            raise e

      self.run_sql_is_set = True
      self.run_sql = run_sql_presto

    def connect_to_hive(
        self,
        host: str = None,
        dbname: str = 'default',
        user: str = None,
        password: str = None,
        port: int = None,
        auth: str = 'CUSTOM',
        **kwargs
    ):
      """
        Connect to a Hive database. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]
        Connect to a Hive database. This is just a helper function to set [`vn.run_sql`][vanna.base.base.VannaBase.run_sql]

        Args:
            host (str): The host of the Hive database.
            dbname (str): The name of the database to connect to.
            user (str): The username to use for authentication.
            password (str): The password to use for authentication.
            port (int): The port to use for the connection.
            auth (str): The authentication method to use.

        Returns:
            None
      """

      try:
        from pyhive import hive
      except ImportError:
        raise DependencyError(
          "You need to install required dependencies to execute this method,"
          " run command: \npip install pyhive"
        )

      if not host:
        host = os.getenv("HIVE_HOST")

      if not host:
        raise ImproperlyConfigured("Please set your hive host")

      if not dbname:
        dbname = os.getenv("HIVE_DATABASE")

      if not dbname:
        raise ImproperlyConfigured("Please set your hive database")

      if not user:
        user = os.getenv("HIVE_USER")

      if not user:
        raise ImproperlyConfigured("Please set your hive user")

      if not password:
        password = os.getenv("HIVE_PASSWORD")

      if not port:
        port = os.getenv("HIVE_PORT")

      if not port:
        raise ImproperlyConfigured("Please set your hive port")

      conn = None

      try:
        conn = hive.Connection(host=host,
                               username=user,
                               password=password,
                               database=dbname,
                               port=port,
                               auth=auth)
      except hive.Error as e:
        raise ValidationError(e)

      def run_sql_hive(sql: str) -> Union[pd.DataFrame, None]:
        if conn:
          try:
            cs = conn.cursor()
            cs.execute(sql)
            results = cs.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(
              results, columns=[desc[0] for desc in cs.description]
            )
            return df

          except hive.Error as e:
            print(e)
            raise ValidationError(e)

          except Exception as e:
            print(e)
            raise e

      self.run_sql_is_set = True
      self.run_sql = run_sql_hive

    def run_sql(self, sql: str, **kwargs) -> pd.DataFrame:
        """
        Example:
        ```python
        vn.run_sql("SELECT * FROM my_table")
        ```

        Run a SQL query on the connected database.

        Args:
            sql (str): The SQL query to run.

        Returns:
            pd.DataFrame: The results of the SQL query.
        """
        raise Exception(
            "You need to connect to a database first by running vn.connect_to_snowflake(), vn.connect_to_postgres(), similar function, or manually set vn.run_sql"
        )

    def ask(
        self,
        question: Union[str, None] = None,
        print_results: bool = True,
        auto_train: bool = True,
        visualize: bool = True,  # if False, will not generate plotly code
        allow_llm_to_see_data: bool = False,
    ) -> Union[
        Tuple[
            Union[str, None],
            Union[pd.DataFrame, None],
            Union[plotly.graph_objs.Figure, None],
        ],
        None,
    ]:
        """
        **Example:**
        ```python
        vn.ask("What are the top 10 customers by sales?")
        ```

        Ask Vanna.AI a question and get the SQL query that answers it.

        Args:
            question (str): The question to ask.
            print_results (bool): Whether to print the results of the SQL query.
            auto_train (bool): Whether to automatically train Vanna.AI on the question and SQL query.
            visualize (bool): Whether to generate plotly code and display the plotly figure.

        Returns:
            Tuple[str, pd.DataFrame, plotly.graph_objs.Figure]: The SQL query, the results of the SQL query, and the plotly figure.
        """

        if question is None:
            question = input("Enter a question: ")

        try:
            sql = self.generate_sql(question=question, allow_llm_to_see_data=allow_llm_to_see_data)
        except Exception as e:
            print(e)
            return None, None, None

        if print_results:
            try:
                Code = __import__("IPython.display", fromList=["Code"]).Code
                display(Code(sql))
            except Exception as e:
                print(sql)

        if self.run_sql_is_set is False:
            print(
                "If you want to run the SQL query, connect to a database first."
            )

            if print_results:
                return None
            else:
                return sql, None, None

        try:
            df = self.run_sql(sql)

            if print_results:
                try:
                    display = __import__(
                        "IPython.display", fromList=["display"]
                    ).display
                    display(df)
                except Exception as e:
                    print(df)

            if len(df) > 0 and auto_train:
                self.add_question_sql(question=question, sql=sql)
            # Only generate plotly code if visualize is True
            if visualize:
                try:
                    plotly_code = self.generate_plotly_code(
                        question=question,
                        sql=sql,
                        df_metadata=f"Running df.dtypes gives:\n {df.dtypes}",
                    )
                    fig = self.get_plotly_figure(plotly_code=plotly_code, df=df)
                    if print_results:
                        try:
                            display = __import__(
                                "IPython.display", fromlist=["display"]
                            ).display
                            Image = __import__(
                                "IPython.display", fromlist=["Image"]
                            ).Image
                            img_bytes = fig.to_image(format="png", scale=2)
                            display(Image(img_bytes))
                        except Exception as e:
                            fig.show()
                except Exception as e:
                    # Print stack trace
                    traceback.print_exc()
                    print("Couldn't run plotly code: ", e)
                    if print_results:
                        return None
                    else:
                        return sql, df, None
            else:
                return sql, df, None

        except Exception as e:
            print("Couldn't run sql: ", e)
            if print_results:
                return None
            else:
                return sql, None, None
        return sql, df, fig

    def train(
        self,
        question: str = None,
        sql: str = None,
        ddl: str = None,
        documentation: str = None,
        plan: TrainingPlan = None,

        collection_name: str = None
    ) -> str:
        """
        **Example:**
        ```python
        vn.train()
        ```

        Train Vanna.AI on a question and its corresponding SQL query.
        If you call it with no arguments, it will check if you connected to a database and it will attempt to train on the metadata of that database.
        If you call it with the sql argument, it's equivalent to [`vn.add_question_sql()`][vanna.base.base.VannaBase.add_question_sql].
        If you call it with the ddl argument, it's equivalent to [`vn.add_ddl()`][vanna.base.base.VannaBase.add_ddl].
        If you call it with the documentation argument, it's equivalent to [`vn.add_documentation()`][vanna.base.base.VannaBase.add_documentation].
        Additionally, you can pass a [`TrainingPlan`][vanna.types.TrainingPlan] object. Get a training plan with [`vn.get_training_plan_generic()`][vanna.base.base.VannaBase.get_training_plan_generic].

        Args:
            question (str): The question to train on.
            sql (str): The SQL query to train on.
            ddl (str):  The DDL statement.
            documentation (str): The documentation to train on.
            plan (TrainingPlan): The training plan to train on.
        """

        if question and not sql:
            raise ValidationError("Please also provide a SQL query")

        if documentation:
            print("Adding documentation....")
            return self.add_documentation(documentation)

        if sql:
            if question is None:
                question = self.generate_question(sql)
                print("Question generated with sql:", question, "\nAdding SQL...")
            return self.add_question_sql(question=question, sql=sql, collection_name=collection_name)

        if ddl:
            print("Adding ddl:", ddl)
            return self.add_ddl(ddl)

        if plan:
            for item in plan._plan:
                if item.item_type == TrainingPlanItem.ITEM_TYPE_DDL:
                    self.add_ddl(item.item_value)
                elif item.item_type == TrainingPlanItem.ITEM_TYPE_IS:
                    self.add_documentation(item.item_value)
                elif item.item_type == TrainingPlanItem.ITEM_TYPE_SQL:
                    self.add_question_sql(question=item.item_name, sql=item.item_value)

    def _get_databases(self) -> List[str]:
        try:
            print("Trying INFORMATION_SCHEMA.DATABASES")
            df_databases = self.run_sql("SELECT * FROM INFORMATION_SCHEMA.DATABASES")
        except Exception as e:
            print(e)
            try:
                print("Trying SHOW DATABASES")
                df_databases = self.run_sql("SHOW DATABASES")
            except Exception as e:
                print(e)
                return []

        return df_databases["DATABASE_NAME"].unique().tolist()

    def _get_information_schema_tables(self, database: str) -> pd.DataFrame:
        df_tables = self.run_sql(f"SELECT * FROM {database}.INFORMATION_SCHEMA.TABLES")

        return df_tables

    # def get_training_plan_generic(self, df) -> TrainingPlan:
    #     """
    #     This method is used to generate a training plan from an information schema dataframe.

    #     Basically what it does is breaks up INFORMATION_SCHEMA.COLUMNS into groups of table/column descriptions that can be used to pass to the LLM.

    #     Args:
    #         df (pd.DataFrame): The dataframe to generate the training plan from.

    #     Returns:
    #         TrainingPlan: The training plan.
    #     """
    #     # For each of the following, we look at the df columns to see if there's a match:
    #     database_column = df.columns[
    #         df.columns.str.lower().str.contains("database")
    #         | df.columns.str.lower().str.contains("table_catalog")
    #     ].to_list()[0]
    #     schema_column = df.columns[
    #         df.columns.str.lower().str.contains("table_schema")
    #     ].to_list()[0]
    #     table_column = df.columns[
    #         df.columns.str.lower().str.contains("table_name")
    #     ].to_list()[0]
    #     columns = [database_column,
    #                 schema_column,
    #                 table_column]
    #     candidates = ["column_name",
    #                   "data_type",
    #                   "comment"]
    #     matches = df.columns.str.lower().str.contains("|".join(candidates), regex=True)
    #     columns += df.columns[matches].to_list()

    #     plan = TrainingPlan([])

    #     for database in df[database_column].unique().tolist():
    #         for schema in (
    #             df.query(f'{database_column} == "{database}"')[schema_column]
    #             .unique()
    #             .tolist()
    #         ):
    #             for table in (
    #                 df.query(
    #                     f'{database_column} == "{database}" and {schema_column} == "{schema}"'
    #                 )[table_column]
    #                 .unique()
    #                 .tolist()
    #             ):
    #                 df_columns_filtered_to_table = df.query(
    #                     f'{database_column} == "{database}" and {schema_column} == "{schema}" and {table_column} == "{table}"'
    #                 )
    #                 doc = f"The following columns are in the {table} table in the {database} database:\n\n"
    #                 doc += df_columns_filtered_to_table[columns].to_markdown()

    #                 plan._plan.append(
    #                     TrainingPlanItem(
    #                         item_type=TrainingPlanItem.ITEM_TYPE_IS,
    #                         item_group=f"{database}.{schema}",
    #                         item_name=table,
    #                         item_value=doc,
    #                     )
    #                 )

    #     return plan
    def get_training_plan_generic(self, df) -> TrainingPlan:
        """
        Generate a training plan from an information schema dataframe.

        This function breaks up INFORMATION_SCHEMA.COLUMNS into groups of table/column descriptions
        that can be used to pass to the LLM.

        Args:
            df (pd.DataFrame): The dataframe to generate the training plan from.

        Returns:
            TrainingPlan: The training plan.
        """
        # Use new column names from the updated SQL query
        schema_column = "TABLE_SCHEMA"
        table_column = "TABLE_NAME"
        columns_column = "Columns"
        constraints_column = "Constraints"
        foreign_keys_column = "ForeignKeys"
        indexes_column = "Indexes"

        # Ensure all required columns exist
        expected_columns = {schema_column, table_column, columns_column, constraints_column, foreign_keys_column, indexes_column}
        if not expected_columns.issubset(set(df.columns)):
            raise ValueError(
                f"Missing expected columns in DataFrame. Found columns: {df.columns}. "
                "Ensure your query returns TABLE_SCHEMA, TABLE_NAME, Columns, Constraints, ForeignKeys, and Indexes."
            )

        # Initialize training plan
        plan = TrainingPlan([])

        # Iterate through schemas and tables
        for schema in df[schema_column].unique():
            for table in df[df[schema_column] == schema][table_column].unique():
                
                # Filter the DataFrame for the specific table
                df_filtered = df[(df[schema_column] == schema) & (df[table_column] == table)]
                
                # Build training documentation
                doc = f"Schema: {schema}\n"
                doc += f"Table: {table}\n\n"
                doc += f"Columns:\n{df_filtered[columns_column].values[0]}\n\n"
                
                if pd.notna(df_filtered[constraints_column].values[0]):
                    doc += f"Constraints:\n{df_filtered[constraints_column].values[0]}\n\n"
                
                if pd.notna(df_filtered[foreign_keys_column].values[0]):
                    doc += f"Foreign Keys:\n{df_filtered[foreign_keys_column].values[0]}\n\n"
                
                if pd.notna(df_filtered[indexes_column].values[0]):
                    doc += f"Indexes:\n{df_filtered[indexes_column].values[0]}\n\n"

                # Append to training plan
                plan._plan.append(
                    TrainingPlanItem(
                        item_type=TrainingPlanItem.ITEM_TYPE_IS,
                        item_group=schema,
                        item_name=table,
                        item_value=doc,
                    )
                )

        return plan


    def get_training_plan_snowflake(
        self,
        filter_databases: Union[List[str], None] = None,
        filter_schemas: Union[List[str], None] = None,
        include_information_schema: bool = False,
        use_historical_queries: bool = True,
    ) -> TrainingPlan:
        plan = TrainingPlan([])

        if self.run_sql_is_set is False:
            raise ImproperlyConfigured("Please connect to a database first.")

        if use_historical_queries:
            try:
                print("Trying query history")
                df_history = self.run_sql(
                    """ select * from table(information_schema.query_history(result_limit => 5000)) order by start_time"""
                )

                df_history_filtered = df_history.query("ROWS_PRODUCED > 1")
                if filter_databases is not None:
                    mask = (
                        df_history_filtered["QUERY_TEXT"]
                        .str.lower()
                        .apply(
                            lambda x: any(
                                s in x for s in [s.lower() for s in filter_databases]
                            )
                        )
                    )
                    df_history_filtered = df_history_filtered[mask]

                if filter_schemas is not None:
                    mask = (
                        df_history_filtered["QUERY_TEXT"]
                        .str.lower()
                        .apply(
                            lambda x: any(
                                s in x for s in [s.lower() for s in filter_schemas]
                            )
                        )
                    )
                    df_history_filtered = df_history_filtered[mask]

                if len(df_history_filtered) > 10:
                    df_history_filtered = df_history_filtered.sample(10)

                for query in df_history_filtered["QUERY_TEXT"].unique().tolist():
                    plan._plan.append(
                        TrainingPlanItem(
                            item_type=TrainingPlanItem.ITEM_TYPE_SQL,
                            item_group="",
                            item_name=self.generate_question(query),
                            item_value=query,
                        )
                    )

            except Exception as e:
                print(e)

        databases = self._get_databases()

        for database in databases:
            if filter_databases is not None and database not in filter_databases:
                continue

            try:
                df_tables = self._get_information_schema_tables(database=database)

                print(f"Trying INFORMATION_SCHEMA.COLUMNS for {database}")
                df_columns = self.run_sql(
                    f"SELECT * FROM {database}.INFORMATION_SCHEMA.COLUMNS"
                )

                for schema in df_tables["TABLE_SCHEMA"].unique().tolist():
                    if filter_schemas is not None and schema not in filter_schemas:
                        continue

                    if (
                        not include_information_schema
                        and schema == "INFORMATION_SCHEMA"
                    ):
                        continue

                    df_columns_filtered_to_schema = df_columns.query(
                        f"TABLE_SCHEMA == '{schema}'"
                    )

                    try:
                        tables = (
                            df_columns_filtered_to_schema["TABLE_NAME"]
                            .unique()
                            .tolist()
                        )

                        for table in tables:
                            df_columns_filtered_to_table = (
                                df_columns_filtered_to_schema.query(
                                    f"TABLE_NAME == '{table}'"
                                )
                            )
                            doc = f"The following columns are in the {table} table in the {database} database:\n\n"
                            doc += df_columns_filtered_to_table[
                                [
                                    "TABLE_CATALOG",
                                    "TABLE_SCHEMA",
                                    "TABLE_NAME",
                                    "COLUMN_NAME",
                                    "DATA_TYPE",
                                    "COMMENT",
                                ]
                            ].to_markdown()

                            plan._plan.append(
                                TrainingPlanItem(
                                    item_type=TrainingPlanItem.ITEM_TYPE_IS,
                                    item_group=f"{database}.{schema}",
                                    item_name=table,
                                    item_value=doc,
                                )
                            )

                    except Exception as e:
                        print(e)
                        pass
            except Exception as e:
                print(e)

        return plan

    def get_plotly_figure(
        self, plotly_code: str, df: pd.DataFrame, dark_mode: bool = True
    ) -> plotly.graph_objs.Figure:
        """
        **Example:**
        ```python
        fig = vn.get_plotly_figure(
            plotly_code="fig = px.bar(df, x='name', y='salary')",
            df=df
        )
        fig.show()
        ```
        Get a Plotly figure from a dataframe and Plotly code.

        Args:
            df (pd.DataFrame): The dataframe to use.
            plotly_code (str): The Plotly code to use.

        Returns:
            plotly.graph_objs.Figure: The Plotly figure.
        """
        ldict = {"df": df, "px": px, "go": go}
        try:
            exec(plotly_code, globals(), ldict)

            fig = ldict.get("fig", None)
        except Exception as e:
            # Inspect data types
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            categorical_cols = df.select_dtypes(
                include=["object", "category"]
            ).columns.tolist()

            # Decision-making for plot type
            if len(numeric_cols) >= 2:
                # Use the first two numeric columns for a scatter plot
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
            elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                # Use a bar plot if there's one numeric and one categorical column
                fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0])
            elif len(categorical_cols) >= 1 and df[categorical_cols[0]].nunique() < 10:
                # Use a pie chart for categorical data with fewer unique values
                fig = px.pie(df, names=categorical_cols[0])
            else:
                # Default to a simple line plot if above conditions are not met
                fig = px.line(df)

        if fig is None:
            return None

        if dark_mode:
            fig.update_layout(template="plotly_dark")

        return fig

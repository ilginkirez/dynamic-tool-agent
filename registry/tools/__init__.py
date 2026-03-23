"""Unified access to all registered tools."""

from .weather_service import SCHEMA as weather_schema, execute as weather_execute
from .code_executor import SCHEMA as code_executor_schema, execute as code_executor_execute
from .web_search import SCHEMA as web_search_schema, execute as web_search_execute
from .currency_converter import SCHEMA as currency_schema, execute as currency_execute
from .calendar_manager import SCHEMA as calendar_schema, execute as calendar_execute
from .database_query import SCHEMA as database_schema, execute as database_execute
from .document_reader import SCHEMA as document_schema, execute as document_execute
from .translation_service import SCHEMA as translation_schema, execute as translation_execute
from .email_sender import SCHEMA as email_schema, execute as email_execute
from .timer_alarm import SCHEMA as timer_schema, execute as timer_execute


TOOL_LIST = [
    weather_schema,
    code_executor_schema,
    web_search_schema,
    currency_schema,
    calendar_schema,
    database_schema,
    document_schema,
    translation_schema,
    email_schema,
    timer_schema,
]

TOOL_EXECUTORS: dict[str, callable] = {
    weather_schema.name: weather_execute,
    code_executor_schema.name: code_executor_execute,
    web_search_schema.name: web_search_execute,
    currency_schema.name: currency_execute,
    calendar_schema.name: calendar_execute,
    database_schema.name: database_execute,
    document_schema.name: document_execute,
    translation_schema.name: translation_execute,
    email_schema.name: email_execute,
    timer_schema.name: timer_execute,
}

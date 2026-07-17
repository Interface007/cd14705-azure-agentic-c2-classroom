import asyncio
import ast
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.functions import KernelArguments

# -----------------
# Logging Setup
# -----------------
# The logging setup below captures all agent interactions and saves them to 'logs/agent_chat.log'.
# 1. Create a dedicated logger for agent interactions.
agent_logger = logging.getLogger("semantic_kernel.agents")
agent_logger.setLevel(logging.DEBUG)

# 2. Prevent agent logs from propagating to other handlers (like console).
agent_logger.propagate = False

# 3. Create a file handler to write to 'agent_chat.log' in write mode.
Path("logs").mkdir(parents=True, exist_ok=True)
agent_chat_handler = logging.FileHandler("logs/agent_chat.log", mode="w", encoding="utf-8")
agent_chat_handler.setLevel(logging.DEBUG)

# 4. Create a minimal formatter to log only the message content.
chat_formatter = logging.Formatter("%(asctime)s - %(name)s:%(message)s")
agent_chat_handler.setFormatter(chat_formatter)

# 5. Add the dedicated file handler to the agent logger.
agent_logger.addHandler(agent_chat_handler)

# 5.a Structured trace logger for workflow/accountability events.
trace_logger = logging.getLogger("workflow.trace")
trace_logger.setLevel(logging.INFO)
trace_logger.propagate = False

trace_handler = logging.FileHandler("logs/trace.log", mode="w", encoding="utf-8")
trace_handler.setLevel(logging.INFO)
trace_handler.setFormatter(logging.Formatter("%(message)s"))
trace_logger.addHandler(trace_handler)


def trace_event(event: str, **fields):
    """Writes one JSON event per line to logs/trace.log."""
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    trace_logger.info(json.dumps(payload, ensure_ascii=True, default=str))

# 6. Function to log agent messages
def log_agent_message(content):
    try:
        agent_logger.info(f"Agent: {content.role} - {content.name or '*'}: {content.content}")
        trace_event(
            "agent_message",
            role=str(content.role),
            agent_name=content.name or "*",
            content_length=len(content.content or ""),
        )
    except Exception:
        agent_logger.exception("Failed to write agent message to log")
        trace_event("agent_message_log_error")

# -----------------
# Environment Setup
# -----------------
load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("API_KEY")
BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("BASE_URL")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or os.getenv("API_VERSION") or "2024-12-01-preview"
DEPLOYMENT_NAME = (
    os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    or os.getenv("DEPLOYMENT_NAME")
)

if not API_KEY or not BASE_URL or not DEPLOYMENT_NAME:
    raise ValueError(
        "add Missing Azure OpenAI as env-variable AZURE_OPENAI_API_KEY, "
        "AZURE_OPENAI_ENDPOINT (or BASE_URL), and AZURE_OPENAI_CHAT_DEPLOYMENT_NAME "
        "(or AZURE_OPENAI_DEPLOYMENT_NAME/DEPLOYMENT_NAME)."
    )

trace_event(
    "environment_config_loaded",
    has_api_key=bool(API_KEY),
    has_base_url=bool(BASE_URL),
    has_deployment_name=bool(DEPLOYMENT_NAME),
    api_version=API_VERSION,
)


# -----------------
# Kernel and Chat Service
# -----------------
kernel = Kernel()
chat_service = AzureChatCompletion(
    service_id="default",
    deployment_name=DEPLOYMENT_NAME,
    api_key=API_KEY,
    endpoint=BASE_URL,
    api_version=API_VERSION,
)
kernel.add_service(chat_service)
trace_event("chat_service_initialized", service_id="default", deployment_name=DEPLOYMENT_NAME)


# -----------------
# Helper Functions
# -----------------
def _load_text_lines(base_dir: str, file_name: str) -> list[str]:
    file_path = Path(base_dir) / file_name
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_quality_instructions(file_path):
    """
    Loads instructional text from a file within the 'specs' directory.

    This function constructs the full path to the file, reads its content,
    and processes it into a list of non-empty, stripped lines.

    Args:
        file_path (str): The name of the file in the 'specs' directory.

    Returns:
        list[str]: A list of strings, where each string is a line of instruction.
                   Returns an empty list if the file does not exist.
    """
    return _load_text_lines("specs", file_path)

def load_reports_instructions(file_path):
    """
    Loads report generation instructions from a file within the 'specs' directory.

    Args:
        file_path (str): The name of the file in the 'specs' directory.

    Returns:
        list[str]: A list of strings for building the report. Returns an
                   empty list if the file does not exist.
    """
    return _load_text_lines("specs", file_path)

def load_logs(file_path):
    """
    Loads agent interaction logs from a file within the 'logs' directory.

    Args:
        file_path (str): The name of the log file in the 'logs' directory.

    Returns:
        list[str]: A list of log entries. Returns an empty list if the file
                   does not exist.
    """
    return _load_text_lines("logs", file_path)

def get_csv_name():
    """
    Interactively prompts the user to select a CSV file from the 'data' directory.

    It lists all available .csv files and asks for a numerical selection.

    Returns:
        str: The relative path to the selected CSV file (e.g., 'data/my_file.csv').
    """
    csv_files = sorted(Path("data").glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the data directory.")

    print("Available CSV files:")
    for index, csv_file in enumerate(csv_files, start=1):
        print(f"{index}. {csv_file.name}")

    while True:
        raw_choice = input("Select a file number: ").strip()
        if not raw_choice.isdigit():
            print("Please enter a valid number.")
            continue

        choice = int(raw_choice)
        if 1 <= choice <= len(csv_files):
            return str(csv_files[choice - 1])

        print("Selection out of range. Try again.")

def load_csv_file(file_path):
    """
    Reads a CSV file and converts its entire content into a single string.

    The CSV data is flattened into a list and then joined by ', '.

    Args:
        file_path (str): The path to the CSV file to load.

    Returns:
        str: A single string containing all the data from the CSV file.
    """
    frame = pd.read_csv(file_path)
    flattened = list(frame.columns.astype(str)) + frame.astype(str).to_numpy().flatten().tolist()
    return ", ".join(flattened)

class PythonExecutor:
    """
    A safe executor for dynamically generated Python code strings.

    This class is designed to run code provided by an AI agent in a controlled
    manner. It includes a retry mechanism and captures execution errors.
    """
    def __init__(self, max_attempts=3, timeout_seconds=20):
        self.max_attempts = max_attempts
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _validate_code_safety(code: str) -> None:
        """Blocks unsafe constructs before execution - got from a previous project"""
        tree = ast.parse(code, mode="exec")

        blocked_names = {
            "os",
            "sys",
            "subprocess",
            "socket",
            "shutil",
            "pathlib",
            "builtins",
            "__builtins__",
        }
        blocked_calls = {
            "eval",
            "exec",
            "compile",
            "open",
            "input",
            "__import__",
            "globals",
            "locals",
            "vars",
        }
        allowed_import_roots = {"pandas", "matplotlib"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in allowed_import_roots:
                        raise ValueError(f"Unsafe import blocked: {alias.name}")

            if isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root not in allowed_import_roots:
                    raise ValueError(f"Unsafe import blocked: {node.module}")

            if isinstance(node, ast.Name) and node.id in blocked_names:
                raise ValueError(f"Unsafe symbol blocked: {node.id}")

            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in blocked_calls:
                raise ValueError(f"Unsafe function blocked: {node.func.id}")

            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                raise ValueError("Dunder attribute access is blocked")

    def _run_once(self, code: str) -> tuple[bool, str | None]:
        """Runs code in an isolated interpreter process."""
        self._validate_code_safety(code)

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            result = subprocess.run(
                [sys.executable, "-I", tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )

            if result.returncode == 0:
                return True, None

            details = (result.stderr or "").strip() or (result.stdout or "").strip()
            return False, details or f"Execution failed with exit code {result.returncode}"
        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {self.timeout_seconds} seconds"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    async def run(
        self,
        code: str,
        repair_callback: Callable[[int, str, str], Awaitable[str]] | None = None,
    ) -> tuple[bool, str | None, str]:
        """
        Executes code with retries and optional async repair callback.

        Args:
            code (str): The Python code to execute.
            repair_callback: Optional async callback to regenerate code on failure.

        Returns:
            tuple[bool, str | None, str]: A tuple containing:
                - A boolean indicating if the execution was successful.
                - The error traceback as a string if an exception occurred,
                  otherwise None.
                - The last attempted code (possibly repaired).
        """
        current_code = code
        last_error: str | None = None

        for attempt in range(1, self.max_attempts + 1):
            trace_event("code_execution_attempt_started", attempt=attempt)
            try:
                ok, err = self._run_once(current_code)
            except Exception:
                ok = False
                err = traceback.format_exc()
            if ok:
                trace_event("code_execution_attempt_succeeded", attempt=attempt)
                return True, None, current_code

            last_error = err or "Unknown execution error"
            trace_event("code_execution_attempt_failed", attempt=attempt, error=last_error)

            if attempt >= self.max_attempts or repair_callback is None:
                break

            current_code = await repair_callback(attempt, last_error, current_code)

        return False, last_error, current_code

def save_final_report(report, path='artifacts/final_report.md'):
    """
    Saves the generated final report to a markdown file.

    Args:
        report (str): The content of the report to be saved.
        path (str, optional): The file path for the saved report.
                              Defaults to 'artifacts/final_report.md'.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")


def extract_code_block(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


async def run_group_chat(chat: AgentGroupChat, prompt: str, final_message_only: bool = False) -> str:
    agent_names = [agent.name for agent in chat.agents]
    trace_event(
        "group_chat_started",
        agents=agent_names,
        prompt_length=len(prompt),
    )

    await chat.reset()
    await chat.add_chat_message(prompt)
    trace_event("group_chat_prompt_added", agents=agent_names)

    messages: list[str] = []
    last_message = ""
    async for content in chat.invoke():
        log_agent_message(content)
        if content.content:
            messages.append(content.content)
            last_message = content.content

    combined = last_message if final_message_only else "\n\n".join(messages)
    trace_event(
        "group_chat_completed",
        agents=agent_names,
        message_count=len(messages),
        output_length=len(combined),
    )
    return combined


# -----------------
# Agent Instructions
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 1. Complete the AGENT_CONFIG with detailed prompts for each agent.
data_quality_instructions = ''.join(load_quality_instructions("Data_Quality_Instructions.txt"))
report_instructions = ''.join(load_reports_instructions("Report_Instructions.txt"))

AGENT_CONFIG = {
    "PythonExecutorAgent": """
Role: Code Generation.
Behavior: Write and execute Python code for data visualization.
Rules:
- Return ONLY executable Python code in a single markdown code block.
- Use pandas and matplotlib only.
- Save the plot image as a file withe the full path artifacts/data_visualization.png.
- DO NOT include explanations outside the code.
""".strip(),
    "DataCleaning": """
Role: Data Cleaning.
Behavior: Identify and remove outliers to prepare a clean dataset.
Output requirements:
- Return ONLY valid JSON (no markdown, no prose).
- Provide these keys exactly:
  - detected_outliers: array of objects with Date and Website_Visits
  - cleaned_data_rows: array of objects with Date and Website_Visits
  - removed_rows: array of objects with Date and Website_Visits
  - assumptions: array of strings
""".strip(),
    "DataStatistics": """
Role: Statistical Analysis.
Behavior: Generate key descriptive statistics from the cleaned data.
Rules:
- Calculate statistics from the cleaned data only.
- Do not extrapolate additional data.
- Include mean, median, std, min, max and short interpretation.
- Return ONLY valid JSON (no markdown, no prose) with a `statistics` object.
""".strip(),
    "AnalysisChecker": (
        "Role: Validation. Behavior: Verify that the analysis meets predefined quality instructions.\n"
        "Validate cleaning/statistics output with these rules:\n"
        f"{data_quality_instructions}\n"
        "Output requirements:\n"
        "- Return ONLY ONE valid JSON object (no markdown).\n"
        "- Merge cleaning + statistics + validation into this final schema:\n"
        "{\n"
        "  \"approved\": boolean,\n"
        "  \"status\": \"Approved\" | \"Failed\",\n"
        "  \"detected_outliers\": [{\"Date\": string, \"Website_Visits\": number}],\n"
        "  \"cleaned_data_rows\": [{\"Date\": string, \"Website_Visits\": number}],\n"
        "  \"removed_rows\": [{\"Date\": string, \"Website_Visits\": number}],\n"
        "  \"assumptions\": [string],\n"
        "  \"statistics\": {\"count\": number, \"mean\": number, \"median\": number, \"std\": number, \"min\": number, \"max\": number},\n"
        "  \"validation_notes\": [string]\n"
        "}\n"
        "- Set status to \"Approved\" only if all checks pass."
    ),
    "ReportGenerator": (
        "Role: Reporting. Behavior: Synthesize logs and artifacts into a structured markdown report.\n"
        "Create a final markdown report from analysis artifacts using this template:\n"
        f"{report_instructions}"
    ),
    "ReportChecker": """
Role: Report Validation.
Behavior: Audit the generated report for accuracy and completeness.
Review the generated markdown report.
If fully complete and accurate, reply with: 'Approved'
Otherwise, list fixes that need to be applied.
""".strip(),
}


# -----------------
# Agent Factory
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 2. Implement the agent factory function.
def create_agent(name, instructions, service, settings=None):
    """Factory function to create a new ChatCompletionAgent."""
    arguments = KernelArguments(settings=settings) if settings else None
    agent = ChatCompletionAgent(
        name=name,
        instructions=instructions,
        service=service,
        kernel=kernel,
        arguments=arguments,
    )
    trace_event(
        "agent_created",
        agent_name=name,
        has_settings=bool(settings),
        temperature=getattr(settings, "temperature", None) if settings else None,
    )
    return agent


# -----------------
# Termination Strategy
# -----------------
# A custom termination strategy that stops after user approval.
class ApprovalTerminationStrategy(TerminationStrategy):
    """A custom termination strategy that stops after user approval."""
    async def should_agent_terminate(self, agent, history):
        if history and getattr(history[-1], "content", None):
            if "approved" in history[-1].content.lower():
                return True

        if len(history) >= self.maximum_iterations:
            return True

        return False


# -----------------
# Agent Instantiation
# -----------------
python_agent = create_agent(
    "PythonExecutorAgent",
    AGENT_CONFIG["PythonExecutorAgent"],
    chat_service,
    OpenAIChatPromptExecutionSettings(temperature=0.1),
)
cleaning_agent = create_agent(
    "DataCleaning",
    AGENT_CONFIG["DataCleaning"],
    chat_service,
    OpenAIChatPromptExecutionSettings(temperature=0.7),
)
stats_agent = create_agent(
    "DataStatistics",
    AGENT_CONFIG["DataStatistics"],
    chat_service,
    OpenAIChatPromptExecutionSettings(temperature=0.5),
)
checker_agent = create_agent(
    "AnalysisChecker",
    AGENT_CONFIG["AnalysisChecker"],
    chat_service,
    OpenAIChatPromptExecutionSettings(temperature=0.2),
)
report_agent = create_agent(
    "ReportGenerator",
    AGENT_CONFIG["ReportGenerator"],
    chat_service,
    OpenAIChatPromptExecutionSettings(temperature=1.0),
)
report_checker_agent = create_agent(
    "ReportChecker",
    AGENT_CONFIG["ReportChecker"],
    chat_service,
    OpenAIChatPromptExecutionSettings(temperature=0.2),
)


# -----------------
# Group Chats
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 4. Create the three agent group chats.
analysis_chat = AgentGroupChat(
    agents=[cleaning_agent, stats_agent, checker_agent],
    termination_strategy=ApprovalTerminationStrategy(maximum_iterations=6, automatic_reset=True),
)
code_chat = AgentGroupChat(
    agents=[python_agent],
    termination_strategy=ApprovalTerminationStrategy(maximum_iterations=4, automatic_reset=True),
)
report_chat = AgentGroupChat(
    agents=[report_agent, report_checker_agent],
    termination_strategy=ApprovalTerminationStrategy(maximum_iterations=4, automatic_reset=True),
)


# -----------------
# Main Workflow
# -----------------
# <TODO: Step 6 - Orchestrate the Main Workflow>
# Implement the main workflow logic, following the sequence described in the instructions.
async def main():
    """The main entry point for the agentic workflow."""
    trace_event("workflow_started")
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    trace_event("directory_ready", path="artifacts")

    # 1. Load the CSV data.
    csv_path = get_csv_name()
    dataset_tag = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(csv_path).stem)
    analysis_output_path = Path("artifacts") / f"analysis_output_{dataset_tag}.json"
    cleaned_data_path = Path("artifacts") / f"cleaned_data_{dataset_tag}.json"
    visualization_image_path = Path("artifacts") / f"data_visualization_{dataset_tag}.png"
    visualization_script_path = Path("artifacts") / f"visualization_{dataset_tag}.py"
    final_report_path = Path("artifacts") / f"final_report_{dataset_tag}.md"
    trace_event("csv_selected", csv_path=csv_path)
    csv_text = load_csv_file(csv_path)
    trace_event("csv_loaded", csv_path=csv_path, csv_text_length=len(csv_text))

    # 2. Invoke the analysis chat.
    analysis_prompt = (
        "Analyze, clean, compute descriptive stats, and validate this CSV data. "
        "The FINAL output must be ONLY one valid JSON object following the checker schema. "
        "Do not return markdown.\n\n"
        f"CSV path: {csv_path}\n"
        f"CSV data:\n{csv_text}"
    )
    analysis_output = await run_group_chat(analysis_chat, analysis_prompt, final_message_only=True)
    analysis_output_path.write_text(analysis_output, encoding="utf-8")
    trace_event(
        "analysis_output_saved",
        path=str(analysis_output_path),
        output_length=len(analysis_output),
    )

    print("\n=== Analysis Result ===")
    print(analysis_output)
    print("=== End Analysis Result ===\n")

    # 3. Get human approval.
    approval = input("Approve analysis to continue? (yes/no): ").strip().lower()
    trace_event("human_approval_received", decision=approval)
    if approval != "yes":
        print("Stopped by user before visualization/report generation.")
        trace_event("workflow_stopped_by_user")
        return

    # 4. Save the cleaned data as JSON.
    try:
        cleaned_data_payload = json.loads(analysis_output)
    except json.JSONDecodeError as ex:
        trace_event("cleaned_data_json_parse_failed", error=str(ex))
        raise ValueError("analysis_output is not valid JSON. Update analysis prompts/termination behavior.") from ex

    cleaned_data_path.write_text(
        json.dumps(cleaned_data_payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    trace_event("cleaned_data_saved", path=str(cleaned_data_path))

    # 5. Invoke the code chat to generate and execute visualization code.
    code_prompt = (
        "Generate Python code to visualize the cleaned dataset summary from this analysis output. "
        f"Save figure to {visualization_image_path.as_posix()}.\n\n"
        f"Analysis output:\n{analysis_output}"
    )
    generated_code_response = await run_group_chat(code_chat, code_prompt)
    generated_code = extract_code_block(generated_code_response)
    trace_event("code_generated", code_length=len(generated_code))

    executor = PythonExecutor(max_attempts=3)

    # 6. Execute the code in a retry loop.
    async def repair_generated_code(attempt: int, execution_error: str, current_code: str) -> str:
        repair_prompt = (
            "Fix the Python script. Return only corrected Python code.\n\n"
            f"Attempt: {attempt}\n"
            f"Error:\n{execution_error}\n\n"
            f"Current code:\n```python\n{current_code}\n```"
        )
        generated_code_response = await run_group_chat(code_chat, repair_prompt)
        repaired_code = extract_code_block(generated_code_response)
        trace_event("code_regenerated", attempt=attempt, code_length=len(repaired_code))
        return repaired_code

    execution_ok, execution_error, generated_code = await executor.run(
        generated_code,
        repair_callback=repair_generated_code,
    )

    # 7. Save the working visualization script.
    visualization_script_path.write_text(generated_code, encoding="utf-8")
    trace_event("visualization_script_saved", path=str(visualization_script_path))

    # 7.a Check if execution was successful after retries - we want the script even if it fails to check for the error.
    if not execution_ok:
        trace_event("workflow_failed", reason="visualization_code_failed")
        raise RuntimeError(f"Visualization code failed after retries:\n{execution_error}")

    # 8. Invoke the report chat to generate the final report.
    report_prompt = (
        "Create the final report in markdown using the template instructions.\n\n"
        f"Analysis output:\n{analysis_output}\n\n"
        f"Execution logs:\n{os.linesep.join(load_logs('agent_chat.log'))}"
    )
    report_output = await run_group_chat(report_chat, report_prompt)
    trace_event("report_generated", output_length=len(report_output))

    # 9. Save the final report.
    save_final_report(report_output, path=str(final_report_path))
    trace_event("final_report_saved", path=str(final_report_path))
    trace_event("workflow_completed")
    print(f"Done - report saved to {final_report_path.as_posix()}")


# -----------------
# Main Execution
# -----------------
if __name__ == "__main__":
    asyncio.run(main())
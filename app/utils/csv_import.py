from io import StringIO
from typing import List, Tuple

import pandas as pd
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, UploadFile
from odmantic import AIOEngine

from app.models.task import TaskStatus, TaskType, Task, ImportCSVResponse, SourceType, EXPECTED_HEADERS
from app.core.exceptions import raise_invalid_id_exception

CANDIDATE_SEPS = [",", ";", "\t"]


def detect_type_and_sep(first_line: str) -> (SourceType, str):
    """Detect the CSV separator by analyzing the first non-empty line.

    Args:
        first_line (str): The first line of the document

    Returns:
        str: The detected separator (e.g., ',', ';', '\t') or ',' as default.

    Raises:
        HTTPException: If no separator can be determined.
    """
    try:
        for sep in CANDIDATE_SEPS:
            cols = [c.strip() for c in first_line.split(sep)]
            if set(EXPECTED_HEADERS[SourceType.JIRA]).issubset(cols):
                return SourceType.JIRA, sep
            if set(EXPECTED_HEADERS[SourceType.GITLAB]).issubset(cols):
                return SourceType.GITLAB, sep
        raise ValueError("Couldn't find expected headers in file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error detecting CSV separator: {str(e)}")


def analyse_csv(content: bytes) -> (pd.DataFrame, SourceType):
    lines = bytes_to_str(content)
    source_type, separator = detect_type_and_sep(lines[0])
    return parse_csv(lines, separator), source_type


def bytes_to_str(content: bytes) -> list[str]:
    """Clean the CSV content by removing surrounding quotes and trailing commas, and split
       the content into lists of str

    Args:
        content (bytes): The raw bytes of the CSV file.

    Returns:
        list[str]: The cleaned CSV content

    Raises:
        HTTPException: If the input is empty or contains no valid lines.
    """
    try:
        text = content.decode('utf-8', errors='ignore')
        if not text.strip():
            raise ValueError("Empty CSV content")

        lines = text.splitlines()
    except Exception as e:
        # logger.error(f"Error cleaning CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error cleaning CSV: {str(e)}")

    else:
        lines = [l.replace("\r\n", "\n").replace("\r", "\n").replace("\"", "") for l in lines]
        lines = [l.lstrip("\ufeff") for l in lines]
        return lines


def validate_file_and_ids(file: UploadFile, sprint_id: str, project_id: str) -> Tuple[ObjectId, ObjectId] or None:
    """Validate file extension and convert sprint/project IDs to ObjectId.

    Args:
        file (UploadFile): The uploaded CSV file to validate.
        sprint_id (str): The sprint ID as a string to convert to ObjectId.
        project_id (str): The project ID as a string to convert to ObjectId.

    Returns:
        Tuple[ObjectId, ObjectId]: A tuple containing the validated sprint and project ObjectIds.

    Raises:
        HTTPException: If the file is not a CSV or if the IDs are invalid.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    try:
        return ObjectId(sprint_id), ObjectId(project_id)
    except InvalidId:
        raise_invalid_id_exception("Sprint or Project", f"{sprint_id} or {project_id}")


def parse_csv(lines: list[str], separator: str) -> pd.DataFrame:
    """Parse CSV content into a pandas DataFrame.

    Args:
        lines (list[str]): The content of the csv file split in lines
        separator (str): The separator used in the CSV (e.g., ',' or ';').

    Returns:
        pd.DataFrame: The parsed DataFrame containing CSV data.

    Raises:
        HTTPException: If parsing fails or the CSV is empty.
    """
    lines = "\n".join(lines)
    try:
        df = pd.read_csv(StringIO(lines), delimiter=separator)
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")  # pragma: no cover
        df = df.replace('""', '')
        return df
    except Exception as e:
        # logger.error(f"Error parsing CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")


def validate_headers(df: pd.DataFrame, expected_headers: List[str]) -> pd.DataFrame:
    """Validate that the DataFrame contains all expected headers and filter to those headers.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        expected_headers (List[str]): The list of required column headers.

    Returns:
        pd.DataFrame: The DataFrame filtered to only the expected headers.

    Raises:
        HTTPException: If any expected headers are missing or cannot be selected.
    """
    actual_headers = df.columns.tolist()
    missing_headers = [h for h in expected_headers if h not in actual_headers]
    if missing_headers:
        missing_cols = ", ".join(f"'{h}'" for h in missing_headers)
        available_cols = ", ".join(f"'{h}'" for h in actual_headers)
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing_cols}. Available columns: {available_cols}"
        )
    try:
        return df[expected_headers]
    except KeyError as e:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Column '{str(e)}' missing from CSV")  # pragma: no cover


def map_csv_to_tasks(df: pd.DataFrame, db_mapping: dict, sprint_id: ObjectId, project_id: ObjectId) -> pd.DataFrame:
    """Map a CSV DataFrame to a format compatible with the Task model.

    Args:
        df (pd.DataFrame): The DataFrame containing CSV data.
        db_mapping (dict): A mapping of CSV headers to Task model field names.
        sprint_id (ObjectId): The sprint ID to assign to tasks.
        project_id (ObjectId): The project ID to assign to tasks.

    Returns:
        pd.DataFrame: A DataFrame with mapped columns and filtered valid rows.

    Raises:
        HTTPException: If mapping fails due to data issues.
    """
    try:
        mapped_df = df.rename(columns={h: db_mapping[h] for h in df.columns if h in db_mapping})
        mapped_df['key'] = mapped_df['key'].astype(str)

        status_mapping = {
            'open': 'OPEN',
            'to do': 'TODO',
            'todo': 'TODO',
            'in progress': 'PROG',
            'done': 'DONE',
            'ready for validation': 'REV',
            'under investigation': 'INVEST',
            'waiting for customer': 'CUST',
            'standby': 'STANDBY',
            'cancelled': 'CANCEL',
            'postponed': 'POST'
        }

        # Type mapping using enum IDs (uppercase versions)
        type_mapping = {
            'bug': 'BUG',
            'task': 'TASK',
            'story': 'STORY',
            'epic': 'EPIC',
            'doc': 'DOC',
            'test': 'TEST',
            'deliverable': 'DELIVERABLE'
        }

        if 'type' in mapped_df.columns:
            mapped_df['type'] = mapped_df['type'].apply(
                lambda x: type_mapping.get(str(x).lower(), 'TASK') if pd.notna(x) else 'TASK'
            )
        else:
            mapped_df['type'] = 'TASK'

        if 'storyPoints' in mapped_df.columns:
            mapped_df['storyPoints'] = pd.to_numeric(mapped_df['storyPoints'], errors='coerce').fillna(0)
        else:
            mapped_df['storyPoints'] = 0

        # if 'assignee' in mapped_df.columns:
        #     mapped_df['assignee'] = mapped_df['assignee'].apply(lambda x: x if isinstance(x, str) else "")
        # else:
        #     mapped_df['assignee'] = [[] for _ in range(len(mapped_df))]
        mapped_df['assignee'] = [[] for _ in range(len(mapped_df))]

        # Handle status column: if missing, fill with To do; otherwise, map values
        if 'status' in mapped_df.columns:
            mapped_df['status'] = mapped_df['status'].apply(
                lambda x: status_mapping.get(str(x).lower(), 'TODO') if pd.notna(x) else 'TODO'
            )
        else:
            mapped_df['status'] = 'TODO'

        mapped_df['sprintId'] = sprint_id
        mapped_df['projectId'] = project_id

        return mapped_df[~mapped_df['key'].isna() & ~mapped_df['summary'].isna()]
    except Exception as e:  # pragma: no cover
        # logger.error(f"Error mapping data: {str(e)}") # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Error mapping CSV data: {str(e)}")  # pragma: no cover


async def process_tasks_and_duplicates(mapped_df: pd.DataFrame, sprint: "Sprint", engine: "AIOEngine") -> Tuple[
    List[Task], int, List[str], pd.DataFrame]:
    """Process tasks, handle duplicates, and save them to the database.

    Args:
        mapped_df (pd.DataFrame): The DataFrame with mapped task data.
        sprint (Task): The sprint object to update with task IDs.
        engine (AIOEngine): The database engine for querying and saving.

    Returns:
        Tuple[List[Task], int, List[str], pd.DataFrame]: A tuple containing:
            - List of created Task objects.
            - Total count of tasks in the database.
            - List of duplicate keys.
            - DataFrame of invalid rows.

    Raises:
        HTTPException: If no valid rows remain or task creation fails.
    """
    invalid_rows = mapped_df[mapped_df['key'].isna() | mapped_df['summary'].isna()]
    if mapped_df.empty:
        raise HTTPException(status_code=400, detail="No valid rows after filtering")

    existing_tasks = await engine.find(Task, Task.sprintId == mapped_df['sprintId'].iloc[0], Task.is_deleted == False)
    existing_keys = {task.key for task in existing_tasks}
    all_keys = mapped_df['key'].tolist()
    duplicate_keys = [key for key in all_keys if key in existing_keys]

    new_tasks_df = mapped_df[~mapped_df['key'].isin(existing_keys)]
    try:
        # Convert enum string IDs to actual enum values before creating Task objects
        tasks = []
        for _, row in new_tasks_df.iterrows():
            task_dict = row.to_dict()

            # Convert status string to enum
            if 'status' in task_dict:
                task_dict['status'] = TaskStatus(task_dict['status'])

            # Convert type string to enum
            if 'type' in task_dict:
                task_dict['type'] = TaskType(task_dict['type'])

            tasks.append(Task(**task_dict))
    except Exception as e:
        # logger.error(f"Error creating task objects: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating tasks from CSV: {str(e)}")

    if tasks:
        await engine.save_all(tasks)
        sprint.task.extend([task.id for task in tasks])
        await engine.save(sprint)

    total_count = await engine.count(Task, Task.is_deleted == False)
    return tasks, total_count, duplicate_keys, invalid_rows


def build_response(tasks: List[Task], duplicate_keys: List[str],
                   invalid_rows: pd.DataFrame) -> ImportCSVResponse:
    """Build the response object for the CSV import operation.

    Args:
        tasks (List[Task]): The list of successfully imported tasks.
        duplicate_keys (List[str]): The list of keys that were duplicates.
        invalid_rows (pd.DataFrame): The DataFrame of rows with missing mandatory fields.

    Returns:
        ImportCSVResponse: The response object with import details.
    """
    invalid_row_count = len(invalid_rows)
    invalid_row_numbers = [idx + 2 for idx in invalid_rows.index] if invalid_row_count > 0 else []
    duplicate_count = len(duplicate_keys)

    message = f"Successfully imported {len(tasks)} tasks"
    if invalid_row_count > 0:
        row_msg = f"row index number: {', '.join(map(str, invalid_row_numbers))}" if len(
            invalid_row_numbers) <= 10 else f"{invalid_row_count} rows"
        message += f". Skipped {row_msg} with missing key or summary"
    if duplicate_count > 0:
        message += f". {duplicate_count} tasks were not added because they already exist in the sprint"

    # logger.info((f"Imported {len(tasks) - duplicate_count} tasks", f"in sprint {str(tasks[0].sprintId)}." if len(tasks) > 0 else "."))

    return ImportCSVResponse(
        status=True,
        msg=message
    )

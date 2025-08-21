from fastapi import HTTPException


def raise_invalid_id_exception(object_type: str = "", object_id: str = "") -> None:
    """
    Raise an HTTPException for an invalid ID format.

    Args:
        object_type (str): The name of the type of object that should raise an exception.
        object_id (str): ID that raised an exception.

    Raises:
        HTTPException: A 400 Bad Request error with the provided detail message.
    """
    #logger.error(f"Invalid id ({object_id}) for object {object_type}.")
    raise HTTPException(status_code=400, detail=f"Invalid id ({object_id}) for object {object_type}")


def raise_not_found_exception(object_type: str = "", object_id: str = "") -> None:
    """
    Raise an HTTPException for a resource not found.

    Args:
        object_type (str): The name of the type of object that was not found.
        object_id (str): The ID that could not be found.

    Raises:
        HTTPException: A 404 Not Found error indicating the object was not found.
    """
    #logger.error(f"{object_type} {object_id} not found.")
    raise HTTPException(status_code=404, detail=f"{object_type} {object_id} not found")

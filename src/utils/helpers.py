# src/utils/helpers.py
# Common utility functions

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Basic sanitization - extend as needed
    return text.strip()

def format_response(content: str, metadata: dict = None) -> dict:
    """Format response with metadata"""
    response = {"content": content}
    if metadata:
        response["metadata"] = metadata
    return response
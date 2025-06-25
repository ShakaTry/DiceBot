def handler(request):
    """Ultra simple Vercel function for testing."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "Hello from ultra-simple function", "status": "working"}',
    }

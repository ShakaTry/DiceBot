import json


def handler(request):
    response_data = {"message": "Working endpoint!", "status": "ok", "vercel": True}

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(response_data),
    }

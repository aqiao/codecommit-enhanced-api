import json


def succeeded_with_data(data):
    result = {"succeeded": True, "payload": data, "message": None}
    return json.dumps(result, ensure_ascii=False, indent=2)


def succeeded_without_data(message):
    result = {"succeeded": True, "payload": None, "message": message}
    return json.dumps(result, ensure_ascii=False, indent=2)


def failed_without_data(message):
    result = {"succeeded": False, "payload": None, "message": message}
    return json.dumps(result, ensure_ascii=False, indent=2)


def failed_with_data(data, message):
    result = {"succeeded": False, "payload": data, "message": message}
    return json.dumps(result, ensure_ascii=False, indent=2)

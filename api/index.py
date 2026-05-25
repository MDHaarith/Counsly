def handler(event, context):
    import sys, os, json
    paths = {
        "cwd": os.getcwd(),
        "file_dir": os.path.dirname(os.path.abspath(__file__)),
        "sys_path": sys.path[:5],
        "cwd_contents": os.listdir(".")[:20],
    }
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(paths, default=str),
    }
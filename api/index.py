import json

def app(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    
    # Check if we are in /api/health
    path = environ.get('PATH_INFO', '')
    
    if 'health' in path:
        response = {"status": "ultra_fast_v214", "msg": "Zero Frameworks Used"}
        return [json.dumps(response).encode('utf-8')]
        
    response = {"message": f"Raw handler reached at {path}. System ready."}
    return [json.dumps(response).encode('utf-8')]

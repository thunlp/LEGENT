
def PathToUser():
    return {
        "api": "PathToUser",
        "args": ""
    }

def PathToObject(object_index):
    return {
        "api": "PathToObject",
        "args": str(object_index)
    }
    
def ObjectInView(object_index):
    return {
        "api": "ObjectInView",
        "args": str(object_index)
    }
    
def SaveTopDownView(absolute_path):
    return {
        "api": "SaveTopDownView",
        "args": absolute_path
    }
    
import json


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
    
def TakePhoto(photo_path, position, rotation, width=4096, height=4096, vertical_field_of_view=90):
    return {
        "api": "TakePhoto",
        "args": json.dumps({
            "position": position,
            "rotation": rotation,
            "width": width,
            "height": height,
            "vertical_field_of_view": vertical_field_of_view,
            "path": photo_path,
            "rendering_type": ""
        })
    }
    
def TakePhotoWithVisiblityInfo(photo_path, position, rotation, width=4096, height=4096, vertical_field_of_view=90, rendering_type=""):
    return {
        "api": "TakePhotoWithVisiblityInfo",
        "args": json.dumps({
            "position": position,
            "rotation": rotation,
            "width": width,
            "height": height,
            "vertical_field_of_view": vertical_field_of_view,
            "path": photo_path,
            "rendering_type": rendering_type
        })
    }
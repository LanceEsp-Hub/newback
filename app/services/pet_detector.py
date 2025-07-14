# import io
# from fastapi import UploadFile, HTTPException
# from PIL import Image
# import torch
# import numpy as np

# # Initialize model (YOLOv5 is more accurate than MobileNet for pet detection)
# try:
#     model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
# except Exception as e:
#     raise RuntimeError(f"Failed to load model: {str(e)}")

# async def verify_pet_image(file: UploadFile):
#     try:
#         # Read image file
#         contents = await file.read()
#         image = Image.open(io.BytesIO(contents))
        
#         # Convert to RGB if needed
#         if image.mode != 'RGB':
#             image = image.convert('RGB')
        
#         # Run detection
#         results = model(image)
#         detections = results.pandas().xyxy[0]
        
#         # COCO class IDs: 15=cat, 16=dog
#         has_cat = any((detections['class'] == 15) & (detections['confidence'] > 0.3))
#         has_dog = any((detections['class'] == 16) & (detections['confidence'] > 0.3))
        
#         # Get all detected objects for error reporting
#         detected_objects = detections['name'].unique().tolist() if not detections.empty else []
#         max_confidence = float(detections['confidence'].max()) if not detections.empty else 0.0
        
#         return {
#             'is_valid': has_cat or has_dog,
#             'is_cat': has_cat,
#             'is_dog': has_dog,
#             'confidence': max_confidence,
#             'detected_objects': detected_objects
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "message": f"Image processing failed: {str(e)}",
#                 "type": "processing_error"
#             }
#         )



import io
from fastapi import UploadFile, HTTPException
from PIL import Image
import torch
import numpy as np

# Model will be initialized on first use
model = None

def load_model():
    global model
    if model is None:
        try:
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            model.to('cpu')  # Force CPU to avoid Render GPU errors
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

async def verify_pet_image(file: UploadFile):
    try:
        # Lazy-load the model
        load_model()

        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Run detection
        results = model(image)
        detections = results.pandas().xyxy[0]
        
        # COCO class IDs: 15=cat, 16=dog
        has_cat = any((detections['class'] == 15) & (detections['confidence'] > 0.3))
        has_dog = any((detections['class'] == 16) & (detections['confidence'] > 0.3))
        
        # Get all detected objects for error reporting
        detected_objects = detections['name'].unique().tolist() if not detections.empty else []
        max_confidence = float(detections['confidence'].max()) if not detections.empty else 0.0
        
        return {
            'is_valid': has_cat or has_dog,
            'is_cat': has_cat,
            'is_dog': has_dog,
            'confidence': max_confidence,
            'detected_objects': detected_objects
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Image processing failed: {str(e)}",
                "type": "processing_error"
            }
        )

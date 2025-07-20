# # backend/app/services/pet_feature_extractor.py
# import os
# import json
# import numpy as np
# from datetime import datetime

# from tensorflow.keras.applications import MobileNetV2
# from tensorflow.keras.preprocessing import image
# from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
# from PIL import Image
# from pathlib import Path

# class PetFeatureExtractor:
#     def __init__(self):
#         # Load models for both dog and cat features
#         self.model = MobileNetV2(weights='imagenet', 
#                                include_top=False, 
#                                pooling='avg')
#         self.img_size = (224, 224)
        
#         # Different weights for dogs vs cats
#         self.type_weights = {
#             'dog': {'main': 0.4, 'face': 0.3, 'side': 0.2, 'fur': 0.1},
#             'cat': {'main': 0.3, 'face': 0.4, 'side': 0.2, 'fur': 0.1}  # More weight on face for cats
#         }
        
#     def load_and_preprocess(self, img_path):
#         try:
#             img = Image.open(img_path)
#             if img.mode != 'RGB':
#                 img = img.convert('RGB')
#             img = img.resize(self.img_size)
#             x = image.img_to_array(img)
#             x = np.expand_dims(x, axis=0)
#             x = preprocess_input(x)
#             return x
#         except Exception as e:
#             print(f"Error processing image {img_path}: {str(e)}")
#             return None
    
#     def extract_features(self, img_path):
#         img = self.load_and_preprocess(img_path)
#         if img is None:
#             return None
#         features = self.model.predict(img)
#         return features.flatten().tolist()  # Convert to list for JSON serialization
    
#     def generate_fingerprint(self, pet_id, pet_type, upload_dir="app/uploads/pet_images"):
#         pet_dir = Path(upload_dir) / str(pet_id)
#         features = {
#             'metadata': {
#                 'type': pet_type,
#                 'generated_at': datetime.now().isoformat()
#             },
#             'features': {}
#         }
        
#         # Check and process each required image
#         for img_type in ['main', 'face', 'side', 'fur']:
#             img_path = pet_dir / f"{img_type}.jpg"
#             if img_path.exists():
#                 features['features'][img_type] = self.extract_features(img_path)
#             else:
#                 print(f"Missing {img_type} image for pet {pet_id}")
#                 return None
        
#         # Save features to JSON
#         features_path = pet_dir / "features.json"
#         with open(features_path, 'w') as f:
#             json.dump(features, f, indent=2)
        
#         return features_path
    
#     def compare_images(self, query_img_path, pet_features_path):
#         # Load pre-computed pet features
#         with open(pet_features_path) as f:
#             pet_data = json.load(f)
        
#         pet_type = pet_data['metadata']['type']
#         pet_features = pet_data['features']
#         weights = self.type_weights.get(pet_type, self.type_weights['dog'])
        
#         # Extract query features
#         query_features = self.extract_features(query_img_path)
#         if query_features is None:
#             return 0.0
        
#         # Calculate weighted similarity
#         total_score = 0.0
#         total_weight = 0.0
        
#         for img_type, weight in weights.items():
#             if img_type in pet_features:
#                 pet_vec = np.array(pet_features[img_type])
#                 query_vec = np.array(query_features)
#                 similarity = np.dot(pet_vec, query_vec) / (np.linalg.norm(pet_vec) * np.linalg.norm(query_vec))
#                 total_score += similarity * weight
#                 total_weight += weight
        
#         return total_score / total_weight if total_weight > 0 else 0.0
    
#     def get_pets_by_type(self, pet_type=None, base_dir="app/uploads/pet_images"):
#         pets_dir = Path(base_dir)
#         pet_ids = []
        
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir():
#                 features_path = pet_dir / "features.json"
#                 if features_path.exists():
#                     with open(features_path) as f:
#                         data = json.load(f)
#                     if pet_type is None or data['metadata']['type'] == pet_type:
#                         pet_ids.append(int(pet_dir.name))
        
#         return pet_ids
    

#     # Add to PetFeatureExtractor class
# def get_matched_angles(self, pet_features_path, query_img_path):
#     with open(pet_features_path) as f:
#         pet_data = json.load(f)
    
#     pet_type = pet_data['metadata']['type']
#     weights = self.type_weights.get(pet_type, self.type_weights['dog'])
#     query_features = self.extract_features(query_img_path)
    
#     angle_scores = {}
#     for img_type in ['main', 'face', 'side', 'fur']:
#         if img_type in pet_data['features']:
#             pet_vec = np.array(pet_data['features'][img_type])
#             query_vec = np.array(query_features)
#             similarity = np.dot(pet_vec, query_vec) / (np.linalg.norm(pet_vec) * np.linalg.norm(query_vec))
#             angle_scores[img_type] = {
#                 'score': float(similarity),
#                 'weight': weights.get(img_type, 0)
#             }
    
#     return angle_scores


# # backend/app/services/pet_feature_extractor.py
# def compare_features(self, source_features, target_features, pet_type):
#     weights = self.type_weights.get(pet_type, self.type_weights['dog'])
#     total_score = 0.0
#     total_weight = 0.0
    
#     for img_type, weight in weights.items():
#         if img_type in source_features and img_type in target_features:
#             source_vec = np.array(source_features[img_type])
#             target_vec = np.array(target_features[img_type])
#             similarity = np.dot(source_vec, target_vec) / (
#                 np.linalg.norm(source_vec) * np.linalg.norm(target_vec)
#             )
#             total_score += similarity * weight
#             total_weight += weight
    
#     return total_score / total_weight if total_weight > 0 else 0.0





















# # backend/app/services/pet_feature_extractor.py
# import os
# import json
# import numpy as np
# from datetime import datetime
# from pathlib import Path

# from tensorflow.keras.applications import MobileNetV2
# from tensorflow.keras.preprocessing import image
# from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
# from PIL import Image

# class PetFeatureExtractor:
#     def __init__(self):
#         # Load MobileNetV2 model pre-trained on ImageNet
#         self.model = MobileNetV2(weights='imagenet', 
#                                include_top=False, 
#                                pooling='avg')
#         self.img_size = (224, 224)
        
#         # Feature weights for different angles based on pet type
#         self.type_weights = {
#             'dog': {
#                 'main': 0.4,    # Highest weight for main profile
#                 'face': 0.3,    # Important for breed identification
#                 'side': 0.2,     # Body shape
#                 'fur': 0.1       # Fur texture/color
#             },
#             'cat': {
#                 'face': 0.5,    # Highest weight for face (most distinctive for cats)
#                 'main': 0.3,    # Body profile
#                 'side': 0.15,   # Body shape
#                 'fur': 0.05     # Less important for cats
#             }
#         }
        
#     def load_and_preprocess(self, img_path):
#         """Load and preprocess image for feature extraction"""
#         try:
#             img = Image.open(img_path)
#             if img.mode != 'RGB':
#                 img = img.convert('RGB')
#             img = img.resize(self.img_size)
#             x = image.img_to_array(img)
#             x = np.expand_dims(x, axis=0)
#             x = preprocess_input(x)
#             return x
#         except Exception as e:
#             print(f"Error processing image {img_path}: {str(e)}")
#             return None
    
#     def extract_features(self, img_path):
#         """Extract features from an image using MobileNetV2"""
#         img = self.load_and_preprocess(img_path)
#         if img is None:
#             return None
#         features = self.model.predict(img)
#         return features.flatten().tolist()
    
#     def generate_fingerprint(self, pet_id, pet_type, upload_dir="app/uploads/pet_images"):
#         """Generate fingerprint (features.json) for a pet"""
#         pet_dir = Path(upload_dir) / str(pet_id)
#         features = {
#             'metadata': {
#                 'type': pet_type.lower(),
#                 'generated_at': datetime.now().isoformat(),
#                 'pet_id': pet_id
#             },
#             'features': {}
#         }
        
#         # Check and process each required image type
#         required_images = ['main', 'face', 'side', 'fur']
#         missing_images = []
        
#         for img_type in required_images:
#             img_path = pet_dir / f"{img_type}.jpg"
#             if img_path.exists():
#                 features['features'][img_type] = self.extract_features(img_path)
#             else:
#                 missing_images.append(img_type)
        
#         if missing_images:
#             print(f"Missing images for pet {pet_id}: {', '.join(missing_images)}")
#             return None
        
#         # Save features to JSON
#         features_path = pet_dir / "features.json"
#         with open(features_path, 'w') as f:
#             json.dump(features, f, indent=2)
        
#         return features_path
    
#     def compare_features(self, source_features, target_features, pet_type):
#         """Compare features between two pets using type-specific weights"""
#         if pet_type not in self.type_weights:
#             pet_type = 'dog'  # Default to dog weights if unknown type
        
#         weights = self.type_weights[pet_type]
#         total_score = 0.0
#         total_weight = 0.0
        
#         for img_type, weight in weights.items():
#             if img_type in source_features and img_type in target_features:
#                 source_vec = np.array(source_features[img_type])
#                 target_vec = np.array(target_features[img_type])
                
#                 # Cosine similarity
#                 similarity = np.dot(source_vec, target_vec) / (
#                     np.linalg.norm(source_vec) * np.linalg.norm(target_vec)
#                 )
#                 total_score += similarity * weight
#                 total_weight += weight
        
#         return total_score / total_weight if total_weight > 0 else 0.0
    
#     def find_similar_pets(self, source_pet_id, threshold=0.65, base_dir="app/uploads/pet_images"):
#         """Find similar pets by comparing against all registered pets"""
#         source_path = Path(base_dir) / str(source_pet_id) / "features.json"
#         if not source_path.exists():
#             raise FileNotFoundError(f"Source pet features not found for ID {source_pet_id}")
        
#         with open(source_path) as f:
#             source_data = json.load(f)
        
#         source_type = source_data['metadata']['type']
#         matches = []
        
#         # Iterate through all pet directories
#         pets_dir = Path(base_dir)
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir() and pet_dir.name != str(source_pet_id):
#                 target_path = pet_dir / "features.json"
#                 if target_path.exists():
#                     with open(target_path) as f:
#                         target_data = json.load(f)
                    
#                     # Only compare with same type pets
#                     if target_data['metadata']['type'] == source_type:
#                         similarity = self.compare_features(
#                             source_data['features'],
#                             target_data['features'],
#                             source_type
#                         )
#                         if similarity >= threshold:
#                             matches.append({
#                                 'pet_id': int(pet_dir.name),
#                                 'similarity': similarity,
#                                 'features_path': str(target_path)
#                             })
        
#         # Sort by highest similarity first
#         matches.sort(key=lambda x: x['similarity'], reverse=True)
#         return matches
    
#     def get_matched_angles(self, pet_features_path, query_img_path):
#         """Get similarity scores for each angle/view"""
#         with open(pet_features_path) as f:
#             pet_data = json.load(f)
        
#         pet_type = pet_data['metadata']['type']
#         weights = self.type_weights.get(pet_type, self.type_weights['dog'])
#         query_features = self.extract_features(query_img_path)
        
#         if query_features is None:
#             return {}
        
#         angle_scores = {}
#         for img_type in ['main', 'face', 'side', 'fur']:
#             if img_type in pet_data['features']:
#                 pet_vec = np.array(pet_data['features'][img_type])
#                 query_vec = np.array(query_features)
#                 similarity = np.dot(pet_vec, query_vec) / (
#                     np.linalg.norm(pet_vec) * np.linalg.norm(query_vec))
#                 angle_scores[img_type] = {
#                     'score': float(similarity),
#                     'weight': weights.get(img_type, 0)
#                 }
        
#         return angle_scores
    
#     def search_by_image(self, query_img_path, pet_type=None, threshold=0.7, base_dir="app/uploads/pet_images"):
#         """Search for similar pets using a query image"""
#         query_features = self.extract_features(query_img_path)
#         if query_features is None:
#             return []
        
#         matches = []
#         pets_dir = Path(base_dir)
        
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir():
#                 features_path = pet_dir / "features.json"
#                 if features_path.exists():
#                     with open(features_path) as f:
#                         pet_data = json.load(f)
                    
#                     # Filter by pet type if specified
#                     if pet_type and pet_data['metadata']['type'] != pet_type:
#                         continue
                    
#                     # Create temporary source features structure
#                     temp_source = {
#                         'main': query_features,
#                         'face': query_features,
#                         'side': query_features,
#                         'fur': query_features
#                     }
                    
#                     similarity = self.compare_features(
#                         temp_source,
#                         pet_data['features'],
#                         pet_data['metadata']['type']
#                     )
                    
#                     if similarity >= threshold:
#                         matches.append({
#                             'pet_id': pet_data['metadata']['pet_id'],
#                             'similarity': similarity,
#                             'features_path': str(features_path)
#                         })
        
#         matches.sort(key=lambda x: x['similarity'], reverse=True)
#         return matches
    
#     def get_all_pets_with_fingerprints(self, base_dir="app/uploads/pet_images"):
#         """Get list of all pets that have generated fingerprints"""
#         pets_dir = Path(base_dir)
#         pet_ids = []
        
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir():
#                 features_path = pet_dir / "features.json"
#                 if features_path.exists():
#                     with open(features_path) as f:
#                         data = json.load(f)
#                     pet_ids.append({
#                         'pet_id': data['metadata']['pet_id'],
#                         'type': data['metadata']['type'],
#                         'generated_at': data['metadata']['generated_at']
#                     })
        
#         return pet_ids

# # backend/app/services/pet_feature_extractor.py
# import os
# import json
# import numpy as np
# from datetime import datetime
# from pathlib import Path

# from tensorflow.keras.applications import MobileNetV2
# from tensorflow.keras.preprocessing import image
# from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
# from PIL import Image

# class PetFeatureExtractor:
#     def __init__(self):
#         # Load MobileNetV2 model pre-trained on ImageNet
#         self.model = MobileNetV2(weights='imagenet', 
#                                include_top=False, 
#                                pooling='avg')
#         self.img_size = (224, 224)
        
#         # Feature weights for different angles based on pet type
#         self.type_weights = {
#             'dog': {
#                 'main': 0.4,    # Highest weight for main profile
#                 'face': 0.3,    # Important for breed identification
#                 'side': 0.2,     # Body shape
#                 'fur': 0.1       # Fur texture/color
#             },
#             'cat': {
#                 'face': 0.5,    # Highest weight for face (most distinctive for cats)
#                 'main': 0.3,    # Body profile
#                 'side': 0.15,   # Body shape
#                 'fur': 0.05     # Less important for cats
#             }
#         }
        
#     def load_and_preprocess(self, img_path):
#         """Load and preprocess image for feature extraction"""
#         try:
#             img = Image.open(img_path)
#             if img.mode != 'RGB':
#                 img = img.convert('RGB')
#             img = img.resize(self.img_size)
#             x = image.img_to_array(img)
#             x = np.expand_dims(x, axis=0)
#             x = preprocess_input(x)
#             return x
#         except Exception as e:
#             print(f"Error processing image {img_path}: {str(e)}")
#             return None
    
#     def extract_features(self, img_path):
#         """Extract features from an image using MobileNetV2"""
#         img = self.load_and_preprocess(img_path)
#         if img is None:
#             return None
#         features = self.model.predict(img)
#         return features.flatten().tolist()
    
#     def generate_fingerprint(self, pet_id, pet_type, status, upload_dir="app/uploads/pet_images"):
#         """Generate fingerprint (features.json) for a pet"""
#         pet_dir = Path(upload_dir) / str(pet_id)
#         features = {
#             'metadata': {
#                 'type': pet_type.lower(),
#                 'status': status.lower(),  # Added status field
#                 'generated_at': datetime.now().isoformat(),
#                 'pet_id': pet_id
#             },
#             'features': {}
#         }
        
#         # Check and process each required image type
#         required_images = ['main', 'face', 'side', 'fur']
#         missing_images = []
        
#         for img_type in required_images:
#             img_path = pet_dir / f"{img_type}.jpg"
#             if img_path.exists():
#                 features['features'][img_type] = self.extract_features(img_path)
#             else:
#                 missing_images.append(img_type)
        
#         if missing_images:
#             print(f"Missing images for pet {pet_id}: {', '.join(missing_images)}")
#             return None
        
#         # Save features to JSON
#         features_path = pet_dir / "features.json"
#         with open(features_path, 'w') as f:
#             json.dump(features, f, indent=2)
        
#         return features_path
    
#     def compare_features(self, source_features, target_features, pet_type):
#         """Compare features between two pets using type-specific weights"""
#         if pet_type not in self.type_weights:
#             pet_type = 'dog'  # Default to dog weights if unknown type
        
#         weights = self.type_weights[pet_type]
#         total_score = 0.0
#         total_weight = 0.0
        
#         for img_type, weight in weights.items():
#             if img_type in source_features and img_type in target_features:
#                 source_vec = np.array(source_features[img_type])
#                 target_vec = np.array(target_features[img_type])
                
#                 # Cosine similarity
#                 similarity = np.dot(source_vec, target_vec) / (
#                     np.linalg.norm(source_vec) * np.linalg.norm(target_vec)
#                 )
#                 total_score += similarity * weight
#                 total_weight += weight
        
#         return total_score / total_weight if total_weight > 0 else 0.0
    
#     def find_similar_pets(self, source_pet_id, threshold=0.65, base_dir="app/uploads/pet_images"):
#         """Find similar pets by comparing against all registered pets"""
#         source_path = Path(base_dir) / str(source_pet_id) / "features.json"
#         if not source_path.exists():
#             raise FileNotFoundError(f"Source pet features not found for ID {source_pet_id}")
        
#         with open(source_path) as f:
#             source_data = json.load(f)
        
#         source_type = source_data['metadata']['type']
#         matches = []
        
#         # Iterate through all pet directories
#         pets_dir = Path(base_dir)
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir() and pet_dir.name != str(source_pet_id):
#                 target_path = pet_dir / "features.json"
#                 if target_path.exists():
#                     with open(target_path) as f:
#                         target_data = json.load(f)
                    
#                     # Only compare with same type pets
#                     if target_data['metadata']['type'] == source_type:
#                         similarity = self.compare_features(
#                             source_data['features'],
#                             target_data['features'],
#                             source_type
#                         )
#                         if similarity >= threshold:
#                             matches.append({
#                                 'pet_id': int(pet_dir.name),
#                                 'similarity': similarity,
#                                 'features_path': str(target_path),
#                                 'status': target_data['metadata']['status']  # Added status
#                             })
        
#         # Sort by highest similarity first
#         matches.sort(key=lambda x: x['similarity'], reverse=True)
#         return matches
    
#     def get_matched_angles(self, pet_features_path, query_img_path):
#         """Get similarity scores for each angle/view"""
#         with open(pet_features_path) as f:
#             pet_data = json.load(f)
        
#         pet_type = pet_data['metadata']['type']
#         weights = self.type_weights.get(pet_type, self.type_weights['dog'])
#         query_features = self.extract_features(query_img_path)
        
#         if query_features is None:
#             return {}
        
#         angle_scores = {}
#         for img_type in ['main', 'face', 'side', 'fur']:
#             if img_type in pet_data['features']:
#                 pet_vec = np.array(pet_data['features'][img_type])
#                 query_vec = np.array(query_features)
#                 similarity = np.dot(pet_vec, query_vec) / (
#                     np.linalg.norm(pet_vec) * np.linalg.norm(query_vec))
#                 angle_scores[img_type] = {
#                     'score': float(similarity),
#                     'weight': weights.get(img_type, 0)
#                 }
        
#         return angle_scores
    
#     def search_by_image(self, query_img_path, pet_type=None, threshold=0.7, base_dir="app/uploads/pet_images"):
#         """Search for similar pets using a query image"""
#         query_features = self.extract_features(query_img_path)
#         if query_features is None:
#             return []
        
#         matches = []
#         pets_dir = Path(base_dir)
        
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir():
#                 features_path = pet_dir / "features.json"
#                 if features_path.exists():
#                     with open(features_path) as f:
#                         pet_data = json.load(f)
                    
#                     # Filter by pet type if specified
#                     if pet_type and pet_data['metadata']['type'] != pet_type:
#                         continue
                    
#                     # Create temporary source features structure
#                     temp_source = {
#                         'main': query_features,
#                         'face': query_features,
#                         'side': query_features,
#                         'fur': query_features
#                     }
                    
#                     similarity = self.compare_features(
#                         temp_source,
#                         pet_data['features'],
#                         pet_data['metadata']['type']
#                     )
                    
#                     if similarity >= threshold:
#                         matches.append({
#                             'pet_id': pet_data['metadata']['pet_id'],
#                             'similarity': similarity,
#                             'features_path': str(features_path),
#                             'status': pet_data['metadata']['status']  # Added status
#                         })
        
#         matches.sort(key=lambda x: x['similarity'], reverse=True)
#         return matches
    
#     def get_all_pets_with_fingerprints(self, base_dir="app/uploads/pet_images"):
#         """Get list of all pets that have generated fingerprints"""
#         pets_dir = Path(base_dir)
#         pet_ids = []
        
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir():
#                 features_path = pet_dir / "features.json"
#                 if features_path.exists():
#                     with open(features_path) as f:
#                         data = json.load(f)
#                     pet_ids.append({
#                         'pet_id': data['metadata']['pet_id'],
#                         'type': data['metadata']['type'],
#                         'status': data['metadata']['status'],  # Added status
#                         'generated_at': data['metadata']['generated_at']
#                     })
        
#         return pet_ids

import os
import json
from datetime import datetime
from pathlib import Path

# Try importing TensorFlow-related modules
try:
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    from tensorflow.keras.applications import MobileNetV2
    import numpy as np
    from PIL import Image
    USE_TENSORFLOW = True
except ImportError:
    print("TensorFlow not installed. PetFeatureExtractor will be disabled.")
    USE_TENSORFLOW = False

class PetFeatureExtractor:
    def __init__(self):
        self.model = None
        self.img_size = (224, 224)

        self.type_weights = {
            'dog': {'main': 0.4, 'face': 0.3, 'side': 0.2, 'fur': 0.1},
            'cat': {'face': 0.5, 'main': 0.3, 'side': 0.15, 'fur': 0.05}
        }

    def get_model(self):
        if not USE_TENSORFLOW:
            return None
        if self.model is None:
            self.model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')
        return self.model

def load_and_preprocess(self, img_path):
        if not USE_TENSORFLOW:
            return None
        try:
            img = Image.open(img_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = img.resize(self.img_size)
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            return x
        except Exception as e:
            print(f"Error processing image {img_path}: {str(e)}")
            return None

    def extract_features(self, img_path):
        if not USE_TENSORFLOW:
            print("TensorFlow not enabled. Skipping feature extraction.")
            return None
        img = self.load_and_preprocess(img_path)
        if img is None:
            return None
        model = self.get_model()
        if model is None:
            return None
        features = model.predict(img)
        return features.flatten().tolist()

    def generate_fingerprint(self, pet_id, pet_type, status, upload_dir="app/uploads/pet_images"):
        pet_dir = Path(upload_dir) / str(pet_id)
        features = {
            'metadata': {
                'type': pet_type.lower(),
                'status': status.lower(),
                'generated_at': datetime.now().isoformat(),
                'pet_id': pet_id
            },
            'features': {}
        }

        required_images = ['main', 'face', 'side', 'fur']
        missing_images = []

        for img_type in required_images:
            img_path = pet_dir / f"{img_type}.jpg"
            if img_path.exists():
                features['features'][img_type] = self.extract_features(img_path)
            else:
                missing_images.append(img_type)

        if missing_images:
            print(f"Missing images for pet {pet_id}: {', '.join(missing_images)}")
            return None

        features_path = pet_dir / "features.json"
        with open(features_path, 'w') as f:
            json.dump(features, f, indent=2)

        return features_path

    def compare_features(self, source_features, target_features, pet_type):
        if pet_type not in self.type_weights:
            pet_type = 'dog'

        weights = self.type_weights[pet_type]
        total_score = 0.0
        total_weight = 0.0

        for img_type, weight in weights.items():
            if img_type in source_features and img_type in target_features:
                source_vec = np.array(source_features[img_type])
                target_vec = np.array(target_features[img_type])
                similarity = np.dot(source_vec, target_vec) / (
                    np.linalg.norm(source_vec) * np.linalg.norm(target_vec)
                )
                total_score += similarity * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def find_similar_pets(self, source_pet_id, threshold=0.65, base_dir="app/uploads/pet_images"):
        source_path = Path(base_dir) / str(source_pet_id) / "features.json"
        if not source_path.exists():
            raise FileNotFoundError(f"Source pet features not found for ID {source_pet_id}")

        with open(source_path) as f:
            source_data = json.load(f)

        source_type = source_data['metadata']['type']
        matches = []
        pets_dir = Path(base_dir)

        for pet_dir in pets_dir.iterdir():
            if pet_dir.is_dir() and pet_dir.name != str(source_pet_id):
                target_path = pet_dir / "features.json"
                if target_path.exists():
                    with open(target_path) as f:
                        target_data = json.load(f)

                    if target_data['metadata']['type'] == source_type:
                        similarity = self.compare_features(
                            source_data['features'],
                            target_data['features'],
                            source_type
                        )
                        if similarity >= threshold:
                            matches.append({
                                'pet_id': int(pet_dir.name),
                                'similarity': similarity,
                                'features_path': str(target_path),
                                'status': target_data['metadata']['status']
                            })

        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches

    def get_matched_angles(self, pet_features_path, query_img_path):
        with open(pet_features_path) as f:
            pet_data = json.load(f)

        pet_type = pet_data['metadata']['type']
        weights = self.type_weights.get(pet_type, self.type_weights['dog'])
        query_features = self.extract_features(query_img_path)

        if query_features is None:
            return {}

        angle_scores = {}
        for img_type in ['main', 'face', 'side', 'fur']:
            if img_type in pet_data['features']:
                pet_vec = np.array(pet_data['features'][img_type])
                query_vec = np.array(query_features)
                similarity = np.dot(pet_vec, query_vec) / (
                    np.linalg.norm(pet_vec) * np.linalg.norm(query_vec))
                angle_scores[img_type] = {
                    'score': float(similarity),
                    'weight': weights.get(img_type, 0)
                }

        return angle_scores

    def search_by_image(self, query_img_path, pet_type=None, threshold=0.7, base_dir="app/uploads/pet_images"):
        query_features = self.extract_features(query_img_path)
        if query_features is None:
            return []

        matches = []
        pets_dir = Path(base_dir)

        for pet_dir in pets_dir.iterdir():
            if pet_dir.is_dir():
                features_path = pet_dir / "features.json"
                if features_path.exists():
                    with open(features_path) as f:
                        pet_data = json.load(f)

                    if pet_type and pet_data['metadata']['type'] != pet_type:
                        continue

                    temp_source = {
                        'main': query_features,
                        'face': query_features,
                        'side': query_features,
                        'fur': query_features
                    }

                    similarity = self.compare_features(
                        temp_source,
                        pet_data['features'],
                        pet_data['metadata']['type']
                    )

                    if similarity >= threshold:
                        matches.append({
                            'pet_id': pet_data['metadata']['pet_id'],
                            'similarity': similarity,
                            'features_path': str(features_path),
                            'status': pet_data['metadata']['status']
                        })

        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches

    def get_all_pets_with_fingerprints(self, base_dir="app/uploads/pet_images"):
        pets_dir = Path(base_dir)
        pet_ids = []

        for pet_dir in pets_dir.iterdir():
            if pet_dir.is_dir():
                features_path = pet_dir / "features.json"
                if features_path.exists():
                    with open(features_path) as f:
                        data = json.load(f)
                    pet_ids.append({
                        'pet_id': data['metadata']['pet_id'],
                        'type': data['metadata']['type'],
                        'status': data['metadata']['status'],
                        'generated_at': data['metadata']['generated_at']
                    })

        return pet_ids

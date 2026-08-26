---
question_id: "2698e78f_abs"
session_index: 22
session_id: "sharegpt_Fva9GhV_0"
timestamp: "2023/05/24 (Wed) 20:13"
is_evidence_session: false
turn_count: 2
translation_status: TODO
---
# Session 022 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Given the code below, can you implement the currently unimplemented crop\_and\_resize\_bodyshot function?

import cv2
import numpy as np
import mediapipe as mp
import time
from tqdm import tqdm

from third\_party.face\_geometry import (
 PCF,
 get\_metric\_landmarks,
 procrustes\_landmark\_basis,
)

# MP objects
mp\_face\_detection = mp.solutions.face\_detection
mp\_face\_mesh = mp.solutions.face\_mesh
mp\_drawing = mp.solutions.drawing\_utils
mp\_drawing\_styles = mp.solutions.drawing\_styles

# Mediapipe stuff
points\_idx = [33, 263, 61, 291, 199]
points\_idx = points\_idx + [key for (key, val) in procrustes\_landmark\_basis]
points\_idx = list(set(points\_idx))
points\_idx.sort()

# Constants estimated from experiments
# In theory, 125 combinations are possible.
# Let's prioritize yaw and pitch now and ignore roll.
NUM\_SAMPLES\_PER\_AXIS = 5
YAW\_ANCHORS = np.linspace(-60.0, 60.0, NUM\_SAMPLES\_PER\_AXIS)
PITCH\_ANCHORS = np.linspace(-40.0, 40.0, NUM\_SAMPLES\_PER\_AXIS)
ROLL\_ANCHORS = np.linspace(-45.0, 45.0, NUM\_SAMPLES\_PER\_AXIS)

FACE\_HEIGHT\_EXPANSION\_FACTOR = 0.25
HEADSHOT\_THRESHOLD = 0.30
TARGET\_HEADSHOT\_COVERAGE = 0.4
def detect\_faces(image, debug=False):
 '''
 Function to detect faces in a given image.
 Model selection is set to "1" which is a full range model which works
 at all distances.

 Args:
 image: Input image
 Returns:
 faces: A list of faces
 '''
 with mp\_face\_detection.FaceDetection(
 model\_selection=1, min\_detection\_confidence=0.5) as face\_detection:

 # Convert the BGR image to RGB and process it with MediaPipe Face Detection.
 results = face\_detection.process(cv2.cvtColor(image, cv2.COLOR\_BGR2RGB))

 # Draw face detections of each face.
 if not results.detections:
 if debug:
 return image, None
 else:
 return None

 if debug:
 annotated\_image = image.copy()
 for detection in results.detections:
 print(detection.location\_data.relative\_bounding\_box)
 mp\_drawing.draw\_detection(annotated\_image, detection)
 return annotated\_image, results.detections
 else:
 return results.detections
def crop\_and\_resize\_headshot(image, bbox, target\_width, target\_height, debug):
 '''
 Crops and resize headshot image
 bbox = realative\_bbox{xmin, ymin, width, height}
 '''
 # Scale image if needed
 image, image\_width, image\_height = scale\_image\_to\_min\_dim(image, target\_width, target\_height)

 # Compute face center
 face\_center\_x = (bbox.xmin + (0.5 \* bbox.width)) \* image\_width
 face\_center\_y = (bbox.ymin + (0.5 \* bbox.height)) \* image\_height
 relative\_face\_height = bbox.height
 relative\_face\_width = bbox.width
 box\_height = bbox.height \* image\_height
 box\_width = bbox.width \* image\_width

 # Mediapipe does not cover the top of the head. So, expand a little bit
 face\_center\_y = face\_center\_y - (box\_height \* FACE\_HEIGHT\_EXPANSION\_FACTOR \* 0.5)
 box\_height = box\_height \* (1 + FACE\_HEIGHT\_EXPANSION\_FACTOR)
 relative\_face\_height = relative\_face\_height \* (1 + FACE\_HEIGHT\_EXPANSION\_FACTOR)

 # Target aspect ratio
 # target\_aspect\_ratio = float(target\_width) / target\_height

 # Target coverage.
 # For headshot we expect a minimum face to image dimension ratio of HEADSHOT\_TARGET\_COVERAGE
 target\_coverage = max(TARGET\_HEADSHOT\_COVERAGE, relative\_face\_width, relative\_face\_height)
 print(f'Target Coverage: {target\_coverage}')
 print(
 f'Max of (Target, rwidth, rheight): {TARGET\_HEADSHOT\_COVERAGE}, {relative\_face\_width},{relative\_face\_height}')

 # Factor to scale target dimensions so that the above coverage is met
 initial\_crop\_height = image\_height + 1
 initial\_crop\_width = image\_width + 1

 while (initial\_crop\_height > image\_height or initial\_crop\_width > image\_width):

 target\_scaler = box\_width / \
 (target\_coverage \* target\_width) if relative\_face\_width > relative\_face\_height else box\_height / \
 (target\_coverage \* target\_height)
 print(f'Target Scaler: {target\_scaler}')

 # Get intial cropping box, that satisfies target\_coverage
 initial\_crop\_width = target\_width \* target\_scaler
 initial\_crop\_height = target\_height \* target\_scaler

 print(f'Original dims (W x H) : {image\_width} x {image\_height}')
 print(f'Initial crop dims (W x H) : {initial\_crop\_width} x {initial\_crop\_height}')

 if initial\_crop\_height > image\_height or initial\_crop\_width > image\_width:
 print('Crop dimensions larger than image! Trying increased coverage')
 target\_coverage += 0.05
 print(f'Target coverage: {target\_coverage}')
 print('------------------------------')

 if target\_coverage >= 1.0:
 return None

 # Check for valid crop without having to squish the face
 if initial\_crop\_width < box\_width or initial\_crop\_height < box\_height:
 print('Crop Dimensions smaller than face box! Skipping crop!')
 return None

 # Get intial bounds
 left\_x = int(face\_center\_x - (initial\_crop\_width/2.0))
 right\_x = int(face\_center\_x + (initial\_crop\_width/2.0))
 top\_y = int(face\_center\_y - (initial\_crop\_height/2.0))
 bottom\_y = int(face\_center\_y + (initial\_crop\_height/2.0))

 print('Initial Bounds:')
 print(f'lx, ty, rx, by: {left\_x}, {top\_y}, {right\_x}, {bottom\_y}')

 # Slide to bounds
 if left\_x < 0:
 left\_x = 0
 right\_x = int(initial\_crop\_width - 1)

 if top\_y < 0:
 top\_y = 0
 bottom\_y = int(initial\_crop\_height - 1)

 if right\_x >= image\_width:
 right\_x = image\_width - 1
 left\_x = int(image\_width - initial\_crop\_width)

 if bottom\_y >= image\_height:
 bottom\_y = image\_height - 1
 top\_y = int(image\_height - initial\_crop\_height)

 print('Final Bounds:')
 print(f'lx, ty, rx, by: {left\_x}, {top\_y}, {right\_x}, {bottom\_y}')

 # Get the initial crop
 initial\_crop = image[top\_y:bottom\_y, left\_x:right\_x]

 # Resize to the target size
 final\_crop = cv2.resize(initial\_crop, (target\_width, target\_height))

 # Pass debug info if requested
 if debug:
 face\_x1 = int(face\_center\_x - box\_width/2.0)
 face\_y1 = int(face\_center\_y - box\_height/2.0)
 face\_x2 = int(face\_center\_x + box\_width/2.0)
 face\_y2 = int(face\_center\_y + box\_height/2.0)

 image = cv2.rectangle(image, (left\_x, top\_y), (right\_x, bottom\_y), (255, 0, 0), 4)
 image = cv2.rectangle(image, (face\_x1, face\_y1), (face\_x2, face\_y2), (0, 255, 0), 4)
 return image, final\_crop

 return final\_crop
def crop\_and\_resize\_bodyshot(image, bbox, target\_width, target\_height, debug):
 '''
 Crops and resize bodyshot image
 '''
 print('Bodyshot Unimplemented')
 return None
def crop\_and\_resize\_person\_image(image, width, height, debug=False):
 '''
 Given an image, crop and resize the image so that the face/person is the primary subject.

 This can be done in the following way:
 1. Get all faces in the image.
 a. If multiple faces, the biggest one will be the primary face
 2. Classify if the image is a headshot or a fullbody picture. This can be done by checking the face:image size ratio
 3. If it is a headshot:
 a. If one of the dimensions is larger, crop such that the whole face is centered. This preserves image quality without 
 having to resize.
 b. If one of the dimensions is smaller, crop to that size and then resize
 4. If it is a full/partial body shot:
 a. Try to preserve the relative face location along the v-axis.
 '''

 # Get Detections
 detections = detect\_faces(image)

 # If no detections, return
 if detections is None:
 return None

 # Identify the primary face
 max\_area = 0
 for detection in detections:
 # detection.location\_data.relative\_bounding\_box.{xmin, ymin, width, height}
 bbox = detection.location\_data.relative\_bounding\_box
 area = bbox.height \* bbox.width
 if area > max\_area:
 max\_area = area
 primary\_detection = detection

 # Classify headshot vs body shot
 primary\_face\_box = primary\_detection.location\_data.relative\_bounding\_box

 # If face is a certain % of image in either dimension, it's a headshot
 print(f'rW, rH: {primary\_face\_box.width}, {primary\_face\_box.height}')
 if primary\_face\_box.width > HEADSHOT\_THRESHOLD or primary\_face\_box.height > HEADSHOT\_THRESHOLD:
 print('Classified as a headshot!')
 # Do headshot stuff here
 return crop\_and\_resize\_headshot(image, primary\_face\_box, width, height, debug)
 else:
 print('Classified as a bodyshot!')
 # Do body shot stuff here
 return crop\_and\_resize\_bodyshot(image, primary\_face\_box, width, height, debug)
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
The `crop_and_resize_bodyshot` function is currently unimplemented. Let's implement it to crop and resize a body shot image. The idea is to maintain the relative position of the face in the image while resizing it to the target width and height.
```python
def crop_and_resize_bodyshot(image, bbox, target_width, target_height, debug):
    '''
    Crops and resize bodyshot image
    '''
    # Scale image if needed
    image, image_width, image_height = scale_image_to_min_dim(image, target_width, target_height)

    # Compute face center
    face_center_x = (bbox.xmin + (0.5 * bbox.width)) * image_width
    face_center_y = (bbox.ymin + (0.5 * bbox.height)) * image_height

    # Determine the scaling factor
    scaling_factor = min(target_width / image_width, target_height / image_height)

    # Calculate the new image dimensions
    new_width = int(image_width * scaling_factor)
    new_height = int(image_height * scaling_factor)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))

    # Calculate the position of the face in the resized image
    new_face_center_x = int(face_center_x * scaling_factor)
    new_face_center_y = int(face_center_y * scaling_factor)

    # Define the cropping rectangle
    left_x = int(new_face_center_x - (target_width / 2))
    right_x = int(new_face_center_x + (target_width / 2))
    top_y = int(new_face_center_y - (target_height / 2))
    bottom_y = int(new_face_center_y + (target_height / 2))

    # Adjust the cropping rectangle if it goes beyond the image boundaries
    if left_x < 0:
        right_x -= left_x
        left_x = 0
    if top_y < 0:
        bottom_y -= top_y
        top_y = 0
    if right_x > new_width:
        left_x -= right_x - new_width
        right_x = new_width
    if bottom_y > new_height:
        top_y -= bottom_y - new_height
        bottom_y = new_height

    # Crop the resized image
    cropped_image = resized_image[top_y:bottom_y, left_x:right_x]

    if debug:
        resized_image = cv2.rectangle(resized_image, (left_x, top_y), (right_x, bottom_y), (255, 0, 0), 4)
        return resized_image, cropped_image

    return cropped_image
```
This implementation first scales the image to fit within the target dimensions while preserving the aspect ratio. Then, it resizes the image based on the scaling factor and adjusts the cropping rectangle if it goes beyond the image boundaries. Finally, it crops the resized image to obtain the desired body shot image.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->

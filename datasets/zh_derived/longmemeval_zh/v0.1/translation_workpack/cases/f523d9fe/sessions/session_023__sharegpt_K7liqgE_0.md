---
question_id: "f523d9fe"
session_index: 23
session_id: "sharegpt_K7liqgE_0"
timestamp: "2023/05/24 (Wed) 16:31"
is_evidence_session: false
turn_count: 2
translation_status: TODO
---
# Session 023 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Identify the flow, process and system of OCR on your app both frontend and backend.
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
To integrate Optical Character Recognition (OCR) into an app, you'll need a structured flow, process, and system that involves both frontend and backend components. Here's an outline of what this might look like:

1. Flow:
a. User captures or uploads an image containing text.
b. The image is sent to the backend for OCR processing.
c. The backend performs OCR on the image and extracts the text.
d. The extracted text is sent back to the frontend.
e. The frontend displays the extracted text to the user.
2. Frontend Process:
a. Image capture/upload:
	* The app provides an interface for users to either capture an image using the device's camera or upload an existing image from their device.
	b. Display extracted text:
	* Once the text is extracted and sent back from the backend, the frontend displays the text to the user in a readable format. The user may have options to edit, save, or share the extracted text.
3. Backend Process:
a. Receive image:
	* The backend receives the image from the frontend, typically as a base64 encoded string or a binary file.
	b. Pre-process image (optional):
	* Depending on the quality of the image, some pre-processing steps may be necessary, such as resizing, rotating, or enhancing the image to improve OCR accuracy.
	c. OCR processing:
	* The OCR engine (e.g., Tesseract, Google Cloud Vision API, or Amazon Textract) processes the image and extracts the text.
	d. Post-process extracted text (optional):
	* The backend may perform additional processing on the extracted text, such as spell-checking, formatting, or natural language processing (NLP) tasks like entity recognition or sentiment analysis.
	e. Send extracted text to frontend:
	* The backend sends the extracted text back to the frontend in a suitable format (e.g., JSON).
4. System:
a. Frontend:
	* The frontend is typically built using a web or mobile app development framework (e.g., React, Angular, Swift, or Kotlin) and communicates with the backend via RESTful APIs or GraphQL.
	b. Backend:
	* The backend is usually developed using a server-side programming language (e.g., Python, Node.js, or Ruby) and may utilize cloud-based services for OCR processing and storage (e.g., AWS, Google Cloud, or Azure).
	c. OCR Engine:
	* The OCR engine can be either an open-source solution (e.g., Tesseract) or a commercial service (e.g., Google Cloud Vision API or Amazon Textract). The choice of OCR engine will depend on factors such as accuracy, speed, and cost.

By implementing this flow, process, and system, you can create an efficient and user-friendly OCR-enabled app that provides a seamless experience for users to extract text from images.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->

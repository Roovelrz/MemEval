---
question_id: "bc8a6e93"
session_index: 36
session_id: "sharegpt_8Sq4v0t_9"
timestamp: "2023/05/28 (Sun) 08:15"
is_evidence_session: false
turn_count: 3
translation_status: TODO
---
# Session 036 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Step 16: Save the composition
After rendering the composition, you can save it by choosing "File" > "Save" or "Save As" from the menu bar. You can also export the composition as a video file by choosing "Composition" > "Add to Adobe Media Encoder Queue" from the menu bar.

Step 17: Reuse the script
To reuse the script in other projects, you can save it as a .jsx file. To do this, select the composition containing the script in the project window, then choose "File" > "Export" > "Add to Adobe Media Encoder Queue". In the export settings, choose "Format" > "Extended Script Toolkit (.jsx)", then choose a destination folder and click "Export". You can then use the .jsx file in other projects by importing it into the ExtendScript Toolkit and running it.

By following these steps, you can create a colorful gradient circle using JSX code in the ExtendScript engine of After Effects, with the ADBE Effect Parade effect, and automate the effect controls using expressions. You can then save the script as a .jsx file and reuse it in other projects, making the process of creating colorful gradient circles more efficient and streamlined.
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_000_END -->

## Turn 001 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
give me the full code
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->

## Turn 002 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
Here's the full code to create a colorful gradient circle using JSX code in the ExtendScript engine of After Effects, with the ADBE Effect Parade effect, and automate the effect controls using expressions:
```swift
// Create a new solid layer
var solidLayer = app.project.activeItem.layers.addSolid([0, 0, 0], "Solid 1", 1920, 1080, 1, app.project.activeItem.duration);

// Add Gradient Ramp effect to the solid layer
var gradientRamp = solidLayer.Effects.addProperty("ADBE Ramp");
gradientRamp.name = "Gradient Ramp";

// Modify Gradient Ramp effect properties
gradientRamp.property("Start Color").setValue([1, 0, 0]); // Change the start color of the gradient
gradientRamp.property("End Color").setValue([0, 0, 1]); // Change the end color of the gradient
gradientRamp.property("Shape").setValue(2); // Change the shape of the gradient to radial
gradientRamp.property("Ramp Scatter").setValue(100); // Adjust the scatter of the gradient
gradientRamp.property("Ramp Width").setValue(1000); // Adjust the width of the gradient

// Add ADBE Effect Parade effect to the solid layer
var effectParade = solidLayer.Effects.addProperty("ADBE Effect Parade");
effectParade.name = "Effect Parade";

// Modify ADBE Effect Parade effect properties
effectParade.property("Radius").setValue(solidLayer.width/2); // Set the radius of the circle to half the width of the solid layer

// Add expression to automate the gradient colors
var startColor = gradientRamp.property("Start Color");
var endColor = gradientRamp.property("End Color");

startColor.expression = "hue = time * 10;\nsaturation = 1;\nbrightness = 1;\ncolor = HSBToRGB(hue, saturation, brightness);\nramp = thisComp.layer(\"Solid 1\").effect(\"Gradient Ramp\")(\"ADBE Ramp-0001\");\n[ramp.startColor = color, ramp.endColor = color]";

endColor.expression = "hue = time * 10;\nsaturation = 1;\nbrightness = 1;\ncolor = HSBToRGB(hue, saturation, brightness);\nramp = thisComp.layer(\"Solid 1\").effect(\"Gradient Ramp\")(\"ADBE Ramp-0001\");\n[ramp.startColor = color, ramp.endColor = color]";

// Add expression to automate the radius of the circle
var radius = effectParade.property("Radius");
radius.expression = "ramp = thisComp.layer(\"Solid 1\").effect(\"ADBE Effect Parade\")(\"ADBE Effect Parade-0001\");\nramp.radius = value[0]/2;";

// Preview and render the composition
app.project.activeItem.openInViewer();
app.project.renderQueue.items.add(app.project.activeItem);
```
Note that this code is an example and may need to be modified to fit your specific needs. It also assumes that you have a composition open and selected in After Effects before running the script.
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_002_END -->

---
question_id: "07b6f563"
session_index: 13
session_id: "sharegpt_zvmX9pX_25"
timestamp: "2023/05/22 (Mon) 04:56"
is_evidence_session: false
turn_count: 5
translation_status: TODO
---
# Session 013 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
| Aspect Ratios |
| --- |
| The --aspect or --ar parameter changes the aspect ratio of the generated image. An aspect ratio is the width-to-height ratio of an image. It is typically expressed as two numbers separated by a colon, such as 7:4 or 4:3. |
| A square image has equal width and height, described as a 1:1 aspect ratio. The image could be 1000px × 1000px, or 1500px × 1500px, and the aspect ratio would still be 1:1. A computer screen might have a ratio of 16:10. The height is 1.6 times longer than the width. So the image could be 1600px × 1000px, 4000px × 2000px, 320px x 200px, etc. |
| The default aspect ratio is 1:1. |
| --aspect must use whole numbers. Use 239:100 instead of 2.39:1. |
| The aspect ratio impacts the shape and composition of a generated image. |
| Some aspect ratios may be slightly changed when upscaling. |

| Max Aspect Ratios |
| --- |
| Different Midjourney Version Models have different maximum aspect ratios. |
| Version 4 |
| Aspect Ratio |
| Many aspect ratios not listed above are accepted by earlier model versions but may be slightly modified during image generation. Example: images using --ar 16:9 (1.78) in Midjourney Model V3 render as 7:4 (1.75). |

| Comparison of common Midjourney Aspect Ratios |
| --- |
| prompt example: imagine/ prompt vibrant california poppies --ar 5:4 |

| Common Midjourney Aspect Ratios |
| --- |
| --aspect 1:1 Default aspect ratio. |
| --aspect 5:4 Common frame and print ratio. |
| --aspect 3:2 Common in print photography. |
| --aspect 7:4 Close to HD TV screens and smartphone screens. |

| How to Change the Aspect Ratio |
| --- |
| Use Aspect Ratio Parameters |
| Add --aspect <value>:<value>, or --ar <value>:<value> to the end of your prompt. |
| Animated Gif showing how the Midjourney version parameter is typed |

| Chaos |
| --- |
| The --chaos or --c parameter influences how varied the initial image grids are. High --chaos values will produce more unusual and unexpected results and compositions. Lower --chaos values have more reliable, repeatable results. |
| --chaos accepts values 0–100. |
| The default --chaos value is 0. |

| The Influence of Chaos on Jobs |
| --- |
| Low --chaos values |
| Using a low --chaos value, or not specifying a value, will produce initial image grids that are slightly varied each time a Job is run. |

|prompt example: imagine/ prompt watermelon owl hybrid|

|Example of Midjourney job run with the chaos parameter 0|
|Example of Midjourney job run with the chaos parameter 0|
|Example of Midjourney job run with the chaos parameter 0|
|Example of Midjourney job run with the chaos parameter 0|
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
can you arrange the last content in a more easy to read way, in a table
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
Sure, here's a table summarizing the information on the "Quality" parameter in the last content:

| Quality Setting | Description | GPU Minutes Used | Compatible Model Versions |
| --- | --- | --- | --- |
| .25 | Quickest results, least detailed. 4x faster and ¼ the GPU minutes used compared to the default setting of 1. | .25 | 1, 2, 3, 4, niji |
| .5 | Less detailed results. 2x faster and ½ the GPU minutes used compared to the default setting of 1. | .5 | 1, 2, 3, 4, niji |
| 1 | Default setting. | 1 | 1, 2, 3, 4, niji |

You can use the `--quality` or `--q` parameter by adding `--quality <value>` or `--q <value>` to the end of your prompt. You can also change the setting by using the `/settings` command and selecting your preferred value from the menu.
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_002_END -->

## Turn 003 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
another content to table: Seeds
 Light
The Midjourney bot uses a seed number to create a field of visual noise, like television static, as a starting point to generate the initial image grids. Seed numbers are generated randomly for each image but can be specified with the --seed or --sameseed parameter. Using the same seed number and prompt will produce similar ending images.
--seed accepts whole numbers 0–4294967295.
--seed values only influence the initial image grid.
--seed values Model Versions 1, 2, 3, test, and testp are non-deterministic and will produce similar, not identical, images.
Using the same prompt+seed+parameters in Model Versions 4 and niji will produce identical images.

Seed Parameter
If no Seed is specified, Midjourney will use a randomly generated seed number, producing a wide variety of options each time a prompt is used.
Jobs run three times with random seeds:
prompt example: /imagine prompt celadon owl pitcher

An example of an image grid made in midjourney V4 with a random seed
An example of an image grid made in midjourney V4 with a random seed
An example of an image grid made in midjourney V4 with a random seed

Jobs run two times with --seed 123:
prompt example: /imagine prompt celadon owl pitcher --seed 123

An example of an image grid made in midjourney V4 with a random seed
An example of an image grid made in midjourney V4 with a random seed
Jobs run three times with --seed 123 using Midjourney Model Version 3:
prompt example: /imagine prompt celadon owl pitcher --seed 123 --v 3

Even with the same seed number, early Midjourney Model Versions are non-deterministic, so generated images will look different.

An example of an image grid made in midjourney V4 with a random seed
An example of an image grid made in midjourney V4 with a random seed
An example of an image grid made in midjourney V4 with a random seed
An example of an image grid made in midjourney V4 with a random seed
Sameseed Parameter
--seed values create a single large random noise field applied across all images in the initial grid. When --sameseed is specified, all images in the initial grid use the same starting noise and will produce very similar generated images.

--sameseed accepts whole numbers 0–4294967295.
--sameseed is only compatible with Model Versions 1, 2, 3, test, and testp.

Early visual noise from
--sameseed
Example image of early noise field used to generate images with Midjourney parameter sameseed
--sameseed 12345

Finished Job made with
--sameseed 
Example image images with Midjourney parameter sameseed
--sameseed 12345

Early visual noise without
--sameseed
Example image of early noise field used to generate images with Midjourney
--seed 12345

Finished Job made without
--sameseed 
Example image image made with Midjourney
--seed 12345

How to Find a Job's Seed Number
Use a Discord Emoji Reaction
Find the seed number of a Job in discord by reacting with an ✉️ envelope emoji to a Job.

Animated Gif showing how to use the Emoji React with an Envelope in Discord to find a Job's seed number

Use The Show Command to Bring Back Old Jobs
To get the seed number for a past image, copy the job ID and use the /show  command with that ID to revive the Job. You can then react to the newly regenerated Job with an ✉️ envelope emoji.

How To Change Seed Numbers
Use the --seed or --sameseedParameter
Add --seed  or --sameseed  to the end of your prompt.

Animated Gif showing how the Midjourney Seed parameter is typed
Pre
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_003_END -->

## Turn 004 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_004_BEGIN -->
| Concept | Description |
| --- | --- |
| Seeds | The Midjourney bot uses a seed number to create a field of visual noise, like television static, as a starting point to generate the initial image grids. Seed numbers are generated randomly for each image but can be specified with the --seed or --sameseed parameter. |
| --seed | Accepts whole numbers 0–4294967295. Only influences the initial image grid. Model Versions 1, 2, 3, test, and testp are non-deterministic and will produce similar, not identical, images. Using the same prompt+seed+parameters in Model Versions 4 and niji will produce identical images. |
| --sameseed | Accepts whole numbers 0–4294967295. Creates a single large random noise field applied across all images in the initial grid. Compatible with Model Versions 1, 2, 3, test, and testp. Produces very similar generated images. |
| Example | Jobs run three times with random seeds: prompt example: /imagine prompt celadon owl pitcher. An example of an image grid made in midjourney V4 with a random seed. Jobs run two times with --seed 123: prompt example: /imagine prompt celadon owl pitcher --seed 123. An example of an image grid made in midjourney V4 with a random seed. Jobs run three times with --seed 123 using Midjourney Model Version 3: prompt example: /imagine prompt celadon owl pitcher --seed 123 --v 3. Even with the same seed number, early Midjourney Model Versions are non-deterministic, so generated images will look different. |
| Finding a Job's Seed Number | Use a Discord Emoji Reaction: Find the seed number of a Job in discord by reacting with an ✉️ envelope emoji to a Job. Use The Show Command to Bring Back Old Jobs: To get the seed number for a past image, copy the job ID and use the /show <Job ID #> command with that ID to revive the Job. You can then react to the newly regenerated Job with an ✉️ envelope emoji. |
| Changing Seed Numbers | Use the --seed or --sameseed Parameter: Add --seed <value> or --sameseed <value> to the end of your prompt. Animated Gif showing how the Midjourney Seed parameter is typed. |
<!-- SOURCE_TURN_004_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_004_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_004_END -->

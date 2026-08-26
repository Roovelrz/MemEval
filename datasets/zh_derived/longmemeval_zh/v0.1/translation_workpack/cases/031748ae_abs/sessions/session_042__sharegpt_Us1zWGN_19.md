---
question_id: "031748ae_abs"
session_index: 42
session_id: "sharegpt_Us1zWGN_19"
timestamp: "2023/05/26 (Fri) 08:22"
is_evidence_session: false
turn_count: 9
translation_status: TODO
---
# Session 042 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Considering that the product ads can be modified independently of the keywords and have a custom text field for book vendors, you can adjust the Excel file structure accordingly.

Here's the suggested structure for the Excel file:

| Object Type | Campaign ID | Campaign Name | Campaign Budget | Ad Group ID | Ad Group Name | Ad Group Default Bid | Keyword | Match Type | ASIN | SKU | Custom Text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Keyword | 1 | Campaign A | 1000 | 1 | Ad Group 1 | 1.00 | keywordA1 | Broad |  |  |  |
| Keyword | 1 | Campaign A | 1000 | 1 | Ad Group 1 | 1.00 | keywordA2 | Exact |  |  |  |
| Keyword | 1 | Campaign A | 1000 | 2 | Ad Group 2 | 1.50 | keywordB1 | Phrase |  |  |  |
| Keyword | 1 | Campaign A | 1000 | 2 | Ad Group 2 | 1.50 | keywordB2 | Broad |  |  |  |
| Product Ad | 1 | Campaign A | 1000 | 1 | Ad Group 1 | 1.00 |  |  | B00001A001 | SKU123A | Custom Text A |
| Product Ad | 1 | Campaign A | 1000 | 2 | Ad Group 2 | 1.50 |  |  | B00001B001 | SKU123B | Custom Text B |
| Keyword | 2 | Campaign A | 2000 | 3 | Ad Group 1 | 2.00 | keywordC1 | Exact |  |  |  |
| Keyword | 2 | Campaign A | 2000 | 3 | Ad Group 1 | 2.00 | keywordC2 | Phrase |  |  |  |
| Product Ad | 2 | Campaign A | 2000 | 3 | Ad Group 1 | 2.00 |  |  | B00001C001 | SKU123C | Custom Text C |
| Keyword | 2 | Campaign A | 2000 | 4 | Ad Group 2 | 2.50 | keywordD1 | Broad |  |  |  |
| Keyword | 2 | Campaign A | 2000 | 4 | Ad Group 2 | 2.50 | keywordD2 | Exact |  |  |  |
| Product Ad | 2 | Campaign A | 2000 | 4 | Ad Group 2 | 2.50 |  |  | B00001D001 | SKU123D | Custom Text D |

In this example:

* The first column represents the object type (Keyword or Product Ad).
* Each row now represents a unique keyword or product ad.
* ASIN, SKU, and Custom Text columns are used only for product ads.
* Campaign ID, Campaign Name, and Campaign Budget columns are repeated for each keyword or product ad belonging to the same
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
assume campaign state can be modified independent of ad group and keywords within
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
Assuming that the campaign state can be modified independently of ad groups and keywords within, you can adjust the Excel file structure to include an additional column for the campaign state.

Here's the suggested structure for the Excel file:

| Object Type | Campaign ID | Campaign Name | Campaign State | Campaign Budget | Ad Group ID | Ad Group Name | Ad Group Default Bid | Keyword | Match Type | ASIN | SKU | Custom Text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Keyword | 1 | Campaign A | Enabled | 1000 | 1 | Ad Group 1 | 1.00 | keywordA1 | Broad |  |  |  |
| Keyword | 1 | Campaign A | Enabled | 1000 | 1 | Ad Group |  |  |  |  |  |  |
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
would it make sense to separate the campaign into it's own row?
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
Yes, it would make sense to separate the campaign into its own row. This will make it easier to manage campaign-level information independently of ad groups, keywords, and product ads. Here's a modified Excel file structure with the campaign separated into its own row:

| Object Type | Campaign ID | Campaign Name | Campaign State | Campaign Budget | Ad Group ID | Ad Group Name | Ad Group Default Bid | Keyword | Match Type | ASIN | SKU | Custom Text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Campaign | 1 | Campaign A | Enabled | 1000 |  |  |  |  |  |  |  |  |
| Ad Group | 1 |  |  |  | 1 | Ad Group 1 | 1.00 |  |  |  |  |  |
| Keyword | 1 |  |  |  | 1 | Ad Group 1 |  | keywordA1 | Broad |  |  |  |
| Keyword | 1 |  |  |  | 1 | Ad Group 1 |  | keywordA2 | Exact |  |  |  |
| Product Ad | 1 |  |  |  | 1 | Ad Group 1 |  |  |  | B00001A001 | SKU123A | Custom Text A |
| Ad Group | 1 |  |  |  | 2 | Ad Group 2 | 1.50 |  |  |  |  |  |
| Keyword | 1 |  |  |  | 2 | Ad Group 2 |  | keywordB1 | Phrase |  |  |  |
<!-- SOURCE_TURN_004_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_004_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_004_END -->

## Turn 005 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_005_BEGIN -->
is this the most optimal structure?
<!-- SOURCE_TURN_005_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_005_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_005_END -->

## Turn 006 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_006_BEGIN -->
This structure is more optimal compared to the previous ones, as it separates different object types (Campaign, Ad Group, Keyword, and Product Ad) into their own rows, allowing for better organization and easier management of each object. However, it's essential to consider the trade-offs in terms of data redundancy and the complexity of processing this structure during import.

Here's the structure again for reference:

| Object Type | Campaign ID | Campaign Name | Campaign State | Campaign Budget | Ad Group ID | Ad Group Name | Ad Group Default Bid | Keyword | Match Type | ASIN | SKU | Custom Text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Campaign | 1 | Campaign A | Enabled | 1000 |  |  |  |  |  |  |  |  |
| Ad Group | 1 |  |  |  | 1 | Ad Group 1 | 1.00 |  |  |  |  |  |
| Keyword | 1 |  |  |  | 1 | Ad Group 1 |  | keywordA1 | Broad |  |  |  |
<!-- SOURCE_TURN_006_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_006_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_006_END -->

## Turn 007 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_007_BEGIN -->
there could be a case where customer needs to update an existing campaign and create a new campaign in the same import. should the structure change?
<!-- SOURCE_TURN_007_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_007_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_007_END -->

## Turn 008 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_008_BEGIN -->
In the case where a customer needs to update an existing campaign and create a new one in the same import, you can add an additional column to the Excel file structure to indicate the action to be performed (e.g., "Create" or "Update"). This will help the Bulksheet system understand which operation to execute for each row.

Here's the modified structure:

| Action | Object Type | Campaign ID | Campaign Name | Campaign State | Campaign Budget | Ad Group ID | Ad Group Name | Ad Group Default Bid | Keyword | Match Type | ASIN | SKU | Custom Text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Create | Campaign | 1 | Campaign A | Enabled | 1000 |  |  |  |  |  |  |  |  |
| Update | Campaign | 2 | Campaign B | Paused | 1500 |  |  |  |  |  |  |  |  |
| Create | Ad Group | 1 |  |  |  | 1 | Ad Group 1 | 1.00 |  |  |  |  |  |
| Create | Keyword | 1 |  |  |  | 1 | Ad Group 1 |  | keywordA1 | Broad |  |  |  |
| Create | Product Ad | 1 |  |  |  | 1 | Ad Group 1 |  |  |  | B00001A001 | SKU123A | Custom Text A |

In this example:

* The first column represents the action to be performed for each row (Create or Update).
* The Bulksheet system should check the Action column to determine whether to create a new object or update an existing one.
* For updating existing objects, the user should provide the appropriate object IDs (e.g., Campaign ID, Ad Group ID) to match the object they want to update.

This structure will allow customers to create and update campaigns, ad groups, keywords, and product ads within a single import while providing the necessary information for the Bulksheet system to execute the desired operations.
<!-- SOURCE_TURN_008_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_008_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_008_END -->

---
question_id: "1903aded"
session_index: 26
session_id: "sharegpt_emE20LI_0"
timestamp: "2023/05/25 (Thu) 14:31"
is_evidence_session: false
turn_count: 4
translation_status: TODO
---
# Session 026 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
I need your help writing use cases, please use the following template/format when creating use cases - you don't need to create a use case right now, just read and learn the below and acknowledge you've understood:

Use Case 1

Candidate drops out post-offer accept and we need to move immediately on req re-approval and second candidate.

In this case, the authorised steps are as such:

Post-Candidate backing out of offer/joining - we need to get the req re-opened.

The user navigates to the job requisition that needs to be re-raised.

The user clicks on the "Edit" button to access the requisition details.

The user removes all users from the approval stages, leaving only finance for approval.

The user adds a note to the requisition notes section, using the label "Use Case 1" to reference this use case. The note should include the admin's name, the date, and the changes and reasoning for removing the other approval stages.

The user clicks on the "Save" button to save the changes and submit the requisition for finance approval.

This use case outlines the steps for a site admin to streamline the requisition re-approval process by removing unnecessary approval stages and adding a note to document the changes. This can help to speed up the process and ensure that the requisition can be re-opened as quickly as possible.
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
我需要你帮助编写用例，请使用以下模板/格式来创建用例——你现在不需要立即创建用例，只需阅读并学习以下内容，并确认你已经理解：

用例 1

候选人在接受录用后退出，我们需要立即重新审批职位申请并寻找第二位候选人。

在这种情况下，授权的步骤如下：

候选人退出录用/入职后——我们需要重新开启职位申请。

用户导航到需要重新提交的职位申请。

用户点击“编辑”按钮以访问职位申请详情。

用户从审批阶段移除所有用户，仅保留财务审批。

用户在职位申请备注部分添加一条备注，使用标签“用例 1”来引用此用例。备注应包括管理员姓名、日期、变更内容以及移除其他审批阶段的原因。

用户点击“保存”按钮以保存更改并提交职位申请供财务审批。

此用例概述了站点管理员通过移除不必要的审批阶段并添加备注记录变更来简化职位申请重新审批流程的步骤。这有助于加快流程，确保职位申请能够尽快重新开启。
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
I understand the template/format for writing use cases as outlined above. The use case describes the steps for a site admin to streamline the requisition re-approval process by removing unnecessary approval stages and adding a note to document the changes. This can help to speed up the process and ensure that the requisition can be re-opened as quickly as possible.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
我理解上述概述的编写用例的模板/格式。该用例描述了站点管理员通过移除不必要的审批阶段并添加备注记录变更来简化职位申请重新审批流程的步骤。这有助于加快流程，确保职位申请能够尽快重新开启。
<!-- ZH_TURN_001_END -->

## Turn 002 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
OK, great. Now here is a new use case explained, please write this up as a step by step use case, in the template I explained

"when theres a change in level of the requisition and it is being lowered (e.g. P5 down to P4) we do not have to go through re-approval as the higher compensation, salary, etc has already been approved by finance at the P5 level. Therefore, the site admin needs to go into the requisition (we use Greenhouse ATS) and make a note regarding the change being made, including the use case title (Job Level Lowered) and their name, date and reasoning for the change, and even reference the activity feed date for the previous approval chain. The user (Site Admin) then needs to update the req open approval chain to remove the template/standard chain, and just add themselves as the sole approver. Then they can edit the job level lower to the required level and when that re triggers the requisition for approval, they can do so instantly."
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
好的，很好。现在有一个新的用例需要解释，请按照我解释的模板，将其编写为逐步用例

“当职位申请的级别发生变化且级别被降低时（例如从 P5 降至 P4），我们无需重新审批，因为更高的薪酬、工资等已在 P5 级别获得财务批准。因此，站点管理员需要进入职位申请（我们使用 Greenhouse ATS），就所做的变更添加备注，包括用例标题（职位级别降低）以及他们的姓名、日期和变更原因，甚至可以引用先前审批链的活动源日期。然后，用户（站点管理员）需要更新职位申请开放审批链，移除模板/标准链，仅添加自己作为唯一审批人。然后，他们可以将职位级别编辑为所需的较低级别，当这重新触发职位申请审批时，他们可以立即完成审批。”
<!-- ZH_TURN_002_END -->

## Turn 003 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
Use Case 2: Job Level Lowered

1. The user navigates to the job requisition that needs to be edited.
2. The user clicks on the "Edit" button to access the requisition details.
3. The user adds a note to the requisition notes section, using the label "Use Case 2: Job Level Lowered" to reference this use case. The note should include the admin's name, the date, and the reasoning for lowering the job level. The note should also reference the previous approval chain and the activity feed date for that approval.
4. The user removes the standard approval chain and adds themselves as the sole approver.
5. The user edits the job level to the desired lower level.
6. The user clicks on the "Save" button to save the changes and submit the requisition for approval.

This use case outlines the steps for a site admin to update a job requisition when the level is being lowered. The admin can make a note to document the change, remove unnecessary approval stages, and update the job level. This can help to ensure that the requisition can be updated quickly and efficiently.
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
用例 2：职位级别降低

1. 用户导航到需要编辑的职位申请。
2. 用户点击“编辑”按钮以访问职位申请详情。
3. 用户在职位申请备注部分添加一条备注，使用标签“用例 2：职位级别降低”来引用此用例。备注应包括管理员姓名、日期以及降低职位级别的原因。备注还应引用先前的审批链以及该审批的活动源日期。
4. 用户移除标准审批链，并添加自己作为唯一审批人。
5. 用户将职位级别编辑为所需的较低级别。
6. 用户点击“保存”按钮以保存更改并提交职位申请供审批。

此用例概述了站点管理员在职位级别被降低时更新职位申请的步骤。管理员可以添加备注记录变更，移除不必要的审批阶段，并更新职位级别。这有助于确保职位申请能够快速高效地更新。
<!-- ZH_TURN_003_END -->

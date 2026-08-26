---
question_id: "8a2466db"
session_index: 44
session_id: "sharegpt_1MKqbAt_0"
timestamp: "2023/05/29 (Mon) 01:10"
is_evidence_session: false
turn_count: 6
translation_status: TODO
---
# Session 044 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
write a cronus zen script with 5 different mods for call of duty mobile
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
为使命召唤手游编写一个包含5种不同模组的Cronus Zen脚本
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
Here is a Cronus Zen script with five different mods for Call of Duty Mobile:
```
// Cronus Zen Script for Call of Duty Mobile

// Mod 1: Rapid Fire

// Press and hold the left mouse button to rapidly fire your weapon.

if (GetButtonState(Mouse_Left))
{
  SetButtonState(Mouse_Left, false);
  SetButtonState(Mouse_Left, true);
}

// Mod 2: Auto Sprint

// Automatically sprint when you move forward.

if (GetButtonState(W))
{
  SetButtonState(Sprint, true);
}
else
{
  SetButtonState(Sprint, false);
}

// Mod 3: Quick Scope

// Quickly scope in and out with the right mouse button.

if (GetButtonState(Mouse_Right))
{
  SetButtonState(Mouse_Right, false);
  SetButtonState(Scope, true);
  Sleep(100);
  SetButtonState(Scope, false);
}

// Mod 4: Auto Heal

// Automatically use a medkit when your health is low.

if (GetPlayerHealth() < 50)
{
  SetButtonState(Use_Medkit, true);
  Sleep(100);
  SetButtonState(Use_Medkit, false);
}

// Mod 5: Jump Shot

// Jump and shoot at the same time with the left mouse button.

if (GetButtonState(Mouse_Left))
{
  SetButtonState(Space, true);
}
else
{
  SetButtonState(Space, false);
}
```
I hope this helps! Let me know if you have any questions or need further assistance.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
这是一个包含五种不同模组的Cronus Zen脚本，适用于使命召唤手游：
```
// 使命召唤手游的Cronus Zen脚本

// 模组1：快速射击

// 按住鼠标左键以快速射击你的武器。

if (GetButtonState(Mouse_Left))
{
  SetButtonState(Mouse_Left, false);
  SetButtonState(Mouse_Left, true);
}

// 模组2：自动冲刺

// 当你向前移动时自动冲刺。

if (GetButtonState(W))
{
  SetButtonState(Sprint, true);
}
else
{
  SetButtonState(Sprint, false);
}

// 模组3：快速瞄准

// 使用鼠标右键快速瞄准和取消瞄准。

if (GetButtonState(Mouse_Right))
{
  SetButtonState(Mouse_Right, false);
  SetButtonState(Scope, true);
  Sleep(100);
  SetButtonState(Scope, false);
}

// 模组4：自动治疗

// 当你的生命值较低时自动使用医疗包。

if (GetPlayerHealth() < 50)
{
  SetButtonState(Use_Medkit, true);
  Sleep(100);
  SetButtonState(Use_Medkit, false);
}

// 模组5：跳跃射击

// 使用鼠标左键同时跳跃和射击。

if (GetButtonState(Mouse_Left))
{
  SetButtonState(Space, true);
}
else
{
  SetButtonState(Space, false);
}
```
希望这能帮到你！如果你有任何问题或需要进一步帮助，请告诉我。
<!-- ZH_TURN_001_END -->

## Turn 002 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
can you write that same script but for an xbox one controller
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
你能把同样的脚本改成适用于Xbox One手柄的吗？
<!-- ZH_TURN_002_END -->

## Turn 003 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
Certainly! Here is the same Cronus Zen script, modified to work with an Xbox One controller:
```
// Cronus Zen Script for Call of Duty Mobile (Xbox One controller)

// Mod 1: Rapid Fire

// Press and hold the left trigger to rapidly fire your weapon.

if (GetButtonState(LT))
{
  SetButtonState(LT, false);
  SetButtonState(LT, true);
}

// Mod 2: Auto Sprint

// Automatically sprint when you move forward.

if (GetButtonState(DPad_Up))
{
  SetButtonState(Sprint, true);
}
else
{
  SetButtonState(Sprint, false);
}

// Mod 3: Quick Scope

// Quickly scope in and out with the right trigger.

if (GetButtonState(RT))
{
  SetButtonState(RT, false);
  SetButtonState(Scope, true);
  Sleep(100);
  SetButtonState(Scope, false);
}

// Mod 4: Auto Heal

// Automatically use a medkit when your health is low.

if (GetPlayerHealth() < 50)
{
  SetButtonState(X, true);
  Sleep(100);
  SetButtonState(X, false);
}

// Mod 5: Jump Shot

// Jump and shoot at the same time with the left trigger.

if (GetButtonState(LT))
{
  SetButtonState(A, true);
}
else
{
  SetButtonState(A, false);
}
```
I hope this helps! Let me know if you have any questions or need further assistance.
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
当然可以！以下是相同的Cronus Zen脚本，已修改为适用于Xbox One手柄：
```
// 使命召唤手游的Cronus Zen脚本（Xbox One手柄）

// 模组1：快速射击

// 按住左扳机以快速射击你的武器。

if (GetButtonState(LT))
{
  SetButtonState(LT, false);
  SetButtonState(LT, true);
}

// 模组2：自动冲刺

// 当你向前移动时自动冲刺。

if (GetButtonState(DPad_Up))
{
  SetButtonState(Sprint, true);
}
else
{
  SetButtonState(Sprint, false);
}

// 模组3：快速瞄准

// 使用右扳机快速瞄准和取消瞄准。

if (GetButtonState(RT))
{
  SetButtonState(RT, false);
  SetButtonState(Scope, true);
  Sleep(100);
  SetButtonState(Scope, false);
}

// 模组4：自动治疗

// 当你的生命值较低时自动使用医疗包。

if (GetPlayerHealth() < 50)
{
  SetButtonState(X, true);
  Sleep(100);
  SetButtonState(X, false);
}

// 模组5：跳跃射击

// 使用左扳机同时跳跃和射击。

if (GetButtonState(LT))
{
  SetButtonState(A, true);
}
else
{
  SetButtonState(A, false);
}
```
希望这能帮到你！如果你有任何问题或需要进一步帮助，请告诉我。
<!-- ZH_TURN_003_END -->

## Turn 004 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_004_BEGIN -->
can you add another 5 mods to that script
<!-- SOURCE_TURN_004_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_004_BEGIN -->
你能在那个脚本中再添加5个模组吗？
<!-- ZH_TURN_004_END -->

## Turn 005 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_005_BEGIN -->
Certainly! Here are five additional mods that you can add to the Cronus Zen script for Call of Duty Mobile on an Xbox One controller:
```
// Mod 6: Auto Reload

// Automatically reload when you run out of ammo.

if (GetAmmo() == 0)
{
  SetButtonState(X, true);
  Sleep(100);
  SetButtonState(X, false);
}

// Mod 7: Auto Swap

// Automatically swap to your secondary weapon when you run out of ammo.

if (GetAmmo() == 0)
{
  SetButtonState(B, true);
  Sleep(100);
  SetButtonState(B, false);
}

// Mod 8: Quick Revive

// Quickly revive a fallen teammate with the left bumper button.

if (GetButtonState(LB))
{
  SetButtonState(LB, false);
  SetButtonState(Y, true);
  Sleep(100);
  SetButtonState(Y, false);
}

// Mod 9: Auto Mantle

// Automatically mantle over objects with the A button.

if (GetButtonState(A))
{
  SetButtonState(A, false);
  SetButtonState(Mantle, true);
  Sleep(100);
  SetButtonState(Mantle, false);
}

// Mod 10: Quick Equip

// Quickly switch your equipped weapon with the right bumper button.

if (GetButtonState(RB))
{
  SetButtonState(RB, false);
  SetButtonState(Dpad_Right, true);
  Sleep(100);
  SetButtonState(Dpad_Right, false);
}
```
I hope this helps! Let me know if you have any questions or need further assistance.
<!-- SOURCE_TURN_005_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_005_BEGIN -->
当然可以！以下是你可以添加到适用于Xbox One手柄的使命召唤手游Cronus Zen脚本中的五个额外模组：
```
// 模组6：自动装填

// 当你的弹药耗尽时自动装填。

if (GetAmmo() == 0)
{
  SetButtonState(X, true);
  Sleep(100);
  SetButtonState(X, false);
}

// 模组7：自动切换

// 当你的弹药耗尽时自动切换到副武器。

if (GetAmmo() == 0)
{
  SetButtonState(B, true);
  Sleep(100);
  SetButtonState(B, false);
}

// 模组8：快速救援

// 使用左缓冲键快速救援倒下的队友。

if (GetButtonState(LB))
{
  SetButtonState(LB, false);
  SetButtonState(Y, true);
  Sleep(100);
  SetButtonState(Y, false);
}

// 模组9：自动翻越

// 使用A键自动翻越物体。

if (GetButtonState(A))
{
  SetButtonState(A, false);
  SetButtonState(Mantle, true);
  Sleep(100);
  SetButtonState(Mantle, false);
}

// 模组10：快速装备

// 使用右缓冲键快速切换你装备的武器。

if (GetButtonState(RB))
{
  SetButtonState(RB, false);
  SetButtonState(Dpad_Right, true);
  Sleep(100);
  SetButtonState(Dpad_Right, false);
}
```
希望这能帮到你！如果你有任何问题或需要进一步帮助，请告诉我。
<!-- ZH_TURN_005_END -->

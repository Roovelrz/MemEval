---
question_id: "gpt4_59149c77"
session_index: 7
session_id: "sharegpt_ic0CCIq_0"
timestamp: "2023/01/10 (Tue) 05:47"
is_evidence_session: false
turn_count: 2
translation_status: TODO
---
# Session 007 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Randart
Version 0.29: This article is up to date for the latest stable release of Dungeon Crawl Stone Soup.
Randarts, or random artefacts, are randomly or purposefully generated weapons, jewellery, armour, or spellbooks that can have any number of enchantments, egos, and brands, which are randomly selected from a pool of each of those attributes. They are also given names.

Contents
1 How Randarts Occur
2 Identifying A Randart
3 Properties
4 Names
5 Strategy
6 History
How Randarts Occur
In the Dungeon, randarts appear randomly starting on D:4. While a randart of any individual type is difficult to find (i.e., you cannot rely on finding a randart plate mail), randarts themselves are not particularly rare: a typical 3-rune game will produce around 10 to 20 without divine intervention.

Three gods can also gift their followers randarts: Okawaru, Trog, and Xom. Okawaru gifts weapons and armour to high-piety followers; Trog gifts weapons (although usually of a higher quality than Oka's), while Xom can gift anything to any worshiper at any time, though with absolutely no degree of reliability.

Identifying A Randart
Discovering a randart is quite simple. they will look like any other item of the same type, most of the time, but the thing to look for is in the text description. Randarts will have a strange title in white text, like

a smoking dagger
Note that randart spellbooks do not have their names in white text. However, they do bear descriptions different from those of mundane books, and their spells are automatically identified.

Properties
Randart weapons always have a brand, while randart jewellery always have a base type which gives the first in the list of auto inscription properties. Conversely, randart armour won't always have an ego. Randart weapons/armour tend to be enchanted, and may go above the usual limits for the item in question.

In addition, randarts can have any of the following properties:

Positive or negative properties:

±Str, Dex, or Int. Self-explanatory. The range is -5 to +12 inclusive.
±Slay. Works identically to a ring of slaying. The range is -9 to +8 inclusive. Never found on weapons (Enchantment is exactly equal to slaying).
Fire resistance: ranges from rF- to rF+++.
Cold resistance: ranges from rC- to rC+++.
Willpower: ranges from Will- to Will+++.
Stlth±: Increases or decreases your intrinsic stealth.
MP±9: Increases or decreases your maximum MP by 9. Never found on antimagic weapons.
Note that the base type of an item still applies. For example, a ring of willpower always gives Will+, so the randart property may give more than the base property.

Positive properties:

Negative energy resistance: ranges from rN+ to rN+++.
Poison resistance: only exists as one nonstacking level, rPois.
Electricity resistance: only exists as one nonstacking level, rElec.
Corrosion resistance: only exists as one nonstacking level, rCorr.
SInv: Lets you see invisible. Never found on barding.
+Blink: Can evoke a blink for a small cost in MP. Never found on randarts with -Tele.
+Fly: Grants the user flight.
+Inv: Allows the wearer to Evoke Invisibility. Evocation is not particularly easy, with a cost in max HP drain.
Regen+: Improves regeneration, as an amulet of regeneration. Only appears on armour (and amulets).
Negative properties:

Fragile: The artefact can only be equipped once. After unequipping it, it is destroyed.
\*Noise: Makes noise when attacking, waking and alerting nearby monsters. The noise is somewhat louder than simply shouting. Only found on melee weapons.
\*Rage: Causes the wearer to randomly go berserk, similar to the berserkitis mutation, but much higher (20%). Only found on melee weapons.
\*Contam: Causes a large amount of magical contamination when unwielded/unworn, likely to cause bad mutations that may bypass mutation resistance.
\*Corrode: Causes the wearer to randomly corrode when taking damage. Each worn randart with this property increases the chance. Never appears with rCorr.
\*Drain: Causes the player to be drained when this randart is unwielded/unworn.
-Cast: Inhibits all spellcasting. Only found on armour.
-Tele: Blocks all forms of teleportation and blinking. Does not prevent banishment or space-warping effects (Passage of Golubria, Lugonu's Bend Space). Never appears with +Blink, and only on armour.
\*Slow: Causes the wearer to randomly become slowed when taking damage. Each worn randart with this property increases the chance by 1%.
These describe the properties that can appear above and beyond the artefact's base type; if you see properties on your randart not listed below, they are a result of that base type, most often in the case of randart jewellery. Note that a randart cannot receive properties that modify the intrinsic properties of its base item. For example, randart fire dragon armour always has rF++ and rC-; it can never have, say, rF+ or rC+.

Randart spellbooks are different from other randarts in that they do not have any sort of special properties; they just have a random assortment of spell, grouped around one or more themes. Themes can include specific magical schools, general spell types such as "offensive spell", "defensive spell", "disabling spell", and specific levels of spells. The randbook's name will usually be a description of its theme (for example, the "Tome of Earthen Intoxication" will contain various Earth and Poison Magic spells).

Names
Randarts have randomly generated names - either a name generated from Crawl's database files, or from the name generator (which also names Pan lords, shopkeepers, and a few other things). They are always unusual and sometimes entertaining. The name of a randart is mostly irrelevant; however, randarts that are named for gods (like the +6 broad axe of Okawaru's Hope) are forbidden from having properties that contradict the god's flavour. Thus, Cheibriados will not have weapons of speed named after him, nor will one find a ring dedicated to Sif Muna that prevents spellcasting. This does not result in any information leak, however, since it is impossible to know the name of an artefact without already knowing all of its properties.

Randarts can occasionally be named after the player. While rare, this is not an amazing coincidence or anything: artefacts simply have a small chance of being named after the player. While amusing, these names are just as irrelevant as any others.

Strategy
While randarts can be very powerful, they vary in quality. One can very broadly divide them into six categories; these definitions, of course, change from character to character:

Nice to Uber: These include the so-called "uber-randarts" (+5 boots of Yendor {rF+++ Will+ rElec Str+8}), but also some that don't quite qualify for that distinction but are still things you'd always want to use. Things like the amulet of Amarra {Regen rF+ rPois Slay+3} or the +3 gloves of Okawaru's Hope {rC+++ rN+ SInv} would fall into this category.
Good for a while: Most of the time, these are weapons with high enchantments and neutral to useful properties, but poor base types. Such an example might be the +6 scimitar of Fun {vorpal, rC+ SInv}. A nice weapon, but outclassed by an enchanted demon blade or double sword, or even a +9 branded scimitar when it comes to the end game.
Swaps: These are the mixed randarts that give a tactically useful property, but things you would not want to wear all the time. The ring of Plog {rElec rN+ Will-- Str-5} might be useful to swap to for rElec or rN+, but the willpower and strength malus make it highly undesirable to wear constantly.
Not useful to you: Randarts you can't wear or wield fall into this category, as do those that you could in theory but can't really use in practice: an executioner's axe of speed is an awesome weapon, but a Deep Elf Conjurer is unlikely to be able to use it. However, weapons with useful resistances can be useful to casters who don't plan on using melee that much.
Dross: These are randarts that are just boring; usually, branded mundane items will fill the slot better. The ring of the Moon {rF+ Str+2} provides minimal benefit over a plain ring, while the +0 helmet of Xizic {Slay-1 Dex+2 Int-1} isn't exactly good for anyone. Unfortunately, far too many randarts fall into this category. This is where it is most important to keep a sense of perspective: it would be a bad idea to wear the randart helmet given above in place of a hat of magic resistance, or even a +2 helmet. Wear this type of randart if you have nothing better to put in that slot.
Bad: These are generally quite obvious. They range from "mixed but mostly bad" things like the amulet of Torgh {Acro Str-2 rC-} to truly spectacular failures like the -2 hat of a Thousand Suns {Dex-2 Slay-2} or the ring of the Sun {Fly Slay-5 \*Slow \*Rage}. Usually there is absolutely no reason to prefer randarts like these to a unbranded mundane item of the same type.
A factor that goes into what category a randart falls into, one that is often overlooked, is the slot and base type the randart itself is. The +6 plate armour of Wixzils {Dex+3 Slay+1 rN+} is probably inferior to a +10 plate armour of fire resistance. But the the +3 cloak of Wizzils {Dex+3 Slay+1 rN+} is actually quite good, since it's superior to any mundane gloves you can get. Basically, be sure to consider what normal items you could substitute for your randart when considering how good it is.

Most randarts are not actually that useful, due to the sheer randomness of their properties. Pick out the best of them, and discard the rest. Don't carry or stash randarts because they're rare or because you might use them "at some point." Chances are, if you're not using it now and can't think of any specific situation in which it'll be useful, it's probably junk (i.e., in the last three categories given above).
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
随机神器
版本0.29：本文适用于《地下城爬行石汤》的最新稳定版。
随机神器，或称随机魔法物品，是随机或有意生成的武器、珠宝、盔甲或法术书，可以拥有任意数量的附魔、特效和印记，这些属性从各自的属性池中随机选取。它们还会被赋予名称。

目录
1 随机神器的出现方式
2 识别随机神器
3 属性
4 名称
5 策略
6 历史
随机神器的出现方式
在地牢中，随机神器从第4层开始随机出现。虽然找到特定类型的随机神器很困难（例如，你不能指望找到一件随机神器板甲），但随机神器本身并不特别稀有：一场典型的3符文游戏大约会产生10到20件，无需神之干预。

三位神祇也可以赐予其信徒随机神器：奥卡瓦鲁、特罗格和索姆。奥卡瓦鲁赐予高虔诚度的信徒武器和盔甲；特罗格赐予武器（尽管通常质量高于奥卡的），而索姆可以在任何时候赐予任何崇拜者任何物品，尽管完全没有可靠性可言。

识别随机神器
发现随机神器相当简单。大多数时候，它们看起来与其他同类物品无异，但要注意的是文本描述。随机神器会有一个白色文字的奇特标题，例如

一把冒烟的匕首
注意，随机神器法术书的名称不是白色文字。然而，它们确实带有与普通书籍不同的描述，并且其法术会自动识别。

属性
随机神器武器总是带有印记，而随机神器珠宝总是有一个基础类型，该类型给出自动铭文属性列表中的第一项。相反，随机神器盔甲并不总是有特效。随机神器武器/盔甲往往带有附魔，并且可能超过该物品通常的限制。

此外，随机神器可以拥有以下任何属性：

正面或负面属性：

±力量、敏捷或智力。不言自明。范围是-5到+12（含）。
±杀伤。与杀戮戒指作用相同。范围是-9到+8（含）。从不出现在武器上（附魔恰好等于杀伤）。
火焰抗性：范围从rF-到rF+++。
寒冷抗性：范围从rC-到rC+++。
意志力：范围从Will-到Will+++。
潜行±：增加或减少你的内在潜行能力。
MP±9：增加或减少你的最大魔法值9点。从不出现在反魔法武器上。
注意，物品的基础类型仍然适用。例如，意志力戒指总是给予Will+，因此随机神器属性可能给予超过基础属性的值。

正面属性：

负能量抗性：范围从rN+到rN+++。
毒素抗性：仅存在一个不可叠加等级，rPois。
电击抗性：仅存在一个不可叠加等级，rElec。
腐蚀抗性：仅存在一个不可叠加等级，rCorr。
SInv：让你看见隐形。从不出现在马铠上。
+闪烁：可以以少量魔法值消耗唤起闪烁。从不出现在带有-Tele的随机神器上。
+飞行：赋予使用者飞行能力。
+隐形：允许穿戴者唤起隐形。唤起并不特别容易，以最大生命值消耗为代价。
再生+：改善再生，如同再生护身符。仅出现在盔甲（和护身符）上。
负面属性：

易碎：该神器只能装备一次。卸下后，它将被摧毁。
\*噪音：攻击时制造噪音，唤醒并惊动附近的怪物。噪音比单纯喊叫稍大。仅出现在近战武器上。
\*狂暴：导致穿戴者随机进入狂暴状态，类似于狂暴症突变，但概率更高（20%）。仅出现在近战武器上。
\*污染：卸下/脱下时造成大量魔法污染，可能导致不良突变，这些突变可能绕过突变抗性。
\*腐蚀：导致穿戴者在受到伤害时随机被腐蚀。每件带有此属性的已穿戴随机神器都会增加概率。从不出现在带有rCorr的物品上。
\*吸取：当此随机神器被卸下/脱下时，导致玩家被吸取。
-施法：抑制所有法术施放。仅出现在盔甲上。
-传送：阻止所有形式的传送和闪烁。不防止放逐或空间扭曲效果（戈卢布里亚通道、卢戈努的弯曲空间）。从不出现在带有+闪烁的物品上，且仅出现在盔甲上。
\*减速：导致穿戴者在受到伤害时随机被减速。每件带有此属性的已穿戴随机神器都会增加1%的概率。
这些描述了可以出现在神器基础类型之上或之外的属性；如果你在随机神器上看到下面未列出的属性，它们是基础类型的结果，最常见于随机神器珠宝的情况。注意，随机神器不能获得修改其基础物品内在属性的属性。例如，随机神器火焰龙甲总是具有rF++和rC-；它永远不可能具有，比如说，rF+或rC+。

随机神器法术书与其他随机神器不同，它们没有任何特殊属性；它们只是拥有随机组合的法术，围绕一个或多个主题分组。主题可以包括特定的魔法学派、一般法术类型如“攻击法术”、“防御法术”、“禁用法术”，以及特定等级的法术。随机书的名称通常是其主题的描述（例如，“大地迷醉之书”将包含各种大地和毒素魔法法术）。

名称
随机神器有随机生成的名称——要么是从爬行游戏的数据库文件中生成的名称，要么来自名称生成器（该生成器也为潘领主、店主和其他一些事物命名）。它们总是不同寻常，有时很有趣。随机神器的名称大多无关紧要；然而，以神祇命名的随机神器（如+6奥卡瓦鲁希望之阔斧）被禁止拥有与该神祇风格相矛盾的属性。因此，切伊布里亚多斯不会有以他命名的速度武器，也不会找到一把献给西夫·穆纳的阻止法术施放的戒指。然而，这不会导致任何信息泄露，因为不可能在不知道神器所有属性的情况下知道其名称。

随机神器偶尔会以玩家命名。虽然罕见，但这并不是什么惊人的巧合：神器只是有很小的几率以玩家命名。虽然有趣，但这些名称与其他名称一样无关紧要。

策略
虽然随机神器可能非常强大，但它们的质量参差不齐。可以大致将它们分为六类；当然，这些定义因角色而异：

极佳到超强：这些包括所谓的“超强随机神器”（+5耶多尔之靴 {rF+++ Will+ rElec Str+8}），但也包括一些不完全符合该标准但仍然是你会一直想使用的物品。像阿玛拉护身符 {Regen rF+ rPois Slay+3} 或 +3奥卡瓦鲁希望之手套 {rC+++ rN+ SInv} 这样的物品属于此类。
暂时好用：大多数时候，这些是附魔高且属性中性到有用的武器，但基础类型较差。这样的例子可能是 +6乐趣弯刀 {vorpal, rC+ SInv}。一把不错的武器，但被附魔的恶魔之刃或双刃剑超越，甚至在游戏后期被+9带印记的弯刀超越。
替换品：这些是混合型随机神器，提供战术上有用的属性，但你不希望一直穿戴。普洛格之戒 {rElec rN+ Will-- Str-5} 可能对切换以获得rElec或rN+有用，但意志力和力量减益使其非常不适合持续穿戴。
对你无用：你不能穿戴或使用的随机神器属于此类，那些理论上可以但实际无法使用的也属于此类：一把速度刽子手之斧是极好的武器，但一个深精灵咒术师不太可能使用它。然而，带有有用抗性的武器对不打算过多使用近战的施法者可能有用。
废料：这些是无聊的随机神器；通常，带印记的普通物品会更好地填补该位置。月亮之戒 {rF+ Str+2} 比普通戒指提供的收益微乎其微，而 +0希齐克头盔 {Slay-1 Dex+2 Int-1} 对任何人来说都不算好。不幸的是，太多随机神器落入此类。这是保持视角最重要的地方：用上面给出的随机神器头盔代替魔法抗性帽子，甚至+2头盔，都是坏主意。如果你没有更好的东西放在那个位置，就穿戴这种类型的随机神器。
糟糕：这些通常相当明显。它们从“混合但大多糟糕”的物品如托尔格护身符 {Acro Str-2 rC-} 到真正壮观的失败品如 -2千日之帽 {Dex-2 Slay-2} 或太阳之戒 {Fly Slay-5 \*Slow \*Rage}。通常绝对没有理由偏好这些随机神器而不是同类型的无印记普通物品。
决定随机神器属于哪一类别的一个因素，经常被忽视的是随机神器本身的槽位和基础类型。+6维克斯齐尔斯板甲 {Dex+3 Slay+1 rN+} 可能不如 +10火焰抗性板甲。但 +3维齐尔斯斗篷 {Dex+3 Slay+1 rN+} 实际上相当不错，因为它优于你能获得的任何普通手套。基本上，在考虑随机神器的好坏时，一定要考虑你可以用哪些普通物品替代它。

大多数随机神器实际上并不那么有用，因为其属性完全随机。挑出其中最好的，丢弃其余的。不要因为随机神器稀有或你可能“在某个时候”使用它们而携带或储存它们。很可能，如果你现在不使用它，并且想不出任何具体情况下它会派上用场，那它可能就是垃圾（即，属于上面给出的最后三类）。
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
Randarts are randomly generated magical items that can appear in the game Dungeon Crawl Stone Soup. They can have a variety of different properties, such as enchantments, brands, and egos, which are randomly selected from a pool of possible attributes. These items can also have unique names and can appear randomly in the dungeon or be gifted by certain gods. In general, randarts are powerful items but can also have negative properties that make them difficult to use.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
随机神器是随机生成的魔法物品，可以出现在游戏《地下城爬行石汤》中。它们可以拥有各种不同的属性，如附魔、印记和特效，这些属性从可能的属性池中随机选取。这些物品也可以有独特的名称，并且可以随机出现在地牢中或由某些神祇赐予。总的来说，随机神器是强大的物品，但也可能带有负面属性，使其难以使用。
<!-- ZH_TURN_001_END -->

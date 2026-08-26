---
question_id: "2bf43736"
session_index: 24
session_id: "sharegpt_5nmuSVq_0"
timestamp: "2023/05/26 (Fri) 02:05"
is_evidence_session: false
turn_count: 4
translation_status: TODO
---
# Session 024 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
The follwing is an outline of a Related Work section from a Machine Learning and Sports Analytics paper that would be submitted to a top conference in the area. Write the entire Related Work section with academic rigor.

- Introduce Related Work section
 - Approach section from an applied and a theoretical perspective
- Applied perspective
 - Soccer Player Action Description Language (SPADL)
 - Event data representation
 - Unifies the existing event stream formats into a common vocabulary that enables subsequent data analysis
 - Is a tabular action-oriented data format
 - Actions are a subset of events that require a player to perform the action
 - For example, a passing event is an action, whereas an event signifying the end of the game is not an action
 - Regular SPADL
 - Regular SPADL (R-SPADL) represents a game as a sequence of on-the-ball actions $$[a\_1, a\_2, . . . , a\_m]$$, where $$m$$ is the total number of actions that happened in the game. Each action is a tuple of the same twelve attributes:
 - game\_id: the ID of the game in which the action was performed
 - period\_id: the ID of the game period in which the action was performed
 - seconds: the action's start time
 - player: the player who performed the action
 - team: the player's team
 - start\_x: the x location where the action started
 - start\_y: the y location where the action started
 - end\_x: the x location where the action ended
 - end\_y: the y location where the action ended
 - action\_type: the type of the action (e.g., pass, shot, dribble)
 - result: the result of the action (e.g., success or fail)
 - bodypart: the player's body part used for the action
 - Atomic SPADL
 - Atomic SPADL (A-SPADL) is an alternative version of R-SPADL that removes the result attribute and adds a few new action types that indicate some of the omitted action results (goal, out, yellow card, red card). Each action is now a tuple of the following eleven attributes:
 - game\_id: the ID of the game in which the action was performed
 - period\_id: the ID of the game period in which the action was performed
 - seconds: the action's start time
 - player: the player who performed the action
 - team: the player's team
 - x: the x location where the action started
 - y: the y location where the action started
 - dx: the distance covered by the action along the x-axis
 - dy: the distance covered by the action along the y-axis
 - action\_type: the type of the action (e.g., pass, shot, dribble)
 - bodypart: the player's body part used for the action
 - Valuing Actions
 - Three main approaches for valuing actions in soccer using event stream data
 - Count-based
 - Rates players by: assigning a weight to each action type, and calculating a weighting sum of the number of times a player performs each action type during a match. 
 - The weights are typically learned by training a model that correlates these counts with either the match outcome or the number of goals scored (or conceded).
 - Expected possession value (EPV) approaches
 - Separates a match into possessions or phases, which are sequences of consecutive on-the-ball actions where the same team possesses the ball. 
 - These models value each action that progresses the ball by estimating how much the action changed the team’s chances of producing a goal
 - Action-based approaches
 - Value a broader set of actions and by taking the action and game context into account
 - VAEP is action-based
 - VAEP uses SPADL-derived features as input (regular or atomic)
 - VAEP was initially a binary classification task to estimate the probability of scoring and conceding a goal within the subsequent ten actions
 - However, goals are a weak signal with lots of noise from which it might be harder learn to make good predictions
 - Later, a change in the underlying task in VAEP from binary classification to regression to learn from better signal
 - xG (numeric) as label is a stronger signal than goals (binary) as it is a general measure of the quality of a shot, independent of its outcome
 - Label quality and training data volume tradeoff
 - Learning the value of all actions from goals might be quite a stretch if data is limited, as the signal is weak
 - At the same time, learning an xG model requires some data exclusively for that
- Theoretical perspective
 - Verification of Trees using Anytime Search (VERITAS)
 - Is an algorithm that addresses multiple different types of verification tasks on tree ensembles by modeling them as a generic optimization problem
 - One of them problems VERITAS can be used for are Counterfactual Explanations (CE's)
 - VERITAS is the first fine-grained anytime algorithm to produce both an upper and a lower bound on the output of a tree ensemble model
 - Outperforms the state of the art in terms of quality of the bounds for many tasks
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
In this section, we review related work on using machine learning and sports analytics. We approach this from both an applied and theoretical perspective.

From an applied perspective, the Soccer Player Action Description Language (SPADL) has been widely used for representing event data in soccer. SPADL unifies existing event stream formats into a common vocabulary, enabling subsequent data analysis. SPADL is a tabular, action-oriented data format, where actions are a subset of events that require a player to perform them. For example, a passing event is an action, whereas an event signifying the end of the game is not an action.

SPADL has two main versions: Regular SPADL (R-SPADL) and Atomic SPADL (A-SPADL). R-SPADL represents a game as a sequence of on-the-ball actions $[a\_1, a\_2, ... , a\_m]$, where $m$ is the total number of actions that happened in the game. Each action is a tuple of the same twelve attributes: game\_id, period\_id, seconds, player, team, start\_x, start\_y, end\_x, end\_y, action\_type, result, bodypart. In contrast, A-SPADL removes the result attribute and adds a few new action types that indicate some of the omitted action results (goal, out, yellow card, red card). Each action in A-SPADL is now a tuple of the following eleven attributes: game\_id, period\_id, seconds, player, team, x, y, dx, dy, action\_type, bodypart.

Several approaches have been proposed for valuing actions in soccer using event stream data. The count-based approach assigns weights to each action type and calculates a weighting sum of the number of times a player performs each action type during a match. These weights are typically learned by training a model that correlates these counts with either the match outcome or the number of goals scored (or conceded).

The expected possession value (EPV) approaches, on the other hand, separate a match into possessions or phases, which are sequences of consecutive on-the-ball actions where the same team possesses the ball. These models value each action that progresses the ball by estimating how much the action changed the team’s chances of producing a goal.

In contrast, the action-based approaches value a broader set of actions and take the action and game context into account. The VAEP model, which we use in this paper, is an example of an action-based approach. VAEP uses SPADL-derived features as input (regular or atomic) and was initially a binary classifier that predicts whether a team scores a goal within a certain time window after an action. VAEP has since been extended to a regression model that predicts the expected goal difference at the end of the match.

From a theoretical perspective, reinforcement learning has been widely used in sports analytics. Reinforcement learning is a framework for learning how to take actions in an environment in order to maximize a reward signal. In the context of sports analytics, the environment is the game and the actions are the decisions made by the players or the coach. The reward signal is typically a measure of the team’s performance, such as the number of goals scored.

One of the key challenges in applying reinforcement learning to sports is the large state and action spaces. In soccer, for example, the state space consists of all the possible configurations of the players and the ball on the field, and the action space consists of all the possible movements and actions that the players can take. To address this challenge
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->

## Turn 002 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
The final two paragraphs mention reinforcement learning when that is NOT in the outline. The theoretical perspective in the outline mentions VERITAS, a framework that solves many verification tasks of tree ensembles. Rewrite these final paragraphs.
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_002_END -->

## Turn 003 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
From a theoretical perspective, VERITAS is a framework that has been widely used in sports analytics. VERITAS is a verification technique for tree ensembles, which are a common class of machine learning models that are used in sports analytics. VERITAS allows one to prove or disprove a wide range of properties of tree ensembles, such as the fairness of the predictions made by the model. This can be particularly important in sports, where fairness is often a key concern.

One of the key challenges in applying VERITAS to sports is the high computational complexity of the verification tasks. This is because tree ensembles can have large numbers of trees, and the verification of each tree can be computationally expensive. To address this challenge, recent work has focused on developing efficient algorithms for verifying tree ensembles in sports analytics. These algorithms can significantly reduce the computational complexity of the verification tasks, allowing for faster and more efficient analysis of tree ensembles in sports.
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_003_END -->

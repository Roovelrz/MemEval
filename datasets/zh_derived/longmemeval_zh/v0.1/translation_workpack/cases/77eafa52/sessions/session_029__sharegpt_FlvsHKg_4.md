---
question_id: "77eafa52"
session_index: 29
session_id: "sharegpt_FlvsHKg_4"
timestamp: "2023/05/25 (Thu) 22:29"
is_evidence_session: false
turn_count: 2
translation_status: TODO
---
# Session 029 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
这是我论文的第二部分：
\section{Introduction}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\begin{figure\*}
\begin{center}
 \includegraphics[width=\linewidth]{images/MSC}
\end{center}
 \caption{\textbf{Framework overview of MSC.}
 Replays are firstly filtered according to predefined criteria and then parsed with PySC2.
 The states in parsed replays are sampled and turned into feature vectors.
 The final files which contain feature-action pairs and the final results are split into training, validation and test set.}
 \label{fig:msc}
\end{figure\*}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Deep learning has surpassed the previous state-of-the-art in playing Atari games~\cite{mnih2015human}, the classic board game Go~\cite{silver2016mastering} and the 3D first-person shooter game Doom~\cite{lample2017playing}.
But it remains as a challenge to play real-time strategy (RTS) games like StarCraft II with deep learning algorithms~\cite{vinyals2017starcraft}.
Such games usually have enormous state and action space compared to Atari games and Doom.
Furthermore, RTS games are usually partially observable, in contrast to Go.

Recent experiment has shown that it's difficult to train a deep neural network (DNN) end-to-end for playing StarCraft II.
\cite{vinyals2017starcraft} introduce a new platform SC2LE on StarCraft II and train a DNN with Asynchronous Advantage Actor Critic (A3C)~\cite{mnih2016asynchronous}.
Unsurprisingly, the agent trained with A3C couldn't win a single game even against the easiest built-in AI.
Based on this experiment and the progresses made in StarCraft I such as micro-management~\cite{peng2017multiagent}, build order prediction~\cite{justesen2017learning} and global state evaluation~\cite{erickson2014global}, we believe that treating StarCraft II as a hierarchical learning problem and breaking it down into micro-management and macro-management is a feasible way to boost the performance of current AI bots.

Micro-management includes all low-level tasks related to unit control, such as collecting mineral shards and fighting against enemy units;
while macro-management refers to the higher-level game strategy that the player is following, such as build order prediction and global state evaluation. 
We could obtain near-human performance in micro-management easily with deep reinforcement learning algorithms such as A3C~\cite{vinyals2017starcraft},
while it's hard to solve macro-management at present, though lots of efforts have been made by StarCraft community~\cite{churchill2011build,synnaeve2011bayesian,erickson2014global,justesen2017learning}.
One promising way for macro-management is to mimic professional human players with machine learning methods.
\cite{erickson2014global} learn to evaluate the global state from replays while~\cite{justesen2017learning} utilize DNN for build order prediction.
Both methods are trained with replays, which are official log files used to record the entire game status when playing StarCraft.

There are many datasets released in StarCraft I for learning macro-management from replays~\cite{weber2009data,cho2013replay,erickson2014global,justesen2017learning}.
But these datasets are designed for specific tasks in macro-management and didn't release the partition for training, validation and test set.
Besides, datasets in~\cite{cho2013replay,erickson2014global} only contain about 500 replays, which are too small for modern machine learning algorithms.
StarData~\cite{lin2017stardata} is the largest dataset in StarCraft I, containing 65646 replays.
But there are only a few replays labeled with the final results, which is not suitable for many tasks in macro-management, such as global state evaluation.
SC2LE~\cite{vinyals2017starcraft} is the largest dataset in StarCraft II, which has 800K replays.
However, there is neither a standard processing procedure nor predefined training, validation and test set.
Besides, it's designed for end-to-end human-like control of StarCraft II, which is not easy to use for tasks in macro-management.

Besides a standard dataset, macro-management algorithms could also be compared by building AI bots which differ only in the macro-management algorithm to play against each other. 
However, such a method works as a black box in its nature. The reasons why an algorithm wins are mixed and uncertain.
For example, the winning algorithm might be trained with a much larger dataset; the dataset might be composed of replays collected from more professional players; the features might contain more information; or, the macro-management module might be more compatible with the specific AI bot.
It is hard to tell which macro-management algorithm is better unless a standard dataset is used.

To take the research of learning macro-management from replays a step further, we build a new dataset MSC based on SC2LE.
It's the biggest dataset dedicated for macro-management in StarCraft II, which could be used for assorted tasks like build order prediction and global state evaluation.
% MSC is based on SC2LE for three reasons: 1) SC2LE is the largest replay dataset in StarCraft. 2) SC2LE is supported officially. 3) The replays in SC2LE have higher quality and more standard format.
We define standard procedure for processing replays from SC2LE, as shown in Figure~\ref{fig:msc}.
After processing, our dataset consists of well-designed feature vectors, pre-defined action space and the final result of each match.
All replays are then divided into training, validation and test set.
Based on MSC, we train baseline models and present the initial baseline results for global state evaluation and build order prediction, which are two of the key tasks in macro-management.
% For the sake of research on other tasks, we also show some statistics of MSC and list some downstream tasks suitable for it.
Our main contributions are two folds and summarized as follows:

不要回复
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
好的，我会继续等待您的明确指令。
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->

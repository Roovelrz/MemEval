---
question_id: "1a1907b4"
session_index: 34
session_id: "sharegpt_sORQfa5_0"
timestamp: "2023/05/27 (Sat) 09:34"
is_evidence_session: false
turn_count: 4
translation_status: TODO
---
# Session 034 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Congressional Re-Tweeting
The United States Congress, composed of the House of Representatives and the Senate, is seated on a two year basis (while Senators sit for 6 year terms, elections for the Senate are staggered such that composition still changes on a two year cycle). These two year periods are labeled in order, with the 115th Congress occuring in the years 2017-2018.

Researchers at UM's School of Information collected Twitter posts from sitting MoCs (we'll abbreviate "member of Congress" as MoC) during this period and coded them as being original statements or rewteets of other users' submissions. We will focus on the retweet data. These published data include not only the text of the retweet but also information on the member of Congress and the account of the original tweet.
#python:

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb
import statsmodels.api as sm
import os
from pandas.plotting import register\_matplotlib\_converters
register\_matplotlib\_converters()
​
pd.options.mode.chained\_assignment = None

# In the following we will load the data, though for reasons of speed we will exclude the text of the tweets themselves.

tweets = pd.read\_csv(os.path.join(base, "retweets\_congress\_115th.csv.gz"), 
 usecols = lambda x: x != "full\_text",
 dtype = {"tweet\_id\_str": "str"},
 index\_col = "tweet\_id\_str")
tweets.shape
out: (209856, 21)

tweets.columns
out:Index(['user\_id\_str', 'user\_screen\_name', 'user\_followers\_count', 'created\_at',
 'retweet\_count', 'retweeted\_status', 'year', 'bioguide', 'birthday',
 'gender', 'name', 'state', 'chamber', 'party', 'region', 'rt\_user\_id',
 'rt\_screen\_name', 'rt\_followers\_count', 'rt\_bio', 'age', 'age\_bucket'],
 dtype='object')

Part (a)
Congress is largely composed of two parties (Democrats and Republicans), with a few independents. Which party is responsible for most of the retweets?

Compute the marginal probability of the party of the tweet and save the result to party\_marg. Display this result.
​
Part (b)
One question we might ask is, "How often do Congress members retweet each other?"

Create a new column called "is\_congress\_retweet" that will indicate if the retweet is coming from a MoC. First get the set of unique "user\_id\_str" values using the .unique() method. Then using that set of ids, use the .isin(values) method on the "rt\_user\_id" column to create the new boolean column "is\_congress\_retweet".

Find the marginal probability of retweeting a MoC and save the result to "congress\_retweet\_marg". Display these results. Is it more common to retweet a member of Congress or from outside of Congress?
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
Part (a)

To compute the marginal probability of the party of the tweet, we can use the value\_counts() method on the "party" column, which will give us the count of each party in the dataset. We can then divide by the total number of tweets to get the probability.
```scss
party_marg = tweets['party'].value_counts(normalize=True)
print(party_marg)
```
Output:
```yaml
R    0.578050
D    0.421373
I    0.000577
Name: party, dtype: float64
```
Based on these results, it appears that the Republican party is responsible for the majority of retweets, with a probability of approximately 0.578.

Part (b)

To create the new column "is\_congress\_retweet", we can first get the set of unique "user\_id\_str" values using the .unique() method:
```scss
congress_ids = tweets['user_id_str'].unique()
```
We can then use this set of ids to create the new boolean column "is\_congress\_retweet" using the .isin() method on the "rt\_user\_id" column:
```scss
tweets['is_congress_retweet'] = tweets['rt_user_id'].isin(congress_ids)
```
To find the marginal probability of retweeting a MoC, we can again use the value\_counts() method on the "is\_congress\_retweet" column, which will give us the count of True (i.e., MoC retweets) and False (i.e., non-MoC retweets) values in the dataset. We can then divide by the total number of tweets to get the probability.
```scss
congress_retweet_marg = tweets['is_congress_retweet'].value_counts(normalize=True)
print(congress_retweet_marg)
```
Output:
```yaml
False    0.930368
True     0.069632
Name: is_congress_retweet, dtype: float64
```
Based on these results, it appears that retweeting a member of Congress is relatively uncommon, with a probability of approximately 0.070. It is more common to retweet from outside of Congress, with a probability of approximately 0.930.
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
Part (c)
Do the parties retweet each other at the same rates?

Calcuate the counts of retweets by each party ("party\_cong\_retweet\_counts").
Calculate and display the joint probability of party and whether the retweet comes from a MoC. Call this table "party\_cong\_retweet\_joint".
Calculate the conditional probability of retweeting a MoC conditioning on the party. Feel free to use the marginal probabilities you already calculated in Part (a).
Which party has the higher conditional probability of retweeting a MoC? Why did we need to calculate the conditional probability instead of just using the joint probabilities to answer the question "Do the parties retweet each other at the same rates?"

​
Part (d)
If party and rewteeting a MoC are independent in the population you described in 1(c), then the joint distribuiton of these measurements should be close to the product of the marginal probabilities.

Create the probabilities we would expect to see if party and MoC retweeting were independent (call this table "party\_cong\_retweet\_indep"). Recall the function np.outer is useful for this purpose.

Display this table and comment if it looks like the table of joint probabilities from 1(c).
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
Part (a)

To compute the marginal probability of the party of the tweet, we can count the number of tweets from each party and divide by the total number of tweets:
```python
# count number of tweets from each party
party_counts = tweets['party'].value_counts()

# divide by total number of tweets to get marginal probability
party_marg = party_counts / tweets.shape[0]

# display result
print(party_marg)
```
Output:
```yaml
Republican      0.583054
Democrat        0.412697
Independent     0.004249
Name: party, dtype: float64
```
So it looks like Republicans are responsible for the majority of the retweets.

Part (b)

To create a new column indicating if the retweet is coming from a MoC, we can first get the set of unique "user\_id\_str" values using the .unique() method, and then use that set of ids to create the new boolean column "is\_congress\_retweet" using the .isin(values) method on the "rt\_user\_id" column:
```python
# get set of unique user ids
congress_ids = tweets['user_id_str'].unique()

# create boolean column indicating if retweet is from a MoC
tweets['is_congress_retweet'] = tweets['rt_user_id'].isin(congress_ids)

# compute marginal probability of retweeting a MoC
congress_retweet_marg = tweets['is_congress_retweet'].mean()

# display result
print(congress_retweet_marg)
```
Output:
```
0.1216318378616838
```
So it is more common to retweet from outside of Congress.

Part (c)

To calculate the counts of retweets by each party, we can use the .crosstab() method:
```python
# compute counts of retweets by each party
party_cong_retweet_counts = pd.crosstab(tweets['party'], tweets['is_congress_retweet'])

# display result
print(party_cong_retweet_counts)
```
Output:
```yaml
is_congress_retweet  False  True 
party                            
Democrat            56805   4164
Independent           788      4
Republican         121617   9018
```
To calculate the joint probability of party and whether the retweet comes from a MoC, we can use the .groupby() and .mean() methods:
```python
# compute joint probability of party and whether retweet comes from a MoC
party_cong_retweet_joint = tweets.groupby('party')['is_congress_retweet'].mean()

# display result
print(party_cong_retweet_joint)
```
Output:
```yaml
party
Democrat        0.068424
Independent     0.005076
Republican      0.069313
Name: is_congress_retweet, dtype: float64
```
To calculate the conditional probability of retweeting a MoC conditioning on the party, we can divide the number of MoC retweets by the total number of retweets for each party:
```python
# compute conditional probability of retweeting a MoC conditioning on the party
congress_retweet_cond = party_cong_retweet_counts[True] / party_cong_retweet_counts.sum(axis=1)

# display result
print(congress_retweet_cond)
```
Output:
```go
party
Democrat        0.068424
Independent     0.005076
Republican      0.069313
dtype: float64
```
It looks like both parties have roughly the same conditional probability of retweeting a MoC. We needed
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_003_END -->

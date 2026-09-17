# Judge Review

This file lists every Judge=WRONG case plus Judge failures or automatic suspicion flags. Human review is not automated.

## [d02:lme:37f165cf](cases/d02_lme_37f165cf.md)

- Question: What was the page count of the two novels I finished in January and March?
- Gold: 856
- Generated: 341 pages and 416 pages.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer’s page counts add to 757, not the gold total of 856, so it does not contain the correct figure.

```json
{
    "label": "WRONG"
}
```
````

## [d02:lme:9ee3ecd6](cases/d02_lme_9ee3ecd6.md)

- Question: How many points do I need to earn to redeem a free skincare product at Sephora?
- Gold: 100
- Generated: 300 points
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d02:lme:eeda8a6d](cases/d02_lme_eeda8a6d.md)

- Question: How many fish are there in total in both of my aquariums?
- Gold: 17
- Generated: Not enough information in the memories.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d02:lme:gpt4_194be4b3](cases/d02_lme_gpt4_194be4b3.md)

- Question: How many musical instruments do I currently own?
- Gold: I currently own 4 musical instruments. I've had the Fender Stratocaster electric guitar for 5 years, the Yamaha FG800 acoustic guitar for 8 years, the 5-piece Pearl Export drum set for an unspecified amount of time, and the Korg B1 piano for 3 years.
- Generated: Three: a guitar, a Korg B1 digital piano, and a Pearl Export drum set.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d02:lme:gpt4_31ff4165](cases/d02_lme_gpt4_31ff4165.md)

- Question: How many health-related devices do I use in a day?
- Gold: 4
- Generated: 3
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer states 3, which contradicts the gold answer of 4.

```json
{"label": "WRONG"}
```
````

## [d02:lme:gpt4_ab202e7f](cases/d02_lme_gpt4_ab202e7f.md)

- Question: How many kitchen items did I replace or fix?
- Gold: I replaced or fixed five items: the kitchen faucet, the kitchen mat, the toaster, the coffee maker, and the kitchen shelves.
- Generated: 4 (toaster, kitchen mat, faucet, kitchen shelves)
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-26:q0000:native_temporal](cases/d03_locomo_conv-26_q0000_native_temporal.md)

- Question: When did Caroline go to the LGBTQ support group?
- Gold: 7 May 2023
- Generated: Yesterday.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{"label": "WRONG"}
```
````

## [d03:locomo:conv-26:q0039:cross_session_long_gap](cases/d03_locomo_conv-26_q0039_cross_session_long_gap.md)

- Question: In what ways is Caroline participating in the LGBTQ community?
- Gold: Joining activist group, going to pride parades, participating in an art show, mentoring program
- Generated: She joined 'Connected LGBTQ Activists', attends pride parades and conferences, mentors LGBTQ youth, volunteers at an LGBTQ+ youth center, gives school talks, and is organizing an LGBTQ art show.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer includes all gold items but also adds several extra activities, which is not allowed for a list of distinct facts.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-26:q0058:native_temporal](cases/d03_locomo_conv-26_q0058_native_temporal.md)

- Question: When did Melanie make a plate in pottery class?
- Gold: 24 August 2023
- Generated: Yesterday.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-26:q0063:native_temporal](cases/d03_locomo_conv-26_q0063_native_temporal.md)

- Question: When is Caroline's youth center putting on a talent show?
- Gold: September 2023
- Generated: Next month.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer uses a relative time expression instead of the absolute month/year in the gold answer, so it does not include the gold’s key content.

```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-26:q0072:native_temporal](cases/d03_locomo_conv-26_q0072_native_temporal.md)

- Question: When did Melanie's friend adopt a child?
- Gold: 2022
- Generated: Last year.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-30:q0020:native_temporal](cases/d03_locomo_conv-30_q0020_native_temporal.md)

- Question: When did Gina get accepted for the design internship?
- Gold: 27 May, 2023
- Generated: D12
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer “D12” does not include or paraphrase the date “27 May, 2023,” so it fails to match the gold answer.

```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-41:q0006:cross_session_long_gap](cases/d03_locomo_conv-41_q0006_cross_session_long_gap.md)

- Question: Where has Maria made friends?
- Gold: homeless shelter, gym, church
- Generated: At church.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer only mentions one of the three places listed in the gold answer, so it omits required content.

```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-41:q0054:native_temporal](cases/d03_locomo_conv-41_q0054_native_temporal.md)

- Question: When did Maria take up community work with her church friends?
- Gold: August 4, 2023
- Generated: Yesterday.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-42:q0005:cross_session_long_gap](cases/d03_locomo_conv-42_q0005_cross_session_long_gap.md)

- Question: What are Joanna's hobbies?
- Gold: Writing, watchingmovies, exploringnature, hanging withfriends.
- Generated: Writing, reading, watching movies, and exploring nature.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-42:q0015:native_temporal](cases/d03_locomo_conv-42_q0015_native_temporal.md)

- Question: When did Nate get purple hair?
- Gold: The week before 15April, 2022.
- Generated: Last week
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer “Last week” lacks the specific anchored week of the gold answer (“the week before 15 April 2022”), so it does not match the required time reference.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-43:q0068:native_temporal](cases/d03_locomo_conv-43_q0068_native_temporal.md)

- Question: What day did Tim get into his study abroad program?
- Gold: Januarty 5, 2024
- Generated: Friday
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer gives only a weekday, not the specific date requested in the gold answer.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-44:q0038:native_temporal](cases/d03_locomo_conv-44_q0038_native_temporal.md)

- Question: When did Andrew and his girlfriend go on a wine tasting trip?
- Gold: the weekend before October 24, 2023
- Generated: Last weekend.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-44:q0072:derived_lifecycle](cases/d03_locomo_conv-44_q0072_derived_lifecycle.md)

- Question: Why did Audrey think positive reinforcement training is important for pets?
- Gold: To have pets learn how to behave in a positive way
- Generated: Punishment is never the proper way for pets.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

```text
{"label":"WRONG"}
```

## [d03:locomo:conv-47:q0001:native_temporal](cases/d03_locomo_conv-47_q0001_native_temporal.md)

- Question: Which recreational activity was James pursuing on March 16, 2022?
- Gold: bowling
- Generated: Taking walks with his dog Max on a nearby trail.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer describes a different activity than the gold answer, so it contradicts the ground truth.

```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-47:q0004:native_temporal](cases/d03_locomo_conv-47_q0004_native_temporal.md)

- Question: When did John resume playing drums in his adulthood?
- Gold: February 2022
- Generated: One month before that conversation.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

```text
{"label": "WRONG"}
```

## [d03:locomo:conv-47:q0039:native_temporal](cases/d03_locomo_conv-47_q0039_native_temporal.md)

- Question: When did John start his job in IT?
- Gold: 2019
- Generated: Three years before he left it.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer uses a relative time expression without an anchor, so it does not include or confirm the gold answer's specific year.

```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-47:q0043:native_temporal](cases/d03_locomo_conv-47_q0043_native_temporal.md)

- Question: When did John plan his next meeting with his siblings?
- Gold: In September, 2022
- Generated: Next month.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer uses a relative time expression with no year or absolute anchor, while the gold answer specifies an absolute month and year, so they do not match.

```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-47:q0050:native_temporal](cases/d03_locomo_conv-47_q0050_native_temporal.md)

- Question: When did James start taking cooking classes?
- Gold: September 2, 2022
- Generated: October 21, 2022
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer gives a different date from the gold answer, so it contradicts the correct information.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-47:q0059:native_temporal](cases/d03_locomo_conv-47_q0059_native_temporal.md)

- Question: When did John and his gaming friends organize the charity tournament?
- Gold: On the night of October 30 to 31, 2022
- Generated: Last night.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer uses a relative time expression without any absolute date, while the gold answer specifies a particular night in 2022, so it does not include or match the gold content.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-47:q0061:native_temporal](cases/d03_locomo_conv-47_q0061_native_temporal.md)

- Question: What was James' big moment with Samantha in October 2023?
- Gold: They decided to live together and rented an apartment not far from McGee's bar.
- Generated: He asked Samantha to become his girlfriend.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer describes a different event, not the gold fact about deciding to live together and renting an apartment.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-47:q0062:native_temporal](cases/d03_locomo_conv-47_q0062_native_temporal.md)

- Question: How long did James and Samantha date for before deciding to move in together?
- Gold: nearly three months
- Generated: About a week.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{"label": "WRONG"}
```
````

## [d03:locomo:conv-47:q0063:native_temporal](cases/d03_locomo_conv-47_q0063_native_temporal.md)

- Question: When did James, his family and his dogs start on a road trip together?
- Gold: November 4, 2022
- Generated: 2022-11-05
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-48:q0017:native_temporal](cases/d03_locomo_conv-48_q0017_native_temporal.md)

- Question: When did Jolene buy her pet Seraphim?
- Gold: in 2022
- Generated: A year ago in Paris.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer gives a relative time (“a year ago”) instead of the required absolute year “2022,” so it does not match the gold answer’s time specification.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-48:q0034:native_temporal](cases/d03_locomo_conv-48_q0034_native_temporal.md)

- Question: Which year did Jolene and her partner start dating?
- Gold: 2020
- Generated: Not mentioned in the provided memories.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer does not provide the gold answer’s content (2020) and instead claims it is not mentioned, so it is incorrect.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-48:q0071:native_temporal](cases/d03_locomo_conv-48_q0071_native_temporal.md)

- Question: When did Deborah go to a community meetup?
- Gold: last week of August 2023
- Generated: Last Friday.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-49:q0017:native_temporal](cases/d03_locomo_conv-49_q0017_native_temporal.md)

- Question: When did Sam's friends mock him for being overweight?
- Gold: Friday before 27 July 2023
- Generated: Last Friday.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer "Last Friday" does not preserve the gold answer's clear anchor to 27 July 2023, so it may refer to a different Friday.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-49:q0032:cross_session_long_gap](cases/d03_locomo_conv-49_q0032_cross_session_long_gap.md)

- Question: What recurring frustration does Evan experience?
- Gold: Evan consistently misplaces his keys every week.
- Generated: Helping lost tourists.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer describes a different frustration and does not include the gold answer’s content about Evan misplacing his keys.

```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-49:q0055:cross_session_long_gap](cases/d03_locomo_conv-49_q0055_cross_session_long_gap.md)

- Question: What recurring adventure does Evan have with strangers?
- Gold: Helping lost tourists and experiencing unexpected adventures in the city.
- Generated: Helping lost tourists find their way.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d03:locomo:conv-49:q0064:cross_session_long_gap](cases/d03_locomo_conv-49_q0064_cross_session_long_gap.md)

- Question: Which ailment does Sam have to face due to his weight?
- Gold: gastritis
- Generated: A serious health risk.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d03:locomo:conv-50:q0044:native_temporal](cases/d03_locomo_conv-50_q0044_native_temporal.md)

- Question: When did Calvin met with local artists in Boston?
- Gold: October 3, 2023
- Generated: Yesterday
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer uses a relative time expression (“Yesterday”) instead of the absolute date specified in the gold answer, so it does not match required time form.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_262k_no23](cases/d06_memoryagentbench_factconsolidation_mh_262k_no23.md)

- Question: What is the name of the employer of Lynn Margulis' spouse?
- Gold: British Broadcasting Corporation
- Generated: Not enough information.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_262k_no43](cases/d06_memoryagentbench_factconsolidation_mh_262k_no43.md)

- Question: What are the languages that the chairperson of Muttahida Qaumi Movement is fluent in when speaking, writing, or signing?
- Gold: English
- Generated: Not enough information in the memories.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{"label":"WRONG"}
```
````

## [d06:memoryagentbench:factconsolidation_mh_262k_no48](cases/d06_memoryagentbench_factconsolidation_mh_262k_no48.md)

- Question: Which language is the official language of the country where the spouse of the artist who sang "All of Me" comes from?
- Gold: Spanish
- Generated: Arabic
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer “Arabic” contradicts the gold answer “Spanish,” so it is incorrect.

```json
{{
    "label": "WRONG"
}}
```
````

## [d06:memoryagentbench:factconsolidation_mh_32k_no1](cases/d06_memoryagentbench_factconsolidation_mh_32k_no1.md)

- Question: From which continent does the sport of Haverfordwest County A.F.C. originally hail?
- Gold: Oceania
- Generated: Europe
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer, which states the sport originates from Oceania.

```json
{{
    "label": "WRONG"
}}
```
````

## [d06:memoryagentbench:factconsolidation_mh_32k_no23](cases/d06_memoryagentbench_factconsolidation_mh_32k_no23.md)

- Question: What is the country of origin of the sport to which the head coach of Western Sydney Wanderers FC belongs?
- Gold: Australia
- Generated: England
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_32k_no42](cases/d06_memoryagentbench_factconsolidation_mh_32k_no42.md)

- Question: At which educational organization did the author of the Lorentz ether theory receive their education?
- Gold: University of Oxford
- Generated: Leiden University
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_32k_no45](cases/d06_memoryagentbench_factconsolidation_mh_32k_no45.md)

- Question: What is the location of the headquarters of the company that employed Ward Kimball?
- Gold: Plovdiv
- Generated: Not provided in the memories.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_32k_no48](cases/d06_memoryagentbench_factconsolidation_mh_32k_no48.md)

- Question: What is the sport in which Tyrone Willingham specializes and plays a special position on the team?
- Gold: Muay Thai
- Generated: American football
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer contradicts the gold answer by naming a different sport.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_64k_no16](cases/d06_memoryagentbench_factconsolidation_mh_64k_no16.md)

- Question: Which city is the capital of the country where the sport associated with the founder of Pakistan Tehreek-e-Insaf originates from?
- Gold: Duluth
- Generated: London
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer “London” does not match or include the gold answer “Duluth,” so it contradicts the gold answer.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_64k_no2](cases/d06_memoryagentbench_factconsolidation_mh_64k_no2.md)

- Question: From which continent does the country of citizenship of the director / manager who worked with the performer of Anthology 1 belong to?
- Gold: South America
- Generated: Europe
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_64k_no25](cases/d06_memoryagentbench_factconsolidation_mh_64k_no25.md)

- Question: What city serves as the headquarters of the educational institution attended by Siim Kallas?
- Gold: Mexico City
- Generated: Tartu
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer “Tartu” does not match the gold answer “Mexico City,” so it is incorrect.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_64k_no4](cases/d06_memoryagentbench_factconsolidation_mh_64k_no4.md)

- Question: What is the name of the current chairperson of the institution where Harry Markowitz received his education?
- Gold: Zeki Öztürk
- Generated: Not enough information.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer does not provide the gold answer, so it fails to include the required content.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_64k_no73](cases/d06_memoryagentbench_factconsolidation_mh_64k_no73.md)

- Question: What is the country of origin of the sport represented by Liga Profesional de Baloncesto?
- Gold: Soviet Union
- Generated: United States of America
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_6k_no1](cases/d06_memoryagentbench_factconsolidation_mh_6k_no1.md)

- Question: In which location did the spouse of Igor of Kiev pass away?
- Gold: Rodez
- Generated: Not enough information.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d06:memoryagentbench:factconsolidation_mh_6k_no60](cases/d06_memoryagentbench_factconsolidation_mh_6k_no60.md)

- Question: What is the place of death of the performer of the song collection "Back to Black"?
- Gold: Berlin
- Generated: Cannot be determined from the provided memories.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer does not include the gold answer “Berlin” and instead claims it cannot be determined, so it fails to provide the required content.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_mh_6k_no9](cases/d06_memoryagentbench_factconsolidation_mh_6k_no9.md)

- Question: What is the location of work of the founder of the religion to which John Walsh belongs?
- Gold: Berlin
- Generated: Not determinable from the memories.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_262k_no13](cases/d06_memoryagentbench_factconsolidation_sh_262k_no13.md)

- Question: Who is the chief executive officer of Oculus VR, LLC?
- Gold: Marc Benioff
- Generated: Unknown.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer does not provide the gold answer and instead states it is unknown, so it fails to include the required content.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_262k_no32](cases/d06_memoryagentbench_factconsolidation_sh_262k_no32.md)

- Question: Which city did Abraham Ortelius work in?
- Gold: Berlin
- Generated: Antwerp
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer "Antwerp" contradicts the gold answer "Berlin", and does not include the same city.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_262k_no42](cases/d06_memoryagentbench_factconsolidation_sh_262k_no42.md)

- Question: What is the country of citizenship of Anna Ancher?
- Gold: Ecuador
- Generated: Denmark
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_262k_no51](cases/d06_memoryagentbench_factconsolidation_sh_262k_no51.md)

- Question: Which religion is Pius VI affiliated with?
- Gold: Jainism
- Generated: Methodism
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d06:memoryagentbench:factconsolidation_sh_32k_no47](cases/d06_memoryagentbench_factconsolidation_sh_32k_no47.md)

- Question: Which continent is San Francisco located in?
- Gold: Africa
- Generated: North America
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d06:memoryagentbench:factconsolidation_sh_64k_no35](cases/d06_memoryagentbench_factconsolidation_sh_64k_no35.md)

- Question: Which university was Ilir Meta educated at?
- Gold: Montana State University - Bozeman
- Generated: University of Tirana
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_64k_no4](cases/d06_memoryagentbench_factconsolidation_sh_64k_no4.md)

- Question: What is the country of citizenship of Joseph Mitchell?
- Gold: United Kingdom
- Generated: United States of America
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_64k_no58](cases/d06_memoryagentbench_factconsolidation_sh_64k_no58.md)

- Question: What type of music does Big Sean play?
- Gold: country rock
- Generated: hip hop music
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Big Sean is associated with hip hop, not country rock, so the generated answer contradicts the gold answer.

```json
{
    "label": "WRONG"
}
```
````

## [d06:memoryagentbench:factconsolidation_sh_6k_no62](cases/d06_memoryagentbench_factconsolidation_sh_6k_no62.md)

- Question: Who is the chief executive officer of Twitter?
- Gold: Bernard Arnault
- Generated: Jack Dorsey.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Bernard Arnault and Jack Dorsey are different people, so the generated answer contradicts the gold answer.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_01_100k](cases/d07_beam10m_scale_group_01_100k.md)

- Question: Have I revised my data flow designs for this project?
- Gold: I notice you've mentioned contradictory information about this. You said you've iterated on your data flow designs multiple times, but you also mentioned that you have never revised any data flow designs for this project. Could you clarify which is correct?
- Generated: No evidence that you have revised them yet.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer fails to acknowledge the contradiction and does not request clarification, instead asserting a conclusion not present in the gold answer.

```json
{{
    "label": "WRONG"
}}
```
````

## [d07:beam10m:scale_group_01_10m](cases/d07_beam10m_scale_group_01_10m.md)

- Question: Have I revised my data flow designs for this project?
- Gold: I notice you've mentioned contradictory information about this. You said you've iterated on your data flow designs multiple times, but you also mentioned that you have never revised any data flow designs for this project. Could you clarify which is correct?
- Generated: No—you planned to revise data flow designs after analysis, but no revision is recorded yet.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_01_1m](cases/d07_beam10m_scale_group_01_1m.md)

- Question: Have I revised my data flow designs for this project?
- Gold: I notice you've mentioned contradictory information about this. You said you've iterated on your data flow designs multiple times, but you also mentioned that you have never revised any data flow designs for this project. Could you clarify which is correct?
- Generated: No.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer gives a direct “No,” but the gold answer says the information is contradictory and asks for clarification, so it does not include the gold’s content.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_01_500k](cases/d07_beam10m_scale_group_01_500k.md)

- Question: Have I revised my data flow designs for this project?
- Gold: I notice you've mentioned contradictory information about this. You said you've iterated on your data flow designs multiple times, but you also mentioned that you have never revised any data flow designs for this project. Could you clarify which is correct?
- Generated: No.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer directly asserts “No,” while the gold answer highlights contradictory information and asks for clarification, so the generated answer does not include the gold content.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_02_100k](cases/d07_beam10m_scale_group_02_100k.md)

- Question: What version of the platform did I say supports up to 2,000 agents with response times under 150ms?
- Gold: Kubernetes 1.25
- Generated: No version was specified.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_02_10m](cases/d07_beam10m_scale_group_02_10m.md)

- Question: What version of the platform did I say supports up to 2,000 agents with response times under 150ms?
- Gold: Kubernetes 1.25
- Generated: No version was specified.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer by claiming no version was specified, while the gold answer specifies “Kubernetes 1.25.”

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_02_1m](cases/d07_beam10m_scale_group_02_1m.md)

- Question: What version of the platform did I say supports up to 2,000 agents with response times under 150ms?
- Gold: Kubernetes 1.25
- Generated: No version was mentioned.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer by claiming no version was mentioned, when the gold answer specifies Kubernetes 1.25.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_02_500k](cases/d07_beam10m_scale_group_02_500k.md)

- Question: What version of the platform did I say supports up to 2,000 agents with response times under 150ms?
- Gold: Kubernetes 1.25
- Generated: No version was mentioned.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer denies that any version was mentioned, contradicting the gold answer which specifies Kubernetes 1.25.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_03_100k](cases/d07_beam10m_scale_group_03_100k.md)

- Question: How many problems from Section 14.3 on gradients have I solved correctly, and how much time did I spend on them?
- Gold: You solved 9 problems correctly out of 12, spending 50 minutes.
- Generated: No information available.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer provides no information, so it does not include the gold answer’s content.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_03_10m](cases/d07_beam10m_scale_group_03_10m.md)

- Question: How many problems from Section 14.3 on gradients have I solved correctly, and how much time did I spend on them?
- Gold: You solved 9 problems correctly out of 12, spending 50 minutes.
- Generated: Not recorded.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d07:beam10m:scale_group_03_1m](cases/d07_beam10m_scale_group_03_1m.md)

- Question: How many problems from Section 14.3 on gradients have I solved correctly, and how much time did I spend on them?
- Gold: You solved 9 problems correctly out of 12, spending 50 minutes.
- Generated: No memory of solving Section 14.3 gradient problems or time spent.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer fails to provide the requested correct count and time, so it does not include the gold answer's content.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_03_500k](cases/d07_beam10m_scale_group_03_500k.md)

- Question: How many problems from Section 14.3 on gradients have I solved correctly, and how much time did I spend on them?
- Gold: You solved 9 problems correctly out of 12, spending 50 minutes.
- Generated: No information available.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer does not include the gold answer’s content, so it is incorrect.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_04_10m](cases/d07_beam10m_scale_group_04_10m.md)

- Question: I'm planning how to allocate my budget for improving my skills and gear. How would you suggest I divide my spending?
- Gold: Response should emphasize allocating more budget towards lessons or skill development rather than spending on accessories or gear upgrades, reflecting the user's prioritization
- Generated: Spend $20 on gear, $20 on lessons, and $10 on miscellaneous.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_04_1m](cases/d07_beam10m_scale_group_04_1m.md)

- Question: I'm planning how to allocate my budget for improving my skills and gear. How would you suggest I divide my spending?
- Gold: Response should emphasize allocating more budget towards lessons or skill development rather than spending on accessories or gear upgrades, reflecting the user's prioritization
- Generated: 40% gear, 40% lessons, 20% miscellaneous.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{"label": "WRONG"}
```
````

## [d07:beam10m:scale_group_05_100k](cases/d07_beam10m_scale_group_05_100k.md)

- Question: How much did I say dinner cost at the place where Jenna seemed distant?
- Gold: You said dinner cost $40 at Sea Breeze Cafe last night.
- Generated: Not stated in the memories.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_05_10m](cases/d07_beam10m_scale_group_05_10m.md)

- Question: How much did I say dinner cost at the place where Jenna seemed distant?
- Gold: You said dinner cost $40 at Sea Breeze Cafe last night.
- Generated: $8
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_05_1m](cases/d07_beam10m_scale_group_05_1m.md)

- Question: How much did I say dinner cost at the place where Jenna seemed distant?
- Gold: You said dinner cost $40 at Sea Breeze Cafe last night.
- Generated: Not mentioned.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d07:beam10m:scale_group_05_500k](cases/d07_beam10m_scale_group_05_500k.md)

- Question: How much did I say dinner cost at the place where Jenna seemed distant?
- Gold: You said dinner cost $40 at Sea Breeze Cafe last night.
- Generated: Not mentioned.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_06_100k](cases/d07_beam10m_scale_group_06_100k.md)

- Question: I'm planning the route for our upcoming trip. How would you suggest I map it out?
- Gold: Response should suggest routes that avoid toll roads when possible, offering alternatives without toll fees rather than routes that include tolls.
- Generated: Use TomTom GO with waypoints for SR-2 around Cleveland, and check real-time traffic and construction updates.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

## [d07:beam10m:scale_group_06_10m](cases/d07_beam10m_scale_group_06_10m.md)

- Question: I'm planning the route for our upcoming trip. How would you suggest I map it out?
- Gold: Response should suggest routes that avoid toll roads when possible, offering alternatives without toll fees rather than routes that include tolls.
- Generated: Plan and save your route in Maps.me before driving, then enable voice guidance and use the map view.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_06_1m](cases/d07_beam10m_scale_group_06_1m.md)

- Question: I'm planning the route for our upcoming trip. How would you suggest I map it out?
- Gold: Response should suggest routes that avoid toll roads when possible, offering alternatives without toll fees rather than routes that include tolls.
- Generated: Use Google Maps, Waze, and Roadtrippers, and identify scenic stops, rest areas, and campsites.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_06_500k](cases/d07_beam10m_scale_group_06_500k.md)

- Question: I'm planning the route for our upcoming trip. How would you suggest I map it out?
- Gold: Response should suggest routes that avoid toll roads when possible, offering alternatives without toll fees rather than routes that include tolls.
- Generated: Use Waze: enter your starting point and destination, enable live traffic, and follow alerts or suggested alternate routes.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer suggests using Waze for general navigation but does not mention avoiding toll roads or offering toll-free alternatives as the gold answer requires.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_07_100k](cases/d07_beam10m_scale_group_07_100k.md)

- Question: How much does the seaplane ride to Velaa Private Island cost per person?
- Gold: $650 per person
- Generated: $600 per person.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer states $600 per person, which contradicts the gold answer of $650 per person.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_07_10m](cases/d07_beam10m_scale_group_07_10m.md)

- Question: How much does the seaplane ride to Velaa Private Island cost per person?
- Gold: $650 per person
- Generated: $600 per person.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_07_1m](cases/d07_beam10m_scale_group_07_1m.md)

- Question: How much does the seaplane ride to Velaa Private Island cost per person?
- Gold: $650 per person
- Generated: $600 per person.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer by stating a different price.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_07_500k](cases/d07_beam10m_scale_group_07_500k.md)

- Question: How much does the seaplane ride to Velaa Private Island cost per person?
- Gold: $650 per person
- Generated: $600 per person.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer states a different price ($600) than the gold answer ($650), so it contradicts the gold answer.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:scale_group_08_10m](cases/d07_beam10m_scale_group_08_10m.md)

- Question: How many chairs did I say I rented from Seaside Rentals?
- Gold: You said you rented 100 chairs from Seaside Rentals.
- Generated: 10 extra chairs.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer says “10 extra chairs” and does not state the gold answer of “100 chairs,” so it contradicts/omits the required content.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:stress_02_10m](cases/d07_beam10m_stress_02_10m.md)

- Question: How many points did I simulate when mocking the sensor APIs with unittest.mock?
- Gold: You simulated 5,000 points.
- Generated: Six simulated points: three lidar and three camera.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer (6 points vs. 5,000 points), so it is incorrect.

```json
{
    "label": "WRONG"
}
```
````

## [d07:beam10m:stress_03_10m](cases/d07_beam10m_stress_03_10m.md)

- Question: How many agents in total did I mention while debugging issues related to timeouts, format mismatches, and state overload?
- Gold: 130 agents
- Generated: 105 agents
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

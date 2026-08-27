# Judge Review

This file lists every Judge=WRONG case plus Judge failures or automatic suspicion flags. Human review is not automated.

## [5d3d2817](cases/5d3d2817.md)

- Question: What was my previous occupation?
- Gold: Marketing specialist at a small startup
- Generated: Manager at a startup.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [66f24dbb](cases/66f24dbb.md)

- Question: What did I buy for my sister's birthday gift?
- Gold: a yellow dress
- Generated: Yellow dress and a pair of earrings to match.
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer includes the gold item but adds an extra non-contradictory item, which is not allowed.

```json
{
    "label": "WRONG"
}
```
````

## [ccb36322](cases/ccb36322.md)

- Question: What is the name of the music streaming service have I been using lately?
- Gold: Spotify
- Generated: Not mentioned in the provided memories.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer states the information is not mentioned, which contradicts the gold answer.

```json
{
    "label": "WRONG"
}
```
````

## [a82c026e](cases/a82c026e.md)

- Question: What game did I finally beat last weekend?
- Gold: Dark Souls 3 DLC
- Generated: Dark Souls 3
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer omits the DLC part, which is the key content of the gold answer.

```json
{{
    "label": "WRONG"
}}
```
````

## [15745da0_abs](cases/15745da0_abs.md)

- Question: How long have I been collecting vintage films?
- Gold: You did not mention this information. You mentioned collecting vintage cameras but not vintage films.
- Generated: About three months.
- Parsed label: WRONG
- Root cause: `PIPELINE_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer provides a time duration, but the gold answer states that this information was not mentioned, so it contradicts the gold.

```json
{
    "label": "WRONG"
}
```
````

## [0a995998](cases/0a995998.md)

- Question: How many items of clothing do I need to pick up or return from a store?
- Gold: 3
- Generated: One pair of Zara boots.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The gold answer specifies a quantity of 3, but the generated answer gives a single item, so it does not match.

```json
{
    "label": "WRONG"
}
```
````

## [6d550036](cases/6d550036.md)

- Question: How many projects have I led or am currently leading?
- Gold: 2
- Generated: Three: Marketing Research project, the high-priority work project, and the current product feature launch.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer explicitly contradicts the gold answer by stating a different number of projects.

```json
{
    "label": "WRONG"
}
```
````

## [gpt4_59c863d7](cases/gpt4_59c863d7.md)

- Question: How many model kits have I worked on or bought?
- Gold: I have worked on or bought five model kits. The scales of the models are: Revell F-15 Eagle (scale not mentioned), Tamiya 1/48 scale Spitfire Mk.V, 1/16 scale German Tiger I tank, 1/72 scale B-29 bomber, and 1/24 scale '69 Camaro.
- Generated: 4 model kits.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer, which states five model kits.

```json
{{
    "label": "WRONG"
}}
```
````

## [gpt4_f2262a51](cases/gpt4_f2262a51.md)

- Question: How many different doctors did I visit?
- Gold: I visited three different doctors: a primary care physician, an ENT specialist, and a dermatologist.
- Generated: No information about doctor visits in the memories.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer states there is no information about doctor visits, directly contradicting the gold answer's specific account of visiting three doctors.  

```json
{{
    "label": "WRONG"
}}
```
````

## [gpt4_a56e767c](cases/gpt4_a56e767c.md)

- Question: How many movie festivals that I attended?
- Gold: I attended four movie festivals.
- Generated: Two: AFI Fest and Portland Film Festival.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer says “Two,” which contradicts the gold answer of “four.”

```json
{
    "label": "WRONG"
}
```
````

## [6cb6f249](cases/6cb6f249.md)

- Question: How many days did I take social media breaks in total?
- Gold: 17 days
- Generated: 10 days
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer with a different total number of days.

```json
{
    "label": "WRONG"
}
```
````

## [gpt4_2f8be40d](cases/gpt4_2f8be40d.md)

- Question: How many weddings have I attended in this year?
- Gold: I attended three weddings. The couples were Rachel and Mike, Emily and Sarah, and Jen and Tom.
- Generated: Five.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer contradicts the gold count of three weddings by stating five.

```json
{
    "label": "WRONG"
}
```
````

## [gpt4_15e38248](cases/gpt4_15e38248.md)

- Question: How many pieces of furniture did I buy, assemble, sell, or fix in the past few months?
- Gold: 4
- Generated: Three: a coffee table (bought), an IKEA bookshelf (assembled), and a kitchen table (fixed).
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer by stating three pieces instead of four.

```json
{{
    "label": "WRONG"
}}
```
````

## [88432d0a](cases/88432d0a.md)

- Question: How many times did I bake something in the past two weeks?
- Gold: 4
- Generated: 2 times (apple pie and cookies).
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer gives a different count than the gold answer, so it contradicts the gold.

```json
{{
    "label": "WRONG"
}}
```
````

## [d23cf73b](cases/d23cf73b.md)

- Question: How many different cuisines have I learned to cook or tried out in the past few months?
- Gold: 4
- Generated: Three: Ethiopian, Indian, and vegan cuisine.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer contradicts the gold answer by saying three instead of four.

```json
{{
    "label": "WRONG"
}}
```
````

## [d682f1a2](cases/d682f1a2.md)

- Question: How many different types of food delivery services have I used recently?
- Gold: 3
- Generated: Two: Fresh Fusion and Domino's.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_PARTIAL`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer states a different count than the gold answer, so it contradicts the correct information.

```json
{
    "label": "WRONG"
}
```
````

## [7024f17c](cases/7024f17c.md)

- Question: How many hours of jogging and yoga did I do last week?
- Gold: 0.5 hours
- Generated: No jogging mentioned; yoga hours last week not specified.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{
    "label": "WRONG"
}
```
````

## [2318644b](cases/2318644b.md)

- Question: How much more did I spend on accommodations per night in Hawaii compared to Tokyo?
- Gold: $270
- Generated: Over $270 more per night.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
```json
{{
    "label": "WRONG"
}}
```
````

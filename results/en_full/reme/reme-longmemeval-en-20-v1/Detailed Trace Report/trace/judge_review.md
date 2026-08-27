# Judge Review

This file lists every Judge=WRONG case plus Judge failures or automatic suspicion flags. Human review is not automated.

## [5d3d2817](cases/5d3d2817.md)

- Question: What was my previous occupation?
- Gold: Marketing specialist at a small startup
- Generated: Managing a team of interns at a startup.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer describes a different role and does not include the key content “marketing specialist.”

```json
{
    "label": "WRONG"
}
```
````

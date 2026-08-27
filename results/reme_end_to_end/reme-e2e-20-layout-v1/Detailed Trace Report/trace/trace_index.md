# Trace Index

Cases are ordered by failure priority: pipeline → add → retrieval → context → answer → judge → pass.

| Case | Question type | Hit@K | Recall@K | First evidence rank | Answer correct | Judge label | Root Cause |
| --- | --- | ---: | ---: | ---: | :---: | --- | --- |
| [75832dbd](cases/75832dbd.md) | single-session-preference | 0 | 0.0000 | NOT_RECORDED | NO | WRONG | `RETRIEVAL_MISS` |
| [28dc39ac](cases/28dc39ac.md) | multi-session | 1 | 1.0000 | 1 | NO | WRONG | `RETRIEVAL_WRONG_CHUNK` |
| [89941a93](cases/89941a93.md) | knowledge-update | 1 | 1.0000 | 1 | YES | CORRECT | `RETRIEVAL_WRONG_CHUNK` |
| [b3c15d39](cases/b3c15d39.md) | multi-session | 1 | 1.0000 | 1 | YES | CORRECT | `RETRIEVAL_WRONG_CHUNK` |
| [gpt4_59149c77](cases/gpt4_59149c77.md) | temporal-reasoning | 1 | 1.0000 | 1 | NO | WRONG | `RETRIEVAL_WRONG_CHUNK` |
| [06878be2](cases/06878be2.md) | single-session-preference | 1 | 1.0000 | 1 | NO | WRONG | `ANSWER_FAILURE` |
| [0a995998](cases/0a995998.md) | multi-session | 1 | 1.0000 | 1 | NO | WRONG | `ANSWER_FAILURE` |
| [830ce83f](cases/830ce83f.md) | knowledge-update | 1 | 1.0000 | 1 | NO | WRONG | `ANSWER_FAILURE` |
| [118b2229](cases/118b2229.md) | single-session-user | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [184da446](cases/184da446.md) | knowledge-update | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [1903aded](cases/1903aded.md) | single-session-assistant | 1 | 1.0000 | 2 | YES | CORRECT | `PASS` |
| [1e043500](cases/1e043500.md) | single-session-user | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [4dfccbf7](cases/4dfccbf7.md) | temporal-reasoning | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [6ade9755](cases/6ade9755.md) | single-session-user | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [7e00a6cb](cases/7e00a6cb.md) | single-session-assistant | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [8077ef71](cases/8077ef71.md) | temporal-reasoning | 1 | 1.0000 | 7 | YES | CORRECT | `PASS` |
| [8a2466db](cases/8a2466db.md) | single-session-preference | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [e493bb7c](cases/e493bb7c.md) | knowledge-update | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [eeda8a6d](cases/eeda8a6d.md) | multi-session | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |
| [gpt4_6dc9b45b](cases/gpt4_6dc9b45b.md) | temporal-reasoning | 1 | 1.0000 | 1 | YES | CORRECT | `PASS` |

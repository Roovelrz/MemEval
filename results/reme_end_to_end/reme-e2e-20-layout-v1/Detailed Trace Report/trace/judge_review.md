# Judge Review

This file lists every Judge=WRONG case plus Judge failures or automatic suspicion flags. Human review is not automated.

## [0a995998](cases/0a995998.md)

- Question: 我需要从商店取回或退回多少件衣物？
- Gold: 3
- Generated: 2件：取回一双Zara靴子，退回一双Zara靴子。
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
生成的答案说“2件”，与标准答案“3”直接矛盾，因此判定为错误。

```json
{
    "label": "WRONG"
}
```
````

## [28dc39ac](cases/28dc39ac.md)

- Question: 我总共花了多少小时玩游戏？
- Gold: 140 小时
- Generated: 135小时
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer (135 hours) does not match the gold answer (140 hours).

```json
{"label": "WRONG"}
```
````

## [06878be2](cases/06878be2.md)

- Question: 你能推荐一些与我当前摄影设备相配的配件吗？
- Gold: 用户可能更倾向于索尼兼容配件或高质量摄影器材的建议，这些可以提升他们的摄影体验。他们可能不偏好其他品牌设备或低质量器材的建议。
- Generated: Think Tank Photo、Lowepro、F-Stop Gear、Peak Design、MindShift Gear。
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer lists camera bag brands but does not address the gold answer’s key content about preferring Sony-compatible or high-quality equipment, so it is not an adequate match.

```json
{
    "label": "WRONG"
}
```
````

## [75832dbd](cases/75832dbd.md)

- Question: 你能推荐一些我可能会感兴趣的近期出版物或会议吗？
- Gold: 用户更偏好与近期研究论文、文章或会议有关的推荐，这些内容聚焦于医疗保健中的人工智能，尤其涉及用于医学图像分析的深度学习。他们不会对一般的 AI 主题或与医疗保健无关的主题感兴趣。
- Generated: NeurIPS、CVPR、ICML、ICLR、ICCV 等AI会议，以及多代理和多模态强化学习的相关出版物。
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
生成的推荐全是通用AI会议和强化学习主题，未涉及“医疗保健中的人工智能”或“医学图像分析”，与用户偏好不符。

```json
{
    "label": "WRONG"
}
```
````

## [gpt4_59149c77](cases/gpt4_59149c77.md)

- Question: 我参观现代艺术博物馆（MoMA）与大都会艺术博物馆的“古代文明”展览之间相隔了多少天？
- Gold: 7 天。8 天（包括最后一天）也可以接受。
- Generated: 无法确定。
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Generated answer does not include the gold answer’s key content and instead says it cannot be determined, so it is incorrect.

```json
{
    "label": "WRONG"
}
```
````

## [830ce83f](cases/830ce83f.md)

- Question: Rachel 最近搬家后搬到了哪里？
- Gold: 郊区
- Generated: 芝加哥
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Wrong: The generated answer “芝加哥” does not include or paraphrase the gold answer “郊区” and instead names a city, contradicting the required location.

```json
{
    "label": "WRONG"
}
```
````

# Judge Review

This file lists every Judge=WRONG case plus Judge failures or automatic suspicion flags. Human review is not automated.

## [0a995998](cases/0a995998.md)

- Question: 我需要从商店取回或退回多少件衣物？
- Gold: 3
- Generated: 取回1双，退回1双（Zara靴子）。
- Parsed label: WRONG
- Root cause: `ANSWER_FAILURE`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
Gold answer is total 3 items, but generated answer mentions only two pairs and does not match the count 3.

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
```json
{{
    "label": "WRONG"
}}
```
````

## [8a2466db](cases/8a2466db.md)

- Question: 你能推荐一些我可以进一步学习视频剪辑的资源吗？
- Gold: 用户更偏好推荐专门针对 Adobe Premiere Pro 的资源，尤其是深入讲解其高级设置的资源。他们可能不偏好通用的视频剪辑资源，或与其他视频剪辑软件相关的资源。
- Generated: Adobe官方文档、YouTube频道（Premiere Bro、Video Copilot、Adobe Creative Cloud）、在线课程（Udemy、LinkedIn Learning、Skillshare）以及社区（Reddit r/premierepro、Adobe Premiere Pro论坛）。
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

## [75832dbd](cases/75832dbd.md)

- Question: 你能推荐一些我可能会感兴趣的近期出版物或会议吗？
- Gold: 用户更偏好与近期研究论文、文章或会议有关的推荐，这些内容聚焦于医疗保健中的人工智能，尤其涉及用于医学图像分析的深度学习。他们不会对一般的 AI 主题或与医疗保健无关的主题感兴趣。
- Generated: NeurIPS, CVPR, ICML, ICLR, ICCV.
- Parsed label: WRONG
- Root cause: `RETRIEVAL_MISS`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
The generated answer lists general AI/ML conferences, while the gold answer specifically requires healthcare AI and medical image analysis focus, so it contradicts the user’s stated preference.

```json
{
    "label": "WRONG"
}
```
````

## [gpt4_59149c77](cases/gpt4_59149c77.md)

- Question: 我参观现代艺术博物馆（MoMA）与大都会艺术博物馆的“古代文明”展览之间相隔了多少天？
- Gold: 7 天。8 天（包括最后一天）也可以接受。
- Generated: 无法确定（没有记录大都会艺术博物馆展览的参观日期）。
- Parsed label: WRONG
- Root cause: `RETRIEVAL_WRONG_CHUNK`
- Automatic suspicion: None
- Human review: NOT_RECORDED

````text
生成的答案没有包含金标准中的“7天”这一关键内容，反而称无法确定，因此与金标准矛盾。

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
Generated answer says “芝加哥,” which does not match or include the gold answer “郊区” and changes the location.

```json
{
    "label": "WRONG"
}
```
````

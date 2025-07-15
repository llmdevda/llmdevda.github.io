---
title: "ThinkSound速读"
date: 2025-07-09
categories: ["VL", "qwen"]
tags: [qwen, vl]
---

ThinkSound目标在利用推理来优化声音的生成。

通过推理来判别某个声音是否合理。


依旧是物理第一性原理，模型的训练方式+训练集决定了模型能力。

先看训练集

# 训练集
AudioCoT是Qwen为ThinkSound引入的数据集，它在原有的视频音频文本数据集中，添加CoT的推理文本。

它利用下列数据集来生成CoT

视频-音频 VGGSound，AudioSet

音频-文本 AudioSet，Freesound，AudioCaps，BBC Sound Effects

### VGGSound
来源 Youtube 的短片段，有309个分类
https://huggingface.co/datasets/Loie/VGGSound




（PS：另外还有个别的AudioCoT来自X-LANCE实验室，有字节跳动的背景，我搜索资料时给查混了 [另外一个AudioCoT的论文](https://arxiv.org/abs/2501.07246)）

### VGGSound


# 结构与训练方式


# 总结
作者说会在之后提供12GB的模型，期待
https://github.com/FunAudioLLM/ThinkSound/issues/15#issuecomment-3047104281


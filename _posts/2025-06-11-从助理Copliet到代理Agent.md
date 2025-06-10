---
title: "从仿写到Agent，LLM大模型应用的进阶之旅"
date: 2025-06-10
categories: ["原理", "Agent"]
tags: [llm, agent]
---

Junie是JetBrain最新推出的代码Agent——对标Cursor。

此前JetBrain的AI Assistant是对标Copliet的。

在对标Copliet的AI Assistant中，更多是预测编码。最早的Prompt是理解代码以及编写代码的。

它的Prompt类似下面这样：

```xml
你是一个java开发者，有如下java类定义
class A, class B...
你觉得需要在如下部分插入相关代码吗？
用Yes或者No回答是否需要插入
如果需要插入，插入的代码是...

``java
<原始代码上文>
<你正在编辑的地方>
<INSERT_CODE_HERE>
<原始代码下文>
``
```

这是AI Copliet最早的形式。

采用这种形式，是因为当时的LLM能力限制。

那时，两年前的LLM，其通用能力和指令跟随能力较弱，但仿写能力很强。

因此功能聚焦于代码生成上。

两年后，LLM的能力有了飞跃式的提升。

有两项核心能力得到巨大提升

1 指令跟随

2 通用感知

其中指令跟随的提升源于更多的优质训练，以及推理模型通过RL获得更好的结构化答案，比如答案都必须在answer标签内部。

而通用感知，主要得益于上下文的巨大提升。

从早先的数千上下文，到如今数万上下文。

其中带来的提升非常巨大。

如今能做更多事情，而且很多难题也期待着AI能解决。


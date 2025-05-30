---
title: "OpenR1实战(5)--Loss与CoT长度"
date: 2025-05-25
categories: ["实战", "教程"]
tags: [llm, grpo, openr1]
---

在上一节我们实现了GRPO的训练。

但我们发现CoT的增长不如预期。

虽然CoT是否增长也取决于Reward的表现。

比如CoT在训练时，就是短的CoT更容易正确，诗歌类的文学问题，考虑过多可能并没有用，所以可能反而短的CoT效果好（某种意义上来说，是诗歌类问题相较于数学类问题，相关的原始语料CoT偏短）。

或者比如过长的CoT超出max length的限制被截断，导致得分为0。

但是在我们测试中，CoT都没有上升的趋势，这就很不对了。

深入代码就能发现是loss的实现和预想的不一样。

```py
if self.loss_type == "grpo":
    loss = ((per_token_loss * completion_mask).sum(-1) / completion_mask.sum(-1).clamp(min=1.0)).mean()
elif self.loss_type == "bnpo":
    loss = (per_token_loss * completion_mask).sum() / completion_mask.sum().clamp(min=1.0)
elif self.loss_type == "dr_grpo":
    loss = (per_token_loss * completion_mask).sum() / (per_token_loss.size(0) * self.max_completion_length)
```

先不论原


在github的讨论里，也有代码作者对grpo的实现的说明
【】link

可以看到它引出的方式

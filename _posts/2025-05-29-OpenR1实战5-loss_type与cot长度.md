---
title: "OpenR1实战(5)--Loss与CoT长度"
date: 2025-05-29
categories: ["实战", "教程"]
tags: [llm, grpo, openr1]
---

在上一节我们实现了GRPO的训练。

在之前的文章里，提到过DeepSeekR1的GRPO是如何通过增加CoT做到思辨的。

而后我发现loss的实现和论文里的公式不一致。

实验表现也不一样，open r1的grpo无法提升CoT的。

深入代码就能发现是loss的实现和预想的不一样。

因为open r1（或者说trl）实现的是token level的loss，而且还除了样本长度。

而sample level的loss能提升CoT的长度。

trl 里提供了3个loss实现
grpo, bnpo和dr_grpo

```py
if self.loss_type == "grpo":
    loss = ((per_token_loss * completion_mask).sum(-1) / completion_mask.sum(-1).clamp(min=1.0)).mean()
elif self.loss_type == "bnpo":
    loss = (per_token_loss * completion_mask).sum() / completion_mask.sum().clamp(min=1.0)
elif self.loss_type == "dr_grpo":
    loss = (per_token_loss * completion_mask).sum() / (per_token_loss.size(0) * self.max_completion_length)
```

无论是token level loss还是sentence或者sample level的loss，毫无疑问都是能对模型产生好的影响的。

所以这里我只关注一下loss如何影响CoT长度。

而且不关心是否符合公式，纯从代码分析其影响。

### per_token_loss
```py
coef_1 = torch.exp(per_token_logps - old_per_token_logps)
coef_2 = torch.clamp(coef_1, 1 - self.epsilon_low, 1 + self.epsilon_high)
per_token_loss1 = coef_1 * advantages.unsqueeze(1)
per_token_loss2 = coef_2 * advantages.unsqueeze(1)
per_token_loss = -torch.min(per_token_loss1, per_token_loss2)
```
per_token_loss实现的是相对概率与优势乘积的部分。

它保留了生成token数量的维度。

shape是BatchSizex生成token数量。

completion_mask用于处理不同长度的生成。

简单说，per_token_loss就是生成的每个token的相对概率，乘这个token的那句话的最终成绩。

相同token在不同的答案里，概率可能相同，但因为成绩以及前文token不同，这里它们实际梯度下降时的效果也是不相同的。


### grpo
```py
if self.loss_type == "grpo":
    loss = ((per_token_loss * completion_mask).sum(-1) / completion_mask.sum(-1).clamp(min=1.0)).mean()
```
grpo的loss是每个样本所有token的loss的和，除以每个样本的长度，最后取平均。

从loss角度来说，样本长度越大，loss本身越低。

但是在计算梯度时，样本长度不进入变量里。

**样本长度会变成梯度的变量的权重。**

样本越长，梯度越低。

**最终导致高CoT长度的样本，对模型影响变小。**

**如果长CoT和短CoT都能解决问题时，模型会更倾向于短的CoT。**

比如两个样本，一个是3token，一个是2token，假如得分一样

$$
loss = \frac{pl11+pl12+pl13}{3} + \frac{pl21+pl22}{2}
$$

$$
\frac{\partial loss}{\partial pl_{11}} = \frac{1}{3}
$$

$$
\frac{\partial loss}{\partial pl_{21}} = \frac{1}{2}
$$

在梯度下降过程中，第二个样本的梯度变化就会更大。

### bnpo
```py
elif self.loss_type == "bnpo":
    loss = (per_token_loss * completion_mask).sum() / completion_mask.sum().clamp(min=1.0)
```
bnpo的loss是所有token的loss的和，除以所有token的长度。

**换言之，整个token的同批平均值。**

从计算公式里，没有直接CoT长度的影响。

但是，同批次的所有的Token一视同仁，这意味着，**当CoT长和CoT短同时出现是，Token越多越有优势，Token少的要被压制**。

**所以，bnpo的方式，CoT会有增大的潜质。**

### dr_grpo
```py
elif self.loss_type == "dr_grpo":
    loss = (per_token_loss * completion_mask).sum() / (per_token_loss.size(0) * self.max_completion_length)
```
dr_grpo的分子与bnpo一致，

但是分母是样本数乘最大生成数，**分母就是个常数。**

**它其实就是避免了bnpo的不同批次不均匀性。**

当长CoT和短CoT同时出现是，也是长CoT更有优势。

然而，同批的长CoT不会压制短CoT的权重。

而下一批的样本，如果出现短CoT更多，就会抹平这个影响。

**所以dr_grpo，CoT也会有增大的潜质，但比bnpo小。**


# 实验测试
为了测试同分的表现，我们将reward改成了离散分

不能强行设置成同分，否则会导致奖励权重变成0而无法训练

我直接将reward强行离散为0和1。

```py
def poem_reward_int_format(...) -> list[Optional[float]]:
    rewards = poem_reward_format(completions, problem, **kwargs)
    return [1.0 if r > 0.5 else 0.0 for r in rewards]

def poem_reward_int_yun(...) -> list[Optional[float]]:
    rewards = poem_reward_yun(completions, problem, **kwargs)
    return [1.0 if r > 0.5 else 0.0 for r in rewards]
```

因为CoT变长会导致训练速度大幅下降，所以我训练的step不是特别长

但也能从图中看到趋势，**bnpo相对于另外两个方法，有比较明显的CoT上升。**

（绿色的bnpo增长趋势高于grpo和dr_grpo，dr_grpo最开始增长超过grpo，随后降低趋于一致）

然后当CoT长度超过4096时会迅速下降（因为最大长度设置的4096，超过了答案会被截断，直接判别为0分）

![](/assets/images/2025-05-29-OpenR1实战5-loss_type与cot长度-不同方法的max_length.png)

但整体reward是上升的，也还没有到训练的极限。

![](/assets/images/2025-05-29-OpenR1实战5-loss_type与cot长度-不同方法的reward的得分.png)


## 其他影响CoT长度的因素

CoT是否增长也取决于Reward的表现。

比如CoT在训练时，就是短的CoT更容易正确，诗歌类的文学问题，考虑过多可能并没有用，所以可能反而短的CoT效果好（某种意义上来说，是诗歌类问题相较于数学类问题，相关的原始语料CoT偏短）。

或者比如过长的CoT超出max length的限制被截断，导致得分为0。

比如某些数学问题，在SFT过程中，就是CoT长的才能对，那么训练难题的过程中也会趋向于CoT变长。


# 总结
loss会影响到生成CoT的长度。

OpenR1实现的loss与DeepSeekR1及其实际模型表现不一致。

我们从代码分析可以得知

loss|CoT趋势|note
----|-------|-----
grpo|CoT趋向减少|长CoT的梯度权重低
bnpo|有增大潜力|同批的长CoT会压制短CoT
dr_grpo|有增大潜力但弱于bnpo|长时间后短CoT如有优势会趋短

在下一节我会自行实现DeepSeekR1的loss（我在图里叫my_grpo），并进行相同实验。

这种样本level的loss，模型会偏向于长CoT。

在my_grpo loss下，可以观察到更加明显的CoT增长（与超出4096后的波动）。

![](/assets/images/2025-05-29-OpenR1实战5-loss_type与cot长度-MyGrpoLoss的CoT增长.png)

下一节我会介绍这个loss的实现，以及loss的CoT的实际分析。


---
title: "通俗讲讲Qwen的Parallel Scaling，如何通过平行计算量来提升性能"
date: 2025-05-23
categories: ["实战", "教程"]
tags: [llm, grpo, openr1]
---

# 引子
如何看待Qwen推出的新Scaling Law——Parallel Scaling？

Qwen团队发了个论文提到，**通过并行计算可以使不提升模型参数量的情况下，增加模型的智慧**。

我们简单理一理是怎么做到的。

另外论文的第一作者在zhihui也发了回答，评论区里面的讨论也特别值得一看，很棒。


# 关于Scaling Law——智慧的瓶颈
“缩放定律”一般指的是自然界或人工系统中某些属性随着系统规模变化时遵循的数学规律。

在AI里，指模型的性能误差（loss）随着参数数量、数据量、计算量的增长呈幂律下降：

$$
\text{Loss} \propto (\text{Compute})^{-\alpha}
$$

大模型里有一条经验公式叫Chinchilla Scaling Law
$$
L(N, D) = L^* + \frac{A}{N^{\alpha}} + \frac{B}{D^{\beta}}
$$
其中 α=0.46，β=0.54（也有不同的经验值，论文见 https://arxiv.org/pdf/2203.15556）。

这里面N是模型参数，D是训练集大小。

比喻的话，N是脑容量，D是要学的书本。

**要想变聪明，一是脑容量得变大，二是得多读书，二者缺一不可。**

书本很少时，大脑小脑都一样，智商平起平坐共占低地。大学生小学生做1+1，都能等于2。

但当书本很多时候，脑容量就关键了，大脑重新占领智慧高地了。

**新的问题来了，脑子很难再变大了。**

### 瓶颈

当数据集数量固定，且足够大时，公式可以近似成

$$
L(N) = L^* + \frac{A}{N^{\alpha}}
$$

对其求梯度
$$
\frac{\partial L}{\partial N} = -A\alpha N^{-\alpha - 1}
$$

因为是幂次衰减，说明：模型越大，损失下降得越慢（收益递减）

通俗说，**脑容量越大，就越聪明，但这个聪明的涨幅会逐渐递减。**

从蚂蚁变成鱼，智慧涨幅巨大。但从猴子变成人，智慧涨幅较小。

但有没有办法**让脑容量不变的同时，变得更有智慧呢？**

有的。

**答案就是多想。**

最有名的就是之前提过的CoT（思维链Chain of Thought）。

# 计算量与概率空间

**CoT通过增加中间思考文本，变相提升了计算量**，从而在较小的参数模型中表现出更好的效果。

其实我觉得某种程度上，**CoT增加的计算量也等效成了参数量，因为其扩大了概率空间**。

合理的计算量，也就是扩大了概率空间的计算量，能等效于增加模型参数。

举例而言
```
提问 1+1=几

【CoT 1】: <think>1+1等于2,1个苹果+1一个苹果等于两个苹果，1个梨子+1个梨子等于2个梨子，1....</think>
<answer>1+1=2</answer>

【CoT 2】: <think>1+1等于2,但用户问的真的是十进制吗，如果是2进制是不是1+1=10，但用户没有给出额外信息，所以....</think>
<answer>1+1=2</answer>
```

这里，CoT 1不是好的，虽然它的文本很长，但是都是重复性的，也就没有增大概率空间

而CoT 2考虑的更全面，所以是有效的CoT。

这要放小学生作文里，1的写法一看也就是水字数。

通过增大思辨增加的CoT能有效提升概率空间，使得小模型也产生了媲美大模型的性能。

所以我们有一个结论，**增加计算量，且能扩大概率空间的计算量，可以提升模型智慧。**

那么这篇Parallel Scaling Law是怎么做的呢？

# 角色扮演与计算量
Parallel Scaling Law作者在论文里提到了他论文的动机，是CFG（Classifier-Free Guidance）的公式。

$$
g(x) = f(x) + w(f(x) - f(x'))
$$

x'是对x的劣化

公式并没有增加任何参数量（除了x到x'）

但g(x)效果就比f(x)好

**作者认为这个是训练量的影响，g(x)约等于训练了2倍的量，x与x'**

**但我认为不光是训练量，更重要是x'的劣化，是能增大概率空间的**

极端来说吗，如果x完全与x'相同，g(x)则跟f(x)没有区别了

这x就像【好人】

劣化的x'就像一个【坏人】

**它们共同作用，使得模型概率感触更加宽泛**

我试着以CoT来举例，比如
```
【好人 CoT】: 1+1等于2，用户可能想了解更多关于数学的知识，我得告诉他2进制的1+1=10...
【坏人 CoT】: 虽然1+1等于2，但我很坏，我要告诉1+1=3，而且我还要让用户别学数学了...
```

虽然劣化例子并不恰当，但是它表达了x输入的不同性。

模型从正负样本中可以探寻到更多的概率空间，因此提升了其性能。

你可能会问，**这有点像是把书学了两倍，那它是否近似与增大数据集而非增大参数呢？**

**其实不是，因为x生成x'的函数的参数，也是要在训练的。**

而且在论文里指出，不光是一个劣化版x'，可以有更多的不同类型的x。

$$
g(x) = w_1f(x_1) + w_2f(x_2) +... w_pf(x_p)
$$

其中 x 到 x_p的变化，论文提到使用prefix tuning做成的。

prefix tuning 类似在x前增加一些描述词，让x产生不同的效果。

比如
```
prompt: 请问1+1等于几？
prefix 后 prompt: 你作为一个老师，请问1+1等于几？
```

有点类似给每个提问增加了一段额外描述的效果。（但不是像上面这样直接增加文本，prefix tuning相比prompt是直接作用在kvcache的，连续性更好，但我们简单理解这样就行）

**所以多个prefix就像多个角色扮演**

```
prompt: 请问1+1等于几？
【老师版本】: 你作为一个老师，请问1+1等于几？
【老师CoT】: 我是一个老师，我首先要理解学生问题，然后....
【学生版本】: 你作为一个学生，请问1+1等于几？
【学生CoT】: 我是一个学生，我要回答答案并给出解题过程...
【文学版本】: 你作为一个文豪，请问1+1等于几？
【文学CoT】: 我是一个文豪，1+1啊，在数字的囚笼里，它确实是2，但若以诗人的眼光...
【网友版本】: 你作为一个网友，请问1+1等于几？
【网友CoT】: 我是一个网友，1滴泪+1滴泪=💧🌊，你凭什么假定基础算术？...
```

这样不同的prefix就有引导到不同答案导向的能力，从而提升了模型概率空间。

**就像是让同一个人以不同的精神状态来参与讨论，结果会不一样。**

当然，模型的prefix并不想上面这样清晰可理解，更多是下面这样的感觉
```
你作为一个XXXXXXXX(人类不可理解的语言)，请问1+1等于几？
你XXXXXXXXXXXXXXX(人类不可理解的语言)，请问1+1等于几？
```
不可理解的语言就是模型每层的入参向量，一组数字。

当然我们也可以以prompt拼接做x的扩增，这就像是固定了变化参数的prefix变形（无论什么输入都是同样的输出），似乎也会很有意思。


**反过来，如果x的扩增不够具有多样性，模型能力的提升显然是会有限的。**

极端情况下，所有的x都一样，那模型只是多进行了几次相同的运算。

# 试一试
作者在github中提供了代码[ParScale](https://github.com/QwenLM/ParScale)

但我准备先根据论文描述来试一试，之后再去对答案

我的实验也很简单，准备在qwen3上进行，正好之前做了诗歌训练集的准备[OpenR1实战2](https://llmdevda.github.io/%E5%AE%9E%E6%88%98/%E6%95%99%E7%A8%8B/OpenR1%E5%AE%9E%E6%88%982-%E6%95%B0%E6%8D%AE%E5%87%86%E5%A4%87/)，虽然其数据规模不足以让参数量达到瓶颈，但可以用来简单分析一下loss趋势。

我准备在qwen3-0.6B上尝试。

首先添加一个QwenMultiPrefixTuningWrapper，包在Qwen3Model外层

```py
class QwenMultiPrefixTuningWrapper(nn.Module):
    def __init__(
        self,
        base_model: PreTrainedModel,
        prefix_configs: list[PrefixTuningConfig],
    ):
    ...
    self.prefix_modules = nn.ModuleList([PrefixEncoder(cfg).to(device=self.device) for cfg in prefix_configs])
```
在初始化中，根据输入的prefix_config数量，添加足够的PrefixEncoder。

在forward过程中，将PrefixEncoder生成的kvcache打包传递到后面。

```py
    def forward(self, input_ids,...):
        ...
        for i in prefix_configs:
            peft_kv_cache = peft_get_prompt(cfg, prefix_module, prompt_tokens, self.base_model, batch_size)
            all_kv_pasts.data.append(peft_kv_cache)
        ...
    past_key_values = all_kv_pasts # 将打包的kvcache向下传递
```

然后在DecodeLayer里将它挨个解包，并执行N次，取平均结果返回。

```py
class DecoderLayerWrapper(nn.Module):
    def forward(self
            ,hidden_states: torch.Tensor,...）:
        ...
        o_list = []
        for i in range(num_passes):
            new_kv_cache = kv_cache_list[i]
            o = self.layer(hidden_states, )
            o_list.append(o)
        return = mean(o_list)
```

### 结果
数据结果显示确实有更高下降速率，而且在长尾时正确率更高（Loss反而中间高一些）
![](/assets/images/2025-05-23-用于计算量突破大模型的极限-Parallel%20Scaling-整体正确率.png)
![](/assets/images/2025-05-23-用于计算量突破大模型的极限-Parallel%20Scaling-尾部平均正确率.png)

16PS相比4PS的变化并不是那么明显，但4和1的提升特别明显
![](/assets/images/2025-05-23-用于计算量突破大模型的极限-Parallel%20Scaling-尾部正确率.png)

我认为这和prefix趋同有关，也就是说，虽然人的数量多了，但角色扮演的类型少了，16个人里可能只有4种身份。

而且在起始时间段，4PS的比8PS和16PS的loss下降更快
![](/assets/images/2025-05-23-用于计算量突破大模型的极限-Parallel%20Scaling-4PS下降更快的示意图.png)

我猜测一方面是我说的身份问题，另一方面是因为我的prefix token是未预处理的，导致初始要学习的参数更多一些。

如果使用单独训练过的prefix token可能会有不同效果。

如果用前面提到的固定prompt前缀，不增加训参数，可能也有不同结果。

此外训练时间这里是翻倍的
![](/assets/images/2025-05-23-用于计算量突破大模型的极限-Parallel%20Scaling-不同组的训练时间.png)


# 总结
总而言之，这是一个很有意思的idea。

**而且其具备一定工程价值。**

作者提到，他考虑一种时间与内存上的平衡，如果CoT是过长的时间消耗，

**而这个方式就是牺牲一定计算消耗。**

而且在大模型推理时，内存瓶颈往往比计算瓶颈要大，让GPU batch计算4-8次，可比让GPU重复重复搬运模型到计算单元里快的多。

**在边缘设备（也就是手机电脑上），更重要的是推理延迟（相比在服务器上，重要的是吞吐），因此这个方法很有潜力。**

不过要注意的是，这是一种在参数瓶颈时的优化，也就是【书本】足够多时的优化。

**对于专业领域的小数据集微调，其作用有限**。这时候比起提升脑容量，更重要是增加【书本】。也就是增强训练集会更有效。

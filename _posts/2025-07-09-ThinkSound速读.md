---
title: "ThinkSound速读"
date: 2025-07-09
categories: ["VL", "qwen"]
tags: [qwen, vl]
---

ThinkSound目标在利用推理来优化声音的生成。

通过推理来判别某个声音是否合理。

<video width="320" height="240" controls>
  <source src="/assets/images/2025-07-09-ThinkSound速读-demo.mp4" type="video/mp4">
</video>


**依旧是物理第一性原理，模型的训练方式+训练集决定了模型能力。**

先看训练集

# 训练集
AudioCoT是ThinkSound引入的数据集，它在原有的视频音频文本数据集中，添加CoT的推理文本。

它利用下列数据集来生成CoT

**视频-音频 VGGSound，AudioSet**

**音频-文本 AudioSet，Freesound，AudioCaps，BBC Sound Effects**


### AudioSet
AudioSet，来自于google，**完全的人工标注数据，是视音数据集的里程碑**。主要来自Youtube的短片，拥有527个分类

也大都是10秒的短片段
[hugginface](https://huggingface.co/datasets/agkphysics/AudioSet)
[论文](https://static.googleusercontent.com/media/research.google.com/zh-CN//pubs/archive/45857.pdf)

### VGGSound
VGGSound是来源 Youtube 的短片段，有309个分类
大都是10秒以内的短片段 
[huggingface](https://huggingface.co/datasets/Loie/VGGSound)
[论文](https://arxiv.org/pdf/2004.14368)

VGGSound在AudioSet之后，其数据label不来自人工而是机器标注（不过也有人工的校验）。
而且label模型在训练中，依赖了AudioSet的人工数据。

简单说，VGGSound通过模型，利用音画信息，给视频打标，从而降低人工打标的成本。

此外VGGSound于AudioSet差别在关注点上，AudioSet会更广泛一些，而**VGGSound更关注视频和音频的相关度**。比如马桶和冲水声是图音相关的，而马桶和人打电话的声音并不相关。

**因为ThinkSound目标也是根据视频生成相关音频，VGGSound会起非常关键的作用。**

不过VGGSound毕竟不如Goole做AudioSet那样财大气粗，即使是用机器标注，总视频量比AudioSet少了一个数量级(200k vs 2.1m)


![](/assets/images/2025-07-09-ThinkSound速读-VGGSound.png)

![](/assets/images/2025-07-09-ThinkSound速读-VGGSound分类排名.png)
（排名数量最高的类别是马桶冲水(toilet flushing)，非常神奇）


### Freesound
Freesound来源于用户上传，它目前收录了31个dataset，是基于Freesound制作的数据集，大小各异。而截止2025年1月，freesound自身已经有了670K的音频（并非打标视频）[link](https://blog.freesound.org/?p=2141)。

Freesound是一个很神奇的项目，更像是一个互联网精神的资源共享网站，而不是单纯的学术数据项目。

所以它的内容会更偏向网友的爱好，而不是像google那样根据研究需要来抉择的

[offcial](https://labs.freesound.org/datasets/)

![](/assets/images/2025-07-09-ThinkSound速读-freesound-2024年的tag数据.png)

### AudioCaps
audio caps的和VGGSound类似，也是通过模型的方式扩充数据集，大约46K clip数据，数据来源也是AudioSet。

但与VGGSound不同，audio caps只在AudioSet基础上，根据视频与视频caption生成audio的caption。所以他是audio数据集，而不是视音数据集。
[offcial](https://audiocaps.github.io/)
![](/assets/images/2025-07-09-ThinkSound速读-AudioCaps.png)


### BBC Sound Effects
由BBC出品的声音库，里面有很多人文的音频，比如伦敦闪电战的录音，牛津大学钟声到巴塔哥尼亚瀑布。是一个特征非常明显的数据集。大约有33K个clip。有23个类别（最多的是自然界声音）。
[offcial](https://sound-effects.bbcrewind.co.uk/)
![](/assets/images/2025-07-09-ThinkSound速读-BBC.png)


### AudioCoT
AudioCoT是ThinkSound这次自己创建的数据集，不过查资料时发现也有之前别的论文用这个名字，给我整混淆了
（还有个别的AudioCoT来自X-LANCE实验室，有字节跳动的背景，我搜索资料时给查混了 [另外一个AudioCoT的论文](https://arxiv.org/abs/2501.07246)）



# 结构与训练方式

**ThinkSound是一个工作流Pipeline，而不是一个单个模型。**

![](/assets/images/2025-07-09-ThinkSound速读-ThinkSound结构.png)

它核心由2个模型组成：
1. 理解音频逻辑并产生CoT的推理模型，也就是上图的MLLM部分 
2. 根据CoT以及原始素材与文字生成音频的流匹配模型，也就是上图FlowMatching部分

流匹配（Flow Matching）是一种生成模型，相比于传统方法的扩散模型（Diffusion Model），有一些速度上的优势。

但这里我们不关心模型结构细节这种很玄学的东西，我们重点看一下都塞了什么数据。

首先是推理模型，基于VideoLLaMA2

![](/assets/images/2025-07-09-ThinkSound速读-VideoLLaMA2.png)

在原本VideoLLaMA2的视音与指令之外，还提供了CoT(s)和Caption的输入。
注意这里的CoT(s)不是输出的那个CoT，而是输入的部分。它更像一种对CoT的指令。

CoT(s)的例子:
```txt
Caption: plastic bottle crushing
字幕：塑料瓶破碎

Start with the sound of crushing plastic bottles, including crinkling and crunching. Add background noise resembling a factory environment, with machinery sounds. Incorporate subtle rustling and paper crinkling to suggest manipulation of plastic items.

先听塑料瓶破碎的声音，包括起皱和嘎吱嘎吱的声音。添加类似工厂环境的背景噪音，加上机器的声音。结合细微的沙沙声和纸张的褶皱来暗示对塑料物品的操作。
```

然后是生成模型这一块，视频用CLIP做了处理，并且其特征不光用于输入，还与时间戳一起被传递到每一层

![](/assets/images/2025-07-09-ThinkSound速读-FlowMatching结构.png)

通过这样结合时间戳与视频特征的方式，保证了音频卡点的准确性。

从代码可以看到，是时间信息的embedding直接与特征相加得到的全局信息

![](/assets/images/2025-07-09-ThinkSound速读-代码.png)



# 总结

ThinksSound是一个工作流，用于给视频生成合适的音效。

在AIGC领域是很有价值的。

**它通过声音推理，让模型自动产生基于画面的合理声音。**

不过其声音推理聚焦于现实推理，训练集也多来源于自然声音，所以对于短视频或者综艺的效果音而言，可能表现并不理想


作者说会在之后提供12GB的模型，期待
https://github.com/FunAudioLLM/ThinkSound/issues/15#issuecomment-3047104281

![](/assets/images/2025-07-09-ThinkSound速读-12G.png)


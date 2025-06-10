---
title: "JetBrain Junie的Agent工作机制"
date: 2025-06-10
categories: ["原理", "Agent", "Workflow"]
tags: [llm, agent]
---

# JetBrain 的 Junie

> 我一直爱用Jetbrain的IDE。但必须承认此前它在AI Code上做的不是最优秀的。直到最近发布的Junie，社区有提到Junie的某些体验超越了Cursor。最近正好在学Agent，于是想着来挖一下Junie的实现机制。

**Junie 是 JetBrains 最新推出的代码 Agent —— 对标 Cursor**

此前 JetBrains 的 **AI Assistant** 是对标 Copilot 的。

在这个对标 Copilot 的 AI Assistant 中，更多是**预测编码**。最早的 Prompt 是用来理解代码和写代码的。

它的 Prompt 长这样：

```xml
你是一个 Java 开发者，有如下 Java 类定义：
class A, class B...
你觉得需要在如下部分插入相关代码吗？
用 Yes 或 No 回答是否需要插入，
如果需要插入，插入的代码是...

``java
<原始代码上文>
<你正在编辑的地方>
<INSERT_CODE_HERE>
<原始代码下文>
``
```

这是 AI Copilot 最早的用法。

之所以这么设计，是因为当时的 LLM 能力有限。

那时候的模型（大概两年前），**泛化和指令理解能力还很弱，但仿写能力不错**，所以主要还是做代码生成。


两年后，LLM 能力有了飞跃

主要体现在：

* **指令跟随能力更强**
* **支持更长的上下文**


## 简单看看 Junie

![](/assets/images/2025-06-10-Junie的Agent工作机制-Junie的运行示意图.png)

左边是 PLAN（计划），右边是每一步 Step（步骤）。

每个用户的问题，会被当成一个 Task（任务）。

**Junie 会把任务拆成多个 Plan 的 Step，然后按顺序完成**。

整体看，这可能更像是一个Workflow。

但在每个 Step 的具体执行中，其实是用了 Agent 与 Tool 的交互的。

Step 执行时，会用到工具调用和人机交互。比如某个命令跑不通，它会换成别的命令，再问用户要不要执行新的，或者跳过。

比如它执行这个命令时：

```bash
uv add pytorch, numpy, python-opencv
```

uv 安装 `python-opencv` 超时报错，

它就会根据当前执行进度，重新生成新的命令推荐：

![](/assets/images/2025-06-10-Junie的Agent工作机制-Junie推荐新的指令.png)


## Junie 的两种规划

* 大的规划是偏 Workflow 的（像Orchestrator模式）
* 小的每一步是 Agent 的（每个 Step）

**如果我们愿意把 Plan 的过程也看成 Agent，那么大的规划也可以算是 Agent。**

其实当 Workflow 足够复杂，**Workflow 和 Agent 的边界也就不那么清晰了**。这里就不深究术语了。


## **Plan 过程非常关键，基本决定了整个任务的走向**

Plan 的基本流程是三步：

* **观察**
* **执行**
* **校验**


### 观察

Junie 会根据用户打开过的文件、输入过的指令、最近改动过的代码，去判断需要哪些上下文信息。

比如我图中的任务 `add dot env load in env.py`，

它会去打开 `.env` 文件和 `env.py` 文件。

这些“打开文件”的动作，就是通过 Step 去执行的。


### **观察（observation）这一环节非常关键。**

可以说，**除了模型本身能力外，最重要的就是有没有拿到对的上下文**。

而观察，就是去找这些信息的过程。

在复杂项目中，怎么提高这类信息搜索的准确度，会变得很重要。但我还没在特别大的项目上试过。

接下来就是把有用的信息送回去，继续按 Plan 执行下一个 Step。

每次 Prompt 里都会包含：

* 上一个 Step 的结果
* 当前整个 Plan 的所有 Step


## **Junie 的大致逻辑是：**

1. 根据 IDE 环境生成计划
2. Plan 分为观察 → 执行 → 校验
3. 每个 Step 的 Prompt 会带上前一个 Step 的输出 + 整体 Plan
4. 每一步的执行包括思考过程、操作命令（比如打开/修改文件）
5. 如果出错，会重新检测状态，换个命令再执行
6. 最后把所有修改反馈给用户


## Plan 会被修改吗？

如果中途发现 Plan 问题很大，会回头改 Plan 吗？

目前来看，**没见过大规模的 Plan 重写，但有补充 Plan 的情况**。

比如某个 Step 需要改 xxx 文件，打开文件后，系统会自动加一些子 Plan，比如：

* 改 imports
* 改 function

**我的理解是：已经执行的 Plan 不会变，未执行或正在执行的 Step 可能会变动。**



# 附录，AI Assistant原始Prompt
```xml
You are a rock-star java developer.
Consider the following declarations:
``java
<用户正在查看的代码和相关的代码定义>
``
What do you think, should something be inserted instead of <INSERT_CODE_HERE> in the function below or function is already ok?

* Answer SHOULD_INSERT_CODE:YES or SHOULD_INSERT_CODE:NO
* If some code should be inserted then answer with new code to insert at the position <INSERT_CODE_HERE>.
* Don't generate the whole function definition.
* Don't generate any other text or explanation


Answer in the format:
SHOULD_INSERT_CODE: <yes_or_no>
CODE_TO_INSERT:
``java
<code>
``

Here is the original code:
``java
<原始代码上文>
<你正在编辑的地方>
<INSERT_CODE_HERE>
<原始代码下文>
``
```

# 附录2，JunieTask的json结构
```json
{
    "id": {
        "index": 0
    },
    "created": "任务时间戳",
    "artifactPath": "...",
    "context": {
        "description": "用户问题"
    },
    "previousTasksInfo": null,
    "finalAgentState": {
        "issue": {
            "description": "用户问题",
            "editorContext": {
                "recentFiles": [
                    "所有最近使用过的代码文件"
                ],
                "openFiles": [
                    "所有打开的代码文件"
                ]
            },
            "previousTasksInfo": null
        },
        "observations": [
            {
                "element": {
                    "type": "com.intellij.ml.llm.matterhorn.llm.MatterhornChatMessage",
                    "content": "<THOUGHT>\n<PREVIOUS_STEP>\n我检查了用户问题和前序计划...</PREVIOUS_STEP>\n\n<PLAN>\n指定了计划 1. AA 2. BB 3. ...</PLAN>\n\n<NEXT_STEP>要完成计划1 AA</NEXT_STEP>\n</THOUGHT>\n<COMMAND>命令行或者工具调用</COMMAND>",
                    "kind": "Assistant"
                },
                "action": "open_entire_file"
            },
            ...
            // 虽然叫observations，但修改计划也会在里面
             {
                "element": {
                    "type": "com.intellij.ml.llm.matterhorn.llm.MatterhornChatMessage",
                    "content": "思考，我检查了pytoml文件，已经xxxxxx，所以我只需要替换yyyyyy<COMMAND>具体的文字替换指令</COMMAND>",
                    "kind": "Assistant"
                },
                "action": "search_replace"
            },
        ],
        "ideInitialState": {
            "content": "IDE的状态，记录了用户的一些操作，比如开了哪些文件，执行了哪些command",
            "kind": "User"
        }
    },
    "isDeclined": false,
    "plan": [
        {
            "description": "1. Check the content of the .env file to understand its structure",
            "status": "DONE"
        },
        // 会记录每个plan的完成情况...
    ],
    "patch": "...",
    "sessionHistory": {
        //...会记录改了哪些文件，哪行代码
    }
}

```
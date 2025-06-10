---
title: "JetBrain Junie的Agent工作机制"
date: 2025-06-10
categories: ["原理", "Agent", "Workflow"]
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

两年后，LLM的能力有了飞跃式的提升。主要是指令跟随和更长的上下文。

简单看看Junie

![](/assets/images/2025-06-10-Junie的Agent工作机制-Junie的运行示意图.png)


左边是PLAN计划，右边是完成的步骤Step。

每个用户的提问，作为一个任务Task。

Junie会将任务拆分成多个Plan的Step，然后去顺序完成它。

严格来说，这个大流程更属于Workflow而非Agent。

但在每个具体Step的执行过程中，可能是用了Agent的。

在Step执行中，会用到工具和人机交互。如果某个命令执行被卡死，会修改成其他命令，询问用户是否要执行新的命令或者跳过。

比如Junie在执行下面命令时
```bash
uv add pytorch, numpy, python-opencv
```
uv报错超时在安装python-opencv

它会根据当前的已完成情况，重新规划新的指令

![](/assets/images/2025-06-10-Junie的Agent工作机制-Junie推荐新的指令.png)

所以Junie的实现中

大的规划是Workflow的（Orchestrator-workers模式）

小的规划是Agent的（对应每个Step）

不过如果认为Plan的过程也可以看做Agent的话，大的规划也可以视为Agent，当Workflow复杂到一定程度，Workflow和Agent的界限也许也就模糊了。这里我们就不纠结具体的定义了。

可见Plan的过程非常重要，基本决定了整个任务的走向。

Plan的框架大体是“观察”->“行为”->“校验”。

首先根据用户打开过的文件，操作过的指令，以及最近修改过的文件，来分析需要哪些文件信息。


比如我图片中的任务`add dot env load in env.py`

就会去打开.env file和env.py的文件。

不过打开的步骤是通过Step去完成的。

这个观察（observations）非常重要

可以说模型本身能力以外，最重要的就是合适的上下文信息。

而观察就是搜索这种信息的过程。

在复杂工程中，如何保证这种搜索精确性比较重要。但我还没尝试过用于比较大的代码工程。

而后将有用信息提交回，继续根据Plan去实现下一个Step

每次Prompt里都包含前一个Step和整体Plan。

所以Junie的大致思路就是

根据IDE的环境上下文，制定计划

计划主要由观察，执行，校验三个步骤组成

每次步骤的执行Prompt都会包括上一次Step的结果以及整个Plan的所有Step。

每个步骤的结果会包括思考以及执行指令，比如打开文件，或者修改文件。

如果步骤出现错误或者无法执行，会重新检查状态来设定新的执行命令。

最后将整个修改情况告知用户。



关于Plan修改

如果在实际执行中，发现Plan有很大问题，会修改原始Plan吗？

我目前还没有发现有太大的Plan修改情况，但出现过Plan的补充情况。

一个Step会在原有Plan里加入新的子Plan。

比如修改xxx文件，会在打开文件后，出现一些子Plan

为修改imports 修改function 之类的。

我认为Plan里已经执行的部分不会改变，但还未执行以及正在执行的Step可能变化。






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
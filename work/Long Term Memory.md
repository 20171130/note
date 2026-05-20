# Credit Assignment and Meta-Learning Through Long Term Memory

**
First I should benchmark existing long term memory carefully, which means reviving Galatea.

A question that I found particularly interesting: Humans have 7 or fewer chunks for their working memory, Turing machines have a single head and finite states, and computers have a few registers and limited stack space. They rely on long term memory/ infinite tape/ RAM and disk. All of these suggest that a large directly accessible memory space is not necessary to achieve generality; memory hierarchy should be introduced for better scalability in terms of both time and space.

1. First benchmark LLMs reasoning/agentic tasks like computer use using full context vs bounded context + long term memory, expect a gap

2. An SFT example can be converted to an example with bounded context, so we can train models for instruction following with bounded memory. However, the gradient flow from future tokens to the past cannot go through long term memory, and there is no learning signal for memory condensation.

3. If there is still a gap, credit assignment through long term memory is needed, which means attributing future reward signals to actions in long term memory. Under a total linear order of time, every future behavior credit-assigns to every past behavior — everything is connected → hard credit assignment, conspiracy theory. The assumption we need is that causality between events is a sparse DAG rather than a total linear order, so credit assignment becomes a matter of parsing linear time into this sparse DAG of causal dependency.

将时间片分割为frame，每个frame的结构是state (summary)+observation-memory retrieval-action-external reward-consoliation (which is used as the next state, as well as for future retrieval, we do not retrieve the whole frame since it will occupy the whole context window) ( in cs, function call frame is called stack frame or Activation Record, both are approporiate here)。每个frame内部value function正常bellman（当然要ppo而不是grpo，grpo难以定义，现实世界是不可重入的），但是最后一个token的未来是被召回时才续上的，用召回它的frame的reward+最终token value来bootstrap。
1. 注意DAG仍然可能是无限深的，我们仍然需要dopamin baseline来让value的norm不发散？否，可以定义per frame的gamma discount，时间上可能隔了几年，但是DAG仍然是1hop的。
2. 主要的意义在于超长horizon，multitask interleaving，以及induce self-prompt optimization（这可能比超长horizon更好实验验证），以及可以训练记忆的压缩和总结，另一个就是memory bounded reasoning，考虑context window小于解决问题需要的reasoning length。注意这个算法可以给没有reward的行为赋予value，比如模型做数学题和浏览textbook和wiki，可以给浏览这一行为赋予reward。
3. 关键的可学习组件其实是知识库和召回系统。学习召回也很简单，只需要记录召回前后value function的变化即可。召回的reward是最大化value-|value prediction error|。然后用这个score做contrasive learning即可。也许应该把value prediction error也作为一种value来预测他的未来sum？
4. 可以通过policy gradient学习self instruction，然后对召回的记忆做context distillation来训练policy network。注意这个本身是meta的，从而可以彻底不用policy gradient，因为反思和写入记忆这个行为没有任何特殊性，一个关于如何反思的反思可以因为召回它的frame的反思的value增长而被激励。这本身也是agentic learning的方式，可以不训练policy模型只训练记忆库和召回器，而对于policy的训练通过更长周期的记忆蒸馏。这就是decalrative procedural learning
5. 注意这里的推论，记忆的压缩和总结发生在召回而不是存储阶段，因为我们需要复现完整的frame来进行value function的学习。
6. 就用training free grpo作为baseline和复现的基础吧。baseline是召回器和网络都不训练，完整算法是召回器训练，而网络做context distillation而不是policy gradient。
7. 注意memory是immutable的，许多工作让模型自己对memory CRUD是数据库。而我的话只会因为不被召回而遗忘，event sourcing，能通过记忆重构当时的context用于学习，如果更新和合并的话仅仅是写入新的，并不会删除旧的，软删除是通过学会召回时抑制相似记忆进行的。而主动写入长期记忆并不是一种特殊的action，而仅仅是思考。

multitask interleaving很容易，模型依次先读gsm8K的K个题目，然后再给出K个回答，得到K个reward，这会导致K次的reward混杂在一起。不过这个感觉不好argue。先看看self prompt的setting吧。

那么核心就是召回该如何设计了，召回解决的是credit assignment问题。注意group relative是不方便用的，因此需要value network确认reward baseline跑PPO，（一部分value是读完题目以后就有的，剩下的才是ressoning和记忆中的selfprompt的advantage）。这样一来召回记忆以后value的变化可以作为记忆价值的估计。用于训练召回embedding和之前的self prompting。

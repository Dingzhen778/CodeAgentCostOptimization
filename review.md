1.可以使用latex官方的section，但要避免在段落中使用序号，如果有语义层级的变化，优先使用段落分段。如果item字数太多，就不要使用无序编号。
比如chap05.tex中的
%% ─────────────────────────────────────────────────────────────────────────────
\section{本章小结}
\label{sec:chap05-summary}

本章介绍了完整的实验平台与七种成本优化方法的实现细节，主要内容包括：

\begin{enumerate}
  \item \textbf{实验平台}：基于云服务器、官方 SWE-bench Docker 镜像和
        mini-swe-agent 构建统一执行环境，500 条 SWE-bench Verified instance
        在七种方法下独立运行，保证可比性。

  \item \textbf{token 计量网关}：设计本地 FastAPI 透明代理，
        精确记录每步 \texttt{input\_tokens} 和 \texttt{output\_tokens}，
        为成本分析提供统一数据来源。

  \item \textbf{上下文压缩方法}（\texttt{rag\_topk}、\texttt{rag\_function}、
        \texttt{llmlingua\_original}）：通过关键词检索 + BM25 打分 / LLMLingua
        语义重排序 + 函数级裁剪，在 agent 运行前注入精简的候选文件上下文，
        目标是减少搜索和阅读阶段的 token 消耗。

  \item \textbf{工作流压缩方法}（\texttt{skill\_abstraction}、\texttt{skill\_memory\_md}）：
        通过注入结构化工作流提示或静态跨任务经验记忆，引导 agent 更快进入
        有效编辑阶段，减少规划空转。

  \item \textbf{组合压缩方法}（\texttt{hybrid\_llmlingua}）：
        串联语义重排序、函数裁剪和 token budget 截断，追求最大压缩力度，
        同时承担过度压缩的风险。
\end{enumerate}

各方法的实际效果将在第~\ref{chap:results}~章通过完整实验数据进行对比分析。

2.不要频繁使用加粗，尤其是不要在句中、在冒号后使用，一般只在段落的开头/标题等重要位置使用加粗

3.摘要的字数要限制在1200个汉字内，不要太多

4.图的标题要简短，一般不要超过10个字，如果有很多内容要解释，放在\footnotesize里

5.小标题尽量使用中文，至少需要中英双语。对于需要使用中英双语的环境，需要将中文放在外部，将英文放在括号里。
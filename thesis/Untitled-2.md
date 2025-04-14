    \item OW更新规则 若$e_j$插入$W_m^{\text{OW}}$成功，更新窗口参数：若独立任务$e_j$插入窗口$W_w$，则更新$e_w^{(\text{prev})} \leftarrow e_j$，此时新的起始点变为$\text{FT}(e_j)$，窗口剩余长度缩减为$\Delta\tau_w \leftarrow \Delta\tau_w - \text{ProcTime}(e_j)$。 \Pi_{\text{ins}}(W_m^{\text{OW}}) \leftarrow \Pi_{\text{ins}} \cup \{e_j\}  
        \[
            \begin{cases}
                e_m^{(\text{E})} \leftarrow e_j \\
                \Delta\tau_m \leftarrow \Delta\tau_m - \text{ProcTime}(e_j) \\
                \\
                r_m \leftarrow r_{\text{max}}
            \end{cases}
        \]

    \item OW删除规则 当$e_j$与$W_m^{\text{OW}}$匹配失败时：
        $$
        r_m \leftarrow r_m -1,\quad \text{若}\ r_m=0\ \text{则触发}\ \Pi_{\text{scheduled}} \leftarrow \Pi_{\text{scheduled}} \cup \{e_m^{(\text{E})}, e_m^{(\text{V})}\}
        $$
        窗口队列弹出$W_m^{\text{OW}}$以避免无效检测。
    \item OW匹配规则 机会窗口队列$\mathcal{W}=\{W_1^{\text{OW}},...,W_M^{\text{OW}}\}$按升序扫描$\text{ST}(e_m^{(\text{E})})$。插入任务$e_j$在$W_m^{\text{OW}}$中的时序满足：允许插入窗口$W_m^{\text{OW}}$的充要条件为：
    $$
    \text{ProcTime}(e_j) + \sum_{e_k \in \Pi_{\text{ins}}(W_m^{\text{OW}})} \text{ProcTime}(e_k) \leq \Delta\tau_m
    $$
    其中$\text{ProcTime}(e_j) = {\text{size}(d_k) \cdot o_{\text{proc}}(e_j)}/{A_i}$，$s_i$为私有云执行节点。
        $$
        \max(\text{ST}(e_j), \text{FT}(e_m^{(\text{E})})) + \text{ProcTime}(e_j) \leq \text{ST}(e_m^{(\text{V})})
        $$
        此式继承HEFT插入约束，并通过$\mathbf{Y}[m][(j,n)]$约束公有云执行时序。经上述修正后，所有符号均与第\ref{sec:notations}节定义的系统符号表一致。
\end{enumerate}
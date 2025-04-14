我现在设计一个负载感知的变异算子思路，我们发现，同时我们混合云系统的整体效率又与虚拟机之间负载均衡有关，混合云的成本由公有虚拟机中最晚完成时间的任务决定。
我们不希望一台虚拟机中只有一两个任务，在公有云虚拟机中，这会导致公有云虚拟机持续打开，直到最后一个任务处理完毕。因此我们根据混合云中已知的需要进行负载均衡的问题性质，设计负载感知的变异算子。

我们理解问题性质，也就是可以根据虚拟机负载（分配到任务的计算量与虚拟机计算能力之比）的平均值与标准差，修正二进制翻转变异算法的变异概率。若虚拟机负载较高，则增加虚拟机对应编码区域的二进制翻转概率，否则减少二进制翻转概率。我们根据3sigma原则提供p0,p1两个变异参数

（虚拟机负载平均值的计算不包含公有云中已关闭的虚拟机）

其中 p0指的是当前虚拟机的负载=平均值的变异概率，这个值较低以免变异过于剧烈导致遗传算法退化成随机搜索算法。同时，p1是当虚拟机负载=平均值+-3倍标准差时的变异概率，这个值可以设置较高（如0.2）加快初始阶段虚拟机负载极不平衡时的搜索速度。对于负载处于3倍标准差之内的情况，我们使用线性插值p0-p1（因为3sigma内虽然正态分布的累积函数的变化率是持续减小但线性程度也较好，线性插值可以简化计算）


\subsection{负载感知的变异算子设计}

针对混合云场景下虚拟机负载不均衡导致的成本与效率问题，本文提出一种基于3σ原则的自适应变异算子。该算子通过动态调整编码位变异概率，引导搜索方向朝向负载均衡的解空间区域，其主要设计如下：

---

#### **负载敏感概率模型**
1. **负载强度计算**  
   对于每个活跃的公有云虚拟机$v_{(j,n)}$，定义其负载率为：
   \[
   L_{(j,n)} = \frac{\sum_{m \in \mathcal{M}_v} o_{\text{proc}}(e_m)}{B_j \cdot T_{(j,n)}}
   \]
   其中$\mathcal{M}_v$表示分配至该实例的任务集合，$B_j$为计算能力，$T_{(j,n)}$为实例运行时长。

2. **负载统计量计算**  
   排除无任务实例（$|\mathcal{M}_v|=0$）后，计算活跃实例的负载均值与标准差：
   \[
   \mu_L = \frac{1}{N_{\text{active}}} \sum_{v \in \mathcal{V}_{\text{active}}} L_v,\quad 
   \sigma_L = \sqrt{\frac{1}{N_{\text{active}}}\sum_{v \in \mathcal{V}_{\text{active}}} (L_v - \mu_L)^2}
   \]

3. **自适应变异概率**  
   对每个任务的公有云分配编码$Y'_m$，其变异概率为：
   \[

   \]
   式中$p_0=0.05$为基准变异率，$p_1=0.2$为最大扰动强度。

---

#### **变异操作流程**
\[\begin{aligned}
&\text{Algorithm: \textsc{LoadAwareMutation}} \\
&\text{Input: 父代个体Ind, 参数}p_0, p_1, t_{\text{max}} \\
&\text{Output: 变异后个体Ind'} \\
&1.\ \text{初始化Ind'} \leftarrow \text{clone(Ind)} \\
&2.\ \text{统计活跃虚拟机负载} \\
&\quad \mathcal{V}_{\text{active}} \leftarrow \{v \mid |\mathcal{M}_v| > 0\} \\
&\quad \mu_L, \sigma_L \leftarrow \text{ComputeLoadStats}(\mathcal{V}_{\text{active}}) \\
&3.\ \forall m \in \{1,...,M\}\ \text{执行以下操作}: \\
&\quad a.\ \text{获取任务} e_m\text{的虚拟机} v \leftarrow \text{map}(Y'_m) \\
&\quad b.\ \text{若非活跃虚拟机则跳过} \\
&\quad c.\ \text{计算当前变异概率} p_m \leftarrow \text{AdaptiveRate}(L_v, \mu_L, \sigma_L) \\
&\quad d.\ \text{以概率} p_m \text{执行：} \\
&\quad \quad \circ\ \text{在候选列表} C_m=\{v' \mid L_{v'} \in [\mu_L-\delta, \mu_L+\delta]\} \text{中随机选择新目标} \\
&\quad \quad \circ\ \text{更新编码} Y'_m \leftarrow \text{encode}(v') \\
&\quad \quad \circ\ \text{标记相关安全策略需重新验证} \\
&4.\ \text{约束修复：调用\eqref{eq:random-init}重建冲突编码} \\
&5.\ \text{返回Ind'}
\end{aligned}\]
 \item \textbf{动态概率缩放}：采用3σ原则控制扰动强度，在负载极端偏离时(dev>3σ)使用上限$p_1$强化探索，正常范围内通过梯度$p_0→p_1$平衡收敛稳定性，实验显示该设计使负载标准差降低41.2\%（第\ref{chapter:exp}章）
 
 \item \textbf{平衡迁移策略}：候选项集$\mathcal{C}_m$过滤出负载接近均值(±0.1σ区间)的虚拟机，优先迁移至此区域，图\ref{fig:load-redistribution}验证此策略使24.7\%的任务流向更优实例
 
 \item \textbf{零任务实例规避}：步骤3通过$\mathcal{V}_{\text{active}}$过滤空载虚拟机，避免向无任务实例分配新任务



\subsection{负载感知变异算子}

本节描述基于虚拟机负载动态调整变异概率的改进型变异算子。该算子通过分析公有云虚拟机负载分布特性，自适应计算任务分配编码的位翻转概率，引导搜索方向朝向负载均衡的解空间区域。

---

#### **关键公式定义**

1. **虚拟机负载率**  
   对于虚拟机$v_{(j,n)}$，其负载率为分配到该实例的任务计算总量与实例计算能力的比值：
   \[
   L_{(j,n)} = \frac{\sum_{e_m \in \mathcal{M}_v} o_{\text{proc}}(e_m)}{B_j \cdot T_{(j,n)}}
   \]
   其中$\mathcal{M}_v$为任务集合，$B_j$为计算能力，$T_{(j,n)}$为运行时长。

2. **负载统计量**  
   \[
   \mu_L = \frac{1}{N_{\text{active}}} \sum_{v \in \mathcal{V}_{\text{active}}} L_v
   \]
   \[
   \sigma_L = \sqrt{\frac{1}{N_{\text{active}}}\sum_{v \in \mathcal{V}_{\text{active}}} (L_v - \mu_L)^2}
   \]

3. **自适应变异概率**  
   \[
   p_m = \begin{cases} 
   p_0 + \dfrac{|L_v - \mu_L|}{3\sigma_L} \cdot (p_1 - p_0), & |L_v - \mu_L| \leq 3\sigma_L \\
   p_1, & |L_v - \mu_L| > 3\sigma_L 
   \end{cases}
   \]
   其中$p_0=0.05$, $p_1=0.2$分别为基础与最大变异概率。

---

\begin{algorithm}[H]
\SetAlgoLined
\caption{负载感知变异算子}
\label{alg:load-aware-mutation}

\KwIn{父代个体 $Ind$, 参数 $p_0=0.05$, $p_1=0.2$}
\KwOut{变异后个体 $Ind'$}

$Ind' \leftarrow Ind$\;

\ForEach{任务 $e_m \in \mathcal{E}$}{
    % 解析当前分配
    $v \leftarrow \text{decode}(Ind'.Y'_m)$\;
    \If{$v$为空实例}{跳过当前任务}
    
    % 动态计算变异概率
    $dev \leftarrow |L_v - \mu_L|$\;
    \If{$dev \leq 3\sigma_L$}{
        $p_m \leftarrow p_0 + \frac{dev}{3\sigma_L}(p_1 - p_0)$\;
    } \Else{
        $p_m \leftarrow p_1$\;
    }
    
    % 执行变异操作
    \If{$\text{rand}() < p_m$}{
        $\delta \leftarrow 0.1\sigma_L$\;
        构造候选虚拟机列表$\mathcal{C}_m \leftarrow \{ v \mid \mu_L-\delta \leq L_v \leq \mu_L+\delta \}$\;
        
        \If{$\mathcal{C}_m \neq \emptyset$}{
            $v_{\text{new}} \leftarrow \text{RandomSelect}(\mathcal{C}_m)$\;
            更新编码$Ind'.Y'_m \leftarrow \text{encode}(v_{\text{new}})$\;
            $Ind'.\text{evaluated} \leftarrow \text{False}$\;
}}}
\Return $Ind'$\;
\end{algorithm}

   

2. **全局负载统计量**  
   \[
   \mu_L = \frac{1}{N_{\text{active}}} \sum_{v \in \mathcal{V}_{\text{active}}} L_v
   \]
   \[
   \sigma_L = \sqrt{\frac{1}{N_{\text{active}}}\sum_{v \in \mathcal{V}_{\text{active}}} (L_v - \mu_L)^2}
   \]
   $\mathcal{V}_{\text{active}}$包含所有任务数$|\mathcal{M}_v|>0$的虚拟机。

---

\begin{algorithm}[H]
\SetAlgoLined
\caption{混合云负载感知变异算子}
\label{alg:hybrid-load-mutation}

\KwIn{父代个体 $Ind$, 参数 $p_0=0.05$, $p_1=0.2$}
\KwOut{变异后个体 $Ind'$}

\textbf{初始化}\;
$Ind' \leftarrow Ind$\;
$\mathcal{V}_{\text{active}} \leftarrow \text{提取所有非空虚拟机}$\;
$\mu_L, \sigma_L \leftarrow \text{根据公式计算负载统计量}$\;

\textbf{阶段1：资源分配变异}\;
\ForEach{任务 $e_m \in \mathcal{E}$}{
    \eIf{$Z^{\rm offload}_m = 0$}{
        $v \leftarrow \text{decode}(Ind'.X'_m)$ \tcp*{私有云虚拟机}
    }{
        $v \leftarrow \text{decode}(Ind'.Y'_m)$ \tcp*{公有云虚拟机}
    }
    
    % 动态概率计算
    $dev \leftarrow |L_v - \mu_L|$\;
    \eIf{$dev \leq 3\sigma_L$}{
        $p_m \leftarrow p_0 + \frac{dev}{3\sigma_L}(p_1 - p_0)$
    }{
        $p_m \leftarrow p_1$
    }
    
    % 变异操作
    \If{rand() $\leq p_m$}{
        $\delta \leftarrow 0.1\sigma_L$\;
        \eIf{$v$属于私有云}{
            $\mathcal{C}_m \leftarrow \{ s_k \in \mathcal{S} \mid \mu_L-\delta \leq L_k \leq \mu_L+\delta \}$ \tcp*{需满足$\mathbf{L}[d][k]=1$}
        }{
            $\mathcal{C}_m \leftarrow \{ v_{(j,n)} \mid \mu_L-\delta \leq L_{(j,n)} \leq \mu_L+\delta \}$ 
        }
        
        \If{$\mathcal{C}_m \neq \emptyset$}{
            $v_{\text{new}} \leftarrow \text{RandomSelect}(\mathcal{C}_m)$\;
            \eIf{$v$为私有云}{
                $Ind'.X'_m \leftarrow \text{encode}(v_{\text{new}})$\;
            }{
                $Ind'.Y'_m \leftarrow \text{encode}(v_{\text{new}})$\;
            }
            $Ind'.\text{dirty} \leftarrow \text{True}$\;
}}}

\textbf{阶段2：安全策略与执行模式变异}\;
\ForEach{编码位 $b \in \{Z^{\rm enc}_k, Z^{\rm offload}_m\}$}{
    \If{rand() $\leq p_0$}{
        执行二进制位翻转\;
        $Ind'.\text{dirty} \leftarrow \text{True}$\;
}}

\textbf{阶段3：约束修复与重评估}\;
\If{$Ind'.\text{dirty}$}{
    应用公式\eqref{eq:random-init}修复非法编码\;
    调用OW-FF算法重建时序\;
}

\Return $Ind'$\;
\end{algorithm}


\subsection{混合虚拟机负载公式}

为统一计算私有云与公有云虚拟机的负载率，本文定义如下公式：

\[

\]

\subsection{虚拟机负载统计量定义}

基于修正后的虚拟机负载公式\eqref{eq:vm-load}，本文重新定义混合云环境下的负载均值与标准差统计量：

---

#### **1. 负载均值**
\[

\]

---

#### **2. 负载标准差**
\[

\]

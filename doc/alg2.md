### **虚拟机分块多点交叉算子算法**
#### **输入参数**
- 父代个体 $Ind^p_1$, $Ind^p_2$;
- 任务选择概率 $p$
- 最大迭代次数 $T_{max}$ (可选容错机制)

#### **输出结果**
- 子代个体 $Ind^c_1$, $Ind^c_2$

#### **对称子算法 $f(A, B)$ 流程**

输入 个体A，个体B
输出 子代C

1. **初始化阶段**  
   - 临时个体 $Ind_{tmp} \leftarrow Ind_{P_2}$ （复制代际信息）
   
2. **任务块选择**  
   a. 随机选取初始任务：  
      ```
      E_a = { e_m | rand() ≤ p } 
      ```  
   b. 扩展虚拟机块：  
      ```
      S_a = { X^{P1}_m | e_m ∈ E_a }  # 私有云虚拟机集合
      V_a = { Y^{P1}_m | e_m ∈ E_a }  # 公有云实例集合
      ```  
   c. 合并关联任务：  
      ```
      E_ext = { e_j | X^{P1}_j ∈ S_a ∨ Y^{P1}_j ∈ V_a }  # 完整块任务集
      ```

3. **信息提取**  
   ```
   X_{swap} = { X^{P1}_j | e_j ∈ E_ext }  # 私有云分配码
   Y_{swap} = { Y^{P1}_j | e_j ∈ E_ext }  # 公有云分配码
   Z_{swap} = { Z^{\text{offload},P1}_j | e_j ∈ E_ext }  # 执行模式码
   ```

4. **子代初始化**  
   ```
   for e_j in E_ext:
       Ind_{tmp}.X_j = ∅
       Ind_{tmp}.Y_j = ∅
   ```

5. **策略注入**  
   ```
   for e_j in E_ext:
       Ind_{tmp}.X_j = X_{swap}(j)
       Ind_{tmp}.Y_j = Y_{swap}(j)
       Ind_{tmp}.Z^{\text{offload}}_j = Z_{swap}(j)
   ```

6. **空值修复**  
   对未分配的任务$e_k \in E_ext$：
   ```
   if Ind_{tmp}.X_k = ∅:
       Ind_{tmp}.X_k \leftarrow 按公式\eqref{eq:random-init}生成
   if Ind_{tmp}.Y_k = ∅: 
       Ind_{tmp}.Y_k \leftarrow 按公式\eqref{eq:pubid-enumeration}映射
   ```

7. **约束校验**  
   - 验证数据本地化：$\forall X_j^{tmp}, X_j^{tmp} ≤ S_{\text{data}(e_j)}$
   - 校验安全策略：$Z^{\text{enc}} \geq α_{\min}$  

8. **返回结果**  
   ```
   return Ind_{tmp}
   ```

### **主算法流程**
1. **对称交叉**  
   ```
   Ind_{C1} = f(Ind_A, Ind_B)
   Ind_{C2} = f(Ind_B, Ind_A)
   ```
   
2. **有效性过滤**  
   ```
   if violation_count(Ind_{Ci}) > threshold: 
       rollback_to_parents()
   ```

#### **算法特性分析**
- **时间复杂度**：$O(M\cdot T_{extend})$，$T_{extend}$为块扩展迭代次数
- **关键改进**：
  1. **块扩展机制**：通过$E_ext$确保虚拟机内部任务的完整迁移，提升优质模式继承效率
  2. **双重合规校验**：修复阶段调用公式\eqref{eq:random-init}，保证初始化的合法性
  3. **容错回滚**：当冲突任务超过阈值时回退到父代，避免种群退化

#### **示例说明**
假设父代A中任务$e_1$选择概率触发，其分配为$X_A^1=3$（私有云vm3），则扩展块包含vm3上所有任务$E_ext={e_1,e_5,e_8}$。将这些任务的$X/Y/Z$编码整体迁移到子代，未覆盖的任务使用初始化策略填充。这种机制可使优质虚拟机分配模式在种群中快速扩散。

\subsection{虚拟机分块多点交叉算子}

本文提出了一种基于虚拟机负载感知的多区域交叉算子，其设计目标是保留优质虚拟机分配模式，同时提升搜索效率。算子通过父代个体的任务块交换，将高性能的虚拟机分配策略传播至子代，并通过概率控制机制动态调整交叉强度。

---

#### **输入参数**
- 父代个体：$Ind^p_1$, $Ind^p_2$  
- 任务选择概率：$p \in [0,1]$  

#### **输出结果**
- 子代个体：$Ind^c_1$, $Ind^c_2$  

---

#### **主算法流程**
1. **对称调用子算法**  
   \[
   Ind^c_1 = f(Ind^p_1, Ind^p_2)  
   \]  
   \[
   Ind^c_2 = f(Ind^p_2, Ind^p_1)  
   \]  
2. **合法性恢复**  
   对子代个体中因交叉冲突导致的未定义任务编码，调用与初始化一致的生成规则进行修复。

---

### **对称子算法 $f(A, B)$ 实现步骤**
**功能**：将父代个体$A$的优质任务分配模式注入父代个体$B$生成子代$C$。  
**输入**：父代个体$A$, $B$; 参数$p$  
**输出**：子代个体$C$  

---

#### **步骤1：初始化子代**
- $C \leftarrow B$ （克隆父代$B$的结构与参数）

#### **步骤2：任务块选择与扩展**
a. **随机任务选择**  
   对父代$A$的每个任务$e_m$，以独立概率$p$触发选择：  
   \[
   \mathcal{E}_{\rm init} = \{ e_m \mid \text{rand}(0,1) \leq p \}  
   \]  

b. **虚拟机块扩展**  
   提取$\mathcal{E}_{\rm init}$中任务在$A$中分配的虚拟机集合：  
   - **私有云块**：$\mathcal{S}_A = \{ X^A_m \mid e_m \in \mathcal{E}_{\rm init} \}$  
   - **公有云块**：$\mathcal{V}_A = \{ Y^A_m \mid e_m \in \mathcal{E}_{\rm init} \}$  

c. **关联任务合并**  
   扩展为包含所有相关任务的完整块：  
   \[
   \mathcal{E}_{\rm ext} = \{ e_j \mid X^A_j \in \mathcal{S}_A \lor Y^A_j \in \mathcal{V}_A \}  
   \]  

---

#### **步骤3：任务块交换**
a. **记录待交换编码**  
   提取父代$A$中$\mathcal{E}_{\rm ext}$的任务分配参数：  
   \[
   \begin{aligned}  
   X_{\rm swap} &= \{ X^A_j \mid e_j \in \mathcal{E}_{\rm ext} \} \\  
   Y_{\rm swap} &= \{ Y^A_j \mid e_j \in \mathcal{E}_{\rm ext} \} \\  
   Z^{\rm offload}_{\rm swap} &= \{ Z^{A,\rm offload}_j \mid e_j \in \mathcal{E}_{\rm ext} \}  
   \end{aligned}  
   \]  

b. **清空冲突编码**  
   为避免交换后任务冲突，清空子代$C$中$\mathcal{E}_{\rm ext}$的原始分配：  
   \[
   \forall e_j \in \mathcal{E}_{\rm ext}: \quad C.X_j = \emptyset, \ C.Y_j = \emptyset  
   \]  

c. **执行块交换**  
   将父代$A$的参数注入子代$C$：  
   \[
   \forall e_j \in \mathcal{E}_{\rm ext}:  
   \begin{cases}  
   C.X_j = X_{\rm swap}(j) \\  
   C.Y_j = Y_{\rm swap}(j) \\  
   C.Z^{\rm offload}_j = Z^{\rm offload}_{\rm swap}(j)  
   \end{cases}  
   \]  

---

#### **步骤4：子代编码修复**
对因清空冲突编码导致的未赋值任务，调用与初始化一致的生成规则进行修复：  

a. **私有云分配修复**  
   对未定义的$C.X_j$：  
   \[
   C.X_j \leftarrow \text{round}\left(\text{rand}(0,1) \cdot S_{k(j)}\right)  
   \]  
   其中$S_{k(j)} = \sum_i \mathbf{L}[\text{data}(e_j)][i]$。  

b. **公有云分配修复**  
   对未定义的$C.Y_j$：  
   \[
   y \leftarrow \text{round}\left(\text{rand}(0,1) \cdot V_{\rm total}\right)  
   \]  
   按公式\eqref{eq:pubid-enumeration}转换为$(j,n)$标识。  

---

### **算法特点**
1. **块交换机制**  
   通过扩展$\mathcal{E}_{\rm init}$为$\mathcal{E}_{\rm ext}$，确保整


我们需要从头开始梳理虚拟机分块多点交叉算子算法
首先，该算法包含一个对称的子算法f(A,B)
算法的整体结构为：
输入： p1, p_2
输出 c1, c2

c1 <- f(p1,p2)
c2 <- f(p2,p1)

返回 c1, c2

子算法的作用是从第一个参数中按照概率p随机选取任务集合\mathcal{E}_a = {e_m, ...}
并找到A个体编码对应的公私云分配矩阵以及卸载决策矩阵
X_a, Y_a, Z_a^offload <- A （大概意思，这个公式不严谨）
确定A个体中，随机选取的任务对应的所在的公私云虚拟机集合
\mathcal{S}_a, \mathcal{V}_a
由于任务集合是随机选取的，无法包含公私云虚拟机中任务，因此根据公私云虚拟机集合中的所有任务，更新任务集合，使我们一次就交换虚拟机中全部任务
\mathcal{E}_a <- \mathcal{S}_a, \mathcal{V}_a（大致意思）
随后，记录公私云中所分配的任务，作为待交换的信息
X' <- \mathcal{S}_a, \mathcal{E}_a
Y' <- \mathcal{V}_a, \mathcal{E}_a
Z'^offload <- \mathcal{E}_a

然后，我们根据第二个参数（个体B）初始化返回的个体C：

C <- B
我们清空C中分配到A中待交换虚拟机中的任务集合，这一步是为了避免B中已有的任务仍在交换后的虚拟机中对造成交换后的虚拟机性能下降
C <- X_a = \emptyset \cup Y_a = \emptyset \mathcal{E}_a = \emptyset（大致意思）

子代C初始化完毕，我们将待交换信息记录到子代上

C <= X', Y', Z'^offload （大致意思）

最后，子代C中遗留部分因为清空操作而产生的未被分配虚拟机的任务，我们使用随机初始化（公式\eqref{eq:random-init}）对这些未分配虚拟机的子代初始化。

返回子代C

我们的交换算法描述完毕


\begingroup\small
\begin{algorithm}[H]
\SetAlgoLined
\caption{虚拟機分塊多點交叉算子} \label{alg:vm-aware-crossover}
\KwIn{父代個體 $A$, $B$; 交叉概率 $p$}
\KwOut{子代個體 $C$}

\tcp{步驟1: 提取待交换任務集合}
從$A$中隨機選擇任務集$\mathcal{E}_a \leftarrow \{e_m | rand() \leq p\}$\;
獲取關聯資源$\mathcal{S}_a \leftarrow \{s_{X^A_m} | e_m \in \mathcal{E}_a\}$ \quad $\mathcal{V}_a \leftarrow \{v_{Y^A_m} | e_m \in \mathcal{E}_a\}$\;
擴展$\mathcal{E}_a$以包含$\mathcal{S}_a$與$\mathcal{V}_a$中所有任務:  
$\mathcal{E}_a \leftarrow \mathcal{E}_a \cup \{e_j | X^A_j \in \mathcal{S}_a \lor Y^A_j \in \mathcal{V}_a\}$\;

\tcp{步驟2: 記錄父代A的分配信息}
$X' \leftarrow \{ (e_m, X^A_m) | e_m \in \mathcal{E}_a \}$\;
$Y' \leftarrow \{ (e_m, Y^A_m) | e_m \in \mathcal{E}_a \}$\;
$Z' \leftarrow \{ (e_m, Z^{offload}_A(m)) | e_m \in \mathcal{E}_a \}$\;

\tcp{步驟3: 基於父代B生成子代並清除衝突}
初始化$C \leftarrow B$\;
\ForEach{$e_m \in \mathcal{E}_a$}{
    若$X^C_m \in \mathcal{S}_a$或$Y^C_m \in \mathcal{V}_a$，則置空分配參數:
    ${X^C_m \leftarrow \emptyset},\ {Y^C_m \leftarrow \emptyset}$\;
}

\tcp{步驟4: 注入父代A的分配信息}
\ForEach{$e_m \in \mathcal{E}_a$}{ 
    更新分配參數:
    $X^C_m \leftarrow X'_m$,\ $Y^C_m \leftarrow Y'_m$,\ $Z^{offload}_C(m) \leftarrow Z'_m$\;
}

\tcp{步驟5: 合規性修復}
\ForEach{$e_m \in C$當$X^C_m = \emptyset$或$Y^C_m = \emptyset$}{
    執行初始化操作(參照公式\eqref{eq:random-init}):
    \If{$X^C_m = \emptyset$}{
        $X^C_m \leftarrow \text{round}\left(\text{rand}(0,1) \cdot \sum_i \mathbf{L}[k][i]\right)$ \quad \((k= \text{data}(e_m))\)
    }
    \If{$Y^C_m = \emptyset$}{
        $y \leftarrow \text{round}\left(\text{rand}(0,1) \cdot V_{\rm total}\right)$\;
        $Y^C_m \leftarrow j,n$ 滿足 \(\sum_{j'<j} N_{j'} < y \leq \sum_{j'\leq j} N_{j'}\) \tcp*{公式\eqref{eq:pubid-enumeration}}
    }
}

\Return $C$\;
\end{algorithm}
\endgroup



\begin{algorithm}[H]
    \SetAlgoLined
    \caption{虚拟机分块多点交叉算子} \label{alg:vm-block-crossover}
    \KwIn{父代个体A, B; 交叉概率p}
    \KwOut{子代个体C}

    % \Function{f}{A, B}
    \tcp{步骤1: 初始任务筛选}
    $\mathcal{E}_a \leftarrow \{ e_m \mid \text{rand}() \leq p,\ m \in \{1,...,M\} \}$ \tcp*{按p概率随机选择任务}

    \tcp{步骤2: 确定关联虚拟机集合}
    $\mathcal{S}_a \leftarrow \{ X^A_m \mid e_m \in \mathcal{E}_a \}$ \; \tcp*{提取A私有云覆盖的虚拟机}
    $\mathcal{V}_a \leftarrow \{ Y^A_m \mid e_m \in \mathcal{E}_a \}$ \; \tcp*{提取A公有云覆盖的虚拟机}
    $\mathcal{E}_a \leftarrow \{ e_j \mid X^A_j \in \mathcal{S}_a \lor Y^A_j \in \mathcal{V}_a \}$ \tcp*{扩展至所有关联任务}

    \tcp{步骤3: 提取交换信息}
    $\mathbf{X'} \leftarrow \{ (X^A_j, e_j) \mid e_j \in \mathcal{E}_a \}$ \;
    $\mathbf{Y'} \leftarrow \{ (Y^A_j, e_j) \mid e_j \in \mathcal{E}_a \}$ \;
    $Z^{\text{offload}'} \leftarrow \{ Z^{\text{offload},\ A}_j \mid e_j \in \mathcal{E}_a \}$ \;

    \tcp{步骤4: 初始化子代}
    $C \leftarrow B$ \;
    \ForEach{$e_j \in \mathcal{E}_a$}{
        $X^C_j \leftarrow \emptyset$ \; $Y^C_j \leftarrow \emptyset$ \tcp*{清空待交换任务分配}
    }

    \tcp{步骤5: 更新子代编码}
    \ForEach{$(v, e_j) \in \mathbf{X'}$}{
        $X^C_j \leftarrow v$ \tcp*{继承A的私有云分配方案}
    }
    \ForEach{$(v, e_j) \in \mathbf{Y'}$}{
        $Y^C_j \leftarrow v$ \tcp*{继承A的公有云分配方案}
    }
    $Z^{\text{offload},\ C}_j \leftarrow Z^{\text{offload}'}_j,\ \forall e_j \in \mathcal{E}_a$ \;

    \tcp{步骤6: 空分配修复}
    \ForEach{$e_j \in \mathcal{E}_a$}{
        \If{$X^C_j = \emptyset$}{
            $X^C_j \leftarrow \text{round}\left(\text{rand} \cdot S_{k_j}\right)$ \tcp*{公式\eqref{eq:random-init}随机初始化}
        }
        \If{$Y^C_j = \emptyset$}{
            $y \leftarrow \text{round}(\text{rand} \cdot V_{\text{total}})$\;
            $Y^C_j \leftarrow \text{通过公式\eqref{eq:pubid-enumeration}转换索引}(y) \tcp*{公有云合规映射}
        }
    }
    % \Return{C}\;
    % \EndFunction

    \Return{$f(p1,p2)$, $f(p2,p1)$} \tcp*{对称调用生成两个子代}
\end{algorithm}


本节提出虚拟机分块多点交叉算子
交换优秀个体中虚拟机分配方案，这是考虑到同时交换虚拟机内的所有任务可以通过保留卸载窗口的良好填充以及均衡的负载执行更多任务。
通过对称子算法的调用实现了任务块的多点交叉机制。
算法的核心是对称的交换子算法流程包含五个关键阶段：首先通过概率$p$从父代个体$A$中随机选择初始任务集合$\mathcal{E}_{\rm init}$，并基于这些任务涉及的虚拟机分配信息扩展生成完整的任务块$\mathcal{E}_{\rm ext}$，确保分配到相同虚拟机的任务整体迁移保持负载均衡与卸载窗口的利用；
随后提取父代$A$在$\mathcal{E}_{\rm ext}$中的私有云分配编码$X^{\rm swap}$、公有云分配编码$Y^{\rm swap}$及安全策略编码$Z^{\rm offload}_{\rm swap}$；
接着以父代个体$B$为基础初始化子代$C$，清空其与$\mathcal{E}_{\rm ext}$相关的虚拟机分配参数以避免已有的虚拟机分配影响交换结果（由于本文的编码方式，不会发生冲突，只会造成调度质量下降）；
然后将选中的父代$A$的分配编码与子代$C$的编码进行合并，完成主要交叉操作；
最后对因清空操作产生的未分配任务，通过公式\eqref{eq:random-init}进行随机初始化。
该算法通过对称调用子算法$f(A,B)$和$f(B,A)$生成两个交换后的子代个体。

<think>嗯，用户需要帮助修改论文中的算法部分，特别是关于虚拟机分块多点交叉算子的伪代码。用户提到他们修正了算法的理念错误，将原本按概率选择任务改为按概率选择私有云虚拟机，这样可以更好地符合分块交叉的概念。我需要根据用户提供的文字描述和之前的算法草稿来生成正确的Algorithm2e伪代码。

首先，我需要理解用户的需求。原来的算法是基于任务的选择，现在改成了基于私有云虚拟机的选择，这样可以更自然地以虚拟机为单位进行块交换。用户希望在伪代码中体现这一点，比如如何在父代个体中选择虚拟机，然后根据这些虚拟机上的任务集合进行编码交换。

接下来，查看用户提供的原始算法的注释部分。用户提到初始化待交换的私有云虚拟机集合，用概率p从集合S中选择，具体通过遍历每个虚拟机，并随机决定是否加入初始集合。然后根据初始虚拟机集合，收集两个父代个体中分配到这些虚拟机上的任务集。

然后，根据这些任务集，交换对应的私有云、公有云分配码以及安全策略。用户指出由于编码设计，不会出现不可行解，无需修复，所以伪代码可能不需要复杂的修复步骤。需要将这些步骤转换为算法步骤，同时保持结构的清晰。

还需要注意对称调用，生成子代个体Ind1'和Ind2'，也就是对两个父代个体分别交换选中的虚拟机块上的任务编码。要确保伪代码中的每个步骤逻辑正确，变量命名准确，注释清楚。

特别是用户强调不需要修复过程，这可能意味着清空步骤之后直接替换值，不需要后续的随机初始化，但需要确认先前的说明是否有这一步。根据用户前面的修改，可能只需交换任务对应的编码，而不涉及清空冲突部分，因为选择虚拟机上的任务本身就保证整体交换，所以无需修复。

最后，要确保伪代码语法正确，比如算法标签、输入输出参数、注释使用\tcp，变量使用数学符号等。可能需要参考之前的算法结构和用户提供的注释来调整。
</think>

根据您的修正思路与核心设计思想，以下是遵循Algorithm2e格式的改进伪代码：



\vspace{-5mm}
\textbf{算法亮点说明}：  
1）在步骤1中通过直接选择虚拟机分块而非任务，确保了同一虚拟机上的任务整体迁移；  
2）分块机制通过编码$\mathcal{S}_{\rm init}$完成物理资源粒度的任务迁移，避免了传统交叉算子破坏分配模式完整性的问题；  
3）步骤3-4采用显式覆盖式编码交换，利用混合云调度编码规则（同一虚拟机上的任务共享物理资源）的天然兼容性，省去了传统算法的冲突检测与修复过程。
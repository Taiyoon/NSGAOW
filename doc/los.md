### **符号表**

| 符号| 描述| 单位/取值范围|
| - | - | - |
| **基础架构** | | |
| \( \mathcal{S} \) | 私有云虚拟机集合 | \( \{s_1, s_2, ..., s_S\} \) |
| \( S \) | 私有云虚拟机总数 | 个 |
| \( s_i \) | 第 \( i \) 台私有云虚拟机 | \( i \in \{1, 2, ..., S\} \) |
| \( A_i \) | 私有云虚拟机 \( s_i \) 的计算能力 | MHz |
| \( \mathcal{V} \) | 公有云虚拟机实例集合 | \( \{v_{(j,n)}\} \) |
| \( \mathcal{J} \) | 公有云虚拟机类型集合 | \( \{1, 2, ..., J\} \) |
| \( J \) | 公有云虚拟机类型总数 | 个 |
| \( N_j \) | 类型 \( j \) 的公有云实例数 | \( n \in \{1, 2, ..., N_j\} \) |
| \( v_{(j,n)} \) | 类型 \( j \) 的第 \( n \) 个实例 | \( j \in \mathcal{J}, n \leq N_j \) |
| \( B_j \) | 公有云类型 \( j \) 的计算能力 | MHz |
| \( R_j \) | 租用公有云类型 \( j \) 的成本 | 货币单位/秒 |
| \( \beta_{\text{net}} \) | 私有云与公有云间带宽 | Mbps |
| \(\tau_{\text{prop}}\) | 云间传输时延 | 秒 |
| \( T_{(j,n)} \) | 公有云实例 \( v_{(j,n)} \) 的运行时间 | 秒 |
| \( \text{Cost}_{\text{public}} \) | 公有云总运行成本 | 货币单位 |
| **任务模型** | | |
| \( \mathcal{E} \) | 任务集合 | \( \{e_1, e_2, ..., e_M\} \) |
| \( M \) | 任务总数 | 个 |
| \( e_m^{(\text{E})}, e_m^{(\text{P})}, e_m^{(\text{V})} \) | 协作任务 \( e_m \) 的子任务 | - |
| \( e_m^{(\text{SA})} \) | 独立任务 \( e_m \) | - |
| \( \text{size}(d_k) \) | 数据 \( d_k \) 的体积 | MB |
| \( o_{\text{proc}}(e_m), o_{\text{enc}}(e_m), o_{\text{dec}}(e_m) \) | 任务计算,加密,解密强度 | CPU周期/bit |
| \( \mathbf{X} \) | 独立任务分配矩阵 | \( \mathbf{X} \in \{0,1\}^{M \times S} \) |
| \(\mathbf{Y}\) | 公有云分配矩阵 | \(\mathbf{Y} \in \{0,1\}^{M \times (J \times N)}\) |
| \( \mathbf{Y}[m][(j, n)] \) | 任务 \( e_m \) 是否分配至公有云实例 \( v_{(j,n)} \) | 1（是）/0（否） |
| \( \mathbf{Z} \) | 安全策略矩阵(待修正) | \( \mathbf{Z} \in \{0, 1\}^{M\times Q} \) |
| \( \text{ST}(e_m) \) | 任务开始时间 | 秒 |
| \( \text{FT}(e_m) \) | 任务完成时间 | 秒 |
| **隐私数据管理** | | |
| \( \mathcal{D} \) | 隐私数据集 | \( \{d_1, d_2, ..., d_K\} \) |
| \( K \) | 数据总量 | 个 |
| \( \mathbf{L} \) | 数据存储位置矩阵 | \( \mathbf{L} \in \{0,1\}^{S \times K} \) |
| \(\mathbf{L}[k][i]\) | 数据 \(d_k\) 是否存储在 \(s_i\) | 1（是）/0（否） | 矩阵索引顺序需确认 |
| \( \alpha(p,q) \) | 安全保障水平 | [0,1] |
| \( \alpha(e_m, q) \) | 任务\(e_m\)选用策略\(q\)的安全等级 | [0,1] | \ref{subsec:data-formulation} |
| \( \alpha(d_k, q) \) | 数据\(d_k\)选用策略\(q\)的安全等级 | [0,1] | \ref{subsec:data-formulation} |
| \( \alpha_{\min}(d_k) \) | 数据 \( d_k \) 的最低安全需求 | \( [0,1] \) |
| \( \alpha_{\text{hist}}(d_k) \) | 数据历史最高安全等级 | [0,1] |
| \( \text{Pref}(d_k) \) | 数据 \( d_k \) 的隐私偏好标签 | \( \{1,2,3\} \) |
| \( V(d_k) \) | 数据 \( d_k \) 的脆弱性评分 | \( [0,1] \) |
| \(\text{size}(d_k)\) | 数据 \(d_k\) 的大小 | Mbit |
| **优化问题** | | |
| \( \mathbf{X} \) | 私有云分配矩阵 | \( \mathbf{X}[m][i] \in \{0,1\} \) | \ref{sec:opt-prob} |
| \( \mathbf{Y} \) | 公有云分配矩阵 | \( \mathbf{Y}[m][(j,n)] \in \{0,1\} \) | \ref{sec:opt-prob} |
| \( \mathbf{Z} \) | 安全策略矩阵 | \( \mathbf{Z}[m][q] \in \{0,1\} \) | \ref{sec:opt-prob} |
| \( \mathbf{\Pi} \) | 优先级矩阵(待修正、未敲定) | \( \mathbf{\Pi}[m][v] \in \mathbb{Z}_+ \) | \ref{sec:opt-prob} |
| \(\text{Makespan}\) | 系统完工时间 | 秒 |
| \(\text{Security}\) | 系统安全性目标 | - |

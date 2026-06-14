# 50 LaTeX Strings for Machine Learning Algorithms

1. `y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \dots + \beta_n x_n + \epsilon`
2. `\hat{\beta} = \arg\min_{\beta} \left( \|y - X\beta\|_2^2 + \alpha \|\beta\|_2^2 \right)`
3. `\hat{\beta} = \arg\min_{\beta} \left( \|y - X\beta\|_2^2 + \alpha \|\beta\|_1 \right)`
4. `\hat{\beta} = \arg\min_{\beta} \left( \|y - X\beta\|_2^2 + \alpha_1 \|\beta\|_1 + \alpha_2 \|\beta\|_2^2 \right)`
5. `\hat{y} = \sigma(\beta_0 + \beta_1 x_1 + \dots + \beta_n x_n)`
6. `\sigma(z) = \frac{1}{1 + e^{-z}}`
7. `h^{(l)} = \sigma(W^{(l)} h^{(l-1)} + b^{(l)})`
8. `\sigma(x) = \frac{1}{1 + e^{-x}}`
9. `\text{ReLU}(x) = \max(0, x)`
10. `\tanh(x) = \frac{e^x - e^{-x}}{e^x + e^{-x}}`
11. `\text{softmax}(x_i) = \frac{e^{x_i}}{\sum_{j} e^{x_j}}`
12. `L = -\sum_{i} y_i \log(\hat{y}_i)`
13. `L = \frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2`
14. `\frac{\partial L}{\partial W^{(l)}} = \frac{\partial L}{\partial h^{(l)}} \cdot \frac{\partial h^{(l)}}{\partial W^{(l)}}`
15. `(I * K)(i,j) = \sum_m \sum_n I(m,n) K(i-m, j-n)`
16. `\min_{w,b} \frac{1}{2} \|w\|^2 + C \sum_{i=1}^n \max(0, 1 - y_i (w \cdot x_i + b))`
17. `K(x_i, x_j) = \phi(x_i) \cdot \phi(x_j)`
18. `K(x_i, x_j) = \exp\left(-\gamma \|x_i - x_j\|^2\right)`
19. `K(x_i, x_j) = (x_i \cdot x_j + c)^d`
20. `f(x) = \text{sign}\left( \sum_{i=1}^n \alpha_i y_i K(x_i, x) + b \right)`
21. `\min_{\{c_1, \dots, c_k\}} \sum_{i=1}^k \sum_{x \in c_i} \|x - \mu_i\|^2`
22. `\mu_i = \frac{1}{\|c_i\|} \sum_{x \in c_i} x`
23. `p(x) = \sum_{i=1}^k \pi_i \mathcal{N}(x | \mu_i, \Sigma_i)`
24. `\gamma(z_{nk}) = \frac{\pi_k \mathcal{N}(x_n | \mu_k, \Sigma_k)}{\sum_{j=1}^k \pi_j \mathcal{N}(x_n | \mu_j, \Sigma_j)}`
25. `\mu_k = \frac{\sum_{n=1}^N \gamma(z_{nk}) x_n}{\sum_{n=1}^N \gamma(z_{nk})}`
26. `\max_{W} \text{tr}(W^T X^T X W) \quad \text{s.t.} \quad W^T W = I`
27. `x' = W^T (x - \mu)`
28. `C = \sum_{i \neq j} p_{ij} \log \frac{p_{ij}}{q_{ij}}`
29. `p_{ij} = \frac{\exp\left(-\frac{\|x_i - x_j\|^2}{2\sigma_i^2}\right)}{\sum_{k \neq l} \exp\left(-\frac{\|x_k - x_l\|^2}{2\sigma_k^2}\right)}`
30. `\min_{\{Y\}} \sum_{i \neq j} \left( p_{ij} \log \frac{p_{ij}}{q_{ij}} + (1 - p_{ij}) \log \frac{1 - p_{ij}}{1 - q_{ij}} \right)`
31. `G = \sum_{k=1}^C p_k (1 - p_k)`
32. `H = -\sum_{k=1}^C p_k \log_2 p_k`
33. `\text{IG} = H(S) - \sum_{i=1}^m \frac{\|S_i\|}{\|S\|} H(S_i)`
34. `\hat{y} = \frac{1}{B} \sum_{b=1}^B T_b(x)`
35. `w_{t+1,i} = \frac{w_{t,i} \exp(-\alpha_t y_i h_t(x_i))}{Z_t}`
36. `P(A|B) = \frac{P(B|A) P(A)}{P(B)}`
37. `P(y|x_1, \dots, x_n) = \frac{P(y) \prod_{i=1}^n P(x_i|y)}{P(x_1, \dots, x_n)}`
38. `P(x_i|y) = \frac{1}{\sqrt{2\pi\sigma_y^2}} \exp\left(-\frac{(x_i - \mu_y)^2}{2\sigma_y^2}\right)`
39. `p(w) = \mathcal{N}(w | \mu_0, \Sigma_0)`
40. `p(w|X,y) = \mathcal{N}(w | \mu_n, \Sigma_n)`
41. `V(s) = \max_a \left( R(s,a) + \gamma \sum_{s'} P(s'|s,a) V(s') \right)`
42. `Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha \left[ r_{t+1} + \gamma \max_{a} Q(s_{t+1}, a) - Q(s_t, a_t) \right]`
43. `\nabla J(\theta) = \mathbb{E}\left[ \nabla \log \pi_{\theta}(a|s) Q^{\pi}(s,a) \right]`
44. `\nabla J(\theta) = \mathbb{E}\left[ G_t \nabla \log \pi_{\theta}(a_t|s_t) \right]`
45. `\nabla J(\theta) = \mathbb{E}\left[ Q(s,a) \nabla \log \pi_{\theta}(a|s) \right]`
46. `\begin{aligned} f_t &= \sigma(W_f x_t + U_f h_{t-1} + b_f) \\ i_t &= \sigma(W_i x_t + U_i h_{t-1} + b_i) \\ o_t &= \sigma(W_o x_t + U_o h_{t-1} + b_o) \\ c_t &= f_t \odot c_{t-1} + i_t \odot \tanh(W_c x_t + U_c h_{t-1} + b_c) \\ h_t &= o_t \odot \tanh(c_t) \end{aligned}`
47. `\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V`
48. `\text{Output} = \text{LayerNorm}(x + \text{Dropout}(\text{MultiHead}(x,x,x) + \text{FFN}(x)))`
49. `\min_G \max_D V(D,G) = \mathbb{E}_{x\sim p_{data}}[\log D(x)] + \mathbb{E}_{z\sim p_z}[\log (1 - D(G(z)))]`
50. `\mathcal{L}(\theta, \phi) = -\mathbb{E}_{q_{\phi}(z|x)}[\log p_{\theta}(x|z)] + \text{KL}(q_{\phi}(z|x) \|\| p(z))`

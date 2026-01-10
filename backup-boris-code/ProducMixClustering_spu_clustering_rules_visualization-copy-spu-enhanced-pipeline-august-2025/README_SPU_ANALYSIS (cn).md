SPU（款粒度）分析

日期：2025-01-27 分析周期：202506A 分析门店总数：2,263

> 分析**SPU**总数：526,846 个唯一门店-SPU组合

管理摘要

本分析包包含了对您的零售网络在SPU（单品）层面的全面分析，包括聚类分析与业务规则
评估。所有分析均以单品（SPU）为单位，提供比品类聚合更细致的洞察。

主要发现

> 跨7个温度带创建了**44**个人温感知聚类
> 应用了**6**项业务规则以识别优化机会 提供交互式看板支持详细探索
>
> 地理可视化呈现区域分布特征

分析包内容

📊 /clustering/

**SPU**层门店聚类结果

> clustering_results_spu.csv- 2,263家门店的主要聚类分配
>
> cluster_profiles_spu.csv- 各聚类详细特征
>
> per_cluster_metrics_spu.csv- 各聚类统计指标
>
> spu_clustering_documentation.md- 聚类技术说明文档

核心洞察：

> 44个聚类，门店数量均衡（每聚类47-75家门店）
>
> 以5°C温度带为粒度实现温感知聚类 针对SPU层面相似性优化

🎯 /rules/

业务规则分析结果

规则**7**：**SPU**缺失机会

> rule7_missing_spu_results.csv- 门店级结果
>
> rule7_missing_spu_opportunities.csv- 详细机会清单
>
> rule7_missing_spu_summary.md- 管理摘要
>
> 结果：共1,611家门店存在3,878个SPU机会

规则**8**：**SPU**分配不均

> rule8_imbalanced_spu_results.csv- 门店级结果
>
> rule8_imbalanced_spu_cases.csv- 详细不均分案例
>
> rule8_imbalanced_spu_z_score_analysis.csv- 统计分析
>
> rule8_imbalanced_spu_summary.md- 管理摘要
>
> 结果：2,254家门店被标记，共43,170个SPU分配不均

规则**9**：**SPU**低于最小值分析 ⚠

> rule9_below_minimum_spu_results.csv- 门店级结果
>
> rule9_below_minimum_spu_cases.csv- 详细案例
>
> rule9_below_minimum_spu_summary.md- 管理摘要
>
> 说明：此规则在SPU层面存在逻辑问题（见技术说明）

规则**10**：**SPU**智能超配分析

> rule10_smart_overcapacity_spu_results.csv- 门店级结果
>
> rule10_smart_overcapacity_spu_opportunities_strict.csv- 保守方案
>
> rule10_smart_overcapacity_spu_opportunities_standard.csv- 平衡方案
>
> rule10_smart_overcapacity_spu_opportunities_lenient.csv- 激进方案
>
> rule10_smart_overcapacity_spu_summary.md- 管理摘要
>
> 结果：601家门店发现1,219个再分配机会

规则**11**：**SPU**错失销售机会分析

> rule11_missed_sales_opportunity_spu_results.csv- 门店级结果
>
> rule11_missed_sales_opportunity_spu_details.csv- 详细分析
>
> rule11_missed_sales_opportunity_spu_summary.md- 管理摘要
>
> 结果：无门店被标记（未发现重大问题）

规则**12**：**SPU**销售表现分析

> rule12_sales_performance_spu_results.csv- 门店级结果
>
> rule12_sales_performance_spu_details.csv- 详细表现数据
>
> rule12_sales_performance_spu_summary.md- 管理摘要
>
> 结果：1,326家门店存在表现机会

综合结果

> consolidated_spu_rule_results.csv- 全部规则合并结果（2.3MB）
>
> consolidated_spu_rule_summary.md- 管理总览

📈 /dashboards/

交互式分析看板

全局总览看板

> global_overview_spu_dashboard.html- 管理KPI看板
>
> 功能：门店业绩、规则违规统计、战略洞察
>
> 用法：浏览器打开即可交互操作

交互式地图看板

> interactive_map_spu_dashboard.html- 地理分析（7.1MB）
>
> 功能：
>
> 2,259家门店带业绩分色
>
> SPU层级详细弹窗，含规则洞察
>
> 基于规则的筛选和聚类分析
>
> 实时统计面板

🎨 /visualizations/

图表与可视化分析

> cluster_visualization_spu.png- 聚类分布可视化图
>
> cluster_map_spu.html- 交互式聚类地图
>
> cluster_plots_spu.html- 交互式聚类分析图
>
> cluster_plots_spu.png- 静态聚类图
>
> cluster_visualization_report_spu.md- 可视化方法报告
>
> cluster_analysis_spu.csv- 可视化底层数据
>
> cluster_detailed_data_spu.csv- 详细聚类指标

📚 /documentation/

技术文档

> README_CLUSTER_VISUALIZATION.md- 聚类可视化指南
>
> create_spu_visualization.py- 可视化脚本

业务影响分析

🎯 高优先级行动项

> 1\. 规则**8**（分配不均）：2,254家门店共43,170个SPU分配不均
>
> 2\. 规则**7**（**SPU**缺失）：1,611家门店共3,878个机会
>
> 3\. 规则**12**（业绩表现）：1,326家门店存在业绩提升空间

💡 战略洞察

> 基于聚类的优化：利用温感知聚类制定区域策略
>
> **SPU**级精细化管理：对单品优化远胜于品类层面
>
> 业绩对标：同类聚类内门店横向对比

📊 数据质量

> 覆盖率：成功分析99.8%的门店
>
> 完整性：处理526,846个门店-SPU组合
>
> 准确性：用Z分数和同行对标作统计校验

技术说明

⚠ 重要限制

> 1\.
> 规则**9**问题：“低于最小值”规则在SPU层级逻辑不严谨，单一SPU不能有小数件，
> 建议在子品类层级应用。
>
> 2\. 数据代理：SPU分析用销售额做分配代理，采用sales_amount / 1000公式。
>
> 3\. 温度依赖：聚类整合了气象数据，结果受季节影响。

🔧 方法说明

> 聚类算法：基于温度分层的K-means
>
> 统计校验：Z分数分析判别分配不均
>
> 同行对标：同聚类门店业绩横向对比
>
> 多策略分析：提供保守/平衡/激进多种优化方案

使用建议

对高管

> 1\. 先阅读consolidated_spu_rule_summary.md了解总览
>
> 2\. 用global_overview_spu_dashboard.html监控KPI
>
> 3\. 重点关注规则7、8、12，优先推动落地

对运营团队

> 1\. 用interactive_map_spu_dashboard.html做区域规划
>
> 2\. 分析各规则CSV文件，制定具体行动
>
> 3\. 利用聚类画像做对标与提升

对分析师

> 1\. 深入分析案例文件，定位根因
>
> 2\. 图表可直接用于报告与展示
>
> 3\. 参考技术文档，确保分析方法规范

下一步建议

> 1\. 验证：与业务方一同复核规则输出
>
> 2\. 优先级：资源聚焦高影响机会
>
> 3\. 落地实施：区域先行，分步推进
>
> 4\. 持续监控：用汇总指标建立KPI体系

联系人：数据分析团队 版本：SPU Analysis v1.0 最后更新时间：2025-01-27

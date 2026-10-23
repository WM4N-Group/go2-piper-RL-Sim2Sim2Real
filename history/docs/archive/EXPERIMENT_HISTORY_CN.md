# 历史实验档案（去重归档）

2026-10-14新增归档入口：[PUSH切换开发逐版记录](#transition-through-v269-20261014)、[CLIMB迁移诊断](#climb-sim2sim-diagnostics-20261009)。归档内“当前/运行中”均为历史快照，接手从[总交接](../AGENT_HANDOFF_CN.md)开始。

归档于2026-10-07；原始版本提交`73343fc0f7c6274d8ce936e2ae8d4e090dcf8847`。下面保留旧文档的独有章节，完全相同的章节合并并列出来源。历史中的“当前”“下一步”“运行中”、PID、目标判据和命令均属于记录当时；不得当作当前运行指令。当前入口见[总交接](../AGENT_HANDOFF_CN.md)。

审计注（2026-10-08）：历史中“448000个采样均三足支撑”的表述不严谨。448000是腿部几何轨迹采样数；步态统计排除初始化前0.1秒，以单足竖直力>2N计支撑。当前指标及终态核验范围见[CLIMB交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)，以下历史正文保持原样。

需要恢复原文件排版或原路径引用时，可用`git show 73343fc0f7c6274d8ce936e2ae8d4e090dcf8847:docs/原文件名.md`。原报告、权重、录像及哈希未修改。

## 原文件索引

<a id="source-agent-handoff-cn"></a>

### AGENT_HANDOFF_CN.md

[record-0001](#record-0001), [record-0002](#record-0002), [record-0003](#record-0003), [record-0004](#record-0004), [record-0005](#record-0005), [record-0006](#record-0006), [record-0007](#record-0007), [record-0008](#record-0008), [record-0009](#record-0009), [record-0010](#record-0010), [record-0011](#record-0011), [record-0012](#record-0012), [record-0013](#record-0013), [record-0014](#record-0014), [record-0015](#record-0015), [record-0016](#record-0016), [record-0017](#record-0017), [record-0018](#record-0018), [record-0019](#record-0019), [record-0020](#record-0020), [record-0021](#record-0021), [record-0022](#record-0022), [record-0023](#record-0023), [record-0024](#record-0024), [record-0025](#record-0025), [record-0026](#record-0026), [record-0027](#record-0027), [record-0028](#record-0028), [record-0029](#record-0029), [record-0030](#record-0030), [record-0031](#record-0031), [record-0032](#record-0032), [record-0033](#record-0033), [record-0034](#record-0034), [record-0035](#record-0035), [record-0036](#record-0036), [record-0037](#record-0037), [record-0038](#record-0038), [record-0039](#record-0039), [record-0040](#record-0040), [record-0041](#record-0041), [record-0042](#record-0042), [record-0043](#record-0043), [record-0044](#record-0044), [record-0045](#record-0045), [record-0046](#record-0046), [record-0047](#record-0047), [record-0048](#record-0048), [record-0049](#record-0049), [record-0050](#record-0050), [record-0051](#record-0051), [record-0052](#record-0052), [record-0053](#record-0053), [record-0054](#record-0054), [record-0055](#record-0055), [record-0056](#record-0056), [record-0057](#record-0057), [record-0058](#record-0058), [record-0059](#record-0059), [record-0060](#record-0060), [record-0061](#record-0061), [record-0062](#record-0062), [record-0063](#record-0063), [record-0064](#record-0064), [record-0065](#record-0065), [record-0066](#record-0066), [record-0067](#record-0067), [record-0068](#record-0068), [record-0069](#record-0069), [record-0070](#record-0070), [record-0071](#record-0071), [record-0072](#record-0072), [record-0073](#record-0073), [record-0074](#record-0074), [record-0075](#record-0075), [record-0076](#record-0076), [record-0077](#record-0077), [record-0078](#record-0078), [record-0079](#record-0079), [record-0080](#record-0080), [record-0081](#record-0081), [record-0082](#record-0082), [record-0083](#record-0083), [record-0084](#record-0084), [record-0085](#record-0085), [record-0086](#record-0086), [record-0087](#record-0087), [record-0088](#record-0088), [record-0089](#record-0089), [record-0090](#record-0090), [record-0091](#record-0091), [record-0092](#record-0092), [record-0093](#record-0093), [record-0094](#record-0094), [record-0095](#record-0095), [record-0096](#record-0096), [record-0097](#record-0097), [record-0098](#record-0098), [record-0099](#record-0099), [record-0100](#record-0100), [record-0101](#record-0101), [record-0102](#record-0102), [record-0103](#record-0103), [record-0104](#record-0104), [record-0105](#record-0105), [record-0106](#record-0106), [record-0107](#record-0107), [record-0108](#record-0108), [record-0109](#record-0109), [record-0110](#record-0110), [record-0111](#record-0111), [record-0112](#record-0112), [record-0113](#record-0113), [record-0114](#record-0114), [record-0115](#record-0115), [record-0116](#record-0116), [record-0117](#record-0117), [record-0118](#record-0118), [record-0119](#record-0119), [record-0120](#record-0120), [record-0121](#record-0121), [record-0122](#record-0122), [record-0123](#record-0123), [record-0124](#record-0124), [record-0125](#record-0125), [record-0126](#record-0126), [record-0127](#record-0127), [record-0128](#record-0128), [record-0129](#record-0129), [record-0130](#record-0130), [record-0131](#record-0131), [record-0132](#record-0132), [record-0133](#record-0133), [record-0134](#record-0134), [record-0135](#record-0135), [record-0136](#record-0136), [record-0137](#record-0137), [record-0138](#record-0138), [record-0139](#record-0139), [record-0140](#record-0140)

<a id="source-climb-crawl-status-20261001-cn"></a>

### CLIMB_CRAWL_STATUS_20261001_CN.md

[record-0141](#record-0141), [record-0002](#record-0002), [record-0003](#record-0003), [record-0004](#record-0004), [record-0005](#record-0005), [record-0006](#record-0006), [record-0007](#record-0007), [record-0008](#record-0008), [record-0009](#record-0009), [record-0010](#record-0010), [record-0011](#record-0011), [record-0012](#record-0012), [record-0013](#record-0013), [record-0014](#record-0014), [record-0015](#record-0015), [record-0016](#record-0016), [record-0017](#record-0017), [record-0018](#record-0018), [record-0019](#record-0019), [record-0020](#record-0020), [record-0021](#record-0021), [record-0022](#record-0022), [record-0023](#record-0023), [record-0024](#record-0024), [record-0025](#record-0025), [record-0026](#record-0026), [record-0027](#record-0027), [record-0028](#record-0028), [record-0029](#record-0029), [record-0030](#record-0030), [record-0031](#record-0031), [record-0032](#record-0032), [record-0035](#record-0035), [record-0036](#record-0036), [record-0037](#record-0037), [record-0038](#record-0038), [record-0039](#record-0039), [record-0040](#record-0040), [record-0041](#record-0041), [record-0042](#record-0042), [record-0043](#record-0043), [record-0044](#record-0044), [record-0045](#record-0045), [record-0046](#record-0046), [record-0047](#record-0047), [record-0048](#record-0048), [record-0049](#record-0049), [record-0050](#record-0050), [record-0051](#record-0051), [record-0052](#record-0052), [record-0053](#record-0053), [record-0054](#record-0054), [record-0055](#record-0055), [record-0056](#record-0056), [record-0057](#record-0057), [record-0058](#record-0058), [record-0059](#record-0059), [record-0060](#record-0060), [record-0061](#record-0061), [record-0062](#record-0062), [record-0063](#record-0063), [record-0064](#record-0064), [record-0065](#record-0065), [record-0066](#record-0066), [record-0067](#record-0067), [record-0068](#record-0068), [record-0069](#record-0069), [record-0070](#record-0070), [record-0071](#record-0071), [record-0072](#record-0072), [record-0073](#record-0073), [record-0074](#record-0074), [record-0075](#record-0075), [record-0076](#record-0076), [record-0077](#record-0077), [record-0078](#record-0078), [record-0079](#record-0079), [record-0080](#record-0080), [record-0081](#record-0081), [record-0082](#record-0082), [record-0083](#record-0083), [record-0084](#record-0084), [record-0085](#record-0085), [record-0086](#record-0086), [record-0087](#record-0087), [record-0088](#record-0088), [record-0089](#record-0089), [record-0090](#record-0090), [record-0091](#record-0091), [record-0092](#record-0092), [record-0093](#record-0093), [record-0094](#record-0094), [record-0095](#record-0095), [record-0096](#record-0096), [record-0097](#record-0097), [record-0098](#record-0098), [record-0099](#record-0099), [record-0100](#record-0100), [record-0101](#record-0101), [record-0102](#record-0102), [record-0103](#record-0103), [record-0104](#record-0104), [record-0105](#record-0105), [record-0106](#record-0106), [record-0107](#record-0107), [record-0108](#record-0108), [record-0109](#record-0109), [record-0110](#record-0110), [record-0111](#record-0111), [record-0112](#record-0112), [record-0113](#record-0113), [record-0114](#record-0114), [record-0115](#record-0115), [record-0116](#record-0116), [record-0117](#record-0117), [record-0118](#record-0118), [record-0119](#record-0119), [record-0120](#record-0120), [record-0121](#record-0121), [record-0122](#record-0122), [record-0123](#record-0123), [record-0124](#record-0124), [record-0125](#record-0125), [record-0126](#record-0126), [record-0142](#record-0142), [record-0143](#record-0143), [record-0144](#record-0144), [record-0145](#record-0145), [record-0146](#record-0146), [record-0147](#record-0147), [record-0148](#record-0148), [record-0149](#record-0149), [record-0150](#record-0150), [record-0151](#record-0151), [record-0152](#record-0152), [record-0153](#record-0153), [record-0154](#record-0154), [record-0155](#record-0155), [record-0156](#record-0156), [record-0157](#record-0157), [record-0158](#record-0158), [record-0159](#record-0159), [record-0160](#record-0160), [record-0161](#record-0161), [record-0162](#record-0162), [record-0163](#record-0163), [record-0164](#record-0164), [record-0165](#record-0165), [record-0166](#record-0166), [record-0167](#record-0167), [record-0168](#record-0168), [record-0169](#record-0169), [record-0170](#record-0170), [record-0171](#record-0171), [record-0172](#record-0172), [record-0173](#record-0173), [record-0174](#record-0174), [record-0175](#record-0175), [record-0176](#record-0176)

<a id="source-climb-edge-training-20261002-cn"></a>

### CLIMB_EDGE_TRAINING_20261002_CN.md

[record-0177](#record-0177), [record-0002](#record-0002), [record-0003](#record-0003), [record-0004](#record-0004), [record-0005](#record-0005), [record-0006](#record-0006), [record-0007](#record-0007), [record-0008](#record-0008), [record-0009](#record-0009), [record-0010](#record-0010), [record-0011](#record-0011), [record-0012](#record-0012), [record-0013](#record-0013), [record-0014](#record-0014), [record-0015](#record-0015), [record-0016](#record-0016), [record-0017](#record-0017), [record-0018](#record-0018), [record-0019](#record-0019), [record-0020](#record-0020), [record-0021](#record-0021), [record-0022](#record-0022), [record-0023](#record-0023), [record-0024](#record-0024), [record-0025](#record-0025), [record-0026](#record-0026), [record-0027](#record-0027), [record-0028](#record-0028), [record-0029](#record-0029), [record-0030](#record-0030), [record-0031](#record-0031), [record-0032](#record-0032), [record-0035](#record-0035), [record-0036](#record-0036), [record-0037](#record-0037), [record-0038](#record-0038), [record-0039](#record-0039), [record-0040](#record-0040), [record-0041](#record-0041), [record-0042](#record-0042), [record-0043](#record-0043), [record-0044](#record-0044), [record-0045](#record-0045), [record-0046](#record-0046), [record-0047](#record-0047), [record-0048](#record-0048), [record-0049](#record-0049), [record-0050](#record-0050), [record-0051](#record-0051), [record-0052](#record-0052), [record-0053](#record-0053), [record-0054](#record-0054), [record-0055](#record-0055), [record-0056](#record-0056), [record-0057](#record-0057), [record-0058](#record-0058), [record-0059](#record-0059), [record-0060](#record-0060), [record-0061](#record-0061), [record-0062](#record-0062), [record-0063](#record-0063), [record-0064](#record-0064), [record-0065](#record-0065), [record-0066](#record-0066), [record-0067](#record-0067), [record-0068](#record-0068), [record-0069](#record-0069), [record-0070](#record-0070), [record-0071](#record-0071), [record-0072](#record-0072), [record-0073](#record-0073), [record-0074](#record-0074), [record-0075](#record-0075), [record-0076](#record-0076), [record-0077](#record-0077), [record-0078](#record-0078), [record-0079](#record-0079), [record-0080](#record-0080), [record-0081](#record-0081), [record-0082](#record-0082), [record-0083](#record-0083), [record-0084](#record-0084), [record-0085](#record-0085), [record-0086](#record-0086), [record-0087](#record-0087), [record-0088](#record-0088), [record-0089](#record-0089), [record-0090](#record-0090), [record-0091](#record-0091), [record-0092](#record-0092), [record-0093](#record-0093), [record-0094](#record-0094), [record-0095](#record-0095), [record-0096](#record-0096), [record-0097](#record-0097), [record-0098](#record-0098), [record-0099](#record-0099), [record-0100](#record-0100), [record-0101](#record-0101), [record-0102](#record-0102), [record-0103](#record-0103), [record-0104](#record-0104), [record-0105](#record-0105), [record-0106](#record-0106), [record-0107](#record-0107), [record-0178](#record-0178), [record-0179](#record-0179), [record-0180](#record-0180), [record-0181](#record-0181), [record-0182](#record-0182), [record-0183](#record-0183), [record-0184](#record-0184), [record-0185](#record-0185), [record-0186](#record-0186), [record-0187](#record-0187), [record-0188](#record-0188), [record-0189](#record-0189), [record-0190](#record-0190), [record-0191](#record-0191), [record-0192](#record-0192), [record-0193](#record-0193), [record-0194](#record-0194), [record-0195](#record-0195), [record-0196](#record-0196), [record-0116](#record-0116), [record-0115](#record-0115), [record-0114](#record-0114), [record-0113](#record-0113), [record-0112](#record-0112), [record-0111](#record-0111), [record-0110](#record-0110), [record-0109](#record-0109)

<a id="source-climb-isaac-status-20261001-cn"></a>

### CLIMB_ISAAC_STATUS_20261001_CN.md

[record-0197](#record-0197), [record-0198](#record-0198), [record-0199](#record-0199)

<a id="source-climb-terrain-reference-plan-20261002-cn"></a>

### CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN.md

[record-0200](#record-0200), [record-0201](#record-0201), [record-0202](#record-0202), [record-0203](#record-0203)

<a id="source-next-steps-cn"></a>

### NEXT_STEPS_CN.md

[record-0204](#record-0204), [record-0002](#record-0002), [record-0003](#record-0003), [record-0004](#record-0004), [record-0005](#record-0005), [record-0006](#record-0006), [record-0007](#record-0007), [record-0008](#record-0008), [record-0009](#record-0009), [record-0010](#record-0010), [record-0011](#record-0011), [record-0012](#record-0012), [record-0013](#record-0013), [record-0014](#record-0014), [record-0015](#record-0015), [record-0016](#record-0016), [record-0017](#record-0017), [record-0018](#record-0018), [record-0019](#record-0019), [record-0020](#record-0020), [record-0021](#record-0021), [record-0022](#record-0022), [record-0023](#record-0023), [record-0024](#record-0024), [record-0025](#record-0025), [record-0026](#record-0026), [record-0027](#record-0027), [record-0028](#record-0028), [record-0029](#record-0029), [record-0030](#record-0030), [record-0031](#record-0031), [record-0032](#record-0032), [record-0035](#record-0035), [record-0036](#record-0036), [record-0037](#record-0037), [record-0038](#record-0038), [record-0039](#record-0039), [record-0040](#record-0040), [record-0041](#record-0041), [record-0042](#record-0042), [record-0043](#record-0043), [record-0044](#record-0044), [record-0045](#record-0045), [record-0046](#record-0046), [record-0047](#record-0047), [record-0048](#record-0048), [record-0049](#record-0049), [record-0050](#record-0050), [record-0051](#record-0051), [record-0052](#record-0052), [record-0053](#record-0053), [record-0054](#record-0054), [record-0055](#record-0055), [record-0056](#record-0056), [record-0057](#record-0057), [record-0058](#record-0058), [record-0059](#record-0059), [record-0060](#record-0060), [record-0061](#record-0061), [record-0062](#record-0062), [record-0063](#record-0063), [record-0064](#record-0064), [record-0065](#record-0065), [record-0066](#record-0066), [record-0067](#record-0067), [record-0068](#record-0068), [record-0069](#record-0069), [record-0070](#record-0070), [record-0071](#record-0071), [record-0072](#record-0072), [record-0073](#record-0073), [record-0074](#record-0074), [record-0075](#record-0075), [record-0076](#record-0076), [record-0077](#record-0077), [record-0078](#record-0078), [record-0079](#record-0079), [record-0080](#record-0080), [record-0081](#record-0081), [record-0082](#record-0082), [record-0083](#record-0083), [record-0084](#record-0084), [record-0085](#record-0085), [record-0086](#record-0086), [record-0087](#record-0087), [record-0088](#record-0088), [record-0089](#record-0089), [record-0090](#record-0090), [record-0091](#record-0091), [record-0092](#record-0092), [record-0093](#record-0093), [record-0094](#record-0094), [record-0095](#record-0095), [record-0096](#record-0096), [record-0097](#record-0097), [record-0098](#record-0098), [record-0099](#record-0099), [record-0100](#record-0100), [record-0101](#record-0101), [record-0102](#record-0102), [record-0103](#record-0103), [record-0104](#record-0104), [record-0105](#record-0105), [record-0106](#record-0106), [record-0107](#record-0107), [record-0108](#record-0108), [record-0109](#record-0109), [record-0110](#record-0110), [record-0111](#record-0111), [record-0112](#record-0112), [record-0113](#record-0113), [record-0114](#record-0114), [record-0115](#record-0115), [record-0116](#record-0116), [record-0117](#record-0117), [record-0118](#record-0118), [record-0119](#record-0119), [record-0120](#record-0120), [record-0121](#record-0121), [record-0122](#record-0122), [record-0123](#record-0123), [record-0124](#record-0124), [record-0125](#record-0125), [record-0126](#record-0126), [record-0205](#record-0205), [record-0206](#record-0206), [record-0207](#record-0207), [record-0208](#record-0208), [record-0209](#record-0209), [record-0210](#record-0210), [record-0211](#record-0211), [record-0212](#record-0212), [record-0213](#record-0213), [record-0214](#record-0214), [record-0215](#record-0215), [record-0216](#record-0216), [record-0217](#record-0217), [record-0218](#record-0218), [record-0219](#record-0219), [record-0220](#record-0220), [record-0221](#record-0221), [record-0222](#record-0222), [record-0223](#record-0223), [record-0224](#record-0224), [record-0225](#record-0225), [record-0226](#record-0226)

<a id="source-project-plan-cn"></a>

### PROJECT_PLAN_CN.md

[record-0227](#record-0227), [record-0228](#record-0228), [record-0229](#record-0229), [record-0230](#record-0230), [record-0231](#record-0231), [record-0232](#record-0232), [record-0233](#record-0233), [record-0234](#record-0234), [record-0235](#record-0235), [record-0236](#record-0236)

<a id="source-push-isaac-runbook-cn"></a>

### PUSH_ISAAC_RUNBOOK_CN.md

[record-0237](#record-0237), [record-0238](#record-0238), [record-0239](#record-0239), [record-0240](#record-0240), [record-0241](#record-0241), [record-0242](#record-0242)

<a id="source-push-load-comparison-20261001-cn"></a>

### PUSH_LOAD_COMPARISON_20261001_CN.md

[record-0243](#record-0243), [record-0244](#record-0244), [record-0245](#record-0245), [record-0246](#record-0246)

<a id="source-training-status-20260929-cn"></a>

### TRAINING_STATUS_20260929_CN.md

[record-0247](#record-0247), [record-0248](#record-0248), [record-0249](#record-0249), [record-0250](#record-0250), [record-0251](#record-0251), [record-0252](#record-0252), [record-0253](#record-0253)

<a id="source-training-status-20260930-cn"></a>

### TRAINING_STATUS_20260930_CN.md

[record-0254](#record-0254), [record-0255](#record-0255), [record-0256](#record-0256), [record-0257](#record-0257)

<a id="source-training-status-20261001-cn"></a>

### TRAINING_STATUS_20261001_CN.md

[record-0258](#record-0258), [record-0259](#record-0259), [record-0260](#record-0260), [record-0261](#record-0261), [record-0262](#record-0262), [record-0263](#record-0263), [record-0264](#record-0264), [record-0265](#record-0265), [record-0266](#record-0266), [record-0267](#record-0267), [record-0268](#record-0268), [record-0269](#record-0269), [record-0270](#record-0270), [record-0271](#record-0271), [record-0272](#record-0272), [record-0273](#record-0273), [record-0274](#record-0274), [record-0275](#record-0275), [record-0276](#record-0276), [record-0277](#record-0277), [record-0278](#record-0278), [record-0279](#record-0279), [record-0280](#record-0280), [record-0281](#record-0281), [record-0282](#record-0282), [record-0283](#record-0283), [record-0284](#record-0284), [record-0285](#record-0285), [record-0286](#record-0286), [record-0287](#record-0287), [record-0288](#record-0288), [record-0289](#record-0289), [record-0290](#record-0290), [record-0291](#record-0291)

## 独有记录

<a id="record-0001"></a>

来源：AGENT_HANDOFF_CN.md。

# GO2-PIPER Agent 交接手册

<a id="record-0002"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 当前交接更新（2026-10-07 22:25）

**CLIMB在Isaac的登台、前脚展开、舒展稳定承重功能已跑通，进入提速和鲁棒性验收阶段。** 用户确认登台后的目标点行走由NAV负责；旧评估中心位置指标0/32只保留作历史任务数据，不再否定CLIMB成功或驱动额外攀爬前移。独立CLIMB完成信号和NAV切换仍需单独落实/验证，本次没有改写评估源码或原报告。

最新iy三秒摆脚全程32/32成功保留、终态缺失0、全部腿部采样净空≥6.075mm；同种子登台停稳平均190.92→172.99秒，双前脚展开222.85→202.85秒。原四秒版本iv/iw两组各32/32；三秒版本另一组尚未开始，不能混算正式验收。22:25核对远端无项目评估/训练/核验进程，iy早已结束；下一步冻结iy回归seed28302，再继续提速。约3～4分钟仍太慢，最终原起点两组未用种子验收、NAV衔接、MuJoCo/实机验证未完成；PUSH技能、MuJoCo、实机暂停。

**交接请先读[CLIMB当前小组交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)**，其中给出技能边界、准确成功率/耗时、物理证据、源包/报告/视频路径与哈希，以及接手顺序。下方为历史日志，旧“正在运行”“原完整任务0/32”和“为达到中心目标继续前移”等描述仅适用于当时，不代表当前状态或工作目标。

<a id="record-0003"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 历史记录（截至2026-10-07 10:25）

<a id="record-0004"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ix三秒摆脚110秒诊断通过，iy冻结参数验证全程成功率和耗时（2026-10-07 10:25）

**先保留成功率，再确认提速。** ix/swingspeed27302于09:52:27正常完成、09:54:56严格核验通过、09:56:42全110秒几何完成。seed27302/32例在首次非零摆动相位前与原iv逐字段严格相同（各203～256样本，无遥测例外），实际PhysX质量相同且缓存同步。唯一运行源改动是评估配置swing_s从4.0变3.0，其余11运行源/actor/reset保持；原真实抬脚/跨步跟踪、卸载/落脚/重载/停稳和碰撞/执行器/关节参考速率加速度限制不变。

**全部176000个20ms实际腿部样本净空最小6.075025mm，低于5mm和负间隙均0。** 三足及以上采样100%、腾空0、安全终止0、|vz|峰.090701364m/s、含子步历史单足合力峰144.183228N、含初始化力矩饱和0。370次起摆均满足原≤5N连续.2秒门禁，352次已发生承重转换满足≥8N/reload1/连续.2秒；18次窗口末摆动尚待重载，原始audit保留no_recorded_reload_for_swing，分类后的已发生门禁违例0、终止失败后未重载0。见release-reload-short-review.json，不能把370次起摆全部写成已完成重载。几何只覆盖20ms原USD腿部原语，不覆盖物理子步或非腿部全机碰撞。

**本轮是110秒短窗口：原完整成功0、四足登台0、终态0、32例预期未完成，不是终态缺失或32成功。** 同期承重转换由原iv前110秒312次增至352次。以同种子相同初始腿序配对，32例首次前脚真实重载平均提前.9619秒，第二前脚平均提前1.9756秒（范围1.00～2.62秒）；前四步腿序仍一致的30例，第四步重载平均提前3.776秒（1.38～5.12秒）。另2例在第三步开始腿序不同，后续只比较进度，不作错误逐步配对。见prefix-progress-comparison.json；局部提速已观察到，完整阶段成功保留及总完成时间收益尚未证明。

ix报告1514617834字节，SHA256 `176fdfe99cb8d70b0eb0e3763255af1ea6bf0a7ce153fde79d29eb80f0bb0c0f`，10:01:46完整本地下载并独立流式哈希通过。env28原速录像110秒/2750帧/25fps，SHA256 `11c08a0b3b91ed225034ee3d38b0220ff0efb6429ae47027f4410abc04acaa9d`，远端/本地一致；已全解码并审阅10/40/80/90/100/109.96秒抽帧，支持前后脚推进和中段转移，不是全片原速验收。

**当前iy/swingspeedfull27302在既有远端GPU1运行，勿重复启动。** 10:23:57启动，监控PID751928、自动核验PID751932；全部脚本上传后于10:24:14启动几何等待PID752212。seed27302/32、280秒/14000步，全32密集轨迹、相机env28。12运行源/源包/actor/reset与ix逐字节相同，只延长110→280秒并更换输出路径，无进一步提速或控制修改。6项前置核验、完整源包及实际启动源/actor/reset核验通过；补丁仍`3e3635221ac0ad2ecaa65af3b8d4da3141d26f0296f84f6f367554df2f8b8334`。本地fetch-verified-report.py/PID2272273已等待严格核验与几何状态，之后下载录像/小型证据/完整报告并独立哈希。

iy完成后先核验全32前5500样本与ix逐字段严格相同、32唯一首回合终态/缺失、原任务与登台/展开/舒展分开计数；相对同seed27302的iv原32报告保留/丢失，检查完整三足/腾空/vz/接触合力/含初始化饱和、释放重载、全部448000腿部样本几何与原速视频。只有全程保留成功且几何通过后才评价总耗时收益并冻结3秒参数回归已用seed28302；短窗口通过不能代替后段登台/前脚展开/收尾保留。如果退化则保留失败证据并诊断，不放宽门禁。

已完整验证的鲁棒基线仍是原4秒摆脚iv/iw两组各32/32阶段完成、全程5mm净空通过；当前3秒候选只有110秒证据。原完整任务在基线仍0/32，原中心目标x1.35m、水平误差<.20m、既有NAV能力与原起点衔接以及最终两组未用种子各32且各至少30成功/无缺失仍待完成。27302/28302已用，29302尚未运行。280秒仅全程失败诊断，约4分钟不是可接受最终时长，不是24秒慢爬或原起点12秒验收。保留四足先承重停稳、前脚逐只展开、再最后前移重心，不重训NAV/PPO。候选源只在外部产物，指定GitHub分支只同步证据文档；PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0005"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：iw另一已用种子32/32且净空通过，ix开始单参数摆脚提速诊断（2026-10-07 09:28）

**两组已用种子的当前阶段鲁棒性均通过；开始小步验证效率，原任务仍未通过。** iw/reservereg28302于08:34:54正常完成，08:38:19严格核验通过、08:39:32释放重载通过、08:41:35全程几何完成。seed28302的32/32均四足登台、双前脚逐只展开及严格最终舒展承重；同种子iq原32例阶段成功全部保留、丢失0。全32前4000个20ms样本与iq前80秒逐字段严格相同，实际PhysX质量相同且缓存同步；12运行源/actor/reset与iv冻结一致。iv seed27302与iw seed28302合计64/64阶段完成，不能作为固定候选的两组未用种子验收。

**iw全部448000个20ms实际腿部样本最小净空6.241024mm，低于5mm与负间隙均0。** 原4例中段缺口env2/3/24/31全280秒最小分别6.501/7.583/6.269/6.534mm，已消除。三足及以上采样100%、腾空0、安全终止0、|vz|峰.100830354m/s、含子步历史单足合力峰148.109055N、含初始化力矩饱和0。640次起摆及其后续重载符合原≤5N连续.2秒释放、≥8N/reload1/连续.2秒重载，704次承重转换，violations为空。几何只覆盖20ms采样的原USD腿部原语，不覆盖物理子步和非腿部全机碰撞。

**原完整任务仍0/32，32唯一首回合终态、缺失0，全部time_out。** 首次四足台面承重停稳185.66～220.92秒、双前脚展开完成214.26～253.78秒、终态连续稳定11.56～52.06秒。距原中心目标x1.35m仍.34738～.39354m，全部未达到水平误差<.20m；至少还需整体前移约.14739～.19785m才到容差边界。目标位置及既有NAV能力与原起点衔接尚待完成，不重训NAV/PPO、不改变原目标判据。280秒仍仅箱沿阶段诊断，约4分钟不可接受为最终时长，不是24秒慢爬或原起点12秒验收。

iw报告3878623470字节，SHA256 `17f98d169addd75740fb88e09837f2f1df82a8c2006f1784d42d7400d09acbc7`，08:54:18完整本地下载且独立流式哈希通过。env3原速录像280秒/7000帧/25fps，SHA256 `69ee799d1cf62d36ebdcccea5c3bc88773bf54763951aaf6c242d8fe04da2fe7`，远端/本地一致；已全解码并审阅40/91.7/110/200/250/279.96秒抽帧，支持中段支撑、后脚登台、前脚展开及终态稳定，**不是全片原速验收**。见video-verification.json、original-goal-audit.json及local-report-verification.json。iv上一批也已全量归档并独立哈希通过。

**已完成两批64例的原轨迹耗时分解。** iv/iw平均摆脚相位推进均79.20秒，支撑转移或卸载93.13/95.80秒，落脚与重载37.86/38.03秒，平台两次前脚之间承重等待10.84/10.46秒。余下含初始化和最终调整/维持至280秒窗口结束，不能把窗口尾部停稳时间都算作完成所必需时间。边界停留和重载耗时包含必要的物理跟踪，不能直接当成可删除等待。见两目录timing-audit.json与audit-timing.py。当前实际swing_s=4.0，20次摆脚的名义轨迹占80秒，先单独检验4→3秒，名义可能减少约20秒，实际收益和稳定性尚未证明；这只是首轮提速，不代表4分钟问题已解决。

**当前ix/swingspeed27302在既有远端GPU1运行，勿重复启动。** 09:27:12启动，监控PID751240、自动核验PID751244；全部脚本上传完成后于09:27:28启动几何等待PID751524。seed27302/32、诊断窗口110秒/5500步、回合上限仍280秒，全32密集轨迹、相机env28。唯一运行源差异是evaluate_box_skills.py里swing_s=4.0改为3.0；其它11源、actor/reset、支撑转移、抬脚/跨步真实跟踪、卸载/落脚/重载/停稳、碰撞/执行器及关节参考速率/加速度限制保持。6项前置核验及实际启动源/actor/reset通过；补丁SHA256 `3e3635221ac0ad2ecaa65af3b8d4da3141d26f0296f84f6f367554df2f8b8334`。原iv/iw成功基线保留，候选只在外部产物。

ix完成后：全32在首次非零摆动相位前须与同种子iv逐字段严格相同，实际质量相同；预期0安全终态/32窗口未完成，明确区分终态缺失与窗口未完成。核验真实释放、已发生重载和窗口末待重载，全110秒安全/三足/腾空/vz/接触合力/含初始化饱和及176000腿部几何采样。若通过再做冻结候选全程280秒阶段保留与另一已用种子回归、比较实际完成时间，不能凭短窗口提速就声称64条阶段成功保留。若退化则按失败诊断，不放宽门禁。本地fetch-verified-report.py/PID2270819已等待严格核验与几何状态，随后拉回录像/证据/全报告并独立哈希。

后续继续处理原目标与原起点衔接、效率及最终固定候选的两组未用种子各32且各至少30成功/无缺失，检查原速录像。27302/28302已用，29302尚未运行。保留先四足承重停稳、前脚逐只展开、再最后前移重心；指定GitHub分支只同步证据文档。PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0006"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：iv全程32/32阶段完成且净空通过，iw冻结控制器回归另一已用种子（2026-10-07 07:33）

**先成功率/鲁棒性，再效率。** iv/groundreservefull27302于07:25:41正常完成，07:27:58严格核验通过、07:29:19释放重载审计通过、07:31:11全程腿部几何完成。**seed27302的32/32均四足登台、双前脚逐只展开及严格最终舒展承重；同种子it原32例阶段成功全部保留、丢失0。** 全32前5500个20ms样本与iu逐字段严格相同，无遥测例外；12实际运行源/actor/reset与iu冻结一致，实际PhysX质量缓存同步通过。阶段成功保留不表示修改后的整条轨迹与it完全相同。

**全部448000个20ms实际腿部样本最小净空6.241329mm，低于5mm与负间隙均0。** 原5例中段缺口env2/15/16/28/30全280秒最小分别7.996/7.837/6.775/7.878/6.241mm，后续登台、展开和收尾均完成。整批三足及以上采样100%、腾空0、安全终止0、|vz|峰.090701364m/s、含子步历史单足合力峰147.570633N、含初始化力矩饱和0。640次起摆均满足此前10×20ms≤5N，全部找到后续≥8N/reload1/连续.2秒真实重载；704次承重转换，violations为空。几何审计覆盖原USD腿部原语的20ms实际根/关节轨迹，不覆盖物理子步或非腿部全机碰撞。

**原完整任务仍0/32；32唯一首回合终态、缺失0，全部time_out。** 四足首次台面承重停稳182.78～218.48秒，双前脚展开完成215.84～248.50秒，终态连续稳定12.00～52.16秒。32例距原目标x1.35m仍.34464～.39300m，全部未达到原水平误差<.20m；还需整体前移约.14465～.19702m才到容差边界，边界本身不算通过。见stage-duration-summary.json与original-goal-audit.json。280秒是箱沿阶段全程诊断，约4分钟仍不可接受为最终时长；不是原起点24秒/12秒，也不是最终两组未用种子验收。

iv完整报告3878758588字节，SHA256 `811440e0d085dc37e24179d686e4b3d914866bb67c0a0d5f33f91663fd9c1d34`。小型核验/终态/规划/事件/几何及完整报告已本地归档；07:40:34独立流式SHA256与字节数核验通过，见local-report-verification.json。iu上一轮1514889388字节报告已于06:26:48本地完整下载并独立SHA256通过，补齐此前待归档状态。iv env28原速录像280秒/7000帧/25fps，SHA256 `bf744274126f6d4a3f9b777cb1a8659a723d78feb7dcd820517cec5f9fd5a232`，远端/本地一致；已全解码并审阅40/91.7/110/200/250/279.96秒抽帧，支持中段转移、后脚登台、前脚展开及稳定终态，**不是全片原速验收**。

**当前iw/reservereg28302在既有远端GPU1运行，勿重复启动。** 07:32:12启动，监控PID750566、自动核验PID750568；全程几何等待器PID750898于07:32:32在全部脚本上传完成后启动。seed28302/32、280秒/14000步、全32密集轨迹、主相机env3。6项前置检查通过；12运行源/源包/actor/reset与iv逐字节相同，补丁仍`59f7095c8d97a3b4179c37d19a347bb966f470397b61f6a4afecc3488a62c41a`，仅更换种子、录像环境和输出路径，没有控制或提速改动。启动检查先重新验证iv的阶段保留、全程净空、真实释放重载及完整终态，再检查无其它评估进程；实际启动源/actor/reset已核验。

**08:22运行核对：** iw监控750566、自动核验750568、几何等待750898均正常；最新日志12400/14000步、completed=0、尚无终态结论，不重复启动。已设置本地fetch-verified-report.py/PID2269416等待严格核验通过及几何审计状态，然后拉回小型证据、原速录像和完整报告并独立流式哈希；见transfer-verification-watch.json。该等待器不是新的物理任务，未产生新的成功率结论。

iw完成后：要求全32前4000样本与同seed28302的iq前80秒逐字段严格相同、实际质量相同；以iq原32逐例报告保留/丢失，不跨种子配对iv。检查32唯一终态/缺失、原任务与阶段计数、全物理指标、含初始化饱和、释放重载及全部448000样本几何，重点旧env2/3/24/31中段余量，随后审查原速录像和报告哈希。27302/28302已用于调试，29302尚未使用；不能把本轮叫作最终未用种子验收。

另一已用种子回归通过后，仍须处理原目标位置、既有NAV接近能力与原起点衔接，随后减少冗余等待/重复规划/转移耗时并重新验证成功率；最终固定候选须原起点两组未用种子各32、各至少30成功且无缺失并检查原速录像。继续保留四足先承重停稳、前脚逐只展开、再最后前移重心，以及原真实释放/重载/停稳/关节参考平滑/碰撞/执行器门禁；不重训NAV/PPO。候选源只在外部产物，指定GitHub分支只同步证据文档；PUSH技能、MuJoCo、实机暂停。

<a id="record-0007"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：iu前110秒消除本批5例中段净空不足，iv冻结控制器检验全程（2026-10-07 06:25）

**先成功率/鲁棒性，再效率。** iu/groundreserve27302于05:49:40正常完成、05:52:01严格核验通过、05:53:53全部腿部几何审计完成。全32例在各自首次ground搜索前与it逐字段严格相同；16例未调用该回退者，整个5500步前缀严格相同，无遥测例外。**全部176000个20ms实际腿部采样净空最小6.241329mm，低于5mm及负间隙样本均0**；此前it的5例中段余量缺口在本110秒窗口内消除。此项不覆盖物理子步或全机器人碰撞，尚不代表完整280秒鲁棒性通过。

旧缺口env2/15/16/28/30在110秒全窗口的最小净空分别7.996/7.837/6.775/7.878/6.241mm。它们在约93～94秒真实起摆并于约99秒完成重载，继续下一只后脚；15/16/30在109秒前还完成下一次重载，2/28在110秒窗口末下一摆动待重载。不是以停在转移前来绕过缺口。见old-gap-cases-progress.json、events.json、full-leg-geometry-audit.json。5例后续完整成功路径仍须全程验证。

**本轮仅110秒、回合仍280秒：原完整成功0、四足登台0、终态0、32例预期未完成，不是终态缺失或32成功。** 安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰141.449081N、含初始化力矩饱和0；12源/actor/reset/实际PhysX质量同步核验通过。330次起摆均符合真实卸载门禁，312次已记录承重转换符合原≥8N/reload1/连续.2秒条件；18次窗口末待重载已在release-reload-short-review.json中单列，已发生门禁顺序违例0、终止失败后未重载0。原始audit保留18个no_recorded_reload_for_swing，不能误写成全部摆动都已完成重载。

iu完整报告1514889388字节，SHA256 `78dd3627e5e6fdabc45a76e316e2861ee77ed978b4d960ef965fd8f51f06e06e`。本地完整报告正在下载，独立哈希核验器PID2267036等待完整文件，未完成前不能声称本地全量归档；见transfer-verification-watch.json/verify-local-transfer.py。 env28原速录像110秒/2750帧/25fps，SHA256 `1372f4b1348936dae7cc90eeb44b8883872835bcf7a5fde2aab7eb75a8b17c61`，本地/远端一致；全解码并审阅40/90/91.7/95/100/109.96秒抽帧，支持中段身体转移及后续后脚推进，不是全片原速验收。it上一轮3878743430字节报告已于05:34:27本地完整下载并独立SHA256通过，补齐此前待归档状态。

**当前iv/groundreservefull27302在原远端GPU1运行，勿重复启动。** 06:23:24启动，监控PID749905、自动核验PID749907；全程几何等待器PID750121于全部脚本到位后启动。seed27302/32、280秒/14000步、全32密集轨迹、相机env28。12运行源/源包/actor/reset与iu逐字节相同，仅扩展窗口并更换输出路径；6项前置检查、源包和启动实际源/actor/reset核验通过，补丁仍`59f7095c8d97a3b4179c37d19a347bb966f470397b61f6a4afecc3488a62c41a`。没有新的控制或提速改动，280秒仍仅诊断。

iv完成后要求全32前5500步与iu逐字段严格相同，再核验32唯一首回合终态/缺失、原任务成功与登台/前脚展开/舒展分开计数、同种子it原32保留/丢失，完整三足/腾空/vz/接触合力/含初始化饱和和真实释放重载。随后全程几何、终态目标距离、完整报告本地哈希和原速视频核验；阶段32/32不能掩盖净空或原目标问题。只有全程保留成功路径且几何通过后，再冻结控制器回归已用seed28302，不能把27302/28302当最终未用种子。29302尚未运行。

最新已完成的全阶段证据仍是it：seed27302登台/展开/舒展32/32，原任务0/32、终态32/缺失0，旧中段5例净空不足；iu虽前110秒改善，iv尚无全程结果。原中心目标x1.35m、水平误差<.20m不变，原目标位置、NAV既有接近能力与原起点衔接、最终效率、冻结候选两组未用种子各32且各≥30成功/无缺失仍未完成。不是24秒慢爬或原起点12秒验收；约4分钟不是可接受最终时长。不重训NAV/PPO，继续保留四足先承重停稳、前脚逐只展开、再最后前移重心及原释放/重载/停稳/碰撞/执行器/参考平滑门禁。候选仅外部产物，指定GitHub分支仅同步证据文档；PUSH技能、MuJoCo、实机暂停。

<a id="record-0008"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：it恢复32/32并精确保留31条路径；iu开始中段净空110秒诊断（2026-10-07 05:25）

**先成功率/鲁棒性，再效率。** it/microclosure27302于04:39:35正常完成、04:43:04严格核验通过、04:44:13释放重载审计通过、04:46:14全程几何审计完成。**seed27302同批32/32登台、双前脚逐只展开及严格最终舒展，ir原31全部保留、恢复29、丢失0。** 其它31例全14000步逐字段严格相同；29号前12754样本严格相同，首次接受收尾微步在255.08秒采样可见，无遥测字段例外。原完整任务仍0/32；32唯一首回合终态、缺失0、全time_out。280秒箱沿诊断不是原起点24秒/12秒或最终候选两组未用种子验收。

29号192.62秒四足登台停稳、223.08秒完成双前脚展开；收尾由原17次拒绝变为1次尝试/1次接受、拒绝0。279.98秒参考剩余从2.049446mm降至1.480162mm，实际剩余1.058936mm，跟踪误差1.362470mm，四足最小承重30.56N、线速度.000282m/s、角速度.001087rad/s、关节指令越限0；首终态连续稳定22.920秒。未放宽2mm参考门槛或.03指令余量门槛。见env29-final-audit.json、verification.json与events.json。

整批三足及以上采样100%、腾空0、安全终止0、|vz|峰.090701364m/s、含子步历史单足合力峰147.576309N、含初始化力矩饱和0。640次起摆均满足此前10×20ms≤5N且找到≥8N/reload1/连续.2秒真实重载，704次承重转换、violations为空；12运行源/actor/reset及实际PhysX质量同步通过。微步只改了符合原closure条件且原规划拒绝后的候选，已有登台与前脚展开顺序完整保留。

**净空问题没有被收尾修复掩盖。** 全32×14000=448000个20ms实际腿部几何样本无负间隙，但与ir相同的5例env2/15/16/28/30仍低于5mm，最小分别4.592/4.948/4.679/4.520/4.911mm；均为约91秒中段支撑转移，16另有约99.5秒一段。不是物理子步或全机碰撞验收。32/32阶段完成不等于鲁棒性通过，5mm门槛不降低，约4分钟仍不是可接受最终时长。

it完整报告3878743430字节，SHA256 `250b6627c2b0febcc9e79c421dbafdc845b3a9d33e165d6623309ca4a0fbad0b`。完整报告本地下载仍在进行（05:25约832MB），独立哈希核验器PID2265853等待完整文件；见transfer-verification-watch.json/verify-local-transfer.py，完成前不能声称已本地全量归档。小型核验/终态/规划/事件/几何与录像文件已本地保存。env29录像280秒/7000帧/25fps，SHA256 `c1984cede8b96fe81c435c663ea0fd9842f49933ca1f8d02aed7052dd412fed4`，远端/本地一致；已全解码并审阅40/100/225/255/260/279.96秒抽帧，支持登台及最终四足稳定姿态，微小参考修正由数值轨迹佐证；不是全片原速验收。

**iu/groundreserve27302已在既有远端GPU1运行，勿重复启动。** 05:24:18启动，监控PID749305、自动核验PID749307；几何等待器PID749502在全部脚本上传完成后启动并核对文件存在。seed27302/32、110秒/5500步、回合仍280秒、全32密集轨迹、相机env28。在已恢复it基础上仅替换expanded_ground_support_pose为先前is准备的整段10mm净空偏好，保留it微步和全部原身体/腿部路径、负载/COM、FK、关节/执行器、真实释放/重载、停稳及参考平滑门禁；严格偏好无解时保留原可行解。is旧目录仍是未启动的历史候选，不覆盖其启动前拒绝记录。

iu全部16份it真实ground输入纯CPU检查通过，12份改选、4份原结果保持；另16例此前未调用该回退。每份都通过“不可满足余量时精确回退原结果”及“偏好结果等于全部原门禁下10mm严格搜索”的核验。5个旧缺口env2/15/16/28/30均有更严格可行解，整段名义最小净空分别10.132/12.576/12.348/10.042/12.421mm；这只是数学可行性，不能冒充实际跟踪净空。6项前置检查、源包12源哈希与启动实际源/actor/reset核验通过。补丁SHA256 `59f7095c8d97a3b4179c37d19a347bb966f470397b61f6a4afecc3488a62c41a`，其它11运行源、actor、reset不变，没有提速改动。

iu完成后先核对每例首次ground搜索之前与it逐字段严格相同；未调用搜索的环境须整个110秒前缀相同。若无安全终态，应记0终态/32预期未完成，而非32成功或终态缺失；区分窗口末待重载摆动与真实门禁违例，随后检查全部176000样本实际腿部净空，重点旧两次转移。自动几何等待器只在严格核验和短窗口释放重载分类无已发生违例时运行。110秒通过后仍需冻结控制器做280秒阶段全程成功路径回归与seed28302回归，不能跳过后续路径和另一种子的验证。

原中心目标x1.35m、水平误差<.20m不变。it32终态距目标.3460～.3933m，均未进入原容差，仍需整体前移约.1461～.1976m才到边界。已有登台不等于达到原目标；原目标、NAV既有接近能力的原起点衔接、完成效率及冻结候选两组未用种子各32且各≥30/无缺失仍未完成。seed27302/28302已用于调试，29302尚未启动。不重训NAV/PPO；候选仅外部产物，指定GitHub分支仅证据文档；PUSH技能、MuJoCo、实机暂停。

<a id="record-0009"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ir旧种子31/32严格阶段完成，定位收尾回退；it仅修复受限小步（2026-10-07 03:38）

**先成功率/鲁棒性，再效率。** ir/preunloadreg27302于03:27:24正常完成，03:30:52严格核验结束，03:32:01释放重载审计通过，03:34:01全程腿部几何审计完成。冻结iq控制器回归旧seed27302：**32/32登台并双前脚展开，但严格最终舒展31/32（96.875%），相对旧ik32丢失env29**；不是32条原路径全部保留。所有环境在首次提前角速度衰减前与ik逐字段严格相同，实际PhysX质量与同种子ik相同。iq新seed28302仍32/32，但两批均已用于调试，不能作为最终两组未用种子验收。完整原任务仍0/32，32唯一首回合终态、缺失0、全time_out。

ir安全终止0、三足及以上采样100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰147.576309N、含初始化力矩饱和0。640次实际起摆均满足此前10×20ms≤5N并找到≥8N/reload1/连续.2秒重载，704次承重转换、violations为空。12实际运行源/actor/reset及实际质量缓存同步核验通过。全程448000个20ms腿部几何样本负间隙0，但5例中段转移不足5mm：env2/15/16/28/30最小分别4.592/4.948/4.679/4.520/4.911mm，集中90.86～92.06秒，16另在99.48～99.60秒；仍不满足几何余量要求。不是物理子步或全机碰撞验收，不降低5mm门槛。

**29号是上台后收尾规划受限，不是跌落或未登台。** 279.98秒已双前脚展开、连续满足最终ready约34.90秒、四足最小承重30.17N，速度.000196m/s，关节指令越限0。实际根位置距阶段高度目标剩1.705mm，参考高度仍差2.049446mm，超过既有2mm参考门槛；不能因仅多49微米就改判通过。255.06秒起17次原收尾规划均拒绝。第一次拒绝的原1/1、1/2、1/4步全路径综合余量分别.022517/.027310/.029700，均低于原.03关节指令余量门槛；负载/FK/身体/腿部间隙合格。保留失败记录，见env29-final-audit.json、final29-planning-audit.json。

原始失败输入纯CPU复现表明：仅把受限收尾的候选步长继续细分为1/8、1/16、1/32，**17份都可找到保留所有原门禁的可行解**，实际候选上移约.211～.213mm，参考剩余降至约1.480～1.493mm。最小综合余量约.030836，仍满足.03；未降低关节/执行器、负载、几何、释放重载、停稳或2mm完成门槛。微步不是最终效率优化，只为恢复原成功路径；约4分钟和280秒窗口仍不可作为最终时长。

**it/microclosure27302已在既有远端GPU1运行，勿重复启动。** 03:36:41启动，监控PID748685、自动核验PID748687；后续全程几何审计等待器PID749196已设置，只有严格核验及释放重载成功才执行纯CPU几何审计；seed27302/32、280秒/14000步、全32密集轨迹、录像env29。只在原先已满足四足承重、双前脚完成、连续10秒稳定等closure条件且原规划被拒绝时增加更小的候选，所有原可行结果保留；另11运行源/actor/reset及初始角速度修正不变。421份来自iq/ir的已记录规划在默认候选下新旧CPU结果逐字段相同，17份失败收尾均找到完整检查通过的微步；6项前置检查、源码压缩包一致性和实际启动源/actor/reset核验通过。补丁SHA256 `db7665eb9feddbb949a46d6ff009cefa31bb3b8206f28641fe57bd2c80a74455`。

**04:22运行核对：** it仍在原远端运行，日志11400/14000步、completed=0；监控748685、自动核验748687正常，无完整终态结论，不重复启动。发现后续几何等待器749196曾早于文件上传完成而退出（缺audit-after.py），物理评估未受影响；已保留初次错误日志及watch，核对脚本和模型文件到位后重启为PID749241，确认进程正常等待。只有严格核验与释放重载通过后才运行几何审计。见geometry-watch.json、geometry-watch-initial.json、audit-after-initial-failure.log、audit-after-retry.log。

it完成后要求：**ir其余31例全14000步逐字段严格相同，29号首次实际接受closure之前逐字段严格相同**，无遥测例外；分别记录原31保留/丢失、新增29和原完整任务成功、终态缺失、全物理指标及初始化饱和、释放重载，再审计全程几何和原速视频。只有CPU可行性，尚没有it物理恢复结论；既有中段净空缺口也没有因该收尾修复而消除。录像及训练/物理评估仍只在远端。

**净空候选is已准备但未启动，不要误报成仿真失败或在运行。** is/groundreserve28302原计划110秒中段诊断，只有expanded_ground_support_pose内整段10mm偏好，其它门禁保持、无更严格可行解则精确保留原结果。全部15份iq实际ground输入检查通过，11份选中更大净空姿态、4份原结果不变；其余17环境未调用该回退。4份已知缺口均可选整段名义10mm以上。03:34:06启动前保留路径检查因ir丢失29而退出1，launch-gate-status.json保留，无launch-record、无物理进程。当前先单独验证it收尾恢复，再把准备好的净空偏好合并到已恢复基线上做110秒/全程回归，不复用is路径覆盖旧证据。

ir完整报告3878798555字节，SHA256 `1f63d4ccdc82f1fba44cdd65dd25d380bd912b4918f908df22c9439a8e6449a1`。03:39:47本地完整下载及独立流式SHA256核验通过，报告已完整归档。 env26原速录像280秒/7000帧/25fps、SHA256 `0213135c822029ebf2e310c356837fbf8c7074ad3696f114cf38200e2a1fe8ef`，远端/本地一致；全解码并审阅40/100/180/225/260/279.96秒抽帧，支持该例登台、展开、终态承重。此片是env26，不能冒充env29失败录像，也不是全片原速验收；it已把主相机设为29。

原中心目标x1.35m及水平误差<.20m判据不变。ir32终态距目标.3460～.3946m，均未入原容差，还需整体前移约.1461～.1978m才到边界，边界本身仍不算通过。原目标与NAV既有接近能力的原起点衔接、完成效率、最终冻结候选两组未用种子各32且各≥30/无缺失仍待完成；不是原起点24秒/12秒验收。29302尚未运行。保留四足先停稳、前脚逐只展开、再最后前移重心的顺序，不重训NAV/PPO，不提速，候选只在外部产物、指定GitHub分支仅同步文档；PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0010"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：iq恢复32/32阶段完成，4例中段净空余量不足；ir回归旧种子（2026-10-07 02:38）

**先成功率/鲁棒性，再效率。** iq/preunloadfull28302于01:28:21正常完成、01:30:09严格核验通过、01:31:17全轨迹释放重载审计结束。同seed28302的旧il为31/32；新iq为**32/32四足登台、双前脚逐只展开及最终舒展承重，原31全部保留、新增26、丢失0**。全32前2000步与ip逐字段严格相同，无遥测例外。**原完整任务仍0/32**；32唯一首回合终态、缺失0、全部time_out。这里是280秒箱沿阶段诊断，既不是原起点24秒/12秒验收，也不是最终冻结候选两组未用种子验收；约4分钟仍不可接受为最终时长。

全程安全终止0、三足及以上采样占比100%、腾空0、|vz|峰.100830354m/s、含子步历史单足合力峰148.109055N、含初始化力矩饱和0。640次起摆均满足此前10×20ms所选足≤5N，均找到后续≥8N/reload1/连续.2秒真实重载；704次承重转换，审计violations为空。12实际运行源/actor/reset及实际PhysX质量同步通过。未降低释放、重载、停稳、关节参考平滑、碰撞或执行器门禁。

原失败26号首次起摆5.10秒、重载11.86秒；第二前脚15.10→22.14秒，首个后脚26.90→32.54秒，最终后脚214.82→220.90秒；220.92秒首次四足台面承重停稳、253.78秒完成双前脚展开，终态已连续稳定14.220秒。首次卸载前平滑减弱外层角速度几何修正的恢复已贯穿本批全阶段，但不能据此忽略下面的几何余量缺口。

**全448000个20ms采样腿部几何审计：负间隙0，但4/32例（12.5%）低于5mm。** env2最小4.540mm（91.02～91.32及99.32～99.50秒）、env3最小4.289mm（91.32～91.58秒）、env24最小4.539mm（88.92～89.22及97.24～97.40秒）、env31最小4.483mm（90.70～91.02及99.02～99.18秒）。均为中段phase0、unload0支撑转移；阶段完成与余量不足可以同时出现，不能把32/32阶段完成写成鲁棒性通过，也不降低5mm门槛。该审计覆盖实际根位姿/关节重建的原USD腿部原语，不覆盖物理子步或全机碰撞。

原远端系统Python的初次纯数学审计因缺pxr失败，原失败日志保留，未安装依赖、未启动新仿真。随后将原USD解析出的模型/碰撞原语按原dtype精确导出，远端核对USD及两份数学源哈希，用既有Isaac Python仅执行torch CPU几何计算，完整审计成功。见geometry-numeric-model.json、audit-full-leg-geometry-portable.py、full-leg-geometry-audit.json及两份审计日志。

已归档transfer-gap-context.json/transfer-gap-summary.json。**这4例第一次缺口对应的已接受ground搜索真实输入均已保存**：env2/3/24/31的planning-inputs.json→climb_ground_pose_inputs首项分别为90.160/90.540/88.060/89.840秒；下一20ms采样发生capture。相应名义整段腿部净空约5.305/6.126/5.359/5.316mm，实际跟踪时余量被消耗。旧10mm偏好只作用于标准规划的末端，后续expanded_ground_support_pose回退搜索仍仅整段5mm；不能仅提高末端偏好便宣称已修复。下一步先用记录输入复现原搜索，再探索保留全部身体/腿部路径、摆动、FK、关节、负载/力矩/COM门禁的整段额外余量偏好；若无更优可行解保留原可行路径。第二次转移缺口仍需后续物理重验，不另开重复采集任务。

**02:38纯CPU规划复现/余量探查完成。** 4例均复现相同原选中位置及可行性；CPU与原GPU四元数最大差2.98e-8、margin最大差1.35e-7，明确不是逐字段完全相同。仅在独立数学探查中将expanded_ground_support_pose整段腿部路径门槛5mm收紧至7/8/10mm，其它原身体/关节/FK/COM/摆动/负载门禁保持，4例在10mm偏好下仍有可行解，名义最小净空分别12.152/10.814/11.945/11.997mm。这不是控制器修复或物理验证，未修改ir运行源；后续可据此实现有回退的余量偏好，先扩大真实输入检查，再在ir完成后验证实际跟踪及成功路径。见reproduce-ground-fixtures.py、ground-fixture-reproduction.json、probe-ground-path-reserve.py及ground-path-reserve-probe.json。ir当前日志2800/14000步、completed=0，仍在运行。

完整报告3878351654字节、SHA256 `c73fa473c84b00daa1791bb0e6f7a65cb5cfa788512afb5cf80ea6c3d3267c24`，**02:34:51本地完整下载并独立流式哈希核验通过**，不再有待下载报告。env26原速录像280秒/7000帧/25fps，SHA256 `62fec7f43e6d9e09452fb9b74c3d24243daf64741e4c5033a704d975e15816d2`，远端/本地一致；已全解码并审阅40/100/200/225/255/279.96秒抽帧，支持后脚登台、前脚展开和终态停稳，**不是全片原速验收**。见video-verification.json、env26-keyframes.jpg。

原目标判据按实际源匹配box_climb.py复核，箱体起点x=.75、长1.2，原中心目标x=1.35m、水平距离须<.20m。32终态距目标.35289～.39393m，全部未进目标容差；保持当前横向位置，尚需整体前移约.153～.197m才到边界，边界本身仍不算通过。上台已实现，原目标位置、NAV既有能力与原起点接近衔接仍未实现/验证；不改原判据、不重训NAV。见original-goal-audit.json。

**当前ir/preunloadreg27302在原远端GPU1运行，勿重复启动。** 02:24:14启动，监控PID747934、自动核验PID747936；02:34核对两进程仍在运行。12运行源/源包/actor/reset与iq逐字节相同，仅改为旧seed27302和新输出目录，280秒/32例/全32密集轨迹/录像env26；6项前置核验及实际运行源启动核验通过。补丁仍`794727da0269b62f8e176ebd95acc929164b0d37cd8709ff9e5861a201d22241`。不与不同种子iq逐例配对；ir必须与同seed27302的旧ik在各例首次front_angular_scale<1之前逐字段严格相同，再报告ik原32的保留/丢失/新增。等待完整终态、质量同步、全释放重载、几何和录像核验，目前没有ir完成结论。

先修复已知中段余量并保留成功路径，再处理原目标与原起点、效率；不因单批32/32提前提速。28302/27302均已用，29302尚未启动，不能充作两组未用种子验收。候选只保存在外部产物，指定GitHub分支仅同步证据文档；PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0011"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ip全32通过40秒前缀及5mm净空，iq冻结控制器检查280秒全程（2026-10-07 00:26）

**先成功率/鲁棒性，再效率。** ip/preunloadprefix28302于00:02:17正常完成、00:02:35严格核验通过、00:02:44释放重载审计完成。全32每例前600步与io逐字段严格相同，无遥测例外。40秒内32例各完成双前脚及一只后脚的真实重载，并已启动下一只后脚；**原失败26号5.10秒首次起摆、11.86秒重载，第二前脚15.10→22.14秒、首个后脚26.90→32.54秒，38.82秒下一后脚起摆，40秒末phase约.295**，没有重现旧6.12秒姿态保护。此时仅两只前脚上台，四足登台0；完整成功0、终态0、32预期未完成，不是终态缺失，也不是32完整成功或原起点24秒/12秒验收。

短窗口安全终止0、三足及以上100%、腾空0、|vz|峰.100830354m/s、含子步历史单足合力峰141.668396N、含初始化单关节累计力矩饱和0；12实际源/actor/reset及实际PhysX质量同步通过。128次起摆均满足此前10×20ms所选足≤5N；96次已发生承重转换（每例3次）符合原≥8N/reload1/连续.2秒条件。每例第4次摆动共32次在40秒窗口末尚待重载；原始audit的no_recorded_reload_for_swing已在release-reload-short-review.json单列为窗口未完成，不冒充全部重载完成。未发现已发生门禁顺序违例。

全部32×2000=64000个20ms样本，按实际关节与根位姿、原USD腿部碰撞原语重建，最小腿部台面净空6.241mm，无低于5mm、无负间隙。26号最小8.633mm（18.80秒第二前脚摆动，FR_calf）。这是前40秒的腿部采样几何审计，不覆盖物理子步、非腿部或约90秒中段支撑转移；**此前il/ik中段5mm余量不足仍未证明消除**。不能用这次前缀通过宣称已完整保留原31条阶段成功路径。

ip报告549420224字节、SHA256 `eaf885f7cfde160b5f7a1cd230fc1e98e7cd6e2ec5f30ea1a354e63633dacb9e`，已本地完整下载并独立流式哈希核验。原速env26录像40秒/1000帧/25fps，SHA256 `9fff4f836a9909a6258ec4afad270b6f58402f0b643df025bab171bc19558bd5`，远端/本地一致；全解码并审阅5.12/12/18/25/33/39.96秒抽帧，支持前脚真实落地与后脚继续推进，不是全片原速验收。见ip/verification.json、release-reload-short-review.json、full-leg-geometry-audit.json及video-verification.json。

**当前iq/preunloadfull28302在既有远端GPU1运行，勿重复启动。** 2026-10-07T00:25:49启动，监控PID747373、自动核验PID747375。12运行源/源压缩包/actor/reset与ip逐字节相同，只把评估窗口40→280秒（2000→14000步），回合仍280秒；同seed28302/32、全32密集轨迹、主录像env26。6项前置检查与实际运行源/actor/reset检查通过，补丁仍`794727da0269b62f8e176ebd95acc929164b0d37cd8709ff9e5861a201d22241`。没有新的控制或提速改动；约4分钟不是可接受最终时长，280秒仅全程失败诊断，候选仅外部产物、指定GitHub分支仅同步文档。

iq完成后首先核验32唯一首回合终态/缺失、完整任务成功与四足登台/双前脚展开/舒展稳定阶段计数、安全终止/三足/腾空/vz/合力/含初始化饱和及真实释放重载。全32前2000步必须与ip逐字段严格相同，无遥测例外；与同seed28302的il按阶段完成逐例列原31保留/丢失/新增26，不能因前缀恢复就提前算32/32。全程实际腿部几何仍需检查，尤其旧中段支撑转移净空缺口。随后还需旧seed27302成功路径回归；28302已用于调试，不能当作最终固定候选未用种子，29302尚未使用。

最新已完成的**完整阶段批次仍是旧控制器il的31/32、新控制器iq尚无全程结论**；原完整任务仍0/32，原目标中心x1.35m及水平误差<.20m等原判据不改，NAV已有能力的原起点接近衔接也尚未完成。坚持四足承重停稳后前脚逐只展开、再最后前移重心；保留关节PD/参考平滑、原碰撞/执行器/真实释放/重载/停稳门禁，不重训NAV或PPO。待鲁棒性确认后再减冗余等待与转移耗时并重验成功率。PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0012"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：新种子31/32阶段完成；io短测恢复首次起摆，ip验证后续逐脚动作（2026-10-06 23:53）

**先成功率/鲁棒性，再效率，280秒仍仅诊断。** il/freshstage28302于22:33:43完成、22:35:18核验通过、22:36:23释放重载审计完成。冻结ik控制器在新seed28302下，**31/32（96.875%）四足登台、双前脚逐只展开及最终舒展承重；1/32（3.125%）在首次起摆前触发bad_orientation**。原完整任务仍0/32；32唯一终态、缺失0，31 time_out/1姿态保护。旧seed27302为32/32阶段完成；不同种子编号不作配对。原目标位置、NAV原起点衔接、效率以及固定最终候选两组未用种子验收均未解决，29302尚未运行。不是24秒慢爬或原起点12秒验收。

il整批三足及以上采样占比99.9923989%、腾空0、|vz|峰0.291207284m/s、含子步历史单足合力峰184.704834N。含初始化力矩饱和只有env26的joint5，98%阈值下累计0.080秒；不可报成0。620次实际起摆均满足此前10×20ms所选足≤5N并找到后续真实≥8N/reload1/连续.2秒重载，682次承重转换无违例；env26从未起摆，不计作未重载摆动。12实际源/actor/reset、PhysX质量同步通过，32例实际质量均与旧seed不同。报告3759728084字节、SHA256 `4ecec28d79c6b2fc7ec4249745563d5b23bd1e6bcc732af85a6742799a7ac245`，本地完整下载独立流式哈希通过。

**env26失败在6.12秒，尚未登台、更不是上台后展开失败。** 4.08秒角速度首次超过.15rad/s、4.16秒超过.3rad/s；4.08秒四足仍约20.97/68.87/73.57/45.24N，参考年龄2.22秒、正处首次卸载准备。5.16秒首次少于三足≥8N，6.12秒姿态保护。全程phase0、无起摆；既有外层角速度修正减弱只在phase>0触发，此例比例始终1。腿部原USD重建最小台面净空63.78mm，无碰撞接近。两批63条阶段成功路径在首次起摆前、参考年龄≥1.5秒时角速度峰均<.15rad/s（旧批最大.10912，新批其它31最大.10278）。这是控制反馈诊断线索，不能把相关性当作已证明因果。见il/initial-failure-audit.json、initial-angular-screen.json、torque-saturation-audit.json。env26少数未过滤的后脚/失败规划输入来自自动复位后的后续回合，时间175秒以后，禁止用于解释首回合6.12秒失败；首回合无前脚摆动规划输入。

il全部首回合共434306个20ms样本腿部几何重建，负间隙0，但成功例16/24仍瞬时低于5mm，最小分别4.345/4.523mm。16在91.34～91.62秒FR_calf，24在88.72～89.02及97.00～97.16秒FL_calf，均phase0支撑转移；与ik的中段余量不足同类，**不因阶段成功而忽略，不降低5mm门槛**。只覆盖采样腿部几何，不是物理子步或全机器人碰撞验收。il env0录像280秒/7000帧/25fps，SHA256 `5f7dea640b6ff4d2445e78de9bdde2116028fe4c7e4c87179599a375ccd6e9ec`，远端/本地一致，全解码并审阅六处抽帧；不是全片原速验收。

im/initialfailure28302只改相机到env26、运行窗口8秒，回合仍280秒。23:29:46完成，23:31:38严格核验通过：**全32与il对应前缀逐字段完全相同，env26终态逐字段相同**。1终态/31预期未完成，不是完整批次验收。原速失败录像只记录到首终态6.12秒，共153帧/25fps，SHA256 `9cc67082da710351d80c0ba5f7d6f286e0f4a1ddd598a3444140e91acde1343a`，远端/本地一致，已全解码并审阅3.5/4.08/4.6/5.16/5.8/6.08秒帧。报告SHA256 `b3f6ce2f772aab35efbed81724c0779991079238cda850ce52da037608679cf7`，本地哈希通过。

**in晚触发修正已拒绝，不能推广。** 仅初始四足地面承重、第一足phase0、准备年龄≥1.5秒且正在卸载、角速度>.15rad/s时，在.2秒内平滑减弱外层角速度几何修正并锁存；保留关节PD、原释放/重载/碰撞/执行器/停稳门禁。12秒短测23:40:01完成，但env26仍无起摆，4.10秒介入后在5.48秒触发姿态保护，比原6.12秒更早。31其它环境12秒共同轨迹严格一致、26介入前严格一致；核验器在这些比较后因“early terminal persists”退出1，原失败状态保留。整批三足占比99.9197132%、腾空0、|vz|峰.146727711m/s、合力峰156.049805N、含初始化饱和0；冲击指标下降不能掩盖任务失败。报告SHA256 `23e642c884912aa06155c6ceec323f7242e31d27c3e194529ffe7d02b79d4d8c`，本地完整哈希通过。见in/rejection-audit.json。

**io提前干预在12秒短测中恢复env26首次起摆；尚不能推广成全程成功。** io/preunloadangular28302于23:48:03完成、23:49:48严格核验通过、23:49:51释放重载审计结束。仅将in同样.2秒平滑减弱的触发提前到首次四足承重卸载开始，移除角速度>.15条件，保持其它作用域与门禁、无环境编号分支；另11源/actor/reset/关节PD不变。作用域/锁存/源哈希等6项本地检查通过。实际env26在3.40秒开始减弱、5.10秒满足原释放条件后起摆、11.86秒完成真实落地重载，12秒末转到下一只前脚准备；原6.12秒保护在该窗口内未再出现。全32每例干预前所有旧字段严格一致；**因提前干预会改变符合条件的健康路径，不再声称31条全程相同，必须重验原成功路径。**

io仅12秒箱沿诊断、回合仍280秒：完整成功0、终态0、32预期未完成、四足登台0；不是原起点12秒验收。安全终止0、三足及以上100%、腾空0、|vz|峰.100830354m/s、含子步历史单足合力峰112.087158N、含初始化力矩饱和0；12实际源/actor/reset/实际PhysX质量同步通过。32次起摆释放条件通过，27次已发生承重转换符合原门禁；28次起摆已观察到重载，另0/6/21/30共4次窗口末待重载，原始audit将其列no_recorded_reload_for_swing，已在release-reload-short-review.json区分为窗口未完成，不能冒充32次重载完成。in另有5次窗口待重载、无已发生门禁顺序违例，但仍是被拒绝的失败候选。io全部19200个20ms采样腿部重建最小净空9.650mm、无低于5mm；不代表中段90秒支撑转移余量问题已修复。

io报告163631097字节、SHA256 `d2a8b0d2588d32e87a28983b1d77fdb3544a8f9ab73cb3260494d17ff5ffd1ba`，本地独立哈希通过。录像env26为12秒/300帧/25fps、SHA256 `c562b23c904ea355626ddf4c1b3edaaa688043e050318080bbc8cd7fd7b227dc`，远端本地一致，已全解码并抽帧4/5.16/8/10/11.84/11.96秒审阅；非全片原速验收。补丁SHA256 `794727da0269b62f8e176ebd95acc929164b0d37cd8709ff9e5861a201d22241`。

**当前ip/preunloadprefix28302在原远端GPU1运行，勿重复启动。** 23:52:05启动，监控746805、自动核验746807。与io的12运行源/源包/actor/reset完全相同，只把评估窗口扩到40秒2000步、回合仍280秒，同seed28302/32、全32密集轨迹、相机env26；6项前置证据核验和实际来源检查通过。没有新的控制或提速改动，候选仍仅在外部产物。自动核验要求全32前600步与io逐字段严格相同、无遥测例外，并核验全部物理质量与真实释放重载；40秒若无终止，必须记32预期未完成，而非32次成功。当前没有ip完成结论。

后续先读取ip进程/status/verification及释放重载结果，检查新26后续前脚/后脚推进与原31条阶段路径有无回退；全32重建早期腿部几何，确认后再决定280秒全程回归。原seed27302的成功路径也需要新控制器回归；28302现已参与调试，不可再当最终冻结候选的“未用种子”，29302尚未使用。完整路径鲁棒性、已知中段5mm余量缺口及原目标/原起点都未解决，先不提速。

保留既有登台与前脚先展开再前移重心的顺序，不重训NAV/PPO，不提速。原目标中心x1.35、水平误差<.20m等原判据不变；待鲁棒性确认后再推进目标/原起点与效率。候选仅外部产物，指定GitHub分支只同步文档；PUSH技能、MuJoCo、实机暂停。

<a id="record-0013"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ik全程保留32/32阶段路径，il冻结控制器检查未用种子（2026-10-06 21:31）

**先成功率/鲁棒性，再效率。** ik/frontcompletefull27302于20:27:41正常完成、20:29:54严格核验通过、20:31:04全轨迹释放重载审计完成。**同seed27302、280秒箱沿阶段32/32四足登台、双前脚逐只展开及最终舒展承重，ii32/id28/hy20路径全部保留**；全32前2000步与ij逐字段严格相同，无遥测例外。原完整任务0/32，32唯一终态、缺失0，全部time_out；原起点24秒/12秒和最终候选两组未用种子各32均未验收，280秒仍仅诊断，约4分钟不可作为最终效率。

全程安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰148.284760N、含初始化力矩饱和0。640次起摆均满足此前10×20ms采样所选足≤5N，均找到后续≥8N/reload1/连续.2秒真实重载；704次承重转换无违例。12实际源/actor/reset、实际PhysX质量同步通过。完整报告3879155453字节，SHA256 `a578961ce40be7a4b31125efd14dca88f94098a8baad89af0579cf014fc41fbd`，已本地完整下载独立流式哈希核验。

全部32环境、共448000个20ms样本的实际关节/根位姿按原USD腿部原语重建，最小间隙4.464mm，负间隙样本0。 低于5mm的环境为['2', '7', '24', '28']，各例最小值(mm)为{'2': 4.61, '7': 4.562, '24': 4.906, '28': 4.464}。这些全程余量缺口必须单独定位，不能因阶段32/32宣称整段几何鲁棒性通过；本轮新种子仍用于收集同一冻结控制器的失败分布，不推广候选。 缺口集中在90.78～91.92秒的phase0四足承重转移，7号另有99.20～99.36秒一段；所选足尚未卸载（unload0），不是已修复的早期第二前脚摆动。已保存最近capture至缺口后的真实轨迹及规划净空于transfer-gap-context.json/transfer-gap-summary.json，后续不得降低5mm门槛。 见`full-leg-geometry-audit.json`；该项纯CPU只读重建，不是本地物理仿真。此前已验证的第二前脚早期摆动32例最小6.421mm由严格相同前2000步继承，仍只代表该次摆动。

主录像env10为280秒/7000帧/25fps，SHA256 `f00812b6e5715f2cfb78eaee750e8af9d903a5b944927bcd5141623db07716df`；全解码并抽帧40/100/170/210/250/279.96秒审阅，支持后脚登台、前脚展开及终态舒展。不是全片原速验收。完整报告、原始终态、核验、质量、释放重载、几何和录像证据已归档。

**原完整任务0/32的确定原因之一是仍未进入原目标位置容差，不能等同于没登台。** 已按与实际运行哈希相同的`box_climb.py`复核：箱体起点x=.75m、长度1.2m，原中心目标x=1.35m，原水平误差要求<.20m并满足其它支撑/姿态/速度条件连续1秒。32终态距中心约.346～.392m，单此一条全部失败；即使保持当前横向位置，至少还需整体前移约.146～.197m才到容差边界，边界本身仍不算通过。原判据不改。见`original-goal-audit.json`；剩余工作还包括达到原目标、NAV已有能力与原起点衔接、缩短时长及最终独立验收，不能仅改标签或停稳等待来补齐。

新外部阶段检查`climb-stage-fresh-seed-20261006-il/freshstage28302`于2026-10-06T21:30:43.127003在原远端GPU1启动，监控PID744592、自动核验PID744594。本地及远端`*/jobs.json`检查未发现种子28302/29302既往使用，本次只运行28302/32；29302仅检查、尚未启动。**12运行源/源压缩包/actor/复位库与ik逐字节相同，控制器和速度冻结；仍280秒箱沿复位、全32密集轨迹，主录像env0。** 源/actor/reset启动核验通过，补丁仍`fe0aaff8c1730ce285331d320a3206f625bc813608411088ae48d8b0646c0f56`。新种子仅检验阶段对随机化变化的鲁棒性，不是用户要求的原起点两组验收；不同种子的环境编号不是配对轨迹，不报告逐env“保留/丢失”。候选只放外部产物，指定GitHub分支只同步文档。

**运行中更新（21:40）：** il日志已到2000/14000步，`completed=1, successes=0`，即出现1个早期非成功终态；此时其余环境仍运行，尚无完整报告可判具体原因。不能将原seed27302的32/32推广为跨种子鲁棒性，也不能把未完成的31例算成功或终态缺失。保留该批运行收集完整失败分布，不提速、不重复启动。

**当前等待il，不启动重复任务。** 先查进程/status/verification.log；完成后核验32唯一终态/缺失、完整任务与阶段登台/展开/舒展计数、安全终止、三足/腾空/vz/合力/含初始化饱和、真实释放重载及12源/actor/reset/实际质量。核验器记录与ik的实际质量样本变化、阶段时序和失败轨迹，不能跨种子要求逐字段相同或把一批32/32当成最终鲁棒性确认。查看新失败分布和全程几何后再决定继续第二个未用种子或先修复共性问题；原目标与NAV接近衔接也必须推进。保留原落脚/重载/停稳和碰撞/执行器/平滑门禁，无NAV/PPO重训；PUSH技能、MuJoCo、实机暂停。

<a id="record-0014"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ij消除本批早期前脚5mm净空不足，ik保持控制器复核全程（2026-10-06 19:26）

**先鲁棒性、后效率。** ij/frontcomplete27302于18:44:34正常完成，18:46:16严格共同前缀核验通过，**无遥测例外**。这仅40秒/2000步前缀、回合仍280秒：完整成功0、已终态0、32例预期未完成、四足登台0，不能写成全任务或阶段32/32。最新完整阶段证据仍为ii同seed27302、280秒箱沿诊断32/32登台/展开/舒展停稳，原完整任务0/32、终态32/缺失0；原起点24秒/12秒及固定候选两组未用种子各32均未验收，约4分钟仍不可作为最终时长。

**此前5/10/13/19/23在第二只前脚摆动中不足5mm的问题，在ij实测重建窗口内已消除。** 使用实际关节、机身姿态与原USD碰撞原语重建该次摆动及落地换腿附近几何，5例最小净空分别8.602/8.371/7.619/9.033/8.663mm，原为4.985/4.628/4.937/4.828/4.970mm。全部32该窗口最小6.421mm（env14），没有低于5mm；这是特定早期摆动的检查，不代表整280秒全部几何已验收。18例新准备之前的所有旧字段严格一致，另14例整个40秒轨迹严格一致；没有重现旧0/6/17/18早期停滞，原29号40秒末仍在卸载准备，属于未改轨迹，不能单凭窗口末phase0判失败。见`front-landing-clearance-audit.json`与`verification.json`。

短窗口安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰141.466095N、含初始化力矩饱和0。12实际运行源/actor/reset与实际PhysX质量同步通过。完整报告549596526字节，SHA256 `750d91c5f9ff13983b65342b95ed6da94d71634eab316285fb484d4cc90468d6`，本地独立流式哈希核验通过；不能把这组40秒质量指标当作280秒改善。

自动释放重载审计最初因继承旧本地绝对路径而FileNotFoundError退出1，未运行物理审计；失败脚本/日志/状态保留。已仅将路径改为`Path(__file__).resolve().parent`，以`release-reload-audit-fixed.py`独立补跑并通过，原失败状态未覆盖。127次起摆均满足之前10×20ms所选足≤5N；96次已发生承重转换满足原≥8N/reload1/连续.2秒要求，无顺序违例；31次窗口末摆动尚未观察到重载，明确记为待完成。修复仅涉及分析脚本，不改变控制源。主录像env10原速40秒/1000帧/25fps，SHA256 `db731be25a9eadb33eb6fb3cabe85f219ca1aaa3da7f8617e3e448fe724bd29a`，本地/远端一致；全解码及1/10/15/20/30/39.96秒抽帧审阅可见前脚落地和后脚继续推进，未冒充全片原速或完整任务验收。

确认远端无重复物理任务后，`climb-front-complete-reserve-full-20261006-ik/frontcompletefull27302`于2026-10-06T19:25:40.484252在GPU1启动，监控PID744017、自动核验PID744019。**12份运行源、actor、reset和源压缩包与ij完全相同**；只延长评估步数2000→14000（280秒）并更换产物路径，仍seed27302/32环境、全32密集轨迹、录像env10。继承ij补丁SHA256 `fe0aaff8c1730ce285331d320a3206f625bc813608411088ae48d8b0646c0f56`，来源与短窗口前置检查通过；没有新的控制/速度改动。未验证候选只放外部产物，指定GitHub分支仅同步文档。

**当前等待ik，不重复启动。** 完成后先核验32唯一完整终态/缺失、原完整成功与登台/双前脚展开/最终舒展、安全终止、三足/腾空/vz/合力/含初始化饱和；全32前2000步必须与ij逐字段严格一致，无遥测例外。逐例报告ii32/id28/hy20保留与丢失，自动做全轨迹真实释放/重载审计；下载报告独立哈希并检查原速录像，特别关注18条改变的后续路径和最后后脚/展开/最终调整。只有全程结果支持保留原成功路径，才继续独立种子鲁棒性检查与效率优化；不能用短窗口净空通过代替全程成功。保持原落脚/重新承重/停稳、关节平滑、碰撞和执行器门禁；无NAV/PPO训练，PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0015"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ii同种子阶段32/32，ij补足旧前脚方案净空后先做40秒诊断（2026-10-06 18:35）

**先鲁棒性、后效率。** ii/rearheight27302于17:34:18正常结束：同seed27302、280秒箱沿阶段**32/32完成四足登台、双前脚逐只展开及最终舒展稳定承重**，原ig31/id28/hy20路径全部保留，新增0号。原完整任务仍0/32，32唯一终态、缺失0，全部time_out。全批安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰148.388260N、含初始化单环境/关节力矩饱和0，质量指标与ig逐值相同。280秒仅阶段诊断；约4分钟仍太慢，原起点24秒/12秒及固定候选两组未用种子各32均未验收，不能把本批写成最终100%成功率。

**原严格核验失败记录完整保留，另作精确限定复核。** 首次严格核验17:37:21退出1；完整差异审计只发现未改动env3第10035～10110步76采样、env28第9883～9963步81采样的`guidance_swing_path_margin`不同，差值均2.9802322387695312e-08rad；两侧分别约.261713/.304242rad、ready均true。AST与全部12运行源检索证实该缓存控制侧仅5处写入、仅报告收集器读取，实际门禁使用局部当前sm。`verify-telemetry-reviewed.py`仅允许这两组确切环境/时段/字段/数值，共157条，复核通过；所有物理量、动作参考、门禁和其它字段仍严格相同。未覆盖原verify.py/verification-status.json，也没有把原严格核验标成通过。10例首次高度修正前的共同前缀严格一致，其余22例除上述只读缓存外全轨迹及终态一致。见`comparison-audit.json`、`telemetry-source-audit.json`和独立`verification-reviewed.json`。

0号179.28秒仅增加原采纳姿态的3mm名义高度余量；182.50秒最后RR起摆时实测前部高度242.485mm，超过原240mm要求；188.54秒真实重载完成、188.56秒进入四足登台停稳，218.70秒双前脚展开完成，239.20秒起连续40.80秒满足阶段舒展条件。全32共636次起摆均逐次满足此前10×20ms采样所选足≤5N，均找到后续≥8N/reload1/连续.2秒重载；700次承重转换无违例。12实际源/actor/reset、实际PhysX质量同步通过。完整报告3878771587字节，SHA256 `b0a8a9cb7821f7dcefc99a318bf34044e2401ace32a6fded51caab44c9105f81`，已本地完整下载独立流式哈希核验。

主录像env0为280秒/7000帧/25fps，SHA256 `85b2a592b53b8fd9cbbcbb35809a5a39a35ba7c2779bec542078029385a2dbd4`，本地/远端一致。全解码及173.2/182.4/195/210/250/279.96秒抽帧审阅显示最后后脚恢复、展开与最终姿态；不是全片原速验收。`env0-recovery-audit.json`保存恢复时序。原5/10/13/19/23早期第二前脚瞬时不足5mm仍未消除，不能因为32例阶段完成就宣称几何鲁棒性已合格。

针对该剩余问题，先对真实捕获输入检查原姿态附近±1～6mm纯竖直微调，不能给全部低余量方案提供满足全部约束的8mm解，探针仅归档、未物理运行。随后外部候选ij**仅在原前脚规划完成后，对名义摆腿净空不足8mm的方案复用已有全约束扩展搜索**；无解仍保留原结果。原已有8mm的方案逐值不变，最后后脚高度修正及最终补齐保留。没有改足端落点、摆腿速度、真实≤5N连续.2秒释放、落地重载、质量同步、关节平滑、PD或原安全/停稳条件；这是四脚接触时的抬脚准备，不是旧上台前前移参数对比。

ij本地8组检查通过：移除新增block后原控制源码逐字节相同、其它11运行源完全不变；全部32真实输入复现原方案、输入张量无原地改变；新方案逐项复核身体10mm/腿5mm完整支撑路径、摆腿8mm/关节.03rad/FK、75%努力、三足裕度25mm、全四足路径≥8N与残差<.1及原80mm/.35rad位姿边界；零努力无解偏好不改原姿态。18份输入改变 `[1,2,3,4,5,9,10,11,12,13,14,19,20,22,23,25,28,31]`，其余14份输出逐值不变。已知5/10/13/19/23的新名义摆腿净空分别8.527/8.496/8.355/9.264/8.559mm；这仅数学证据，不能当作实测净空或物理成功。

确认既有远端无重复物理作业后，`climb-front-complete-reserve-20261006-ij/frontcomplete27302`于2026-10-06T18:34:35.220752在GPU1启动，监控PID743454、自动核验PID743456。**仅40秒/2000步前缀，回合仍280秒**，seed27302/32环境、全32密集轨迹、主录像env10，12实际源/actor/reset核验通过。补丁SHA256 `fe0aaff8c1730ce285331d320a3206f625bc813608411088ae48d8b0646c0f56`。未验证候选只存外部产物，指定GitHub分支仅同步文档。

**当前等待ij，先查远端进程/status/verification.log，不重复启动。** 先核验完整成功/终态与32例预期未完成、安全终止、三足/腾空/vz/合力/含初始化饱和；与ii按首次前脚输入结果改变时刻比较全部旧字段，未改变者前40秒全轨迹严格相同，**本轮不允许任何遥测例外**。随后审计实际关节重建的前脚摆动净空、真实释放/落地重载及5例和原14不改路径，确认无早期退步才考虑280秒全程。自动核验后有释放重载审计，`front-landing-clearance-audit.py`供本地只读几何重建；40秒末待重载/未终态必须单列，不能冒充完整成功。鲁棒性确认后再减少冗余等待和重复规划耗时并重验成功率。无NAV/PPO训练；PUSH技能、MuJoCo、实机继续暂停。

<a id="record-0016"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ih补录与原轨迹严格一致；ii验证最后后脚卸载前的3mm名义高度余量（2026-10-06 16:32）

**先成功率、后效率；约4分钟仍不可作为最终速度。** 已确认完整阶段基线仍为ig：同seed27302、280秒箱沿阶段31/32四足登台、双前脚展开并舒展承重，id28/hy20既有路径全部保留；原完整任务0/32、32唯一终态、缺失0。固定候选两组未用种子各32及原起点24秒/12秒验收均未开始。新候选还未产生完成率，不能将数学检查或正在运行的评估当作32/32。

ih/rearplancapture27302于15:23:05正常结束，15:25:39自动核验通过，15:26:34释放重载审计完成。**全部32环境、每例11000步与ig前220秒逐字段严格相同，无遥测例外。** 已拿到32环境共241份最后后脚已采纳/拒绝规划输入，含0号179.259995秒的真实重力/质量/COM/接触/受载偏置/软限制/摆腿路径及已采纳姿态。12实际源/actor/reset与实际PhysX质量同步通过。完整报告3035836385字节，SHA256 `0643b46aa721d256d8cd97f03393d2925a7e9ac936dff8d93248dba338b65a13`，已本地完整下载独立哈希核验。

ih仅220秒前缀、回合仍280秒：完整成功0、已终态0、32例预期未完成，31例截至窗口曾四足登台；不是32完整终态或新的280秒完成率。安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰148.388260N、含初始化力矩饱和0。615次已起摆满足之前10个20ms采样≤5N，657次已发生重载转换符合原条件；10次末尾摆动仍未观察到重载，单列待完成，未发现已发生顺序违例。原速录像env0 SHA256 `ad32118367785cede5b0814ad7ac5ebdb94643541e4fe934cc0bf9fef5009268`，全解码5500帧/25fps/220秒，抽帧40/173.2/179.28/182.4/190/219.96秒确认最后后脚准备后停住；非全片原速验收。

真实输入复核：0号原采纳名义前髋至足高度240.758mm，原记录的起点244.331mm，最后计划卸载后实测降到239.117mm并触发原240mm起摆门禁。直接在原常规离散搜索中要求243mm并叠加完整支撑载荷检查，10份低余量/完整三足规划均未找到候选，探针已归档、没有物理运行。于是保留已找到可行姿态的水平位置和四元数，只检查它周围0～6mm、每1mm一档的竖直抬升，选择满足名义目标+3mm的最小档，避免重新选择整个姿态。

新外部候选ii仅在**最后后脚、phase0、非platform_hold、四足实测均≥8N、原计划已可行且预测三足裕度≥25mm、名义前部高度不足原目标+3mm**时尝试偏好修正。原240mm实测起摆要求、≤5N连续.2秒释放、真实落脚/重载/停稳、质量同步、关节参考平滑、PD和所有原安全门禁不变。每个微调从当前实测起点重新检查原完整支撑路径（身体10mm/腿5mm、路径关节余量及FK）、受载/努力75%与关节.03rad余量、完整摆腿41点及原净空/关节要求、原80mm位置与.35rad姿态边界，并额外检查四足支撑路径各足预测≥8N/合力残差<.1。任何无解偏好保留原可行结果，不让部分支撑转移冒充完整三足姿态。

8项本地源码/实际输入数学检查通过：移除新增调用/日志及helper后，旧控制源逐字节相同，另外11份运行源完全不变；241份记录中231份输出逐值不变，10份完整通过独立路径/载荷/摆腿复核。0/9/18/21抬升3mm，12/29抬升2mm，4/11/20/31抬升1mm；各自再减1mm就达不到所要求名义余量。0号名义高度243.758mm、身体路径净空24.479mm、腿路径18.929mm、摆腿净空25.175mm、摆腿关节余量.073877rad、四足路径最小预测23.908N、三足裕度37.811mm；这是冻结真实输入的数学可行性，不是物理改善。作用域关闭/原不可行/高度约束未启用/零努力限制均不会采纳修正，输入张量未被原地改写。`ii/local-test.json`与`ih/local-height-reserve-probe.json`保留证据。

确认远端无其它物理作业后，`climb-last-rear-height-reserve-20261006-ii/rearheight27302`于2026-10-06T16:32:15.718843在GPU1启动，监控PID742858、自动核验PID742860。同seed27302/32、14000步/280秒箱沿阶段、全32密集轨迹，主录像env0；12实际源/actor/reset已核验。补丁SHA256 `b93d2149e5944ba5ebfa97621f46e0a724ae54a736feeab9d51e2e54d1f16ee6`；候选只存外部产物，未提交推广控制源码。没有提速或NAV/PPO训练。

**当前等待ii，不启动重复评估。** 完成后核验32唯一完整终态/缺失、原完整成功/登台/展开/舒展、安全终止、三足/腾空/竖直速度/合力/含初始化饱和；与ig逐字段比较每例首次采纳新余量前的共同前缀，未采纳者全轨迹及终态严格相同，无遥测例外；ig31/id28/hy20分别列保留/丢失/新增，自动全轨迹真实释放重载审计。尤其检查0号是否恢复最后后脚、后续上台展开及停稳，同时检查其它9条改动路径，不能只看总数。5/10/13/19/23初次前脚瞬时不足5mm的旧问题本次作用域更晚，仍需单独解决；原起点与独立种子验收未通过。PUSH技能、MuJoCo、实机继续暂停；文档/产物同步指定分支和既有远端。

<a id="record-0017"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ig阶段完成31/32且既有路径全保留；定位0号最后后脚高度等待（2026-10-06 14:35）

**先成功率、后效率。** ig/frontreservefull27302于13:30:21正常结束，自动核验13:32:23通过，释放/重载审计13:33:32完成。**同seed27302、280秒箱沿阶段31/32（96.875%）完成四足登台、双前脚逐只展开、最终舒展稳定承重；id原28条全部保留，新增6/17/18，hy历史20条也全部保留。** 原完整任务仍0/32；32唯一完整终态、缺失0，全部time_out。原起点24秒/12秒和固定候选两组未用种子各32验收均未开始，不能把本批31/32当作验收通过。280秒仍仅诊断窗口，约4分钟并非可接受最终时长。

全程底座/姿态/低姿态/臂碰撞安全终止0，三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰148.388260N、含初始化单环境/关节累计力矩饱和0，以上整批质量与id逐值相同。12实际运行源/actor/reset、实际PhysX质量同步核验通过；全部32例前2000步与if逐字段严格相同，无遥测例外。633次起摆逐次满足此前10个20ms采样所选足≤5N，并均找到后续≥8N、reload1、连续承重.2秒；另695个含换腿/进入hold/展开完成的承重转换，无已发生顺序违例。0号末段卸载但尚未起摆，不应算作一次已完成摆动。

完整报告3877183809字节，SHA256 `cd1f12797343369e3c26a5a387b4f1fed33ecd6a24cadc47f73ae193a80c1a66`，已完整下载本地独立哈希核验。主录像env29 SHA256 `0cc4aa90b553a6c84cb44db9dac5be6e87e5c4800616d8cf0e2f1e525a63c074`，全解码7000帧/25fps/280秒；40/80/160/200/240/279.96秒抽帧审阅可见后续推进、登台及最终舒展。它证明29号40秒末等待卸载没有成为全程失败；这是抽帧审阅，不冒充全片原速验收。if中已发现的5/10/13/19/23初次前脚瞬时净空不足5mm仍在，不能因31例阶段完成就宣称所有几何余量合格。

**剩余0号已越过旧早期停滞点，卡在最后RR起摆前，而非上台后调整失败。** 173.20秒RL完成登台重载后开始最后RR准备；179.28秒采纳的名义前髋至足高度约240.76mm（末态脚位重算240.83mm），卸载后实测降至239.117mm，低于原240mm实测起摆门槛。自182.38秒至窗口结束连续97.62秒保持phase0、所选足0N/无接触、卸载比例1；其余三足约44.85/111.95/70.54N、支撑裕度40.05mm、pose/swing可行、命令超限0。足未起摆但接触已消失，feedback_unload不向无接触足恢复负载；重新规划又要求四足接触且卸载归零，形成稳定三足等待。`ig/env0-stall-audit.json`和源码support_ready/feedback_unload/requested对应此机制，不能靠降低240mm门槛强行释放。

已扫描全部32最后后脚阶段，只有0号存在参考age>10秒且前部高度不合格的持续等待；但4/9/11/12/18/20/21/29/31等原成功轨迹也曾采纳接近240mm的参考，统一提高名义目标可能改变其可行性。`ig/last-rear-captures.json`、`last-rear-nominal-height-audit.json`保存时刻和姿态；现有报告仅记录首次失败、地面恢复等规划输入，没有0号179.28秒已采纳方案当时的精确重力/载荷/搜索输入，不能用末态负载冒充。

因此本轮先做**控制行为不变的输入补录**：`climb-last-rear-plan-capture-20261006-ih/rearplancapture27302`于2026-10-06T14:34:25.011995在既有远端GPU1启动，监控PID742280、自动核验PID742282。220秒/11000步前缀、回合仍280秒、同seed27302/32环境、全32密集轨迹，主录像env0。只新增只写诊断字典、最后后脚已采纳/拒绝规划输入收集器，以及报告字段`climb_last_rear_pose_inputs`；移除这些日志语句后控制源与ig逐字节相同，评估源移除一个输出字段后也逐字节相同，另10份运行源不变。4项静态等价/来源检查通过，12实际源/actor/reset核验通过；诊断补丁SHA256 `83e4021159a4b07a7f5ee4ab5205ea6638067238c878c38c56d0a4a66c85901e`。没有新的控制器或提速改动，不能将补录称为进一步提高成功率。

ih完成后必须验证全32前11000步与ig逐字段严格相同（无遥测例外）、32份最后后脚输入含0号179.28秒可行采纳记录、实际质量/来源、全任务成功/终态与预期未完成、全部质量指标及实际释放重载。220秒仍未到280秒回合结束，存活者应记预期未完成，不能写终态齐全。**当前等待ih，不启动重复评估。** 随后用真实输入先检验卸载前更充足的名义前部高度及完整原几何/载荷/执行器检查是否有解，再做小范围物理验证并检查原31路径；仍保留原240mm实测起摆、5N连续.2秒释放、真实落脚重载、关节平滑与所有原安全/停稳门禁。鲁棒性确认后再减少冗余等待和规划耗时，不能靠放宽门禁提速。PUSH技能、MuJoCo、实机暂停；无NAV/PPO训练；未验证候选仅在外部产物，指定GitHub分支只同步文档。

<a id="record-0018"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：if恢复15且保留原4例推进；ig保持控制器做280秒全程诊断（2026-10-06 12:28）

**先提高成功率与鲁棒性，再提速；约4分钟仍太慢，280秒仅作当前阶段诊断。** 本次不改动作速度、真实释放/落脚重载/停稳等待。最新完整阶段证据仍是id同seed27302的28/32（87.5%）四足登台、双前脚展开并舒展承重，原完整任务0/32、32唯一终态且缺失0；原起点24秒/12秒及固定候选两组未用种子各32验收均未开始。

if/frontreserve27302的40秒诊断于11:44:33正常结束，11:46:06自动核验通过。完整报告549432678字节，SHA256 `6358e7fecc98070758957770bc0ffcb23a503b6eb8e0cbbd65e717f9e7cc5979`，已本地完整下载独立核验。12实际运行源/actor/reset、实际PhysX质量同步通过。完整成功0、已终态0、32例因短窗口结束预期未完成（不是终态齐全或32成功），尚无四足登台。短窗口安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰146.377060N、含初始化力矩饱和0；这些40秒数据不可冒充280秒改善。

**ie新回退的15号已恢复后脚动作，原0/6/17/18也继续推进。** 40秒末15第二后脚phase.515，0/6/17/18分别.955/.56/.80/.46。真实关节及原USD碰撞原语审计中，0/6/15/17/18的第二前脚摆动实测最小净空分别7.162/8.481/7.979/7.799/8.992mm，重载换腿时约7.162/8.705/8.391/7.799/9.007mm；新增准备作用的12例该窗口均未低于5mm。全32仍有5/10/13/19/23这5条未改旧路径瞬时低于5mm，最小4.985/4.628/4.937/4.828/4.970mm。它们不是本补丁新回退，但仍需解决，不能宣称全部实际几何已通过。初次前脚原姿态改善搜索仍非覆盖所有摆动的强制5mm门禁。

if真实释放/重新承重审计：127次起摆的此前10个20ms采样均所选足≤5N；96次已发生承重转换符合≥8N、reload1、连续.2秒；31次末尾摆动因窗口截止尚待重载，没有把它们当作完成，未发现已发生顺序违例。29号40秒时第二后脚phase0，但可行姿态为true、规划腿净空14.194mm，所选RL接触力由37秒35.32N降到39.98秒5.1109N，卸载进度.9067；尚不能判停滞，也不降低5N释放门禁。全程录像选29号检查后续真实释放及路径。

相对id的共同前缀仍仅有已单独审计的env5第551～1062步只写不读裕度遥测舍入差异（512样本、≤3e-8rad，两边裕度>.19且ready=true），其余所有要求字段严格逐值一致；纯严格脚本仍保留。if主录像env15 SHA256 `b3d0d8f3e1053534f22762397c0a3a7659abc9d9f1e7c404592d52d6e70bd2be`，全解码1000帧/25fps/40秒并抽帧审阅10/15/20/25/32/39.96秒，确认前脚落地及后脚推进可见；尚非全片原速验收。审计、规划输入、本地报告哈希及视频核验元数据已同步远端。

确认原远端无其它物理作业后，`climb-front-ascent-reserve-full-20261006-ig/frontreservefull27302`于2026-10-06T12:28:09.535627在GPU1启动，监控PID741682、自动核验PID741684。**12份控制/评估运行源、actor、reset与if完全相同，源压缩包也逐字节相同；仅评估步数2000→14000、报告路径及主录像15→29改变。** 同seed27302、32环境、全32密集轨迹、280秒箱沿阶段，非未用种子验收。8mm新增准备净空补丁SHA256仍`d00c412eadc5624f498f4e1e52c6258983fe8d763020145632e4ecf07e838d20`。候选只存外部产物，不提交推广控制源码。

ig结束后自动核验12实际源/actor/reset/实际质量、32唯一完整终态与缺失、原完整成功、登台/双前脚展开/最终舒展、安全终止、三足/腾空/竖直速度/合力/含初始化饱和；全部32例前2000步对if逐字段严格比较，**此处不允许任何遥测例外**。对id28条及hy历史成功路径分别列出保留/丢失/新增，随后全轨迹扫描真实释放及落脚重载。核验器预设成功流程，不代表尚在运行的结果已通过。当前等待ig，先查进程/status/verification.log及release-reload-audit，不重复启动。随后下载完整报告独立哈希、审查原速录像和净空/晚期停滞，再决定下一步。PUSH技能、MuJoCo、实机暂停，无NAV/PPO训练。自动推进提示已同步“先成功率、后效率”，GitHub指定分支只同步文档。

<a id="record-0019"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：先提高成功率再提速；ie推进原4例但15回退，if增加准备净空（2026-10-06 11:35）

**用户最新优先级：先继续提高成功率并保留已实现路径，之后再提高完成效率；当前约4分钟明显太慢。** 280秒仅为当前定位失败的阶段窗口，不作为可接受的最终速度。现阶段不靠缩短真实落脚/重新承重/停稳等待来换速度；鲁棒性验证后再逐段减少冗余等待、重复规划和转移时间，并重新验证成功率。最终仍需固定候选、原起点两组未用种子各32、每组≥30成功且无缺失及原速录像。

当前完整阶段基线仍为id：同seed27302、280秒箱沿诊断28/32登台、双前脚展开并舒展承重；原完整任务0/32，32唯一终态、缺失0。原起点24秒/12秒及两组独立种子验收均未开始。ie不是新的完整阶段成功率。

ie/frontprep27302的40秒前缀于10:44:02正常结束。完整报告549541507字节，SHA256 `ed8746685c42ad21f9a9e55eba5627f0382544e72325b17c44fa2ee887cbf5f7`，已本地下载独立核验；12实际源/actor/reset及实际质量同步通过。完整成功0，已终态0，32例因窗口结束预期未完成，不能写成终态齐全。安全终止0、三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰146.377060N、含初始化力矩饱和0。这组短窗口指标不能与id整280秒指标混作同窗口改进。

**原0/6/17/18都越过原先停滞点。** FR落脚重载分别21.46/21.38/21.28/21.44秒；首个后脚RR在31.82/31.80/31.66/31.80秒完成真实落脚重载，下一RL分别在36.58/38.08/37.94/38.08秒起摆、窗口结束时仍未完成。全32共126次起摆，之前10个20ms采样均所选足≤5N；95次已记录的承重转换符合≥8N、reload1及连续.2秒，另31次末尾摆动因短窗口尚未观察到重载。`ie/release-reload-audit.json`无已发生顺序违例，未把这31次算完成。

严格逐字段核验原始结果仍保存为失败：env5第551步`guidance_swing_path_margin`差异。完整差异审计确认只有env5在551～1062步共512样本该字段相差`2.9802322387695312e-08`rad，两侧裕度都>.19rad、swing_path_ready均true；源码AST及其它控制源检索证明该缓存只写不读，实际门禁使用当前局部计算结果。`verify-telemetry-reviewed.py`只允许这一个环境/时段/字段/差值范围，所有物理量、动作参考、门禁与其它字段仍严格逐值比较，复核通过；原脚本、失败日志和status均未覆盖。12例首次新增姿态采纳前共同字段一致，其它20例整个40秒前缀一致（env5仅上述只读遥测差异）。不能静默忽略所有遥测差异。

**ie新增env15后脚准备停滞，尚不可推广全程。** 15完成FR重载后自21.08秒停在RL准备，已尝试1次扩大搜索仍未采纳、四足承重且无命令超限；规划腿净空约4.573mm。`ie/front-landing-clearance-audit.json`重建真实关节几何：其新计划名义摆腿净空5.595mm，按抬脚前实测姿态重算只4.649mm，实际摆动最小4.579mm、FR重载后4.583mm。0/6/17/18重载后分别6.797/6.433/7.166/7.007mm，但6摆动中仍短暂降到4.859mm，不能把阶段推进解释为所有几何余量已满足。

据此if仅将ie新增的初次前脚准备搜索中的名义摆腿净空要求从5mm提高到8mm，为承重后的几何偏差留余量；原5mm支撑转移净空、身体10mm、.03rad关节余量、75%努力、四足≥8N/残差<.1与所有真实释放/重载/平滑门禁不变，足端路径/落点不变。曾在本地尝试10mm静态条件，但env0无解后提前停止并归档`if/rejected-10mm`，没有启动物理评估；原固定搜索集合中0/6/15/17/18可用的最大名义摆腿净空约9.162/9.690/8.993/9.281/9.215mm，不能盲把门槛提到无解后声称修好。8mm新候选还需真实物理验证。

if本地7组检查通过，含32份原捕获输入、候选全路径/载荷/摆腿复核、原可行方案逐值不变、相对ie唯一源码改变为更严格的一个净空比较、11份其它运行源完全相同及零努力限制不可采纳。相对id数学上改变[0, 6, 7, 8, 15, 16, 17, 18, 24, 27, 29, 30]；0/6/15/17/18均有通过8mm名义摆腿净空及其它原检查的姿态。补丁SHA256 `d00c412eadc5624f498f4e1e52c6258983fe8d763020145632e4ecf07e838d20`。这是冻结真实捕获输入的数学检查，不是成功率证据。

确认无重复物理作业后，`climb-front-ascent-reserve-20261006-if/frontreserve27302`于2026-10-06T11:34:59.106395在既有远端GPU1启动；监控PID741122，自动共同前缀核验PID741124，12实际源/actor/reset已核验。核验仅保留已在ie逐项证明的env5只读裕度舍入例外，所有其它字段严格逐值，未排除新的差异，纯严格脚本另存verify-strict.py。仍40秒/2000步前缀、280秒回合、seed27302/32环境、全32密集轨迹，主录像env15。**当前等待if结果，不启动重复评估；先检查15是否恢复、4例推进是否保留和其它原成功前缀有无回退，再决定280秒全程复核。** 新候选未提交推广。PUSH技能、MuJoCo、实机暂停，无NAV/PPO训练；文档同步指定GitHub分支。

ie主录像env17 SHA256 `d4c1bab1d7a57037a333bef5a4d41a84b5d9dacebb32e913ff66f8f997db1953`，全解码1000帧/25fps/40秒，10/15/20/25/32/39.96秒抽帧审阅；用户已查看该原速短片。它不是完整登台或全片原速验收。

<a id="record-0020"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：id完成28/32上台后舒展；ie检查第二只前脚落地前准备（2026-10-06 10:34）

id/finalclosure27302于09:34:00正常结束，自动核验09:37:14通过。**同seed27302、280秒箱沿诊断中，四足登台、双前脚逐只前移、最终舒展稳定承重均28/32（87.5%）；ic原24舒展路径全部保留，新增1/13/24/30。** 原完整任务仍0/32；32唯一完整终态、缺失0。全部32超时，底座/姿态/低姿态/臂碰撞安全终止均0。三足及以上100%、腾空0、|vz|峰.090701364m/s、含子步历史单足合力峰148.388260N、含初始化单环境/关节累计力矩饱和0，与ic全批指标逐值相同。280秒箱沿阶段不等于原起点24秒慢爬或12秒验收，尚未开始固定候选两组未用种子各32。

完整报告3879082332字节，SHA256 `bb37b3314b57ba38d96b51c82272ddd597b4d15e8dc5ec982bf579b23972613a`，已下载本地独立SHA核验。12实际运行源/actor/reset与实际质量同步通过；4例第一次补齐前所有旧轨迹字段逐值相同，其它28例全部旧轨迹及终态逐值相同。ic28条登台/展开路径无丢失；对hy原20舒展路径保留19，仍丢失17，不能称已完整恢复历史路径。

`id/closure-audit.json`实测：1/13/24/30各只尝试并采纳一次末段补齐，时刻264.96/255.16/255.48/255.16秒。最终参考高度剩余.979/0/0/0mm，连续满足原阶段舒展停稳条件分别12.04/21.84/21.52/21.84秒；四足最小承重在补齐至结束区间仍≥31.016N，速度峰≤.004168m/s、关节命令超限0，固定目标不变。真实释放/重载审计通过严格共同前缀与未改28例全轨迹的一致性继承ic的564次起摆及各次后续重载、620个承重转换事件；独立核对4例改动尾段始终platform_hold、双前脚完成、phase1/reload1、每足≥8N，无新摆动。`release-reload-inheritance.json`明确这是传递审计而非重新全扫描。

id主录像env1 SHA256 `507ae0b826424c6a3eb1897f90802735e5e603709bc2dd18857957f314afb76d`，完整解码7000帧/25fps/280秒；180/210/240/264.9/269/279.96秒抽帧审阅支持四足登台、展开和最终稳定姿态。这是原速文件全解码及抽帧检查，未冒充全片原速验收。

剩余0/6/17/18仍卡在早期后脚准备。新增`id/front-landing-clearance-audit.json`用ic真实关节和原USD碰撞原语重建全部32第二只前脚摆动（id此前轨迹已证实相同）：4例分别在17.44/17.22/17.00/17.16秒、右前脚仍下落时就低于5mm规划净空，限制部位FR_calf；途中最小约1.958/1.209/.598/.004mm，重新承重换腿时仅4.771/4.305/4.102/3.777mm。不是末段舒展导致，也不是仅到后脚规划才出现。全部32中有17例在该摆动窗口短暂低于5mm，因此无安全终止不能解释为所有实际几何余量都充足；极小正间隙也不构成安全认证。

源码定位：初次前脚登台的`front_ascent_pose`是改善姿态的优先搜索，失败后保留原已规划姿态；它不能被描述成覆盖所有初次前脚摆动的强制5mm门禁。4例在10.8～11.3秒的原搜索均尝试但未采纳，随后约14秒仍按原路径起摆。此前“保留原门禁”指代码门槛没有放宽，不意味着全部实际摆动已有足够余量。需在前脚落地前改善准备姿态，不能在后脚阶段直接降低5mm门槛。

新外部候选ie只在原初次第二前脚姿态搜索已失败时，增加带全部原检查的支撑姿态搜索。复用已存在的支撑/摆腿全路径检查，仍保持身体10mm/腿5mm、受载关节.03rad、75%执行器努力、四足≥8N与残差<.1、三足质心裕度25mm、FK与位姿移动边界；候选排序优先小幅位移及转角，落地重载预测加入质心随姿态旋转。脚端落点与摆动曲线、真实≤5N连续.2秒释放、实际落地重新承重等待、关节平滑/PD、低外层角速度反馈和最终补齐均不变。它不复活旧上台前前移参数对比，也没有放宽门槛。

本地6组检查通过，涵盖全部32份真实捕获输入及新增候选逐项路径/受载复核、原可行方案逐值不变、11份其它运行源相同和零努力限制不得采纳。数学作用于[0, 6, 7, 8, 15, 16, 17, 18, 24, 27, 29, 30]，其余输入原结果逐值相同；这不是物理改善结论。0/6准备平移约6.65mm，17/18约15.03mm，保留原落脚点；姿态转角仍由原.35rad边界约束。补丁SHA256 `84de6cfba6434062fe5ab0ac7eaf6f9f7be518d056b67f2bf60a7c07eba849c9`。候选源码只放外部产物，未推广提交。

确认远端无重复物理作业后，`climb-front-ascent-preparation-20261006-ie/frontprep27302`于2026-10-06T10:34:30.371976在既有远端GPU1启动，监控PID740554，自动核验PID740556。**本轮仅40秒/2000步前缀，回合仍280秒；存活但未终止者必须记为预期未完成，绝不当作32成功或完整终态齐全。** 录像env17、全32密集轨迹。12实际源/actor/reset已核验，自动脚本会记录完整成功/终态与预期未完成、三足/腾空/vz/合力/含初始化饱和，以及首次新增front_ascent_applied前逐值共同前缀。当前等待短评估，先查进程/status/verification.log，禁止重复启动。之后需审查四例真实前脚落地重载、实际净空、后脚能否推进以及id28路径前缀有无回退，再决定完整280秒复核；原起点验收尚未开始。PUSH技能、MuJoCo、实机继续暂停，无NAV/PPO训练，指定GitHub分支仅同步文档。

<a id="record-0021"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ic消除本批安全终止、28例登台；id补齐最终参考停止区（2026-10-06 08:35）

ic/angularhold27302于07:38:18正常完成，自动核验07:41:00通过。完整报告3847271377字节，SHA256 `8e1b88665f3e0b5957499c4b96fe0abdfbf94379d3de1422111c4b3aa4cb0592`。**四足登台及双前脚展开28/32（87.5%），最终舒展稳定承重24/32（75%），原完整任务仍0/32；32唯一完整终态、缺失0。** 全部32超时、底座/姿态/低姿态/臂碰撞安全终止均0；三足及以上比例100%、腾空0、|vz|峰.090701m/s、含子步历史单足合力峰148.388N、含初始化单环境/关节累计力矩饱和0。对比hy三足99.947905%、腾空.080秒、|vz|.870630m/s、合力215.744N、饱和.300秒，动态质量明显改善。这仍是同seed27302、280秒箱沿诊断，绝非原起点24秒/12秒或独立种子验收。

12实际源/actor/reset、实际质量同步、首次外层角速度反馈改变前与hy所有旧字段逐值一致、首次保持系数产生差异前与ib逐值一致均已通过。**hy原20舒展路径只保留15，丢失1/13/17/24/30，新增9/10/16/19/21/22/23/26/27；不得仅凭24大于20推广。** 1/13/24/30已登台、前脚展开且四足稳定承重，只差固定终点参考；17与0/6/18一起卡在早期后脚准备。原10例安全失败在本批均不再安全终止，其中6/18仍停滞；所有32无安全终止不等于32完成任务。

ic主录像env26 SHA256 `45a211253e21835eaa88db74ef4163efb6f629b6ca0876de68ac74886ba15e49`，全解码7000帧/25fps/280秒；10.8/25/120/200/250/279.96秒抽帧确认首前脚登台、双前脚支撑、后脚登台、上台后展开与稳定舒展。这是原速文件的解码/抽帧审阅，尚非最终全片原速验收。完整报告已下载本地并独立SHA核验；全32轨迹共564次起摆，逐次核对之前10个20ms采样所选足≤5N，并为每次摆动找到其后真实落脚重载≥8N、reload1、连续承重≥.2秒的记录，未发现违例。另记录620个含同腿复位、换腿、进入hold/展开完成的承重事件；两种事件计数不等价。26在186.44秒四足上台hold，218.86秒双前脚展开完成。证据为`ic/release-reload-audit.json`。

四例最终停滞是**实测位置与命令参考的停止区不一致**，未发生上台后跌倒。1/13/24/30参考距固定高度还差2.393/2.147/2.257/2.226mm，而实测只差约1.966/1.798/1.911/1.876mm，原adjust_platform_final_pose在实测差≤2mm时不再请求下一段；最终阶段判据却要求参考差≤2mm。四例低速、四足最小31～33N、无命令超限，最终规划拒绝计数0。扫描全部32的完整密集轨迹，增加“实测连续停稳累计≥10秒、已有最终调整段、实测差≤2mm而参考差>2mm”后，只有这4例进入新作用域，首次约264.96/255.16/255.48/255.16秒；`ic/final-closure-scope.json`保留证据。

新候选id保留ic低外层角速度反馈，针对上述已完成双前脚落脚重载、四足承重与全部原停稳条件合格的4例，允许向**同一个固定终点**再做一段小调整。普通规划的2mm最小动作仍不变；仅该停止区补齐分支把“是否值得移动”的数值最小位移改为1e-6m，允许约1～2mm末段。它不是碰撞/关节安全余量：21点全路径原.03rad受载关节余量、75%执行器努力、每足≥8N、合力残差<.1、身体10mm/腿部5mm净空、FK和真实跟踪/停稳检查完全保留。补齐段若不可行则维持原参考，不触发额外的横移/姿态搜索；完成后仍等待原实测停稳，未改变目标或成功判据。

28项源码/张量/实际方法检查通过：所有其它控制/角速度保持/质量/释放/重载/平滑方法不变，10份其它运行源相同；原规划器默认调用在8个真实规划输入上逐值相同；覆盖13种作用域/门禁排除、不可行保持和部分reset隔离。用末态实际几何/COM/接触，重力暂冻结于上一真实规划记录，数学补齐1/13/24/30分别需上升.983/1.798/1.911/1.876mm，目标参考剩余.983/0/0/0mm，完整原路径检查通过。这是冻结载荷数学探针，不是物理成功；运行时仍读取当前真实质量、重力、关节、接触重新检查。

确认ic及其核验退出、远端无其它物理作业后，`climb-final-reference-closure-20261006-id/finalclosure27302`于08:32:08在原远端GPU1启动，监控PID739975，自动核验PID739980。仍同seed27302/32、14000步/280秒箱沿诊断、全32密集轨迹，主录像env1。12运行源/actor/reset已核验，补丁SHA256 `7fbe971f9f66c46488c5f6aa981db46270d14064a19fb0cb468bc896928a40da`，候选仅在外部产物，未推广提交控制代码；没有PPO训练。完成后核验32唯一完整终态/缺失0、实际质量/完整质量，ic原24舒展和28登台/展开保留、4例是否补齐，以及首次补齐尝试前所有旧字段相同、未尝试28例全部旧轨迹与终态相同；安全/饱和/接触等变化必须单列。**当前id在运行，先查进程/status/verification.log，不得重复启动。**

另外4例0/6/17/18的后脚准备路径腿部净空约4.763/4.296/4.093/3.767mm，低于原5mm；仅1次扩大搜索且未采纳，四足承重、phase0、无关节命令超限。这个问题独立于最后参考停止区，id不修改它。后续需要核对真实关节几何、当前规划起点与双前脚落脚后的承载姿态，避免在进入净空不足的姿态后再盲搜；不能盲降5mm余量。原hy成功17的回退仍必须补回，保留动态改善后再推进其余3例。原起点24/12秒、固定候选两组未用种子各32（每组≥30且无缺失）未开始；PUSH技能、MuJoCo、实机继续暂停，指定GitHub分支同步继续。


补充实际几何核对：`ic/ground-clearance-audit.json`用记录的真实关节、机身姿态及原USD碰撞原语重建，4例限制部位均为FR_calf；实际关节算得净空约4.763/4.296/4.093/3.767mm，与足端逆运动学重建相差约1e-7m量级。不是关节名义/实测口径造成的假失败，进入后脚准备时起点就已低于5mm规划余量。下一步优先核对第二只前脚落地重新承重后的几何预测，并在此前支撑转移中预留净空；保留既有足端登台目标，旧上台前前移参数对比仍只归档。

<a id="record-0022"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：短对照定位外层角速度反馈敏感性；ic验证全程保持（2026-10-06 06:39）

**已验证的完整阶段基线仍是hy20/32，原完整任务0/32、32唯一终态/缺失0。** 本轮没有把短窗口存活记成登台成功。hy的20条四足登台、双前脚展开、最终舒展承重路径继续保留为基线；剩余2例早期净空停滞和10例安全终止尚未宣告解决。原起点24秒慢爬/12秒验收、固定候选两组未用种子各32仍未开始，PUSH技能、MuJoCo、实机暂停。

在hz精确失败复现上，按上一采样机身姿态重建支撑腿几何修正，env26/21/4/20关键采样与记录名义关节误差<1e-4rad（实际约1e-7）。26在4.6～5.4秒的支撑腿修正峰仅25.34mm，尚未触及原50mm限幅，但角速度已振荡增长；支撑腿待采纳命令与平滑后的实际目标差最大.231445rad，21为.058515rad，成功4/20约1e-7rad。现有支撑位置反馈增益.5、速度反馈.08、关节参考速度2.5rad/s及加速度15rad/s²。该证据支持检查外层角速度反馈与平滑/执行动态的相互作用，不能直接认定阻尼不足，也尚非完整动力学因果证明。`hz/support-feedback-diagnosis.json`和`support-reference-lag.json`保留数据。

ia仅在**首个前脚从全地面支撑开始上台**时，在摆动前10%用五次平滑函数将外层角速度几何反馈从.08减到.04；位置/平移反馈及执行器PD不改，换腿后恢复旧值。13.2秒箱沿前缀（episode仍280秒）于06:28:48结束、returncode0，报告176238909字节，SHA256 `c938453a214435a83e183a51bb9293639c72383bf7f1fc92eabb20b9cf9e0ed1`，本地完整SHA核验。1例底座终止26、31例预期未完成、完整成功0。26首次超限5.54→6.44秒，但仍在约7.14秒倒下；不能接受为修复。三足比例99.975759%、腾空0、|vz|峰.401716m/s、合力峰149.744N、含初始化累计饱和最大.200秒；同窗口hz分别99.887898%、.060秒、.413976m/s、136.136N、.140秒，接触峰与饱和反而增加。ia主录像179帧/25fps/7.16秒，全解码并抽帧确认仍倒下；SHA256 `4e9f992936471cac0ba1a419c79e3610e2d6101a71e2aa59931936604d6b8b77`。

ib只把上述同一作用域的外层角速度反馈平滑降到0；**关节PD阻尼仍是原值，关节参考平滑、真实释放/重载、碰撞/执行器/停稳门禁全部保留。** 06:33:31正常结束；报告178810937字节，SHA256 `7e1f4a997e630b1989862763e6e59a8ffd7eff97a5e806995a0d325f17b36171`，本地完整SHA核验。13.2秒内安全终止0、已完成终态0、预期未完成32、完整成功0；三足比例100%、腾空0、|vz|峰.287355m/s、合力峰113.951N、含初始化累计饱和0。不能把32例尚未结束写成32成功或终态齐全。ia/ib均通过12实际源/actor/reset/实际质量及干预前所有旧字段逐值一致核验；全部32在4.06～5.12秒首次受到反馈调整，8项本地源码/张量/生产代码片段/部分reset检查通过，无物理门禁例外。

ib中26/21都在4.30秒起摆，之前10个20ms采样FL竖直力≤5N；10.88/10.90秒完成第一只前脚落脚重载并换腿，上一采样FL约33.401/33.114N、reload1、连续承重.20秒，足端约x.8305/z.2237m；`release-reload-audit.json`保存实测。8～11秒角速度分量峰约.006～.009rad/s，首步明显稳定。然而换腿时外层反馈恢复.08，12～13.2秒角速度分量峰又增到1.076/1.245rad/s，21在12.8秒再现命令超限。不能宣称已解决后续动态失败。ib主录像330帧/25fps/13.2秒，全解码及抽帧审阅第一只前脚登台、承重与后续机身运动；SHA256 `1ddac9cd507d9664bc56ab3a124fd5e34bc817a5bc20591a42f95ed78f97ba75`，并非完整原速验收。

据此新候选`climb-angular-feedback-latched-20261006-ic/angularhold27302`保持ib的平滑降幅，之后**外层角速度反馈系数只减不增，直到对应环境回合reset才恢复初值**，避免下一次支撑转移重新开启这一路反馈。它只改ib的一处系数更新表达式，其余11运行源相同；没有去掉关节PD阻尼，也未改变身体位置/平移反馈、参考速度/加速度、质量同步、足端路径与原规划/释放/重载/安全门禁。11项本地检查通过，增加跨换腿/hold/短时disengaged保持和逐环境reset隔离检查。补丁SHA256 `5c2ce4717a779b9d90dd9d3c60dac75efa2ad9cf2bfca693d73efd0c42f4ad19`。候选仍仅在外部产物，未推广提交控制代码。

确认ia/ib均退出、无重复物理作业后，ic于06:36:45在原远端GPU1启动，监控PID739385，Isaac PID739388；同seed27302/32，14000步、280秒箱沿完整阶段诊断，全32密集轨迹、主录像env26。12运行源/actor/reset已独立核验。完成后自动核验进程PID739823（`verify-after.py`）会生成`verification-status.json`及`verification.log`，核查32唯一终态无缺失、实际质量、完整质量、hy原20保留/丢失/新增、首次反馈改变前与hy逐值一致，以及首次系数保持产生差异前与ib逐值一致。**ic当前运行，尚无改善结论；不能重复启动。**

下一轮先核对ic进程/status与核验日志，完整下载报告并独立SHA；逐项审阅新增/丢失阶段成功、真实释放/重载、全部10例原安全失败及0/19停滞，特别检查全程低外层反馈是否损伤后脚路径或最终舒展保持。检查env26原速文件，并明确抽帧与全片原速验收的区别。出现原20丢失、新安全终止、接触/饱和/腾空增加须单列，不因第一步改善推广。GitHub指定分支继续同步文档，未启动PPO训练。

<a id="record-0023"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hy恢复20/32完整阶段路径；hz复现并定位早期命令拒绝（2026-10-06 05:43）

hy/rearprep27302于04:24:25正常结束、returncode0。完整报告2790935540字节，SHA256 `78207830d4bed6af10b1d5f6434193cb1bd39f324afa14be8c00f256bcaa3bb1`，本地完整下载并独立SHA核验；12实际运行源/actor/reset、实际质量同步、32唯一完整终态/缺失0均通过。**四足登台、双前脚前移、最终舒展承重均为20/32（62.5%）；原hx17全部保留，新增11/12/25。** 完整原任务仍0/32，280秒箱沿阶段并非原起点24秒慢爬或12秒验收，固定候选两组未用种子各32尚未开始。

小幅四足准备仅在11/12/25生效，各2段，首次189.22/193.14/193.18秒。所有环境干预前原物理/控制共同前缀逐值相同，其它29例全程旧字段及终态逐值相同，遥测差异为空。核验中曾把hx最后轨迹采样279.98秒与hy回合终态280秒混比，误报微小差异；同类同刻比较后已排除，严格verify.py没有失败，没有降低比较要求或改写报告。

三例最后RR进入摆动分别208.48/212.40/212.44秒，之前10个20ms采样该脚竖直力均0N；214.52/218.54/218.58秒完成落脚重载，前一帧RR载荷36.548/31.988/31.878N，reload1、连续重载.20秒、触地年龄.88秒。双前脚展开完成在246.96/251.22/251.34秒，此后达到原舒展目标并停稳。`rear-release-reload-audit.json`保留实测顺序；不能把准备抬身或足端到台面但未承重视作完成。全32质量与hx逐值相同：22超时/3底座/7姿态/0低姿态，三足及以上99.947905%、最长腾空.080秒、|vz|峰.870630m/s、含子步历史单足合力峰215.744N、含初始化单环境/关节累计力矩饱和最大.300秒。

hy主录像env11 SHA256 `19fd51ffe98133e9cbe8040539986fae23db35f72f907d8f8c37f25bee7b00e4`，全解码7000帧/25fps/280秒；188/195/215/240/265/279.96秒抽帧审阅支持最后后脚登台、前脚展开及舒展保持。这是原速文件的解码/抽帧核对，不冒充最终全片原速验收。20条路径目前是同seed27302诊断结果，不是独立成功率验收。

**剩余12例：0/19两例早期腿部净空停滞，另10例安全终止6/9/10/16/18/21/22/23/26/27。** 下一优先级转向动态失稳。对所有32个首个FL释放前的实际记录复算，原41点摆腿关节/几何和完整卸载承载检查均通过：摆腿余量最小.20535rad、腿路径净空最小11.027mm、受载支撑余量最小.059565rad；仅增加同样静态检查不能区分这些失败与20条成功。来源依赖climb_stage_math/kinematics/body_clearance/crawl_gait与运行manifest哈希一致。记录在`first-front-release-preflight.json`；这是释放时冻结机身姿态的数学结果，不能覆盖摆动中的动态变化。

已保存`safety-onset-audit.json`，区分初始化与抬脚后的第一次命令不可行、失去三足和倾斜时刻。初始化0.02秒全32都曾出现命令余量超限遥测，不能用“第一次>0”定位后续失败，也不从饱和统计剔除初始化。最早失败26在4.30秒开始FL摆动、5.54秒出现FL受载候选命令超限.007737rad（phase.315），此时仍3脚有力，足力约0/109.51/66.42/14.24N、支撑裕度28.62mm；5.98秒机身倾斜增大，6.02秒底座终止。26在终止前没有失去三足接触；所以不将它简单归因为释放时支撑脚数不足。21首次失去三足10.94秒、支撑RL命令不可行11.20秒，失稳过程与26不同。其它8例仍应按具体动作及先后顺序定位，不以晚期错误推定共同原因。

hz/frontreview27302已于05:34:50正常结束、returncode0；当前没有运行中的hy/hz物理评估。12份源、actor/reset/seed27302/32环境全部与hy相同；只把录像主环境改26、执行前660步（13.2秒），episode设置仍280秒。完整报告174535819字节，SHA256 `10d608ea97fedb7ce7fbc8ce111ddc75a351abebfdd24ee41bbabd3110bfbff1`，本地完整下载并独立SHA核验。严格verify.py通过：全部32环境已记录前缀与hy所有字段逐值相同，已发生终态也逐值相同。**2例已终止（26底座、21姿态）、30例因短窗口预期未完成，完整成功0。** 这是箱沿失败前缀诊断，不是原起点12秒验收，也不能当成32例完整评估。

hz主录像env26 SHA256 `cdbed5bf3e96d0366d6344637019edf71258655befc74b4623101e28ed8f9f12`，全解码151帧/25fps/6.04秒，随26终止停止录制；4.3/4.8/5.2/5.54/5.8/6.0秒抽帧见首FL摆动中机身旋转并倒下。按控制先计算、物理后采样的顺序，将当前足参考对齐上一采样机身姿态，7个关键采样重建FL名义关节最大误差<1e-6rad；加入记录载荷偏置后重建超限也<1e-6rad。5.54秒名义髋角.908416rad仍在范围内，加.041801rad偏置后的**待采纳命令**为.950217rad，超过原.942480rad上限.007737rad。原loaded_leg_reference拒绝该腿候选并保留前参考，不能说超限候选已发送执行器；名义IK不可行也不是这个时刻的准确描述。

`aligned-dynamic-diagnosis.json`保存对齐计算：同一足端参考下，冻结释放姿态的髋角.669670rad；仅保留实际平移、冻结旋转为.650508rad；仅保留实际旋转、冻结平移为.936149rad。因此该时刻旋转漂移明显侵蚀侧摆余量，但这一几何反事实没有证明机身为何开始转动，也未证明其它9例同因。源码已有支撑腿位置/角速度反馈及50mm笛卡尔修正限幅，不能笼统说没有姿态反馈；接触力分配中的水平加速度仅跟踪平移速度。下一步须量化最早旋转增长前支撑腿反馈、限幅、实际载荷与关节跟踪，再验证摆动中姿态稳定/动态余量修正，保持真实释放、重载、关节与碰撞门槛。

hy20条完整阶段路径作为当前正确质量分支基线；hz无控制器改变，没有新PPO训练，也没有启动后续候选。下一轮先核对远端进程，避免重复启动；优先处理10例动态安全失败，并单独保留0/19早期净空停滞，不盲降原5mm规划余量。原起点24/12秒及固定候选两组未用种子各32仍未开始。PUSH技能、MuJoCo、实机继续暂停，指定GitHub分支文档同步继续。

<a id="record-0024"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hx补齐17例上台后舒展；hy验证最后后脚登台前的小幅四足准备（2026-10-06 03:32）

hx/finalpose27302于02:29:10正常结束、returncode0。完整报告2749074439字节，SHA256 `954892c9e80840f5bcd8af29a269d505b023a16308b5cd8813785928557bb613`；本地完整下载并独立SHA核验，远端12实际源/actor/reset、实际质量同步及32唯一完整终态/缺失0均通过。**四足登台、双前脚展开、最终舒展稳定承重均为17/32（53.125%）；登台后的17例全部完成。** hw原14全部保留，新增1/3/14；完整原任务仍0/32，不能解释为未登台，也不能把280秒箱沿阶段诊断冒充原起点24秒慢爬或12秒验收。

最终小幅调整只在1/3/14各采纳一次，轨迹首次计数分别252.34/250.16/249.56秒；所有环境干预前原物理/控制字段逐值一致，未采纳29例原终态及全程旧字段一致，没有遥测例外。双前脚完成在224.84/225.16/224.56秒，采纳前各脚真实载荷最小31.883/32.044/31.717N；`front-before-final-audit.json`保存顺序及实测力。三例参考高度达到原固定目标约.503813m，实际末态高约.50424m，参考保持年龄27.66/29.84/30.44秒，四足承重、低速、原命令无超限。没有改目标或降低.03rad受载余量、真实释放≤5N连续.2秒、落脚重新承重和平滑/碰撞/执行器/停稳门槛。

全32质量与hw逐值相同：22超时/3底座/7姿态/0低姿态，三足及以上99.947905%、最长腾空.080秒、|vz|峰.870630m/s、含子步历史单足合力峰215.744N、含初始化单环境/关节累计力矩饱和最大.300秒。**仍有15例未完成阶段：5例登台过程停滞，10例安全终止。** 17例阶段成功不能抵消这些失败，也还没有固定候选的独立种子验证。hx主录像env14 SHA256 `f853aed7bfe1df313b22814f9e75f1ca1557d6f8e167918795ba0faadb2bd7a8`，全解码7000帧/25fps/280秒，204/225/248/252/260/279.96秒抽帧审阅支持双前脚展开后小幅抬身并稳定保持；此处仍是抽帧审阅，未冒充最终全片原速验收。

下一步针对11/12/25：三足已在台面、最后RR仍在地面，旧三足承载/摆腿姿态规划失败，四足持续承重且卸载0；机身高度约.3886～.3899m。0/19早期腿净空停滞和10例安全终止仍另外处理。对未被hx改变的记录做冻结载荷数学递推：先保持四脚落地，每次抬身5mm并朝支撑平面调平最多.025rad，11/12经过2段、25经过3段后，旧完整三足/摆腿规划分别找到.030398/.031360/.036846rad余量的候选。每段均经过21点受载/努力/正向运动学、四足≥8N与残差、身体及腿路径检查；准备段最小余量.042908rad。此推演未更新真实重力/肢体质心，不是动态可行证明；运行时必须每次重新读真实姿态/质量/重力/接触，原三足规划继续独立把关。

对hx全部32密集轨迹独立扫描新增准备资格：仅11/12/25满足连续10秒，估计首次189.22/193.14/193.18秒；原17成功与其它12失败的最长连续资格均0。作用域是仅三足台面且当前后脚地面上台、phase0、原规划失败并保留有效参考、卸载0、四足真实≥8N、参考年龄≥3秒、位置误差<10mm/姿态误差<.025rad、线速<.001m/s/角速<.01rad/s、原关节/命令条件通过。条件中断重计10秒；每次准备先保持所有脚着地，等待真实跟踪/承重/低速停稳后才恢复原三足规划，准备本身始终`pose_feasible=false`，不能授权起脚。最多4次小段，既有上台路径、前脚展开和最终机身调整源码不变。

确认hx已结束且远端GPU空闲后，`climb-last-rear-preparation-20261006-hy/rearprep27302`于03:30:37启动，监控PID737216、GPU1；同seed27302/32、280秒箱沿、全32密集轨迹，主录像改为env11。28项源码/张量/实际准备方法集成检查通过，包括10秒连续资格、17类门禁/阶段排除、三例记录实际方法进入、真实停稳前不放回原规划、不可行保持原参考、4段上限、部分reset隔离。仅guidance/evaluator两份源改变，其余10份相同；原所有辅助函数及真实起脚/重新承重/PD/碰撞门禁方法AST不变，requested只增加作用域准备调用及准备期间防止重新捕获参考。远端12运行源/actor/reset核验通过，补丁SHA256 `9dbd5e664e979852f14727230380eb4c91e499a0dd5fca2c4887663634e3c617`。候选仅在外部产物，未推广提交控制代码；没有新PPO训练。

下一轮先查hy进程/status，**不要重复启动**。完成后运行hy/verify.py，核对32唯一完整终态、来源/实际质量/完整质量、hx原17条阶段成功及全部登台/展开是否保留，首次`rear_prep_applied`前所有旧物理/控制字段完全相同，未采纳者全轨迹和原终态相同。检查11/12/25是否真正完成最后RR卸载≤5N/.2秒、摆动、落脚重新承重，再前脚展开和舒展，而不把准备抬身或单腿推进记作完整阶段成功；新增安全失败/饱和/腾空/旧成功丢失须单列并拒绝推广。原起点24/12秒及固定候选两组未用种子各32（每组≥30成功、无缺失）尚未开始；PUSH技能、MuJoCo、实机继续暂停，指定GitHub分支同步继续。

<a id="record-0025"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hw全部17例完成前脚展开、14例舒展；hx验证最后3例的承重调整（2026-10-06 01:38）

hw/platformpose27302于00:27:37正常结束、returncode0。完整报告2729032379字节，SHA256 `d3c050917e190f7aef37438d45c2ce2c811fca2ca5db416a63e2c8e39f988b1a`，本地完整下载后独立SHA核验通过；远端12实际源/actor/reset、实际质量同步、32唯一终态/缺失0均通过。**四足登台17/32（53.125%），双前脚展开17/32（53.125%），最终舒展承重14/32（43.75%）。** 相对hv，17条登台全部保留，双前脚展开10→17，舒展承重10→14；hv原10全部保留，新增7/24/29/30。完整原任务仍0/32；当前是280秒箱沿阶段诊断，不是原起点24秒慢爬或12秒验收。历史错误质量缓存分支hq16仍仅作比较：hw保留其中11条、丢失0/11/12/19/25、新增2/8/13，不能宣称已超过历史16。

hw新前脚支撑搜索只在1/3/7/14/24/29/30生效，各采纳一次，首次204.42～215.88秒。所有环境干预前物理/控制共同前缀逐值一致，未采纳25例原终态字段及全程旧字段一致；本轮`diagnostic_differences`为空，没有实际用到hv已记录的非作用域遥测例外。后脚登台逻辑、真实≤5N连续.2秒释放、落脚重新承重、关节参考平滑、碰撞/执行器/停稳条件均保留。全32质量与hv逐值相同：22超时/3底座/7姿态/0低姿态，三足及以上99.947905%、最长腾空.080秒、|vz|峰.870630m/s、含子步历史单足合力峰215.744N、含初始化单环境/关节累计力矩饱和最大.300秒。既有10例安全失败仍未解决。

**剩余3例1/3/14不是前脚没迈出去，也不是上台后跌落。** 均已两前脚展开、四足稳定承重，最后固定高度参考尚差4.69/6.71/6.69mm，原最终规划分别拒绝19/20/21次。实测机身x已经超过固定x目标，旧规划把x增量夹为0，只尝试竖直抬升。精确重放首次拒绝输入252.32/250.14/249.54秒：当前起点受载命令余量.034014/.031174/.038405rad，而最小1/4抬升候选也降到.028066/.022450/.029736rad，均低于原.03rad门槛；身体/腿部净空、支撑力和合力残差并非这一拒绝原因。`final-plan-gate-diagnosis.json`保留首末拒绝完整输入、21点各类余量及候选结果。其它5例未完成登台（0/19早期净空、11/12/25最后RR准备）与10例安全终止仍独立处理。

hw主录像env14 SHA256 `1fc048f5913352dbde369d023f6fd5ced61095518033849096f5a2e8b7270eb5`，完整解码7000帧/25fps/280秒；188/204/212/225/250/279.96秒抽帧显示上台、前脚展开后稳定保持。这个例子的最终高度仍未完成；不以录像看似站稳替代固定目标判据，也不把抽帧审阅说成最终全片原速验收。

针对上述最后3例，hx仅在**原最终规划拒绝，双前脚已前移并重载、四足台面≥8N、原低速/调平/关节/跟踪/停稳条件全部满足**时增加135候选的小幅平移和滚转/俯仰搜索。原可行规划优先保留，原固定目标不改；每段向前≤10mm、横向≤5mm、XY总位移≤12mm、转角≤.025rad，上升仍原10/15mm上限且不超过目标。机身已超过固定x目标时才允许向目标回退，且不能退到目标后方；不能靠改目标算完成。保留21点整个路径原.03rad受载/名义余量、75%努力、每足≥8N、残差<.1、身体10mm/腿部5mm路径净空、FK误差等检查，并额外要求终点综合余量≥.05rad。

三例记录的数学解分别再前移5/10/5mm、横移5mm、抬升4.268/6.312/6.290mm，微调姿态后达到原目标高度；21点受载综合余量最小.034014/.031174/.038405rad，终点.055781/.050497/.051977rad，最弱足约31.39～31.67N。是冻结重力/COM模型下的预检，不是物理成功。22项源码/张量/完整`adjust_platform_final_pose`集成检查通过，包括12种作用域/门禁排除、真实14捕获、固定目标不变、旧可行规划逐值保持、不可行时保持原姿态、部分reset隔离；仅guidance/evaluator两份源改变，其余10份相同，全部原辅助函数及其它门禁方法AST相同。

确认hw完成、远端无重复评估且GPU空闲后，`climb-platform-final-redistribute-20261006-hx/finalpose27302`于01:36:16启动，监控PID736630、GPU1；同seed27302/32、280秒箱沿、全32密集轨迹、主录像14。远端12实际源/actor/reset已核验，补丁SHA256 `ca7831a637c885fb4d5b4c8ff723dfb228a5360aaf62db3c0cf737e33c356074`。候选控制源码仅保存外部产物，没有推广提交；近期是控制器物理评估，未启动新PPO训练。

下一轮先核对hx进程/status，**不要重复启动**。完成后运行hx/verify.py，核对32唯一完整终态/来源/实际质量/全质量，hw原14舒展、17登台和17双前脚展开分别保留多少，首次`final_search_applied`前每个旧控制/物理字段相同、未采纳者旧终态及全轨迹相同。重点检查1/3/14是否达到原高度并稳承重、最终调整确实在双前脚重载之后；新增安全终止、腾空、饱和或旧成功丢失必须单列，不因局部成功推广。主录像保留原速，原起点24/12秒及固定候选两组未用种子各32验收仍未开始。PUSH技能、MuJoCo和实机继续暂停，GitHub指定分支文档同步继续。

补充数学探针：hu归档输入的11/12/25最后RR登台停滞，在同一高度做约.025rad四足调平可找到单段可行解（余量.212822/.203669/.203186rad），存`hu/last-rear-four-support-level-probe.json`。只证明这一小段数学可行，未证明连续推进或真实抬脚；没有并行启动其它评估，不抢占当前最后3例的修复优先级。

<a id="record-0026"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hv恢复17例登台、10例展开；hw验证上台后的前脚支撑转移（2026-10-05 23:34）

hv/groundpose27302于22:26:57正常结束、returncode0。完整报告2707502379字节，SHA256 `420d613e0ba2c85d92a01d752dc4db30e15365d2c48a61e484bb0df82ce99cce`，已完整下载本地并独立SHA核验；远端12实际源/actor/reset、实际质量与缓存同步、32唯一终态/缺失0均通过。**正确质量分支四足登台从hu5/32提高到17/32，其中10/32完成双前脚展开并舒展承重。** 10例为2/4/5/8/13/15/17/20/28/31，hu原5全部保留，新增2/8/13/15/28。相对历史hq16，保留4/5/15/17/20/28/31共7例，新增2/8/13，仍丢失9条旧完成路径，不能说已超过历史16。完整原任务仍0/32，不等于没有登台；280秒箱沿阶段不是原起点24秒或12秒验收。

后脚恢复实际作用在1/2/3/7/8/13/14/15/24/28/29/30这12例，首次采纳在87.84～89.70秒，各只采纳一次。这12例均登台。其它20例原终态字段全部相同，所有环境干预前的物理状态、动作参考、实际接触和原门禁逐值相同。严格全字段比较第一次在env0的173.30秒报错，原因是两个只读遥测`guidance_swing_path_margin/gap`随同批其它环境是否启用摆动预检而写入非零；env0共380采样，实际仍phase0/地面目标、两次ready均true，源码AST证实这两个buffer仅被控制类写入，没有读取参与控制。原严格脚本/失败日志、逐样本条件审计保留；仅明确排除这两项非作用域遥测后其余旧字段全程相同。第二次比较发现终态新增的两项ground计数未排除，修正终态schema后完整核验通过。没有改物理报告、候选源或安全门槛以通过比较。

hv全部32质量与hu逐值相同：22超时/3底座/7姿态/0低姿态，三足及以上99.947905%、最长腾空.080s、|vz|峰.870630m/s、含子步历史单足合力峰215.744N、含初始化单环境/关节累计饱和最大.300s。既有10例安全失败没有解除，不能用局部推进抵消这些风险。14在87.84秒采纳新后脚支撑姿态，91.06秒进入RR摆动，之前10个20ms采样该足竖直力均0；96.52秒落脚重载换腿，前一条RR力54.350N/reload1/loaded_age.2s/touch_age.88s。188.52秒四足上台承重进入hold，199.62秒请求FL前移，之后规划失败停滞。对应env14-release-reload.json/events.json可审计，不能把预卸载时已经失去接触的时刻混同91.06秒才首次离地。

**剩余7例上台后停滞集中在前脚展开准备，而非再次跌落。** 1/3/7/14/24/29未完成第一只FL前移，30完成FL后卡在FR；均四足承重、低速、pose_feasible=false、unload0，原命令没有超限、原停稳条件没有放宽。末态支撑裕度约22.37～23.54mm，低于原25mm准备条件；第一轮受载规划拒绝输入约204.40～204.98秒（30为215.86秒），持续42～50次重规划仍未找到方案。不是只差窗口尾部几秒。0/19早期腿净空问题、11/12/25最后RR登台规划以及10例安全终止保持原结果，继续独立处理。

hv原速文件SHA256 `30120bc67ee8c1b7b5f866b687b7e5262dcf6775e3682539fd10b148f0d8a15b`，完整解码7000帧/25fps/280秒，85/95/150/200/240/279.96秒抽帧审阅支持后脚真实推进、上台后前脚准备停滞。视频及全部密集报告、终态/事件/逐例尾态/完整规划输入已本地归档；此处是抽帧检查，不冒充最终全片原速验收。候选尚未具备原起点完整任务验收资格。

针对7个原记录规划输入，新增台面前脚展开支撑搜索：**前脚迈出前机身和预测COM都禁止前移**，只搜索小幅后退/横移/姿态调节。保留原8cm/.35rad上限，并进一步限制XY≤6cm、竖直变化≤2.5cm、转角≤.15rad；同时保留原关节/75%努力/10mm身体路径/5mm腿路径/摆动及接触探测重载检查，追加21点四足路径最弱足≥8N、残差<.1。7个数学候选均可行，综合关节/受载余量最小.067784rad、四足路径最弱足24.747N、腿路径最小52.341mm。未采用无小幅约束时偏大下蹲的搜索结果；数学可行不等于物理成功。

确认hv退出且GPU空闲后，`climb-platform-front-pose-search-20261005-hw/platformpose27302`于23:33:04启动，监控PID736032、GPU1，同seed27302/32、280秒箱沿、全32密集轨迹、主录像14。以hv完整实际质量/后脚恢复为基线，只在原规划失败且四足台面≥8N承重、低速、phase0、正在逐只前脚展开时增加搜索；已有可行姿态不变，攀爬/后脚/最终机身调整不在新增作用域。原支撑转移、≤5N连续.2秒真实起脚、落脚重载、参考平滑、碰撞/执行器门禁保持，候选源码仅在外部产物，不推广提交。

17项源码/张量/实际capture块集成检查通过，覆盖10类作用域排除、真实14捕获、前脚展开前机身与COM不前移、小幅限幅、已有可行计划不变、重复失败原点限频和部分reset。仅guidance/evaluator两份源变动，其余10份逐字相同，全部原辅助函数与运行时门禁方法AST相同；远端12源/actor/reset匹配。补丁SHA256 `1d1973e017124fe37b1ee32ccfbdf3ccf4300efe7b92e3e97337be141bf40b68`。当前是远端控制物理对照，未启动新PPO训练。

下一轮先查hw进程/status，**不要重复启动**。完成后运行hw/verify.py并保留任何失败日志：32唯一完整终态/全部来源/质量同步/完整质量，hv10已完成路径与17登台数分别保留多少，新增支撑搜索首次作用前的物理与控制字段共同前缀及未采纳者全程一致。只允许已有明确证据的地面非作用域只读摆动遥测例外；其它差异先定位，不能盲目扩大忽略字段。检查7例实际前脚迈出/落脚承重、双前脚展开后才最终调节，任何新增碰撞/饱和/腾空或旧成功丢失须拒绝推广。原起点24秒/12秒与最终固定候选两组未用种子各32仍未开始；PUSH、MuJoCo、实机继续暂停。

<a id="record-0027"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hu质量同步正确但阶段退步至5/32；hv验证后脚受载姿态搜索（2026-10-05 21:33）

hu/masssync27302于19:43:21正常结束、returncode0。完整报告2686821978字节，SHA256 `cd92091f6dc8c94276eaf9e39dd539120d49d22512c3e9ff44180f69e9634ecf`；完整本地文件独立SHA、远端12实际源/actor/reset、32唯一终态/缺失0均通过。全部32实际startup质量与ht同种子快照逐值一致；末尾缓存等于实际质量，各环境最迟第一步起始终使用正确重量。**质量缓存缺陷修复有效，但动态控制效果退步，hu不推广。** 四足登台、两前脚展开、舒展承重仅5/32（4/5/17/20/31），均属于hq原16；丢失0/7/11/12/15/19/24/25/28/29/30共11条，无新增。完整原任务0/32，不能解释为没有登台案例。hq16/32保留为历史路线对照，不以错误质量缓存替代后续正确载荷计算。

hu完整质量：22超时/3底座/7姿态/0低姿态；三足及以上99.947905%，最长腾空.080s，|vz|峰.870630m/s，含子步历史单足合力峰215.744N，含初始化单环境/关节累计力矩饱和最大.300s。hq对应为22/2/7/1、99.959802%、0/.789996m/s/250.319N/.280s。冲击峰下降不能掩盖成功率下降、腾空与饱和增加。hu主录像14已完整本地保存，SHA256 `d1817a1ff9292c146f3e6b19b66566011de3a8026083d8375a991d32cee1c0ce`，全解码7000帧/25fps/280秒，1/30/60/90/180/279.96秒抽帧审阅显示前脚推进后混合高度下停滞；不是最终全片原速验收。

**失败已分解，不能笼统归因为卸载压力。** 12例1/2/3/7/8/13/14/15/24/28/29/30在后续RR地面跟进前卡住，四足持续承重、速度很小、原规划pose_feasible=false、卸载0；7/14首个拒绝在87.90/87.82秒。对记录的实际输入以65高度/3645候选复算，7/14所有候选受载余量不通过，最佳完整卸载载荷余量仍为−.023993/−.041392rad，去掉载荷余量检查才分别有93/74条候选，所以不能放松关节/执行器门槛。0/19属于更早后脚准备停滞；0在21.28秒记录起点腿primitive净空4.879mm，所有路径都包含这个不足5mm的起点，扩大高度搜索无法修复。11/12/25已达三足台面，但最后RR受载/摆动姿态仍不可行。其它10例安全终止仍独立待解。所有32终态、事件和失败尾态已归档hu/failure-analysis.json；四个代表规划复算在planner-gate-analysis.json，未运行本地物理仿真。

下一步保持正确质量同步，对原搜索未覆盖的后退/横移/滚转组合增加**仅限旧规划失败的混合高度后脚地面跟进**候选。实际记录12例的数学探针均能找到符合原8cm位移/.35rad转角、30mrad关节/载荷余量、75%努力、身体路径10mm/腿路径5mm等条件的姿态；额外检查测量COM随姿态旋转、21点四足承重路径≥8N/合力残差<.1、真实计划摆动路径、15mm接触探测和落脚重载。12候选最小综合余量0.040434rad、四足路径最小力34.741211N、腿路径最小净空0.005796m。这是数学可行性，不是动态成功；接近原净空下限的路径尤其要检查实际承载下沉和碰撞。

确认hu评估退出且GPU空闲后，`climb-rear-ground-pose-search-20261005-hv/groundpose27302`于21:32:42启动，监控PID733662、GPU1，同seed27302/32、箱沿280秒、全32密集轨迹和主录像14。以hu实际质量同步为基线，仅guidance/evaluator两份源码改变，其余10份逐字相同；原所有辅助函数及支撑/真实抬脚≤5N连续.2s/落脚重载/力矩/参考平滑方法AST相同。仅原规划失败、双前脚台面/双后脚地面、四足接触、后脚地面目标、phase0和低速时启用32768固定Sobol搜索；已有可行捕获保留原结果，平地、台面展开、前脚与后脚上台均排除。单独记录次数/实际采纳及完整输入，重复失败原点不反复搜索，局部reset只清对应环境。没有继承hr后脚trim或未启动hs方案；未提交候选控制器为已验证代码。

16项张量/源码/实际capture块集成检查通过，包含原可行路径不变、真实14成功进入候选、原preview不修改、重复失败原点限频、部分复位和8类排除；远端12运行源/actor/reset全部匹配。补丁SHA256 `09b8a28bc2dd70b91bfe556027c12419cc2fc4b687d5c0e7f570ec104e53d4fe`。评估已启动，尚无结果；近期是物理控制评估，没有新PPO训练。

下一轮先核对hv进程/status，**不要重复启动**。完成后运行hv/verify.py：核对32唯一终态/完整质量/来源及质量同步；所有环境首次ground_applied前旧轨迹字段须与hu逐值相同，无采纳者全程与终态相同；hu5条是否保留、hq丢失11条恢复多少和新增安全失败分列。重点核对真实RR起脚/重新承重后是否继续完整登台和双前脚展开，不能以找到数学姿态或单脚推进算改善完成。保留hu/hq完整来源，记录全部质量；若新增失稳不推广。原起点24秒/12秒和最终两组未用种子各32验收未开始；当前仍280秒箱沿课程。PUSH、MuJoCo、实机暂停。

<a id="record-0028"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：确认复位后质量缓存过时；hu修复实际质量同步并评估（2026-10-05 18:50）

**发现可直接验证的控制器缺陷：StageClimbAction在ActionManager构造时缓存body mass，Isaac随后才执行startup随机载荷；缓存从未同步。** 远端只读ht初始化审计（同seed27302/32/actor/reset/物理源）直接比较PhysX实际body masses与action.mass：32例全部不同，差异仅在base，随机增量−.513958～+2.996620kg。缓存重量所有环境213.514648N，第1/14例实际分别239.687958/241.219223N，质量增量+2.668021/+2.824113kg。hq稳定尾段500采样足力总和均值239.688422/241.219607N，与实际重量仅差.000464/.000383N，和旧缓存相差约26.17/27.70N。这解释了载荷分配输入不正确；尚不能宣称它是全部失败的唯一根因。

Isaac实际安装源码确认顺序：`ManagerBasedEnv.load_managers()`先建立ActionManager，`ManagerBasedRLEnv.load_managers()`随后应用startup事件；源码及SHA已归档ht/startup-order.json。缓存不仅用于重量，还用于全身COM加权，因此旧规划的预计关节载荷和支撑位置都可能偏离实际。ht完整JSON SHA256 `5065ac24df30c9d48bf832c5ff3ac8bcb898feaa4f0d49b0521775be54454dff`，本地独立SHA及12实际源/actor/reset/evaluator匹配。只做初始化/复位读取，没有策略动作、完整物理回合或成功率证据。快照保存后app.close停留超过3分钟，定向SIGTERM停止该审计；随后进程返回0，实际停止方式保存在teardown-stop.json，不能说成无干预正常退出。没有留下旧审计/GPU进程。

确认GPU空闲后，`climb-runtime-mass-sync-20261005-hu/masssync27302`于18:49:36启动，监控PID731464、GPU1，同32/seed27302、箱沿280秒、全32密集轨迹、主录像14。**以已完整验证的hq为基线，只在pending复位环境第一次处理动作、任何COM/支撑规划之前，从PhysX重新读取对应body masses。** 每次复位均同步，运行中的其它环境不改变；物理质量和随机化配置、actor/reset、全部guidance/路径/接触/碰撞/PD/参考限幅/努力/停稳代码保持hq原文。没有继承hr后脚微调或未运行的hs搜索候选。未把候选控制源码提交为已验证控制器。

11项测试通过：32真实审计质量同步、无复位时不读不变、局部复位仅更新对应环境、重复复位读取最新值、缓存不别名共享、重量和加权COM一致、移除同步段后原stage模块AST相同、仅stage/evaluator两份源变化、guidance与原门禁逐字相同。补丁SHA256 `d26a7dce54ca1690e122615acc480e4cf15c15fd7f2adb6b004016c314df28f9`；远端12源+actor/reset全部核验。evaluator新增只读初始/末尾cache与实际质量来源、逐帧使用重量和COM遥测。质量正确性已单独核对，但hu动态成功率尚未得到；质量修复会从初始化起影响全部32环境，不能要求旧轨迹共同前缀不变或预先保证16条路径不受影响。

**上一轮hr没有提高成功率，因新增碰撞不推广。** hr/rear27302于18:25:27正常完成，完整报告2576029511字节、SHA256 `d46d2d7818373dc278d0a70fbb1aea2de006eea71ae9916bdc431d803c714601`，已完整本地下载并独立SHA核验。12源/actor/reset/evaluator、32唯一终态/缺失0通过。与hq仅1/14改变，首次变化与rear_active均在147.50/97.16秒；其它30旧字段轨迹/终态逐值相同。旧16全部四足登台/前脚展开/舒展承重，仍16/32；完整任务0/32。终止21超时/3底座/7姿态/1低姿态，新增14底座碰撞。三足及以上99.956383%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化单环境/关节累计饱和最大.280s。足力峰和饱和未增加不能抵消新增碰撞。

hr两例均真实推进后脚：1在148.88秒开始RL摆动、148.92离地、154.40落脚重载换RR，此后完成RR和双前脚跟进；186.48秒起下一次RL地面步规划不通过，末态余量−.02954m/pose_feasible=false/卸载0、四足承重，目标x=.69m，不能说后脚登台。14在99.82秒开始RL、99.86离地、105.34落脚承重，后续RR和FL完成跟进；137.36开始FR台面跟进，139.86秒底座碰撞。hr录像SHA256 `d568188bc61acb7300bd775aee4defea3f850d6758c0693cbfacef0c240211c5`，完整解码3497帧/25fps/139.88秒，六张关键帧审阅显示后续滚转/下沉；280秒是本批最长窗口，14提前终止，不冒充280秒录像或最终全片原速验收。

14最早可定位的参考异常：规划预计受载余量.035800rad，起脚前FL小腿实际请求余量仅.009119rad；137.44秒请求越过软限位.000183rad，原门禁将该腿标为无效，随后137.64秒角速超过.2rad/s、138.48秒一条支撑足力≤8N、139.74秒支撑裕度变负，最后碰撞。用记录nominal+load_torque/30重算超限，误差≤5.57e−8rad；这是请求被原门禁拒绝，不能混同实际关节已越过物理限位。冻结实际起脚姿态的摆动几何仍有约20.98mm腿净空、85.98mm底座间隙，不能只靠几何可达宣布受载稳定。

hs仅做了未启动的数学候选：65高度采样增加.08rad余量无可行解，扩展位置/姿态搜索找到名义.15059rad候选，但身体路径最低净空仅11.3mm，且.08阈值预检会触及许多旧成功路径。保存在`climb-front-loaded-reserve-20261005-hs/not-launched.json`，未执行任何hs物理训练/录像，质量缓存缺陷优先。相关原始轨迹、真实释放/载荷、几何与参考超限分析均保存hr目录；旧16/32仍是实际阶段结果，修复后结果需重新评估。

下一轮先核对hu进程/status，**不要重复启动**。完成后运行hu/verify.py，要求初始实际质量与ht同种子快照逐值一致、末尾cache与实际质量逐值相同、每个环境最迟第一步已使用正确重量且之后持续正确；同时核对32唯一完整终态/质量、hq旧16条是否保留及新增成功/安全失败。若丢失旧成功或新增安全失败，定位真实受载状态后继续修正，不能以修了缓存就宣布爬台完成。原起点24秒/12秒以及最终两组未用种子各32验收尚未开始；当前仅280秒箱沿课程。PUSH、MuJoCo和实机继续暂停。

<a id="record-0029"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hq前脚停滞解除但阶段仍16/32；hr验证后脚地面跟进卸载（2026-10-05 17:35）

hq/residual27302于17:22:52正常结束、returncode0。完整报告SHA256 `e2c8d2eefcff64559eecfcd9964dfe0ed0d8c96f5dc4ff417995fa52733da4f8`，已经完整下载本地并独立流式SHA核验；远端12实际源码、actor/reset/evaluator、32唯一终态/缺失0、全部32密集轨迹共同前缀核验通过。与hp相比，仅env14旧终态改变，其余31终态及旧轨迹字段全程逐值相同；14在51.44秒首次extended生效，同步首次旧字段差异，之前2572条完全相同。**原16条四足登台、两前脚展开、舒展承重路径全部保留；仍16/32，没有新增完整阶段成功。完整原任务0/32。**

第14例原来卡住的FR这次实际抬起并落稳：51.44秒允许超出原3mm微调，实际最大3.908mm，几何拒绝0；55.98秒进入摆动，此前连续10个20ms采样选足力最大4.98446N，卸载稳定计时累积至.2秒；56.02秒实际离地。63.22秒落脚重载后切换RL，前一采样FR力33.828N、reload1、loaded_age.2秒、touch_age.88秒，真实足位约(.83071,-.17079,.22370)m。没有放松原≤5N/.2秒条件，也没有以低压力代替实际迈步。随后RL和RR均迈出地面跟进步，84.18秒起卡在下一次RL准备；尚未完整登台。

**下一个具体障碍是后脚地面跟进的残余载荷。** hq第1例自134.52秒、第14例自84.18秒停在RL/phase0；末10秒选足分别5.707～5.770N（均值5.74247）和6.884～6.953N（均值6.91824）。线速均约.0002m/s、角速约.0016rad/s，三足余量分别29.30/32.46mm、其它三足>8N、卸载进度1、位姿与摆动预检通过、command超限0、未重规划，但现有force trim后脚作用域关闭、值0。1下一落点x=.65210m，14落点x=.39831m，均仍是箱沿混合高度下的后脚地面跟进，不能描述成后脚已登台或重新训练平地行走。3仍是未解决的动态前脚停滞，其它旧失败也未消失。

全32完整质量汇总与hp/hi相同：22超时/2底座/7姿态/1低姿态，三足及以上99.959802%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。汇总未恶化不等于成功率改善。env14原速文件SHA256 `7a4521b36e38b4f569d865fcb768ba69008ddaea97ab6521c349a5e919be1716`，已完整解码7000帧/25fps/280秒，51/56.2/62/75/90/279.96秒六张关键帧审阅支持前脚推进后后脚停滞；这是抽帧核对，不冒充最终全片原速验收。报告、全部来源、三条局部轨迹、事件、前脚真实释放/落脚审计、后脚载荷分析及视频已在本地/远端hq同名目录保存。

确认hq已退出且远端GPU空闲后，`climb-rear-ground-trim-20261005-hr/rear27302`于17:34:31启动，监控PID729394、GPU1；同seed27302/32、箱沿280秒、全部32密集轨迹、主录像14，相同actor/reset/20cm箱。**仅把既有受限force trim增加到“双前脚台面、双后脚地面、当前后脚地面向前步”的近静止残余载荷作用域。** 要求真实其余三足>8N、余量≥.025m、线速<.001/角速<.01、卸载1、原位姿/摆动/关节/命令/重规划检查，且全部条件与选足>5N连续10秒才激活；capture/reset清零。既有8N上限、最多2N/s增长/退回、摆动前1/4五次渐退保持，实际起脚≤5N/.2秒、真实落脚重载、PD/参考限幅/努力/碰撞终止均不变。前脚hq辅助类和原force trim类AST完全相同；未把hr候选控制源码提交为已验证版本。

启动前21项数学/集成检查通过，包含10秒连续性、条件中断重计、低压力后保留平滑控制、局部复位、真实记录1/14通过新分支、位姿/运动/重规划排除、排除平地/台面/后脚上台/前脚、新增evaluator只有两项只读遥测，原接触及轨迹方法AST相同。两例真实受载状态0～8N/33点局部Jacobian预测，最小估计关节余量分别.27993/.26799rad、最小腿primitive净空54.61/31.27mm；这是局部运动学估计，不是动态证明。对hq全32旧轨迹独立扫描，新10秒条件仅1/14达到（估计147.52/97.18秒），旧成功16例均未触发，28最长仅.26秒；采样顺序可能带来一拍差异，真实作用范围仍需hr报告确认。补丁SHA256 `4ec5180b0779cf1b8d2ac0060b90acf81b1a55156573f025f10e312249a61078`；远端12运行源码+actor/reset全部匹配。

下一轮先核对hr进程/status，**不要重复启动**。完成后运行hr/verify.py，比对hq全部32旧字段在rear_active前的共同前缀、未触发环境全程相同、原16条阶段成功及全质量；逐例看1/14真实后脚抬起、落脚承重及后续是否完整登台/展开，不能只看压力下降或某个终止类别减少。若有新增安全失败或原成功路径丢失，不推广。原起点24秒/12秒及最终两组未用种子各32验收未开始；当前280秒箱沿诊断不能充当验收，PUSH/MuJoCo/实机暂停。

<a id="record-0030"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hp完整重跑确认16条路径保留；hq按实测残余载荷验证追加卸载（2026-10-05 16:31）

hp/replay27302于16:19:17正常结束，returncode0，完整报告2586715954字节、SHA256 `838133f1de8ba53b8b757972eadae1d45ffe05ed75533006f9527b513169b677`，已完整本地下载并独立流式SHA核验。远端12实际源码、actor/reset/evaluator、32唯一终态/缺失0、共同前缀和全部终态核验通过；**hp全部32终态与ho恢复终态逐值相同**，确认保存修复未改变物理结果。hi原16例全部保留四足登台、两前脚展开及舒展承重，没有新增完整阶段成功，当前仍16/32；完整原任务0/32。

hp相对hi仅1/14终态改变，30例旧字段相同，已有其它密集轨迹旧字段全程相同；14前1323采样相同、26.46秒首次作用。全部32范围扫描仅1和14有卸载微调，最大分别1.892/3.000mm，几何拒绝均0。1在35.40秒以实测3.371N进入原摆动、35.44秒真实离地、42.12秒落脚重载后换后腿，随后完成多个地面跟进；134.52秒起卡在下一次RL地面步（落点x=.6521,z=.024），最后10秒选足5.707～5.770N，尚未进入后脚登台。3未触发微调，末态线速约.00265m/s、角速.0384rad/s，未达到新微调的近静止门槛，不能说微调修复了3。14达到3mm后仍未抬脚，末10秒5.340～5.383N（均高于原5N条件）。

全32完整质量与hi汇总相同：22超时/2底座/7姿态/1低姿态，三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。这只是本批未恶化，不等于鲁棒性或原起点验收通过。env14录像与ho并非字节相同，已独立完整解码7000帧/25fps/280秒并审阅六张关键帧，持续前脚停滞；视频SHA256 `fc7c20ff98ba253191308e8f76ca117f08516ba2e005139b04a999bac3d3517c`，不冒充最终全片原速验收。

**hq追加调整依据实测力—位移响应，不放松实际起脚条件。** hp第14例0.3～2.8mm微调段625个近静止采样，载荷拟合斜率-430.284N/m、截距6.65028N，残差RMS.011961N、最大.220222N；不参与拟合的3mm稳定平台预测5.35943N、实测5.36241N。外推4.5mm约4.714N，仅是假设，不是物理成功证明。对当前3mm实测受载末态再增加0～1.5mm的16点局部运动学检查，估计受载关节余量最小.123113rad、预测腿部净空6.9896mm、追加关节变化最大.009412rad；真实接触、身体运动和碰撞仍须远端验证。

确认hp已退出且GPU空闲后，`climb-stalled-unload-residual-20261005-hq/residual27302`于16:30:58启动，监控PID726968、GPU1。同seed27302/32、箱沿280秒、全32密集轨迹和主录像14、相同actor/reset/20cm箱。以hp为基线，只给原微调辅助类增加“原3mm上限、全部原eligible条件持续成立且实测仍>5N至少10秒”后才允许上限4.5mm；继续.2mm/s、4N停止增长、原近静止/其余三足>8N/支撑/位姿/摆腿/命令和每步5mm净空/.03rad余量检查。新上限在capture/reset清零前保留，避免摆动时突退；真实抬脚仍≤5N持续.2秒，落脚重载/原PD/参考限幅/碰撞与执行器门禁不变。

StageGuidance整个类AST与hp相同；仅StalledFootUnload内部条件上限与evaluator两项只读遥测改变。26项数学/差分/集成检查通过，包括延后10秒前与hp辅助类逐值一致、作用域外一致、原3mm及新增4.5mm运行时几何分支、低压力/无资格/摆动不升级、局部清零、所有原支撑/真实抬脚/落脚门禁未改；这些不是本地物理仿真。补丁SHA256 `905ffe9c152dff11359979b2e7f71ce40be556363bd6285bb4c9e85ac165f122`。仍使用hp紧凑JSON/先保存终态质量/临时文件完成后发布，墙钟6000秒但仿真仍280秒。候选源码独立保存在仓库外，未推广为已验证控制器。

下一轮先核对hq进程/status，**不要重复启动**。完成后运行已保存verify.py，核对12来源/actor/reset/32唯一终态、完整成功与阶段成功分列、全质量、原16条路径；与hp所有32密集轨迹和终态对比，新增extended首次生效前旧字段必须逐值相同，无extended环境全程应相同。重点看14是否真正卸载/抬脚/落脚重载并继续完整登台，而不是只降至低压力。若出现新增安全失败不能采用；1的后脚残余载荷、3小幅振荡和其它旧失败仍需独立处理，不能把一个前脚修复说成整体完成。原起点24秒/12秒及最终两组未用种子各32验收未开始；PUSH/MuJoCo/实机暂停。

<a id="record-0031"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ho报告保存超时，hp同控制器重跑补齐证据（2026-10-05 15:28）

ho已在日志`EVAL_STEP=14000 completed=32 successes=0`完成全部32回合，但全32密集轨迹的缩进JSON写入触及3000秒墙钟时限。进程于15:24:29结束、returncode -9，报告约2.6GiB处截断，SHA256 `4b2d3254d44e4493626c231841827579abbfdd27f4fe955790e7e53354f8f33a`；**报告不完整，不能按完整评估或质量验收使用。** 终态缺失不是这次故障的原因：已从原文件前缀恢复32个唯一完整终态，但写在轨迹后的质量汇总未保存。原截断报告、错误退出、录像和恢复前缀均保留，未覆盖或伪造returncode0。发现超时风险后尝试暂停看门狗父进程时，内层timeout已经退出；外层runner/monitor已立即恢复，没有留下暂停进程，也没有改变物理控制器。

恢复证据仅支持：与hi相比全部旧终态字段30例相同，仅1和14改变；原16例双前脚展开后的终态全部逐值一致。1由前脚停滞推进至后脚RL/phase0、机身x=.869319m，但仍未完整登台；3仍与hi相同，14达到3mm修正上限后仍停在前脚。未见新增完整展开，不宣称成功率提高，缺失的冲击/支撑/饱和汇总仍需完整重跑确认。`recovered-prefix.json`及`recovered-terminal-comparison.json`已本地归档。主录像env14全解码7000帧/25fps/280秒，26/40/70/140/220/279.96秒抽帧审阅显示持续停滞；SHA256 `64eba5df2742b2462eebf57be981c90dc3b9d5df51bdf540e3aa2be329ef3925`。不是最终全片原速验收。

确认旧评估已退出、GPU空闲后，`climb-stalled-foot-unload-replay-20261005-hp/replay27302`于15:27:56启动，监控PID725531、GPU1。**11份非evaluator源码全部与ho逐字相同，同actor/reset/seed27302/32环境、280秒、全部32密集轨迹、主录像14；没有调整任何物理控制参数。** 只修改评估结束后的保存：先输出含全部终态/来源/成功/质量/执行器指标的`.outcomes.json`（明确dense_report_pending），全量JSON改为紧凑格式，写入`.json.partial`完成关闭后再改名最终报告。评估墙钟6000秒、runner6030秒、monitor6400秒；仿真窗口仍280秒，不能称为延长攀爬时间或24/12秒验收。

保存逻辑6项检查通过：撤回保存块后evaluator完整AST与ho一致；JSON数值/类型无损；先保存32终态；完整报告完成后发布；拒绝覆盖已有报告；NaN导致失败时保留partial而不发布最终文件。序列化补丁SHA256 `1d5cc5ce9dfc0c76e0495af210e749cb29ff4d24233d527414e41f9f3214e5ea`。没有本地物理仿真，也没有把基础设施修复算作策略改善。

下一轮先核对hp进程/status，**不要重复启动**。结束后运行hp已保存`verify.py`：核对来源/actor/reset、32唯一终态与完整质量；与hi比较作用前前缀、全部终态、16条已成功路径；另要求hp全部32终态与ho恢复终态逐值相同，确认此次仅修复保存。之后才据实际受力/新抬脚及失败过程决定下一项控制修正，不能继续盲增足端修正或放松5N/.2秒抬脚条件。最佳已完整验证阶段基线仍hi16/32；原起点两组未用种子各32验收未开始；PUSH/MuJoCo/实机暂停。

<a id="record-0032"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ho验证静止前脚停滞的微量卸载修正（2026-10-05 14:34）

用户要求继续提高鲁棒性。已核对远端无重复训练/评估、GPU空闲；`climb-stalled-foot-unload-20261005-ho/unload27302`于14:34:14启动，监控PID724602、GPU1。**基线改回最佳hi的归档源码和完整280秒配置**，同seed27302/32环境、actor、箱沿复位库和20cm箱；没有继承hj的10N上限、hl保持卸载0、hm减小阻尼或hn目标减速。主录像env14，全部32环境从0秒记录20ms密集轨迹，避免用记录子集推断干预范围。该轮仍是箱沿阶段诊断，不是原起点24秒/12秒验收；完整任务、登台、两前脚展开和舒展承重分别计数。

干预针对hi的1/3/14等静止前脚卸载停滞：原8N修正达到上限、卸载进度1、停滞至少10秒、其余三脚各>8N、支撑余量≥.025m、线速<.001m/s/角速<.01rad/s，以及原位姿/摆腿/关节/命令门禁合格时，允许待抬前脚的世界竖直参考以最多.2mm/s上移，累计最多3mm；实测压力≤4N后停止增加。退出条件时按原小速率退回，真正摆动第一四分之一段按五次曲线渐退；capture/reset清零。每步另查名义/估计受载关节余量≥.03rad及实测关节附近增量预测腿部primitive间隙≥5mm，拒绝时保留原请求并记录。该几何预测不是实际碰撞安全证明，必须评估真实轨迹。

**实际起脚仍要求实测力≤5N持续.2秒；原重新承重、身体路径、规划器、PD、关节速度/加速度/努力和碰撞终止均不放宽。** 这与直接放宽抬脚压力阈值不同：仅产生受限的预卸载参考，是否能卸掉残余压力要由远端物理结果判定。归档源码12份中仅guidance及evaluator改动，10份逐字相同；support_ready/landing_ready/balanced_load_bias等原方法AST相同。候选未进入Git控制代码，仅仓库外独立产物。补丁SHA256 `f65ac50343637426d55c23ed6ea346dba73835330491f3255716f3d34d058310`；远端12实际源码+actor+复位库核验通过。

19项数学/集成检查通过：幅度/速率、10秒等待、4N停止增长、局部复位、摆动渐退、前脚/地面/静止/真实支撑/位姿/摆腿/卸载/重规划作用域排除、范围外q/desired逐值一致，以及实际几何分支接受3mm记录状态和拒绝重叠状态。hi第14例静止尾态0～3mm局部运动学探针：估计受载关节余量最小.126627rad、预测腿部最小间隙7.006mm、最大关节增量.018891rad。这些都是离线数学，没有本地物理仿真或成功证明。

下一轮先查进程/status，**禁止重复启动ho**。结束后在远端运行已保存的`verify.py`，验证12源码/actor/reset、32唯一终态/缺失0、所有32干预范围、hi已有密集轨迹首次作用前共同前缀与所有终态；特别核对hi已有16例是否仍全部完成上台/两前脚展开/舒展承重。不能只用三条目标失败或单个录像宣布改善。仍记录三足支撑、腾空、|vz|、含子步历史单足合力峰、含初始化饱和及新增安全失败；查看真实卸载/抬脚/落脚重载事件和原速视频。最佳已验证阶段结果暂仍hi的16/32，原起点最终两组未用种子各32验收尚未开始；PUSH/MuJoCo/实机暂停。

顺带补完hn诊断：env3在142.26～154秒角速度RMS.253149rad/s，最后20秒.251210rad/s，仍约4.1Hz，低速条件仅37%、卸载最高.04、无后腿起脚。使用记录的真实参考速度和明确关节映射，单步位置复算误差1.192e-7rad、速度5.96e-6rad/s；CPU float32长段回放仍可偏离.025959rad，**不能声称已逐值重建长段控制或证明限幅是唯一根因**。含初始化.380秒饱和定位env27的FR_thigh_joint，hn未记录27密集轨迹，首次发生时刻仍未知。hn视频25fps/4500帧/180秒全解码，6张抽帧已审阅，仍混合高度停滞，不冒充全片原速最终验收；视频SHA256 `01c64972a4b5b18855f1f91b39fd6061506f004e8d9b6365d890c80827ad4760`。分析脚本/数据已同步本地远端；hn不推广。

<a id="record-0033"></a>

来源：AGENT_HANDOFF_CN.md。

## 同批成功与失败占比核对（2026-10-05）

用户询问四类录像占比。四片跨hj/hk/fi/ft版本，不能当作同批失败分布。以当前最佳hi、seed27302、箱沿起点280秒32回合核对全部唯一终态：16例登台+双前脚展开+舒展承重（50%）；前脚卸载停滞1/3/14共3例（9.375%）；后脚推进位姿不通过而超时2/8/13共3例（9.375%）；登台前底座碰撞6/18共2例（6.25%）；姿态终止9/10/16/22/23/26/27共7例（21.875%）；早期低姿态21共1例（3.125%，13.74秒）。无缺失。已登台16例全部完成展开舒展，当前这批上台后调整失败0例。不能把全部碰撞/姿态终止直接归为录像2前脚滑落；录像3为历史fi/env6，hi的低姿态env21不是最后后脚阶段，精确机制分布尚未逐例标注。完整任务仍0/32，以上50%是阶段成功率，非原起点24/12秒验收。可复核分组保存于仓库外`../artifacts/go2-piper/climb-platform-final-recovery-rise-20261005-hi/outcome-distribution.json`，关联原报告SHA256 e21098fa6f803f7fe8a93f4d4c0ea77827dd10e7c3882f62d319172267fbdeaa。

14:21远端复查无Isaac训练/评估进程，GPU无计算进程；hn四条密集轨迹及规划输入已补齐本地，尚未新增物理运行，继续原hn跟踪/受载目标诊断待办。

<a id="record-0034"></a>

来源：AGENT_HANDOFF_CN.md。

## 用户正在查看的四类失败录像（2026-10-05）

对比页：`climb-failure-gallery-20261005/index.html`，本地HTTP进程2196800；完整索引及原片哈希在仓库外`../artifacts/go2-piper/climb-failure-gallery-20261005/cases.json`。页面按原速播放、提供关键段跳转，用户若说“第几个案例”按以下顺序理解：1＝hj/env14前脚卸载停滞（26秒起，可跳270秒）；2＝hk/env3两前脚落稳后后腿转移晃动、157.52秒底座碰撞（137秒起）；3＝历史fi/env6最后后脚未起、低姿态终止（150～160.6秒）；4＝历史ft/env6四脚上台后身体调整失稳（182～190.76秒）。前两例10月5日，后两例10月3日，不能说成同版失败分布；3使用已去除重置尾段的远端首回合原片。四原片哈希与既有核验一致，仅新增本地页面/解码封面，没有新物理评估或录像。页面已请求在Codex浏览器显示。

<a id="record-0035"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新核对：hn仍未解决后腿起脚，且累计饱和增加（2026-10-05）

hn/braking27302于13:43:40正常完成，returncode0，报告SHA256 `1eaa320e4be57b256e4258213c46d05ebfff84b5e6652ba74e760fa9dd162b64`。远端12实际源码/actor/evaluator/复位库、32唯一终态/缺失0核验通过。与hk比较排除新增参考速度/制动开关遥测：3前7113条旧字段相同，142.26秒开始变化；1/28首次差异37.82/30.14秒，14全部9000条旧字段相同。12个终态旧字段相同，20个改变，必须继续按全部32例分析。

**重点失败案例3仍没有迈出后腿。** 两前脚落稳后137.64秒选择RL，至180秒一直phase0；末条选中足46.416N、卸载0，没有新的后腿lift/落脚重载事件。提前减速没有在本短诊断内完成这个修复，不能推广为已验证改进。全32完整任务0/32、缺失0，22超时/1底座/8姿态/1低姿态；三足及以上99.934003%、腾空0、|vz|峰.776772m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.380s（原hk .280s）。底座类别减少不能掩盖累计饱和增加和任务未完成。

当前远端本批评估已退出，没有新训练在运行。报告与遥测正在归档，最终候选没有更换，最佳阶段基线仍hi的16/32上台、双前脚展开并舒展承重；这是箱沿起点/280秒阶段结果，不是原起点24秒慢爬或12秒验收。近期减小身体速度反馈和提前减速两个方向均未解决3，不能继续盲扫同一参数。

下一步使用hn新增的真实参考速度与`reference_joint_ids`，先完成参考限幅的长段一致重建，定位新增.380s饱和的环境/关节及最早偏离；同时检查原支撑转移目标、姿态/重心与实测载荷，区分不合适的受载目标和控制跟踪问题。hn视频尚未完成本轮解码/原速复核，不以单帧宣称稳定改善。完整终态和质量已核验，但新物理修正尚未启动；启动前重新核对远端进程。保留hi路径、原接触/碰撞/执行器/停稳门禁；PUSH/MuJoCo/实机暂停，最终两组未用种子各32的原起点验收未开始。

<a id="record-0036"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hm减小速度反馈使振荡增大；hn验证参考接近目标时提前减速（2026-10-05 13:23）

hm/damping27302于12:45:43正常完成，returncode0，报告SHA256 `f51c867e8775a2f6ca294e50b4f66f692f5609c012dfcc17920e11013278dc95`。12实际源码/actor/evaluator/复位库、32唯一终态/缺失0及本地独立完整SHA核验通过。与hk比较时排除新增mix遥测字段：3前7113条旧字段逐值相同，142.26秒首次mix非零及运动差异；1/28首次差异37.82/30.14秒，14全部9000条旧字段相同、mix0。12个完整终态旧字段相同，20个改变；3由底座终止变超时、27由姿态终止变超时，其余终止类别不变。

**减小外层身体速度反馈的假设未通过物理验证，不沿该参数继续减小，也不推广hm。** 第3例142～154秒角速度RMS由hk的.444445增为hm的.830428rad/s、峰1.398892rad/s，主频约2.08Hz；160～179.98秒RMS.850736rad/s，低速条件满足比例仅7.7%。两前脚仍承重，RL从137.64秒选择后始终phase0，没有后腿lift；末态选中足45.052N、卸载0。第1例仍停于后续RL卸载，180秒末足5.739N>5N；14仍约5.126N停在前脚。避免3原碰撞但晃动更大、任务未完成，不算改善完成。

hm第3例最后20秒策略输出仍恒0，FL/FR髋参考加速度达到15rad/s²原上限的采样比例98.697%/99.098%；目标关节标准差最大.08718rad（hl .04554），实际反馈耦合抵消了此前冻结测量状态的低加速度估计。137.64～179.98秒2118个20ms样本四脚持续接触，1912个未满足低速条件；FK最大2.088e-6m，腿部primitive最小间隙6.585mm、底座包围盒最小间隙44.602mm。几何无该段5mm缺口并不等于受载姿态稳定。

hm全32：完整任务0/32、缺失0，23超时/2底座/6姿态/1低姿态；三足及以上99.945614%、腾空0、|vz|峰.776772m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。仍是180秒短诊断，不能由此宣布hi的280秒16条阶段路径保留。env3录像SHA256 `04afbf6bc720e462be6b975164a2ff60c4a95d3288ca11ee830a18f006b9a8f2`，25fps/4500帧/180秒全解码；138/141/150/157.5/170/179.96秒抽帧已审阅。稀疏抽帧只能显示混合高度停滞，振荡由密集轨迹量化，不当作最终原速录像验收。

接下来检验参考限幅与反馈的耦合，而非继续猜测阻尼数值。原`limit_reference`限制速度/加速度，并在接近关节软限位时减速；接近每个请求目标时则仍用误差除dt作为期望速度，随后才限制加速度。数学对照中从静止到.02rad目标，原函数超调.004rad，新目标距离减速无超调，两者最终都收敛；**不能声称原限幅器对固定目标必然持续振荡。** hm密集记录的单步原公式重建误差1.192e-7rad，但用位置差分推回参考速度后长段自由回放可偏离.2126rad，故不把长段回放当逐值复现，也不将其较小跟踪误差当物理改善。新诊断增加真实参考速度及动作关节索引，便于消除这一重建不确定性。

确认远端无训练/评估且双GPU空闲后，`climb-reference-target-braking-20261005-hn/braking27302`于13:22:44启动，监控PID723664、GPU1。同seed27302/32环境、180秒/9100步、actor/复位库、主录像3及密集1/14/28。**以hk原源码为基线，完整climb_guidance逐字相同，恢复原.08身体速度反馈和全部卸载逻辑；不继承hl保持卸载0或hm减小阻尼。** 只在两前脚台面、两后脚地面、四脚接触、选择后腿地面落点、phase0、参考age≥3秒的准备范围，对腿部参考加入请求目标距离减速；臂参考不启用。范围外使用原算法，正常速度/加速度平滑及原关节界限继续约束进入/退出。

新算法把期望速度幅值再限制为`sqrt(2*a*abs(target-position)+(a*dt)^2)-a*dt`，然后仍经过原2.5rad/s、15rad/s²及软限位制动流程。它只减少期望速度，不提高执行器/关节限制；已有非零速度而目标突变时，可能仍有不可避免的越过目标，不做无条件无超调保证。接触≤5N持续.2秒、落脚重载、原载荷/位姿/碰撞/停稳门禁均保留。hn是独立180秒诊断源码，不是已验证候选，Git分支控制器未变；12份源码9份相同、crawl_gait/stages/evaluator三份诊断改动，补丁SHA256 `899b060ce0265cfd02a9dcdc3df57229caeeb08c61d2b530579a1e3e8f55722a`。

6类数学检查通过：500步默认关闭逐值回归、每关节混合开关范围外逐值回归、1152关节移动目标的原速度/加速度/位置约束、静止小目标超调、带初速度目标反向且仍按原加速度减速并收敛、布尔与张量开关。峰速2.5rad/s、峰加速度15rad/s²（浮点误差2e-15），三份源码编译通过；这些都是数学检查，不是本地物理仿真或成功证明。

下一轮先核对进程/status，禁止重复启动。核对12实际源码/actor/复位库及32唯一终态/缺失0；比较新增braking范围首次生效前所有原字段，14应无范围启用且原字段全程相同。新增`guidance_reference_velocity`为动作关节顺序，使用报告`reference_joint_ids`映射到机器人关节，不能直接猜顺序。重点分析3真实晃动/参考限幅/卸载与起脚落脚承重，完整审计32终态，拒绝以低冲击停滞冒充登台。若短诊断改善，再做同源280秒验证hi已完成16条上台/展开/舒展路径；原起点24秒/12秒及最终两组未用种子验收仍独立。

hm完整报告、全部终态/共同前缀、几何/振荡/参考分析、视频与脚本已本地/远端归档；hn独立保存manifest、补丁、命令、数学测试和启动记录。最佳已完成阶段基线仍hi的16/32上台、双前脚展开并舒展承重，完整任务0/32；原目标、时间、NAV接口、覆盖率与旧动态净空未解决。最终固定候选的原起点两组未用种子各32、每组≥30成功/无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0037"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hl排除卸载是持续振荡的必要条件；hm验证身体速度反馈与参考限幅（2026-10-05 12:25）

hl/hold27302于11:46:56正常完成，returncode0。报告SHA256 `2a8c9ca4bfe33087f231ff2dda82021021d8c2e7e3148cf65926a2721222f090`；实际12源码/actor/evaluator/复位库核对、32唯一终态/缺失0及本地独立完整SHA通过。3的前7041条轨迹与hk逐字段相同，首次干预140.82秒；1/28首次差异分别36.32/28.64秒，14全部9000条相同。25个完整终态改变、7个不变，符合该干预有意影响多例后腿推进的范围；不能当作攀爬候选或保留16路径的证明。

**第3例在卸载始终为0的情况下仍持续约3Hz身体振荡，但到180秒未再滑落碰撞，后腿仍未抬起。** 142～154秒角速度RMS从hk的.444445变为hl的.434680rad/s，160～179.98秒仍.453630rad/s、峰.785013rad/s，低速条件满足比例仅20.9%。139.24～140.80秒、第一次卸载干预之前，两者已逐值相同地振荡（角速RMS.330750rad/s，卸载0）。这排除卸载启停是振荡存在的必要条件；取消启停避免本条在180秒内滑落，说明它可能参与后续恶化，但不能由此声称已确定全部因果或治好攀爬。

hl第3例137.64～179.98秒每20ms几何复算：2118样本、四脚持续接触，FK最大2.313e-6m，腿部primitive最小净空6.585mm、底座包围盒最小间隙44.602mm；1673个样本未满足低速条件。最后20秒最弱足23.136N；加载保持只是诊断，不是目标完成。录像SHA256 `95dd2306716b6e06fba26d950e9bba2967595ba6b0a844a21a3dbb187e57e848`，25fps/4500帧/180秒完整解码，138/141/150/157.5/170/179.96秒抽帧已审阅，未做最终全片原速验收。

**发现身体速度反馈与关节参考限幅相互影响的可检验线索。** hl第3例最后20秒原始策略输出完全不变；FL/FR髋关节参考加速度达到原15rad/s²上限的采样比例分别97.896%/97.495%，至少一个腿关节达到上限的比例99.900%。名义IK关节标准差最大.07879rad，载荷偏置标准差最大.01155rad。离线按实际姿态/速度/锚点复算原身体反馈，按控制前状态→下一条控制后记录对齐，原.08系数的名义IK最大误差3.576e-7rad；同一时刻直接比较会差.0452rad，不能忽略一步时序。冻结测量状态下把外层身体速度反馈系数.08改为.02，名义关节二阶差分峰值39.195→14.200rad/s²、95分位31.889→12.266rad/s²、最大标准差.07881→.03084rad。此处只统计名义IK，未计后续载荷偏置/动态轨迹变化，不保证实际稳定，更不放宽原限幅。

hl全32：完整任务0/32、缺失0，23超时/0底座/8姿态/1低姿态；三足及以上99.923041%、最长腾空.040s、|vz|峰.776772m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.300s（env6、关节索引2）。6和18由原底座终止变为姿态终止，3和9转为超时。**底座碰撞归零不是整体改善：腾空从0增加，饱和从.280增加到.300秒，且后腿推进被主动抑制。** hl永久保持四足载荷方案不推广。

确认远端无训练/评估且双GPU空闲后，`climb-rear-feedback-damping-20261005-hm/damping27302`于12:24:31启动，监控PID722992、GPU1。同seed27302/32环境、180秒/9100步、actor/复位库、主录像3和密集1/14/28。**回到hk原完整卸载逻辑，balanced_load_bias整个函数AST逐字结构相同；未继承hl卸载置0。** 仅在独立诊断源码中，对两前脚台面/两后脚地面、四足接触、选择后腿地面落点、尚未摆腿、参考age≥3秒的准备段，把外层身体速度反馈系数用1秒五次平滑从.08降低到.02，离开范围按同速平缓恢复，episode reset清零。仍保留原位置反馈.5、5cm笛卡尔修正上限、关节PD、2.5rad/s和15rad/s²参考限制、75%努力上限、真实≤5N持续.2秒卸载、落脚重载及碰撞门禁。

hm源码10份与hk相同、1份guidance改动、1份evaluator只增加`guidance_diagnostic_damping_mix`遥测；补丁SHA256 `b38c5a5c6ef6e34f1186af01196b5a05f7475652c7b81ed83704fdeabce30670`，Git分支控制器未改，不当作已验证候选。抽取实际反馈代码的12项作用域/边界/进入退出/局部复位检查通过；系数最大单步变化.002247602，作用域外且无退出渐变时原公式逐值相同，编译通过。新的物理结果尚未产出。

下一轮先查进程/status，禁止重复启动。验证12源码/actor/复位库及32唯一终态/无缺失；比较新增mix首次非零前所有原字段共同前缀，14的原字段应保持一致（新mix字段应0）。重点检查3的3Hz振荡、前髋参考加速度限幅比例、实际卸载/后脚lift/落脚重载以及后续推进，不能以振荡降低或低冲击停滞替代登台。完整审计全部32终态和原安全失败，不只看主录像。hm仍是180秒短诊断，若改善还要在同源280秒批次核验hi已完成16条阶段路径；不可直接声明16保留或24/12秒验收通过。

hl完整报告/终态/共同前缀/几何/频谱及反馈复算/含初始化饱和/录像/脚本已本地与远端归档；hm有独立源码补丁、manifest、命令、测试与启动记录。最佳阶段基线仍hi的16/32上台、双前脚展开及舒展承重，完整任务0/32；原目标、时间、NAV接口、覆盖率与旧动态净空仍未解决。最终原起点两组未用种子各32、每组≥30成功/无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0038"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hk复现前脚落稳后后腿转移失稳；hl隔离卸载反复启停（2026-10-05 11:27）

hk/failure27302于10:41:46正常完成，returncode0。报告SHA256 `5129c6251bd8dcdb76b66168259ba44e060cbeaebb5c3f91d6f12a2708948438`；12源码、actor/evaluator、32唯一终态/缺失0及本地独立流式SHA均通过。14/28各9000条20ms轨迹与hj前180秒逐字段相同，全部11个180秒前安全终态与hj逐值相同，3底座碰撞复现157.52秒。缩短窗口没有改变这些共同前缀；180秒失败诊断不能与280秒登台计数直接比较。

**已定位3失败的动作阶段：两只前脚上台并重新承重之后，第一次RL地面跟进的支撑转移，尚未抬后脚；不是四足上台后前脚展开阶段。** 右前130.34秒实测3.478N完成卸载等待，130.38秒真实抬脚；137.64秒完成落脚重载后选择RL，其落点z=.024m，是地面准备步。约139.24秒开始第二段机身转移，最后目标(.478923,-.077308,.328223)m，142～154秒位置误差约7～9mm，但角速度反复超限。137.64～157.50秒994个20ms样本中819个未满足原低速条件（线速<.05m/s、角速<.2rad/s）；卸载进度最高仅.026667，无后脚lift事件。位姿/摆腿可行、关节/命令、支撑高度等门禁未失败；不能把名义可行解释为实际稳定。

左前157.14秒首次失去实测接触，157.30秒足x退到箱沿.75m之后，157.36秒足z低于.19m；157.52秒base_contact终止。每20ms实测关节/根姿态复建，FK最大2.147e-6m；该段腿部primitive最小净空6.585mm，没有5mm腿部几何缺口，底座包围盒在157.50秒出现-2.224mm重叠，与随后base_contact一致。包围盒重叠不是精确碰撞网格/子步接触证明。仍不能断定微小卸载反复启停是晃动的原因，而不是晃动后的结果。

对照1首轮RL转移33.30～38.08秒240个样本，77个未满足低速条件，卸载能达到1并实际起脚，腿部/底座最小间隙7.259/39.269mm，FK最大2.029e-6m。1随后推进多步，到125.72秒再次选择RL后停滞；180秒末选中足5.735N>5N、卸载1、命令无越限。14仍停在前脚约5.115N。先处理3新增安全失败，不继续增加卸载修正上限或放松真实5N抬脚条件。

hk全32：完整任务0/32、缺失0，21超时/3底座/7姿态/1低姿态；三足及以上99.938759%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。这是180秒统计，不能与280秒比例直接当改善比较。env3录像SHA256 `0f55bdb3de69877dd617feed7b9ef2cacf45e4c980720721ce9ae2e333210c3e`，25fps/3938帧/157.52秒全解码，时长对应该环境终止；30/60/110/150/156/157.44秒抽帧已审阅，末帧采样修正到有效索引，不是最终全片原速验收。

**hl是因果诊断，不能作为新攀爬候选。** 确认远端无训练/评估、双GPU空闲后，`climb-rear-transfer-load-ablation-20261005-hl/hold27302`于11:26:43启动，监控PID722464、GPU1。仍32环境seed27302/180秒/9100步、同actor/复位库、主录像3及密集1/14/28；11份源码完全相同，仅在独立产物源码的balanced_load_bias加入明确标注的诊断干预，Git分支控制器未改。干预只在两前脚台面、两后脚地面、四脚实际接触、选择后腿地面落点且尚未摆腿时，将卸载插值保持0，使用原四足载荷分配；原真实起脚/重新承重、位姿/碰撞/执行器门禁不变。作用域外逐值保留，所有其它模块/类方法AST相同，编译通过。补丁SHA256 `08fed7aecaf988e175ce8671268b32c08af043f5420f2caad74e085b38f7fcf2`，独立manifest记录完整源码哈希和补丁。

离线作用域回放（非物理结果）显示hk中的1/3/28首次非零卸载将分别于36.32/140.82/28.64秒被干预，14无作用；所以**这组会有意阻止其它环境的后腿推进，不要求保留16条完整阶段路径，也不能用较少碰撞/停滞代替攀爬改善**。下一轮先核对进程/status，禁止重复启动；核对3首次干预前轨迹、14全轨迹和全部32终态，分析保持四足载荷后是否仍晃动/前脚滑落/底座碰撞。若仍发生，卸载启停不是该失败的必要条件，回到受载姿态/反馈与足端滑动分析；若改善，仅支持进一步设计连续稳定的载荷转移，后续候选仍必须验证真实卸载和保留hi已完成16例，不能保留永久四足停滞方案。

hk完整报告、核验、密集轨迹、接触滑落事件、几何/门禁分析、录像与脚本已本地/远端归档；hl独立保存命令、补丁、12源码哈希、作用域回放与启动记录。**最佳已完成阶段基线仍hi：16/32四足上台、双前脚展开并舒展承重；完整任务仍0/32。** 原目标/时间、NAV接近接口、覆盖率、旧7/29/15摆动与8转移动态净空未解决；最终固定候选原起点两组未用种子各32、每组≥30成功/无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0039"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hj未增加登台且新增3底座碰撞；hk补录缺失失败轨迹（2026-10-05 10:21）

hj/frontstall27302于10:13:37正常完成，returncode0；报告SHA256 `116ee3533d79d9c54552194d1aaee28b0eaf91f14a4c773b478bb7bc60e0dfbe`，源码/actor/evaluator、32唯一终态/缺失0与本地独立流式SHA通过。**登台/双前脚展开/阶段舒展均仍16/32，无新增完整登台。** 已完成16例的完整终态与hi逐值相同。保留hi作为已完成阶段的基线，hj不算改善完成。

**原“只有14改变”的预期被完整32终态审计否定。** 实际变化为1、3、14，共29个终态不变；21条其它已有密集轨迹所有字段/长度相同，14前1323样本一致、26.46秒开始差异。此前只扫描22条密集轨迹，漏掉了未录密集轨迹的1、3；hi全部32终态中1/3/14都曾处于8N上限且停滞超过10秒。原verifier在“31其它终态相同”断言处正确失败，保留verification.log与scope-audit-failure.json，不抹掉这项失败。**后续作用域评估必须同时审计全部32终态，密集子集未触发不能证明未记录环境不受影响。**

14修正已到10N，但末态选中前脚仍5.115N>5N，phase0、从未抬脚；最后10秒最小载荷5.097N、线速≤.000213m/s/角速≤.001148rad/s、命令越限0。低冲击停滞不能算完成。14在26.44～279.98秒每20ms几何复建FK最大6.983e-7m、最小腿部间隙6.985mm，未发现该段5mm缺口；此结果仅适用于14，不说明新增3碰撞的原因。1从原前脚停滞推进到后脚转移末态（机身x≈.869m、当前腿RL/phase0），但未完整登台；3在157.52秒触发base_contact，当前RL/phase0、机身z≈.271m，不能在缺少过程记录时归因为某个具体碰撞动作。不要继续增加修正上限来试探。

全32汇总：完整任务0/32，21超时/3底座/7姿态/1低姿态（底座比hi多1）；三足及以上99.959026%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。32都有终态，但存在新增安全失败；不能只引用不变的力峰/饱和或保留16例就宣称通过。hj env14录像SHA256 `9f9e50d53740d01ef8ec93962bad487b8ea4301f6d729d89ee79f61e8319e72d`，280秒/25fps/7000帧全解码；26/32/60/100/145/159秒抽帧显示14仍在前脚卸载停滞，无法解释3的失败，亦非最终全片原速验收。

确认远端训练/评估已退出、GPU空闲后，`climb-front-stall-failure-traces-20261005-hk/failure27302`于2026-10-05T10:20:28.048520启动，监控PID721780、GPU1。**控制器仍d551627，12份源码与hj逐字相同，未继续修改控制器或抬脚/执行器门禁。** source记录dd5e0a5（文档提交）；同seed27302/32环境、actor/复位库/所有控制参数，改为180秒/9100步失败诊断，主追踪及录像env3，额外密集追踪1/14/28。180秒覆盖已知3在157.52秒的碰撞，减少无关等待和报告体积；不是280秒完整阶段重复评估，更不是24秒或原起点12秒验收，不能把180秒登台计数与280秒直接比较。

下轮先核对进程/status，禁止重复启动。验证32唯一终态/无缺失、actor/来源/复位库；比较14/28在180秒内的共同轨迹前缀与hj逐值相同，若缩短窗口改变前缀则先处理复现问题。核对3是否同在157.52秒base_contact，结合实际接触力/身体与足位置/参考/关节/力矩定位失败前后变化；同时定位1后脚转移停滞。诊断完成再决定修正，优先保留hi已实现16例路径。

hj完整报告、过程退出状态、独立哈希/来源核验、原范围审计失败、全部终态差异、21轨迹不变证明、32终态停滞检查、14实际几何/录像及脚本已本地远端归档；hk单独保存manifest、完全相同源码、命令/复位库和新采集范围。阶段诊断不算完整任务验收；原目标、时间、NAV接口、覆盖率、旧7/29/15摆动和8转移动态净空仍待解决。最终固定候选的原起点两组未用种子各32、每组≥30成功且无缺失与原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0040"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hi完成16例上台后展开与舒展；hj转向箱沿前脚卸载覆盖率（2026-10-05 09:26）

hi/rise27302于09:09:55正常完成，returncode0。报告SHA256 `e21098fa6f803f7fe8a93f4d4c0ea77827dd10e7c3882f62d319172267fbdeaa`，来源/actor/evaluator、32唯一终态/缺失0和本地独立流式SHA均通过。**16/32四足登台、16/32双前脚展开，16例均达到阶段舒展承重末态，新增第28例。** 阶段判据采用原规划正向x/z参考剩余≤2mm（已越过目标的分量按0）、参考age≥3秒、实测距参考<1cm、四足各≥8N、线速<.025m/s/角速<.1rad/s及命令无越限；不是原任务成功判据，也不要求所有参考逐字等于固定目标。31其它终态和21密集轨迹所有字段/长度与hh完全相同，28前13110个样本一致，262.20秒首次改变，已实现的登台和两前脚展开完整保留。

28最终规划从262.18秒开始，共6段、拒绝0，274.68秒最后一段已将x/z参考设为固定目标；末态参考age5.30秒。末态z=.501157m、固定z目标.503778m，完整位姿平移参考残差3.664mm。最后2秒每20ms记录四足持续接触、最弱足39.288N、最大线速.000386m/s/角速.001718rad/s、命令越限0；最后10秒含末段运动，最大线速.023977m/s/角速.012599rad/s。262.18～279.98秒实际关节/根位姿primitive复建：FK最大2.080e-6m、最小腿部间隙55.720mm，无该段5mm缺口；仍不替代子步碰撞冲量，旧7/29/15摆动与8后续转移的净空不足尚未修复。

全32汇总不变：完整任务0/32、22超时/2底座/7姿态/1低姿态；三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。原目标位置、时间及其它质量条件未达，0/32不等于没有登台。hi env28录像SHA256 `34d7030208048563d8673e49b2184fdea8206f123f71c5433fcce953b5416b4c`，280秒/25fps/7000帧全解码；257/263/267/272/276/279.5秒抽帧审阅显示双前脚展开后机身抬升并保持舒展承重。不是最终全片原速验收。

接下来保留16例已实现路径，提高登台覆盖率。hi第14例箱沿第二只前脚仍在地面，原位姿/摆腿预检合格、其余三脚载荷约54～116N、支撑余量.06646m、命令未越限，但选中前脚实测6.650N高于原5N抬脚条件，卸载修正已经到8N上限。22条轨迹扫描显示只有14连续卸载停滞超过10秒，首次26.44秒；2/8/13虽短暂到8N，停滞最多4.4秒，28也最多4.32秒。

实现`d551627`增加默认关闭`--climb-guidance-front-stall-trim`：仅对前脚仍低于箱面、计划上升>10cm、连续停滞≥10秒的原箱沿卸载作用域，允许修正上限8→10N；保持原2N/s增速、支撑/低速/位姿/摆腿/关节/命令门禁和75%执行器努力上限。修正超过8N后通过原实测卸载等待继续保留较高上限，避免刚降到5N以下就突退；失去条件按原2N/s渐退，摆动仍按原曲线渐退。台面前脚展开、混合高度台面跟进、早期和后脚修正仍限8N。**实际抬脚仍须≤5N持续.2秒，落脚/重新承重与关节参考平滑不变；增加2N修正不直接批准抬脚。**

7项相关测试通过（.137秒）：新作用域及早期/后脚/台面排除、2N/s/10N上限、真实卸载等待中保持、失效渐退和抬脚平滑退出、精确14状态关节/执行器余量、原5N抬脚和旧修正门禁。26.44秒入口及末态分别检查8→10N，新增关节力矩最大绝对值.36818Nm、命令余量≥.12663rad、75%执行器上限余量≥1.0945Nm；只是静态检查，不保证动态卸载成功。关闭新选项后完整controller AST与hi相同，编译/diff通过。

确认远端无其它训练/评估、GPU空闲后，`climb-front-stall-unload-20261005-hj/frontstall27302`于2026-10-05T09:24:55.354030启动，监控PID721195，GPU1，source/controller d551627，12源码3项改变/9项相同。同seed27302/32环境/280秒/14100步、actor/复位库、全部旧控制选项，仅开启front-stall-trim；主追踪/录像改为env14，env28换入额外追踪，仍是同22个密集环境。下轮先查进程/status，禁止重复启动；核对32终态/缺失0、31其它终态/21轨迹及14约26.44秒前前缀，保留16登台/16展开/16舒展，检查14真实卸载/抬脚/上台落脚/重载及后续完整路径，不能把载荷下降或单脚推进当作新增登台成功。

hi完整报告、独立核验、终态/轨迹比较、阶段舒展判据、事件、几何、录像、修正作用域扫描/入口与末态余量及脚本已本地远端归档；hj保存独立manifest/源码/命令/复位库/测试fixture与审计。仍为280秒箱沿参考控制器诊断，不是PPO，不计24秒慢爬或原起点12秒验收。NAV接近接口、原目标位置、时间预算、覆盖率和动态净空仍待解决；最终候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0041"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hh第28例提前展开并抬升；hi验证末段1.5cm受限抬升（2026-10-05 08:23）

hh/settled27302于08:12:35正常完成，returncode0，报告SHA256 `23dfad95721f3c9fbca0235a6bf4ad5d41725d6a48d5da61e55b30ef6e95cbd1`；来源/actor/evaluator、32唯一终态/缺失0及本地独立流式SHA均通过。**仍16/32四足登台、16/32双前脚展开，原15例完成最终姿态；第28例最终姿态尚未完成。** 除28外31个终态和21条密集轨迹所有字段/长度与hg完全相同；28前10937个样本一致，218.74秒首先改变停滞计时，219.74秒新反馈首次非零。没有新增原终止门禁失败。

28在226.24秒进入左前展开；234.72秒实际左前4.57185N通过原卸载等待，234.76秒真实离地，240.02秒落脚重新承重；243.04秒右前转移，251.94秒实际右前3.33251N通过原卸载等待，251.98秒真实离地，**257.12秒完成第二只前脚落脚承重，比hg提前20.04秒**。261.12秒最终保持残差修正启动，262.18秒开始最终机身规划；到279.68秒共8段通过原受载/几何/执行器/停稳条件、拒绝0，各段相隔2.5秒。末态z=.477440m（hg .433489m），固定目标z=.503778m；仍差约26.34mm且第8段尚在执行，不计新增舒展成功。最后10秒四足持续接触、最低载荷34.109N、最大线速.018668m/s/角速.012812rad/s、命令越限0；低速承重与8段计数不能代替固定目标完成。

全32汇总与hg相同：完整任务0/32、22超时/2底座/7姿态/1低姿态；三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。0/32包含原目标位置和时间等条件，不等于没人登台。28改变路径218.74～279.98秒每20ms实际关节/根位姿primitive复建：FK最大2.135e-6m、最小腿部间隙49.949mm，无该段5mm缺口；仍不替代子步碰撞冲量，也不覆盖旧7/29/15摆动与8后续转移的净空问题。

实现`fe5ed51`增加默认关闭`--climb-guidance-platform-final-recovery-rise`，依赖已有settled-recovery。仅当两前脚已真实完成、四足承重并通过原最终调整到位/连续停稳条件，且位姿残差修正已锁定时，最终规划的单段竖直上限从1cm改为1.5cm；未锁定仍1cm，前移上限仍1cm。固定目标、原1.5秒五次插值、参考age≥2秒及连续.5秒等待保持；整段21点载荷/关节/执行器余量和原身体/腿部路径检查仍执行，失败保持原姿态。仅名义参考的竖直峰速上界.01875m/s、前上合成.022535m/s，不当作实测速度保证。目的在同280秒窗口减少收尾分段耗时，不延长窗口或放宽任务门禁。

5项相关测试通过（8.743秒）：实际hh首末规划输入的较高抬升及执行器不足拒绝；显式1cm与旧默认逐值相同；未完成双前脚/未承重/未连续停稳不调整；未锁定1cm、锁定1.5cm且目标不重建；失衡支撑拒绝；原静稳恢复条件保持。hh全部8个规划输入的1.5cm静态预检通过，综合余量最小.142690rad；这不是后续运动的动态保证。关闭新选项后完整controller AST与hh相同，Python编译/diff通过。

确认远端无其它训练/评估进程且GPU空闲，`climb-platform-final-recovery-rise-20261005-hi/rise27302`于**08:22:05启动，监控PID720211、GPU1**。源码/controller fe5ed51，12源码3项改变/9项一致；同seed27302/32环境/280秒/14100步、actor/复位库、22密集轨迹和env28录像，只增加final-recovery-rise。新结果尚未产出。下轮先查进程/status，禁止重复启动；核对32终态/无缺失、31其它终态和21轨迹逐值一致、28至262.18秒首个最终规划前一致，检查16登台/16展开和原15最终姿态保留，28是否实际接近固定目标并承重停稳，不能仅数分段。核对更高分段后的实际速度/接触/力矩/动态净空与录像。

hh录像SHA256 `10e084dd40fd9243ae80633a3d734b92437673fe9e720c532eb991b977d0b079`，280秒/25fps/7000帧全解码；220/235/250/260/270/279.5秒抽帧审阅显示前脚展开后机身抬升，末态未到固定高度，不算最终全片原速验收。完整报告、独立核验、终态/轨迹比较、事件、几何、静态探针、录像核验与脚本已本地远端归档；hi独立保存manifest/源码/命令/测试fixture与审计。

仍为280秒箱沿参考控制器诊断，不是PPO，不计24秒慢爬或原起点12秒验收。原目标、时间预算、NAV接近接口、登台覆盖率与动态净空仍待解决；最终候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0042"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hg正常复现16登台/16展开；hh验证静稳后及时修正与最终姿态（2026-10-05 07:26）

hg/summary27302于07:09:06正常完成，**returncode0**，报告SHA256 `13f98f9ba864cc5177233f05127a0539b1cef492e9737e7e83aee0a97acae6a6`。来源/actor/evaluator、32唯一终态/缺失0、本地独立流式SHA均通过。全部32终态和22条密集轨迹所有字段与hf逐值一致，确认摘要日志改动后正常收尾且控制结果复现；hf原returncode=-9仍保留。**16/32四足登台、16/32双前脚展开，仍只有原15例完成最终机身姿态。** 第28例右前277.16秒落脚重新承重，末态z=.433489m、位置残差10.3726mm，final_started=false、参考age2.84秒。不能将前脚展开计作已完成最终姿态。

全32汇总：原完整任务0/32、22超时/2底座/7姿态/1低姿态；三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。原完整任务包含原目标位置等条件，0/32不等于没有登台；原15舒展末态距离原目标仍.356～.388m，未满足<.20m。已知旧7/29/15摆动与8后续转移动态净空问题仍未解决。

实现`7102c98`增加默认关闭`--climb-guidance-platform-settled-recovery`，只在已有台面保持/前脚展开修正范围内，将最小参考age从10秒改为3秒，并在启动反馈前额外要求实测线速<.001m/s、角速<.01rad/s，继续满足原连续1秒位姿停滞或.5秒卸载停滞。反馈启动后沿用原低速界限.025m/s/.1rad/s，避免自身修正运动导致反复开关。另允许双前脚真实完成后的四足承重保持使用同一受限位姿反馈，处理阻挡最终姿态调整的受载残差。额外增益≤.75、速率.1/s、笛卡尔修正≤5cm，卸载修正≤8N、速率2N/s；原位置1cm/角度.025rad到位、≤5N连续.2秒真实卸载、触地重新承重、关节参考平滑、目标/锚点/PD/碰撞与执行器门禁均保留。仍是先四脚上台停稳、双前脚逐只前移，再最终机身调整。

10项相关数学/作用域测试通过（.629秒），覆盖age不足、尚未静稳、连续等待、反馈启动后保持及超速渐退、支撑/接触/命令排除、精确末态关节余量与旧展开计数。关闭新选项后完整controller AST与cea0b03相同，编译/diff通过。回放hg22条轨迹，只有28存在新增合格样本：218.74秒台面保持、240.16秒前脚卸载、259.54秒展开转移；连续等待后预计约219.72/240.64/260.96秒启动修正。这只是旧输入回放，不是新运动的实测时间。精确hg28末态扫描总比例.5/.75/1/1.25，名义关节余量≥.566346rad、受载命令余量≥.200023rad、笛卡尔修正≤12.644mm、FK<1e-7m、静态名义primitive间隙≥44.130mm；额外8N组合探针仅为假设组合，最终保持并未施加该卸载修正。静态检查不替代远端动态评估。

确认远端无其它训练/评估且GPU空闲后，`climb-platform-settled-recovery-20261005-hh/settled27302`于**07:24:55启动，监控PID719630、GPU1**。source/controller7102c98，12源码3项改变/9项相同；同seed27302/32环境/280秒/14100步、actor/复位库、22条密集轨迹和env28录像，只增加新settled-recovery选项并保留summary-log。**没有延长280秒窗口，新结果尚未产出。** 下轮先查进程/status，禁止重复启动；核对完整32终态/无缺失、31其它终态和21轨迹及28新增反馈前前缀，保留16登台/16展开及原15最终姿态，重点检查28能否完成最终调整与承重停稳、修正是否平缓退出、实际动态几何与全程质量。

hg env28录像SHA256 `4606c50e737923a9c6e9e19912604285e495e9a791a8ac17b83fbb915ad7c03c`，280秒/25fps/7000帧完整解码；264/268/272/275/278/279.5秒抽帧审阅显示前脚前移后承重，但最终机身仍低。录像字节不同于hf，物理轨迹逐值相同；不算最终全片原速验收。hg完整报告/验证/终态与轨迹比较/录像核验/回放/静态余量及脚本已本地远端归档，hh独立保存manifest、源码、命令、复位库、测试fixture/日志与审计。

以上仍为280秒箱沿参考控制器诊断，不是PPO，不计24秒慢爬或原起点12秒验收。原目标、时间预算、NAV接近接口、覆盖率与动态摆腿净空仍待解决；固定候选后的原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0043"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hf完整记录显示16例双前脚展开，收尾异常退出；hg以摘要日志复核（2026-10-05 06:22）

hf/transfer27302在约50分钟墙钟时限收尾阶段被终止，监控于06:13:29记录**returncode=-9**。保留异常状态，不改写成正常完成。此前完整JSON已写出，SHA256 `3ffbadb0e0848ad32497a35fb10a7d735afd651df84eaf01fdd2e52d9dc77347`；远端完整解析、来源/actor/evaluator及32唯一终态/缺失0检查通过，本地完整同步后的独立流式SHA一致。录像亦全量可解码。旧日志约2GB，末尾截在重复打印的密集轨迹JSON中途；源码是在完整报告落盘后再次json.dumps整个报告到stdout，再关闭环境。此证据支持处理重复大日志这一收尾风险，但不把异常退出当作正常验收。

**完整物理记录显示登台16/32，双前脚展开从15/32增为16/32**，新增第28例；原15例及其它31个终态、21条密集轨迹所有字段/长度与he完全相同。28前13326样本一致，266.52秒开始新反馈停滞计时；267.52秒额外反馈首次非零，268.94秒位置误差降至9.607mm并开始原右前卸载修正，反馈峰值.446001。271.98秒右前实测3.32325N、原卸载计时.21999997秒后phase>0；272.02秒真实右前力降至0、lifted=true；277.16秒落脚重新承重，右前42.9795N、reload1.0、loaded_age.21999997秒，展开完成计数2。右前卸载力修正峰5.9782N，仍低于原8N上限。不是计时器直接加成功数，也没有放宽1cm到位或5N抬脚门槛。

**第28例还没有完成最后机身姿态调整。** 末态四足承重、机身z=.433489m，位置残差10.3726mm仍大于最后调整前原1cm条件；姿态残差.011260rad，final_started=false、final_segments0，参考age仅2.84秒，尚无age3秒最终姿态输入。最后2秒四足持续接触，最小载荷28.2948N、线速≤.017356m/s、角速≤.028202rad/s、命令越限0。不能把这一短承重段冒充原15例已经达到的舒展末态，也不能断言只要延长时间就能通过。下一步需在280秒内处理保持残差和动作耗时，不延长窗口来宣称完成。

233.22～279.98秒逐20ms实际关节/根位姿及同USD primitive复建：FK最大误差2.061e-6m、最小腿部间隙49.957mm，无该新增台面路径的5mm缺口；仍不替代物理子步碰撞冲量，不覆盖旧7/29/15摆动与8后续转移已知净空不足。全32汇总仍22超时/2底座/7姿态/1低姿态，三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s；原完整任务0/32，包括原目标和时间条件，不等于没有登台。

实现`cac03e7`只给evaluator增加默认关闭`--summary-log`，完整JSON写入器、全部物理控制、轨迹与指标内容保持；启用时stdout仅打印任务/种子/回合计数/缺失/终止/来源哈希/完整报告路径，避免再次序列化和打印多GB轨迹。移除新CLI参数并还原旧打印分支后，整个evaluator AST与hf一致；实际摘要分支以不可序列化的密集轨迹占位对象执行通过，证明未遍历轨迹并保留选定计数和报告路径。Python编译/diff通过。没有改actor、PD、关节参考、目标、碰撞/支撑/到位/停稳门槛，未重跑无关控制数学测试。

确认hf进程已退出、无其它Isaac训练/评估进程、GPU空闲后，`climb-platform-summary-log-20261005-hg/summary27302`于06:20:08启动，监控PID719034、GPU1。源码cac03e7，**controller仍2d8835d**，12份源码仅evaluator改变，11份逐字一致。同seed27302/32环境/280秒/14100步、actor/复位库、全部控制参数、22密集轨迹/env28录像；仅增加summary-log，3000秒运行时限和280秒仿真窗口均不变。此轮用于异常退出后的正常收尾与同控制器复现确认，不是另一次控制优化。下一轮先查进程/status，禁止重复启动；要求returncode0、完整报告/无缺失、**全部32终态和22条轨迹与hf逐值相同**，核验16登台/16展开以及28最后机身尚未调整的限制。不要再tail包含单行多GB JSON的旧日志；读取旧日志末尾用固定字节seek。

hf env28录像SHA256 `a0b28665e30a8c0c24602ca456d1ec1a94bcd1ca89a0de4f7be7f70de681203b`，280秒/25fps/7000帧全解码，264/268/272/275/278/279.5秒抽帧审阅显示右前脚前移、落脚和末段四足承重；最终机身尚未调整，不当作完整成功录像或最终全片原速验收。hf的完整报告/异常status/独立验证/终态与轨迹比较/事件/末段/transfer-tracking-analysis/实际几何/录像核验及脚本本地与远端归档；hg保存独立manifest/源码/命令/复位库/日志审计，更新指定feature/go2-piper-sim2real分支。

当前仍为280秒箱沿参考控制器诊断，不是PPO，不计24秒慢爬或原起点12秒验收。原目标位置、时间预算、NAV接近接口、登台覆盖率、末态舒展与动态摆腿净空仍待解决；最终候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0044"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：he第28例左前脚真实展开，右前受载残差待修正；hf已启动（2026-10-05 05:24）

he/unload27302于05:10:30正常完成，报告SHA256 `2cdf943718f6cbf92ab000feeb152358fd0d8164e88f1fdac2fcd8ad428a5f28`，完整同步本地后独立流式SHA一致，控制源码/actor/evaluator通过；32唯一终态、缺失0。**实际登台仍16/32、两前脚完整展开仍15/32。** 原15例保留，28新增完成左前脚一步，尚未完成右前脚；不能把这一局部推进计作新增完整展开成功。其余31个终态和21条密集轨迹全部字段/长度与hd完全相同。28前12334样本一致，246.68秒首次区别仅开始新的卸载停滞计时；实际力修正247.16秒启动。

28在248.20秒测得左前4.56242N、原卸载计时.21999997秒后phase>0；248.24秒实际左前接触力降至0、lifted=true，修正峰值仅1.94947N（远低于8N上限）。253.52秒完成真实落脚和重新承重，左前42.602N、reload1.0、loaded_age.21999997秒，展开计数变1。256.54秒进入右前脚转移。末态右前6.163N、支撑余量.037963m、姿态与摆腿预检可行、命令未越限，但机身位置残差10.6046mm、角度残差.011155rad；**位置仍略高于原卸载修正作用域1cm，故右前trim一直0，尚未抬脚。** 最后10秒四足持续接触、最低载荷6.126N、线速≤.000213m/s、角速≤.001310rad/s，不是任务完成。

对改变后的233.22～279.98秒路径，逐20ms用实际关节/根位姿及同USD primitive复建，FK最大误差2.061e-6m、最小腿部几何间隙49.957mm，未发现该新增台面动作的5mm间隙缺口；不替代物理子步碰撞冲量，也不覆盖既有7/29/15摆动及8后续转移的未修复几何问题。全32汇总与hd一致：22超时/2底座/7姿态/1低姿态，三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。原完整任务仍0/32，包括原位置/时间门禁，不等于无人登台。

实现`2d8835d`增加默认关闭`--climb-guidance-platform-extension-tracking`。对已登台、前脚展开转移中phase0、age≥10秒、四足接触、其余三脚>8N、实际支撑余量≥.025m、卸载分配已完成、姿态/摆腿/关节/命令合格且低速的状态，复用原PlatformHoldTracking缓慢修正受载位姿残差。仅在原修正范围位置<2cm/角度<.05rad且尚未满足原1cm/.025rad到位条件、连续1秒时启动；初次需选中脚仍>5N，锁定后保留到实际卸载等待结束。沿用额外反馈上限.75、增减速率.1/s、原5cm笛卡尔上限和PD/关节参考限制，抬脚或范围失效时渐退。**卸载修正仍要求原1cm/.025rad，真实抬脚仍要求≤5N连续.2秒；目标、锚点、落脚/重载、先两前脚后最终机身调整的次序均不变。** 2cm/.05只允许误差修正，不能直接批准抬脚。

8项相关测试通过（.436秒、exit0）：精确he28状态触发与支撑/速度/姿态/路径/关节/早期/已卸载等排除，未到1cm时原trim仍拒绝、到位后可进入原trim，反馈通过卸载等待保持且抬脚后渐退；新旧保持上限/速率、原展开停稳与落脚计数及静态关节余量均覆盖。关闭新选项并还原默认函数参数后，完整controller AST与he完全相同；Python编译/diff通过。流式回放22条he轨迹，只有28右前转移满足新增停滞条件，266.52秒开始合格、预计约267.5秒开始反馈；其余21条均无合格样本。精确he28冻结状态扫描总比例.5/.75/1/1.25，并叠加最大8N右前卸载修正：命令余量最小.108505rad、执行器75%上限余量最小3.60288Nm、笛卡尔修正最大12.254mm、FK<1e-7m；原比例重建名义关节误差1.46e-5rad。这些是静态检查，不保证反馈后的真实负载或动态稳定性。

确认he结束、无其它Isaac训练/评估进程且GPU空闲后，`climb-platform-extension-tracking-20261005-hf/transfer27302`于05:23:14启动，监控PID718281、GPU1，source2d8835d。相同seed27302/32环境/280秒/14100步、actor/复位库/22密集轨迹/env28录像及全部旧控制选项，仅开启platform-extension-tracking；12源码中3项变化、9项不变。下一轮先查进程/status，禁止重复启动。核验32终态/缺失0、31其它终态和21轨迹及28新增反馈前前缀；检查右前位置误差真实收敛、力修正和增益渐退耦合、真实卸载/抬脚/落脚/重载、两前脚完成及最终停稳。280秒诊断剩余时间有限，未完成就照实记录，不能继续延长窗口冒充改善完成；现在仍只确认16登台/15完整展开。

he env28录像SHA256 `048dbf5f1f3459d9056c061e71eaab4d762ae7af0628452b33dc1b56be77b596`，280秒/25fps/7000帧全解码，245/250/256/264/273/279.5秒抽帧审阅显示左前展开、承重后右前转移停滞；不是完整成功录像或最终全片原速验收。he完整报告、verification、终态/轨迹差异、事件与末段、精确输入、extension-unload-analysis、实际几何、增益/卸载组合检查、作用域回放、视频核验及脚本已在本地和远端归档；hf独立保存manifest/源码/命令/复位库/相关测试fixture和审计，更新指定feature/go2-piper-sim2real分支。

以上均为280秒箱沿参考控制器诊断，不是PPO，不计24秒慢爬或原起点12秒验收。原目标位置、时间预算、NAV接近接口、登台覆盖率与动态摆腿净空仍待解决；最终候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0045"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hd解锁第28例展开前支撑转移；he验证真实前脚卸载（2026-10-05 04:24）

hd/bound27302于04:09:50正常完成，报告SHA256 `032d13c38deca7732bdfa861e1e718df58306edddcad3a490c36970a32f2c3ab`，完整同步本地后独立流式SHA一致，控制源码/actor/evaluator通过；32唯一终态、缺失0。**实际登台16/32、完成两前脚展开15/32，仍未新增成功。** 与hc比较，除28外31个终态和21条密集轨迹全部字段/长度完全相同；28前11585样本一致，首次不同231.70秒，正是原额外增益.5上限处。全回合终止仍22超时/2底座/7姿态/1低姿态，原完整任务0/32；不能把完整0说成未登台。

28这次通过了原位置1cm/角度.025rad/倾角/低速/有效关节与命令门禁，原连续到位计时从232.20秒开始，233.20秒记录.99999958秒，233.22秒原release正常开启左前展开支撑转移。没有通过放宽阈值或重置误差允许迈步。额外保持反馈实际峰值仅.649999，尚未达到.75上限即退出保持并按原速率渐退；保持期间无下降/反复锁定，最弱足载仍≥8.27685N。

**新的停滞发生在左前脚真实卸载，尚未抬脚。** 支撑转移后机身升到约.457m且接近水平，末态姿态/摆动预检均可行，支撑余量.035499m、卸载参考已到1.0、命令越限0，但左前实测5.542N仍高于原5N抬脚条件，phase0、lifted=false、两前脚完成数0。末10秒四足接触，最弱足载5.5205N，线速≤.000325m/s、角速≤.001203rad/s。保持结束后的整个支撑转移最大线速.168145m/s/角速.331330rad/s，不能将最后10秒低速替代全过程速度；这也是阶段诊断，非自然慢爬完整达标。

全32汇总仍三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，与hc相同。旧7/29/15摆动及8后续转移实际几何余量缺口尚未修复；此汇总不构成全过程碰撞达标证明。hd env28录像SHA256 `fe6a1fd4786aeaee5870be53466e742a2e679b57075f91c4b193de44ad761e3b`，280秒/25fps/7000帧完整解码，228/238/248/258/270/279.5秒抽帧审阅显示机身抬升后支撑转移停滞、前脚未迈出；不当作成功录像或最终全片原速验收。

实现`4096377`添加默认关闭`--climb-guidance-platform-extension-force-trim`，把原受限卸载反馈应用到**四足已登台、正在前脚展开、参考age≥10秒且跟踪到位**的停滞。脚仍在原台面范围、其余三脚接触，前脚计划同高度向前2～8cm；沿用原支撑余量≥.025m、其余三脚实测>8N、低速、姿态/摆腿预检、有效关节/命令未越限等条件。复用原UnloadForceTrim：实测>5N连续.5秒后以最多2N/s增加、上限8N、目标3N；条件失效等待时渐退，摆动中按原曲线退出。原**实测≤5N且连续.2秒**抬脚门槛不变，触地/重载/关节参考平滑/两前脚完成后才最终调整的次序不变。未修改已实现登台的控制范围。

6项相关测试通过（.148秒、exit0），包括精确hd28状态的作用域及排除情况、8N最大修正下关节与执行器余量、原实测卸载门槛、渐增/上限/失效渐退、向上虚功方向、原展开停稳和落脚计数。以关闭新选项重建完整controller AST，与hd逐项一致；Python编译/diff检查通过。流式回放22条hd密集轨迹，只有28满足新作用域，首次合格246.68秒、连续停滞.5秒预计247.16秒开始修正，其余21条均无合格样本。回放和冻结状态余量检查不是动态负载/碰撞保证，物理结果仍需核对31其它终态与21轨迹及全部质量。

确认远端hd结束、无其它Isaac训练/评估进程且GPU空闲后，`climb-platform-extension-unload-20261005-he/unload27302`于04:22:08启动，监控PID717548、GPU1。source4096377；同seed27302/32环境/280秒/14100步、actor/复位库/22密集轨迹/env28录像、保持增益上限.75和全部旧控制选项，仅打开新platform-extension-force-trim；12源码中3项变化、9项不变。下一轮先查进程/status，禁止重复启动。先核验32终态/缺失0、31其它终态/21轨迹和28新修正前前缀，检查实际卸载、真实抬脚/落脚/重新承重、两前脚完成与最终停稳；若280秒内未完成则照实记未完成，不继续拉长时间以宣称成功。当前只有16登台/15展开已确认。

hd完整报告/verification/终态与轨迹差异/22环境事件和末段数据/输入fixture/hold-tracking-analysis/extension-scope-replay/录像核验与分析脚本在本地和远端归档；he独立保存manifest/源码/命令/复位库/测试fixture与AST审计，更新指定feature/go2-piper-sim2real分支。保持280秒箱沿参考控制器诊断标签，不是PPO，不计24秒慢爬或原起点12秒验收。原目标位置、时间预算、NAV接近接口、登台覆盖率与动态净空仍待解决；最终候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0046"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hc降低保持误差但未解锁展开；hd仅调整受限反馈上限（2026-10-05 03:23）

hc/tracking27302于02:13:27正常完成，报告SHA256 `baa1ec9209c3cb15582ce166024aeb48cdabeae4db2bdebb5fc55cf682d95db5`；本地完整同步后独立流式SHA一致，源码/actor/evaluator通过，32唯一终态、缺失0。**登台仍16/32、前脚展开仍15/32，没有增加成功。** 除28外31个终态的全部旧字段和21条密集轨迹的原字段/长度与hb完全相同；28原字段首次不同226.72秒，之前11336样本完全相同，恰为新增反馈第一次非零。原15例展开/停稳成果保留，完整原任务仍0/32。

28的额外反馈从226.72秒开始，以.1/s增到231.70秒的.5上限；229.20秒在extra=.25时原水平化逻辑又完成一次可行capture，段数2→3。原到位位置/角度/倾角条件曾匹配80个离散样本，但展开的原连续等待最长仅.400000秒，未达1秒；不能把累计1.6秒散点说成已经停稳通过。最终位置误差8.612mm、角度误差.025115rad，前者已低于1cm，后者仍略高于原.025rad；两前脚展开完成数仍0。此次物理结果只支持反馈减小了误差，未证明展开改善完成。

新增反馈后28最弱足载荷曾到8.27685N、最大线速.021383m/s、角速.090685rad/s、命令越限0；最后10秒四足持续接触，最小足载10.9885N、线速≤.000216m/s、角速≤.000676rad/s。载荷余量接近反馈的8N保护条件，下一步不能只看误差减小而忽略支撑减弱或反馈反复增减。全32统计保持22超时/2底座/7姿态/1低姿态、三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。此前7/29/15摆动与8后续转移的实际几何缺口仍未解决；该统计不作完整碰撞达标证明。

在hc28当前实际状态/旧目标/载荷力矩上重算总比例1.0/1.1/1.25：名义关节余量最小.243782rad、载荷命令余量.411002rad、FK误差<1e-7m、笛卡尔修正最大7.952mm，仍远低于原5cm上限。这是冻结状态的命令余量，不能预测真实增益变化后的接触载荷、动态稳定性或全过程净空。

实现`b5a21f4`增加显式`--climb-guidance-platform-hold-tracking-max-extra`，默认保持.5、参数硬上限.75，非默认参数必须启用原hold-tracking选项。hd仅使用.75（总比例最多1.25），以原+.1/s缓增、-.1/s渐退，所有原触发范围/载荷≥8N/低速/参考age10秒+连续1秒/目标位姿/位置1cm与姿态.025rad/原展开连续1秒/支撑转移/落脚重载/关节参考限速与PD不变。不是把角度门槛加一个浮点容差绕过到位。

4项相关测试通过（.179秒）：显式.5与默认逐步输出完全相同、.75上限/原速率、无效参数拒绝；原保持触发/到位等待时锁定反馈/退出渐退/实际支撑速度排除；hb及hc精确状态的关节/命令/FK与碰撞近似复核。此前hc完整71项已过，此处未重跑无关数学检查。用默认.5还原新增参数后完整控制AST与fb05180相同，Python编译/diff通过。

确认hc完成且远端无训练/评估进程、GPU1空闲后，`climb-platform-hold-bound-20261005-hd/bound27302`于03:21:08启动，监控PID716693、GPU1。相同seed27302/32环境/280秒/14100步、actor/复位库、22密集轨迹和env28录像，仅添加max-extra=.75；源码12项中3项变化、9项保持。下一轮先查进程/status，不重复启动；核对31其它终态/21轨迹不变、28在原.5上限之前前缀不变。重点检查是否真实满足原连续到位条件并完成前脚展开，弱足载荷是否逼近8N触发渐退/振荡，实际卸载/触地重载和末态；对照全部安全质量。保持16登台/15已有展开与缺失0为回归要求，不以更小误差或长期四足停滞冒充成功。

hc env28录像SHA256 `14bf30de4439b5eb8ffb5b6cf864e1017e5585c6fa4bb0d8aef762f58fdabdbb`，280秒/25fps/7000帧全解码，218/228/238/250/265/279.5秒抽帧审阅仍为台面低姿态保持，前脚没有展开；不是成功录像或最终全片原速验收。报告、verification、terminal/trace差异、22环境事件与末段样本、hold-tracking-analysis（含原连续到位等待峰值）、精确输入、gain-probe、视频核验及脚本本地/远端归档；hd独立保存manifest/源码/命令/复位库/相关fixture与测试/AST审计。同步feature/go2-piper-sim2real。

当前仍是280秒箱沿参考控制器诊断，不是PPO，不计240秒、24秒慢爬或原起点12秒验收。原目标位置、时间预算、NAV接近接口、覆盖率及动态摆腿净空仍待解决；最终候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0047"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：hb确认15例展开后连续停稳；hc保持门槛验证台面受载误差反馈（2026-10-05 01:26）

hb/held27302于01:09:57正常完成，报告SHA256 `c74c1b498146109a3db231b4e7ba354d7afc6973eea2c46a5baa6e0d34e0a67e`；完整同步本地后独立流式SHA相同。源码/actor/evaluator核验通过；32唯一终态、缺失0，**全部终态和原有19条密集轨迹的所有字段/长度与ha逐值一致**。真实登台仍16/32、前脚展开仍15/32，原完整任务仍0/32；不是新增成功或完整验收。新增5/24/30密集轨迹确认最后10秒四足持续接触，最小足载分别37.636/46.307/51.047N、最大线速.000286/.000346/.000335m/s、角速≤.001342rad/s、指令越限0。至此15个展开回合都有连续末段停稳证据：整体最小足载37.636N，最大线速.0003462m/s、角速.001746rad/s。保留前述部分摆动时实际几何余量不足的限制，末态停稳不等于全过程达标。

全回合仍22超时/2底座/7姿态/1低姿态、三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，与ha一致。ha已明确的7/29/15摆动间隙缺口和8后续支撑转移缺口未由此次只读采集解决。目标中心距离、耗时、NAV接近接口及覆盖率仍未达标。

新preextension采集只有env28触发；其他环境均没有“台面保持、未展开完、age≥3秒、四足接触低速、关节有效且指令未越限”的有效记录。28在218.74/225.72/235.72秒、参考age3.02/10.00/20.00秒分别记录位置残差10.814/10.640/10.640mm、姿态残差.030140/.029540/.029524rad；最弱后足载荷14.236/14.291/14.389N。参考段数一直2，说明这是稳定受载偏差，并非尚在移动或多等几秒即可到位。原展开前1cm/.025rad跟踪门槛继续保留，没有直接重捕获来“清零”误差。

实现`9a943d5`新增默认关闭`--climb-guidance-platform-hold-tracking`。仅四足都在原台面范围、platform_hold、前脚尚未展开完且extension不运动、各足实测≥8N、位姿预检可行、关节有效/命令未越限、线速<.025m/s和角速<.1rad/s时，允许诊断反馈。参考age≥10秒，位置误差<2cm且姿态误差<.05rad但仍不满足原1cm/.025rad到位条件，连续1秒后，把**现有笛卡尔姿态误差反馈**以每秒最多.1缓慢增加，额外上限.5（原比例.5，最多到1.0）。到位后保持这项反馈以完成原1秒停稳等待；退出合格保持范围后以同速渐退。目标位姿/锚点不改，原5cm笛卡尔修正上限、腿PD30、冻结actor、关节参考速度/加速度限制、全部原到位/释放/真实落脚/重载/最终停稳门禁均不改。它不会用自身计时直接允许抬脚；StageClimbAction控制逻辑原样保留。

71项数学与门禁测试通过（57.657秒、exit0）。新增覆盖10秒+1秒等待、增量≤.5/速率≤.1每秒、到位等待时保持反馈、范围退出渐退、reset及实际四足载荷/速度/已完成/命令越限排除；精确hb28末态重建原比例.5名义关节与运行值误差<5e-5rad。在同一冻结实际状态、负载力矩下扫描比例.5/.6/.75/1.0，名义关节余量最小.226rad、载荷命令余量.391rad，FK误差<1e-7m、笛卡尔修正最大约7.963mm，未碰到原5cm上限。这里仅是局部静态命令余量检查，不能当作动态稳定性或全过程碰撞证明。关闭新选项后，去除新增状态/helper/flag分支，完整控制AST与3692556相同；Python编译/diff通过。

确认hb完成且远端无训练/评估进程、GPU1空闲后，`climb-platform-hold-tracking-20261005-hc/tracking27302`于01:24:47启动，监控PID716125、GPU1。相同seed27302/32环境/280秒/14100步、actor/复位库、22密集环境及全部既有控制开关，仅打开新hold-tracking；录像env28。12份源码中3份变化，9份保持。预审依据hb只env28出现合格保持输入，预计其它31回合不触发，仍必须物理核对。下一轮先查进程/status，不重复启动：要求其余31终态与21共同轨迹原字段不变，28首个实际增益前前缀不变；记录增益触发、原到位条件真实达成、原1秒等待、支撑转移/实际卸载/触地重载/两前脚展开与末态。比较16登台/原15展开是否保留及28是否恢复，同时核对32终态/全部质量。当前仍在运行，未宣称修复成功。

hb env0新成功示例录像SHA256 `10e485c7c7d473694a284e75a981d1462c2d68535cfdd3603492c185b356031b`，280秒/25fps/7000帧全解码；80/130/180/220/250/279.5秒抽帧已审阅，看到了后脚跟进、四足登台、前脚展开后站姿保持。仅为阶段诊断录像/抽帧审阅，非最终全片原速验收。完整报告、只读输入、terminal/trace比较、22环境事件与末段样本、录像验证、hold-gain-probe及脚本本地/远端归档；hc冻结源码/manifest/命令/复位库/测试fixture与AST审计独立保存，结果同步feature/go2-piper-sim2real。

仍为280秒箱沿参考控制器诊断，不是PPO，不计240秒、24秒慢爬或原起点12秒验收。最终冻结候选原起点两组未用种子各32、每组≥30成功且无缺失与原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0048"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ha登台16/32、展开15/32；hb补采展开前受载残差与新增成功录像（2026-10-05 00:23）

ha/preview27302于10月4日23:19:38正常结束，报告SHA256 `603ad8e9473eceb77f1327af7af5709e73282dc754581af0b07517f48e177ae4`。完整报告已同步本地并单独流式SHA核验一致；源码/actor/evaluator通过，32唯一终态、缺失0。**真实四脚登台从8/32增到16/32，两前脚展开从8/32增到15/32，原8例均保留。** 新登台0/5/15/17/19/24/28/30，除28外其余7例完成两前脚展开。原八例的最终阶段成果保留，不等于全过程参考/轨迹逐值不变；19条共同轨迹中18/14/26完全相同，其余首次不同在60.84～77.52秒各自前脚跟步捕获后。13个终态与gz完全相同，没有新增原安全终止。

15个已展开终态机身高.500927～.504756m、距原中心.356399～.387639m；完整原任务仍0/32（包含原目标位置及耗时），不能把完整0说成没有登台，也不撤原位置/碰撞/执行器/最终停稳门禁。已有密集轨迹覆盖其中12例0/4/7/11/12/15/17/19/20/25/29/31：最后10秒全部四足接触，最小足载39.092N、最大线速.0003443m/s、角速.001746rad/s、指令越限0。5/24/30本轮只有终态和全回合摘要，不能据单点宣称同样持续停稳；hb补齐三者密集轨迹。

全32回合终止仍22超时/2底座/7姿态/1低姿态；三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足接触合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，与gz相同。**这些汇总不代表所有实际几何余量均达标。** 50秒后按0.1秒抽样、使用实际关节/根位姿和同USD primitive重建，最大FK误差2.166e-6m；7/29左前小腿首次低于5mm在70.8秒、15在71.5秒的前脚摆动中，最小间隙近零。8在98.7秒后续转移时也低于5mm。2/13/28在该抽样窗口最小约5.114/5.294/5.394mm。未采样时刻和缺少密集轨迹的回合不作完整几何保证，近零primitive间隙不直接等于真实碰撞冲量。

实际抬脚前输入的完整摆动+15mm虚拟触地探测重算：7/29/15左前实际位姿名义间隙9.108/9.441/15.566mm，之后仍在运动中下降到5mm以下，说明仅增加静态10mm名义余量不足以覆盖整段受载姿态变化。2/8/13/28左前同口径约33.221/33.297/32.515/32.415mm，确实改善了原低间隙前步；但2/13随后卡在后地面脚支撑转移、8后续转移又损失净空。不要再把所有停滞归为前脚卸载力不足，也不要盲加静态余量替代动态路径检查。

28已在211.70秒进入四足台面保持，最后10秒四足承重最小14.274N、最大线速.000102m/s、角速.000518rad/s、指令越限0；它尚未开始前脚展开。末态实际与旧参考位置差10.637mm、姿态差.02954rad，超过展开前原内部1cm/.025rad到位条件；gravity_z=-.940579，已满足展开倾角条件且不再触发前两步前的额外水平化。因此保持稳定却卡在旧参考到位检查。当前没有放宽检查或直接重置参考；需要精确COM/重力/偏置/关节限制和承重状态，验证如何连续衔接新的支撑转移。

实现`6e11b1a`只读增加`climb_platform_preextension_inputs`，在台面保持、尚未展开完、四足接触、低速、有效关节且指令未越限时，记录参考age3/10/20秒的实际位姿、足点、COM/重力、质量/力矩限制、旧参考与偏置、各足载荷及到位残差。与原已展开最终姿态记录分开保存，原采集逻辑默认不变；所有新记录按真实终态过滤。移除新增字典/采集调用并还原只读记录方法后，控制AST与9e68b1e一致；实际evaluator过滤块执行230s有效/281s晚到、280s终态fixture通过。Python编译/diff通过；未为只读采集重跑不受影响的68项数学检查。

确认ha完成、无Isaac评估/训练进程、GPU1空闲后，`climb-platform-preextension-inputs-20261005-hb/held27302`于00:21:42启动，监控PID715562、GPU1；controller仍fd8d8b7，seed27302/32环境/280秒/14100步、actor/复位库和全部控制开关不变。19条原密集轨迹保留，再加5/24/30；录像选新增登台展开的env0。下一轮先查进程/status，不重复启动；要求32终态和19条共享轨迹全字段/长度与ha一致，核验16登台/15展开及全部质量。优先用28精确保持输入重放连续展开衔接，保留已实现登台与先两前脚展开再最终调整的顺序；另跟进7/29/15摆动中的动态间隙缺口，不把此批提升晋升为完整达标候选。

ha env2录像SHA256 `6d5aee2caadf8d8969cef90b80b5ce9258c4ab1f88e670944f031bc4c2d3c324`，280秒/25fps/7000帧全解码；70/74/82/100/180/279.5秒抽帧审阅显示前身抬起、前脚跟步及后续混合高度停滞，该主录像不是本批新增成功代表，也非最终全片原速验收。ha完整报告/精确输入/verification/terminal-differences/trace-difference-fields、followup-analysis、tail-samples、geometry-windows、实际关节几何复建及prelift重算和脚本在本地与远端归档；hb保存独立manifest/冻结源码/命令/输入与审计。同步指定feature/go2-piper-sim2real分支。

以上均为280秒箱沿参考控制器诊断，不是PPO，不冒充240秒、24秒慢爬或原起点12秒验收。NAV接近接口、原目标接近、耗时与覆盖率仍待解决；最终冻结候选原起点两组未用种子各32、每组≥30成功且无缺失及原速录像验收尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0049"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gz逐值复现并定位跟步净空缺口；ha验证完整前脚跟步预检（2026-10-04 22:37）

gz/inputs27302于22:05:37正常完成，报告SHA256 `a21d76da6945a49adbc1a46b9755adabeac5012c9f8f93c5facaa33ee18c74d4`。本地完整同步后独立流式SHA一致；来源/actor/evaluator核验通过。**32终态和19条密集轨迹的全部字段/长度与gy完全相同**，缺失0。真实四足登台、两前脚展开及末段承重停稳仍8/32（4/7/11/12/20/25/29/31），完整原任务仍0/32；原目标距中心<.20m及时间门禁没有放宽。终止22超时/2底座/7姿态/1低姿态，三足及以上99.959802%、腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，均与gy一致。此轮只增加精确输入，不能宣称新增成功。

精确重放补上此前遗漏的混合高度前脚跟步：env2左前捕获目标的完整摆动+15mm落脚探测名义间隙5.154mm，8/13/28为4.397/3.745/3.782mm；实际抬脚前状态重算同一完整虚拟路径，2/8/13/28仅1.79/1.73/.95/.75mm。受载跟踪使几何比原名义目标更紧，故仅增加卸载力不能解决。落脚探测的15mm是保守虚拟参考，实际接触可能提前停止；不能把这些预测值直接等同真实碰撞。原成功例11/31的完整虚拟路径同样较紧，因此新增检查会改变部分旧参考，必须做原八例物理回归，不能预先声称路径不变。

离线探索把名义完整摆动间隙留到10mm，并同时检查四足承重转移、旋转后的冻结COM、完整落脚/重载。2/8/13/28左前初始捕获可选择机身抬高约22.7mm的姿态，名义完整间隙约36mm；这是采样静态近似，不是动态安全保证。几例旧右前初始捕获只允许改善支撑的中间转移，尚不允许抬脚；若强制第一次捕获就具备最终三足姿态，会阻断这些旧路径。2/8/13/28已完成旧低净空左前步后的右前状态则已有起点间隙缺口，65高度重搜仍拒绝，支持把修正放在前一步，而非事后降低门槛。

实现`fd8d8b7`新增默认关闭`--climb-guidance-front-followup-preview`。仅两前脚台面/两后脚地面、前脚同高度向前跟步，加入现有capture的完整swing预检、15mm落脚探测和重载；跟步的支撑与落脚载荷预测都使用旋转后的冻结COM，并检查四足转移路径。该范围完整摆动名义净空要求10mm，其他范围保持5mm；原机身/支撑腿路径、关节软限位、力矩、实际卸载≤5N稳定.2秒、落脚重新承重及参考平滑不变。允许改善支撑的分段转移，但规划与实际释放共用完整摆动判定，**partial feasible不等于swing ready**；预检不通过时不得卸载/抬脚。没有改已登台后的前脚展开与固定末态保持逻辑。

68项数学/门禁检查通过（56.542秒、exit0），新增保存gz精确fixture验证2左前可行抬高、2右前已有缺口拒绝、11右前中间转移不得释放及20左前可行目标保留；同时覆盖10mm与旧5mm门禁及关节/FK条件。关闭新开关后，移除仅新增分支/掩码/可选输入并展开共享判定、规范布尔AND结合顺序，控制AST与2c09242一致。Python编译和diff检查通过。探索probe的冻结源码另存gz/probe-source及清单：它仍用旧落脚COM平移近似，最终ha增加了跟步落脚COM旋转，68项测试针对最终实现；不混淆探索数值和最终运行结果。

确认gz结束、无其它CLIMB进程、GPU1空闲后，`climb-front-followup-preview-20261004-ha/preview27302`于22:35:22启动，监控PID714919、GPU1。与gz保持相同seed27302、32环境、280秒/14100步、actor/复位库、19条密集轨迹及env2录像，只开启新preview；源码12项中3项改变、9项保持。22:36环境完成初始化，GPU1正常占用，尚无结果。下一轮先查进程/status，禁止重复启动；核对32终态/无缺失，单列原8登台/展开是否保留、新增真实登台及完整原任务成功，复查实际关节重建净空、支撑比例、速度/接触合力/初始化饱和，检查原速录像。低冲击但卡住不能算改善。

gz录像env2 SHA256 `ad809f6776b6cb1b4858632026f86c3b34ebe2f859fdcf08e484af6b64a6ab39`，280秒/25fps/7000帧全解码，70/74/82/100/180/279.5秒抽帧已审阅：前脚迈动后保持混合高度停滞。不是成功视频或最终全片原速验收。完整报告、小型核验/终态差异/19轨迹差异、精确capture/prelift输入、三份数学probe及源码清单保存本地/远端gz；ha保存manifest/source快照/命令/复位库/测试/默认关闭审计。更新指定feature/go2-piper-sim2real分支。

当前仍是280秒箱沿参考控制器诊断，不是PPO，不计入240秒、24秒慢爬或原起点12秒验收。原目标接近、耗时、登台覆盖率和NAV接口尚待解决；冻结候选后的原起点两组未用种子各32、每组≥30/无缺失和原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0050"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gy打通五例前脚卸载但随后几何停滞；gz补采精确跟步规划/抬脚输入（2026-10-04 21:23）

gy/followup27302于21:06:21正常结束，报告SHA256 `32d9fc810f897fb06812e57c5986fa84e69548389882d76d00ddabc2473b575f`；本地完整同步后独立SHA核验一致。来源/actor/evaluator核验通过，32唯一终态、缺失0。原8/32四足登台、两前脚展开及最终承重停稳全部保留；原八例完整密集轨迹与gx逐值一致。完整原任务仍0/32、登台数没有增加，不能把此次单步推进计作完整改善。

新力修正实际作用于2/8/13/15/28，分别从73.80/73.50/73.46/81.24/73.74秒开始前脚台面跟步的卸载微调；抬脚前最大修正1.301/.461/.554/.709/.907N，均远低于原8N上限。实际lifted分别在74.50/73.78/73.78/81.64/74.24秒，随后80.82～87.82秒完成落脚重载并切下一腿，切换时四足实测均承重（最小约38.81N）。2/8/13/28完成左前跟步后卡在右前规划，15完成右前跟步后卡在后脚规划，均活至280秒。其它27终态完全相同；15条共同密集轨迹中14条全字段/长度相同，env2首个诊断差异73.32秒是stall计时，实际力修正73.80秒才开始。新增四条密集轨迹没有gx全过程基线，不虚称全过程不变。

终止保持22超时/2底座/7姿态/1低姿态，没有新增这些安全终止。三足及以上99.959802%、最长腾空0、|vz|峰.789996m/s、含子步历史单足接触合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，全与gx相同。但“终止统计不变”不能掩盖新增路径几何余量不足：以记录的实际关节/机身姿态和同USD重建（FK最大误差2.11e-6m），2/8/13/28的左前小腿与箱体间隙在76.8/76.1/76.1/76.5秒、摆动phase约.58～.595已低于原5mm，最小接近0。15在78.6秒、尚未此次右前trim和抬脚时，左前小腿间隙已降到4.962mm，故它的起因是既有承重转移，而非此次右前力微调；不混成一个因果结论。这些是原primitive模型下实际姿态的几何证据，近零或微负数不直接冒充真实接触冲量。

源码检查：现有capture只对rear_ascent或四足台面的platform_step构造完整swing_preview；两前脚台面/两后脚地面的front_followup没有进入这条分支，因此其swing_path_ready=True可能是默认值，并不证明完整摆动已校验。后续应在前脚跟步前规划并检查完整摆动、落脚探测/重载和受载姿态，不能在发生5mm间隙缺口以后降低碰撞门槛或盲目抬高。当前仍保留gy作为诊断证据，未晋升为完整达标候选。

gy主录像env2 SHA256 `731f8fded6aed12cc10f737d306caef521a41b03a76888e9ad0cc37f24fc07fc`，280秒/25fps/7000帧全解码通过，70/74/82/100/180/279.5秒抽帧看到前脚前移后持续混合高度停滞；不是成功视频或最终原速全片验收。verification、terminal-differences、followup-analysis、followup-geometry-windows、followup-leg-geometry、failed-pose-inputs、视频核验和脚本保存本地/远端。followup-analysis已修正为只在phase0识别此次前脚台面trim，排除了19秒附近初次前脚抬升的渐退力，不能使用旧脚本的误标时间。

实现`7fed16e`仅增加只读输入采集：capture中的front_followup_pose_inputs每环境最多16份，保留原规划load/gravity/COM/bias/软限位/几何与结果，另记实际四足力、reference_bias和此前未校验的完整swing_request；抬脚释放点front_swing_inputs新增键后缀:followup，精确记录实际位姿和旧参考、COM/重力/限位/摆动。旧初次登台输入键和值格式保持。报告两类新输入均按真实终态时间过滤。移除采集代码后控制AST与gy相同，实际evaluator过滤块已执行有效/晚到fixture检查通过，语法/diff通过；没有改动作、目标、门禁或求解器，因此未重复运行66项不受影响的数学测试。

确认gy结束、无其它CLIMB进程且GPU1空闲后，`climb-front-followup-inputs-20261004-gz/inputs27302`于21:20:38启动，监控PID714335、GPU1。沿用gy全部控制参数、actor/复位库、seed27302、32环境、280秒/14100步、录像env2及19条密集轨迹，源码12项只climb_guidance/evaluator的采集变化，10项保持。21:23进程正常，EVAL_STEP400，无报错。下一轮先查进程/status不重复启动；要求32终态、19密集轨迹全部字段与长度及质量与gy完全相同，再抽取2/8/13/15/28与原8成功路径的精确capture/prelift输入，重放完整摆动+15mm落脚探测/重载、关节和碰撞余量。定位原始受载/机身高度/俯仰哪个环节使前小腿贴近箱沿，再构造保留原路径的有界修正，不能仅继续等或加力。

结果和源码同步feature/go2-piper-sim2real。当前全部是280秒箱沿参考控制器诊断，不是PPO，也非24秒/12秒原起点验收。目标位置、耗时、覆盖率与NAV接口仍待解决；最终候选原起点两组未用种子各32且每组≥30/无缺失及原速视频验收尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0051"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gx消除末段重复重设并保持八例停稳；gy针对混合高度前脚卸载卡点（2026-10-04 20:23）

gx/retain27302于19:48:21正常完成，报告SHA256 `3b4b8e8af93db5d3c9b5af4eb9003bbf191a79d55dc998bc4a2b27c72ea4b144`，本地完整报告单独哈希核验通过。来源/actor/evaluator通过，32唯一终态/缺失0。四足登台8/32、两前脚展开8/32保留；原六例到名义高度后持续稳定承重，新增7/29固定最后参考后分别连续四足承重停稳22.92/25.44秒，最小足载45.829/46.004N、最大线速.000342/.000371m/s、角速<.001462rad/s、指令越限0。它们仍有约2.563/2.562mm的受载高度残差，未达到分析使用的2mm名义高度匹配条件；这不否认四足真实登台并站稳，也不等于通过原完整任务。

7/29最终规划段从gw各22段变成12/11段，拒绝仍0，参考年龄延续到25.420/27.940秒。260～279.98秒末段，实际机身最大位移仅.000000868/.000001916m，足点最大位移约.00000289m，未再出现原重复重设造成的毫米级横移；不将此前调整中最多1.20cm足点位移改称全程无滑移。原六例和另外24个未登台环境全部30终态逐值一致；13条共同密集轨迹完全相同，7/29首次不同恰在257.08/254.56秒原重复capture处，之前全部字段相同。此次证据支持修复重复重设与末段漂移，尚未提高8/32登台覆盖率。

完整原任务仍0/32，距中心仍约.356～.383m，原位置门禁未撤销。终止22超时/2底座/7姿态/1低姿态，无新增安全失败；三足及以上99.959802%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，与gw一致。该280秒箱沿参考控制器诊断不算240秒/24秒/原起点12秒验收，不是PPO。gx录像env7 SHA256 `c7093ace762452adea762ce118b3be58dd71a1f1e18c8514ee32bf78e9644482`，280秒/25fps/7000帧解码通过，224.6/240/252/257/270/279.5秒抽帧审阅看到抬身后站姿保持；尚非最终全片原速验收。verification、retain-prefix-verification、final-adjustment-analysis、tail-and-failures、front-stall-evidence、failed-pose-inputs、followup-scope-audit及视频核验/脚本保存本地/远端。

接下来转回提高登台覆盖率。gx env2两前脚已在台面、两后脚仍在地面，当前左前脚需向台内跟进一步；名义卸载u=1，支撑/摆动可行、三足余量约28.7mm、关节指令不越限，却因实测选中足5.267～5.384N始终高于原5N释放门槛而停住。260～280秒其它支撑足最小26.200N、线速<.000295/角速<.001434。原力反馈只覆盖地面前脚初次抬升，因此此处trim=0。另有env14地面前脚已用满8N修正仍6.627～6.673N、以及17/19等几何不可行，属于不同卡点，本次不混改。

实现`3666ec7`新增默认关闭`--climb-guidance-front-followup-force-trim`：仅两前脚在原台面范围、两后脚仍在地面、当前为前脚同高度向前一步且尚未platform_hold时，允许复用原UnloadForceTrim。所有原age≥3秒、名义卸载完成、其它足各>8N、支撑余量≥25mm、实际低速、可行/摆动/关节/指令门禁保留；连续实际足载>5N停滞.5秒才积分，目标3N、上限8N、力率≤2N/s和原抬脚渐退不变。实际≤5N且稳定.2秒的释放要求、碰撞/执行器/落脚重载门禁不变。不是增加原地面trim上限或绕过卸载门禁。66项数学检查通过（51.765秒、exit0），覆盖混合支撑范围及各排除项、足载5.36N即使施加trim也不得直接放行；移除新范围分支/helper后旧控制AST完全一致。

已记录15条轨迹的触发预审中，仅env2在约73.8秒命中连续停滞，原八例成功轨迹均未命中。此预审以实测选中足近似start，运行时仍使用精确a.start，不能冒充物理回归证明。需实际验证是否抬脚、真实落脚/重新承重并继续后腿跟进，不能把足载降低但继续停滞算作改善完成。

确认gx结束、无其它CLIMB进程且GPU1空闲后，`climb-front-followup-trim-20261004-gy/followup27302`于20:22:30启动，监控PID713755、GPU1。保持seed27302/32环境/280秒14100步、actor/复位库及原所有控制开关，仅打开新followup-trim；源码12文件中3项改变（climb_guidance/box_climb_stages/evaluator），9项保持，gx末态参考修复保留。主录像env2；原15密集环境全部保留，另加8/13/15/28。下一轮先查进程/status，禁止重复启动；核对32终态/无缺失及全部安全质量，比较共同轨迹首次实际trim变化之前的一致性，单独列原8条路径是否改变及新增真实登台数。不盲调种子或放宽门禁。

本轮结果与实现同步指定GitHub分支feature/go2-piper-sim2real。NAV接口仍需独立验证；原目标接近、动作耗时与成功率尚未达标。最终原起点两组未用种子各32/每组≥30且无缺失、原速录像验收未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0052"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gw确认已登台姿态与末段重复重设；gx验证固定末态参考保持（2026-10-04 19:08）

gw/window27302于18:59:47正常完成，报告SHA256 `a8d9b504be99db144b5f5a0eefe49c6f1756d6d2901b957d1dfc8cbf85cac239`，本地完整同步并单独校验一致。32唯一终态、缺失0；来源/actor/evaluator核验通过，15条密集轨迹在240秒前与gv全部逐值一致（严格排除240秒截止样本）。这是280秒箱沿参考控制器延长诊断，不能计作240秒、24秒慢爬或原起点12秒验收，也不是PPO训练。

必须先报告真实上台成果：8/32四足登台且完成两前脚展开。原六例4/11/12/20/25/31保持约.503～.505m机身高度，最后段age≥2.5秒后的稳定承重时间扩至46.62～64.68秒，最小足载≥39.512N，最大线速<.000304m/s、角速<.00114rad/s、实际指令越限0。7/29继续抬到.501233/.501271m（调整前分别.427377/.428432m），前脚展开后全程四足接触、最小足载36.368/36.317N、指令越限0。视频看到的上台是真实成果；原完整任务0/32另包含距中心<.20m的位置要求，当前末态约.3556～.3826m，不能用完整0暗示没有上台，也不能擅自撤掉原门禁。

延长窗口还揭示一个末态保持问题：7/29已分别在254.56/252.06秒附近把最终x/z目标交给控制器，却因实际受载高度约低于固定参考2.5mm，继续每2.5秒capture_hold重设锚点和参考年龄。精确规划输入显示7从257.06秒起重复10次、29从254.54秒起重复11次；末次相对首次重复时高度仅变化.0067/.0474mm，横向却累积偏移3.49/3.79mm。目标高度仍约.50378m，延长40秒没有让它们通过本次分析使用的2mm名义高度匹配条件；这一分析条件不等于原上台成功门禁。不能声称8例全部末态完成，也不能继续只靠延长等待解决重复重设。

全局三足及以上99.959802%、最长腾空0、|vz|峰.789996m/s、含子步历史单足接触合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。终止22超时/2底座接触/7姿态/1低姿态，无新增安全失败；三足比例上升来自更长观察分母，不能宣称控制改进。八例调整足点最大3D位移仍1.20cm，不能称完全无滑移。verification.json、window-prefix-verification.json、final-adjustment-analysis.json、terminal-states.json、last-trace-samples.json、redundant-final-recapture.json保存本地/远端。

gw主录像env7 SHA256 `c372eb7b800d1fa0572a7b5a9bc71f17dce9f43cfd25d568a4b154504fb63158`，280秒/25fps/7000帧全片解码通过，224.6/240/252/257/270/279.5秒关键帧审阅可见上台后持续抬高、最后站姿保持；只做了解码与抽帧，未冒充最终全片原速验收。

修复`181a317`仅在默认关闭的platform_final_adjust分支增加“固定x/z目标已下达后保留原参考”的判断；保留原锚点/插值年龄，受载跟踪残差不会再触发相同目标的重新capture。没有设置实际完成标志，没有增大高度容差，也没有改变中心、受载、碰撞、执行器及停稳判据。原分段尚未走到目标时继续规划。64项数学与门禁检查通过（53.419秒、exit0），新增回归覆盖已下达目标但实际高度仍低2.6mm时不得重设参考；原未完成两前步/失载/稳定等待和固定目标跨段测试保留。精确gw规划记录预审仅7/29命中新抑制条件，物理结果仍待gx。

核对gw结束、无其它CLIMB评估、GPU1空闲后，`climb-platform-retain-goal-20261004-gx/retain27302`于19:07:56启动，监控PID713173、GPU1。保留seed27302、32环境、280秒/14100步、actor/复位库、全部控制开关、录像env7及15密集轨迹；12源码只climb_guidance.py哈希改变，evaluator等11项保持。19:08核对评估进程存活、初始化中无报错。下一轮先查进程/status，不重复启动；完成后核对32终态/缺失、全部质量/初始饱和、原8登台/8展开/6例稳站。重点比较7/29首次被抑制capture以前的轨迹一致性及之后是否参考年龄持续、停止重设、实际漂移减少和真实承重停稳；若仍有2.5mm残差如实保留，不能仅因目标已下达或段数变少就宣布改善完成。

GitHub连接已恢复，此前待推送83ccdbb/9c3cc3b已同步至指定分支feature/go2-piper-sim2real；本轮修复和记录随后同步。后续仍需提高登台覆盖率、缩短动作耗时并单独验证NAV接口及原目标接近；不得在足点固定时强推大幅重心位移。最终原起点两组未用种子各32、每组≥30/无缺失和原速视频验收尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0053"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gv六例达到名义机身高度并停稳；gw独立延长窗口观察余下两例（2026-10-04 18:20）

GitHub同步暂缓：本轮结果提交83ccdbb已在本地保存，SSH到github.com:22及备用ssh.github.com:443均连接超时；未改变远端分支或凭据配置。下轮先重试推送feature/go2-piper-sim2real的本地待推送提交，物理评估gw已正常运行，不因GitHub连接故障重复启动。

gv/adjust27302于17:59:10正常完成，报告SHA256 `688936971854a9bff25b40e64027ec652c2211aecc49249a496c394869cfd995`；来源/actor/evaluator和32唯一终态核验通过，缺失0。240秒箱沿诊断，四足曾登台8/32、两前脚展开8/32全部保留；新增最终机身调整后，4/11/12/20/25/31六例达到约.503～.505m名义机身高度并停稳，7/29截止时仍在段内，不能算末态调整完成。原完整任务仍0/32，末态中心距离.3556～.3826m仍超原.20m要求。终止保持22超时/2底座/7姿态/1低姿态，无新增安全失败。

最低env31从约.3897m抬升.113408m到.503156m，实际前移.042309m，13段、拒绝0；最后一段230.88秒开始，age≥2.5秒之后四足稳定承重6.62秒，最小足载39.513N，最大线速.000299m/s、角速.000989rad/s，实际指令越限0，末态倾角.844度。env11抬升.106712m到.503497m，实际前移.046627m，12段、拒绝0，最后段后稳定7.74秒、最小足载41.330N。4/20各4段、抬高约1.83cm，随后稳定9.12/9.78秒；12/25各5段、抬高约5.03/4.90cm，随后稳定24.30/24.68秒。六例最后段稳定期间最大线速均<.00030m/s、角速<.00114rad/s、实际指令越限0。实际前移约4.15～4.68cm，部分比固定4cm目标多约6.8mm，不宣称精确无超调。

7/29在224.58/224.56秒才完成前脚展开，227.08/227.06秒启动机身调整；至240秒各规划6段、拒绝0，机身分别到.457996/.459568m，相对调整前提高3.06/3.11cm、前移3.83cm，最后一段仅运行.42/.44秒。全段保持四足接触及实际指令越限0；目标高度仍约.50378m，暂无证据认定已完成或必能继续完成，需要明确标注的延长观察。

原8登台环境全部共同轨迹在新调整首次启动前逐值一致（首次变化200.88～227.08秒，均为两前脚完成后2.5秒）；其余7条密集轨迹全部共同字段和长度一致，24个未登台环境原终态字段一致。全局三足及以上99.953472%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，与gu一致。单足合力不是冲量或底座接触峰。新增调整后8例全程四足接触，最大线速.032748m/s、竖直速度.017600m/s、实际指令越限0。固定支撑足点最大3D位移约1.20cm，不能写成完全无滑移。55份真实最终姿态规划输入逐份数学重放，位置/姿态/余量与运行匹配，最大误差1.20e-7；最小规划余量.141410rad，最小实际段初足载28.221N。

gv固定env31录像SHA256 `b92660551892486294a704ea7571c476dd88ec2b9d8613ef74f7299fb039ad97`，240秒/25fps/6000帧全片解码通过；198.4/201/210/220/230/239.5秒关键帧已审阅，低站姿逐渐抬起、前移，末态更舒展并保持。仅解码和抽帧审阅，不冒充最终全片原速验收。verification.json、final-adjustment-analysis.json、trace-difference-fields.json、final-plan-replay.json、视频核验和脚本保存本地并同步远端；本地大报告完成同步后单独核验SHA，未读取半传输文件。

本轮不改控制参数。核对无CLIMB任务、GPU1空闲后，`climb-platform-final-window-20261004-gw/window27302`于18:19:49启动，监控PID712458、GPU1。沿用gv12源码哈希、actor、复位库、seed27302、32环境和全部控制开关，仅将诊断观察窗240→280秒、步数14100；对应walltime3000/3030/3200秒，主录像选择余下env7，原15密集环境保留。该280秒结果单独报告，不算240秒阶段完成、24秒慢爬或原起点12秒验收。下一轮先查进程/status，完成后核验前240秒共同轨迹与gv相同（截止超时样本单独处理），确认7/29是否最终达到高度并真实停稳、原六例是否持续承重；同时检查固定目标超调、足点漂移、全部碰撞/执行器/速度/终态门禁。不能仅因多等40秒提高成功计数就宣称控制器改进。

原中心目标仍待后续台面行进解决，固定足点下不能直接把4cm前移扩成大幅重心前推。当前优先完成用户要求的登台后舒展验证，再基于实际支撑范围规划后续动作；NAV接口另验。当前为参考控制器诊断，不是PPO；最终候选原起点两组未用种子各32、每组≥30且无缺失，以及原速录像验收均未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0054"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gu精确末态输入核验；gv验证两前脚落稳后的分段抬身/前移（2026-10-04 17:25）

gu/final27302于16:59:23正常完成，报告SHA256 `0ace30e767d9ae050e562eb62204843d788bca3160f07f83d42f4b9a31f37bfd`。来源/actor/evaluator核验通过，32唯一终态/缺失0，32终态与15条密集轨迹（含全部字段和长度）与gt逐值一致。四足曾登台8/32、两前脚展开8/32，原完整成功0/32；22超时/2底座/7姿态/1低姿态。三足及以上99.953472%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，与gt一致。单足合力不等于冲量或底座接触峰；只读采样没有改物理结果。

采到8环境22份真实终态之前的展开后稳定受载输入：4/11/12/20/25/31各3份，7/29各2份，env26晚到记录排除。第一份在第二前脚完成后参考age3秒，记录实际COM、四足力、重力补偿、软限位与旧参考偏置，支持针对低站姿的精确规划。8份首次输入的机身前移1cm/抬升1cm组合均通过21点路径受载、预测力矩/软限位、FK及原底座/腿碰撞门禁：最小预测足载28.067N、最小关节/力矩等效余量.208024rad、最大平衡残差范数3.404e-5。直接前移4cm并升至原名义clearance .28m时，env7/29的旧偏置关节路径余量分别−.006054/−.002675rad，不能一次提交该整段路径或放宽软限位。小段可行不证明重新承重后每一后续段均可行，因此必须每段重新检查。

实现`a6663ad`新增默认关闭`--climb-platform-final-adjust`，要求已有front-first与全部支撑/落脚/碰撞依赖。只在两前脚都完成真实落脚、平台hold且不在摆动时启动；原参考age≥2秒，四足实际各≥8N、腿有效、实际指令不越限、参考跟踪误差<1cm/转角<.025rad、gravity_z<−.985、线速<.025/角速<.1，连续满足.5秒后才规划。首次冻结世界坐标目标为当前机身x+4cm、z不低于当前且尝试恢复足点均高+.28m；不逐次重设向前目标，y和当前近水平姿态保持。每段x/z各最多1cm，优先完整小段、其次半段/四分之一段；21采样上所有足预测≥8N、平衡残差<.1、FK<1mm、名义/预测受载关节余量≥.03rad及75%执行器力矩上限均保留，底座1cm/腿5mm间隙和原旧参考偏置全路径软限位保留。采用既有1.5秒平滑与capture_hold连续参考，段末重新等真实承重和低速，拒绝则保留当前hold，至多每1.5秒重试。没有放开原上台、前腿两步、终止或完整成功门禁。

新增终态调整段数/拒绝数/固定目标/等待状态，以及每段规划输入和结果（按真实终态过滤）。64项数学检查通过（75.798秒，exit0）：8份精确末态fixture检查1cm小段，COM不平衡/执行器不足均拒绝，到目标不生成额外运动；运行门禁fixture验证未完成两步、失载、未满稳定等待均不启动，并验证第二段不滚动扩大目标。移除新默认关闭分支及只读采样后原控制AST相同，语法/diff通过。该规划仍使用冻结重力与近似COM，实测动态/滑移及最终停稳需远端结果证明。

核对无CLIMB进程、GPU1空闲后，`climb-platform-final-adjust-20261004-gv/adjust27302`于17:24:21启动，监控PID710715、GPU1。沿用gu seed27302、32环境、240秒/12100步、actor、复位库、主录像env31及15条密集轨迹；核对命令仅新final-adjust控制开关不同（除产物路径/任务名），12源码哈希冻结。下一轮先核对进程/status，完成后检验32终态/无缺失、原8登台/8前脚展开是否保留，所有共同物理轨迹在两步完成和新调整启动前是否保持，机身真实抬升/前移、段数/拒绝、四足受载/滑移/实际指令余量及全部安全质量。最晚完成展开7/29仅剩约15秒，240秒内可能只能完成部分抬升，不能把截断当成舒展完成。总前移4cm是末态舒展诊断，仍不足以将原约.40～.42m中心距离压到.20m以内，不承诺原完整成功；后续目标接近须独立推进，不能改原中心门禁。

gu env31视频SHA256 `249c3eac97f6f9bbc3efcbe06c7f6d359791f8f102b079ee3d3e3f6420ebf6fb`，240秒/25fps/6000帧全片解码通过，190/198.4/202/210/225/239.5秒抽帧审阅确认两步后低站姿保持，非最终原速全片验收。verification.json、platform-final-inputs.json、final-pose-probe.json、视频核验及脚本更新本地/远端。参考控制器诊断继续，不是PPO、24秒慢爬或原起点12秒；最终原起点两组未用种子各32及原速录像尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0055"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gt前脚先展开从6→8，修复两例调平失败；gu采集展开后末态受载（2026-10-04 16:25）

gt/frontfirst27302于15:29:08正常结束，报告SHA256 `0b0da872aedf4ee119649673325f2715bd4ecc4612f0622ad69c5a81f261d008`；来源/actor/evaluator核验通过，32唯一终态/缺失0。240秒箱沿、同seed27302诊断：原8/32四足曾登台全部保留，两前脚展开从gs的6/32增至8/32（4/7/11/12/20/25/29/31）；原完整任务仍0/32。22超时/2底座/7姿态/1低姿态，gs为20/2/7/3，无新增安全失败，7/29由低姿态失败改为完成两前脚展开后存活至240秒。该结果支持用户“先前脚逐只前移，再作最终机身/重心调整”的顺序，但尚未完成最终舒展和原目标验收。

新增env7于211.52/224.58秒完成两步，随后四足连续承重15.42秒，最小足载36.368N，最大线速.011445m/s、角速.016301rad/s，实际指令越限0、末态倾角2.715度；env29于211.50/224.56秒完成两步，承重15.44秒，最小36.317N，最大线速.011352、角速.015918、越限0、倾角2.666度。原六例也全部完成，展开后四足接触始终保持，持续21.62～41.62秒。前脚实测净前移约3.24～4.07cm（第一展开capture到235秒），并非只改完成标记；部分后脚伴随后移，最大env31右后脚约1.14cm，不能宣称完全无滑移。

全部质量：三足及以上99.953472%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节饱和最大.280s；后三项和腾空与gs一致。单足合力不是冲量或底座接触峰。24个未登台环境原终态字段逐值一致；原8登台环境首个轨迹差异均发生于平台hold之后（175.44～198.56秒），原登台过程保持。其余7条密集轨迹中6条全部逐值一致，env17仅guidance_swing_path_margin/gap两个诊断字段不同，其余全部字段包含物理/动作轨迹逐值一致，不能写成15条全轨迹均不变。30份已接受前脚展开姿态输入核验：机身x与旋转预测COM x均未前移（最大变化均−.004648m），原四足路径受载/恢复与残差门禁均通过；这是规划约束证据，不冒充实际COM全过程无前移。

8例展开末态距目标中心仍.3971～.4248m，超原.20m；env11/31机身z仅.3968/.3898m，7/29为.4274/.4284m，4/20约.4858m，12/25约.455m。虽均近水平且承重停稳，低站姿尚不够舒展。源码确认PlatformFrontExtension在两步后永久hold，level_hold仅对gravity_z>−.985请求调平；上述末态gravity_z均约−.999，故不会主动抬身或向中心前移。本次顺序开关没有新增最终重心运输行为，不能把原完整0仅解释成随机成功率不足，更不能降低原中心/停稳门禁。下一步在已扩大前脚支撑范围后规划平缓抬身/前移，需精确最终受载输入验证路径与余量，不能直接给大幅位移。

gt主录像env7全片解码通过：240秒/25fps/6000帧，SHA256 `543acd92ba23d149ad4ea0f5f8b26f2d27a6a82ea7d576d591d0fb6f16b1f09c`；190/198/205/215/230/239.5秒抽帧已审阅，可见原失败例完成前腿展开并站住。仅全片解码和抽帧审阅，不是全片原速最终验收。verification.json、extension-analysis.json、prefix-verification.json、env17-diagnostic-differences.json、front-first-pose-verification.json、extension-foot-displacement.json和核验脚本保存本地并同步远端。gt原plan里继承的旧seed/inspect字段存在陈旧描述，实际冻结jobs为seed27302/主env7/15轨迹；下一轮gu已按实际参数修正清楚，不修改gt原启动记录。

实现`55b0067`仅新增只读platform_final_inputs：两前脚完成且平台hold、四足接触、原腿有效/指令不越限/低速条件满足后，在参考age≥3/10/20秒各采一次，记录实际足点/机身/COM/重力/关节软限位/参考偏置/足载/速度/既有参考，按真实终态剔除晚到记录。没有新控制开关或姿态运动。删除新增采样初始化/方法/调用后控制AST与gt完全一致；采样形状、足与关节索引、采样次数、不修改控制张量及报告终态过滤检查通过，AST/diff通过。

确认无CLIMB进程、GPU1空闲后，`climb-platform-final-inputs-20261004-gu/final27302`于16:24:43启动，监控PID703472、GPU1，沿用gt全部控制参数、actor、复位库、seed27302、32环境、240秒/12100步和原15条密集轨迹；主录像换env31以检查最低末态。约16:25进程存活、无报错，初始化中。12源码哈希冻结。下一轮先核对gu进程/status，完成后要求32终态/15轨迹及所有质量与gt相同，再重放展开后精确受载输入，设计有原四足受载/几何/关节/平滑门禁的最终姿态微调，保留gt已实现8展开路径。仍是参考控制器诊断，不是PPO、24秒慢爬或原起点12秒；最终原起点两组未用种子各32与原速录像尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0056"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 用户最新试验方向（2026-10-04）：先扩大前脚支撑范围，再做最终机身/重心调整

用户观看gp失败案例后要求：四足登台后，在最后向前调整重心之前，让两前腿逐只向前移动，为后续调整扩大支撑范围。保留已实现登台路径及原真实落脚、重新承重等待、三足/执行器/碰撞/停稳门禁。当前6/32展开基线保持独立，新的先前脚顺序作为受控实验，不能以实现或启动等同物理通过。

实现`67aef25`新增默认关闭`--climb-platform-front-first`：四足真实登台并承重后，仅保留达到原展开释放条件gravity_z<-.94所需的最小调平；在两前脚分别完成原4cm落脚并重新承重以前，不再继续额外调平到原-.985水平，且台面支撑姿态候选的机身x和旋转预测COM x均不得超过capture初态。必要侧向/后向支撑转移、抬升与全部原几何/关节/受载/摆动检查保留。两步完成后恢复原调平策略和后续姿态规划。这是动作顺序与候选约束变化，不是改落点距离或降低原抬脚姿态要求；原12秒/24秒验收门禁不改。

61项数学检查通过：原倾角准备门槛保留，第二前脚完成前推迟额外调平，完成后恢复；精确原失败fixture的向前机身/COM方案被拒绝并找到不前移替代，关闭范围位逐值恢复原选择；语法/diff通过。新旧远端命令核对除录像/密集轨迹排列和新开关外完全相同，actor、复位库、seed27302、32环境、240秒/12100步及原参数保留。

gs/level27302已于14:53:51完成：报告SHA256 `e421b0e9f436c78182b8995a09fd04c5cdfd77a41aa1c468d992dfe0e04eac59`，来源/actor/evaluator哈希通过，32唯一终态/缺失0，全部32终态及15条共同密集轨迹与gr逐值一致。四足曾登台8/32、两前脚展开6/32，原完整成功0/32；20超时/2底座/7姿态/3低姿态。三足及以上99.952932%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s。新增只读采样未改变物理结果，gs可作为gt精确基线。7/29调平输入已抽出platform-level-inputs.json，尚未数学重放；按用户新优先级先比较动作顺序，不盲改高度。

gs固定env11录像SHA256 `3d77f7d1b863dfaa24dae0eabf453c286702ef20ddb62491cf0bc77c1517a154`，240秒/25fps/6000帧全片解码通过，169/190/196.6/202.1/215/239.5秒关键帧已审阅，可见后段前足展开与末态站立。仅全片解码和抽帧审阅，不冒充全片原速最终验收。此前gr/env4也已全片解码和抽帧审阅；用户看到的gp/env4失败片已明确标注为历史已修复碰撞案例，不代表gr/gs当前仍有该同例碰撞。

等待gs退出、核对GPU1空闲后，`climb-front-first-order-20261004-gt/frontfirst27302`于2026-10-04 14:54:30启动，监控PID696866，GPU1；保留原32环境、seed27302、240秒/12100步及15条密集轨迹，主录像改为此前调平失败env7。源码12文件冻结，源实现67aef25。约15:00核对进程存活，EVAL_STEP=1800、已有8个终态、无Traceback/Error；仍在早期登台阶段，不能据此评价新增顺序。没有重复启动或触碰其它GPU任务。

下一轮先读gt进程/status，完成后核验来源及32终态/缺失，逐项比较gs：原8个登台和6个展开是否保留，7/29能否在原抬脚门槛达标后先迈前脚，前脚扩展期间支撑载荷、实际机身/COM运动、首次轨迹差异是否仅在平台hold之后；检查最终姿态/中心距离及全部安全质量指标。若低冲击但停滞或新增失稳，不能算改善。两前脚完成后只是恢复既有调平/规划，本次没有新增最终向台面中心运输行为，因此不能承诺解决原中心距离>.20m。当前仍为240秒箱沿参考控制器诊断，不是PPO、24秒慢爬或原起点12秒验收；最终原起点两组未用种子各32及原速录像尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0057"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gr完成展开4→6，实际弱后脚先恢复承重；gs补采余下调平失败输入（2026-10-04 14:21）

gr/recover27302于13:56:31正常完成，报告SHA256 `3a6f217b6a5c3ec277a2f95779952c7f095eb5c3d8ca77c1dac181b512507636`；来源/actor/evaluator及32唯一终态核验通过，缺失0。240秒箱沿、同seed27302，四足曾登台仍8/32，两前脚展开从4/32升至6/32（4/11/12/20/25/31），原完整成功仍0/32。20超时/2底座/7姿态/3低姿态，与gq相同，没有新增安全失败。其它30环境原终态字段逐值一致；15条共同密集轨迹只有11/31从其第一平台capture后的189.96/186.54秒开始变化，其余13条全部逐值一致，含原成功4/12/20/25与登台未展开7/29。

新增11/31实际右后脚承重从6.811/6.418N于190.52/187.10秒恢复到≥8N，同一时刻起已有连续.26秒四足各≥8N；直到196.54/195.06秒才开始第一前脚摆动。抬前脚时其它三足真实承重约130.5/60.5/25.1N和130.5/57.6/29.5N，第一摆动期间支撑足最小21.94/21.24N，恢复到抬脚前实际指令越限0。不是跳过承重等待或强行抬脚。详细见recovery-load-verification.json。

env11于202.02/214.90秒完成第一/第二前脚展开，随后四足承重25.10秒，最小足载40.87N，最大线速.001993m/s、角速.004555rad/s，指令越限0、末态倾角.742度。env31于200.64/213.52秒完成两步，四足承重26.48秒，最小足载40.67N，最大线速.002264m/s、角速.005746rad/s，越限0、末态倾角.679度。末态中心距离.3897/.3954m，仍超原.20m要求；其它四例保持原结果，所以完整成功0是真实门禁结果，阶段展开不代替完整验收。

总体三足及以上99.952932%、最长腾空0、|vz|峰.789996m/s、含子步历史单足合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s，均与gq相同。单足合力不称冲量，也不代表底座接触峰。gr固定env4录像SHA `9b3bd3155a2c83716e0a0a748f8fb00ec75bc52fe22e8de55018a5bbc5a998f4`，该环境密集轨迹与gq逐值一致，但视频字节不同，本轮未把它当作新增11/31的视频证据；新成功env11的原速录制安排在下一轮。

余下登台后未展开7/29均在190.48秒进入hold，机身z约.394m；调平过程中累计7段后205秒z降至.389/.390m，最终约207.86/208.06秒低姿态终止，末态z.379m。尚未进入前脚展开，不能继续调整展开参数解释。已有轨迹显示参考与实际高度逐段下移，需精确调平规划的gravity/COM/偏置/限位输入辨别是候选高度选择、跟踪误差累积或两者共同导致，不能直接指定抬高量或放宽原.18m净空门禁。

实现`b5ecb15`只增加只读platform_level_inputs（每环境最多64条，既有调平候选选择前的精确输入/输出、实际四足接触/竖直力、前一参考），沿用pose-fixtures开关。同时修复platform pose/level报告过滤：按每环境真实终态时间排除后续继续步进采样，并列出排除数量；gr原报告保持不改，env26的6条晚到pose不作原回合证据。抽取报告生成AST执行，过滤结果与gr有效派生记录完全相同，另验证晚到level样本剔除。移除新collector初始化/方法/调用后控制AST与gr完全相同，AST/diff通过；没有改动控制候选或运行门禁。

确认远端无CLIMB进程、GPU1空闲后，`climb-platform-level-inputs-20261004-gs/level27302`于14:19:51启动，监控PID694926、GPU1，GPU0原其它进程未触碰。32环境/seed27302/240秒/12100步，gr全部控制开关、actor/复位库及12源码哈希冻结；原15个密集环境保留，主录像由env4切换env11。下一轮先读gs状态，要求32终态及15轨迹与gr一致，再数学重放7/29每段调平输入，检查候选与实际支撑净空/受载，并审阅新增env11视频。参考控制器诊断继续，不是PPO；24秒慢爬、原起点12秒与最终2×32均尚未验收。verification.json、extension-analysis.json、有效/晚到平台输入、受载恢复核验和脚本同步本地/远端，8806成功页面保留。PUSH/MuJoCo/实机暂停。

<a id="record-0058"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gq展开完成2→4且修复4例碰撞；gr验证弱后脚承重恢复（2026-10-04 13:22）

gq/support27302于12:54:34正常结束，报告SHA256 `9cca2a57ea19568b574461d1e31c8b2c69cd55aedb7a5e8b4288cb4c1d65e627`，来源/actor/evaluator核验通过，32唯一终态/缺失0。240秒箱沿同seed27302：四足曾登台仍8/32（4/7/11/12/20/25/29/31），两前脚展开由gp的2/32升至4/32（4/12/20/25），原完整成功仍0/32。gp新增登台后碰撞的4/11/20/31全部转为活到240秒，未新增安全失败；11/31只避免了碰撞，尚未展开，不能把其停滞计作完成。20超时/2底座/7姿态/3低姿态，gp为16超时/6底座/7姿态/3低姿态。其余28环境原终态字段逐值一致，原成功12/25完整密集轨迹与gp逐值一致。共同12条轨迹只有env4在205.20秒（平台capture205.18秒后首采样）开始变化，其余共同轨迹全部一致；gp没有11/20/31密集轨迹，不能宣称已验证它们全过程不变。

新增env4于217.14/230.06秒完成第一/第二前脚小步，随后四足承重9.94秒，最小足载39.63N，最大线速.002205m/s、角速.004081rad/s，实际指令越限0，末态倾角.970度。env20于218.70/231.62秒完成两步，四足承重8.38秒，最小足载39.61N，最大线速.002194m/s、角速.004553rad/s、越限0、末态倾角.960度。原12/25仍分别稳站23.24/23.62秒。四条展开末态中心距离约.3805/.3846/.3809/.3861m，均超原.20m目标；完整成功0是原门禁结果。不会改目标或用阶段成功代替完整验收。

总体三足及以上99.952932%、最长腾空0、|vz|峰.789996m/s、含子步历史单足接触合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s；后三项及腾空与gp一致。单足合力不是冲量，不代表底座接触峰。gq主录像env4已全片解码并抽帧审阅，240秒/25fps/6000帧，SHA `a9314af2bdacf152447a0f18067ec6d10566457569e8ec562430c630ff34dfd6`，关键帧看到四足登台后前腿展开并站稳；不是最终全片原速验收。视频`climb-platform-support-path-20261004-gq/support27302-env4.mp4`可作为最新阶段进展，8806原成功对照页面保留。

11/31停滞定位：第一展开capture分别189.94/186.52秒，四脚都接触，但预测右后脚初态承重只有7.737/7.407N（实际约6.82/6.42N）。gq要求整条路径含初态均≥8N，故任何终点都会被拒绝，保留参考后一直未抬脚；240秒重搜拒绝32/35次。不能直接把8N阈值调低放行原危险前移。精确fixture数学重放找到承重恢复路径：初始各脚≥2N，原弱脚在21个插值采样上不减载，其它脚一直≥8N，终点所有脚恢复≥8N，原平衡残差<.1及几何/关节/三足/摆动限制保留。11/31候选右后脚终点预测48.316/47.981N；原危险移动与原地不恢复均不通过。成功4/12/20/25首个capture的选择逐值保持。这里只证明准静态候选可行，仍需实测恢复与实际前脚展开。

实现`9ee0d77`新增默认关闭`--climb-guidance-platform-support-recovery`，必须搭配原platform-support-path，只在四足台面展开规划中允许上述单调恢复路径，不改登台、前脚4cm落点或原真实卸载/落脚/承重等待/执行器门禁。59项数学检查、AST/diff通过。确认无CLIMB运行、GPU1空闲后，`climb-platform-support-recovery-20261004-gr/recover27302`于13:21:44启动，监控PID685643、GPU1（GPU0有其它进程，未触碰）。32环境/seed27302/240秒/12100步，沿用gq全部actor/复位/参数和15条密集轨迹，仅开启恢复开关，12源码哈希冻结。

下一轮先读gr进程/status，核验32终态/无缺失和全部质量、原8登台与4展开是否保留、11/31是否真实恢复受载并完成展开，不能只看不碰撞。gq verification.json、extension-analysis.json、support-recovery-probe.json、录像核验及脚本已本地/远端同步。原platform collector仍会记录已终止环境继续步进后的数据；此次env26的6份均在其终态之后，原报告不改，派生platform-pose-inputs-valid.json排除、另存after-terminal文件，不能当成26原回合平台活动。最终原起点2×32、24秒慢爬/12秒完整验收尚未开始；当前是参考控制器诊断，不是PPO。PUSH/MuJoCo/实机暂停。

<a id="record-0059"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：定位台面展开前四足承重规划缺口；gq路径受载检查远端评估中（2026-10-04 12:21）

先核对无CLIMB进程，未重复启动。gp的32份早期四足front-ascent输入已用匹配源码逐一数学重放，接受/重试标志及position/quaternion/margin均匹配（容差1e-6），证实早期输入与运行结果对应，未用后期三足fixture冒充。结果front-ascent-replay.json。

细查env4：186.02秒进入四足hold，随后8段调平，后脚承重逐步降至约17～18N。205.18秒第一前脚展开capture选择了中间承重转移姿态，swing_path_ready=false、卸载分数0，尚未抬前脚。约206.10秒左后脚承重跌破2N，206.74秒底座接触终止。原partial-transfer允许预测重心向三足区域改善而无需已满足三足条件，但没有另查四足承重路径；原support_load_preview在此返回1000占位值，platform-load-reserve也未因其触发完整受载候选重搜。

按该精确205.18秒fixture，用同一重心旋转和四足承重求解器对21个插值姿态重放，原计划左后脚预测承重从17.786N降到0，末段力/力矩平衡残差范数升至2.081895。这与实际未卸载前就丢失左后支撑相符；仍是准静态模型归因，不宣称已证明全部动力学原因。强制完整三足余量30或80mrad的65点搜索均无解，因此不能只禁掉中间转移。给中间转移补全四足受载检查后，可找到保留原路径/关节/摆动限制的候选，65点探针预测全路径最小承重17.786N、最大残差2.8e-5；需物理验证能否连续推进，而非停滞。env12/25原第一展开计划的四足路径最小承重23.407/22.615N，均未触发新限制。

实现`2141515`新增默认关闭`--climb-guidance-platform-support-path`，只在四足台面前脚展开capture给load-preview标记范围。对候选21个插值位姿检查预测每足承重≥8N、力/力矩平衡残差范数<.1（沿用现有四足调平规划阈值），防止未抬前脚就计划卸掉后支撑；原几何、关节、三足受载、摆动、真实落脚/重新承重与限位门禁均保留。该模型不预言动态误差，不能代替实际受载检查。登台阶段不启用该过滤，前脚仍逐只4cm展开。58项数学检查通过；精确失败fixture检出原0N路径并找到替代，成功env12候选逐值保留，关闭范围位保持原结果。AST/diff通过，移除新helper/开关调用后控制AST一致。

`climb-platform-support-path-20261004-gq/support27302`于12:20:49启动，GPU1、监控PID681149，32环境/seed27302/240秒/12100步。沿用gp actor/受载复位库、front-ascent修正及其它参数，仅打开新平台支撑路径开关；12源码哈希冻结。主录像env4，原12条密集轨迹另加11/20/31，便于核对其它新增登台失败链条。当前是参考控制器远端物理诊断，不是PPO、24秒慢爬或12秒原起点验收。下一轮先读gq状态，核查32终态/缺失、全部质量指标、原12/25展开、gp8登台是否保留、首个平台capture前轨迹是否一致；若只降低冲击却停滞，不算完成。

gp录像已全片解码并抽帧审阅：固定env4，25fps/5169帧/206.76秒，随该环境失败结束，SHA256 `9f4e7a301422059a3dc6ce31a46449f53e6b3e35b04aa39697149028f40debc8`。关键帧显示低姿态四足上台后，转移时前部下沉并失稳；不是240秒完整片长，也不是最终全片原速验收。transfer-analysis.json、four-support-path-probe.json、platform-full-load-probe.json、four-support-guard-probe.json、录像核验及脚本保留本地/远端。8806成功展开页面不替换。最终原起点2×32尚未开始，PUSH/MuJoCo/实机暂停。

<a id="record-0060"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gp四足曾登台4→8，但新增四回合展开前底座碰撞；尚未提高稳定完成率（2026-10-04 11:57核验）

gp/pose27302实际已于06:55:31正常结束，本次用户询问进展时核验并同步完整结果；当前远端没有CLIMB训练或评估进程，不能继续称其运行中。报告SHA256 `ada0efde7d0fbfbf48599b9d462f761ae5f7d8cac6640f4fca75174c87ee950c`，来源/actor/evaluator哈希通过，32唯一终态、缺失0。240秒箱沿诊断、同seed27302：四足曾台面支撑从gn的4/32增至8/32（新增4/11/20/31），两前脚展开仍2/32（12/25），原完整成功仍0/32。原先两条成功展开路径保留，但不能把新增瞬时登台计作稳定完成。

新增4/11/20/31分别在206.74/191.42/208.30/187.96秒触发底座接触终止，均extension_completed=0、extension_moving=true、当前前脚phase=0，终态左后脚失去接触、机身高度约.373～.381m，支撑余量为负。env4密集轨迹显示185.12秒四足在台面接触、186.02秒进入hold，随后在第一前脚展开的承重转移阶段失稳，未完成第一小步。并非原初次前脚卡点完全未变，而是走到后续低姿态承重转移失败。env11/20/31没有独立密集轨迹，其精确失稳链条仍需补证，不能只凭相似终态宣称完全同因。

总体16超时/6底座接触/7姿态/3低姿态；gn为20超时/0底座/10姿态/2低姿态。三足及以上99.945506%、最长腾空0、|vz|峰.789996m/s、单足接触合力峰250.319N、含初始化累计单环境/关节力矩饱和最大.280s；gn对应99.937900%/0/.737580m/s/202.263N/.280s。单足合力含子步历史，不是冲量，也不覆盖底座碰撞峰。新增安全失败和接触峰上升，因此不晋升候选。

17环境各应用一次新姿态，其余15环境原终态字段逐值一致；8份共同密集轨迹中，应用环境首次差异均恰在首次applied（约10.86～10.94秒），env2/14全共同轨迹一致。原成功12/25虽也应用修改，仍完成两步展开并四足接触到240秒，终态实际指令越限0，但不宣称全过程完全不变。verification.json、front-ascent-inputs.json、stage-terminal-summary.json和核验脚本保存在本地产物并同步远端。

下一步保留gn/gl成功路径及上台后4cm逐前脚展开目标，优先分析新登台低姿态的台面hold→第一前脚承重转移：实际重心、四足承重、机身高度/俯仰与规划参考是否匹配，定位失去左后脚承重前的最早偏离。先重放gp精确早期四足capture验证初次修正，再据env4完整轨迹修复后续转移；不要盲扫种子、继续加前移量或放松碰撞/关节/停稳门禁。本次录像已同步但尚未重新全片原速核验，不冒充最终视频验收。240秒箱沿诊断与24秒慢爬/原起点12秒分开；最终原起点2×32未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0061"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：四足受载时提前规划初次前脚抬升姿态；gp受控诊断运行中（2026-10-04 06:25）

实现`6b3c3b4`新增默认关闭`--climb-guidance-front-ascent-pose`，针对gn中初次前脚摆动/落台后小腿几何间隙不足、随后后脚转移被原门禁拒绝的问题。只在既有capture、四足都真实接触、恰好一前足在台上/另一前足待抬且两后足在地面、progress=0、原计划可行时检查原前脚完整摆动。原预览若受载余量不足30mrad、FK误差超限或小腿间隙不足5mm，才调用已有65点高度/姿态搜索。候选必须保留原机身/腿全路径、关节与受载余量、25mm预测三足余量、摆动和15mm落脚探测/重新承重检查；只采用完全可行替代，无解保持原计划。初次前脚落点未改，旧single-front-pose保持关闭。应用候选使用既有平滑capture和真实卸载，不在已悬空的三足预抬脚状态重新capture或重置卸载。

新增front_ascent_attempts/applied与精确早期四足capture输入，未来报告按各环境真实终态时间过滤该collector。数学fixture来自go较晚的env4三足prelift，只证明搜索候选满足既定数学门槛，不能证明早期物理capture已可行；本轮将采集匹配输入后重放核验。57项数学检查通过（修正旧support_ready测试桩缺失的只读guidance_pose_fixtures=False字段），语法/diff检查通过；去掉新增helper/state/开关调用后，guidance控制AST与修改前相同，默认关闭保持原控制。

核对远端无CLIMB训练/评估、GPU1空闲后，`climb-front-ascent-pose-20261004-gp/pose27302`于06:24:56启动，监控PID677149，GPU1。沿用gn seed27302、32环境、240秒/12100步、actor/受载复位库和其余控制参数，仅开启新front-ascent-pose；12源码哈希冻结。主录像预先选env4，密集轨迹另外覆盖19/2/18/14/17/26/0/7/12/25/29，尤其保留原成功展开12/25。该任务是240秒箱沿参考控制器诊断，不是PPO训练，不是24秒慢爬或原起点12秒验收。

下一轮先核对gp进程/status，不重复启动。完成后核验源码/actor/复位哈希、32唯一终态/缺失与原完整成功；对照gn的登台/展开、安全终止、三足比例/腾空/竖直速度/含子步历史的单足合力峰/含初始化累计力矩饱和。检查首次applied前共同轨迹和未应用环境终态，原成功12/25是否保留；用新增早期四足fixture重放候选并核查实际前脚摆动落台间隙，不能把数学可行或低冲击失败当改善。保留原登台后逐前脚4cm展开和停稳门禁。最终固定候选原起点两组未用种子各32（每组≥30且无缺失）和全片原速录像尚未开始。8806成功展开页面保留；PUSH、MuJoCo和实机暂停。

<a id="record-0062"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gm/gn配对无新增改善，定位初次前脚落台间隙；go补采抬脚前受载输入（2026-10-04 05:31）

gm/without27302与gn/with27302分别于04:52:21/04:52:01正常完成；报告SHA256分别`33248235bdd4506119adeb34319111bb3fdf793e92f1259a123b1be55cbf3ce9`、`6c5992ad363500fdbc647ce0d399911647729314bc95cb5d55b038dbfdbb0284`。两份来源/actor/evaluator与32唯一终态核验通过。新seed27302、240秒箱沿课程，两组均原完整0/32、终态32/缺失0；四足曾达到台面支撑4/32（7/12/25/29），完成两前脚展开2/32（12/25），20超时/10姿态/2低姿态。没有新增安全失败，也没有修复更多回合，不能声称提高新种子成功率。

两组总体质量相同：三足及以上99.937900%、最长腾空0、|vz|峰.737580m/s、单足合力峰202.263N、含初始化累计单环境/关节饱和最大.280s。步态排除前.10秒；合力峰含子步/历史，不是冲量。load-reserve只在env12/25各采用一次，两者仍完成展开，逐环境力峰/速度峰/腾空/三足比例/饱和与基线相同；其余30环境原终态字段逐值一致，全部32max_supported_feet一致。原8份密集轨迹均逐值一致，但它们没有覆盖12/25，不能把这次共同轨迹核验说成证明两应用回合的完整阶段过程。另有平台fixture保存两回合的原精确规划输入。env7/29没有进入展开，虽四足曾上台，207.86/208.06秒触发低姿态门禁；机身z约.379m、extension_completed=0，不能算停稳展开成功。

对gn的env4/17/18/19原USD几何重建，关节/足序映射及FK误差通过：初次右前脚摆动期间已跌破原5mm小腿-箱体间隙（env4为16.72秒、phase.665；19为17.48秒、phase.845），并在21秒左右落脚承重结束时仍只有3.355/4.557/4.306/4.255mm。下一后脚姿态搜索包含这个已经不足的初态，因此拒绝是合理门禁，不能放宽检查或继续细化终点来掩盖。env0另有后续前脚跟进后FL间隙不足，不混为同一抬脚时刻。间隙是保守primitive几何量，不宣称已发生实际碰撞。

局部固定机身数学探针排除简单“前脚落点再往前”的做法：env4在落地前最后帧把FR足x前移5mm，会使该小腿估计间隙从3.355mm降至-1.253mm；前三个同类环境方向一致。相同足点/姿态只抬机身15mm，env4终点几何间隙可到5.536mm、20mm约6.204mm，但这只是假设固定接触和姿态的几何探针，没有证明受载、抬升路径和实际跟踪可行，因此未改落点或直接加高度。front-landing-probe.json、front-body-height-probe.json、clearance-analysis.json保留结果。

实现280c186只增加只读`climb_front_swing_inputs`：沿用pose-fixtures开关，在原卸载/稳定条件允许初次地面前脚抬升之前，各环境/前脚最多保存一次，记录实际机身/足点、原参考origin/anchors/target、gravity/COM/weight/effort/软限位、原起落点、真实接触与卸载。原搜索fixture没有覆盖这个单前脚阶段，所以不能从后续失败输入假装还原。去除新增收集方法/初始化/调用后，控制AST与修改前完全一致，语法和diff检查通过；没有重新启用已失败的single-front-pose，也没有改变登台/展开控制。

确认gm/gn已结束且两GPU空闲后，`climb-front-lift-inputs-20261004-go/front27302`于05:23:48启动，监控PID670912、GPU1。32环境、seed27302、40秒/2100步，actor/受载复位库及gn全部控制参数保留，12源码哈希冻结；主录像预先选env4，额外19/2/18/14/17/26/0/7/12/25/29共12份密集轨迹。此为40秒初次前脚受载采样，不能冒充240秒诊断、24秒慢爬或12秒完整验收，也不是PPO训练。


go已于05:29:55正常结束，报告SHA256 `85a2ae25793bcfaa72258127f055effa8cc81fd0d4139e5c01981250cb5d155f`。来源/actor/evaluator及32唯一终态通过，8份原共同轨迹直到各自终止或40秒均与gn逐值一致。40秒诊断原完整0/32、终态32/缺失0、四足登台0、展开0；23超时/9姿态，三足99.715930%、腾空0、|vz|峰.540995m/s、单足合力峰202.263N、含初始化累计最大饱和.280s。这是缩短观察窗口后的统计，不与240秒直接作为改善比较。

原始报告采到58份前脚输入；发现已终止环境仍会随其他环境继续物理步进，26:1/21:1/10:1三个采样时间在其已记录终态之后。原报告原样保留，派生`front-swing-inputs.json`只保留55份有效记录，另外3份单独归档，不作为原回合证据。b3b71d2修复未来评估报告：按每环境终态时间过滤此新增collector，并显式列出剔除键。提取报告生成AST对go原数据执行，结果与55份派生产物一致；未改变控制或原报告哈希。

基于这些精确受载输入的数学重放：固定姿态只搜索0～80mm机身抬高，env17/19分别有约10/12.5mm抬高可通过原路径、关节、30mrad受载余量、25mm三足、摆动与15mm落脚探测门槛；env4没有任何可行高度。额外固定姿态XZ小范围搜索也未解决env4，不能简单统一加高度或前移。`prelift-height-probe.json`、`prelift-xz-probe.json`保留全部候选。

进一步使用已有65点高度与姿态搜索、开启真实COM旋转、完整前脚swing+reload预览，并要求完整三足受载（full_load_reserve=.03，防止partial-transfer占位绕过），env4/17/19/12/25均找到数学可行解。env4候选XY几乎不变、z增加18.542mm，需同时调整俯仰；预测三足余量37.063mm、受载/关节综合余量40.877mrad、摆动全路径最小腿间隙7.507mm。env17/19需抬高11.059/10.735mm，对应摆动间隙6.423/6.023mm；原成功12/25也有可行解，但这不证明修改后能保住物理成功。精确结果在`prelift-pose-probe.json`及脚本。未部署这些候选，没有声称物理卡点已经修复。

**下一步具体实施点**：已有精确候选可供设计“初次第二前脚抬升前的小幅机身抬升/俯仰修正”，而非重开gd那种早期全面single-front-pose。需要先处理连续承重转移：采样时env4/12/25选中前脚已经无接触，卸载分数均为1，因此不能直接调用capture_hold并把feedback_unloading重置为0给悬空脚分配支撑。需在原3足实测支撑/速度/余量门槛内，保持原关节参考连续、原卸载和落脚反馈，再验证候选过渡；或在四足仍真实承重时规划并收集匹配的早期gravity输入。只在明确安全的阶段应用，未找到可行替代不靠放宽门槛。优先修复已确定的初次前脚摆动/落台间隙，保留gl平台展开修复及当前成功路径，并在同seed27302的32环境做受控物理对照。不要再盲扫新种子或直接把局部几何抬高量写进控制。

gm/gn主录像均为固定env19、240秒/25fps/6000帧，全片解码且抽帧审阅，显示前脚落台后停滞，未覆盖12/25成功展开；SHA分别`1630a8617991680a98fb78f65291b89115c61eda06e82b662868bd5b212d958c`、`c4eaae26d7daaaf93f12088d5211d01db6837a1dd9d959e6b7d716b670d781c2`。go env4原片40秒/1000帧/SHA `c0b35e3e7a87c597f67e5ef93fef38537a8a9e32ca7b578e3477f2265fd9faf8`，已解码并检查关键帧。均不是最终原速验收。8806继续保留fy/fz。上述分析/核验/脚本在本地和远端同步；本轮结束时没有训练或评估运行，没有重复启动。最终原起点两组未用种子各32、每组≥30且无缺失和原速录像尚未开始，NAV接口另验；PUSH/MuJoCo/实机暂停。

<a id="record-0063"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gl修复登台后第二前脚展开失稳；gm/gn新种子配对验证运行中（2026-10-04 04:24）

gl/load27301于03:50:39正常完成，报告SHA256 `82159909cf24583401eee08556c40c5df1dc9037cf17928aeb082769b2375e07`，来源/actor/evaluator哈希、32唯一终态核验通过。原完整成功仍0/32、终态32/缺失0；登台3/32不变，两前脚展开由2/32增至3/32（env4/18/19）。24超时/1底座/6姿态/1低姿态，env19由姿态失败变为稳定站到窗口结束，没有新增安全终止。是展开阶段的实质修复，不是完整技能验收通过。

三足及以上99.925489%、最长腾空.040s、|vz|峰1.343221m/s、单足合力峰218.410N、含初始化累计单环境/关节饱和最大.360s。相对gk的1187.763N/.540s下降；env26既有竖直速度问题未变。步态排除前.10秒，接触合力峰包含物理子步/历史，不称冲量。29个未应用修改的环境原有终态字段与gk逐值一致，全部32的max_supported_feet一致；8份密集轨迹中，首次platform_load_applied前共同数据一致：env4在200.58秒、18在196.48秒、19在221.02秒分歧，其余5份全共同轨迹一致。修改没有改变这批已观测的登台路径。

env19保持190.46秒登台hold、218.00秒第一前脚展开，在229.46秒完成第二前脚真实落脚/重新承重，随后四脚接触持续约10.52秒。这段四脚最小竖直承重32.67N，线速最大.01162m/s、角速最大.01519rad/s，最终倾角.7365°；两前足相对登台hold前移约39.19/44.23mm。第二前脚阶段command_limit_excess始终0，valid_legs全有效，原224.44秒RR越限链条未复现。按nominal_joints+load_torque/30重建的完整受载参考最小RR余量只有18.783mrad（224.80秒），并非全过程80mrad保证；此重建量不包含actor残差，应以实际command_limit_excess核查越限，不能把规划余量当作鲁棒性证明。

env4/18仍完成两步，分别209.06/222.30秒和204.96/218.14秒；最终四足稳定约17.68/21.84秒。三条展开末态离台面中心分别.3806/.3838/.4098m，均超过原.20m条件，因此完整成功为0是真实门禁结果，不修改目标或以阶段停稳替代。大多数其它环境尚未登台，成功率不足仍是主问题。

gl env19录像`load27301-env19.mp4`为240秒、25fps、6000帧，SHA256 `4665876a15b0117d33c287e4d9bc68561f980807db6cbd4e3c3eb9f7181c4c99`。已全片解码并目视190.5/218/224.3/226/231/239.5秒关键帧，看到上台、逐前脚展开和最后站稳；这是抽帧审阅，不冒充最终全片原速验收。verification.json、extension-analysis.json、platform-pose-inputs.json、video-verification.json、env19-keyframes.jpg与复现脚本均保存本地并同步远端。8806继续保留fy/fz成功展开对照。

考虑本修复只在seed27301证实，且实际受载余量仍窄，先冻结控制源码做另一种子的开关配对。核对两GPU空闲、无训练/评估后，启动：
- `climb-load-validation-20261004-gm/without27302`：GPU0，监控PID668744，04:21:55；平台load-reserve关闭。
- `climb-load-validation-20261004-gn/with27302`：GPU1，监控PID668786，04:21:56；平台load-reserve开启。

两个独立远端checkout，均seed27302/32环境/240秒/12100步，沿用gl全部12源码哈希、actor和受载箱沿复位库、其余参数、预先固定env19主录像及另外7份密集轨迹。源代码实现仍0e0f957；计划记录当前Git来源8b8dd48，无控制改动，无新PPO。2600/2630/2800秒超时。27302在本地产物jobs/plan中未发现此前使用，本轮明确是新种子诊断，不能当作最终未用验收种子。两进程已进入Isaac并占用各自GPU。

下一轮先核对gm/gn进程/status，勿重复启动。两份报告完整后配对分析：32终态/缺失/原完整成功、登台/两步展开、安全终止及全部质量；无applied环境应保持共同轨迹，首次应用前不能提前分歧；有应用环境检查实际指令余量、真实落脚承重和停稳，尤其不能用新的安全失败换展开数量。若新种子没有触发平台阶段，不声称修复已泛化，也不反复空跑种子；转向已定位的前脚落台/机身转移间隙与未登台阻塞，保留gl展开修复。原始起点接近/NAV接口仍待独立验证。240秒箱沿诊断与24秒慢爬、原起点12秒严格分开；最终原起点两组未用种子各32且每组≥30、无缺失及原速录像尚未开始。PUSH/MuJoCo/实机暂停。

<a id="record-0064"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gk精确复现展开失败并找到更大受载余量姿态；gl仅测试登台后展开（2026-10-04 03:24）

gk/platform27301于02:48:15正常结束，报告SHA256 `be2e53b667265ed0c17e516f77d38e5aedcfd20bdc3e8572bb34c9801dc771f4`。来源哈希/32唯一终态通过，全部32终态及8份逐步轨迹与gj逐值一致，主录像切换env19和新增只读fixture没有改变这次物理结果。原完整0/32、终态32/缺失0、登台3/32、两前脚展开2/32（env4/18），23超时/1底座/7姿态/1低姿态。三足99.922286%、腾空.040s、|vz|峰1.343221m/s、单足合力峰1187.763N、含初始化累计单环境/关节饱和最大.540s；没有新增物理改善。

共采11次台面展开姿态capture（env4/18各4、19有3），全部保存完整gravity/COM/load/swing输入。用原USD和原候选算法在本地只做数学重放，11次均复现相同position/quaternion，可行性一致，margin的CPU/GPU差异均<1e-6rad。env19第二前脚capture221.0s的预测三足支撑余量35.20mm、受载指令最小余量44.678mrad，限制部位是RR膝关节（预测指令约-.976685rad，软上限约-.932007rad）。实际224.28s离地前只剩约22mrad；224.44s开始越限。因此不是规划完全缺失或单纯等落地，而是原窄受载余量未覆盖跟踪/加载变化。

数学对照还发现：仅把预览margin门槛调高，原partial-transfer的1000占位余量会让尚未达到25mm三足条件的候选被选中，不能称“完整受载姿态”。明确同时要求预测三足余量≥25mm后，65点高度搜索仍找到保留所有原路径/关节/swing约束的候选：同XY、相对原规划终点降低约13.84mm并小幅调整姿态，预测三足余量35.00mm、真实受载预览余量约92.739mrad；100mrad要求则无可行候选。记录在loaded-plan-analysis.json、full-load-reserve-probe.json和implemented-reserve-replay.json。这里证明数学可行，不代表物理已完成。

实现0e0f957新增默认关闭`--climb-guidance-platform-load-reserve`。仅四脚已经在台面、正在前脚展开且原规划可行、原完整受载预览余量<80mrad时，原65点候选重新搜索，同时要求full_load_reserve≥80mrad和预测三足≥25mm；部分重心转移不能用1000占位绕过。原机身/腿路径、关节/力矩、8cm/.35rad、实际卸载/落脚重新承重和参考平滑门槛全部保留。只采用完全可行替代，否则保留原已可行候选；是规划余量偏好，不是实际全过程安全证明。登台阶段不触发本修改，台面前脚目标仍为原4cm。新增platform_load_attempts/applied遥测。

56项数学检查、AST/diff通过；新增冻结的精确221秒fixture验证原选择复现、80mrad候选满足原全路径和三足条件、100mrad无法借partial bypass逃逸、禁止低于原30mrad门槛。未重训NAV/平地行走，也没有开启PPO。

确认gk完成、远端无训练/评估、两GPU空闲后，`climb-platform-load-reserve-20261004-gl/load27301`于03:23:46启动，监控PID666633，GPU1。与gk同seed27301/32环境/240秒/12100步、actor/受载箱沿复位库、所有既有参数和env19录像、额外2/4/18/14/17/26/0密集轨迹；仅开启platform-load-reserve。12源码哈希冻结，2600/2630/2800秒超时，未把此前gj组合提升为已通过候选。

下一轮先查gl进程/status，不重复启动。核对所有登台轨迹不变以及首次platform_load_applied前共同数据一致；检查env19第二前脚展开是否真实落脚、重新承重并停稳，RR组合指令余量和触发越限情况，保留env4/18原展开。报告全部32原完整成功/终态/阶段/安全失败、三足/腾空/速度/合力峰/含初始化饱和，不能把停在地面等待或更低冲击算完成。若改善仍仅是阶段，继续与24秒慢爬/原起点12秒验收区分。

gk env19原片实际228.24秒/25fps/5706帧，在该环境终止时结束（不能硬断言6000帧）。SHA256 `62d41351ed57c6055d9c377536596429b9575e51c5b20c3c4c35d25ba4060a75`。全片解码并审阅190.5/218/224.3/225.2/226/228秒关键帧，确认登台、第一前脚展开后再次收缩下沉；没有声称已完成全片原速动作验收。env19-keyframes.jpg与原片明确是失败诊断，8806仍保留fy/fz成功展开对照。核验/分析产物本地和远端已同步。最终原起点两组未用种子各32、每组≥30成功/无缺失及原速录像尚未开始；NAV接口独立验证，PUSH/MuJoCo/实机暂停。

<a id="record-0065"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gj新增登台回合却在第二前脚展开失稳；gk重放精确受载输入及env19录像（2026-10-04 02:22）

gj/body27301于01:49:17正常结束，报告SHA256 `8e1490fb3fb92cb740dbbcf105ae6f8434da5a8fc69eb0a489e92eb26963db47`，来源哈希和32唯一终态核验通过。原完整成功0/32、终态32/缺失0；四脚登台3/32，但完成两前脚展开仍2/32（env4/18）。新增env19登台后失稳，23超时/1底座/7姿态/1低姿态，相对gi新增1个安全终止。单足合力峰升至1187.763N（env19），不能将多一条登台当作整体改善，也不能提升本组合为完成候选。

质量：三足及以上99.922286%、最长腾空.040s、|vz|峰1.343221m/s、单足合力峰1187.763N、含初始化累计单环境/关节饱和最大.540s。相对gi力峰218.410N和饱和.360s均恶化。步态排除前.10秒，合力峰包含接触历史/物理子步，不能拿控制步净竖直力峰替代或称冲量。env26的原速度回退不变。

共同轨迹首次分歧与body_reserve_applied对应：env4=96.18s、18=96.12s、19=98.34s；env2/14/17/26/0全部共同轨迹与gi一致。env4于171.46秒四脚hold、209.04/222.28秒完成两前脚展开；env18为171.32/204.94/218.12秒。env19越过原机身间隙卡点并于190.46秒四脚承重hold，207.62秒开始左前脚展开、218.00秒完成并再次hold；221.02秒切右前脚，228.24秒姿态终止，右前脚未完成。是登台路径取得局部进展、上台后展开暴露新失败，完整任务仍未成功。

密集轨迹定位：env19于224.28秒右前脚离地，支撑余量35.4mm，三支撑足真实力约77.5/33.4/114.9N；右后腿组合指令距膝关节软上限仅约22mrad。224.44秒、右前脚摆动phase约.055时，RR组合指令首次越软限位3.136mrad，此时三足仍接触、支撑余量34.0mm，远早于落地。224.84秒RR越限已约.115rad；右后腿参考保持在已有有效值附近，机身继续下沉，另一后腿逐渐卸载。227.86秒前支撑丢失，随后姿态失败。因此不能将原因归结为“最终落脚没等稳”，也不能直接以当前swing_path_margin约.1586rad认定承重支撑腿全程有足够余量。extension-failure-analysis.json、rr-limit-onset.json保留完整事件链；没有放宽软限位、忽略负载或绕过真实落脚门槛。

下一步需对展开前接受的规划进行精确受载重放。此前pose fixture只采首次失败规划，env19该次姿态规划本身可行，因此缺少原gravity/COM/load输入；仅凭后续轨迹不能假装精确还原。评估器/采集逻辑71a2214将已有`--climb-guidance-pose-fixtures`扩展为另存climb_platform_pose_inputs：每环境最多64次台面展开capture，含可行/不可行结果及extension_completed，原feet/origin/target/quaternion、bias、软限位、load、swing全部保留批次和世界坐标。原首次失败输入结构保留。控制AST在排除只读fixture收集后完全一致，AST/diff通过；控制数学逻辑仍沿用55项已通过检查，无新控制修正。

确认gj完成、远端无训练/评估且两GPU空闲后，`climb-extension-load-inputs-20261004-gk/platform27301`于02:21:20启动，监控PID666065，GPU1。仍32环境/seed27301/240秒/12100步，同actor、复位库、全部控制参数（包括两个实验终点reserve）。主录像显式改为env19，额外2/4/18/14/17/26/0密集轨迹，原8环境均保留。12源码哈希冻结，2600/2630/2800秒超时。此为失败复现与录影，不是新PPO或已改进控制；本轮没有继续盲调余量。

下一轮先核对gk进程/status，勿重复启动。要求32终态和全部8份共同轨迹与gj逐值一致，再读取env19第二前脚展开的精确capture，比较原预测三足承重指令余量与实际离地前约22mrad、首次越限时刻，检验能否在原门禁内选择受载余量更足的姿态。保留既有登台及env4/18展开；先验证可行候选，再改控制，不把新增等待当作成功。检查env19原速失败录像，明确标注190.46秒登台、218秒第一前脚展开、228.24秒失败；不能把这条剪成成功片。

gj固定env2视频240秒/25fps/6000帧全解码，SHA256 `750e9cd1bff7e273d5a3b13de7ca76640df8591a414555c1a26a642489175268`，它未展示env19失败，也未声称全片原速动作验收。核验/分析产物已本地和远端同步。8806保留fy/fz成功展开对照。240秒箱沿诊断独立于24秒慢爬、原起点12秒；最终原起点两组未用种子各32、每组≥30成功/无缺失与原速录像尚未开始。NAV接口独立验证，PUSH/MuJoCo/实机暂停。

<a id="record-0066"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gi保留2条登台展开但完整成功未增；gj检验后脚转移机身终点余量（2026-10-04 01:22）

gi/reserve27301于00:58:37正常结束，报告SHA256 `fb6ace66ac8e3b72e603aa5275abec49a2595a2258d60ae7036bd751980d17b7`，来源哈希/32唯一终态核验通过。原完整成功0/32、终态32/缺失0；四脚登台并完成两前脚展开仍2/32（env4/18），24超时/1底座/6姿态/1低姿态，没有新增或减少安全终止。env4于170.10秒进入hold、207.78/221.02秒完成两前脚展开；env18对应171.32/204.94/218.12秒。保留了阶段成功，但尚未提高完整成功或登台数量，不提升为完成候选。

三足及以上99.925489%、腾空.040s、|vz|峰1.343221m/s、单足合力峰218.410N、含初始化累计单环境/关节饱和最大.360s。相对gh力峰299.309N和饱和.600s下降，但竖直速度峰从1.008284升高；峰值环境为26，该环境安全终止由41.96秒提前到37.86秒。不能以低冲击/少饱和宣布整体改善。步态排除前.10秒，合力峰不是冲量。

原共同轨迹首次分歧恰好等于endpoint_reserve首次应用：env4=22.30s、18=22.22s、19=24.06s、26=33.72s；env2/14/17/0全部共同轨迹与gh一致。10个环境尝试并采用过终点腿余量，env0既有落台前腿间隙缺口不受此修改影响。局部进展：env19越过原88.08秒卡点，92.84秒开始后脚leg3迈步，随后切换leg2并完成下一步，但108.72秒又遇到新的机身间隙缺口，未四脚登台。

用同USD及gi完整几何轨迹重建：env19在98.34秒切换leg2的机身转移终点规划间隙12.924mm；99.86秒重规划终点10.784mm、规划全路径最小10.604mm。实际100.44秒已降至9.951mm，108.72秒仅7.392mm，全部脚承重后再次规划失败。精确失败输入重放1053候选，461个只被机身路径间隙挡住；因为初态本身<10mm，不能靠搜索或降低门槛解决。env25仍为初态腿间隙4.696mm，env31约.005mm，另有独立缺口，未被本次修复。详细记录在clearance-analysis.json、base-clearance-events19.json、constraint-analysis.json和逐步gap轨迹。

新增默认关闭`--climb-guidance-endpoint-body-reserve`（ab93982），仅原规划已可行、四脚接触、选中地面后脚、原机身终点间隙<15mm时，使用原完整受载/swing预览及65点高度搜索找终点≥15mm的替代；若同时开启leg-reserve，替代仍须腿终点≥10mm。原机身全路径≥10mm、腿全路径≥5mm、8cm/.35rad、关节/力矩、卸载、落脚承重门槛全部不变。仅采用完全可行替代，无替代则保留原已可行选择。这是终点余量偏好，不是新的15mm全程实际保证；不重新开启失败的单前脚姿态搜索、不改变台面展开。新增body_reserve_attempts/applied遥测。55项数学检查、AST/diff通过；gi98.32秒几何/实测bias fixture只证明几何可用，未冒充精确受载重放或物理效果。

确认gi已结束、远端无其它训练/评估、两GPU空闲后，`climb-body-reserve-20261004-gj/body27301`于01:21:34启动，监控PID664914，GPU1。与gi同seed27301/32环境/240秒/12100步、actor/受载箱沿复位库及其它全部参数；只开endpoint-body-reserve，固定env2录像及4/18/14/17/19/26/0密集几何轨迹。12源码哈希冻结，2600/2630/2800秒超时；不是PPO或通过验收的控制基线。

下一轮先查gj进程/status，避免重复。检查原共同轨迹首次body_reserve_applied前一致、env4/18登台展开保留、env19实际机身间隙是否保持原10mm且能继续后脚跟进，报告全部32完整成功/终态/阶段/安全失败和质量，特别关注env26竖直速度回退。只消除缺口但静止等待不能算完成；若仍有前脚摆动/落点缺口需独立处理，不能混入本次对照。

gi录像240秒/25fps/6000帧全解码，SHA256 `33f196e1aa915e088b22c25e4e0f31f8efd6382db035c4e944bbc512b2f7da9c`，未称全片原速动作验收。核验和诊断产物本地/远端均已同步。8806仍保留fy/fz；240秒箱沿诊断独立于24秒慢爬和原起点12秒，最终原起点两组未用种子各32、每组≥30成功/无缺失及原速录像尚未开始。NAV接口独立验证，PUSH/MuJoCo/实机暂停。

<a id="record-0067"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gh精确复现并定位前脚摆动/后脚转移间隙缺口；gi检验终点余量（2026-10-04 00:31）

gh/geometry27301于10月3日23:50:23正常结束，报告SHA256 `08bbcd290938567b79889a276ee8c72aa249b5f905ea2db4b5818b4cccde920e`。来源哈希、32唯一终态通过；全部32终态和原7份共同逐步轨迹与gg逐值一致。原完整成功0/32、终态32/缺失0，登台且完成两前脚展开2/32（env4/18）；24超时/1底座/6姿态/1低姿态。独立重算质量与gg相同：三足99.910987%、腾空.040s、|vz|峰1.008284m/s、单足合力峰299.309N、含初始化累计单环境/关节饱和最大.600s。步态排除前.10秒，力峰不是冲量。本轮是诊断复现，没有新增物理成功。

用同USD、完整root quaternion、实际关节和四足位置离线重建primitive间隙，按joint_names和body_names足顺序映射。env0/19/4/18的足端FK误差均小于2.3微米，坐标映射通过。clearance-analysis.json和逐步gap-trace-env*.json给出具体连杆、接触、reload、机身目标、规划间隙和实际间隙：

- env0：右前脚第一次上台，17.48秒、摆动phase约.845时FR_calf间隙已降至4.962mm，尚未触地；21.34秒完成真实落脚/重新承重时只有4.291mm，下一后脚规划随后不可行。因此不能只归因于落地后承重，也不能靠后脚阶段细化修复。该前脚摆动阶段没有启用完整前脚swing碰撞预览，stored plan gap=0不代表实际零间隙。原成功env4/18此阶段也暂时低至3.415/3.528mm，但之后恢复；这些数值是保守几何裕量，不是实际碰撞接触证据。
- env19：70.98秒左前脚台面跟进摆动，FL_calf暂时跌破5mm，71.24秒恢复，落脚承重后约16mm。右前脚跟进末段83.98秒又短暂低于5mm，随后恢复。真正导致88.08秒持续规划拒绝的缺口发生在86.58秒切换后脚leg3后：实际起点约8.022mm，已接受的规划路径最小约5.289mm；执行这一机身转移时，87.24秒实际FL_calf降至4.946mm，88.08秒仅1.854mm。不是此时后脚已经抬起，phase一直0，四脚承重，名义卸载为0。说明紧贴原5mm规划门槛的终点不能覆盖本次受载跟踪偏差。

局部数学探针使用env19的86.56秒捕获几何/实测torque bias（来自下一条trace的reference origin/anchors），没有该时刻精确gravity/load-preview输入，因此只证明几何可用，不能称完整受载重放。保持全部原路径/关节/机身门槛，增加终点腿间隙≥10mm后，65点高度搜索可找到高约5mm的姿态，路径腿间隙约7.941mm、名义/测得bias关节余量约.0961rad。near-margin-pose.json、endpoint-reserve-probe.json保留限制与来源；小型几何fixture已提交。

新增默认关闭`--climb-guidance-endpoint-leg-reserve`，控制实现4936be3。仅原规划已经可行、四脚接触、下一只选中脚是地面后脚、原终点腿间隙<10mm时，使用原完整受载/swing预览和65点高度搜索寻找终点≥10mm的替代姿态；原全路径腿≥5mm、机身≥10mm、8cm转移/高度、.35rad角度、关节/力矩、抬脚及落脚承重门槛不变。找到完全可行替代才采用，否则保留原已可行选择。这是额外终点余量偏好，不是新的10mm全程硬门禁或已证实安全保证；不修改前脚展开，不重新开启gd失败的single-front-pose，不处理env0已存在的前脚落脚缺口。新增endpoint_reserve_attempts/applied遥测；54项数学检查、AST/diff通过，物理待验证。

确认gh结束、远端无训练/评估、两GPU空闲后，`climb-endpoint-reserve-20261004-gi/reserve27301`于00:30:50启动，监控PID663296，GPU1。32环境/seed27301/240秒/12100步，与gh同actor、受载箱沿复位库、全部其余参数、固定env2录像及4/18/14/17/19/26/0密集几何轨迹；仅新增endpoint-leg-reserve。12源码哈希冻结，2600/2630/2800秒超时。trim/retain/refine仍为配对研究组合，不是通过验收基线；无新PPO。

下一轮先查gi进程/status，避免重复启动。核对各轨迹首次applied之前共同数据与gh一致、原env4/18登台展开是否保留，重点检查env19首次应用时刻、实际间隙是否保持≥5mm且后脚能继续跟进；同时报告全部32完整成功/终态/阶段/安全失败和质量。若仅变成安全等待或新增失败，不能提升为完成候选。env0前脚摆动/落点问题需另案按轨迹验证，不通过全面重启已失败的单前脚姿态搜索或放宽门槛来混在本轮处理。

gh env2视频240秒/25fps/6000帧全解码，SHA256 `61a0b728492d1d463fcf123392d08e1756431fef031de8222a04f665d2083d50`，不声称原速全片动作验收。核验和分析产物已本地保存并同步远端，8806保留fy/fz。全部为240秒箱沿诊断，独立于24秒慢爬和原起点12秒；最终原起点两组未用种子各32/每组≥30、无缺失及原速录像尚未开始。NAV接口独立验证，PUSH/MuJoCo/实机暂停。

<a id="record-0068"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gg恢复受阻回合登台展开；gh补齐落脚承重几何轨迹（2026-10-03 23:24）

gg/height27301于22:49:31正常结束，报告SHA256 `6b82f5ca88ee3c29c86c3720551dfcdfca4505dc222f8963a087c7b091952788`，源码/actor/evaluator哈希及32唯一终态核验通过。原完整成功0/32、终态32/缺失0；四脚登台并完成两前脚展开2/32（env4/18），相对gf的1/32恢复env4，仍只是恢复gc原有2条阶段成功，不能称为最终技能完成。24超时/1底座/6姿态/1低姿态，与gf相同，没有新增安全终止。

细化首次生效前env4的4962条共同轨迹与gf逐值相同；99.24秒首次高度细化后继续前进，188.18秒四脚登台承重进入hold，221.60/234.58秒分别完成两前脚展开。末态root=(.981483,.013614,.491215)m、倾角约1.655°，距台面中心约.368768m，仍超过原.20m任务门槛。env18全部12000条共同轨迹及终态与gf相同；env2/14/17/19/26共同轨迹也全部相同。env0/19首次失败输入与gf完全一致且细化次数为0，没有绕过初态腿间隙不足。env1/5/8/22/25也各尝试细化一次，但仍未登台，不能把尝试次数算恢复成功。

gg质量：三足及以上99.910987%、最长腾空.040s、|vz|峰1.008284m/s、单足合力峰299.309N、含初始化累计单环境/关节饱和最大.600s；与gf相同。步态排除前.10秒，合力峰不是冲量。env2原片240秒/25fps/6000帧全解码，SHA256 `158c563cd9cb7d1d60a794233c83d6b89794b0bde00bd47ef54a31d301ee4475`，仅解码验证，不是env4恢复录像或全片原速动作验收。verification.json、pose-inputs.json及核验脚本已本地保存并同步远端。8806保留fy/fz成功展开对照。

下一卡点是原始承重状态的腿间隙缺口。旧逐步轨迹没有root quaternion和完整四足xyz，不能精确重建每一时刻的腿碰撞几何，也不能凭重力方向代替完整姿态。为定位间隙在哪次支撑转移/落脚/重新承重过程中跌破原5mm，评估器d046350仅新增CLIMB trace字段：robot_quaternion、feet_position、guidance_body_origin、guidance_origin_orientation、guidance_anchors、guidance_reference_age。位置统一减env_origin，四足顺序沿用现有feet selector；离线分析必须按joint_names及body_names中.*_foot的顺序映射核对。没有修改控制器或任何判据。AST解析/diff通过；移除新只读字段/分支后，原执行AST完全一致，控制器仍是已通过53项数学检查的c35f309。

确认远端无训练/评估、两GPU空闲后，`climb-clearance-trace-20261003-gh/geometry27301`于23:23:00启动，监控PID662434，GPU1，32环境/seed27301/240秒/12100步，固定env2录像、额外4/18/14/17/19/26/0密集轨迹。同gg actor/箱沿受载复位库及全部控制参数，12源码哈希冻结，2600/2630/2800秒超时。首次启动前的进程保护误匹配自身检查命令，launch未执行；随后独立核对无进程才启动，只有这一批。不是新PPO，也不是新控制候选。

下一轮先核对gh进程/status，不重复启动。完成后要求32终态及原7份共同轨迹与gg逐值一致；用同USD和实际关节/四足/完整姿态离线重建腿primitive间隙，先核对FK，再确定env0/19最先不足的具体腿/连杆、时刻及当时落脚/承重/重规划阶段，对照规划路径裕量和跟踪误差。优先在缺口出现前保留间隙，不降低原5mm腿/10mm机身门槛；此前数学“恢复例外”仍未实现或授权为控制路径。修复后的env4/18作为必须保留的回归轨迹。

以上全部为240秒箱沿课程，独立于24秒慢爬和原起点12秒。最终固定候选原起点两组未用种子各32、每组至少30成功/无缺失及原速录像尚未开始；NAV接口单独验证，PUSH/MuJoCo/实机暂停。

<a id="record-0069"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：精确输入定位采样漏解与初态间隙两类卡点；gg仅细化失败高度搜索（2026-10-03 22:23）

gf/inputs27301于21:46:11正常结束，报告SHA256 `30f49dc08ced18fd4f50af221f27a13fc0bcc6967664df36067d388549aebdba`。32终态以及原5份轨迹与ge逐值一致，来源哈希核验通过，采集25个环境首次不可行姿态的精确输入。原完整0/32、终态32/缺失0、1/32登台展开（env18），24超时/1底座/6姿态/1低姿态；三足99.910987%、腾空.040s、|vz|峰1.008284m/s、单足合力峰299.309N、含初始化累计单环境/关节饱和最大.600s。没有新增物理改善。录像SHA256 `8ceae3232813467e443c384917b9ae2a9b139e4a584f2637394001c867462929`已存，未重做/声称新的全片原速验收；8806仍为fy/fz。

本地只做冻结输入的数学分析，物理/录像仍全部远端。用相同USD、原feasible_support_pose的1053候选精确重放env4/19/0，均复现不可行。constraint-analysis.json逐项记录FK、名义/受载关节余量、加载力矩、机身/腿路径间隙及高度/角度门槛：

- env4/99.22秒：有45个候选通过其它全部检查，但机身路径间隙都不到原10mm，最好7.014mm；初态本身间隙足够（base约16.00mm、legs34.96mm）。把独立高度间隔从10mm细化到2.5mm后找到4个满足所有原门槛的候选。示例相对捕获高度抬升约5mm，机身路径间隙10.706mm、腿31.259mm、名义关节余量52.427mrad、预计加载余量62.232mrad，原关节/姿态/8cm位移边界保留。这里只证明搜索漏解，不证明真实加载动作成功。
- env19/88.08秒：269个候选除腿路径间隙外均通过，但初态腿间隙已只有1.854mm，全部路径包含这个初态，因此不可能满足全程≥5mm。env0首次后脚转移类似，初态腿间隙4.291mm，764个候选仅被腿间隙挡住。这属于实际落脚/加载后的几何裕量不足，继续密化候选不能解决；不能据此降低5mm门槛或忽略碰撞检查。

未修改碰撞门槛。纯数学对“起点间隙不足时单调恢复到原裕量”的可达候选做过独立分析，结果仅存recovery-analysis.json，没有实现或启动该例外路径。后续处理19/0应优先考察上一步落脚、承重后的实际姿态裕量与规划误差，不能将此分析当作批准降低原全程间隙要求。

新增默认关闭`--climb-guidance-refine-height`，实现c35f309：保留原搜索（包括既有扩展搜索）成功选择；仅原候选全失败且捕获初态base≥10mm、legs≥5mm时，用65点/2.5mm独立高度重试，原高度范围±8cm、角度、支撑/受载、FK、碰撞与执行器门槛全部相同。初态已有间隙缺口的环境直接跳过细化。新增height_refinements遥测。冻结gf/env4输入已保存为scripts/fixtures/climb_support_height_grid.json，53项数学检查通过，含原17点失败/65点通过、原全部路径与位移门槛检查；AST/diff通过。

确认gf结束、远端无训练/评估后，`climb-height-refinement-20261003-gg/height27301`于22:22:30启动，监控PID661861，GPU1，32环境/seed27301/240秒/12100步，同actor/箱沿受载复位库/全部动作参数，新增refine-height；固定env2录像及4/18/14/17/19/26密集轨迹，失败输入采集保留。12源码冻结哈希，2600/2630/2800秒超时。single-front-pose继续关闭，trim/retain仍仅配对实验，不是已通过基线；没有PPO训练。

下一轮先查gg进程/status，不重复启动。核对第一次细化前共同轨迹、env18原完成是否保留、env4能否从原拒绝位姿继续后脚跟进并完成展开；初态间隙不足组不能通过细化绕过原门槛。报告全部32成功/终态/安全失败、登台展开、三足/腾空/速度/接触合力峰/含初始化饱和。即使恢复env4也只是修复ge回退，不自动构成比gc更高登台成功率，更不是最终验收。

240秒箱沿课程仍独立于24秒慢爬和原起点12秒；最终两组未用种子各32/每组≥30无缺失与原速录像未开始。NAV接口单独验证，PUSH/MuJoCo/实机暂停。

<a id="record-0070"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ge制止下沉但登台降至1/32；gf采集被拒绝规划的精确输入（2026-10-03 21:19）

ge/retain27301于20:45:12正常结束，报告SHA256 `bbcd9b3419422b30febe84e919204107a41cd9ed3ce9384ba49c9f8e5f73960a`，来源哈希和32唯一终态核验通过。原完整成功0/32、终态32/缺失0，登台且完成两前脚展开1/32（env18）。24超时/1底座/6姿态/1低姿态；相对gc，7个安全终止转为超时（0/3/6/11/15/19/28），无新增安全终止。原env4登台展开变为后脚转移卡住，env18终态共同字段与gc完全相同。属于已证实的局部下沉修正，但完整任务/阶段完成没有提高，不提升为完成候选。

ge质量：三足及以上99.910987%、最长腾空.040s、|vz|峰1.008284m/s、单足合力峰299.309N、含初始化累计单环境/关节饱和最大.600s。步态排除前.10秒，力峰不是冲量。更多回合静止等待会提高三足占比，不能因此宣称整体慢爬完成。

新增遥测剔除后，env2/14/17/26全部共同轨迹与gc逐值一致；env19前4405条一致，首次分歧恰为88.10秒第一次不可行重规划拒绝。此后到239.98秒，env19固定一个body target，root z范围.36941263–.36942774m，末态.36941862m；100次拒绝未再出现原来的6.48cm累积下沉，未再底座接触。但leg3/phase0且pose_feasible=false，仍没迈后脚。env4也因不可行重规划被保留93次，240秒还卡住。下一步必须找出规划拒绝的具体约束，并寻找可实现支撑转移；不能把“站着没倒”算上台成功。

ge固定env2原片240秒/25fps/6000帧已全解码，SHA256 `2b7fef89cd11c464c345fcaab94764b3af7446ba7381369bf14700ab17aa9edd`。详细对照/指标/高度范围在verification.json，已同步远端。本轮没有将该诊断片替换8806成功展开对照，也没有声称原速全片动作验收。

为了按证据调整规划，新增仅采集数据的`--climb-guidance-pose-fixtures`（提交bdc99ba），在每个环境第一次无可行候选时保存精确feet/target/origin/quaternion、当前实测受载bias、软限位、箱体bounds、重力/力矩限额/COM的load preview、swing preview及返回结果。保留原世界坐标和批次维度；从冻结USD加载相同base/leg碰撞几何。该字段只读状态，不改控制、接触或候选判据。AST/diff检查通过；控制逻辑沿用已完成52项数学检查的ge。

确认ge结束且远端无其它训练/评估后，`climb-pose-inputs-20261003-gf/inputs27301`于21:18:59启动，监控PID659646，GPU1。与ge同seed27301/32环境/240秒/12100步、actor/复位库、全部动作参数和固定env2录像；只增加上述首个失败输入及env4/18逐步轨迹（原14/17/19/26保留）。12份源码冻结哈希，2600/2630/2800秒超时。不是新控制候选或PPO，single-front-pose继续关闭，trim与retain仅用于配对研究，未提升基线。

下一轮先查gf进程/status，不重复启动。核对32终态及原5份轨迹与ge一致；读取climb_failed_pose_inputs，在数学脚本中重放feasible_support_pose（必要时原expanded_support_pose），逐项统计FK/名义与受载关节余量、力矩余量、机身/腿碰撞路径、三足COM与高度约束拒绝，优先env4、19和首次后脚转移负裕量组。无精确重现不能靠放宽门禁或大幅姿态扫描继续试。以改善完整登台并保留展开为目标，安全等待仅作局部诊断。

仍为240秒箱沿课程，不能替代24秒慢爬或原起点12秒；最终固定候选原起点两组未用种子各32/每组≥30且无缺失及原速录像验收未开始。NAV接口独立验证，PUSH/MuJoCo/实机暂停。

<a id="record-0071"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gd单前脚搜索回退；ge独立检验不可行重规划时保留承重参考（2026-10-03 20:20）

gd/singlefront27301于19:45:14正常结束，报告SHA256 `a65887bb050f6d21fdbde3ba0ea4a73c95eac75a663109d9a27f177361acc26b`，源码/actor/evaluator和32唯一终态核验通过。原完整成功0/32、终态32/缺失0，四脚上台0/32、展开0/32；9超时/2底座/12姿态/9低姿态。相对gc新增8次安全终止（12/10/27/5/8/1/22/25），原本登台展开的env4/18改为两前脚上台后leg3/pose_feasible=false卡住。env14/17仍在第二前脚phase0失败，仅时间推迟到25.80/22.94秒。扩展姿态搜索覆盖范围未改善稳定性，明确不提升该选项为基线，后续实验关闭single-front-pose。

gd质量：三足及以上99.743931%、最长腾空.120s、|vz|峰1.008284m/s、单足合力峰402.955N、含初始化累计单环境/关节饱和最大.420s。尽管速度峰/饱和下降，登台数下降及安全失败、腾空、接触峰上升，属于回退。步态排除前.10秒，力峰不是冲量。额外5份轨迹与gc在第一前脚落稳切换前逐值一致，首次分歧分别env2=11.82s、14=13.24s、17=13.50s、19=10.92s、26=10.94s，均为切换第二前脚时；实现作用阶段核对通过，不能据此称物理效果通过。verification.json保存完整核验。固定env2原片240秒/25fps/6000帧全解码，SHA256 `2297e50fcd4a9096bbe612222af6f35724873b6eadc6bcf10ecc71acbb4922f4`，未作成功片或全片原速动作验收。

针对gc/env19证实的反复不可行重捕获与6.48cm下沉，新增默认关闭`--climb-guidance-retain-infeasible-reference`，实现c644cf1。只在已有的四脚接触、机身平静、phase0、名义卸载为0、目标已接近的重规划路径中使用：先保存原anchors/origin/target/两端姿态/load_bias/参考插值age，再执行原受载/碰撞规划。若候选不可行且之前四腿参考valid、组合指令未越限，则恢复这些已有参考，保留pose_feasible=false及失败诊断阻止抬脚。已落脚的新阶段capture及成功候选继续原流程；不改变5N释放、承重等待、关节平滑和所有门禁。拒绝后单独计时，至少1.5秒后才可再次尝试；未拒绝之前不额外改变原重规划时序。

增加replan_reference_retained/rejections/retry_age遥测。52项数学检查通过：新增三次连续拒绝不累积降低原参考、成功候选更新、未选环境不变、原参考已无效时不错误标为保留、拒绝后可行性仍false；原hold测试同步验证。AST/diff检查通过。这只是参考状态逻辑验证，能否制止物理下沉仍待远端；安全等待也不能算完整成功。

已确认gd结束、远端无其它训练/评估后，`climb-retain-reference-20261003-ge/retain27301`于20:20:04启动，监控PID655777，GPU1。32环境/seed27301/240秒/12100步、固定env2原速录像、14/17/19/26额外密集轨迹、actor/受载箱沿复位库与gc一致，12份源码哈希冻结。以gc为对照，只开retain-infeasible-reference，明确关闭gd的single-front-pose；trim仅为复现gc失败的配对诊断开启，仍不提升保留基线。不是新PPO或原起点验收。

下一轮先核对ge进程/status，禁止重复。核对首次拒绝前共同物理轨迹（新增遥测字段排除后）、原4/18登台展开是否保留、env19固定目标与身体高度是否仍缓慢下降/是否触碰箱体、拒绝次数与重新找到可行规划情况；报告全部32成功/终态/安全失败、登台/展开和质量。若只消除下沉却仍卡住，明确为局部修正，继续处理可行支撑转移与后脚跟进。不要重新开启失败的单前脚全搜索，也不要抬高trim上限或放宽门禁。

8806保留fy/fz成功展开与同窗对照，未替换回退片。240秒箱沿课程独立于24秒慢爬及原起点12秒验收；最终固定候选原起点两组未用种子各32、每组≥30且无缺失/原速录像尚未开始。NAV接口单独验证，PUSH/MuJoCo/实机暂停。

<a id="record-0072"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gc精确复现并定位下一次支撑转移失稳；gd单前脚受载姿态检查运行（2026-10-03 19:20）

gc于18:41:17完成，报告SHA256 `cadc6290b221d669f84107a3fd7c5805c1d2f8384fac7416c4a29f85ca0f0a4d`。32回合完整终态逐值与gb一致，env2全部12000条轨迹逐值一致；新增多环境遥测没有改变这次物理结果。源码/actor/evaluator manifest通过，原完整成功0/32、终态32/缺失0，登台且展开2/32（env4/18）；17超时/2底座/11姿态/2低姿态。质量同gb：三足99.836356%、腾空.040s、|vz|峰1.256650m/s、单足合力峰305.303N、含初始化累计单环境/关节饱和最大.600s。步态排除前.10秒，力峰不是冲量。verification.json与landing-transition-evidence.json保存详细时序。

新增4份逐步轨迹确认：env14/17分别13.24/13.50秒结束第一前脚落脚，前一帧reload=1、loaded_age约.20秒，第一前脚实测33.62/33.84N，机身平静；随后第二前脚一直phase0，约18秒发生支撑/姿态失稳，分别20.74秒低姿态、19.66秒姿态终止。不是第一前脚未承重就跳步。env26在33.72秒第二前脚落稳后转leg3，39.30秒起丢失接触，41.96秒姿态终止。env19从88.10秒pose_feasible=false后反复捕获更低的当前位姿；82个目标记录的root高度从.36941降至.30466m（约6.48cm），211.86秒底座接触，期间四脚仍接触且关节参考valid。它是另一类不可行规划/反复重捕获的下沉问题，不能将4种失败全部归因于补偿幅度。

源码检查发现：原完整受载姿态搜索仅覆盖两前脚都在台面的混合高度阶段及指定台面展开，恰有一只前脚在台面、另一只仍在地面时未进入该搜索。新增默认关闭`--climb-guidance-single-front-pose`（实现d611741）：仅四脚真实接触、恰一前脚在原箱面范围、另一前脚及两后脚仍在地面、下一只选中脚为地面前脚时，启用已有受载/关节/箱体及腿碰撞路径检查和姿态候选搜索。保留原8cm/1.5秒转移限制及5N卸载、真实落脚/重新承重、执行器、停稳门禁。此处只补搜索覆盖范围，不据此宣称已修好动态失稳；未同时修改env19重复捕获问题。

51项数学检查通过，包括新增左右镜像、接触丢失、第一前脚尚未上台、双前脚已上台、箱面越界/后脚阶段隔离；AST及diff检查通过。确认gc已结束、远端无其它训练/评估后，`climb-single-front-pose-20261003-gd/singlefront27301`于19:19:39启动，监控PID652829，GPU1，32环境/seed27301/240秒/12100步，同actor与复位库、固定env2录像、额外14/17/19/26密集遥测，12源码哈希冻结。相对gc只新增single-front-pose开关。为配对诊断保留gb/gc实验trim开启，未把trim或本次组合提升为保留基线。

下一轮先查gd进程/status，不重复。先核对第一前脚登台之前轨迹与gc相同，再看14/17是否完成下一次支撑转移、原4/18成功阶段是否保留，以及全部32的成功/终态/安全失败和质量。若仅消除跌倒却停住，必须报告为阶段停滞，不能算改善完成。env19下沉仍需单独处理，后续可检验不可行时保留既有承重参考、避免重捕获不断降低目标，但须有独立对照。

gc原片240秒/25fps/6000帧已全解码，SHA256 `971bdfeaf021f9ab0be6ea492c5581570b3b09c3b807ef7097ca6d9011717690`；不是新的成功片，未声称全片原速动作验收。8806仍显示fy/fz。所有阶段结果仍为240秒箱沿课程，不是24秒慢爬或原起点12秒验收；原起点两组未用种子各32/每组≥30及无缺失尚未开始。NAV接口独立验证，PUSH、MuJoCo、实机暂停。

<a id="record-0073"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gc复现新增安全失败并采集4环境密集轨迹（2026-10-03 18:16）

已读最新交接/CLIMB状态，确认远端无训练或评估、两GPU空闲后，启动`climb-transfer-diagnostic-20261003-gc/trace27301`，监控PID651109，18:16:15开始。保持gb的32环境、seed27301、240秒、actor、复位库、全部控制参数和env2录像不变；只增加env14/17/19/26从0秒起的逐控制步遥测。新增`--inspect-extra-env-indices`仅用于CLIMB读状态，主录像索引不变，各环境动作记录对应自身索引；评估器提交`6763cc0`。AST、原单环境采样体归一化等价检查和diff检查通过，物理结果待远端运行完成核验。

gb终态已细分：env17在19.66秒姿态失败、env14在20.74秒低姿态失败，两者均处第二前脚phase0且load_replan=true；env26在41.96秒姿态失败，处leg3/phase0；env19在211.86秒底座接触，处leg3/phase0、pose_feasible=false。四者终态trim均为0，不能仅凭这一帧断言补偿无影响，也不能区分此前落脚/重新承重与下一次转移的因果顺序。gb目录另存`new-failure-terminal-summary.json`。

本轮是失败复现与支撑转移诊断，不是新控制候选或PPO训练；保留基线关闭front-force-trim，本诊断为复现gb明确开启该实验参数。12文件源码/actor/复位库来源继续冻结。单次评估2600秒、子进程2630秒、监控2800秒，GPU1；不另起重复批次。

下一轮先查gc进程/status。完成后先验证32回合终态原因/时间及env2轨迹与gb一致，再从4份额外轨迹定位首个支撑丢失、落脚/重新承重、load_replan与姿态偏离的先后；未复现就不能当作gb根因证据。继续记录原完整成功/缺失、登台/展开阶段数量、三足支撑、腾空、竖直速度、单足合力峰、含初始化饱和。没有新增成功结论，8806继续保留fy/fz成功展开与同窗对照。240秒箱沿诊断与24秒/原起点12秒验收分开，原门禁、NAV接口独立验证及PUSH/MuJoCo/实机暂停均不变。

<a id="record-0074"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：gb卸载修正未提高登台率，新增4次安全终止，不提升为候选（2026-10-03 17:55）

gb/trim27301于17:43:40正常结束，监控644930已退出。报告SHA256 `098bf59e0c60d020c2648a481afcaac489acc16d4c68eea8e3e1e8ca71af8049`，源码/actor/evaluator manifest和32唯一终态核验通过。产物位于本地及远端`climb-front-unload-trim-20261003-gb`，详细对照保存在`verification.json`。本轮未启动新训练或评估。

同seed27301、32环境、240秒箱沿课程对照ga：仍只有2/32四脚登台且完成两前脚展开（env4/18），持续承重/姿态停稳阶段也是2/32；原完整成功0/32，终态32/缺失0。17超时、2底座接触、11姿态、2低姿态；ga为21/1/9/1。新增安全终止env14/17/19/26，因此本轮是回退，不能把走出局部卡点算成整体改善。

原13个前脚卸载卡点都增加了一个最大箱面支撑脚数量：原第一前脚5回合从0到1，原第二前脚8回合从1到2。但其中4回合随后新增安全终止，其余仍有后续卡点。固定env2在4.34秒开始补偿、4.88秒实际抬第一前脚、11.82秒进入第二前脚支撑转移；到240秒仍停在第二前脚phase0，补偿达到8N上限，所选脚实测竖直力5.09854N，未通过原≤5N释放门槛。此证据说明局部卸载可以推进，不能证明后续支撑稳定。

完整质量：三足及以上99.836356%（ga99.901845%），最长腾空.040s，|vz|峰1.256650m/s，单足合力峰305.303N，含初始化累计单环境/关节力矩饱和最大.600s（ga.480s）。步态排除前.10秒，力指标是合力峰而非冲量。较高三足比例也不能抵消新增安全终止。

固定env2诊断原片`trim27301-env2.mp4`为240秒/25fps/6000帧，全解码通过，SHA256 `6a0ad35d2e05716ace64776fd78479ffa9a0837d446fafc3830c76bd68489f28`；不是成功片，未宣称全片原速动作验收。8806保留fy已完成上台后展开的录像及fz同窗对照。

决策：保留原已实现的登台和上台后逐前脚展开路径，front-force-trim保持默认关闭，不提升gb为基线。下一步先定位4个新增失败在前脚落脚、重新承重、下一次支撑转移中的具体时间与载荷/姿态变化，再修正迈步后的支撑稳定性；双前脚上台后负支撑裕量的混合高度问题仍单独处理。不得直接提高补偿上限、放宽5N释放门槛或跳过重新承重等待。

240秒箱沿诊断仍独立于24秒慢爬与原起点12秒验收。20cm箱、中心位置、停稳、碰撞、执行器门禁保持；最终原起点两组未用种子各32、每组≥30且无缺失和原速录像验收尚未开始。NAV接口独立验证，PUSH、MuJoCo、实机暂停。

<a id="record-0075"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：针对前脚卸载卡点加入有界实测力修正；gb运行中（2026-10-03 17:20）

本轮先读交接和ga记录、确认远端无训练/评估且两GPU空闲，针对ga的13/32前脚实际卸载不足继续推进。新增默认关闭`--climb-guidance-front-force-trim`，实现提交`bd4e82e`；它是小幅受载参考修正，不是新PPO，不放宽原≤5N实测卸载释放门槛，不直接推进脚步时钟。

作用范围仅第一/第二只前脚从地面上台前：所选前脚x<.75/z<.10、落点高差>.10、phase0，原名义卸载已到≥.999、参考保持≥3秒，三足裕量≥25mm、其它三脚实测各>8N、机身线速度<.025/角速度<.1、姿态/摆腿/关节参考检查通过、无组合越限和加载重规划阻塞。所选脚实测>5N连续.5秒才开始补偿。以后腿、台面前脚补步或正常已卸载环境为对象的修正均未开启。

补偿以3N为目标，积分增长速率最多2N/s、上限8N，通过当前所选脚世界竖直雅可比转置`+J_z^T * trim`转换为向上虚功的关节力矩修正，再经过原75%力矩规划限幅及PD30/.6位置参考合成、原关节限位/限速/限加速度。不是向地形或接触传感器写入力，不将预计零载荷当作实测零载荷。保护条件丢失且脚未起步时以2N/s回退；实际摆腿开始后，前1/4摆腿进度内用五次平滑渐退至0，新支撑转移/hold/reset清零。原真实接触≤5N等待、三足支撑、抬脚/横移追赶、落脚/重新承重及登台后展开全部保留。该符号与幅度只经数学检查，实际卸载效果仍待远端物理验证。

50项数学检查通过（原47项加：连续停滞才触发/2N每秒速率与8N上限/不替代5N实测门槛、保护丢失回退/摆腿渐退/reset、雅可比转置补偿的向上虚功符号）。AST及diff检查通过。没有根据数学检查宣称成功率改善。

独立`climb-front-unload-trim-20261003-gb`于17:19:12启动，监控PID644930，GPU1/trim27301。与ga同seed27301、actor/受载箱沿复位库、32环境、240秒/12100步、前脚展开4cm，新增上述修正开关；12份源码冻结哈希bootstrap核验。固定录像改为预先指定env2（ga中第一只前脚卡死的环境），从0秒开始密集遥测，目的是观察卸载卡点，不是事后挑选成功回合；文件trim27301-env2.mp4。单批2600秒/子进程2630秒/监控2800秒。seed27301是与ga配对的诊断种子，不是原起点最终验收种子。

新增遥测guidance_front_trim_n/integral_n/stall_s。下轮先读进程/status，禁止重复启动；检查实测脚力是否真的降到原门槛、其它三脚是否保持受载、原5个第一前脚/8个第二前脚卡点是否走出、是否出现新增安全失败。仍必须报告全部32回合原完整成功/终态缺失、登台/展开阶段数量及六类质量指标，不能用卸载成功或单条录像代替完整任务改善。若补偿有相反效果/饱和或新增跌倒，应保留原版本并明确回退。

gb当前尚无完整结果。最近完成的ga仍原完整0/32、终态32/缺失0、2/32登台且展开；三足99.901845%、腾空.040s、|vz|峰1.256650m/s、单足合力峰305.303N、含初始化累计单环境/关节饱和最大.480s。这些是对照值，不属于gb。8806继续为fy成功展开/fz同窗对照页面，尚未替换新录像。

240秒箱沿诊断独立于24秒慢爬及原起点12秒验收。20cm箱、原中心/1秒停稳/碰撞/净高/执行器门禁不变；最终固定候选原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像仍未开始。NAV接口独立验证，PUSH、MuJoCo、实机暂停。

<a id="record-0076"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：新种子ga仅2/32登台展开；13回合前脚实际卸载不足（2026-10-03 16:35）

用户询问进展，本轮核对ga已于16:09:43正常结束，监控642963已退出，当前没有由本轮新启动的训练/评估。`climb-post-ascent-seed-20261003-ga/outputs/extend27301.json` SHA256 `4d1c0aa0a2ddce9c0e96adf6d84a95ad46907f23598dd07dfc31d09860b92e0a`与status一致，源码/actor/评估器manifest及32唯一终态核验通过。

新种子27301的32回合中仅2/32（env4/18）曾四脚上台，两者均完成两前脚展开、重新承重并在末态hold。连续四足支撑≥1秒和原速度/姿态阶段停稳≥1秒均2/32，最长满足原速度/姿态分别22.6403/19.8403秒。相比调参seed513的4/32登台、3/32展开，可重复性仍低；不同种子结果不能当作新控制版本回退，因为源码和参数未改。原完整成功0/32，终态32/缺失0；21超时/1底座/9姿态/1低姿态。不能把这两个成功阶段回合当作总体通过。

完整240秒质量：三足及以上99.901845%、最长腾空.040s、|vz|峰1.256650m/s、单足合力峰305.303N、含初始化累计单环境/关节饱和最大.480s。步态排除前.10秒，接触是合力峰而非冲量。新种子存在短暂腾空、更大竖直速度和饱和，不能只看接触峰下降宣称安全改善。

末态分组（verification.json保存环境ID及字段）：5回合卡第一只前脚卸载，8回合卡第二只前脚卸载，5回合卡双前脚上台后的第一后脚跟进支撑转移，1回合卡更后面的后脚跟进；另外11回合在登台过程中触发安全终止；2回合完成登台与展开。上述是末态所在阶段分类，不把timeout当作全部安全，也不等于每类根因已经完全确定。

13个前脚卡点有一致的直接证据：phase0，unload_fraction=1，预测所选脚载荷0，但实测所选脚竖直力5.108–7.597N，未通过原≤5N卸载门槛；三足裕量35.83–58.14mm、pose/swing可行、四腿参考valid，目标未越限，机身已平静。说明计划零载荷未实现实际零载荷，现有反馈到1后仍不能释放，不是继续等待就会走。下一步优先围绕真实接触力修正前脚抬起前的支撑转移/受载参考，保留≤5N与原三足支撑、关节/碰撞门禁，不靠放宽阈值或跳过等待“提高成功率”。双前脚上台后5个卡点的支撑裕量约−72至−79mm、pose_feasible=false，是另一类需独立处理的混合高度支撑问题。

两个完成回合的实际前脚前移：env4左/右3.719/4.073cm，env18左/右3.813/4.076cm；末态倾斜1.648°/1.460°，四腿valid、组合目标越限0、hold=true。说明“上台后展开”在新种子的已登台回合仍能复现，当前主瓶颈在登台前各阶段。此结论只基于2个完成样本，不宣称展开鲁棒性已验收。

固定env6录像未挑样，在31.42秒触发失败，原片25fps/786帧/31.44秒已全解码，视频SHA256 `0c9de2f13278e26248b67fee227ff3fd1d67917bd56acb0ade2c794da00092cd`。保留失败原片，不用事后挑选env4/18替换固定录像，也不标作240秒成功片；本轮未宣称原速全片动作验收。8806继续展示此前fy成功展开及fz同窗对照，ga核验/失败分类保存在本地和远端独立目录。

本轮无控制代码改动、无新PPO、未重复启动。下一轮先按上述13个前脚卸载卡点推进，不能把缩短等待等同于真实完成支撑转移。保持已证实的登台后逐前脚展开、20cm箱和原中心/1秒停稳/碰撞/净高/执行器门禁；240秒箱沿诊断仍独立于24秒慢爬和原起点12秒。最终原起点两组未用种子各32/每组≥30成功且无缺失与原速视频验收尚未开始。NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0077"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：同窗对照支持登台后展开改善站姿；ga独立种子复核运行（2026-10-03 15:51）

fz/holdlevel240于15:42:56完成，报告SHA256 `ff293a502351bf81583d78a8ce487cb1678e7118aaadd841c6e13a0cb6a0b252`核验通过。与fy使用同一源码261770f、actor、受载箱沿复位库、seed513、32环境、GPU1、240秒，唯一动作参数差异为关闭前脚展开。固定env6共2332个轨迹采样逐值一致至208.86秒，fy首次展开释放为208.88秒，支持将其后的差异归于展开阶段的整套支撑转移/前脚步进，而非额外观察40秒。

| 固定env6在240秒的测量 | fz只调平保持 | fy两前脚展开 |
| --- | --- | --- |
| 前后脚平均x间距 | .281419m | .321691m |
| 机身倾斜 | 9.7659° | 1.2693° |
| root高度 | .421885m | .488385m |
| root x | 1.070387m | .978399m |
| 左后/右后膝角 | −2.07318/−2.03911rad | −1.63990/−1.48759rad |

展开后平均前后脚距离多4.027cm、机身更直立、两后腿更伸展，符合用户要求的上台后舒展方向。不要表述为所有腿都更直：左前膝略更弯，右前膝略更直。支撑转移使机身x后移约9.20cm，因此距原中心目标更远；不能把姿态改善说成原完整任务成功改善。两组均4/32曾四脚登台、4/32有持续四脚支撑/原速度姿态阶段停稳≥1秒；fy仍3/32完成两前脚展开，fz没有该动作。原完整成功均0/32，终态32/缺失0，21超时/1底座/10姿态/0低姿态，未改变失败统计。

两组完整240秒质量完全相同：三足及以上99.903877%、最长腾空0、|vz|峰1.025006m/s、单足合力峰373.566N、含初始化累计单环境/关节饱和最大.460s。步态排除前.10秒，接触是合力峰而非冲量。此处时间窗口已匹配，但证据仍限于当前调参种子的阶段诊断，不是鲁棒性或原起点验收。

fz固定env6原片240秒/25fps/6000帧全解码，视频SHA256 `190d12153f57b2d256b8cb6a989a50a3766da0a1c86188eb416327688864b402`；actor/控制/评估器manifest通过，已看抽帧，未宣称全片原速验收。fz目录保存verification.json和contactsheet；fy的8806原速页面新增对照表、可展开的fz原片和matched-control-verification.json，仍以已逐脚展开的fy为主片，没有另开页面服务。全部对照产物已同步本地/远端。

本轮控制源码未改。确认fz结束且远端无其它训练/评估后，冻结当前实现，独立`climb-post-ascent-seed-20261003-ga`于15:49:01启动，监控PID642963，GPU1/extend27301。种子27301未出现在现有本地plan/jobs和远端climb*/jobs记录中；采用新种子的32环境、同一受载箱沿复位库、同一actor、240秒/12100步、前脚展开4cm、固定env6预先选定录像，2600秒评估/2630秒子进程/2800秒监控，源码12文件bootstrap核验。唯一任务参数差异为seed；不是新PPO，也不是两组原起点验收中的任一组。

下一轮先查ga进程/status，避免重复。报告32回合完整成功/缺失、曾四脚上台、完成两前脚展开、阶段停稳和六类质量指标；分清失败在前脚上台、后脚跟进、调平、支撑转移还是展开落脚，不能只选成功录像。fy/fz仍只4/32登台，独立种子复核用于检验当前参考的可重复性及定位主要失败阶段；不要恢复旧上台前前移扫描。原起点两组未用种子各32、每组≥30且无缺失和原速录像验收尚未开始。

保持20cm箱与原中心/1秒停稳/碰撞/净高/执行器门禁；240秒箱沿诊断与24秒慢爬、原起点12秒独立标注。NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0078"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fy三回合完成登台后两前脚展开；原速视频8806；fz同窗对照运行（2026-10-03 15:22）

fy/extend240于15:06:43完成，报告SHA256 `ee5b3cec550cbf8856e593f8c29d5d841d624d232fde3bf5e4b9ec9929668ccb`与远端status一致。3/32（env6/8/20）完成上台后左前、右前两次迈步和真实落脚重新承重，终态hold=true；env13仅完成第一只，第二只尚在支撑转移，不能计两步完成。4/32曾四脚箱面支撑；4/32有连续四足支撑≥1秒、且有原速度/姿态阶段停稳≥1秒，分别15.46/17.26/21.26/20.20秒。原完整任务成功仍0/32、终态32/32、缺失0，21超时/1底座/10姿态/0低姿态。阶段动作有进展，完整攀爬鲁棒性和原起点验收尚未达标。

完整240秒批次质量：三足及以上99.903877%、最长腾空0、|vz|峰1.025006m/s、单足合力峰373.566N、含初始化累计单环境/关节饱和最大.460s。步态排除前.10秒，合力峰不是冲量。支撑比例的统计窗口比fu/fv多40秒静止/支撑时间，不以比例升高宣称步态改善；其它峰值与此前一致。阶段4/32停稳也不能直接与200秒fv的3/32作同窗口优劣比较。

固定env6实测时序：187.68秒进入四脚hold，189.70–205.86秒开始9段小幅调平；208.88秒释放hold准备左前脚，213.86秒真实抬脚，219.14秒重新承重完成第1步；222.16秒准备右前脚，226.90秒真实抬脚，232.10秒重新承重完成第2步，随后保持7.90秒到240秒。相对首次展开时的实际前脚落点，终态左前x增.036665m、右前增.040720m；不是仅指命令目标4cm。终态FL/FR x=1.15465/1.16404，RL/RR x=.84171/.83359，四脚z≈.2234；末帧竖直支撑力FL/FR/RL/RR≈50.22/40.20/65.14/54.17N。四腿valid=true、组合目标越限0、unload0，两步计数2/moving=false，真实四足承重成立。

env6终态root[.978399,.024625,.488385]、gravity_z=−.999755、倾斜约1.269°，抽帧可见四脚站姿更直立。原目标中心距离约.37242m，仍在原.20m范围外，所以原完整成功为0；不修改中心门槛，也不将向原中心走完当作本次用户要求的展开动作。机身支撑转移期间后移，最终舒展程度需要结合原速录像和匹配时间的对照，不能把所有直立变化都归因于前脚前移。

与fv固定env6共1888个轨迹采样逐值一致至199.98秒（忽略新增展开遥测），已保留原登台和前200秒调平。fy中展开首次释放在208.88秒，因此需要独立240秒对照来区分额外调平时间。全批没有新增“曾上台”数量，仍4/32；不可借延长窗口宣称原200秒或24秒/12秒完整任务改善。

最新原速页面 `index.html` ，HTTP PID2066404，已请求Codex打开，页面HTTP200。固定env6、240秒/25fps/6000帧全解码，无剪接/变速/重置；视频SHA256 `566d92db2ac2281b464d9aa6a1e1ebf97a3ec783d08e3d30676275a6c17a041a`。重点看208–240秒两前脚展开，175秒起可看最后后脚登台；页面按钮只定位原片并保持1倍速。actor/控制/评估器manifest通过，已看抽帧及密集轨迹，不冒充全片原速动作质量验收。本地/远端fy目录保存verification.json、extension-timing.json、contactsheet/poster/index及原片。

为核验同窗口动作作用，确认fy/fx均结束、远端无其它训练/评估且两GPU空闲后，独立`climb-post-ascent-control-20261003-fz`于15:20:34启动，监控PID642316，GPU1/holdlevel240。与fy同冻结源码261770f、actor/受载箱沿复位库/seed513/32环境/240秒/12100步/固定env6录像，仅去掉`--climb-platform-front-extension .04`，保持调平和hold；每批2600秒、子进程2630秒、监控2800秒。不改任何控制代码、不增加时间窗口，也没有PPO训练。下轮先查进程与status，不重复；比较展开前共同轨迹、相同240秒下实际前后脚间距/关节姿态/机身位置/承重、六类整批指标和原完整成功。若只调平也能直立，应明确前脚迈步的独立贡献是落点布局及舒展变化，不能混报。

旧fx已归档，未继续上台前前移扫描。front111在14:43:47完成（SHA256 `f7ccf5cd51ff55c0619f9ed75a89ea9cd55049e29ea6eebf33dbd860505fb634`），front112在15:03:53完成（`0f1b2bb059193af7b68c2e60645d2a54e9846da068820803ce64b1c385a593f5`）；两批均0/32原完整成功、0/32曾四脚上台、终态32/缺失0、21超时/1底座/10姿态/0低姿态。三足支撑99.885963%、腾空0、|vz|1.025006、单足合力373.566N、含初始化累计单环境/关节饱和最大.460s，与fw一致。archival-comparison.json及全部原始产物保存，旧批次不再作为主线。

240秒均为箱沿阶段诊断，独立于24秒慢爬和原起点12秒验收；20cm箱及原中心/1秒停稳/碰撞/净高/执行器门禁保留。最终固定候选须原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像；当前尚未进入该验收。NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0079"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 用户最新纠正：登台后前腿再前移展开；fy已启动（2026-10-03 14:42）

用户明确：“登上去了之后，前腿应该往前走，姿态就舒展开了。”主线改为保留已能四脚上台的fu/fv路径，四脚登台并承重停稳后，再逐只前脚小步前移，最终保持舒展站姿。此前fw/fx的“上台前扩大前脚落点”不再作为主要优化方向；正在运行的fx原批次保留作归档，不继续追加参数搜索。此次操作不代表已实现舒展步态。

新增默认关闭入口`--climb-platform-front-extension .04`，基于fv保持/调平模式。先通过原四脚箱面支撑、实际抬落脚、接触/重新加载确认进入hold；机身当前段已稳定≥2秒、目标位置误差<1cm/转角误差<.025rad、四脚接触/关节参考有效/无组合越限、gravity_z<−.94、线速度<.025/角速度<.1的条件连续满足1秒后，才申请第一只前脚的支撑转移。左前、右前各一次，目标在首次释放时从实测落点加4cm并冻结，脚侧向及落点高度保持，原平台边界限制不变。只有每只脚真实抬起、落到目标邻域并通过原2N/100ms接触、600ms加载、8N/200ms承重等待，才计完成；两步完成后重新hold，不循环向前走。reset清除计数、目标和等待。

释放hold只重置脚步时钟并捕获平滑支撑参考，当帧不会直接抬腿。展开步单独启用既有平台机身姿态、41点摆腿+15mm寻触+落地受载预检；旋转COM预测也限定增加到该阶段。保留原8cm支撑转移范围、1.5秒平滑、关节限速限加速度、PD30/.6、延迟0–4、力矩/关节余量、机身1cm/腿5mm路径净空，以及实际卸载和三足支撑门槛。不修改上台前阶段，也不全局开启旧fs/ft平台动作。

47项数学检查通过：原44项，加必须hold/连续停稳才释放、边界拒绝、两次实际承重后停止/目标不累加/reset，以及fv实测终态来源的4cm前脚摆腿/寻触/落地加载几何回归与超额力矩拒绝。AST和diff检查通过。新fixture `scripts/fixtures/climb_platform_front_extension.json`来源报告SHA256 `6f831c168709d461b717129d58ef0023f303ab7daff9f4cac1cffa48e140df59`，重建重力与捕获COM平移是静态近似，不是新复位库或动力学成功证据。几何找到左前脚候选且完整摆腿余量.27646rad/间隙.08309m，但仍必须远端实测。

冻结实现提交`261770f`。独立`climb-post-ascent-20261003-fy`在14:40:42启动，监控PID640340，GPU1（启动前确认仅1MiB、无计算进程），任务extend240。GPU0原fx监控639181保持运行，候选不同/输出目录独立，未重复训练或覆盖产物。fy沿用同一actor、受载箱沿复位库、seed513、32环境、前脚上台前目标1.10/后脚.83、前身准备.24、最后后脚内收.02，固定env6录像，12份源码按manifest核验。新增遥测extension_completed/moving/stable/goals。没有PPO训练。

本次240秒仅是独立“登台后展开”诊断：原200秒登台观察之外留40秒检查调平和两个前脚小步，12100步；2600秒单批/2630秒子进程/2800秒监控。不能与200秒批次直接比较总成功而归因为动作改善，也不能将200秒以后才上台的回合算原窗口改善。下轮先核对进程，不重复启动；分别报告前200秒登台里程碑、展开启动时刻/两只脚实际位移和承重时序、后脚是否仍稳定、展开后姿态/关节舒展，以及整240秒完整成功/终态缺失与六类质量指标。核验与fv前缀直到展开首次释放是否一致，检查固定env6原速录像；目标前移或计数本身不能当作姿态改善。

当前fy还没有完成物理结果；最新已完成fw两批仍各0/32完整成功和0/32四脚上台，32终态/0缺失；三足支撑99.885963%、腾空0、|vz|峰1.025006m/s、单足合力峰373.566N、含初始化累计单环境/关节饱和最大.460s。此前fv有4/32曾上台、3/32连续承重并达原速度/姿态≥1秒，但原完整成功仍0/32。保持原20cm箱、中心/1秒停稳/碰撞/净高/执行器门禁；240秒阶段诊断独立于24秒慢爬与原起点12秒验收。最终固定候选原起点两组未用种子各32、每组≥30成功且无缺失，并检查原速录像；NAV接口单独验证，PUSH、MuJoCo、实机暂停。自动推进提示已更新为用户最新顺序。

<a id="record-0080"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：前脚前移4/8cm丢失最后后脚登台；fx缩小至1/2cm（2026-10-03 14:26）

用户要求后脚上台前前半身再向台内走一点、最终姿态舒展。fw两组均正常结束：front114在14:01:30完成，报告SHA256 `21c44e06a83e311d9c439182ba2208dde7ef76db3bdb7fcc463feaea8f22aeeb`；front118在14:20:22完成，SHA256 `6b41953fe9bf2c1750d29f3b464219c0e1bd96134940fb3d44689b815edfa37c`。每组32终态/0缺失、原完整成功0/32；曾四脚箱面支撑、连续支撑≥1秒、原速度/姿态阶段停稳≥1秒均0/32。相较fu的4/32曾上台、3/32持续支撑是明确回退，没有推广fw，也不能把前脚间距增加当改善完成。fv的3/32阶段速度/姿态停稳仍属于此前独立调平诊断，不能归给fw。

| 指标 | fw/front114 | fw/front118 |
| --- | --- | --- |
| 原完整成功 / 终态 / 缺失 | 0/32 / 32 / 0 | 0/32 / 32 / 0 |
| ≥3足支撑比例 | 99.885963% | 99.885963% |
| 最长腾空 | 0s | 0s |
| 竖直速度绝对峰值 | 1.025006m/s | 1.025006m/s |
| 单足合力峰值 | 373.566N | 373.566N |
| 含初始化累计单环境/关节饱和最大 | .460s | .460s |
| 终止：超时/底座/姿态/低姿态 | 21/1/10/0 | 21/1/10/0 |

步态指标排除前.10秒，饱和含初始化，接触为合力峰而非冲量。两组安全聚合指标与fu一致，但登台阶段退步；不能用低冲击的停住替代任务完成。保持20cm箱和所有原门禁。

固定env6证据：两组均与fu的298个共同轨迹采样逐值一致至124.50秒，之后前脚第二次补进才分叉。front114实际FL/FR x=1.15710/1.16180，front118=1.19686/1.20058；前脚确实比fu约1.12更靠台内。前脚补进发生于约125–143.5秒，第一只后脚登台发生在其后；front114于175.24秒、front118于178.36秒切换最后RR，此后phase0/lifted=false/unload0，直到200秒没有抬脚。RL已上台x≈.839，RR仍在地面x=.70476/.70320、z≈.022。前身撑起高度.25606/.25396已满足.24门槛，因此不能简单归因为前身未抬起。

最后RR起步处，front114三足支撑裕量23.75mm，front118仅.63mm，均低于25mm释放门槛；候选姿态feasible=false，候选腿路径间隙3.64/2.89mm低于5mm，摆腿预测关节余量−.42359/−.27781rad、ready=false。当前实测四腿参考仍valid、组合目标越限0，不能把被拒绝的候选预检值说成已经执行碰撞或关节越限。终态倾斜27.30°/26.21°、未进入hold。现有前移布局配合既有支撑姿态规划，未给最后后脚留下可执行的转移/摆腿路径；还不能据此否定所有更宽布局。

本地和远端fw目录保存两份报告、status、comparison.json、各自verification、contactsheet和index.html。固定env6原片均200秒/25fps/5000帧全解码，无剪接/变速/重置；actor/控制/评估器manifest核验通过，已看抽帧及密集轨迹，未宣称全片原速动作质量验收。front114视频SHA256 `b02ab82df2d814aad570a22e3b231373fa17831361f4b44bfb7d6dae4a245226`；front118 `03f9bc916bf1ac23ee1ebaeffcdb912c2e6d2069d555d06ffb5d75d4fee708b8`。8805仍保留此前fv已四脚上台的录像，fw页面明确标为回退诊断。

确认fw监控638082结束、远端无其它训练/评估及GPU计算进程后，独立`climb-front-room-fine-20261003-fx`于14:24:45启动，监控PID639181。顺序front111/front112，前脚第二次目标1.11/1.12（较fu增加1/2cm）；其余沿用fu保持版和fw冻结源码。源代码未改，12文件哈希和复位库哈希本地/远端bootstrap核验通过。仍同一actor/受载箱沿复位库/seed513/32环境/200秒/10100步，固定env6分别录像，每批2200秒、监控4600秒。调平、平台姿态/摆腿扩展继续关闭，只比较前移幅度；没有PPO训练、没有加长窗口、没有放宽关节/支撑/碰撞/落脚等待门槛。

下轮先检查fx进程和front111/front112-status，禁止重复启动。比较是否保留四脚上台/连续承重、实际前后跨度及舒展姿态，不能只看脚目标或挑一条视频。若1/2cm仍失去最后后脚，停止继续扫更大前移量，回到fu最后后脚前的实测几何，联合检查前脚布局、支撑机身姿态和整段后脚路径。200秒仍仅箱沿课程诊断，不计24秒慢爬或原起点12秒；最终候选需固定后原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像。原中心/1秒停稳/碰撞/净高/执行器门禁保留，NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0081"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fv三回合达到阶段速度/姿态停稳；fw前脚前移对比已自动启动（2026-10-03 13:49）

fv/level200于13:42:37完成，报告SHA256 `6f831c168709d461b717129d58ef0023f303ab7daff9f4cac1cffa48e140df59`与远端status一致。4/32曾四脚箱面支撑，3/32连续四脚支撑≥1秒（env6 13.22s、env8 13.70s、env20 24.40s）；这三回合现在同时满足原线速度<.15、角速度<.4、gravity_z<−.94并持续≥1秒，分别5.86、6.14、20.50秒，阶段速度/姿态指标由fu的0/32变成3/32。原中心目标完整成功仍0/32、终态32/32/缺失0，21超时、1底座、10姿态、0低姿态。不能把阶段3/32当作原起点验收成功或整体鲁棒性达标。

完整质量指标：三足及以上99.885963%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节饱和最大.460s。步态排除前.10s，接触指标是合力峰值而非冲量。各项聚合质量与fu一致，没有用少数静止片段代替整批失败统计。

固定env6：187.68秒保持锁定，189.70秒开始第1段调平，之后191.72/193.74/195.76/197.78/199.80秒开始后续段，共6段（末段在200秒截止前刚启动，不能称6段全部完成）。终态root[1.06651,.00303,.41488]，gravity_z=−.962922，倾斜从fu的23.04°降为15.65°；线/角速度低，四腿valid=true、组合目标越限全0，四脚连续承重保持。距原目标中心.28351m，仍在原.20m成功范围外；没有为取得成功修改中心门禁。platform-level-timing.json保存阶段时长、姿态和分段时序。

最新原速页面 `index.html` ，HTTP PID2061898，已请求Codex打开。固定env6、200秒/25fps/5000帧全解码、无剪接/变速/重置；与fu的1373个共同采样逐值一致至189.68秒，首次调平前的攀爬和保持已保留。actor/控制/评估器manifest通过，视频SHA256 `6393f899d3ce563cab2be8f79eea312da4c3bc6605819839430bba4554198bfd`。已看抽帧并核验密集轨迹，不冒充全片原速动作质量验收。原片、页面、verification/comparison和阶段时序保存本地并同步远端。

用户最新主线仍是“后脚上台前前半身再往台内走一点，使最终姿态舒展”。fw等待器在fv正常结束并确认无其它训练/评估后，于13:42:53自动启动，实际监控PID638082，queue-status=launched；当前运行front114（前脚目标1.14，较fu前移4cm），之后自动顺序运行front118（1.18，前移8cm）。两组仍以fu保持版为独立对照，不启用fv调平，避免混淆前脚布局本身的效果；所有落脚等待、前身抬起和原门禁保留。本轮未再开任何评估/训练或改控制源码，未抢占现有任务。

下轮先核对fw监控、front114-status与front118进程，避免重复；两组都要报告完整结果，比较前脚实际落点/前后跨度、前脚重新承重再后脚上台的时序、是否仍能逐脚登台，以及阶段停稳/原完整成功/六类质量指标。当前fw尚无完整结果，不能将fv的3/32归给前脚前移。fu/fv仍是200秒箱沿课程，不计24秒慢爬或原起点12秒验收。20cm箱、原中心/1秒停稳/碰撞/净高/执行器门禁保持；最终固定候选原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像。NAV接口独立验证，PUSH、MuJoCo、实机暂停。

<a id="record-0082"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 用户新方向：后脚上台前，前半身再向台内推进；fw已排队（2026-10-03 13:32）

用户看视频指出：前半身可在后半身上来前再往前走一点，这样全部上来后姿态更舒展、不缩在一起。下一步优先比较前脚在后脚上台前的落点间距，同时保留“前身先撑起、后脚逐只跟进、全部承重后结束迈步”。这是待验证的姿态改善假设，不保证加大前脚距离就一定更稳定。当前fu第二次前脚补进目标x1.10、后脚首次上台目标x.83；实际env6前脚约1.12、后脚约.83–.84，前后足间距约28cm。旧fg曾试1.16/1.20但没有后来的前身准备/最后后脚COM修正/上台保持，不能把旧结果当作本次组合已经验证。

新增独立`climb-front-room-20261003-fw`，顺序评估front114和front118：前脚第二次落点目标分别x1.14和1.18，较fu增加4cm和8cm。沿用已有front-followup参数与顺序：双前脚先上台、后脚地面跟到位后，前脚逐只向台内补进，真实落脚重新承重确认完成后才能继续后脚。后脚首次落点.83、前身准备.24、最后后脚内收.02、原COM范围/支撑/摆腿/参考平滑/接触等待/加载/执行器/碰撞门禁全部保持。只改前脚目标，基线采用已完成的fu保持版，不开启fv调平及fs/ft平台迈步修正，以便区分前脚布局本身的效果。

本轮不改控制源码，11项现有阶段数学检查通过；12份源码哈希按dc0de34冻结，启动bootstrap时核验。两个批次均远端Isaac、同一actor/受载箱沿复位库/seed513/32环境/200秒/10100步，固定env6分别录制front114-env6.mp4、front118-env6.mp4，完整报告两组结果。重点比较实际前后脚x间距、机身姿态/关节展开、前脚承重完成到后脚开始的顺序、是否保留两后脚上台，以及阶段保持/原完整成功与六类质量指标；不以目标变大当作实际改善。

启动前核对fv仍运行，没有中断或另起并发评估。fw等待器于13:31:20启动，PID637266，queue-status=waiting_for_fv；最多等1800秒，fv正常结束且无其它训练/评估进程才自动启动两个顺序任务。等待器外层1950秒，使用文件锁避免重复队列；每批2200秒/进程2230秒，实际运行监控4600秒（从fv结束后启动）。fv失败、资源持续占用或等待超时会写queue-status=failed，不抢占进程。下轮先读queue-status/launch-record及远端进程，禁止重复启动；front114完成时也要核对front118是否正在运行。当前还没有fw物理结果，fv结果也待收集。

最新已完成结果仍fu：4/32曾四脚箱面支撑，3/32连续承重≥1秒、0/32满足原速度/姿态停稳≥1秒，原完整成功0/32、终态32/32/缺失0。三足及以上99.885963%、腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节饱和最大.460s。步态排除前.10s，合力峰不是冲量。8804仍为fu原速保持录像，没有用未完成候选替换。

200秒箱沿课程保持/布局诊断独立于24秒慢爬和原起点12秒验收。保留20cm箱、原中心目标/1秒停稳/碰撞/净高/执行器门禁；最后固定候选原起点两组未用种子各32、每组≥30且无缺失并检查原速录像。NAV接近接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0083"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fu上台后保持承重，尚未满足直立姿态；fv做小幅四足调平（2026-10-03 13:24）

fu/hold200于13:12:36正常完成，报告SHA256 `211650a12bdfee17bf848364dd2435b88d7ebaf3aba01cb8816e281e43beb496`与远端status核验一致。三种结果分开：4/32环境曾四脚同时得到箱面支撑；3/32四脚连续支撑≥1秒（env6 13.2201s、env8 13.7001s、env20 24.4004s，env13只有.5800s）；同时满足原线速度/角速度/姿态并持续≥1秒为0/32；原中心目标完整成功仍0/32。32终态齐全/0缺失，21超时、1底座、10姿态、0低姿态。三足及以上99.885963%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节饱和最大.460s；步态排除前.10s，合力峰不是冲量。恢复到fr/fs整批安全指标，但不称完整成功改善。

固定env6在187.68秒锁定hold，之后12.32秒一直保持到200秒，没有再迈平台步；四脚连续支撑13.22秒包含锁定前的落脚确认。终态root[1.06132,.00294,.39483]，线/角速度接近零，四腿valid=true、组合目标越限全0、unload0；仍保留爬沿姿态，gravity_z=−.920227，对应倾斜23.04°，未达原−.94（约19.95°）姿态门槛。故“已上台”和“持续承重”明确成立，但原姿态停稳仍未成立。env6/8/20锁定保持，其他环境不能借此视作成功。platform-hold-timing.json记录三类结果及首次锁定时序。

最新原速录像页面 `index.html` ，HTTP PID2059940，已请求Codex打开。固定env6、200秒/25fps/5000帧全解码，无剪接/变速/重置。与fr共同1272采样逐值一致至187.66秒（忽略新增hold遥测），控制/actor/评估器manifest通过；视频SHA256 `b2504bc4bd453131e683e6c32dd2e0b2d7fcdf75933ab442b87df44b3447309d`。已看抽帧并核验密集遥测，未宣称全片原速动作质量验收。页面、核验、阶段时序、几何诊断已同步远端。

下一步保留“最后脚承重后结束迈步”的主线。新增默认关闭`--climb-guidance-platform-level`，仅在hold已锁定、四脚接触、关节参考有效、机身平静、上一段目标位置误差<1cm/旋转误差<.025rad、距上次捕获≥2秒时，规划四脚锚点不动的调平段。每段朝箱面支撑平面姿态最多转.025rad，候选高度为当前z+[0,.0025,.005]m，XY目标不变，用既有1.5秒五次平滑过渡；没有直接设状态或一次升到名义站高。达到gravity_z<−.985后不再新增段，原站稳验收−.94不变。每段重新捕获连续PD参考偏置，仍保持四足受载、unload0、不启动下一步。

调平预检使用当前COM及机身旋转偏移预测、冻结重力与四足竖直载荷估计；候选需每脚预计≥8N、力/矩残差范数<.1，保留原30mrad受载关节余量、75%执行器规划力矩上限、FK<1mm、机身路径≥1cm、腿路径≥5mm及路径关节门禁。该准静态预检不等于实际稳定；真实接触、速度、姿态、关节与完整终态仍是判断依据。候选无效保持当前目标，不强行移动。新增platform_level_segments便于确认调平是否实际执行，reset清零。

44项数学检查通过（原43项，加来源于fu终态的25mrad/5mm边界、XY不变/姿态改善、原路径门禁和执行器超额拒绝后保持原位）。冻结fu几何找到候选[1.06132,.00294,.39983]、四元数[.982255,−.063800,−.176365,.000106]、受载余量.242266rad。fixture注明腿重力重建与捕获COM平移估计，仅是静态回归。编译及git差异检查通过。

确认fu结束且远端无其它训练/评估后，独立`climb-hold-level-20261003-fv`于13:23:29启动，监控PID636126，GPU0/level200。同一actor/受载箱沿复位库/seed513/32环境/200秒/10100步、固定env6录像、170秒后密集遥测，12份源码哈希冻结核验，2200秒单批/4600秒监控。无新PPO、未加时，fs/ft平台迈步修正继续关闭。下轮先查进程/终态，比较调平前轨迹与fu，检查持续四足承重是否保留、实际姿态是否趋平、阶段原速度/姿态停稳≥1秒环境数及完整六类指标。不得把姿态目标变化或静态候选当物理改善。

200秒仍是箱沿诊断，不计24秒慢爬或原起点12秒验收。20cm箱、原中心目标/1秒停稳/碰撞/净高/执行器门禁保留；最终固定候选原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像。NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0084"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 用户纠正后的主线：四脚已上台，先验证就地站住；fu运行（2026-10-03 12:54）

用户指出“这不是上来了吗”。已确认并明确区分：录像中的四脚上20cm箱是已发生的攀爬阶段进展；原0/32还含指定箱面中心与停稳要求。后续优先验证最后脚承重后就地保持站姿并结束攀爬动作，原中心位置完整任务验收独立保留，不继续把向箱面中心挪步当作“最后脚还未上来”。回查fr、fs、ft的原supported_feet指标，三批各4/32环境曾经四脚同时得到箱面支撑；这是至少一次的阶段里程碑，不是稳定成功率，更不是30/32验收通过。

ft/platformswing200于12:41:11结束，报告SHA256 `5bb548d861a5ac28417c27df5f1224128f1b3a474c50ad38af5d2e79613ef8fc`与远端status核验一致。完整成功0/32、终态32/32/缺失0；18超时、1底座、11姿态、2低姿态。三足及以上99.875140%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节饱和最大.640s。步态排除前.10s，合力峰不是冲量。相较fs新增1姿态/2低姿态失败且最大饱和从.460s增到.640s，明确是回退，未推广ft平台动作。

ft固定env6保留此前四脚登台，与fs/fr1272个共同采样逐值一致至187.66秒；随后新平台候选调整中失稳，190.76秒因low_posture提前结束，root[1.19034,.11387,.34445]，gravity_z=−.87029，后两腿valid=false，仍未摆出下一步。说明静态全路径预检通过不等于实际支撑转移可行。原片25fps/4769帧/190.76秒全解码并对齐实际终态，视频SHA256 `2e76e6a4cd97984ac542ff98f210d1847eb56b1ddacf3f5bda80fae54f03cc4d`，源码/actor/评估器核验通过，已看抽帧；ft目录保留明确标记回退的页面/原片/verification，不替换8803为“更好”录像，未宣称全片原速动作质量验收。200秒仅最大窗口，非ft实际视频长度。

新增默认关闭`--climb-guidance-platform-hold`独立诊断。以fr已确认的攀爬为基线，不开启fs/platform-pose或ft/platform-swing。只有四脚均在原箱面内且接触、所选脚确实抬过并到phase1、既有落脚重新承重确认已通过、时钟稳定等待已满足，才锁定hold。随后阻止下一步，不重新分配落点或向中心搬动；捕获实际四脚锚点/机身位置与姿态、保存现有关节参考相对测量q的负载偏置，通过原平滑偏置过渡维持四足载荷，卸载比例固定0。没有瞬间设置机器人状态或改地形。仍使用原参考限速限加速度、PD/延迟/力矩限制；hold中的脚不再作为悬空脚跟踪，禁止支撑三角重规划，环境reset解除锁定。

这是保持“当时已落脚姿态”的诊断，不宣称姿态已直立或可实机部署。评估新增platform_stage_diagnostic，逐环境记录四脚实际箱面支撑的最长连续时长，以及同时满足原线速度<.15、角速度<.4、gravity_z<−.94的最长连续时长和≥1秒环境数；排除的只有原中心位置要求。这些阶段观测不修改成功终止，也不取代碰撞/执行器验收；历史曾出现阶段支撑、之后失败的环境仍按原完整终态计失败。不能把仅有四脚接触称稳定完成。

43项数学检查通过（原41项，加完整落脚前不锁定、锁定后不推进时钟，以及保持捕获的参考连续性/其它环境不变）；编译和git差异检查通过。核对ft结束且远端无其它训练/评估后，独立`climb-platform-hold-20261003-fu`于12:53:17启动，监控PID635574，GPU0/hold200，同一actor/受载箱沿复位库/seed513/32环境/200秒/10100步、固定env6录像、170秒后密集遥测，12份源码哈希冻结核验，2200秒单批/4600秒监控，无新PPO/未加时。下轮先查进程和终态，不重复启动；比较hold前轨迹与fr（忽略新增platform_hold_active遥测），报告四脚上台里程碑、就地原姿态/速度停稳时长和原完整成功三者，再检查安全指标与原速录像。fu运行中不得借用旧批次指标代替。

20cm箱、原中心目标/1秒停稳/碰撞/净高/执行器门禁保留。200秒箱沿保持诊断不计24秒慢爬或原起点12秒验收；最终候选仍须固定后原起点两组未用种子各32、每组≥30且无缺失并检查原速录像。NAV接近接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0085"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fs右前脚已迈出但落脚承重失败；ft补全平台摆腿/寻触/加载预检（2026-10-03 12:23）

fs/platform200于12:14:31正常结束，报告SHA256 `9077c1c76d2314e4bcdbcf4bcb0c02e3ac6cb200e4dc52bdf702a1d2d0186a4c`按远端status核验。完整成功0/32、32终态齐全/0缺失；21超时、1底座碰撞、10姿态失败、0低姿态。三足及以上99.885963%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节饱和最大.460s。步态排除前.10s，接触指标是合力峰值而非冲量。本批全部指标与fr相同，完整成功没有改善，不能将右前脚迈出当完成。

固定env6保留两后脚登台：与fr的1272个共同轨迹采样逐值一致至187.66秒；187.68秒四脚登台后的平台姿态修正才改变控制。189–192秒原右前腿起步越限消失，192秒卸载.88，194秒phase.40，196秒phase.90，均四腿valid=true。随后右前脚落在[1.34197,−.17801,.22354]附近，但触地力仅约0–1.22N，未达到原2N/100ms确认，reload一直0；向下寻触到约3.9mm时右前膝参考失效，末态寻触14.32mm、虚拟脚参考z=.21018、名义calf−.83812rad，guidance_limit_excess=.10388rad、组合目标越限.08711rad、FR valid=false。末态root[1.01265,.06971,.43675]、距目标.34448m、phase1/unload1、三足裕量34.69mm。四脚登台是此前完成过的阶段，末态右前脚尚未重新承重。

最新原速页面 `index.html` ，HTTP PID2056941，已请求Codex打开。固定env6、200秒/25fps/5000帧全解码，无剪接/变速/重置；控制/actor/评估器manifest通过，视频SHA256 `62b5178f3febdc6143cef4688b22f6954329a9b95cf2dc75dd5c3093fbcfeaa3`。查看192–199秒；已核验抽帧与密集遥测，未宣称全片原速动作质量验收。fs目录保存verification/comparison/platform-landing-timing及原片，页面/核验同步远端。

遗漏在于原摆腿预检只覆盖后脚上台，平台右前脚仅检查起步支撑姿态，没有预检完整摆腿与落脚寻触余量。新增默认关闭`--climb-guidance-platform-swing`，依赖platform-pose与原swing-preview；四脚在原箱面边界内且接触时，平台步也进入41点摆腿预检，再加5点检查既有15mm向下寻触行程，保留原关节余量/FK/腿碰撞净空。另在新落脚位置预测四足重新加载，检查原75%力矩规划余量和受载关节限位；该预测仍是冻结重力、平移COM和准静态竖直受力估计，不等于实际落脚。实际2N/100ms接触确认、600ms重新加载、8N/200ms承重等待和所有实测门禁不变。台面前的混合高度/前身抬起/逐后脚上台路径不启用新寻触/加载预检。

41项数学检查通过（原39项，加来源于fs实测终态的寻触膝限回归，以及加载力矩超额拒绝/非目标行不变）。冻结fs实测姿态在15mm寻触时预测余量−.11036rad，与物理卡点一致；零寻触附加采样与旧算法逐值一致。该fixture不是新物理复位库。编译和git差异检查通过。仍需物理评估验证是否找到可执行完整台面步，而非只更严格地停住。

核对fs完成且远端无其它训练/评估进程后，独立`climb-platform-swing-20261003-ft`于12:22:20启动，监控PID631658，GPU0/platformswing200。同一actor/受载箱沿复位库/seed513/32环境/200秒/10100步，170秒后密集遥测、固定env6录像；12份源码哈希冻结核验，2200秒单批/4600秒监控。没有追加时限或新PPO。下一轮先核对进程及完整终态，避免重复；比较187.68秒前共同轨迹，再检查新候选是否通过完整寻触预检、右前脚实际承重及整机目标/停稳，不以无冲击停滞算改善。

200秒仍为箱沿诊断，不计24秒慢爬或原起点12秒验收。保留20cm箱、原目标范围/1秒停稳/碰撞/净高/执行器门禁。最终候选固定后须原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像；NAV接近接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0086"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：最后右后脚已登台，完整任务仍失败；fs检查台面支撑转移（2026-10-03 11:56）

fr/unload200于11:37:56完成。报告SHA256 `9cb55db3ec12b189893e28fe047b73981422b4e5edeb3d540ce5219cd96e4f4c`与远端status一致，0/32成功、32终态齐全/0缺失；21超时、1底座碰撞、10姿态失败、0低姿态。三足及以上99.885963%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节力矩饱和最大.460s。步态排除前.10s，合力峰值不是冲量；更长观察窗口会改变支撑占比的分母，不能称整批安全性改善。fr只是冻结fq控制器的一次200秒观察延长，不是24秒慢爬或原起点12秒验收，无新PPO。

固定env6最后右后脚约182秒离地，187秒左右回到箱面并承重，187.68秒完成落脚等待后切换右前脚。200秒末四脚实测位置/竖直受力：FL[1.11789,.19170,.22265]/79.38N，FR[1.12337,−.17482,.22265]/44.04N，RL[.84176,.21660,.22366]/40.99N，RR[.83231,−.21203,.22350]/45.47N。最后脚确已上台，不再是还在地面；但机身距目标中心.32463m，原成功需<.20m、四脚箱面承重、姿态/速度门禁并停稳1秒，控制器停步范围更严格为.15m。故仅停止所有动作也不能满足原任务。

新卡点：187.68秒四脚上台后仍须向台内移动，`StageGuidance.capture`的可行姿态搜索原来只覆盖后脚仍在地面的混合高度支撑，all-top直接跳过；身体目标z从.39210变成.50319m，保留爬沿俯仰，右前腿组合目标超软限位，末态FR command_limit_excess=.44878rad、valid=false，phase0/unload0。不是应取消成功距离要求。冻结fr终态的纯几何/实测PD偏置回归，旧目标/旧目标姿态越限，原路径/关节守卫可找到候选位置[1.00459,.04296,.48312]、近水平四元数[.99994,0,0,−.010917]、组合余量.26019rad。仅为几何候选，不含新的物理成功证据。

最新原速视频页面 `index.html` ，HTTP PID2055884，已请求Codex打开；182–188秒可检查最后脚动作，随后检查台面卡住。固定env6、200秒/25fps/5000帧全部解码，无剪接/变速/重置；与fq共同轨迹408采样至179.5秒逐值一致，控制/actor/评估器manifest通过。视频SHA256 `fb4aa1c80a7e914559ef1a0e5c5a2b0283f5fc5750a7b984bbf6d941ec60a3d2`。抽帧、实测受力与时序已核验，未宣称全片原速动作质量验收。fr目录保留verification/comparison/last-rear-timing/platform-pose-probe及原片，页面/证据同步远端。

修正新增默认关闭`--climb-guidance-platform-pose`，仅在四脚均在原箱面边界内并接触后，把后续支撑转移接入已有feasible_support_pose、受载预估、机身/腿碰撞路径及原限位检查。原混合高度路径保留；前身先撑起、后脚卸载/落脚等待、参考限速限加速度保持。39项数学检查通过（原37项，加平台接触范围和来源于fr的旧目标越限/候选路径回归）；编译、git差异检查通过。冻结终态fixture记录报告哈希，仅几何回归，不是物理复位库。

核对fr结束且远端无其它训练/评估后，独立`climb-platform-pose-20261003-fs`于11:55:37启动，监控PID631104，GPU0/platform200。同一actor、受载箱沿复位库、seed513/32环境、200秒/10100步、固定env6录像、170秒后逐控制步遥测，2200秒单批/4600秒监控；12份载荷源码哈希冻结核验。fs只有新平台姿态检查，无延时追加或新PPO。下轮先检查进程/完整终态，避免重复启动；比较187.68秒前共同轨迹须保留最后脚登台，再看台面挪步、目标距离、停稳及完整指标。运行中不能沿用fr数据代表fs。

仍须固定候选从原起点两组未用种子各32，每组≥30且无缺失并检查原速录像；20cm箱、原1秒停稳、碰撞、净高、执行器门禁均保留。200秒箱沿诊断不得计入24秒慢爬或12秒验收。NAV接近接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0087"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 当前运行：冻结fq，单独增加20秒观察最后脚卸载（2026-10-03 11:19）

先核对fq已经结束、远端没有其它评估/训练进程。复查fq最后几秒：172.5秒切换RR时三足裕量−112.6mm、RR仍承重约82N；178.5秒摆腿预检才通过，裕量23.7mm；179秒裕量25.7mm，但角速度约.227rad/s仍在调姿；180秒裕量29.86mm、速度已平稳，卸载进度刚.066667，RR仍承重22.23N，尚高于原≤5N释放要求，unload_stable=0。现有0.5秒轨迹不足以分辨之后持续卸载还是反复恢复承重；不能先假定延时必成功。

本次不改控制器，新增独立`climb-unload-window-20261003-fr`，一次性把观察窗口从180秒增加到200秒，仅用于查看最后卸载的后续20秒。必须标为200秒诊断，不能计作180秒改进、24秒慢爬或原起点12秒验收。全部11份非评估器源码哈希与fq一致；同一actor/复位库/seed513/32环境、固定env6原速录像，20cm箱、原1秒停稳及所有碰撞/高度/支撑/执行器门禁保持。无新PPO、无动作或阈值改动。

评估器新增默认关闭`--inspect-dense-after-s`，fr设170秒，此后每个控制步（.02秒）记录固定env6状态，以查前身高度/三足裕量/角速度/受力/关节有效性/卸载进度在末段是否反复。只增加遥测，参数检查有限非负值，报告记录设置；编译及git差异检查通过，不重复运行未改控制器的37项数学检查。

远端12份载荷源码哈希核验后于11:17:59启动，监控PID628226，GPU0/unload200，10100步上限/200秒回合、2200秒单批/4600秒监控。下一轮先看进程及完整终态，不重复启动；先验证共同180秒前轨迹与fq一致，再解释新增窗口。若仍停滞，用密集记录定位具体拒绝门禁；若开始抬脚，核验实际离地、落脚受力和最终停稳，不能以时间延长本身称改善。按实际首回合结束时间核验录像帧数。

当前最新完整结果仍为fq：成功0/32、终态32/32/缺失0；21超时/1底座/10姿态/0低姿态，三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节饱和最大.460s；步态排除前.10s、力峰不是冲量。用户已看8801并询问最后脚为何不抬，已解释承重未卸完及180秒截止。fr暂无完整结果，不能沿用fq指标代表fr；最终验收仍须固定候选原起点两组未用种子各32、每组≥30且无缺失并检查原速录像。NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0088"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## fq最新录像交付（2026-10-03 11:11）

fq/lastcom180于11:02:08完成，报告SHA256 `ee95a308fa4c21ce909f6d52055eb18829b597e0005efb32c76f5181a1edb0ac`核验通过。0/32成功、32终态齐全/0缺失；21超时/1底座/10姿态/0低姿态，三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节饱和最大.460s。步态排除前.10s，力峰不是冲量。env6恢复fo前身抬起和左后脚上台；180秒末RR仍地面，phase0，卸载.066667，实测三足裕量29.86mm，前身高度.240873m，摆腿ready=true、com_rotation_active=true。末刻刚进入卸载不能称最后脚已抬起，也不能保证延长就成功。

最新原速页面 `index.html` ，HTTP PID2053085，已请求Codex打开。固定env6、180秒/25fps/4500帧全解码，无剪接/变速/重置；与fo共同轨迹至178秒/405个采样一致（排除新增遥测），actor/控制/评估器manifest通过。视频SHA256 `f624a5aef93ffc8c6ae5b7edecc6850c3485081bd5f4d6d889aaee3e9206708f`，核验/页面/原片保存fq并同步远端；未宣称全片动作质量验收。此轮用户仅索要最新视频，未新开实验。下一次继续前先读fq完整末段，判断卸载是否持续/反复、前身高度与受力等待是否限制最后一步；保留原180秒诊断与24秒/12秒验收区分及全部门禁。

<a id="record-0089"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fp过早改动前脚阶段导致回退；fq把旋转COM限定到最后后脚（2026-10-03 10:46）

fp/rotate180于10:34:19正常结束，报告SHA256 `54f15a013cc89b952bbc8ae9833d836c10f001a0961815cc5415f7292790856b`，本地按远端status核验。完整成功0/32、32终态齐全/0缺失；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s；步态排除前.10s，合力峰值不是冲量。整批聚合指标不变，但固定env6的攀爬进度明显退步，不能把它描述成“仍只差最后脚”。

env6终态机身x=.58931、z=.37343，所选FR仍在前脚跟进准备，参考从[.84106,−.17175,.22395]到[1.06106,−.17175,.2245]，后脚上台尚未执行；四脚接触、相位0、卸载0，FL受载组合目标越限.006561rad，FL valid=false。pose_feasible=false，expanded_searches=0。新COM模型在早期混合高度阶段就改变了选择，未保留fo的前身撑起和左后脚登台。fp完整原速180秒/4500帧已解码、源码/actor/评估器manifest核验、抽帧确认前脚阶段卡住；与fo共同轨迹仅至23.5秒/96个采样一致。录像SHA256 `02791acc852fa385d5133a7b04dd653b78f56a9c4b0bfa28dc21353d9454f72e`，原片、标注回退的index.html与核验保存在本地/远端fp。没有将回退录像替换此前8800的fo进展页，也不宣称全片动作质量验收。

范围修正：`--climb-guidance-rotate-com`现仅在三脚已在箱面支撑、选中后脚仍地面且目标上台、四脚接触的最后后脚准备阶段启用。首后脚、前脚、缺失支撑、地面步均保留原平移COM；还恢复原`com + positions - origin`运算顺序，避免非目标阶段因改写浮点加减顺序产生额外差异。load/partial-transfer/expanded-search继续共享同一预测；新增guidance_com_rotation_active记录真正启用时段。前身.24m准备及原净高、限位、碰撞、受力/稳定等待门禁保留。

37项数学检查通过（原36项，加最后脚范围与非目标阶段逐值相同运算回归）；编译与差异检查通过。核对fp旧进程已结束、12份源码哈希冻结核验后，独立远端`climb-last-com-20261003-fq`于10:44:37启动监控PID626984，GPU0/lastcom180，同一受载箱沿复位库/actor/seed513/32环境/180秒，固定env6录像，单批2200秒/外层4600秒，无新PPO、未延长任务时限。是否恢复fo的早期动作和接上最后脚需要本次物理结果，尚不能宣称已恢复。

下一轮先核对fq进程与终态；首要比较最后后脚前与fo的共同状态轨迹，忽略新增com_rotation_active遥测字段，不能只和失败的fp比较。确认前身撑起→左后脚登台仍保留，再检查最后脚支撑转移/卸载/摆腿/落脚和整机停稳。完整指标如实报告，低冲击失败不算完成。180秒箱沿诊断不计24秒慢爬或原起点12秒验收；20cm箱和原1秒停稳/碰撞/执行器门禁保持。最终固定候选仍需原起点两组未用种子各32、每组≥30成功且无缺失并检查原速录像；NAV接口单独验证；PUSH、MuJoCo、实机暂停。

<a id="record-0090"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fo已先撑起前身再抬左后脚，最后右后脚仍失败；fp补上转动重心预测（2026-10-03 10:18）

fo/frontrise180于09:50:52正常结束，报告SHA256 `69cfb8fdd46b5b9322ab0d3f9f59e2559274ed1dc046f4707c8d63064881d8b8`，与远端status核验一致。完整成功0/32，32终态齐全、0缺失；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s。步态排除前.10s、合力峰值不是冲量。相较fn消除一次低姿态失败，但完整成功率仍未改善。

用户要求的前身准备已在env6时序中出现：162.5秒第一只后脚登台准备，前髋至前脚高度约.22391m；164秒升至.25078m并开始卸载，166秒.25091m开始摆腿；172.5秒左后脚登台后切换最后RR，前身高度.25047m。末段约.25m，终态.253336m，没有回到原低前身动作。但RR仍地面[.70362,−.20421,.02207]，相位0/卸载0/四足接触；机身[1.06802,−.01133,.39442]，三足裕量23.83mm，摆腿余量−.197412rad，pose/swing_ready均false，expanded_searches=2。前身抬升不等于完整攀爬完成。时序与终态保留fo/front-rise-timing.json。

最新录像：`index.html` ，本地/远端`climb-front-rise-20261003-fo`，HTTP PID2048965。固定env6、180秒完整首回合、25fps/4500帧全部解码，未剪接/变速/混入重置。比较时排除新增前高两项遥测，与fn在首次前身准备改变动作前373个共同轨迹采样（至162秒）一致；actor、控制源码与评估器manifest匹配。抽帧确认前身较高、最后右后脚留地，结合实测高度/阶段/卸载记录核验动作顺序；未把抽帧当全片动作质量验收。录像SHA256 `dda482dd5b114be03d733098a30d004a2df2bf67a1113abdc9f9c74208b9c8ab`；页面、原片、核验、时序均同步远端。

冻结末态检查发现最后右后脚在抬升顶点（phase=.25）的髋关节参考约−1.107rad，超出原软限位。改变内收0/2/4cm或抬脚净空3/2/1.5cm均未在当前搜索找到满足全部门禁的姿态；没有把这些探索参数投入新物理评估。另一处模型遗漏是姿态预测只平移测量COM，忽略机身旋转带来的COM偏移。将当前COM相对机身的向量转回机身坐标，再随候选旋转/平移预测，原2cm内收/3cm抬脚条件可找到位置[1.06564,−.00660,.39842]、四元数[.974477,−.037540,−.221308,.002992]，组合关节余量.037237rad、预计三足裕量30.07mm、前身高度.255524m。保留fo/last-rear-lift-probe.json及rotated-com-probe.json。只是冻结重力与机身COM偏移的几何估计，尚未建模关节变化造成的质量再分配，不能当物理证明。

新增默认关闭`--climb-guidance-rotate-com`，依赖前身抬升准备。载荷预估、部分支撑转移选择和扩展姿态搜索统一调用同一COM预测；没有改变实测支撑/受力/平静、.24m前身高度、.18m真实卸载净高/.19m规划净高、完整摆腿、碰撞、关节余量、8cm位移/.35rad转角或执行器门禁。默认不传初始姿态时仍使用旧平移估计。

36项引导数学检查通过：原34项，加COM转动/平移一致性及来源为fo的冻结末态回归（旧平移无解、新预测候选满足原前身高度/支撑/净高/关节/角度/位移门禁）。编译与差异检查通过。确认旧评估进程已退出、12份源码哈希冻结核验后，远端`climb-rotate-com-20261003-fp`于10:17:16启动监控PID625983，GPU0/rotate180，同一受载复位库/actor/seed513/32环境/180秒、固定env6录像，2200秒单批/4600秒监控。无新PPO、未延长时限，前身抬升保持开启；fp物理结果待验证。

下一轮先查fp进程与终态，不重复启动；比较首后脚动作是否保留、前身实测高度是否满足后脚释放时序、最终右后脚是否真正卸载/登台承重/整机停稳。按完整成功及全部六类指标报告，不把低冲击失败或几何可行当完成。180秒箱沿诊断仍不计24秒慢爬或原起点12秒验收；20cm箱及原1秒停稳/碰撞/执行器门禁保留。最终固定候选需原起点两组未用种子各32、每组≥30成功且无缺失，检查原速录像；NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0091"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 用户纠正主线：后脚登台前先撑起前半身；fo加入实测前身抬升准备（2026-10-03 09:32）

运行更新（09:34）：等待器已确认fn正常退出并于09:33:42启动fo，监控PID622654；queue-status=launched，launch-record已同步本地。无需再次启动。fn完整结果已收回并核验SHA256 `9bba0c73e743c3ea8235e40d3efcd9e729ff51ac52ea24dd82799ac422fc05b4`：0/32成功、32终态齐全/0缺失，20超时/1底座/10姿态/1低姿态；三足及以上99.873744%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计单环境/关节饱和最大.460s。fn新增一次低姿态失败，不能称内收调整已改善。fn录像尚未核验，保留原片待下轮分析。fo仅确认启动，尚无物理成功证据。

用户明确指出：前半身已经上台，后脚上去前应该先把前半身撑起来，不能继续压低两前腿。后续优先按“箱面双前脚承重→前腿平缓伸展、前身抬起→支撑转移与后脚卸载→逐脚跟进”推进；不要把最后脚内收搜索继续当唯一主线。已有fm记录支持存在该问题：后脚跟进时前膝反复屈曲，175秒rootz约.33466m；末态前髋至前脚垂直跨度只有FL .23497m、FR .23432m。机身中心保高不等于前半身已经充分撑起，亦不能宣称这已解释全部失败。

新增默认关闭`--climb-front-raise-height .24`（fo诊断参数，非验收门槛替代）。在双前脚箱面接触、选中后脚执行上台的阶段，以两前髋到对应前脚的最小垂直高度衡量前半身是否抬起，使用真实USD髋位置并考虑机身俯仰/横滚。规划在四脚接触时分段向.24m推进：每段候选至少比当前提高1cm或达到.24m，达到后保留该高度。前身未达标进入重新规划需求；实际卸载与释放后脚都要求实测高度≥.24m，同时仍满足原平静、三足裕量、受力、净高、摆腿及稳定等待条件。不是直接把前膝伸到关节极限，也没有放宽任何原限位/碰撞/停稳/执行器门禁。

记录新增guidance_front_raise_height和guidance_front_raise_ready，便于核验“先起身再抬后脚”的实际时序。与旧批次比较前缀时应忽略这两个新遥测字段，只比较共同控制/状态字段。默认关闭时行为保持原分支，只有显式开启后新增前身高度要求。落脚等待、参考限速限加速度、1.5秒平滑转移和原后脚步序保留。

34项数学检查通过：原33项，加前身高度的俯仰/平移不变性、阶段提高及达标后保高；现有实测释放回归扩展验证前高.23m不释放、.245m且原稳定等待后才释放。编译与git差异检查通过。冻结fj第一只后脚登台前几何诊断，原前身高度.232638m；开启新约束后扩展搜索找到前高.245118m、组合关节余量.137327rad的候选，位置[.93519,−.05773,.39191]，仍通过原支撑/路径/关节检查。此为几何可行性，不能当作前腿已在物理中成功撑起；fo/first-rear-front-rise-probe.json保留结果。

远端旧fn评估仍在运行，没有中断或重复启动。新`climb-front-rise-20261003-fo`已冻结12份源码哈希，GPU0同一actor/受载复位库/seed513/32环境/180秒，保留fn最后脚2cm内收以单独比较新增前身准备，固定env6录像。09:32:04启动等待器PID622646：最多等fn600秒、确认其正常结束且无任何其它评估/训练进程，再启动fo/frontrise180；失败写queue-status.json，不并发抢占。队列自身650秒外层上限，实际评估2200秒单批/4600秒监控；下轮必须先读queue-status与launch-record再查进程，禁止再启动一份。此时fo物理效果未验证。

最近完整批次仍为fm：成功0/32、终态32/32、缺失0；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s。步态排除前.10s，合力峰值不是冲量。fn结果待收集，fo未有完整结果，不能沿用旧指标声称新动作改善。仍是180秒箱沿诊断、无新PPO，不计24秒慢爬或原起点12秒验收。20cm箱和原1秒停稳/碰撞/执行器门禁保留；最终固定候选需原起点两组未用种子各32、每组≥30且无缺失，检查原速录像；NAV接口单独验证；PUSH、MuJoCo、实机暂停。

<a id="record-0092"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fm保高成功但最后脚仍卡住；fn仅减少最后地面后脚内收（2026-10-03 09:18）

fm/heightprogress180于09:02:28正常结束，报告SHA256 `fc90dce59bfba268178ae269c1ff3874b214ac0866d875f2b8c10683e8a4957a`，本地按远端status核验一致。完整成功0/32，32终态齐全、0缺失；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s。步态排除前.10s，合力峰值不是冲量；完整成功率未改善。

env6的机身高度回退已消除：180秒root=[1.01530,.04346,.39164]，目标高度.39164，最后RR仍在地面[.70001,−.20110,.02237]，三脚在箱上。实测三足裕量22.83mm低于原25mm准备卸载门禁；完整摆腿余量.000596rad低于.03rad，ready=false、pose_feasible=false，expanded_searches=3，卸载0、相位0、四脚接触、无目标越限。不能把保高视作完成攀爬。诊断保存fm/last-rr-diagnosis.json。

最新录像：`index.html` ，本地/远端`climb-height-progress-20261003-fm`，HTTP PID2043056。固定env6、180秒完整首回合、25fps/4500帧全部解码；未剪接、变速、混入重置。与fl在保高首次改变动作前405个共同轨迹采样（至178秒）逐值一致，actor、控制源码和评估器manifest匹配。抽帧核对末段机身保高与右后脚留地，未宣称全片动作质量验收通过。录像SHA256 `0161826664d25586796e8012320529285d5b60d319fb7e32a08eda8d8ec034ba`；页面、原片、核验和诊断均同步远端。

冻结fm末态保持原8cm/.35rad/25mm支撑/.19m净高/.03rad关节及完整摆腿和路径门禁，扫描最后RR横向内收：6cm、8cm没有找到姿态；4cm找到组合余量.04464rad，2cm找到.05469rad，0cm找到.04574rad。2cm候选位置[1.05415,−.00030,.39307]，四元数[.973502,−.057024,−.221451,−.001601]。这是冻结重力及平移COM估计下的几何结果，不是物理证明；无解扫描也不是不可行证明。保留全部结果fm/last-rr-path-probe.json。转动时真实重心变化仍由实测支撑门禁兜底，尚未改COM模型。

新增默认关闭参数`--climb-last-rear-swing-inset .02`，要求已有angle-coverage及所有原检查。只在三脚已在箱面接触、所选后脚仍地面且目标上台时覆盖原6cm内收；前脚、第一只上台后脚、地面补进保持原选择。内收量在每次换脚时锁定，完整摆腿期间不随足高/接触变化；规划预检、实际脚轨迹和横移完成门禁共用同一锁定值，落脚仍恢复原宽度。没有放宽原接触、净高、限位、碰撞、停稳和执行器门禁。

33项引导数学检查通过（原32项，加最后地面后脚适用范围及来源为fm的冻结末态回归：6cm未找到解、2cm满足原高度/角度/位移/支撑/关节门禁）。编译与差异检查通过。核对无既有仿真后冻结核验12份源码，独立远端`climb-last-inset-20261003-fn`于09:16:54启动，监控PID621124，GPU0跑inset180，32环境/seed513/180秒、固定env6录像，2200秒单批/4600秒外层时限。使用同一受载复位库与actor，无新PPO、未延长时限；物理结果待下一轮。

下一轮先查fn进程/完整终态，不重复启动。比较进入最后后脚前与fm的共同轨迹，检查最后RR实际卸载、抬升、落脚承重及最终停稳；如果180秒末仍进行中或卡住，如实标注。180秒箱沿课程诊断仍不计24秒慢爬或原起点12秒验收；20cm箱、原1秒停稳/碰撞/执行器门禁保留。最终固定候选需原起点两组未用种子各32、每组≥30成功且无缺失，并检查原速录像；NAV接口单独验证，PUSH、MuJoCo、实机暂停。

<a id="record-0093"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fl最后脚摆腿可行但高度回退，fm保持已获得的卸载净高（2026-10-03 08:48）

fl/angle180于08:33:10正常结束，报告SHA256 `1e7d95d59c23240750f65a0b4c3f17834a4cd6a78a0413c72ab5a27283259a0c`，本地与远端status核验一致。完整成功0/32，32终态齐全、0缺失；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s。步态排除前.10s，合力峰值不是冲量。整批成功率与上述指标未改善，没有稳定攀爬验收结果。

env6保留左后脚上台，最后RR仍在地面。约177秒扩展搜索选择了可行姿态，目标机身z=.3909m；178.5秒实测z=.3911m，但实测三足裕量约19mm，仍不足25mm准备卸载要求，于是继续横向转移。原规划允许预测COM仍在三足边界外的四足中间姿态暂不满足卸载净高；这次选择了较低z=.3611m的中间目标。180秒实测rootz=.361809m，三足裕量30.17mm、摆腿余量.066879rad且ready=true，然而剩余三脚箱面以上净高只有.161224m，低于原.18m卸载门禁，故卸载比例0、RR仍地面承重。此前重规划条件只包含支撑裕量、姿态/摆腿可行性和限位，不包含实测净高不足，因而无法主动恢复。问题和末段轨迹保存在fl/height-regression-analysis.json。

最新录像：`index.html` ，本地/远端`climb-angle-coverage-20261003-fl`，HTTP PID2041885。固定env6、180秒完整首回合、25fps/4500帧全部解码；未剪接、变速或混入重置。与fk在首次角度扩展改变动作前402个共同轨迹采样（至176.5秒）逐值一致，actor、控制源码及评估器manifest匹配。已看抽帧核对抬升后下降、最后脚留在地面，结合受力和净高数据定位原因；未把抽帧核验当完整动作质量验收。页面、原录像、核验与诊断同步远端。

修正load-preview中的部分转移衔接：当当前姿态已经达到剩余三脚以上.19m规划净高，后续四足中间转移也必须保留.19m，不能因预测COM略在三足边界外而重新降下机身；尚未获得该高度的初始四足中间转移继续允许。实测净高低于原.18m时纳入重规划需求，仍需四足接触、平静、当前转移到位及未卸载才能重规划。原预计25mm/实测支撑、完整摆腿、载荷、路径、8cm位移、.35rad姿态、关节限位、落脚等待及原终止门禁均保留，没有放宽高度门禁。

32项引导数学检查通过（原31项，加最后地面脚的中间转移保高回归：已抬高时禁止.3911→.3611m回退、低初态四足转移仍允许）；编译与git差异检查通过。这些仅证明规划规则回归，物理效果未确认。已核对旧评估退出，12份源文件哈希冻结核验后，远端`climb-height-progress-20261003-fm`于08:46:08启动，监控PID620568，评估PGID620570/PID620571，GPU0跑heightprogress180，32环境/seed513/180秒、固定env6录像，2200秒单批/4600秒外层时限，已到200步。保持同一actor、复位库和已有参数，无新PPO、未延长任务时限。

下一轮先查fm进程与完整终态，不重复启动；关注机身抬升是否保留、最后RR是否实际卸载/抬起/落脚，以及是否只是180秒到期仍进行中。对比fl末段前缀和全部失败原因，按实际结果报告；不能把规划可行或低冲击失败当完成。180秒箱沿诊断不计入24秒慢爬或原起点12秒验收；20cm箱及原1秒停稳/碰撞/执行器门禁保留。最终候选仍需原起点两组未用种子各32回合、每组≥30成功且无缺失，并检查原速录像；NAV接口单独验证，PUSH、MuJoCo和实机暂停。

<a id="record-0094"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fk左后脚登台承重，最后右后脚仍卡住；fl补查原角度门禁内遗漏的姿态（2026-10-03 08:19）

fk于08:01:52正常结束，报告SHA256 `4c63a1b54ff2781b1600e9f7a6c08d83c16bc78a063d833d55544d6778b1f484`，本地按远端status核验一致。完整成功0/32，32终态齐全、0缺失；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s。步态排除前.10s；合力峰值不是冲量。局部脚序推进，但完整成功及上述整批指标未改善。

env6首次扩展搜索在162.5秒采样已触发，左后脚约166秒开始抬升，170—173秒落到箱面承重，174秒已切换最后RR。180秒RL足约[.83762,.20778,.22360]，竖直接触力30.93N；RR足约[.69992,−.20445,.02239]仍在地面，当前参考起点[.68947,−.20966,.02322]、落点[.83,−.20966,.2245]。机身[1.03318,−.00363,.32932]，实测三足裕量23.13mm；最后RR相位0、四足接触、卸载0、无组合目标越限，摆腿余量−.23895rad，ready=false。expanded_searches=2、expanded_pose=false；没有重复宣称最后脚已完成。

最新录像：`index.html` ，本地/远端`climb-edge-pose-20261003-fk`，HTTP PID2040236。固定env6、完整180秒首回合、25fps/4500帧全部解码；未剪接/变速/混入重置。首次扩展搜索前373个共同轨迹采样（至162秒）与fj/edgeprep180逐值一致；actor、控制源码、评估器manifest核验通过。抽帧显示左后脚登台和最后阶段停滞，终态受力确认承重；没有把单条视频或抽帧核验当完整动作质量验收。页面、核验、完整结果和抽帧同步远端，新录像不是正在运行的fl。

末态原扩展搜索仍无解。排查发现总姿态转角门禁一直为.35rad，但每个roll/pitch偏移样本只覆盖±.25rad，遗漏门禁内部分方向。保持原全部门禁，把采样覆盖扩大为每轴±.30rad，32768样本可找到位置[.998721,.052094,.393172]、四元数[.981855,.058247,−.178986,.023063]，组合关节余量.030572rad、预测三足裕量28.31mm，满足原总转角≤.35rad、位移≤8cm、卸载净高≥.19m及路径/摆腿检查。余量仅略高于原.03rad要求，仍需物理验证；不是稳定或可交付证据。更宽范围的离散扫描未找到解，不构成不可行证明，全部扫描结果保留于fk/rotation-coverage-probe.json；原无解记录在last-rr-pose-probe.json。

新增默认关闭`--climb-guidance-pose-angle-coverage`，依赖已有edge-pose-search。原±.25rad搜索有解时逐环境保留原选择；只有原搜索失败的环境补查±.30rad，仍执行原.35rad总角度过滤及所有载荷、净高、支撑、碰撞、限位、平滑和落脚等待门禁。没有提高总姿态角上限。31项引导数学检查通过（原30项加来源为fk的最后RR几何回归），确认原覆盖无解、新覆盖候选满足原角度/高度/8cm位移/25mm支撑/.03rad关节余量。测试fixture仅保存必要冻结几何及报告哈希。编译与差异检查通过。

核对fk及旧评估进程已退出后，独立远端`climb-angle-coverage-20261003-fl`于08:16:50启动监控PID620007，GPU0运行angle180：同一受载箱沿复位库、actor、seed513/32环境/180秒，固定env6录像，单批2200秒、外层4600秒。没有延长时限，没有新PPO。下一轮先查进程/完整结果，核对保留第一后脚登台、最后右后脚是否真正卸载/抬起/落脚，以及前缀轨迹与fk一致性；如只到进行中或再次卡住，须按实际阶段记录，不能当成功。新视频按终态核对首回合帧数。

180秒箱沿诊断不计入24秒慢爬或原起点12秒验收。20cm箱、原1秒停稳、碰撞、执行器及高度门禁保留；最终固定候选仍需原起点两组未用种子各32回合，每组≥30成功、无缺失，并检查原速录像；NAV接近与CLIMB接口单独验证。PUSH、MuJoCo、实机暂停。

<a id="record-0095"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fj后脚补进完成但卡在首只后脚登台；fk扩大该处姿态搜索（2026-10-03 07:48）

fj两批均结束：heightguard180于07:07:01、edgeprep180于07:23:57正常退出，完整成功各0/32、终态各32/32、无缺失，均21超时/1底座/10姿态/0低姿态。两批三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节力矩饱和最大.460s。步态排除前.10s；合力峰值不等于冲量。消除fi新增低姿态失败并未解决完整攀爬，不能算完成。报告SHA分别为`a17600668597968dc4748aed2a8ec7f4a7fa92327bd742a8fa5c9b9538460fdc`和`7a4e76541b507cada228ad0f506afe142a3575ef8d407a7a988a3cbb32c1dae1`，按远端status核验；fj/comparison.json同时保留两批。

edgeprep180的env6完成双后脚地面补进，但**两只后脚仍在地面，停在第一只后脚RL上台准备；此版未保留此前RR已登台的进度**。180秒末FL/FR约[1.10916,.18698,.22333]/[1.11363,−.17960,.22336]，RL/RR约[.69107,.20288,.02265]/[.69634,−.20478,.02270]。机身[.98010,−.01046,.39292]，所选RL落点[.83,.20274,.2245]；实测三足裕量36.76mm，卸载0、相位0、四足接触、组合目标无越限，摆腿余量−.08843rad、ready=false。原候选列表无解，而扩展搜索只允许三脚已在箱上，因此expanded_searches=0。不能把这一状态继续称为“最后一只脚卡住”。

新原速录像：`index.html` ，本地/远端fj，HTTP PID2039142。固定env6、完整180秒首回合、25fps/4500帧全部解码；未剪接、变速或混入重置。首次补进动作变化前335个共同轨迹采样（至143秒）与heightguard180逐值一致，actor、控制源码和评估器manifest哈希通过。抽帧确认两只后脚均未登台和末段停滞；仅完成抽帧/时序/数据核验，未宣称动作质量验收。页面、verification.json、两批比较与抽帧已同步远端；新录像对应fj，不是正在运行的fk。

在fj冻结末态调用原扩展搜索，可找到机身位置[.933464,−.071960,.369039]、四元数[.983200,.038283,−.177987,.013111]，组合关节余量.150835rad、预测三足裕量49.09mm，满足原机身/腿部路径、完整摆腿、卸载支撑高度、载荷与限位要求。另一后脚此时仍在地面，最低支撑面计算保持原规则；最后地面脚卸载时仍必须满足箱面以上净高门禁。该结果是冻结重力/COM估计下的几何可行性，不是物理成功，记录fj/edge-pose-probe.json。

新增默认关闭`--climb-guidance-edge-pose-search`，依赖rear-edge-prep及全部已有预检。只有双前脚箱面承重、双后脚都到x≥.68且仍在地面、四脚接触、选中后脚执行上台、原姿态候选失败时，允许第一只后脚使用原32768样本扩展搜索。原最后后脚触发条件仍保留；较早的后脚地面跟进、前脚及缺失承重条件不会被新分支放行。原8cm位移/.35rad转角、名义/受载关节余量、FK、底座/腿部净空、预计.19m/实测.18m卸载高度、接触等待、平滑及执行器门禁保持。30项引导数学检查通过，含原29项及新范围/承重/准备位置回归；编译及差异检查通过。

确认fj及旧评估进程已结束，独立远端`climb-edge-pose-20261003-fk`于07:45:30启动监控PID619451，仿真PID619454/PGID619453，GPU0跑edgepose180：同一受载箱沿复位库/actor/seed513、32环境、180秒，固定env6录制首回合；单批2200秒、外层4600秒。已看到600步正常进度，无重复进程。无新PPO，仍先验证攀爬参考动作。

下一轮先看fk进程/终态，核对首次expanded_searches前轨迹与fj是否一致、首后脚是否实际登台、最后后脚能否衔接，以及完整成功/三足/腾空/竖直速度/峰值接触力/含初始化力矩饱和；不能仅凭几何候选宣称修好。新视频须按实际终态核对时长和帧数。180秒课程诊断、24秒慢爬和原起点12秒验收保持区分，20cm箱及原1秒停稳/碰撞/执行器门禁不变。最终固定候选仍需原起点两组未用种子各32回合，每组≥30成功、无缺失并检查原速录像；NAV接近与CLIMB接口单独验证。PUSH、MuJoCo、实机暂停。

<a id="record-0096"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fi因卸载后机身过低失败；首回合录像已交付，fj预检高度并提前后脚补进（2026-10-03 06:54）

运行核对补充（07:12）：fj首批heightguard180于07:07:01正常结束，SHA256 `a17600668597968dc4748aed2a8ec7f4a7fa92327bd742a8fa5c9b9538460fdc`，本地按远端status核验一致。完整成功0/32、32终态齐全、0缺失；21超时/1底座/10姿态/0低姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化累计环境/关节饱和最大.460s（步态排除前.10s）。env6仍为最后RL准备相位0、四脚接触、卸载0、姿态/摆腿不可行，扩展搜索尝试2次，原低机身候选未执行，180秒超时。消除fi新增低姿态失败不等于完成攀爬。核验保存于fj/heightguard180-verification.json；第二批edgeprep180与固定env6录像正由PID616868/PGID616867运行，初检到2000步。未重复启动，等待第二批完整结果再比较，当前可查看视频仍fi/8795。

fi于06:36:09正常结束，报告SHA256 `291ccf8f4bed070af92ac00e0fa9b0e0a143c324a8b1d662e9e14faaf9716378`，本地按远端status核验一致。完整成功0/32，32终态齐全、0缺失；19超时/1底座/10姿态/2低姿态。三足及以上99.873%、最长腾空0、竖直速度峰值1.025006m/s、单足接触合力峰值373.566N、含初始化最长累计环境/关节饱和.460s。步态排除前.10s；合力峰值不是冲量。相较fh新增2次低姿态失败，不能以姿态搜索起效声称整体改善。

env6在约158秒实际执行扩展姿态（expanded_searches=1、expanded_pose=true），机身转移与完整摆腿预检通过，最后RL开始卸载；但在160.58秒因原low_posture终止，**不是180秒超时，也不是单纯卸载未完成**。末态RL接触力为0，FL/FR/RR竖直接触力约88.52/33.00/88.93N，机身z=.318984，支撑三足所在表面最低约.200496，离支撑面仅.118488m。原LowPosture按受力>2N的最低脚面（足中心减.0225）计算净高，要求≥.18m，持续低于.2s即失败。最后地面脚卸载后，最低支撑面从地面切换到箱面，此前几何搜索漏查这个既有条件。env8也发生低姿态失败，env13仍超时；没有改终止门禁。

最新录像页面：`index.html` ，本地/远端`climb-last-pose-20261003-fi`，HTTP PID2037580，已请求在Codex打开。录像前固定env6，首次扩展搜索之前364个共同轨迹采样（至157.5秒）与fh/front110逐值一致，actor及源码manifest哈希核验通过。原始latest-env6.mp4为180秒/4500帧，发现其在首回合终止后仍录入重置尾段；原文件保留，远端ffmpeg仅导出前4015帧为first-episode-env6.mp4，25fps/160.6秒，最后原回合画面160.56秒，首回合内部未剪接/变速。两个文件全部解码通过，抽帧确认终止前机身确实低、最后脚未登台。页面明确标注裁掉重置尾段、低姿态失败和未通过验收；并未声称完整观看后的动作质量验收。verification.json保存帧数/哈希/来源/统计；页面、核验和抽帧已同步远端。修正评估录像条件：只在被录环境首回合quota仍active时写帧，后续批量评估继续计数但不混入重置录像。

给规划补上原姿态要求：support_load_preview对预计达到三足支撑的卸载目标，要求机身高于剩余三脚最低支撑面至少.19m（原.18m门禁加1cm规划余量）；实际准备卸载与释放摆腿也检查原.18m。基于fi高度过低的候选现在应拒绝，不再只靠终止器拦截。原关节、8cm分段位移、.35rad转角、底座/腿部净空、原1秒停稳和执行器门禁保留，20cm箱不变。

加入原高度条件后，fh末态32768样本仍无同时满足完整摆腿和25mm预测支撑的候选。把尚在地面的最后RL脚位反事实改到原有地面落点x=.69，可找到机身z=.391547、预测三足裕量27.34mm、组合关节余量.056274rad的几何候选；它只是冻结姿态/受力假设，不能视为物理成功，记录在fh/last-posture-filter-search.json、last-ground69-posture-search.json、rear-edge-prep-pose-probe.json。最后三脚已在箱上时再补地面脚，也面临同一卸载净高问题，因此将实际补进安排在两只后脚都还在地面时。

新增默认关闭`--climb-rear-edge-prep`：双前脚在箱面承重、双后脚仍在地面、所选后脚x<.68且原下一步将上台时，先把该脚目标改为原地面锚点.69；两后脚逐脚补进，然后按原选择器登台。已经到位、另一后脚已登台、前脚动作或前脚不承重时均不触发，不新增平地行走任务，不降低箱沿净空。29项引导数学及11项阶段数学检查通过：拒绝旧低姿态候选、验证实际高度门禁、保留执行器补偿上限拒绝，以及提前补进作用范围和禁止循环。编译/差异检查通过；无新PPO。

确认fi进程结束后，独立远端`climb-unload-height-20261003-fj`于06:52:43启动监控PID613834，首个仿真PID613837/PGID613836。GPU0顺序运行heightguard180（补高度检查）和edgeprep180（再加后脚提前补进并录固定env6），各32环境seed513、180秒，同一受载箱沿复位库/actor、源码哈希核验；各2200秒、外层4600秒。已观察首批600步，无重复进程。下一轮先取两批结果，区分“避免低姿态失败”和“真正完成最后脚/完整任务”，核对新视频首回合时长。若仍失败须据新末态继续修正，不能靠延时或门禁放宽。

本轮及fj均为180秒箱沿诊断，24秒慢爬和原起点12秒验收仍未通过。最终固定候选需从原起点两组未用种子各32回合、每组≥30成功且无缺失，并检查原速录像；NAV接近与CLIMB接口单独验证。PUSH、MuJoCo、实机暂停。

<a id="record-0097"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fh完整任务仍失败，fi补充最后后脚的机身姿态搜索并录制（2026-10-03 06:20）

fh两批均已正常结束，rear83front116于05:31:36完成，rear83front110于05:44:56完成；完整成功各0/32，终态各32/32，无缺失，均21超时/1底座/10姿态。两批三足及以上支撑99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足接触合力峰值373.566N、含初始化最长累计环境/关节力矩饱和.460s。步态统计排除前.10s；合力峰值不等于冲量。两份报告SHA256分别为`a29d0fae337865073d17c1610ff12dc7a568d9dd0dc7182a6b30656c13b0ff01`和`b476123e47e9ea17970871a7be68e09a460ba7f94baff7f764d55e6647a3c1a2`，按远端status核验一致；fh/comparison.json同时保留两批，单批verification已更新完成状态。缩短落点未带来完整任务改善。

rear83front110的env6末态仍停在最后RL准备相位0、卸载0、四脚接触，无组合关节目标越限。FL/FR约[1.11457,.18496,.22293]/[1.11800,−.17690,.22303]，RR约[.83875,−.20420,.22367]在箱面，RL约[.66821,.19900,.02213]仍在地面。机身[1.02982,.00114,.33652]，实测三足裕量26.88mm；完整摆腿余量−.23384rad，ready=false。不能将三脚已搭上平台当作完成。

对该末态保持原8cm平移/.35rad转角和原关节/净空要求，固定Sobol seed913检查32768姿态：7127静态受载候选、3006机身路径候选、34条完整摆腿路径，其中**仅1个同时满足预测三足支撑≥25mm**。位置约[.996839,−.048140,.325947]、四元数[.998842,−.045527,−.012639,−.009044]，组合余量.054989rad、腿部路径净空30.45mm、预测三足裕量28.22mm。它包含向后/侧向移动和小幅侧倾，原以向前偏移及支撑平面俯仰为主的列表未覆盖。该结果是冻结重力/COM估计下的离散几何候选，并非物理成功。分析在fh/rear83front110-pose-search.json与expanded-search-probe.json。

新增默认关闭的`--climb-guidance-last-pose-search`：只在原候选失败、恰有三脚在箱面接触、所选后脚从地面登台时补充搜索。使用固定32768个相对机身位置/roll/pitch样本，保留8cm平移/.35rad转角，要求预测三足裕量≥25mm、原名义/估计受载关节余量≥.03rad、FK误差<1mm、底座路径净空≥1cm、腿部路径净空≥5mm及完整41点摆腿检查，仍以实测支撑/卸载/落脚门禁决定执行。没有放宽原阈值。无解返回保持；同一静止姿态不反复做大搜索，只有首次或机身变化>1cm/转角>.05rad才重试。记录expanded_searches和expanded_pose，便于确认物理运行实际走过该分支。

29项引导数学检查通过，包括原28项及来源明确的fh末态回归：扩展候选可满足原几何/支撑检查；压低执行器补偿上限后必须拒绝并保持原姿态。测试fixture仅保留必需几何/受载数据及报告哈希，不含日志、权重或视频。编译与差异检查通过。该测试不替代远端物理验证，也未证明自碰撞或完整动态安全。

核对远端无旧评估进程后，独立`climb-last-pose-20261003-fi`于06:18:57启动监控PID609186。GPU0从同一受载箱沿课程重新运行32环境seed513、180秒，使用fh/front110/rear83设置加新搜索开关，固定env6录制完整首回合25fps原速视频；单批墙钟2200秒、外层4600秒，源码payload哈希核验后启动。仍为控制参考的攀爬阶段诊断，无新PPO，不能计入24秒慢爬或原起点12秒验收。保留20cm箱、原1秒停稳、碰撞与执行器门禁。

下一轮先看fi状态/全部子进程，不重复启动；核对首次expanded_searches之前轨迹与fh的一致性，再检查是否实际执行新姿态、能否卸载/抬起RL以及完整成功率和全部质量指标。录像结束后核对时长、帧数、来源与报告再展示；当前已交付视频仍fe/fd `index.html` ，fi视频尚在生成，不能提前称为新结果。最终候选仍须原起点两组未用种子各32回合，每组≥30成功且无缺失终态，并检查原速录像；NAV接近/CLIMB接口单独验证。PUSH、MuJoCo、实机暂停。

<a id="record-0098"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fg两种前脚间距均卡在最后左后脚，fh检查后脚首次登台落点（2026-10-03 05:19）

运行核对补充（05:43）：fh首批rear83front116已于05:31:36完成，SHA256 `a29d0fae337865073d17c1610ff12dc7a568d9dd0dc7182a6b30656c13b0ff01`，本地按远端status核验一致。完整成功0/32、终态32/32、0缺失，21超时/1底座/10姿态；三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计环境/关节饱和.460s（步态排除初始.10s）。env6保留RR登台（x.83959、z.22361），RL仍在地面（x.67028、z.02194），最后RL准备相位0、卸载0；实测三足裕量28.85mm，但摆腿余量−.13383rad、ready=false，完整成功未改善。冻结末态32768姿态探查得到4463静态受载候选、1653机身路径候选、8条完整摆腿路径；这8条预测三足裕量最高仅4.47mm，全部未达到25mm，因此仍无可卸载解。结果/分析保存在fh/rear83front116-verification.json和rear83front116-pose-search.json，几何搜索不算物理验收。第二批rear83front110正在既有进程PID603476/PGID603475中运行，已到7400步；未重复启动，先等完整对比，不能只用首批作两批结论。

fg两批已结束：front120于04:43、front116于04:57正常退出，均完整成功0/32、32终态齐全、0缺失，均21超时/1底座/10姿态。三足及以上支撑99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足接触合力峰值373.566N、含初始化最长累计环境/关节力矩饱和.460s。**统计口径澄清：步态遥测原实现排除最初.10s，力矩饱和包含初始化；此前将所有步态指标一并称为“含初始化”不准确。** 接触数值是合力峰值，不是冲量积分。两批没有完整成功率改善；32完整仅指每个回合都有终态，失败不算成功。报告SHA分别为`50a2449fafbe92d91f920ac62e24d367eabf984cf6134708963f9ce66f1de286`、`5072fdf01872944f9c2148f1382bc2ff40602a3302e0686a7900c14f02fcf7de`，已按远端status核验。仓库外fg/comparison.json同时保留两批，旧front120-verification已更新为两批完成状态。

两版env6均保留RR箱面落脚，RL仍在地面，180秒末停在RL准备相位0、四脚接触、卸载0、无关节组合目标越限。front120实测三足裕量18.12mm，front116为25.29mm；对应完整摆腿余量−.16083/−.19209rad，摆腿未就绪。front116双前足实际x约1.176/1.178、RR约.8684，RL约.6715；较短前脚改善局部支撑，未解决最后一步可达性。

对front116末态做固定Sobol seed913的32768姿态几何检查，保持8cm位移、.35rad转角及原关节/净空约束。4994静态/估计受载候选、1833机身路径候选中，只有1条完整摆腿路径达到原要求（余量.03349rad、腿部净空5.934mm）；该机身约[1.0064,−.04997,.34214]，预测三足裕量却为−3.99mm。因此它只是关节/净空可行，**不是可以卸载抬脚的解**；没有将该候选写入执行器或放宽支撑门禁。搜索/补充支撑检查在fg/last-pose-path-search.json。离散搜索不证明无解。

进一步固定该机身和COM做落点反事实：将RR x从.8684缩为.83，前脚第二次目标为1.16/1.12/1.10时，三足裕量估计约13.40/26.69/33.82mm；原RR落点配前脚1.10仅约16.00mm。该分析仅说明后脚首次落点也影响最后一步的支撑区，未验证改变脚位后的关节/碰撞或动力学，不能当成功证据。记录fg/last-tripod-counterfactual.json。

新增默认None的`--climb-rear-ascent-target`诊断参数：只有双前脚在箱面承重、选中后脚当前仍在地面且下一步将登台时，限制首次登台x；本轮设.83，即箱前沿.75内8cm，保持原落点最小边沿留量。不改变后脚地面跟进、前脚落点、已经在箱面的后脚后续步进，也不向后退脚。原落脚高度、摆动时长/平滑、支撑转移、接触确认、关节/执行器/碰撞门禁保持。10项阶段数学检查通过（原9项加后脚首次落点作用范围、禁止退脚、落地后继续下一后脚），编译和git diff检查通过；源码为待远端物理验证的诊断候选。

确认远端无遗留训练/评估进程后，独立目录`climb-rear-foothold-20261003-fh`于05:18:11启动监控PID603206，首个仿真PID603209/PGID603208，GPU0顺序运行rear83front116和rear83front110，各32环境seed513、180秒、固定env6；单批墙钟2200秒，外层4600秒。首版只改变后脚首次落点，可与fg/front116比较；第二版同时缩短前脚第二次补进，两版都必须保留完整结果。新目录复制冻结训练树并覆盖已哈希核验源码，actor和受载箱沿复位库未变；没有新PPO。这是箱沿攀爬参考动作的物理诊断，不能记为训练收敛或原起点成功。

下一轮先核对fh全部相关进程/状态，避免重复运行；关注是否保留RR登台、能否接上RL、完整任务和碰撞/执行器结果，若无解再据新末态检查姿态与摆腿路径。不得仅因局部支撑裕量变好继续盲目缩步长或延长时限。最新已交付视频仍fe/fd控制器：`index.html` ，不是fg或fh；无新录像时不得称其为新候选表现。180秒诊断、24秒慢爬和原12秒任务独立标注，20cm箱及原1秒停稳保持。最终固定候选仍需原起点两组未用种子各32回合、每组≥30成功且无缺失终态，并检查原速录像；NAV接管单独验证。PUSH、MuJoCo、实机暂停。

<a id="record-0099"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fe三脚登台原速视频已交付，fg对比更短的前脚第二次补进（2026-10-03 04:22）

运行核对补充（04:42）：fg首批front120仍在运行，已到8200步，尚无完整结果。发现ff外层监控虽已停止，其内部timeout另建进程组，导致ff仿真子进程在本轮初检时仍存在；按已核实PID准备清理时594871/594872已自行退出，实际未发送终止信号。现在仅fg运行。ff继续排除在效果证据之外；以后中止实验必须复核该实验路径对应的全部子进程及进程组，不能把外层监控停止当作仿真已停。该情况可能增加本轮运行耗时，不能将耗时变长误判为策略停滞。

最新视频：`index.html` ，本地/远端`climb-rear-ascent-review-20261003-fe`；HTTP PID2027414。固定env6，180秒完整首回合、25fps、4500帧全部解码，未剪接/加速/混入重置；已检查抽帧与事件时间，页面默认原速供用户复核，未宣称通过动作质量验收。168—170秒右后脚落脚承重，随后切换最后左后脚准备，180秒超时，左后脚仍在地面。全段408个轨迹采样、32终态、步态和关节指标与fd transfer180逐值一致；actor、控制源码及评估器等哈希匹配。fe报告SHA256为`ee1014f0e0c4d804ff6ac61074096ffba360911bafcf77a80181eb87015d2ca6`，核验及页面同步本地/远端。

fe完整成功0/32、终态齐全，21超时/1底座/10姿态。三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计环境/关节力矩饱和.460s。此为180秒箱沿诊断，三脚登台不等于完整攀爬，更不是24秒慢爬或原起点12秒验收。接触指标为峰值合力，并非冲量积分。

针对最后RL，离线扩展32768个固定随机种子的Sobol机身候选，保留8cm位移、原角度/高度/关节/净空要求，发现4050个静态候选、1405个机身路径候选，但没有完整摆腿可行解；较好的摆腿余量约.02340rad，仍低于原.03rad。另做16cm“后续两段动作目标”的几何探查（没有将16cm用于执行），也未找到同时满足完整摆腿和预测支撑裕量35mm的终点。它们只是离散几何搜索，不是数学上不可攀爬的证明；不会以此放宽原门禁。分析保存在fd/last-pose-search.json、last-pose-path-search.json、last-pose-lookahead-search.json。

改为检查更早的前脚落点分布：当前第二轮前脚补进从约1.07一步走到约1.30，拉长了最后卸载RL时由FL/FR/RR构成的斜边。固定fd的COM、机身与其他脚，反事实把双前足x设为1.30/1.23/1.20/1.18/1.16，预测三足裕量约−15.33/+8.38/+19.89/+28.04/+36.58mm。这个假设检查并未同时找到可行完整机身/摆腿解，不能当作物理成功；它说明缩短前脚补进值得从原箱沿课程重新运行，而不是继续只调末态。记录在fd/front-spacing-analysis.json。

新增可选`--climb-front-followup-target`（默认None，旧行为保留）。仅当双前足已在箱面、双后足x均≥.55且仍有脚未登台时，限制前脚第二次补进到配置x，不向后退脚；选择下一只脚的阈值设为目标前2cm，避免到位后反复补进。首次上台、第一次前脚补进、后脚路径保持；四脚都上台后恢复原普通前进脚步，不让这个局部上限阻碍后续走到停稳位置。9项阶段数学检查通过，覆盖原8项行为、新落点/脚序、禁止退脚和四脚登台后解除局部限制；编译及差异检查通过。没有修改任务成功、原1秒停稳、20cm箱、关节、碰撞或执行器门禁。

远端`climb-front-spacing-20261003-fg`于04:21:23启动监控PID595489，GPU0顺序运行front120（目标x1.20）和front116（x1.16），各32环境seed513/180秒、固定env6轨迹，墙钟各2200秒、外层4600秒。本次不重复已跑过的180秒baseline，以fd为历史参考、原阶段测试验证默认行为；两版都须报告完整结果，不能只挑更好一版。之前ff启动后审查发现局部上限也影响四脚登台后的步进，已终止仅属于该实验的进程组594869，产物和原因保留，修正后在独立fg目录重启；ff不计入效果证据。先检查fg，避免重复启动。

本轮仍无新PPO，只有明确落点假设的远端物理对比。下一轮优先取fg结果，检查是否保留右后脚成功、能否接上最后左后脚，以及完整成功/碰撞/执行器指标；不能把更短步长当作自动更稳定。最终固定候选仍需原起点两组未用种子各32回合≥30成功、无缺失并检查原速录像；NAV接管单独验证。源码、四份交接及仓库外产物更新，PUSH、MuJoCo、实机暂停。

<a id="record-0100"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fd右后脚已登台承重，卡在最后左后脚；fe录制完整回合（2026-10-03 03:51）

fd两批已正常结束，各0/32完整成功，64终态齐全。baseline逐值复现fc swing180终态、env6轨迹、步态与关节指标（仅忽略新增swing_path_ready遥测）。transfer180于03:13:56结束，报告SHA256为`2efdb524cd2301dc85720b0d1f9bd1cb1d5c7850adadac7a6af6e7af667fda7a`。两批均21超时/1底座/10姿态，三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计环境/关节力矩饱和.460s。局部脚序继续推进，但完整成功率和这些整批指标未改善，仍未通过验收。峰值接触合力不等同于冲量。

env6的四足分段转移本次实际起效：156秒摆腿未就绪时保持卸载0，164秒已满足摆腿余量.03052rad/腿部净空16.74mm、实测三足支撑裕量35.82mm，RR完成卸载并开始抬脚，168秒进入落脚，170秒脚序已切换到RL。180秒RR足中心约[.87057,−.20707,.22367]，实测竖直接触力53.27N，确认是箱面落脚承重；FL/FR约[1.3041,.1851,.22383]/[1.29787,−.19034,.22387]。尚在地面的RL约[.67164,.19673,.02183]，整机未完成登台。接触力数组必须按`contact_body_names`索引；位置数组按`body_names`，两者顺序不同，不能混用。

最后RL停在准备相位0、四脚接触、卸载0、组合关节目标无越限。机身约[1.08203,−.01749,.35029]，实测三足裕量−16.66mm，目标RL落点[.88473,.20220,.2245]。当前RL calf名义目标约−.96797rad，接近原软上限−.93226rad；右后脚已在高台，机身调整需要同时兼顾两条高度不同的后腿。完整摆腿余量约−.17549rad，摆腿路径ready=false。此次不能再说卡在第一只后脚，也不能把三只脚在箱上当完整成功。

离线按fd终态重建的原1053个机身候选，端点联合可行数0：最佳名义关节余量约.02344rad，小于原.03rad要求；未到摆腿检查之前就全被拒绝。分析保存在fd/last-leg-gates.json。尝试目标后移4/8cm、额外侧移和−.3/−.2/−.1/+.1rad侧倾（含独立侧倾）仍未找到同时通过原全部检查的解；它们没有被加入控制源码或提交为新物理候选，也没有放宽限位/余量。诊断在fd/rear-pose-analysis.json与roll-pose-analysis.json，属于冻结状态的几何估计，当前重力由原补偿及雅可比重建。后续需检查三脚登台时的落点分布、最后一步前机身调整路径与前一步结束姿态的兼容性，避免只为当前脚找一个无法接下一脚的姿态。

保持已验证源码9dd10d5和同一actor/seed513/32环境，远端`climb-rear-ascent-review-20261003-fe`于03:47:28启动监控PID590346，GPU0录制固定env6完整180秒/25fps首回合，相机[1.05,2.6,1.15]指向[1.05,0,.35]。墙钟2200秒、外层2300秒。下一轮先检查fe进程和结果，核对与fd报告/轨迹的一致性并检查原速画面，再更新视频页面；当前新录像仍在生成，最新可查看仍fb/8793。不能用延长时限或重复启动同样训练代替最后一脚修正。

本轮无新PPO、无新控制源码修改；fd比较/分析同步本地与远端，四份交接推送指定Git分支。180秒箱沿课程仅诊断，24秒慢爬和原起点12秒验收仍未通过；保留20cm箱及原停稳/碰撞/执行器门禁。NAV接管仍需单独验证，最终固定候选须从原起点两组未用种子各32回合≥30成功、无缺失并检查原速录像。PUSH、MuJoCo、实机暂停。

<a id="record-0101"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fc拦住越限抬脚但卡在准备，fd允许四足分段转移（2026-10-03 02:47）

fc两批正常结束，完整成功均0/32，64终态无缺失。100秒baseline逐值复现fa preview100的全部终态、env6轨迹、步态和关节指标；180秒swing180在02:17:25结束，SHA256为`84eb2155bd95113639b83f6d4f8272e2234dc0820485041a3b166bf065106092`，与fb到140秒的329个共同采样逐值一致（比较共同字段）。候选与fb均21超时/1底座/10姿态、三足及以上99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计环境/关节饱和.460s；100秒baseline三足为99.786%，其余峰值相同。没有完整成功或这些整批质量指标的改善。接触指标是峰值合力，未当作冲量积分。

新摆腿预检确实阻止了原右后脚抬起后髋越限，但把env6卡在更早的准备阶段。180秒末四脚仍受载、卸载0、无组合目标越限，RR未离地；双前脚x约1.300/1.292，双后脚约.659/.647。机身约[.89358,−.02365,.39423]，待抬脚之外三脚的支撑裕量−69.08mm。全部候选被完整摆腿检查拒绝，返回保持姿态，摆腿余量约−.18478rad、未来摆腿腿部净空−24.78mm。此处负净空指假定现在抬腿的未来路径，不能误报为当前四脚静止姿态已经发生碰撞。原本需要多次≤8cm的四足机身转移后才具备抬脚条件；fc却要求每个中间转移端点都先具备完整摆腿能力，形成准备阶段死锁。

新增默认关闭`--climb-guidance-swing-transfer`，依赖已有swing-preview。允许预测三足裕量仍<25mm、且比当前位置改善>2mm的中间机身姿态进入候选；原静态四足关节余量、底座/腿部整段转移净空、8cm水平上限、平滑约束保持。增加独立`guidance_swing_path_ready`，只有完整41点摆腿余量≥.03rad、FK残差<1mm、腿部净空≥5mm且机身候选可行才成立。中间转移即使允许，卸载与抬脚仍被该标志阻止，保持四足承重；稳定后继续重规划。不得把“中间机身移动允许”等同于“摆腿允许”。新开关关闭时保留fc选择行为，回归比较需忽略新增加的ready遥测字段。

在fc记录姿态的局部重建中，旧选择无解；新选择得到约[.96340,.01541,.36423]的四足中间目标，关节余量约.11386rad。这时完整摆腿余量仍−.17312rad、未来净空−23.05mm，因此必须继续保持四脚而不能卸载。局部分析只验证可以提出受限中间转移，不证明能完成后续上台；文件fc/swing-transfer-analysis.json。28项引导数学检查通过，新增覆盖拒绝后退/原地假进度、禁止以三足区内不可行摆腿继续放行，以及实测支撑稳定但摆腿未通过时不能释放抬脚；编译和差异检查通过。

远端`climb-swing-transfer-20261003-fd`于02:46:39启动监控PID586772，GPU0顺序运行fc180秒回归和transfer180候选，各32环境seed513、env6轨迹，墙钟各2200秒、外层4600秒。先检查fd进程和结果，不重复训练。候选物理结果尚未产生，不声称准备死锁已解除。仍为箱沿180秒诊断，无新PPO；不能计入24秒慢爬或原起点12秒验收。20cm箱、原停稳/碰撞/执行器门禁、最终两组未用种子各32回合≥30成功及原速录像要求保持，NAV接管仍待单独验证。

最新已录制视频仍fb：`index.html` ，未把fc仅有报告的结果冒充新录像。fc完整报告、状态、比较及局部分析已同步本地与远端，源码和四份交接更新指定GitHub分支。PUSH、MuJoCo、实机暂停。

<a id="record-0102"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fb原速视频已就绪；后脚抬升触及髋限位，fc预检摆腿路径（2026-10-03 01:57）

最新录像：`index.html` ，本地目录`artifacts/go2-piper/climb-load-preview-review-20261003-fb`（位于仓库外的同级artifacts），HTTP PID2019366。远端fb在01:31:39正常完成；固定env6的180秒首回合、25fps、4500帧全部解码通过，未剪接/加速/混入重置。已检查抽帧画面、时间对应关系和末段停滞；默认原速播放供用户复核，不能冒充已通过动作质量验收。前100秒248个共同轨迹采样与fa preview100逐值一致，actor、控制源码、评估器和辅助源码哈希均一致。报告SHA256为`41e599f26d4c079317f496e399f10f35ebc5102f6f21725d71bfc40309ad666f`，完整核验在fb/verification.json，本地和远端均已保存。

fb完整成功仍0/32，32终态无缺失：21超时、1底座接触、10姿态失败。含初始化/失败回合的整批三足及以上支撑99.874%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、最长累计环境/关节力矩饱和.460s。接触数据这里报告峰值合力，不是冲量积分；高三足比例不能替代攀爬成功或实机电机安全验证。

env6在100—124秒继续后脚地面跟进，126—144秒完成双前脚第二轮箱面补进；末态FL/FR x约1.297/1.296，RL x约.664且仍在地面。约159秒开始卡在RR抬脚阶段.25，180秒超时：实际RR足[.69298,−.20138,.22498]，参考[.70,−.20176,.2545]；其名义hip目标−1.032858rad已低于原软下限约−.94248rad，含重力补偿组合目标越限.114342rad，RR参考被拒绝。其余三脚支撑，卸载比例1；不能把悬空等待当作后脚登台，也不能继续用延长时间解决该固定卡点。

新增默认关闭`--climb-guidance-swing-preview`诊断：只改变后脚从地面上台的摆腿，空中平滑向内收6cm，落脚前恢复原横向位置，沿用五次平滑曲线、4秒摆腿、原落点高度/脚距与关节速度/加速度限制。横移阶段到位判断同步使用收脚后的高位航点，落脚确认仍使用原落点，避免人为制造新的.75相位等待。准备卸载时对候选机身姿态采样41个摆腿点，检查原名义/重力补偿关节界限、FK残差<1mm、真实USD腿部形状与箱体≥5mm净空，并保留原关节余量.03rad、底座1cm、承重、碰撞、停稳和执行器门禁。没有可行全程路径就不抬脚。该预测仍固定未来机身姿态和当前重力估计，离散采样不等于完整动态安全证明；本轮未覆盖所有前腿摆动/自碰撞。

局部冻结姿态分析可拒绝原抬升路径（摆腿余量约−.114rad）；加入内收并重新选择机身后可找到约.03075rad摆腿余量、15.04mm腿部净空的几何候选。起点用记录中的抬脚前脚位与终态机身重建，明确不是新的物理成功证据。分析在fb/swing-rejection-analysis.json与swing-pose-analysis.json。26项引导数学检查通过，包括原髋越限复现、内收可达性、世界平移不变、原落点保持、相位连接平滑与高位横移终点；编译/差异检查通过。

远端`climb-swing-preview-20261003-fc`于01:56:07启动监控PID585847，GPU0顺序运行fa100秒回归（新开关关闭）及摆腿预检180秒（开启），各32环境seed513、固定env6轨迹。墙钟分别1000/2200秒，外层3400秒。先查fc进程、状态与结果，不要重复启动；候选物理结果尚未出，不声称已跨过后脚卡点。此次是受载箱沿课程诊断，无新PPO。180秒、24秒慢爬及原起点12秒验收继续分开；NAV接管未验证，最终仍需固定候选从原起点两组未用种子各32回合、每组≥30且无缺失终态，并检查原速录像。PUSH、MuJoCo、实机暂停。源码和四份交接推送指定feature/go2-piper-sim2real分支。

<a id="record-0103"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：fa越过前脚卸载卡点；fb延长诊断并录制原速视频（2026-10-03 01:16）

fa两批已结束，64终态无缺失，完整成功仍均0/32。baseline逐值复现ez primitive100全部终态、env6轨迹、步态和关节指标；两批均21超时/1底座/10姿态，三足99.786%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。局部进度改善未改变本批完整成功率或这些质量指标，仍不具备交付条件。

preview100的env6已通过原FR卸载卡点：约78秒完成前移承重转移，80—84秒完成FR箱面补进，86—96秒继续RR地面跟进。100秒末双前脚x约1.0691/1.0654，RL/RR约.4193/.5240，机身x=.8264；四足接触、组合目标无越限，RL处于下一步准备，实测支撑裕量32.42mm，正好完成新的机身转移。之前的FR阶段卸载比例停留在.267，本版该阶段已到1并抬脚完成。env6采样轨迹未出现load_replan=true，故不能声称卸载失败恢复分支已被该回合物理验证；当前证据支持载荷预估后的另一机身参考避开了原卡点。

本轮停止于100秒时限前仍有连续脚序推进，与此前延时不动的情况不同。冻结b829472控制源码和同一actor/起点/seed513，远端`climb-load-preview-review-20261003-fb`于01:14:55启动监控PID584313，GPU0运行一批32环境180秒诊断，同时录制固定env6的25fps原速视频，视角[1.05,2.6,1.15]朝向[1.05,0,.35]。仿真步上限9100、墙钟1800秒；仅用于观察后脚临箱沿、上台及是否出现新卡点，明确不是24秒或原起点12秒验收，也没有改训练课程标准。

下一轮先检查fb进程和结果，避免重复fa。拉回报告、录像与状态，核对前100秒env6轨迹和fa一致性、首回合终态及全32回合完整性；解码并检查真实速度录像，主片只保留首回合，清楚标注180秒诊断和真实成功/失败。最终验收仍需固定候选从原起点两组未用种子各32回合，每组≥30成功、无缺失，并在原时限/停稳/碰撞/执行器门禁下检查动作。尚无新PPO，PUSH、MuJoCo、实机暂停。

fa比较和全量报告已保存本地与远端仓库外。最新可查看视频仍ev/8792；fb正在录制，未替换旧视频或声称新录像已就绪。本轮仅更新交接与实验记录，控制源码保持b829472，指定Git分支同步。

<a id="record-0104"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ez恢复后脚跟进，卡在前脚卸载限位；fa加入承重预估与退回重规划（2026-10-03 00:53）

ez两批已结束，64终态完整无缺失，完整成功均0/32。baseline逐值复现ey leg100全部终态、env6轨迹、步态和关节指标；两批均21超时/1底座/10姿态，三足99.786%、最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。真实形状检查恢复了部分动作进度，尚未改善完整成功或这些质量指标。100秒只作箱沿诊断。

primitive100的env6已跟进双后脚至x约.4006/.3926，FL箱面补进至1.0631，FR仍在.8412。100秒末四脚都有接触、无小腿搭箱，停在FR补进准备，支撑裕量74.1mm；卸载比例约.267时，FL组合calf目标越软上限约.00085rad，FL参考被拒绝。原反馈在“可卸载/不可卸载”之间切换，卸载比例反复回到同一水平，既无法完成也回不到0，而重规划要求卸载为0，形成循环等待。继续延时不解决该问题；不能把越限量小当作放宽限位的理由。

当前选择器用四足承重时的实测力矩偏置判断候选，没有预估FR完全卸载后其他腿承担的载荷。新增默认关闭`guidance_load_preview`：根据候选腿部雅可比、平移后的实测COM、重量和当前重力补偿，预估三足静态载荷及组合关节目标；检查原软限位和原75%补偿力矩上限，并保留.03rad等效余量。预测COM未到原支撑门槛的中间转移仍保持四足，运行时卸载门禁不变。新增+4/+8cm前移候选以保留前腿弯曲空间，单段水平位移仍≤8cm，所有原机身/腿部路径净空与平滑检查保留。候选计算分批每次最多2个环境，限制GPU临时内存。

另加卸载失败状态：准备阶段卸载中出现组合目标/关节参考拒绝时，保持失败标记，逐渐将载荷还给仍接触的待抬脚；等四脚稳定且卸载归零后重新规划，避免在同一临界比例反复试探。未接触的脚仍不能强行分配恢复载荷。记录`guidance_load_replan`用于核对实际行为。该载荷预估忽略未来重力变化、COM随姿态的非平移变化及瞬态加速度，仍须实测支撑/碰撞/执行器验证。

离线同一ez终态，旧保持姿态预测完全卸载的组合限位余量约−.13274rad；新候选目标约[.67125,−.00209,.37446]，预测余量约.03767rad。该估计用记录力矩和雅可比恢复重力补偿，不是新物理结果；分析在ez/load-preview-analysis.json。24项数学检查、编译和差异检查通过，包括解析雅可比对有限差分、拒绝当前卸载目标、找到受限转移及多环境分批一致性。

远端`climb-load-preview-20261003-fa`于00:51:13启动监控PID583773，GPU0顺序运行ez100秒回归及载荷预估100秒，各32环境seed513、env6轨迹。新候选墙钟上限1000秒、监控2000秒，仅为增加计算量预留时间，仿真回合仍100秒；先检查fa结果，勿重复启动ez。未新增PPO，20cm箱及原碰撞/执行器/停稳门禁保留，24秒与原起点12秒验收仍未通过。最新视频仍ev/8792；本地/远端诊断产物、源码及指定Git分支交接更新。PUSH、MuJoCo、实机暂停。

<a id="record-0105"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ey腿部包围盒误拒绝转移；ez按实际圆柱几何检查（2026-10-03 00:20）

ey两批已结束，64终态无缺失，完整成功仍均0/32。baseline逐值复现ex independent100全部终态、env6轨迹、步态及关节指标。baseline为19超时/2底座/11姿态、三足99.556%；leg100为21超时/1底座/10姿态、三足99.786%。两批最长腾空均0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。候选更少碰撞但前进退步，不能把低冲击或站住算攀爬成功；100秒仍仅箱沿诊断。

leg100 env6在双前脚首次上台后、第一只后脚RR准备阶段就停住，100秒末四脚均接触、无腿部其他接触力，机身约[.36932,−.02157,.36058]，双前脚x约.836、双后脚x约.159，支撑裕量−73.93mm。最小腿部包围盒间隙约.145mm，小于新增5mm检查，从路径起点就否决了全部候选。发现原因是把倾斜圆柱再包成连杆坐标下的长方体，新增了本不存在的角点。按USD真实圆柱方向、半径和长度计算分离轴支撑范围，同一终态最小分离间隙下界为15.13mm，已满足5mm；此前ex实际FR小腿搭箱状态则仅约.00453mm，仍被拒绝。

新增默认关闭`guidance_primitive_collision`，在已有腿部路径检查上使用真实USD hip/calf圆柱和thigh立方体的局部变换、缩放及支撑半径，保留原物理碰撞资产。采用有限候选分离轴与朝向箱体最近点的附加方向；正间隙可证明该方向分离，有限轴仍可能保守误拒绝，不能冒充精确最近距离或动力学保证。腿部5mm、底座1cm、21点采样、原软限位与完整/半段/四分之一段转移优先级均保留。

同一ey终态的几何对照，旧包围盒无可行转移，真实形状得到目标约[.40586,.04960,.33786]，关节余量.18920rad、腿部路径最小间隙8.62mm。该结果尚非物理改善。22项数学检查、编译及差异检查通过，新增检查覆盖圆柱空角点、实际相交、USD真实尺寸和ey误拒绝姿态。比较和分析在ey/comparison.json与primitive-analysis.json，已同步本地/远端。

远端`climb-primitive-clearance-20261003-ez`于00:18:23启动监控PID582023，GPU0顺序做ey100秒回归及真实形状100秒，各32环境seed513、env6轨迹。先检查ez进程与结果，勿重复启动ey；无新PPO。20cm箱、原碰撞/执行器/停稳标准保留，24秒及原起点12秒验收均未通过。最新视频仍ev/8792。源码与交接推送指定分支，PUSH、MuJoCo、实机暂停。

<a id="record-0106"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ex卡在前小腿搭箱承重；ey补齐腿部净空与短机身转移（2026-10-02 23:54）

ex两批已结束，64终态无缺失，完整成功均0/32。baseline逐值复现ew clearance100全部终态、env6轨迹、步态和关节质量。两批均19超时/2底座/11姿态失败，三足分别99.562%/99.556%；最长腾空均0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。独立高度候选未带来完整成功或安全指标改善，仍仅100秒箱沿诊断。

新诊断说明为何机身目标可行仍不前进：ex env6在约87秒后FR足离开台面，终态FR足中心z=.28634m、足接触0，而FR_calf承受101.519N；FL足仅约3.04N，双后足约72.89/32.01N。原分配器仍预测FR足应支撑约52.11N，卸载比例保持0，RL未抬起。实际机器人已靠前小腿搭在箱沿承重，不能误判为正常三足支撑或单纯力矩不足。机身目标z=.29622m，实际z=.34139m，目标底座避开了箱子，但小腿没有避开。

从实际USD读取hip圆柱、thigh立方体和calf圆柱碰撞几何及局部变换，按原关节链计算12个腿部连杆位姿；与ex终态实测连杆位置最大误差约1.01e−6m。实际FR小腿保守包围盒与箱体间隙约−1.91mm，和接触力证据一致。原低位独立候选的名义腿部路径间隙约−88.35mm；同一近似ew起点的完整XY转移无满足新增5mm腿部间隙的候选，但半段转移有1个，目标约[.66072,−.05586,.37609]、路径关节余量.03764rad、腿部最小间隙6.46mm。这只是几何诊断，尚非物理改善；分析在ex/leg-collision-analysis.json。

新增默认关闭`guidance_leg_collision`：要求机身路径与独立高度检查已开启，沿同样21个名义姿态样点检查hip/thigh/calf碰撞包围盒与箱体至少5mm分离；底座仍1cm、端点关节余量仍.03rad，未改执行器、原碰撞/停稳判据。完整XY转移不可行时依次尝试半段和四分之一段；仅在实际支撑裕量、速度和承重达标后才能抬脚，短转移不能跳过卸载门禁。运行时首次捕获校验12个连杆位置误差≤5e−5m，并记录腿部路径最小间隙。仍未覆盖摆脚全路径、采样间隙和跟踪/载荷变化，不能当作动态安全证书。

20项引导数学检查、编译和差异检查通过，覆盖腿链FK、USD立方体尺寸只缩放一次、拒绝原低位腿部碰撞路径、保留原软限位与底座门禁的短转移。远端`climb-leg-clearance-20261002-ey`于23:52:05启动监控PID580395，GPU0顺序运行ex100秒回归及腿部净空100秒，各32环境seed513、env6轨迹。先检查ey结果，勿重复启动ex；无新PPO，20cm箱、24秒/原起点12秒验收区分保留。最新视频仍ev/8792，未展示ex失败。比较、分析、本地产物与指定Git分支均更新；PUSH、MuJoCo、实机暂停。

<a id="record-0107"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ew完成前脚箱面补进但仍0/32；ex解耦机身高度与俯仰（2026-10-02 23:21）

ew两批结束，64终态完整无缺失。baseline逐值复现eu feasible100终态、env6轨迹、步态和关节指标；两版完整成功均0/32。baseline为15超时/9底座/8姿态，三足99.764%；clearance100为19超时/2底座/11姿态，三足99.562%。两批最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。底座碰撞减少但姿态失败增加，不能据此宣称整体改善或安全达标。100秒仍仅箱沿诊断。

净空版env6通过了原33.82秒底座碰撞位置，随后完成前脚箱面补进：FL/FR实际x约1.0684/1.0624，双后脚x约.3997/.3999；这是唯一终态双前脚均推进至x>1.0且有接触的环境。100秒末停在RL准备，四脚接触，机身[.6422,−.0223,.3661]，名义与组合目标无越限，但支撑裕量−41.65mm、原15个新机身候选全部被拒绝。尚无完整登台。

离线按该实测终态分析：原候选把机身高度与俯仰绑定，估计所需转移目标[.6792,−.0894]；大多数候选伸直RL过多、组合calf超限，低位候选又触及净空边界。COM由记录载荷加权近似，非新的物理证据。将高度和俯仰独立采样后102个额外候选中有16个满足原几何门禁，最佳候选路径关节余量约.2085rad、端点.2927rad、最小底座间隙约10.99mm；不代表动态可实现。分析与比较保存于ew/pose-rejection-analysis.json及comparison.json，本地和远端一致。

新增默认关闭`guidance_independent_height`，要求原机身路径净空检查已开启。原15候选可行时仍优先使用原选择；仅其全部失败时允许额外102候选（当前高度±8cm、1cm步距，配5种支撑斜面俯仰及当前实测姿态）。保留端点.03rad余量、21点路径FK/软限位、1cm底座间隙、8cm/.35rad机身变化限制与原平滑/接触/执行器门禁。新增记录捕获时真实COM及筛选前机身目标，减少后续近似诊断。19项数学检查、编译与差异检查通过，新增用ew失败姿态检查几何解恢复并验证原可行候选保持；物理结果待验证。

远端`climb-independent-height-20261002-ex`于23:19:18启动监控PID578952，GPU0顺序做ew100秒回归、额外候选100秒，各32环境seed513、env6轨迹。启动前ew已结束，无重复训练，无新PPO；先检查ex进程与结果。最新视频仍ev/8792，尚未展示ew补进进展。20cm箱及原停稳/碰撞/执行器标准保留；24秒和原起点12秒验收未通过。产物更新本地/远端仓库外，源码与交接推送指定GitHub分支；PUSH、MuJoCo、实机暂停。

<a id="record-0108"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：定位eu底座撞箱，ew增加机身路径净空检查（2026-10-02 22:56）

最新视频ev/8792中env6在33.82秒终止，四脚仍有接触，实测base合力约[−2.0503,0,4.0922]N。追溯发现新机身选择器只优化关节余量，忽略了机身与箱沿的空间关系：目标root约[.45066,.03273,.28326]、近乎水平，使底座前端进入20cm箱沿。直接读取USD实例化碰撞mesh并转换到base坐标，包围范围为x[−.127998,.331958]、y[−.097223,.096777]、z[−.096839,.088834]；有向包围盒与箱体分离轴间隙在目标处为−13.58mm、实际终止处为−6.78mm。包围盒重叠本身不证明精确mesh穿透，但与独立实测底座接触一致；不能一概归因于失去支撑。依据和报告哈希保存在ew/eu-collision-diagnosis.json。

新增默认关闭`guidance_body_collision`：在原15个混合支撑机身候选上，沿运行时同样的位置/四元数插值采21点，检查真实USD底座碰撞mesh的保守有向包围盒与固定箱体至少1cm分离，同时检查四腿全路径名义软限位、按当前实测力矩估计的加载目标软限位及1mm FK残差。端点.03rad余量和原机身/关节平滑限制保留；无可行候选则保持当前姿态、禁止卸载。记录所选/保持路径最小间隙和关节余量。该检查仅覆盖base包围几何，未覆盖其他连杆、两采样点之间、跟踪误差和未来载荷变化，仍需原碰撞/执行器/承重门禁与物理验证；不能当作安全证明。

18项引导数学检查、编译与差异检查通过。新增检查包含USD实例变换、拒绝本次过低目标、接受抬高/前倾可净空姿态、世界平移不变性、端点无碰撞但路径穿过箱体、关节可行但碰撞时拒绝。远端`climb-body-clearance-20261002-ew`于22:53:17启动监控PID575279，GPU0顺序运行eu feasible100回归、开启净空检查100秒，各32环境seed513、env6轨迹。已确认首批环境初始化完成并进入rollout，无重复训练。仍为箱沿100秒诊断，未新增PPO，未计入24秒或原起点12秒验收；先检查ew进程与两份结果再继续。

最新已完成eu两批均0/32且无缺失：baseline24超时/1底座/6姿态/1低姿态、三足99.861%；feasible100为15超时/9底座/8姿态、三足99.764%。两批最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。ew尚无结果，不能声称已改善。最新原速视频仍 `index.html` 。源码与交接更新指定分支，实验快照/诊断位于本地及远端仓库外；PUSH、MuJoCo、实机暂停。

<a id="record-0109"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：eu失败，ev最新原速视频已交付（2026-10-02 22:38）

用户要求“最新视频”。已完成远端ev录制并交付 `index.html` （本地HTTP PID2006401），目录`climb-feasible-review-20261002-ev`。固定展示与前版相同的env6，在新评估结果出来前确定，未按成功筛选。原始100秒/2500帧/25fps，远端空闲GPU1录制，与GPU0原评估32终态、env6轨迹、步态与关节指标逐值相同，actor及源码哈希一致，整段解码通过。

最新eu端点可行参考未通过物理验证：env6在33.82秒因底座接触终止。主视频`latest-episode-env6.mp4`只保留第一次终止前846帧，33.84秒/25fps，无时间缩放；最后画面采样在33.80秒，下一帧自动重置未混入主片。原始`latest-env6.mp4`100秒完整保存，后半段含重置，页面明确标注并可下载。已检查抽帧、画面与时长；开头渲染初始化画面保留。

eu两批64终态完整，完整成功均0/32。baseline逐值复现et100秒全部终态、轨迹及质量：24超时/1底座/6姿态/1低姿态，三足99.861%；feasible100为15超时/9底座/8姿态，三足99.764%。两版最长腾空0、竖直速度峰值1.025006m/s、单足合力373.566N、含初始化累计饱和.460s。几何端点检查增加后，碰撞失败增多，不能作为改善或可交付策略；本轮100秒仍仅箱沿诊断，不计入24秒或原12秒验收。

录制与原评估均结束，无新PPO、评估或录像需重启。下一轮需追查端点有余量但过渡/承重失稳的原因，验证连续路径与实测支撑载荷，不能仅以候选端点可行继续扩大同配置训练。eu comparison.json及ev核验/原始和主片均保存在本地与远端仓库外；源码仍0bef3be，当前只更新交接。PUSH、MuJoCo、实机暂停。

<a id="record-0110"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：et卡在前脚箱面补进准备；eu可行机身参考对照运行中（2026-10-02 22:18）

et三批结束，96终态无缺失，完整攀爬仍均0/32；baseline逐值复现es quarter全部终态、env6轨迹及质量。follow60也与baseline同终态及质量，因新增前脚跟进尚未发生。三批均24超时/1底座/6姿态/1低姿态终止；60秒两批三足99.775%，100秒为99.861%，最长腾空0、竖直峰值1.025006m/s、单足合力373.566N、含初始化累计饱和.460s。三足比例受时长影响，不是安全改善；100秒仅诊断，不计入24秒或原12秒验收。

follow100有9个环境进入前脚箱面补进准备，但未完成下一次抬脚。env6机身x约.640/z.326，FL落点目标1.0658，四脚接触、支撑裕量32.5mm；FR名义calf−2.64256rad超过原软下限，名义越限量含.01rad保护约.02411rad，虽然组合加载目标未超限，仍被几何门控拒绝。前脚补进流程已触发，固定机身姿态不能满足该阶段四腿同时可行，继续延时无效。

新增默认关闭`guidance_feasible_pose`：双前脚箱面承重、后脚仍低处时，在5种斜面比例×3种高度偏移共15个候选中检查四条腿IK残差、名义软限位及按实测已施加力矩/30估计的加载目标；需至少.03rad综合余量，单次高度变化≤8cm、姿态变化≤.35rad。选择余量较大的小幅机身姿态，仍沿原1.5秒插值并经过关节q/v/a、载荷分配和接触门禁。无可行候选则保持实测机身姿态，禁止卸载；在四脚稳定、相位0且几何目标被拒绝时允许重新规划。候选只检查端点，载荷估计不含未来变化，不能证明轨迹/动力学可行，也不能替代物理验证。

16项引导数学检查及编译/差异检查通过，新增检查覆盖实测混合脚高近似姿态的全部关节余量与无可行候选时保持。远端`climb-feasible-pose-20261002-eu`于22:17:01启动监控PID570805，GPU0顺序做et100秒回归、新参考100秒，各32环境seed513、env6轨迹。仍是100秒箱沿诊断，20cm箱、停稳/碰撞/执行器门禁不变，无新PPO。先核对eu进程与结果，避免重复启动et。最新视频仍en/8791；PUSH、MuJoCo、实机暂停。比较/诊断本地和远端保存，源码与交接推送指定分支。

<a id="record-0111"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：es后脚承重进展到9/32，et补充箱面前脚跟进（2026-10-02 21:47）

es三批全部完成，96终态无缺失，完整攀爬仍均0/32；全幅baseline逐值复现er60秒全部终态、env6轨迹和步态/关节质量。quarter为24超时/1底座/6姿态/1低姿态，三足99.775%；half为24超时/1底座/7姿态，三足99.770%；baseline同half终止分布，三足99.772%。三组最长腾空0、竖直峰值1.025006m/s、单足合力373.566N、含初始化累计饱和.460s；不能把局部脚序进展等同安全或完整任务改善。60秒均仅诊断。

quarter/half各9个终态选中RL，已通过RR承重门控；quarter env6可继续交替后脚：约22.5秒RR、33秒RL、45秒再次RR、55秒再次RL，60秒机身x约.651，后脚跟进至x约.39/.40，而前脚始终x约.845。half env6仍在第一轮RL准备，组合目标越限约.0305rad，未因延时解决。quarter前进是局部进展，不宣称9个回合完整成功。

代码检查发现旧选脚只在前脚未上台时选择前脚；双前脚上台后会持续选择落后的后脚，使前脚支撑锚点固定在箱沿，无法为持续前移保留跨度。新增默认关闭`front_followup`：双前脚实际在台面、后脚最小x达到.35时，逐脚补齐前脚到至少1.03；后脚最小x达到.55时补齐到至少1.23。实际仍用原22cm箱面步幅、单脚卸载/落地承重/停稳检查；后脚12cm地面跟进及四脚上台后的原循环保持。该阶段规划适用于当前固定箱几何，尚待物理验证；不改箱高、执行器、碰撞和验收条件。8项阶段数学检查通过，覆盖前脚首次上台优先、逐脚补进、后脚继续跟进及全上台回退循环；编译/差异检查通过。

远端`climb-front-followup-20261002-et`于21:46:01启动监控PID566300，GPU0顺序做quarter60秒回归、新脚序60秒、新脚序100秒，各32环境seed513、env6轨迹。100秒仅用于暴露完整后续脚序问题，不算24秒或原起点12秒达标；门禁、20cm箱保留。先检查et进程与输出，避免重复启动es，无新PPO。最新视频仍en/8791，不展示新脚序。比较和诊断同步本地/远端仓库外目录，源码与交接推送指定Git分支；PUSH、MuJoCo、实机暂停。

<a id="record-0112"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：er完整斜面姿态失败；es小幅抬升/俯仰对照运行中（2026-10-02 21:16）

er三批全部完成，96终态无缺失，完整攀爬仍均0/32。关闭斜面姿态的baseline40逐值复现eq12cm全部终态、env6轨迹及步态/关节质量。baseline为23超时/2底座/7姿态终止，三足99.671%、最长腾空0、竖直峰值.619553m/s、单足合力373.566N、含初始化累计饱和.420s。plane40和plane60均24超时/1底座/7姿态，三足分别99.670%/99.772%，最长腾空0、竖直峰值1.025006m/s、足力373.566N、饱和.460s。60秒更高三足占比受时长影响，不是成功或安全改善；完整斜面候选未通过，后脚进度退步。

plane40/60的env6均停RR准备，相位0，支撑裕量约29mm、四脚接触；FR名义calf−.96795rad虽在限位内，加实际计算载荷补偿2.1808Nm/30后组合目标超出软上限约.03675rad，因而不允许卸载。机身实际z约.3806m、俯仰约−.293rad。延时至60秒仍未推进，不能仅归因于时间不够。

从USD读取实际关节限位并应用原.9软限位，按实测脚位和记录载荷补偿做固定姿态几何对比：er env6在原斜面幅度.25/.5时估计最小组合限位余量分别.1663/.1314rad，全幅约.0092rad；eq12cm的RL阶段也更支持较小幅度。eq16cm的RL姿态在部分幅度下仍不可行，故不宣称存在全程几何保证。该离线估计不含实时姿态反馈和载荷变化，不替代物理验证；数据在er/pose-blend-analysis.json。

新增`guidance_plane_fraction`默认1，保持er行为；仅在支撑斜面已启用时可配置[0,1]，将机身高度在低处净空与斜面高度间插值、俯仰按同一比例缩放，保留原平滑、接触、限位与20cm箱。15项引导检查及编译/差异检查通过，包括0/1端点与部分俯仰/高度。远端`climb-plane-fraction-20261002-es`于21:15:45启动监控PID563574，GPU0顺序做全幅60秒回归、.25幅度60秒、.5幅度60秒，各32环境seed513、env6轨迹。60秒仅诊断，不计入24秒或原12秒验收；先检查es结果，避免重复启动，无新PPO。视频仍en/8791，PUSH、MuJoCo、实机暂停。代码和比较产物分别更新至指定Git分支与仓库外本地/远端目录。

<a id="record-0113"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：eq完成首只后脚承重，er混合高度机身姿态对照运行中（2026-10-02 20:46）

eq三批完成，96终态无缺失，完整攀爬仍均0/32；baseline逐值复现ep40秒全部终态、env6轨迹、步态和关节指标。16cm后脚短步为23超时/1底座/8姿态终止，三足99.659%；12cm为23超时/2底座/7姿态，三足99.671%；baseline为24超时/1底座/7姿态，三足99.689%。三组均最长腾空0、竖直峰值.619553m/s、单足合力373.566N、含初始化累计力矩饱和.420s。40秒只是箱沿诊断，未通过24秒或原起点12秒验收。

两个短步版本各3/32通过RR地面落脚承重门控、进入RL准备；12cm版其中2个终态已抬起RL。其余早期失败仍保留，不能把3个回合的脚序进展当完整成功。16cm env6在RL准备时，FR名义hip约1.127rad，名义限位超量.19466rad、组合目标超量.28577rad；实际机身z约.305m，前脚已在20cm台面且机身几乎水平，前腿空间在侧向转移中不足。12cm env6尚无越限、40秒末RL处于.265摆动相位；有时间预算因素，仍需完整终态验证。

新增默认关闭`guidance_support_plane`：只在双前脚实际箱面接触且至少一只后脚仍在低处时，根据前后脚高差与纵向间距计算支撑斜面，坡度限幅.35（俯仰约±19.3度）；机身目标高度按斜面加原.28m净空，俯仰朝向斜面、保留偏航。位置与四元数用原1.5秒平滑阶段插值，仍经过原关节q/v/a、软限位与力矩限制。此为待验证参考，不宣称倾斜或抬高后一定可承重。新增检查验证俯仰方向、世界平移/偏航不变性及四元数同向插值，15项引导检查通过；记录目标四元数便于追溯。

远端`climb-support-plane-20261002-er`于20:45:36启动监控PID562249，GPU0顺序做eq12cm/40秒回归、新机身参考40秒、新参考60秒，各32环境seed513、env6轨迹。60秒仅用于观察后脚后续过程，不冒充24秒或原12秒达标；门禁及20cm箱不变。先检查er进程及输出，避免重复启动eq；无新PPO。eq比较与诊断在本地/远端仓库外目录；视频仍en/8791，尚未包含新后脚控制。PUSH、MuJoCo、实机暂停。

<a id="record-0114"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：ep开始后脚摆动但落地越限；eq后脚短步对照运行中（2026-10-02 20:16）

ep三批已结束，96终态无缺失，完整攀爬均0/32；默认关闭回归逐值复现eo全部终态、env6轨迹、步态和关节指标。反馈40秒版为24超时/1底座/7姿态终止，三足99.689%、最长腾空0、竖直峰值.620m/s、单足合力373.566N、含初始化累计力矩饱和.420s；反馈24秒版25超时/1底座/6姿态终止，三足99.602%，其余上述峰值相同。baseline40秒为24超时/1底座/4姿态/3低姿态，三足99.463%、.120s、.742m/s、588.144N、.960s。较低冲击不等于任务完成，尚无可交付策略。

40秒反馈版10个环境进入RR阶段，其中3个终态到摆腿相位1、1个相位约.37、6个仍准备。env6由原来的支撑区外约11mm，转移到支撑区内33mm并确实抬起、前移RR；但落脚仍未通过承重门控。其RR实际脚位约[.3751,−.1743,.02346]，落地参考下探至z=.009，名义关节软限位超量.10124rad、组合目标超量.08482rad，参考遭拒绝。此为后脚摆动局部进展，非后脚落地成功或完整攀爬通过。

同一实测env6机身位姿和下探深度的离线几何计算：22cm地面步幅对应RR膝关节−.84076rad，16cm为−1.05700，12cm为−1.13886；缩短步幅可增加屈膝余量，但这只是固定姿态计算，不能证明动态承重可行。新增默认关闭`rear_ground_stride`：仅双前脚已在箱面接触、当前选择后脚且原目标仍在地面时，使用指定短步；前脚、箱沿跨越与其他落点保持原规划，20cm箱及碰撞/执行器/停稳门禁保留。原长步名义IK由实测记录复算一致，编译与差异检查通过。

远端`climb-rear-followup-20261002-eq`于20:15:33启动监控PID559626，GPU0顺序做ep40秒回归、16cm后脚跟进、12cm后脚跟进，各32环境seed513、40秒，记录env6。40秒仅诊断，不算24秒或原起点12秒验收；未开始新PPO。先核对eq进程与结果，不重复启动ep。ep比较与几何记录已本地/远端同步。视频仍en/8791，不展示ep/eq新控制；PUSH、MuJoCo、实机暂停。

<a id="record-0115"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：eo证实延时仍卡住；ep实测支撑反馈对照运行中（2026-10-02 19:45）

40秒eo诊断已完成：完整成功0/32，32终态无缺失，24超时/1底座/4姿态/3低姿态终止；三足99.463%、最长腾空.120s、竖直峰值.742m/s、单足合力588.144N、含初始化累计力矩饱和.960s。该40秒实验仅诊断，不计入24秒或原起点12秒验收。10个环境仍停RR准备，没有后脚抬升；env6到40秒仍相位0，支撑裕量−10.98mm，FL失去接触，预测卸载份额已1。延时本身未解决后脚转移，不能再解释为只是录像时间不足。结果SHA `c918f73cc60cf328ddea4babff22f3a76c01cc34aade45a1fd02df2e5689c5b0`，comparison.json已本地/远端保存。

代码诊断发现机身捕获只允许一次最多8cm的目标位移，目标到达后不会继续转移；卸载仍仅随时间推进，即使实际COM仍在预期三脚支撑区外。新增默认关闭`guidance_support_feedback`：身体到达目标1cm内、四脚接触且低速、未开始卸载时，若支撑裕量<25mm，则重新捕获下一段最多8cm、原1.5秒平滑转移；卸载改为1.5秒斜率，需实测其他脚接触、裕量≥25mm、低速、名义及前一帧组合目标限位有效。条件失去时仅在选中脚确有接触下恢复其载荷；摆腿开始后保持该脚卸载，仍用原落脚控制恢复承重。原关节q/v/a、力矩前馈限制及20cm箱不变。此为待验证控制修正，不等于稳定性已改善；现有支撑力求解仍有接触可行性限制，需看实际结果。

远端`climb-support-feedback-20261002-ep`于19:44:42启动监控PID556241，GPU0顺序做eo40秒零actor回归、新反馈40秒、新反馈24秒，各32环境/seed513，记录env6。14项引导数学检查通过，编译/差异检查通过；未开启新PPO。首先核对ep输出和进程，避免重复启动。最新视频仍en/8791的24秒em版本，页面已更新eo40秒诊断结论，不拿旧录像冒充反馈修正。PUSH、MuJoCo、实机暂停。

<a id="record-0116"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, CLIMB_EDGE_TRAINING_20261002_CN.md, NEXT_STEPS_CN.md。

## 最新：en两前脚录像已交付，eo区分时限与后脚转移阻塞（2026-10-02 19:39）

用户询问“腿已经搭上去了，怎么不继续动了”。已交付新视频 `index.html` （本地HTTP PID1997794），目录`climb-mixed-review-20261002-en`。按em中进入RR准备环境的最小编号选择env6，公开标明整批0/32与选择依据。远端录像24秒/600帧/25fps，32终态、步态/关节质量逐值复现em零actor，源码及actor哈希一致；env6原评估无轨迹，未声称轨迹相等。完整解码与抽帧检查通过，两前脚确有台面承重；首帧渲染黑帧保留。录像已结束，不重复启动。

新轨迹显示env6约12秒进入第二前脚准备，22.5秒才进入RR准备，24秒超时；终态仍四脚接触，RR约56.7N，预期三脚支撑裕量−9.1mm，尚不满足卸载/抬腿门控。因此不能把24秒截止直接认作永久卡死，也不能据两前脚已上台宣称登台成功。旧8790仍是ej首脚悬停版本，不展示最新进展。

已启动独立`climb-mixed-duration-20261002-eo`诊断：只将em零actor回合延长至40秒/2100步，仍32环境seed513、20cm箱、原停稳/碰撞/执行器及步态门禁，记录env6。该40秒实验不属于24秒或原起点12秒验收；目的是判断后脚推进仅缺时间还是持续支撑转移阻塞。监控PID555588，19:37:15启动并等待en结束后执行；先核对进程和输出，不重复启动。未启动新PPO；PUSH、MuJoCo、实机暂停。下方em/el结果与失败指标均保留。

<a id="record-0117"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：em两前脚进展仍伴随失稳，完整攀爬未通过（2026-10-02 19:33）

el/em均已结束，各96个终态无缺失，完整攀爬仍全部0/32。el零actor有28/32通过首脚实际接触、加载及停稳门控；em混合高度参考让零actor10/32、训练actor9/32进一步转入后脚RR准备，但尚未完成后脚跟进。em回归逐值复现el零actor全部终态、步态和关节指标；记录环境由0改为3，未声称轨迹相等。

em零actor：27超时/1底座/3姿态/1低姿态终止，三足99.478%、最长腾空.100s、竖直峰值.729m/s、单足合力588.144N、含初始化累计饱和.940s。训练actor：19超时/1底座/11姿态/1臂接触，三足98.836%、.380s、.914m/s、255.578N、1.060s。推进了脚序，但冲击与部分稳定性指标恶化，不能作为成熟策略或安全改善交付。

em零actor env3第700步在FR完全卸载后仍有36mm支撑裕量，但第725步RL失去接触、RR组合目标超限约.00869rad；随后持续卸载、目标拒绝和支撑退化同时出现。降低机身目标没有解决加载可行性。下一轮优先验证实际接触、组合关节/力矩余量约束下的渐进载荷转移，以及失去支撑时的卸载恢复；不能只继续降低高度或扩大同配置PPO。还需检查已进RR准备的回合为何无法后脚跟进。

远端`climb-mixed-support-20261002-em`三批已完成，不重启旧监控PID554334；无新PPO。本地/远端comparison.json保存完整指标和报告SHA。13项引导+5项步态检查通过。现有视频8790是ej版本，未包含el/em新落脚，不能拿旧视频展示本轮进展。保留20cm箱、碰撞、执行器和停稳门禁；本轮均为24秒箱沿课程，原起点12秒及最终两组独立种子验收未通过。PUSH、MuJoCo、实机暂停。

<a id="record-0118"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：el首脚已实际承重，完整攀爬仍失败；em混合高度对照运行中（2026-10-02 19:26）

el三批全部完成，96终态无缺失、完整成功均0/32。落脚控制零actor有28/32通过首脚接触、≥8N加载和200ms稳定门控，进入FR准备；训练actor为26/32。两组终态各19个环境仍有脚在台面承重。零actor为25超时/6姿态/1低姿态终止，三足99.376%、腾空.040s、竖直峰值.651m/s、单足185.601N、含初始化累计饱和.480s；训练actor20超时/1底座/10姿态/1臂接触，三足99.035%、.380s、.725m/s、200.084N、1.060s。首脚承重是局部进展，不代表完整攀爬或稳定性通过；推进到第二脚后新增失稳。

混合高度诊断：28个进入FR准备的零actor终态均有后腿目标拒绝，名义FK误差均<0.1微米；env3名义软限位误差0，组合加载目标仍拒绝。原捕获机身高度用四脚平均高度+.28m，首脚上台会将目标抬高约5cm。新em显式对照在脚高差>10cm时改用最低脚高度+.28m，平地和四脚同高仍沿用原平均值；增加名义关节与组合限位超量记录。此为待验证参考修正，不宣称已解决混合高度动力学。

远端`climb-mixed-support-20261002-em`于19:25:58启动，监控PID554334，GPU0顺序做el零actor回归、新高度零actor、ef299加新高度，各32回合/24秒，记录env3轨迹。13项引导+5项步态检查通过。先核对em进程及输出，避免重复启动；el已结束，无新PPO。视频8790仍是ej落脚修正之前的版本，不代表el/em。保留20cm箱、碰撞、执行器与停稳门禁，24秒箱沿诊断不替代原起点12秒验收；PUSH、MuJoCo及实机暂停。

<a id="record-0119"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：el接触探测与承重恢复对照运行中（2026-10-02 19:16）

已核对ej/ek全部评估与录像进程结束，未重复训练。当前已交付视频仍 `index.html` ：ej零学习修正28/32首脚移到箱面附近，但尚未接触承重，完整登台仍0/32。

本轮el新增默认关闭的落脚控制：摆腿到末端后以4mm/s向下探测，最多15mm；实际接触连续100ms后用600ms逐渐恢复四脚载荷；选中脚实际承重≥8N、其他脚接触、身体低速连续200ms才允许换脚。失去接触时立即撤销对该脚的支撑分配并重新确认；原碰撞/执行器/参考限速与20cm箱不变。新增换脚门控叠加在原真实抬脚、横移和四脚接触条件上，不用时间代替落脚。24秒箱沿课程不是原起点12秒验收。

远端目录`climb-landing-contact-20261002-el`，19:16:16启动监控PID552748，GPU0顺序做ej零actor回归、新落脚控制零actor、ef299加新控制，各32回合/24秒。12项引导及5项步态检查通过，物理结果待出。无新PPO；首先核对el进程与输出，不能重复启动。用户最新视频请求已处理。PUSH、MuJoCo及实机暂停。

<a id="record-0120"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：ej首脚已移到台面附近，仍未承重；ek原速录像已交付（2026-10-02）

ej三批已全部结束，96个终态完整，完整攀爬仍均0/32。先卸载版本不加学习修正：28/32终态首脚移到台面附近并进入下降末段、4/32仍等待卸载；全部超时，三足100%、无腾空、竖直峰值.102625m/s、单足118.916N、含初始化饱和0。叠加ef299：26/32终态首脚移到台面附近，26超时、1底座接触、4姿态终止、1机械臂接触；三足99.499%、最长腾空.380s、竖直峰值.724949m/s、足力200.044N、饱和1.060s。两版终态均没有台面承重，不能称首步或完整攀爬成功。

下一瓶颈是接触落脚与恢复承重：有移动的回合相位停在1，脚中心约z=.2248m、参考.2245m，实际法向力不足接触阈值，选中脚载荷分配仍为0，因而无法触发四脚稳定/换脚。后续应在原安全/执行器范围内验证接触探测、渐进受载和落脚等待，不能按时间直接换脚或跳过接触门禁；仍等待卸载的4回合也需单独保留诊断。

ek三段原速录像全部完成并取回，入口 `index.html` ，本地HTTP PID1995092。主视频为无学习修正env3（原评估按ID排序首个完成前移的回合），另有训练修正env0与等待卸载env0。每段完整24秒、600帧、1280×720/25fps；全部96终态、步态和关节质量逐值复现原评估，两个env0轨迹也逐值一致；env3原报告没有轨迹，未声称其轨迹已匹配。已检查解码、时长和画面，前脚清晰可见，但始终没有台面承重。源码/报告/录像/核验在仓库外`artifacts/go2-piper/climb-preunload-review-20261002-ek`。不新增独立验收样本，当前无PPO或录像作业需重启。下一轮优先接触探测与恢复承重。24秒箱沿课程不替代原起点12秒；PUSH优化、MuJoCo及实机暂停。

<a id="record-0121"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：ei水平力矩对照失败，ej先卸载后抬脚运行中（2026-10-02 18:47）

ei三批全部完成、96个终态完整，无台面承重，完整攀爬均0/32。水平力矩补偿零actor为32底座接触：三足87.737%、无腾空、竖直峰值.202m/s、单足143.496N、累计饱和0；训练actor为28底座接触/4姿态终止：三足87.094%、腾空.060s、竖直峰值.530m/s、单足254.649N、累计饱和.420s。低冲击失败不算改善，未继续相同PPO。

定位到可核对的时序缺口：ei零actor env0第225步，选中脚高.117m且实际足力0N，但分配仍要求该脚承担24.084N；此时RR也失去接触，COM支撑裕量−.0183m。原卸载随抬升相位渐变，脚已离地时仍把部分重量交给悬空脚。该证据不排除其他支撑/几何问题。

ej新增默认关闭的先卸载门控：1.5秒身体转移后，在原脚位用1.5秒完成四脚→三脚载荷转移；另三脚接触、选中脚≤5N、COM裕量≥15mm、机身速度<.04m/s、角速度<.15rad/s同时持续.2秒才放行抬脚。已完成实际卸载后进入摆腿，避免原四足接触等待阻塞已轻载的脚。原20cm箱、碰撞/执行器限制、24秒和停稳门禁保留；仍是箱沿诊断，不是原起点验收。

目录`climb-preunload-20261002-ej`，18:47:39监控PID549246，GPU0依次做ei零actor回归、零actor新门控、ef299新门控，各32回合；10项数学检查通过。ej关闭新门控的32终态、trace、步态和关节数据已逐值复现ei；开启项已进入物理评估。先核对ej进程和物理结果，避免重复启动。新候选未达标，最新视频仍dc/8789；NAV接管、实际混合高度及原起点完整攀爬未通过。详见[箱沿记录](#source-climb-edge-training-20261002-cn)。PUSH优化、MuJoCo及实机暂停。以下旧状态仅为历史。

<a id="record-0122"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：ef及eh均失败，ei水平支撑力矩对照运行中（2026-10-02 18:30）

ef的300轮训练及四批评估全部完成，128个终态完整，攀爬均0/32；最终箱沿三足89.626%、无腾空、竖直峰值.561m/s、单足196.521N、含初始化累计饱和1.420s；原起点为97.914%、.060s、.951m/s、569.397N、2.100s。不继续相同训练，尚无达标策略。

eh载荷分配对照三批全部结束，无新PPO。关闭新项回归逐值复现ee全部32终态、轨迹和质量；重新分配竖直承重的零actor32次底座接触，训练策略26底座接触/6姿态终止，均0/32且无台面承重。零actor三足89.589%、无腾空、竖直峰值.263m/s、单足147.790N、饱和0；训练策略89.268%、.080s、.542m/s、184.132N、.280s。较低冲击不能算改善，载荷分配失稳时的力矩残差也已记录。eg只因TorchScript加载参数错误在回合开始前失败，日志保留、进程已结束。

ei新增默认关闭的水平支撑力及力矩配合：根据机身转移参考速度与实测速度误差给出最大.4m/s²的水平加速度，按每脚实际高度修正承重力矩并记录完整六维残差；原PD/延迟/限位/力矩前馈75%限幅和20cm箱均保留。目录`climb-wrench-balance-20261002-ei`，18:30:40监控PID548312，GPU0依次做旧竖直力回归、零actor新控制、ef299新控制，各32回合/24秒；不要重复启动。9项数学检查通过，包括不同脚高下合力/力矩一致性，但不是实际混合高度攀爬验证。ei关闭水平项的回归已逐值匹配eh零actor全部32终态、轨迹和质量；开启项的候选已进入物理评估。

下一步先核对ei物理结果，不以奖励、初态稳定或三足比例代替完整成功。最新视频仍dc/8789；混合高度实际支撑、NAV接管、原起点完整攀爬未通过，24秒课程不替代12秒验收。详见[箱沿记录](#source-climb-edge-training-20261002-cn)。PUSH优化、MuJoCo及实机暂停。以下旧运行状态仅为历史。

<a id="record-0123"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：受载初始化已验证，箱沿残差训练 ef 运行中（2026-10-02 17:38）

本轮发现da的21个超时终态均触发IK软限位拒绝，单腿无效曾冻结全部支撑腿目标。新增默认关闭的受载目标捕获、逐腿有效性检查、前移抬脚轨迹和可配置机身净空。dd关闭新选项回归与dc全部32终态、轨迹和质量指标一致；开启后仍0/32。ee重新采用实测受载站姿并保留加载位置目标，初始化单独检查32/32站满24秒、无安全终止、无饱和，但引导攀爬仍0/32，不能作为稳定攀爬交付。

ef于北京时间17:34:04在既有远端启动箱沿残差PPO，512环境、300轮、seed634、GPU0；训练/监控PID543078/543080，17:38核对正常迭代。使用ee验证的受载起点、显式足端引导（净空.28m、转移1.5s/摆腿4s），学习支撑与平衡修正；std=.3、lr1e-4，姿态/可达奖励权重各6。目录`climb-guided-residual-train-20261002-ef`，监控等待训练完成后评估50/150/299轮箱沿和299轮原起点，不要重复启动。此前dd/ee评估已结束。

最新视频仍是dc的 `index.html` ，不是ef。混合高度、NAV接管、原起点完整攀爬均未通过；24秒课程不替代12秒验收。完整指标与来源见[箱沿记录](#source-climb-edge-training-20261002-cn)。PUSH对外交接改用[PUSH最新入口](../PUSH_CURRENT_HANDOFF_CN.md)，其优化及MuJoCo/实机仍暂停。下方旧运行状态仅为历史。

<a id="record-0124"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：箱沿训练与引导诊断未达标，近景视频已交付（2026-10-02）

cx/cy各600轮及12批评估全部结束，384个终态完整，完整登台仍均0/32。两组最终模型均曾抬起首脚，但都没有台面承重。cy把32/32终态落点带回腿长几何范围内，对照cx仍全部不可达；这是局部变化，不是稳定攀爬成功。

本轮转为默认关闭的显式支撑转移/足端IK诊断。cz零actor引导为17姿态终止、15超时；da加入实测机身位姿和速度反馈后为21超时、4底座接触、7姿态终止，仍0/32且无台面承重。da三足97.895%、最长腾空.22s、竖直峰值.600m/s、单足合力191.331N、含初始化累计力矩饱和.76s；不能把安全终止减少等同于改善，腾空/饱和反而变差。不能直接扩大或继续相同训练。当前无新PPO；da预备residual脚本未启动。

用户要求的最新侧面近景视频已完成，入口 `index.html` ，本地产物为仓库外 artifacts/go2-piper/climb-edge-close-review-20261002-dc 。分别展示cy599训练策略与da零actor反馈诊断，均为env0完整24秒、1280×720/25fps/600帧；全部64终态、完整轨迹与质量指标逐值复现db对应报告，cy另已匹配原32回合诊断。画面已检查，前脚不再被箱体遮住；两版均无台面承重。dc录像进程已结束；无需重录或重启旧作业。8788仍是历史平地视频。所有箱沿诊断为24秒课程，不能冒充原起点12秒验收；尚无达标慢爬策略。

优先：结合用户最新近景检查继续箱沿首脚落台与受载支撑控制，不重复训练失败配置。应先核查实测机身偏差、支撑脚滑移、摆腿IK受限/拒绝更新及落脚承重；不能仅增加奖励或按等待时间推进。默认关闭的引导只测试了cu全脚在地面的箱沿起点，混合高度支撑尚未验证。混合高度起点、NAV接管、原起点全程仍未通过。详见[箱沿记录](#source-climb-edge-training-20261002-cn)。PUSH/MuJoCo/实机暂停。下文保留历史，旧“运行中”不覆盖本节。

<a id="record-0125"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：出现局部抬脚，完整登台仍失败（2026-10-02 15:48）

cv/cw训练及12批评估全部结束，384个终态完整、全部超时，箱沿与原起点成功仍均0/32。不能再笼统说“完全没有抬脚”：cw/model299箱沿有24/32终态锁存曾离地，17/32相位通过抬高门槛进入前移，但所有环境均无台面承重；env0最高脚高.22565m。cv/model299也有30次短暂离地，但均卡在抬升阶段，env0最高仅.05784m。这是局部训练变化，不是自然稳定攀爬或验收成功。

cw新的主要问题是机身后退并降低：终末root x=.183–.350、z=.236–.270m；按实测终态姿态复算，31/32的抬高落点超出腿几何伸展范围，FK目标残差最大.08167m，实测脚位FK误差仅1.684微米。该诊断仅针对固定终态姿态，不是完整动作不可行证明。

下一步cx/cy从同一cw/model299继续各600轮、512环境、std=.45、seed633。cx沿用原奖励作为续训对照；cy将地形姿态权重2→6，新增几何伸展外界/3cm裕量反馈权重6。外界只是必要条件，不代表满足关节限位、碰撞或稳定性。动作控制及全部原门禁不变。cx远端回归已逐值复现cw/model299的32终态、完整trace及质量指标。两组已于北京时间15:50:33启动；cx训练/监控PID535142/535144，cy为535145/535147，GPU0/1。监控100/300/599轮的箱沿及原起点诊断，不要重复启动。视频8788仍为旧版，不代表当前模型。详见[箱沿记录](#source-climb-edge-training-20261002-cn)。

<a id="record-0126"></a>

来源：AGENT_HANDOFF_CN.md, CLIMB_CRAWL_STATUS_20261001_CN.md, NEXT_STEPS_CN.md。

## 最新：cu训练结束，转入卸载与抬脚反馈对照（2026-10-02 14:45）

2026-10-02 15:07核查：cv/cw的300轮训练均已结束，两个自动评估监控仍运行；各自第50轮箱沿与原起点评估均0/32、32超时且无缺失，尚未检测到首脚抬起。第150轮箱沿评估进行中，最终299轮结果未出；不要重复训练或在最终诊断前延长相同配置。

cu的300轮PPO与全部六批评估已结束，远端旧训练/监控进程均已退出；50/150/299轮箱沿与原起点均0/32，192个终态完整、全部超时，不能算攀爬改善。全部仍卡在首脚抬升阶段。最终箱沿三足100%、无腾空、竖直峰值.489m/s、足力119.588N、累计饱和.22s；原起点为99.830%、.04s、.840m/s、196.725N、.26s。模型299仅作下一轮初始化，未交付。

已定位训练信号缺口：最后env0首脚仍承担45.87N，脚高.02328m，参考高.25450m；原接触奖励在该脚仍触地时也给3/4分，没有明确的逐步卸载反馈。新cv/cw保持同一动作控制、箱沿起点、20cm地形及安全门禁，只调整学习反馈：其余三脚真实承重时奖励首脚卸载、离地；新抬脚高度按本脚已达到的最高值增量一次性计分，避免悬停/反复上下刷高度奖励。新增两项反例检查排除腾空和缺支撑时的奖励。

cv/cw已于北京时间14:49:27从同一cu/model299开始各300轮、512环境、seed632、lr1e-4；仅探索std=.15/.45不同，GPU0/1。cv远端零actor回归通过，32终态、整段轨迹和质量指标与cu逐值一致。cv训练/监控PID530854/530855；cw为530857/530858。评估监控会等待各自训练释放GPU，再检查50/150/299轮的箱沿与原起点。见[箱沿训练记录](#source-climb-edge-training-20261002-cn)。不要重启cu或重复启动cv/cw。PUSH/MuJoCo/实机仍暂停。

<a id="record-0127"></a>

来源：AGENT_HANDOFF_CN.md。

## 当前方向：按用户要求直接训练攀爬（2026-10-02）

用户明确“训练攀爬而不是行走，NAV已经可以稳定行走”。停止把平地逐脚行走和整段离线路径搜索作为主要推进方向。新增隔离任务 `GO2-PIPER-Box-Climb-Stages`：在20cm箱沿开始学习前脚上台、混合高度支撑、身体抬升、后脚跟进。训练用近箱/分阶段起点必须单独标注；`Stages-Play`默认仍用原起点，仅显式传入 `--climb-stage-bank` 才启用训练起点诊断。24秒实验与原12秒验收分开；保留原碰撞、执行器限制和连续停稳1秒条件。

当前尚无达标慢爬策略。cp/cq/cr四阶段起点检查均0/32，全部终态完整；cr修正初始化目标与显式PD增益后没有腾空，但仍27次姿态终止，拒绝直接拿这组名义姿态训练。cs实测过渡姿态平移到箱沿也32次姿态终止，不能当作稳定站姿。ct默认站姿贴箱过近导致32次底座接触。cu将前脚放在x=.60（箱面x=.75），32回合均站满24秒、零安全终止，三足100%、无腾空、竖直峰值.553m/s、足力111.338N。cu箱沿PPO已于北京时间14:01:53启动，512环境/300轮，训练PID526883、监控PID526884；还没有新训练策略的攀爬成功结果。详细结果及后续启动记录见[箱沿训练记录](#source-climb-edge-training-20261002-cn)。视频8788仍为旧平地诊断，不是新攀爬成果。

后续优先事项：核对cu训练及监控进程，不要重复启动；第50/150/299轮分别做训练起点及原起点的32回合诊断，报告成功、完整性、三足支撑、腾空、竖直速度、足力和饱和时长，不能以奖励代替成功。候选固定后才做两组未用种子各32回合（每组至少30成功、无未完成）与真实速度录像。PUSH/MuJoCo/实机暂停。

以下内容按历史阶段保留，旧“下一步”不覆盖本节。

最新cn为离线整段参考预检，不是新的Isaac回合。新增plan_crawl_route.py，将原起点的支撑转移、机身前移/抬升/俯仰和20cm足端越沿统一求解，并由原2.5rad/s、15rad/s²参考限制估算时间。513的env0/7/14分别只找到25/19/14个连续名义可行步，完整路线均未完成；前三个名义落点上台也不能算成功。仅这些前缀的参考运动时间含10%余量已35.55/26.21/19.22秒，还不含初始化和实际卸载/承重等待，方案拒绝接入物理执行或训练。四足转移与摆腿分段停顿仍是瓶颈，不继续给该方案调短固定等待。下一步必须联合优化整个身体连续轨迹、步点与接触时序，并用随关节变化的全身COM/载荷检查替代冻结COM近似；先获得有可信24秒预算的完整路径，再远端Isaac验证。新增4项数学检查与原28项通过，58步用1537点复查关节/支撑近似/参考速率通过。远端无运行作业；最新物理数据仍cm的0/32，视频仍cj/8788。本地和远端cn保存报告、源码和SHA；未更改运行控制器或任务门禁。

最新cl–cm：发现固定慢摆腿方案的整段时间预算不成立。用cm全部32个准备前实测足位复算，在24cm固定步长/2.8秒逐脚摆动、支撑足不滑移的名义安排下，至少需要15–19次摆腿，仅摆腿即42.0–53.2秒，超过24秒；这不是机器人不能平缓爬箱的物理结论。停止继续微调这一固定节奏，下一步按CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN设计原起点→接近→20cm越沿→台顶停稳的整段协调轨迹，保持原任务/执行器门禁。已新增默认关闭的关节/机身/支撑位置联合采样预检：不可行时四足保持，不继续把脚送到被限位截断的落点；实际执行路径名义残差≤.106mm，但不是所有原失败已解决。cm的4.1/2.8秒首脚完成23/32、20/32，完整四步及20cm成功仍均0/32；四组候选均32个完整终态、零安全终止。全回合三足99.827%、腾空.06秒、竖直峰值.951m/s、法向足力203.635N、累计饱和最大.28秒；接管后三足100%、无腾空，cm法向峰值149.126/150.255N，不能称动力学全面改善。28项检查通过，cm关闭选项逐值复现cj/513原32终态与质量，规划决策/位移由保存输入重算一致。所有本轮远端评估及回归已结束，无新PPO；源码/原始结果/审计已归档，视频仍8788旧平地版。PUSH/MuJoCo/实机暂停。

用户已进一步明确：CLIMB必须通过平缓步态逐脚攀爬，旧model0奔跳动作不合格。新增24秒慢爬实验，单独于原12秒任务报告。b已完成：直接限速与300轮跳跃权重微调均0/32；默认站姿32回合均站满24秒但没有攀爬。c第100轮仍0/32（29超时、3底座接触），已停止。d的600轮已完成，100/300/599均0/32；最后32回合都站满24秒但不攀爬。e已复现全部32终态，确认均卡在第一只左前脚抬升阶段、未实际抬脚。下一步补充支撑转移与可执行单步控制，不延长同一无效训练。尚无达标慢爬策略。最新契约、证据与运行路径见[慢爬记录](#source-climb-crawl-status-20261001-cn)。

用户已切换优先级：**PUSH优化暂停，当前只推进CLIMB在Isaac达标**；训练、评估和录像均在远程服务器。MuJoCo及实机暂停。自动推进任务已同步此范围。PUSH保留ac已验收候选（30/32、32/32），af接管交叉检查不再启动。

CLIMB本轮目录为`/path/to/artifacts/go2-piper/climb-isaac-20261001-a`，从现有Smooth model0（SHA `ef52829997ee25677f3b3e432bc5e8ce3294d337fcb6f390d5b60d861bf29aa7`）起步，当前源码、选择性自碰撞开启，20cm固定箱/12秒/原1秒停稳。512复现30/32且全部终态匹配；预先固定的1511/2511新验收为29/32、31/32，未通过门槛，共4次早期底座接触。冻结model200在1511也为29/32，不采用回退。用户要求的同一model0成功与失败视频已完成，隐藏其他环境渲染且全部64终态匹配原报告；入口climb-isaac-20261001-a/index.html。最新结果见[CLIMB本轮记录](#source-climb-isaac-status-20261001-cn)。

注意：本轮修复录像相机原点固定env0的问题。此前PUSH非零inspect环境的视频不作为对应环境的视觉证据；遥测与批量验收不变。

<a id="record-0128"></a>

来源：AGENT_HANDOFF_CN.md。

## PUSH暂停时的记录（以下非当前待办）

最新结果：固定aa/model199与80mm压入，减至4kg/.4摩擦或5kg/.3摩擦均32/32，零安全终止、零超时。原5kg/.4任务改为100mm压入，三个诊断批次均32/32；预先固定候选后的独立2701/3701为 **30/32、32/32**，无未完成回合，达到既定Isaac门槛。2701仍有2次上沿无效接触，不能称为零安全失败或实机成熟策略。详见[负载与验收记录](#source-push-load-comparison-20261001-cn)。

更新日期：2026-10-01

当前优先级是普通 PUSH 在 Isaac 原12秒任务中达标，训练只在远程服务器执行；MuJoCo、CLIMB暂停新增实验。当前100mm候选已通过Isaac数量门槛；保留2次无效接触风险，尚未完成跨仿真与实机验证。

用户已明确持续授权本项目既有服务器上的同步、训练、评估、录像及下载，并要求提交到 `WM4N-Group/GO2-ARX5-MUJOCO` 的 `feature/go2-piper-sim2real` 分支。当前会话Full access已生效，无待确认授权。Git提交包含源码、检查和文档；原始权重、日志、录像保存在仓库外。

最新控制对照z已完成8组：间距减速未改善；60/70mm压入退化，不采用。普通腿部接管由.5改为.7秒、合法接触后仍.2秒，在已使用的517/701/1701为 **30/32、30/32、27/32**，三批均零安全终止。两次旧上沿误接触消失，剩余为推进不足与停稳过晚。该结果不是新独立验收。

当前远程aa微调：`/path/to/artifacts/go2-piper/push-ramptrain-20261001-aa`；run=`2026-10-01_09-36-12_ramp70_all_seed628`；训练PID3911950，监控PID3911952。seed628、512环境、200轮、std.03、固定lr1e-5，从u/model199初始化。实际env/agent配置已核验并下载。200轮训练及全部评估已完成：第100轮在517/701/1701为30/32、32/32、27/32，第199轮为 **31/32、32/32、28/32**，六批均零安全终止、回合完整。按预定规则选定model199，SHA `b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721`，已备份本地；不要重复启动该训练。

aa监控在80mm配置下因第三批低于30/32跳过验收。后续ac固定同一权重，将压入参考改为100mm，517/701/1701均32/32且零安全终止；2026-10-01 10:09（北京时间）固定权重、控制、物理配置后启动独立2701/3701，两批最终30/32、32/32，均完整且无超时。2701的env27/22在9.22/9.54秒因上沿无效手接触终止，均未计入成功。两个种子已使用；后续若用于修正，不能再次称为未见验收。完整校验见ac/acceptance-verification.json。

新失败历史记录已通过Isaac接入：z关闭分支与u原1701报告共有终态字段逐值一致，每个失败回合保存128步。ab离线FK复核1152个状态，位置重建误差最大2.91微米；六个推进不足回合参考对应手端约14cm、实际约6cm，提示继续检查受载跟踪。FK本身不是动力学或安全证明。

最新录像ae已完成：aa/model199、100mm压入、.7秒普通接管，3701/env0在11.40秒成功，2701/env27在9.22秒上沿无效接触后自动重置。两组全部64终态与ac原验收报告逐值一致，视频各11.68秒、1280×720/25fps；复现不新增独立样本。本地入口`../artifacts/go2-piper/push-review-20261001-ae/index.html`。后续af将普通接管改为.9/1.1秒，seed2701均31/32、零安全终止；env22到位但仅停稳.42/.40秒。优先交叉检查.9秒，尚未替换已验收的.7秒候选。

此前y录像使用u/model199与.5秒接管，不代表当前候选。

源码执行方式见[当前PUSH运行说明](#source-push-isaac-runbook-cn)，细节见[本日记录](#source-training-status-20261001-cn)。产物在仓库外 `../artifacts/go2-piper/` 下的z、aa、ab、ac、ad、ae、af、y对应目录，远程路径和哈希见各manifest；GitHub单独克隆不包含这些二进制产物。

<a id="record-0129"></a>

来源：AGENT_HANDOFF_CN.md。

## 历史阶段记录

以下按发生时间保留；其中“进行中”“种子未使用”“等待确认”等描述仅表示当时状态，以顶部最新状态为准。


本轮较早状态：u可控阶段采样训练model100在原12s调参seed517达到 **30/32、零安全终止**，32回合完整。尚未独立验收，最终199轮评估待完成后固定候选。all组50/100轮均29/32，active为29/30。失败env24推进不足、env28停稳.36s；此前env5已成功。

候选已备份本地u/candidates/active-model100/model_100.pt，SHA `7cc9d8b7a36c7b6de0b63a31a1e600f837ac00dad8c40d5d92a76e54dd7ebf9f`。原r29/32基线保留。

r追加姿态权重.4/.35均29/32零安全，但env28退化，不采用，保留.5。最佳n/lr1e5/model99已备份本地r/selected-candidate/model_99.pt，SHA `b9ce9d3efa88a8846ab8efb7bf212fac3c69ace5a8c04022a583fb900e6ee4a3`。

s卸力5/10mm均29/32、零安全失败，env5/28停稳仍.40/.32s，未改善，不采用；卸力距离恢复0。

t底盘制动增益.5/1均29/32、零安全终止、回合完整，未改善，不采用；相关两份报告已归档本地。当前活动u：在匹配r29/32接触控制下，从n/lr1e5/model99进行完整样本与可控阶段样本对照训练；seed627、每组512环境、200轮、std.03、固定lr1e-5，GPU0/1。

u首批50轮评估：all/active均29/32、零安全终止、32回合完整。all的env5/28停稳.46/.42s，active为.48/.34s，均未达到.5s；env24推进不足。成功数暂未改善，100/199轮评估继续。

远程目录`/path/to/artifacts/go2-piper/push-contacttrain-20261001-u`；训练PID all=3905193、active=3905194，run为`2026-10-01_06-08-49_contactstate_{all,active}_seed627`。自动评估50/100/199轮，监控启动PID3905826/3905828，状态`outputs/auto-evaluation-{all,active}-status.json`。实际环境/算法/采样配置已核对并下载；原12s、5kg/摩擦.4、全部成功与安全门禁不变。r原副本未包含采样入口，本轮补齐三份既有采样/遥测源码，控制器保持r版，不混入s/t。不要重复启动。

n微调已完成：lr1e5第25/50/99轮均27/32，lr3e5为27/27/25，各1次无效接触，所有回合完整；训练PID3897186/3897505已退出。不延长n。完整六份报告和SHA已备份本地n。

o高度增权已完成且拒绝：权重2/3均0/32，分别3/0次安全终止；完整32回合。虽然接触略早，但随后手端下沉、推进中断。高度权重恢复1，默认不采用该诊断。

p已全部完成：接触期.2/.3s为28/27成功；追加.15s、姿态权重.5/.75为28/24，均零安全终止、全部回合完整。保留较温和的contact20配置，不采用追加方案。34项控制检查通过，p源码快照和四份报告已保存。

q录像已完成：两次均28/32、零安全终止、回合完整。视频已取回本地`../artifacts/go2-piper/push-review-20261001-q/review-env{0,24}.mp4`，1280×720/25fps/12s；检查8.8/10/11.5s画面，成功env0与推进不足env24可见。本地manifest有视频和报告SHA，index.html可本地浏览。

诊断纠正：env24并非真实合法接触丢失。约10s高度暂降到.060m导致几何approach_completed清零，但hand_contact持续为真、法向力约22N；参考从面内80mm改为面外30mm，随后底盘触发原最小间距停止。

已完成实验r：`/path/to/artifacts/go2-piper/push-contactstate-20261001-r`，固定j/model100与p/contact20其他配置，off/on对比默认关闭新选项`push_press_on_legal_contact`。保留原几何接近计算/阈值，当前真实合法手接触且无禁止接触、SAFE_APPROACH完成时可继续压入；安全/停稳门禁未变。GPU0/1，原12s/32回合/seed517，700s限时。日志/报告`outputs/contact-press-{off,on}-seed517.{log,json}`，检查env24时序。三份源码SHA核验通过，34项既有控制检查通过；A/B已完成：off/on均28/32、零安全失败、所有回合完整。on使env20误差.332→.114m且停稳.46s，env28误差.363→.167m，env24只略改善；env5仍.20s停稳。追加同一r控制开启选项，比较已有n/lr1e5/model99与n/lr3e5/model25（此前停稳较早），日志/报告`outputs/refine-{lr1e5-model99,lr3e5-model25}-seed517.{log,json}`，GPU0/1，已完成且均29/32、零安全终止；姿态权重对照已完成，见上方。r本身无PPO，当前u训练见顶部。

原独立验收种子701/1701仍未使用；冻结包未改，MuJoCo/CLIMB暂停。q视频为28/32候选，旧i为16/32；均不代表当前29/32权重。


以下为历史阶段记录：

共同权重为j/lr3e5/model100（226→12），SHA
`dd02f3026f3464a5fc2c5add56ba6b14c2a96a1235fa1a73ae5e33e827a13b4e`，
本地备份j/selected-model_100.pt。原12s/seed517/5kg/摩擦.4，保留701/1701未使用。

- j两组200轮已完成，最好19/32、2无效接触；最终8/18，不延长旧配置。
- k到位保持使同一候选19→21成功、无效接触2→0。
- l控制停止距离.105/.110m均22/32、零安全终止；成功判据仍误差<.12m、
  速度<.08m/s、保持.5s。8个失败的连续停稳仅.08–.48s，另2个推进不足。
  腿部渐进接管.4s→25/32、1初始无效接触，.3s→21/32、8初始无效接触。
  后者不采用，说明简单提前释放会扰动接触。结果和源码在本地l目录。
- m：`/path/to/artifacts/go2-piper/push-contactrelease-20261001-m`，
  新增默认关闭 `push_leg_release_on_contact`：保留完整SAFE_APPROACH，
  真正合法手接触出现后才释放腿部动作，按.3/.2s渐进；每环境重置清空锁存。
  其他固定l的stop.11/press80/限位内IK/到位保持，原任务和安全判据不变。
  32项控制检查通过，远程SHA已核对；日志/报告
  `outputs/contact-ramp{30,20}-seed517.{log,json}`，GPU0/1，已完成。
  .3/.2s仅11/13成功，均零安全失败；等待接触损失推进时间，不采用。
  本地manifest/source-snapshot在 `../artifacts/go2-piper/push-contactrelease-20261001-m/`。
- i的press80视频仍是16/32旧候选，env0推进.524m后超时，不代表当前25/32。

g采样对照与h姿态权重诊断均未改善，不采用。保留seed701/1701未使用。

- g：两组同 seed624、150 轮，原采样 model50/100/149 成功 9/6/8，
  活动采样 8/6/5；全部 32 回合完整、其余失败为超时或无效手接触。
  未观察到筛选 actor/critic/entropy 样本的收益，不延长训练。
  [完整结果](../../../artifacts/go2-piper/push-sampling-20261001-g/RESULTS_CN.md)。
- h：同一 e/press40 model50，姿态残差权重0.5为2/32（24无效接触），
  0.25为7/32（17无效接触），均不采用。默认权重仍1.0。
- i：`/path/to/artifacts/go2-piper/push-boundedik-20261001-i`，同一 e/model50，
  比较原 IK 与限位内投影下降32次，原12s/seed517/32回合、姿态权重1.0。
  新求解器默认关闭；保留原关节限位、参考限速、净空和全部接触/停稳门禁。
  29项控制检查通过、四文件远程SHA一致；日志/报告为 `outputs/{original,bounded}-seed517.{log,json}`。
  原分支复现e的9/32；限位内求解平均推进0.0891m，终态法向力多为4–16N。
  60/80mm追加诊断分别8/16成功，安全终止均零，已完成。
  100/120mm参考已完成，成功下降且重现无效接触；原物理/安全门禁不变；
  日志/报告 `outputs/bounded-press{100,120}-seed517.{log,json}`，GPU0/1。
  本地清单在 `../artifacts/go2-piper/push-boundedik-20261001-i/manifest.json`。

此前 e 两轮远程微调和全部检查点评估已完成，e 的 PPO 进程已核验退出。
普通 PUSH 尚未达标。此前 e 的原 12 s、名义 5 kg / 摩擦 0.4、调参 seed 517 最好
**9/32**，来自 40 mm 压入参考分支的 model50：7 超时、16 无效手接触，
其余安全终止均零，无未完成回合。仍未使用保留种子 701、1701。

- 20 mm 分支：`2026-10-01_01-44-49_nav_gain2_conservative_lr1e5`，seed 622，
  完成 600 迭代。model50/100/200/400/599 成功数 0/4/3/6/1；最终退化，
  最好 model400 为 6/32（23 超时、3 无效接触），不继续该配置加训。
- 40 mm 分支：`2026-10-01_02-08-47_nav_gain2_press40_lr1e5`，seed 623，
  完成 200 迭代。model50/100/199 成功数 9/7/7；未改善训练前 9/32，
  不继续该配置加训。

两轮源与状态位于 `/path/to/artifacts/go2-piper/push-feedback-20261001-e/`，
`outputs/auto-evaluation-status.json` 与 `auto-evaluation-press40-status.json`
均 finished。配置：NAV actor 初始化、std 0.05、固定 lr 1e-5、512 环境，
俯仰 0.6 rad、高度 +0.03 m、净空参考 0.10 m、接触保持 0.1 s、
腿部渐进接管 0.5 s、前进命令增益 2.0。body-first 与 P/PI 关闭。
当前主要瓶颈是底盘跟进和合法接触；压入参考 20/30/40 mm 的原 NAV 诊断
为 3/6/9 成功，无效接触 4/9/17。大量失败接触点漂到箱体上边缘。

选定录像候选为 40 mm model50，SHA
`16350cc853f001beb62964091aab1e4ceebb78309e5a3c699ace6b59cc3708ea`，
已备份至 `../artifacts/go2-piper/push-feedback-20261001-e/selected-candidate/model_50.pt`。
录像及报告已取回本地同一产物目录：`selected-video-evaluation.json`、
`selected-push-diagnostic-env0.mp4`；录像复核仍 9/32，env0 在 10.7 s 因
无效手接触终止，随后重置。视频 12 s、1280×720、25 fps，画面与 SHA 已核对。
[本轮简报](../../../artifacts/go2-piper/push-feedback-20261001-e/RESULTS_CN.md)；视频不是验收证据。

`push-reach-20261001-f` 的 0.54 m 前伸限制诊断为 0/32、30 超时、2 无效接触，
不采用。其代码在本地默认关闭，25 项控制检查通过；e 源码没有被覆盖，
本地 `source-snapshot/` 保留 e 的匹配版本。g 从 e 源码复制，未包含 f。
有效动作采样已实现并通过 5 项本地检查、远端真实 rsl_rl/TensorDict 检查；
g 的 A/B 结果未显示收益，保持默认关闭。完整安全接近和原 12 s 门禁保留。
冻结策略未改，源码同步授权仍有效，旧审批故障已解除，不要重复请求。
详见 [2026-10-01 实验记录](#source-training-status-20261001-cn)。

最新用户优先级：先推进普通 PUSH 的 Isaac 达标，暂停 MuJoCo 和 CLIMB 新实验。
修改后 PUSH 源码同步与远程优化训练已获明确授权，远程审批和执行已恢复。
`../artifacts/go2-piper/push-isaac-priority-20260930-a/` 是早期准备包，
当前结果以 10 月 1 日记录和匹配报告为准。

最新控制候选、远端同步阻塞和 CLIMB 自碰撞检查见
[2026-09-30 诊断记录](#source-training-status-20260930-cn)。以下成功率为已完成的历史评估。

<a id="record-0130"></a>

来源：AGENT_HANDOFF_CN.md。

## 项目定位

本仓库用于 GO2-PIPER 的 NAV、PUSH 与 CLIMB 底层技能训练、仿真验证和 Sim-to-Real 控制开发。

开始工作前先确认当前 Git 分支、工作树和实际产物哈希。不要将历史评估、训练日志或单条成功录像当作新的验收结果。

<a id="record-0131"></a>

来源：AGENT_HANDOFF_CN.md。

## 当前状态

| 技能 | 历史原生基线 | 最新候选 | MuJoCo 状态 | 实机状态 |
| --- | --- | --- | --- | --- |
| NAV | 已通过 | 本轮无新增验收 | 随机平地目标 `98/100` | 未验证 |
| PUSH | `31/32`、`30/32` | u/active/model100：调参`30/32`、零安全失败；独立验收待执行 | 未通过双组门禁 | 未验证 |
| PUSH-LOW | 训练止于 `58/3000`；`model_0` 接触诊断未成功 | 继续暂停 | 仅初始场景契约通过 | 未验证 |
| CLIMB | `30/32`、`32/32` | Smooth 低标准差 seed `511/512`：`32/32`、`30/32` | 候选 seed `500/600`：`14/32`、`14/32`，未通过 | 未验证 |

同日后续 CLIMB 探针：保留原 checkpoint std 约 `0.05`、lr 1e-5 的 `model_0`
在 Smooth-Play Isaac seed 511/512 达到 `32/32`、`30/32`，但 MuJoCo seed 500/600
均只有 `14/32`；冻结 actor 同配置 seed 500 为 `16/32`。此候选只在
`../artifacts/go2-piper/climb-stability-20260929-a/model0-smooth-diagnostic/`
诊断导出，未替换冻结策略。最新结论以
[训练记录](#source-training-status-20260929-cn)和[下一步计划](#source-next-steps-cn)为准。
首轮 std 0.25 Smooth 候选在 seed 511 为 `0/32`，不能与本次探针混用。

PUSH 和 CLIMB 只有在原生与 MuJoCo 各两组独立 `32` 回合评估均达到至少 `30/32` 后，才能进入分级实机验证。当前策略均不得直接用于实机接触任务。

<a id="record-0132"></a>

来源：AGENT_HANDOFF_CN.md。

## 2026-09-29 训练与交接状态

普通 PUSH、CLIMB 已获授权继续优化训练。首轮探针的隔离目录为
`/path/to/artifacts/go2-piper/smooth-tracking-20260929-a/`；两项各完成 10 轮探针，
均保存 `model_9.pt`，各评估 32 回合且无未完成回合，成功数均为零：

- PUSH Tracking：取消接触锁臂并增加末端跟踪、手部接触奖励；29 回合触发
	`arm_body_clearance`，另有 `base_contact=3`、`box_contact=3`，终止标志非互斥。
	`0.597655 m` 是机器人底座最大前移，箱体最大终态前移约 `0.400 m`；
	没有安全完成，不能据位移替换基线。同任务冻结模型也是 `0/32`，
	详见[最新训练记录](#source-training-status-20260929-cn)。
- CLIMB Smooth：增加动作变化、关节加速度/力矩、底盘角速度和倾斜惩罚；
	`base_contact=31`、`bad_orientation=1`。关节速度峰值约 `30.10 rad/s`、
	倾角峰值约 `0.862 rad`、力矩限幅比例 `1.0`，尚未解决起步失稳与电机风险。

两份报告 `video_path=null`，没有本批新录像或 MuJoCo 验收。用户此前查看的
9 月 26 日诊断录像与 9 月 15 日原技能录像都不能代表本批候选。原 checkpoint
在 `/path/to/artifacts/go2-piper/generalize-20260929-a/original/` 的备份哈希与
本地冻结训练交接包一致；冻结 actor、checkpoint 和交接包清单保持原样。
本次核查没有活动训练/评估进程，不代表普通 PUSH、CLIMB 优化授权撤销。

下一轮先诊断 PUSH 接近耗时、在线跟踪净空与全身支撑，以及 CLIMB 重置/准备姿态、
动作接管和底座接触，随后再扩大训练。逐关节补齐速度、加速度、目标变化、饱和时长
和功率统计；电流、温升和电机额定参数尚未实测，奖励惩罚不是硬件保护。
完整 checkpoint/报告/源码哈希见 [训练与评估记录](#source-training-status-20260929-cn)，
执行顺序以 [下一步计划](#source-next-steps-cn) 为准。

以下日期条目为历史诊断，保留当时命令、失败与纠正过程；其中的“下一步”、训练暂停
和未完成状态以本节及最新计划为准。PUSH-LOW 训练与实机接触仍暂停。

<a id="record-0133"></a>

来源：AGENT_HANDOFF_CN.md。

## 2026-09-25 PUSH-LOW 状态

运行状态复核：`outputs/train.log` 最后记录为 `Learning iteration 58/3000`，服务器上
已无该 PIPER 训练进程；只保存了 `model_0.pt`，长训未完成。日志末尾没有记录停止原因，
不推断为正常完成或某种异常。新增 PRECONTACT 姿态尚未通过跨初态真实 PD 动态净空
验收，不能沿用 SAFE_APPROACH 的 `20.06 mm` 最小净空结论。

ARX5 的 `GO2-ARX5-Box-Push-Low` 不是沟壑场景，而是在平地上直推一块已经与机器人
对齐的轻板；`gap_bridge` 是使用同尺寸轻板的后续组合原型。PIPER 已注册
`GO2-PIPER-Box-Push-Low[-Play]`，低板尺寸 `1.10 x 0.48 x 0.08 m`、名义质量
`2.5 kg`、摩擦 `0.7`、初始中心 `(0.94, 0, 0.04) m`、目标推动距离 `0.90 m`；训练
随机化为质量 `2.0..3.5 kg`、静/动摩擦 `0.5..0.9`。

PIPER 保留已验收的 16 段 SAFE_APPROACH，不复制 ARX5 专用机械臂 waypoint。安全路径
完成后，身体需连续静稳 `0.5 s`，再进入 PIPER PRECONTACT 姿态和在线接触 IK。当前
PUSH-LOW 诊断配置使用位置 IK、接触后不锁臂；预接近腿动作缩放 `0.15`、臂速率缩放
`0.25`、PRECONTACT 姿态段速率缩放 `1.0`。这不是已验收的 PUSH 姿态 IK 控制契约。
预接近 4 s 超时从 SAFE_APPROACH 完成后计时，单回合为 `24 s`。

**配置阻塞：** 子类声明 `push_approach_distance = 0.08`，但父类 `__post_init__` 将其
覆盖为 `0.03`；名称带 `80mm` 的已有报告中 `actual_physics.push_approach_distance`
实际为 `0.03 m`，不能据文件名宣称已验证 80 mm。下一步需修正初始化覆盖并重新导出
运行时配置，再在新文件中评估；不得覆盖这些诊断报告。

验证边界：本地 MuJoCo 初始场景只存在低板与地面的 4 个零穿透接触，机器人无初始穿模；
预览为 `../artifacts/go2-piper/push-low-arx5-contract-preview-20260924.png`。远端 Isaac
已通过任务注册、`16 env x 1 iteration` PPO smoke 和 NAV actor 初始化 smoke。零动作启动
检查在 4 s 与 10 s 均为 `16/16` 无终止；10 s 时 SAFE_APPROACH 为 `16/16` 完成，
body-ready 为 `9/16`。报告与源码哈希归档在
`../artifacts/go2-piper/push-low-2026-09-24/`。这些结果不证明推板成功、训练收敛、
MuJoCo 闭环通过或实机安全。

训练在服务器隔离目录
`/path/to/artifacts/go2-piper/2026-09-24-push-low-piper-z2O4vb` 启动，原 tmux 会话名为
`piper-push-low-20260924`，请求 GPU 0、1024 环境、3000 iteration，从 SHA-256
`72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8` 的 PIPER NAV actor
初始化腿部输出，初始探索标准差 `0.25`。本次核查该 run 仅找到 `model_0.pt`，不能把
启动参数当作 3000 迭代完成证据，也不能继续沿用“长训进行中”的历史状态。

诊断 checkpoint 为
`logs/rsl_rl/go2_piper_box_push_low/2026-09-24_17-40-48_piper_push_low_nav_init_v1_20260924/model_0.pt`，
SHA-256 为 `fa0a6e3b1b0d9b9a94e48dadd2b211c1451520b9cf7c01a11f3ae112c27b8375`。
以下均为同一 checkpoint、seed `100`、1 环境、1 回合，不同控制版本的诊断，全部未成功：

| 报告前缀 | 时长 | 终止项 | 推动方向位移 | 目标误差 | 终态有效手接触 |
| --- | --- | --- | --- | --- | --- |
| `model0_eval_seed100` | 11.32 s | `arm_body_clearance` | 0.00004 m | 0.89996 m | 否 |
| `model0_position_ik_eval_seed100` | 11.28 s | `invalid_hand_contact` | -0.00012 m | 0.90012 m | 否 |
| `model0_precontact_80mm_fast_eval_seed100` | 24.00 s | `time_out` | 0.04508 m | 0.85606 m | 是 |
| `model0_precontact_80mm_unlocked_eval_seed100` | 10.20 s | `invalid_hand_contact` | 0.05247 m | 0.84894 m | 否 |

前两项已有原生录像，位于本地 `../artifacts/go2-piper/push-low-2026-09-24/`，文件为
`model0_eval_seed100.mp4` 和 `model0_position_ik_eval_seed100.mp4`，对应同名 JSON。
它们用于检查失败过程，不代表当前 PRECONTACT/不锁臂配置的录像。最后一项远端报告位于
上述隔离目录的 `outputs/`，该次 `video_path` 为 `null`，本次另行补录见下文；报告 SHA-256 为
`a70baeaa71d48b9736e94736f39dda30aac71512a07c1528aa746af4378db89a`。

PUSH-LOW 使用接触高度边界 margin `0.0 m`、末端邻域半径 `0.12 m`，与历史 PUSH 的
`0.01 m` / `0.07 m` 不同。这些诊断判据尚未完成 PIPER 几何与动态接触验收，不能按
历史 PUSH 的成功标准放行。继续工作前应冻结并记录任务配置、控制器、评估脚本及资产
哈希；当前没有 PUSH-LOW 独立 32 回合验收、MuJoCo 闭环验收或实机放行。

### 本轮录像与验证

2026-09-25 已补录当前控制源码的单回合 Isaac 视频，仍使用上述 `model_0`、seed `100`、
1 环境、1400 步预算，实际在第 510 步结束。报告确认有效接近距离为 `0.03 m`、接触后
不锁臂；结果为 `0/1` 成功、无未完成回合，`10.20 s` 因 `invalid_hand_contact` 终止，
前推 `0.05247 m`、目标误差 `0.84894 m`，与上一份无录像诊断一致。

- [本次运行视频](../../../artifacts/go2-piper/push-low-2026-09-24/model0_effective30mm_unlocked_video_seed100_20260925.mp4)
- [对应评估报告](../../../artifacts/go2-piper/push-low-2026-09-24/model0_effective30mm_unlocked_video_seed100_20260925.json)
- [四帧预览](../../../artifacts/go2-piper/push-low-2026-09-24/model0_effective30mm_unlocked_video_seed100_20260925-frames.png)

视频为 `1280 x 720`、`25 fps`、`10.20 s`，255 帧均可解码；首帧为渲染初始化黑帧，
后续预览可见机器人、低板和接近接触过程。视频及完整 JSON 保存在上述本地产物目录，
服务器副本位于隔离工作目录的 `outputs/`；产物不提交 Git，仓库只提交源码与文档索引。

来源校验：录像报告内的 5 个控制模块、评估脚本和 6 个机器人资产文件 SHA-256 均与本地
一致，任务配置也已与服务器逐文件比对。关键哈希如下：

- 录像：`40ee428986c5be0acca864a6aeaa72c1d0fb50b2f763237a12f7b7abb88057b0`
- 评估 JSON：`9ebd42d7c412f9770c9be9adec7190ed04cea09381d5fce147a7b9e82da67c4b`
- `go2_piper/box_env_cfg.py`：`2c9920104d52e306a1c655baf6972d67ec423ba95a24f3fe9b52c841222d3725`

提交前验证：本轮修改的 Python 均通过语法检查；`check_box_push_control.py` 的 12 项和
`check_box_evaluation.py` 的 3 项测试通过；共享 `check_box_push_contract.py` 在服务器
Isaac 环境输出 `PUSH_FRAME_CONTRACT_PASSED`。MuJoCo 初始场景契约通过，只出现低板与
地面的 4 个零穿透接触。这些检查验证接口、统计与初始场景，不构成 PUSH-LOW 技能验收。

<a id="record-0134"></a>

来源：AGENT_HANDOFF_CN.md。

## 2026-09-22 PUSH 安全状态

2026-09-23 补充：SAFE_BASE 独立训练任务的最终 `model_99.pt` 已完成固定 12 s 的 Isaac
多 seed 评估：seed `100..103`，每组 32 环境，共 `128/128` 到时且所有其他终止项为零。
checkpoint SHA-256 `85a3981d595170d3b224a9fdc45890217e9fbdf7aa3561f81702c58d42b02980`；
逐环境 JSON 在 `../artifacts/go2-piper/safe-base-2026-09-23/`，评估入口为
`scripts/evaluate_safe_base.py`。最低底座高度 `0.3139 m`，最大倾角 `0.2210 rad`；
最大瞬时线/角速度分别为 `0.9726 m/s` / `2.8565 rad/s`，最小臂身刚体中心距离
`0.1007 m`（不是表面净空）。这不是推箱成功率，尚无静稳速度门槛、SAFE_APPROACH
切换或 MuJoCo 验收；SAFE_BASE 不得直接接入实机或未验证的 PRECONTACT。
更新后的分时段评估仅在 seed `100` 重跑：前 `2 s` 峰值线/角速度为
`0.973 m/s` / `2.857 rad/s`，`2–10 s` 降至 `0.048 m/s` / `0.100 rad/s`，
末 `2 s` 为 `0.031 m/s` / `0.093 rad/s`。这仅说明零速初态下冲击集中在启动阶段，
尚不能外推到安全接近结束后的非零速度初态；其脚本哈希不同于上述四组 JSON。

PUSH 的安全控制候选正在开发，冻结 actor 仍未通过新安全契约。`native_collisions` 候选
必须保留 arm-link 对 base/leg 的碰撞，仅排除固定安装座和相邻 arm link。MuJoCo 会报告
`arm_self_collision`、最小净空和主动撤退状态；Isaac 已注册 `arm_body_clearance` 几何
净空终止。任何正式 checkpoint 仍须通过 collision profile 的真实 PD 动态路径验收。

SAFE_APPROACH 的版本化 16 段路径已在 seed `500..531` 通过 `32/32` MuJoCo runtime
gate，最低动态净空 `20.06 mm`。它在完成前保持腿部策略和直达接触 IK 禁用；PRECONTACT、
有效推箱和安全重训尚未完成，不能据此更新冻结 actor 的验收状态。

runtime 在 SAFE_APPROACH 完成后默认 hold 最后安全姿态，避免落回未验证的直达 IK。固定
PRECONTACT joint path 不能跨初态复用：虽然动态净空合格，但末端相对箱体前推面可出现约
`140 mm` 误差。后续 PRECONTACT 必须基于当前 box/base 状态在线求解，并配合专门训练的
腿部稳定控制。

<a id="record-0135"></a>

来源：AGENT_HANDOFF_CN.md。

## 2026-09-26 普通 PUSH 动态接触诊断

PUSH-LOW 训练继续暂停；本节只记录冻结 `model_599.pt` 的普通 `GO2-PIPER-Box-Push-Hybrid-Play`
诊断。箱体保持 `1.2 x 1.2 x 0.20 m`、`5 kg`、摩擦 `0.4` 与 `0.60 m` 目标不变。使用
选择性原生碰撞 USD、五段 Cartesian PRECONTACT、`pitch=1.0 rad`、`base_start_x=-0.14 m`
和 `push_height_offset=0.03 m`；所有 `invalid_hand_contact`、`arm_body_clearance`、
`arm_contact` 与 `hand_other_contact` 终止均保持启用。

- 静腿接触基线 `push-static-upperface-seed210-20260926.json`：40 s 超时，无安全终止；
	最长连续合法接触 `19.3403 s`、最大手部力 `2.2112 N`，箱体 x 位移仅
	`3.39e-5 m`。这只证明安全贴合，不是 PUSH 成功。
- 去除 `--neutral-legs` 的动态回合
	[JSON](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-dynamic-upperface-seed210-20260926.json)
	/ [视频](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-dynamic-upperface-seed210-20260926.mp4)：
	40 s 超时，无安全终止；策略腿动作最大绝对值 `4.6133`，合成腿命令最大绝对值
	`0.5224`，因此腿部接口并未失效。但最长连续合法接触仅 `0.18 s`，箱体 x 位移仍为
	`3.39e-5 m`。
- `--contact-action-ramp-time 2.0` 将接触期腿部渐变放缓，最长连续合法接触提升到
	`1.94 s`，底座一度前移约 `0.12 m`，但 27.02 s 因 `invalid_hand_contact` 终止；最大
	力 `16.3187 N`，箱体 x 位移 `4.95e-5 m`。
- 高度参考修复后的同参回合最长接触 `1.96 s`，27.04 s 因 `invalid_hand_contact` 终止，
	箱体 x 位移 `4.05e-5 m`，没有恢复推进。
- 接触后锁臂的同参回合
	[JSON](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-dynamic-upperface-ramp2-locked-seed210-20260926.json)
	/ [视频](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-dynamic-upperface-ramp2-locked-seed210-20260926.mp4)
	在 29.0 s 因 `invalid_hand_contact` 终止；最长接触 `1.92 s`、最大力 `16.9640 N`、
	箱体 x 位移 `4.37e-4 m`。其
	[关键帧](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-dynamic-upperface-ramp2-locked-seed210-20260926-frames.png)
	可见底座前移而箱体没有可见推进。

物理下限也排除了把 `8 N` 接触力伺服当作推箱方案：该箱体的静摩擦下限为
$5 x 9.81 x 0.4 = 19.62 N$。但不能直接提高目标力或放宽合法接触判据，因为当前锁臂回合
在 `16.9640 N` 时已因无效手接触安全停止。

本轮控制修复与遥测：`side_approach_ready()` 现在以配置的接触高度而非箱体中心高度判断
接近状态，避免上沿接触时将 `box_push_approached` 错误重置；混合 PUSH trace 记录原始腿动作、
合成腿命令、接触持续时间和实际 `PushArmIK.target_position`，不再通过遥测调用改变状态的
通用目标函数。`--contact-action-ramp-time` 仅为诊断参数，默认仍为 `0.50 s`。

当前来源哈希：`evaluate_box_skills.py`
`255d5e94a766546c8aeb6db8cd61ccdec3f8c645286fb585cc52afd95446dde8`；
`create_piper_collision_variant.py`
`5494b133b29bbaf5803ea4f3d3e860774d59d357202bffc72dfe268793c063e5`；
`box_push.py` `e890ae8b087b7141e9806585a6243364c598d99ddc8e54086bd61e317c8a3748`；
`box_push_control.py` `1994a0057bae104be600665798d6295475585e3096c58ca4c68851e16c256ad0`；
`box_push_ik.py` `93b78406da94d5dedc25859beb44c7e21a71f669ff18356f51a757d00ee63a59`；
选择性碰撞 USD `d8421ef50d69b7d43dd7a7d07675fa3b4c651ffcaf9d3d00d74c85544bbdf21f`。
本地 `check_box_push_control.py` 为 18/18、`check_piper_collision_variant.py` 为 7/7，
且受影响 Python 均通过编译；这些是控制与资产回归，不构成技能验收。

下一步先在真实 PD/碰撞约束下求解从 `base x=-0.14 m` 到前推所需底盘位置的在线
机械臂姿态/可达性轨迹，并以实际 IK 目标、关节限位、力矩和最小净空验证。只有该轨迹能在
合法手接触下跨越静摩擦所需力而不触发安全项，才可重新开始独立动态回合；随后再建立
Isaac/MuJoCo 对同一逐物理步状态、目标、力矩和接触的对照。禁止恢复 PUSH-LOW 训练、
修改箱体参数、放松安全终止或进入实机接触。

2026-09-26 后续几何诊断新增
`mujoco/scan_piper_push_reachability.py`。它在 `seed=210` 的实际失败底座轨迹
`(-0.141522, 0.042374, 0.270552)`、`(-0.103301, 0.098154, 0.282458)`、
`(-0.074062, 0.120670, 0.281920)`、`(-0.022384, 0.111226, 0.283702)` 上搜索
`pitch=0.8/1.0/1.2 rad` 的机械臂支路。12 个候选中 10 个满足 `25 mm` 末端误差、
`0.15 rad` 姿态误差、软限位和 `15 mm` 净空；通过枚举相邻候选并进行 25 点同步
底座/关节插值，找到连续分支，最低静态净空 `59.87 mm`。因此失败不是该真实状态轨迹下的
静态几何无解，而是现有一步 DLS 没有收敛到该支路。

该连续分支的“运动学预设基座 + 真实 MuJoCo 臂 PD、延迟、力矩限幅和每子步碰撞”验证
仍失败，但没有自碰撞：最低动态净空 `62.60 mm`，初始保持 `2 s` 后已存在
`105 mm` 末端误差和 `0.105 rad` 关节误差，过渡期间稳定到约 `0.16 rad` 的 joint2
偏差。无接触的第 `0.2 s` 已出现该偏移，不能归因于箱体力。单点补偿比例探测表明零补偿和
全量补偿分别不足/过补偿，`0.66` 仅在单一采样时达到 `0.039 rad` 关节误差但仍有
`42.9 mm` 末端误差；不得据此修改运行时补偿比例。该验证只验证机械臂动态阻塞，不能代替
腿部闭环、Isaac 回合或验收。

MuJoCo `BoxPushArmController.hand_target()` 已对齐 Isaac：接近状态与保持窗口现在相对于
`hand_height_offset` 判断，不再将上沿接触误判为未接近。`check_piper_box_collision.py`
新增该回归并通过 7/7。扫描器哈希为
`b8d0fc89863bb6864edcfd060396bbaa2a8202e3881bbed408e3074bf16336cf`，MuJoCo
`box_push_runtime.py` 哈希为
`8db4f3d5626459c6629a0aaff6c83aac5b83b83feb05d20fe7535170693b281d`；报告为
[连续静态路径](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-reachability-observed-continuous-seed210-20260926.json)
和 [预设基座 PD 失败](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-reachability-observed-pd-settled-seed210-20260926.json)。

为隔离该 PD 阻塞，新增 `mujoco/trace_piper_push_hold.py` 和 PUSH 任务支持的
`scripts/replay_piper_control_trace.py`。固定首个连续姿态节点、初始腿目标、零目标延迟历史，
并在每个物理步运动学回写根位姿后，MuJoCo/Isaac 对相同 40 步目标、初态和延迟的比较仍出现：
根误差始终低于 `1.1e-8 m`，但速度在第 0 步分叉 `2.688 rad/s`，力矩在第 1 步分叉
`1.267 N m`，关节位置在第 5 步分叉 `0.0531 rad`。到 `0.2 s`，joint2 的目标为
`2.62248 rad`，MuJoCo/Isaac 位置分别为 `2.69249/2.61926 rad`，力矩分别为
`0.0415/4.4817 N m`；joint3 也分别为 `-2.17740/-2.20526 rad` 与
`2.0875/4.5052 N m`。这不是根部反作用、腿部目标或延迟预填充造成的分叉。

两端声明的臂 `kp=[50,50,80,30,30,20]` 和
`kd=[3,2,3,3,2.5,1]` 已逐项核对一致。当前证据只允许下一步在固定状态/固定目标 trace
中受控标定 MuJoCo 显式 PD 与 Isaac `DelayedPDActuator` 显式执行器的积分、阻尼和 armature；不得基于单点
`0.66` 重力补偿试探修改运行时，也不得把该 trace 当作 PUSH 验收。根部固定报告为
[MuJoCo trace](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-holdlegs-rootfixed-mujoco-seed210-20260926.json)、
[Isaac replay](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-holdlegs-rootfixed-isaac-seed210-20260926.json)
和 [比较报告](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-holdlegs-rootfixed-compare-seed210-20260926.json)。
trace 工具哈希为 `4a6a9769019b43e606c244748b2990b54ec83b895697e636cbefafcffef569d4`，
Isaac 重放器哈希为 `e68c023fed5174a2bf20b745cf015a5e83e6e18d6117a7db66634d75df2fb156`；
既有 `check_piper_trace.py` 回归为 6/6。

### 2026-09-26 节点 2 执行器标定诊断

为避免把节点 0 的 trace 错配到连续姿态路径的节点 2，使用同一节点的 40 个物理步、同一
初态、目标序列、根部处方和延迟重新生成 Isaac replay。MuJoCo 输入为
[节点 2 trace](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-rootfixed-mujoco-seed210-20260926.json)，
Isaac 输入为
[节点 2 replay](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-rootfixed-isaac-seed210-20260926.json)。
两者均为 `kinematic_prescribed_each_physics_step`，`physics_dt=0.005`，Isaac 报告中的
`trace_sha256` 与 MuJoCo 输入匹配；重放器源码哈希为
`331ec829805c2410af813e80c36366ccc1b9f52dd527b0838063857db3cb23a9`。

新增 `mujoco/calibrate_piper_push_actuator.py` 仅用于拟合诊断，不写回运行时配置。节点 2
的小规模搜索结果如下：

- passive armature/damping：目标函数 `6.3004 -> 6.0107`，joint2 最终位置误差约
	`0.0696 rad`；仅调被动参数不足以消除首发分叉。
- PD 比例：目标函数 `6.3004 -> 2.8037`，joint2 最终位置误差约 `0.0071 rad`，但
	joint3 仍约 `0.0613 rad`。该搜索仅 3 轮、只覆盖 joint2/joint3，不能作为运行时参数或
	PUSH 验收依据。

标定报告为 [passive](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-passive-calibration-seed210-20260926.json)
和 [PD](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-pd-calibration-seed210-20260926.json)。
随后对连续路径节点 `0/1/3` 生成同样的 40 步 MuJoCo/Isaac trace，并各做 2 轮 PD 比例
搜索。四节点的目标函数（基线 -> 搜索结果）为 `0: 4.6497 -> 2.3452`、
`1: 5.3094 -> 2.6287`、`2: 6.3004 -> 2.8037`、`3: 5.7098 -> 3.7992`；节点 0
的 joint2 最终误差仍为 `0.0935 rad`，节点 1/2/3 的 joint3 最终误差仍分别为
`0.0632/0.0613/0.0630 rad`。最优 PD 比例随节点变化，不能据此选择一个全局运行时参数，
也说明增益拟合不足以解释全部分叉。

随后以 `max_iterations=40`、`population=8` 对四个节点各运行完整 passive/PD 搜索。PD
目标函数（基线 -> 完整搜索）为：节点 0 `4.6497 -> 1.6663`，节点 1
`5.3094 -> 1.3479`，节点 2 `6.3004 -> 1.8742`，节点 3 `5.7098 -> 1.3209`；
但最优比例仍随节点变化，节点 2/3 的 joint3 最终误差分别为 `0.0835/0.0808 rad`。
passive 搜索仅达到 `4.4841/3.6945/5.3145/5.4126`，不能解释主要分叉。完整报告为
`push-actuator-node{0,1,2,3}-{passive,pd}-calibration-full-seed210-20260927.json`，
均位于本地诊断产物目录；这些报告仍不构成运行时参数选择或 PUSH 验收依据。

新增 `--delay-buffer-initialization {zero,current}` 时序探针，对节点 2 重新生成 MuJoCo
trace 并进行 Isaac replay。两种初始化的首步 MuJoCo/Isaac 力矩均一致，基线位置 RMSE
均为 `0.029836 rad`、速度 RMSE 均为 `0.364153 rad/s`、力矩 RMSE 均为 `2.410745 N m`，
最终 joint2/joint3 误差也完全一致。因此已排除延迟历史初始化为主要原因；下一步应转向
PhysX 隐式积分、关节摩擦实现和 MuJoCo 显式 PD 更新时序的逐物理步对照。

新增节点 trace 与 PD 报告均为诊断产物，不属于 PUSH 验收。下一步需逐关节核对积分、延迟、
阻尼、armature 与执行器更新时序，优先解释跨节点稳定存在的 joint3 误差；在首发物理步
分叉未被来源匹配地消除前，不得修改 Isaac/MuJoCo 运行时参数、写入 PushArmIK 或恢复训练。

四节点 4 子步 PD 搜索（`max_iterations=20`、`population=8`）的基线目标函数为
`4.2798/5.2677/5.4487/5.6509`，优化后为 `2.2459/1.6540/1.9572/1.4932`；
节点 0/1/2/3 的 joint3 最终误差分别为 `0.0518/0.0706/0.0878/0.0762 rad`。
积分细化改善了速度和力矩误差，但没有消除位置分叉；报告为
`push-actuator-node{0,1,2,3}-pd-substeps4-full-seed210-20260927.json`，仍仅作诊断。

标定工具另新增 `--constraint-substeps {1,2,4}`，默认值仍为 `1`。节点 2 的低成本 PD
对照中，2 子步将基线目标函数从 `6.3004` 降至 `5.5840`，4 子步降至 `5.4487`；
速度与力矩误差同步下降，但 joint2 最终位置误差仍约 `0.0713 rad`。这说明 MuJoCo
积分粒度确实影响分叉，却不是唯一根因。四节点 4 子步完整搜索正在生成独立报告，不覆盖
1 子步结果。

### 2026-09-27 箱体初态对齐诊断

此前 actuator trace 只恢复了机器人 root/joint 状态，没有恢复 PUSH 箱体的 root state。
MuJoCo `make_episode()` 会按 seed 随机化箱体横向位置和 yaw，而 Isaac Play 配置固定箱体
初态；这会在相同 link6 COM 轨迹下制造不同的接触时序。`trace_piper_push_hold.py` 现在
记录 `box_initial_state.root_pose/root_velocity`，`replay_piper_control_trace.py` 在 trace
包含该字段时恢复 Isaac 箱体状态，旧 trace 仍保持兼容。

节点 2 新 MuJoCo trace 为
[box-aligned trace](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-boxaligned-rootfixed-mujoco-seed210-20260927.json)，
其箱体初态为 `y=-0.019823 m`、yaw 约 `0.0271 rad`。恢复该状态后，MuJoCo 的 link6/箱体
首次接触仍在物理步 `1`，峰值手箱接触力约 `22.65 N`。远端 Isaac replay 在 Kit/GPU
初始化后未写出 JSON，当前没有来源匹配的 Isaac 接触步结果，不能据此宣称双仿真时序已修复。
需要在远端 CUDA/Kit 状态稳定后重新运行该 trace，再比较首次接触步、手箱力和关节分叉。

后续通过显式选择 GPU1、取消 `CUDA_VISIBLE_DEVICES` 重跑成功。Isaac replay 需要在
`gym.make()` 前设置 `config.scene.box.init_state` 并禁用 `events.reset_box`，否则 reset
会覆盖 trace 箱体状态；运行时直接调用 `box.write_root_state_to_sim` 会在远端 Kit 中提前
退出。最终报告为
[matched Isaac replay](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-boxaligned-final-gpu1-isaac-seed210-20260927.json)。
其 measured box pose 与 MuJoCo trace 在微米/微弧度量级一致，Isaac 与 MuJoCo 首次手箱
接触均为物理步 `1`，Isaac 峰值 hand force 为 `30.26 N`。

使用该来源匹配 replay 的 node2 PD 标定报告为
[matched calibration](../../../artifacts/go2-piper/contact-repair-20260925/native-safety/push-actuator-node2-boxaligned-pd-full-matched-seed210-20260927.json)：
baseline objective `1.7440`、position RMSE `0.01537 rad`、velocity RMSE
`0.22893 rad/s`、torque RMSE `1.26375 N m`；小规模 PD 搜索降至 `0.5240`，但仍有
约 `0.02955 rad` 最大位置误差。接触时序问题已被隔离，剩余问题属于 PhysX/MuJoCo
执行器积分/动力学响应差异，不能据此修改运行时 PD 或恢复训练。

逐物理步数据补充显示：Isaac 第 `1` 步 hand force 为 `19.56 N`，峰值约 `30.26 N`，
MuJoCo 同状态峰值约 `22.65 N`；Isaac 手箱接触在第 `24` 步后消失，但 joint2/joint3
位置误差继续增长，最终约 `0.0436/0.0219 rad`。root solver 位置误差早期约
`3.7e-4 m`、第10步后约 `5e-5 m`，不足以单独解释后段关节误差。下一步应固定相同
接触力/接触点序列或做无箱体 actuator replay，继续隔离接触响应与显式 PD 动力学；不把
拟合增益写回运行时。

新增 no-box 诊断：将 node2 trace 箱体移至 `x=3.0 m`，机器人、目标、延迟和根轨迹保持
不变，Isaac replay 正常完成 40 步。来源匹配 PD 标定的 no-box baseline objective 为
`2.1145`、position RMSE `0.01969 rad`、velocity RMSE `0.18810 rad/s`、torque RMSE
`1.38707 N m`；接触版 baseline 为 `1.7440/0.01537/0.22893/1.26375`。无箱体时仍存在
同量级位置分叉，因此接触响应不是唯一根因；下一步继续隔离无接触 PhysX/MuJoCo
执行器积分和隐式/显式 PD 响应。

no-box 零重力 A/B 也已完成：baseline objective `2.3357`、position RMSE `0.02080 rad`、
velocity RMSE `0.19232 rad/s`、torque RMSE `1.45795 N m`，相较有重力 no-box 的
`2.1145/0.01969/0.18810/1.38707` 没有改善。因此重力项不是主要根因，后续应优先
对照 PhysX 隐式执行器与 MuJoCo 显式 PD 的离散更新时间、延迟取样和状态反馈。

逐步检查还确认 Isaac replay 的 `torque_before_step` 与 step 后 `torque` 在每个采样步
完全相同，因此剩余 torque 差异不是报告采样错位，而是物理步内状态演化差异。当前 Isaac
articulation 为 `Is fixed root: False`；replay 只在物理步前后处方 root，步内仍会受到四足
接触和机械臂反作用影响。下一步应建立真正的 PhysX root-fixed 或腿部反作用隔离 replay，
再与 no-box trace 对照；不得继续用单点 PD 拟合替代该隔离。

新增 `mujoco/scan_piper_contact_solver.py` 对固定箱体 `y=0/yaw=0` 扫描 robot geom
margin `0/0.0005/0.001/0.002 m` 与 solref time constant `0.005/0.01/0.02/0.04 s`，
四节点各 `16` cases。首次接触步范围为节点 `0=6..8`、`1=3..5`、`2=0..1`、`3=0..1`；
因此 MuJoCo 接触 solver 参数只能覆盖节点0/1的少量差异，不能解释节点2/3相对 Isaac 的
第6步延迟。不要把 margin/solref 扫描最优值写回碰撞资产。Replay 现另记录
`box_contact_hand_time` 和 `box_contact_hand_position`，待 CUDA/Kit 恢复后用于区分
几何接触与力传感器更新时间。

新增 `mujoco/scan_piper_push_contact_timing.py` 对四个连续路径节点各扫描 `7` 个横向位置
和 `5` 个 yaw，共 `35` 个箱体姿态。固定箱体 `y=0/yaw=0` 时 MuJoCo 首次接触步为
节点 `0/1/2/3 = 8/5/1/1`；扫描范围分别为 `6..8/2..6/0..4/0..4`。旧 Isaac
trace 中 link6 首次非零总力为 `9/7/6/6`，所以箱体随机初态会影响接触边界，但无法解释
全部延迟。MuJoCo link6/箱体碰撞 geom 为 `margin=0`、`condim=3`；Isaac link6/7/8
collider 报告中 contact/rest offset 均未显式设置，下一阶段需在来源匹配的 Isaac replay
恢复后核对 PhysX 默认 offset 与接触传感器时序。

### 2026-09-28 固定根部来源纠正

2026-09-27 的 fixed-base MuJoCo trace 删除 free joint 后仍以 `data.qpos[:7]` 和
`data.qvel[:6]` 记录根状态；它们已变成关节坐标/速度，不是根姿态/速度。Isaac
据此初始化固定根，因此此前的“正常重力首步分叉”和资产重力不一致推断无效。
现已按真实 node2 根姿态 `[-0.074062, 0.12067, 0.28192, 1, 0, 0, 0]`
重新生成同源 trace，并增加零力矩诊断与固定根状态回归。

- 正常重力、固定根、无地面、箱体位于 x=3 m 时，joint2/3 初态重力矩：MuJoCo
	`[-15.778774, -5.770777] N m`，Isaac `[-15.778770, -5.770771] N m`。
	32 步零力矩首步速度分别为 `[0.128050, -0.101016]` 与
	`[0.128336, -0.101583] rad/s`，两端施加力矩均为零。joint2 后续到达
	`3.14 rad` 上限，MuJoCo/PhysX 限位响应不同，不能以末步差异推断重力差异。
- 40 步正常重力 PD replay 输入哈希匹配，初态关节误差小于 `9e-8 rad`；
	全关节最大位置误差约 `0.000631 rad`，最大力矩误差约 `0.0221 N m`。
	诊断产物为 `../artifacts/go2-piper/contact-repair-20260925/native-safety/`
	下的 `push-actuator-node2-fixedroot-nofloor-{zeroeffort-v2,gravity-rootcorrected}-*20260928.json`。
- 早期 Isaac root link 实测初态与源根姿态曾差约 `11.35 mm`、偏航 `0.0269 rad`，
	严格比较器正确拒绝该报告。后续 fixed-root replay 禁用 `reset_base` 后，初态
	与源根姿态一致到浮点精度，并增加初态一致性检查；该偏差由重置随机化造成，
	不能继续作为 USD 锚点错误的依据。足地响应和任务级风险仍未解决，后续接触力
	采样、运动学分解与完整 PUSH 时序见 [下一步计划中的诊断记录](#source-next-steps-cn)。

### 2026-09-27 根部固定与重力补偿边界（已由上节纠正）

为区分根部反作用、接触约束和执行器更新，诊断工具新增了 `--fix-root-link`、
`--disable-floor/--disable-ground`、`--zero-gravity` 以及重力遥测；这些参数只用于
trace/replay，不改变生产任务配置。MuJoCo 通过删除 `base_link` 的 free joint 生成真正
fixed-base 模型，Isaac 使用 `articulation_props.fix_root_link=True`；两端均使用 node2、
无箱体、40 个物理步和来源匹配的目标/延迟。

- 在 fixed-base、无地面、零重力且保留同一重力补偿目标的动态对照中，trace SHA-256
	匹配；最大 joint2/joint3 位置误差 `1.11e-4 rad`、速度误差 `2.31e-3 rad/s`、
	力矩误差 `1.48e-2 N m`。这排除了 `DelayedPDActuator` 的延迟、PD、armature 和
	物理步采样顺序是首要根因。
- 常重力、无地面 fixed-base 的原始来源匹配对照中，MuJoCo 初态 `qfrc_bias` 的
	joint2/joint3 为 `[-16.153, -6.141]`，Isaac `get_gravity_compensation_forces()` 为
	`[+15.880, +6.003]`。使用 MuJoCo 原始补偿目标时，Isaac 首步速度已明显分叉，40 步
	后 joint2/joint3 速度约 `[-2.914, -1.453]`；这不是箱体接触或地面碰撞造成的。
- 直接把 MuJoCo `qfrc_bias` 的符号翻转曾作为试验，但来源匹配回放反而使 MuJoCo
	快速运动而 Isaac 保持补偿静止；该试验已撤回，不能把简单加号改减号当作修复。
	当前结论是 MuJoCo/Isaac PIPER 资产的关节坐标、惯性/重力响应或 compensation API
	约定仍未对齐，需要先做来源匹配的 robot gravity/inertial 校准；不得调整训练 PD、
	恢复 PUSH-LOW 训练或进入实机接触。
- fixed-base 且保留地面接触的 MuJoCo probe 会出现静态腿部过约束，因此不作为技能或
	执行器验收证据；正式双仿真仍需在同一物理接触语义下重新验证。

本轮新增诊断产物均在 `../artifacts/go2-piper/contact-repair-20260925/native-safety/`，
包括 `push-actuator-node2-nobox-fixedroot-nofloor-physicszerogravity-*` 和
`push-actuator-node2-nobox-fixedroot-nofloor-gravity-*`。它们只用于定位首发分叉，不代表
PUSH/CLIMB 验收；下一步优先比较两端初态 gravity torque、link inertial frame、joint
axis/pose 和无补偿零力矩自由响应，再决定是否需要只修 MuJoCo 资产 profile。

<a id="record-0136"></a>

来源：AGENT_HANDOFF_CN.md。

## 冻结策略与产物

本地产物根目录：`../artifacts/go2-piper/2026-09-15/`。

| 技能 | 包 | 策略 SHA-256 |
| --- | --- | --- |
| NAV | `piper-nav-baseline-bundle` | `72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8` |
| PUSH | `piper-push-pose599-bundle` | `c3ddb39280fbbfd15327153b5bfd001dbbc75a49d86505b1bded762f344fc83a` |
| CLIMB | `piper-climb-center200-bundle` | `6d25118145668e381de648eebbe57b5ffe7dd4eb781ede7d1bc341eb559ecc32` |

原生录像：

- `../artifacts/go2-piper/2026-09-15/piper-push-pose599-native.mp4`
- `../artifacts/go2-piper/2026-09-15/piper-climb-center200-native.mp4`

三技能证据索引：`sim2real/go2-piper-low-level-policy-handoff/validation/piper-three-skills-index.json`。

<a id="record-0137"></a>

来源：AGENT_HANDOFF_CN.md。

## 运行入口

- PIPER 训练配置：`source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/`
- PIPER 训练与原生评估：`scripts/rsl_rl/train.py`、`scripts/evaluate_box_skills.py`、`scripts/evaluate_safe_base.py`
- PIPER MuJoCo 运行时：`mujoco/reconfigurable_navigation/piper_*_runtime.py`
- PIPER MuJoCo 检查：`mujoco/check_piper_*.py`
- 部署交接包：`sim2real/go2-piper-low-level-policy-handoff/`
- 训练交接包：`sim2real/go2-piper-low-level-training-handoff/`

本地 MuJoCo Python：`../.envs/go2-arx5-nav/bin/python`。Isaac 训练使用独立服务器环境，启动前必须重新检查 GPU 占用。

<a id="record-0138"></a>

来源：AGENT_HANDOFF_CN.md。

## GO2-PIPER 固定安装模型

仿真中 PIPER 不是独立刚体或安装关节，而是 Go2 `base_link` 的固定子体，二者共享同一
floating base、动力学求解器和底座状态估计。MuJoCo 原始 XML 的 `Piper` body 变换为
`(x, y, z) = (0, 0, 0.06 m)`；运行时会由 `mujoco/deploy/piper_robot_profile.json`
覆盖为 USD profile 的 `(0, 0, 0.07 m)` 和单位四元数。Isaac 组合 USD 同样将固定连接
合并进单一 articulation。

这只描述仿真名义安装，不代表实物已完成安装或标定。实机前必须测量并回写实际安装变换、
安装板/紧固件/线缆质量、总质量、全局质心和惯量；安装座 `Piper` profile 质量约 `1.02 kg`。

<a id="record-0139"></a>

来源：AGENT_HANDOFF_CN.md。

## 重要契约

- 策略关节顺序为 `FR, FL, RR, RL`，每腿 `hip, thigh, calf`，之后为 `joint1` 至 `joint6`；MuJoCo 模型顺序不同，必须显式重排。
- NAV 为 `210 -> 18`，PUSH 为 `226 -> 12` 加 IK 合成 6 个机械臂目标，CLIMB 为 `253 -> 18`。
- 冻结 PUSH 使用匹配的姿态 IK：末端俯仰 `0.8 rad`、预接近 `0.03 m`、接触后锁臂，并将实际组合的 18 维命令写入历史。PUSH-LOW 的位置 IK/不锁臂配置仅属诊断，不继承该验收。
- PIPER 的质量、安装、碰撞与执行器 profile 是训练资产对齐值，不是实物标定值。
- 任何策略、控制器、profile 或评估门槛变更必须产出新的 manifest、报告和 SHA-256，不回写既有验收产物。

<a id="record-0140"></a>

来源：AGENT_HANDOFF_CN.md。

## 安全边界

实机必须先完成机械安装、供电、通信、急停、只读状态采集、零点/方向/限幅、延迟与质心标定。先做断电回放、悬空低增益、支架测试和平地低速验证，再进入接触任务。

详细工作顺序见 [下一步计划](#source-next-steps-cn)，目标和验收标准见 [项目计划](#source-project-plan-cn)，
固定安装与实物标定见 [GO2-PIPER 固定安装与 Sim2Real 标定](../GO2_PIPER_MOUNTING_CN.md)。

<a id="record-0141"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

# CLIMB 慢速步态改造：2026-10-01

<a id="record-0142"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 当前方向：按用户要求直接训练攀爬（2026-10-02）

用户明确“训练攀爬而不是行走，NAV已经可以稳定行走”。停止把平地逐脚行走和整段离线路径搜索作为主要推进方向。新增隔离任务 `GO2-PIPER-Box-Climb-Stages`：在20cm箱沿开始学习前脚上台、混合高度支撑、身体抬升、后脚跟进。训练用近箱/分阶段起点必须单独标注；`Stages-Play`默认仍用原起点，仅显式传入 `--climb-stage-bank` 才启用训练起点诊断。24秒实验与原12秒验收分开；保留原碰撞、执行器限制和连续停稳1秒条件。

当前尚无达标慢爬策略。cp/cq/cr四阶段起点检查均0/32，全部终态完整；cr修正初始化目标与显式PD增益后没有腾空，但仍27次姿态终止，拒绝直接拿这组名义姿态训练。cs实测过渡姿态平移到箱沿也32次姿态终止，不能当作稳定站姿。ct默认站姿贴箱过近导致32次底座接触。cu将前脚放在x=.60（箱面x=.75），32回合均站满24秒、零安全终止，三足100%、无腾空、竖直峰值.553m/s、足力111.338N。cu箱沿PPO已于北京时间14:01:53启动，512环境/300轮，训练PID526883、监控PID526884；还没有新训练策略的攀爬成功结果。详细结果及后续启动记录见[箱沿训练记录](#source-climb-edge-training-20261002-cn)。视频8788仍为旧平地诊断，不是新攀爬成果。

后续优先事项：核对cu训练及监控进程，不要重复启动；第50/150/299轮分别做训练起点及原起点的32回合诊断，报告成功、完整性、三足支撑、腾空、竖直速度、足力和饱和时长，不能以奖励代替成功。候选固定后才做两组未用种子各32回合（每组至少30成功、无未完成）与真实速度录像。PUSH/MuJoCo/实机暂停。

以下内容按历史阶段保留，旧“下一步”不覆盖本节。

<a id="record-0143"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 用户目标与当前结论

用户看过model0录像后明确否定奔跳登台，要求自然、稳定、平缓的步态攀爬，以减少后续Sim2Real的冲击和电机风险。PUSH优化暂停；只在远程Isaac推进CLIMB，MuJoCo与实机仍暂停。**当前没有已达标的慢爬策略。** 旧Smooth策略保留为对照，不作为动作质量合格的交付候选。

最新cl–cm：发现固定慢摆腿方案的整段时间预算不成立。用cm全部32个准备前实测足位复算，在24cm固定步长/2.8秒逐脚摆动、支撑足不滑移的名义安排下，至少需要15–19次摆腿，仅摆腿即42.0–53.2秒，超过24秒；这不是机器人不能平缓爬箱的物理结论。停止继续微调这一固定节奏，下一步按CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN设计原起点→接近→20cm越沿→台顶停稳的整段协调轨迹，保持原任务/执行器门禁。已新增默认关闭的关节/机身/支撑位置联合采样预检：不可行时四足保持，不继续把脚送到被限位截断的落点；实际执行路径名义残差≤.106mm，但不是所有原失败已解决。cm的4.1/2.8秒首脚完成23/32、20/32，完整四步及20cm成功仍均0/32；四组候选均32个完整终态、零安全终止。全回合三足99.827%、腾空.06秒、竖直峰值.951m/s、法向足力203.635N、累计饱和最大.28秒；接管后三足100%、无腾空，cm法向峰值149.126/150.255N，不能称动力学全面改善。28项检查通过，cm关闭选项逐值复现cj/513原32终态与质量，规划决策/位移由保存输入重算一致。所有本轮远端评估及回归已结束，无新PPO；源码/原始结果/审计已归档，视频仍8788旧平地版。PUSH/MuJoCo/实机暂停。

<a id="record-0144"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 对照结果

实验b：`/path/to/artifacts/go2-piper/climb-crawl-20261001-b`，本地同名目录在仓库外`../artifacts/go2-piper/`。全部使用调参seed512、每环境一个回合，共32回合，零未完成；没有消耗新验收种子。

| 配置 | 成功 | 平均回合时长 | 安全终止/超时 |
| --- | --- | --- | --- |
| 旧Smooth model0，原12秒 | 30/32 | 3.763秒 | 1底座接触、1超时 |
| 旧actor补51维观测，直接限速 | 0/32 | .668秒 | 9底座接触、16姿态、7臂接触 |
| 同起点PPO第100轮 | 0/32 | .408秒 | 25底座接触、4姿态、3臂接触 |
| 同起点PPO第299轮 | 0/32 | .371秒 | 24底座接触、2姿态、6臂接触 |
| NAV观测投影并限速 | 0/32 | .862秒 | 28底座接触、4姿态 |
| 零动作/默认站姿并限速 | 0/32 | 24秒 | 32超时、零安全终止 |

除旧对照外均为**24秒实验任务**。零动作仅验证基础站立，不是攀爬成功。NAV投影重复当前帧代替历史，属于兼容性诊断，不能据此否定原NAV能力。旧策略复现的32个终态与a目录原报告完全相同。

旧model0的32回合全部出现四足同时离地，最长连续.12秒；至少三足支撑的时间占比约72.7%，底座竖直速度峰值1.015m/s，单足合力峰值617.94N，单控制步关节目标最大变化1.147rad。限速对照将目标变化压至.05rad，但失稳和任务失败显著增加，**不能把目标更平滑或更小的接触力当作任务改善**。NAV投影对照还出现2214.74N足部峰值。

零动作站姿的三足及以上支撑占比99.885%，但初始接触过渡仍有8回合检测到腾空、最长.06秒，竖直速度峰值.902m/s。因此“站满24秒”不等于启动阶段无冲击，也不等于电机安全。

步态指标采用20ms控制步采样、足部Fz>2N判定支撑、排除前.10秒初始化；单足峰值使用5个物理步的接触传感器历史。报告同时保留所有失败，不能只统计成功或隐藏起步瞬态。更短于采样周期的腾空可能漏检；这些指标不是电流/温度测量。完整指标与哈希见b目录`comparison.json`；`summarize_reports.py`复核完整性、成功记账、控制源码和旧终态一致性。

<a id="record-0145"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 新控制与观测契约

新增独立任务`GO2-PIPER-Box-Climb-Crawl`及`-Play`，不修改既有CLIMB/PUSH任务默认行为。

- 保留20cm、1.2×1.2m固定箱，原碰撞、力矩/速度上限、PD与延迟设置；选择性自碰撞开启；成功仍要求四足安全顶面与姿态速度合格、连续停稳1秒。臂接触同时阻止成功记账。
- 允许24秒慢速回合，单独报告，不能声称通过原12秒任务。
- 步序FL→RR→FR→RL；其余三足支撑时推进相位，所选足实际抬起且四足接触稳定.15秒后才换腿。转移阶段.10秒、摆动.60秒、步长.25m、参考额外净空.07m。
- 这是**接触门控的训练参考与奖励**，尚非足端IK/全身控制器。暂停相位和单腿参考不保证真实机器人只抬一腿，也没有实现显式质心转移闭环。质量必须由实际轨迹证明。
- 18维动作关节顺序、缩放、默认偏置不变。参考速度限制：腿2.5rad/s、臂.5rad/s；参考加速度限制：腿15rad/s²、臂3rad/s²。限位附近使用制动包络。这些约束针对目标，不等于实际关节速度/力矩受同样边界控制。
- 原253维CLIMB前缀之后追加51维步态状态，共304维，包括所选腿、相位、触地状态、落脚误差、已施加关节参考及其速度。目标速度命令换为慢爬命令，最大前进.12m/s。304维候选必须与新控制器成套使用，不能直接替换冻结253维CLIMB。
- 增强不足三足支撑、腾空、滑移、竖直运动、接触冲击、力矩裕量的惩罚，并增加落脚跟踪。显式记录观测、控制及物理来源哈希。

本地检查：4项步态/限速检查、9项评估记账检查通过；Python编译及diff格式检查通过。检查覆盖突变命令下q/v/a限制、缺支撑时不推进、实际抬脚落脚条件、跨回合腾空计时清零、脚先抬高再跨越。b的300轮远程运行和六组评估验证了Isaac接入，但不构成慢爬成功。

<a id="record-0146"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 已停止的站姿实验c

路径`/path/to/artifacts/go2-piper/climb-crawl-20261001-c`。从已经验证能保持站立的零输出actor起步（保留隐藏层，末层置零），304→18，初始SHA `d9673b2b49f5dce08d844a1de81a3a37e7f90e85d20b86489a5751b8aa2b1dee`。改变初始探索std为.10；落脚跟踪由5cm宽的平方距离高斯改成距离指数、尺度.12m，使未迈到目标的脚仍有连续训练反馈。不是单变量消融。

seed630、512环境、600轮、固定学习率1e-4，每100轮保存；原计划训练GPU0、在GPU1评估100/300/599轮（seed512、32回合、24秒）；发现相位调度问题后已停止训练及监控，仅100轮完成评估。训练有2400秒上限，监控有3300秒等待上限，单批评估700秒上限。状态见`monitor-status.json`、启动记录`launch-record.json`，源码与初始actor在启动前逐项SHA核验。

c还加入固定地形契约检查，避免使用其他高度/尺寸时仍错误沿用20cm落脚参考；评估器修复多回合腾空计时跨重置累加。b远程源码快照保持不变；其每环境一个回合的结果不受此修复影响。复现b或c必须使用各自source-snapshot；仓库当前源码对应后续d。

<a id="record-0147"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 已完成实验d：仍未学会攀爬

c第100轮评估0/32：29超时、3底座接触，全部回合完整。至少三足支撑占比99.877%，但主要停留在原地；各环境最大前向坐标的均值仅.062m（注意这不是相对初始位置的位移）。最长连续腾空仍.06秒，单足峰值206.13N。原本为600轮的c训练及自动监控已经按启动记录中的专属进程组停止，不再等待c的300/599评估。

进一步检查调度发现：虽然换腿要求实际离地再落地，但单次摆动内部仍按时间走完抬升、前移、下降。如果实际脚未及时抬起，参考已经降回地面且等待换腿，不能持续教会它抬脚。该问题由本地状态机回归检查复现并修复：参考停在25%阶段，直到实际脚离地并达到目标净空高度（容差2cm），才继续水平移动；参考停在75%阶段，直到实际脚到达落点上方（XY误差≤3cm，仍满足高度），才开始下降。其余三足支撑与最后四足落稳.15秒的门控继续保留。重置后的第一步先初始化落脚参考，不推进相位。

新目录`/path/to/artifacts/go2-piper/climb-crawl-20261001-d`。沿用c的站姿初始化、seed630、512环境、std.10、固定lr1e-4、600轮及24秒任务，只修正上述相位逻辑及其来源记录；GPU0训练，GPU1自动评估100/300/599轮。`launch-record.json`给出专属进程，`monitor-status.json`记录每批状态；超时上限与c相同。不要重启c，也不要在d首次评估前宣称实际步态已改善。

4项步态检查包含一个专门的反例：经过任意多控制步，实际脚仍未抬到高度时，参考必须停在抬升段末端；脚未到达落点上方时不能下降；未真实落稳时不能换腿。这验证了调度逻辑，并不验证机器人动力学上的成功。

<a id="record-0148"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## d最终结果与当前诊断e

远程600轮已完成，用时约19分33秒，训练和监控进程均正常退出。100/300/599轮均为0/32，三批均完整；100/300各30超时、2底座接触，599为32超时、零安全终止。未通过任务验收，不延长同一训练。

| 检查点 | 至少三足支撑占比 | 最长连续腾空 | 底座竖直速度峰值 | 单足合力峰值 | 单关节累计饱和时长最大值 |
| --- | --- | --- | --- | --- | --- |
| 100 | 99.892% | .06s | .887m/s | 200.59N | .30s |
| 300 | 99.889% | .06s | .921m/s | 207.73N | .36s |
| 599 | 99.893% | .06s | .940m/s | 206.08N | .34s |

高支撑比例主要来自站着不动，不能当作已学会慢爬。599的env0采样末端相对初始仅前移约4.86cm，四脚仍在地面承重；各环境最大前向坐标均值.023m也不是推进距离。腾空/竖直峰值仍包含初始化接触过渡；上述饱和时长是阈值98%下的累计量，不是电机温度证明。三份完整报告与来源检查已取回本地d目录，汇总为comparison.json，状态completed_rejected。

当前短程诊断e：`/path/to/artifacts/go2-piper/climb-crawl-phase-20261001-e`，同一d/model599、seed512、32回合、24秒，记录真实足位置、参考位置、摆动阶段和触地状态，定位未迈步的具体环节。仅增加遥测，控制和物理源码沿用d；独立脚本evaluate_crawl_phase_e.py不覆盖旧评估器。报告完成后须逐项核对32个原有终态字段，确认遥测没有改变行为。初始启动PID3931417，700秒上限。 **e已完成**：32个原有终态逐字段一致，物理/控制哈希、关节运动及步态指标完全一致。32回合均停在第一只FL足的抬升阶段（phase=.25，lifted=false）；env0末端实际足心z=.02287m，参考z=.12004m，四足均接触。由此确认参考已正确等待，但策略未完成第一步抬脚；尚不能仅凭这一结果断言唯一原因是重心位置。完整校验见e/verification.json。

<a id="record-0149"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 训练依据与下一阶段方法

当前PPO获得机器人状态、地形、目标、步序和足端参考误差，输出18个关节目标偏移，通过物理仿真后的任务/步态奖励更新神经网络。它不是读懂文字要求的语言模型。当前足端轨迹是观测和奖励目标，只有关节目标的限位/限速/限加速度被直接执行；还没有足端IK或全身控制去保证跟随轨迹，也缺少显式重心转移基础控制。

因此现在仍要求RL自行发现如何承重、卸载一条腿、抬脚、移动和落地，难度太大。三批0/32表明这套引导不足；成功奖励未被触发，而原地保持接触能获得部分奖励并避免失稳惩罚。下一阶段先建立可执行的支撑转移和单步参考，验证实际足端跟踪和支撑/力矩裕量，再让RL学习有限残差修正；课程从平地稳定单步、慢走到低台逐步提升至20cm。课程结果单独报告，最终20cm和原安全/停稳要求不放宽。先完成具体失败诊断，不靠继续加训练轮数掩盖控制结构缺口。

<a id="record-0150"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 接下来如何判断

d已证实仍不会有效攀爬，先用e定位未迈步阶段，再实施支撑转移与单步基础控制。不能在没有前进的情况下仅因站立时间/奖励增加就宣称改善。若步态参考长期无法跟踪，优先检查轨迹速度、足端可达空间、质心转移和接触时序，考虑受限足端/全身参考控制以及分阶段课程；不要无限延长同一无效微调。

得到可用候选后先固定权重、控制、物理参数，再用两组未使用的32回合检查成功率（每组至少30成功、零未完成），同时检查三足支撑、腾空、竖直速度、接触力和力矩饱和时长。动作质量不合格即使成功率过线也不能作为平缓版本交付。成功与失败均录真实速度视频，不能用慢放代替动作改进。电机热风险仍需真实额定参数、电流及温度数据和分级验证，仿真指标只能用于筛查。

<a id="record-0151"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 支撑转移与平地单步诊断 f–k

本轮没有追加PPO。先验证可执行的单步基础控制：站稳2秒、用3秒将组合机器人实际质心移向其余三脚支撑三角形、左前脚抬5cm并前移8cm、落脚等待。支撑位置与雅可比来自当前Isaac articulation，质心按实际各刚体质量加权；腿部30Nm/rad刚度、执行器力矩限制及原目标限位/限速/限加速度保持不变。所有试验在远程运行，每批seed512、32个完整首回合、24秒、零未完成。20cm箱仍保留，但只做箱前平地单步；**全部CLIMB成功率仍为0/32，不属于20cm攀爬验收。**

f将足端误差积分为关节参考，连零位移站立也容易失稳；减小增益仍有长时间力矩饱和，拒绝。g改成实测姿态上的笛卡尔反馈，两组均32次安全终止。h零修正站姿32回合保持，但没有迈步。i冻结受载站姿并以初始雅可比生成IK位移，无质心转移时能站住但脚仍不离地；有转移时机身下沉。j加入机身/足端误差反馈仍无完整单步，不能据此声称改善。

曾怀疑雅可比的关节映射：实测核验发现PhysX浮动基雅可比使用根刚体**质心**线速度，不能用根链接原点线速度。改用正确速度约定后，四足预测与实测速度误差最大9.36e-8m/s，排除了这项映射错误。h旧审计的约.0137m/s共同残差来自约定不匹配。

k加入准静态支撑力前馈：按实际重量和水平力矩平衡分配各脚竖直力，抬脚过程中把左前脚承重逐渐转到另外三脚；以重力补偿减去接触力广义力矩计算关节偏置，前馈裁剪到实际力矩限值的75%，再除以原刚度转换为位置目标偏置。这不是完整全身动力学/摩擦约束控制器，裁剪后不保证精确力矩平衡，原PD也可能叠加反馈力矩达到饱和。

| 实验/重心转移 | 单步完成且无后续安全终止 | 安全终止 | ≥三足支撑占比% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| i/centroid | 0/32 | 10 | 99.722 | 0.060 | 0.902 | 204.383 | 0.280 |
| i/none | 0/32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| h/none | 0/32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| j/centroid | 0/32 | 7 | 98.911 | 0.060 | 0.902 | 462.633 | 1.540 |
| j/none | 0/32 | 10 | 98.737 | 0.060 | 0.902 | 601.787 | 0.280 |
| k/centroid | 18/32 | 9 | 97.150 | 0.060 | 0.902 | 1025.646 | 0.420 |
| k/none | 3/32 | 16 | 96.970 | 0.060 | 1.108 | 607.641 | 0.700 |
| f/centroid | 0/32 | 31 | 93.308 | 0.100 | 0.902 | 322.713 | 5.280 |
| f/gain02-centroid | 0/32 | 16 | 94.075 | 0.060 | 0.902 | 208.651 | 15.800 |
| f/gain02-none | 1/32 | 25 | 98.472 | 0.060 | 0.902 | 206.494 | 14.260 |
| f/none | 0/32 | 32 | 91.536 | 0.860 | 0.902 | 647.160 | 1.400 |
| g/centroid | 0/32 | 32 | 97.995 | 0.080 | 1.162 | 766.991 | 0.320 |
| g/none | 0/32 | 32 | 97.670 | 0.060 | 1.198 | 936.405 | 0.340 |

单步计数仅表示经过抬升、移动、落脚，并满足四脚接触/低线速度等待.20秒；它不是CLIMB的1秒姿态速度停稳标准。表中支撑占比按32回合等权平均，其他指标取全部回合最大值，包含失败；步态指标排除前.10秒，仍包含启动接触瞬态。力矩饱和阈值98%，是累计时长。初始目标写入也在关节运动报告内，不能把参考限速当作实际电机限速或热安全证明。

k/centroid首次得到18/32个完整单步，其他为9次安全终止和5次未完成单步的超时。对照不转移质心仅3/32、16次安全终止。env0左前脚实际从z=.0236m抬高到约.09m，最终前移约7.4cm后落地；这次观测到真实足运动，不再只是参考轨迹。但全批峰值1025.65N，来自env14姿态失败；9次安全终止中7次发生在转移阶段、2次在水平摆动阶段。**这只是基础控制的局部进展，仍不够稳定，不能扩大为成熟慢爬策略。**

远程目录前缀为`/path/to/artifacts/go2-piper/`，依次为`climb-support-step-20261001-f`、`climb-support-step-20261001-g`、`climb-support-audit-20261001-h`、`climb-support-anchor-20261001-i`、`climb-support-feedback-20261001-j`、`climb-support-load-20261001-k`。本地仓库外同名目录保存脚本快照、启动记录与报告；k/comparison.json核验15份报告（含l两次录像复现）的脚本哈希、每环境唯一终态和回合完整性。所有候选及对照均未替换冻结策略。

### 已完成复核 l

`climb-support-review-20261001-l`复用k/centroid控制、seed512和原物理环境，仅新增独立1秒落脚停稳计数与真实速度录像。新增计数要求四脚接触、线速度<.05m/s、角速度<.4rad/s、重力投影z<-.94、落点误差<2.5cm连续1秒；仍是平地单步诊断。分别录env0和最大冲击失败env14，25fps、每2个20ms控制步1帧，首回合终止后停止该视频。两个32回合复核必须逐项匹配k原终态，不能因重新录像增加独立样本量。复核已完成：两批原32终态全部逐字段匹配k，步态/运动指标及资产哈希一致；18个单步也全部通过新增1秒稳定检查，零未完成。视频分别24秒/6.12秒、1280×720、25fps，已取回本地。关键帧显示env0真实抬脚、前移和落稳，env14在转移期机身转偏、下沉、倾倒；尚不判定步态质量通过。完整连续动作可由本地index.html按真实速度检查，verification.json保存复现与视频哈希。

下一步定位转移期失稳、约束单步控制的支撑力与姿态；稳定平地单步后才进入多腿慢走/低台课程，最终回到20cm。没有稳定基础控制前不恢复同一PPO长跑。新增3项本地纯Torch检查验证三角形边界、阻尼IK及支撑力/水平力矩守恒；Isaac接入已通过，但数学检查不构成任务成功证明。

截至本轮结束，f–l实验及录像进程均已结束，无PPO在运行。l复核未消耗新验收种子。d四份任务源码与冻结计划哈希一致，完整44份任务Python及实际环境YAML的哈希另存于k/l的task-source-verification.json。下次从k的支撑转移失败继续，不重复d训练或l录像。

<a id="record-0152"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 支撑闭环、执行器延迟与交叉诊断 m–r（本轮最新）

本轮仍未追加PPO，先推进平地单步基础控制。全部批次32个首回合、24秒、20cm箱与原碰撞/执行器门禁不变；机器人尚未登箱，**所有CLIMB成功率仍为0/32**。本节单步成功统一采用l新增的严格1秒落脚稳定标准，不能与早期仅.20秒的相位完成计数混用。

m将10cm上限的重心居中转移改为沿同方向只移动到3cm三脚支撑裕量，实际起脚门槛仍1.5cm。env14位移从10cm降到5.98cm，安全失败反而从9增至11，不采用；对照的32原终态和运动/步态指标完整复现k。新的逐环境遥测确认失稳前已有横向与角速度振荡，故继续隔离机身反馈回路，而不是放松成功门槛。

n关闭全部机身纠偏时，32回合均通过支撑转移，但17次在抬脚/移动/落脚后失稳；只关速度阻尼则更差。o据此在四脚转移期间保留受载姿态IK与支撑力前馈，抬脚卸载时用1.5秒平滑开启原机身位置/姿态/速度纠偏，得到29/32严格单步、1次安全失败，转移期不再失败。

o剩余问题为一次落脚后失稳和两次足端跟踪等待；三者腿部实际延迟均为4个5ms物理步。p分别测试落地后.75秒平滑返回支撑腿反馈，以及受限足端积分修正，仍有新增失败。积分仅在抬升/移动/下降参考段结束、三脚支撑、摆动脚未接触且该腿力矩低于90%时更新，增益.5/s、各轴限幅3cm；它补偿参考IK的残差，不能代替限位/力矩门禁。

q保留o分阶段机身反馈，将外环修正系数从.5减至.25，**原PD刚度/阻尼及0–4步延迟分布不改**。与受限足端积分配合，seed512得到32个相位完成、其中30个通过1秒落脚稳定，零安全终止；env11/16最终落点误差3.26/2.85cm，仍超出2.5cm要求，未算成功。仅降低系数不加积分为27/32，不能只用“降低增益”解释结果。

| 实验/批次 | 严格单步成功 | 安全终止 | ≥三足支撑占比% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| m/centroid-seed512 | 18/32 | 9 | 97.150 | 0.060 | 0.902 | 1025.646 | 0.420 |
| m/margin-seed512 | 19/32 | 11 | 97.316 | 0.060 | 1.175 | 1242.915 | 0.580 |
| n/bodyoff-seed512 | 15/32 | 17 | 94.958 | 0.060 | 0.902 | 276.627 | 0.280 |
| n/derivativeoff-seed512 | 1/32 | 23 | 94.020 | 0.060 | 1.075 | 834.299 | 0.840 |
| o/phased-seed512 | 29/32 | 1 | 99.643 | 0.060 | 0.902 | 204.383 | 0.280 |
| p/integral-seed512 | 29/32 | 2 | 99.202 | 0.100 | 0.902 | 236.566 | 1.060 |
| p/stance-seed512 | 27/32 | 2 | 99.522 | 0.060 | 0.902 | 252.574 | 0.280 |
| q/lowbody-seed512 | 27/32 | 2 | 95.815 | 0.060 | 0.902 | 204.383 | 0.280 |
| q/lowbody_integral-seed512 | 30/32 | 0 | 98.549 | 0.060 | 0.902 | 204.383 | 0.280 |
| r/cross513 | 26/32 | 3 | 97.926 | 0.060 | 0.951 | 224.762 | 0.540 |
| r/replay512 | 30/32 | 0 | 98.549 | 0.060 | 0.902 | 204.383 | 0.280 |

以上全部完成32回合、零未完成；“单步未成功”与“回合未完成”不同。支撑占比按回合等权，峰值覆盖失败与初始化过渡，未剔除差样本。

### r：交叉种子仍不够稳定

固定q的`.25机身反馈 + 分阶段开启 + .5/s受限摆动积分`后，用seed513作平地诊断交叉检查，只有26/32通过1秒稳定、3次落脚后姿态失败。另有env0在转移阶段因速度未充分稳定而等待至超时，env2/3相位完成但未通过严格落脚检查。不能把调参批次30/32当成可泛化的稳定基础控制，也不能把这两个平地批次冒充20cm的两组独立验收。seed512/513现都属于诊断使用过的种子。

r的seed512录像复核与q全部32终态逐字段一致，运动/步态及资产哈希一致。额外的2秒后视图显示：seed512/513均未检测到四脚同时腾空，但最大竖直速度仍为.182/.491m/s，足部峰值160.32/224.76N。完整回合的.06秒腾空及.902/.951m/s峰值仍保留报告；初始化约.33m高度落到承重站姿的瞬态没有被隐藏。

当前录像：seed512/env16落点不合格、seed513/env0转移等待；另补录已通过单步的seed512/env23。全部为远程32环境批量复现、25fps真实速度，只隐藏其他机器人视觉，不改变物理。入口为仓库外`../artifacts/go2-piper/climb-support-crossreview-20261001-r/index.html`。三份录像均已完成并取回，24秒、1280×720；两次seed512录像的全部32终态均匹配q。关键帧显示成功env23仍有明显机身倾斜变化，因此虽满足单步停稳门禁，也未判定自然慢爬动作质量通过。浏览入口`index.html`。

实验目录前缀为`/path/to/artifacts/go2-piper/`，后缀依次为`climb-support-margin-20261001-m`、`climb-support-bodyloop-20261001-n`、`climb-support-phased-20261001-o`、`climb-support-landing-20261001-p`、`climb-support-delaymargin-20261001-q`、`climb-support-crossreview-20261001-r`；本地仓库外同名目录已保存源码快照、实际配置、日志、报告和验证。r/comparison.json核验来源、唯一首回合终态和完整性；r/verification.json记录复现与视频哈希。控制源码SHA为`791a8239042325fae6cc4464e817b81a8454fc86777585625b6500480f10b269`，仅诊断参考，未替换冻结策略。新增两项数学检查覆盖支撑位移裕量及积分门控/限幅/回退，共5项通过。

下一步优先处理两个已测得的缺口：落地后足端相对目标发生漂移，以及较大执行器延迟下支撑姿态不能保持。为失败环境补齐落脚前后历史，验证实际支撑/足端闭环与参考平滑；保留q作诊断对照，不继续无限加长PPO，也不因seed512已达30/32就直接进入多腿爬台或放宽落点/停稳门槛。稳定单步后再推进多步与低台课程，最终仍按20cm完整任务验收。

本轮m–r及三份录像已结束；本项目无PPO、评估或录像在运行。5项纯Torch检查、Python编译与diff格式检查通过；四份d任务源码保持冻结计划哈希，44份实际任务Python及环境YAML哈希另存。其他共享服务器作业未干预。

<a id="record-0153"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 静止摇晃、参考保持与落脚切换 s–y（最新）

针对用户“不爬时仍一直摇晃”的反馈，本轮只做远程Isaac控制诊断，没有追加PPO。先将q控制停在3秒支撑转移之后，不抬脚，以隔离静止问题；再测试完整平地单步。所有批次保持20cm箱、原碰撞/执行器门禁、24秒实验，与原12秒任务区分。**全部CLIMB成功仍为0/32；静止试验不承担登箱动作，表中单步记为不适用。**

新增末段连续5秒安静检查：从第5秒后计时，四脚接触、机身线速度<.025m/s、角速度<.1rad/s、重力投影z<-.94，计时窗口内位置漂移<1cm；终态仍持续满足至少5秒且没有安全终止。它是附加诊断，未替代原单步1秒检查或CLIMB门禁。**该检查只证明末段安静，不约束从转移结束到最终稳定之间的位置漂移，因此32/32通过也不能称为站姿保持合格。**

s/live静止基线26/32通过末段安静、零安全终止，env0在目标停止后仍持续运动。负载补偿使用实时质心、足位、雅可比，将力矩换为关节目标偏移；机身目标停止不代表这些关节目标停止。改用固定计划几何的s/planned虽30/32安静，却出现2次安全终止，拒绝采用。t将补偿低通滤波.1/.25秒，两组均32次安全终止，也拒绝；不能通过任意冻结或放慢补偿解决承重闭环问题。

u在四脚承重、支撑裕量与姿态/速度满足条件时，保存现有受载关节参考，继续由原限速与延迟PD执行；另比较用实际q、dq、力矩重建PD目标。两种方式在seed513均32/32末段安静、零安全终止。env0最后6秒抽样线速度峰值由.130342降为.000917m/s，角速度由.183732降为.003555rad/s（command方案）。这是减少持续摇晃的局部证据。

**y录像复核同时揭示u的明显缺口：env0从5秒到末帧23.8秒，机身净位移14.02cm，一只后脚净位移8.22cm；相比之下原基线分别约1.91cm/最大足位移.37cm。** 保存关节参考后，机器人改变承重姿态并移动了支撑脚，最终才安静，未保持计划支撑位置。关键帧5/10/18/23秒也显示此变化。不能把这一方案作为已修复的站立或攀爬控制；后续必须同时记录完整保持阶段的机身位置、姿态、各支撑脚漂移与支撑裕量，不能只检查最终5秒速度。

v将command保存用于抬脚前与落脚后，完整单步退化为15/32和10/32，11/14次安全终止；w改为重建PD平衡参考或仅在落脚后保存，仍明显退化，全部拒绝。失败历史显示，捕获瞬间虽然速度小，加速度仍有.82–2.11m/s²、角加速度1.45–8.92rad/s²；摇晃的转向点被误认为已稳定。

x保留q原抬脚前与摆动控制，仅在落脚后连续.5秒满足更严格低速度及加速度条件才保存参考。新增安全失败消失，但单步仍26/32、3次原安全失败；单步且末段安静从基线25/32降到24/32，没有净改善，不采用。x/baseline的32个原终态字段、步态/运动指标、资产与延迟分布逐项复现r/cross513，确认新增诊断默认关闭时未改变原控制。

| 实验/批次 | 完成/未完成 | 严格单步 | 末段安静5秒 | 单步且安静 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s/live-seed513 | 32/0 | — | 26 | — | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| s/planned-seed513 | 32/0 | — | 30 | — | 2 | 99.521 | 0.060 | 0.951 | 203.635 | 0.280 |
| t/filter10-seed513 | 32/0 | — | 0 | — | 32 | 91.026 | 0.060 | 0.951 | 256.221 | 0.660 |
| t/filter25-seed513 | 32/0 | — | 0 | — | 32 | 93.184 | 0.060 | 0.951 | 216.895 | 0.320 |
| u/command-seed513 | 32/0 | — | 32 | — | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| u/equilibrium-seed513 | 32/0 | — | 32 | — | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| v/seed512 | 32/0 | 15 | 18 | 15 | 11 | 96.824 | 0.060 | 0.902 | 204.383 | 0.280 |
| v/seed513 | 32/0 | 10 | 16 | 9 | 14 | 96.709 | 0.060 | 0.951 | 219.259 | 0.480 |
| w/both | 32/0 | 9 | 16 | 8 | 14 | 96.722 | 0.060 | 0.951 | 290.240 | 0.640 |
| w/landing | 32/0 | 10 | 18 | 10 | 11 | 97.333 | 0.060 | 0.951 | 224.762 | 0.540 |
| x/baseline-seed513 | 32/0 | 26 | 26 | 25 | 3 | 97.926 | 0.060 | 0.951 | 224.762 | 0.540 |
| x/guarded-seed513 | 32/0 | 26 | 25 | 24 | 3 | 97.926 | 0.060 | 0.951 | 224.762 | 0.540 |
| y/after | 32/0 | — | 32 | — | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| y/before | 32/0 | — | 26 | — | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

所有数量分母为32，回合均完整，无未完成；安全终止也计入完整回合。严格单步为原落脚误差<2.5cm、四脚接触与姿态速度门槛连续1秒；“单步且安静”要求同时通过此检查和末段5秒安静。支撑按回合等权，峰值与饱和覆盖全部回合含失败；原统计排除前.10秒，仍保留初始化腾空.06秒及约.95m/s竖直速度峰值。没有以2秒后子集替代完整统计，也没有电机热安全结论。

### y录像、复现与来源

两段录像均为seed513/env0、24秒/600帧/25fps/1280×720真实速度，由远程32环境复现。before使用s源码、after使用u源码；两次全部32原终态、步态/运动、资产哈希、执行器延迟分别匹配各自原报告，录像不增加独立样本量。已检查5/10/18/23秒关键帧与数值轨迹，尚未将连续动作质量判为通过。新页面`index.html`明确标注“仅静止诊断，存在位置漂移”；旧8769单步页保留。

本地仓库外与远程`/path/to/artifacts/go2-piper/`同名目录依次为`climb-support-static-20261001-s`、`climb-support-filterhold-20261001-t`、`climb-support-capture-20261001-u`、`climb-support-stancecapture-20261001-v`、`climb-support-equilibriumstep-20261001-w`、`climb-support-settledcapture-20261001-x`、`climb-support-staticreview-20261001-y`。源码快照、实际环境YAML、日志、启动记录与报告已取回；y/comparison.json汇总14份报告及脚本哈希核验，y/verification.json记录复现、视频哈希和env0漂移，video-metadata.json记录视频格式。四份d任务源码匹配冻结计划；44份实际任务Python及各批YAML哈希保存在task-source-verification.json。

当前新增源码开关均默认关闭，仅保留已远程验证的诊断路径，不替换冻结策略。7项纯Torch检查、Python编译与diff格式检查通过。s–y控制诊断及录像均已结束，本项目无训练/评估/录像在运行；其他共享服务器作业未干预。

下一步：保留q/r为单步对照，u仅作为“末段能安静但位置保持失败”的诊断证据。优先修正受载支撑平衡和落脚后的连续切换，在保持完整段同时约束机身漂移、足部滑移、支撑裕量及关节参考；使用现有失败历史验证，不继续任意冻结补偿或盲加滤波。通过完整单步与保持质量后再推进多腿、低台、20cm，最终固定候选并使用两组未用种子各32回合≥30成功、零未完成和真速录像验收。

<a id="record-0154"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 质心水平制动与完整保持测量 z–ad（当前最新）

本轮继续远程Isaac控制诊断，没有新增PPO。仍为独立24秒实验，保留20cm箱、原停稳/碰撞/执行器门禁；PUSH、MuJoCo、实机暂停。**20cm CLIMB全部0/32；下述31/32与32/32只表示平地左前脚单步，不是登箱验收。** seed512/513均已用于调参，未消耗新的最终验收种子。

### 改动与静止结果

原支撑分配只给竖直承重力。新可选控制根据整体质心速度与平滑支撑转移参考速度之差，给出水平加速度（速度误差增益4/s、加速度向量模长上限.4m/s²），同时调整竖直承重分配，补偿水平反力的俯仰/横滚力矩。通过原重力补偿及`G−JᵀF`换算关节目标，继续由原PD30/.6、0–4个物理步延迟及q/v/a限制执行；力矩前馈仍限于额定75%。本轮不保存/冻结关节参考，也不使用已拒绝的补偿低通滤波。

新增`HoldQuality`从支撑转移参考结束或落脚阶段开始，累计整个保持阶段的机身位移、机身相对目标误差、各脚位移/目标误差、线角速度峰值、支撑裕量和缺少四脚接触的时间。中途重新安静或返回原位置都不清零历史最大位移，从而避免上一轮只看末段5秒的遗漏。它是附加遥测，不修改CLIMB成功记账。

z静止对照：原基线仍26/32末段安静、零安全终止；新增水平制动为32/32、零安全终止。原基线全部32终态原字段、步态/关节指标、资产和延迟逐项复现s/live。新方案全部32个环境各记录完整19秒保持：最差机身位移1.134mm、足部位移.602mm，机身相对计划目标最大误差1.914cm、足部目标误差最大1.119cm，全部四脚持续接触，三脚支撑裕量最小3.963cm。原基线整个保持阶段机身最大位移5.572cm、足部.760cm。此处累计最大位移与y记录的5秒至末帧“净位移”不同，不混为同一指标。

z的静止改善不再依赖u那种先漂移14cm再安静的行为。不过末态最大机身倾角仍约10.50°，暂不宣称所有姿态都自然，也不将一次诊断种子扩大为实机鲁棒性结论。

### 完整单步与剩余缺口

aa固定同一制动参数，完整平地单步在seed512/513分别31/32、32/32，均无安全终止、无未完成；两批末段安静均32/32。相较q/r的30/32、26/32及0/3次安全终止，单步计数与安全结果改善。2秒后两批未检测到四足同时腾空；至少三足支撑100%/99.923%，最大竖直速度.202/.197m/s、足部峰值120.03/123.80N。完整回合初始化峰值仍保留在下表。

**aa仍未达到自然稳定单步的完整质量要求。** seed512/env23最终左前脚误差8.44cm，严格单步不通过；落脚阶段机身最大位移8.97cm、右前脚位移17.75cm，缺少四脚接触累计.52s。该环境在旧q中曾通过，不能只汇报总数而漏掉新退化。seed513虽32/32通过原检查，env3/11/31仍有落脚短时滑移，最大机身位移3.87cm、最大足部位移3.03cm；原1秒与末段5秒检查均不能代表整段动作平缓。继续处理落脚后的承重与摆动反馈交接，不直接推进多腿登台。

### 力臂模型对照 ad：拒绝采用

z/aa的力矩补偿使用平均足端高度，是平地近似；抬起左前脚时，它也影响平均高度。aa两个env0轨迹在6.6秒的请求力矩残差约.077/.080Nm。ad改为每只脚的实际反力力臂，将反力作用线投影到质心高度后分配承重；离线不等高足端检查满足总力与零合力矩，但完整Isaac单步仍31/32、32/32，seed512/env30在17.50秒新增姿态安全终止。**数学一致性改善没有带来整体控制改善，ad不替换aa。** ad独立源码与报告保留在产物目录；仓库中的诊断参考恢复为已验证的aa快照，控制SHA `81883005c7e8b9c6795014b746cc5f5c7179f7d90ec403770815e008a7913d1a`。该近似仅作平地诊断，不作为通用台阶全身控制器或可部署策略。

| 实验/批次 | 严格单步/32 | 末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| z/baseline | — | 26 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| z/damping | — | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| aa/step512 | 31 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| aa/step513 | 32 | 32 | 0 | 99.757 | 0.060 | 0.951 | 203.635 | 0.320 |
| ab/after | — | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| ab/before | — | 26 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| ac/failure512 | 31 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| ac/success513 | 32 | 32 | 0 | 99.757 | 0.060 | 0.951 | 203.635 | 0.320 |
| ad/step512 | 31 | 31 | 1 | 99.835 | 0.060 | 0.902 | 204.383 | 0.320 |
| ad/step513 | 32 | 32 | 0 | 99.767 | 0.060 | 0.951 | 203.635 | 0.300 |

每行32个完整首回合、零未完成；所有CLIMB为0/32。静止行单步不适用。支撑按回合等权，峰值覆盖失败，力矩饱和为98%阈值的最大单关节累计时长；保留初始化.06秒腾空与.902/.951m/s竖直峰值。此表未证明电机电流/温度安全；低冲击失败也未计为成功。

### 录像、校验与后续

ab为z的静止前后对照，seed513/env0；ac为aa的单步失败seed512/env23与成功seed513/env0。四段均远程32环境复现、24秒/600帧/25fps/1280×720真实速度，全部32原终态、步态、运动、完整保持指标、资产和延迟分别匹配对应原报告。录像不增加独立样本。已检查静止5/10/18/23秒与单步5/7/10/12/18/23秒关键帧及轨迹；完整连续动作仍留给视频检查，不据关键帧判定自然慢爬通过。新检查页`index.html`；旧8770保留为被拒绝的关节参考保存方案。

本地仓库外与远程`/path/to/artifacts/go2-piper/`同名目录为`climb-support-wrench-20261001-z`、`climb-support-wrenchstep-20261001-aa`、`climb-support-wrenchreview-20261001-ab`、`climb-support-wrenchstepreview-20261001-ac`、`climb-support-wrenchheight-20261001-ad`。报告、源码快照、实际YAML、日志、启动记录和视频均已取回。ab/comparison.json汇总10份报告并验证源码哈希；ab/ac的verification.json记录复现和视频哈希。四份d任务源码仍匹配冻结计划，44份实际任务Python与环境YAML哈希另存。9项纯Torch检查、Python编译与diff检查通过；新增检查覆盖受力/力矩一致性和完整保持位移不会被重新安静抹除。

全部z–ad远程诊断与录像进程已结束，没有本项目PPO或评估在运行。默认关闭新支撑力控制，不覆盖冻结策略。下一步优先利用ac失败全过程定位落脚冲击、前脚滑移与较大延迟的耦合，验证摆动脚落地后连续恢复承重/支撑反馈（既有stance_after_landing可作单变量对照），同时保留全保持阶段位移指标。不能因计数31/32、32/32就跳过质量缺口；完善后再逐腿、多步、低台、20cm，最终固定完整候选后再做两组未用种子各32回合≥30成功、零未完成及真实速度录像验收。

<a id="record-0155"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 普通待机与抬脚预备分离、腿部解析几何 ae–ai（最新）

用户指出“静止时一条腿明显更弯，NAV能停稳，为何CLIMB不能”。此前ab静止录像实际为**完成重心转移后、未抬脚的预备姿态**，不是普通待机；长期保持该姿态并将其笼统称作站立不恰当。ab/after/env0末帧四脚均接触，足部中心高度差约0.28mm，因此该样本的视觉高低主要是腿部屈曲/机身相对脚的位置不对称，并非一脚悬空；不能据此推断用户观看的每一帧。

### 排除落脚反馈混合，修正名义腿部几何

ae直接启用既有stance_after_landing，单步退化为24/32、24/32。发现该开关在phase1→2时因摆动权重仍为0，误改了抬脚首个控制样本。af用landing_feedback仅在phase≥5混合，seed512/env23的98个落脚前抽样状态与ac逐值相同，但完整单步仍26/32、25/32，后一批新增1次安全失败，拒绝将混合作为候选。保留边界修复，开关继续默认关闭。

旧控制用一次局部雅可比线性近似从足位得到关节参考，参考足端几何误差最高6.252cm。这会在较大重心位移时产生多余屈曲和跟踪偏差。新增crawl_leg_kinematics.py读取实际Isaac组合USD中的四腿关节坐标、轴和尺寸，以解析逆运动学计算名义参考；仍保留原闭环、质心制动、承重补偿、关节限位与相对捕获姿态±.7rad包络。没有运行MuJoCo仿真。

离线重建ac的1320个实际Isaac足位，最大误差1.80微米；ag/ah实际每步也校验，超过.5mm立即报错。ag原线性基线全部32原终态、步态/运动、资产/延迟逐值复现aa。单变量替换为解析参考后，seed512严格单步由31/32变32/32，落地后最大足部位移由17.75cm降为1.42mm，机身位移由8.97cm降为7.85mm。ah固定同一控制在已用seed513交叉检查也32/32，最大落地足部位移4.34mm、机身1.72cm。两组均末段安静32/32、零安全终止、无未完成。

解析求解不代表目标完全可达：受±.7rad包络限制，ag名义足位残差仍最高2.783cm；不能把解析IK写成零误差。两组均是平地左前脚单步诊断，seed512/513已经用于调参，**20cm CLIMB仍全部0/32，未达到完整慢爬验收**。

### 普通待机仍需改进进入过程

新增idle-only保持默认关节站姿，不开始重心转移；climb-start-s可延迟开始预备（默认2秒）。ah/idle512独立32回合均完整，均末段连续5秒安静、零安全失败。第2秒至24秒四脚始终接触；该段最大竖直速度.0359m/s、足部峰值102.26N。但完整22秒统计仍有最大机身位移7.82cm、足位移8.57mm，不能称为全程位置保持通过。末段连续安静实际为14.46–19.02秒。

idle阶段未启用攀爬足位/机身参考，报告中的target_error仍相对初始化保存坐标，仅供原始遥测，不作为待机目标误差；三角支撑裕量按预留抬起左前脚的三脚计算，也不是四脚站姿稳定性门槛。待机质量以四脚接触、完整段漂移、姿态与速度判断。该诊断**未调用NAV actor**，不得说已完成NAV停车接入。

NAV停车已有独立任务验证；普通站立不应作为每次CLIMB重训的新技能。下一步优先保持NAV原生观测历史、动作顺序、PD与延迟契约，验证停车→停稳等待→平滑进入攀爬预备的交接。此前b直接把NAV投影进crawl接口0/32，不能重复未经验证的直接接线。启动条件需看实测支撑/速度及持续停稳，不能仅经过2秒和四脚接触就视作停稳；多腿/低台/20cm在此前提后推进。

### 全回合统计（24秒诊断，保留初始化峰值）

| 实验/批次 | 完成/未完成 | 严格单步/32 | 末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae/step512 | 32/0 | 24 | 25 | 0 | 99.880 | 0.060 | 0.902 | 204.383 | 0.280 |
| ae/step513 | 32/0 | 24 | 25 | 0 | 99.762 | 0.060 | 0.951 | 203.635 | 0.280 |
| af/step512 | 32/0 | 26 | 28 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| af/step513 | 32/0 | 25 | 25 | 1 | 99.625 | 0.060 | 0.951 | 203.635 | 0.340 |
| ag/analytic | 32/0 | 32 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| ag/baseline | 32/0 | 31 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| ah/cross513 | 32/0 | 32 | 32 | 0 | 99.822 | 0.060 | 0.951 | 203.635 | 0.280 |
| ah/idle512 | 32/0 | — | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |

所有CLIMB成功0/32。静止行单步不适用；峰值含失败及初始化，力矩饱和为98%阈值最大单关节累计时间。此处仍有初始化.06秒腾空和约.90/.95m/s竖直峰值，未给出电机热安全结论；不能用末段平静或单步成功替代完整登台与真实动作质量验收。

### 来源与录像

本地仓库外及远程/path/to/artifacts/go2-piper/同名目录：climb-support-wrenchstance-20261001-ae、climb-support-landingguard-20261001-af、climb-support-analyticpose-20261001-ag、climb-support-idle-cross-20261001-ah、climb-support-idlereview-20261001-ai。报告/源码快照/启动记录/实际配置均独立保存，不覆盖冻结策略。控制源码SHA-256：`1db1c47b74d29e14b6560c373f9704a3b35962a92128c4fec5e6626b3959f3c7`。默认仍为linear，analytic仅在上述诊断显式启用。

ai两段远程录像已完成，均为seed512/env23、24秒/600帧/25fps/1280×720真实速度。普通待机全部32原终态、步态/运动、保持、资产/延迟逐项匹配ah/idle512；单步对应ag/analytic全部32原字段与原有保持阶段匹配，新增idle遥测不影响复现。视频/报告SHA及元数据保存在ai/verification.json。已检查2/5/7/10/18/23秒关键帧与数值轨迹，尚未凭关键帧将连续动作自然性判定为通过。检查页`index.html`明确区分普通待机和预备/单步；旧8771保留。

四份d任务源码仍匹配冻结计划，44份实际任务Python及实际YAML哈希已保存各目录task-source-verification.json。12项纯数学检查、Python编译与git diff检查通过。ae–ai进程全部结束，本项目没有训练/评估/录像运行；未干预共享服务器其他作业。下一轮先解决停车到攀爬预备的进入条件和过渡，不重复运行已完成实验。

<a id="record-0156"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 实测停稳后再启动的对照 aj–ak（最新，未替代ag/ah）

远程Isaac新增默认关闭的start-stable-s诊断：第2秒之后，连续.5秒满足四脚接触、线速度<.025m/s、角速度<.1rad/s、线加速度<.5m/s²、角加速度<1rad/s²、重力投影z<-.98，才捕获当前站姿并开始原3秒重心转移。速度低但加速度较大的摇摆转向点不能触发。保持原20cm箱、24秒时限、停稳/碰撞/执行器门禁、PD30/.6、0–4物理步延迟及原关节参考限速；没有NAV actor接入，也没有训练。

aj先在已用seed513做关闭/开启配对。关闭版本全部32原终态、步态/关节/完整保持指标、资产及延迟逐值复现ah/cross513，说明诊断默认关闭不改旧行为。开启仍32/32严格单步、32/32末段安静、零安全终止；各环境开始时间从固定2秒变为3.28–7.00秒。env0原来在速度.166m/s时启动，新版到6.52秒才启动（6.60秒抽样速度.0204m/s）。转移完成后保持段最大角速度由.409降为.0183rad/s，落脚足位移由4.34降为2.62mm。第2秒后支撑比例100%、无腾空、竖直峰值.0768m/s、足力111.70N；完整统计仍保留初始化峰值。

**ak在已用seed512交叉检查发现退化，因此不采用为新基线。** 严格单步由ag的32/32降为30/32，末段安静31/32、零安全终止，32回合均完整。env11在5.68秒通过待机门槛后，进入重心转移却持续摇晃，最终角速度.814rad/s，卡在phase1未抬脚；env27四脚接地且速度很低，但最终机身倾斜11.83°（gravity z=-.97874）不满足新增启动姿态门槛，整回合留在phase0。两者均为任务失败，不能将安全阻止抬脚或更低冲击计为成功。

剩余30个完成单步的环境落脚阶段最大足位移2.06mm、机身位移7.84mm，此为完成者子集，不能掩盖两个失败。默认站姿从第2秒起最大机身漂移仍为7.82cm（512）/8.04cm（513）；新增等待没有修复普通站姿收敛过程，只改变了接管时刻。末段安静的宽姿态门槛与开始抬脚所需更严格姿态不同，这也解释“能静止但不能直接抬脚”；不放宽门槛。

| 批次 | 完成/未完成 | 严格单步/32 | 末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aj/baseline513 | 32/0 | 32 | 32 | 0 | 99.822 | 0.060 | 0.951 | 203.635 | 0.280 |
| aj/wait513 | 32/0 | 32 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| ak/wait512 | 32/0 | 30 | 31 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| ak/wait513 | 32/0 | 32 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

全部20cm CLIMB为0/32。ak/wait513为aj同32回合录像复现，不增加独立样本；ak/wait512是另一已用诊断种子，不是未见验收。饱和为98%阈值最大单关节累计时长，未做电机热安全结论。

ak两段视频均24秒/600帧/25fps/1280×720，seed512/env23与seed513/env0。已检查2/5/8/12/18/23秒关键帧，均为成功样本，页面明确不能代表env11/27失败已修复。seed513全部32终态/指标/保持/资产/延迟匹配aj；seed512为新诊断，只有来源/回合完整性/视频格式核验，未伪称独立复现。入口`index.html`，旧8772仍为ag/ah。

本地仓库外和远程/path/to/artifacts/go2-piper/同名目录climb-support-startwait-20261001-aj、climb-support-startreview-20261001-ak已保存源码、计划、报告、实际YAML、日志、视频与SHA校验；ak/failures.json记录两例失败，aj/verification.json核验默认关闭回归。控制SHA：`e568101722131e862e9ad36c8ceb4cffad66ca849834957df17f26b7feaf7408`。四份d任务源码保持冻结，44份实际Python和YAML哈希已核验。13项纯数学检查、Python编译、diff检查通过。本轮进程均结束，无本项目训练/评估/录像运行。

下一步保留ag/ah作为平地单步对照，aj/ak仅用于失败诊断。优先检查env11从已停稳站姿切入负载补偿/反馈时的参考连续性和全身姿态响应；同时按原NAV历史/动作契约准备真实停车接口，不能用重复当前帧替代三帧历史。env27需修正待机姿态/进入参考而非放宽启动倾角；不要重复“仅增加等待时间”试验，不延长24秒掩盖停滞。完成交接后才继续多腿/低台/20cm。

<a id="record-0157"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 接管参考连续性 al–am（最新，局部修复，尚未采用完整候选）

针对ak/seed512/env11“停稳后进入重心转移反而持续摇晃”，新增原始目标与接管首帧目标跳变量遥测。al关闭新开关时全部32原终态及步态/关节/保持/资产/延迟逐项匹配ak/wait512。原控制接管瞬间原始关节目标最大跳变.29456rad，env11为.21544rad；这是送入既有关节限速器之前的请求跳变，不能说真实关节瞬间跳了该角度。

新增默认关闭takeover-s，开启.5秒时，从捕获的实际执行参考出发，以五次平滑插值逐步接入完整支撑控制目标；原PD、0–4物理步延迟、关节q/v/a限幅、支撑门禁、.5秒实际停稳启动门槛全部不改。不是冻结补偿或对补偿持续低通，.5秒后完整支撑控制恢复。原始目标跳变仍记录，首帧请求跳变降为0。

**al的seed512/env11已从转移超时变为严格单步成功，末段连续安静10.02秒。** 接管后相同最初3秒抽样窗口（0.2秒采样），角速度峰值由.937降至.0286rad/s。整批严格单步30/32→31/32、末段安静31/32→32/32、零安全终止；最大转移完成后保持角速度1.109→.00858rad/s，但两组保持时长不同，该阶段峰值不单独作为全程改善依据。默认待机漂移未被修复。

seed512/env27仍因待机倾角11.83°不启动；原始历史显示四脚均接地，前脚法向载荷约26.34/28.49N，后脚90.70/88.62N，后小腿目标-1.5rad而实际约-2.17/-2.16rad、力矩20.09/19.65Nm。说明默认关节目标在此落脚/承重状态下形成明显受载偏差；不能将单纯低速度当成合格待机姿态，未放宽启动倾角。

**am固定.5秒接管，在已用seed513交叉检查为31/32，较aj/wait513的32/32退化。** env11在phase4已四脚接地且最终安静，但左前脚误差2.658cm超过原2.5cm门槛（x=-2.049cm、y=1.694cm），保留失败；名义足位几何残差2.476cm，提示检查参考±.7rad包络约束和可达性。两批均没有安全终止和未完成回合。不能因为修复一例持续摇晃，就将新控制作为完整可靠方案；ag/ah仍保留原平地对照，al/am只保留为已验证诊断路径。

| 批次 | 完成/未完成 | 严格单步/32 | 末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| al/baseline512 | 32/0 | 30 | 31 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| al/ramp512 | 32/0 | 31 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| am/ramp512 | 32/0 | 31 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| am/ramp513 | 32/0 | 31 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

完整回合峰值保留初始化，饱和为98%阈值最大单关节累计时长；所有20cm CLIMB仍0/32，均为独立24秒慢爬诊断，非原12秒或未见种子验收。am/ramp512为al同32回合原速录像复现，不增加样本；seed512/513早已用于调参。

am视频为seed512/env11（已修复的摇晃例）及seed513/env0（成功样本），均24秒/600帧/25fps/1280×720。512全部32终态、步态/关节/保持/资产/延迟逐项匹配al；513为新交叉诊断，不伪称单独复现。已检查2/5/7/10/18/23秒关键帧，未凭关键帧判定完整自然慢爬通过；页`index.html`明确标注两批各1失败，旧8773保留。

本地仓库外及远程/path/to/artifacts/go2-piper/目录climb-support-takeover-20261001-al、climb-support-takeoverreview-20261001-am保存计划/源码/报告/实际YAML/日志/视频及SHA。al/baseline-verification.json验证回归，takeover-analysis.json记录接管量及env27关节承重，am/failure513-analysis.json记录落脚缺口，verification.json记录视频。控制SHA为`3ed22c44d3fa3cb53906398e7296c058c01530b141d060e057f4e269b2422653`；四份d任务源码仍匹配冻结计划，44份实际任务Python及配置哈希核验通过。13项现有纯数学检查、Python编译、diff检查通过。

本轮全部进程结束，无本项目训练/评估/录像运行。开始时其他项目占用GPU0，因此al在GPU1顺序运行；其他作业自然结束后才在两GPU录制am，未干预共享作业。PUSH、MuJoCo、实机仍暂停。

下一步：保留接管连续性的因果证据；优先把普通待机从固定无负载关节目标恢复为匹配NAV契约的站立/停车行为，并验证真实三帧历史和交接，不宣称当前已集成NAV。落脚参考需在原限位/包络内检查可达性，调整身体/足位参考而非放宽2.5cm门槛。以env27受载倾斜和seed513/env11不可达残差为具体诊断，避免只扫等待时间、插值时间或无效追加PPO。

<a id="record-0158"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 原生NAV观测/历史接入与受限动作兼容性 an–ao（最新，拒绝直接接管）

本轮落实NAV接口验证，没有再将当前帧重复3次投影到210维。新增可选nav-policy，仅允许idle-only，防止未经验证直接接入攀爬。加载冻结actor（SHA72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8），复制GO2-PIPER-Flat原生观测组，由Isaac观测管理器维护真实3帧历史。保留原term顺序、缩放、关节默认偏置、输出关节顺序和.25动作scale；原生请求clip±10。速度命令为0，机械臂命令(.5,0,.1)+单位四元数，采用既有native-flat-lower16验证过的位置值，但该历史报告原速度为.25m/s，不能冒充本次零速验收。

实验仍使用原crawl的20cm箱、24秒、全部安全终止、PD/延迟、执行器限幅和关节参考速度/加速度限制；**它是NAV迁移到crawl动作接口的兼容性试验，不是NAV原生任务验收**。没有改动冻结actor、放开限速、关闭接触门禁，也没有进行NAV→CLIMB切换。

an/observe512只增加原生观测和命令，继续默认站姿，全部32原终态、步态/运动、完整保持、资产和延迟逐值复现ah/idle512。表明新增观测本身没有改变该批物理轨迹。随后an/nav512在2秒后执行NAV：32/32安全失败，19次底座接触、13次姿态失败；回合结束2.58–4.40秒，末段安静0/32，拒绝接管。

真实历史已逐项核验：对inspect env27的99–103步，每项3帧缓存逐步左移；actions历史最新帧严格等于上一控制步实际送入动作管理器的请求。七项顺序为base_ang_vel、projected_gravity、joint_pos、joint_vel、actions、velocity_commands、pos_commands，维度3/3/18/18/18/3/7，各3帧共210。ao进一步核验实际default_joint_positions逐值匹配冻结native-flat-reference16。没有以张量维度正确代替历史/默认偏置/动作顺序校验。

请求与实际执行参考之间存在明显差异：an/env27接管首帧最大归一化请求5.90（某关节原始目标偏移1.475rad）；其中后左小腿原始目标-.7268rad、实际受限目标-1.4940rad，差.7672rad，下一步差.9276rad。此数据来自原始动作与下一物理采样的实际目标匹配，包含限速/加速度/位置限制影响；尚未将全部失败唯一归因于某一限制，也不能说真实关节跳变1.475rad。

ao固定原生观测与限制，增加.5秒五次平滑NAV接管，历史使用实际混合后的动作。首帧请求归零、初始跟踪差消除，但仍32/32安全失败（22底座接触、10姿态），结束3.08–5.84秒，末段安静0/32。峰值足力虽下降，但任务仍失败，不计为改善完成；拒绝采用，不继续扫描接管时间。NAV在原部署接口能停车，不意味着放入不同的参考执行链后自动保留稳定性；本轮结果也不否定其原接口历史能力。

| 批次 | 完成/未完成 | 末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| an/nav512 | 32/0 | 0 | 32 | 87.953 | 0.060 | 0.962 | 1812.279 | 0.600 |
| an/observe512 | 32/0 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| ao/navramp512 | 32/0 | 0 | 32 | 89.365 | 0.060 | 1.072 | 1033.975 | 0.600 |

所有20cm CLIMB成功为0/32，单步不适用；安全失败也属于完整终止回合，不隐藏短回合。支撑为回合等权，峰值覆盖所有回合，初始化保留；饱和为98%阈值最大单关节累计时长。没有实机或电机热安全结论。未为失败迁移版本新增展示录像，原8774仍是al/am，不能误认为NAV新版本。

本地仓库外及远程/path/to/artifacts/go2-piper/同名目录climb-support-navidle-20261001-an、climb-support-navramp-20261001-ao保存源码、冻结actor副本、计划、实际YAML、日志、报告、comparison.json、verification.json、reference-tracking-audit.json。四份d任务源码保持冻结；44份任务Python和实际YAML哈希保存于task-source-verification.json。最新诊断脚本SHA：`9b19ba45c112f57ff4ec7efd249af58bf315223229ff5f51b0f74c8519fb5eae`；crawl_support.py仍为al/am SHA3ed22c44d3fa3cb53906398e7296c058c01530b141d060e057f4e269b2422653。13项原有数学检查、Python编译和diff检查通过，NAV接口主要由实际远程历史和默认偏置核验覆盖。

an/ao均已结束，无本项目训练/评估/录像运行；使用GPU1顺序执行，没有干预GPU0其他项目。新NAV路径仅为可选诊断，不替换ag/ah或al/am。PUSH、MuJoCo和实机仍暂停。

下一步不再直接把原NAV输出接入crawl参考限速器，也不重复早期错误历史投影。需要在保持既定安全限制下建立匹配的受载站立/停车参考与执行接口，优先解决env27后腿过度承重的姿态偏差；可保留原NAV作为独立能力对照，但不得承诺未经验证的直接复用。并行的几何问题仍为am/seed513/env11落脚2.658cm误差，应在原关节包络内调整身体/足位参考，不放宽2.5cm门槛、不把低冲击失败当进展完成，不延长无效PPO。

<a id="record-0159"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 受载站姿水平恢复 ap–ar（最新，仅站立诊断）

针对默认待机后腿受载下沉、env27倾斜11.83°的问题，新增默认关闭level-stance。在原解析足位IK与支撑/重力补偿之上，固定已接触足位、捕获的机身位置和朝向，用3秒五次平滑过程恢复水平机身；支撑接管仍为.5秒。该开关只允许不转移重心、不抬脚的静态诊断。保留原PD30/.6、0–4物理步延迟、关节q/v/a限制、捕获姿态±.7rad包络、20cm箱与所有安全终止。未接入NAV、未训练PPO、未实现站立到单步的交接。

ap首先在已用seed512固定8秒开始，对比仅承重支撑与额外水平恢复：两者均32/32末段安静、零安全终止；最大最终机身倾角11.843°→.773°，严格启动倾角通过31/32→32/32。说明单纯低速度并不能修复受载姿态，而匹配足位几何的机身姿态参考可以改善这一缺口。ap仍保留2–8秒默认待机的7.82cm漂移，不能称为全程站稳。

aq将同一恢复提前到2秒，在已用seed512/513各32回合做原速录像；ar仅增加完整准备段遥测，全部64原终态字段、原保持阶段、步态/运动、资产与延迟逐值复现aq。两组均完整、零安全终止，最终32/32满足严格启动倾角，最大最终倾角.775°/.559°，所有环境末段连续安静至少19.02秒。

**恢复后的保持已明显稳定，但接管过程仍有移动，不能称为整个待机已完全修复。** ar从2秒接管至24秒，全部64回合持续四脚接触。全22秒最大机身位移为2.833/4.232cm、最大足位移3.698/5.016mm、最大线速度.1281/.2113m/s、最大角速度.1826/.2432rad/s。第5秒水平参考完成之后，19秒保持段最大机身位移仅.577/1.531mm、足位移.083/.188mm、最大角速度.00609/.00705rad/s。后者是明确的保持区间，不能替代全22秒指标。

静态模式未执行三足支撑转移，遥测中的support_margin仍是去掉左前足的三角形裕度，可以为负；四脚稳定不能作为允许抬脚的证据。下一步仍需真实停稳门槛和支撑转移，不能从“最终水平”直接跳到单步成功。

| 批次 | 完成/未完成 | 完整20cm CLIMB成功/32 | 末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ap/loaded512，8秒接入 | 32/0 | 0 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| ap/level512，8秒接入 | 32/0 | 0 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| aq与ar/level512，2秒接入 | 32/0 | 0 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| aq与ar/level513，2秒接入 | 32/0 | 0 | 32 | 0 | 99.827 | .060 | .951 | 203.635 | .280 |

表中保留初始化峰值，饱和是98%阈值最大单关节累计时长。aq/ar在2秒之后均100%≥三足支撑、无腾空，最大竖直速度.0484/.0719m/s、足力峰值102.619/99.410N。四脚接触由完整preparation遥测另外核验。没有电机温升或实机安全结论。全部回合以24秒超时终止，单步不适用，20cm攀爬仍0/32；这些静态诊断不是原12秒验收，512/513不是未见种子，录像复现不增加独立样本。

aq视频为512/env27（原承重倾斜样本）与513/env11（本次只检查站立，不代表先前落脚误差已修复），均24秒/600帧/25fps/1280×720，入口`index.html`。已检查0/2/3/4/5/23秒关键帧；最初相机帧黑屏，未剪去初始化。关键帧及数值检查不替代连续动作自然性的最终验收。旧8774继续保留al/am单步版本。

本地仓库外及远程/path/to/artifacts/go2-piper/同名目录climb-support-levelstance-20261001-ap、climb-support-levelreview-20261001-aq、climb-support-levelmetrics-20261001-ar保存计划、源码、实际YAML、完整报告/日志；aq另有视频，ar/level-analysis.json核验全64回合复现与倾角/接触，comparison.json记录完整准备/保持统计。task-source-verification.json核验四份d任务源码未变并记录44份Python和实际配置哈希。控制SHA：45fe6e4c471e05110418daaab3817494a370d1433d99649bb7948194d78a311d；ar诊断脚本SHA：3402a989ef5a59419fd7da01ec5f26a57cbfd6538fde135c6d3e40b7fa5fade1。14项数学检查、Python编译和diff检查通过。

ap/aq/ar进程全部结束，无本项目训练/评估/录像运行。没有重复启动旧实验或干预其他作业。PUSH、MuJoCo及实机仍暂停。

下一步：在已有受载水平恢复后，通过实际四脚接触、速度、角速度、加速度和严格倾角的连续.5秒门槛，再捕获受载姿态并平滑进入原重心转移与单步。全流程保持24秒，新增预备时段不得隐藏超时；先在已用种子检查完整单步及全段冲击，再考虑多腿/低台/20cm。特别复查513/env11在原±.7rad包络内的可达性，不能放宽2.5cm落脚门槛。ag/ah仍是原平地单步对照，ap–ar没有替代它。

<a id="record-0160"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 受载站稳到单步的真实交接 as–au（最新，尚有落脚缺口）

新增默认关闭level-before-step：2秒起执行上一版3秒受载水平恢复，然后连续.5秒满足四脚接触、线速度<.025m/s、角速度<.1rad/s、线加速度<.5m/s²、角加速度<1rad/s²、gravity z<-.98，才重新捕获实际受载机身/足位/关节参考，平滑接入原3秒支撑转移。准备期间禁止抬脚；转移之后仍需原真实三足支撑裕度≥1.5cm等门禁，才允许原5cm抬脚、8cm前移、下降和落脚等待。两次接管都从实际执行参考开始，采用.5秒平滑。物理关节限位、q/v/a、PD30/.6、0–4物理步延迟、20cm箱及原安全终止不变；名义±.7rad包络仍围绕该阶段重新捕获的受载关节姿态计算，没有扩大包络。

as/baseline512关闭新选项，全部32原终态、步态/运动、全部原保持阶段、资产/延迟逐值复现ar/level512。as/step512随后为32/32严格单步、32/32末段安静、零安全终止。at在同一配置完成512原速录像复现，所有32终态/指标逐值相同；固定配置后在已用513做交叉检查，为31/32严格单步、32/32末段安静、零安全终止。两批全部64回合完整且24秒结束，均在5.5秒通过实测门槛进入重心转移，两次首帧请求跳变均为0。不是仅按固定5.5秒强制启动：每环境保留实际连续停稳计数和门槛值并逐项核验。

之前512/env27因承重倾斜不启动，本次完成单步，最终足位误差3.31mm；之前513/env11落脚超差，本次误差1.677cm，通过原2.5cm门槛。**但出现513/env5新失败：最终足误差2.54466cm、名义几何残差2.13513cm，phase4等待至24秒。** 即便最终已安静10.32秒，仍记单步失败；没有放宽阈值。还不能说所有单步可达性问题已经解决。

**落脚全过程仍有质量缺口。** 512落脚阶段最大角速度.641rad/s（env14）、最大机身位移2.841cm（env16）、足位移4.369mm；513已进入落脚保持的31个环境最大角速度.497rad/s、机身位移1.571cm、足位移9.632mm，该子集不包含phase4的失败env5。env14在约13.6秒前脚接触后发生承重变化，13.8秒抽样角速度.522rad/s，名义几何残差约2.184cm，之后才安静。计数和末段稳定不能代表整个动作平缓，不批准多腿登台或实机。

au用已有最短支撑转移选项做单变量诊断：沿同一重心射线只达到计划3cm裕度，保留实际1.5cm抬脚门槛与8cm落点，尝试降低前脚伸展需求。**结果明显退化，拒绝采用**：严格单步22/32、21/32，新增3/6次bad_orientation；两批各10个停在抬脚phase2，后者还有1个phase5未通过完整验证。513峰值足力升至551.41N、单关节累计饱和.44秒。说明缩短重心转移、名义裕度为正不足以保证动态承重稳定，不继续盲扫裕度阈值，也不以低冲击部分样本作改善依据。原centroid设置保留。

| 批次 | 完成/未完成 | 完整20cm CLIMB成功/32 | 严格单步/32 | 单步且末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| as/baseline512静态 | 32/0 | 0 | 不适用 | 不适用 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| as与at/step512 | 32/0 | 0 | 32 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| at/step513 | 32/0 | 0 | 31 | 31 | 0 | 99.825 | .060 | .951 | 203.635 | .280 |
| au/step512，拒绝 | 32/0 | 0 | 22 | 20 | 3 | 98.789 | .060 | .902 | 204.383 | .280 |
| au/step513，拒绝 | 32/0 | 0 | 21 | 21 | 6 | 98.801 | .060 | .951 | 551.410 | .440 |

完整统计遵循已有前.10秒排除规则，保留其余初始化峰值，饱和为98%阈值最大单关节累计时长。at在2秒之后≥三足支撑100%/99.997%、无腾空、竖直速度峰值.0964/.0838m/s、足力115.705/120.076N。24秒慢爬诊断不冒充原12秒；512/513已用于开发，不是未见验收；at/512是复现，不增加独立样本。没有电机热安全结论。

at两段原速视频为512/env14（最大落脚摇摆样本）和513/env11（旧失败本次恢复），24秒/600帧/25fps/1280×720。入口`index.html`，明确保留31/32与落脚摇摆缺口、au拒绝结论；旧8775是仅站立。已检查2/5/8/10/12/14/16/23秒关键帧与13秒附近数值轨迹，没有凭关键帧声称连续自然性验收通过；当前视频不展示513/env5，不能用env11成功掩盖它。

本地仓库外及远程/path/to/artifacts/go2-piper/同名目录climb-support-preparedstep-20261001-as、climb-support-preparedreview-20261001-at、climb-support-preparedmargin-20261001-au保存计划、源码、实际YAML、报告/日志/分析；at另有录像、verification.json与页面。prepared-analysis.json核验交接门槛、失败与基线；终态preparation_gate八项依次为连续停稳秒数、线速度、角速度、线加速度、角加速度、重力z、接触脚数、水平恢复计时。task-source-verification.json确认四份d任务源码未变并记录44份Python及实际YAML哈希。

控制SHA：ef332453aa4e7584f4c8eece820ab3a4fd00ae74b7f1896606ec18ba0a421331；诊断SHA：8b46b8c872ef953c6d62d586549108418fef10a243d2f1746b54d18dee4da393。14项现有数学检查、Python编译、diff检查通过；新增阶段交接以实际远程64回合门槛值及关闭选项基线复现核验。全部as/at/au进程结束，无本项目训练/评估/录像运行；PUSH、MuJoCo、实机继续暂停。

下一步保留as/at的真实站稳交接，优先补齐全部环境在交接时的精确捕获关节/足位/机身状态，联合检查整个8cm摆动路径的解析IK、原±.7rad包络和实际承重裕度。目标是在保持足够支撑的同时规划可达身体/脚路径；不能只缩短支撑转移、放宽2.5cm落脚门槛，或冻结落脚摇摆中的参考。尤其复查513/env5的几何残差和512/env14的承重切换。解决完整单步与落脚质量后再推进逐腿、多步及20cm，不追加无效PPO。

<a id="record-0161"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 用户指出抬脚晃动：外层脚速反馈对照 av–ax（最新，主要振荡减弱，仍有一例残余）

用户明确指出8776视频中抬起的脚明显晃动。核对at的目标和实际轨迹：横向目标不动，实际足位反复变化；前移阶段名义IK残差接近零，不能统一归因于之前落脚不可达问题。原检查重视最终落脚/站稳，对空中足部往复不足。本轮增加SwingQuality，对phase2–4且摆动脚未接触（沿用2N阈值）记录横向/各轴误差范围、足速峰值、最大跟踪误差、实际/目标路程和误差变化累计路程，全部环境统计；inspect轨迹从0.2秒改为可选每控制周期0.02秒，避免低频采样掩盖往复。

定位到外层脚速项：原摆动反馈为足位误差减去0.1秒×测得脚速，再映射为关节位置目标，后面仍经过关节参考限制、执行器PD和0–4步延迟。它意在阻尼，但在当前执行链中加剧反复反向纠偏。新增swing-damping-s，默认仍.1以复现旧版本；候选显式设0。**只移除这一项外层速度纠偏，物理PD30/.6、延迟、q/v/a、支撑/几何轨迹、受限积分、20cm箱及所有门禁不变。** 这是控制器诊断与修正，没有新PPO训练。没有通过放开限速或减小底层电机阻尼来改善视频。

av/seed512按.1与0配对；默认.1全部32旧终态、步态/运动/保持、资产/延迟逐值复现at/step512。ax/seed513补齐相同配对，默认.1同样完整复现at/step513。新遥测和密集记录未改变这两批原轨迹。两组修正后均32/32严格单步、32/32末段安静、零安全终止；旧513/env5的2.54466cm落脚失败本次通过原门槛，没有放宽阈值。

| 种子与版本 | 最大空中横向误差范围cm | 中位横向范围cm | 最大足速m/s | 中位误差变化路程m | 最大误差变化路程m |
| --- | --- | --- | --- | --- | --- |
| 512原.1 | 3.942 | 2.094 | .770 | .822 | 1.431 |
| 512修正0 | 1.202 | .941 | .176 | .069 | .123 |
| 513原.1 | 4.116 | 2.579 | .805 | .978 | 1.292 |
| 513修正0 | 1.901 | .951 | .501 | .074 | .711 |

这些范围包含离地、前移和落地过渡，不等于纯周期振幅；误差变化路程是在连续未接触样本上累计实际位移减目标位移的模长，接触断开时不跨段连接。各环境采样数/实际路程/目标路程均保留，不以较短空中时长伪装平滑。

同一512/env14，原版空中实际路程1.273m、目标.138m；修正后实际.221m、目标.139m。只比较同样1.72秒的phase3前移段，横向误差范围3.230→.528cm，脚横向速度超过.02m/s的反向次数12→0；两者名义IK残差峰值同为.138mm。这提供了外层速度反馈放大振荡的直接配对证据，但没有单独拆分延迟、限速、姿态和各关节动力学的因果贡献。

落脚阶段512最大机身角速度.641→.0261rad/s，机身位移2.841→.196cm、足位移4.369→.281mm；513修正后最大角速度.1826rad/s，机身位移.325cm、足位移.718mm。不能将最后站稳当作整个动作自然。

**残余问题明确保留：513/env3仍有空中晃动。** 腿部延迟4个物理步，但其他同延迟环境已显著改善，不能唯一归咎于延迟。修正后该环境空中实际路程.734m（目标.131m）、足速峰值.501m/s、误差变化路程.711m；phase3仍7次超过.02m/s的横向反向，原版14次，名义几何残差峰值两者均6.964mm。它最后虽通过单步和停稳，仍不属于自然平缓已达标。ax为此单独录制env3，未只展示env14/11的改善样本。

| 批次 | 完成/未完成 | 20cm CLIMB成功/32 | 严格单步且末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| av/baseline512，原.1 | 32/0 | 0 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| av与aw/nod512，修正0 | 32/0 | 0 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |
| ax/baseline513，原.1 | 32/0 | 0 | 31 | 0 | 99.825 | .060 | .951 | 203.635 | .280 |
| aw与ax/nod513，修正0 | 32/0 | 0 | 32 | 0 | 99.817 | .060 | .951 | 203.635 | .280 |

完整统计沿用前.10秒排除，保留其余初始化；饱和为98%阈值最大单关节累计时长。修正后2秒起，512/513≥三足支撑100%/99.989%，无腾空，竖直速度峰值.0484/.0719m/s、足力117.134/121.311N。没有电机温升或实机安全结论。全部是独立24秒平地单步诊断；20cm仍0/32，不冒充原12秒或最终未见种子验收。512/513均已用于开发，录像复现不增加样本。

新页`index.html`提供同一512/env14原版与修正版1×同步对照、修正513/env11及残余513/env3。aw两段及ax残余视频均24秒/600帧/25fps/1280×720。aw/512的32终态、步态/运动/完整保持/空中足部/资产/延迟匹配av；ax/513逐值匹配aw。已核对关键帧与50Hz轨迹，没有用稀疏关键帧宣布连续自然性验收通过。旧8776继续保留原版本。

本地仓库外及远程/path/to/artifacts/go2-piper/同名目录climb-support-swingvelocity-20261001-av、climb-support-swingreview-20261001-aw、climb-support-swingresidual-20261001-ax保留源码/计划/实际YAML/报告/日志/视频及SHA。swing-analysis.json记录全部环境指标/失败；av/swing-env14-translation.json与ax/residual-phase3-analysis.json记录相位分析；verification.json核验视频与完整复现。四份d任务源码仍未改，44份任务Python及实际配置哈希已保存。

控制SHA：a541c9c1b85661df56b4fb0da6194a3c8cb061cbe414b114cb79c8646b05ffe6；诊断SHA：f8d39e4144b9ffbe79883cb511827347c4343245534166191f8cbb19151670c3。14项现有数学检查、Python编译和diff检查通过；遥测与默认行为由实际两组配对复现核验。全部av/aw/ax进程结束，无本项目训练/评估/录像运行。

下一步固定显式swing-damping-s=0作为进一步诊断起点，优先检查513/env3的实际执行参考/关节响应与名义包络残差，区分离地卸载、位置纠偏与几何约束的作用；不能仅凭两组32/32继续多腿登台。继续保留空中足部与全保持指标，再完善逐脚动作、低台与20cm。PUSH、MuJoCo、实机仍暂停。

<a id="record-0162"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 残余摆动的位置反馈对照 ay–az（最新，仍保留离地滞后缺口）

固定上一版swing-damping-s=0，检查513/env3的50Hz原始记录：10.0–10.6秒名义IK残差接近零时，左前小腿关节请求已反复反向，不能把这一段都归因于后续6.964mm名义几何残差。按实际动作与机器人关节顺序映射核对：FL在动作数组索引3/4/5，在机器人数组索引0/4/9；不能把command_target前3项（FR）与FL实际关节误配。本轮增加明确的action_joint_names、名义腿关节顺序、捕获关节参考，以及inspect实际关节速度/力矩，便于后续重建；没有改变观测或控制关节顺序。

ay只将既有外层swing-feedback从1改为.5，受限积分仍.5/s，脚速项保持0。物理PD30/.6、延迟0–4物理步、q/v/a、名义±.7rad包络、重心转移/8cm落点、20cm箱、24秒及所有安全/成功门槛不变。诊断脚本默认仍1/.1，当前实验需显式给出`--swing-feedback .5 --swing-damping-s 0 --level-before-step --start-stable-s .5 --takeover-s .5`，其余参数见az计划/启动脚本；未替换冻结策略或新训PPO。

ay/baseline513保持位置系数1，全部32原终态、步态/关节/全部保持/空中足部/资产/延迟逐值复现ax/nod513，确认新增遥测不改旧行为。half513仍32/32严格单步且末段安静、零安全终止。固定.5后，az在已用512交叉检查也32/32；az/513原速录像全部32终态和指标逐值匹配ay。两组64回合均完整、24秒结束，20cm成功仍0/32。

**原残余env3的反复摆动进一步降低。** 空中足速峰值.501→.169m/s、实际路程.734→.196m（目标.131/.134m）、误差变化路程.711→.089m。phase3前移段时长1.74/1.72秒，横向误差范围1.830→.536cm，速度超过.02m/s的横向反向7→0次。小腿关节位置纠偏加积分的请求变化范围.269→.0231rad，请求与上一实际执行参考差的峰值.268→.00631rad；后者包含控制步与执行延迟，不是物理关节瞬时跳变。名义几何残差两者仍6.964mm，相对±.7rad包络接触样本仍27/26个，不能说名义可达性已修复。

| 版本/种子 | 最大空中横向范围cm | 中位横向范围cm | 最大足速m/s | 最大跟踪误差cm | 中位误差变化路程m | 最大误差变化路程m |
| --- | --- | --- | --- | --- | --- | --- |
| ay原位置反馈1 / 513 | 1.901 | .951 | .501 | 4.134 | .074 | .711 |
| ay与az位置反馈.5 / 513 | 1.320 | 1.029 | .173 | 4.385 | .077 | .089 |
| az位置反馈.5 / 512 | 1.234 | 1.022 | .170 | 4.305 | .076 | .087 |

最大往复显著减少，但不能说所有指标都下降：513中位横向范围与中位误差路程略增，最大跟踪误差也略增。离地时足位仍落后目标；inspect513/env3在9.76秒目标足高约6.59cm、实际约2.44cm，trace新命令与当前状态距离4.467cm；表中按既有sample时点（对应上一执行目标）的峰值4.385cm，二者采样时序不同，不混用。需要检查卸载与抬脚同时进行造成的滞后，不以降低增益等同于全程自然步态完成。

落脚保持阶段，512/513最大机身位移1.567/1.654mm，足位移.226/.245mm，角速度峰值.0237/.0244rad/s；原513残余版本对应3.254mm/.718mm/.1826rad/s。保持段覆盖全部32回合，但它不能取代空中与离地过程指标。

| 批次 | 完成/未完成 | 20cm CLIMB成功/32 | 严格单步且末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ay/baseline513 | 32/0 | 0 | 32 | 0 | 99.817 | .060 | .951 | 203.635 | .280 |
| ay与az/half513 | 32/0 | 0 | 32 | 0 | 99.827 | .060 | .951 | 203.635 | .280 |
| az/half512 | 32/0 | 0 | 32 | 0 | 99.885 | .060 | .902 | 204.383 | .280 |

保留初始化峰值及原前.10秒排除规则，饱和为98%阈值最大单关节累计时长。修正后2秒起两组≥三足支撑均100%、无腾空，竖直速度峰值512=.0484/513=.0719m/s、足力111.189/114.763N。没有热安全或实机结论。24秒单步不冒充原12秒、20cm完整攀爬或未见种子验收；512/513已用于开发，录像复现不增加样本。

原速页面`index.html`以同一513/env3展示上一版和.5修正的对比，并提供512/env14交叉检查。新视频均24秒/600帧/25fps/1280×720；旧8777仍是位置系数1版本。已检查2/5/8/10/12/14/16/23秒关键帧及50Hz轨迹，不能仅靠关键帧宣布连续自然性达标。

本地仓库外及远程/path/to/artifacts/go2-piper/同名目录climb-support-swingposition-20261001-ay、climb-support-swingpositionreview-20261001-az保存源码、计划、实际YAML、报告/日志/分析；az另有录像和页面。joint-feedback-audit.json明确关节映射、相位反向、包络与参考跟踪；swing-analysis.json含全32回合足部统计；verification.json含视频哈希与复现核验。四份d任务源码仍冻结，44份任务Python及实际配置哈希已记录。

控制SHA：9bac6fdf2aafd894ad29530cadedba0eb76dd19ab379e1644e9987aa0ca89ec9；诊断SHA：8c06f49c2ecd23947c28bdeaba8e1200a7c2a3ad1ed07eaa684be5a2305ac11e。Python编译、diff检查与实际旧轨迹逐值复现通过。ay/az所有进程结束，无本项目训练/评估/录像运行；PUSH、MuJoCo与实机暂停。

下一步以显式外层位置.5、速度0为单步诊断起点，优先梳理承重卸载→实际轻载→抬脚的时序，检查全路径可达性与既有包络，保留24秒时限。目标是减少离地滞后而不重新激起足部往复；再逐步扩展多腿和台阶，最终仍需固定完整20cm候选后两组未用种子验收。不要回到已拒绝的短重心转移或凭32/32直接宣布慢爬完成。

<a id="record-0163"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 先卸载、再按实测轻载抬脚 ba–bb（最新，平地单步进展）

az的513/env3从8.70秒开始抬脚，约1秒后实际脚仍接地，而新足高参考已上升约3.95cm，实测FL负载从32.8N逐渐下降。原控制将卸载和足高轨迹同时推进，累积跟踪误差后才离地。这是配对诊断的具体依据，不将所有摆动都归因于RL或电机延迟。

新增默认关闭`--unload-before-lift`：原质心转移和支撑门禁通过后，先用1秒五次平滑曲线把支撑分配转为三足，足位目标保留原地面锚点。实际FL法向力≤5N、其余三脚真实接触、三足几何裕度≥1.5cm、机身速度<.05m/s、角速度<.1rad/s连续至少.1秒才开启独立抬脚时钟；浮点步进实际观察为.12秒。5N为本次轻载诊断阈值，不是硬件验收结论。此后仍1.5秒抬5cm、1.5秒前移8cm、1.5秒落脚，积分计时也排除卸载等待；24秒总时限不延长。保留显式外层位置.5/脚速0、物理PD30/.6、延迟0–4步、关节限位/速度/加速度/名义±.7rad包络、20cm箱与全部成功/碰撞/执行器门禁。冻结任务与策略包未改，无新PPO训练。

ba/baseline513逐值复现az/half513所有32旧终态、步态/关节/保持/空中足部/资产/延迟字段，确认默认关闭分支不改行为。ba/unload513完成32/32严格单步且末段安静，零安全失败。固定后bb录制同一513/env3并在已用512/env14交叉检查，两组仍32/32且无未完成；513全部32终态/指标逐值复现ba。录像重放不增加独立样本，512/513均为开发种子。

| 版本/种子 | 最大空中横向误差范围cm | 中位范围cm | 最大足速m/s | 最大跟踪误差cm | 中位误差变化路程m | 最大误差变化路程m |
| --- | --- | --- | --- | --- | --- | --- |
| baseline513 | 1.320 | 1.029 | 0.173 | 4.385 | 0.077 | 0.089 |
| unload513 | 0.516 | 0.280 | 0.161 | 1.942 | 0.020 | 0.025 |
| unload512 | 0.451 | 0.288 | 0.149 | 1.689 | 0.019 | 0.023 |

513/env3抬脚阶段按50Hz新命令与当前状态计算的最大误差4.467→.541cm；原目标已升高但脚仍接地的情况，在该修正版样本中消除。9.82秒实际释放时FL力0N、另三脚95.45/88.96/38.37N、三足裕度4.54cm，速度约.00165m/s；所有32环境均9.82秒释放。完成单步时刻由14.08延后到15.20秒，保留充足末段停稳，不通过缩短动作或漏记回合改善指标。上表沿用SwingQuality上一执行目标采样口径，与trace新命令口径分开。

| 批次 | 完成/未完成 | 20cm成功/32 | 严格单步且末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ba/baseline513 | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| ba/unload513 | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bb/unload512 | 32/0 | 0 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bb/unload513录像复现 | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

完整步态统计仍只排除原前.10秒，保留初始化峰值。饱和采用98%阈值的最大单关节累计时长，足部峰值取接触历史；不是温升或实机电机安全证明。所有批次完整20cm攀爬均0/32，仍是独立24秒平地单步，不能代替原12秒验收。

unload512从2秒起≥三足支撑100.000%，最长腾空0.000s，竖直速度峰值0.0484m/s，足力峰值102.892N；整个落脚保持阶段最大机身位移1.571mm、足位移0.228mm、角速度0.0232rad/s。

unload513从2秒起≥三足支撑100.000%，最长腾空0.000s，竖直速度峰值0.0719m/s，足力峰值101.093N；整个落脚保持阶段最大机身位移1.703mm、足位移0.247mm、角速度0.0248rad/s。

落脚保持指标并非全部下降：例如513最大机身位移由az的1.654mm略增到1.703mm，角速度也略增；本轮主要改善离地/空中足位跟踪，不能宣称所有阶段都更平稳。

真实速度视频入口`index.html`，同一513/env3旧版/卸载版同步1×播放，另有512/env14。两段新视频24秒、600帧、25fps、1280×720。关键帧和50Hz轨迹已检查；尚未把逐帧连续视觉审查或完整自然慢爬验收标成通过。旧8778保留同时卸载抬脚版。

限制：关节包络与全路径几何残差没有修复；此次卸载保持阶段处于phase2，既有全32 HoldQuality尚未单列该阶段，当前只有inspect完整轨迹加全32步态/关节/空中足部与释放时间遥测，不能拿末段安静代表整个卸载过程。下一轮优先补全卸载/摆腿支撑质量和释放时门禁快照，核对所有环境名义可达路径，再推进低台单步与多脚顺序；不盲扫增益或缩短重心转移。

产物位于本地仓库外artifacts/go2-piper/及远程/path/to/artifacts/go2-piper/同名目录climb-support-unload-20261001-ba、climb-support-unloadreview-20261001-bb，保存计划、五份脚本、实际配置、SHA、报告/日志/分析和bb录像。unload-timing-analysis.json保存配对时序，comparison.json与swing-analysis.json覆盖完整32，verification.json保存录像/逐值复现核验。四份d任务源码未变，44份Python清单及实际配置SHA已保存。

控制SHA：82d36b5c7df225db2642ceb93b154cef0ab4ca25798083163cec116721d3639b；诊断SHA：add49431d0eb194f330cd8b133f4694956de32ce21f10f114c3b987be039dba1。14项既有数学检查、Python编译、diff检查通过；默认行为用远端实测逐值复现验证。ba/bb已结束，无本项目训练/评估/录像运行。PUSH、MuJoCo、实机仍暂停。

<a id="record-0164"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 身体随前脚前移的可达性对照 bc–be（2026-10-02，仍是平地单步）

本轮先补齐全32环境卸载保持、摆腿期间另外三足的支撑质量、实际释放时8项门禁快照，以及按生成目标时相位划分的名义FK残差。卸载段跟踪全部4脚位置，但缺失接触只检查FR/RL/RR；摆腿段只跟踪这3脚，机身位移包含有意前移。既有完整保持统计不改，默认新动作关闭。bc/baseline513所有旧终态和旧保持/步态/关节/空中足部/资产/延迟字段逐值复现bb/unload513，证实新增遥测没有改变控制。

新证据：固定足位目标8cm前移时，原FL大腿名义参考碰到捕获姿态−.7rad包络，513最大名义FK落点残差在前移阶段1.282cm、落脚/保持阶段3.150cm；物理FK重建本身仍通过0.5mm门禁。不能用末段实际纠偏到位掩盖名义轨迹超出既有包络。两组已用种子的离线几何检查支持在前脚前移时让机身一并向前，而不是放宽关节包络或减少足步长。

候选新增默认0的`--step-body-advance-m .025`，仅在前脚原1.5秒、8cm前移过程中，用同一五次平滑曲线把身体向前推进2.5cm；其余脚目标锚点不变，平动速度前馈同步。保留先卸载→实际轻载门禁、原质心转移、5cm抬脚、落脚等待、.5位置/0速度外层反馈、PD30/.6、0–4步延迟、q/v/a与名义±.7rad包络、24秒、20cm箱和原安全/停稳门禁。没有改变冻结任务或策略包，也没有新训PPO。

bc同种子513配对两版均32/32严格单步且末段安静、零安全失败。候选固定后bd用已用512交叉检查，并对513/env3录像；两组各32/32，全部24秒完整，20cm仍0/32。be另录513/env2（本候选最大足速样本）的旧版/候选配对，完整32均逐值复现bc。全部重放不增加独立样本，未用种子验收尚未开始。

| 版本/种子 | 最大足位误差cm | 最大横向误差范围cm | 最大足速m/s | 中位误差路程m | 最大误差路程m |
| --- | --- | --- | --- | --- | --- |
| baseline513 | 1.942 | 0.516 | 0.161 | 0.020 | 0.025 |
| advance513 | 0.814 | 0.289 | 0.184 | 0.019 | 0.024 |
| advance512 | 0.780 | 0.324 | 0.174 | 0.018 | 0.023 |

两组候选在全路径/全部腿的名义FK残差峰值均低于0.0002mm，在此次采样精度内消除了包络导致的几何残差；这只验证本次平地参考轨迹，不证明20cm台阶可达。实际足位跟踪仍有毫米级误差。

代价不能省略：513最大足速由.161升至.184m/s；摆腿期间三足最小几何支撑裕度4.447→2.799cm，支撑脚最大位移.683→2.950mm，机身速度峰值.0203→.0396m/s。512支撑脚最大位移2.992mm。身体计划前移2.5cm，因此位移增加不等同于无意晃动，但接触点移动与足速增大仍需检查。2秒后的足力峰值513从101.093增至110.283N，512从102.892增至106.330N，不宣称所有冲击指标都改善。

| 批次 | 完成/未完成 | 20cm成功/32 | 严格单步且末段安静/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 足部峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bc/advance513.json | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bc/baseline513.json | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bd/advance512.json | 32/0 | 0 | 32 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bd/advance513.json | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| be/advance513.json | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| be/baseline513.json | 32/0 | 0 | 32 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

以上保留初始化峰值，只排除原前.10秒；饱和为98%阈值最大单关节累计时长，不是电机温升或实机安全结论。各候选从2秒起≥三足支撑100%、无腾空，512/513竖直速度峰值.0484/.0719m/s。不能用这些单步指标代替24秒完整登台，更不能冒充原12秒验收。

advance512：全32卸载段均1.12秒，另外三足缺失接触0秒、最低支撑裕度5.627cm，机身最大位移2.242mm、角速度0.0446rad/s；全32释放快照均通过原实测轻载/稳定条件。随后摆腿段5.16秒，三足缺失接触0秒、最低裕度4.104cm、角速度峰值0.0567rad/s。

advance513：全32卸载段均1.12秒，另外三足缺失接触0秒、最低支撑裕度4.469cm，机身最大位移2.282mm、角速度0.0480rad/s；全32释放快照均通过原实测轻载/稳定条件。随后摆腿段5.16秒，三足缺失接触0秒、最低裕度2.799cm、角速度峰值0.0556rad/s。

最大足速样本513/env2的50Hz分相分析：

- baseline513 phase2：足速峰值0.0656m/s，时刻10.60s，速度xyz=[0.0004, -0.0007, 0.0656]；横向速度超过.02m/s的反向0次。
- baseline513 phase3：足速峰值0.1030m/s，时刻12.32s，速度xyz=[0.1030, 0.0006, -0.0013]；横向速度超过.02m/s的反向0次。
- baseline513 phase4：足速峰值0.0741m/s，时刻14.06s，速度xyz=[-0.0139, 0.0029, -0.0727]；横向速度超过.02m/s的反向0次。
- advance513 phase2：足速峰值0.0656m/s，时刻10.60s，速度xyz=[0.0004, -0.0007, 0.0656]；横向速度超过.02m/s的反向0次。
- advance513 phase3：足速峰值0.1062m/s，时刻12.34s，速度xyz=[0.1062, -0.0005, -0.0008]；横向速度超过.02m/s的反向0次。
- advance513 phase4：足速峰值0.1841m/s，时刻14.40s，速度xyz=[-0.0794, -0.0221, -0.1647]；横向速度超过.02m/s的反向0次。

本轮原速页面`index.html`提供513/env3前后、512/env14交叉检查、513/env2最大足速样本前后，均24秒/600帧/25fps/1280×720。关键帧与50Hz轨迹已检查，不将其冒充连续自然性最终验收。旧8779仍是身体不前移版本。

进一步检查be/env2：14.24秒实际FL接触力0、计划承重0N、竖直足速−.057m/s；14.40秒仍未接触、计划承重已4.41N、竖直足速−.165m/s，14.44秒才接触。原落脚相位1秒后按时间恢复承重，与接触前加速同时发生；这是下一步配对实验的依据，尚未单独验证因果。轨迹保存在be/precontact-reload-trace.json。

下一步保留可达的名义路径，优先试验真实接触后才平滑恢复承重，并检查是否出现脚停在地面上方不接触、接触反复、超时或静止漂移；不能凭小跟踪误差或32/32直接进多腿登台。随后按三足支撑裕度和完整可达路径扩展多脚、近台单步。20cm箱与最终门禁保留，若新增低台诊断必须独立标注。PUSH、MuJoCo、实机继续暂停。

产物：本地仓库外artifacts/go2-piper/及远程/path/to/artifacts/go2-piper/下climb-support-bodyadvance-20261002-bc、climb-support-bodyreview-20261002-bd、climb-support-bodyworst-20261002-be。comparison.json、swing-analysis.json、verification.json记录完整指标/复现/视频哈希，be/peak-speed-analysis.json记录最坏足速分相；计划/实际YAML/源码及SHA均保存。四份d任务源码冻结，44份Python清单和配置SHA已核验。

控制SHA：16e949eb25cb6ef50d17e27494a2c580b936b79926cd9e72ee01f37372cfd3f4；诊断SHA：176ff803559d9fef243af85d7a6661badd329849db8f32aab3145f41c126d98c。14项既有数学检查、编译、diff检查通过，新增观测由旧行为逐值复现核验。bc/bd/be所有进程已结束，无本项目训练/评估/录像运行。

<a id="record-0165"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 落脚后再承重 bf–bi（2026-10-02，失败对照与修正版）

针对be/env2在落地前恢复计划承重、足速升至.184m/s的问题，本轮进行三个连续配对实验，保留失败结果。全部远程Isaac、32环境、原24秒/20cm箱与安全门禁；都只是平地单步，完整CLIMB均0/32。没有新PPO训练。

1. bf：默认关闭`--reload-on-contact`，真实FL力>2N连续.06秒、另外三足支撑才启动.5秒五次平滑承重曲线，失去条件时曲线时钟以同速回退。落脚相位还须完成承重曲线再通过原连续接触/.20秒相位门禁。结果0/32单步完成，全部落脚超时；虽然足速变小，不能算改善。终态足位误差不到.31mm，FL力只有0–.258N；原承重地面锚点不是足够的主动触地指令。
2. bg：新增默认0的`--landing-probe-m .003`。原1.5秒下降结束后，如未达到2N接触且另外三足支持，以1秒平滑曲线最多向下探3mm；接触时暂停，落脚后保留实际探深，避免突然撤回参考。结果严格单步27/32，单步且末段5秒安静仅10/32。env2约15.5秒已有1.1N真实轻触，但直到19秒才达到2N，另外5个环境24秒仍未完成；拒绝此版本作为候选。
3. bh：保留3mm探脚，将启动承重的轻触阈值单独设为`--reload-touch-force-n .5`，仍要求持续.06秒。该阈值只启动.5秒承重曲线，原三足支撑、四足落稳和最终成功的2N接触判据全部保留。结果32/32严格单步且末段安静、零安全失败、完整24秒。继续保留既有先卸载、2.5cm机身前移、8cm足步长、原PD30/.6/延迟0–4/q-v-a/±.7rad名义包络/碰撞门禁均保留，未降低最终成功门槛。

每次新增遥测/默认关闭分支均通过远端旧终态/步态/关节/保持/足部/资产/延迟逐值复现：bf基线=bd/advance513，bg基线=bf/contact513，bh基线=bg/probe513。候选固定后bi复查已用512并录513/env2，513全32结果逐值匹配bh；512/513都是开发种子，录像不增加样本，尚无未用种子的完整20cm验收。

| 批次 | 完成/未完成 | 严格单步/32 | 单步且末段安静/32 | 20cm成功/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 最大竖直速度m/s | 峰值足力N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bf/baseline513.json | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bf/contact513.json | 32/0 | 0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bg/baseline513.json | 32/0 | 0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bg/probe513.json | 32/0 | 27 | 10 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bh/baseline513.json | 32/0 | 27 | 10 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bh/touch513.json | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bi/touch512.json | 32/0 | 32 | 32 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bi/touch513.json | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

完整统计仍保留初始化峰值，只排除原前.10秒；饱和为98%阈值的最大单关节累计时长。失败32回合完整结束不等于动作成功，0/32和10/32已明确列出。全程峰值仍由初始化主导，不能用它掩盖落脚过程，也没有电机温升或实机安全结论。

| 版本 | 最大空中足速m/s | 最大足位误差cm | 最大横向误差范围cm | 最大误差变化路程m |
| --- | --- | --- | --- | --- |
| bf/baseline513 | 0.184 | 0.814 | 0.289 | 0.024 |
| bf/contact513 | 0.106 | 0.814 | 0.690 | 0.028 |
| bg/probe513 | 0.106 | 0.814 | 0.595 | 0.027 |
| bi/touch513 | 0.106 | 0.814 | 0.289 | 0.022 |
| bi/touch512 | 0.106 | 0.748 | 0.324 | 0.021 |

touch512从2秒起≥三足支撑100.000%、腾空0.000s、竖直速度0.0484m/s、足力106.330N；完整摆腿/落脚期间三支撑脚缺失接触0秒、最低几何裕度4.104cm、支撑脚最大位移2.992mm。全32承重启动在15.18–15.38秒，真实轻触力0.548–0.657N，最终探深1.500–2.587mm。

touch513从2秒起≥三足支撑100.000%、腾空0.000s、竖直速度0.0719m/s、足力110.283N；完整摆腿/落脚期间三支撑脚缺失接触0秒、最低几何裕度2.799cm、支撑脚最大位移2.950mm。全32承重启动在15.18–15.40秒，真实轻触力0.540–0.639N，最终探深1.500–2.720mm。

同一513/env2下降段（原2N接触口径）足速峰值0.1841→0.0666m/s；完整轨迹见landing-speed-audit.json。first_landing_contact_speed是50Hz采样到>2N后的速度，不能冒充碰撞前速度或冲击冲量。max_airborne_reload_force_n是旧2N阈值下的计划承重峰值，含.5–2N轻触段，名称不意味着真实足底完全腾空；轻触恢复承重期间该字段可以非零。

限制：仍有原机身前移带来的支撑裕度缩小和约3mm支撑脚移动；本轮没有重新优化它们。3mm参考探深是仿真接触搜索幅度，不是实机标定。基于接触状态的曲线回退机制仅在本次轨迹验证，不等于鲁棒接触丢失恢复已通过。名义平地可达路径仍保留，不证明台阶可达。

新原速页面`index.html`提供同一513/env2原按时间承重与轻触版对照，以及512/env14交叉检查。视频24秒/600帧/25fps/1280×720，报告/源码/完整32重放已核验，已检查关键帧和50Hz轨迹；不把稀疏关键帧当作连续自然性最终验收。旧8780保留前移但按时间承重版本。

下一步固定可达单步与实测卸载/轻触承重时序，扩展下一只脚的支撑转移与落点可达性，先核对完整动作时间预算；不能把24秒单步等同20cm完整慢爬。原箱高、停稳/碰撞/执行器门禁继续保留，最终仍需固定完整候选后两组未用种子各至少30/32，检查原速录像。PUSH、MuJoCo、实机暂停。

控制SHA：c0dd27f21d60e79d6642d8c145b4903309771db3b419dd91abfd7491c45cda0d；诊断SHA：a647aedfe06306f1f590e709bd575b64d5a18e77d1ecbf93ec5e9e712c8e8132。产物位于本地仓库外artifacts/go2-piper/和远程/path/to/artifacts/go2-piper/下climb-support-contactreload-20261002-bf、climb-support-contactprobe-20261002-bg、climb-support-lighttouch-20261002-bh、climb-support-touchreview-20261002-bi目录，包含源码、计划、实际YAML、SHA、日志/报告/分析及bi录像。四份d任务源码冻结，44份Python清单及配置SHA已保存。既有14项数学检查、编译/diff检查通过，默认行为由远端实际复现验证。bf–bi均已结束，无本项目训练/评估/录像运行。

<a id="record-0166"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 第一步后转向右后脚支撑准备 bj–bl（2026-10-02，未执行第二步）

本轮从已验证的FL平地单步向顺序步态推进，新增默认关闭`--next-support-only`。第一步落稳后，还须实际四足接触、机身速度<.025m/s、角速度<.1rad/s、线加速度<.5m/s²、角加速度<1rad/s²、gravity-z<−.98连续1秒，才捕获当前承重姿态/足点，以原.5秒平滑接管开始第二次3秒质心转移。第二次朝向FL/FR/RL的三角形质心，为未来RR抬脚准备；本轮RR始终不抬，不能算两步完成。所有脚保持接触、原20cm箱/24秒/PD/延迟/q-v-a/名义±.7rad包络/安全门禁不变，第一步先卸载/轻触承重沿用bi，没有新PPO训练。

新增phase7独立记录第二次转移的全阶段保持质量、真实接管门禁、最终支撑裕度。辅助“准备就绪”判据：3秒转移完成后，真实四足接触、潜在RR三足几何裕度≥1.5cm、机身速度<.025、角速度<.1、gravity-z<−.98、机身目标误差<1.5cm连续1秒。这个辅助指标不是原5秒末段安静，也没有验证RR卸载后的动态三足支撑。

bj基线逐值复现bi/touch513全部32旧终态/步态/关节/保持/足部/资产/延迟；开启第二转移后第一步32/32保留，RR支撑准备仅27/32，零安全失败。env9/10/13/18/21终态几何裕度只有1.13–1.44cm，仍低于原1.5cm门禁，不允许抬脚。原10cm位移上限截断了向下一支撑区的转移。

离线用已用512/513姿态审计第二转移路径：12cm上限预测最低几何裕度3.34/3.83cm，关节变化峰值.554/.533rad，在原±.7rad包络内；该几何检查不是动力学证明。bk只把新增第二转移上限`--next-shift-max-m`从默认.10改为.12，第一转移保持10cm上限。bk基线逐值复现bj/next513；12cm同组RR准备32/32，零安全失败。固定后bl在已用512交叉检查并录513/env13（旧最小裕度样本）；录像复现不增加独立样本。

| 批次 | 完成/未完成 | 第一步严格完成/32 | 第一步且末段5秒安静/32 | RR准备就绪/32 | 20cm成功/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直速度峰值m/s | 峰值足力N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bj/baseline513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bj/next513.json | 32/0 | 32 | 0 | 27 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bk/baseline513.json | 32/0 | 32 | 0 | 27 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bk/cap12_513.json | 32/0 | 32 | 0 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bl/next512.json | 32/0 | 32 | 0 | 32 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bl/next513.json | 32/0 | 32 | 0 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

保留初始化峰值与原前.10秒排除规则；饱和为98%阈值最大单关节累计时长，无温升/实机安全结论。基线未启用RR准备时，辅助就绪0是未执行，不是原第一步失败。24秒回合完整结束，不等于完整动作通过。

next512：第一步32/32；RR准备32/32；第二次转移在17.10–17.30s开始，最终裕度2.502–6.479cm，准备就绪连续时间3.70–3.90s。全阶段机身速度峰值0.0825m/s、角速度0.0183rad/s、足位移15.276mm、机身目标误差9.237mm，四足接触缺失0.000s。原末段安静只有4.18–4.40s，未满足5秒。

从2秒起≥三足支撑100.000%、腾空0.000s、竖直速度0.0484m/s、足力106.330N。全程名义FK残差0.000151mm；真实接管门禁全部通过=True。

next513：第一步32/32；RR准备32/32；第二次转移在17.10–17.32s开始，最终裕度2.896–7.542cm，准备就绪连续时间3.68–3.90s。全阶段机身速度峰值0.0821m/s、角速度0.0173rad/s、足位移14.901mm、机身目标误差8.980mm，四足接触缺失0.000s。原末段安静只有4.16–4.38s，未满足5秒。

从2秒起≥三足支撑100.000%、腾空0.000s、竖直速度0.0719m/s、足力110.283N。全程名义FK残差0.000137mm；真实接管门禁全部通过=True。


本轮代价和限制：第二次转移支撑脚中心移动约1.5cm，比原单步的约3mm明显增大；不能仅因四足都接触、机身角速度低就称稳定支撑已解决。记录的是脚刚体中心位移，不单凭它断言接触面全为滑移；需结合接触点、足速度和受力分析。10→12cm同组最大足位移12.545→14.901mm、机身速度.0683→.0821m/s。未缩小三足门槛，也未抬RR绕过未达标状态。

时间预算现在有实测依据：第一步落稳加1秒确认后约17.1–17.3秒才启动第二转移，3秒后只剩约3.7秒，无法按现有卸载/1.5秒抬脚/1.5秒前移/落脚承重时序再完成RR一步并保留最终停稳。没有延长24秒、没有降低停稳门槛；本轮新序列的原末段5秒安静为0/32，完整20cm仍0/32。不能把辅助RR准备32/32冒充完整顺序步态验收。

原速页面`index.html`提供24秒全过程：先FL单步，约17秒后第二次质心转移，RR不抬。512/env14及513/env13两段24秒/600帧/25fps/1280×720，源码/报告/视频SHA与513全32复现已核验；关键帧与50Hz轨迹已检查，不声明连续自然性最终验收通过。旧8781保留已验证的单步。

下一步先检查第二次转移中足点移动与载荷分配，再设计可执行的连续步态和时间分配；保持原关节/接触门禁，不能用单纯加快所有阶段或延时绕过24秒问题。RR真正卸载与摆腿仍未验证，随后再扩展台阶。PUSH、MuJoCo、实机暂停。

产物本地仓库外artifacts/go2-piper/及远程/path/to/artifacts/go2-piper/下climb-support-nexttransfer-20261002-bj、climb-support-nextmargin-20261002-bk、climb-support-nextreview-20261002-bl，包含计划/五份源码/实际YAML/SHA/日志/完整报告和next-support-analysis.json，bl含录像与verification.json；四份d任务源码未改，44份Python及实际配置SHA已保存。控制SHA：f47a6ce03a2c64ddb86b56a72ed5accd550a018bcb2d8aa1ede48268f34963fc；诊断SHA：7f4da847ce23fcb9b21ebf0a7d15a1c615642443de33d978907e3496685f64cb。14项既有数学检查、编译/diff及远端旧轨迹逐值复现通过；bj/bk/bl均已结束，无项目训练/评估/录像运行。

<a id="record-0167"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 圆足滚动审计与右后脚卸载 bm–bo（2026-10-02，未执行第二步）

本轮继续远程Isaac、原24秒/20cm箱/PD30与.6/0–4步延迟/关节q-v-a/±.7rad名义包络/碰撞与停稳门禁。PUSH、MuJoCo、实机暂停，无新PPO训练。所有回合只是平地第一步加下一腿准备，完整20cm均0/32；辅助指标不替代完整慢爬验收。

bm只补遥测，512/513全部32终态、步态、保持、关节、资产与延迟逐值复现bl。按先前全32最大足位移选择512/env27与513/env7，而非挑平静样本。实际USD每脚为半径22mm球，碰撞球心相对脚刚体原点有(-2mm,0,0)偏置。因此HoldQuality记录的是脚刚体原点，不能将其位移直接称为接触面滑移。新增50Hz足姿态与角速度、碰撞形状/变换/半径，供接触运动审计。

核对远端IsaacLab/contact_sensor_data.py：net_forces_w明确仅为法向接触力之和，不含切向摩擦。旧遥测字段measured_foot_force_w名字保留以复现历史，新报告明确其语义；近零水平分量不能作为地面无摩擦的证据。

用相邻实测足姿态计算旋转增量，并按球心偏置与地面最低点重建滚动位移，与实测脚刚体位置增量比较。该模型只适用于本次水平地面球形接触，并非实测接触斑/切向力。

- 512/env27：扣除滚动后的水平净残差最大0.0460mm，残差累计路径最大0.4862mm，50Hz残差速度峰值0.000353m/s。
- 513/env7：扣除滚动后的水平净残差最大0.0506mm，残差累计路径最大0.4209mm，50Hz残差速度峰值0.000342m/s。

两个最坏样本约1.5cm移动与球底滚动基本吻合，暂不加入“把脚刚体坐标拉回固定点”的额外支撑反馈。此结论不表示全部状态零滑移或实机橡胶足底已验证。另发现直接积分50Hz瞬时线速度与位姿变化不一致（保留原始残差），不能用它积分出一个未经确认的滑移距离；上述结论采用相邻位姿差分，详细双口径见foot-roll-analysis.json。

bn新增默认关闭--next-unload-only，要求next-support-only与centroid。第二次转移完成后须按原辅助准备判据连续1秒：四脚真实接触、RR潜在支撑裕度≥1.5cm、机身速度<.025m/s、角速度<.1rad/s、gravity-z<−.98、机身目标误差<1.5cm。随后用1秒五次平滑曲线将RR计划承重降为0；记录RR当时真实脚点，并按同一曲线接入地面参考及适度位置反馈，保持原物理PD。三脚接触或裕度丢失时曲线时钟回退；该失效恢复分支尚未经独立扰动验证。

重用原载荷分配器时临时把RR放到摆腿槽，计算后恢复FL/FR/RL/RR顺序。实际卸载就绪仍要求另外三脚各>2N、RR≤5N、裕度≥1.5cm、机身速度<.05、角速度<.1连续.1秒；只记录就绪，完全没有RR抬脚指令。卸载期间独立累计三支撑脚位移、接触缺失、机身速度与裕度。bn基线逐值复现bm/513，候选513实测卸载32/32；固定后bo交叉检查已用512，并录像复现513全32终态和质量指标，录像不增加独立样本。

| 批次 | 完成/未完成 | 第一步/32 | RR卸载/32 | 原末段5秒安静/32 | 20cm/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直速度峰值m/s | 峰值法向足力N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm/audit512.json | 32/0 | 32 | 0 | 0 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bm/audit513.json | 32/0 | 32 | 0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bn/baseline513.json | 32/0 | 32 | 0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bn/unload513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bo/unload512.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bo/unload513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

全程保留初始化峰值（沿用原前.10秒排除），饱和按98%阈值累计；峰值法向足力不是冲量或电机热评估。未启用卸载的基线RR卸载0表示未执行。回合完整超时不代表完整任务成功。

unload512：RR卸载32/32，开始21.12–21.32s，最终连续就绪1.68–1.88s，RR最终真实法向力0.451–0.932N。卸载阶段三脚缺失0.000s，最低裕度2.320cm，支撑脚最大位移0.292mm，机身速度峰值0.00613m/s、角速度0.02403rad/s。全程名义FK残差最大0.000151mm。

从2秒起≥三足支撑100.000%，最长腾空0.000s，竖直速度峰值0.0484m/s，法向足力峰值113.414N。

unload513：RR卸载32/32，开始21.12–21.34s，最终连续就绪1.66–1.88s，RR最终真实法向力0.433–0.945N。卸载阶段三脚缺失0.000s，最低裕度2.733cm，支撑脚最大位移0.309mm，机身速度峰值0.00646m/s、角速度0.02141rad/s。全程名义FK残差最大0.000137mm。

从2秒起≥三足支撑100.000%，最长腾空0.000s，竖直速度峰值0.0719m/s，法向足力峰值110.783N。

载荷转移后，512从2秒起峰值法向足力由原106.330升至113.414N，513由110.283升至110.783N；不能声称本轮减小了整体接触冲击。RR末段只有轻触、低于原2N支撑阈值，因此原四足末段安静计时归零，5秒安静0/32不再只是时间不足；卸载就绪和完成后四足停稳是不同阶段，必须在后续摆腿落脚后重新满足原门禁。

新原速页面`index.html`，两段512/env27与513/env7各24秒、600帧、25fps、1280×720，报告/来源/视频SHA已验证，已检查关键帧和50Hz轨迹。末段只是RR卸载，不能看作第二步，更不是20cm慢爬通过；没有把抽帧检查当作连续自然性最终验收。旧8782保留未卸载版。

时间预算仍不满足完整步态：约21.1–21.3秒才启动RR卸载，约22.2秒就绪，剩余不到2秒。下一步先设计连续摆腿与转移的时序，在足速/加速度、可达性、三足支撑和最终停稳约束下审计时间预算，再执行RR摆腿；不能整体提速或延长24秒掩盖问题。后续才是近台与20cm登台，最终仍需固定完整候选后两组未用种子各≥30/32且无未完成，并检查原速视频。512/513均是开发种子。

产物位于本地仓库外artifacts/go2-piper及远程/path/to/artifacts/go2-piper下climb-support-footroll-20261002-bm、climb-support-rrunload-20261002-bn、climb-support-rrreview-20261002-bo。含源码快照、计划/实际YAML、SHA、报告/日志、滚动与卸载分析，bo含录像/校验。四份d任务源码保持冻结、44份Python清单和实际配置SHA已保存；14项既有数学检查、编译/diff及实际旧轨迹复现通过。控制SHA：0bb3fad258a229a91b29cc468d85f5cab036da01bd7a2266bf03e577eb796eba；诊断SHA：49bfa7b46cac1c5c563a082a5fa79e58611e6946407efd3253f23709e54f8df8。bm/bn/bo已结束，无项目训练/评估/录像运行。

<a id="record-0168"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 连续弧线与复用落稳观测 bp–bt（2026-10-02，仍未完整登台）

本轮只推进远程Isaac中的平地步态基础，无新PPO训练。新增24秒诊断与原12秒验收分开；20cm箱、真实接触、物理PD30/.6、0–4步延迟、原关节q-v-a/±.7rad名义包络、碰撞和最终停稳门禁保持。完整20cm均0/32，辅助第一步/RR准备成功不算完整CLIMB成功。PUSH、MuJoCo、实机继续暂停。

bp先离线审核名义路径：将原各1.5秒的抬升、前移、下降合成3秒连续弧线，x=.08×五次平滑函数(u)，z=.05×64u³(1−u)³，u为归一化时间；两端速度和加速度均为0，峰值净空仍5cm。机身同步前移2.5cm并使用匹配速度前馈。名义足速峰值.06661m/s、加速度.13333m/s²，64条已有512/513姿态的最大名义关节偏移.66265/.67405rad，低于原.7包络，关节速度约.370rad/s、加速度约.703rad/s²。该审核是局部几何和参考检查，不是动力学/台阶验证。新增数学检查覆盖弧线端点、C2连续性、净空与3秒速度上界；共15项通过。

bq新增默认关闭--continuous-swing-s 3。先按原门禁实测卸载FL，再执行连续弧线；另外记录实际离地≥3.5cm，且在离地≥3cm时实际前移≥3cm，均观测到后才允许完成弧线并进入落脚。原真实轻触>.5N持续.06秒、.5秒承重曲线、2N支撑判据、最多3mm接触搜索，以及弧线结束、落脚和保持阶段的.2秒确认继续保留；不按时间直接给悬空脚恢复载荷。弧线在phase2执行，phase3不用；到终点后接入phase4原接触搜索和落稳，不再重放另一段下降。积分补偿只在弧线结束后启用。

bq基线逐值复现bo/unload513全部32旧终态/步态/关节/保持/足部/资产/延迟。连续弧线513第一步及RR卸载均32/32，零安全失败；摆脚峰速.106413→.070058m/s，峰值跟踪误差仍.008135m，后续支撑转移提前约1.74秒。br固定后交叉检查512并录制513摆脚峰速最大env4；513全32重放一致。512峰速.069815m/s、峰值误差.007483m。实际抬升约4.98–5.07cm，全部64个清障/中段观测均满足。

进一步审计env7：完全恢复承重、四脚接触、足位误差合格且机身持续满足原落稳门禁的部分观测，在phase4/5中未被下一步计时器使用。bs新增默认关闭--reuse-landing-stability：从完全恢复承重后的phase4/5/6累计同一连续1秒的四足/速度<.025/角速度<.1/线加速度<.5/角加速度<1/gravity-z<−.98观测，任一条件失效则清零；仍须phase6才允许下一次转移。没有缩短实测1秒，也没有改原第一步验证或最终停稳判据。 对bs/env7、bt/env25与env4各取转移前完整1秒的51个50Hz观测，全部满足原四足、完全承重、足位、速度、角速度、线/角加速度及重力方向门槛；复用窗口包含phase4/5/6，检查结果保存为overlap-gate-audit.json。bs基线逐值复现bq，513又提前约.42秒，第一步与RR卸载均32/32，零安全失败。bt固定后复查512并录制最大摆脚速度样本512/env25、513/env4，513全32重放bs一致。

| 批次 | 完成/未完成 | 第一步/32 | RR卸载/32 | 原末段5秒安静/32 | 20cm/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直速度峰值m/s | 峰值法向足力N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bq/arc513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bq/baseline513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| br/arc512.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| br/arc513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bs/baseline513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bs/overlap513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bt/overlap512.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bt/overlap513.json | 32/0 | 32 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

全程仍保留初始化（沿用原前.10秒排除），98%阈值累计饱和。法向足力峰值不是冲量或温升证明。RR保持轻触卸载、未抬脚，末段四足安静仍0/32；回合完整超时不等于任务完成。

overlap513：第二次转移开始14.94–15.18s，RR卸载开始18.96–19.20s，约在20.1秒后实测卸载就绪；验证后剩余时间约3.68–3.92s（50Hz计时）。足速峰值0.070058m/s，峰值跟踪差0.814cm，真实最高抬升4.995–5.074cm，全部32清障与中段观测通过。RR卸载阶段三脚缺失0.000s，最低裕度2.739cm，支撑脚最大位移0.310mm。

从2秒起≥三足支撑100.000%，最长腾空0.000s，竖直速度峰值0.0719m/s，法向足力峰值110.771N。最大名义FK残差0.000137mm。

overlap512：第二次转移开始14.96–15.16s，RR卸载开始18.98–19.18s，约在20.1秒后实测卸载就绪；验证后剩余时间约3.70–3.90s（50Hz计时）。足速峰值0.069815m/s，峰值跟踪差0.748cm，真实最高抬升4.978–5.072cm，全部32清障与中段观测通过。RR卸载阶段三脚缺失0.000s，最低裕度2.316cm，支撑脚最大位移0.295mm。

从2秒起≥三足支撑100.000%，最长腾空0.000s，竖直速度峰值0.0484m/s，法向足力峰值113.423N。最大名义FK残差0.000151mm。

限制：足速下降与时间缩短有配对证据，但峰值足位跟踪差未改善，不能称所有晃动已解决。SwingQuality以旧2N阈值筛选，可能包含卸载轻触；first_landing_contact_speed为50Hz采样接触后的速度，不是碰撞前冲击速度。之前圆足滚动解释仍适用，不能直接用脚刚体坐标位移判滑移。

下一步的RR弧线名义几何初查（bq/513全32终态）：8cm/5cm/3秒轨迹加2.5cm机身前移，最大相对捕获关节偏移.63558rad、名义关节速度.34457rad/s、加速度.69588rad/s²，简化COM平移模型的最低支撑裕度3.768cm；这不是实际卸载后摆腿验证。虽然本轮比bo节约约2.16秒，剩余时间仍不足直接追加3秒RR弧线、实际接触搜索/承重以及最终1秒停稳，更不满足5秒附加安静诊断。下一步优先检查弧线结束与接触搜索/承重之间能否复用已观测接触、消除重复等待，再设计RR实际摆腿；保留真实接触与最终停稳，不按时间提前承重、不整体提速/延长24秒。随后才是近台与20cm完整登台。

新原速页面`index.html`展示最终bt，512/env25与513/env4均为批次最大摆脚速度样本；每段24秒、600帧、25fps、1280×720。视频与报告SHA/来源已验证，检查关键帧及50Hz轨迹，不把抽帧检查当作连续自然性最终验收。br中间录像保留；旧8783为原分段摆腿。512/513均为开发种子，最终完整候选仍须两组未用种子各≥30/32且无未完成，并检查原速录像。

产物：本地仓库外artifacts/go2-piper及远端/path/to/artifacts/go2-piper下climb-support-arc-20261002-bq、climb-support-arcreview-20261002-br、climb-support-overlap-20261002-bs、climb-support-overlapreview-20261002-bt；bp=climb-support-arcplan-20261002-bp是本地离线名义审核，不含本地仿真/训练。计划、源码快照、实际YAML、来源SHA、报告/日志/分析、br/bt录像已保存。四份d任务源码冻结，44份Python与实际配置SHA已核验。15项数学检查、编译/diff、默认行为逐值复现通过。控制SHA：2919008eb984c21a06c1a1d5cf3f40aaafa3a1c097a3af3678b50dfad646491e；诊断SHA：71f191a011e0b6667f1e758a71b89b12055734f3ba82948f4f764b6198c5cf30。bq/br/bs/bt已结束，无项目训练/评估/录像运行。

<a id="record-0169"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 平地连续两步与合并准备 bu–bw（2026-10-02，20cm仍未达标）

本轮在既有远程Isaac中运行6组32回合，其中录像513复现不新增独立样本。没有新增PPO。默认关闭`--next-step`实现RR真实摆腿；默认关闭`--prepare-with-shift`合并初始调平和第一次质心转移。所有运行仍为24秒平地诊断，保留20cm箱与原碰撞、执行器、最终登台停稳判据；不冒充原12秒验收。FR、RL尚未迈步，完整20cm全部0/32。

bu先按最终bt几何复核RR路径：8cm前移/5cm抬高/3秒弧线及2.5cm机身前移，32条名义路径最大关节偏移.63556rad，低于原.7包络；这只是几何审核。实际起脚严格使用本帧三脚接触、RR≤5N、支撑裕度≥1.5cm、机身速度<.05/角速度<.1持续.1秒的卸载门禁，而非历史成功锁存。实际高度≥3.5cm以及离地≥3cm时前移≥3cm都必须被观测到。三脚支撑/裕度丢失暂停弧线；该恢复行为有数学门控检查，尚无独立动力学扰动验证。

RR弧线末端实际足位误差<2.5cm连续.2秒后才进入接触搜索；最大3mm/1秒平滑探地，真实法向轻触>.5N持续.06秒才开始.5秒承重恢复，失去接触时平滑回退载荷。最终必须四脚真实>2N、完全恢复承重、RR足位误差<2.5cm，并满足机身速度<.025m/s、角速度<.1rad/s、线加速度<.5m/s²、角加速度<1rad/s²、gravity-z<−.98连续1秒，才记为第二步停稳通过。这是比原单步辅助保持更严格的平地检查，不替代箱顶成功条件。

bu的默认关闭基线逐值复现bt/513全部32原终态及物理、运动、保持指标。新增RR弧线32/32实际离地、前移，零安全失败；但24秒结束时28个恢复承重、4个仍在恢复承重，最终1秒停稳0/32。因此不能把“第二条腿动起来”直接算作成功。

bv把原独立3秒调平和3秒首次移重心合并：四脚支撑时按同一3秒平滑曲线调平并移向FL以外三脚的质心位置。结束后保留原连续.5秒实测稳定门禁，并额外要求真实三脚裕度≥1.5cm、机身目标误差<1.5cm，再捕获受载姿态并进行原实测卸载；没有缩短实际落脚/最终停稳，没有加快所有阶段。该结构调整节省约3.2秒。bv基线逐值复现bu的RR32个终态和原指标，候选513两步及最终1秒停稳32/32，零安全失败。固定源码后bw交叉检查已用512，并录制513全32复现；两组均32/32。

| 批次 | 完成/未完成 | FL一步/32 | RR一步+1秒停稳/32 | 20cm/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直速度峰值m/s | 法向足力峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bu/baseline513 | 32/0 | 32 | 未执行 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bu/rrstep513 | 32/0 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bv/baseline513 | 32/0 | 32 | 0 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bv/combined513 | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bw/combined512 | 32/0 | 32 | 32 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| bw/combined513 | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

全回合沿用前.10秒排除，仍包含初始化瞬态；力矩饱和以98%阈值累计，法向足力峰值不是冲量/摩擦/温升。各批附加5秒安静均0/32：新候选末段仅3.24–3.40秒，不能声称5秒通过。32回合完整超时与完整爬箱成功严格分开。

combined512：RR开始16.84–16.96秒，实际最高抬升4.847–4.923cm，末端相对原卸载锚点前移8.441–8.626cm。最终连续稳定3.28–3.40秒；RR足速峰值0.070768m/s、跟踪峰差7.624mm。另三脚接触缺失0.000秒，最低裕度2.457cm，支撑脚刚体位移最大3.126mm（含圆足滚动，不直接判为滑移）。

从2秒起≥三足支撑100.000%，腾空0.000秒，竖直速度峰值0.0483m/s，法向足力峰值114.174N。名义FK最大残差0.000143mm。

combined513：RR开始16.86–17.00秒，实际最高抬升4.833–4.926cm，末端相对原卸载锚点前移8.424–8.600cm。最终连续稳定3.24–3.38秒；RR足速峰值0.070693m/s、跟踪峰差7.480mm。另三脚接触缺失0.000秒，最低裕度2.844cm，支撑脚刚体位移最大3.072mm（含圆足滚动，不直接判为滑移）。

从2秒起≥三足支撑100.000%，腾空0.000秒，竖直速度峰值0.0728m/s，法向足力峰值111.601N。名义FK最大残差0.000137mm。

同seed513，FL跟踪峰差由旧bt的8.135mm降至2.789mm，足速约.0700m/s；512为2.585mm/.0699m/s。RR仍有约7.5–7.6mm跟踪峰差，不宣布全部晃动消除或自然性最终通过。旧bt/513从2秒起足力峰值110.771N，新候选111.601N略升，因此也不声称全面减小冲击。

验证：所有32个准备/FL卸载/RR卸载/最终RR稳定门禁逐项核对；bv/env7、bw/512-env25、bw/513-env13另从50Hz稠密轨迹独立重建完整1秒51帧，四脚/承重/足位/速度/角速度/线角加速度/重力方向全部通过。17项数学与门控检查、Python编译、diff检查通过。bu关闭开关复现bt，bv基线复现bu，bw录像复现bv全部32终态和质量指标。未消耗新验收种子。

新原速视频`index.html`，两段各24秒、600帧、25fps、1280×720，均为远程录制。512/env25在运行前按旧bt最大FL足速选定，本轮也是RR足速/跟踪误差最大；513/env13按bv最大RR足速选定。已核对视频/报告来源与哈希并检查关键帧、实际足轨迹；抽帧检查不能替代完整连续动作的自然性验收。旧8784仍保留仅FL一步及RR卸载版本。

本地仓库外`artifacts/go2-piper/`和远程`/path/to/artifacts/go2-piper/`中的`climb-support-rrstep-20261002-bu`、`climb-support-combinedprep-20261002-bv`、`climb-support-twostepreview-20261002-bw`保存全部计划、源码快照、真实YAML、SHA、日志、报告与分析，bw含视频。四份d任务源码未改，44份任务Python清单与实际YAML已核对。所有本轮进程已结束，无PPO运行。下一步扩展可循环的四腿支撑转移/步序并审计总时间，随后才进入近台/低台至20cm；保留真实接触与最终停稳，不直接延长24秒掩盖完整任务缺口。

当前控制SHA：36d07e9a8e262fa957b087e5217f4fec957255c236b516bb37476507c98ccc88；诊断SHA：0efa80d9d3483baa3f117a2ccaba6b25173d89716d513050f79f5eeaa1ec7561。

<a id="record-0170"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 可选步序与右前/左后两步 bx–by（2026-10-02，尚非四步连续循环）

本轮先补齐另外两腿的实际控制证据。默认步序FL→RR保持；新增`--first-leg FR`在同一24秒、20cm箱、PD30/.6、0–4物理步延迟、关节q-v-a/名义±.7rad包络及碰撞门禁下，从原初始站姿独立执行FR→RL。**没有承接bw的末态，没有完成第三/第四步连续衔接，更没有登上20cm箱。** 不是两段视频拼成一次完整行走；没有新增PPO训练。

几何、脚刚体、接触传感器、雅可比与关节槽统一按照所选物理腿顺序使用。FR模式为FR/FL/RR/RL，沿用原第一槽和第四槽的两步状态机，实际执行的是FR和RL。机器人资产没有做镜像；原18维动作顺序与关节重排、力矩和延迟契约保持。`LegKinematics.reordered`只重排已读取的USD几何，并逐帧与Isaac实测足位置核对，差值超过0.5mm即中止。新增一项纯数学检查覆盖不同关节姿态、完整几何重排、逆映射与重复腿名拒绝，共18项通过。

为兼容历史报告，`rr_*`和`next_unload_*`等旧字段名仍存在，但FR模式下它们代表第二腿RL；新`physical_step_order`与`telemetry_leg_mapping`明确实际物理腿名，`leg_reference_order`及卸载门禁列名也按实际顺序输出。分析FR模式时不能把rr字段当成右后腿。两步仍按8cm/5cm/3秒连续弧线、真实卸载、接触搜索及承重恢复执行，最终四脚承重与机身速度、线角加速度、足位误差合格连续1秒才计为通过。

bx的默认FL基线逐项复现bw/513全部32终态，以及运动、步态、保持、资产和延迟指标。FR候选在513的FR一步/RL一步+1秒停稳均32/32，零安全失败。固定控制后by交叉检查已用512，并从右侧录制513/env13（按bx最高RL足速选择）；录像的全部32原终态与运动/保持/足部指标逐值复现bx，录像不新增独立样本。

| 批次 | 物理步序 | 完成/未完成 | 第一步/32 | 第二步+1秒停稳/32 | 20cm/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直速度峰值m/s | 法向足力峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bx/baseline513 | FL→RR | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| bx/otherpair513 | FR→RL | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |
| by/otherpair512 | FR→RL | 32/0 | 32 | 32 | 0 | 0 | 99.885 | 0.060 | 0.902 | 204.383 | 0.280 |
| by/otherpair513 | FR→RL | 32/0 | 32 | 32 | 0 | 0 | 99.827 | 0.060 | 0.951 | 203.635 | 0.280 |

完整回合沿用前.10秒排除，保留初始化峰值；98%力矩阈值累计，不是电流/温升验证。所有批次额外5秒安静0/32，末段只有约3.3秒；完整回合均超时，不能计为20cm成功。

otherpair512：RL起步16.84–16.96秒，最高抬升4.830–4.934cm，末端相对卸载锚点前移8.438–8.604cm。最终连续稳定3.28–3.40秒。FR足速峰值0.070073m/s，跟踪峰差2.689mm；RL足速峰值0.070971m/s，跟踪峰差7.520mm。RL摆动/落地期间另外三脚接触缺失0.000秒，最低裕度3.008cm，最大支撑脚刚体位移3.160mm（包含圆足滚动，不直接判定滑移）。

从2秒起三足支撑100.000%，腾空0.000秒，竖直速度峰值0.0485m/s、法向足力峰值115.219N；名义FK最大残差0.000154mm。

otherpair513：RL起步16.86–16.98秒，最高抬升4.842–4.924cm，末端相对卸载锚点前移8.439–8.541cm。最终连续稳定3.26–3.38秒。FR足速峰值0.069923m/s，跟踪峰差2.717mm；RL足速峰值0.070736m/s，跟踪峰差6.990mm。RL摆动/落地期间另外三脚接触缺失0.000秒，最低裕度2.890cm，最大支撑脚刚体位移3.011mm（包含圆足滚动，不直接判定滑移）。

从2秒起三足支撑100.000%，腾空0.000秒，竖直速度峰值0.0732m/s、法向足力峰值111.415N；名义FK最大残差0.000141mm。

不能据此声称晃动全部解决或接触冲击全面下降：后腿跟踪峰差仍约7–7.5mm，512从2秒起法向足力峰值115.219N，比上一对腿的114.174N略高。只有两对腿的组件验证，没有完整四步或攀爬成功。

连续第三步的几何检查使用bw真实末态：若此时抬FR，512仅18/32、513仅14/32已有≥1.5cm支撑裕度。沿现有几何规划方向移至3cm裕度，512需要0–2.958cm、513需要.478–3.910cm质心位移。这比直接再次移至三角形中心更短，但仅是固定足点的平面几何，不证明实际机身、关节可达性或时间预算。旧末段剩余约2秒，不足直接追加3秒第三腿摆动、真实落脚与最终停稳；不能重置机器人或延长24秒后声称原任务通过。

本轮全部32准备、首腿卸载、第二腿卸载及最终停稳门禁逐项核验；bx/env7、by/512-env0、by/513-env13另独立重建完整1秒的51个50Hz观测，四脚接触、承重、足位、速度、角速度、线角加速度、重力方向均通过。视频600帧/25fps/24秒/1280×720，SHA及全32复现已核验，已检查关键帧和稠密轨迹，不把抽帧检查当作连续自然性最终验收。

新入口`index.html`提供FR→RL原速右侧视角；旧8785保留FL→RR，两者明确标注为独立回合。产物位于本地仓库外`artifacts/go2-piper/`及远程`/path/to/artifacts/go2-piper/`下`climb-support-otherpair-20261002-bx`、`climb-support-otherpairreview-20261002-by`，含源码、计划、YAML、日志、报告、几何/门禁分析、哈希及by录像。四份d任务源码和44份Python来源清单核验未变；18项检查、编译和diff通过。所有本轮进程已结束，无PPO运行。

下一步应转向真实连续循环：将固定两步调度改为可循环步序，依据实际支撑裕度规划必要的重心移动，统一记录连续回合中的每次起脚、落脚和最终停稳。当前两对已经各通过两组开发种子，除非新证据指出问题，不重复增加独立单腿/成对微调；重点解决两对之间的衔接与24秒内的完整运动。仍保留20cm、原碰撞/执行器/最终停稳门禁，最终完整候选固定后才用两组未用种子各32回合验收。

crawl_support.py SHA：230f0d2e3a80e445ce8e75e0bb2e6a2ca00ecb45934b972526d35b7c6e7418c7。

diagnose_crawl_step.py SHA：dc135a4c78d6df4672aca656f839948bfd10c8c60ab44b9d9a2f8942dff7b54e。

crawl_leg_kinematics.py SHA：4e3f293f339c4d01bedd78fc25355bcd28b17b7f27cba337f1315d6174461719。

<a id="record-0171"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 连续换腿与全路径支撑规划 bz–cc（2026-10-02，24秒平地诊断未通过）

从同一回合的实际FL落脚状态继续执行RR、FR、RL，真实捕获每次换腿的足位、机身姿态、关节及控制参考；没有重置、拼接独立两步或瞬移。本轮没有PPO训练，先验证可学习的连续动作参考。`--cyclic`默认关闭，旧两步行为在bz/513全部32终态及质量指标逐值复现bx。

原先每对两步之间的1秒组件检查不再作为内部等待；连续模式在实际四脚承重、足位、机身速度及线角加速度合格连续.2秒后换腿，最终四步后仍要1秒稳定。原20cm箱、原登台成功/1秒停稳、碰撞、自碰撞、PD30/.6、0–4物理步延迟、关节参考q/v/a及名义捕获姿态±.7rad不变，24秒诊断与原12秒验收分开。内部.2秒不意味着原交付标准降低。

bz最初连续候选在代码复核中发现：落地稳定丢失后恢复可能重复递增完成计数；已在完成前停止，该运行无有效评估结论。ca引入独立当前步索引，只有本步记录过真实起脚且未记过完成才能计数，新增检查覆盖重复静止/丢失恢复/下一步未起脚。ca全部32回合完整，但env18在第二腿RR尚未起脚的卸载阶段失稳、姿态终止；28个完成RR，仅2个完成第三腿FR，不能采用。

根因证据：ca/env7在第三腿FR起步时名义裕度3.000cm，但机身继续前移2.5cm后，固定支撑三角形中的名义裕度只剩1.425cm，已经低于真实1.5cm门禁。因此多数样本会中途暂停，不能通过放松门禁解决。旧`support_shift`还暗含10cm限幅，调用后再缩放至14cm上限实际无效，导致部分RR移重心达不到目标。cb改为同时规划前进轨迹两端的3cm裕度；凸三角形内直线路径的两端满足裕度，才支持中间也满足同一几何裕度，实际接触和动态跟踪仍须另查。此例移重心距离由1.872cm变3.571cm，末端名义裕度恢复3.000cm。另修正暂停移重心时仍输出非零期望速度的问题。不是单变量消融，不能将安全改善归因到某一个改动。

移重心采用五次平滑曲线，按距离计算时长，参考速度≤.075m/s、加速度≤.133m/s²；摆腿保持8cm前进/5cm净空/3秒，卸载1秒、实触地搜索3mm、>.5N持续.06秒后.5秒恢复承重。起脚仍须其余三脚>2N、实际裕度≥1.5cm、选中脚≤5N、速度与角速度达标连续.1秒。规划上限14cm不可保证所有几何可达，报告`cycle_planned_path_margin_m`，真实门禁不由名义规划替代。

| 批次 | 完成/未完成回合 | 完成RR/FR/RL | 四步+1秒稳/32 | 20cm成功/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直速度峰值m/s | 法向足力峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bz/baseline513 | 32/0 | 旧两步32/-/- | — | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| ca/cycle513 | 32/0 | 28/2/0 | 0 | 0 | 1 | 99.711 | 0.060 | 0.9514 | 229.595 | 0.560 |
| cb/cycle513 | 32/0 | 32/2/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| cc/cycle513 | 32/0 | 32/2/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| cc/cycle512 | 32/0 | 32/3/0 | 0 | 0 | 0 | 99.885 | 0.060 | 0.9018 | 204.383 | 0.280 |

完整回合步态统计沿用前.10秒排除，保留起始接触瞬态；力矩累计包含初始化。力矩饱和采用原98%阈值；法向接触力不含切向摩擦，也不是电流/温升证明。所有连续诊断20cm成功和额外5秒安静均0/32。

ca/cycle513从2秒起：三足支撑99.869%，腾空0.000s，竖直速度峰值0.4995m/s，法向足力峰值229.595N，摆动期接触或裕度门禁累计不满足最长2.360s。 RR起脚28/32、落地并承重稳定28/32；起脚区间[13.699999809265137, 14.65999984741211]，完成区间[17.65999984741211, 18.619998931884766]。 FR起脚28/32、落地并承重稳定2/32；起脚区间[19.219999313354492, 20.559999465942383]，完成区间[23.51999855041504, 23.639999389648438]。 RL起脚0/32、落地并承重稳定0/32；起脚区间None，完成区间None。

cb/cycle513从2秒起：三足支撑100.000%，腾空0.000s，竖直速度峰值0.0728m/s，法向足力峰值117.886N，摆动期接触或裕度门禁累计不满足最长0.000s。 RR起脚32/32、落地并承重稳定32/32；起脚区间[13.679999351501465, 14.59999942779541]，完成区间[17.639999389648438, 18.559999465942383]。 FR起脚32/32、落地并承重稳定2/32；起脚区间[19.68000030517578, 20.639999389648438]，完成区间[23.959999084472656, 23.979999542236328]。 RL起脚0/32、落地并承重稳定0/32；起脚区间None，完成区间None。

cc/cycle513从2秒起：三足支撑100.000%，腾空0.000s，竖直速度峰值0.0728m/s，法向足力峰值117.886N，摆动期接触或裕度门禁累计不满足最长0.000s。 RR起脚32/32、落地并承重稳定32/32；起脚区间[13.679999351501465, 14.59999942779541]，完成区间[17.639999389648438, 18.559999465942383]。 FR起脚32/32、落地并承重稳定2/32；起脚区间[19.68000030517578, 20.639999389648438]，完成区间[23.959999084472656, 23.979999542236328]。 RL起脚0/32、落地并承重稳定0/32；起脚区间None，完成区间None。

cc/cycle512从2秒起：三足支撑100.000%，腾空0.000s，竖直速度峰值0.0483m/s，法向足力峰值118.598N，摆动期接触或裕度门禁累计不满足最长0.000s。 RR起脚32/32、落地并承重稳定32/32；起脚区间[13.779999732971191, 14.719999313354492]，完成区间[17.739999771118164, 18.68000030517578]。 FR起脚32/32、落地并承重稳定3/32；起脚区间[18.979999542236328, 20.739999771118164]，完成区间[23.239999771118164, 23.53999900817871]。 RL起脚0/32、落地并承重稳定0/32；起脚区间None，完成区间None。

cb/513已消除ca中的摆动中途裕度暂停与安全终止，但没有提高完整任务成功率。FR在19.68–20.64秒才起脚，即使全部按3秒弧线执行，剩余时间也不足再执行第四腿和最终1秒停稳；不能将第三腿执行完弧线写成落地稳定通过，更不能声称四步完成。初始化竖直峰值/腾空仍存在。下一步要依据实际稳定状态重排首步准备、移重心、卸载与落脚等待，消除重复等待，并验证重叠阶段的真实动态；禁止直接延长24秒或全部动作提速来伪造通过。

日志字段：第一步FL仍用原phase/swing_quality；后续三步读取`cycle_*`及`cycle_report`，主phase保持6不再描述后续阶段。`cycle_missing_support_s`包含接触丢失或实际裕度不足，不能直接称为失去三脚接触的时长。计数基于真实顺序事件及高度、接触、承重/静止门禁；报告分析逐回合验证时间递增，未起脚不计完成。cc仅新增可选录像相机方向，不改变控制；全部32终态和质量指标已精确复现cb。视频是513/env5原速右侧视角（cb第三腿FR足速最大样本），视频600帧、25fps、24秒，来源和文件哈希一致。

产物：远程`/path/to/artifacts/go2-piper/`及本地仓库外`artifacts/go2-piper/`下bz/ca/cb/cc上述同名目录，含隔离源码、启动计划、进程记录、实际YAML、日志、32回合报告、时序/支撑路径分析与哈希。23项数学/记账检查、编译与diff检查通过。d冻结任务4份来源及44份Python清单未变。当前无训练、评估或录像运行。两组512/513都是已用开发种子，尚未进入两组未用种子的最终验收。

原速视频入口：`index.html`。关键帧、连续遥测及25fps/24秒视频元数据已核验；抽帧不等于已完成连续动作自然性的最终验收。尚未冻结交付候选。

crawl_support.py SHA：7c85e16c93fb10098f8f4644cbd715aeac7084d98fc87a64588d7dda79e99ccb。

crawl_cycle.py SHA：2279f475cc30921423042ff34244187483a96b78942f3723e750084545f4c6ab。

diagnose_crawl_step.py SHA：a8d4cd62c8f56f52e4490f61183bbd733e841be13e88e034b182e283fdade586。

<a id="record-0172"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 首步为后续支撑预留位置 cd–ce（2026-10-02，仍为平地组件诊断）

新增默认关闭`--prepare-for-next-support`，只用于连续FL起步。原先首步将重心移至三足中心，第一脚落地后又需较大幅度移向对角侧。此次尝试让首步准备位置同时考虑即将发生的FL前移8cm、机身前移2.5cm，以及下一步RR离地后的支撑三角形。起点和前进终点都保持名义3cm裕度，实际卸载仍须1.5cm、其他三足>2N及原稳定条件。没有修改实际成功和安全门禁。

cd将下一组三足中心投影到当前安全区域，部分环境产生不必要的沿边界移动。env4/8目标达到14cm上限，准备末段左后脚法向力约.996N/0N；足端名义FK残差远小于1微米，不能把该问题归因到名义IK限幅。控制器按真实接触门禁停住，这两例没有开始FL摆动。其余30回合完成前两腿，但完整四步仍失败，动作期法向力峰值从基线117.886N增至139.245N，拒绝该版本。

ce用下组支撑中心确定应靠近哪条边界，再选到该安全边界的最短位移，消除不必要的切向移动；投影在质心附近的局部坐标内计算，以减小并行环境远离世界原点时的浮点误差。数学检查覆盖整段前进轨迹的裕度、三角形绕序、坐标平移、未来支撑裕度改善和移位方向，没有将数学证明当作物理控制成功。

两版均保持原2秒后启动、3秒准备及3秒摆腿、8cm/5cm弧线、卸载/实触地/承重/最终1秒停稳门禁。24秒诊断不能替代原12秒任务；20cm箱、PD30/.6、0–4物理步延迟、自碰撞、关节q/v/a和名义±.7rad不变。

| 批次 | 完成/未完成 | FL完成/32 | RR/FR/RL完成 | 四步+1秒稳/32 | 20cm成功/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直峰值m/s | 法向足力峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cd/baseline513 | 32/0 | 32 | 32/2/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| cd/anticipate513 | 32/0 | 30 | 30/1/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| ce/anticipate513 | 32/0 | 32 | 32/16/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |

全回合沿用前.10秒排除，保留初始化瞬态；饱和累计包含初始化，阈值仍为物理力矩限值的98%。法向足力不含切向摩擦，不能代表电流/温升。

cd/baseline513从2秒起：三足支撑100.000%，腾空0.000s，竖直速度峰值0.0728m/s，法向足力峰值117.886N，摆动期间接触或裕度门禁不满足最长累计0.000s。 RR起脚32/32，区间[13.679999351501465, 14.59999942779541]，完成32/32，区间[17.639999389648438, 18.559999465942383]。 FR起脚32/32，区间[19.68000030517578, 20.639999389648438]，完成2/32，区间[23.959999084472656, 23.979999542236328]。 RL起脚0/32，区间None，完成0/32，区间None。

cd/anticipate513从2秒起：三足支撑100.000%，腾空0.000s，竖直速度峰值0.0706m/s，法向足力峰值139.245N，摆动期间接触或裕度门禁不满足最长累计0.000s。 RR起脚30/32，区间[13.479999542236328, 13.679999351501465]，完成30/32，区间[17.459999084472656, 17.779998779296875]。 FR起脚30/32，区间[19.639999389648438, 20.35999870300293]，完成1/32，区间[23.899999618530273, 23.899999618530273]。 RL起脚0/32，区间None，完成0/32，区间None。

ce/anticipate513从2秒起：三足支撑100.000%，腾空0.000s，竖直速度峰值0.0725m/s，法向足力峰值132.496N，摆动期间接触或裕度门禁不满足最长累计0.000s。 RR起脚32/32，区间[13.479999542236328, 13.739999771118164]，完成32/32，区间[17.440000534057617, 17.899999618530273]。 FR起脚32/32，区间[18.920000076293945, 20.239999771118164]，完成16/32，区间[23.239999771118164, 23.979999542236328]。 RL起脚0/32，区间None，完成0/32，区间None。

ce的第三步落地稳定16/32，较匹配基线2/32提高，但第四腿仍没有起脚，完整20cm成功率没有提高。动作期法向足力峰值132.496N高于基线117.886N，因此不能宣称低冲击改善完成；新准备选项保持默认关闭，也没有进行无意义的最终验收或实机放行。

同种子513用于开发，未消耗新验收种子。cd关闭组全部32终态和步态/关节/保持/摆腿/资产/延迟指标逐值复现cb，证明新选项未改变默认控制。全部报告验证起脚顺序、真实卸载门禁、抬升高度和完成计数，24项数学/记账检查及编译/diff通过。d任务4份冻结源码与44份Python来源清单核验未变。

产物在远程`/path/to/artifacts/go2-piper/`及本地仓库外`artifacts/go2-piper/`的`climb-support-anticipate-20261002-cd`、`climb-support-anticipate-20261002-ce`，包含隔离源码、配置、32回合报告、完整性分析和SHA；本轮无新增录像，8787依然是cb/cc，不能作为ce视觉证据。本轮所有远程进程已结束，无PPO训练运行。

下一步应基于整条步序的时间预算继续处理支撑转移与落地等待，而不是重复独立两步测试。任何参考时长变化都须先核对足端/机身速度、加速度以及现有跟踪和力矩裕量，再做隔离动力学对照；不能通过统一提速、缩短真实接触/最终停稳门禁或延长24秒把组件测试写成爬箱完成。完整候选仍须固定后两组未用种子各32回合、每组≥30成功且无未完成，并检查原速视频。

crawl_cycle.py SHA：e79971ff7709a2030b70e48e331d14869f64093c31e5959650a6e1a5fe6a0b46。

crawl_support.py SHA：67dd33e9715be18a4c87a073cfdb746dbcd50634adce183614a6b33292a6a1f2。

diagnose_crawl_step.py SHA：8b0394cebde5a8f2c9583dadd20e7365c7b5929957d524e479102afac95b09c2。

<a id="record-0173"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 连续四步与完整末段停稳 cf–cj（2026-10-02，平地组件通过，20cm爬箱未通过）

本轮没有PPO训练，先补齐可用动作参考。ci两组开发种子512/513中，四腿实际抬起/前移/落地/承重各32/32，四步后连续1秒稳定32/32、31/32，无安全终止，无未完成回合。513/env14最终静止.92秒，严格不计通过。**这些都是同一24秒回合中的平地控制组件结果，机器人没有上20cm箱，完整CLIMB成功仍0/32。** 不能把低冲击组件结果当作完整任务改善完成，也没有使用两组新种子进行最终验收。

### 控制和时间安排

1. cf把3秒摆腿改为显式可选的受预算约束时长，比较2.1秒、1.8秒，仍是8cm前进/5cm抬升的原多项式弧线，起落点参考速度及加速度为零。无中断名义弧线的保守速度/加速度界为`.2/T`、`1.2/T²`，1.8秒对应.1112m/s、.3704m/s²，2.1秒对应.0953m/s、.2722m/s²。数学检查对曲线自动求导复核，**参考界不是实际机器人或电机安全证明**。1.8秒实际足速峰值约.119m/s，略高于名义峰值；应看实际值。cf两档均32/32完成前三步；第四腿分别30/32、32/32起脚，但尚无第四步完成。
2. cg尝试更早开始准备，被旧代码的`climb_start_s>=2`校验拒绝，未产生有效回合，不能记作0/32物理评估。Isaac关闭会吞掉未打印的异常，本轮补充关闭前的异常日志及`.error.json`，避免将无报告退出误判为完成。
3. ch增加显式`--early-preparation`，允许1秒后考虑接管，但须四脚实际触地、速度<.15m/s、角速度<.5rad/s、重力投影z<−.94持续.1秒；仍以.5秒平滑接管。**这只是开始四足准备的条件，不是抬脚条件。** 准备结束后仍须原更严格的连续.5秒承重稳定，再执行真实卸载。实测512/513准备约1.1秒开始。
4. `--adaptive-preparation`按重心位移与去除横滚/俯仰所需角度决定准备时长，保留平移参考.075m/s、.133m/s²，姿态参考.2rad/s、.5rad/s²。使用归一化四元数插值的解析导数界，数学检查覆盖多个姿态角，ch/513实际参考时长1.000–1.490秒；该参考时长后还要等真实稳定。ch固定3秒准备仍无第四步落稳；按需准备31/32完成四步、24/32达到最终1秒静止。
5. ci的`--overlap-landing-waits`仅在完整弧线结束、真实抬升/中途高度/前进已验证后，开始原3mm五次曲线触地搜索，同时进行原.2秒末端稳定检查。加载仍须真实>.5N接触持续.06秒，并执行原.5秒承重恢复；没有提前给悬空脚施加计划支撑载荷。第一步复用已经记录的实际.2秒承重稳定，去掉phase5重复等待。最终1秒静止复用最后落脚的连续稳定观测，避免重复等待和转移帧重复计时，阈值仍为1秒。

每一步仍须实际其他三脚>2N、实际质心裕度≥1.5cm、将抬脚≤5N、速度/角速度达标持续.1秒才放行；原20cm箱/安全碰撞/自碰撞、PD30/.6、0–4物理步延迟、关节参考q/v/a、名义姿态±.7rad不变。24秒诊断与原12秒任务分别报告。新选项默认关闭；没有覆盖冻结策略包。

### 结果与风险边界

| 批次 | 完成/未完成回合 | RR/FR/RL完成 | 四步+1秒稳/32 | 20cm成功/32 | 安全终止 | ≥三足支撑% | 最长腾空s | 竖直峰值m/s | 法向足力峰值N | 最大单关节累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cf/arc180_seed513 | 32/0 | 32/32/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| cf/arc210_seed513 | 32/0 | 32/32/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| ch/early513 | 32/0 | 32/32/0 | 0 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| ch/adaptive513 | 32/0 | 32/32/31 | 24 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| ci/overlap513 | 32/0 | 32/32/32 | 31 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| ci/overlap512 | 32/0 | 32/32/32 | 32 | 0 | 0 | 99.885 | 0.060 | 0.9018 | 204.383 | 0.280 |
| cj/review513 | 32/0 | 32/32/32 | 31 | 0 | 0 | 99.827 | 0.060 | 0.9514 | 203.635 | 0.280 |
| cj/review512 | 32/0 | 32/32/32 | 32 | 0 | 0 | 99.885 | 0.060 | 0.9018 | 204.383 | 0.280 |

全回合步态沿用前.10秒排除，保留初始化瞬态；饱和累计包含初始化，阈值仍为物理力矩限值的98%。法向力不含切向摩擦。未测电流和温升，不能据此实机放行。额外5秒静止仍未完成，最终门禁是本组件的原1秒，不冒充5秒。

cf/arc180_seed513从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0725m/s，法向足力峰值133.841N。摆动期接触或裕度门禁不满足最长累计0.000s。

cf/arc210_seed513从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0725m/s，法向足力峰值133.340N。摆动期接触或裕度门禁不满足最长累计0.000s。

ch/early513从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0486m/s，法向足力峰值133.104N。摆动期接触或裕度门禁不满足最长累计0.000s。

ch/adaptive513从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0607m/s，法向足力峰值133.205N。摆动期接触或裕度门禁不满足最长累计0.000s。

ci/overlap513从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0607m/s，法向足力峰值133.205N。从各环境实际接管时刻起（包含1–2秒准备）：三足支撑100.000%，腾空0.000s，竖直峰值0.0737m/s，法向足力峰值133.205N。摆动期接触或裕度门禁不满足最长累计0.000s。

ci/overlap512从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0456m/s，法向足力峰值139.624N。从各环境实际接管时刻起（包含1–2秒准备）：三足支撑100.000%，腾空0.000s，竖直峰值0.0697m/s，法向足力峰值139.624N。摆动期接触或裕度门禁不满足最长累计0.000s。

cj/review513从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0607m/s，法向足力峰值133.205N。从各环境实际接管时刻起（包含1–2秒准备）：三足支撑100.000%，腾空0.000s，竖直峰值0.0737m/s，法向足力峰值133.205N。摆动期接触或裕度门禁不满足最长累计0.000s。

cj/review512从2秒起：三足支撑100.000%，腾空0.000s，竖直峰值0.0456m/s，法向足力峰值139.624N。从各环境实际接管时刻起（包含1–2秒准备）：三足支撑100.000%，腾空0.000s，竖直峰值0.0697m/s，法向足力峰值139.624N。摆动期接触或裕度门禁不满足最长累计0.000s。

review513：相比同种子旧对照，各环境各关节累计饱和的最大增量0.000000s。 FL实测足速峰值0.119082m/s，跟踪峰差3.034mm。 RR实测足速峰值0.115781m/s，跟踪峰差5.219mm。 FR实测足速峰值0.117375m/s，跟踪峰差2.666mm。 RL实测足速峰值0.114367m/s，跟踪峰差6.128mm。

review512：相比同种子旧对照，各环境各关节累计饱和的最大增量0.000000s。 FL实测足速峰值0.119730m/s，跟踪峰差3.110mm。 RR实测足速峰值0.115267m/s，跟踪峰差5.437mm。 FR实测足速峰值0.117703m/s，跟踪峰差2.574mm。 RL实测足速峰值0.114468m/s，跟踪峰差6.965mm。

不能声称所有动力学指标降低：ci接管后法向足力峰值512约139.624N、513约133.205N，仍高于早期较慢两步参考；初始化.06秒腾空/.95m/s竖直瞬态也未消除。本轮取得的是完整平地步序的可复现证据，不是完整爬箱完成或实机安全结论。

### 视频、审计与下一步

cj固定ci控制，按25fps/600帧/24秒真实速度录制512/env7和513/env14，左侧视角看FL/RL。前者是两批共64回合RL峰值足速最大的样本，后者是唯一最终停稳不足的组件失败样本。全部64终态与质量指标逐值复现ci；录像不增加独立样本。补充gravity/reload/final-rest历史，用原接触、速度、线角加速度、重力与足位误差条件重建末段稳定窗口；详情见`hold-audit.json`。关键帧已检查，不能把抽帧检查称为已完成连续自然性最终验收。

入口`index.html`；8787保留旧3秒步序，不能混为新版本。产物位于远程`/path/to/artifacts/go2-piper/`与本地仓库外`artifacts/go2-piper/`的cf/cg/ch/ci/cj同名目录，包含源码、计划、实际YAML、日志、完整32回合报告、失败历史、分析、录像与SHA清单。cg单独标记启动校验拒绝，没有物理评估结果。26项数学/记账检查、编译和diff通过；d任务4份冻结源码及44份Python清单未变；全部本轮训练/评估/录像进程已结束，本轮无PPO训练。

下一步应转向真正20cm台阶的接近、抬脚越沿、承重面切换与机身抬升参考，保留本版平地四步作回归对照。除非视频或新证据揭示具体缺陷，不再重复平地独立两步微调。先验证单脚上台与后续支撑转移，再完成原20cm条件的整回合；完整候选固定后才做两组未用种子各32回合、每组≥30成功且零未完成。PUSH、MuJoCo与实机持续暂停。

crawl_cycle.py SHA：bdac215c9ac24e69814d24416cc37bde74d34724b5e072a4665de2b16a1dfaeb。

crawl_support.py SHA：635f05b4b78f1f29852e69a2f038f393e5f9efa15a3dec09c95792a58f29957d。

diagnose_crawl_step.py SHA：791a67880c9bda162d6dbdfacc8bd8cdd6711f187d92dd639de29c2a47a6506c。

<a id="record-0174"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 原地面接近与步长可达性 ck（2026-10-02，候选未通过）

原任务箱沿距环境原点75cm，cj/513四步后最近足端距离箱沿仍为37.94–59.61cm，中位50.66cm；5cm抬脚曲线不可能越过20cm箱沿。因此本轮开始接近阶段的可执行参考诊断，并未重置机器人到箱前、修改箱体、把接近等同爬箱或启动新的PPO。已知an/ao中NAV经crawl动作链32/32安全失败，未重复直接NAV接管。

默认关闭`--approach-stride-m`，仅适用于明确启用的连续四步控制：比较16cm步长/每脚机身前移4cm/摆腿3秒与24cm/6cm/4.1秒。整体COM支撑转移仍按当前三足支撑多边形与计划前进量计算，保留实测卸载、落地接触、恢复承重与最终1秒稳定。地面足端目标须止于原箱沿前6cm，否则禁止抬脚；本轮没有触发此门禁，尚未在箱沿附近完成物理验证。保持5cm抬升；该选项明确不是上台轨迹。多项式参考速度保守界分别.1153/.1175m/s、加速度.1683/.1090m/s²（精确值见plan），不是实测上限或电机安全证明。

| 配置(seed513，开发样本) | 完整回合/无终态 | FL/RR/FR/RL落稳 | 四步+1秒稳 | 20cm成功 | 安全终止 | 末态最近足端距箱沿中位 |
| --- | --- | --- | --- | --- | --- | --- |
| 8cm/1.8s旧行为回归 | 32/0 | 32/32/32/32 | 31/32 | 0/32 | 0 | 50.66cm |
| 16cm/3s | 32/0 | 32/32/32/0 | 0/32 | 0/32 | 0 | 42.61cm |
| 24cm/4.1s | 32/0 | 24/24/24/0 | 0/32 | 0/32 | 0 | 35.90cm |

两组候选都未完成四步+停稳，更未上箱，不能用接近距离或较小峰值代替任务改善完成。16cm组32个RL均已起脚，24秒终止时仍在摆动；24cm组只24个回合进入后续步序，其余8个仍卡首脚。没有延长24秒，也不冒充原12秒验收。

### 名义可达性与失败原因

16cm组完整轨迹的名义FK残差最大约0.14微米，inspect env14首脚实测跟踪峰差2.63mm。24cm组第一步名义残差全程峰值47.43mm，后续步序峰值33.55mm；首步失败env为1、2、3、11、12、18、20、29。

独立重建这8个末态：读取同一冻结USD的关节硬限位，按实际0.9因子生成软限位，结合每回合捕获姿态±.7rad局部包络，对真实足端目标和机身姿态做IK、截断后FK。重建名义关节与记录差均<1e-6rad；实际被截断的足位残差为30.40–39.27mm，8个FL法向力均0、恢复承重进度均0。要求的FL大腿偏移约−.86至−.99rad，小腿偏移约+.83至+1.20rad，超过局部包络；部分环境同时遇到小腿软上限−.932rad。不能把它只解释为等待不够，也不能放宽落脚误差门槛或执行器限制。这里是名义几何不可达证据，不是所有动态失败原因的穷尽分析。

### 完整回合质量和原始证据

三批全回合数值相同：三足支撑99.827%、最长腾空.060秒、竖直速度峰值.951424m/s、最大法向足力203.635N、最大单关节累计力矩饱和.280秒。全回合步态仍按既有口径排除前.10秒，保留此后的初始化瞬态；饱和累计包含初始化。两组候选各环境各关节相比cj/513最大饱和增量0。

接管后另计：三足支撑100%、腾空0；16cm/24cm竖直峰值均约.073686m/s，法向足力峰值128.546/123.116N（旧8cm133.205N）。这些低冲击指标没有解决任务失败，不能据此实机放行。

27项数学/记账检查通过，包含可变步长轨迹自动微分的速度/加速度、端点静止与环境坐标下的箱沿门禁；Python编译和diff检查通过。默认关闭新选项的baseline513逐值复现cj/review513所有原32终态和质量指标、资产、执行器延迟，未替换旧四步参考。原d任务4份冻结源码SHA不变，44份Python清单及实际env.yaml哈希归档；新选项仅是已评估的诊断，不是发布策略。

产物本地`../artifacts/go2-piper/climb-terrain-approach-20261002-ck/`、远程`/path/to/artifacts/go2-piper/climb-terrain-approach-20261002-ck/`：plan、baseline-plan、三组完整报告/YAML/日志、source脚本快照、approach-analysis、reachability-analysis、authored-joint-limits及SHA清单。8cm默认回归只复现已用513种子，不计新增验收。没有新增录像，8788仍为cj平地四步版。全部本轮远程进程已结束。

下一步：根据关节限位及整个摆动路径预检落脚点，把机身前进与抬升纳入同一可达轨迹规划，并核对从原始起点到20cm台顶的总时间预算。需先得到地面接近→首脚上台→混合支撑面的实际完整回合；不继续只扫描步长/等待时长，也不恢复已否决的NAV直接接管。保留原24秒慢爬、20cm、停稳与安全门禁；原12秒及最终两组未用种子验收仍独立，当前均未通过。

<a id="record-0175"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 关节与机身联合预检 cl–cm，以及整段时间预算纠偏（2026-10-02）

**关键结论：现有固定慢步序不具备24秒完成原任务的时间条件。** 用cm/search28保存的32个首轮准备前足位，按24cm固定步长、支撑足参考不滑移计算，到四脚均进入原箱体合法区域（x>.79m）至少需15–19次摆腿；每次2.8秒，仅摆腿就要42.0–53.2秒，尚未计准备/卸载/支撑转移/恢复承重/抬升与最后1秒停稳。cj两条早期样本复算为16步/44.8秒。该下界适用于这个固定名义安排，不是平缓攀爬物理不可能，也不代表已规划越沿轨迹。

停止沿这个固定节奏继续扫描步长或等待时间。下一步以[整段参考与时间预算修正](#source-climb-terrain-reference-plan-20261002-cn)为准，把接近、越沿、混合支撑和机身抬升连成完整参考，再做动力学评估。不会通过移近初态、延长回合、降低20cm箱或放松成功/执行器门禁伪造通过。当前内部足端/机身速度预算和固定卸载时长是诊断设计，不是实测电机参数；今后分配时程应依据完整路径与原执行器限制，并通过真实载荷/运动验证。

### 已实现的预检与实际边界

默认关闭`--plan-approach`：从实际足位、全身COM、机身姿态和关节状态，同时选择2–12cm机身前移与三足支撑转移位置。对支撑转移、摆腿以及3mm触地搜索端点进行65点采样，核对FK、USD软限位和原捕获姿态±.7rad包络，留.025rad裕量；采样关节速度/加速度（有限差分乘1.1）须≤1rad/s、5rad/s²，机身参考≤.075m/s、.133m/s²。此处的采样不是连续时间安全证明，也不包括整条碰撞/电流/热模型。

预检无可行路径时，首次起步留在四足准备，后续步序留在四足承重阶段，不开始卸载和摆腿。实际接触、卸载、承重、最终1秒静止与原安全终止仍生效。首次准备后沿用既有实测站姿重捕获，后续步序保持原捕获契约；新规划不会放宽关节包络来追目标。

cl只用既有优选COM转移点。cm的`--approach-support-search`在每个前移量下比较6个支撑位置，均在按未来前移量与3cm裕量收缩的支撑三角形内，转移距离仍≤14cm。新增保存每次规划的59维原始输入，便于独立重算。两批都比较4.1秒与2.8秒摆动；规划模式足端参考保守速度界可至.18m/s、加速度仍≤.4m/s²，并同时通过上述关节/机身预算，不改变实际动作链的2.5rad/s、15rad/s²腿部参考硬限制。

### 完整回合与任务结果

| 批次(seed513，全部是开发样本) | 完整终态/无终态 | FL/RR/FR/RL落稳数 | 四步+1秒稳定 | 20cm成功 | 安全终止 | 首次预检拒绝且四足保持 |
| --- | --- | --- | --- | --- | --- | --- |
| cl/plan41 | 32/0 | 23/23/2/0 | 0/32 | 0/32 | 0 | 9 |
| cl/plan28 | 32/0 | 19/19/12/0 | 0/32 | 0/32 | 0 | 13 |
| cm/search41 | 32/0 | 23/22/1/0 | 0/32 | 0/32 | 0 | 9 |
| cm/search28 | 32/0 | 20/19/18/0 | 0/32 | 0/32 | 0 | 12 |
| cm/baseline关闭新规划 | 32/0 | 32/32/32/32 | 31/32 | 0/32 | 0 | 不适用 |

所有候选均未通过，未替换cj平地参考。cm/search28只有5个RL起脚，search41没有RL起脚。原ck首脚失败的8个环境中，cm仅env12实际完成首脚，其余被预检挡住；不能把避免悬空失败说成8个都已恢复通过。实际执行路径名义FK峰差cl/cm约.081–.106mm，较ck的47.43mm截断残差减少，但包含筛掉不可行路径的影响，不代表完整任务改善完成。

### 步态、载荷与审计

以上五批全回合均为三足99.827%、最长腾空.060秒、竖直速度峰值.951424m/s、法向足力峰值203.635N、最大单关节累计力矩饱和.280秒。仍使用既有步态统计前.10秒排除口径并保留之后初始化瞬态；饱和累计包含初始化。相比同种子cj，各环境各关节累计饱和最大增量0。

接管后另计均三足100%、无检测腾空、竖直峰值约.073686m/s；法向足力峰值cl/4.1为137.972N、cl/2.8为131.521N、cm/4.1为149.126N、cm/2.8为150.255N，旧8cm对照133.205N。因此不能声称新增规划使所有冲击指标降低，更不能据此实机放行。

独立审计核对了首次预检失败未抬脚且四足保持、后续预检失败未卸载，以及所有已释放腿的实测接触/力/速度/支撑裕度门禁。cm按保存输入重算首步32+32和最后一段20+23个规划，可行性决策和机身前移量一致。CPU/局部坐标与GPU/世界坐标的采样导数并非逐值相等：最大关节加速度统计差约.01204rad/s²，受浮点坐标消减与二阶差分放大影响；审计逐列记录误差及容限，没有把它写成逐值复现。

cm关闭新选项的32个完整终态、步态/关节运动/保持指标、资产和延迟逐值复现cj/review513。28项数学/记账检查通过，新增支撑位置搜索的平移不变性、1001点更密关节路径复查与不可达路径拒绝；编译和diff通过。d任务4份冻结源码不变，44份Python清单与实际YAML哈希归档。没有新PPO训练、没有未见种子验收、没有新录像；8788仍是cj旧平地四步。

原始结果与源码位于本地仓库外及远端的`climb-terrain-jointplan-20261002-cl`和`climb-terrain-supportplan-20261002-cm`。保存plan、完整报告/YAML/日志、source快照、approach-analysis、planner-audit、schedule-lower-bound及全部32状态预算、SHA清单和重算脚本。cl曾准备但未执行baseline启动文件；实际回归只在最终cm源码上执行。所有本轮进程已结束；下一轮按整段参考计划推进，不重复本批固定慢节奏扫描。

<a id="record-0176"></a>

来源：CLIMB_CRAWL_STATUS_20261001_CN.md。

## 整段几何与执行器参考时间预检 cn（2026-10-02，离线，不是Isaac评估）

本轮没有重新扫描旧2.8/4.1秒固定摆腿，也没有继续PPO。先核对远端双GPU空闲、无训练/诊断进程，在保存的cm/513实际准备前状态上，生成原起点到台顶的整段参考草案。`scripts/plan_crawl_route.py`是独立数学工具，不被当前控制器加载；所有物理评估和录像仍只在远端。本轮未产生新的物理回合或视频。

### 新增的整体约束

以FL→RR→FR→RL足序递推，同时求解每步四个机身位置/俯仰/横滚节点，保留测量的偏航；准备阶段固定四足、摆腿阶段固定其余三足。第一对短步10cm，此后草案步长20cm，遇箱沿先在x=.69m地面停脚或落到x≥.83m台面。地面使用4.5cm平滑弧线；跨20cm箱沿先将脚抬到高于目标面3cm，再越沿、下降到足坐标z=.2245m。按实际22mm足碰撞球加2mm偏置形成24mm包络，检查与箱体的距离。此处只检查足部包络，不包含小腿、底座、机械臂的完整碰撞网格。

每步将机身与足轨迹联合做IK，检查USD软限位和每段捕获姿态±.7rad包络；优化留.03rad余量，385点复查至少.025rad，不能把优化器的“成功退出”当作路径通过。准备阶段检查四足凸包、摆腿检查三足凸包；优化目标裕度32mm，复查至少30mm。**COM只用了初始实测整体质心在机身坐标中的固定偏置，没有按腿姿更新全身COM，因此这些是几何近似，不能称为真实三足支撑或稳定性证明。** 后续实际执行还必须使用实测载荷、接触、速度与原安全门禁。

全段时间由每步关节路径差分，按原腿参考2.5rad/s、15rad/s²重定时，再给每段时长10%余量。该数值只是采样参考的均匀重定时估计，不是连续时间最优控制下界，也不是实测电机额定性能。没有把接触等待计为零后宣称可交付，而是将零额外等待作为最乐观比较，先拒绝预算已不成立的草案。

### 结果：没有形成可执行的24秒整段候选

| cm/513保存状态 | 连续名义可行步数 | 已到顶的名义足数 | 已完成前缀参考时间（无/有10%余量） | 下一个失败阶段 |
| --- | --- | --- | --- | --- |
| env0 | 25 | 3 | 32.32 / 35.55秒 | RR跨沿，求解器未找到满足预检余量的轨迹 |
| env7 | 19 | 2 | 23.83 / 26.21秒 | RL跨沿，优化退出成功但密采样关节余量仅.02342rad，低于.025rad |
| env14 | 14 | 1 | 17.48 / 19.22秒 | FR跨沿，求解器未找到可行轨迹 |

三条整段路线均未完成；表中时间只计算已通过的前缀，未包含失败步、初始化接管、实测卸载/承重等待和最终1秒停稳。env0与env7在这些缺项之前就已超24秒。因此没有将这批参考交给Isaac执行，也不为它启动残差RL。局部优化失败不证明其他身体轨迹或其他落点物理不可行；尤其env7是新增预检余量拒绝，不能伪称已经违反原执行器硬限位。

**下一步转为整个身体连续轨迹与步点、接触时序的联合规划。** 这个逐步停车的几何工具可继续用于拒绝不可行段及复算预算，但不能继续靠扫描相同停顿方案、缩短固定等待或只增加PPO轮数推进。需要允许准备下一只脚的载荷转移与前脚真实落地/承重合理衔接，并验证承重而不是删除接触等待。整体参考须补上随腿姿变化的全身COM、支撑力可行性，以及小腿/底座/臂净空；获得有可信24秒预算的完整路径后再进行远端物理评估。原12秒验收仍独立，任务起点、20cm箱、最终1秒停稳及碰撞/执行器门禁不变。

### 验证、物理指标与产物

4项新增检查通过：与既有USD腿模型在含偏航/横滚/俯仰与世界平移下的FK/IK独立互证；箱沿24mm足球包络净空和端点静止；地面足弧/机身节点连续性；参考重定时对解析五次曲线速度/加速度及密采样复核。原28项检查、Python编译与diff检查通过。58个已接受名义步再次用每阶段1537点重建，最小关节余量.02687rad，冻结COM支撑近似最小32mm，参考峰速≤2.27312rad/s、加速度≤12.40125rad/s²。这里没有实际力矩、温升或动态安全结论。

本轮物理指标全部**无新数据**：完整回合成功率、真实三足比例、腾空、竖直速度、接触冲击、累计力矩饱和均不能由上述几何报告计算。最新实际数据仍cm：20cm成功0/32，32个完整终态/无缺失；全回合三足99.827%、最长腾空.060秒、竖直峰值.951424m/s、法向足力203.635N、累计饱和最大.280秒（含初始化）。接管后另计三足100%、腾空0，cm法向峰值149.126/150.255N。没有新独立验收或新录像，8788还是cj旧平地四步。

本地产物`../artifacts/go2-piper/climb-route-preflight-20261002-cn/`，远端同名目录：`route-preflight.json`保留完整输入、每步身体节点/落点/关节/时程与失败记录；`dense-audit.json`为1537点复核；`scripts/`为源快照，另有来源/SHA清单。运行控制器、冻结d任务和冻结策略均未改；PUSH/MuJoCo/实机保持暂停。

<a id="record-0177"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

# CLIMB 箱沿训练：2026-10-02

<a id="record-0178"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## 最新：定位eu底座撞箱，ew增加机身路径净空检查（2026-10-02 22:56）

最新视频ev/8792中env6在33.82秒终止，四脚仍有接触，实测base合力约[−2.0503,0,4.0922]N。追溯发现新机身选择器只优化关节余量，忽略了机身与箱沿的空间关系：目标root约[.45066,.03273,.28326]、近乎水平，使底座前端进入20cm箱沿。直接读取USD实例化碰撞mesh并转换到base坐标，包围范围为x[−.127998,.331958]、y[−.097223,.096777]、z[−.096839,.088834]；有向包围盒与箱体分离轴间隙在目标处为−13.58mm、实际终止处为−6.78mm。包围盒重叠本身不证明精确mesh穿透，但与独立实测底座接触一致；不能一概归因于失去支撑。依据和报告哈希保存在ew/eu-collision-diagnosis.json。

新增默认关闭`guidance_body_collision`：在原15个混合支撑机身候选上，沿运行时同样的位置/四元数插值采21点，检查真实USD底座碰撞mesh的保守有向包围盒与固定箱体至少1cm分离，同时检查四腿全路径名义软限位、按当前实测力矩估计的加载目标软限位及1mm FK残差。端点.03rad余量和原机身/关节平滑限制保留；无可行候选则保持当前姿态、禁止卸载。记录所选/保持路径最小间隙和关节余量。该检查仅覆盖base包围几何，未覆盖其他连杆、两采样点之间、跟踪误差和未来载荷变化，仍需原碰撞/执行器/承重门禁与物理验证；不能当作安全证明。

18项引导数学检查、编译与差异检查通过。新增检查包含USD实例变换、拒绝本次过低目标、接受抬高/前倾可净空姿态、世界平移不变性、端点无碰撞但路径穿过箱体、关节可行但碰撞时拒绝。远端`climb-body-clearance-20261002-ew`于22:53:17启动监控PID575279，GPU0顺序运行eu feasible100回归、开启净空检查100秒，各32环境seed513、env6轨迹。已确认首批环境初始化完成并进入rollout，无重复训练。仍为箱沿100秒诊断，未新增PPO，未计入24秒或原起点12秒验收；先检查ew进程与两份结果再继续。

最新已完成eu两批均0/32且无缺失：baseline24超时/1底座/6姿态/1低姿态、三足99.861%；feasible100为15超时/9底座/8姿态、三足99.764%。两批最长腾空0、竖直速度峰值1.025006m/s、单足合力峰值373.566N、含初始化最长累计饱和.460s。ew尚无结果，不能声称已改善。最新原速视频仍 `index.html` 。源码与交接更新指定分支，实验快照/诊断位于本地及远端仓库外；PUSH、MuJoCo、实机暂停。


用户要求直接训练攀爬，NAV已有稳定行走能力。当前任务改为从20cm箱沿学习抬前脚、载荷转移、抬升机身和后脚跟进。平地逐脚行走与离线路径搜索不再作为主任务。

<a id="record-0179"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## 训练与验收分开

新增任务 `GO2-PIPER-Box-Climb-Stages`，304维观测、18维动作，腿部动作围绕站姿参考学习残差；本实验机械臂保持参考姿态，策略的臂动作不执行。脚步选择由几何和触地状态引导，先前脚后后脚，保留抬高后才前移、落稳后才换腿。奖励覆盖落脚跟踪、三足支撑区域、适应地形的机身姿态及实际完成换脚，仍保留冲击、滑移、竖直运动及力矩惩罚。奖励不代表动作已经实现。

`Stages-Play`默认使用原起点，仅显式指定 `--climb-stage-bank` 才使用训练初态，并在报告标记 `training_curriculum_diagnostic`。近箱训练成功不能算原任务验收。保持20cm箱、原碰撞/执行器限制/停稳1秒条件。24秒慢爬与原12秒验收独立。

<a id="record-0180"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## 起点检查

以下均为零输出actor的32回合远端Isaac诊断，全部终态完整，均未成功登台。足力是单足合力峰值；饱和时间是单环境单关节累计最大值，包括启动阶段。三足支撑为按有效采样数加权比例，腾空/竖直速度/足力口径见原慢爬记录。

| 实验 | 结果与原因 | 三足 | 最长腾空s | 竖直峰值m/s | 足力峰值N | 饱和s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| cp | 0/32；初始PD目标错误为零 | 11.404% | 23.140 | 1.952 | 1196.267 | .440 |
| cq | 0/32；修正重置目标，显式PD增益误读为PhysX零增益 | 42.625% | .220 | 2.018 | 1623.052 | .460 |
| cr | 0/32；增益修正，27姿态终止、5超时；四阶段名义姿态拒绝用于训练 | 97.273% | 0 | .775 | 170.545 | .540 |
| cs | 0/32；32姿态终止 | 81.200 | 0.000 | 0.638 | 136.807 | 0.260 |
| ct | 0/32；32底座接触，均在采样排除期结束前终止 | 不适用 | 不适用 | 不适用 | 不适用 | 0 |
| cu | 0/32；32站满24秒，零安全终止（可用起点） | 100.000 | 0.000 | 0.553 | 111.338 | 0.200 |

cs将cm/env14/step150实测过渡姿态及关节目标平移到箱沿，仍32次姿态终止（1.02–1.40秒），不能作为稳定静态初态。ct采用原默认站立参考、前脚x=.68；32回合均在.10秒触发底座碰撞，起点拒绝。cu将前脚初始x改为.60（箱面x=.75），首次目标x=.83、z=.2245，仍直接训练上台，远端起点检查已通过（32回合站满24秒，零安全终止）。最新源码移除已拒绝的初始静力补偿，原起点评估也使用相同默认站立参考，避免引入额外控制差异。

所有目录在 `/path/to/artifacts/go2-piper/` 与本地仓库外 `../artifacts/go2-piper/` 同名保存：

- `climb-stages-train-20261002-cp`
- `climb-stages-reset-20261002-cq`
- `climb-stages-pdgain-20261002-cr`
- `climb-edge-reset-20261002-cs`
- `climb-edge-default-20261002-ct`
- `climb-edge-clearance-20261002-cu`

每个目录的plan记录来源哈希，source-payload保存当次实际源码。不能用仓库最新代码复现旧实验后宣称相同结果。

<a id="record-0181"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## 后续训练

2026-10-02 14:01:53（北京时间）已启动cu隔离箱沿PPO，训练PID526883、监控PID526884，目录`climb-edge-clearance-20261002-cu`。不要重复启动。已确认实际训练进入第33轮，run=`2026-10-02_14-02-23_edge_stages_seed631`，env/agent落盘配置与启动参数一致；这不是策略评估结果。训练参数：512环境、seed631、300轮、std=.15、固定lr=1e-4、每50轮保存。监控已启动，在50/150/299轮各跑训练起点及原起点32回合诊断（seed513，已用调参种子）。候选固定后再选择未用种子，完成两组各32回合、每组至少30成功且无未完成，以及真实速度录像。PUSH/MuJoCo/实机暂停。

<a id="record-0182"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## cu训练中间检查（北京时间14:07）

训练已确认进入116/300轮，训练及自动评估进程均存活，未启动重复作业。第50轮箱沿起点评估完成：**0/32成功、32超时、无缺失终态、零安全终止**；三足支撑100%，无腾空，竖直速度峰值.548885m/s，单足合力109.962N，含初始化的单关节累计饱和最大.20秒。

全部32回合仍停在首只前脚抬升阶段（phase=.25，未检测到完成抬脚），env0实测该脚最高仅.02978m，没有台面承重。此结果是稳定站立，不能算攀爬改善。第50轮原起点诊断正在执行，保留原计划150/299轮检查后再决定下一次训练修改，不根据早期奖励扩大或延长同一训练。本地已保存报告及`model50-stage-diagnosis.json`。

<a id="record-0183"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## cu最终结果及cv/cw下一轮

300轮训练和六批评估均完成，旧进程已退出。以下全部为24秒任务、seed513，均32个终态、零缺失、零安全终止、32超时；未通过攀爬要求。

| 轮次 | 起点 | 成功 | 三足支撑 | 最长腾空s | 竖直峰值m/s | 单足合力N | 累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 箱沿训练起点 | 0/32 | 100.000% | 0.000 | 0.549 | 109.962 | 0.200 |
| 50 | 原起点 | 0/32 | 99.830% | 0.060 | 0.936 | 209.523 | 0.300 |
| 150 | 箱沿训练起点 | 0/32 | 100.000% | 0.000 | 0.524 | 102.998 | 0.200 |
| 150 | 原起点 | 0/32 | 99.827% | 0.060 | 0.909 | 200.378 | 0.260 |
| 299 | 箱沿训练起点 | 0/32 | 100.000% | 0.000 | 0.489 | 119.588 | 0.220 |
| 299 | 原起点 | 0/32 | 99.830% | 0.040 | 0.840 | 196.725 | 0.260 |

所有终态仍为第一只前脚、相位.25，未完成抬脚。最终env0整段最高脚高.02978m（初始化即在这一高度），终末首脚负载45.87N，脚高.02328m，对应参考高.25450m。完整报告哈希逐份复核，汇总在cu/final-comparison.json；model299（SHA `8da0820f4334fd90e8ff843e6ba274126d4887f0b24e4829dfd4389c9c70bf32`）已本地备份，仅作为继续学习的初始化。

cv/cw新增三足支撑约束下的首脚卸载反馈（按总实测负载归一），摆动期首脚离地才获得接触奖励；原来的3/4站立分不再保留。新高度奖励只支付同一步内最高抬脚高度的正增量，每步最多12分；悬停或重复抬落不会持续领取高度奖励，换腿/重置清空记录。其余三脚缺承重或全身腾空时，卸载和抬高均不得分。门禁与控制轨迹限速没有改变；这些只是训练反馈设计，不是实际步态改善证明。

北京时间14:49:27两组已启动。cv训练/监控PID530854/530855，cw训练/监控PID530857/530858。目录 `climb-lift-std15-20261002-cv` / `climb-lift-std45-20261002-cw`，各512环境/300轮、同seed632及cu/model299初始化；std=.15/.45为两组之间唯一设置差异，固定lr1e-4。训练GPU0/1，自动评估等各自训练退出后使用同一GPU，避免重叠占用。评估仍为50/150/299轮各箱沿+原起点32回合；seed513只用于诊断。启动前同一零actor回归通过：32个终态、trace_env0、三足/腾空/冲击指标、关节运动指标逐值等于cu零actor报告，见cv/reward-control-regression.json。6项阶段数学检查通过，包含腾空/缺支撑/非活动阶段/仍在承重时无抬脚奖励的反例。最终仍须独立原起点验收和真实速度录像。

运行确认：cv/cw均已进入第10/300轮，实际run分别为`2026-10-02_14-50-06_lift_std15_seed632`与`2026-10-02_14-50-06_lift_std45_seed632`。512环境、24秒、lr1e-4、新奖励项和起点路径已通过落盘配置核对，两组任务源码SHA相同。

启动记录补充：14:47的首次启动因脚本替换run_name时误改了初始化checkpoint路径，在加载权重时退出，未进行训练迭代。保留failed-launch-record与日志；修正后14:49:27重启，并在启动前逐项检查真实命令中的checkpoint路径及SHA，旧监控已终止。

<a id="record-0184"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## cv/cw中间评估（15:07）

2026-10-02 15:07核查：cv/cw的300轮训练均已结束，两个自动评估监控仍运行；各自第50轮箱沿与原起点评估均0/32、32超时且无缺失，尚未检测到首脚抬起。第150轮箱沿评估进行中，最终299轮结果未出；不要重复训练或在最终诊断前延长相同配置。

四批均零安全终止。三足、腾空、竖直速度、单足合力口径与前表相同；饱和包含初始化。这里只报告中间模型，不作为最终模型结论。

| 模型 | 起点 | 成功 | 三足支撑 | 最长腾空s | 竖直峰值m/s | 单足合力N | 累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cv/50 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.485 | 122.833 | 0.220 |
| cv/50 | 原起点 | 0/32 | 99.833% | 0.040 | 0.780 | 205.285 | 0.280 |
| cw/50 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.474 | 126.168 | 0.220 |
| cw/50 | 原起点 | 0/32 | 99.838% | 0.040 | 0.776 | 205.327 | 0.340 |

第50轮箱沿env0首脚终末负载cv=38.07N、cw=51.93N；两者整段最高脚高都仍为初始化的.02978m，全部终态未完成首脚抬升。更低负载本身不算攀爬进展。已下载报告并核对SHA/32终态完整性，保存各目录的interim-comparison.json。训练进程已退出，监控继续执行150/299轮，不启动重复作业。

<a id="record-0185"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## cv/cw最终结果与cx/cy机身姿态对照（15:48）

12批评估完成，全部32回合超时、零安全终止、无缺失终态；没有一只脚在台面承重。指标口径同前，24秒训练/诊断不是原12秒验收。

| 模型 | 起点 | 成功 | 三足支撑 | 最长腾空s | 竖直峰值m/s | 单足合力N | 累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cv/50 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.485 | 122.833 | 0.220 |
| cv/50 | 原起点 | 0/32 | 99.833% | 0.040 | 0.780 | 205.285 | 0.280 |
| cv/150 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.491 | 127.661 | 0.320 |
| cv/150 | 原起点 | 0/32 | 99.846% | 0.040 | 0.789 | 198.933 | 0.440 |
| cv/299 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.479 | 136.811 | 0.340 |
| cv/299 | 原起点 | 0/32 | 99.827% | 0.040 | 0.790 | 204.135 | 0.540 |
| cw/50 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.474 | 126.168 | 0.220 |
| cw/50 | 原起点 | 0/32 | 99.838% | 0.040 | 0.776 | 205.327 | 0.340 |
| cw/150 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.480 | 139.046 | 0.220 |
| cw/150 | 原起点 | 0/32 | 99.778% | 0.040 | 0.740 | 205.713 | 0.340 |
| cw/299 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.486 | 148.229 | 0.220 |
| cw/299 | 原起点 | 0/32 | 99.793% | 0.020 | 0.812 | 206.469 | 0.360 |

终态锁存的离地记录不代表有效登台。cv/model299箱沿30/32曾离地，但全部相位.25，env0脚高峰值仅.05784m；cw/model299有24/32曾离地、17/32相位已进入前移（.75），env0脚高峰值.22565m。cw仍后退、降低机身并失去目标可达范围。未因这些局部变化将其记作成功。

`scripts/audit_climb_stage_reach.py`将实测终态关节/姿态与既有经过核对的GO2几何复算，当前脚位误差最大1.684微米；保持各自终态机身姿态，31/32的台面上方目标无法由腿长达到，目标残差最大81.675mm。结果及输入SHA在cw/terminal-reach-diagnosis.json。此处不包含机身后续运动、关节限位和碰撞，不能用于声明完整攀爬不可行。

cx/cy目录为`climb-body-continue-20261002-cx`、`climb-body-reach-20261002-cy`。共同从cw/model299（SHA `d414c8256132903fb8898a521559c73f3300f36338330ba0f4894b02fcc53151`）初始化，seed633、512环境、std=.45、600轮、lr1e-4、每100轮保存，GPU0/1。cx继续相同奖励；cy增加目标距髋部的几何外界裕量奖励（权重6，保留3cm距离），同时提高地形姿态权重至6。几何半径由运行时髋/大腿/小腿/脚位置与刚体链尺寸计算，没有修改资产。外界只提供必要条件，不是充分可达性或理论创新结果。两组对比的是一组机身引导奖励，不能分别归因于其中某一权重。

同一cw/model299回归已通过：新版默认关闭几何奖励时，32终态、trace、步态和关节质量指标与cw原报告逐值相同，见cx/control-regression.json。两组于15:50:33启动，cx训练/监控PID535142/535144，cy为535145/535147。动作参考/PD/延迟/速率/加速度/20cm箱/碰撞/停稳门禁不变。没有接入新的IK动作控制，原因是先检查发现终态落点已不可达，需要先改善身体姿态。监控等各自训练退出后评估100/300/599轮，每个模型各箱沿及原起点32回合。运行确认：两组已进入13/600轮，实际奖励配置cx为reach0/pose2、cy为reach6/pose6。run分别为`2026-10-02_15-51-00_body_continue_seed633`与`2026-10-02_15-51-01_body_reach_seed633`，运行时配置哈希已保存。训练上限4800s、监控7200s、单评估700s。7项阶段数学检查通过，新增后退越界与环境平移不影响几何裕量的检查。

<a id="record-0186"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## co模型审计（辅助结果，不是攀爬训练成果）

实际PhysX默认总质量21.765kg，USD直接读取为20.765kg；差异来自end_effector的运行时1kg与USD显式0kg。未更改资产或物理质量。原控制器本来就读取实际PhysX质量/COM；问题只在新增离线模型的USD读取方式。

运行时属性对齐后，回放既有4800帧的全身COM误差最大2.119微米、足端FK最大2.267微米。仅用USD时COM误差最大17.028mm；cn本身冻结实测COM近似的误差为3.686mm，二者不可混淆。cn/env14的14步静态审计支撑裕量最小30.483mm、支撑力19.710–116.979N、静态力矩/上限最大.61448。此审计不包含惯性、摩擦、冲击或温升，不能推翻cn整段时间预算失败，也不能证明动态可执行。

结果在 `climb-centroidal-audit-20261002-co/centroidal-audit-final.json`，包含远端初始化快照、实际属性、回放与来源哈希；没有新增技能回合。

<a id="record-0187"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## cx/cy最终结果与显式足端引导诊断（16:48）

两组600轮训练及12批评估均结束，已核对远端无遗留训练/监控进程；384个终态齐全，完整攀爬全部失败。全部为24秒诊断、seed513；安全标志可能同时触发，不能相加作为回合数。含初始化的力矩累计饱和口径不变。

| 模型 | 起点 | 成功 | 三足支撑 | 腾空s | 竖直峰值m/s | 单足合力N | 累计饱和s | 终止标志 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cx/100 | 箱沿 | 0/32 | 99.992% | 0.000 | 0.470 | 140.660 | 0.200 | 32time_out |
| cx/100 | 原起点 | 0/32 | 99.812% | 0.020 | 0.808 | 204.533 | 0.360 | 32time_out |
| cx/300 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.457 | 152.981 | 0.220 | 32time_out |
| cx/300 | 原起点 | 0/32 | 99.509% | 0.020 | 0.667 | 194.314 | 0.260 | 21time_out、11base_contact |
| cx/599 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.501 | 154.712 | 0.220 | 26time_out、6bad_orientation |
| cx/599 | 原起点 | 0/32 | 99.739% | 0.040 | 0.777 | 230.464 | 0.280 | 31time_out、1low_posture |
| cy/100 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.473 | 137.896 | 0.200 | 32time_out |
| cy/100 | 原起点 | 0/32 | 99.814% | 0.020 | 0.712 | 196.562 | 0.360 | 32time_out |
| cy/300 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.461 | 136.039 | 0.200 | 32time_out |
| cy/300 | 原起点 | 0/32 | 99.631% | 0.040 | 0.813 | 189.652 | 0.260 | 24time_out、5base_contact、4bad_orientation |
| cy/599 | 箱沿 | 0/32 | 100.000% | 0.000 | 0.467 | 197.431 | 0.220 | 32time_out |
| cy/599 | 原起点 | 0/32 | 99.712% | 0.040 | 0.803 | 259.812 | 0.280 | 31time_out、1bad_orientation |

最终箱沿：cx全部32回合曾离地、全部停在前移相位.75，6次姿态终止；cy全部曾离地、30个停在前移相位、2个在抬升相位，32超时。两者台面承重始终为0。cy机身引导改善了固定终态的落点几何范围：cx的32/32终态目标均超过腿伸展范围（残差最大105.979mm），cy的32/32均在该几何范围内；实测脚位FK误差分别1.454/1.608微米。但这不包含软限位、支撑稳定或碰撞证明，实际脚仍未上台，不能将其算作攀爬达标。cy终态root x=.272–.390、z=.218–.257m，机身仍偏低。

不延长相同奖励训练。新增默认关闭的StageGuidance：用经Isaac核对的腿部几何，先平滑转移机身以使全身COM进入其余三脚支撑三角形，再按真实接触门控的足端参考生成关节目标；支持转移等待至少1.5秒且实测COM裕量达到15mm，摆腿4秒；IK残差超过1mm或距离软限位不足.01rad时拒绝更新名义目标，保留原关节参考速率/加速度限制。机身目标与接触等待仅为实验控制，尚无动态稳定性保证。手臂仍保持原参考，原20cm箱、碰撞、执行器和停稳门禁不变。

cz隔离目录`climb-guided-edge-20261002-cz`首先跑零actor的关闭引导回归和开启引导箱沿诊断，各32回合/24秒。这是首脚可执行性诊断，不能冒充完整任务成功，也不是重新训练平地走路。北京时间16:48:02启动，baseline/guided PID539148/539149。新增3项纯数学检查及原7项阶段检查通过；待实际物理结果再决定训练。没有新的PPO作业。

<a id="record-0188"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## cz未通过；da反馈诊断与用户要求的录像（16:54）

cz两批均32个完整终态。关闭引导的零actor回归逐值复现cu的全部32终态、完整trace、步态和关节指标。开启引导仍0/32，17次姿态终止、15超时，无台面承重；14个终态到达首脚前移相位，18个仍在支撑转移。三足97.760%、最长腾空0.000s、竖直峰值0.552m/s、单足合力140.218N、含初始化累计饱和0.200s。env0机身在1秒已由x=.422后退至.234m，随后失稳；名义支撑位姿没有被实际受载机器人保持，拒绝此配置。

da目录`climb-guided-feedback-20261002-da`新增实测机身位姿/速度反馈（比例.5、阻尼.08s，足端修正范数上限5cm），仍经原IK残差、软限位检查与关节参考限速。此为待验证补偿，不宣称已消除失稳。用户此时要求运行视频，优先录制最新训练cy599与最新da零actor控制诊断；db目录`climb-edge-review-20261002-db`从各自冻结源码运行32回合并录制env0原速视频。16:53:49启动，guided/trained PID539641/539642，GPU0/1。da预先准备的独立zero/residual launch脚本尚未启动，避免重复运行。没有新PPO。

<a id="record-0189"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## db录像与da物理结果（16:59）

两段远端原速录像均为1280×720、25fps、600帧/24秒，各包含env0完整回合。训练版cy599的全部32终态、trace、步态和关节指标逐值复现原评估，不新增独立验收样本。da零actor加机身反馈仍0/32，21超时、4底座接触、7姿态终止，无缺失、无台面承重；三足97.895%、腾空0.220s、竖直峰值0.600m/s、足力191.331N、含初始化累计饱和0.760s。相对cz虽然提前终止数变少，腾空和饱和变差，不能称控制已改善或通过。

视觉检查发现默认机位远且箱子遮挡前脚，因此保留db原录像，另外开dc侧面近景重录。dc使用同一任务控制与同一策略/零actor，仅新增可显式保存的摄像机位置/目标参数；相机环境坐标分别(.35,1.7,.85)、(.55,0,.25)。目录`climb-edge-close-review-20261002-dc`，16:59:33启动guided/trained PID540666/540668。两份来源SHA已核验。待复核各自32终态与db一致后提供用户。下一步继续箱沿受载支撑/落脚执行性；不能直接扩大失败控制的训练，更不能回到平地走路主线。

<a id="record-0190"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## dc近景视频交付

dc两段均已完成并下载：`trained-env0.mp4`、`guided-env0.mp4`，均为1280×720/25fps、600帧、24秒，无加速/剪辑。全部64个终态、完整env0轨迹、步态和关节指标逐值等于db相应报告。视频解码与时长核对通过，抽帧视觉检查确认前脚不再被箱子遮挡；两个版本都无台面承重。入口 `index.html` ，本地HTTP PID1983827。近景不新增物理验收样本。源码、报告、视频与SHA在dc目录，`verification.json`保留核验结果。dc两个进程已退出，没有新训练或评估运行；不重启cz/da预备脚本。

新控制代码保持默认关闭；10项本地纯数学检查通过，cz关闭引导回归逐值一致，dc补充验证开启反馈的录像重放。cz/da实测失败及其全部指标保留，不作为可用控制策略交付。

<a id="record-0191"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## dd/ee受载目标诊断与ef残差训练（2026-10-02 17:38）

复算da：全部21个超时终态的名义IK越过软限位.04561–.30802rad；env0在6秒后关节参考完全冻结。原全腿有效性判定让一个摆腿拒绝冻结其余支撑腿，直接IK接管又丢失受载PD偏差。新增选项均默认关闭：静稳四足支撑后捕获实际锚点与目标−实测角度偏差，只有摆腿渐退载荷偏差；逐腿判定，保留原IK残差/限位以及组合目标限位。新增前移抬高轨迹在越箱面前获得足够高度，及可配置机身净空。姿态库可显式保留受载位置目标，原实际关节软限位复位规则不放宽。6项引导检查及7项阶段检查通过。

dd目录`climb-loaded-guidance-20261002-dd`：关闭新增选项逐值复现dc引导版全部32终态、trace、步态和关节指标；开启受载捕获仍全部失败。ee目录`climb-loaded-edge-arc-20261002-ee`：取cu零actor env0的24秒实测稳定终态，平移使前脚均值x=.60m，保存实际姿态和加载目标，先独立检查24秒受载稳定性，再执行新轨迹引导。箱面x=.75m、20cm高度及原安全门禁保持。

| 诊断（各32完整回合） | 完整攀爬成功 | 超时/底座/姿态 | 三足支撑 | 最长腾空s | 竖直峰值m/s | 单足合力N | 含初始化累计饱和最大s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dd受载捕获 | 0/32 | 27/0/5 | 99.746% | 0 | .553268 | 143.394 | .200 |
| ee仅初始化站立 | 0/32（预期站立） | 32/0/0 | 100% | 0 | .102625 | 68.885 | 0 |
| ee引导，净空.28m | 0/32 | 19/8/5 | 88.915% | 0 | .591163 | 185.692 | 1.000 |

均无台面承重。dd支撑腿叠加载荷偏差后受限，身体过伸；ee初始化确实稳定，但运动时支撑和平衡仍失败，31/32终态摆腿参考无效，其他支撑腿仍可更新。不能把初始化低冲击当作攀爬改善。原始报告与`final-comparison.json`分别保存在上述目录，dd另有`prior-diagnosis.json`。

ef目录`climb-guided-residual-train-20261002-ef`于17:34:04启动：相同ee箱沿起点与冻结源码，从`stand_actor304.pt`零actor开始，512环境、seed634、300轮、std=.3、固定lr1e-4，每50轮保存；开启受载捕获与前移抬高，机身净空.28m、转移1.5秒、摆腿4秒、残差动作尺度.2、stage_pose/stage_reach权重各6。初始化checkpoint SHA256为`d9673b2b49f5dce08d844a1de81a3a37e7f90e85d20b86489a5751b8aa2b1dee`。训练/监控PID543078/543080，GPU0，限时3000/6000秒。17:38远端已正常PPO迭代，尚无独立评估结果。

监控等待训练退出后依次评估50/150/299轮箱沿，再单独评估299轮原起点，均24秒32回合；不能作为原12秒验收。该实验验证能否学会显式足端参考下的支撑/身体修正，零actor引导失败已如实保留，不预判训练成功。旧da残差脚本没有启动。最新视频仍dc/8789，不代表ef。

<a id="record-0192"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## ef最终诊断与eg载荷对照（2026-10-02 18:20）

ef训练和监控已退出，所有原始报告已下载并核对monitor记录SHA；四批各32个唯一env终态，无未完成。完整登台均失败。

| 模型/起点 | 成功 | 超时/底座/姿态 | 三足% | 腾空s | 竖直峰值m/s | 单足N | 含初始化累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 50/stage | 0/32 | 22/6/4 | 80.072 | 0.060 | 0.696 | 185.104 | 1.800 |
| 150/stage | 0/32 | 19/5/8 | 86.311 | 0.000 | 0.489 | 222.550 | 0.360 |
| 299/stage | 0/32 | 21/7/4 | 89.626 | 0.000 | 0.561 | 196.521 | 1.420 |
| 299/original | 0/32 | 18/2/12 | 97.914 | 0.060 | 0.951 | 569.397 | 2.100 |

本轮不足不是训练时间短的证据。最终箱沿31/32终态摆腿IK/组合目标拒绝，26/32相位停在.25；env0在3.5秒身体x由.351退至.210m，6秒退至−.047m，脚参考仍保持箱沿世界坐标，终末IK残差.187m。当前四脚静稳时捕获的载荷偏差固定不变，抬脚仅去掉摆腿偏差，没有把承重转给支撑腿。该缺口是待验证原因，不把相关性当作唯一根因。

默认关闭的`guidance_force_balance`加入准静态竖直力分配：根据实测全身COM、四足位置和重量求合力与水平力矩平衡，随相位向三脚分配平滑过渡，负力截断后保留并记录残差。利用PhysX重力补偿和实测Jacobian计算`G−JᵀF`，限额定力矩75%，除原30Nm/rad刚度转成位置偏差；原PD、延迟及所有q/v/a门禁保持。刚接管用1.5秒平滑混合旧偏差，卸载脚仍保留自身重力补偿。该方法不保证裁剪后全身力矩可行，也不能等同真实稳定攀爬。

eg使用同一ee起点、seed513、24秒、32环境，三组：关闭新项零actor回归、开启新项零actor、开启新项ef299。训练策略搭配新控制只能叫新诊断候选，不冒充ef原验收。源码、起点、脚本与SHA独立冻结在`climb-force-balance-20261002-eg`；18:20:05远端监控PID545670，GPU0回归和GPU1候选并行，GPU1两组顺序执行；每组限时700秒，总1700秒。8项数学检查通过，含各摆腿选择的卸载、可行时平衡、不可行残差、平移不变性与载荷连续性。尚无eg物理结果，未开始新PPO。


### 启动修正：eg未运行物理回合，eh接续

eg的两个零actor作业误用`--checkpoint`读取TorchScript，在actor载入阶段报NotImplementedError，未产生物理回合，不能计为策略失败或新评估。已终止这两个确认报错的自有进程并保留日志。训练模型使用checkpoint正确；零actor应使用`--actor-policy`。发现GPU1有另一任务作业，未干预，将后续三个诊断改为GPU0顺序执行。

eh目录`climb-force-balance-20261002-eh`保留完全相同控制源码及起点，只修正launcher；18:23:18启动监控PID546965，每组700秒，总2300秒。三个独立输出为baseline、balanced-zero、balanced-trained。没有新PPO；后续核对eh而非重启eg。关闭选项回归需先逐值匹配ee的终态、轨迹和质量；完整攀爬及安全指标照常汇总，不能以初始化或三足比例代替成功。


### eh物理结果：拒绝作为改善，转入ei水平力矩对照（18:30）

eh三批均完成，96个唯一终态，无缺失，无台面承重。baseline逐值等于ee的32终态、完整trace、步态和关节数据；代码默认关闭路径未改变。

| 对照 | 成功 | 超时/底座/姿态 | 三足% | 腾空s | 竖直峰值m/s | 单足N | 含初始化累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 0/32 | 19/8/5 | 88.915 | 0.000 | 0.591 | 185.692 | 1.000 |
| balanced-zero | 0/32 | 0/32/0 | 89.589 | 0.000 | 0.263 | 147.790 | 0.000 |
| balanced-trained | 0/32 | 0/26/6 | 89.268 | 0.080 | 0.542 | 184.132 | 0.280 |

零actor env0在4.88秒失败，身体x=.430、y=.124、z=.291m，相位.135、脚高.045m，目标.156m；载荷矩残差约−12.30/−11.15Nm，不能称重新分配后承重已可行。训练actor也不能补偿该控制问题。eh完整证据及SHA见`comparison.json`，本轮低冲击失败仍拒绝。

ei延续同一20cm箱沿起点，显式新增水平速度反馈：目标速度是1.5秒五次平滑转移曲线导数，反馈增益4/s，水平加速度模长限.4m/s²。各脚水平力与法向力成比例`Fxy=Fz*a/g`，按实际足高把水平力臂修正为`r_xy−r_z*a/g`再分配竖直承重，因此混合脚高时也记录合力及三轴力矩残差；非负力裁剪和关节前馈75%裁剪仍可能使请求不可行。名义力学测试不保证动态稳定，也不替代摩擦约束全身控制。

目录`climb-wrench-balance-20261002-ei`，18:30:40启动监控PID548312，GPU0依次运行旧竖直分配零actor回归、水平配合零actor、水平配合ef299，均seed513、32环境、24秒。源码/起点SHA冻结，9项数学检查通过，包括不同脚高下合力、力矩、无加速度退化及平移不变。启动时eh已全部完成，未重启训练，旧视频dc/8789继续保留且不标为新候选。

ei关闭水平项回归于18:31:34结束；32终态、trace、步态和关节指标逐值等于eh/balanced-zero，核验记录为`baseline-regression.json`。开启水平项候选已进入物理评估，仍不能称改善或验收通过。

<a id="record-0193"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## ei全部失败；ej分离卸载和抬脚（2026-10-02 18:47）

ei三批结束，96终态完整，无台面承重。报告已取回，关闭水平项回归与eh逐值一致。

| 对照 | 成功 | 超时/底座/姿态 | 三足% | 腾空s | 竖直峰值m/s | 单足N | 含初始化累计饱和s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 0/32 | 0/32/0 | 89.589 | 0.000 | 0.263 | 147.790 | 0.000 |
| balanced-zero | 0/32 | 0/32/0 | 87.737 | 0.000 | 0.202 | 143.496 | 0.000 |
| balanced-trained | 0/32 | 0/28/4 | 87.094 | 0.060 | 0.530 | 254.649 | 0.420 |

`airborne-load-diagnosis.json`保存ei零actor env0原始trace摘录：第175步四足承重、COM裕量.0362m；第200步仍4脚且正在抬升；第225步前脚高.11728m、实际法向力0N，目标载荷仍24.08446N，RR实际足力亦为0、分配17.165N，三足支撑已丢失，COM裕量−.01826m。原卸载与抬脚共用相位，即使脚已离地仍为它保留支撑份额。这是明确不一致，尚不是其他失稳原因已排除的证明。

新增默认关闭`guidance_preunload`，必须配套受载引导和力分配。时间分为先1.5秒身体转移、再1.5秒在原脚位将选中脚载荷降为零；在实际另三脚法向力>2N、选中脚≤5N、COM裕量≥.015m、线速度<.04m/s、角速度<.15rad/s连续.2秒后，才让摆腿时钟开始。仅在卸载已确认后跳过原时钟的四脚接触等待，避免选中脚已无接触时死锁；之后保留其余三脚接触、真实抬高/横移/落脚等待。全程保持原q/v/a、PD、延迟、20cm箱和安全终止，时间预算仍24秒，不以额外等待延长回合。

ej目录`climb-preunload-20261002-ej`，18:47:39启动监控PID549246，GPU0依次执行原ei零actor回归、零actor启用卸载门控、ef299启用门控，均seed513/32回合。新门控行为是诊断，原训练actor搭配新控制不冒充原策略验收。源文件、起点和启动脚本SHA冻结。10项数学检查通过，新增检查拒绝选中脚仍带24N、其他脚失去接触、COM越界或身体运动过快时开始抬升。没有新PPO，下一步取决于真实箱沿物理结果。

ej回归于18:48:35完成，全部32终态、trace、步态和关节数据逐值复现ei/balanced-zero，核验写入ej/comparison.json。开启新门控的候选已正常进入物理回合，尚未新增成功结论。

<a id="record-0194"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## ej结果：首脚到达台面附近，尚未接触承重；录制ek（2026-10-02）

ej三批全部完成，96终态无缺失，完整成功均0/32。原始数据与比较表已同步本地。

| 版本 | 超时/底座/姿态/臂接触 | 三足% | 腾空s | 竖直峰值m/s | 单足N | 含初始化累计饱和s |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 0/32/0/0 | 87.737 | 0.000 | 0.201869 | 143.496 | 0.000 |
| balanced-zero | 32/0/0/0 | 100.000 | 0.000 | 0.102625 | 118.916 | 0.000 |
| balanced-trained | 26/1/4/1 | 99.499 | 0.380 | 0.724949 | 200.044 | 1.060 |

无学习修正版本28/32首脚进入相位1并位于箱面上方，4/32仍等待卸载；训练策略26/32到相位1、6/32未开始抬脚。终态接触检查显示两版台面承重均0/32。训练版env0脚中心[.831777,.172482,.224818]，落点参考[.83,.172406,.2245]，三脚支撑且选中脚接触false、卸载份额1，故仍等待实际落脚、尚未换脚。该局部动作进展不是首步成功或完整登台通过；后续优先接触探测与受载恢复，不放宽20cm/碰撞/执行器/停稳门禁。

用户要求录像。ek冻结ej的同一源码、起点、参数，新增侧面相机(.35,1.7,.85)指向(.55,0,.25)，32环境seed513，真实24秒回合，视频25fps。18:58:03监控PID550484先录无学习修正env0与训练修正env0；发现无学习修正env0属于4个等待卸载回合，保留该录像，并选原评估按env_id排序首个完成前移的env3增加代表回合，18:59:01监控PID551081等待前两段结束后执行。所有选择均公开标注，不能以代表录像掩盖整批失败。目录`climb-preunload-review-20261002-ek`。待全部终态/质量及可比轨迹核对和解码后提供浏览入口，旧dc视频不替换成新结果。


### ek三段原速录像交付（19:08）

全部远端录像已完成、下载并核验，入口 `index.html` ，本地HTTP PID1995092。`guided-representative.mp4`展示无学习修正env3，`balanced-trained-env0.mp4`展示训练修正env0，`balanced-zero-env0.mp4`保留仍等待卸载的对照。页面明确说明环境3的选择依据与整批0/32，不把首脚悬在台面附近当作承重成功。

每段1280×720、25fps、600帧、完整24秒，无加速或剪辑。三个报告各32终态、步态和关节指标逐值等于ej对应评估，两个env0的完整trace也一致；env3原报告未记录trace，核验范围明确不含该项。checkpoint/actor、评估及控制源码哈希均与来源一致，`verification.json`记录报告和视频SHA及解码信息。抽帧检查显示脚部可见，前移后停在台面附近；仍未换脚。首帧为渲染初始化黑帧，保留原始录像不裁剪。

产物在本地仓库外和远端同名`climb-preunload-review-20261002-ek`，没有将视频或权重提交Git。录像已完成，不重启录制或旧训练。后续改进落脚接触探测与渐进恢复承重，仍需从原起点独立验收。

<a id="record-0195"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## el：接触探测与确认承重再换脚（2026-10-02 19:16）

针对ej的悬停落脚，新增默认关闭`guidance_landing_contact`，依赖原先卸载门控。到摆腿相位1后，在其余三脚接触、身体线速<.05m/s/角速<.2rad/s时，以4mm/s下探，深度上限15mm。选中脚在落点XY3cm、Z2cm以内且实际法向力>2N，连续接触100ms才逐渐恢复该脚载荷，分配由三脚在600ms内转到四脚；只要失去接触就撤销该脚载荷分配，不能让悬空脚承担预测支撑力。实际选中脚承重≥8N、四脚接触及低速持续200ms后，才满足额外换脚门控；保留CrawlClock原已抬脚、到末相位与四脚接触稳定条件。探测不改变箱体、地面或碰撞形状，也不放宽软限位及参考q/v/a。

初始过渡、足端参考及加载仍经过原PD30/.6、延迟与力矩前馈75%限制。默认关闭不影响旧任务。新增两项落脚状态测试以及一项时钟换脚检查，连同既有测试共12项引导+5项步态通过；测试覆盖无接触不分配载荷、探测深度上界、触地但未承重不换脚、失去接触撤销加载。物理有效性尚待验证。

隔离目录`climb-landing-contact-20261002-el`冻结11份控制/配置/评估源码（新增crawl_gait.py）和原ee受载起点，seed513、32环境、24秒；19:16:16监控PID552748，GPU0顺序执行原ej零actor回归、零actor新落脚、ef299新落脚。每组700秒、总2300秒。无新训练，未覆盖原报告或策略；原起点12秒验收及最终独立种子门禁仍未通过。


### el结束：首脚实际加载后进入FR准备，但第二步失稳（19:26）

三批各32完整终态，无缺失；baseline逐值匹配ej全部终态、trace、步态和关节质量。完整攀爬仍全部0/32。

| 版本 | 超时/底座/姿态/低姿态/臂接触 | 三足% | 腾空s | 竖直峰值m/s | 单足N | 累计饱和s | 已转FR准备 | 终态台面承重 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 32/0/0/0/0 | 100.000 | 0.000 | 0.102625 | 118.916 | 0.000 | 0/32 | 0/32 |
| balanced-zero | 25/0/6/1/0 | 99.376 | 0.040 | 0.650681 | 185.601 | 0.480 | 28/32 | 19/32 |
| balanced-trained | 20/1/10/0/1 | 99.035 | 0.380 | 0.724949 | 200.084 | 1.060 | 26/32 | 19/32 |

只有实际触地、渐进恢复支撑份额、选中脚≥8N及低速稳定200ms，并保留原CrawlClock真实抬脚/末相位/四脚接触门控，才能转FR。因此28/32与26/32是首脚接触承重门控通过的局部证据；之后的安全终止仍按失败记录，没有成熟策略交付。两个版本终态各19个环境仍有台面承重，不能把首步进展等同完整任务。

零actor全部28个FR准备终态均至少一条后腿参考被拒绝；名义FK误差最大6.83e-8m，部分名义关节越限，env3名义越限为0但RL/RR组合目标均拒绝，其加载前馈calf为26.606/18.023Nm。源代码按四脚平均高度+.28m计算下一机身目标，一个脚升高20cm使该目标约升5cm；在受载余量不足时继续抬高身体并不合理。诊断摘录保存在el/mixed-support-diagnosis.json，尚不能断言这是唯一失稳原因。

<a id="record-0196"></a>

来源：CLIMB_EDGE_TRAINING_20261002_CN.md。

## em：混合脚高时保持低处支撑净空（19:26）

新增默认关闭`guidance_mixed_height`，仅在捕获脚高差>10cm时使用最低脚高度+.28m作为机身目标；平地及四脚同一台面保持旧平均高度计算。脚位、落点、卸载/触地/承重门槛、PD、延迟和限位不变。候选额外记录机身目标、名义关节目标及组合加载后的逐腿限位超量，以区分几何和承重目标拒绝。该规则是局部待验证诊断，不是全身轨迹可行性保证。

隔离目录`climb-mixed-support-20261002-em`，19:25:58监控PID554334，GPU0顺序评估el落脚零actor回归、新高度零actor、新高度ef299，各32回合/24秒、seed513。三批记录env3（el中进入第二脚准备后支撑退化的回合），故回归比对全批终态/质量，不将env3轨迹与旧env0相等作要求。13项引导+5项步态检查通过，新增检查覆盖混合脚高、四脚同高退化与世界坐标平移。实际物理结果待出，无新PPO；8790视频仍ej。


### em结束：em两前脚进展仍伴随失稳，完整攀爬未通过（2026-10-02 19:33）

el/em均已结束，各96个终态无缺失，完整攀爬仍全部0/32。el零actor有28/32通过首脚实际接触、加载及停稳门控；em混合高度参考让零actor10/32、训练actor9/32进一步转入后脚RR准备，但尚未完成后脚跟进。em回归逐值复现el零actor全部终态、步态和关节指标；记录环境由0改为3，未声称轨迹相等。

em零actor：27超时/1底座/3姿态/1低姿态终止，三足99.478%、最长腾空.100s、竖直峰值.729m/s、单足合力588.144N、含初始化累计饱和.940s。训练actor：19超时/1底座/11姿态/1臂接触，三足98.836%、.380s、.914m/s、255.578N、1.060s。推进了脚序，但冲击与部分稳定性指标恶化，不能作为成熟策略或安全改善交付。

em零actor env3第700步在FR完全卸载后仍有36mm支撑裕量，但第725步RL失去接触、RR组合目标超限约.00869rad；随后持续卸载、目标拒绝和支撑退化同时出现。降低机身目标没有解决加载可行性。下一轮优先验证实际接触、组合关节/力矩余量约束下的渐进载荷转移，以及失去支撑时的卸载恢复；不能只继续降低高度或扩大同配置PPO。还需检查已进RR准备的回合为何无法后脚跟进。

远端`climb-mixed-support-20261002-em`三批已完成，不重启旧监控PID554334；无新PPO。本地/远端comparison.json保存完整指标和报告SHA。13项引导+5项步态检查通过。现有视频8790是ej版本，未包含el/em新落脚，不能拿旧视频展示本轮进展。保留20cm箱、碰撞、执行器和停稳门禁；本轮均为24秒箱沿课程，原起点12秒及最终两组独立种子验收未通过。PUSH、MuJoCo、实机暂停。

<a id="record-0197"></a>

来源：CLIMB_ISAAC_STATUS_20261001_CN.md。

# CLIMB Isaac 优先：2026-10-01

> 2026-10-07交接索引：当前CLIMB边界、结果及优先级见[CLIMB当前小组交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)。本页保留历史实验/计划，不作为当前进程或下一步指令；登台后到目标点由NAV负责。PUSH技能、MuJoCo、实机暂停。

> 后续用户否定本页旧候选的奔跳动作。当前慢爬改造与实验d见[慢爬记录](#source-climb-crawl-status-20261001-cn)；本页保留原12秒任务与旧视频的历史证据。

用户已暂停PUSH优化，当前只推进CLIMB在Isaac达标；远程训练、评估和录像，MuJoCo及实机暂停。自动推进任务已同步新范围。PUSH保留ac已验收候选，af后续交叉检查不启动。

<a id="record-0198"></a>

来源：CLIMB_ISAAC_STATUS_20261001_CN.md。

## 当前候选与新验证

选定既有Smooth model0，SHA `ef52829997ee25677f3b3e432bc5e8ce3294d337fcb6f390d5b60d861bf29aa7`。当前源码副本在`/path/to/artifacts/go2-piper/climb-isaac-20261001-a/train`。使用选择性自碰撞USD（SHA `d8421ef50d69b7d43dd7a7d07675fa3b4c651ffcaf9d3d00d74c85544bbdf21f`），20cm固定箱、1.2×1.2m顶面、原12秒任务、四足安全顶面支撑与原姿态速度条件连续1秒。地面静/动摩擦.8/.6，初始净高.33m；不是PUSH的自由箱体。

选择元数据先于评估保存，SHA `f4cb359abfb65a9e1bd96591170a3e2d06b218e5bcabebbff3ef7000779a500e`。首批新种子1511/2511在选择时未使用，后续归因已使用1511，今后不可再视为新验收样本。

| 权重 | 种子/用途 | 成功 | 底座接触 | 超时 | 未完成 |
| --- | --- | --- | --- | --- | --- |
| Smooth model0 | 512 复现 | 30/32 | 1 | 1 | 0 |
| Smooth model0 | 1511 新验收 | 29/32 | 3 | 0 | 0 |
| Smooth model0 | 2511 新验收 | 31/32 | 1 | 0 | 0 |
| 原冻结model200 | 1511 后续诊断 | 29/32 | 2 | 1 | 0 |

**当前model0未通过本轮两组门槛。** 512的32个完整终态与旧报告逐值一致，说明当前源码保持旧行为。1511失败env22/8/30分别在.80/1.38/1.76秒触发底座接触；2511的env3在1.00秒底座接触。所有批次无臂接触终止。源匹配的冻结model200（SHA `5cbdb0d8523a10b7f6a4870a3385afdd8289d5d87bc93408ac5c7b404ac7b548`）同样29/32，不能只靠回退一次Smooth更新解决。

本地verify_reports.py核对32回合完整性、控制与物理哈希、逐环境成功记账；成功终态复核四足位置/受力、目标误差、线/角速度、姿态及原停稳标志。max_standing_seconds在终态前一步采样，约.9999996s；真正成功仍由原BoxSettled的一秒计时器判定，没有放宽门槛。

<a id="record-0199"></a>

来源：CLIMB_ISAAC_STATUS_20261001_CN.md。

## 视频

按用户要求录制同一model0。首轮32环境共享地形导致录像可见多台机器人和调试标记，已增加默认关闭的`--video-isolate-environment`，仅隐藏其他环境渲染、关闭命令标记；32环境继续完整仿真。相机改为使用inspect_env_index对应的原点，修复此前非零环境仍指向env0的问题。录像已完成并核验：成功512/env0在3.42秒停稳成功，失败1511/env22在.80秒底座接触。两批录像的全部64终态与原报告逐值一致，控制和物理不变；只改变显示。提供首回合片段climb-model0-success.mp4（3.44秒）与climb-model0-failure.mp4（.80秒），避免把自动重置后的动作算入原回合；完整录像分别12秒和4.12秒，均1280×720/25fps。已核对画面单机可见和远程视频SHA，入口为仓库外climb-isaac-20261001-a/index.html。

这也意味着此前PUSH ae等非零inspect环境视频不能单凭标签当作该环境的视觉证据；原遥测和批量验收报告不受影响，PUSH暂停状态不变。历史视频保留，不覆盖。

本轮暂无新增PPO训练；先明确早期底座接触的时序和支撑缺口，再作受控优化。不要用旧32/32、30/32或单条成功视频宣称当前候选达标。原始报告、录像、脚本和哈希清单位于仓库外`../artifacts/go2-piper/climb-isaac-20261001-a/`。


本地7项评估记账检查通过，修改后的评估器编译通过；远程两批录像逐终态一致验证覆盖了渲染隔离与非零环境相机修复。新候选仍未通过两组门槛，下一步聚焦早期底座接触，不继续盲目提高平滑惩罚或学习率。

<a id="record-0200"></a>

来源：CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN.md。

# CLIMB 整段参考与时间预算修正

> 2026-10-07交接索引：当前CLIMB边界、结果及优先级见[CLIMB当前小组交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)。本页保留历史实验/计划，不作为当前进程或下一步指令；登台后到目标点由NAV负责。PUSH技能、MuJoCo、实机暂停。

当前固定步长/固定慢摆腿方案不能满足24秒完整任务。下一步首先设计从原始起点到台顶的整段参考，再检查实际接触和运动质量；不继续把完成四次平地摆腿当作接近完整交付。

<a id="record-0201"></a>

来源：CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN.md。

## 可复现的时间下界

原20cm任务要求四足x均严格大于`.75+.04=.79m`，还要求机身到位及连续1秒停稳。cj两条原始Isaac轨迹在首脚释放前，前足约`.11–.18m`、后足约`−.36至−.31m`。按固定支撑足参考、每步24cm且不利用足底滑移推进，前足各至少3步、后足各至少5步，合计至少16次摆腿。每次2.8秒，则**仅摆腿至少44.8秒**；准备、支撑转移、卸载、恢复承重、20cm越沿和最终停稳尚未计入。

进一步用cm/search28保存的全部32个首轮准备前足位复算，每回合至少15–19次摆腿，仅摆腿下界为42.0–53.2秒。这是这32个初态在当前名义参考安排下的下界，不是“机器人不能平缓攀爬”的物理结论。原始足位、报告SHA和可复算脚本见cm的`schedule-lower-bound-all32.json`（全部32个）与`schedule-lower-bound.json`（早期两条），以及仓库`scripts/audit_crawl_schedule_budget.py`。不能靠增加PPO轮数解决不可达的固定节奏，也不应延长回合或挪动起点掩盖问题。

<a id="record-0202"></a>

来源：CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN.md。

## 下一步实施顺序

1. 在生成完整足序前计算四足到合法台面的必要落点、机身路径和全段时间预算。地面接近与上台使用不同的足端曲线；上台必须在水平越沿前满足真实高度净空，不能把5cm平地弧线直接拉长到箱体上。
2. 联合规划支撑位置、机身前移/抬升和足端路径，逐段检查关节软限位、局部姿态包络、原关节参考速度/加速度，以及支撑约束。cl/cm的采样预检可复用，但其固定慢速节奏不是交付候选。
3. 原执行链腿部参考硬限速为2.5rad/s、加速度15rad/s²，机械臂为.5rad/s、3rad/s²；PD30/.6和0–4物理步延迟保持不变。内部`.12/.18m/s`足速、`.075m/s`机身速度、1秒卸载/固定恢复承重时长是已有诊断设计，不能误当实测电机参数或用户规定的最终步态。应按完整路径和实测载荷重新分配内部时程，并验证真实卸载、稳定承重与关节跟踪，不能只统一提速或删去接触检查。
4. 落脚、支撑转移和下一个摆腿的时序依据实际力和状态衔接，避免机械地反复等待同一稳定事件。任何时间复用都要独立重建接触/稳定区间，不能把悬空时间、未承重时间计为停稳。
5. 先在既有远端做原起点/原20cm/24秒的完整回合，报告成功、三足支撑、腾空、竖直速度、法向足力和累计饱和。关节参考满足限速不等于机器人稳定；低冲击失败不算任务通过。出现明确可执行轨迹后，才决定是否用其指导残差策略训练。

原12秒任务与新增24秒慢爬分别记录；最终候选固定后，仍须两组未用种子各32回合、每组至少30成功且没有无终态回合，并检查原速视频。PUSH、MuJoCo和实机暂停。这次是控制参考设计修正，无需更改验收条件。

<a id="record-0203"></a>

来源：CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN.md。

## cn离线预检后的具体收敛方向

新增`plan_crawl_route.py`把机身抬升/俯仰、20cm越沿和整体参考时间纳入同一报告。三个保存状态分别仅得到25/19/14步可行前缀，带10%时程余量的参考运动已35.55/26.21/19.22秒，完整路线均未完成。它是拒绝草案的离线工具，没有实测支撑/冲击证明，也没有接入运行控制器。详见慢爬状态cn节。

下一步不能再沿逐步停车的几何参考扫描固定等待。应在完整路线中联合优化连续机身轨迹、落点和接触时序，并补充随关节变化的全身COM与支撑力可行性。载荷转移可与前脚落地后的实际承重衔接，但不得在空中计承重或删除实测门禁。新的完整路径必须先有可信24秒预算，再进入既有远端Isaac；当前GPU空闲，未挂训练。

<a id="record-0204"></a>

来源：NEXT_STEPS_CN.md。

# GO2-PIPER 下一步计划

<a id="record-0205"></a>

来源：NEXT_STEPS_CN.md。

## 当前方向：按用户要求直接训练攀爬（2026-10-02）

用户明确“训练攀爬而不是行走，NAV已经可以稳定行走”。停止把平地逐脚行走和整段离线路径搜索作为主要推进方向。新增隔离任务 `GO2-PIPER-Box-Climb-Stages`：在20cm箱沿开始学习前脚上台、混合高度支撑、身体抬升、后脚跟进。训练用近箱/分阶段起点必须单独标注；`Stages-Play`默认仍用原起点，仅显式传入 `--climb-stage-bank` 才启用训练起点诊断。24秒实验与原12秒验收分开；保留原碰撞、执行器限制和连续停稳1秒条件。

当前尚无达标慢爬策略。cp/cq/cr四阶段起点检查均0/32，全部终态完整；cr修正初始化目标与显式PD增益后没有腾空，但仍27次姿态终止，拒绝直接拿这组名义姿态训练。cs实测过渡姿态平移到箱沿也32次姿态终止，不能当作稳定站姿。ct默认站姿贴箱过近导致32次底座接触。cu将前脚放在x=.60（箱面x=.75），32回合均站满24秒、零安全终止，三足100%、无腾空、竖直峰值.553m/s、足力111.338N。cu箱沿PPO已于北京时间14:01:53启动，512环境/300轮，训练PID526883、监控PID526884；还没有新训练策略的攀爬成功结果。详细结果及后续启动记录见[箱沿训练记录](#source-climb-edge-training-20261002-cn)。视频8788仍为旧平地诊断，不是新攀爬成果。

后续优先事项：核对cu训练及监控进程，不要重复启动；第50/150/299轮分别做训练起点及原起点的32回合诊断，报告成功、完整性、三足支撑、腾空、竖直速度、足力和饱和时长，不能以奖励代替成功。候选固定后才做两组未用种子各32回合（每组至少30成功、无未完成）与真实速度录像。PUSH/MuJoCo/实机暂停。

以下内容按历史阶段保留，旧“下一步”不覆盖本节。

最新cn为离线整段参考预检，不是新的Isaac回合。新增plan_crawl_route.py，将原起点的支撑转移、机身前移/抬升/俯仰和20cm足端越沿统一求解，并由原2.5rad/s、15rad/s²参考限制估算时间。513的env0/7/14分别只找到25/19/14个连续名义可行步，完整路线均未完成；前三个名义落点上台也不能算成功。仅这些前缀的参考运动时间含10%余量已35.55/26.21/19.22秒，还不含初始化和实际卸载/承重等待，方案拒绝接入物理执行或训练。四足转移与摆腿分段停顿仍是瓶颈，不继续给该方案调短固定等待。下一步必须联合优化整个身体连续轨迹、步点与接触时序，并用随关节变化的全身COM/载荷检查替代冻结COM近似；先获得有可信24秒预算的完整路径，再远端Isaac验证。新增4项数学检查与原28项通过，58步用1537点复查关节/支撑近似/参考速率通过。远端无运行作业；最新物理数据仍cm的0/32，视频仍cj/8788。本地和远端cn保存报告、源码和SHA；未更改运行控制器或任务门禁。

最新cl–cm：发现固定慢摆腿方案的整段时间预算不成立。用cm全部32个准备前实测足位复算，在24cm固定步长/2.8秒逐脚摆动、支撑足不滑移的名义安排下，至少需要15–19次摆腿，仅摆腿即42.0–53.2秒，超过24秒；这不是机器人不能平缓爬箱的物理结论。停止继续微调这一固定节奏，下一步按CLIMB_TERRAIN_REFERENCE_PLAN_20261002_CN设计原起点→接近→20cm越沿→台顶停稳的整段协调轨迹，保持原任务/执行器门禁。已新增默认关闭的关节/机身/支撑位置联合采样预检：不可行时四足保持，不继续把脚送到被限位截断的落点；实际执行路径名义残差≤.106mm，但不是所有原失败已解决。cm的4.1/2.8秒首脚完成23/32、20/32，完整四步及20cm成功仍均0/32；四组候选均32个完整终态、零安全终止。全回合三足99.827%、腾空.06秒、竖直峰值.951m/s、法向足力203.635N、累计饱和最大.28秒；接管后三足100%、无腾空，cm法向峰值149.126/150.255N，不能称动力学全面改善。28项检查通过，cm关闭选项逐值复现cj/513原32终态与质量，规划决策/位移由保存输入重算一致。所有本轮远端评估及回归已结束，无新PPO；源码/原始结果/审计已归档，视频仍8788旧平地版。PUSH/MuJoCo/实机暂停。

用户已进一步明确：CLIMB必须通过平缓步态逐脚攀爬，旧model0奔跳动作不合格。新增24秒慢爬实验，单独于原12秒任务报告。b已完成：直接限速与300轮跳跃权重微调均0/32；默认站姿32回合均站满24秒但没有攀爬。c第100轮仍0/32（29超时、3底座接触），已停止。d的600轮已完成，100/300/599均0/32；最后32回合都站满24秒但不攀爬。e已复现全部32终态，确认均卡在第一只左前脚抬升阶段、未实际抬脚。下一步补充支撑转移与可执行单步控制，不延长同一无效训练。尚无达标慢爬策略。最新契约、证据与运行路径见[慢爬记录](#source-climb-crawl-status-20261001-cn)。

用户已切换优先级：**PUSH优化暂停，当前只推进CLIMB在Isaac达标**；训练、评估和录像均在远程服务器。MuJoCo及实机暂停。自动推进任务已同步此范围。PUSH保留ac已验收候选（30/32、32/32），af接管交叉检查不再启动。

1. 本轮model0新验收1511/2511为29/32、31/32，均完整；4次失败均早期底座接触。512复现全部终态与旧报告相同。原冻结model200在1511同为29/32，回退无成功率改善。
2. 用户要求的同版本CLIMB录像已完成，成功/失败首回合片段及完整视频保存在climb-isaac-20261001-a；两批64终态与原报告完全一致。后续新候选应使用--video-isolate-environment，正确显示被检查的机器人。
3. 当前以慢爬记录中的d结果及e诊断为准：20cm/24秒/连续停稳1秒，新增真实步态质量要求；原12秒结果仅作历史对照。保持安全接触及执行器限制，训练在远程执行。
4. 1511/2511现已使用，任何新候选验收需先固定配置，再选择未用种子。更新本地产物与GitHub分支；PUSH优化、MuJoCo与实机保持暂停。

详细状态见[CLIMB本轮记录](#source-climb-isaac-status-20261001-cn)。

以下为历史记录，其中进行中/授权阻塞等描述仅表示当时状态。

<a id="record-0206"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-30 当前工作

用户最新指示：先集中推进普通 PUSH，先在 Isaac 达标，MuJoCo 暂不推进；
CLIMB 暂不追加实验。用户已明确允许同步修改后的 PUSH 控制与训练代码到既有
服务器 `SIM_HOST` 的隔离实验目录，继续远程优化训练。此前源码同步的
授权阻塞已解除。当前阻塞为自动审批服务连续两次返回 HTTP 503，提示
`gpt-5.6-luna` 在当前分组无可用通道；远程只读检查亦未执行，不能标记训练已启动。

本地已准备 `../artifacts/go2-piper/push-isaac-priority-20260930-a/`：包含六个
待同步源码文件、哈希清单及受控对照脚本。恢复远程执行后，先对同一 Tracking
checkpoint、seed 517、32 环境比较关闭约束与 0.10 m 净空修正；据实际残差、
有效接触和箱体推进决定控制修正与训练。最终独立验收预留 seed 701、1701，
各 32 回合、每组至少 30 成功且无未完成回合。MuJoCo 暂停不等于实机放行。

以下为本日此前状态：

PUSH 已实现默认关闭的 IK 线性净空约束候选，本地控制测试通过；远端控制源码同步
被自动审批阻止，等待用户对具体同步动作的授权，尚未评估候选。CLIMB 已定位
MuJoCo 自碰均为 `link2/link5`；远端启用选择性自碰撞的 Isaac 独立两组仍为
`32/32`、`30/32`，均无臂接触终止。下一步核对失败姿态下该碰撞对的几何与过滤，
不能仅归因于自碰撞开关。详见[本日控制诊断记录](#source-training-status-20260930-cn)。

<a id="record-0207"></a>

来源：NEXT_STEPS_CN.md。

## 最新状态：候选未达标

同日 PUSH 复核：冻结 PUSH 在 Tracking-Play、seed 517 为 `0/32`，32 回合均因
臂身净空停止；Tracking 候选仍为 `0/32`，但箱体最大终态 x 位移从约
`0.107 m` 增至 `0.400 m`。全部候选回合终止时已完成安全接近，失败主要在
接触前后 `link4/link5` 与右前腿的净空及足部支撑。只将目标俯仰角改为
`1.0 rad` 仍为 `0/32`，无效手接触升至 14 回合。先验证满足关节限位、
PD 跟踪、净空和接触约束的在线手端路径，再处理接触期全身支撑；
不要把机器人前移量当作箱体推进量。报告见
[训练与评估记录](#source-training-status-20260929-cn)。

同日追加的 CLIMB std 0.05、lr 1e-5 `model_0` 在 Isaac seed 511/512 为
`32/32`、`30/32`，但 MuJoCo 独立 seed 500/600 仅 `14/32`、`14/32`；
同配置冻结 actor 的 MuJoCo seed 500 为 `16/32`。候选仅为隔离诊断导出，
没有跨仿真放行，也没有稳定的关节运动风险改善。下一轮先比较两端启动阶段的
重置状态、观测/动作顺序、首命令、PD/延迟与碰撞事件，并针对姿态异常、底座接触、
臂自碰做来源匹配的失败归因；在可复现的控制问题明确前，不扩大 CLIMB 训练。
完整结果和 SHA-256 见 [训练与评估记录](#source-training-status-20260929-cn)。
以下首轮结果仍保留为当时的独立探针记录。

用户已授权继续优化、训练普通 PUSH 与 CLIMB。首轮隔离候选在 Isaac 各完成一组
32 回合评估，均为 `0/32`，不能替换原技能，也不能进入实机接触：

- `GO2-PIPER-Box-Push-Tracking-Play`，seed `517`：`arm_body_clearance=29`、
	`base_contact=3`、`box_contact=3`。终止标志可同时出现，不能把三项相加作为
	回合数。`0.597655 m` 是机器人底座最大前移，箱体最大终态前移约
	`0.400 m`，没有安全完成并停稳。
- `GO2-PIPER-Box-Climb-Smooth-Play`，seed `511`：`base_contact=31`、
	`bad_orientation=1`；关节速度峰值约 `30.10 rad/s`，最大倾角约 `0.862 rad`，
	最大力矩/限幅比例仍为 `1.0`。平滑奖励尚未解决起步失稳或电机风险。

报告位于服务器 `/path/to/artifacts/go2-piper/smooth-tracking-20260929-a/outputs/`，
分别为 `push-tracking-seed517.json` 与 `climb-smooth-seed511.json`。原 PUSH、CLIMB
checkpoint 备份保留在 `/path/to/artifacts/go2-piper/generalize-20260929-a/original/`；
本次只读核查未发现训练或评估进程。9 月 26 日诊断录像不属于这批候选，不能用作其
运行效果证据。训练完成日志、checkpoint/报告/源码哈希及检查入口见
[训练与评估记录](#source-training-status-20260929-cn)。以下 9 月 28 日及更早条目保留为
历史诊断，下一轮以本节和当前优先级为准。

<a id="record-0208"></a>

来源：NEXT_STEPS_CN.md。

## 当前优先级

1. PUSH 先分解安全接近、就位、首次合法接触、持续推进与停止的耗时，定位
	Tracking 候选臂身净空停止前的目标/实测关节、接触点、底盘姿态和四足支撑。
	在真实 PD、限速和碰撞约束下验证在线手端跟踪与全身支撑，再扩大训练；保持
	箱体参数、目标、成功判据和全部安全停止不变，不能以最大位移替代安全完成。
2. CLIMB 已补齐目标变化、速度、加速度、力矩饱和时长、功率和底盘角速度遥测。
	下一步用同一初态的两端启动轨迹核对动作接管、PD/延迟和碰撞事件，并归因
	MuJoCo 的底座接触、臂自碰及姿态异常；之后再验证受限动作与训练配置。
	缺少实测电机额定参数、电流
	和温升时，不得宣称电机安全；仅提高奖励惩罚不构成硬约束或放行依据。
3. 用来源匹配的 MuJoCo 回放检查同一观测/动作接口和失败时序。仅当差异
	可能改变任务结果或揭示可信实机风险时，做有明确可证伪假设的局部
	Sim2Sim 探针；若只是无任务影响的逐步接触力差异，记录边界并停止深挖。
	不得用调材料或放松安全阈值来追求两个引擎逐帧一致。
4. 原生 Isaac 的 PUSH、CLIMB 各自两组独立 32 回合、每组至少 30 成功且
	无未完成回合；MuJoCo 沿用同样口径作为独立风险报告，而非自动实机许可。
	MuJoCo 的未解释任务失败或安全风险必须先归因，可信或未排除的风险阻止
	对应实机阶段。两端证据均不替代硬件标定、观测/动作/时延核对、独立
	急停和从无接触到接触的分级实机验证。PUSH-LOW 训练和实机接触继续暂停。

以下为可追溯的接触诊断记录，不是当前任务级验收结果；只有上述任务时序
显示相关性时才继续查 PhysX 子步冲量聚合窗口。

<a id="record-0209"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 普通 PUSH 完整回合接触时序

- 用冻结 `model_599.pt` 和原选择性碰撞、安全终止、箱体参数重跑 seed 210
	的锁臂动态回合；仅将评估 trace 从每 25 控制步改为所有有力手接触步采样。
	报告完成 1/1 回合、成功 0/1，29.0 s 因 `invalid_hand_contact` 终止，
	箱体 x 位移 `0.000437 m`；与原回合的终止和位移一致。
- 384 个有力接触采样中，最大合法前向推力约 `16.956 N`（手所受力沿
	箱体推进轴的反向分量）；低于 `5 x 9.81 x 0.4 = 19.62 N` 的静摩擦
	估算门槛。末步仍有约 `16.74 N` 手部接触力，终态接触点 z 为
	`0.1902498 m`，箱体中心 z 为 `0.0999998 m`，相对高度约 `0.090250 m`；
	现有合法前面接触的高度上限为 `0.20/2 - 0.01 + 0.0001 = 0.0901 m`。
	越界约 `0.15 mm`，安全停止正确触发，不应放宽此边界。
- 峰值合法力附近 joint2 与 joint5 已达到力矩比例 `1.0`；终态底盘有
	明显倾斜，手端相对箱体上沿上移。现有数据能确定本回合在达到估算
	推箱门槛前先失去合法接触，不能单凭一次回放证明力矩饱和或足地
	支撑是唯一原因。下一步在不改安全/箱体的前提下，核查接触点上移
	与臂关节跟踪、底盘姿态和足地支撑的逐控制步关联，再验证可动态
	保持的在线手臂路径；仍不得恢复 PUSH-LOW 训练或实机接触。
- 本地报告 `../artifacts/go2-piper/contact-repair-20260925/native-safety/push-dynamic-upperface-ramp2-locked-contact-trace-seed210-20260928.json`
	SHA-256 `11977d0c0d55e02f4b00ceb2939cdfefc5de0564c2744aa907b7c1dadf4bdf9e`；
	诊断评估脚本 SHA-256 `c4f9977173288fdc992116c4f14c301dfb78895c9a821b23ce1a6eb122bdbe8e`。

<a id="record-0210"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 普通 PUSH 锁臂与支撑补采

- 同一冻结模型、seed 210、箱体和安全配置复跑，额外记录接触点、箱体姿态、
	臂关节参考/实测值与四足法向力。新旧报告的模型哈希、控制哈希、物理参数、
	终态和去除新增遥测后的全部 426 个 trace 样本一致；仍于 29.0 s 因
	`invalid_hand_contact` 停止，不能视为任务验收。此次诊断脚本 SHA-256
	`d92b590d37d0022db97ec4c573dbcfa293be5f33fb9d8c87caf538349aeedfd2`。
- 初次接触后的锁臂会短暂释放并重锁；从 step 1359 到最后采样 step 1449
	连续锁定 91 个控制步。在这一段中，接触点相对箱体中心高度从约 29 mm
	升至 86 mm，step 1399 已达 50 mm，手端比世界系目标高约 20 mm。
	step 1443 底盘俯仰分量达到约 0.179（投影重力 x 为 -0.179），此时
	一只脚的法向力只有 4.68 N；到 step 1446 两只脚法向力为零。因而
	足部减载发生在可观测的接触点上移之后，不能单独解释上移的起点。
- step 1449 时仍是合法接触，接触点相对高度 86.21 mm；joint2 实测值比
	锁定参考高约 0.157 rad，joint5 高约 0.138 rad，二者力矩比例均为 1.0，
	手端实际高度比目标高约 54.6 mm，前向力约 15.88 N。下一物理步接触点
	相对高度越过 90.1 mm 上限约 0.15 mm，安全停止。该同回合关联支持
	“底盘姿态/臂跟踪漂移使固定关节参考不能保持合法接触”的控制假设，
	但不证明哪一项是唯一原因，也不证明目标力超过静摩擦估算即可推动箱体。
- 下一次隔离实验只比较锁定关节参考与受限速率的在线手端高度保持，沿用
	原模型、腿策略、箱体和全部安全终止；先要求接触点保持在原合法区域、
	四足不丢支撑且无新的碰撞，再检查是否产生足够持续的箱体位移。
	若接触点仍上移或关节/足部先饱和，应停止该方案并转向全身支撑控制，
	不提高推力目标或放宽安全阈值。
- 补采报告 `../artifacts/go2-piper/contact-repair-20260925/native-safety/push-locked-contact-posture-seed210-20260928.json`
	SHA-256 `ed9365479de751d66a9ce9bad644b00c87072d481c182a46aa6966a508523416`。

<a id="record-0211"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 同帧接触力 dt 查询探针

- 对同源 node2 轨迹，在 Isaac `sim.step`、`scene.update(0.005)` 后对四脚
	精确地面过滤视图再以 `dt=0.0025 s` 查询一次，未增加物理步或改变控制。
	40 步回放与此前足球几何报告逐步关节位置、标准 `dt` 过滤法向及摩擦力一致。
	首步四脚法向 Z 与摩擦 X 的半 `dt` / 标准 `dt` 比值均精确为 `2`。
	这证实传入的 `dt` 参与冲量到力的换算，但**不能**从同帧两次查询
	推断 PhysX 累计冲量的内部子步窗口或与 MuJoCo 静态 `mj_forward` 的同口径性。
	本次仅为隔离诊断，未改变 PUSH 安全停止或技能验收状态。
- 新报告为 `../artifacts/go2-piper/contact-repair-20260925/native-safety/push-contact-dt-probe-node2-gpu1-isaac-20260928.json`，
	SHA-256 `9b505c6f2cc2a271521d44defaae71dfc87934bd82e3412b6577bcd63ea65760`；
	输入轨迹 SHA-256 `2da8a4395a8770e721530c723b88450d6f3cc0daf92d83511a0e0ee0778db00a`。
	远端运行的隔离脚本 SHA-256 `0eae71315861e222dc135a5a4f03b2f67fc32e6fb801be813dfeb36d5aaa428e`。
	后续需借助明确的子步/接触点冲量记录验证聚合窗口，不能据此改材料。

<a id="record-0212"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH node2 首步足端运动学分解

- 在上述同源报告中，Isaac 实测初态与 MuJoCo 初态的最大关节位置差为
	`5.75e-8 rad`，根位置差为 `1.40e-5 mm`，关节初速度均为零；Isaac
	步前 `applied_torque` 与 MuJoCo 首步 `data.ctrl` 的最大差为
	`6.71e-6 Nm`。首步积分后的 FL 小腿速度差为 `1.859 rad/s`，四条腿
	小腿差依次为 `1.859/1.516/1.190/1.205 rad/s`。这将明显状态分叉
	定位在积分后，但未隔离接触约束、执行器内部或求解器的单独贡献；两端
	根速度字段也不应用于直接动力学归因（Isaac 回放规定根状态）。
- 由匹配哈希的 node2 路径、Isaac 足球几何回放与 MuJoCo 步末探针，在独立
	MuJoCo 正向运动学中分别代入首步两端求解根姿态和关节位置。最大关节位置差
	为 RR 小腿 `0.018355 rad`（Isaac 减 MuJoCo），最大速度差为 FL 小腿
	`1.858961 rad/s`；四条腿大腿/小腿均有位置差，机械臂关节差较小。
- 固定 MuJoCo 根姿态，仅替换为 Isaac 关节位置后，FL/FR/RL/RR 足球心 Z
	分别增加 `2.38/2.70/2.83/2.88 mm`；随后替换根姿态另贡献
	`0.39/0.61/-0.01/0.20 mm`。两端状态代入同一模型所预测的总差为
	`2.77/3.30/2.82/3.08 mm`；实际步末球底差为
	`2.53/2.84/3.41/3.49 mm`。预测与实测逐足残差来自将 Isaac 状态代入
	MuJoCo 几何时足球心 Z 的 `0.25/0.46/-0.59/-0.41 mm` 模型差；
	MuJoCo 自身重算状态的距离/球心 Z 残差为零（浮点精度）。
- 不能把 MuJoCo `foot_centers_world_before_projection` 直接当作独立
	`mj_forward` 步末球心：两者相差约 `1.5–2.3 mm`，属于不同几何采样阶段。
	复现命令：`PYTHONPATH=mujoco OPENBLAS_NUM_THREADS=1 ../.envs/go2-arx5-nav/bin/python
	mujoco/compare_piper_foot_kinematics.py --path-json
	../artifacts/go2-piper/contact-repair-20260925/native-safety/push-reachability-observed-continuous-seed210-20260926.json
	--isaac-json ../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-geometry-node2-gpu1-isaac-20260928.json
	--mujoco-json ../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-post-step-probe-node2-mujoco-20260928.json`。
	以上仅说明首步间隙差的主要运动学来源；PhysX 力查询的内部时间窗口
	和动力学分叉成因仍未核实，不能据此修改材料或宣称技能验收。

<a id="record-0213"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH node2 首步足球步末几何对照

- 对远端 IsaacLab `contact_sensor.py` 核查：`_update_buffers_impl` 分别调用
	`get_net_contact_forces`、`get_contact_force_matrix` 和 `get_friction_data`，三者
	均传 `dt=self._sim_physics_dt`；前两者是法向力，摩擦力另行按接触点求和。
	回放在 `sim.step` 后 `scene.update(dt)` 读取这些值；这不是对步末状态重新
	求解的 MuJoCo `mj_forward` 力。源码尚不足以证明 PhysX 内部的子步冲量窗口。
- 在独立远端副本上对同一 node2 轨迹（SHA-256
	`2da8a4395a8770e721530c723b88450d6f3cc0daf92d83511a0e0ee0778db00a`）
	重跑 40 步，启用足球球心及逐足精确地面过滤；相对原精确过滤报告，逐步
	过滤法向/摩擦力、关节位置和求解根姿态完全相同。新脚本 SHA-256
	`a6ba63be0bd465b10309b2ab4518d5c2330fd47208bedde707605c402f8adf6c`，
	新报告 SHA-256 `703a48f99556d17a90c2ad65956d9ea946bdd0c6fe73246332e9453c1e30cfbd`，
	路径为 `../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-geometry-node2-gpu1-isaac-20260928.json`。
- 两端球半径均为 `22 mm`，初始足球球心逐项接近；首步 Isaac 求解后、根部恢复前
	FL/FR/RL/RR 球底 Z 为 `-35.58/-30.39/-21.20/-20.45 mm`。同源 MuJoCo 独立
	`mj_forward` 步末接触距离为 `-38.10/-33.23/-24.61/-23.93 mm`，其步末球心
	减半径与距离一致；两组步末几何差为 `2.53/2.84/3.41/3.49 mm`。
	首步根姿态和关节位置也已分叉，因此力差不能归因于相同状态下的接触求解器。
	下一步需对齐步末速度及求解前状态，并确认 PhysX 查询的冲量聚合窗口；
	在此之前不改材料/箱体参数、控制与安全停止，也不将此诊断视为技能验收。

<a id="record-0214"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 足地力查询窗口核查

- 远端 IsaacLab `contact_sensor.py` 的 `_update_buffers_impl` 将过滤法向力交给
	`get_contact_force_matrix(dt=self._sim_physics_dt)`，摩擦力交给
	`get_friction_data(dt=self._sim_physics_dt)`；本次回放 `physics_dt=0.005 s`。
	它们在 `scene.update(dt)` 后读取，不是对积分后构型执行一次新的静态接触求解。
	现有 MuJoCo 副本 `mj_forward` 步末法向力不能与 Isaac 查询结果直接当作同一测量量。
	这仅核实了 API 参数和调用时刻，未验证 PhysX 内部子步冲量聚合方式。
- 原 Isaac 精确过滤报告的 `collider_offsets=[]`；上文独立重跑已补充足球球心
	步末观测和 MuJoCo `foot_contacts_post_step` 对照，原报告保持不变。

<a id="record-0215"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 首步积分后采样探针

- node2 路径 SHA-256 `48dadb2084ee8c354d06dd5767c1d2dda6d5d587678ab3650fe0f329278a2ee9`、
	箱体 `x=3 m`、正常摩擦、`0.005 s` 步长的 MuJoCo 四步 trace，在独立 `MjData`
	中以每步积分后、关节限速和根部恢复前的状态执行 `mj_forward`。首步四足法向力
	为 `42.50/38.37/25.72/27.09 N`，逐足与原投影后重算力相等（浮点精度）；
	原 `mj_step` 约束力则为 `80.92/71.17/49.90/51.25 N`。与同源正常摩擦旧报告
	相比，原记录的首步扭矩、关节位置、两阶段法向力均完全相同，探针未改变轨迹。
- Isaac 精确地面过滤报告首步法向为 `43.00/39.62/19.53/16.73 N`，包含另记
	的切向摩擦力；零摩擦 MuJoCo 报告属于不同动力学条件，不可与之作为同条件
	力幅度对照。新增的积分后重算并未消除后脚法向差距；下一步核实 Isaac 过滤
	力的时间窗口及接触冲量换算，再对齐两端步末穿透和速度，才能判断材料/求解器
	是否贡献差异。以上均为诊断，不构成 PUSH/CLIMB 安全验收。
- 新报告：`../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-post-step-probe-node2-mujoco-20260928.json`
	SHA-256 `32db017f56465acb8a3ce53c89d1d65b2bedb37e926207b0e30f5932d5b4dee0`；
	其源码哈希与当前 trace 文件一致。

<a id="record-0216"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH Isaac 地面摩擦分量验证

- IsaacLab 地面 Plane 的实际碰撞 prim 为
	`/World/ground/terrain/GroundPlane/CollisionPlane`。以它为过滤目标、每只脚独立
	建立诊断传感器后，同一输入 trace SHA-256
	`2da8a4395a8770e721530c723b88450d6f3cc0daf92d83511a0e0ee0778db00a`
	的 40 步回放完成，无过滤器错误。旧报告与新报告的实测初态、逐步目标、关节
	位置/速度及原 `net_forces_w` 逐项相等，表明新增传感器未改变这次回放。
- 首步 FL/FR/RL/RR 的过滤地面力 Z 为 `43.00/39.62/19.53/16.73 N`，
	与原足体 `net_forces_w` 一致；独立摩擦力的世界 X/Y 分别为
	`(-20.49,-24.94)`、`(-17.33,21.87)`、`(-6.40,-10.82)`、
	`(-2.95,8.76) N`。此场景原 `net_forces_w` 的横向近零**不表示无摩擦力**；
	MuJoCo 的 `floor`-足端世界力包含切向分量，不应直接与单独的 Isaac
	`net_forces_w` 横向分量比较。两端合成力的 X/Y/Z 仍有差异，且采样时刻不同，
	尚不能据此归因材料或求解器。
- 加上 Isaac 独立摩擦力后，首步 FL 地面三维合力约为
	`(-20.49,-24.94,43.00) N`；MuJoCo `mj_step` 后为
	`(-21.56,-22.16,80.92) N`，重新 `mj_forward` 后为
	`(-11.13,-12.79,42.50) N`。横向分量在前一阶段更接近，竖直分量在
	后一阶段更接近；不能混用两阶段的分量构造一组“匹配”接触力。
- 来源报告：`../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-ground-exact-node2-gpu1-isaac-20260928.json`。
	此前使用 `/World/ground/terrain/.*` 的过滤器匹配 5 个 prim，产生全零读数，
	对应 `push-foot-ground-filter-node2-gpu1-isaac-20260928.json` 和
	`push-foot-ground-plane-probe-node2-gpu1-isaac-20260928.json` 均为无效探针。
	下一步对齐步末状态及接触冲量换算窗口，再比较包含切向力的四足响应；不改变
	运行时材料、策略、接触终止或 PUSH-LOW 训练状态。

<a id="record-0217"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 足端摩擦隔离诊断

- IsaacLab 当前 `contact_forces` 未设置接触对过滤器；传感器调用
	`get_net_contact_forces(dt=physics_dt)` 取得足体净接触力。回放报告现显式记录
	`contact_body_names` 和采样语义，不能把该净力等同于 MuJoCo 的 `floor`-足端约束力。
- 同一 node2 输入 SHA-256 `48dadb2084ee8c354d06dd5767c1d2dda6d5d587678ab3650fe0f329278a2ee9`，
	移远箱体至 `x=3 m`，仅在 MuJoCo 诊断中将地面和四脚摩擦置零。首步初态、目标、
	`0.005 s` 步长均与常规报告一致，两者首步均有四个 `floor`-足端接触。零摩擦时
	FL/FR/RL/RR 投影后世界系横向力各分量绝对值小于 `0.00024 N`；常规摩擦时
	最大横向分量为 `12.79 N`。竖直力从 `42.50/38.37/25.72/27.09 N` 变为
	`30.23/28.14/22.24/24.83 N`，关节速度也变化，因此这不是保持动力学不变的
	传感器读数转换，不能据此断言 Isaac 摩擦为零或断定求解器差异的原因。
- 新产物：`../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-zero-friction-node2-mujoco-20260928.json`。
	下一步在 Isaac 使用单足对地过滤接触传感器确认净力与地面力之差，并记录接触力
	换算的物理步长；随后才比较法向和切向响应。诊断不构成独立技能验收。

<a id="record-0218"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 足端世界系接触力对照

- 同一 node2 路径 SHA-256 `48dadb2084ee8c354d06dd5767c1d2dda6d5d587678ab3650fe0f329278a2ee9`、
	箱体移至 `x=3 m` 的 MuJoCo 四步诊断现记录 `floor` 对各足体的世界系三维力，
	分别在 `mj_step` 后及关节投影、`mj_forward` 后采样。首步投影后 FL/FR/RL/RR 的
	X/Y/Z 力分别为 `(-11.13,-12.79,42.50)`、`(-9.64,10.47,38.37)`、
	`(-3.77,-4.11,25.72)`、`(-2.17,3.48,27.09) N`。四脚的 Z 分量等于原法向力；
	新旧同源四步的限幅位置、速度和法向力逐项相等。
- 现有 Isaac 40 步报告输入 SHA-256 `2da8a4395a8770e721530c723b88450d6f3cc0daf92d83511a0e0ee0778db00a`：
	首步四个足体的 `net_forces_w` 横向分量几乎为零，Z 为 `43.00/39.62/19.53/16.73 N`。
	两端 Z 差异依然存在；MuJoCo 横向接触力也未在 Isaac 足体净力中出现。
	Isaac 传感器为足体所有接触的净力，MuJoCo 此字段仅累计 `floor`-足端球接触；
	且 Isaac `scene.update` 的传感器值与 MuJoCo `mj_forward` 重新求解的值不能直接认作
	相同物理时刻。下一步核对两端摩擦接触输出及传感器定义，再比较接触求解参数。
	这不是技能验收或材料差异的因果证明。
- 新诊断报告：`../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-world-force-node2-mujoco-20260928.json`；
	足端力方向及 trace 回归共 9 项测试通过。

<a id="record-0219"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 足端力采样时刻核对

- 对同一 node2 路径 SHA-256 `48dadb2084ee8c354d06dd5767c1d2dda6d5d587678ab3650fe0f329278a2ee9`、
	移远箱体 `x=3 m` 的回放，MuJoCo 在 `mj_step` 后、关节速度/位置投影前读取的首步
	FL/FR/RL/RR 法向力为 `80.92/71.17/49.90/51.25 N`；投影并 `mj_forward` 后为
	`42.50/38.37/25.72/27.09 N`。后者才是此前报告的 `foot_normal_forces`。
	两种读数并非同一状态下的求解结果；新旧 MuJoCo 四步接触力及关节速度逐项一致。
	四脚在两个采样阶段均仅与 `floor` 接触，首步接触法向均为世界 `+Z`；
	法向轴方向不是上述差异的原因。
- Isaac 同一输入 SHA-256 `2da8a4395a8770e721530c723b88450d6f3cc0daf92d83511a0e0ee0778db00a`
	的 40 步回放，在根位姿恢复前与恢复后读取的传感器 `net_forces_w` 逐分量相等，
	新旧首步速度也逐项一致。首步足端竖直力为 `43.00/39.62/19.53/16.73 N`。
	Isaac 传感器记录的是足体净力，MuJoCo 记录的是 `floor`-足端接触约束的局部法向力；
	仅凭这些数值不能把后脚力差归因于求解器或材料。下一步先对齐接触对、法向投影及
	采样状态，再比较力与速度响应；不修改运行时碰撞体、PD 或安全停止。
- 新报告：本地 `../artifacts/go2-piper/contact-repair-20260925/native-safety/push-foot-contact-direction-final-node2-mujoco-20260928.json`，
	远端隔离目录 `outputs/push-foot-force-timing-node2-gpu1-isaac-20260928.json`；均仅为诊断，
	不构成 PUSH/CLIMB 的双仿真独立 32 回合验收。

<a id="record-0220"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 PUSH 接触首发分叉隔离

- fixed-root Isaac replay 禁用 `reset_base` 后，初始根位姿与源 trace 一致到浮点精度；
	`reset_base` 的随机平移/偏航解释了此前 `11.35 mm` / `0.0269 rad` 的锚点偏差。
	回放现在对固定根初态增加一致性检查。此前锚点不匹配的报告不可作为动力学来源证据。
- 节点 2、40 物理步、源轨迹 SHA-256 `48dadb2084ee8c354d06dd5767c1d2dda6d5d587678ab3650fe0f329278a2ee9`：
	原箱体接触回放中 Isaac 首次非零手部接触力在第 1 步，持续至第 23 步；
	但首步最大速度差 `1.85896 rad/s` 出现在腿部小腿关节。只将箱体移到 `x=3 m`
	时首步误差仍为 `1.85896 rad/s`，接触不是首发分叉的必要条件。
- 保持逐步指定自由根、相同关节初态和远处箱体，只禁用两端地面碰撞后，首步速度差
	降至 `0.00419 rad/s`，40 步末最大关节位置差 `0.00208 rad`。下一步优先核对两端
	足底/地面的碰撞几何、初始穿透、接触对与求解器响应；不得用无地面结果宣称动态
	PUSH 验收，也不得据有地面全关节误差直接调臂 PD。
- 该节点 MuJoCo 初态四个 `floor`-足端接触的距离分别为
	`-40.45/-35.28/-26.13/-25.40 mm`；trace 现记录初始接触对、位置和距离。
	这解释了为什么起步时腿部地面响应敏感，但不能单凭穿透认定 USD 碰撞体不同。
	同源路径 SHA-256 `48dadb2084ee8c354d06dd5767c1d2dda6d5d587678ab3650fe0f329278a2ee9`
	的进一步对照显示，Isaac/MuJoCo 四脚球半径均为 `22 mm`，初始球心世界坐标差
	小于 `0.3 µm`；足端几何中心和半径不是首步分叉原因。首步 `0.005 s` 四脚接触力
	在 Isaac 为 `43.00/39.62/19.53/16.73 N`，MuJoCo 法向力为
	`42.50/38.37/25.72/27.09 N`（FL/FR/RL/RR）。MuJoCo 新 trace 与旧同源 trace
	的初态及首步腿速完全一致。两端接触力的传感器采样/求和语义仍待核对；下一步优先
	比较地面材料、接触参数和求解器的首步响应，不改运行时碰撞几何或 PD。MuJoCo
	四脚的运行时 `solref=[0.02,1]`、`solimp=[0.9,0.95,0.001,0.5,2]`、摩擦 `0.6`、
	margin `0`；Isaac 机器人配置的最大去穿透速度为 `1.0 m/s`，但尚未证明这项
	差异导致首步速度分叉。诊断报告分别为
	`native-safety/push-foot-contact-params-node2-mujoco-20260928.json`
	及远端 `outputs/push-actuator-node2-ground-nobox-foot-geometry-gpu1-isaac-seed210-20260928.json`。
- 本次 Isaac 回放请求 `--capture-contact-details` 时，在读取手部传感器
	`current_contact_time` 后未写出报告；关闭该开关即可完成 40 步，接触力仍有记录。
	手部接触位置与持续时间的独立核对尚未完成。三组新同源 trace 和比较报告保存在
	`../artifacts/go2-piper/contact-repair-20260925/native-safety/`，均为诊断产物，
	不替代每模拟器每技能两组独立 32 回合的安全验收。

<a id="record-0221"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-28 固定根部 trace 来源纠正

- 旧 fixed-base MuJoCo trace 在删除 free joint 后仍用 `qpos[:7]` 记录 `initial_state.root_pose`，
	实际记录的是七个关节值；Isaac replay 因此使用了错误的固定根姿态。下方 2026-09-27 的
	fixed-base 重力分叉及资产不一致推断已失效，不能据此修改资产或重力补偿。
- 使用真实根姿态重做无地面、无箱体 node2 对照：正常重力下 joint2/3 初态重力力矩
	MuJoCo 为 `[-15.778774, -5.770777] N m`，Isaac 为 `[-15.778770, -5.770771] N m`；
	32 步零力矩首步速度分别为 `[0.128050, -0.101016]` 与
	`[0.128336, -0.101583] rad/s`。40 步正常 PD 的全关节最大位置/力矩误差约
	`0.000631 rad`/`0.0221 N m`。零力矩长时段到达 joint2 上限后，两端限位响应不同，
	不属于初态重力资产差异。
- Isaac fixed-root 实测 root link pose 与源锚点平移约 `11.35 mm`、偏航约
	`0.0269 rad`；严格来源比较仍会拒绝这项根位姿差异。下一步先对齐 fixed-root
	USD 锚点/根 frame，并在自由根、无箱体的同源 trace 上核对重力与接触；再返回
	PUSH 动态跟踪。PUSH-LOW 训练、实机接触和双仿真验收仍暂停。

<a id="record-0222"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-27 Sim-to-sim 重力模型边界

以下是纠正根位姿前的历史诊断，仅保留溯源，不作为资产不一致证据。

- 已完成真正 fixed-base、无地面、零重力的 node2 40 步来源匹配对照：最大位置误差
	`1.11e-4 rad`、速度误差 `2.31e-3 rad/s`、力矩误差 `1.48e-2 N m`。当前不再把
	actuator delay、PD 更新顺序、armature 或 torque 采样顺序列为首要嫌疑。
- 常重力 fixed-base 对照显示 MuJoCo 初态 `qfrc_bias=[-16.153,-6.141]`，Isaac
	gravity compensation 为 `[+15.880,+6.003]`。两端的重力响应/补偿约定不一致，正是
	原始 no-box 分叉的可重复边界；“直接翻转 MuJoCo 补偿符号”试验已证伪并撤回。
- 下一步只做来源匹配的 robot asset 对照：初态零力矩 gravity response、PIPER link
	inertial frame、joint axis/pose、质量与惯量；保持箱体尺寸/质量/目标、安全终止和冻结
	actor 不变。未完成该对照前，不修改运行时 PD，不恢复 PUSH-LOW 训练，不进入实机接触。
- `--fix-root-link`、`--disable-floor/--disable-ground` 和重力遥测是诊断开关，不属于
	生产任务契约。fixed-base + 地面接触的 MuJoCo 过约束结果不用于验收。

<a id="record-0223"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-26 普通 PUSH 安全接触边界

- PUSH-LOW 训练保持暂停。普通 PUSH 的最新动态安全诊断全部使用冻结 `model_599.pt`、
	不变的 `5 kg`/摩擦 `0.4`/`0.60 m` 箱体任务和选择性原生碰撞，不得把诊断参数或单条录像
	写成训练成功或验收通过。
- 静腿上沿接触可连续保持 `19.3403 s`，但没有推进；去除中性腿后策略腿动作与合成关节命令
	均可观测到，说明不是动作接口断开。当前动态失败的直接边界是底盘前移后手部合法接触只能
	保持约 `1.9 s`，随后由 `invalid_hand_contact` 正确终止，箱体至多移动 `0.44 mm`。
- 接触力伺服的 `8 N` 小于箱体静摩擦下限 `19.62 N`；不得仅通过提高目标力解决，因为锁臂
	动态回合在 `16.9640 N` 已失去合法手接触。详细报告、视频、哈希和代码修复见
	[交接手册](#source-agent-handoff-cn)。
- 下一步只做一个几何/动力学闭环切片：对 `base x=-0.14 m` 至前推所需位置求解在线手臂
	姿态和最小净空轨迹，记录实际 IK 目标、关节软限位、力矩比例、接触位置和逐物理步接触。
	该轨迹先在 Isaac 与 MuJoCo 同状态对照，随后才运行新的独立动态回合；不扫描力阈值，
	不放松接触或碰撞终止，不恢复训练。
- 已在实际失败底座 x/y/z 轨迹上找到最低 `59.87 mm` 净空的静态连续机械臂支路；但以
	预设基座驱动真实 MuJoCo 臂 PD 时，无接触状态下 joint2 仍出现约 `0.16 rad` 稳态偏移，
	末端误差超过阈值。下一步必须先建立与 Isaac 同状态的执行器重力补偿/延迟闭环对照，
	证明该支路可动态跟踪后才能写入 PushArmIK。不得从单点 `0.66` 重力补偿试探推导运行时参数。
- 已完成 40 步、每物理步根部固定的 MuJoCo/Isaac PUSH actuator 对照。根位姿、初态、
	目标与延迟均已对齐，joint2/joint3 仍在第 0–5 物理步出现速度、力矩和位置分叉；这不是
	腿部目标或根部反作用。节点 2 的来源匹配 trace 已完成小规模标定：被动
	armature/damping 只能将目标函数从 `6.3004` 降至 `6.0107`，PD 比例搜索可降至
	`2.8037`，但 joint3 仍有约 `0.0613 rad` 误差；这些结果是诊断，不是运行时参数。
	节点 0、1、3 的同源搜索结果分别为 `4.6497 -> 2.3452`、`5.3094 -> 2.6287`、
	`5.7098 -> 3.7992`，最优增益随节点变化，不能选择一个全局 PD 比例。下一步逐关节
	核对积分、阻尼、armature、增益和延迟，优先解释跨节点稳定存在的 joint3 误差。完整
	`40 x population 8` 搜索后，PD 目标函数分别降至 `1.6663/1.3479/1.8742/1.3209`，
	但节点 2/3 的 joint3 误差仍约 `0.0835/0.0808 rad`，且最优比例不一致；因此不能
	选择全局运行时参数。只有来源匹配的首发分叉消除后，才可重新验证连续臂姿态路径或动态 PUSH。
	延迟历史初始化的 `zero/current` A/B 对照在节点 2 上逐项相同，已排除它是主要分叉来源。
	下一步转向 PhysX 隐式积分、关节摩擦实现和 MuJoCo 显式 PD 更新时序的逐物理步对照。
	完整 `max_iterations=40` 搜索后，四节点 PD 目标函数分别为 `1.6663/1.3479/1.8742/1.3209`，
	但节点 2/3 的 joint3 误差仍为 `0.0835/0.0808 rad`，且最优比例依赖节点；passive
	搜索不能解释主要误差。下一步应转向逐物理步的执行器更新时序、软限位和 PhysX 隐式积分
	对照，不得把搜索参数写回运行时。节点 2 的 2/4 子步低成本对照已将基线目标函数降至
	`5.5840/5.4487`，但位置误差仍约 `0.0713 rad`；待四节点 4 子步完整搜索结束后，
	四节点 4 子步搜索已完成，基线目标函数为 `4.2798/5.2677/5.4487/5.6509`，优化后为
	`2.2459/1.6540/1.9572/1.4932`，但 joint3 误差仍为 `0.0518/0.0706/0.0878/0.0762 rad`。
	积分细化不是唯一根因，下一步继续对照 PhysX 隐式积分、摩擦实现和软限位时序。
	另外，来源匹配的 actuator trace 必须恢复箱体 root state；当前新 trace 已记录该字段，
	但远端 Isaac replay 尚未产出 JSON，接触时序修复仍未完成验收。四节点 MuJoCo 固定箱体
	首次接触步为 `8/5/1/1`，旧 Isaac link6 首次非零力为 `9/7/6/6`；下一步优先核对
	PhysX 默认 contact/rest offset 和 sensor update 时序，不得先修改碰撞参数或恢复训练。
	四节点 margin/solref 扫描已排除 solver 参数单独解释节点2/3延迟；恢复远端后优先读取
	新增的 `box_contact_hand_time/position`，再决定是否需要修正 USD 碰撞资产或传感器配置。
	节点2 已用同箱体初态完成 Isaac replay，首次接触与 MuJoCo 均为第 `1` 步；匹配 trace
	标定 baseline objective 为 `1.7440`，PD 搜索降至 `0.5240`，但最大位置误差仍约
	`0.02955 rad`。下一步从接触时序转回来源匹配的 PhysX/MuJoCo actuator 动力学差异，
	保持训练暂停，不写回搜索得到的 PD 参数。逐步数据表明 Isaac hand force 峰值约 `30.26 N`、
	MuJoCo 约 `22.65 N`，第24步后 Isaac 接触消失但关节误差继续增长；下一步做无箱体或固定
	接触序列 replay，区分接触响应与执行器积分误差。no-box node2 对照已完成：箱体移至
	`x=3.0 m` 后 baseline objective `2.1145`、position RMSE `0.01969 rad`，仍有与接触版
	同量级的分叉；接触不是唯一根因。下一步优先做无接触状态下的 PhysX/MuJoCo 执行器
	积分、延迟和隐式/显式 PD 响应对照。no-box 零重力 baseline objective 为 `2.3357`，
	没有优于有重力的 `2.1145`，因此重力不是主要根因。Isaac step 前后 torque 采样完全
	一致，剩余误差来自物理步内状态演化；当前 root 并非 fixed，下一步建立真正的 PhysX
	root-fixed/腿部反作用隔离 replay。

<a id="record-0224"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-25 PUSH-LOW 接触诊断

- 运行状态已复核：训练日志止于 `58/3000`，当前无该 PIPER 训练进程，只有 `model_0.pt`；
	日志未说明停止原因。新增 PRECONTACT 姿态需单独通过真实 PD 动态净空验收。
- 已确认 ARX5 `push-low` 的真实训练任务是平地直推低板，不是 gap 本体。低板参数已按
	ARX5 迁移到 PIPER；gap/bridge 只作为训练成功后的组合任务，不得用其静态截图替代
	`push-low` 物理验收。
- PIPER 保留 16 段 SAFE_APPROACH；当前低板诊断使用位置 IK 和接触后不锁臂，没有复制
	ARX5 机械臂关节姿态。身体静稳门为 gap `0.36 +/- 0.07 m`、横向误差 `<0.08 m`、底座高度
	`0.28 +/- 0.035 m`、线/角速度 `<0.06/0.20`、重力投影 z `<-0.96`，连续保持 `0.5 s`。
- 预接近 4 s 超时从 SAFE_APPROACH 完成后开始；回合由 12 s 扩为 24 s，避免安全路径与
	理论最短 7.5 s 推动时间挤占成功窗口。
- 已完成本地 MuJoCo 初始几何/穿透契约、远端任务注册、PPO 单迭代 smoke、NAV 初始化
	smoke，以及 4 s/10 s 各 16 环境启动检查。10 s 检查为 SAFE_APPROACH `16/16` 完成、
	body-ready `9/16`、所有环境无终止；这不是推动成功率。
- 1024 环境、3000 iteration 的 NAV 初始化训练已尝试启动，探索标准差 `0.25`。工作目录
	为 `/path/to/artifacts/go2-piper/2026-09-24-push-low-piper-z2O4vb`；本次该 run 仅找到
	`model_0.pt`，日志止于 `58/3000` 且无该训练进程，不能继续按“训练进行中”交接。
- `model_0` 的 seed `100` 单回合诊断全部未成功：初版姿态 IK 在 `11.32 s` 因
	`arm_body_clearance` 终止，位置 IK 在 `11.28 s` 因 `invalid_hand_contact` 终止；
	PRECONTACT 快速段且锁臂的版本在 `24 s` 超时，推动方向位移 `0.04508 m`；最新不锁臂
	版本在 `10.20 s` 因 `invalid_hand_contact` 终止，位移 `0.05247 m`，目标误差
	`0.84894 m`。这不是训练后验收或成功率统计。
- 优先修正配置初始化：低板子类的 `push_approach_distance = 0.08` 被父类覆盖成
	`0.03 m`，已有 `80mm` 报告也记录为 `0.03 m`。修复后先验证实际环境参数，再用新的
	报告名与哈希重跑；不能把旧结果标为 80 mm 对照。
- 核对低板判据与碰撞几何：当前 margin `0.0 m`、末端邻域 `0.12 m` 不同于历史 PUSH
	的 `0.01 m` / `0.07 m`；须说明物理接触位置及力方向，避免以放宽判据代替控制改善。
- 已有两段失败录像与同名 JSON 位于 `../artifacts/go2-piper/push-low-2026-09-24/`：
	`model0_eval_seed100.mp4`、`model0_position_ik_eval_seed100.mp4`。本次另行补录
	[当前不锁臂候选](../../../artifacts/go2-piper/push-low-2026-09-24/model0_effective30mm_unlocked_video_seed100_20260925.mp4)，
	有效接近距离 `0.03 m`，仍在 `10.20 s` 非法手接触终止；视频与同名 JSON 的来源核对
	通过，完整哈希和验证记录见 [交接手册](#source-agent-handoff-cn)。
- 修正参数和接触控制后，先做动态诊断与短训，再在新 run 继续训练；阶段性独立 Play
	评估至少记录 SAFE_APPROACH、body-ready、有效手接触、板位移、目标静稳、臂身净空
	和全部终止原因。只有来源匹配的独立评估可用于选模，详细结果见交接手册。
- 选模后建立同尺寸低板的 MuJoCo 闭环场景并验证动态碰撞/穿模，再进入 gap/bridge 的板放置、
	双岸支撑和 NAV/CLIMB 组合验收。当前不得进入实机低板接触。

<a id="record-0225"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-23 SAFE_BASE 独立评估

- `go2_piper_box_push_safe_base/2026-09-22_20-13-25/model_99.pt` 已结束 100 迭代训练；
	checkpoint SHA-256 为 `85a3981d595170d3b224a9fdc45890217e9fbdf7aa3561f81702c58d42b02980`。
- `scripts/evaluate_safe_base.py` 以 SAFE_BASE Play 配置独立加载该 checkpoint，固定每回合
	12 s、32 环境、seed `100..103`；仅 `time_out` 且无其他终止计为通过。实际结果 `128/128`
	到时，`base_contact`、`arm_body_clearance`、`low_posture`、`bad_orientation` 及其余终止
	均为零。四份逐环境结果在 `../artifacts/go2-piper/safe-base-2026-09-23/eval_seed_*.json`，
	评估脚本 SHA-256 为 `b15d544646bf0bc5fc8a2f7f2f894adb89fd5424562172f0be5eacf96934935d`。
- 四组极值：底座最低高度 `0.3139 m`、最大倾角 `0.2210 rad`、最大瞬时线速度
	`0.9726 m/s`、最大瞬时角速度 `2.8565 rad/s`；臂与受保护刚体的**中心距离**最小
	`0.1007 m`，终止阈值 `0.08 m`，不是几何表面净空。速度尚未按预接触静稳阈值验收。
- 单独的分时段诊断只完成 seed `100`（32 环境）：`0–2 s` 线/角速度峰值为
	`0.973 m/s` / `2.857 rad/s`，`2–10 s` 为 `0.048 m/s` / `0.100 rad/s`，
	`10–12 s` 为 `0.031 m/s` / `0.093 rad/s`。这是零初速度重置下的启动冲击与后续
	静稳趋势，不代表 SAFE_APPROACH 完成后的实际切换速度；该诊断使用更新后的评估脚本，
	结果为 `../artifacts/go2-piper/safe-base-2026-09-23/eval_window_seed_100.json`，
	不得与上面四组旧版哈希混作同一批验收。
- 结论仅限于 Isaac 中安全臂姿态启动后的定时站立，未覆盖 SAFE_APPROACH 到 SAFE_BASE 的
	状态切换、MuJoCo 回放、在线 PRECONTACT 或任何推箱接触。下一步先量化接近结束状态
	分布，并用非零初速度复核切换后静稳速度，再设计基于当前 box/base 状态的在线
	PRECONTACT，不得放行实机 PUSH。

<a id="record-0226"></a>

来源：NEXT_STEPS_CN.md。

## 2026-09-22 PUSH 安全控制更新

- MuJoCo 已具备选择性 arm-base/leg collision、路径投影和主动撤退；seed `500..503`
	的 12 s 回放均无受保护接触。
- Isaac 已加入 `arm_body_clearance` 终止和 failure reward。2048 环境短训中该项触发率
	约 `0.49%`，但冻结 `model_599` 没有完成奖励，不能直接继续训练。
- 全局 articulation self-collision 会造成约 `99%` base-contact，已证伪。静态 FK 安全的
	waypoint 也可能在真实 PD 回放中进入碰撞谷，不能作为训练候选。
- 已证伪：安全接近阶段将腿部名义刚度和阻尼整体提高到 `2x`，第二段 waypoint 在真实
	PD 回放 step `32` 出现约 `-3.64 mm` 的 arm-base 穿透，不能作为 base-hold 方案。
- waypoint 搜索实测：8 段路径的动态最小净空为 `6.59 mm`，16 段为 `10.06 mm`，32 段
	回落至 `6.07 mm`。段数不能替代动力学代价，下一轮必须以真实 PD 最小净空排序候选。
- 已完成 SAFE_APPROACH：动态排序后的 16 段路径已固化为
	`mujoco/deploy/piper_push_safe_approach.json`。实际 runtime gate 在 seed `500..531`
	达到 `32/32` 完成、最低动态净空 `20.06 mm`、无受保护接触。该成果只覆盖安全接近，
	尚未覆盖 PRECONTACT、有效接触、推箱或策略验收。
- SAFE_APPROACH 完成后已启用安全 hold：在 32 个初态继续保持 12 s，仍为 `32/32` 无碰撞，
	冻结 PUSH actor 未被放行。固定 joint-space PRECONTACT 路径虽然满足净空，但因底座/箱体
	相对状态变化出现最大约 `140 mm` 末端误差，已拒绝固化；PRECONTACT 必须使用当前状态的
	在线目标与专门的腿部稳定/接近控制。
- 当前阻塞：`mujoco/plan_piper_push_waypoints.py` 必须找到动态最小净空至少 `15 mm` 的
	`PRECONTACT` 多段路径，随后才可接入 Isaac `PushArmIK` 并启动新训练。
- 本轮外部诊断位于 `../artifacts/go2-piper/piper-collision-projection-*` 和
	`../artifacts/go2-piper/piper-waypoint-search-*`，不属于验收产物。

### 1. 修复 PUSH 机械臂净空与自碰撞

现状：PIPER PUSH 的手臂由箱体目标微分 IK 驱动，训练资产关闭自碰撞，IK 没有 Go2 机身、头部与前腿净空约束，导致可达但不安全的臂链轨迹。

执行：

1. 为 PIPER 臂链与机身、头部、前腿建立白名单碰撞对和最小净空距离。
2. 在姿态 IK 中加入碰撞距离代价或约束投影；输出可审计的最小净空与违规 link 对。
3. 将自碰撞/净空违规加入训练终止、评估失败原因和 MuJoCo 对照。
4. 在新任务与新 checkpoint 上重训 PUSH，完成两组 Isaac 和两组 MuJoCo 验收。

### 2. 提升 CLIMB 姿态质量与稳定性

现状：CLIMB 能在 Isaac 终态达标，但动作存在明显左右非对称和高冲击支撑；MuJoCo 最佳独立组仅 `23/32`。

执行：

1. 建立接近、前足上台、后足转移、四足停稳的阶段课程。
2. 添加左右对称、关节速度/加速度、足端冲击、机身姿态和能耗约束，并记录各项指标。
3. 将完整 18 维策略与“固定安全机械臂姿态加腿部策略”做受控消融。
4. 对来源匹配的失败种子做逐物理步接触、关节边界和状态分叉分析。

### 3. 收敛 Sim-to-Sim

现状：PUSH 与 CLIMB 静态资产和观测已对齐，但接触丰富阶段仍存在 PhysX/MuJoCo 约束与接触时序差异。

执行：

1. 固定 actor、初态、目标、延迟和数值后端，持续使用逐物理步重放定位首次分叉。
2. 不再扫描已证伪的接触参数组合；仅依据首次分叉证据修改约束或接触实现。
3. 新控制候选必须先通过来源匹配开环对照，再进入两组 32 回合闭环验收。

### 4. 准备实机分级验证

1. 确认机械安装、实际安装变换、总质量和全局质心。
2. 确认 Go2/PIPER 的控制模式、状态频率、延迟、关节方向、零点与力矩/速度/电流限制。
3. 建立统一时间戳、独立急停、通信超时、姿态异常与驱动器故障处理。
4. 仅在双仿真验收通过后，依次进行悬空、支架、平地低速、无箱体动作和低风险接触测试。

<a id="record-0227"></a>

来源：PROJECT_PLAN_CN.md。

# GO2-PIPER 项目计划

更新日期：2026-10-07（CLIMB技能边界与当前优先级）

<a id="record-0228"></a>

来源：PROJECT_PLAN_CN.md。

## 目标

建立可复现、可审计的 GO2-PIPER 底层技能闭环：平地导航、指定末端推箱和低台攀爬，以安全、分级的 Sim2Real 为最终目标。MuJoCo 是独立风险筛查工具，不是必须与 Isaac 逐步一致的部署目标。

<a id="record-0229"></a>

来源：PROJECT_PLAN_CN.md。

## Re-NAV 分工与跨组交付

Re-NAV 有三个并行方向：本组负责 GO2-PIPER 底层技能训练、优化和实机部署；世界模型组负责可重构核心研究，目前在 GO2-ARX5 上使用其自训策略；reachability 组使用 GO2-PIPER 研究本体可执行可达性，目前缺少成熟控制策略。现有实物条件只有 PIPER 机械臂，因此世界模型研究成果的实机迁移也依赖可用的 PIPER 技能。

本组应向其他两组交付可版本化的 GO2-PIPER 技能，而不只是权重文件：每项技能包含任务语义、观测/动作和关节顺序契约、匹配控制器与资产、checkpoint/actor 哈希、独立评估结果及适用边界。世界模型组当前的 ARX5 策略不能直接作为 PIPER 策略；reachability 组可先使用明确标注边界的仿真参考策略，不得将其当作实机许可。世界模型若需要低板或架桥动作，普通 PUSH 的验收也不能代替 PUSH-LOW。

<a id="record-0230"></a>

来源：PROJECT_PLAN_CN.md。

## 系统结构

```text
PIPER 训练资产与任务
        -> PPO 策略 / PUSH 姿态 IK
        -> Isaac 原生验收
        -> MuJoCo 来源匹配的任务级风险筛查与失败归因
        -> 实物参数标定与安全控制器
        -> 分级实机验证
```

技能职责：

- NAV：平地目标位置与朝向控制。
- PUSH：12 维腿部策略加受限机械臂 IK，以指定手部推面推动自由箱体。
- CLIMB：冻结actor与受约束控制器配合，逐脚登上20cm固定台面；四足承重停稳后前脚逐只展开，再最后前移重心达到舒展稳定姿态。之后到任务目标点由NAV负责，技能切换另行验证。

<a id="record-0231"></a>

来源：PROJECT_PLAN_CN.md。

## 安装假设

GO2 与 PIPER 在训练和 MuJoCo 中按刚性固定安装建模：PIPER 是 `base_link` 的子体，没有
安装自由度或独立悬挂。实际运行的 MuJoCo profile 使用相对平移 `(0, 0, 0.07 m)`、单位旋转；
原始 XML 的 `0.06 m` 仅是被 profile 覆盖前的源值。任何实物安装偏差都会同时改变 FK、
碰撞距离、重力补偿、质心、接触反作用和 Sim2Real 初态，必须作为受控模型版本更新。

<a id="record-0232"></a>

来源：PROJECT_PLAN_CN.md。

## 验收标准

| 阶段 | 条件 |
| --- | --- |
| 原生 Isaac | 两组独立 32 回合，每组至少 30 成功，无未完成回合 |
| MuJoCo 风险筛查 | 沿用两组独立 32 回合、每组至少 30 成功及相同成功/安全判据报告结果；未通过必须定位失败机制和实机相关性，不作为逐步物理量一致性门槛 |
| 控制来源 | checkpoint、actor、任务源码、控制器、profile、资产和数值后端均可追溯 |
| 实机 | 安全链路与标定完成后，按悬空、支架、平地、接触的顺序逐级验证 |

PUSH 的成功要求指定手部接触、目标误差小于 `0.12 m`、箱体速度小于 `0.08 m/s` 并持续 `0.5 s`。CLIMB 要求四足位于安全顶面、姿态和速度合格，并保持 `1 s`。不得通过降低碰撞、姿态或停稳门槛提升结果。

MuJoCo 未通过不等于策略在实机必然失败，但未解释的摔倒、碰撞、超限、停止失效或任务失败也不能被跳过。先核对观测/动作接口和资产来源，再用任务时序与物理量判断风险是否可能出现在实机；可信或未排除的安全风险阻止相应实机阶段。完成两端批量验收、风险归因和独立实机安全链路验证后，才可逐级推进；不要求 Isaac 与 MuJoCo 的首步接触力或轨迹完全重合。PUSH-LOW 训练及实机接触仍暂停，诊断报告不构成验收。

<a id="record-0233"></a>

来源：PROJECT_PLAN_CN.md。

## 当前优先级（2026-10-07）

CLIMB功能在Isaac阶段初态中已验证：四秒摆脚两组各32/32，三秒摆脚一组32/32并平均提前20秒完成双前脚展开。先冻结提速版完成另一组回归，再逐项提高效率且重验成功率；不重训NAV/PPO。当前约3～4分钟仍不满足效率目标。证据、运行状态和交付路径见[CLIMB当前小组交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)。

CLIMB完成以逐脚登台、真实承重停稳、前脚展开和舒展稳定为边界；旧台面中心目标属于位置任务，保留原指标但不再作为CLIMB是否学会的结论。补齐独立完成信号、既有NAV接近与稳定后接管；正式原起点两组未用种子各32、各至少30成功/无缺失及原速录像验收仍待完成，不能用调试种子替代。

PUSH技能、MuJoCo、实机暂停。物理评估、训练和录像仅在既有远端；候选只存外部产物，指定Git分支同步交接文档。下面为历史记录，旧奔跳/未攀爬结果不代表当前候选。

<a id="record-0234"></a>

来源：PROJECT_PLAN_CN.md。

## 2026-09-29 优化状态

同日追加的 CLIMB 低标准差探针在 Isaac 两组达到 `32/32`、`30/32`，
但 MuJoCo 两组均为 `14/32`，相同配置的冻结 actor 为 `16/32`（一组）。
候选未改善跨仿真验收，仍仅作诊断；详见[训练与评估记录](#source-training-status-20260929-cn)。
以下为更早的 Tracking/Smooth 首轮结果。

用户已授权继续普通 PUSH、CLIMB 优化与训练。原技能 checkpoint 已独立备份；
首轮 Tracking 与 Smooth 候选均未通过 Isaac 评估：PUSH seed `517` 为 `0/32`，
29 回合触发臂身净空停止；CLIMB seed `511` 为 `0/32`，31 回合触发底座接触、
1 回合姿态异常。PUSH 报告中的 `0.598 m` 是机器人底座最大前移，箱体最大
终态前移约 `0.400 m`，也未安全完成停稳；CLIMB 的力矩仍达到
仿真限幅，不能将增加平滑惩罚等同于电机保护。当前无已验收的新策略或实机放行。

下一轮先解决 PUSH 接近效率与跟踪净空、CLIMB 起步接管与姿态/关节运动风险，
再扩大独立训练和多种子评估。具体优先级见 [下一步计划](#source-next-steps-cn)；
历史原生成功率、9 月 26 日诊断录像与 9 月 29 日新候选必须分别记录来源。
本轮产物身份与结果见 [训练与评估记录](#source-training-status-20260929-cn)。

<a id="record-0235"></a>

来源：PROJECT_PLAN_CN.md。

## 训练与控制原则

- 冻结通过验收的 actor；任何优化在新 run、独立 checkpoint 和独立报告中进行。
- PUSH 机械臂采用受限 IK，训练和运行时都必须包含关节限位、速度限制、净空与合法接触约束。
- CLIMB 训练需要接触课程、左右对称、动作平滑、关节速度/加速度、冲击与能耗约束，不能只优化终态成功。
- 先对质量、质心、惯量、安装变换、关节零位、延迟、FK/Jacobian、重力与观测逐项对齐，再讨论接触迁移。
- 实机数据仅以只读状态和受控试验采集方式进入标定与训练回灌。

安全接近必须经过动态验证的多段 waypoint；静态 FK、单条录像或关闭碰撞后的成功不构成
安全证据。

<a id="record-0236"></a>

来源：PROJECT_PLAN_CN.md。

## 交付物

- 冻结策略包与完整 checkpoint；
- 训练、评估、导出和回放入口；
- PIPER 资产、碰撞与惯量 profile；
- 每项候选的 SHA-256、评估报告和失败原因统计；
- 分级实机控制与安全验证记录。

<a id="record-0237"></a>

来源：PUSH_ISAAC_RUNBOOK_CN.md。

# 当前 PUSH Isaac 运行说明

**跨组使用请先读 [最新PUSH交接入口](../PUSH_CURRENT_HANDOFF_CN.md)**，其中提供已验收100mm候选的完整命令、策略目录、接口和适用范围。本文保留旧诊断与训练背景，下方首段80mm命令不是当前交付配置。

最新aa/model199配合100mm压入，原5kg/.4摩擦/12秒独立2701/3701为30/32、32/32，无未完成回合，已达到Isaac数量门槛；2701有2次无效手接触，仍须继续改进。下方80mm命令仅保留为旧诊断复现。完整结果见[负载与验收记录](#source-push-load-comparison-20261001-cn)。

<a id="record-0238"></a>

来源：PUSH_ISAAC_RUNBOOK_CN.md。

## 环境与产物

训练和物理评估在既有服务器运行，使用 `/path/to/bin/isaac-python`；在包含本分支源码的隔离检出目录执行。保留仓库中的 `mujoco/deploy/piper_push_safe_approach.json`，它也是Isaac控制器读取的安全接近资源。不要只复制scripts/source而漏掉该文件。

本地CPU检查使用项目隔离Python，不安装到系统环境。权重、原始报告、日志和录像存储在仓库外；Git提交不代表策略已经验收。远程aa根目录为 `/path/to/artifacts/go2-piper/push-ramptrain-20261001-aa`。

<a id="record-0239"></a>

来源：PUSH_ISAAC_RUNBOOK_CN.md。

## 复现已知诊断基线

以下仅复现旧u/model199配合当前.7秒控制的seed1701诊断，预期27/32且无安全终止。输出路径必须是新的文件，避免覆盖历史结果；这不是新的独立验收。

```bash
export PYTHONPATH="$PWD/source/LeggedManip_Lab"
export CUDA_VISIBLE_DEVICES=0
CHECKPOINT=/path/to/artifacts/go2-piper/push-contacttrain-20261001-u/train/logs/rsl_rl/go2_piper_box_push_hybrid/2026-10-01_06-08-49_contactstate_all_seed627/model_199.pt
REPORT=/tmp/push-ramp70-seed1701-new.json
/path/to/bin/isaac-python scripts/evaluate_box_skills.py \
  --task GO2-PIPER-Box-Push-Tracking-Play \
  --checkpoint "$CHECKPOINT" \
  --num_envs 32 \
  --episodes-per-env 1 \
  --seed 1701 \
  --steps 900 \
  --episode-length-s 12 \
  --headless \
  --device cuda:0 \
  --push-ik-clearance-minimum 0.10 \
  --push-hand-pitch 0.6 \
  --push-height-offset 0.03 \
  --push-contact-memory-s 0.10 \
  --push-leg-release-ramp-s 0.7 \
  --push-leg-contact-ramp-s 0.2 \
  --push-press-on-legal-contact \
  --push-forward-command-gain 2.0 \
  --press-depth 0.08 \
  --push-ik-joint-limit-solve \
  --push-goal-hold-pose \
  --push-stop-distance 0.11 \
  --push-ik-orientation-weight 0.5 \
  --output-json "$REPORT" \
  --push-contact-gap-slowdown-start 0 \
  --failure-history-steps 128
```

该权重SHA-256为 `8c73bc1628da628cb4330143f14b2fd1fb5e7cdf1fb1e98a92fd55418f7de748`。报告记录控制器、机器人资产、权重和评估源码哈希；比较前核对这些字段。128步失败历史约2.56秒，状态采于下一步执行前，终态另在重置前保存；不要把上一命令参考当作下一动作结果。

<a id="record-0240"></a>

来源：PUSH_ISAAC_RUNBOOK_CN.md。

## 复现当前100mm候选

沿用上面的全部控制参数，将CHECKPOINT替换为：

```text
/path/to/artifacts/go2-piper/push-ramptrain-20261001-aa/train/logs/rsl_rl/go2_piper_box_push_hybrid/2026-10-01_09-36-12_ramp70_all_seed628/model_199.pt
```

同时显式设置 `--press-depth 0.10`，选择seed2701或3701及新的输出路径。重跑这两个种子属于复现，不能算新独立验收。模型SHA为 `b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721`。完整原验收脚本为ac目录的 `launch-held-out-2701.sh` 与 `launch-held-out-3701.sh`。

本地ac/selected-candidate保存权重、源码快照和evaluation-contract.json。training-params/env.yaml的压入是80mm；复现已达标候选需按100mm评估契约覆盖，勿仅使用训练配置。减载对照使用80mm，并分别设置 `--box-mass 4` 或 `--box-friction 0.3`，其他参数不变；不同时减小两者。

<a id="record-0241"></a>

来源：PUSH_ISAAC_RUNBOOK_CN.md。

## 当前训练与选择流程

aa从旧u/model199初始化，seed628、512环境、200轮、std.03、固定lr1e-5。使用完整样本PPO，原12秒/5kg/摩擦.4/推进.6m；保留原奖励、力矩、关节、净空、合法接触与停稳要求。训练实际env.yaml/agent.yaml和有限启动/监控脚本已归档aa目录。

第100/199轮分别在517/701/1701评估，每批32回合；按最差批次、总成功数、较少安全失败依次选择model199。80mm未达到三批门槛，因此aa未启动验收；ac的100mm诊断三批均32/32，先写入选定权重、控制、物理配置及SHA，再于10:09启动2701/3701。最终30/32、32/32，满足每批>=30/32且无未完成回合。此后不得将这两个已用种子再次称为新验收。

可查看远程 `outputs/pipeline-status.json` 追溯训练与评估。原训练PID3911950、监控PID3911952对应的流程已结束。当前PUSH优化暂停，保留本版供Isaac仿真接入；研发主线为CLIMB，MuJoCo与实机暂停。

<a id="record-0242"></a>

来源：PUSH_ISAAC_RUNBOOK_CN.md。

## 提交前本地检查

使用项目隔离Python运行：

```bash
python scripts/check_box_push_control.py
python scripts/check_box_evaluation.py
python scripts/check_skill_initialization.py
python scripts/check_push_action_sampling.py
```

本轮共59项通过。它们验证控制数值、采样/初始化和评估记账；策略性能仍以来源匹配的远程Isaac报告为准。

<a id="record-0243"></a>

来源：PUSH_LOAD_COMPARISON_20261001_CN.md。

# PUSH 负载与压入参考对照：2026-10-01

给其他小组使用的当前版本、文件和完整启动命令见 [最新PUSH交接入口](../PUSH_CURRENT_HANDOFF_CN.md)。本文作为验收证据保留；当前研发优先级以交接首页为准。

用户要求适当减小箱体质量或摩擦后进行实验。当前两组减载均已完成，固定同一权重、seed1701、32回合、12秒，箱体尺寸1.2×1.2×.20m，目标推进.60m。原合法接触、净空、关节/力矩限幅和成功停稳条件均不变。

| 质量 | 静/动摩擦 | 压入参考 | 成功 | 安全终止 | 未完成 |
| --- | --- | --- | --- | --- | --- |
| 5kg | .4/.4 | 80mm | 28/32 | 0 | 0 |
| 4kg | .4/.4 | 80mm | 32/32 | 0 | 0 |
| 5kg | .3/.3 | 80mm | 32/32 | 0 | 0 |
| 5kg | .4/.4 | 90mm | 31/32 | 0 | 0 |
| 5kg | .4/.4 | 100mm | 32/32 | 0 | 0 |

前两种减载是独立的单变量实验，没有同时降低质量和摩擦。质量降低20%，或静/动摩擦从.4降至.3，均使原失败env0/1/10/11成功，且无超时。Isaac实际物理视图读回的质量、静/动摩擦系数已经核对。

减载后的推进改善支持负载影响持续推力/跟踪的判断，但不能断言只有某一个关节或力矩上限是原因。4kg下原四个失败回合的终态手端高度约.072–.110m；摩擦.3下约.062–.074m。后者仍可在手端较低时完成，说明“高度恢复”不是成功的必要充分条件，需同时看接触、推进与停稳。

原负载的90/100mm是控制目标变化，并未提高实际执行器力矩上限。100mm在已用于调参的517/701/1701均达到32/32、零安全终止，随后固定候选进入两个新种子的独立验收。较轻任务的32/32也不能替代原5kg/.4任务的独立证据。

<a id="record-0244"></a>

来源：PUSH_LOAD_COMPARISON_20261001_CN.md。

## 来源与复核

固定权重为aa/model199，SHA-256 `b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721`。aa原80mm在517/701/1701为31/32、32/32、28/32，均无安全终止；200轮训练及六份检查点评估已完成。

共同控制：限位内IK、姿态权重.5、净空参考.10m（原终止.08m）、手端俯仰.6rad、高度偏移.03m、接触记忆.1秒、真实合法接触维持推压、普通腿部接管.7秒/接触后.2秒、到位保持、控制停止距离.11m。间距减速、到位卸力与制动关闭。

远程结果：`/path/to/artifacts/go2-piper/push-lightload-20261001-ad/outputs/` 与 `push-loadprobe-20261001-ac/outputs/`。本地报告、脚本、逐失败环境对比与SHA清单位于仓库外同名目录 `../artifacts/go2-piper/`。Git只保存源码与说明，不含权重、视频或训练日志。

| 报告 | SHA-256 |
| --- | --- |
| mass4-seed1701.json | a3321d8adc9187ea04ef006832001e0806c19d2c3e6ee1ef2f408a6980877c8a |
| friction30-seed1701.json | eac12a767b2a60ac96b2c7c74afe0f6630515849b4f182fdeb0904bd169330bd |
| press90-seed1701.json | f5e4d36eabc496138149516e6992bf367f49f31b8815ad088b19b306c2673cf0 |
| press100-seed1701.json | 2ea373783cd8cafb5d05d771ec0873eb984323028f96e0e111625c8f2c075235 |

<a id="record-0245"></a>

来源：PUSH_LOAD_COMPARISON_20261001_CN.md。

## 原负载独立验收

2026-10-01 10:09:10（北京时间）保存候选选择，10:09:12启动两批；selection SHA为 `961045099fe5f9d8cd1a4e79637be9c46e7a6470867276a5a9128b72e6a5f91f`。使用同一aa/model199、100mm压入、5kg、静/动摩擦.4、12秒、目标.60m。

| 新独立种子 | 成功 | 无效手接触 | 其他安全终止 | 超时 | 未完成 |
| --- | --- | --- | --- | --- | --- |
| 2701 | 30/32 | 2 | 0 | 0 | 0 |
| 3701 | 32/32 | 0 | 0 | 0 | 0 |

**达到既定Isaac门槛（各至少30/32、无未完成回合），但不是零安全失败。** 2701的env27/22分别在9.22/9.54秒触发箱体上沿无效手接触；接触点高度约.194/.192m，箱体仅前移.0011/.0009m，未形成持续合法推压。这两次均计为失败，不是推进不足超时。62次成功均满足原合法接触历史、安全、误差<.12m、速度<.08m/s与连续停稳>=.5s条件。

验收复核脚本ac/verify_acceptance.py核对候选选择先于启动、权重和控制哈希、实际物理、32个唯一环境各一回合、成功条件与逐环境记账；结果保存在acceptance-verification.json。

| 独立报告 | SHA-256 |
| --- | --- |
| held-out-press100-seed2701.json | 1b821710ed922592d72da677f8aab9a2a7d07a46e23d039c0a4996ccedb37b4f |
| held-out-press100-seed3701.json | 770e2432c84a476e6fcab01b7026b3fd0c914f3e0d2548126811ada464c02b3b |

权重、训练参数、100mm评估契约和源码快照已保存ac/selected-candidate；训练参数中press为80mm，不能将其误当本次100mm控制配置。原有冻结包未覆盖。当前旧y录像使用u权重与.5秒接管，不代表本候选。

2701/3701已使用，未来控制变更需重新固定候选并使用其他未用种子验收。后续Isaac工作优先处理上沿初始接触，补充当前候选录像；MuJoCo/CLIMB暂停，本结果不构成实机许可。

<a id="record-0246"></a>

来源：PUSH_LOAD_COMPARISON_20261001_CN.md。

## 后续录像与接管对照

ae已录制当前100mm候选：3701/env0成功，11.40秒停稳、目标误差.07195m；2701/env27在9.22秒无效接触并重置。两段各11.68秒/1280×720/25fps；全部64终态逐值复现原报告，未新增独立验收样本。视频和index.html在仓库外ae目录，旧y录像已不代表当前效果。

af只改变普通腿部接管时间，.9/1.1秒在seed2701均31/32、零安全终止、零未完成；原env27成功，env22目标误差.0781/.0793m，停稳.42/.40秒而超时。两种都消除本批的2次上沿无效接触，但尚未跨种子验证。优先复核.9秒，当前已验收候选仍为.7秒。

| af诊断报告 | SHA-256 |
| --- | --- |
| ramp090-seed2701.json | f0114fd5b1db7e5841e240991146a3ac973ff62ea258c4b4915542dc4d23b99a |
| ramp110-seed2701.json | 6d71a1999da0f1575de4705c5648f979661b8e6fc45a7b83e9968fbbe499de9e |

<a id="record-0247"></a>

来源：TRAINING_STATUS_20260929_CN.md。

# GO2-PIPER 训练与评估记录：2026-09-29

更新日期：2026-09-29

<a id="record-0248"></a>

来源：TRAINING_STATUS_20260929_CN.md。

## 结论与适用范围

### 同日追加：PUSH 阶段归因与同任务基线

在远端 Isaac 服务器用同一 `GO2-PIPER-Box-Push-Tracking-Play`、seed `517`、
`32` 环境、`12 s` 时限和相同评估器复核冻结 PUSH `model_599.pt`：`0/32`，
32 回合均触发 `arm_body_clearance`；箱体最大终态 x 位移约 `0.107 m`。
原 Tracking `model_9.pt` 同条件也是 `0/32`，其中 29 回合触发臂身净空，
箱体最大终态 x 位移约 `0.400 m`、最小目标误差约 `0.202 m`。
原报告的 `max_forward_per_env=0.597655 m` 是**机器人底座最大前移**，
不是箱体位移；此前按“最大前推”解读有误。原 Tracking 报告
[JSON](../../../artifacts/go2-piper/push-stability-20260929-a/push-tracking-seed517.json)
SHA-256 为 `770c26f129edce49a4b282a75221b021fdaa90c6d24fb51e594a2ff03d5b9627`；
冻结基线[JSON](../../../artifacts/go2-piper/push-stability-20260929-a/push-frozen-tracking-seed517.json)
SHA-256 为 `fb33991df479b9a23eeb1ef34266bb47ca5f449babbb986fa67f95ed011c4874`。

评估器此前把 Tracking 误标为纯学习式机械臂，遗漏内置 IK 的阶段、目标和控制源码哈希。
修正后在远端隔离源码副本补采的[阶段报告](../../../artifacts/go2-piper/push-stability-20260929-a/push-tracking-stage-v2-seed517.json)
SHA-256 为 `db0876c13eb35ffba922ed66c93daf67f8e6cec85442aa2a2b2b3bd28776d54a`。
补采与旧报告的 32 个终态箱体位移、成功数和终止统计一致；全部回合在终止时
已完成 16 段安全接近。代表回合约 `7.5 s` 完成安全接近、`9.0 s` 首次合法手接触，
`9.8 s` 因净空停止，终态一只后足法向力为零。终态最近刚体中心对主要是
`link4/FR_hip`（21 回合）与 `link5/FR_hip`（8 回合）。这定位了接触前后右前腿
邻域的臂路径风险，但中心距离不等于表面净空，尚不能单凭它判断真实碰撞。

只把机械臂目标俯仰角从 `0.8` 改为 `1.0 rad` 的受控[诊断](../../../artifacts/go2-piper/push-stability-20260929-a/push-tracking-pitch1p0-seed517.json)
仍为 `0/32`：臂身净空终止 `19`、无效手接触 `14`（终止标志可并存），
箱体最大终态 x 位移约 `0.389 m`。报告 SHA-256 为
`e0983e29f1a4d1d6ca887b50c54041f34f22223360cf9744166197d4ceedae27`。
仅调目标姿态会转移失败类型，不能作为放行方案。下一轮先在真实 PD、延迟和碰撞约束下
求解可连续跟踪的手端路径，并让腿策略在接触期保持足部支撑；控制级净空、
关节跟踪与支撑检查通过后，再扩大远端训练和独立批量评估。
PUSH-LOW 仍暂停，冻结交接包未改。

### 同日追加：CLIMB 保留标准差探针与双仿真筛查

后续热启动探针发现旧训练入口会把 CLIMB 原 checkpoint 的逐动作探索标准差
约 `0.05` 静默重设为 `0.25`。训练入口现默认保留 checkpoint 值，只有显式
`--initial_std` 才覆盖；导出 actor 的初始化仍默认使用 `0.25`。新实验均在远端
`/path/to/artifacts/go2-piper/climb-stability-20260929-a/` 的隔离训练副本中运行，
本地只做源码检查与 MuJoCo 筛查，冻结交接包未修改。远端核查无遗留训练或评估进程。

同一 `GO2-PIPER-Box-Climb-Smooth-Play` 条件下，32 回合 Isaac 结果如下；两组 seed
分别为 `511`、`512`，且均无未完成回合：

| checkpoint / 设置 | seed 511 | seed 512 |
| --- | ---: | ---: |
| 冻结 `model_200.pt` | 32/32 | 31/32 |
| 原 Smooth `model_9.pt`，std 0.25 | 0/32 | 未重跑 |
| std 0.05、lr 1e-3，`model_9.pt` | 0/32 | 未评估 |
| std 0.05、lr 1e-4，`model_9.pt` | 10/32 | 11/32 |
| std 0.05、lr 1e-5，`model_9.pt` | 31/32 | 27/32 |
| std 0.05、lr 1e-5，`model_0.pt` | 32/32 | 30/32 |

最后一项仅满足 Isaac 批量门槛。checkpoint SHA-256 为
`ef52829997ee25677f3b3e432bc5e8ce3294d337fcb6f390d5b60d861bf29aa7`；
诊断导出 actor SHA-256 为
`15889d6aca77bba871f7d90fc091bd32efa846ed12b51497cc68f0cdfdbe0283`。
导出包在 `../artifacts/go2-piper/climb-stability-20260929-a/model0-smooth-diagnostic/`，
manifest 标注 `diagnostic=true` 和 MuJoCo 未通过，不是新交付版本。

在同一 MuJoCo 配置（原生碰撞、`coupled-bounds` 速度模式、1 个约束子步、
固定 0.20 m 支撑箱）下，候选 seed `500..531` 和 `600..631` 均为 `14/32`；
前一组失败为底座接触 7、臂自碰 5、姿态异常 5、超时 1，后一组分别为 5、2、9、2。
seed 500 组的 5 次臂自碰中位发生在约 `0.36 s`（范围 `0.32..1.78 s`），
应优先核对启动时的机械臂初态、首命令和碰撞状态；这尚不能判定是控制还是资产差异。
同配置冻结 actor 的 seed `500..531` 为 `16/32`，没有证据表明候选改善跨仿真表现。
三份报告分别为
[候选 seed 500](../../../artifacts/go2-piper/climb-stability-20260929-a/climb-model0-mujoco-seed500-32.json)、
[候选 seed 600](../../../artifacts/go2-piper/climb-stability-20260929-a/climb-model0-mujoco-seed600-32.json)、
[冻结基线 seed 500](../../../artifacts/go2-piper/climb-stability-20260929-a/climb-frozen-mujoco-seed500-32.json)；
其 SHA-256 依次为 `fa8ae7632e2a53ecbe91a67d1b91cb4261ef7dc7e7330a54ce5ae9b7deaf7041`、
`39b0b8ba4cd1372254e9bf0f6d94bc886246d9b6b458a6dfb21acdcab4e8d048`、
`3913723d85f26f01070839cb3e35aa28518e001398f86f9f30d1d00279f0aefb`。
逐关节遥测显示候选仍触及仿真力矩限幅，目标跳变峰值约 `1.14 rad/步`，
不能据成功率宣称动作平滑或电机安全。下一步须先归因两端失效和启动接管，
再考虑新训练；当前不得作为跨组成熟策略或实机接触许可。

### 首轮 Tracking / Smooth 探针

普通 PUSH、CLIMB 已获授权继续优化、训练，但本轮 Tracking 与 Smooth 候选均未达标，
不能替换冻结技能或用于实机接触。两项各完成 10 轮 Isaac 训练探针和一组 32 回合评估；
无新录像、无本批 MuJoCo 验收。本次核查未发现活动训练或评估进程。
PUSH-LOW 训练与实机接触继续暂停。

本记录依据服务器完成的训练日志、评估 JSON 和实际文件 SHA-256。9 月 15 日原技能
成绩、9 月 26 日诊断录像、较早的泛化探针和本轮结果属于不同证据，不能互相替代。

<a id="record-0249"></a>

来源：TRAINING_STATUS_20260929_CN.md。

## 隔离目录与原技能备份

服务器别名：`SIM_HOST`；Isaac Python：`/path/to/bin/isaac-python`。

- 本轮根目录：`/path/to/artifacts/go2-piper/smooth-tracking-20260929-a/`。
- 本轮源码工作副本：根目录下 `train/`；报告和日志：`outputs/`。
- 原技能备份：`/path/to/artifacts/go2-piper/generalize-20260929-a/original/`。
- 本地冻结训练包：[训练交接包](../../sim2real/go2-piper-low-level-training-handoff/README_CN.md)。
- 历史部署契约：[策略交接包](../../sim2real/go2-piper-low-level-policy-handoff/README_CN.md)。

以下是完整 PPO checkpoint 的哈希，不是导出 actor 的哈希。远端原技能备份与本地
训练交接包对应 checkpoint 逐项相同；原包的模型、清单和源码快照不随本轮更新。

| 原技能文件（相对备份目录） | SHA-256 |
| --- | --- |
| `push/model_599.pt` | `aaff6614b641238ab4579c11fff8329b566904163f04d5e20cc4dab6b1ec891a` |
| `climb/model_200.pt` | `5cbdb0d8523a10b7f6a4870a3385afdd8289d5d87bc93408ac5c7b404ac7b548` |

未通过验收的 checkpoint、训练日志、录像和完整诊断 JSON 留在隔离产物目录，不作为
新发布模型提交 Git。主仓库保存实验配置、工具和本记录，冻结交接包仍是历史快照。

<a id="record-0250"></a>

来源：TRAINING_STATUS_20260929_CN.md。

## 本轮候选

训练日志 `outputs/push-train.log`、`outputs/climb-train.log` 均记录
`Learning iteration 0/10` 到 `Learning iteration 9/10`，并记录 actor/critic checkpoint
初始化、探索标准差 `0.25`。两项最终候选均为 `model_9.pt`，不是原技能替代品。

| 项目 | PUSH Tracking | CLIMB Smooth |
| --- | --- | --- |
| 训练任务 | `GO2-PIPER-Box-Push-Tracking` | `GO2-PIPER-Box-Climb-Smooth` |
| 评估任务 | `GO2-PIPER-Box-Push-Tracking-Play` | `GO2-PIPER-Box-Climb-Smooth-Play` |
| 主要变更 | 接触不锁臂；末端位置跟踪权重 `2.0`、手接触权重 `1.0` | 动作变化 `-0.12`、关节加速度 `-1e-6`、关节力矩 `-4e-5`、底盘角速度 `-0.5`、姿态 `-4.0` |
| 评估 seed | `517` | `511` |
| 请求/完成/未完成回合 | `32 / 32 / 0` | `32 / 32 / 0` |
| 成功回合 | `0/32` | `0/32` |
| 终止标志 | `arm_body_clearance=29`、`base_contact=3`、`box_contact=3` | `base_contact=31`、`bad_orientation=1` |
| 最大倾角 | `0.382629 rad` | `0.861644 rad` |
| 最大关节绝对速度 | `15.666808 rad/s` | `30.100027 rad/s` |
| 最大力矩/仿真限幅比例 | `1.0` | `1.0` |
| 准备时间覆盖 | `0.0 s` | `0.0 s` |
| 报告视频字段 | `null` | `null` |

终止标志允许同回合并存，不能求和作为失败回合数。速度和倾角均为本次报告的峰值，
不代表实测电机电流、温升、饱和持续时间或全程运动平滑度。

PUSH 评估实际箱体为 `1.2 x 1.2 x 0.20 m`、`5 kg`、静/动摩擦约 `0.4`、自由箱体、
目标前推 `0.60 m`。`max_forward_per_env` 中的 `0.597655 m` 是机器人底座最大前移；
箱体最大终态 x 位移约 `0.400 m`，没有安全完成并停稳。CLIMB 使用
固定支撑，所有环境在 25 个评估控制步内已终止；当前只能确认起步失败，尚不能把原因
单独归于奖励、准备时间或接管方式。不得通过延长训练或降低安全停止阈值掩盖这些问题。

<a id="record-0251"></a>

来源：TRAINING_STATUS_20260929_CN.md。

## 产物身份

候选 checkpoint 路径均相对于本轮根目录：

- PUSH：`train/logs/rsl_rl/go2_piper_box_push_hybrid/2026-09-29_13-18-24_push_tracking_probe/model_9.pt`。
- CLIMB：`train/logs/rsl_rl/go2_piper_box_climb/2026-09-29_13-17-02_climb_smooth_probe/model_9.pt`。

| 产物 | SHA-256 |
| --- | --- |
| PUSH `model_9.pt` | `96ddf499994ced13f80be50272d5ebeb21bba2fd2244d8074ea1640ae0d9eaf3` |
| CLIMB `model_9.pt` | `f762bcf8345d7fa5a8ff7175a625e4ea128dde399644e7ac084ac36dd917a780` |
| `outputs/push-tracking-seed517.json` | `770c26f129edce49a4b282a75221b021fdaa90c6d24fb51e594a2ff03d5b9627` |
| `outputs/climb-smooth-seed511.json` | `5b3167a62b4b82e863e57592849965199b1ee6fe0121318f70f2c8a4e797e864` |

候选文件实际哈希与各自评估 JSON 的 `checkpoint_sha256` 一致。下列远端运行源码与
本次归档版本逐文件哈希一致；两份 JSON 的 `evaluation_sha256` 也与评估器一致。

| 源码 | SHA-256 |
| --- | --- |
| [评估器](../../scripts/evaluate_box_skills.py) | `9b07177657b58dbcf9d390e1bc363e27770e2b9409e15653480bd38adda595df` |
| [PIPER 箱体任务配置](../../source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/box_env_cfg.py) | `5a233d7178682df3bb8704997663135b2eafecefaa1a1785e67c672e522a108a` |
| [任务注册](../../source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/__init__.py) | `a28bc0d0916354beef0ac1239a7e7d078f0f30620bc69901d2ad236e2b40c1f5` |

控制模块及机器人资产的更多哈希由各 JSON 的 `control_sha256`、
`actual_physics.robot_asset_sha256` 保存。复用结果前必须重新匹配；不能把后续
修改后的控制器与这些报告组合成新的验收证据。

<a id="record-0252"></a>

来源：TRAINING_STATUS_20260929_CN.md。

## 后续实验与放行边界

1. PUSH 分解安全接近、就位、首次合法接触、持续推进与停止的耗时，定位净空停止前
   的手端路径、关节跟踪、底盘姿态和足部支撑，再验证受限在线跟踪与全身支撑控制。
2. CLIMB 冻结候选复现起步底座接触，核查重置/准备状态和动作接管；补齐逐关节
   目标变化、速度、加速度、力矩饱和持续时间、功率、底盘角速度与冲击统计。
3. 控制级检查通过后，再扩大独立训练、保留原 checkpoint 回归并补录来源匹配的视频。
   Isaac 与 MuJoCo 各两组独立 32 回合、每组至少 `30/32` 且无未完成回合，才满足
   仿真批量门禁；安全判据和箱体参数不得降低，单条视频不能替代批量结果。
4. 实机前仍须完成安装/执行器标定、观测与延迟核对、急停与 watchdog、分级验证。
   在电机额定参数、电流、温升未实测前，不宣称电机安全，不进入实机接触。

9 月 28 日的足地力采样、固定根来源纠正和完整 PUSH 时序详见
[历史诊断与当前优先级](#source-next-steps-cn)。它们用于解释风险，不是新策略验收。

<a id="record-0253"></a>

来源：TRAINING_STATUS_20260929_CN.md。

## 本地代码检查入口

以下命令从仓库根目录运行，使用隔离的 MuJoCo 环境；这些检查验证统计、奖励和
诊断工具，不会启动训练，也不能替代 Isaac/MuJoCo 技能评估：

```bash
OPENBLAS_NUM_THREADS=1 ../.envs/go2-arx5-nav/bin/python mujoco/check_piper_trace.py
OPENBLAS_NUM_THREADS=1 ../.envs/go2-arx5-nav/bin/python scripts/check_box_evaluation.py
OPENBLAS_NUM_THREADS=1 ../.envs/go2-arx5-nav/bin/python scripts/check_box_skill_rewards.py
OPENBLAS_NUM_THREADS=1 ../.envs/go2-arx5-nav/bin/python scripts/check_box_push_control.py
git diff --check
```

本次文档归档前实跑结果：trace `9/9`、评估统计 `3/3`、奖励 `7/7`、PUSH 控制
`18/18`，合计 `37/37`；7 个待提交 Python 文件编译通过，补丁格式和编辑器检查
通过。5 份文档的 42 个本地链接有效，3 项源码及 2 项原 checkpoint 哈希与记录
一致；足端运动学对照入口在已归档输入上复现了 9 月 28 日记录。
隔离环境未安装 Ruff/pre-commit，这两项检查未运行；本次没有重新训练或执行
Isaac/MuJoCo 批量技能验收。

<a id="record-0254"></a>

来源：TRAINING_STATUS_20260930_CN.md。

# GO2-PIPER 控制诊断记录：2026-09-30

<a id="record-0255"></a>

来源：TRAINING_STATUS_20260930_CN.md。

## 最新指示与执行阻塞

用户要求优先使普通 PUSH 在 Isaac 达标，MuJoCo 暂不推进；已明确授权将修改后的
PUSH 控制与训练源码同步到既有远程服务器的隔离目录。后续不再以源码授权缺失
为由重复请求许可。远程训练要求仍然有效。

两次 SSH 只读检查都在执行前遭遇自动审批服务 HTTP 503：CC Switch 本机代理
审批服务 返回审批模型 `gpt-5.6-luna` 在当前分组
无可用通道。这是审批基础设施故障，不是危险操作判定，也不是 SSH/服务器运行
报错。只读本机配置显示对话配置为 `gpt-6-astra`，使用同一个代理入口；同入口
不同模型的通道可用性不同。已向用户说明并请求恢复审批模型通道，没有绕过审批。

本地重新运行控制测试 `21/21`、评估测试 `4/4`，均通过；准备六文件源码 overlay、
SHA-256 清单与 `run_compare.sh`，位于
`../artifacts/go2-piper/push-isaac-priority-20260930-a/`。脚本语法检查通过，
远程对照尚未执行，训练尚未启动。脚本将核对源码和 checkpoint 哈希、拒绝覆盖
已有输出，比较相同 seed 517 的 32 回合基线与 0.10 m IK 净空投影候选。
0.08 m 原安全终止、箱体物理参数与成功判据保持不变。训练必须继承评估验证的
控制设置；当前净空开关仅在评估入口启用，不能直接把普通 Tracking 训练当作
已训练该控制器。最终固定版本以新 seed 701、1701 各 32 回合独立验收。

<a id="record-0256"></a>

来源：TRAINING_STATUS_20260930_CN.md。

## PUSH：IK 净空约束候选

9 月 29 日的 Tracking 报告把失效定位在安全接近结束后的接触阶段，最近刚体对主要为
`link4/link5` 与右前腿。新增默认关闭的 `--push-ik-clearance-minimum` 诊断参数，
仅允许在 `GO2-PIPER-Box-Push-Tracking-Play` 中使用，距离必须位于 `(0.08, 0.15] m`。

候选对安全接近完成后的机械臂关节参考进行局部线性投影，使用臂与被保护刚体的距离
梯度，把目标修正限制在现有关节软限位和逐步参考变化上限内。保持原 `0.08 m`
净空终止；拟议对照采用 `0.10 m` 候选距离，其他任务、策略、箱体参数相同。
线性距离是刚体中心距离，不是表面距离；有限迭代的残差、实际 PD 跟踪、移动腿部和
接触反力都可能导致失败，因此该候选不能当作碰撞安全保证。

新增遥测 `ik_clearance_residual`、`ik_clearance_correction`、`ik_clearance_distance`
用于区分约束不可满足、目标受到修正和实际距离变化。基于残差的保护动作尚未实现；
原安全终止继续负责停止回合。默认关闭时保持原控制行为，冻结策略包未修改。

本地控制测试 `21/21`、评估统计 `4/4` 通过，相关 Python 编译和 `git diff --check`
通过。新增测试覆盖可行投影、多距离约束、关节边界、限速导致不可满足与零梯度。
尚未验证 Isaac Jacobian 与距离线性化的动态效果，不能声称 PUSH 成功率改善。

远端目录：`/path/to/artifacts/go2-piper/push-clearance-20260930-a/`。
独立源码副本已建立，评估器已同步；两个控制模块上传被自动审批两次拒绝，
因此尚未运行候选或使用这个不完整副本启动评估。已向用户请求允许同步修改后的
`box_push_ik.py` 与 `box_push_control.py` 到既有服务器 `SIM_HOST`。

| 本地候选文件 | SHA-256 |
| --- | --- |
| `box_push_ik.py` | `867332ff496459dd71f3c0f47a0a4d8c95c23fe50c145be8e718f29d37e8aa08` |
| `box_push_control.py` | `3d3e23a55d30cdf5fd46cf3e818613e855030342171043cdb0f6d5efa82c5190` |
| `scripts/evaluate_box_skills.py` | `d159ddbde32872e044c597706ccb7a4d71c2d0e1c68046758d8d3ca625465d48` |

同步获准后，先以同一 Tracking checkpoint、seed 517 和 32 环境比较关闭/开启
候选约束。目标是减少右前腿邻域净空失效，且不增加无效手接触、底座接触或未完成回合。
若约束持续不可满足或推进消失，先处理姿态支路和全身支撑，不直接扩大 PPO 训练。

<a id="record-0257"></a>

来源：TRAINING_STATUS_20260930_CN.md。

## CLIMB：自碰撞契约检查

对现有 MuJoCo 报告的只读分析发现：候选 seed 500/600 两组中，7 次臂自碰全部是
`link2` 与 `link5`；冻结 actor 的 seed 500 组 3 次臂自碰也是该对。候选中 5 次在
`0.32..0.42 s` 内被报告终止，另外两次为 `1.78 s`、`2.34 s`。

导出的 `env.yaml` 明确记录 `enabled_self_collisions: false`，对应 Isaac 原报告
`collision_variant=null`。这是需要受控验证的配置差异，不能单凭它把任务失败
归于自碰撞，也不能据此改变碰撞几何或安全阈值。

利用服务器已有工具、选择性碰撞 USD 和 `model_0` checkpoint 完成独立对照，
输出目录为 `/path/to/artifacts/go2-piper/climb-collision-20260930-a/outputs/`。
该评估不依赖新 PUSH 控制源码。seed 511 已完成 `32/32`、无未完成回合、
`arm_contact=0`；seed 512 为 `30/32`、无未完成回合，`time_out=1`、
`base_contact=1`、`arm_contact=0`。开启选择性自碰撞并未复现 MuJoCo 的
臂自碰失效；两端评估种子并不代表相同初态。该配置满足 Isaac 两组成功数门槛，
MuJoCo 的 `14/32`、`14/32` 仍未达标。

第一组[评估报告](../../../artifacts/go2-piper/climb-collision-20260930-a/climb-model0-selfcollision-seed511.json)
SHA-256 为 `dc056f08bca4714c23fca6b3a84ae60a38cecc63e07333d88f54ecac6d0cddd0`；
checkpoint 保持 `ef52829997ee25677f3b3e432bc5e8ce3294d337fcb6f390d5b60d861bf29aa7`。
第二组[评估报告](../../../artifacts/go2-piper/climb-collision-20260930-a/climb-model0-selfcollision-seed512.json)
SHA-256 为 `239af42b0944f2931cff7056a3d6f8476c91bda04eb8de502a4354e1d50f4b45`。
这是反对“仅开启自碰即可解释失败”的证据，未消除 MuJoCo 已记录的安全风险。
下一步针对 MuJoCo 失败时的实际关节姿态核对 `link2/link5` 碰撞几何、距离及两端
碰撞过滤；采用同姿态局部检查，避免继续做无明确假设的奖励或学习率扫描。

<a id="record-0258"></a>

来源：TRAINING_STATUS_20261001_CN.md。

# PUSH Isaac 优先实验：2026-10-01

> 2026-10-07交接索引：当前CLIMB边界、结果及优先级见[CLIMB当前小组交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)。本页保留历史实验/计划，不作为当前进程或下一步指令；登台后到目标点由NAV负责。PUSH技能、MuJoCo、实机暂停。

最新结果：固定aa/model199与80mm压入，减至4kg/.4摩擦或5kg/.3摩擦均32/32，零安全终止、零超时。原5kg/.4任务改为100mm压入，三个诊断批次均32/32；预先固定候选后的独立2701/3701为 **30/32、32/32**，无未完成回合，达到既定Isaac门槛。2701仍有2次上沿无效接触，不能称为零安全失败或实机成熟策略。详见[负载与验收记录](#source-push-load-comparison-20261001-cn)。

当前优先级是普通 PUSH 在 Isaac 原12秒任务中达标，训练只在远程服务器执行；MuJoCo、CLIMB暂停新增实验。当前100mm候选已通过Isaac数量门槛；保留2次无效接触风险，尚未完成跨仿真与实机验证。

用户已明确持续授权本项目既有服务器上的同步、训练、评估、录像及下载，并要求提交到 `WM4N-Group/GO2-ARX5-MUJOCO` 的 `feature/go2-piper-sim2real` 分支。当前会话Full access已生效，无待确认授权。Git提交包含源码、检查和文档；原始权重、日志、录像保存在仓库外。

最新控制对照z已完成8组：间距减速未改善；60/70mm压入退化，不采用。普通腿部接管由.5改为.7秒、合法接触后仍.2秒，在已使用的517/701/1701为 **30/32、30/32、27/32**，三批均零安全终止。两次旧上沿误接触消失，剩余为推进不足与停稳过晚。该结果不是新独立验收。

当前远程aa微调：`/path/to/artifacts/go2-piper/push-ramptrain-20261001-aa`；run=`2026-10-01_09-36-12_ramp70_all_seed628`；训练PID3911950，监控PID3911952。seed628、512环境、200轮、std.03、固定lr1e-5，从u/model199初始化。实际env/agent配置已核验并下载。200轮训练及全部评估已完成：第100轮在517/701/1701为30/32、32/32、27/32，第199轮为 **31/32、32/32、28/32**，六批均零安全终止、回合完整。按预定规则选定model199，SHA `b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721`，已备份本地；不要重复启动该训练。

aa监控在80mm配置下因第三批低于30/32跳过验收。后续ac固定同一权重，将压入参考改为100mm，517/701/1701均32/32且零安全终止；2026-10-01 10:09（北京时间）固定权重、控制、物理配置后启动独立2701/3701，两批最终30/32、32/32，均完整且无超时。2701的env27/22在9.22/9.54秒因上沿无效手接触终止，均未计入成功。两个种子已使用；后续若用于修正，不能再次称为未见验收。完整校验见ac/acceptance-verification.json。

新失败历史记录已通过Isaac接入：z关闭分支与u原1701报告共有终态字段逐值一致，每个失败回合保存128步。ab离线FK复核1152个状态，位置重建误差最大2.91微米；六个推进不足回合参考对应手端约14cm、实际约6cm，提示继续检查受载跟踪。FK本身不是动力学或安全证明。

最新录像ae已完成：aa/model199、100mm压入、.7秒普通接管，3701/env0在11.40秒成功，2701/env27在9.22秒上沿无效接触后自动重置。两组全部64终态与ac原验收报告逐值一致，视频各11.68秒、1280×720/25fps；复现不新增独立样本。本地入口`../artifacts/go2-piper/push-review-20261001-ae/index.html`。后续af将普通接管改为.9/1.1秒，seed2701均31/32、零安全终止；env22到位但仅停稳.42/.40秒。优先交叉检查.9秒，尚未替换已验收的.7秒候选。

此前y录像使用u/model199与.5秒接管，不代表当前候选。

源码执行方式见[当前PUSH运行说明](#source-push-isaac-runbook-cn)，细节见[本日记录](#source-training-status-20261001-cn)。产物在仓库外 `../artifacts/go2-piper/` 下的z、aa、ab、ac、ad、ae、af、y对应目录，远程路径和哈希见各manifest；GitHub单独克隆不包含这些二进制产物。

以下保留按阶段记录的原始实验历史，其中进行中、授权阻塞和未使用种子的描述仅表示当时状态。

<a id="record-0259"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 执行恢复

用户完成审批模型配置后，实际审批请求已使用 `gpt-6-luna` 并正常返回；
SSH 只读检查成功，启动前两张 GPU 均空闲。整目录上传曾被要求核验载荷与目标，
随后逐文件核验哈希及远端目录，两个 PUSH 控制模块和训练入口均已成功同步。
此前的旧审批模型 HTTP 503 阻塞已经解除。

<a id="record-0260"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 净空控制对照

远端源码：`/path/to/artifacts/go2-piper/push-clearance-20260930-a/train`。
结果目录：`/path/to/artifacts/go2-piper/push-isaac-20261001-a/outputs`。
本地报告：[产物目录](../../../artifacts/go2-piper/push-isaac-20261001-a/)。

三组均为 Tracking `model_9.pt`、seed 517、32 环境、每环境一个回合、12 s 时限。
checkpoint SHA-256：`96ddf499994ced13f80be50272d5ebeb21bba2fd2244d8074ea1640ae0d9eaf3`。
名义箱体 1.2×1.2×0.20 m、5 kg、摩擦 0.4、前推目标 0.60 m；
原 0.08 m 臂身刚体中心距离终止以及合法手接触、停稳判据未改。

| IK 净空参考 | 成功 | 未完成 | 臂身净空 | 无效手接触 | 底座接触 | 非手部碰箱 | 姿态异常 | 超时 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 关闭 | 0/32 | 0 | 29 | 0 | 3 | 3 | 0 | 0 | 0.1915 m |
| 0.10 m | 0/32 | 0 | 6 | 16 | 7 | 6 | 0 | 3 | 0.3691 m |
| 0.12 m | 0/32 | 0 | 4 | 15 | 5 | 2 | 4 | 4 | 0.5606 m |

终止标志非互斥。三组均未达标；位移不能替代安全完成与停稳。
0.10 m 修正减少了原净空终止，但新增大量无效手接触；0.12 m 仍未成功，
且出现姿态异常。参考距离不等于实际距离，线性投影不是碰撞安全证明。

<a id="record-0261"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 控制适应训练

新的独立源码副本：`/path/to/artifacts/go2-piper/push-isaac-20261001-a/train`。
从上述 Tracking checkpoint 初始化，使用 0.10 m IK 净空参考、512 环境、
seed 619、探索 std 0.05、固定学习率 1e-4，请求 100 迭代、每 25 迭代保存。
保持原奖励与安全判据，先检验腿部策略对修正控制器的适应。

首次启动在 Hydra 配置载入阶段失败：默认 `None` 的字段不能通过 Hydra
覆盖为浮点数，未训练。新增 `--push-ik-clearance-minimum` 训练 CLI 参数，
仅允许普通 PIPER Tracking，范围 `(0.08, 0.15] m`，在配置载入后赋值；
同一配置字段会写入训练 `env.yaml`。修正后训练已完成全部 100 迭代，
实际 run 为 `logs/rsl_rl/go2_piper_box_push_hybrid/2026-10-01_00-09-42_push_clearance100mm_std005_lr1e4/`，
日志为 `outputs/train-clearance100mm-v2.log`，最终保存 `model_99.pt`。
落盘 `env.yaml` 已核对 `episode_length_s=12.0` 和 `push_ik_clearance_minimum=0.1`。

中间 `model_25.pt` 的独立 seed 517 评估：`0/32`、无未完成回合，
`arm_body_clearance=23`、`invalid_hand_contact=9`，其他终止项为零；
平均箱体 x 位移 0.3192 m。底座接触虽消失，净空失败回升，尚无成功率改善。
env0 末段速度命令 x 为零，底座仍以约 0.48 m/s 前移并下沉；
现有 Tracking 配置将高度和转向跟踪奖励设为零，需要针对该失效检查控制适应。
最终 `model_99.pt` 的 seed 517 评估同样 `0/32`、无未完成回合：
净空 21、无效手接触 16、姿态异常 1，标志重叠。该训练未达标，不提升为交付候选。

<a id="record-0262"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 姿态训练与稳定腿部对照

第二轮仍从原 Tracking model9 初始化，std 0.05、lr 1e-4、512 环境、
seed 620、100 迭代已完成。仅恢复高度跟踪权重 1.0、转向跟踪 1.5，
关闭箱体质量/材料随机化，在名义 5 kg、0.4 摩擦条件训练；安全判据不变。
run：`2026-10-01_00-20-43_push_nominal_support_std005_lr1e4`。
最终 model99 评估为 `0/32`：25 超时、5 净空、1 非手部碰箱、1 无效手接触；
平均箱体位移仅 0.0253 m。增加稳定性奖励后主要学会停留，未完成推进。

另将冻结 NAV actor 的 210 维观测前缀和前 12 个腿部输出保留，额外 16 个
箱体观测权重置零，生成仅用于诊断的 226→12 actor。129 个输入输出与源 NAV
腿部输出一致；源哈希 `72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8`，
诊断 actor 哈希 `e8b705bd78aeb96af2616d019e9e24c30724495e04775be29c4551e68c03a226`。
没有改动冻结策略。

在相同 Tracking IK、0.10 m 净空参考、seed 517、12 s 时限下：

| 对照 | 成功 | 超时 | 无效手接触 | 净空/底座终止 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- |
| NAV 腿部 + 原 20 mm 压入参考 | 0/32 | 31 | 1 | 均为 0 | 0.0113 m |
| NAV 腿部 + 40 mm 压入参考 | 0/32 | 31 | 1 | 均为 0 | 0.0296 m |

40 mm 对照末段肩部关节达到力矩限幅，env0 有效前向推力约 7 N；
继续增大位置参考不能视为推力控制方案。该结果说明稳定腿部策略有助于避免
底座/净空失败，但尚未形成有效连续推箱。

原 Tracking model9、0.10 m 净空参考下仅抬高手端目标 20 mm 的对照仍为
0/32：5 超时、3 底座、2 非手部碰箱、17 无效手接触、8 净空。未采用。
无效手接触离线拆分表明既有下边缘越界，也有接触点距手端超过 0.07 m；
不得扩大合法接触区域来消除这些失败。

<a id="record-0263"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 接触姿态力矩余量诊断

本地仅以来源匹配的 Isaac USD 导出关节/质量配置进行 FK 和静力学计算，
未运行 MuJoCo 仿真。产物 `analyze_arm_pose.py`、`arm-static-pose-probe.json`。
固定直立底座、假设水平力作用于 end_effector 原点时，0.8 rad 姿态的理想
静态推力上限约 15.6–18.2 N（依身体间距而异），接近或低于名义静摩擦
估计 `5×9.81×0.4=19.62 N`。0.6 rad 部分姿态约 19.8–20.1 N。
这是局部 IK 解上的估计，不是全局力可达性证明；实际接触点力矩、PD、身体
姿态、碰撞和动态效应都未计入，不能据此宣称任务不可能或已解决。

NAV 腿部 + 0.6 rad 手端姿态的 20 s 诊断已完成，仍为 `0/32`，无未完成：
22 超时、10 无效手接触，净空/底座/非手部碰箱/姿态异常均为零。
平均箱体 x 位移 0.05899 m，最大 0.21192 m。延长窗口与改变俯仰角未解决推进。
报告为 `nav-legs-pitch06-duration20-seed517.json`。此试验时限不同于原 12 s，
不作为原任务验收证据。

<a id="record-0264"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 接触状态切换修正

上述 20 s 轨迹 env0 在第 500 步后记录 40 个样本，其中 22 个合法手接触，
但 `approach_completed` 全为假，另 18 个样本 x 命令为负。几何接近判定要求
手端仍在箱面外 30 mm；当手端已碰到合法推面而漏过接近判定时，控制器仍追踪
箱面外的目标，底盘又随瞬时接触力消失切回后退。此计数为稀疏且接触偏采样的
轨迹统计，不是全回合时间比例。

在新副本 `/path/to/artifacts/go2-piper/push-contact-20261001-b/train` 中测试
默认关闭的 `push_contact_memory_s`：已完成 SAFE_APPROACH、手端靠近箱面且
当前合法接触时允许确认接近完成；推进命令可保持该接触最多 0.10 s，离面、
高度/横向偏离或到达目标时立即取消。原接触分类、失败终止、净空、力矩和
停稳判据未改。此状态仅供控制使用，不用于累计成功接触时间。

控制检查 22 项、评估检查 4 项通过，编译与 diff 检查通过。逐文件同步了
evaluator、PIPER config、box_push、box_push_ik、box_push_control，冻结包不变。
两组对照均为 NAV 诊断 actor、seed 517、32 回合、0.10 m 净空参考，均已完成：

| 姿态 / 时限 | 成功 | 超时 | 无效接触 | 净空 | 平均 / 最大箱体 x 位移 |
| --- | --- | --- | --- | --- | --- |
| 0.8 rad / 12 s | 0/32 | 31 | 1 | 0 | 0.01140 / 0.04353 m |
| 0.6 rad / 20 s | 0/32 | 14 | 18 | 0 | 0.12050 / 0.39828 m |
| 0.6 rad、高度 +30 mm / 12 s | 0/32 | 3 | 23 | 6 | 0.00181 / 0.02382 m |

均无未完成回合，其他终止项为零。0.6 rad / 20 s 的接近状态能确认，
推进增加但上边缘无效接触增多；不少失败时 joint2 已到硬上限约 3.14 rad。
抬高目标虽在离线静态计算中减少肩关节限制，真实 PD 运行却在腿部接管时
带来明显手端高度瞬变，未采用为成熟控制器。

<a id="record-0265"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 腿部渐进接管

新副本 `/path/to/artifacts/go2-piper/push-release-20261001-c/train` 保留前述
接触修正，增加默认关闭的 `push_leg_release_ramp_s`。打开时在原就位条件
允许腿部接管后，逐步将输出从保持姿态的零偏置过渡到策略动作；测试 0.5 s。
没有更改关节力矩/速度限幅、SAFE_APPROACH 路点或任务安全/成功判据。

两组均完成且无未完成回合。0.6 rad、高度 +30 mm / 12 s 为 `0/32`：
22 超时、10 无效接触、净空及其他项为零，平均 / 最大箱体 x 位移
0.04029 / 0.15075 m。相对无渐进接管时 23 无效接触、6 净空明显减少，
但没有任务成功。

0.6 rad、原高度 / 20 s 为 `0/32`：8 超时、24 无效接触，其他项为零；
平均 / 最大箱体 x 位移 0.13948 / 0.36195 m。原高度方案仍存在肩关节
到限后手端上漂，不作为交付候选。

<a id="record-0266"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 从 NAV 初始化的负载适应训练（已提前停止）

GPU 0 实际运行至日志 iteration 131/400 后被主动中断，保存 0/50/100 检查点。
原因是任务评估与训练失败组成均显示退化，未继续消耗剩余迭代。run：
`push-release-20261001-c/train/logs/rsl_rl/go2_piper_box_push_hybrid/2026-10-01_00-58-24_nav_contact_ramp_pitch06_height30/`。
日志：该实验 `outputs/train-nav-contact-ramp.log`。

- 来源为上述 SHA 已核验的 NAV 腿部诊断 actor（226→12），不再从失败的
  Tracking model9 初始化；critic 新建。seed 621，512 环境，400 迭代，
  std 0.05、固定 lr 1e-4，每 50 迭代保存，最长运行限制 3600 s。
- 控制器：净空 0.10 m、接触保持 0.10 s、腿部渐进接管 0.5 s、俯仰 0.6 rad、
  手端高度偏置 +0.03 m；对应配置字段均写入 `params/env.yaml`。
- 固定名义箱体 5 kg / 摩擦 0.4；关闭两项箱体随机化；box_progress 权重 16，
  高度跟踪 0.25（目标 0.28 m、std 0.05）、转向跟踪 0.25，其余沿用 Tracking。
  避免上一轮强站立奖励主导，同时从稳定 NAV 腿部开始学习负载跟进。
- 训练窗口设为 20 s，增加接触后的探索时间；最终普通 PUSH 验收仍用原 12 s。
  成功、碰撞、接触、净空及力矩约束均未修改。

这轮依据是渐进接管对照中手端可产生约 20 N 推力，但底盘在 0.25 m/s 前进
命令下仍停留/后退，导致身体到箱面的间距从约 0.58 m 增至 0.65 m，随后
肩部/腕部饱和。需要训练腿部在推箱反作用力下向前跟进，不能用继续增大压入
参考来补偿。本轮固定 lr 1e-4 未改善该问题。

原 12 s、seed 517 的检查点评估（每组 32 回合，无未完成）：

| 检查点 | 成功 | 超时 | 无效接触 | 净空 | 低姿态 | 底座 | 姿态异常 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| model50 | 0/32 | 21 | 10 | 0 | 0 | 0 | 1 | 0.02082 m |
| model100 | 0/32 | 1 | 1 | 7 | 20 | 2 | 1 | 0.04498 m |

NAV 原 actor 的低负载诊断（1 kg、20 s、同控制器）同样 0/32，全部 32 个
回合为无效手接触，平均位移 0.15721 m。它不是验收结果，也没有形成可以直接
使用的训练课程。将 NAV 观测中的手端命令改为中性参考也未改善：5 kg / 20 s
为 0/32（30 无效接触、2 超时），1 kg / 20 s 为 0/32（32 无效接触）。不采用。

<a id="record-0267"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 底盘先就位的阶段控制（未通过）

之前接触建立时身体距箱面常达 0.58–0.65 m，低位手端目标已经很难在关节
范围和推力条件内实现；低负载下也会因追逐远处箱面而上漂越界。
新副本 `/path/to/artifacts/go2-piper/push-drive-20261001-d/train` 加入默认关闭的
`push_body_first`：保留原 SAFE_APPROACH 全部路点和静稳判定，完成后保持末段
臂姿，让底盘先接近 0.46 m 间距并通过原 `preapproach_state` 的身体稳定检查，
然后才释放在线低位 IK。原 0.43 m 最小间距和 0.08 m 净空终止不变。

另有默认 1.0 的 `push_forward_command_gain`，仅放大正向速度命令，可选最大
2.0（原 0.25 m/s 命令上限对应 0.5 m/s）；后退、最小间距与到达目标停止逻辑
不变，原关节速度/力矩限幅不变。本地 23 项控制检查通过。

远端两组均为 NAV actor、名义 5 kg / 摩擦 0.4、0.6 rad、高度 +30 mm、
接触保持 0.1 s、渐进接管 0.5 s、净空 0.10 m、seed 517、32 回合、20 s
诊断窗口，比较前进增益 1 和 2，均完成且为 0/32，无未完成回合。
两组底座接触均 32 次，非手部碰箱分别 32/31 次；其他项为零，平均箱体 x
位移约 0.00280 / 0.00254 m。env0 原增益组在命令 0.15 m/s 时底盘已达到
约 0.34–0.42 m/s，越过最小间距后继续靠近箱体，故该阶段方案不采用。

<a id="record-0268"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 底盘速度反馈

新副本 `/path/to/artifacts/go2-piper/push-feedback-20261001-e/train` 加入默认关闭的
`push_velocity_feedback_gain` 与 `push_velocity_integral_gain`。控制器将名义
任务速度与实测水平底盘速度比较，生成有界的腿部 actor 命令；x 限制为
[-0.5, 0.5] m/s、y 为 [-0.2, 0.2] m/s，积分状态限制为 ±0.4，保持/重置
阶段清零。原最小间距以内禁止正向命令；目标阶段名义速度仍为零，允许反向
命令制动。原碰撞/接触/停稳/关节力矩与速度阈值不变。这不是实机速度估计器
或制动能力的验证，当前只在 Isaac 使用仿真状态做控制诊断。

NAV actor 加底盘先就位的 20 s 诊断仍未通过：P=2 时 0/32（7 超时、22
底座/非手部碰箱、3 无效接触），P=2/I=2 时 0/32（19 底座/非手部碰箱、
13 无效接触）。均无未完成回合，其他项为零，不采用该组合。

回到原 Tracking model9、原 0.8 rad / 零高度偏置、不启用底盘先就位，
净空 0.10 m、接触保持 0.1 s、腿部渐进接管 0.5 s、原 12 s、seed 517：

| 反馈 | 成功 | 超时 | 底座 | 非手部碰箱 | 无效接触 | 净空 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P=2 | 0/32 | 24 | 1 | 1 | 5 | 2 | 0.13415 m |
| P=2 / I=2 | 0/32 | 26 | 1 | 1 | 4 | 1 | 0.10628 m |

均无未完成回合，其他终止项为零。安全终止减少，但推进未达任务要求，
不能以超时增加视为成功。后续 20 s 的 P=2/I=2 仍为 0/32：23 超时、
2 底座、2 姿态、2 非手部碰箱、4 无效接触、1 净空，平均位移 0.10847 m。
0.6 rad / 高度 +30 mm 对照也为 0/32：7 超时、11 底座、9 姿态、
10 非手部碰箱、1 无效接触、4 净空，平均位移 0.21872 m；均未采用。

最终候选须固定 checkpoint、源码、控制器和物理配置，以未用于调参的 seed
701、1701 各 32 回合评估，每组至少 30 成功、无未完成回合。此阶段只证明
Isaac 能力，不构成 MuJoCo 或实机放行。

<a id="record-0269"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## 原 12 s 首次成功与保守微调

保持 NAV 腿部诊断 actor，关闭 body-first 与 P/PI 反馈，仅采用正向命令
增益 2.0，搭配俯仰 0.6 rad、高度 +0.03 m、净空参考 0.10 m、接触保持
0.10 s、腿部渐进接管 0.5 s。名义箱体与原安全、停稳、力矩判据不变。

| 时限 | 成功 | 超时 | 无效手接触 | 其余安全终止 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- |
| 原 12 s | 3/32 | 25 | 4 | 均为 0 | 0.168607 m |
| 诊断 20 s | 5/32 | 22 | 5 | 均为 0 | 0.171369 m |

两组均为 seed 517、无未完成回合。12 s 最大终态位移 0.535576 m；
成功计数来自原停稳/容差条件，不能将平均或最大位移替代成功率。
报告位于 `../artifacts/go2-piper/push-feedback-20261001-e/`，文件名为
`nav-gain2-pitch06-height30-duration12-seed517.json`（及远端 duration20 报告）。

本轮训练 run：
`/path/to/artifacts/go2-piper/push-feedback-20261001-e/train/logs/rsl_rl/go2_piper_box_push_hybrid/2026-10-01_01-44-49_nav_gain2_conservative_lr1e5/`。
训练日志 `outputs/train-nav-gain2-conservative.log`，实际 Python PID 3880351。
从 NAV 诊断 actor 初始化、critic 新建；seed 622、512 环境、600 迭代、
std 0.05、固定 lr 1e-5（此前失败训练的十分之一），每 50 迭代保存。
原 12 s 时限，固定名义箱体；box_progress 权重 16、高度跟踪 0.25
（目标 0.28 m、std 0.05）、转向跟踪 0.25。落盘配置已核验上述控制参数。

有限评估流程 `monitor_training.py` 已同步并启动，SHA-256 为
`47a8c427a504a1111ca51098d034d2b610814443bc743befc0484fbe6ad9a835`。
GPU0 训练，GPU1 依次评估 model50/100/200/400/599，seed 517、原 12 s、
每次完整 32 回合。状态与报告哈希写入 `outputs/auto-evaluation-status.json`。
连续两个检查点零成功且安全失败回合数至少 16 时，对核验身份的本次训练
发送 SIGINT；评估流程故障同样停止该训练，避免未经检查继续训练。
调参结果至少 30/32 才对固定候选使用保留种子 701、1701；当前尚未使用。
本轮尚未通过 Isaac 门禁，也没有生成与此候选匹配的新录像或部署导出。


保守微调早期检查点（seed 517、原 12 s、完整 32 回合）：

| 检查点 | 成功 | 超时 | 无效手接触 | 其他安全终止 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- |
| model50 | 0/32 | 24 | 8 | 均为 0 | 0.168323 m |
| model100 | 4/32 | 23 | 5 | 均为 0 | 0.170451 m |

model100 SHA-256：`6744fd09f6709ae1427d4e10e874d4b3077e89d3e2ddcabf0afbda06a7199a80`。
早期成功率有波动，尚无稳定提升证据；继续检查后续候选，不消耗保留种子。
终态分析发现很多停滞回合在底盘距箱面约 0.43 m 后停止，手接触力约 5–13 N。
正在对原 NAV gain2 候选做压入参考 20→40 mm 的单变量诊断；不修改本次
训练或安全边界。首次命令误用 checkpoint 加载 TorchScript actor，在推理前失败；
已改为 `--actor-policy` 重试，失败日志保留为 `nav-gain2-press40-duration12-seed517.log`。


40 mm 压入参考对照已完成：原 12 s、seed 517 为 **9/32**，6 超时、
17 无效手接触，其余安全终止均为零，无未完成回合；平均箱体 x 位移
0.385728 m。比 20 mm 的 3/32 推进更充分，但接触风险增加，不能交付。
绝大多数新增接触失败在箱体上边缘：接触点世界高度约 0.190–0.196 m，
底盘落后箱面约 0.59–0.70 m，手端追逐远处目标时上漂。

新的隔离目录 `push-reach-20261001-f` 加入默认关闭的
`push_target_maximum_reach`。它只在底盘 yaw 坐标系限制手端目标的前向位置，
保留目标高度/横向坐标、原 SAFE_APPROACH 路点、原 IK 净空与关节速率边界；
原身体最小间距、合法接触和成功判据不变。评估了 0.54 m 限制与 40 mm
压入参考组合，结果如下。25 项控制检查、编译检查及 diff 检查通过；远端四个改动文件
与本地 SHA 一致。此改动仅在 f，同步未覆盖正在训练/评估的 e。
保守微调 model200 的独立评估为 3/32、7 回合安全失败，仍继续至后续检查点。


前伸限制 0.54 m 对照已完成：0/32，30 超时、2 无效手接触，其他安全
终止为零，平均箱体 x 位移 0.028440 m；均完整回合。它抑制了接触上漂，
但同样阻止了持续推进，因此不采用，保持默认关闭。
以实际成功 9/32 的 40 mm 压入参考候选追加一轮有限短微调：远端 e 的
同一源码、GPU1、seed 623、200 迭代、512 环境、NAV 诊断 actor 初始化，
固定 lr 1e-5、std 0.05，其余控制/奖励/名义物理配置与 seed 622 一致。
run_name 为 `nav_gain2_press40_lr1e5`，日志 `outputs/train-nav-gain2-press40.log`。
这轮唯一控制变化是压入参考 0.04 m；前伸限制关闭。每 50 轮保存检查点，
以原 12 s、seed 517 的独立评估检验负载跟进是否改善，不能只看训练奖励。


后续检查点与中间参考值（均调参 seed 517、原 12 s、完整 32 回合）：

| 候选 | 成功 | 超时 | 无效手接触 | 其余安全终止 | 平均箱体 x 位移 |
| --- | --- | --- | --- | --- | --- |
| NAV，30 mm 压入参考 | 6/32 | 17 | 9 | 均为 0 | 0.264034 m |
| 20 mm 微调 model200 | 3/32 | 23 | 7 | 均为 0 | 0.194573 m |
| 20 mm 微调 model400 | 6/32 | 23 | 3 | 均为 0 | 0.178463 m |
| 40 mm 微调 model50 | 9/32 | 7 | 16 | 均为 0 | 0.387477 m |
| 40 mm 微调 model100 | 7/32 | 8 | 18 | 均为 0 | 0.378100 m |

20 mm 第 400 轮出现成功率提升并减少安全失败，因此继续该轮至终点；
40 mm 微调未形成明确提升，继续有限 200 轮后比较最终结果，不扩大训练。
短微调 run 为 `2026-10-01_02-08-47_nav_gain2_press40_lr1e5`，PID 3882463。
监控 `monitor_press40.py` SHA 为
`79d1402c50a9123a3a1c147aef934dd1b24fc66e75eb02b169956bcfa1a58781`；
评估 model50/100/199，使用 GPU0，状态为 `outputs/auto-evaluation-press40-status.json`。
该监控不会自行消耗保留种子，以免两个分支重复使用验收集。

实际训练环境 YAML 已取回 `training-configs/seed622-env.yaml` 和
`seed623-env.yaml`，除种子/日志目录外仅压入参考不同；e 中四个控制/评估源码
已取回 `source-snapshot/`，与早先同步 SHA 一致，避免与 f 本地诊断代码混用。

`render_selected.py` 已在远端启动有限录像流程，等待两个检查点评估流程结束，
按调参成功数、再按安全失败数选择候选，记录 env0 并重新生成完整 32 回合报告。
SHA：`2010fd9037359b5411d89ecde274f921a8188ab9b79c4a23876fd55942dfc5d6`。
输出 `outputs/selected-video-status.json`、`selected-video-evaluation.json` 和
`selected-push-diagnostic-env0.mp4`。尚未生成前不得称有本轮新录像；即使有录像，
也只代表被标明的单个环境，不能替代完整验收。


40 mm 短微调完成全部 200 迭代，最终 model199 在原 12 s / seed 517 为
7/32、17 回合安全失败，未超过 model50 的 9/32；不延长该分支。
短微调有限评估状态为 finished，保留种子仍未使用。

训练效率只读核查：`BoxPushLegAction` 在 SAFE_APPROACH 期间将策略腿部动作
置零，但远端 rsl_rl PPO 的 surrogate/entropy loss 对全部 rollout 样本取均值，
未按动作实际生效阶段筛选样本。安全接近约占 env0 的前 7.5 s，因此存在大量
无腿部控制作用的样本参与策略更新。尚未验证这是否造成策略退化，不能直接
归因为 PPO bug；后续可在独立实验中验证有效动作掩码，保留完整物理接近过程
与原 12 s 验收，不能通过跳过安全接近来提高成功率。


两轮训练均已结束：seed 622 完成全部 600 迭代，seed 623 完成全部 200 迭代。
原配置最终 model599 的评估正在进行，有限录像流程随后选择候选；本轮不追加训练。


原配置最终 model599 完成原 12 s / seed 517 评估：1/32，27 超时、2 无效
手接触、2 净空，其他终止项零；无未完成回合，平均位移 0.084776 m。
因此保留 model400 的 6/32 作为该分支最好结果，不采用最终 checkpoint。
两轮训练 PID 3880351 / 3882463 已确认退出，两个评估流程均 finished。

本轮选定录像/复核候选为 40 mm 分支 model50（9/32，16 无效接触）。
该检查点已取回 `selected-candidate/model_50.pt`，SHA 与完整报告一致：
`16350cc853f001beb62964091aab1e4ceebb78309e5a3c699ace6b59cc3708ea`。
两轮训练都未达到 30/32，不消耗保留种子，不替换冻结策略，不追加同配置训练。


本轮录像与匹配报告已完成并取回：录制时仍为 9/32、7 超时、16 无效接触，
其余安全终止零、无未完成回合。env0 在 10.7 s 触发无效手接触，随后自动
重置；该失败示例用于检查动作，不能替代验收。视频 12 s、1280×720、25 fps，
抽查了 8.0 / 10.4 s 画面，机器人与箱体可见；视频 SHA 为
`406a1a2577dd39e33ffd69e2587a3d79396d2b4f2deef77f123b682f54d9ce64`。
全部有限流程已完成，当前无活动 PPO 训练；本轮仍未达标。简报与录像见
[RESULTS_CN.md](../../../artifacts/go2-piper/push-feedback-20261001-e/RESULTS_CN.md)。

<a id="record-0270"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## g：有效动作采样的受控对照（进行中）

远端 `push-sampling-20261001-g` 从 e/train 复制，不包含 f 的前伸限制。
从 e/press40 model50（SHA `16350cc853f001beb62964091aab1e4ceebb78309e5a3c699ace6b59cc3708ea`）
初始化 actor 和 critic，两组同 seed 624、512 环境、150 迭代、std 0.05、固定 lr 1e-5，
press40 和 e 的控制/奖励/名义物理保持一致。run：

- `2026-10-01_02-52-30_press40_sampling_all_seed624`，GPU0、PID 3886001。
- `2026-10-01_02-52-30_press40_sampling_active_seed624`，GPU1、PID 3886120。

新增默认关闭 `--push-action-sampling`。all 记录动作是否生效，训练批次不变；
active 只对腿部动作真正生效的样本训练 actor、critic 与 entropy，重新在选中
样本上归一化优势。完整物理接近、完整轨迹 GAE 保留；空批次不更新 Adam。
此为待验证假设，不将原 PPO 宣称为 bug。首次启动在保存元数据时因目录缺失
退出，尚无训练更新；增加 mkdir 后重新启动，原失败日志保留。

5 项本地采样检查通过；真实 rsl_rl RolloutStorage/TensorDict 的 6 样本索引
烟雾检查通过。两组已观测到第 48 轮，活动样本约 19–22%，更新正常。
有限监控脚本 SHA `055ab0e76e0263a3fc80b40bb9c238f6f5985a7eb377ab5acb30075acad73a40`，
分别评估 model50/100/149；调参 seed 517、32 回合、原 12 s，
连续两检查点零成功且至少 16 安全失败则停止对应训练，流水线异常同样停止。
保留 seed 701、1701 尚未使用；尚无 g 成功率结论。
本地源码哈希、run 和状态见 `../artifacts/go2-piper/push-sampling-20261001-g/manifest.json`。


g/model50 首个评估完成：all **9/32、16 安全失败**，active **8/32、17 安全失败**；
均为完整 32 回合，尚无收益证据。实际 env.yaml 除 log_dir、agent.yaml 除 run_name
外一致，已取回本地 `push-sampling-20261001-g/training-configs/`。

<a id="record-0271"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## h：IK 姿态残差权重诊断（进行中）

e/press40 model50 的 16 个无效接触终态，手端平均高于目标约 0.0606 m。
Isaac 原 pose DLS 将米与弧度残差直接拼接；增加默认 1.0 的
`push_ik_orientation_weight`，诊断 0.5 和 0.25 的旋转残差比例。
它同时缩放旋转误差与 Jacobian 旋转行，再作 lambda=0.1 的 DLS，
使求解更偏向位置跟踪；原姿态目标不变，默认 1.0 直接走原求解器分支。
不更改 SAFE_APPROACH、限位/限速/力矩、净空投影或合法接触/停稳门禁。

远端 `push-poseweight-20261001-h` 从 e/train 复制，显式更新评估、控制 helper、
IK 与 cfg 四文件；源码 SHA 已逐一核验。包含本地 f 的可选前伸限制但关闭。
27 项控制检查通过，包括与增广最小二乘解的数值对照、冲突任务解析解；
编译与 diff 检查通过。同一 e/press40 model50、原 12 s、seed 517、32 回合、
名义物理与 e 控制参数，GPU0 跑 0.5，GPU1 跑 0.25。未额外训练；结果待定。
本地清单 `../artifacts/go2-piper/push-poseweight-20261001-h/manifest.json`。


g 已完成全部150轮，原采样 model50/100/149=9/6/8成功，活动采样=8/6/5成功；
最终分别18/21次无效手接触，其他安全项零，所有评估无未完成回合。
两个监控 finished，PPO PID已核验退出。不采用活动采样，不延长本配置。
h 已完成：权重0.5=2成功、6超时、24无效接触；权重0.25=7成功、8超时、
17无效接触，其余安全项零、无未完成。不采用。原权重默认1.0。

<a id="record-0272"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## i：关节限位内 IK 求解对照（进行中）

原 IK 先求无约束关节增量，再逐关节裁剪；e及h失败轨迹均有肩关节 joint2
到上限3.14rad后手端上漂。增加默认关闭 `push_ik_joint_limit_solve`：
以裁剪后的 DLS 为初值，在原关节界内做32次投影下降，目标为带lambda=.1
正则的线性化位姿误差，步长采用Hessian的Frobenius上界。每次迭代不增加
该局部目标；它不是全局可达性或碰撞安全证明。仍保留原参考变化率限制
和后续净空投影，原SAFE_APPROACH与安全/成功阈值不变。

29项控制检查通过，包括饱和关节解析例、相对裁剪解的目标下降和边界保持，
编译与diff检查通过。远端 `push-boundedik-20261001-i` 从h复制，四个
显式改动文件SHA与本地一致。同一 e/press40 model50、权重1.0、原12s、
调参seed517、32回合，GPU0复核原求解器，GPU1测试限位内求解器；结果待定。


i 首轮完成：原求解器复现9/32、7超时、16无效接触，平均箱体推进0.387477m；
限位内求解为0/32、32超时，所有安全终止零，平均推进0.089088m。
末端从上漂转为偏低，身体跟进至最小间距附近；终态法向力多为4–16N，
低于名义静摩擦估计19.62N，肩/腕关节终态仍有部分力矩余量。
追加同源同策略的压入参考0.06/0.08m诊断，保持限位内求解、姿态权重1，
原12s/seed517/32回合、物理和安全约束不变。GPU0/1分别运行，尚无结果。


i 压入参考对照有改善：60mm **8/32、零安全失败**、平均推进0.399872m；
80mm **16/32、零安全失败**、平均推进0.504347m。均无未完成回合。
60mm的time_out原始标志25次，与成功有1次重叠；成功按评估器正式成功数8计，
不能将标志相加当作回合数。80mm的16个超时中14个终态已进目标误差0.12m，
主要欠缺停稳/保持时长；2个明显推进不足。继续同源100/120mm参考对照，
不改原12秒或停稳门槛；日志/报告 `bounded-press{100,120}-seed517`，GPU0/1。


i 的100/120mm分别8/6成功、5/8无效接触，其余安全终止零、无未完成。
平均推进0.511309/0.507215m。成功与超时标志有重叠，不能相加；
不继续增大压入参考。选择80mm（16/32、零安全失败）进行负载/停稳适应训练。

<a id="record-0273"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## j：限位内IK/press80 有限微调（进行中）

远端 `push-boundedtrain-20261001-j` 从i/train复制，控制源码未修改。
两组同seed625、512环境、200轮、std.05、原12s、名义箱体，从e/press40
model50初始化actor+critic；原PPO全部采样，不启用g的筛选。
- GPU0，lr1e-5：`2026-10-01_03-25-35_bounded_press80_lr1e5_seed625`，PID3890772。
- GPU1，lr3e-5：`2026-10-01_03-25-37_bounded_press80_lr3e5_seed625`，PID3890925。
实际env YAML除日志目录一致，agent YAML仅学习率和run_name不同。
已核对限位内求解为true、press.08、12s；reward与此前e训练配置一致。
有限监控SHA `91cb56cc6806d77e7d5d2ecbcf10fe80914a5264399bf973f079dab6e0982f87`，
绑定各自PID/run，评估model50/100/199、seed517。异常或连续两次0成功且
至少16安全失败会停止对应训练。训练3200s、监控4200s上限。
保留种子未使用。i同时在录制press80的env0原速录像并重跑32回合报告。


i/press80录像已完成并取回，复核仍16/32、零安全终止、无未完成。
env0在12秒超时，推进0.5240666m，缺少完整停稳保持；不作为成功示例。
视频12s、1280×720、25fps、300帧，抽查8.8/10.5/11.8s机器人及箱体可见。
SHA `5c005dadbf17c1b0ad5dd6d32d81360385f9c3892e047c3e412e85e1bbebbe33`；
匹配报告SHA `ba57f576dd82cf5305fc673929b06f69d661466e85e14057f91f5eb8a6cfa885`。
本地i/RESULTS_CN.md和press80-video-status.json已更新。


j首个model50评估：lr1e-5为8/32、2安全失败，lr3e-5为3/32、1安全失败，
均无未完成回合；未超过控制基线16/32，不替换基线。训练最新核验101/114轮，
model100评估已开始；继续有限200轮检查，不扩展训练预算。


j全部200轮和六个检查点评估已完成：lr1e-5成功8/17/8、安全失败2/4/3；
lr3e-5成功3/19/18、安全失败1/2/5。所有安全失败均无效手接触，无未完成。
最好lr3e-5/model100的SHA dd02f3026f3464a5fc2c5add56ba6b14c2a96a1235fa1a73ae5e33e827a13b4e，已备份本地j/selected-model_100.pt。
最终未改善，不追加同配置训练。

<a id="record-0274"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## k：到位保持手端位姿（进行中）

19/32候选的多数失败已进目标区域，2次无效接触在11.88/11.98s停稳阶段。
原控制到位时将手端x参考从箱面内80mm切到箱面外30mm，突变110mm。
增加默认关闭push_goal_hold_pose，在原x剩余距离<.10m且安全接近/腿部
接管已完成时，记录并保持实测世界手端位置及姿态。回退出该阈值即释放，
重置每个环境时清空；观测/奖励的位置参考与控制器保持一致。
不更改到位阈值、成功保持0.5s、碰撞/合法接触/净空、关节限位与限速。
30项控制检查、编译、diff检查通过，五文件明确同步新k/train且SHA一致。
分别在i基线和j/lr3e5/model100评估，原12s/seed517/32回合，尚无结果。


k已完成：到位保持使i基线16→18成功，j/lr3e5-model100为19→21成功，
后者无效接触2→0；两组所有安全终止零、无未完成。剩余11个失败全超时。
控制目标变化带来收益，仍未达标，不消耗保留种子。

<a id="record-0275"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## l：小幅提前停止推进（进行中）

在k同一j/model100基础上，将控制器停止推进距离从默认.10m分别改为
.105/.110m。统一手端目标/到位保持/接触记忆/底盘命令的停止状态；
不修改PushSettled的误差<.12m、速度<.08m/s、连续.5s，原12s任务。
参数仅控制制动时机，范围校验限制[.05,.11]m。新增终态settle_duration和
goal_hold_active字段，在重置前采集；用于诊断尚欠多少稳定保持时间。
31项控制检查、编译和diff通过，5个文件新目录l/train的SHA与本地一致。
GPU0/1，原seed517/32回合；日志/报告stop105-seed517和stop110-seed517，待结果。


l制动.105/.110m均为22/32，零安全终止、无未完成。剩余10失败中8个
已在目标区域且静止，.110m方案连续停稳仅.08–.48s；另2个推进不足
（env24误差.541m、env28误差.152m）。原成功保持要求仍.5s。
同源追加渐进腿部接管.4/.3s对照（原.5s），固定stop.11，保留完整
SAFE_APPROACH与全部限位/限速/净空门禁；日志/报告stop110-ramp{40,30}-seed517。


l接管时长对照完成：.4s为25/32、1次初始无效接触、6超时；.3s为21/32、
8次初始无效接触、3超时，其他安全终止均零，无未完成。.3s不采用。

<a id="record-0276"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## m：真实合法接触后释放腿部（进行中）

新增默认关闭push_leg_release_on_contact，将首次接管条件从仅几何就位
进一步约束为SAFE_APPROACH完成且确有原分类器判定的合法手接触。锁存每
回合独立，短暂断接不会反复禁用腿部，重置清空；成功接触计数仍使用原传感器。
同一j/model100，l的stop.11/press80/限位内IK/到位保持，分别测试接触后
.3/.2s渐进接管（GPU0/1），原12s/seed517/32回合。没有跳过安全接近，
没有更改接触分类、净空、力矩/速度或成功门槛。32项控制检查及编译/diff
通过，四文件明确同步新m/train，5份运行源码SHA与本地清单一致。结果待定。


m已完成：接触后.3s为11/32，.2s为13/32，所有安全终止均零、无未完成，
等待实际接触损失推进时间，不采用。新开关保持默认关闭。
转而在l的同一25/32控制（stop.11/ramp.4/goal-hold/bounded/press80）上
复核已有j/lr3e5-model150和199，原seed517/12s/32回合，不新增训练。
源码仍使用l的已核验版本，不混入m。日志model{150,199}-stop110-ramp40-seed517。

<a id="record-0277"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## l后续复核与n有限微调

当前最新：普通PUSH在原12s调参seed517达到 **27/32、1次初始无效接触**，全部32回合完整，尚未达标。来自j/lr3e5/model100加l控制：限位内IK、姿态残差权重.5、press80、到位保持、stop.11、腿部渐进接管.4s、前进增益2.0。姿态权重.75为26/32；后续model150/199在权重1配置复核为23/20，未改善。完整结果见本地l/RESULTS_CN.md。

活动实验n：`/path/to/artifacts/go2-piper/push-refine-20261001-n`，两组匹配27/32控制的微调已启动；seed626、512环境、100轮、std.03、lr1e-5/3e-5，GPU0/1。训练PID3897186/3897505；run分别`2026-10-01_04-19-42_refine_weight50_lr1e5_seed626`和`2026-10-01_04-20-24_refine_weight50_lr3e5_seed626`。自动评估第25/50/99轮，状态在`outputs/auto-evaluation-{lr1e5,lr3e5}-status.json`。训练最多3200s、监控4200s。实际配置已核对，本地n有脚本、哈希、配置及状态副本。下一轮先读取这些状态并归档结果，不重复启动。

原独立验收种子701/1701仍未使用；冻结包未改，MuJoCo/CLIMB暂停。旧i视频是16/32诊断，不代表当前候选。

<a id="record-0278"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## n完整结果与o高度控制诊断

n两组第25/50/99轮分别27/27/27与27/27/25，均1次无效接触、所有回合完整；不延长。o固定原27/32的策略与控制，对比世界z误差权重2/3，保持原安全门禁；33项控制检查通过，正在远程GPU0/1评估。

<a id="record-0279"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## o结果与p接触接管诊断

o高度权重2为0/32、2无效接触和1净空终止；权重3为0/32、全超时，不采用。p恢复高度权重1，在合法接触前后按.5s与.2/.3s速率连续增加腿部接管比例，原任务/安全判据不变，正在远程评估；34项控制检查通过。

<a id="record-0280"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## p首批改善

接触期.2/.3s方案分别28/27成功，零安全终止、回合全部完整。首批失败env5停稳.20s，env20/24/28推进不足。追加接触期.15s、姿态权重.5/.75远端对照；原任务与成功标准不变。

<a id="record-0281"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## q录像与接触状态诊断

两次录像复核均28/32、零安全终止、全部回合完整；env0成功、env24推进约.0715m后超时，视频已取回、帧画面已检查。时序纠正此前“失联”推断：env24 hand_contact仍真、约22N，但短暂高度偏离使几何接近标志清零，压入参考切换后撤、底盘随后停止。r在原几何条件和安全判据不变的前提下，对照当前真实合法接触维持压入参考的默认关闭选项；off/on原32回合远端运行中。

<a id="record-0282"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## r首批结果与检查点组合复核

off/on均28/32、零安全终止、32回合完整。on使env20进入成功容差但只停稳.46s，env28目标误差降至.167m，尚未达标。继续用r开启配置复核已有n/lr1e5/model99和n/lr3e5/model25，选用先前停稳较早的检查点；未新增加训。

<a id="record-0283"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## r已有检查点达到29/32

n/lr1e5/model99及n/lr3e5/model25均29/32、零安全终止、所有回合完整。前者失败env5/28已到位但停稳.40/.32s，env24推进不足。追加仅修改姿态权重.4/.35，检查env5时序，原12s/seed517。

<a id="record-0284"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## s到位卸力对照

r姿态权重.4/.35均29/32，env28退化，不采用。s固定model99/r29配置，在到位姿态锁存时沿箱面向外偏移5/10mm，保持高度姿态，不改.5s停稳。35项控制检查通过、远端哈希核验一致，GPU0/1有限评估已启动。

<a id="record-0285"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## s结果与t受限底盘制动

s两组均29/32零安全，env5/28停稳仍.40/.32s，不采用。t固定29/32配置，原stop.11区域内才给底盘正向余速负反馈，x下限原-.10m/s，增益.5/1；新参数默认0，36项控制检查通过，远端源码核验一致，正在GPU0/1评估。

<a id="record-0286"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## t结果与u接触控制适应训练

t底盘制动增益.5/1均29/32、零安全终止、回合完整，未改善，不采用；相关两份报告已归档本地。当前活动u：在匹配r29/32接触控制下，从n/lr1e5/model99进行完整样本与可控阶段样本对照训练；seed627、每组512环境、200轮、std.03、固定lr1e-5，GPU0/1。

远程目录`/path/to/artifacts/go2-piper/push-contacttrain-20261001-u`；训练PID all=3905193、active=3905194，run为`2026-10-01_06-08-49_contactstate_{all,active}_seed627`。自动评估50/100/199轮，监控启动PID3905826/3905828，状态`outputs/auto-evaluation-{all,active}-status.json`。实际环境/算法/采样配置已核对并下载；原12s、5kg/摩擦.4、全部成功与安全门禁不变。r原副本未包含采样入口，本轮补齐三份既有采样/遥测源码，控制器保持r版，不混入s/t。不要重复启动。

两个监控遇评估异常会停止对应训练；若连续两检查点0成功且至少16次安全失败，也停止该分支。训练最多3200s、监控4200s；保留701/1701不会自动消耗，达到调参门槛后先固定候选再独立验收。采样适配5项本地检查通过，远端源码哈希核对，完整轨迹GAE保留。

<a id="record-0287"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## u中期改善

可控阶段采样model100达到30/32、零安全终止，完整样本model100为29/32；均32回合完整。active的env5已成功，env28停稳.36s、env24推进不足仍失败。权重已备份本地u/candidates/active-model100；最终199轮与独立验收尚待执行。

<a id="record-0288"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## u最终调参结果与首次独立验收

当前最新：u完整样本训练model199在原12s调参seed517达到 **31/32、零安全终止**，32回合完整，仅env24推进不足。两组200轮训练均结束，原训练PID3905193/3905194已退出。all第50/100/199轮为29/29/31，active为29/30/29，均零安全终止、回合完整。

已固定all/model199及r控制，checkpoint SHA `8c73bc1628da628cb4330143f14b2fd1fb5e7cdf1fb1e98a92fd55418f7de748`，备份在本地u/selected-candidate。独立验收seed701/1701已首次启用，各32回合、原12s，GPU0/1启动PID3907547/3907549；报告`u/outputs/held-out-seed{701,1701}.json`。当前结果待定，两个种子不得再标记未使用，也不应反复用于选择新候选。

<a id="record-0289"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## u独立验收失败与后续诊断

当前最新：u/all/model199调参seed517为 **31/32、零安全终止**，但首次独立seed701为 **29/32**、seed1701为 **27/32**，各1次无效手接触，其他失败为超时；两组32回合均完整。**Isaac验收未通过，不能交付为成熟策略。**

现有证据：701/env2在8.78s、1701/env22在9.58s出现约.193m箱体上沿无效接触，箱高.20m、原接触边缘裕量.01m不改。1701/env0合法接触持续但手端降至约.06m，肩/腕接近力矩上限；底盘到箱面间距跌破原.43m时前进命令置零，箱体距目标仍.382m。不能靠降低间距保护、提高力矩上限或放宽接触定义解决。

两个已准备并上传的录像复现脚本`launch-diagnostic-{701,1701}.sh`拟观察701/env2与1701/env0，各原12s/32回合/700s限时。启动连续两次被自动审批拒绝，理由是此前视频/远程优化授权未明确覆盖额外诊断；命令未执行、没有新录像或运行PID。已向用户发出具体操作确认，勿标记诊断已启动或绕过拒绝。已有遥测继续可用。

<a id="record-0290"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## v本地候选与既有轨迹复核

本轮后续：已完成既有遥测的本地复核，并准备v渐进减速候选`push_contact_gap_slowdown_start`，默认0关闭；测试值.52m。仅安全接近完成且当前真实合法接触时，向原.43m停止边界连续降低正向速度上限；不使用接触记忆触发，不改变物理/安全/成功标准。39项控制检查、编译及diff通过。对既有env0状态代入公式：成功517未修改，701/1701会减速；这不是新仿真结果，也可能延迟701的到位，未采用。上沿误接触复核为高出原接触裕量3.59/2.26mm，v不宣称解决首次误接触。

v仅本地准备，目录`../artifacts/go2-piper/push-gapcap-20261001-v`，含完整匹配源码快照、哈希、离线分析脚本/结果和off/.52远程对照脚本。未上传、未创建远程v目录、未执行新仿真或训练。本轮没有重试被拒绝的u录像命令；上轮具体确认仍待用户回复。详见[v本地候选记录](../../../artifacts/go2-piper/push-gapcap-20261001-v/RESULTS_CN.md)。

<a id="record-0291"></a>

来源：TRAINING_STATUS_20261001_CN.md。

## w离线USD运动学核对

后续w离线核对已完成：用u匹配USD重建96个记录终态，机械臂刚体位置最大误差2.77微米，7项资产哈希一致。两次上沿误接触的实际指令前伸约.664m，在原.9软限位内局部姿态拟合残差43/45mm并触及肩关节软上限；6个推进不足终态拟合残差0–4.50mm，不能将两类失败混为同一原因。全程.60m前伸上限虽改善两次误接触的静态拟合，却会把成功517/env0的50个合法推进记录样本的面内目标移到面外，因此不直接采用；局部拟合不是动力学/碰撞/全局可达性证明。

本地w：`../artifacts/go2-piper/push-kinematic-audit-20261001-w`，含可重跑脚本、96状态结果、CSV、SHA和[解释](../../../artifacts/go2-piper/push-kinematic-audit-20261001-w/RESULTS_CN.md)。本轮未改控制器、未启动仿真或训练；v仍默认关闭。上轮两次录像具体确认仍待回复，本轮未重试或改换方式执行。


<a id="push-through-v216-20261013"></a>

## PUSH开发记录归档：截至2026-10-13交接整理前

以下完整保留整理前的PUSH页。文中的“当前”、运行中PID和旧复现入口均为历史记录；接收组使用[当前v212交接](../PUSH_CURRENT_HANDOFF_CN.md)。v216后续状态在当前页单列，不覆盖用户认可版本。

## 最新 PUSH：跨组使用入口

候选核对：2026-10-02；自碰风险复核与安全控制诊断：2026-10-10；MuJoCo sim2sim诊断开始：2026-10-08。其他小组先读本页；当前交付范围是 **GO2-PIPER 的 Isaac 仿真参考技能**。

### 安全 PUSH 当前状态（2026-10-13）

#### 用户最新要求与当前运行

**当前结果：精简接近路径v212在已用3701/8环境中8/8，15.98～20.50秒完成；已用2701/32环境为30/32，另2例非法手接触，不能替换原候选。v214被静态门槛拒绝；v216已调整接近终点并保留一个转折点，配合高度减速进入动力学验证；尚未安全交付验收。** 用户允许继续降低箱体负载/摩擦，要求训练出原起点接近→合法接触→持续推到目标→停稳的完整技能；不再以5cm阶段录像作为完整PUSH交付。首个训练域为**1kg、静/动摩擦0.15**，箱体尺寸仍1.2×1.2×0.2m，目标推进0.60m；目标误差<0.12m、速度<0.08m/s持续0.5秒的原成功判据保留。48秒仅用于本次完整任务训练和诊断，原12秒及独立验收仍单列；新负载成功不能称为3kg/0.3通过。

2026-10-13 14:54心跳后核对：v212精简版env0完整原速录像已完成并同步到`push-direct-approach-v212/video-development-seed3701-8env-48s/full-push-env0-original-speed.mp4`，**16.00秒、1280×720、25fps、400帧**，SHA256 `5825476ea9dfe7915bba69780cefa926f92922c65e1cd233dbdd316d8985cc47`。录像报告SHA256 `2cea320b10f56621b265b448bcfdc6da7af49548cb0fe55662e836fd27ddcc08`；全部8终态及物理汇总与非录像8/8逐值一致。env0实测接近完成11.28秒、接触面准备13.42秒、合法手接触13.86～15.14秒，15.98秒成功，视频取整到16.00秒。六帧抽样显示接近、推箱和末态，首帧渲染黑屏仍保留；这是稀疏视觉复核，不冒充全片逐帧审查。该录像只展示一个开发成功回合，32环境2例非法接触仍计失败。

v213的固定末端中点优化达到迭代上限，最低箱距15.947mm，未过25mm静态规划目标；v214条件工作流因此`rejected_static`，**没有启动动力学**。补查发现旧固定末端自身箱距仅17.435mm，因此在保持该终点时不存在整段≥25mm的路径，不能只继续优化中间点。原报告/失败求解保留。

`push-box-approach-audit-v215/`改为后移并居中接近终点，再优化一个转折点。末端求解器首次未收敛，其候选直接段仍碰箱、单转折段只有22.79mm，均未通过；后续`refine_midpoint.py`在新终点上收敛，3点路径每段401点复核，**臂/手—箱最低25.990mm、臂—机身最低59.999mm**，满足原25/55mm规划目标。中点相对旧第18点最大变化0.03216rad；第一姿态保持原样。这是一个实测env26固定机身/箱/腿姿态下的静态结果，不是完整动力学安全或全部随机初态证明。

`push-retracted-guarded-v216/`已冻结上述3点短路径及v214准备的手高度减速，其他速度/参考平滑、原接触分类、35mm实际净空、0.98力矩及停稳门禁不变。与v212仅路径JSON和`box_push.py`的正向速度上限两处有差异，计划SHA256 `6872792bdd8b10c7b973aac7c5428d7492ecb24220b65e54e6af58186101c6b1`，229项源码本地/远端核对一致。`height-guard-check.json`验证实际函数在40～60mm高度误差时的前进缩放、后退/非活动/到目标状态保持，以及不修改命令输入和就绪状态，检查通过；这不替代物理测试。

两张GPU已无外部物理占用，v216 worker1120409/1120410分别启动：GPU0已用3701/8环境，至少7成功且无安全失败/缺失后扩大已用2701/32；GPU1使用**已用**913701/32回归v210启动失败，不能把该种子重新计为未用验收。本地小型同步3260506；v212成功/失败报告、16秒录像和旧21点路径均保留。当前只更新本地交接，Git维持be8bb19，待下一动态里程碑再合并。

2026-10-13 13:54心跳后核对：v212动力学诊断完成。8环境**8/8、缺失0、安全终止0，15.98～20.50秒**；32环境**30/32、缺失0、2次非法手接触，成功例14.64～20.26秒**。与同权重旧21点路径的32/32、38.38～44.48秒相比明显提速，但env9/26丢失成功，旧版本保留。报告SHA256分别`5d39f86db91a792ed4f9e9edf7802bb746d211ca574c11be79c37a04e672f56d`、`ef00079983df4af5dc7681d4f493b747a17a4e126bb92d27365a5b1597e28481`；`audit_results.py`核对229项源、终态/采样计数、实际负载和成功判据。两批均是已用种子48秒开发诊断，不是12秒验收或新独立验证。

32环境含初始化/终止步的27134个20ms样本：实际臂—机身净空最低44.414mm，最大力矩比0.969700，0.98违规0；腾空58、少于三足868个环境采样，竖直速度峰0.563428m/s，单足合力峰309.86N、足力向量和模长峰425.45N。8环境对应7262样本、净空45.445mm、力矩0.971736、超阈值0、腾空14、少于三足234、竖直速度0.561303m/s、单足199.07N、合力向量和371.56N。不是子步安全证明。

失败已分开定位：env26在10.60秒尚未完成接近时碰到箱上沿，手接触点世界z=0.20054m（箱高0.20m）；env9在14.08秒已推0.279m后接触点升到z=0.19222m，触发原非法手接触门禁。`push-box-approach-audit-v213/`把env26同一机身/腿/箱状态置入匹配MuJoCo静态几何：直接路径臂—机身仍≥60.5mm，但臂/手—箱几何最低−5.33mm，说明v211仅检查机身不能排除箱沿碰撞；该负值不是PhysX穿透深度。复用旧第18点作为单个转折点可将臂/手—箱静态最小间距提高到15.95mm，尚未满足此次25mm规划目标，正在原软限位附近优化该转折点。静态结果不当作动态通过。

`push-short-guarded-approach-v214/`条件工作流PID1120041：只有v213优化路径通过≥25mm箱体/≥55mm机身静态检查，才冻结新副本并进入严格完整8环境诊断，通过后再扩大到已用2701/32。除3点短路径外，在实测接触面准备完成后，手高度相对目标偏差40～60mm时将正向前进命令连续缩至0，保留后退和目标制动；原接触分类/执行器/实际净空/碰撞/停稳终止不变。实际函数的命令边界、非活动/目标保持及状态不被修改的检查会在物理运行前执行。该条件工作流仍未取得动态结果；GPU0在录像结束后按占用排队，本地小型同步PID3238366。

v212短路径完整原速视频正在GPU0补录已用3701/8环境成功批，worker1119480，本地视频同步3236515；GPU1被外部世界模型进程1118747占用，未干预。原v210的39.40秒完整视频已完成并同步，SHA256 `0c3f6cae8c591064dc5a415ca1557f3c332b9e7f97e192ee6f212dbcf1e2ab41`；全部8终态及物理汇总与v209同权重非录像批逐值相同，视频为1280×720、25fps、985帧。它仍是旧21点路径，不能冒充本次15～20秒精简版；原速视觉检查分别记录。

`v211`静态捷径核对完成：原21路点可直接保留第0/20点；按每轴≤0.005rad、483点采样，臂—机身最低净空60.500mm，通过原55mm规划余量。另601点快速对照最低值一致。累计最大关节段长由6.350rad降到2.407rad（约减少62%）；这不是预计执行时间，也不证明臂—腿、手箱、全自碰或动态力矩安全。全节点搜索因直接段已通过同一几何门槛而停止，无需继续搜索；`audit_direct.py`和`result.json`保留证据。

`push-direct-approach-v212/`已按用户意见进入原起点完整动力学对照：与v210相比只把路径JSON的21点改成同一首末2点，原权重、速度/平滑、实际到位/速度、碰撞/35mm净空/0.98力矩/真实接触/停稳条件全部保留。计划SHA256 `c4eda1d2bbdd6329c22128cb61f3670d3d14d402d85336352a79f8d130a4ae6b`；GPU0先已用3701/8环境/48秒，至少7成功且无安全失败/缺失才自动扩大到已用2701/32环境。首次准备脚本字段名漏`_s`，在启动物理前失败，已修正并保留失败启动记录；新PID见`launch.json`，本地小型同步PID3213118。v210旧路径保留，v212未出结果前不得称直接接近已动态安全或已提速成功。

用户指出完整视频前段多余机械臂动作后，复核v203录像：前36.18秒用于旧21路点接近，每个路点均要求关节误差<0.04rad且速度<0.12rad/s后才前进；39.08秒才首次合法接触。该路径来自避碰探索，尚无证据证明21点都必需。已启动独立`push-path-shortcut-audit-v211/audit.py`（远端CPU PID1116023），检查保留原首末姿态、55mm静态臂—机身规划余量的跨路点捷径；不修改v210冻结候选或放宽实际35mm/碰撞/力矩门禁。静态通过仍需真实自由机身的完整动力学复测。

v210两组未用种子48秒验证已结束：A（913701）**31/32、缺失0，1例臂力矩门禁失败**；B（913702）**32/32、缺失0、安全终止0**。A的env12在0.32秒、第一路点即终止，尚未接触/推进；不能写成零安全失败或安全交付已完成。两报告SHA256为`449f56da5398df5981920e10cf7bbfaffb4e1fbf0b3e8dd1bfa1e283fbf255d3`、`72968c18926caf267a75c75bfc9bd3f05b275399bef653285146516da99b9f51`。两组成功数量满足≥30，但初始化力矩边界需继续处理，原12秒与MuJoCo验收仍未通过。原队列因A有安全失败未自动录像；用户已要求看视频，现单独在GPU1以已成功的开发seed3701/8环境补录匹配8052/v210完整原速录像（worker1116078），只作开发成功例展示，不能掩盖该失败。视频完成后由独立本地视频监听保存（实际PID见`sync-video-launch.json`），不下载大报告。

2026-10-13 11:54心跳后核对：v209两路均结束。已用2701/32环境/48秒中，8051与8052均**32/32成功、缺失0、安全终止0**，分别37.88～44.20秒、38.38～44.48秒完成；原26个成功环境保留，env8/10/11/15/19/26六个超时全部转为成功。8052的已用3701/8环境也为8/8；不是把两份权重在同一开发种子的结果当成独立验收。独立只读审计已核对全部四份报告的唯一终态、实测物理、成功/停稳条件、来源及含终止步力矩。

| v209开发报告 | SHA256 |
| --- | --- |
| 8051／2701／32环境 | `ba521335ff89a3ee80fbb2d5d528904fb2bd6c6fc87afde3626b3cf8adcf1dbe` |
| 8052／2701／32环境 | `c6664ff72494415fe1ad1971ee405d4816fa4c4043f1c5cf1358fa4cfe87a72e` |
| 8052／3701／8环境 | `a5962f8534c0916b8a257db2a2f6653956ab51ec07c81231e853047baa283ac8` |

两份32环境物理汇总按8051／8052顺序：65578／65658个20ms样本，实际净空最低40.169／46.925mm、最大力矩比0.973687／0.973768、0.98违规0／0；腾空58／58、少于三足898／885个环境采样；竖直速度峰0.563885／0.563883m/s，单足合力峰294.43／292.28N，足力向量和模长峰443.47／385.08N。包括初始化和终止步，不能外推为物理子步证明或全程四足支撑。

`push-fixed-validation-v210/`选择8052，依据是同一32回合开发批的净空余量更大、足力峰更低，不以最快选型；8051和旧成功路径保留。checkpoint SHA256 `4d1a4616928b4d06002285e870a1d6dd114e27b8cafcdd9a41dbdae1aceed419`，与v209相同；控制源码没有改变。评估器仅纠正入口推进段元数据90mm→30mm，并让录像在被观察环境结束时停止，避免混入重置画面；两处都不改物理/成功/安全条件。冻结计划SHA256 `46ebbee25392ccac86c893216e6b1f1490f3c30577f47b4d415ceeab5b47a23f`，229项匹配源码已本地核对。预先固定两组seed913701／913702，各32回合、原起点、48秒；两组分别至少30成功且缺失0，所有安全失败单列。**这是48秒延长窗口独立验证，不能标作原12秒验收；MuJoCo独立验证也尚未完成。** GPU0该组完成并满足启动门槛后，自动以已用3701/8环境补录env0完整原速视频，视频另作复跑一致性和视觉检查。 历史1226份小型计划/启动/命令/状态元数据及文件名的精确种子字段检查未发现913701/913702；检查范围和排除项保存在`seed-history-audit.json`。两路worker已启动，PID1115260/1115261，本地小型同步PID3194561；不重复启动。

2026-10-13 10:54心跳后核对：`push-entry-retreat-v209/trained8051-used3701-8env-48s/`为**8/8完整成功、缺失0、原生安全终止0**，39.12～43.92秒完成，均满足原目标误差/箱速及连续0.5秒停稳条件。之前超时的env4在43.28秒完成，箱体前移0.664m、终态误差0.064m；原7个成功环境全部保留。报告SHA256 `f6a6b4b3858e1f93bf6d2991a415f511cfd7cf87a0f75d271efcae543d549e97`。独立只读审计`audit_completed.py`及小型`independent-audit.json`核对229项源码、报告哈希、8个唯一终态、实测1kg/0.15、停稳及终止步力矩；合法接触历史由匹配的原生`PushSettled.contact_seen`条件保证，报告没有单独导出每回合该锁存值。

全批16645个控制样本（含初始化/终止步）计数一致：最低实际表面净空46.467mm，最大力矩限额比0.976178，0.98违规0；腾空14、少于三足239个环境采样，最大竖直速度0.561851m/s，单足合力峰202.38N、足力向量和模长峰345.38N。不能称全程四足稳定或物理子步无风险。报告的`actual_physics.controller_contract.approach_pitch_transition`沿用了旧`0_to_90mm`文字，匹配的冻结源码实际为30mm；审计明确勘误，未改写原报告或运行中源码。下一版报告器需修正此描述字段。

GPU0已自动进入8051的已用2701/32环境/48秒诊断（PID1113752），GPU1外部任务退出后开始8052的已用3701/8环境诊断（PID1114413）；均核对为实际运行，没有重复启动。本地只同步小型证据，32回合结果待完整后再决定固定候选及新原速录像；当前最新完整录像仍为v203成功例。该8/8属于已用开发种子、48秒诊断，不是原12秒或Isaac/MuJoCo两组未用32验收。仍需先验证鲁棒性，再缩短接近耗时；Git暂不为单次轮询新增提交。

2026-10-13 09:54（北京时间）核对：v207两路已用2701/32环境/48秒扩展诊断均结束，**各26/32、6超时、缺失0、原生安全终止0**；这是两份权重对同一开发种子的对照，不是两组独立未用种子验收。8051报告SHA256 `8436102de5d43d81022a9cdb8d85b50e675f5ff3d799b7d736e1c64f0861cc98`，8052为`9fa3f3852c65acdf8165f522f179bd1f33b9922ae3306def36ee3e94e5f43440`。两份都在env8/10/11/15/19/26超时；前5例均走完21路点但未通过入口高度/位置就绪，箱体未推进。env26在8051中已接触并推约0.173m后超时，8052仍未完成接近，不应把全部6例归为同一入口机制。

全批控制采样审计一致：8051/8052分别68351/68368样本，最低实际净空44.118/44.527mm、最大力矩比0.973687/0.973768、0.98违规0、腾空58/58、少于三足746/747、竖直速度峰0.563885/0.563883m/s、单足合力峰303.77/270.08N、足力向量和模长峰391.07/403.00N。均含初始化/终止步，不代表子步安全；没有缺失也不等于达到鲁棒性要求。v207两路及小型同步均已结束，无重复启动。

`push-entry-ik-audit-v208/`对已用3701的env4及2701的5个入口失败终态做静态匹配复核，末端FK与Isaac实测误差最大0.773微米。固定实测机身、原90%软关节范围及joint4下限、55mm臂—机身优化净空，以原120mm退让入口作局部优化：原0.1或降低到0.03的姿态软权重均未使这些局部解通过原位置条件；部分求解达迭代上限，不能证明全局不可达。把中间退让目标改为60mm、保留原0.1姿态权重时，6个静态解都满足原入口位置门槛；实测起点至候选关节线段101点采样净空最低50.34mm，候选末端约55mm。`result.json`、`entry060-result.json`和两份脚本保留来源。此筛查没有动态、手箱接触、力矩、全自碰或机身受载效果，不是物理通过。

`push-entry-retreat-v209/`继承v207和同一两份model255，仅将箱面前中间入口退让从120mm改为60mm、随后推进段90mm相应改为30mm；**最后箱面准备点仍为后方30mm**，入口位置/速度/连续100ms、真实接触、0.98力矩、35mm实际净空及停稳门槛均不变，关节参考平滑保留。两路仍先已用3701/8环境/48秒，至少7/8且无安全终止/缺失后才自动扩大到已用2701/32环境。计划SHA256 `c22bdf9bbe0b319294b50af09b32463a5b84c193af8e0065cd00521ca1ebaaff`；worker PID1113243/1113244，本地小型同步PID3151257。启动时外部集成PID1112641使用物理cuda:1，GPU1曾排队；当前进程及已完成结果见上方最新核对。计划与原始报告保持不变，Git维持7cb8268。

2026-10-13 08:54（北京时间）核对：v207的两份已用3701/8环境诊断都仍为**7/8、缺失0、安全终止0**，原成功环境保留，env4仍接触前超时；不能称接触前残差限幅已解决剩余失败。报告SHA256分别`94f30cd326bed2f9ae4a70000042d9ca448e3ba4565b1364b6cfc6664b623432`（8051）和`5cb2dc8a1e12ec87b88d3c5ff9d2d931599a8cfa151727ebbc46658627ad395a`（8052），含初态/终止步采样计数一致。两路已按既定门槛自动进入已用2701/32环境/48秒扩展诊断，Isaac PID1111902（GPU0）与1111942（GPU1）均实际运行，约2000/2400步；结果尚未完整，不汇报中途成功数为最终成功率。本地同步PID3111077继续运行，无新增Git提交。

`v207/remaining-entry-timeout-audit.json`保留两份env4小型终态：实测入口X误差约61.6～64.0mm（原门槛50mm）、Y误差73.8～78.7mm，速度门槛满足、几何屏障未阻挡。逆解期望joint4到1.5705rad边界且姿态误差仍较大；下一步应核对入口逆解的可达性与位置/姿态软目标取舍，而不是放宽实测门槛或继续扩大残差限幅。此为失败诊断线索，尚未证明具体修复。

2026-10-13 07:54（北京时间）核对：v205/v206全部退出，工作流完成不等于验收通过。v205 seed8052最终model255严格原起点/已用3701/8环境/48秒为**7/8，1超时、缺失0、原生安全终止0**，成功时间39.64～44.08秒；报告SHA256 `a750ff8ec96bc4e9a6bb5c6c3a1cb0d84c43d45ccc08a96581f04b1758ad99a8`。v206只限制路点残差，将seed8051最终model255从0/8恢复为**7/8，1超时、缺失0、原生安全终止0**，成功时间39.46～44.26秒；报告SHA256 `f862bae1b3eb52b1a2fe1fa960e3bad4136984524fc57de13f29333f1bab309c`。原model63的同改动对照仍6/8且原成功例保留，报告SHA256 `febe64fe4795944438efafcc7faca92ca5887fbe8d9de5b4580d541ca955ba09`。两个7/8版本都仅env4在接触前超时，实测横向偏差约7.8～9.5cm；全部路点已完成，实际碰撞屏障未阻挡。不能把路点修正称为已解决全部接触问题。

两份7/8全批遥测分别为：8052/v205最低净空47.077mm、力矩峰0.976296、0.98超阈值0、腾空14/少于三足214个环境采样、竖直速度峰0.56185m/s、单足合力峰203.62N、足力向量和模长峰324.02N；8051/v206最低净空46.746mm、力矩峰0.976178、超阈值0、腾空14/少于三足213、竖直速度峰0.56185m/s、单足力峰291.58N、足力向量和模长峰394.89N。均包含初始化和终止步、20ms控制采样；三份报告终态/采样计数独立核对见`v207/parent-comparison-audit.json`，不是物理子步或两组32验收。两组model255与manifest已本地保存于v205的`preserved-model255-seed8051/8052/`；不能混用匹配控制源，旧失败报告和原6/8权重也保留。

`push-entry-residual-v207/`继承v206，唯一控制差异是把±0.02rad残差限幅保留到**实测`approach_face_ready`**，之后恢复原学习残差；原实际到位/速度/100ms保持、真实接触、35mm几何、0.98力矩、关节参考平滑和停稳判据不变。不修改已训练权重。GPU0 seed8051权重worker PID1111208、Isaac PID1111224；GPU1 seed8052权重worker PID1111209、Isaac PID1111225。两路均先原起点/已用3701/8环境/48秒严格诊断，只有至少7/8成功、无缺失且无安全终止才自动进行**已用2701/32环境/48秒扩展诊断**；该种子用于开发诊断，不占用未来独立验收名额。未通过则停止该分支扩大，不自动追加训练。计划SHA256 `b35ed1287db280c4ddb7c30bef5d9958cb80c4c7aff20e67afde4df2fda60116`；229项源码已冻结并本地同步；小型自动同步PID3111077，当前结果未出，不能预告通过。

2026-10-13 03:54（北京时间）核对：v203冒烟seed8030、4环境、64迭代已完成，其固定model63的原起点、已用3701/8环境/48秒严格诊断为**5/8完整任务成功，缺失0；2例在0.32秒触发臂力矩门禁，1例48秒超时**。5例成功环境为0/1/2/3/7，实际推进0.630～0.676m、目标误差0.032～0.076m、停稳0.50秒，完成时间41.12～46.16秒；没有原生碰撞/姿态/实际净空终止。env4已走完21路点，但未形成有效推箱。报告SHA256 `e0f71deaaaaf90a99ab9fa3157197c5134859452f69080921eafdee19404e4bf`，权重SHA256 `49cd7955f08a8f28ce4f33c3b5c16e806fd1e4916297a2adfbd0ee3a2413ee68`；独立终态核对见`v203/strict-terminal-audit.json`。原源码、权重保留，已另存本地`v203/preserved-smoke-model63/`，必须匹配226→19与冻结腿部hook，不能交给旧接口。

全批含初态/终止步13446个20ms环境采样，计数审计一致；最低实际净空50.16mm，最大力矩比0.984407，超过0.98的样本2个；腾空14个环境采样、少于三足支撑150个（单足竖直力>2N的遥测口径），竖直速度峰0.56179m/s、单足合力峰272.85N、足力向量和模长峰364.91N。不能将5个原生任务成功扩展成全批无腾空、始终三足或已安全交付；这些是控制采样而非物理子步证明。两次早期失败使工作流按既定门禁拒绝长训，seed8031/8032未启动，所有v203计算/同步进程已结束。

同轮用不变v202权重只换新路径的配对诊断仍**0/8、缺失0，8例48秒超时**，从旧索引15推进到18，没有接触。最低实际净空68.87mm、力矩峰0.970622；19208采样计数一致。报告SHA256 `937e9bb3f192cbcef3366743b53cc332ccb85cf3cab948179fa42985a6de8ed0`。因此5/8进展对应新路径上的新训练权重，不能归功于仅换路径。

2026-10-13 04:54核对：`push-startup-blend-v204/blend-used3701-8env-48s/`已结束，同一model63、原起点、已用3701/8环境、48秒，**6/8完整任务成功、缺失0；2例超时，原生安全终止0**。原5个成功例均保留，env5从启动失败变为成功；env4/6仍在接触前停住。全程最大力矩比0.976332、0.98违规采样0、最低实际净空50.145mm；18136个环境采样计数一致。仍有腾空14、少于三足支撑169个环境采样，竖直速度峰0.56185m/s、单足合力峰203.63N、足力向量和模长峰375.55N，含初始化、不冒充子步或最终安全验收。成功时间41.36～46.42秒、停稳0.5秒，报告SHA256 `83c61044fc154c780cbe2facdd02f4f3b220b3964856876be0157b8c9e83d510`。v204仅在原软限位/平滑/屏障前，用重置后1秒三次曲线将臂残差从0平滑引入、速度系数从原初始化0.2过渡到网络输出；不修改状态、计时和门禁。两例终态实际手端横向偏差约7～10cm，原几何接近门禁未满足、没有合法接触，不通过放宽门槛解决。

完整录像在`push-startup-blend-v204/video-used3701-8env-48s/full-push-env0-original-speed.mp4`，**它使用不变v203控制与权重，是v203的5/8批次成功env0，不是v204的6/8录像**。1280×720、25fps、1028帧、41.12秒，SHA256 `59089b90f0c32fa9c3310ba1d6285a0410f948707c65bf35837f91e945125852`。录像重跑的全部终态与物理汇总逐值匹配原非渲染报告，8例终态齐全；报告SHA256 `a0ff49a3217a043b8db2d9f707b9a7f53cf19b394d51bb742f9a91bcc01bd69a`。仅在env0终止后停止写帧，避免后续重置混入动作，未改变控制/成功统计；已检查抽帧画面和时长，仍须用户检查原速运动。逐步trace核对env0：36.18秒走完路点、38.48秒接触准备就绪、39.08～40.32秒有合法手接触、41.12秒完成；主要耗时在接近路径，不能称已解决效率。该例腾空采样只出现在0和0.02秒，1秒后仍有26个少于三足支撑采样，不能推及全批次。视频、`video-audit.json`与`trace-stage-audit.json`同步本地；v204计算/同步进程均已结束。

`push-warmstart-train-v205/`从上述v203已学会完整推箱的model63初始化机械臂网络，继承v204启动平滑，原奖励/门禁/物理参数不变。两条独立训练分支seed8051/8052各16环境256迭代，学习率3e-5；腿输出仍来自原model199独立冻结actor，critic和optimizer重新初始化，所有旧权重/成功路径保留。64随机观测加载逐值一致、100次Adam更新后腿输出仍逐值冻结、训练/评估加载一致及整回合违规锁存检查通过。计划SHA256 `967f56c5c13fab1a89dad08c0912f693ea83765fb717f141937ef4cfa765449a`。工作流PID1108598、worker PID1108601/1108602，本地小型同步PID3052058。2026-10-13 05:54核对两组均在训练：GPU0 seed8051的Isaac PID1108611、GPU1 seed8052的Isaac PID1109122；外部集成任务PID1107985已自然退出，旧`gpu1-queue.json`仅为历史排队快照。两组本轮约142/108迭代、尚未完成256迭代及固定权重严格评估；训练回合成功计数不替代验收。当前229项源码哈希与计划一致，本地同步正常，没有重复启动或修改运行中源码。各训练完成后自动做同规格严格8环境诊断；当前尚未开始独立两组32验收。Git维持上次里程碑8ec3531，先更新本地证据与本页，避免逐轮冗余提交。

2026-10-13 06:54核对：v205两组256迭代训练均已正常结束。seed8051最终model255严格原起点/已用3701/8环境/48秒评估为**0/8、缺失0，8例超时**，终态路点索引19/19/19/19/11/19/19/13，没有进入推箱；所有原生安全终止0、力矩峰0.976431、净空最低53.266mm。报告SHA256 `a5e9f6da1adece355c80e7e1df04d6a6ebf18cb702f67aafcc6533fb161c19ef`。训练过程曾累计38次安全训练成功/48个已结束回合，不能代表最终确定性策略；seed8052累计37次安全训练成功/48回合（39次原生到达中有2次违规不计成功），固定最终权重严格评估正在GPU1、Isaac PID1109962运行。没有继续延长训练，不覆盖v204的6/8版本。

`v205/waypoint-residual-audit.json`定位一个确定的到位冲突：env0末态停在路点19，joint5学习偏置为+0.063270rad，实测相对名义路点误差+0.063290rad，超过原0.04rad位置门槛；几何屏障此时未阻挡。当前确定性偏置使位置到位条件无法满足，训练采样噪声可能掩盖这一问题，但不能据此解释全部失败。

`push-waypoint-residual-v206/`只在**尚未实测完成全部路点时**，把学习残差限制为原位置容差的一半（每关节±0.02rad）；原0.04rad位置与0.12rad/s速度到位条件不变。完成路点后恢复原±0.20*tanh残差，仍先经过关节软限位、参考平滑和几何屏障；继承v204启动平滑，不改变权重、PD、延迟、接触或成功门槛。用原成功model63和退步8051model255分别做同规格严格对照，避免只挑一份有利权重。计划SHA256 `4952d1ddb7d84d583c813e62519349e32cfe7447e9330ecd6ea4d9a24246f91c`，229项源码冻结。GPU0原成功权重worker PID1110322已启动；GPU1退步权重worker PID1110323按实际GPU UUID上的进程占用排队，等v205评估结束。小型本地同步PID3091606，仍不复制大报告和中间权重。物理结果尚待完成，不将该实现改动称为已修复。


v202固定冒烟checkpoint的严格诊断为**0/8、缺失0，8例均48秒超时且停在索引15，无合法手接触或箱体推进**；无原生安全终止，含终止步力矩比峰0.970622。报告SHA256 `46e0fa7d6b5aa6c7fe8eb27adba886f778838751bb4c7b65f6b0854a3ccb15dd`。独立静态审计确认继承路径索引15/16/20的名义机身净空分别30.12/27.65/25.02mm，低于原35mm实际终止门槛；索引19为39.09mm，也低于预测屏障50mm余量。此冲突解释了继续奖励训练之前必须修正参考的原因，但不证明整个0.04rad到位容差邻域都不可行。旧路径SHA256 `c5a775cd9fe17ef33c6c0ebc4629d56f7b7850b8d523f44ef4ecde2120c161c6`，详见v202的`waypoint-geometry-audit.json`。仅停止本任务两组训练和工作流，外部任务未干预；停止原因、原状态、精确进程清理记录保存在`stop-for-path-audit.json`等文件，旧权重/日志保留。旧本地同步监听已退出。

v203保留原起始姿态及其他路点，仅最小位移修正15/16/19/20四个路点；单关节最大变化0.05934rad。20段各201个静态采样的臂—机身最小净空60.17mm，详见`path-audit.json`；这只是静态几何证据，不是动态自碰/力矩/接触通过。计划SHA256 `052a09bb925d6d72eac3a5885da6f4ae293210340760aad19b9c061f9b257b3e`冻结229项源码。初始化检查及整回合违规奖励锁存检查通过；226→19接口、独立冻结腿部actor、原PD/延迟/真实接触/停稳契约不变。评估新增所有活动环境含初态及终止步的物理汇总，记录支撑、腾空、竖直速度、足力、净空及全关节力矩；采样频率20ms，非物理子步证明，计数一致性已由本页顶部两轮评估核实。原同步PID3013479已结束；大报告/日志留远端，成功冒烟权重另作本地保留。

v203沿用v202的60ms最终PD目标滤波、从接近阶段实际干预的几何屏障，以及取消接近等待的持续姿态正奖励、将原−0.1/秒时间成本覆盖等待。实际35mm净空终止、含初始化0.98力矩门禁及原成功判据均未降低。源路径修正与训练均在独立目录，不覆盖已保留的参考候选；Git按实质里程碑合并更新。

2026-10-13 00:54（北京时间）核对：seed7981/7982两组均已完成1024迭代训练，安全完整成功均为0，seed7982的14次原生目标到达全部未取得安全成功；不继续延长本轮训练。seed7981固定最终model1023的已用3701、8环境、48秒严格评估已结束，**0/8，缺失0**：env0/3/5/6在0.02秒joint5触限，其他4例到48秒仍停在第一接近路点。报告SHA256 `94b939be7a77fce54401abf3564589ab8c87b1d44e24fe63ad1316194d0a9536`，权重SHA256 `07501a8a85313f19d544ff050b3a11fed83f5d6436a84c203e2782a3e9b68370`；合并终态后的力矩峰值比1.0。`final-evaluation-audit.json`保留独立审计。seed7982同规格严格评估也已结束：**0/8、缺失0，6次臂力矩失败、2次超时**，报告SHA256 `36077c61d06e4e2686ddb3cb8ef3b05aa9d847f4d405367856067728b79a2dd3`。两个训练/评估worker均已退出，工作流正常完成不等于安全通过。

GPU0转入启动瞬态配对诊断，所有轮均使用原重置、同一smoke model63、已用3701/8环境，严格执行含初始化0.98力矩门禁，2秒只检验启动，完整PUSH成功仍为0。`push-command-slew-v199/`在原几何参考平滑后，对含重力补偿的最终PD位置命令增加0.5rad/s限速：即时0.02秒失败消失，但8/8在0.22～0.24秒joint3超限，启动0/8。`push-command-slew-v200/`将最终命令上限改为1.5rad/s，原几何参考限幅不变：3/8到2秒、第三路点，其余5/8在0.34秒力矩失败，整体仍拒绝；记录峰值比0.990001。两轮报告SHA256分别`0f7da2cf5a34d1cba46d9e0c8378eda29c93bf38ff70d8cc8ac9b948136760a8`、`f9783fb55f35fcb8351560c212e1f347e28c062fd0d2648809e943f5c90c4670`。`push-command-filter-v201/`用60ms一阶滤波替代最终命令线性限速，原PD、延迟、几何参考限幅、实际碰撞/净空/力矩门禁保留。**2秒启动诊断8/8未触发安全终止，均到第二个路点**；包括终止步的最大力矩比0.970760，完整PUSH仍0/8（8次2秒超时，缺失0）。报告SHA256 `0d52b934816e68bee066163bb1b60d0216d07a460242117dce073f4b44d8a0f2`，计划SHA256 `0b77268557e4ae33023fc96b0195e04925b815c57ee03e1ac3c916293ebdd822`；这只是该种子启动进展，不是已解决所有初态或完整推箱。

v201的`original-start-48s/`完整诊断已结束：**完整0/8、缺失0，8例均在17.04～17.54秒因实际表面净空低于35mm终止**，接近索引15～16；臂力矩终止0，含终止步最大力矩比0.970760，箱体未实际推进。报告SHA256 `dc321974ee56b6988d4e8fb100f43dd36b5df95e935821125e41c7dbe422d180`。这证明该配对样本的启动力矩问题已被滤波越过，但接近碰撞风险仍未解决；没有完整推箱录像可交付。60ms最终命令滤波属于新控制契约，须匹配v201/v202源码。v201工作流1103151及同步监听已完成退出，原失败报告保留，后续v202已停止，由本页顶部v203继续。

中间权重独立检查`intermediate-training-audit.json`通过：229项冻结源码哈希和原model199哈希一致，实测物理1kg/0.15；两组最近已保存checkpoint为model512/model256，参数均有限，臂特征、臂输出和速度输出确实更新，存储的腿输出层与腿部标准差未变化。实际腿输出仍必须由冻结actor hook提供，不能仅用未变化的输出层替代该契约。检查只证明训练执行和来源一致，不证明PUSH成功。

前置seed7980、4环境、64迭代冒烟正常结束，通过的是“至少2秒轨迹/第二路点”的训练进展检查，最长17.3秒、索引15，8个训练终态安全成功0。其固定checkpoint在严格8环境评估中为**0/8，缺失0，8例均为臂力矩门禁失败**；报告SHA256 `fab063e4a64f5356f3f12f40ee55ac452b2015aed0381f7d164d996c54cb4332`。独立`terminal-effort-audit.json`核对：env0/3/5/6在0.02秒、其余在0.32秒触发joint5门禁，终态最大力矩比1.0；原报告标量0.975729仅采样步前，漏了最后终止步，不能据此宣称无饱和。原`joint_motion`已包含终止步、各例joint5超阈值0.02秒；原报告保留，审计补充终态峰值，没有修改成功判定或初始化门槛。后续最终评估也须合并终态峰值，下一轮评估器修订再统一修正标量采样。

补充启动负载诊断`startup-load-audit.json`：在原8个失败姿态，用历史已校验质量/质心模型做零速度静态计算，joint5重力负载约2.97～3.01N·m、全部臂关节静态负载比最高0.616；实测失败力矩却为4.97～5.00N·m。因此记录不支持“轻载箱仍太重”或“静态重力已超过5N·m限额”的解释。当前几何参考先平滑，再叠加约−0.10rad的joint5重力补偿；该最终目标偏置没有被前面的参考速度限幅覆盖，是下一轮启动瞬态检查的具体对象。此为静态归因线索，尚未证明动态修复；不改正在训练的冻结源码，不取消含初始化力矩门禁。

接手先读`workflow-state.json`、`training-progress.json`和实际进程。远端根目录为`/path/to/artifacts/go2-piper/sim2sim-current-20261008-a/`，本地同名目录在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/`。**当前开发结果及录像以本页顶部为准：v212精简路径30/32但有2次非法手接触，v210旧路径独立批31/32、32/32且有1次初始化力矩失败。尚无完整安全交付验收通过结论。**

训练设计修正：旧v117只在接触面就绪后学习，旧env0在7.32秒、尚未完成接近时已低于35mm，12.46秒净空最低19.214mm。v198沿用v197，将机械臂学习覆盖接近全过程，并采用独立可学习特征网络；腿部输出来自独立冻结model199，避免v116共享特征更新损坏腿部策略。**新接口226→19**：12维冻结腿部输出、6维有界机械臂位置修正、1维机械臂速度系数。速度系数为sigmoid，范围0～1，仅降低原关节参考速度上限，初始0.2；允许策略学习何时减速。6维修正仍为0.20*tanh，位于原软限位、参考平滑和几何屏障之前。必须使用匹配`install_frozen_legs`加载器与原model199 SHA256 `b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721`，不能交给旧226→12/18运行时。

静态检查通过：64组随机观测、100次Adam更新后，腿部输出仍与原actor逐值相同，机械臂特征层确实更新，训练/评估加载结果逐值一致。 新增违规锁存/奖励检查通过：违规后恢复低负载仍不能取得完成奖励；仅被重置的环境清除历史，其他环境保留；评估仍即时触发0.98门槛（`safety-credit-check.json`）。`plan.json` SHA256 `f50e0c01fffb31b64d0fd9f562a7afca54b51125a544619d45fc00e818b6a2cf`冻结匹配源码；静态检查不构成物理成功。原路点到位/速度条件、PD、延迟、原生自碰、合法接触和停稳条件保留。初始化仅将原生重置后的关节目标设为实测随机初态q、速度/额外力矩目标置零，未移动根/关节状态或改延迟值；物理效果必须继续验证。

每个20ms控制步物理更新后、重置前测量实际表面净空；低于35mm在训练与评估中都立即失败。**v198的训练采样与最终验收明确区分：**训练保留原执行器硬限幅，臂力矩比达到0.98时逐步惩罚并锁存整条回合不安全，允许继续采集接近/推箱轨迹；即使后来到达目标，也不给完成奖励，不计入`safe_full_task_successes`。原生碰撞、姿态、非法接触等仍立即终止。最终评估维持0.98即刻失败，没有初始化宽限或删去早期样本。该区别是为避免所有训练轨迹在0.3秒截断，不能将训练的`native_goal_reaches`当成安全成功；启动饱和问题仍待训练/控制证据解决。全程（含初始化）记录全关节饱和、少于三足支撑、腾空、竖直速度、单足接触合力峰及足力向量和峰；这是控制步遥测，不是物理子步安全证明。训练与评估均读取PhysX质量/材质，若不是1kg/0.15立即退出。正式Isaac/MuJoCo两组未用32验收尚未开始；实机暂停。

**v195/v196/v197被冒烟拒绝，原件保留，均未进入长训。** v195新增早期力矩门禁后，回合平均0.276秒即结束。v196修正重置目标后，初期记录竖直速度峰从0.894降至0.580m/s、单足力峰从291.65降至101.24N（不同训练种子，仅诊断，不能视为受控性能提升），仍在约0.28～0.36秒、第一路点触及joint3/joint5限额。原固定参考速度使小幅位置残差无法充分减速，因此v197引入速度学习输出；v197的速度输出与神经网络确实更新，但前832个控制步仍最长0.32秒、路点索引1，未产生后续任务样本。因此v198只在训练中延后力矩违规回合的重置，保留整回合违规标记与最终评估门槛。三轮日志/早停状态留远端，不将停止称为正常完成或安全通过。

v198/v201旧工作流和同步均已结束，旧`gpu1-queue.json`等待状态为历史快照；v202因路径冲突也已停止，v203冒烟/评估已结束，v205/v206也已结束；v207也已结束；v209也已结束；当前v210验证进程和同步以本页顶部为准。大报告、原始日志和中间权重留远端，Git只按实质里程碑合并推送。

**v194已结束：实际3kg/0.3，4个选中环境都将箱子推了4.54～5.07cm，但仅env2/4满足阶段末段保持，阶段2/4。** env0/3因后足负载分配不足停止；8环境终态齐全、原生安全失败0，完整0.6m任务仍0/8、8次超时。报告SHA256 `026994db5cf796022ba00b2faf78074a31805abb884e9e019d47ac646832a672`。24秒原速视频SHA256 `e179229fd84650bfc6aa9ed2b53cb44bfc9f69d37798277fbd61b1cb81d0a560`，画面是env0阶段失败例。视频动作小主要由于5cm阶段目标限制；实测手力约9～10N，与3kg/0.3约8.83N滑动阻力相符，不能说箱子太重或完整推箱已完成。

v194的80%增量外力矩补偿改善了受载后接触迁移，原PD不变；0/4/8.829/10/12N的20个静态点通过，20～22N拒绝报告保留。该短程控制器及v193失败后保持作为阶段证据保留；v195采用完整任务训练，未把其5cm目标或保存接触初态冒充完整起点。

2026-10-12用户指出旧录像长时间准备、接触后不推、机身也不前顶；后续重点改为实际机身前推和箱体位移，并缩短准备流程。用户随后明确把箱子改为**3kg、静摩擦0.3、动摩擦0.3**，恢复系数0，地面摩擦1.0、组合方式min不变；水平摩擦力估算约8.83N。旧录像v154对应5kg/0.4，不能作为新参数录像或验收证据。

`push-contact-reserve-v189/`已结束：已用3701、8环境、16秒新场景，env0/2/3/4连续接触保持约7.86～7.96秒，阶段4/8；另4例未达到新增1.5N连续0.2秒锁定条件，原生安全终止0、终态缺失0。报告SHA256 `1d67258bd73b7582c4a1efb5b01d00c5779439e1286f69ad44aad4e0d5a4cbbb`。条件队列v190已按失败条件退出，**未启动原起点物理复测**，不继续等旧队列。

`push-body-drive-v191/`已结束且被参数审计拒绝：虽然启动命令写3kg/0.3，冻结`safe_retraining.configure()`在参数应用之后把质量/摩擦重新设为5kg/0.4，PhysX实际值8环境均为5kg/0.4。此前“新参数已用于运行”的确认不准确；该轮与录像必须标记**实际5kg/0.4，不符合本次请求**。原始退出状态`valid=false`保留，独立结果见`result-audit.json`，报告SHA256 `e3d9bfbafc7998efe7934f84c8440b83683f0f87d9f81408e9ba37e8918fe27f`。

v191的4个选中环境env0/2/3/4均重新确认连续接触后开始前顶，实际机身最大前移11.76/14.98/15.93/21.26mm，箱体最大位移不足0.05mm，短程阶段0/4。四例在8.64～9.50秒触发停止，最低保护净空53.16～53.85mm，未守住55mm阶段门槛；env0另触发原生`invalid_hand_contact`，其余7例超时。终态8例齐全，记录始终至少三足支撑、腾空0、含初始化力矩饱和0，最大力矩比0.667708，最大竖直速度0.003806m/s。不能称安全PUSH已完成。

修正轮`push-body-physics-v192/`复用同一控制器和已用3701、8环境、24秒阶段，仅在冻结训练配置完成之后应用用户指定3kg/0.3；物理生成后、推进/录像前读取PhysX实际质量与材质，写`startup-physics.json`，不匹配立即退出。其他物理契约及35mm原生屏障、55mm支撑保持门槛保留。4个选中环境的短程目标仍为实际箱体前移至少1cm并末段稳定2秒；另外4个环境保持作为对照。这不是完整0.6m PUSH、原起点或sim2sim验收。

5cm机身/腿部静态可行性检查包含0/10/20/22N假设反力，保护净空最低64.08mm、机械臂最大力矩比0.893203，但未覆盖真实受力下的机械臂变形，不能证明动态净空或实际推箱成功。v192已由资源队列1091488启动，launcher1091499；启动PhysX实测8环境质量均3.0kg，静/动摩擦均0.3000000119，参数检查通过（`startup-physics.json`已同步本地），该轮现已结束，结果见下文。本地完成同步监听2848254；接手先核对实际进程和`queue-state.json`，避免重复启动。小型代码/计划/结果同步本地，原始大报告留远端，Git按实质里程碑合并推送。

**v192已完成：实际3kg/0.3，短程0/4通过。** 8环境终态齐全，env0在8.42秒触发`invalid_hand_contact`；env2/3/4触发55mm净空停止，实测最低分别53.77/53.48/54.75mm。选中环境机身最大前移8.39/14.13/15.51/23.65mm，箱体最大前移0.215/0.088/0.102/5.596mm，均未达到1cm且稳定2秒要求。始终至少三足支撑、腾空0，含初始化力矩饱和0，最大力矩比0.675092、竖直速度峰0.001645m/s。报告SHA256 `5cb26b78a5b7ab727d12e21706d621ac1aa23ffbb617154a324eec3ca4183cf6`。退出状态`valid=true`仅说明参数/来源/报告完整性通过，`batch_stage_passed=false`，不是PUSH成功。

v192原速录像`original-speed-body-push.mp4`已同步本地，24秒、25fps、600帧、1280×720，全帧解码通过、本地/远端SHA256一致：`cf9b27e34d5c66d6be1bb4f844933ce04936da6f48e82fad58e24ace6ad15098`。镜头对应env0，并非5.596mm的env4；env0在8.42秒安全终止，后续帧不能当作仍在主动推箱。该录像从已接触状态开始，无原起点准备流程。下一步检查受力后的关节偏转和机械臂承力补偿，保持原门禁，不重复调等待时间。暂无后续物理试验启动。

**录像与统计边界纠正（用户指出姿态失稳）：** v192完整视频后半段确实倒伏。逐帧复核显示8.40秒仍在原接触姿态，8.44秒机器人和箱子已被环境重置；`StageHold`没有随环境重置，继续发出上一场景的关节目标。原统计因`quota.active=false`在8.42秒截止，终止前最大倾角2.826°、角速度峰0.009704rad/s，不能据此宣称整段录像姿态稳定。后半段不是有效任务轨迹，也不能忽略其暴露的重置/停止控制问题；记录见`reset-boundary-audit.json`与`reset-boundary-review.jpg`。

`push-terminal-hold-v193/`专门验证失败后是否仍失稳：沿用v192实际3kg/0.3、控制器与种子，保留原终止判据和首次失败快照；首次终止后不重置根/关节/箱体状态，保持最后实际关节目标，在真实物理下再观察3秒。视频明确标注前推/失败后保持，终止后姿态、足力、净空、力矩和目标连续性单独记录。其他环境因此可能有意未结束，必须如实报告缺失，不能当作完整批量验收。审计逐字段核对env0首次失败前轨迹是否与v192相同。队列1093648、launcher1093946已结束，GPU1世界模型1093008未干预。

**v193停止诊断已完成，env0失败后保持3秒通过本轮稳定检查。** 首次失败仍是8.42秒`invalid_hand_contact`，此前env0完整轨迹与v192逐字段完全一致。保留真实物理状态、最后关节目标后连续3秒四足>8N，腾空0，目标变化0rad，机身漂移最大0.855mm、倾角最大2.515°、最低机身高度239.61mm、竖直速度峰0.001251m/s、最大力矩比0.651767、最低保护净空55.588mm、单足合力峰88.517N。该结果支持旧录像后半段倒伏来自重置与阶段目标不匹配；仅验证3秒停止保持，不构成长期保持或推箱成功。主动推箱首次失败没有修复。

该轮有意在env0首次终止后3秒结束，共1例已完成失败、另外7例未结束，**必须报告缺失7，不能作为完整批量或sim2sim验收**。报告SHA256 `0e8c509ef1d106bc384eac7132e3df2375dcf8cdd5a92f8a233246994b197df2`，匹配原速视频11.44秒/25fps/286帧，SHA256 `9ca2eb6e1081a5f0f2b998bf0901afadc18db8345c87b6a932e3d2873ae1d7b3`。视频已全帧解码、6个关键帧检查并核对本地/远端哈希，画面标明失败后保持；没有宣称连续播放检查。小型结果与视频已同步本地。后续控制候选保留失败后停止观测，继续处理受力关节偏转、真实合法接触和净空，不能只裁剪倒伏画面或放松门禁。该诊断已结束；后续运行状态见本页顶部。

#### 前置接触诊断与证据

2026-10-12，v179原起点机身跟踪修正已结束，独立审计8/8通过；保留该成功路径，不重复启动。短程入口v180初始化保持0/8，env0启动后真实竖直速度约0.415m/s、机身漂移25.9mm；原因检查发现写入根/关节状态不会清空安装版本`DelayedPDActuator`的目标历史。原报告SHA256 `3fcb2861243ecce5bdb72c55c4fe8b4876ccdb0d1f085c44431487281f8e8909`，失败证据保留。

`push-stage-buffer-init-v182/`已完成已用seed3701、8环境、6秒阶段初始化检查，**8/8通过**。用保存的稳定目标初始化延迟缓存，逐环境延迟值、原PD、物理与控制元数据均未改变。每环境299个物理步后接触样本均至少三足支撑、腾空0；连续健康保持5.98秒，竖直速度绝对峰0.000073875m/s、机身漂移最大0.01456mm、记录最小净空60.00865mm、最大力矩限额比0.710718；单足合力峰78.0416N、四足接触向量和峰213.6122N。t0物理步前接触读数另列，力矩和净空含初始化。终态齐全、原生安全终止0、完整PUSH0/8。报告SHA256 `d333f5e5f0669bc77d8ade43d6fc50e239dc8f22c7249c6f88b4cf8d3be14dbd`。

随后`push-short-transfer-v181/`的20秒短程机身转移仅**4/8通过**（env2/4/6/7）。另外4例在约12.12～12.74秒触及55mm保持门禁，实际最低54.672～54.755mm；原生安全终止0、终态缺失0、记录始终至少三足支撑且腾空0。这表明仅恢复物理姿态与延迟缓存，尚未复现完整流程的足端锚点、机身参考及控制器历史；具体差异仍待逐项确认。不能将短程结果替代原起点v179的8/8，不能宣称已实现等价提速，也不因此修改已通过的完整路径。报告SHA256 `0a55c24f7697b8e01b0881d65acd0379b06223d8cdaeaf0f4cf70a5aa267f232`。上述两轮摘要与退出状态均已同步本地，旧队列1082822/1082823及物理启动器均已退出。

**已完成：`push-physical-recontact-v185/`实际重新接触0/8。** 原起点、已用3701、8环境、160秒延长窗口；8例均到达规划终点，但合法接触全部为0，最大记录手箱合力仅0.144042N，低于原判据要求的法向反力>1N。末端位置跟踪误差仅0.051～0.162mm，因此不能通过延长原位置保持来宣布接触成功。全过程原生安全终止0、缺失0；重新接触阶段6000个环境控制采样全部至少三足支撑、腾空0，最低净空55.22585mm、最大力矩比0.627311、竖直速度绝对峰0.000420582m/s，单足合力峰92.8441N、四足接触向量和峰213.6986N。含初始化饱和仍逐关节保留（joint3最大0.16秒、joint5最大0.24秒）。env0前145秒和全8环境完整机身转移轨迹与v179严格一致，原成功路径保留。launcher1085046/Isaac1085048均已退出。

v185报告SHA256 `dca1b0b6e7ea319a3cf421bdeca759fb9b22323b22aa3fd9677400ee0f2b3f84`，`stage-summary.json`与`contact-failure-audit.json`已同步本地。全程0/8是没有建立合法接触，不是机身转移失败；不能把几何到位记成接触或完整推箱成功。

**已完成：`push-bounded-contact-v186/`受限接近仍0/8。** 原起点、已用3701、8环境、170秒窗口；最大手箱力0.290146N，没有合法接触，无安全终止或终态缺失。全8环境保留v179完整机身转移轨迹，env0前145秒逐字段一致。重新接触阶段10000个环境控制样本均至少三足支撑、腾空0；最小净空55.22585mm、最大力矩比0.628256、最大竖直速度0.000420582m/s，单足合力峰92.8441N、四足向量和峰213.6986N；含初始化饱和仍为joint3最大0.16秒、joint5最大0.24秒。原报告SHA256 `dc49880510a6fc7d9492a8fce659fbd1fd58f4b56d1a5e200d7e0d964e0d4f51`。launcher1086110与Isaac1086112均已退出。

`normal-error-audit.json`对8个实际终态分解误差：整体误差0.507～0.545mm，全部超过v186新增的0.5mm接近推进条件，导致计划最多3mm的延伸实际只到0.327～0.717mm。切向误差仅0.213～0.321mm、法向误差0.424～0.470mm；定位到该新增位置条件与受力接近存在冲突。这不是物理安全门禁触发，也不能降低>1N合法接触条件把本批改判成功。摘要、退出状态和误差审计已同步本地。

**已完成：`push-normal-contact-v187/`重新接触0/8。** 原起点、已用3701、8环境、170秒，所有终态齐全、安全终止0，v179机身转移全8轨迹及env0前145秒仍完全保留。拆分法向/切向误差后延伸到0.729～1.193mm，但8例又均停在新增0.5mm切向推进条件，终态切向误差0.550～0.670mm，最大手箱力仅0.582488N。实测审计在`tangent-error-audit.json`，报告SHA256 `37cdfffe86a4e6034cb9c5659e7e87a39a7ecf1d6c34e57cc948b64ca5f6e246`。重新接触阶段10000个环境控制样本全部至少三足支撑、腾空0，最小净空55.22585mm、最大力矩比0.630389、竖直速度绝对峰0.000420582m/s、单足合力峰92.8441N、四足接触向量和峰213.6986N；初始化饱和仍逐关节保留。原launcher1087070和Isaac1087072已退出，不重复启动。

**短程诊断v188b已完成：真实接触8/8，连续保持0/8。** `push-short-contact-v188b/`直接恢复v185实测稳定终态及保存的原PD目标，并按v182方式初始化延迟缓存，逐环境原延迟值不变。已用3701、8环境、16秒新场景；重新实测约3秒四足稳定后开始接近，8例均于8.26～8.84秒达到原合法接触条件。锁定时参考只延伸2.329～2.623mm，最高接触力1.021～1.079N；锁定后末态法向力回落至0.848～1.007N，最长连续合法健康保持仅0.02～0.18秒，严格阶段仍0/8。失败定位为刚跨越1N判据就锁定，缺少保持余量；没有降低合法接触阈值。

v188b独立逐行审计已完成，终态缺失0、原生安全终止0；6392个物理步后环境接触样本全部至少三足支撑，腾空0，最低记录净空60.09207mm、最大力矩比0.637320、竖直速度峰0.000518698m/s、单足合力峰92.7151N、四足向量和峰213.6539N。最大机身漂移2.7581mm、足部漂移0.2953mm；力矩/净空含初始化，详细逐关节饱和见摘要。报告SHA256 `2821ff656d0d405dc3462ae4979368eb5cce97378c519914a91cdeba635cb8b6`，独立`result-audit.json`记录实测运行耗时371.6秒。短程腿部保持保存的PD目标，未运行完整v179机身控制器，**不是等价重放、原起点成功、完整PUSH或sim2sim验收**。

初次v188启动器在生成源码时因异常处理模板缩进匹配失败，未启动物理；失败记录保留。v188b修正生成方式后完成以上物理检查，原launcher1088012及Isaac1088014已退出。短程初始化保持与连续接触分别核验，不能把8例首次接触标成8例接触保持成功。

**已结束v189，v190未放行（过程配置归档）：** `push-contact-reserve-v189/`沿用v188b短程流程，改为真实合法接触且法向反力≥1.5N连续0.2秒才锁定，推进力上限1.6N；参考法向延伸最多5mm、8秒五次平滑。仍保留整体跟踪<4mm、姿态误差<0.04rad、35mm原生屏障、55mm保持、原PD/延迟/执行器/落脚/停稳、真实合法接触>1N及20N合力停止条件。5mm仅为命令上限，不是实际穿透许可。

已重新完成5mm参考路径的静态几何、0/1/5/10/20N受载和90%力矩/支撑余量检查，8/8通过，最小保护净空60.22792mm、最大机械臂静态力矩比0.894536；静态通过不等于物理通过。v189的launcher1088492及监听2825217已结束。v189生成独立逐行审计后，只有8/8连续保持通过、无缺失且安全检查通过，原条件队列1088483才允许`push-full-contact-reserve-v190/`回到保留的完整原起点流程进行170秒、已用3701/8环境复测；否则记录失败并停止该衔接，不按时间自动放行。

v190接触控制接口检查通过：1.1N不会提前锁定，1.7N真实合法接触持续0.2秒后锁定；原4mm误差及执行器停止分支保留。辅助源码SHA256 `251a8b11d8c80def3dd0e1ea2c44a16f58d89281ef3d18251ef8365f46885b82`，启动前核对107个冻结源码、v179依赖、v189报告与静态检查。结果必须逐字段核对env0前145秒及全8机身转移轨迹与v179一致。v190完成监听2825218，小型摘要/退出/失败状态同步本地；两轮都不执行持续推箱，不是原12秒验收。GPU1世界模型1087410继续运行，接手先检查实际进程及队列状态，避免重复启动。当前完整安全PUSH和安全版sim2sim仍未通过，本轮不新增Git冗余提交。

训练范围也已重新核对：v117只训练机械臂六个输出行，特征网络与腿部网络冻结；不能将该权重称为完整安全PUSH已训好。本轮没有启动新的训练。

#### 当前主线：真实退开8/8、机身转移8/8；推进重新接触，完整推箱未完成

截至2026-10-12，v151收紧近箱机身调整幅度后准备检查8/8通过，另外7例已通过轨迹全部保留；v152实际姿态路径审计8/8通过，自动衔接的v153也实现**8/8合法接触并持续健康保持9.38～12.46秒**，无安全终止或终态缺失。该阶段接触后最大力矩限额比≤0.760，最小记录净空62.046mm。仍不是完整PUSH：箱体位移最大约0.18mm，原任务0/8，当前是120秒延长窗口的接触保持诊断。v154原速录像已完成，3000帧完整解码通过，env0轨迹与v153完全相同；已检查12个关键帧并同步本地。v155进一步发现该接触构型在20N持续反力假设下7/8超过执行器力矩限额、8/8未达到90%设计余量，因此尚未释放行走推进；v156/157已找到并独立核对8个新承力端点，20N假设反力下均有90%静态力矩余量；v170已完成8/8规划路径的平滑/稠密几何与时序检查；v175全8环境真实退开与停稳已通过，v179机身转移也已通过8/8；重新接触和动态推箱尚未通过，原执行器限额不变。未用种子及sim2sim正式验收仍未通过。

v125已在既有远端Isaac完成原起点、已用seed3701、8环境的准备位保持试验：沿原路径运行至索引13路点后保持，8/8均满足独立的准备保持条件；env0停止前288个控制步与原报告逐字段相同。首次进入保持在5.62～5.84秒，末段连续稳定5.66～5.84秒，保持阶段无力矩饱和，最大力矩限额比0.6169以下，最小记录净空76.55mm，单足最小竖直力27.44N。原报告仍保留含初始化遥测，不能将保持阶段的无饱和扩展为全程无饱和。

此试验没有移动到新的承力构型，也没有推箱：原PUSH指标仍为0/8、8次12秒超时、终态缺失0、安全失败0。8/8只表示原路径准备位可稳定停留，不能当作PUSH成功率或12秒验收。实现只重复索引13路点并暂停后续推进，原腿部保持、关节参考处理及物理终止条件保留。产物`push-entry-hold-v125/stage-summary.json` SHA256为`ba6b5b2cb5dd6ba71529db51642f6e98f514d38f299468fa43ec80be13e441b8`；原报告SHA256为`bbc477bd3bc5112fad2fb7a9ae5be452f2d43eb73ad64e28e3b8f38a7837e456`。

v126的`push-preunload-v126/`准备阶段试验已结束：原起点、已用seed3701、8环境、24秒，8条终态齐全；原任务0/8，7次超时、1次`bad_orientation`（env4约13.48秒失稳），因此整批卸载试验不通过。仅env6在末段连续8.62秒满足卸载条件，其余环境主要因机身振荡未达到平稳门禁。转移前env0共414步与v125相同；转移阶段无记录力矩饱和，最小记录净空76.55mm，但这些指标不能抵消姿态失稳。阶段摘要SHA256为`0c621abc5b480eabeec5da45d16aed0a388e6863bad2ccac272c1b9135236d2c`，原报告SHA256为`c3af3a13349130c052eb7adffd4e21af167ba05648252a4e1246121f44f3873a`。失败证据保留，不能将个别环境卸载成功计为PUSH成功。

v127的`push-preunload-damping-v127/`已结束：原起点、已用seed3701、8环境、24秒，终态齐全；4个环境末段连续11.78～12.18秒满足卸载条件，另4个失败（3次`bad_orientation`、1次`base_contact`），整批卸载仍不通过，原PUSH仍0/8。此版锁定机身目标，采用2秒五次平滑接管及已有水平速度反馈，水平加速度命令限于0.4m/s²，但未解决全部环境的振荡。env0在约10.8秒后速度和足力振荡逐渐放大；env3转移阶段有9个控制采样达到饱和阈值，最大力矩限额比1.0。不能仅凭4个稳定环境宣布修复。转移前env0共414步与v125相同。报告SHA256为`ae2e755c4be16b55d435cf0260935e966761ed7f211181087dd21d6a3ada2502`，阶段摘要SHA256为`aea15605ddff6346dee68d7e0be4fc80ea04c67fa2f3d0ae5b30ca570b9eca77`，摘要及退出状态已同步本地。

`push-transfer-isolation-v128/`四足承重对照已完成：保持v127机身转移和控制接管，仅将卸载比例固定为零，原起点、已用seed3701、8环境、24秒。8/8均通过独立的四足转移稳定条件，末段连续稳定13.26～13.66秒，终态缺失0、安全终止0；原PUSH为0/8、8次超时，尚未摆脚或推箱。转移阶段无记录饱和，最大力矩限额比0.5908以下，实际单足最小竖直力29.09N，记录机身竖直速度绝对峰0.00730m/s以下，全部控制采样至少三足>8N、全足≤2N的腾空采样0，四足竖直力之和峰215.22N。初始化饱和单独保留在`telemetry-audit.json`；env0含初始化的单足接触合力峰119.82N、四足接触向量和模长峰326.67N。这些均为控制频率采样，不能称为物理子步峰。原报告SHA256为`ce8dd2276d3ad1667db6e2735c765bfa424848fac6418ea953a70f6838b943e9`，阶段摘要SHA256为`584e89922bdf06c51d141e7948d6754b8f84cadb5e9256d4bbb4f9ca39721037`。

`push-unload-after-settle-v129/`已完成，同一已用seed3701、8环境、原起点24秒。机身到位且原支撑、姿态和速度条件连续满足2秒后开始卸载，随后沿用v127实际足力和释放判据，8/8均满足卸载稳定条件。开始卸载为12.34～12.74秒，末段连续卸载稳定9.78～10.18秒；终态缺失0、安全终止0，原PUSH仍0/8、8次超时。转移阶段无记录饱和，最大力矩限额比0.5908以下；其他三足最小竖直力25.32N，6310个环境控制采样均至少三足>8N、记录腾空0，竖直速度峰0.00730m/s以下，四足竖直力之和峰215.22N。初始化逐关节饱和另列于`telemetry-audit.json`，不能称全程无饱和。env0卸载前629步与v128逐字段相同，支持本批次中分开完成机身转移和卸载可避免此前失稳；尚未进行新种子鲁棒性验收。报告SHA256为`950946563bcfe9c7b9f14db99e667561d4b11428ff50b530790987426ea9bbb5`，阶段摘要SHA256为`f4579821300c410da2e0f85f391b9e635107b0c3866d02ae653c0b7573fc37d4`。

`push-single-step-v130/`已完成原起点、已用seed3701、8环境、24秒单步诊断。实际卸载稳定0.2秒后，前左足执行前移3cm、抬高3cm的4秒分段五次平滑参考；8/8观察到真实离地并完成参考路径，但完整落脚重载阶段**0/8通过**。7个环境末态落点水平误差6.44～7.50mm，env0重载后出现增长振荡，末态落点偏差84.27mm；各环境最长连续重载停稳仅0.06～1.94秒，没有达到2秒条件。终态8/8、缺失0、原安全终止0，原PUSH0/8、8次超时；转移阶段无记录力矩饱和，不能据此认定稳态安全。起步前env0共714步与v129一致。报告SHA256为`f0197c2e4919819dcd4f63668d64a4e1bb4558d37f8bc0405a57e5b30bdedaa2`，阶段摘要SHA256为`7067d3718767bc3e3e958fe0fe2c2d04fe56b7bf916ab5adb7a90ea98b474d6d`，遥测及含初始化逐关节饱和保存在`telemetry-audit.json`。

v130落脚探测累积向下9.52～10.00mm参考偏移，恢复承重后仍保持该偏移。`push-landing-anchor-v131/`尝试实测落点参考平滑接管，30秒延长单步诊断**失败并弃用**：7/8触发`bad_orientation`，仅env7最终连续停稳7.04秒；整批阶段0/8通过，原PUSH0/8，终态缺失0。env0切换前1055个控制步与v130一致，无法支持仅消除探测偏移即可修复的假设。报告SHA256为`2bf58a82dc92f03b6c1204ff36f2ad7ae6c57cb2b0c5a0d50edc00be617d9473`，阶段摘要SHA256为`80012b480c24e5d4681840105e9cd4c521783b6b658d962842edbd39145d81fb`。`stage_state_at24s`存的是24秒前最近采样，提前终止环境必须结合该条时间和终态读取，不能当作其仍存活至24秒。

继续核对发现v130/v131的0.6秒线性重载结束时，env0限速后的关节参考仍在运动：首次重载达到1时最大参考速度分别0.518/0.673rad/s，后续出现参考滞后和机身振荡，证据在`push-smooth-reload-v132/reload-reference-audit.json`。v132回到v130足端参考，只将实测接触后的重载改为1.5秒五次平滑过渡，首尾参考比例的速度、加速度为零；接触失效仍立即取消分配给该足的支撑载荷，足力、停稳、限速和物理终止门禁不变。保留原准备、卸载和摆脚轨迹，env0重载前1055步与v130逐字段一致。

`push-smooth-reload-v132/`现已完成**已用seed3701、8环境、30秒延长单步诊断，8/8通过单足阶段**：实际水平前移28.57～28.93mm，落点水平误差6.42～7.50mm，重载后末段连续平稳6.94～7.54秒。终态缺失0、安全终止0；转移后无记录力矩饱和，最大力矩限额比0.5908以下，8710个环境控制采样均至少三足>8N、记录腾空0，竖直速度绝对峰0.00730m/s以下，单足接触合力峰118.51N以下、四足接触向量和模长峰215.22N。初始化逐关节饱和另列`telemetry-audit.json`，这些不是物理子步峰。**24秒时连续重载停稳仅0.94～1.54秒，未满足2秒门槛**；原PUSH仍0/8、8次超时，不能称24秒单步通过、完整PUSH通过或sim2sim通过。报告SHA256为`4b39a29c384bf18455fd57e40a653e1c2a4ad105502cc7f88093017ed00f8c7a`，阶段摘要SHA256为`7b791839fbe5377db962c66b06329ae6285ec0328bcd9cece76b3a563c374548`。

`push-single-step-confirm-v133/`已完成固定v132评估器与辅助源码的两组**已用种子**3701/2701、各32环境、原起点30秒单足阶段确认，均为**32/32阶段通过**，两组终态齐全、安全终止0，物理/资产/控制契约、107个冻结源码及v132辅助源码哈希匹配。它们不进行推箱，原PUSH各0/32、32次超时，不是未用种子正式验收，也不是sim2sim通过。

| 已用种子 | 30秒末段连续重载稳定 | 24秒前最近连续稳定 | 转移后最大力矩限额比 | 转移后竖直速度绝对峰 | 转移后单足合力峰 |
| --- | --- | --- | --- | --- | --- |
| 3701 | 6.40～7.86秒 | 0.40～1.86秒 | 0.6005以下 | 0.01051m/s以下 | 121.52N以下 |
| 2701 | 5.80～7.70秒 | 0～1.70秒 | 0.5997以下 | 0.00985m/s以下 | 122.04N以下 |

两组分别34728/34821个转移后环境控制采样均至少三足>8N，记录腾空0、转移后力矩饱和0；四足接触向量和模长峰分别215.90/216.02N以下。初始化逐关节饱和单独记录于各组`telemetry-audit.json`，以上均非物理子步峰。**24秒时两组均尚未满足连续停稳2秒门槛**。seed3701报告/阶段摘要SHA256分别为`bdeda5d5e12af85cedc33617fd1508f0564c27deb4ba95a36e1eb959e7c4b15f` / `c1752c6db1ec0aafa7885d779d70a5d4fbb677a0cc8b715be3d4abaa0e3020e8`；seed2701分别为`2255a4754484141f8708843f892cdf954f81f7323ddc06c9e3447485590b0da8` / `581f0e8ae7011b7321eb64f0567385c6ad8ca5ed8a097850cee1a57ccec28edd`。计划、摘要与遥测审计已同步本地，原始报告与轨迹留远端。

`push-single-step-video-v134/video-used3701-8env/`已完成匹配v132源码的原速**3cm单足阶段**录像，8/8阶段通过，env0逐字段轨迹与无录像v132完全相同，物理契约匹配。`original-speed-stage-only.mp4`为25fps、750帧、30秒，SHA256为`7a50a5bc1fdff39568f6eb96d860af1581d6d7610737dc39d0604c4c67019762`；完整解码并检查12个关键帧，看到机械臂保持准备姿态、单前足移动及末段停稳，未执行推箱。这不等于连续视觉播放检查或仅凭视频证明无碰撞。开头有1个黑帧（0.04秒），原文件未裁剪。视频、关键帧及审计已同步本地，原始大报告仍留远端。录像报告SHA256为`3d9b11ecd2889b7e7d194f9865d053c2057f5f8667e13b326978986f95a5d02f`。

`push-step-eight-cm-v135/`将前左足参考前移由3cm扩大至8cm，其余准备、卸载、抬高3cm、4秒摆脚、平滑重载及安全门禁保留，已用seed3701、8环境、30秒单足诊断**8/8通过**。实际水平前移78.14～79.01mm，落点误差6.64～7.73mm，末段连续重载平稳6.62～7.20秒；终态缺失0、安全终止0、转移后记录力矩饱和0、最大力矩限额比0.5908以下。24秒前最近连续停稳仅0.62～1.20秒，不能算24秒阶段通过；原PUSH仍0/8、8次超时。起步前轨迹与保留路径一致。报告SHA256为`593d300c3aadb4aeb0f9bd1b63bf2dc385f0e88edcfea02495969b40e62dd8b6`，阶段摘要SHA256为`99cc1f44fe1e999d9aeb8184f4eb6deaa515c60d7133aa40f502ebc42c090fca`。尚未对8cm版进行双32环境检查，上述录像对应3cm版。

`push-two-front-steps-v136/`已完成原起点、已用seed3701、8环境、**60秒双前足阶段诊断，8/8通过**，终态齐全、安全终止0；原PUSH仍0/8、8次超时。组合两份同一冻结v135单足控制，前左足完成8cm步并实测重载稳定2秒后，重新确认四足>8N、机身平稳、力矩与净空，再切换前右足。接管发生在24.82～25.40秒，最大关节参考变化仅1.49e-8rad，接管参考加速度变化≤0.02981rad/s²；接管前第一步轨迹与v135一致。前右足实际水平前移77.67～79.53mm，两前足最终落点误差均≤7.67mm，末段连续重载平稳19.82～20.68秒。

v136两段分别6768/13942个环境控制采样均至少三足>8N，记录腾空0，两段转移后饱和0、无无效控制命令；机身竖直速度绝对峰分别0.00730/0.00601m/s以下，单足合力峰分别118.51/109.73N以下。完整接触合力和含初始化逐关节饱和见`telemetry-audit.json`及阶段摘要，均为控制采样，不是物理子步峰。报告SHA256为`3fe5fdacae9cb759388af1d13ef51cb564acfc162b5ef37f2122a5879880ba7d`，阶段摘要SHA256为`288a537dd0c4e635ddc5e119ba74dd365bbb81365cd73f545a409790956d1af8`。这不等于30秒或完整PUSH验收，尚未做双前足版本的两组32环境检查。

`push-four-foot-preparation-v137/`已完成原起点、已用seed3701、8环境、**90秒四足承力准备诊断**，完整阶段0/8通过，终态缺失0、安全终止0、原PUSH0/8且8次超时。8个环境均完成FL、FR、RL三足起落及实测重载，并切入RR阶段；前三足接管参考连续、前两步与v136轨迹一致。RR在单次机身转移达到8cm限幅后保持四足承重，未开始卸载或抬脚：最终三角支撑裕量仅13.57～17.50mm，低于原25mm门槛，故不会被允许抬脚。这是门禁停住，不是跌倒。四段所有控制采样均至少三足>8N、记录腾空0、转移后饱和0；分段速度/接触合力及含初始化逐关节饱和见审计。

v137原始摘要中RR目标/起点未初始化却计算了世界坐标距离，`checks`里的RR数米误差不是实际足部移动；原件保持不改，`RR-not-started-audit.json`明确将该足的步长和落点误差标记为不可用，完整阶段0/8结论不变。报告SHA256为`caa6aa18a5e9c72f8ca2d8b336f7d45f2c49bf5522ff002bbcc85c88e78d586f`，原阶段摘要SHA256为`7ea43ce4dbe6f1e940286eb7aac0c6b3e77d7111fdb83e9c5449d669f461eba8`。小型摘要、澄清和遥测审计已同步本地。

`push-rr-bounded-replan-v138/`已完成已用seed3701、8环境、90秒四足准备诊断。保持v137路径，仅在RR尚未卸载、第一次受限转移已到位、实际四足>8N且连续平稳2秒时，追加一次受原8cm单次限幅约束的转移；25mm卸载裕量与足力/姿态门槛未降。**8个环境均实际完成四足起落重载**，RR末段连续平稳12.06～12.80秒，终态缺失0、安全终止0；重规划前轨迹与v137一致，参考接管步长≤1.49e-8rad、接管加速度变化≤0.160rad/s²。但最终FR误差11.43～12.45mm超过原10mm门槛，严格阶段仍**0/8**；FL/RL/RR误差均在门槛内，原PUSH仍0/8、8次超时。报告SHA256为`5fa3e5310f0570a74c47ec01630ae85bb93dc19d938d4d922230aab9eefd7649`，阶段摘要SHA256为`73fa02f23ad8507268c3bd75683ccd744a4e015aaee119a76c07dca5fc9935a0`。

v138另有审计口径修正：冻结单足控制器在某环境退出后、其他环境仍运行时，会清零该环境的内部落脚缓存；不能用后续非活动缓存的`landing_reload=0`否定已发生的承重。`placement-failure-audit.json`逐段核对最后一条活动控制采样：四足各自均实测重载比例1、至少2秒稳定、四足>8N及有效参考，实际失败项仍为最终FR位置误差。原报告/摘要不改写，v139审计改用各段最后有效实测记录，并继续保留初始化饱和与全部原位置/安全门槛。

前右足在最初重载稳定后，到追加RR转移前已累计水平位移约5.8～6.4mm。`push-retained-stance-anchor-v139/`已完成，对其稳定落地时的实测水平位置作一次受8mm上限约束的参考保留，最终FR相对原起摆目标仍为11.46～12.52mm，未优于v138；8个环境均稳定，无安全终止、终态缺失，旧末态位置检查仍0/8。因此不继续沿用该修正，保留v138动作路径。v139报告SHA256为`40934af502d866e946aa8f7d8e66b74d2ff03fc9c6970dcc6ab09b0f6a5bdb1c`，阶段摘要SHA256为`96d18b319c86124c589014a3f802f4b1c8b9b201cb1ddc22a0d9be6f18d9537e`。

**测量口径分离**：10mm落点误差应在该足真实落脚、完成重载时核对；后续支撑转移产生的位置变化另记为支撑位移。v138各足完成重载时的误差范围：FL6.64～7.73mm、FR6.48～7.67mm、RL6.01～6.20mm、RR3.18～3.45mm，8/8满足逐足落脚与重载条件。此后FL/FR/RL相对各自完成时的最大水平位移分别9.78/9.19/9.37mm，仍须持续监测。原90秒末态与每次起摆目标比较的记录及0/8结果全部保留，不改写成通过；这也不是完整PUSH验收。两版独立的`placement-phase-audit.json`同时列出落脚误差、后续位移、旧末态误差及实测重载条件；v138/v139该审计SHA256分别为`168859ea1f74ad99e1554af1f79b5df64129af6ff671f710cd0e7027a24f262a` / `dc60649bdb88df268941ab75c62eb80b76ba52422ec3bedd062b544d03bb7a7c`。接触、载荷、稳定时长、执行器和物理安全门槛未放宽。

`push-final-body-pose-v140/`已完成已用seed3701、8环境、**100秒最终机身姿态阶段诊断，8/8通过**。保留v138四足动作，RR实测重载稳定2秒并重新确认四足承重后，机身以8秒五次平滑参考前移8cm、降低4cm，腿不再摆动。实际体位误差6.64～6.84mm、四足支撑多边形末态裕量107.3～113.3mm、本次机身调整中最大足位水平变化≤6.88mm，末段连续稳定12.02～12.76秒。8155个环境控制采样均至少三足>8N、记录腾空0，机身竖直速度绝对峰≤0.00957m/s，单足合力峰≤91.93N、四足接触向量和模长峰≤213.94N；最终机身阶段最大力矩限额比≤0.5861，无安全终止、终态缺失。含初始化逐关节饱和单列，以上非物理子步峰。接管前与v138轨迹一致，接管参考步长≤1.49e-8rad。报告SHA256为`9dd712fe5807a6322e4f2cda7749179226d489f77ac2cf4f76595a54c6f5376f`，阶段摘要SHA256为`0e6f345adbbf245f873c0d900c7ed64003523756c1d94d7c11817fb6ca068a8b`。该报告未恢复机械臂接近，原任务0/8只表示诊断停在准备阶段；不是完整推箱成功率或最终可接受耗时。

`push-resume-approach-v141/`已结束：原起点、已用seed3701、8环境、120秒接近诊断上限。全组在90秒恢复旧第14路点后，8/8在94.14～94.84秒提前终止，合法手接触0、终态缺失0。重叠安全标志为base_contact 2、bad_orientation 5、box_contact 2、invalid_hand_contact 1，不能相加当作环境数。原生motion_ready从未成立，未释放行走策略。报告SHA256 `865c6ace8d89acce66addcb617670c74228c25f4dd6287b1774d75f90f49f2e9`，阶段摘要 `4654180f4eb6f5b6855cfe8d68679234cff49e58d3a58553f91c1c4da0c585c9`。

失效链已定位：91.40～91.44秒净空低于55mm时，最终机身控制的门禁冻结腿部参考更新；91.50～91.54秒低于35mm，92.56～92.66秒机身误差超过10mm，随后支撑恶化。旧路点阶段只观察几何，几何投影在safe_approach_complete之后才启用；旧路径部分路点净空25～30mm，与当前35/55mm要求不兼容。正净空本身不证明已经穿模。下一版必须处理接近路径与承重保持的耦合，不能靠降低净空门槛放行。

`push-preparation-confirm-v142/`和`push-preparation-confirm-v144/`均已退出，冻结相同v140评估器及辅助源码，各32/32准备通过、安全终止0、终态缺失0。种子分别为已用2701、3701，窗口100秒；不恢复机械臂接近，不计为完整PUSH。报告SHA256分别为`49b89dba83f256b922dd8f812b7a4e56af0c79c3745a3beb8d6caff51126d756`和`0fa5a4cc02ad8d452d613d1068ccf76e6d28187d74b04ca9055f1d9054ca71fd`；小型阶段摘要和退出记录已同步本地，原大报告保留远端。

`push-approach-replan-v143/`的两条静态候选以实际v141释放前记录为起点，假设机身相对v140最终位置后退80mm、足端保持固定，由腿部IK求关节角；这仍是待动态实现的姿态。两条候选手高偏移分别为0和60mm，均满足规划的65mm保护净空、10mm箱体净空和100mm机身中心距离。独立审计按最大10mrad采样144/123点，均无新增或恶化的非相邻碰撞几何穿透；最小静态单足载荷33.33/33.68N，机械臂重力力矩限额比最大0.666/0.641，腿部静态比最大0.345/0.341。该检查使用实际质量/质心和冻结承重分配函数，不含手部推力、动态碰撞、跟踪误差或整个接触过程，不能写成全程无自碰证明。首轮审计因Float/Double混用退出，已统一静态审计dtype后重跑完成，未改物理控制代码。

原生接近契约已重新核对：入口在箱面后120mm、pitch1.5rad，随后到后30mm并过渡到pitch1.0rad；入口位置容差X/Y/Z为50/80/45mm，姿态是软优化项，没有硬姿态误差阈值。早期8mm位置和0.15rad姿态筛选是额外规划偏好，不能描述为原生门禁。当前路径仅到入口附近；后续仍需验证到实际接触的连续过程。旧路点参考限速为1rad/s，进入后续笛卡尔接近才是0.25rad/s，动态试验需核对跟踪能力。

**2026-10-12接近衔接筛查与运行交接：**v143追加了固定机身/足端、理想关节跟踪下的入口衔接筛查，调用冻结的bounded_pose_delta，核对原生位置/速度/100ms保持条件及0.25rad/s参考限速。第一轮height_weight=1仅归档，当前匹配配置的是height_weight=2。原55mm软净空偏好下，两条路径继续向箱面接近时分别在3.56/4.02秒跌至54.39/54.80mm，被既有55mm腿部保持阈值拦下。仅将软净空偏好提前到65mm的设计对照，在3.48/3.80秒通过几何箱面准备条件，采样最低净空64.45/64.89mm。硬净空、腿部保持、碰撞、执行器、实际接触和停稳门禁均未修改；此处65mm是软优化目标，不是实测全程下限。此筛查省略学习残差、PD/延迟、完整预测屏障和刚体中心投影，也没有接触力，不能当作原生完整控制器或动态通过，更不能把几何箱面准备记成合法手箱接触。对应`entry-continuation-heightweight2-screen-summary.json`和`entry-continuation-preference065-screen-summary.json`及源码已同步本地。

`push-approach-body-preparation-v145/`现已完成：保留v140四足路径与4cm/8秒机身降低，仅取消最后8cm前移；已用3701、8环境、原起点100秒准备诊断8/8通过，无安全终止、无终态缺失。最终机身误差2.38～2.49mm、连续稳定12.02～12.76秒，最终机身阶段最大力矩限额比0.586以下。报告SHA256 `bf1fe5b3c42c422be4fcad53e6b293611411c710ccc80305fc728ddc394219aa`。该版尚未释放机械臂；原队列PID1050834和launcher PID1050989均已结束，不重复启动。小型计划、源码、摘要与退出记录已同步本地。

**v146实际初态路径核对：**`push-safe-path-contact-v146/actual-preparation-path-audit.json`使用v145的8个实际终态、匹配质量/质心和冻结支撑分配函数，逐一检查共享v143高度0路径。6/8通过；env4路径与箱体最小间距−10.67mm，env7仅0.44mm，且两者入口X误差80.15/61.03mm超过50mm原生门槛。二者没有新增或恶化的机器人非相邻自碰，失败对象是箱体几何/入口位置。不能把单一姿态静态通过扩展为全部初态可执行。

较早交给原生笛卡尔接近的共享后撤路点对照，仅7/8满足10mm箱体规划预留（env4最小6.68mm），未放宽阈值；理想跟踪接近筛查6/8达到几何箱面准备，env0/7在20秒预算内未达到。对照仅归档，没有启动物理执行。`run_pose_bank.py`（原CPU launcher PID1052681）现已结束：8份报告齐全。最初25mm位置误差范数筛选得到7条路径，env7最优候选约26.5mm，未过这一额外规划偏好；原报告保留。随后对所有8个环境统一按箱体坐标轴核对原生50/80/45mm入口容差，并预留20%余量为40/64/36mm，复用已有候选；没有新增搜索、放宽物理碰撞或改动原生入口门禁。8条路径均通过方向位置筛查及最大5mrad间距的几何检查。

`directional-path-full-audit.json`又独立按最大10mrad采样核对实际8个准备姿态，8/8通过静态路径条件：臂—保护几何最小70.00mm、与箱体最小30.51mm，没有相对实测准备姿态新增/恶化的非相邻机器人穿透；使用匹配质量/质心、无手部外载，最大机械臂重力力矩限额比0.668以下。该结果没有包含推力、动态跟踪或物理子步。审计SHA256 `7a61b8a3070b0d0da9f2147597551712e5d1f234c824b03a7132d644c544ec2d`。

入口后续筛查已修正为原生净空梯度提前15mm计算的语义（旧简化筛查仅在低于偏好时计算梯度，归档）：采用65mm软偏好时，6/8在理想跟踪下达到几何箱面准备，env5/7在20秒预算内未达到，均未跌破原55mm腿部保持阈值；采样最小净空63.06mm。该筛查仍省略完整预测屏障、身体中心投影和真实动力学，不能证明接触成功，也不能作为覆盖所有环境的稳健性结论。

**已完成动态诊断v147：**`push-adaptive-entry-contact-v147/`使用冻结v145准备过程，原起点、已用3701、8环境、140秒接近/接触诊断窗口。全组实际稳定承重≥2秒且时间≥100秒后，先核对实际体位/箱体/关节与路径审计来源匹配，再接入各环境路径；原生按实测关节位置/速度推进路点，不强制就绪或接触标志。释放后参考限速收紧至0.25rad/s，软净空偏好提前到65mm，原35mm几何屏障、55mm腿部保持、碰撞、执行器、真实接触和停稳要求保留。批量路点索引已核对正确选取各环境路径及最终节点。此为已用种子的固定路径库诊断，不是通用在线规划器或完整PUSH验收；腿部仍保持承重，原生压入逻辑可能造成箱体位移。队列PID1054208及launcher PID1054241均已结束，不重复启动。





v147的6个合法接触环境为0/1/2/3/5/6，首次接触在107.54～109.54秒；最长连续健康接触只有0.10～0.14秒，最终健康保持全部为0。持续原生压入期间，6例joint2均达到限额，≥98%饱和累计28.34～31.08秒；最终箱体前移8.7～15.1cm不能当成完整推箱成功。全8例记录始终至少三足>8N、腾空0，但最小记录净空在6例中降至15.75～35.70mm；支撑计数不能抵消净空/力矩不合格。env0首次合法接触109.54秒时净空66.84mm、力矩比0.718；110.04秒跌破55mm，111.66秒达到98%力矩限额。冻结腿部姿态同时持续追踪随箱体前移的压入目标，是下一轮需要隔离的受力因素，不能仅凭时间先后认定唯一原因。

另2例env4/7分别在107.74/109.56秒触发`invalid_hand_contact`，没有合法接触，其记录净空始终≥65.92mm、力矩比≤0.651。原分类器逐项复算与终态标志完全一致：接触点距手部原点99.09/89.28mm，超过原70mm手端邻域判据；env4接触高度距箱体中心94.96mm，也超出原90.1mm含容差的高度范围。接触力方向、箱体前面及宽度条件通过。没有修改分类器、扩大合法区域或把这种接触改记为成功。报告SHA256 `74ef66750bcdf6a053832a73277a7664c2d9dcabe9f1e5e6c5161d4a728033cf`，`contact-failure-audit.json`保存逐项判据和时序；env0释放前5000个控制采样与v145完全相同，8条终态齐全。

**已完成v148接触锁定对照：**`push-contact-lock-isolation-v148/`保留v147准备/路径/65mm软偏好/0.25rad/s参考，只在释放后启用现有原生`lock_arm_on_contact`；仍由实际合法接触触发锁定，不伪造接触或就绪标志。目的为区分接触建立和持续压入负载，并不解决env4/7的非法首次接触，也不计为完整PUSH。原起点、已用3701、8环境、120秒诊断，GPU0 launcher PID1057078已结束。6个合法接触环境均持续健康保持10.46～12.46秒，接触后最大力矩限额比0.760以下、最小记录净空62.06mm；三足支撑记录覆盖全部活动样本，腾空0。env4/7仍分别107.74/109.56秒非法接触终止，所以“健康接触环境6/8”与“整批通过false”分别记录，不能宣布PUSH完成。所有原物理/接触/停稳判据保留。

首轮后处理使用了“控制契约必须完全相同”的断言，没有允许本试验明确启用的`lock_arm_on_contact: false→true`，因此原`exit-status.json`保留`valid:false`。独立`revalidate.py`只允许这一项预先声明的差异，其余物理、权重、源码、8个唯一终态和释放前5000步均重新核验通过；未重跑仿真、未改原报告或失败标签。有效结果入口为`revalidated-status.json`、`revalidated-stage-summary.json`，报告SHA256 `457f39de4cc80f4248b53dc1b2ccdaf8aa6b88cde80ecd46ad68f99146bb6824`。原报告的`nominal_ik_clearance_margin=0.055`是静态元数据；实际65mm软偏好/0.25rad/s参考由已记录哈希的包装代码实现，摘要已显式说明。

**当前v149近箱姿态静态对照：**实际准备后，env4/7机身到箱前面的法向距离分别439.6/460.8mm，其余6例489.4～540.2mm。`push-entry-spacing-v149/`对法向距离<480mm的姿态，测试足端固定、机身后退到515mm并把横向偏移限制在±80mm，保持每个XY分量移动≤80mm；六个其余姿态不变。这是根据当前失败样本提出的规划条件，尚无鲁棒性或动态证明。CPU launcher PID1057513已结束，两例均找到路径。固定足端IK误差≤1.4e-16m；独立路径审计未见新增/恶化的非相邻机器人穿透，最小保护净空70.59/71.00mm、静态最小单足载荷43.21/36.53N、机械臂重力力矩比≤0.668，均通过静态筛查。理想跟踪入口衔接在3.14/3.60秒达到几何箱面准备，最小净空均≥67.19mm；这些结果仍不是实际合法接触，也没有证明机身移动过程或受载动态安全。小型摘要/审计/代码已同步本地，大报告留远端。

`push-entry-spacing-preparation-v150/`已结束：8条终态齐全，无安全终止，准备条件7/8通过。仅env4/7实际触发了间距调整，另外6例保持原参考。env7通过；env4实际稳定12.76秒、机身误差8.81mm、力矩比≤0.587、净空≥76.55mm，但足端最大水平变化10.1168mm，超过10mm门槛，因此仍判失败。最大偏差出现在末段并持续到终态，不能仅延长等待或把它解释成瞬态通过。原报告SHA256 `67d6d457c277763cd274a26746a6d389fbc180210f1ba958d7bcb7a5e3161ba3`。

**已完成v151及自动后续：**`push-entry-spacing-cap-v151/`只将近箱机身XY每分量调整上限由80mm收紧到65mm；在本批输入中仅限制env4原76.45mm后退，其他7例参考不受影响，后处理逐一核对其身体参考及完整轨迹是否与v150相同。515mm为受限调整的目标，不保证碰到位移上限时精确达到；10mm足位变化、承重、净空、力矩和稳定门槛均保持。原起点、已用3701、8环境、100秒准备诊断已完成8/8，launcher PID1059968已退出。另7例身体参考误差为0、完整最终机身阶段轨迹逐字段完全相同。报告SHA256 `b46662e0a0676c43fdf6f95a5b31d20cb809e858f13ab926508182ce05b5d643`。

`push-spacing-paths-v152/continue_after_preparation.py`（原PID1060271）已按前置检查完成串行衔接：保留6例既有路径，按env4/7实际终态重规划，两例均找到路径；统一实际姿态全碰撞/承重/静态力矩审计8/8通过后才启动v153。该编排进程已结束，不重复启动。

**v153接触保持阶段8/8通过：**`push-spacing-contact-lock-v153/`原起点、已用3701、8环境、120秒诊断，launcher PID1060723已退出。8例连续健康接触保持9.38～12.46秒，接触后最大力矩限额比0.7596、最小记录净空62.046mm，安全终止0、终态缺失0；三足支撑/腾空及含初始化饱和继续分别保留在阶段摘要与原报告。原始PUSH成功仍0/8，箱体X位移最大0.1804mm，未完成推箱；不要将接触锁定保持称为PUSH训练完成。报告SHA256 `b231f050bf874f4613c32dbf0f029492235a15a756839d702f62ddd429e4eb66`，`exit-status.json`明确`stable_contact_environment_count=8`、`batch_stage_passed=true`。这一轮后处理已显式允许预先声明的原生锁臂开关差异。

**v154原速录像已核验：**`push-contact-video-v154/`冻结v153评估器、辅助源码、路径和已用3701/8环境，原起点120秒接触阶段录像已完成，8/8阶段通过、无安全终止或终态缺失，env0完整轨迹与v153逐字段完全一致。视频1280×720、25fps、3000帧、120.000秒，全帧解码无错误，SHA256 `c1aaf3eec9cef8f14e8d1e49cd1552c229f4804bb89126d0c652bd3f6461934f`。本地视频为`../artifacts/go2-piper/sim2sim-current-20261008-a/push-contact-video-v154/original-speed-contact-stage.mp4`（相对仓库根）；画面是env0，其他7环境由报告核对。人工检查1/20/40/60/80/100/105/107/109/112/115/119秒关键帧，准备调整、机械臂下降和末端保持可见，所检帧未见明显穿越机身；没有声称连续播放审阅，单视角抽帧不替代碰撞遥测。`visual-review.json`和`decode-check.json`独立保存核验，原`exit-status.json`中生成时的待审阅文字不改写。此为接触保持阶段视频，不是推箱完成录像；图像没有通过加速或剪辑改变诊断时长。


**v155持续受力筛查：**`push-contact-load-envelope-v155/load-envelope.json`使用v153实际稳定接触终态、匹配PhysX质量/质心和执行器限额，在实测接触点施加假设的0～30N反向法向力并求静态平衡。0/5N均8/8达到90%力矩预算，10N为7/8，15/20/25/30N均0/8；20N机械臂最大力矩比范围0.981～1.068，其中7/8超过实际限额。足端四点各≥8N、摩擦菱形系数0.4和静态支撑解仅为设计假设，不能当作实测推力或全局不可行证明。它说明当前接触保持构型不足以直接获得持续推箱的可靠力矩余量；没有据此增大执行器限额或减轻箱体。

**当前v156承力姿态规划：**`push-loaded-posture-v156/`以实际合法接触为起点，静态测试足端固定、机身前移80mm、实测接触材料点提高到箱体中心上60mm，要求20N载荷下臂/腿≤90%限额、端点保护净空65mm、手部最近表面仍在60mm手端邻域和85mm箱体半高范围内；0/20N支撑核对，30N余量单独报告。初次模型适配因`end_effector`只是无碰撞标记而退出；碰撞几何实际在其焊接的link6组内，显式核对该组并加入手端邻域/高度判据后，首轮5/8找到满足静态条件的端点，另外3例局部求解未通过。额外局部初值求解PID1063415已结束，7/8满足同一静态条件，原失败记录保留。剩余env6的接触材料点本来偏高；固定提高到箱体中心上60mm时，最近手部几何预测到达箱面上缘附近并违反高度/净空约束，因此未执行。CPU PID1063528的有界接触高度求解也已结束：剩余env6仍未通过，位置误差6.51mm且最差约束违反11.99mm；不能使用该候选。其余7个端点保留。随后允许剩余env6的接触点在合法手部表面迁移，并把机身前移量限制在0～80mm内求解，保留原手端邻域、高度、碰撞及20N力矩约束，找到前移33.80mm的新端点；其余7例保留80mm前移端点。该例原接触材料点迁移约数厘米，尚未执行真实转换，不能把端点可行当作连续接触证明。端点找到后仍须独立全机器人碰撞、连续路径、真实接触保持及动态受载验证，尚未执行这些身体/机械臂动作。小型结果和本地交接已同步。

**v157独立承力端点审计：**`push-loaded-endpoint-audit-v157/endpoint-audit.json`以实际最近手部碰撞表面接触点重新计算受力（不只使用规划的固定材料点），核对8个端点的全机器人非相邻碰撞、实际足端位置/腿关节余量、保护净空、箱体及手端邻域/高度。8/8在0～20N静态反力条件下通过；20N最大机械臂力矩比0.8951以下。25N时8例均未达到90%余量，30N部分超过实际限额，不能宣称任意冲击负载安全。原接触保持构型v155与新端点v157必须分开引用；新端点尚未在Isaac或MuJoCo动态执行。

**连续过渡筛查v158～v163（均未执行物理动作）：**v158的41点检查为3/8通过5N采样条件，5例因接触位置或间隙不合格被拦下；它没有强制末端关节向量等于已通过20N审计的端点，因此这些路径也不能继承端点承载结论。v159改为合法接触区域约束、明确100mm身体中心距离、每节点关节变化≤40mrad，并固定最终关节为已审计端点，5/8通过。v160仅调整数值导数步长后为4/8；v161保留v159的5条通过路径，对另外3条用标量接触间隙等式继续求解，仍只有5/8。全部失败路径保留，未通过整体筛查不执行。

数值核对发现，默认约1.49e-8rad差分得到的接触距离梯度与1e-4rad结果存在显著差异；已记录`v159/gap-gradient-diagnostic.json`，这只能解释部分求解困难，不能据此宣称所有失败都是数值问题。改变导数步长没有改变物理阈值，也没有解决全部路径。

v162开始静态检查“先退开25mm→保持与箱体至少10mm间距调整姿态→重新接触”方案，未启动物理执行。其0/8结果包含一个已识别的几何见证点处理错误：离开箱面后，两几何最近点的中点不在箱体表面，用它做箱面位置判据会错误拒绝正常退开。v163已依据MuJoCo接口契约改用`fromto[3:6]`的箱体侧表面见证点；距离、保护净空和实际接触分类器未改。新承力端点也以箱体侧见证点独立重审，`v157/box-witness-endpoint-audit.json`仍为8/8通过0～20N静态条件，力矩比结论不变。

**v163～v166结果：**v163静态采样6/8通过；env0重新接近时最近手部表面靠近箱体上沿，env6在退开初段被接触区域预测拦下。v164从已验证承力端点倒向寻找退开路径，只到约2.9mm间隙后求解失败，未连接到原路径，未执行。v165保留6条路径，仅复核另外2条：此前在几何已分离但距离<5mm时仍要求最近表面点满足真实接触位置条件，属于额外的预接触规划假设；改为几何接触附近（≤10µm）才应用该代理条件后，8/8采样通过。10µm只覆盖当前v153接触姿态在静态模型中的−4.3～+0.87µm间隙校准，不能保证未用初态或动态提前接触。实际力>1N的原接触分类器/终止条件没有改动；后续物理试验必须验证这个假设，不能据静态通过宣布安全。

v166给路径加入PCHIP关节/身体插值和五次时间曲线，并按≤2mrad关节/0.2mm身体间距设计稠密采样，只有1/8通过原规划要求。其余7例在插值中保护净空降至59.941～59.987mm，低于60mm规划门槛；没有放宽该门槛或改写失败报告。v168保留env1已通过路径，把其余规划点的保护净空提高到61mm、自由转移箱体间距提高到11mm，为原60/10mm稠密检查留出1mm余量。

**v170稠密时序检查8/8：**v168采样路径8/8通过后，`push-reserved-timed-audit-v170/`独立检查全部8条平滑路径通过，规划运动时间13.20～13.90秒（不含前置120秒诊断或真实解除接触/停稳/重新接触等待）。检查包括全部非相邻机器人碰撞、非手部对箱体、机械臂对地、足端IK、静态支撑/力矩、参考速度和加速度；沿途是假设0～5N，20N承力只在终点审计。env0/6仍各记录33/12个“有正间隙但最近表面不满足接触区域代理”的采样，未把它们计成实际接触，也没有隐藏；这两例尤其需要原实际接触判据的物理核对。该结果不证明PD/延迟、实际接触力、身体跟踪或行走推箱通过。所有源路径与审计保留独立哈希。

**v171真实退开隔离试验已完成：**`push-withdrawal-physics-v171/`已在GPU0完成，launcher PID1068278已退出。原起点、已用3701、8环境、130秒，前120秒复用v153接触保持；只让v166中已完整通过稠密退开检查的env1/2/4/5/6/7执行退开，env0/3继续原接触保持。此次不做身体转移、重新接触或推箱，不能把6个尝试环境写成8个成功。手部合力≤1N且原合法接触为false连续0.2秒，才清除接触锁定/就绪历史；真实重新接触时不强制清除真实标志，更不强制置true。实际手部参考额外经过原几何屏障和0.25rad/s、3rad/s²平滑限制，原物理/非法接触终止保留。手部力消失、四足承重和停稳必须实际观测；不能用静态正间隙替代。结果6/6尝试环境通过，全部8个终态齐全、安全终止0。6例在120.40～120.82秒实测确认解除接触，随后完成参考轨迹并连续健康保持7.80秒；接触锁定/就绪标志审计无违例，未强制置true。退开阶段最大力矩限额比0.7583以下，最小实测净空59.316mm，满足原55mm保持门禁；这也说明静态60mm规划留量不能直接当作动态下限。最大竖直速度绝对值0.002455m/s以下；三足支撑/腾空、接触合力峰及含初始化饱和见`result-audit.json`。未尝试的env0/3继续健康接触保持20.46/20.68秒。前120秒env0轨迹与v153完全相同。报告SHA256 `5caef87a31bb028ad91f0b225f70c3410e2492bbb9241c85785880bf208ab53f`。此次仍未转移身体、重新接触或推动箱体。

**行走接管另有姿态风险：**旧v117同种子env0的141个实际加载行走采样，身体高度中位数278.48mm（273.999～285.489mm），与当前约239～242mm静止接触姿态不同。v167/v169尝试身体上升40mm、接触点提高到箱体中心上75mm的替代端点；v172独立静态审计8/8满足0～20N承载设计条件，数值容差为几何10µm、力矩比1e-8。v167原先env5/7因严格浮点比较高出0.9约1e-13～1e-12而标false，原报告保留；新审计明确容差，不改变实际执行器限额。原v167说明末尾残留“60mm”旧文字，以实际参数/数据字段75mm及新审计为准。

仅匹配身体高度仍不能证明固定锁臂后的行走安全：旧行走记录的身体俯仰为−0.0628～+0.0663rad。把该历史身体高度/姿态变化施加到新端点的固定臂形状，接触材料点的运动学高度可达221～227mm，超过原箱面高度范围。该`v172/historical-attitude-sensitivity.json`只是反事实敏感性检查，不是新策略实际运动预测；它说明后续必须验证世界系手端跟踪或分级接管，不能仅凭静态承力足够就释放行走。当前没有执行该行走接管。控制衔接注意事项另存`push-withdrawal-physics-v171/NEXT_CONTROL_NOTES_CN.md`，明确规划姿态与PD命令的差别、实际解除/重建接触以及身体运动时世界系手端跟踪的要求。

**v173/v174计算开销检查：**仅把几何查询中的`mj_forward`换为`mj_kinematics`虽输出相同，但耗时没有实质改善，不作为主要优化。v174改为对原±1mrad差分，使用刚体包围球、关节祖先关系和转动位移上界筛选“可能成为最近”的几何对；保留当前全量距离观测、最终屏障投影、数值保护量，并在近穿透状态回退原全量梯度。112个查询（48个实测姿态、64个随机姿态）的距离、梯度、残差、投影、阻挡及预测距离逐值完全相同。48个实测姿态的梯度计算2.987秒降至0.327秒，约9.1倍；这是局部计算耗时，不是机器人动作时间或整轮仿真加速结论。v175实际回归已确认前120秒env0完整轨迹逐字段不变，全部8环境退开通过；整轮壁钟1880.15秒，未进行同资源条件的完整耗时对照，不宣称整轮9.1倍加速。

**v175全8环境真实退开已完成：**`push-withdrawal-all-fast-v175/`，原起点、已用3701/8环境/130秒。launcher PID1069439已退出，独立`result-audit.json`确认**8/8退开通过、8个唯一终态、安全终止0、终态缺失0**；解除接触在120.42～120.82秒，完成退开后全部连续健康保持7.80秒。退开阶段三足支撑覆盖全部采样、腾空0，最大力矩限额比0.758214、最低记录净空59.323mm（满足55mm保持门禁，不能声称动态净空≥60mm），最大竖直速度绝对值0.002435m/s、单足合力峰79.054N、四足向量和模长峰214.224N。含初始化饱和仍完整记录：joint3单环境最大0.16秒、joint5最大0.24秒；不把退开阶段无饱和扩大为全程无饱和。以上峰值为控制采样口径。前120秒env0完整轨迹与v153相同，原107冻结源码、物理与checkpoint哈希核验通过。原任务仍0/8；没有身体转移、重新接触或推箱。报告SHA256 `fc93fe385289fc62dbaea471539f1a4ff4f70607fe5d2eb090da4a50a2327383`。小型状态/审计已同步本地，原大报告留远端。

**v176机身转移诊断（运行异常，未通过）：**`push-free-body-transfer-v176/`的launcher PID1071286及Isaac PID1071368已退出；原起点、已用3701/8环境/145秒。保持v175前130秒，再在实测解除接触、四足承重、停稳≥2秒后接入v170自由转移段；7例机身前移约80mm、env6约33.8mm。世界系手端位置/姿态使用实际Jacobian闭环，初始实测偏差连续消除，机械臂原几何投影与0.25rad/s、3rad/s²参考限制保留。跟踪误差过大暂停路径推进，四足平衡反馈继续；真实重新接触、足滑>10mm或原执行器/净空条件不合格则停止推进。本轮不接入重新接触和行走推箱。v175终态与路径起点的世界手端预检8/8，最大位置误差2.059mm、姿态误差0.00241rad；仅是起点预检，不能作为动态通过。须核对前130秒env0轨迹一致、完整终态、实际支撑/足滑/力矩/世界跟踪和最终停稳。所有新增辅助代码在独立v176目录及新脚本中，已通过基线未覆盖。后续先完成该段物理验证，再接真实重新接触与受载推进；未用种子、原时限和MuJoCo正式验收尚未通过。 在约130秒首次进入机身转移入口时，单环境`compute_pose_error`传入1维向量，实际Isaac函数要求(N,3)/(N,4)，触发`IndexError: too many indices for tensor of dimension 1`。未发出机身转移指令，也未生成最终报告；本轮不能算物理转移通过或获得完整终态。异常后的Kit关闭挂起，确认堆栈后仅对失败Isaac PID1071368发送SIGTERM退出；原退出文件虽然returncode为0，但valid为false，独立`failure-audit.json`保留真实运行异常。v175已验证基线不变。

### 当前续跑入口（2026-10-12）

`push-free-body-transfer-v177/`为v176接口修复重跑：单环境位姿误差输入保留批量维度，原路径、145秒已用种子诊断窗口及全部物理门禁不变。远端Isaac Python直接加载当前安装的数学函数，使用v175实测状态和明确标注的合成Jacobian/传感器替身，对启动前、实际启动、非零路径进度、暂停及摘要接口进行了回归，`interface-check.json`通过；这是接口测试，不是动力学或阶段通过。辅助源码SHA256 `a74849453774c382d34cb47c46221e20b1c5d0c28b22b66a2e9525eba8ad2d44`。新的评估脚本对未处理异常先写`runtime-failure.json`再以非零退出，避免异常清理继续占用GPU；正常运行路径不变。已完成，launcher PID1072054及Isaac PID1072136均已退出；不重复启动。

**v177实测结果：机身转移1/8通过，整批不通过。**独立`result-audit.json`已核对8个终态齐全、原生安全终止0、原完整任务0/8；前130秒env0全部轨迹与v175完全一致。仅env6完成转移并健康保持6.20秒，其实际机身前移37.4mm（规划33.8mm）。另7例在136.54～137.22秒触及原55mm保持门禁并停止推进：当时净空54.919～54.996mm，后续最低54.422mm；实际前移78.7～84.5mm。没有把门禁触发改记成成功，`batch_safe:true`只表示无原生任务安全终止，不表示满足更严格阶段净空要求。全部控制采样至少三足承重、腾空0，阶段最大力矩限额比0.711，最大足漂移8.99mm，最大世界手端位置误差2.513mm；其余竖直速度、接触合力峰及含初始化饱和均保留在阶段和独立审计中。首个停止时手箱力全部0N，主要停止原因是净空，不是重新接触或力矩饱和。报告SHA256 `5ef7bcd352bc49d916f65231b48632f76c736c758ee71c12f90d6fb0d2d15247`。

**v178失败机制复算：**`push-transfer-clearance-audit-v178/root-error-decomposition.json`针对env0首次停止状态，实测机身相对静态路径前移多9.760mm，而姿态差只有约0.0017rad。保持同一规划世界手端姿态，仅替换机身平移的运动学复算净空为54.344mm（原规划62.111mm）；仅替换姿态为62.336mm，两者都替换为54.561mm，实测54.936mm。说明平移误差足以解释主要净空损失；该复算不是新物理试验或因果完全证明。机身参考从既有`body_ref`接管，与路径源实际位置存在初始偏移；原四足控制仅使用水平速度反馈，转移时还有实际位置误差。

**v179跟踪修正已完成：8/8机身转移阶段通过。**`push-body-tracking-v179/`，原起点、已用3701/8环境/145秒，launcher PID1073939及Isaac PID1074023均退出，独立审计已自动完成并同步本地。保留v175前130秒与v170路径；仅对此前失败7例消除初始身体参考偏移，并增加8/s²水平位置反馈（1秒五次平滑启用），原0.4m/s²加速度上限不变。全部在138.8秒完成8.8秒转移并在末段健康保持6.20秒；8个唯一终态、安全终止0、终态缺失0、原PUSH0/8。阶段最低记录净空55.936mm、最大力矩限额比0.71075、最大足漂移8.859mm、最大世界手端误差2.439mm；6000个环境控制样本全部至少三足>8N、腾空0、手箱力0N。竖直速度绝对峰0.000982m/s以下，单足合力峰91.224N以下、四足向量和模长峰213.754N以下。含初始化joint3最大饱和0.16秒、joint5最大0.24秒仍单列，以上是控制采样峰而非物理子步峰。

前130秒env0轨迹与v175完全一致，env6原已通过的整段转移轨迹与v177完全一致。原55mm保持门禁、机械臂限速/加速度、几何屏障、碰撞、真实支撑和执行器限制均保留；最低净空距离55mm门槛只有0.936mm，不能据此认定鲁棒性验收通过。报告SHA256 `205934a2b87ff70f6c212a7cf77791219c0a6aacd63559b0e43f9be87701d9ad`，有效入口`stage-summary.json`与`result-audit.json`，同步状态`sync-watch-result.json`为completed。此轮没有重新接触或推箱，完整PUSH、未用种子及MuJoCo验收仍未通过。

**下一段准备：**`push-actual-recontact-audit-v183/`从v179实际终态复核v170重新接触路径：固定实测根/腿/箱体姿态，以世界手端目标解算机械臂，检查实际55mm保持门禁、非相邻/箱体/地面几何、原90%静态力矩余量、支撑分配与参考速度/加速度。在远端隔离MuJoCo环境进行CPU静态核对，不推进物理、不宣称接触成立；本次静态检查7/8通过；env0在手箱间隙约4.96mm时最近表面点落在箱体上沿，未通过额外的近接触表面预筛，不能将正间距记为已经发生非法接触。`push-recontact-top-reserve-v184/`保留另外7条，env0最终选取中段最大3mm退让、起终点位置与姿态不变的3.2秒路径（原2.9秒）。选定8条均通过实际终态静态检查；env0最小保护净空56.200mm、最大关节参考速度0.22267rad/s，全部8条最低净空55.951mm、假设20N端点反力时最大机械臂力矩比0.888以下。原55mm保持门禁没有放宽，但几何裕量仍小，尚无动态鲁棒性证明。纯下移的3个对照失败；更大后退对照侵蚀净空；这些失败保留，未替换原7条路径。选定`recontact-bank.json` SHA256为`6472245112f70b35057132da31674c41dcda163b24019de1b81021b04d4971ad`，`selected-summary.json`记录每条来源及指标，均已同步本地。只是在MuJoCo内做静态几何/载荷计算，没有推进物理，不能称sim2sim或重新接触通过。GPU短程初始化v182及后段v181继续等待既有世界模型作业释放资源。







v128目录的`reference-settling-audit.json`为远端CPU上的参考信号检查：直接调用当前提取的限速函数，0.01/0.05/0.10/0.20rad固定目标均在20秒检查末段收敛，没有持续振荡，故目前没有证据将失稳单独归因于该函数。此检查不含机器人或物理仿真。v141/v142/v144及v143静态审计均已完成，不再重复启动。下一步验证新姿态连续过渡与新路径到原生接触门禁的衔接，再进行动态接近、受载净空及推箱检查。落脚误差和后续位移分开报告，不用非活动缓存判断已完成阶段，也不把阶段成功当完整PUSH。v117冻结快照107个源码哈希由每次launcher逐一核验，保持不变。

v126/v127均须先达到v125实际稳定保持，再执行受限机身XY转移及FL卸载，尚不执行水平摆脚或推箱。复用CLIMB已有数学函数，源码来源在各目录`helper-provenance.json`；进入准备控制后显式覆盖腿部参考，不能把旧`motion_ready=false`误读为腿部没有动作。原生碰撞、执行器/延迟、PUSH物理终止项均未改，臂仍保持原准备姿态。释放条件保持实际选中足≤5N、其余三足各>8N、支撑裕量≥25mm及机身平稳，连续0.2秒；腿部参考限速0.8rad/s、限加速度3rad/s²。准备试验不计入完整PUSH验收，原报告保留初始化遥测。仅同步小型计划、退出状态和摘要；完整报告留在远端。

v123/v124已完成三处记录工况的联合规划和独立静态受力检查。**这是构型提案，不是新的PUSH成功回合或已验证控制器。** 三个样本来自保留权重env0的16.26、16.98、17.80秒，选取原四足竖直力均>8N、手箱合力20～40N的记录；不覆盖首次碰箱的高峰冲击。当前正式来源仍为v117，原24秒已用种子30/32、31/32及12秒0/8结论不变。

规划将机身前移、降低、足位和接触高度一起求解。仅降低机械臂静态力矩的早期提案在全身支撑检查中被拦下；随后同时要求有记录推力和零手部力时，每足预留≥8N支撑，并将剩余支撑力中心保持在支撑多边形内至少10mm。独立线性力平衡检查还限制腿部静态力矩≤90%限额，采用`|Fx|+|Fy|≤0.4Fz`的诊断摩擦锥。该摩擦模型是静态设计假设，不能代替实测滑移/接触验证。

最终采用`push-supported-posture-v123/coherent_support/`分支，底盘俯仰增量固定在1e-7rad容差内，避免三个端点采用不同俯仰分支；臂腿参考的连续路径仍未验证。结果如下，力矩比取对应肢体中最大值：

| 原记录时间 | 有载机械臂力矩比 | 有载/无载腿部力矩比 | 臂—保护几何净空 | 规划足位前移 |
| --- | --- | --- | --- | --- |
| 16.26秒 | 0.8400 | 0.5887 / 0.5937 | 47.46mm | 9.43cm |
| 16.98秒 | 0.7847 | 0.4834 / 0.4755 | 35.00mm | 10.86cm |
| 17.80秒 | 0.8500 | 0.5050 / 0.7391 | 48.80mm | 6.36cm |

相对原记录，机身计划前移约15.43～18.33cm、降低4cm，接触材料点沿箱体竖直方向上移6cm，仍在原合法箱面高度范围内。材料点目标不能直接当作原控制器的手端中心高度参数，须结合末端姿态转换。接触点误差≤0.2mm，手—箱几何间距约±10微米；原80mm刚体中心门禁的静态距离为101.5～125.6mm。在排除焊接及直接相邻刚体的几何比较中，没有发现相对原记录新增的非相邻刚体穿透；这不是完整原生碰撞或运动路径证明。中间端点贴近35mm边界，后续须关注动态余量。

v124用匹配v117的Isaac原起点、seed3701、8环境，仅执行1个控制步采集实际PhysX质量/质心，env0首帧与旧报告逐字段相同。总质量21.7650kg；`push-support-wrench-v124/startup-physics.json` SHA256为`baf2fea4657817105ea9c0f6d59f6e18fa605433a92ac6e6453a9115b1ac0318`。该单步采集的`valid:true`仅表示参数采集及来源核对有效，不表示PUSH完成。随后用这些质量/质心复算静态重力、足端反力和腿部力矩；最终有载/无载力平衡报告分别为`coherent_support-force1-balance-results.json`、`coherent_support-force0-balance-results.json`，哈希为`5874ed14c3c49b6908bfbbd13de8eaa846768950f2d7bf50f14440a081935f26`、`de7e1f54f10f064108570b29fe9fe181a6a209b3e53ef2ce2ed2ce896c811eec`。

本轮静态任务和参数采集均已结束，未改变或执行v117控制器。入口为v123的`coherent-summary.json`和`coherent_support/`；根目录初次因缺少独立腿部运动学辅助文件退出的记录保留，不能据其旧失败状态否定后续结果。显式补齐辅助文件后已核对解析腿部FK与模型几何；各规划分支、源码哈希和退出状态独立保存。本地仅同步摘要、最终端点与必要参数，原大报告留远端。

**下一步：**构造保持真实支撑的逐脚落脚与机身转移参考，验证进入、接触力消失后的退出及端点间连续性；遵守原关节参考限速、碰撞、执行器、合法手箱接触和停稳门禁。不能同时平移四足、瞬移机身或直接插值这些关节向量冒充可执行轨迹。还要处理首次碰箱冲击，再进入既有远端Isaac的明确标注阶段诊断；原起点12秒、未用种子和MuJoCo验收均未因此通过。

v121两组256迭代及最终24秒/12秒评估均已结束。已用seed3701、8环境、原起点24秒中，两组仍为**7/8，超时1，缺失0**；原12秒均0/8、全部超时。没有新增碰撞/无效接触终止，但降低饱和的目标没有明显实现：`joint2`累计饱和从v117基线16.60秒变为17.06/16.16秒；低于35mm的环境步从592变为621/603，最低全程净空仍19.214mm。两组成功耗时16.54～18.82/16.42～18.74秒。保留v117的30/32、31/32权重，v121不晋级、不继续盲目延长。完整报告审计和实际checkpoint核对确认两组原腿部特征层/输出逐值不变；结果在`push-arm-load-retrain-v121/final-audit.json`及`training-comparison.json`。末版权重SHA256为`53c8d0914ba30622acbf614a50ed19b283c69b3110e2e084b3fa363ef1ec988b`、`4007cae365f35bc646aef62dbfabb87af577a9610b3c2521ea48c288360e90a7`，仅留远端实验产物，不替换保留候选。

后续`push-load-mechanism-v122/`使用已有连续成功轨迹做静态受力分解，没有新增动力学回合。env0在v117及v121两份末版分别有141/145/142个合法接触控制样本；全18关节和机身姿态恢复后手端FK误差最大1.55微米。v117的`joint2`静态重力项绝对值约14.99～16.03N·m；加上记录的手箱合力及接触点后，静态平衡力矩绝对值中位数约23.71N·m，超过20N·m限额。125个实际饱和样本中120个的静态估算也超过限额，两份v121分别122/130、119/127。该分解不含惯性、阻尼、未测接触力矩及其他外力，不能作为任务不可行证明或动力学复现；详细假设和来源见`load-summary.json`及远端`recorded-load-audit.json`。

同时核对到硬限位附近的实际位置：v117的141个合法接触样本中，63个`joint2>3.13rad`，38个距源硬上限3.1399998rad不超过1mrad；最大实际角3.140002rad，而控制器参考最大2.9829998rad。两份v121同样出现近硬限位样本。这里只测到了角度，尚未直接测得关节限位约束反力，不将其改写为已证明由限位承重；证据见`limit-observation.json`。

在15.60、16.74、17.92秒三个实际接触姿态上，分别完成4个固定预算的静态优化起点，暂未找到同时满足接触点误差≤2mm、姿态变化≤0.35rad、净空≥35mm、非手部箱体间隙≥5mm及90%静态力矩预算的构型。求解器均未收敛到可行点，失败的有限搜索不证明全局不可行；固定机身与记录接触点尤其限制了解空间。原Isaac软限位因子0.9与静态运行时范围匹配，未扩大限位。下一步优先验证更短受力臂的承力构型与底盘相对位置，须保留真实足端支撑并再做Isaac动态验证；不靠增加电机限额、减轻箱体或放宽接触判据宣称解决。v121和v122本轮任务均已结束，旧PID不可复用。

v120两组只读探针已正常结束，完整终态、env0轨迹、终止原因及原有关节遥测与v118/v119逐字段一致；新增记录未改变这两组物理结果。阶段统计覆盖全部32环境的控制调用，含初始化，仍不覆盖所有物理子步。机械臂`joint2`是主要饱和关节：原批次逐关节统计累计饱和73.14/74.20秒，每环境最大2.82/2.80秒。腿部饱和累计仅后腿大腿各0.02～0.08秒量级。不能把推箱阶段的持续饱和归因于初始化或腿部行走。

| 阶段 | 最低控制步净空，seed3701/2701 | 低于35mm环境步 | 任一关节饱和环境步 |
| --- | --- | --- | --- |
| 安全路点（包含初始化） | 19.700/18.530mm | 2072/2075 | 217/266 |
| 接触面接近 | 18.539/17.115mm | 263/259 | 0/0 |
| 实际推箱 | 14.908/13.939mm | 129/105 | 3451/3480 |
| 目标保持 | 44.352/42.638mm | 0/0 | 128/127 |

推箱阶段分别3960/4071环境步，腾空均0，少于三足支撑778/783环境步；此处是PUSH行走统计，不将CLIMB的三足门禁移作PUSH判据。记录到的腾空均在包含初始化的安全路点阶段，分别117/133环境步；该阶段全批次竖直速度峰0.913/0.981m/s、单足接触合力峰302.16/292.84N，不能再用先前env0峰值代表全批次。实际推箱的手部合力峰86.71/96.10N。详见`push-phase-audit-v120/phase-audit-summary.json`（SHA256 `1f2e44197e99b6bad57d9c6acea563d8bd46b19a44309b5259e76d1ecb581b17`）；原两组探针报告SHA256分别为`8f01bec94d0efd98a02939ce236809e40f9ed03120ddaea95015c75d1360e2b0`、`cfd91215fc9c969867c269bb2716940092be1944b6ad40b7afc4b206409b1c8e`。

根据上述实测，v121从保留的seed7512/model255继续训练，先针对受载机械臂饱和。旧负载代价为六关节超出85%限额幅度的平方均值；仅一个关节达限额时，加权瞬时代价为0.015。现改为按15%余量归一化、取最重载关节平方值，原权重-4保留，单关节达限额时加权瞬时代价为4（均在时间步缩放之前）。这是训练目标变更，不改实际力矩上限、控制器、原生自碰或终止判据，也不保证优化后保住成功率。接近阶段净空、初始化瞬态及原12秒超时仍须另行处理，不能期待该机械臂接管后的训练解决它们。

远端`push-arm-load-retrain-v121/`，隔离源码`train/`；与v117的107份冻结源比较，仅`scripts/rsl_rl/safe_retraining.py`变化：负载代价、从完整18维actor初始化及机械臂探索尺度。初始18维均值与保留权重完全一致，原特征层和12维腿部输出继续冻结；价值网络、优化器重新初始化。学习率3e-5，腿/臂探索标准差1e-4/0.10，每迭代32步。初始化与100次Adam更新检查通过：腿部输出逐值不变、机械臂层实际更新；新负载代价正确区分85%以内、单关节达限额及六关节达限额。`plan.json` SHA256为`84a196bcf0ffe74f8fa2784f5fffcfa853c0ea7ec3d788909b835fe09f3d9d13`。

工作流PID1008206此前完成seed7610、4环境、64迭代冒烟及GPU0/1的seed7611/7612各16环境、256迭代，并完成最终24秒/12秒诊断，现已退出，结果见本节开头。实际序列化配置核对确认终止项、仿真参数、初态事件、执行器、箱体物理和机器人USD字节与v117一致，见`safety-config-check.json`。新摘要、计划和必要源码已同步本地，原始大报告及未晋级权重留远端。

2026-10-11恢复核对：v119已正常结束。同一份seed7512/model255在已用seed2701、32环境、原起点24秒诊断中为**31/32，超时1，缺失0**，没有触发机身接触、无效手接触或姿态失败终止；成功耗时16.04～18.86秒。加上v118已用seed3701的30/32，说明该权重在扩大诊断中保留了大部分成功路径，**仍不是两组未用种子或原12秒验收**。seed2701最低控制步净空13.939mm、2439环境步低于35mm目标、含初始化最大力矩限额比1.0；安全余量和耗时问题尚未解决。报告SHA256为`e0f4903f1dd08029ca2171f100f4c466983951cd276e9eb203d2d3cd9f71c80b`，完整来源、终态、物理契约和逐关节饱和审计见`push-arm-confirm-video-v119/completed-audit.json`。

v119原速录像对应seed3701、8环境诊断，7/8成功、超时1、缺失0。录像完整解码600帧、25fps、24秒；env0在18.72秒成功后被仿真自动重置，完整录像尾段包含重置。`video-trained7512-used3701-8env-24s/episode0-until-success-original-speed.mp4`仅保留到该成功终态，没有变速；原完整录像和裁剪命令/哈希保存在同目录。已检查12个关键帧，看到前段机械臂接近、约15.6秒起推箱和成功后的重置；这不等于连续回放或几何无碰撞证明。完整录像SHA256为`ede5e62b6eff79a94cab8395baeca4115f8c876eac2da4c08140ade228c1cfd6`，原速终态片段SHA256为`563f77c4e7fd7951752bef357ab85c8ae9f95b2bd7b61bf7633a5e592d1ce799`。本地已同步录像和小型摘要，未下载原始大报告。

v120旧launcher PID1003610/1003611已退出，结果和轨迹一致性核验见本节开头。107份原冻结源保持原哈希，只增加独立评估器与记录辅助文件。辅助检查确认返回动作和输入未变、阶段计数正确、已完成环境不再计数；原始回合和只读探针报告分别保留，不重写历史结果。

2026-10-10 21:00（北京时间）：v117两组256迭代已正常结束。固定原腿部网络、仅训练接触面就绪后的机械臂修正，在已用seed3701、8环境、原起点24秒诊断中，两组末版均为**7/8，完整终态8/8、缺失0**，原生机身接触/无效手接触/姿态失败均0；原12秒检查仍均**0/8、全部超时**。这比v116末版0/8改善，但仍不是安全候选或sim2sim通过。两组均保留作扩大批次对照，不按小批结果宣称鲁棒性。

| v117最终权重 | 24秒成功/失败 | 成功耗时 | 最低控制步净空 | 低于35mm环境步 | 含初始化最大力矩限额比 |
| --- | --- | --- | --- | --- | --- |
| seed7511/model255 | 7/8，超时1 | 16.76～19.26秒 | 12.143mm | 847 | 1.0 |
| seed7512/model255 | 7/8，超时1 | 16.48～18.72秒 | 19.214mm | 592 | 1.0 |

两组同为env4超时：安全路点已完成，但原接触面就绪条件未满足，机械臂修正和腿部接管未生效；env4末态手端目标误差约73mm前后、55mm横向，净空53.46mm，末态几何屏障未阻挡。不能据此降低就绪门槛，也不能仅以更长训练解决一个训练动作尚未接管的阶段。env0独立时间记录为安全路点12.42秒完成、接触面就绪15.46秒、首次合法手箱接触15.60秒，说明原12秒窗口的主要障碍还在前置接近流程；不能将env0时间当作env4时间。证据见`approach-timeout-audit.json`。

最终权重哈希分别为`1e48b03a815064fd6e901a6024658ec05634aa2991afc271236f4d646a770ced`、`38e2964d89cd6fdcc0b3d0d20b33ab40753da3f1724690483451d2d8f45809ae`。实际checkpoint核对确认原特征层和12维腿部输出逐值未变，见`final-network-check.json`；四份报告完整性、控制源码、107份冻结源哈希及实际物理匹配均已审计，见`final-audit.json`。24秒env0记录963/936帧，少于三足支撑45/41帧、腾空均6帧（竖直足力>2N）；含初始化竖直速度峰均0.730m/s，单足接触合力峰170.15/180.57N、手部合力峰34.94/83.01N。以上支撑/力峰仅为env0控制步记录，不能代替全批次或物理子步；全批次逐关节饱和时长在审计中。24秒报告SHA256分别`29a8df2a0deb4a0e7d98f141f221995b890bcf387a7eb22689ff3f9601a36a4b`、`63e73e4830e3eb85ddab7cc2af2e7738f74747ece084e4c0e86a1fe08c5fe255`。

2026-10-10 22:00核对：v118两份固定末版在同一已用seed3701、32环境、原起点24秒扩大诊断中，**7511为29/32（机身接触1、超时2），7512为30/32（超时2）**，均完整终态32/32、缺失0。7511排除；7512保留为后续诊断权重，尚非安全候选。两组最低控制步净空2.486/14.908mm，低于35mm目标3486/2464环境步，含初始化最大力矩限额比均1.0；7512成功耗时16.12～18.90秒。两组超时均为env4/20，安全路点完成而接触面未就绪；7511另有env16在15.56秒机身接触失败。

v118首次后处理将8环境与32环境的逐环境质量/材质数组直接作整字典比较，误判为物理差异；两份原`exit-status.json`的`valid:false`保留。`revalidate.py`逐项确认32个质量均5kg、摩擦/恢复系数均与8环境参考相同、其他物理参数完全一致，并重新核对报告/权重/源码哈希及32个唯一完整终态。新`report_revalidation.json`记录复核通过和原文件哈希，`batch-audit.json`汇总结果；没有修改报告、物理门禁或重跑回合。比较器已验证可拒绝单环境质量/摩擦变化、数量缺失和仿真步长变化。不能仅凭旧退出状态推断该批没有有效报告。

v118的env0控制步记录分别961/942帧，少于三足支撑41/42帧、腾空均6帧；含初始化竖直速度峰均0.729m/s，单足接触合力峰172.73/184.79N、手部合力峰34.51/83.13N。仍仅覆盖env0控制步；全批次逐关节饱和时长及数据范围在审计中。两份最终权重共约8.65MiB、审计及元数据已核验同步本地，原始大报告仍留远端。

上述v119诊断与录像已完成，旧launcher PID1000415/1000416已退出，结果见本节开头。权重、控制源码和门禁未变，逐环境质量/材质及其他物理参数均核对通过。原12秒当前仍0/8，实机继续暂停。

v117针对v116暴露的训练耦合问题：此前机械臂修正在原接触面就绪前介入，且腿部尚未接管的样本仍共同更新共享网络。现保留原model199的全部特征层及12维腿部输出，梯度只更新新增6维机械臂输出层和其探索尺度；机械臂修正仍为`0.20*tanh(action)`，但仅在原`safe_approach_complete & approach_face_ready`锁存成立、未目标保持/锁臂时生效。训练采样也只取对应生效阶段，回报仍来自完整物理轨迹。残差继续位于原关节软限位、参考平滑和几何屏障之前；未更改原接触面进入条件、真实接触、原生自碰、执行器、5kg/0.4摩擦、0.60m推进及停稳判据。腿部均值网络固定，训练腿部探索标准差固定为1e-4；评估使用确定性均值。不是重新训练NAV。

这是一个受限的机械臂学习实验：只训练固定特征上的6维输出层，不等于已经得到通用机械臂策略，也不保证解决承力问题。接口仍为226→18，但运行时必须匹配v117的残差生效阶段，不能混用v116或旧226→12运行时。初始化及100次Adam更新静态检查通过：64组随机观测上腿部输出始终与原actor逐值相等，机械臂输出实际改变，腿部探索尺度保持固定，价值网络未被旧权重覆盖；结果见`initialization-check.json`。该检查不替代物理冒烟或安全验收。 实际物理冒烟已进入训练迭代；序列化配置核对确认终止项、仿真参数、初态事件、机器人执行器、箱体物理及USD字节与v116一致，见`safety-config-check.json`。

远端目录`/path/to/artifacts/go2-piper/sim2sim-current-20261008-a/push-safe-arm-retrain-v117/`，隔离源码`train/`；107份源文件冻结，`plan.json` SHA256 `7e91b851c3d0a23340f936f81582edda97983ae2659f7ede7f7944dc0d5c0617`。工作流PID992942已完成seed7510、4环境、64迭代物理冒烟，正常退出；2048次控制调用、1282个修正生效环境步，机械臂输出层最大绝对权重0.007493，原特征层及腿部输出逐值未变。冒烟只通过启动/更新检查，安全尚未通过：最低控制步净空20.460mm、627环境步低于35mm，最大力矩限额比1.0。冒烟权重SHA256为`c8a2b2923d072ca1f4ea4b2222a44b52b3ad9bcd086d0d124895b3882fe0f9bf`，结果在`smoke-seed7510/validated.json`及`optimizer-check.txt`。随后GPU0/1上的seed7511/7512各16环境、256迭代均已正常结束，旧工作流和worker已退出，最终物理评估结果见本节开头。学习率1e-4、每迭代32步、每64迭代保存；最终各自已自动运行已用seed3701、8环境的24秒诊断和原12秒检查。恢复时先查`workflow-state.json`和实际进程；本地仅同步摘要、计划及必要源码。尚未形成候选，未启动未用种子验收或实机。

#### 已结束并排除：v116联合腿臂训练

v116两组末版`model_511.pt`在原起点、已用seed3701上，24秒及12秒均**0/8**，每批完整终态8/8、缺失0。24秒seed7411为机身接触3、无效手接触1、超时4；seed7412为低姿态4、无效手接触1、超时3。箱体最大前进分别92.29/163.83mm；最低控制步几何净空17.855/19.198mm、低于35mm目标594/588环境步，含初始化最大力矩限额比均1.0。12秒两组全部超时，env0在整个600控制步内尚未完成安全接近，箱体位移不足0.1mm；保留原起点12秒门禁，24秒仅作机制诊断，不能以延长时间冒充通过。

四份报告的完整性、权重、评估器、控制源码和114份冻结源哈希核验通过，`actual_physics`与v105逐项一致。24秒env0记录分别793/893帧，按足部竖直力>2N统计，少于三足支撑8/38帧，腾空均6帧；含初始化竖直速度峰均0.730m/s，单足接触合力峰119.82/144.15N、手部合力峰15.69/33.17N。支撑/力峰仅覆盖env0控制步，不代表全批次或物理子步；全批次逐关节饱和时长保存在`final-audit.json`。四份报告哈希、终态和时长分组均在该审计中，本地已同步摘要，原大报告留远端。两组权重SHA256分别`54535cc950e71867241b905c8e4c055349d62ec334dbf4c1d2d1c016ff1cdf25`、`58142fe54a93212eacec2e4a2b2bc1364e443ed77550fa8dc48a1eecc9ed5422`。旧工作流和worker均已退出，不再恢复为活动任务。

以下为v116来源和中途证据记录。

用户已明确要求转向重新训练，停止以反复修改旧控制参数作为主线。下方 ARX5 复核及 v33–v115 保留为历史依据。**v116 是新的实验策略接口，不是已通过安全验收的候选。** 新策略仍使用226维观测，输出从12维变为18维：前12维腿部动作，后6维通过 `0.20*tanh(action)` 生成机械臂关节目标修正；修正只在安全路点完成后、未进入目标保持时生效，并位于原软限位、参考速率限制、机身净空投影及最终几何屏障之前。不能交给旧226→12运行时，也不能解释为旧210→18 NAV接口。

训练从原 `model_199.pt` 的腿部网络初始化，机械臂输出均值置零，价值网络和优化器重新初始化；没有重新训练平地NAV。控制链固定为v105加上述残差入口，不在训练期间扫描高度/速度/接管时间。训练奖励保留原完成/失败项，降低纯速度跟踪权重，以原合法接触下真实箱体推进为主要过程奖励，增加臂力矩负担、净空不足及近箱追赶的代价。5kg、摩擦0.4、20cm箱体、0.60m目标、原生自碰、合法接触、执行器与停稳终止均保留。首阶段关闭观测噪声，仍保留原起点扰动，尚非随机鲁棒性训练结论。

远端产物：`/path/to/artifacts/go2-piper/sim2sim-current-20261008-a/push-safe-retrain-v116/`；本地同名副本位于仓库外 `../artifacts/go2-piper/sim2sim-current-20261008-a/`。使用隔离源码 `train-v2/`，训练计划 `plan.json` SHA256 `33c1d17214536a82e855de591c2cfe0fa617cc380d7aef6faeee4ee3f2e70167`。首次准备仅因评估器schema断言退出，未启动物理；保留原未完成的 `train/`，修正后另建 `train-v2/`。其后仅修复专用评估器与已安装 `rsl_rl` 包的导入重名，训练源码未变；冒烟启动时的原计划和新旧哈希另存 `plan.before-evaluation-import-fix.json`、`evaluation-import-fix.json`。

初始化检查已通过：64组随机观测上前12维输出与原actor完全一致，新增6维均值为零，价值网络未被旧权重覆盖，残差入口在限速和最终屏障之前；结果在 `initialization-check.json`。实际冒烟配置与此前固定安全配置的终止、物理、初态事件、执行器及箱体参数逐项一致；机器人资产目录不同但USD字节哈希相同，见 `safety-config-check.json`。远端工作流PID978554已完成seed7410、4环境、40迭代冒烟，退出码0：1280次控制调用、916个可控环境步；新机械臂输出层最大绝对权重0.004513，腿部输出层最大变化0.004006，确认两部分都实际更新。检查只通过训练链路，**未通过安全验收**：最低控制步净空17.593mm、498个环境步低于35mm、最大力矩限额比1.0。冒烟最终权重SHA256 `134c1a7efe7cba30ab404a883587fc6a403544bf13521615d615ffaa57ae0125`，见 `smoke-seed7410/validated.json` 和 `optimizer-check.txt`。工作流此前自动启动GPU0/1上的seed7411/7412两组独立训练（现已结束），worker PID979051/979052；各16环境、512迭代、每迭代32步，每64迭代保存。学习率1e-4，腿/臂初始探索标准差0.12/0.30。恢复工作先核对 `workflow-state.json`、实际PID和各 `run.log`，不能根据旧PID重复启动。

历史中途记录（2026-10-10 15:59北京时间，已被上述最终评估更新）：当时两组训练仍在运行，最新日志分别为288/512、248/512迭代；近期训练完成项仍为0，不能宣称学成。固定第64次迭代的两组权重已完成已用seed3701、8环境、原起点24秒确定性诊断，**均为0/8，完整终态8/8、缺失0**。seed7411八次均超时，箱体前进最大9.21mm、终态接触面就绪0/8；seed7412无效手箱接触6次、超时2次，前进最大85.02mm、接触面就绪6/8。两组原生base_contact终止均0，但最低控制步净空均19.199mm，低于35mm目标分别582/590环境步，含初始化最大力矩限额比均1.0；不能解释为安全通过，也不能用第64次迭代结果代表尚在训练的最终权重。

审计已核对114份冻结源哈希、actor/评估器/控制源码来源，两份报告的`actual_physics`与v105逐项一致。env0从首控制步连续记录分别1200/795帧：按足部竖直力>2N计算，少于三足支撑均8帧、腾空均6帧，含初始化竖直速度峰均0.730m/s；单足接触合力峰119.82/140.00N，手部合力峰0/32.90N。这些支撑/力峰属于env0控制步记录，不是全批次或物理子步峰；完整批次逐关节力矩饱和时长已保存在`early-iter64-audit.json`。报告SHA256分别为`3e34c3a1d4e9565d511fde3639238fb5f37988b5e11438a73a930a97503a88da`、`1bbc3e4925e449330bf523685a0842b0def0a6021e04dca97b1138d6066dfd53`。seed7411的env0未形成合法手箱接触；seed7412的env0形成接触后于15.90秒无效接触终止。该中途证据说明接近/承力协同尚未学成；随后已完成上述512迭代和最终24/12秒评估。

有效报告目录为`early-seed7411-iter64-used3701-8env-24s-retry1/`和对应7412目录，两组均已结束。首次启动因缺少`push_shadow_observer.py`在环境创建前退出，虽返回码0但报告缺失，原目录的退出状态保留`valid:false`。补齐两个仅评估使用的observer依赖，来源与哈希见`evaluation-dependencies.json`，训练未重启。恢复工作须核对实际进程、报告完整性及哈希，不只看退出码。`collect_progress.py`更新远端小型`training-progress.json`；本地已同步并核对两份结果摘要、审计和来源元数据，原始报告仍留远端。

正常完成后，各组已自动以匹配新接口的 `scripts/evaluate_residual_push.py` 对最终权重运行已用seed3701、8环境的24秒诊断与原12秒检查。24秒训练/诊断不是12秒验收；尚未运行两组未用种子各32回合，未产生安全或sim2sim通过结论。控制步遥测包含首次调用的力矩、净空和残差幅度，但不代表物理子步全程安全。原速录像、全批次支撑/力峰审计和双仿真验收仍是候选交付门禁。新源码及权重暂存仓库外，不提交未验证候选、不增加冗余GitHub推送。

#### ARX5 历史修复复核与后续方向（2026-10-10）

按用户要求复核了 ARX5 技术指南、实际控制源码、历史提交 `6367b5c860f374b2ac831ded4ce67123d1a56fde`（2026-09-20，`Fix collision-safe staged box pushing`）及原始单回合报告。**确有可复用的控制设计，但没有找到可直接证明 Piper 原任务已解决的验收结果。** 本次是文档、源码与已有产物审计，没有新增物理回合；远端核对时两张 GPU 均空闲，未发现目标训练/评估进程。

历史来源位于 `/path/to/user/re-nav/GO2-ARX5-MUJOCO/`：`docs/GO2_PIPER_PUSH_CLIMB_COLLISION_GUIDE_CN.md`、归档 `docs/archive/pre-handoff-20261007/docs/STATUS_AND_NEXT_PLAN_CN.md.txt` 的“关键证据与产物”、`mujoco/reconfigurable_navigation/box_push_runtime.py`。复核同时读取了 Git 提交差异，避免把当前工作树当作当年的完整实现。

| 核查项 | ARX5 历史实现/证据 | 当前 Piper v105 与处理结论 |
| --- | --- | --- |
| 旧成功率 | 旧 29/32 曾关闭臂—机身碰撞，已在原交接中作废 | Piper 原 30/32、32/32 同样不能证明本体碰撞安全；继续使用开启自碰的诊断 |
| 接近与承力姿态 | 安全路点后持续位置 IK，并用 null-space 姿态回拉保持推箱构型 | v105 已有安全路点、重力补偿、关节限位、参考平滑及几何保护；尚无等价的持续承力构型目标。现有六维姿态 IK 和净空偏好不等价于该设计 |
| “锁臂”的准确含义 | 该提交明确删除 `locked_reference` 的关节冻结；`locked` 保留相对手端位置作为策略观测，机械臂继续 IK，并将压入目标移回箱面 | v105 当前 `lock_arm_on_contact=false`；其旧开关仍会用 `locked_reference` 覆盖关节参考，直接开启并非复用 ARX5 修复。此前旧流程还在未接触前自碰，不能据此排除正确语义的持续 IK 方案 |
| 腿部与机身协同 | model700 → 第 150 控制步 → model900；箱速和机身间距反馈 | Piper 已有箱速/间距反馈，并非漏掉反馈；目前单 actor 与安全控制链不匹配的风险仍需验证。ARX5 actor、关节姿态和切换时刻不能直接移植 |
| 任务负载 | 修复提交把箱体从 5kg/摩擦0.4 改成 3kg/0.2；综合序列常用 3kg/0.3 | Piper 仍为 5kg/0.4。仅按水平滑动的 μmg 粗估为 19.6N，对比旧单例约 5.9N，约 3.3 倍；不是实测接触力，也不构成机械臂不可行证明 |
| 判定与净空 | 同一提交将 MuJoCo 手端接触半径从 70 改为 110mm，Isaac 禁止/无效接触改为持续 0.25s；MuJoCo 臂—机身目标净空 3mm | 不复制这些数值或判定变更。当前合法接触、自碰、原执行器/停稳门禁及附加几何目标继续保留。旧函数对安全终点直接返回，仅回退分支检查插值，不能作为完整路径/动态安全保证 |

原始 `/path/to/user/re-nav/artifacts/push-safe-staged-20260920/seed2-staged700-900-m3-f02.json` 只有 **1 个 seed2 回合**：3kg/0.2，4.44秒，推进0.59896m，目标误差9.15mm，22个合法接触步。其 `passed=true` 是单例比例检查，不能理解成32回合验收。历史交接另记3kg/0.3连续执行器 PUSH 26/32；本次未复算该远端报告，作为历史文档记录，不升级证据。两者均不覆盖当前 Piper 的原任务和安全要求。

耗时原因包括原成功路径依赖关闭自碰，打开后必须重新协调可达姿态、真实受载与底盘跟随；同时此前多轮只改高度、速度或接管时长，收益已很低。应更早逐项核对历史修复并补齐成功/失败的连续受载轨迹。这是工作方法需要纠正的部分，不能归因于 GPU 数量不足，也不能用更多迭代替代机制诊断。

后续保留 v105 为诊断基线，暂停仅调接管时长/近距速度的扫描。先用 v112/v113 同源连续轨迹确定接触初期可保持的承力构型，审计手端目标、实际接触点、机身相对位姿、IK与几何修正方向和力矩余量；据此设计 Piper 专用的持续 IK 姿态引导，必要时联合调整机身相对位置，避免仅在已饱和终态固定机身搜索。切换须基于实际合法接触，关节参考保持连续，不冻结实际物理关节、不直接打开旧锁臂开关。先验证一项明确机制能否改善完整推进与净空，再决定匹配腿部策略训练；未找到满足门禁的方案就保留失败结论。当前 v105 仍仅4/8、17.14～17.74秒，最近 v114/v115 为3/8、1/8，**安全 PUSH 尚未完成**。

相关 Piper 世界模型文档 `PIPER_PUSH_POST_CONTACT_STALL_V1_CN.md`、`PIPER_PUSH_DRIVE_CONTACT_AUDIT_V1_CN.md` 也说明 `drive_contact=false` 不等于箱体停止、`hand_contact=true` 不等于持续有效施力。这些属于旧来源事后审计，仅作机制参考，不能混入本次安全候选统计。

**尚无通过验收的无本体碰撞 PUSH 候选，实机暂停。** 原 `aa/model199` 的30/32、32/32来自关闭本体自碰的配置，只能保留为历史仿真参考。当前在既有远端的隔离运行树开启原生自碰，保留指定手箱接触、无效接触终止、执行器限制和停稳门禁；未修改冻结权重。以下均为**已用 seed2701、8环境、原尺寸5kg/0.60m、24秒延长诊断**，不能作为原12秒或两组未用种子验收。

| 对照 | 完整成功 | 安全/任务失败 | 报告 SHA256 |
| --- | ---: | --- | --- |
| 原0.20m中心距、25mm几何目标屏障 `v33` | 1/8 | 自碰1、无效手接触5、超时1 | `5e50b8195f173a804782e19a6de2a68c0dfe2f357c9b0b8d9e760df026b8b9bd` |
| 原0.20m中心距、预测屏障 `v36` | 0/8 | 无效手接触3、超时5、自碰0 | `122aac22673a56a8933de49ab4640f773c26114865ddbd7967431a48bc531aac` |
| 恢复原0.10m中心距、25mm预测屏障 `v39` | **6/8** | 无效手接触2、自碰0、终态缺失0 | `edb0f5f054c0c34b2d37ece5d00ae63c9223ac960ccbd4534a956e9a6de91ab6` |
| 在同配置把手端俯仰改为0.6rad `v40` | 5/8 | **原生自碰2**、无效手接触1；排除 | `b3d4f885e322061ba798de64f6dceac528e532a1613f702f62ba00517ce74840` |
| 同配置压入从0.10m减到0.08m `v41` | 6/8 | **原生自碰1**、超时1；排除 | `c98b8e7764f29c685d47c4ae810930093c4e388a5dcd878dfc001cdf357467a0` |
| 同配置手端俯仰0.8rad `v42` | 7/8 | **原生自碰1**；排除 | `31f3d8f72e8b45d865061d6fb7272dc0efe2559dd6687a141162119294a86232` |
| 原0.10m中心距、俯仰1.0rad、压入0.10m、`joint4`参考下限0.8rad、25mm预测屏障 `v44` | **8/8** | 自碰0、无效手接触0、终态缺失0；**仅已用种子小批诊断** | `048964d69b24ad6caf0bb70ad8a8c7defde9d8ac28bba2574fd3ee753f20b88a` |

`v44`八次成功的终态时间约15.40～16.96秒，**未满足原12秒窗口，也未经32回合鲁棒性、未用种子、MuJoCo和原速录像检查**；不能称为训练完成或实机安全。`v39`两次失败在推进约0.27/0.35m后，指定手部刚体中心与接触点相距约90mm，超过原70mm合法接触半径；`joint2`接近3.14rad上限并触及20N·m力矩限值。`v44`用关节参考下限避免该两次失败，但本批最大力矩限额比仍为1.0，饱和持续时间及初始化阶段尚未完整审计。**不能通过扩大合法接触半径或关闭自碰把失败计为成功。** 0.20m中心距是新增的保守诊断值；恢复原0.10m不降低原任务门禁，25mm凸包目标屏障仍是额外约束。屏障检查机械臂/机身凸包及100ms关节速度外推，尚不覆盖臂腿几何、物理子步或制动保证；原生自碰终止仍须保留。`v35/v37`高度门禁分别8/8超时、箱体几乎未动，`v38`在原中心距下仅2/8成功；不保留为候选。`v32`报告因非有限净空值写入而截断，旧退出文件误报成功，**不得引用为有效物理结果**。原始报告、计划和日志位于远端`sim2sim-current-20261008-a/push-safe-detour-v33`至`v44`，已完成报告的本地副本在仓库外同名目录。

扩大批次后的反证（均为已用种子、24秒延长诊断）：`v46`在seed3701的32环境仅**22/32**完整成功，自碰7、无效手接触1、超时2、终态缺失0，报告SHA256为`a01f04b577f9c9f0c1269d35daf91eaf84b3000b457981d11a2933ed54f55100`。七例自碰发生在首次合法手箱接触之后，`joint2`制动力矩已触及-20N·m，底盘仍收到约0.48～0.50m/s前进命令。`v47`在seed2701的32环境为**27/32**，自碰1、超时4、终态缺失0；控制步实际凸包净空最低**-2.12mm**，合计966步低于25mm目标，报告SHA256为`5db1268ac4df69d02c31954fc02500dde094895f4e0aa6da92519e92ae5b7c4e`。多数任务成功回合也跌破25mm，个别仅剩3～5mm。现有预测屏障不构成动态安全保证，`v44`的8/8不能升级为候选或安全结论。

`v48`按`joint2`重载和净空限制底盘推进，在seed3701的8环境为**0/8**，均24秒超时，箱体仅推进0.013～0.207m；自碰0但最低实测净空12.64mm，故既未完成任务也未守住25mm目标，报告SHA256为`af7cae13d55d6899577bff444f778d3dcbaef80fa8d098ea7f43078e7d09922b`。`v49`将`joint4`参考下限从0.8升至1.0rad，在同一已用种子的8环境为**6/8**、自碰2、终态缺失0，最低净空-0.77mm，报告SHA256为`145e1738225c589fdacf7a57677953c6ce9b5214a02df41bf4406ac3616c70b8`。两项均排除，不应以减速无自碰或姿态调整局部成功冒充安全版本。

继续在seed3701的8环境筛选：`v50`把手端俯仰从1.0升至1.2rad，为**4/8**、自碰1、无效手接触2、超时1，最低净空0.99mm，报告SHA256为`effdda06c7619fe4eeb3bb0cf15565cd2e61445091c2385992a0f2474c020ca7`。`v51`只将底盘前进命令增益从2.0降至1.5，为**5/8**、自碰2、超时1，最低净空-0.51mm，报告SHA256为`24eb3be21b82a8843f118d2d1ebba4e8d554619a24f63fd40d3788e1c2833191`。`v52`将增益降至1.0，为**0/8**、全部24秒超时，原生自碰0但最低几何净空仍为-0.51mm，报告SHA256为`8d50760cef878211c914bb881dc69b195c48ebca8d613dbd070cc4a0595be89f`。三项均排除；减小底盘命令不能同时保持推进和几何安全。

另在既有远端GPU1的隔离树`sim2sim-current-20261008-a/push-safe-train-v54/`启动原生自碰开启的PUSH训练：512环境、seed7302、200迭代、24秒训练课程，从未改的`model_199.pt`初始化；任务配置保留5kg箱体、0.4摩擦、0.60m目标、原执行器与接触/失败判据，`joint4`参考下限0.8rad及1.0rad手端俯仰。启动脚本SHA256为`e7596fe593b1f5b9f3f5ccff61150a5a3bd1ae619c3a4c008f0c205be753f10b`，计划SHA256为`7a88c3b9667898ffc5afdffa4fbb74ca31b0ec5ed152a379ccf7162e0a10bb17`；本地副本在仓库外同名目录。先前两次冒烟仅在Hydra配置解析退出，没有训练迭代；第三次两迭代冒烟正常退出，长训练另用新运行树及新种子。训练尚未形成候选，且训练阶段为吞吐量未启用MuJoCo预测几何屏障；后续必须在原生自碰、实测凸包净空和原12秒窗口下逐权重筛选，不能把24秒课程奖励当成安全PUSH成功率。

上述`v54`训练在约113迭代因`base_contact`约98%、`box_settled`仅约0.4%而主动终止，保留`model_50.pt`和`model_100.pt`，不延续为候选。`model_50.pt`哈希`d3a0ec7c31b74fde30a2240c55db6e6cb1446e9cd9877a518930bfb860c0e579`在已用seed3701的8环境、24秒`v55`物理复核为**5/8**，自碰2、无效手接触1，最低实测凸包净空-0.61mm，报告SHA256为`41b87ba40df33d05f9501c5e4f8b4cbb87548b7fb0aae2b7680ef9619c454ac2`；与原冻结权重的失败回合相似。该训练阶段不能靠继续迭代或训练奖励宣称安全，需改变接触负载/姿态规划。训练退出码134来自主动终止，原始日志和两份权重已同步到本地仓库外同名目录。

静态接触姿态诊断`v56`使用`v55`失败env1约12.8～13.04秒的记录、同源MuJoCo凸包、25mm保护净空及`joint4≥0.8rad`，按30N箱面推力估算`joint2`杠杆力矩。固定手端目标时，加权搜索只从8.73降至8.61N·m；手端目标上移3cm的静态可达解降至7.47N·m，下移3cm升至9.51N·m。最小静态保护净空均超过约69mm，但记录没有相同时刻完整腿关节，不能据此推断动态支撑或箱体上沿接触合法性。首次`observed-terminal`高度对照因脚本忽略位置偏移而无效；修正后`v2`报告及脚本保存在本地仓库外`push-load-pose-v56/`。随后`v57/v58`分别将手端目标上移2/3cm，在已用seed3701、8环境、24秒延长窗口中为**7/8、6/8**，各有1/2次无效手接触；两组均8/8完整终态、原生自碰0，但控制步实测最低保护净空仅**13.65/5.91mm**，分别有144/238步低于25mm目标，最大力矩限额比均为1.0。报告SHA256分别为`e8fd989e7e2900fa8613c1327aa8a26d377143e979aa8ac5a6fe42fc6e5da8c0`和`670b39bd004d98400fb3bda9378906fe68e45a01d598cda32a19fb0581ac82ac`；原件在远端`push-safe-eval-v57/v58/`，本地仓库外副本已核对。两项均排除，不以无原生自碰掩盖几何净空不足和非法接触。

`v59`仅做机身降低3cm的**静态支撑可行性筛查**：对原自碰失败报告30个已用初态，在7.5秒及接近8.0秒分别固定四足世界落点并求腿部逆解，共60个姿态的足端残差最大约3.2皮米；7.5秒最小硬关节限位余量0.611rad、四足原接触力最小26.9N。但7.5秒已有7/30、接近8.0秒已有23/30的机械臂保护几何净空低于25mm，后者最低为-0.85mm。静态报告在本地仓库外`push-lower-base-stance-all-v59.json`，**不包含**动态支撑、力矩、子步碰撞和完整PUSH。2cm静态对照同样在接近8.0秒有23/30低于25mm。接触后降低3cm的单环境`v59`虽成功，实测净空最低19.55mm，抽样轨迹中接触后最低两足承重、竖直速度峰0.115m/s、单足竖直力峰173N且机械臂力矩达到限额；含初始化阶段有6个抽样控制步四足均低于2N，竖直速度峰0.720m/s。单回合报告SHA256为`87eb3f923bba9be958ca3f692477f50446650fee06d5e2e6b3c1f7ba0b01985b`。该动态对照不能称安全。

机身降低已由已用seed3701、8环境、24秒四组隔离Isaac对照排除：接触后降3cm、25mm屏障`v61`为**6/8**且原生自碰2、净空最低-0.41mm；接触后降3cm、35mm屏障`v60`为**5/8**且自碰1、无效手接触2、净空最低-0.44mm。安全接近完成后提前降2cm、35mm屏障`v62`仅**3/8**且自碰4、无效手接触1、净空最低-1.10mm；提前降3cm的`v63`为**4/8**且自碰3、无效手接触1、净空最低-1.84mm。四组均8/8完整终态、最大力矩限额比1.0，成功回合也不代表几何净空合格。原始报告SHA256依次为`652511d1716280cfff7d2ae90792a169a47cd96a62ebb1b017d4662dc549f74f`、`6b8f56ca5227111bc2b661e85264b1bdd70a342366ba23a2943af719841ca6aa`、`34e65414361281f4aee0d1682f51d2dfc48d983f8599b22ac3d3b784715d0e93`、`f671a0b8a7adee0df46fdebf403d8b6079702c7bb345b09516487d7e18df82d9`；远端目录分别为`push-safe-lower-base-v61/v60/v62/v63/`，仓库外本地报告哈希一致。自碰终态中同源MuJoCo凸包的`link3`/机身穿入约0.7～0.8mm。试验性降机身控制未纳入当前默认代码，保留隔离树用于复盘。

`v64`在自碰env1/5终态固定机身上搜索原手端位置、25mm几何净空、原`joint4`下限和朝向门禁，扩大到12候选/160迭代仍无合格目标；最接近位置误差约28.6/34.0mm。仅将目标向机器人方向退20mm并把规划净空放宽至20mm，可找到目标附近姿态，但同状态下臂箱间距约25/27mm，**不能视为合法手箱接触或完整PUSH**。搜索报告在本地仓库外`push-contact-goal-search-v64-*`，只作为机身相对位置/手端姿态联合规划线索。

`v65`以同两次自碰终态做机身x位置静态对照：后退3cm的原手端目标位置误差约40.8/47.1mm；前移3cm时找到满足25mm保护净空与25mm手端误差上限的两个姿态，误差约18.0/23.2mm、臂箱几何间距约10mm。前移5cm时env1朝向误差0.376rad超出0.35rad门禁，env5静态合格；前移8cm的目标位置误差降到约11mm，但朝向误差约0.41～0.43rad，双双超过门禁。增大前移量不能同时保证完整接触姿态，且静态结果未证明接触或可执行性。原始报告在本地仓库外`push-contact-baseoffset-v65-*`。下一步先联合搜索机身位置、手端接触姿态与四足支撑，再测有接触力的自由机身物理过程；不能直接把静态前移量塞进现有PUSH控制。

`v66/v67`据此只把**诊断初始机身位置**前移3/5cm，其他保留原生自碰、合法接触、执行器和35mm预测几何屏障；已用seed3701、8环境、24秒延长窗口均为**7/8**完整成功、0终态缺失、0原生自碰，但各有1次无效手接触。`v66`实测最低保护净空6.00mm；`v67`七个有在线几何观测的回合最低6.97mm，另一个env4在接近结束前发生无效手接触，几何观测步数为0。此前将该回合的未观测占位值误读为0mm，现予以更正；它是几何观测缺失，不是终态缺失，也不是已证实的零净空。两组已有观测中低于35mm目标的控制步分别250/100，最大力矩限额比仍为1.0，均排除。报告SHA256分别为`7b4cba988d2de6f28e8b5eaa1c3a92eb02ece96770c4cc01f39be56844212d72`和`05803f072bbea44b7aed86586c9cae8935a7cdffc5c893b4c80797c9dffca2f8`，远端/本地仓库外同名`push-safe-base-start-v66/v67/`副本已核对。改起点诊断既不满足几何安全，也不能替代原起点验收。

本轮观测审计`v68`复核`v47/v66/v67`的953/355/345个已记录关节姿态：含可视网格的保护几何与仅启用原生碰撞几何的距离对照，在1微米容差下没有可视网格更严格的样本，也没有25mm门槛判定反转。因此不能把当前低净空归因为可视网格误报，碰撞几何不缩减。报告是稀疏静态样本，不能代替全控制步最小值；SHA256为`15e4bd1ce3ffd9a5b224a99ed1f19cc6bb761ae0ed525bd88de77a895667b62b`，本地产物为`sim2sim-current-20261008-a/push-shield-geometry-audit-v68.json`。

几何观测修复已把“是否记录实测净空”与“是否介入关节参考”分开：接近阶段及保持阶段也记录控制步净空，投影介入条件保持原样；报告新增观测范围标识。该范围不覆盖物理子步，也不声称覆盖控制器首次调用前的初始化瞬间。3项几何检查及原有62项控制/评估/初始化/采样检查通过。远端隔离`push-safe-observation-v69/forward005-clear035-seed3701-8env-24s`按`v67`相同已用种子、初始前移5cm及35mm屏障复核完成，仍为7/8、无效手接触1、原生自碰0、终态缺失0；八个回合除几何观测字段外的全部终态字段与旧版完全一致。此前无观测的env4现有576个控制步，最低21.64mm；全批最低6.97mm，低于35mm的记录由100增至649步，说明旧统计漏掉接近阶段。报告SHA256为`bacb73d0cd112b0b9467f695780f4e0de05d2ad531d28f7540160c6378d6dcec`，本地报告/计划/退出状态已与远端核对。含初始化的最大力矩限额比1.0；env0的209个稀疏采样中，少于三足承重50次、四足均不超过2N有6次，竖直速度峰0.730m/s、单足竖直力峰146.3N、手部合力峰94.9N。这些抽样统计不是全步/子步峰值证明，完整对照在同名目录`paired-audit.json`。历史报告保持原样，仍无安全候选。

侧向接触姿态静态对照`v70`使用`v47`自碰env22在13.4秒的已记录状态：原机身位置下，手端中心及世界y方向±12cm目标均未找到25mm位置误差门禁内的姿态；固定腿角并把机身前移3cm后，三者静态合格，右侧目标的保护净空约70.5mm、位置误差19.9mm、30N推力的joint2杠杆力矩估计10.58N·m。但joint2仍接近软限位，且未验证真实接触、腿部支撑或可执行路径；不能视为安全动作。六份静态报告、脚本及哈希索引在本地仓库外`push-contact-lateral-v70/`。

原起点侧向对照已结束：已用seed3701、8环境、24秒，右偏8cm的`v71`为**1/8**、无效手接触6、超时1、原生自碰0；中心目标`v72`为**5/8**、原生自碰1、无效手接触2。均8/8完整终态且全回合有几何观测；最低实测保护净空分别19.76/-0.24mm，低于35mm的控制步分别705/936，含初始化最大力矩限额比均1.0。报告SHA256分别`c7a5a6b3216a64533b51be5ab571b09a147b39aa3fcae6128ce31fd9c5cf26a0`和`dba4bb18f461b20337bbee349a753df67c2a4ce400d891a92f02d6979404f0e4`；报告、计划、退出文件已同步本地并核对SHA256。右偏虽然减少本批机身碰撞，但完整PUSH明显退步，不作为候选。

终态接触分类复核显示，`v71`六次无效接触中四次触及箱面上边沿（其中两次也不满足推力方向），另两次接触点超过指定手端70mm半径；`v72`两次无效接触均在上边沿。历史轨迹显示，接近路径末端手部已降到约0.10m，但切入姿态IK后又升到约0.17～0.20m并触碰箱沿。因此下一轮先约束进入接触前的高度和推进顺序，不放宽合法接触半径或箱沿门禁。源记录、终态判据分解以及含初始化的稀疏env0支撑/速度/力峰统计在本地仓库外`push-safe-lateral-paired-audit-v71-v72.json`，抽样数据不冒充全步峰值。

接近高度门禁对照`v73/v74`已完成：原起点、已用seed3701、8环境、24秒，均仅**2/8**，无原生自碰或无效手接触，8/8完整终态。高度权重2的`v73`另有超时4、姿态失败2；权重3的`v74`另有超时6。最低实测净空14.45/11.75mm，含初始化最大力矩限额比均1.0，仍不合格。报告SHA256分别`d161292f65f3dad632d1b8adae04c888d47cf1f498c3db81192ee4762bc5cc2b`和`87916bad60f37ecddf57d3a46bf66a90016fbf9fb7e9ad3d9bae9e8c5bb4d281`，报告/计划/退出文件已同步本地并核对；各项安全指标和稀疏env0支撑/力峰单列在`push-safe-height-entry-paired-audit-v73-v74.json`。

接触确认退出门禁的`v75-r1/v76-r1`已完成，同样仅**2/8**：权重2仍超时4、姿态失败2，权重3仍超时6；两批无原生自碰或无效手接触、8/8完整终态、全回合几何观测完整。最低实测净空10.39/11.75mm，含初始化力矩限额比1.0。报告SHA256分别`cad3bec08228f0f6ea3295c18b1fd429e1ceda9c8aa2a1b3e7ab73f8f9057c29`和`b4e4ab78ceb44d081bee35dfc5e09eac514c43948fdb98cd94be3a6c31da8b2f`，报告/计划/退出文件已同步本地并核对；审计见`push-safe-contact-entry-paired-audit-v75-v76.json`。首次v75/v76仅在脚本插桩阶段因标记重复退出，未启动物理仿真，不计入结果。

这轮反证说明，新增“原分类器合法接触持续100ms可退出”的分支并未解决大多数停滞：env4/6/7尚未完成高度对齐，env0/1/5已完成90mm接近但未稳定满足接触/姿态门禁。权重3的失败终态中，底盘最多向后漂移0.178m，env0倾斜约26.6度，手端横向误差约0.19m；在此期间腿部策略被硬置零，无法主动稳定机身。先前“接触退出逻辑卡住”的解释不充分，需同时修复等待阶段的姿态保持。

等待阶段释放冻结腿部策略的`v77/v78`已结束并排除：原起点、已用seed3701、8环境、24秒，两组均**0/8**、完整终态8/8。两组各有4个回合触发base_contact、4个超时，同时记录box_contact 3、invalid_hand_contact 1；终止标记允许同回合重叠，不能相加作为回合数。底盘明显侧漂，终态y偏移约-0.35～-0.55m，箱体几乎未推进。机械臂/机身观测几何最低19.71mm不覆盖其他身体/箱体接触，不能据此否定原生碰撞失败；含初始化最大力矩限额比1.0。报告SHA256分别`aacf2e321c8c0c7f433c64eace3823f30e11508d735329feff107025f34f535f`和`5954e30a6d9cc8c59d371e68a4b97bb460936071c05bfce0d30c8cc3aaffbdb1`，报告已同步本地并核对退出文件哈希。该改动只在隔离运行树中，不并入控制候选。两组进程均已结束。

最新代码复核发现确定的门禁逻辑冲突：`approach_height_gate`计算箱前高度对齐的IK目标，但`hold_for_height`又在高度尚未对齐时用上一关节waypoint覆盖`desired`，导致机械臂无法主动完成对齐。这比此前仅归因接触退出或站立保持更直接；不能因个别回合依靠机身漂移偶然过门禁，就视为控制正确。

移除高度等待时的关节参考覆盖后，`v79/v80`物理复核分别**1/8、0/8**，仍非安全候选：权重2为成功1、超时7，无原生自碰或非法接触；权重3为超时7、非法接触1。两组原起点、已用seed3701、8环境、24秒，8/8完整终态、几何观测无缺失，最低实测保护净空均19.76mm，含初始化最大力矩限额比1.0。`v79`成功env0在19.32秒停稳，不能计为12秒验收。报告SHA256分别`a976bb6293582a553b3b79bb3125532713754a8ccca06069d3586ac7318c90f9`和`9f842b555a3bf9002c46ab539defce3579849b69a9ec208fe0eb854fad532d52`；报告、计划、退出状态已同步并核对，完整/缺失/净空及稀疏env0支撑、竖直速度、力峰在`push-height-ik-fix-paired-audit-v79-v80.json`。

修复逻辑冲突后仍多数无法完成高度对齐，因此追加`v81`静态姿态可达性检查，而不是只继续调整等待时间。在`v79`失败env4/7的箱前12cm目标上，35mm保护净空、10mm臂箱间距、joint4≥0.8rad的有限搜索未找到同时满足25mm位置误差和0.35rad朝向误差的固定1.0rad手端俯仰姿态；俯仰降至0.6rad更差。改为退后位置1.5rad、中间前进45mm时1.25rad、最后前进90mm时1.0rad，两个状态的三个静态目标均找到合格解。env1原1.0rad目标也有解，说明不是所有失败同一原因。这是有限搜索与离散目标证明，不是不可达性定理或完整动态路径；原腿部预步记录缺失时使用终态腿角，世界x偏移也不能代替箱体局部完整路径。11份静态报告、匹配脚本和SHA256索引在本地仓库外`push-entry-target-static-v81/`。

接近阶段俯仰1.5→1.0rad的`v82`与附加IK阻尼的`v83`已结束，完整PUSH分别**1/8、0/8**，仍排除。两组原起点、已用seed3701、8环境、24秒，均8/8完整终态、几何观测无缺失；v82另有超时7，无base_contact或非法手接触；v83超时7、非法手接触1。只有v82的env6完成高度对齐并在21.94秒停稳，但其最低保护净空仅**6.15mm**；v83最低19.76mm。低于35mm控制步664/558，含初始化最大力矩限额比均1.0。报告SHA256分别`9bde5475a4ad68bb977de81378018eaec997f3ad00161116422c1e617fbdc494`和`d21c553ac49505e4c92eb0485e6015bc2bf47b1d9b29a7ba6d99c6c37f142573`，报告/计划/退出状态已同步本地并核对远端哈希；完整指标与稀疏env0支撑、腾空、竖直速度及力峰见`push-entry-pose-paired-audit-v82-v83.json`。静态可达端点未转化为稳定动态接近，增加速度反馈也未解决。

接近IK朝向权重0.10/0.25的`v84/v85`完成后分别**1/8、0/8**，仍未改善鲁棒性。v84成功1、超时6、非法手接触1；v85超时7、非法手接触1，两组base_contact均0、完整终态8/8、几何观测无缺失。最低保护净空均19.76mm，低于35mm控制步567/558，含初始化力矩限额比均1.0。唯一成功在23.72秒，非12秒验收。报告SHA256分别`f46c1a634dd34ba8cdcfb71a5243f74d435f33553edc9d59890bc2b7cbe16144`和`4a2ef7838d75274324261393afa47309bd8660adf507a6e1a49cc20f5715abb8`，报告/计划/退出状态已同步本地并核对远端；完整审计及稀疏env0支撑、腾空、速度、力峰在`push-entry-weight-paired-audit-v84-v85.json`。

v84超时回合末段128个控制步中，几何屏障干预34～83步，机械臂经常超过0.25rad/s停稳门槛；降低朝向权重仍未稳定进入高度对齐。`v86`对其中env1/6的记录姿态追加55mm静态净空搜索，均找到原箱前目标附近姿态，保护净空63.47/62.79mm、朝向误差0.348/0.131rad。55mm高于当前屏障50mm预测制动触发距离，但这只是有限静态端点搜索，缺失预步腿角仍使用终态腿角，未证明连续路径或动态可达；来源脚本及报告索引在`push-entry-braking-clearance-v86/`。

只补录控制中间量的`v87`已完成，与v84的**全部原终态字段逐项完全一致**，仍为成功1/8、超时6、非法接触1，无base_contact、终态缺失0、几何观测无缺失；最低净空19.76mm、低于35mm控制步567、含初始化最大力矩比1.0。报告SHA256为`3e850c4aabe47b05d25afb1be46b191c39409102499dcd2c7bd0bf6d0e699359`，报告/计划/退出文件已同步本地并核对远端。失败历史中屏障实际改写关节参考435次，其中434次与IK关节目标方向相反；六个超时回合末段128步，高度/位置和速度条件同时满足的连续时长最多0.06秒，达不到原0.10秒确认门槛。该关系支持检查IK与屏障的振荡，但关节方向内积不是笛卡尔进展或唯一因果证明；数据为上次控制器计算后在下一预步采样。完整审计含稀疏env0支撑、腾空、速度和力峰，位于`push-shield-observation-audit-v87-v88.json`。

接近参考限速0.25rad/s的`v88`在1200秒墙钟运行上限及15秒终止宽限后退出-9，未生成报告，**8个终态记录均缺失，不计成功率**。最后日志是第1000步、临时成功2；不得将临时计数当作完整物理结果。保留原日志和退出文件，未覆盖目录。计划至退出文件相隔约1215秒，与启动器计算预算相符；没有据此认定为物理崩溃。

延长墙钟预算后的`v89/v90`均已取得完整8/8终态、0缺失，但完整PUSH均仅**2/8**。0.25rad/s接近的v89另有超时6，无base_contact或非法手接触；0.50rad/s的v90另有超时5、非法接触1，无base_contact。高度对齐提升至6/8、7/8，但最低实测保护净空恶化至**0.975/0.274mm**，低于35mm控制步3885/2114，含初始化最大力矩限额比1.0，均排除。报告SHA256分别`522d5a783de8b175d32b88296dc3316d93af593e9d946fdc984bd753143d6ed4`和`efbcc8b820a8609c97fb5e33b3d565b4f42049f10a2e4af7f31d36005201997d`；报告/计划/退出文件已同步本地并核对远端。完整指标及稀疏env0支撑/腾空/速度/力峰见`push-entry-rate-paired-audit-v89-v90.json`。延长的是计算预算，物理窗口仍为24秒，不计12秒验收。

进一步定位到屏障恢复分支的确定问题：当实际姿态与一次受限修正都未达到35mm时，末尾回退会丢掉已增大净空的修正，直接重新保持实际姿态。v89/v90的env0/5因此可长时间停在约7～14mm净空、关节速度接近零的状态。隔离修复保留“受限修正”和“保持实际姿态”中净空更大者，不降低35mm阈值。在记录env5的静态回归中，旧版保持8.153mm，新版同样0.005rad步长内改善到11.530mm；**尚未达到35mm，更不是动态安全证明**。三项原几何检查与两项恢复回归共5项通过，脚本和结果在`push-recovery-v91/`。

恢复回退修复的`v91`完整PUSH仍**2/8**、超时6，无base_contact或非法手接触；与v89相比，低于35mm的控制步由3885减至828，最低净空由0.975提升至7.836mm，进入接触面就绪由3/8增至5/8，仍不合格。另将避碰修正限速恢复1rad/s的`v92`为**0/8**、超时6、非法接触2，无base_contact，最低10.711mm、低于35mm控制步621；该速率拆分不采用。两组完整终态8/8、无几何观测缺失，含初始化最大力矩限额比均1.0。报告SHA256分别`66a91d8af4cc8071d4bd1d3b886a27bd720506940b52dfece2de4bb7fe1ea08a`和`7d3ce1060e5507bb996d56e79711fe855a56aa6562de56b0f9fe3633defb5ef8`；报告/计划/退出状态已同步本地并核对远端，完整及稀疏安全指标见`push-recovery-paired-audit-v91-v92.json`。

v91失败env4/7末段净空约49～51mm，手端位置仍明显偏离箱前目标。下一轮把局部净空梯度加入**同一次IK求解**，与位置/朝向共同计算，减少先靠近、后被屏障推回的冲突；额外偏好55mm净空，原35mm屏障及50mm预测制动仍在最后执行，软偏好不是安全保证。保持v91恢复修复和0.25rad/s接近限速，未采用v92速率拆分；原生自碰、接触/停稳100ms及执行器门禁保留。新增梯度方向、未激活环境保持和扩展IK维度/响应检查，连同原回归共7项通过。

将净空纳入接近IK的`v93/v94`均达到接触面就绪7/8，但完整PUSH均仅**3/8**、超时5，无base_contact或非法接触；完整终态8/8、几何观测无缺失。权重3/10的最低实测净空分别12.870/14.949mm，低于35mm控制步804/750，含初始化最大力矩限额比均1.0，仍非安全候选。报告SHA256分别`40d830908e770646dcb8d0817ea6a58bac420196bc94641c0e9fd0a45cbac7a0`和`51a18ef86197263f190ae8e92a59e94e69996a32a55f9bcc009d4edb7ce904e5`；报告/计划/退出状态已同步本地并核对远端，完整及稀疏支撑/腾空/速度/力峰见`push-clearance-ik-paired-audit-v93-v94.json`。

v94的env0/3/5/7已到合法手箱接触，但末段仍超时：手端目标沿推进方向误差约110mm，joint2在后三例触及-20N·m限值，箱体只推进约0.26～0.32m。主要剩余问题已包含受载推进，不能继续只检查接近成功。下一轮保持v94接近路径，将压入参考从100降至80mm以检查减载效果；另对照在受载推进阶段也保留55mm净空IK偏好。80mm改变的是隔离控制候选的目标，不修改5kg/0.4摩擦/0.60m任务及原合法接触、原生自碰、执行器和停稳判据；不能沿用原100mm参考版验收。

80mm固定压入的`v95`完整PUSH为**4/8**、超时4；延续受载净空偏好的`v96`为**3/8**、超时5。两组均无base_contact或非法接触、完整终态8/8、无几何观测缺失，接触面就绪7/8；最低实测保护净空14.869/19.214mm，低于35mm控制步726/616，含初始化最大力矩限额比均1.0。v96改善了本批最低净空，但成功率和24秒窗口仍不合格。报告SHA256分别`bf550ccd37ad03b90a921fd1f1070cee76e9ca2193d5e8492088cc1d1385f3d1`和`1b13e2c1fa76eb11c5b767bb97377b9c043bf3516d21054127085139559cec9a`；报告/计划/退出状态已同步本地并核对远端。完整及稀疏安全指标在`push-loaded-clearance-paired-audit-v95-v96.json`，可用同产物根的`audit_completed_push_diagnostics.py`重算。

v95/v96受载失败中仍出现joint2达到-20N·m；部分末段2.54秒箱体仅移动约4～31mm，不能仅靠延长窗口解决。随后v97/v98保留v96接近路径及受载净空偏好，在原接触面就绪门禁之后使用实际指定手部的箱面法向力，连续调节机械臂目标：从箱前30mm缓慢推进，最大压入80mm、目标速度限40mm/s，分别以25/30N为力控制目标（高于5kg、摩擦0.4的约19.6N名义摩擦估计）。这只是控制目标，不是放宽接触或力安全门槛。腿部actor与原观测计算保持来源契约；仅IK目标改为力反馈，接口差异明确记录在报告。原控制40项检查通过，所用力反馈函数与远端匹配源码AST一致。

力反馈对照`v97/v98`已完成且均排除：两组都是**0/8**，超时7、无效手接触1、base_contact 0、完整终态8/8、缺失0；接触面就绪7/8，最低实测保护净空19.214mm、低于35mm的控制步610/611，含初始化最大力矩限额比均1.0。力反馈推进量最终几乎都达到110mm上限，未解决受载推进；env0分别在21.98/22.04秒无效接触终止，箱体只前进约0.152/0.143m。报告SHA256分别`993635b0cdb35114bd348887f6e2f6c2516db3d335613ab2732db75691ad8395`、`ac7c33ff4c7b731d2d11da552a7027249dc6eb3093bc0ad7da2e07804b2c877f`，本地/远端报告、计划、退出状态已核对；审计位于本地产物根`push-force-servo-paired-audit-v97-v98.json`。这仍是已用seed3701的24秒延长失败诊断。

已完成一轮**匹配安全控制器的PUSH腿部策略微调**，保留v96完整IK/几何恢复/受载净空偏好及原接近路径，不采用v97/v98力反馈。新隔离目录`push-matched-train-v99/`从原`model_199.pt`初始化12维腿部actor；原生自碰、35mm几何屏障、50mm预测制动、原接触/停稳/执行器门禁及原奖励均保留。原始权重、NAV与默认控制不变。先在GPU1运行seed7310、4环境、40迭代×32步的完整控制链冒烟，确认几何屏障实际运行、有可控状态参与更新、配置与源哈希一致；冒烟是启动/优化器检查，不是安全通过。随后启动seed7311、16环境、128迭代的有限微调（控制步几何检查保留，以较小训练批次控制运行耗时），24秒训练回合、std0.03、学习率3e-5。actor/critic仅在可控状态采样，完整物理轨迹用于回报计算；不随机截短初始回合。为首次对照关闭观测噪声并固定原5kg/0.4摩擦；未增加随机鲁棒性结论。训练会保留控制步净空及含第一调用的力矩抽样，但不冒充物理子步验收。

`v99`冒烟已正常退出：40迭代、1280次控制调用、5120个几何观测环境步、927个可控环境步，确认PPO实际更新；最低控制步净空17.603mm、494个环境步低于35mm目标、力矩最大限额比1.0。该结果只通过启动/优化器检查，训练仍出现无效接触，不能称安全PUSH通过。完整冒烟日志、配置、权重、监控及修复脚本共10项与远端SHA256一致，索引`push-matched-train-v99/smoke-completed-sha256.json`。

原单次队列曾因源码和输出共用`train/`目录而在启动前报错；`launch_v2.py`已将输出分开为`finetune/`，旧失败记录保留。**128迭代训练及最终model_127物理评估均已正常退出，但该末版权重排除。** 在匹配v96控制器、实际物理、评估源码及相同seed3701/8环境/24秒条件下，完整PUSH由原权重的3/8降至**0/8**：超时5、姿态失稳2、无效手接触1、base_contact 0，8个唯一完整终态、缺失0。两例姿态失稳在16.58/17.38秒；接触面就绪仍7/8。最低控制步净空19.214mm、低于35mm目标641步，含初始化最大力矩限额比1.0。末版权重不能作为安全候选，不继续盲目延长这轮训练。

最终checkpoint SHA256为`76541b8442dd81f1815f7634d00e1a505893dc1a8ec6159ca5f28dbfdff38db5`；报告SHA256为`6788f4002ea91b950ab339e70fad43934724d18ece9b57e28225ad7bd0da7f92`，位于`push-matched-train-v99/final-checkpoint-seed3701-8env-24s/`。最终日志、权重、监控及报告等7项已同步本地并核对远端哈希；`completed-sha256.json`和`evaluation-contract-comparison.json`记录来源核对。`push-matched-training-final-audit-v99.json`单列完整与稀疏指标：env0含初始化495个抽样帧中少于三足支撑10帧、腾空6帧，竖直速度峰0.730m/s、单足竖直力峰200.41N、手部合力峰92.34N；不是全批次物理子步峰值。

较早权重对照已完成并排除：`model_32/v100`为**2/8**、超时6；`model_64/v101`为**0/8**、超时8。两组均8个完整终态、缺失0、原生base_contact/姿态/无效手接触失败0，接触面就绪7/8；最低控制步净空19.214/16.856mm、低于35mm目标698/707步，最大力矩限额比1.0。评估控制与实际物理逐项匹配v96，报告/计划/退出状态6项与远端哈希相符；报告SHA256分别`ea91f44727cc39ef6fdd8a94e57ae97d1d7b2f69d7646878aae068a4f27c2fd5`、`cb103254e43c8e1086840910f210e9a20e8b2c593f86560c6b50f1a5a8da3a7b`。原始报告在`push-matched-checkpoint-v100/v101/seed3701-8env-24s/`，审计在`push-matched-checkpoint-audit-v100-v101.json`。未从这轮训练得到优于原model199的权重。

回查原v96停滞轨迹，发现一个明确的命令分支：当前指定手部仍合法接触箱面中心附近，但箱面在**底盘坐标系**中的横向距离超过0.12m，`contact_push_velocity`取消了0.18m/s前推分量。env0末128个已记录控制步有127步符合这种情况，其中79步前向命令绝对值小于0.05m/s；该2.54秒窗口箱体只前进5.06mm。env3有34/128步出现同样情况。该诊断解释部分停滞，不证明所有失败同因，也不构成新物理成功；证据脚本及`alignment-audit.json`在`push-contact-alignment-v102-v103/`。

`v102/v103`接触对齐对照已结束：均**3/8**、超时5，base_contact/姿态/无效手接触失败0、完整终态8/8、缺失0；最低控制步净空19.214mm、低于35mm目标616步、最大力矩限额比1.0。env0箱体推进分别0.196/0.372m，完整成功数仍未提高。报告SHA256分别`6d6b0f800ee1a0df4172441346f6a617770a7f545080efd8cf60e808962e3062`、`b18eb21dd134c25f49eb08ab5e43ca8ff230d1ff5851f0226270cf77a76dab01`；原件在`push-contact-alignment-v102/v103/seed3701-8env-24s/`，6项报告/计划/退出状态远端及本地哈希一致，实际物理、checkpoint和计划中的控制源码匹配。完整/稀疏指标在`push-contact-alignment-audit-v102-v103.json`。

该对照还暴露了新增前推条件选错状态量：用了会随手端高度再次清除的`box_push_approached`，而不是既有100ms确认后锁存的`approach_face_ready`。env0第900步以后的300个“真实合法接触且face_ready为真”抽样中，v102/v103分别有300/234帧临时approached为假，使新增驱动再次关闭；不能据此排除接触对齐假设。修正只公开原锁存张量，并改用`approach_face_ready & safe_approach_complete`；原100ms进入条件、原地清零的reset及IK方程不改。

`v104/v105`锁存修正对照已完成（2026-10-10 10:31心跳回收）：较弱0.09m/s新增驱动的v104为**3/8**、超时3、无效手接触2，排除；0.18m/s的v105为**4/8**、超时4，无base_contact、姿态或无效手接触失败。两组均8个唯一完整终态、缺失0、接触面就绪7/8；最低控制步净空19.214mm、低于35mm目标622/616步，含初始化最大力矩限额比均1.0。v105四次成功耗时17.14～17.74秒，仍不是12秒验收，也不是已确认安全候选。报告SHA256依次为`1605993e58820e853956451e65ab2a078ae642579f329ae1b62b6b43a6bfa468`、`3b9ff528cdd086ca02b4f407c1a6f19fc1d36d9d59f5b9a117fb07a35ca8018d`。6项报告/计划/退出文件已同步本地并核对远端哈希；实际控制与计划一致，实际物理、checkpoint、评估器及臂控制参数匹配v96。完整与稀疏统计在`push-contact-latch-audit-v104-v105.json`；v105的env0含初始化499帧中少于三足支撑50帧、腾空6帧、竖直速度峰0.730m/s、单足竖直力峰172.97N、手部合力峰83.84N，均不是全批次/物理子步峰值。已停止的旧PID不再作为运行状态。

v105剩余失败分为两类：env4未完成接近高度对齐，未接触箱体；env0/1/5末128个预步样本全部仍为真实合法接触，但分别有51/72/60步触及原0.43m底盘间距停止线，其余77/56/68步收到至少0.30m/s前向命令。joint2分别有60/67/64个样本达到-20N·m；env0已推进0.474m，却在最后2.54秒仅推进6.63mm。此证据支持检查最小正向命令与近距停止之间的反复切换，尚不能证明因果；env4的接近IK停滞是独立问题。来源核对与逐失败窗口数据在`push-contact-latch-completed-audit-v104-v105.json`。

近距连续减速`v106/v107`已完成并排除：从0.49/0.53m开始限制正向命令，分别只有**1/8、0/8**，超时7/8，均无原生base_contact、姿态或无效手接触失败，完整终态8/8、缺失0。两组最低控制步净空19.214mm，低于35mm目标730/615步，接触面就绪仍7/8，含初始化最大力矩限额比1.0。说明这两种减速配置主要损失推进，不能把降低碰撞风险的意图当成安全且有效的结果；后续恢复v105，不降低原0.43m停止线。报告SHA256依次为`3e96e08b4d66753321e91f6109cdcea636a8b5c728ee29fe49a052b2ff1a52fa`、`50cdd33febb9fd3d970532ca56de47850f6080e2aa5ca61179f18097825b71bd`。启动器错误地要求含控制参数的`actual_physics`整体与v105完全相同，导致退出文件`report_valid=false`，但两份报告完整且进程退出0；独立复核确认唯一差异恰为计划中的`controller_contract.contact_gap_slowdown_start`，控制源码/权重/评估器及其他物理字段一致。原报告和退出文件未改写，各目录另存`report_revalidation.json`及6项远端/本地哈希核对；`launch_v2.py`修正检查但未重跑。完整及稀疏指标在`push-contact-gap-audit-v106-v107.json`：env0含初始化499帧，少于三足支撑48/35帧、腾空均6帧、竖直速度峰0.730m/s，单足竖直力峰172.57/172.97N，手合力峰83.84N；不是全批次子步指标。

`v108`转而检查v105未接触箱体的env4：其终态joint4=1.57058rad贴近软上限1.57050rad、关节近乎静止、位置误差约91mm。将**同一终态**机身及完整18关节装入MuJoCo，保持55mm净空偏好、0.10m中心距、10mm臂箱规划间距及joint4≥0.8，分别搜索1.3/1.5/1.7rad手端俯仰。三个有限搜索均未通过原静态25mm位置/0.35rad朝向筛选，`selected_candidate`仍为null；不能称找到完整避碰路径。不过1.5rad的四个备选均在joint4约0.80rad，位置误差36.7～39.5mm、朝向误差0.228～0.259rad，位置误差范数已小于原接近门禁最严的45mm轴阈值，支持检查当前上限附近的局部停滞。静态端点不证明连续路径、动态接近或PUSH成功，报告保持原筛选结论。

同一批**精确终态**的静态受载审计中，MuJoCo手端FK与记录吻合；env0按零速度重力和记录手箱合力/接触点估算joint2平衡力矩约-22.33N·m，其中重力-13.62N·m，接触反力另需-8.71N·m；env1/5约-18.97/-19.02N·m。原20N·m限制保留。该估计省略惯性、阻尼和接触力矩，并非实际施加力矩或全程安全证明，但说明仍须处理受载姿态，不能只修接近或再增加驱动。三份静态搜索、脚本、计划和`static-load-audit.json`在`push-terminal-entry-static-v108/`，已回收本地。

`v109/v110`接近停滞回退已完成，均仍**4/8**、超时4、无base_contact/姿态/无效手接触失败，完整终态8/8、缺失0。仅env4触发回退，各315个控制步（6.30秒），仍未完成原高度对齐；终态joint4从约1.5706降至1.5040/1.1347rad，但位置/朝向及停稳尚未同时满足。不能把关节开始运动当作接近成功。其他七个env的**全部原终态字段**与v105逐项相同，回退累计步均0，因此它既未破坏原四次成功，也未改善其余受载停滞。两组最低控制步净空19.214mm、低于35mm目标616步、接触面就绪7/8、含初始化最大力矩限额比1.0；env0稀疏支撑/腾空/竖直速度/力峰与v105相同，仍不代表全批次物理子步指标。报告SHA256依次`3574f972c8aa88bb7df8fa98c65e19023cafbc7ddcd3f05623d330623bd353e4`、`687cf1c8a2db22f47bb2d32ffc12c9b1d0052b76d8ec483b052afba6313afec5`；六项报告/计划/退出文件已回收本地并核对远端，控制、评估源码与计划匹配，物理字段除新增回退说明外与v105相同。完整指标与终态一致性核对在`push-entry-escape-audit-v109-v110.json`及`push-entry-escape-contract-audit-v109-v110.json`。该回退未升级为候选，不追加更长物理窗口冒充完成。

`v111`补充受载姿态的约束搜索：用v105的env0/1/5**精确终态**机身和18关节，保持记录的手箱合力及手部局部接触点，分别做8个起点的有限静态搜索。要求接触点代理误差≤2mm、手姿态变化≤0.35rad、保护净空≥55mm、非手部距箱体≥5mm、手部几何穿入不超过1mm，并在原软限位内为各执行器预留10%静态力矩余量；这些是离线搜索约束，没有修改任何原生物理门禁。三组均无同时满足约束的候选；低力矩解往往失去接触点位置，不能只看力矩降低就采用。手端FK重建误差分别0.264/0.916/0.711微米。固定机身、固定合力及接触点代理未包括惯性、真实接触建立或连续路径，有限搜索失败不等于安全姿态不存在。三份报告、脚本与计划已完成远端/本地哈希核对，索引`push-loaded-posture-static-v111/completed-sha256.json`。

`v112/v113`每控制步补录已完成：原成功env2共857帧、失败env1共1200帧，步号从0连续，无有效控制步记录缺失。两份报告的**全部8个终态和失败历史**与v105逐字段相同，仍为4/8、超时4、缺失0；实际物理、控制源码及checkpoint完全匹配，补录评估器与计划哈希一致。最低控制步净空19.214mm、低于35mm目标616步、含初始化最大力矩限额比1.0；不因此成为安全候选。报告SHA256依次`aabf90eb5489f10126d06f3d5803aa3c45ab1916c46dad5d16dd0edca2cd7d11`、`7ad72e84c6ce938ed2c4ace32a2e8bbf8cc9ca463132d9d34dddb9142e9336e3`，6项报告/计划/退出文件远端及本地一致。轨迹字段名按实际被检查环境分别为`trace_env2/trace_env1`，不能固定读取`trace_env0`；新增审计工具v4按`inspect_env_index`读取并标注连续性。控制步指标中，env2/1少于三足支撑44/87帧、腾空均5帧，竖直速度峰0.657/0.667m/s、单足接触**合力**峰165.34/154.46N、手接触合力峰32.88/42.94N；这些包含已记录的初始化，但不覆盖首次控制调用之前或物理子步，也不是全批次峰值。原始审计与逐秒对照在`push-load-trace-audit-v112-v113.json`。

匹配对照明确了受载分化时序：成功env2在13.52秒首次接触、13.66秒腿部满幅接管；失败env1为13.76/13.88秒。两者随后都出现joint2达到20N·m，因此不能仅凭饱和判断哪例会成功。env2在15/16秒段的平均底盘间距保持0.471/0.460m，箱体最终推进0.504m；env1在14/15/16秒段的间距从0.530降至0.440/0.430m，较早触及原停止线，16秒后只缓慢推进到0.264m。这支持检查接触初始的腿部接管瞬态及机身追上箱体的速度，尚不能排除接触/姿态/策略输出的共同作用。

`v114/v115`合法接触腿部接管0.40/0.70秒对照已完成并排除：分别**3/8、1/8**，低于v105的4/8；v114超时5，v115超时5、无效手接触2。两组完整终态8/8、缺失0、base_contact与姿态失败0，最低控制步净空19.214mm、低于35mm目标603步、接触面就绪7/8、含初始化最大力矩限额比1.0。较慢接管没有同时改善持续推进与合法接触，恢复v105的原0.20秒接触渐变作为诊断基线，不继续只延长接管时间。报告SHA256依次`9385b75e1753a2eebf625f579624c31c561f8fc50ecd33e88db8c1c0e669fb19`、`5a37d9b588acc26702678aaaf85402a2c4964fa94526b8a1f0782ad43736362b`。6项报告/计划/退出文件远端及本地一致，实际控制源码与checkpoint匹配v105，实际物理仅包含计划中的接触渐变时长差异，补录评估器与计划匹配；完整控制步指标与来源核对在`push-contact-ramp-audit-v114-v115.json`及`push-contact-ramp-contract-audit-v114-v115.json`。两组远端进程已结束，核对时两张GPU空闲；旧PID977860/977861不再作为运行中证据。下一步依据已补齐的受载成功/失败轨迹，处理机身—机械臂相对姿态与承力协同，不靠放宽碰撞/执行器门禁或延长窗口提升结果。仍无安全可交付候选；本地产物与交接已更新，未增加冗余GitHub推送。

后续先修复推进中的关节重载与实际指定手部接触，在已用种子小批原起点检查完整终态、碰撞、实际净空、合法接触、箱体推进和含初始化阶段的力矩饱和；候选固定后再按项目计划做两组各32个未用种子的Isaac及MuJoCo验收，并检查原速录像。24秒成功不得冒充12秒验收；通过成功率和安全门禁后再优化效率。

### 应使用哪一版

| 项目 | 当前版本 |
| --- | --- |
| 策略 | `aa/model199`，在 `ac` 固定并验收 |
| Isaac 任务 | `GO2-PIPER-Box-Push-Tracking-Play` |
| 控制 | **100mm 压入，普通腿部接管0.7秒，合法接触后接管0.2秒** |
| 箱体与目标 | 1.2×1.2×0.20m，自由箱体；5kg，静/动摩擦均0.4；推进0.60m，12秒回合 |
| 独立验收 | seed2701：**30/32**；seed3701：**32/32**；均无未完成回合 |
| 剩余问题 | 2701有2次箱体上沿无效手接触；**Isaac本体自碰关闭，机身／机械臂碰撞安全未通过** |
| 当前适用范围 | Isaac 仿真研究与接入诊断；本版尚未通过本体自碰、MuJoCo和实机验证 |

Checkpoint SHA-256：

```text
b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721
```

**不要把30/32和32/32解读为无机身穿模。** 匹配PUSH资产的`enabled_self_collisions=False`；仅在隔离复跑打开自碰，同一seed3701从32/32降到2/32，30例在有效手箱接触前因机身／机械臂接触终止。同源MuJoCo凸包还在成功轨迹的91个合法接触姿态中发现23个机身／`link3`负间距样本，最深19.11mm。该几何核对不能精确确认外部世界模型视频的每一帧，也不能证明真实机器人一定按相同深度碰撞；但现有候选**没有通过自碰安全门禁，不得据此部署实机**。完整来源与限制见下文“本体自碰隔离诊断”。

训练文件中的压入距离是80mm，**运行本候选必须使用100mm评估契约**。后续0.9/1.1秒接管只做过单种子诊断，没有替换本版。仓库 `sim2real/` 下历史冻结包也没有被本版覆盖，不能按目录名默认当作最新策略。

### 策略和配套资源在哪里

仓库：`WM4N-Group/GO2-ARX5-MUJOCO`，分支：`feature/go2-piper-sim2real`。

既有服务器上的候选目录：

```text
/path/to/artifacts/go2-piper/push-loadprobe-20261001-ac/selected-candidate/
├── model_199.pt
├── evaluation-contract.json
├── piper_push_safe_approach.json
├── source-snapshot/
├── training-params/
└── README_CN.md
```

本地备份在仓库外 `../artifacts/go2-piper/push-loadprobe-20261001-ac/selected-candidate/`。权重、报告和视频不在Git中，**仅克隆仓库不能获得完整候选**。本次交接已将候选目录同步到既有服务器；接收方需同时取得该目录。

`source-snapshot/` 是匹配控制、配置和评估源码的补充快照，不是完整Isaac环境。原复现环境位于 `/path/to/artifacts/go2-piper/push-ramptrain-20261001-aa/train`，源码基础提交为 `ceb62fe4fe74ef1866d9628ad6d9e4d00a4d1f37`。换环境时需配套仓库及GO2-PIPER资产，再按候选快照与评估契约核对；不能仅复制权重。

SAFE_APPROACH资源运行时仍放在仓库的 `mujoco/deploy/piper_push_safe_approach.json`，Isaac控制器也读取它。不要因为目前只使用Isaac而漏掉这个文件。

### 最直接的运行入口

以下供恢复Isaac PUSH复现时在既有服务器运行，先按总交接检查进程、GPU0和资源完整性；本轮没有重跑Isaac PUSH。复现seed3701，使用新的报告目录，不覆盖原验收证据。该种子原结果32/32，重跑属于复现，不是新增独立验收，结果须重新核对。

```bash
cd /path/to/artifacts/go2-piper/push-ramptrain-20261001-aa/train
export PYTHONPATH="$PWD/source/LeggedManip_Lab"
export CUDA_VISIBLE_DEVICES=0
PUSH_CANDIDATE=/path/to/artifacts/go2-piper/push-loadprobe-20261001-ac/selected-candidate
PUSH_REPLAY_DIR="$(mktemp -d /path/to/artifacts/go2-piper/push-replay.XXXXXX)"
sha256sum "$PUSH_CANDIDATE/model_199.pt"

/path/to/bin/isaac-python scripts/evaluate_box_skills.py \
  --task GO2-PIPER-Box-Push-Tracking-Play \
  --checkpoint "$PUSH_CANDIDATE/model_199.pt" \
  --num_envs 32 --episodes-per-env 1 --seed 3701 \
  --steps 900 --episode-length-s 12 --headless --device cuda:0 \
  --push-ik-clearance-minimum 0.10 \
  --push-hand-pitch 0.6 --push-height-offset 0.03 \
  --push-contact-memory-s 0.10 \
  --push-leg-release-ramp-s 0.7 --push-leg-contact-ramp-s 0.2 \
  --push-press-on-legal-contact --push-forward-command-gain 2.0 \
  --press-depth 0.10 --push-ik-joint-limit-solve \
  --push-goal-hold-pose --push-stop-distance 0.11 \
  --push-ik-orientation-weight 0.5 --push-contact-gap-slowdown-start 0 \
  --failure-history-steps 128 \
  --output-json "$PUSH_REPLAY_DIR/seed3701.json"
```

完整原验收脚本在 `ac/launch-held-out-2701.sh` 和 `ac/launch-held-out-3701.sh`，原始报告在 `ac/outputs/`。不要直接执行原脚本并覆盖其固定输出路径。

启动前还须将完整运行树对应文件与`source-snapshot/`逐文件核对；`evaluation-contract.json`的`robot_asset_sha256`及物理参数必须匹配，SAFE_APPROACH资源应与候选内副本一致。只核对checkpoint不能保证复现。完成后检查退出码、32个唯一终态/0缺失、成功和失败原因、实际物理及控制源码哈希，再计算新报告SHA256。`verify_acceptance.py`针对原固定路径，不能直接用它或旧验收JSON给新报告盖章。

### 接到其他小组系统时要保留什么

这是 **226维观测 → 12维腿部策略输出 + 6关节机械臂IK** 的混合技能，控制周期20ms。机械臂接近、限位内姿态IK、合法接触判断、接管渐变及到位保持都属于技能的一部分；只运行网络不能复现本版结果。观测历史、关节重排、PD、延迟和实际组合的18维命令历史沿用配套源码。

目前直接可复现的入口是上述Isaac任务和评估脚本；本页不代表已提供独立的上层技能调度SDK或已验证NAV→PUSH接管接口。Reachability组可用GO2-PIPER任务作仿真参考；世界模型组若使用本技能，需要配套GO2-PIPER本体与观测接口，不能直接加载到GO2-ARX5。普通PUSH也不覆盖低板/架桥用的PUSH-LOW任务。

### 结果、视频与进一步说明

- [历史验收与负载对照](../archive/EXPERIMENT_HISTORY_CN.md#source-push-load-comparison-20261001-cn)：减载、压入和后续接管诊断。
- [历史运行与训练背景](../archive/EXPERIMENT_HISTORY_CN.md#source-push-isaac-runbook-cn)：旧80mm命令仅供追溯，复现当前候选使用本页100mm完整命令。
- 当前视频目录：本地仓库外 `../artifacts/go2-piper/push-review-20261001-ae/`，入口 `index.html`，含成功和失败两段；两批64个终态与原验收逐值一致。
- 视频移交时携带整个`push-review-20261001-ae/`目录，由接收方在自己的机器预览`index.html`；历史`127.0.0.1:8767`只在原机器预览服务运行时有效，不是可分享地址。

本页沿用2026-10-02核对的验收入口，本轮只读复核源码/资产与候选一致；没有重新训练或新增一轮PUSH物理验收。

### MuJoCo sim2sim迁移状态

2026-10-08在既有远端启动迁移诊断，产物目录`/path/to/artifacts/go2-piper/sim2sim-current-20261008-a/`，本地报告副本在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/`。已从当前`model_199.pt`导出226→12 TorchScript actor：checkpoint SHA256与本页相同，65组探针推理的最大导出误差为0。每次导出文件哈希可能不同，须以对应报告的`source.exported_actor_sha256`核对，不以早期导出值代替；导出文件没有替换Isaac候选。

`push-legacy-contract-v3`误用了旧分段预接触及锁臂流程，10.08秒发生`base_link`与`link4`自碰，合法手接触0，箱体未前进。报告SHA256：`f7c8a32837d780055e4d7607b34eddf59be42b353b59b3a0f4572a4088fa1bae`。这项结果只定位旧流程故障，不能归因于已验收的普通Tracking候选。

新增显式`current-prefix`诊断配置，设置100mm压入、合法接触维持压入、0.7/0.2秒腿部接管、前进命令增益2及停机距离0.11m，并关闭旧分段预接触和锁臂。`push-current-prefix-v3`在seed3701运行12秒，无自碰，但225个控制步受到机械臂保护净空约束，合法手接触0，箱体位移近零；最小保护净空16.93mm。报告SHA256：`824ff37e52b090ea57803c9fd2a07f1a2ac767f6c5f670326ddfcb196d325e08`。该配置仍缺来源匹配的限位姿态IK、0.5姿态权重、PhysX机身净空投影、接触记忆、目标姿态保持和重置分布，**不能据此计算当前PUSH的sim2sim成功率**。下一步优先核对臂部几何、初态和同状态IK/观测/动作轨迹，保留碰撞门禁；对齐后再进行独立种子完整回合。实机仍暂停。

后续`push-bounded-ik-v2`在显式诊断模式直接调用候选源码的`pose_task_scale`及`bounded_pose_delta`，姿态权重0.5，继续保留MuJoCo物理自碰监测与15mm几何净空门禁。相同seed3701/12秒仍超时、合法手接触0、箱体未推进；净空阻挡224步。终态最近受保护几何为`link4`侧`piper_collision_21`与`base_link`侧`piper_collision_0`，间距17.87mm；手至目标尚有184.68mm。报告SHA256：`37e011885a71ec16f34cf5378157c1ce3193a6c553d4e653df4251aac795d97c`，本地副本在上述产物根。下一步对照这对几何体的USD/PhysX碰撞形状、初态与Jacobian/软关节限位；在核对前不放宽净空或碰撞终止。该结果仍是单种子迁移故障诊断，不是sim2sim成功率。

资产来源复核：匹配的`aa/train`中Tracking任务继承`piper_box_robot_cfg()`，使用基础`go2_piper.usd`；切换到`go2_piper_selective_collision.usd`的配置属于CLIMB Crawl。MuJoCo的`piper_collision_profile.json`从基础USD导出，所记录的该USD SHA256 `7096d6fe13922bb16678a7963eb5eef9a4e5fafc8de0cfc8b512f002f83dfc16`与远端`aa/train`文件一致。Isaac原任务的`arm_body_clearance_violation`检查臂部与机身/腿部**刚体位置**的最小距离80mm；MuJoCo当前控制器检查**碰撞几何表面**的最小距离15mm，并在关节目标插值路径上拦截。两者不是同一个量，17.87mm不能直接与80mm比较；USD同源也尚不能证明PhysX与MuJoCo凸包、接触或关节轨迹等价。下一轮应在同一初态和命令轨迹上同时记录刚体中心距、几何间距、Jacobian与关节限位，再定位224次阻挡，保留现有门禁。

`push-body-origin-v1`在隔离运行时增加终态刚体中心距记录，仍用seed3701和12秒窗口，未改变控制或安全门禁。与`push-bounded-ik-v2`逐项对照：超时、224个净空阻挡步、合法接触0、最小几何间距16.895mm均相同。终态最近刚体中心为`link4`与`FR_thigh`，距离124.674mm；终态最近几何仍为`link4`与`base_link`，距离17.865mm。只说明**终态**的Isaac式中心距高于80mm，不能证明整段轨迹或Isaac物理会通过。报告SHA256：`1f9f4b44742719113b76f126266f8148065917ae0586dd82c0c0c9515b3bd4ce`；副本在上述本地产物根。下一步记录逐步和候选关节路径的两种净空及初态对应，再判断是几何、轨迹还是求解差异。

随后`push-candidate-clearance-v1`在同种子单回合中记录600次IK候选目标，原有结果和终态字段与上一报告严格相同。224次拦截中，64次候选终点同时低于80mm中心距和15mm几何间距，154次中心距达标而几何间距不足，6次候选终点两项均达标但插值路径被拦截。首个拦截发生于7.14秒，候选终点中心距63.873mm、几何距离-11.681mm，故**最早的阻挡不能仅归因于两种门禁口径差异**；后续154次说明口径差异确实影响可行集合。这里的中心距取MuJoCo刚体位置，仍不是同状态Isaac重放。报告SHA256：`43e67f1fd4c2b34b319b6a347e3476f768f8fb475b77be35c177db6c4e36fa7f`。下一步对齐Isaac与MuJoCo的初态、Jacobian及目标轨迹后，逐步比对碰撞形状和安全可行路径；不放宽碰撞门禁。

`push-body-projection-v1`再加入匹配源码的100mm刚体中心距投影：对臂部和受保护刚体计算MuJoCo Jacobian，调用候选`project_clearance_target`，之后仍执行15mm几何路径门禁和物理自碰监测。该诊断出现22步合法手接触、箱体前进76mm，但9.82秒发生`base_link`/`link3`自碰，**失败，未保留为候选**；原报告SHA256：`148cb0d5ef729378408f746d4e5c4d6f4f58dda05be7e277dba00d5c1e140170`。原因是目标路径几何检查无法覆盖随后机身相对机械臂的运动。增加每步**实际**净空低于15mm立即失败的诊断门禁后，`push-projection-stop-v2`在9.16秒以`arm_clearance`终止，最低实际几何净空13.595mm，自碰0；此前16步合法手接触，箱体前进47.8mm，仍远未完成0.60m任务。100mm投影终态剩余线性约束误差为0，实际中心距约180mm；该数值不证明几何安全。报告SHA256：`4263dc093a9cf59f749194999d2863579a822cb4be6e96622eef49a0f254e6a6`，本地副本在上述产物根。单种子短窗口只定位接触后净空闭合，下一步须诊断机身和臂部相对运动并在动态接触中保持几何净空，不能以新增合法接触宣称sim2sim成功。共享运行时6项测试、PUSH控制数学39项测试通过；旧流程1秒冒烟运行通过。

逐步安全轨迹显示首次合法接触在8.82秒，此时净空35.14mm；0.2秒接触腿部接管到8.92秒达到满幅，9.16秒实际净空降到13.60mm。单独将接管延至0.4/0.7秒仍分别于9.16/9.22秒净空失败。接触前启动几何速度减速会造成箱体上沿无效手接触；只在合法接触后以50mm净空开始减速，可延至10.68秒和82步合法接触，但箱体仅推进68.8mm后仍净空失败。60mm减速配合**仅用于该减速条件**的0.1秒接触记忆，在原12秒窗口内没有自碰或净空终止，152步合法接触，箱体推进71.3mm，仍超时；20秒**延长诊断**551步合法接触却只推进86.5mm，表明基本停滞，绝不是12秒验收。12秒报告SHA256：`6279f40c936809a5484401eb71595f0d59545f8b80623ba68f50ee3962c9dba2`；明确标记延长窗口的20秒报告SHA256：`ea6cf7e69d380a522fdb037f99787383a1ddf319a49141572ccfe924c2033b8a`。原0.2秒/无减速配置复跑核心结果和终态严格一致。减速是**MuJoCo诊断参数**，没有替换Isaac已验收控制；下步需寻找接触后既满足几何净空又能持续推进的机身/机械臂协同路径，不以减速掩盖失败。

`push-drive-probe-extended20-v1`用独立运行时复跑同一seed3701/20秒诊断，仅增加逐控制步前进命令、腿部动作、关节目标/实测及控制步末力矩记录。原`result`和IK净空轨迹与上述20秒报告逐字段相同：仍超时、551步合法接触、箱体前进86.5mm。9秒后551个样本的**下一观测帧**前进命令均值0.1516m/s、范围0.0122～0.3020m/s；腿部动作非零，目标与实测关节平均绝对差0.156rad、最大0.766rad。1000个控制步末端样本中腿部力矩饱和0次，**未覆盖初始化瞬间及每个物理子步**，不可用作完整执行器门禁。报告SHA256：`8f081a987f802072544b04702eb4327808a5754d6eaa16af227fcb16e20c547e`；诊断脚本SHA256：`095d0c7dc90440550e50f0bcf85441dbb17fc4a9ad1026ce25a45a31fa7c00f1`，本地副本在上述产物根。可排除“前进命令已归零”作为主要停滞原因；还不能区分腿部跟踪、足地摩擦/滑移、受力和策略跨仿真差异。下步记录足端接触力/滑移、完整子步力矩及同状态Isaac对照，不放宽碰撞或实际净空终止。

`push-foot-probe-extended20-v1`在另一独立运行时加入物理子步足端诊断，原`result`及IK净空轨迹仍与上一报告逐字段相同。20秒有1000控制步、4000个5ms物理子步；**运行开始后的**腿部力矩饱和子步0，仍未覆盖初始化瞬间。9秒后的551控制步中，按单足竖直接触力>2N计，FL/FR/RL/RR平均分别有4.00/3.94/3.60/3.45个着地子步（每控制步4个）；各控制步最大法向力的均值，14秒后前脚合计约142N、后脚约71N。14秒后承重足体水平速度的控制步最大值均值约0.004～0.013m/s，存在瞬时更高峰值；该**足体速度不是接触点切向滑移速度**，不能由此证明无滑移。记录表明策略在重载四足支撑下持续输出腿动作与前进命令，但未获得持续底盘位移；接下来优先逐项对齐Isaac/MuJoCo接触、足端速度、关节目标与实测，而不是调低安全阈值。报告SHA256：`f70eff91b9272776fce78f4a419c68008ed0cfa61977f9225e6a3500`；诊断脚本SHA256：`8d3c8826a20374ef1c0cda37452079936faa874ad75c37011bec121c5595a7cd`。两份20秒报告均为同一已用seed的**延长失败诊断**，不是12秒正式验收或跨仿真成功率。

`push-contact-point-extended20-v1`用接触点Jacobian记录足端相对地面的切向速度。14秒后的301个控制步，FL/FR/RL/RR按单个接触竖直力>2N加权的均值分别约2.49/0.21/4.37/4.68mm/s；单次峰值可达51/0.53/129/159mm/s，故不能宣称全程无滑移，但没有持续高速打滑的证据。其`result`及IK净空轨迹与上述报告逐字段相同；报告SHA256：`f827c065baf9ec5282b71af270c1b9ce0bb6133a4736b64293316f50e4c6ccb7`。这是同一已用种子20秒延长诊断。

`push-arm-reference-extended20-v1`继续分开记录补偿前关节参考、重力偏置、补偿后PD目标、子步力矩和箱底水平接触力。原`result`及IK净空轨迹仍逐字段相同：551步合法手接触、箱体推进86.5mm、超时，最小实际保护净空15.47mm。14～20秒的301个控制步中，`joint2`参考均值2.983rad，正好贴近由物理关节[0,3.14]和运行时5%余量计算的软上限；实际均值3.092rad，补偿前参考误差均值0.109rad。对应1204个物理子步**全部**触及原定-20N·m力矩限值，重力偏置均值约-17.03N·m，手端目标距离均值111.5mm。注意补偿后PD目标与实测相差约0.45rad，不能把这个差值直接称为位置跟踪误差。箱底水平接触力每控制步子步峰值的均值约15.8N；冻结契约对应5kg箱体、摩擦系数0.4，`5*9.81*0.4=19.6N`仅是名义摩擦量级，不能直接等同求解器的瞬时阻力或证明单一因果。Isaac原验收报告`joint2`饱和累计均值在seed2701/3701分别约0.666/0.736秒，但起点和时窗不同，尚无同状态对照。下一步应对齐两仿真器的同状态机身/关节/手端和接触轨迹，检查为何机身未持续向前且机械臂贴近软限位；保留20N·m执行器、15mm实际净空及碰撞终止。报告SHA256：`6de19f4841cf1e003d5b56073628a4080ffd608aada541ce5ae4ed85569edb5a`，诊断脚本SHA256：`3bac5785483a8059c40c0d347e257987d5348759fa4a87517fc138dca99bd6b5`，本地副本在上述产物根；这仍是同一已用种子的20秒延长失败诊断。

对照原Isaac seed3701成功报告的env0轨迹，step460～540（约9.2～10.8秒）前进命令均值0.481m/s，机身前进0.427m、箱体前进0.498m。MuJoCo seed3701的9.2～10.8秒，下一观测帧前进命令均值0.133m/s，额外几何净空减速比例均值0.272；去掉该比例后的命令均值约0.482m/s。MuJoCo机身在9.02～11.02秒从x=-0.029m到-0.052m，箱体只前进0.042m。**两组使用不同复位分布，不是同状态回放**；这些数字只把迁移差异收窄到额外净空减速、机身未前移与随后机械臂限位/饱和的耦合。无减速的早期MuJoCo诊断曾触发实际净空失败，不能直接关闭减速或放宽门禁。下一轮先在相同初态对齐机身和手端轨迹，再寻找维持≥15mm实际几何净空、同时允许持续前移的机身/臂协同路径。

`push-arm-trace-align-v1`用[mujoco/check_current_push_arm_trace.py](../../mujoco/check_current_push_arm_trace.py)把原Isaac seed2701的两例失败回合中256个**已记录**机身/机械臂姿态静态放入来源匹配的MuJoCo本体。手端位置误差均值0.639微米、最大1.850微米，朝向误差均值0.000526rad、最大0.000992rad；输入Isaac报告、导出actor、MuJoCo资产与脚本均有哈希核对。报告SHA256：`4060e368baabb9b9c4027008f5b7adb1ed3b1bc56569ed1181366abaea39647e`，脚本SHA256：`67c2e77ea7d58f1393c2c65d8f79f3bc26dd3bfbcfca5fd2407dbceca2f1211f`；本地副本在上述产物根。**256个样本均无合法手接触，时间为6.66～9.52秒**；此结果仅支持接触前机械臂运动学对齐。成功回合接触段的同状态静态对照见下文。

30mm提前几何退让的三次隔离试验均未改善迁移：全程启用时20秒合法接触0、箱体位移0；只在接触后启用的首次实现误关了原有接触前退让，7.88秒在接触前以实际净空14.85mm终止；保留原接触前17.25mm退让、仅在接触后升至30mm的修正版，seed3701在16.38秒以实际净空14.28mm终止，330步合法接触、箱体前进76.5mm。三者均为同一已用种子的20秒延长**失败诊断**，没有成为候选，也不能替代12秒验收。后两份报告及匹配隔离运行时分别保存在远端`push-contact-retreat030-extended20-v1/v2`和`runtime-contact-retreat/v2`，报告SHA256分别为`cf94689e5e7d134a06db568c838aca53d3d182de6cb1ba8b4a56a28cc00de089`、`207bad6d9c0ecb3ae3b63f84b6f365bc2b7e5fe9bfc460d35d14c452f25f802b`；报告本地副本在上述产物根。仓库运行时保留原有行为。

`push-success-static-3701-v3`补录原Isaac成功批次env0的机身四元数、18关节状态和手端四元数：使用同一seed3701、32环境和冻结控制，除新增轨迹字段、评估脚本哈希及checkpoint文件路径外，结果与原验收报告逐字段一致，仍为32/32、无终态缺失。将159个完整姿态静态放入来源匹配的MuJoCo本体，手端位置最大误差2.673微米、朝向最大误差0.000922rad。91个Isaac合法接触样本中，31个在MuJoCo的`link3`碰撞体`piper_collision_20`与机身`piper_collision_0`之间低于15mm，集中在9.12～9.72秒，最小间距**-19.11mm**；这些样本的最近刚体中心距至少178.6mm，全部159个样本均高于原Isaac 80mm中心距门禁。同一姿态下手端运动学对齐，但MuJoCo当前几何门禁会拒绝一段Isaac成功路径；这不证明Isaac的PhysX碰撞体实际互穿，也不是MuJoCo动力学成功。下一步核对`link3`/机身的PhysX与MuJoCo碰撞外形及动态接触，再规划同时满足实际15mm净空、碰撞和20N·m力矩限制的路径，不放宽门禁。补录Isaac报告、MuJoCo静态报告SHA256分别为`6dc716d34fb29848e37473d47fe27d83d77f6cd1c8cb74449c38adc2c479266a`、`a2f21b4691711a9f9cce90215033f79e9d29aa32168627863a353504026d1015`；补录脚本位于本地产物根`evaluate_push_success_pose_trace.py`，SHA256为`60fc900db3ef24f253e82b0558327f924239eda61f85471fd056ba460ece5463`；静态核对脚本SHA256为`bc48b017948c06a00d9ae4c1264e8860700a956d26f884eeeb34402b941951f8`。报告均有远端原件与本地副本；这是已用种子的静态sim2sim诊断，不增加独立验收样本。

**世界模型组 `s38` 视频对应回合的机身自碰复核（2026-10-09）**：按其单页交接（原路径`/path/to/world-model/docs/PIPER_S38_PUSH_SELF_COLLISION_HANDOFF_CN.md`，2026-10-14核对已不存在，以下保留当时证据）固定的两份Isaac报告、seed7204和冻结`model_199.pt`，将各自`failure_histories[0].pre_step_samples`的128个机身/机械臂姿态静态放入来源匹配的MuJoCo碰撞本体。导出actor SHA256为`be73f97e5fc9ac02bb775df722464e1fac2ef213464f5b84019c1ca9c9b2308c`，诊断脚本SHA256为`0ef668400390ecb31b3aaff6ba212caaa99f277e07533e2d97cf462f33609b83`。两条记录均只覆盖**11.44～13.98秒**，20ms一帧，128/128帧为合法手箱接触；最近碰撞体均为机械臂`link3/piper_collision_20`与机身`base_link/piper_collision_0`。`s38-m6-f35`有128/128帧负有符号间距，最小**-73.42mm**（11.72秒），手端位置最大对齐误差0.85微米；`s38-m8-f25`同为128/128，最小**-75.38mm**（13.60秒），最大对齐误差0.70微米。首个*已记录*的负间距均在11.44秒，实际首次发生时刻未知。原Isaac的`arm_body_clearance=0`不能排除这种几何重叠：原门禁是80mm刚体中心距，不是碰撞表面净空。

两份静态报告本地副本位于仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/push-s38-arm-base-static-v1/`，SHA256依次为`fad696436b6c4b6a7e4c8277af26c85951cc9760c654c7239c7c4444e953ce5a`、`c9c3ba1988eb6a787d5bce03b4225d842cc8e8df52572d61868a7a79465fb160`；远端同名目录保存原件。这是**对应`s38`的MuJoCo凸包静态证据**，不是Isaac PhysX接触力、视觉网格穿透深度、完整14秒视频逐帧测量或动态sim2sim结果。报告只记录了最后128帧的完整机身四元数和臂角，没有同一时刻的腿关节；不能将负间距的毫米值直接说成Isaac头部穿透深度。

**同seed Isaac自碰隔离复跑（2026-10-09）**：CLIMB当时占用物理GPU1，本试验在空闲的物理GPU0运行，`CUDA_VISIBLE_DEVICES=0`后的`cuda:0`映射到物理GPU0。使用上述世界模型组原计划的两条完整命令，输出指向新目录；评估器、checkpoint、控制源码、seed、箱体尺寸/质量/摩擦等实际物理字段均与原报告一致，实际资产哈希仅`go2_piper_articulation_cfg.py`变化：从`enabled_self_collisions=False`改成`True`。世界模型只读shadow仍随原命令执行，不控制动作。`s38-m6-f35`和`s38-m8-f25`均为**0/1成功、1/1完整终态、7.82秒`base_contact`**，有效手箱接触0，箱体x位移仅0.023/0.015mm；终态`base`与`end_effector`接触力等大反向，手箱力为零。原两回合均运行到14秒`time_out`，所以这项隔离对照直接表明**原路径在推箱前已碰到机身**；它没有测得原视频中头部视觉网格的穿透深度，也没有证明所有随机初态都会碰撞。

两份新Isaac报告及原速录像保存在远端`sim2sim-current-20261008-a/push-s38-self-collision-v2/{s38-m6-f35,s38-m8-f25}/`，本地仓库外同名副本一致；报告SHA256依次为`e096e8fedb1414eb0773eead978ed9551c260125c7a6d175ba17f9a70c8af597`、`471f89d73ca189897e932270ff178818cd449dd27355ba4cd6347e298ce73a96`。复跑入口为[scripts/diagnose_s38_push_self_collision.py](../../scripts/diagnose_s38_push_self_collision.py)；首次`v1`启动器缺`PIPER_SOURCE_ROOT`，未写出报告且已留故障日志，结论仅引用修正后的`v2`。旧`model_599`及当前成功候选训练时均关闭自碰；先前同种子32环境隔离开启自碰，仅2/32完成任务。历史选择性碰撞PUSH诊断尚未实现有效推进，故**目前没有已验证可交付的无本体碰撞完整PUSH候选**。保留实机暂停，下一步在开启自碰、实际几何净空和执行器门禁下修复接近与推进，并重新做完整独立验收；这些已用seed诊断不增加验收样本。

**本体自碰隔离诊断（2026-10-08）**：匹配PUSH训练资产`go2_piper_articulation_cfg.py`把`enabled_self_collisions`设为`False`，Tracking配置没有覆盖；CLIMB使用选择性碰撞USD并显式设为`True`。PUSH基础USD中机身和`link3`的碰撞网格均启用，近似类型为`convexHull`；MuJoCo碰撞profile引用相同源路径，网格点数经简化但包围盒相同，尚未证明两侧动态接触等价。上述91个合法接触姿态中，23个在MuJoCo同源凸包下为负间距，最深`-19.11mm`，时间9.12～9.56秒。另复制完整`aa/train`，仅将PUSH资产的一行`enabled_self_collisions=False`改为`True`，其他候选源码快照、checkpoint、seed3701、32环境和评估命令保持一致。原验收同种子为32/32；隔离重跑为**2/32**、0缺失，30例约7.88～8.98秒以`base_contact`终止，安全接近已完成、有效手接触尚未发生，箱体几乎未移动、手端力为零。29个失败终态的机身与`link4`或`link6`接触力等大反向；另1例在终态采样相位的瞬时力为零。将这30个失败终态逐一装入来源匹配的MuJoCo本体，30/30的`link4`或`link6`与机身凸包间距均为负，最深约`-2.70mm`；手端位置误差最大约`2.01µm`。两份Isaac报告的控制源哈希完全一致，实际物理缓存仅资产配置哈希变化。这证明打开PhysX本体自碰会破坏当前PUSH路径，同姿态MuJoCo几何也与失败位置一致；不能把原32/32解释为已排除机械臂/机身自碰的安全结果，也不能靠关闭MuJoCo碰撞门禁宣称sim2sim通过。隔离报告、计划SHA256分别为`44d0dd63872afc3c7c6f39a930a2d00a46e41afd1be630006e58d90e0f626f10`、`3c7a9818bec2ad04caa212bf23fa5c3c8728f4e39bb63d442d9425c050ea379b`，远端/本地副本在`sim2sim-current-20261008-a/push-self-collision-diagnostic-v1/`。下一步需在保留实际碰撞监测、几何净空及20N·m限制下寻找可行接近/推进轨迹；此轮是已用种子风险诊断，不增加验收样本。

**env0避碰路径探索（2026-10-08，未成为候选）**：用上述自碰报告的env0第7.50秒机身/箱体/手臂姿态及失败终态的手端目标，在来源匹配MuJoCo中固定机身，腿关节暂取8.60秒终态值。确定性搜索得到三节点路径，按每轴不超过0.02rad采样，两段保护几何最小净空分别25.20/21.20mm，臂箱最小间距233.97/77.83mm；终点手端数值位置误差约3.3nm，朝向误差0.284rad，尚不满足更严的0.25rad朝向阈值。以0.2rad/s执行、每20ms重置机身姿态的PD对照运行9.78秒，含初始及最终保持无记录自碰、臂箱接触或力矩饱和，但终点关节最大误差**0.337rad**，故未通过跟踪门禁。自由机身且仅保持终态腿关节角的对照在0.30秒即跌落，保护净空越过15mm门槛后在该控制步内最低达2.17mm，并发生机身触地；因缺少7.50秒对应的完整腿部状态和NAV动作，不能推断原控制链也会如此。早期`push-detour-pd-v1`曾只凭指令路径走完误报`passed=true`，已由终点关节误差门禁纠正，**不得引用其通过标志**。静态、修正后规定机身PD、自由机身PD报告SHA256依次为`ba6657db0d1870f524e0607bef32f17cf0b69af5b4d55c9657cc1118e5f8896b`、`0a29a17a3d566ce8aec00f8aff65bd7389f1cca5c739ae26d72997a29993e3fd`、`7499c1178b5a7b7a03abb06f10f4ea478dc17d177aa49b7e9897d7504586b703`；本地副本在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/push-detour-diagnostic-v1/`，远端原件分别在`push-static-detour-v2/`、`push-detour-pd-v5/`、`push-detour-pd-free-v1/`。下步须补录与源时刻匹配的18关节位置/速度、执行器状态和NAV动作，先查明第二关节跟踪差，再在真实自由机身及全任务中验证。该试验是单个已用env的局部诊断，不计成功率或独立验收。

**完整初态复核（2026-10-08，取代上述不匹配腿角的动力学推断）**：在隔离Isaac副本只补录失败历史的完整18关节位置/速度/目标/力矩、机身角速度和足接触力，原seed3701、32环境、自碰开关、checkpoint和控制参数不变。补录报告与原报告的32个终态、30例`base_contact`、2例成功、0缺失、原失败历史字段、env0轨迹、控制与物理哈希逐字段一致；报告SHA256为`c112c2a389c6b6a155bcaa613cd2f721361324e68ad6f44aa643922c3441ea59`，补录评估脚本SHA256为`536b81f0a4d3fe2626e3747adb862ec30e8ab0dff236ced1e26ff3d06b7ede3c`。用env0第7.50秒同一时刻的完整关节和速度重新搜索，三节点静态路径仍存在；静态报告SHA256为`01085bda27b7a76e917b81bdc4a57a3f8dd81f157e2ed2d8a9b4a4a125f7c22f`。匹配腿部目标、自由机身、0.2rad/s关节速率及末端局部修正的MuJoCo PD子步诊断耗时13.24秒：四足接触数最低4（各>2N）、腾空子步0、机身触地0、竖直速度峰0.0194m/s、单足接触力峰78.33N；保护几何最低**15.99mm**、臂箱最低58.36mm、无记录自碰、含初始化力矩饱和0、最大力矩限额比0.659；终点关节/手端位置/朝向误差分别0.00007rad/4.53mm/0.168rad。局部末端优化器未报告收敛，但所得修正段通过静态采样及PD子步门禁；最小几何裕量仅0.99mm，应继续提高。PD报告SHA256为`87a12b8c7f513086db699ae856848bec9c1939a150a08ceed364b374f2c86364`。三份报告及补录脚本本地副本在`../artifacts/go2-piper/sim2sim-current-20261008-a/push-detour-diagnostic-v1/`，远端原件在`push-self-collision-fullstate-v1/`、`push-static-detour-fullstate-v1/`和`push-detour-pd-fullstate-free-v5/`。**这只是单个已用env从失败前姿态开始的接近路径诊断**：未接触箱体，未执行NAV及完整PUSH控制，所耗13.24秒也超过原12秒任务窗口；不能计入成功率或称sim2sim已通过。下一步需在更多源初态上验证并将避碰规划接入完整控制链，保持15mm碰撞门禁和执行器限制。

**20mm净空多初态诊断（2026-10-08，仍非完整PUSH）**：从同一份自碰失败报告的env0/1/2/3/4/5/10/27在7.50秒的匹配完整初态出发，各自静态搜索三节点避碰路径；env27默认4次搜索未找到满足朝向的候选，扩大至12次、160迭代后找到，不能将默认搜索成功率写成8/8。统一的自由机身MuJoCo PD参数为0.2rad/s、起始保持0.1秒、末端朝向权重0.06；8/8局部轨迹报告通过：保护几何最低20.893mm（相对原15mm门槛余5.893mm，相对提高后的20mm诊断门槛余0.893mm），耗时8.30～12.08秒，手端位置误差最大16.89mm、朝向误差最大0.273rad，四足接触数最低4、腾空0、含初始化力矩饱和0、最大力矩限额比0.682。报告没有箱体接触或完整PUSH过程，耗时也只是从失败前姿态开始的局部段，不能与原起点12秒成功率混用。原始8份PD与9份静态报告保存在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/push-detour-clear20-multienv-v1/`，`SHA256SUMS`校验17/17通过，清单SHA256为`93b5e845040306ece4b71e84b5fb4ca898c62f5ca11ef16cded57959a8ce8479`；对应远端目录以相同报告目录名位于`sim2sim-current-20261008-a/`。全部8份PD报告的脚本SHA256同为`cbae612d8a76ee9a88ed4c3611ed7181432e39f3d07357c001ec0a67de117c98`，来源补录报告SHA256同为`c112c2a389c6b6a155bcaa613cd2f721361324e68ad6f44aa643922c3441ea59`。

**剩余22例已用失败初态（2026-10-09）**：同一来源报告的7.50秒初态已全部完成搜索和核对，22例中19例通过相同20mm自由机身PD子步门禁，env11/23在起始保持约0.05～0.06秒时分别跌至19.93/19.98mm并终止，env28未找到满足0.35rad朝向阈值的静态目标；这是局部预接触诊断的19/22，不能解释成PUSH成功率。19例通过报告的最小四足承重数4、腾空0、机身触地0、含初始化力矩饱和0；最小保护净空20.932mm、最大竖直速度0.0581m/s、单足力峰96.68N、力矩限额比0.679，局部耗时8.40～12.98秒。52份原始报告与`summary.json`同步到本地仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/push-detour-clear20-allfail-v1/`，52份逐项SHA256与汇总匹配，汇总SHA256为`bd5f6c0c14590bc089f73d5fe32805f9a266efa815076066eefecb7134206529`。

针对env11/23从同一Isaac补录轨迹提前0.1秒取7.40秒初态，保持原20mm净空、PD和末端门禁，二者均通过；最低净空20.423/22.888mm，四足承重数最低4、腾空0、含初始化力矩饱和0，局部耗时13.58/11.30秒。env28在7.50秒分别以0.10/0.15姿态权重扩大搜索，并在7.40秒做12候选、160迭代搜索，仍无满足原位置/朝向门禁的静态目标；不能因最接近朝向阈值的旧候选相差约0.005rad就视为通过。七份补充报告本地/远端SHA256一致，位于`push-detour-clear20-repair-v1/`；env11/23的PD报告SHA256分别为`a85b4a2162c659816a145bf0b23aacda246588adba8350e9e2ec488e9776cacb`和`75e5e27205407852b2e811c69dc5fed1f4f5c2ad53f67c08d9d34e7e4a9e2dc5`。提前初态改变了诊断起点，不能和固定7.50秒的19/22合并成单一通过率。下一步优先定位env28的位置/朝向/净空可行域，再将避碰接近、真实手箱接触及推进接入完整控制链，最后回到原起点独立种子验收；原碰撞和执行器门禁不放宽。

**env28命令目标对照（2026-10-09，仍非完整PUSH）**：上述搜索以失败终态的**实测**手端姿态为目标；它与当时Isaac记录的`arm_command_position`不同，不能把未找到该实测姿态解释成原命令不可达。诊断脚本新增显式`--goal-kind source-command --hand-pitch 0.6`，从同一来源记录取命令位置、箱体四元数及匹配候选的手端俯仰角。env28第7.50秒初态的命令目标静态可达：20mm保护净空、5mm臂箱规划门槛下找到13节点路径；自由机身PD在12.875秒臂箱间距跌至4.84mm并停止，未完成路径。将**静态规划**臂箱门槛提高至10mm后找到17节点路径，静态最小保护/臂箱净空25.034/16.185mm；动态在20.475秒保护净空跌至19.990mm，最低19.932mm，仍未通过原20mm诊断门槛。第二次动态的最小三足承重、腾空0、含初始化力矩饱和0，单足接触峰98.57N、竖直速度峰0.0451m/s、力矩限额比0.805；停止时手端位置/朝向误差10.22mm/0.338rad，不能以终点误差合格代替全程通过。两个局部路径均未接触箱体或推进，运行时间也不能当作原12秒完整任务耗时。四份报告在远端`sim2sim-current-20261008-a/push-detour-command-goal-v1/`及`push-detour-command-goal-clear10-v1/`，仓库外本地同名副本SHA256一致；两份PD报告SHA256分别为`137524ddfbe6d0f0abe65732783ecb903fd3f89995a6d15fcaa96306ca7f169c`、`2f855cbcfbac66293de7fe74483de6aed3a0fdf2cdc4fe6387d22f1dc8c64ad3`，新版静态脚本SHA256为`1e08a18d091bce4002e61996ce3c159b0cf2576c93010cd4b92a0334b7767f0a`。下一步需要把实际命令目标、机身支撑和动态避碰放进同一控制链，保留子步碰撞与执行器门禁，再验证真实手箱接触和推进。

### 验收证据与维护检查

当前候选62次成功均通过原合法接触、安全、目标误差<.12m、箱体速度<.08m/s和连续停稳≥.5s条件。seed2701的env27/22分别在9.22/9.54秒出现箱体上沿无效手接触并计失败；不是零安全失败。`ac/verify_acceptance.py`与`ac/acceptance-verification.json`记录候选先固定后验收、来源哈希、实际物理和每环境唯一回合检查。

| 原独立报告 | SHA256 |
| --- | --- |
| held-out-press100-seed2701.json | `1b821710ed922592d72da677f8aab9a2a7d07a46e23d039c0a4996ccedb37b4f` |
| held-out-press100-seed3701.json | `770e2432c84a476e6fcab01b7026b3fd0c914f3e0d2548126811ada464c02b3b` |

控制代码后续如有修改，用项目隔离Python按改动范围运行`scripts/check_box_push_control.py`、`scripts/check_box_evaluation.py`、`scripts/check_skill_initialization.py`、`scripts/check_push_action_sampling.py`。旧记录59项通过属于当时版本，不代表此次新增物理或测试验收。PUSH恢复优化前先核对当前授权与进程，不自动执行历史待办。


<a id="transition-through-v269-20261014"></a>

## 2026-10-14归档：PUSH切换v217至v270启动前后记录

以下为整理前快照，旧PID、“正在运行”和2/2等进度只代表当时；当前结果以[当前PUSH](../PUSH_CURRENT_HANDOFF_CN.md#平稳切换实施进展2026-10-13)为准。v268后续已失败停止、v270后续已有单例整链成功，不回写历史实验描述。

## 平稳切换实施进展（2026-10-13）

用户当前优先级为NAV→v212→NAV连续切换。交付基线仍为v212；以下为独立候选和前置诊断，尚未形成可供上层启用的切换控制器。

**当前摘要（2026-10-14）**：入口v252为8/8 READY；连续NAV→PUSH的v263为4成功/5已运行、1原表面净空失败、0缺失，其余3起点未运行；v261单起点已完成推箱后制动、收臂与严格停稳，38.34秒原速录像已核验。返回NAV的v264/v265均超时，当前尚无完整NAV→PUSH→NAV通过。全身接管v266已能向目标后退，但距目标91.48mm仍超时；v269已完成后退与收臂停稳，但最终53.76mm超出50mm目标门槛；GPU0验证v270制动后微调，GPU1的v268已2/2通过并继续筛查；接手必须核对实际进程和报告，开发起点不当作独立验收。

- 新增[切换契约模块](../../scripts/piper_skill_transition_contract.py)和[检查脚本](../../scripts/check_piper_skill_transition_contract.py)，13项测试通过。包含实际18轴状态、源/对象绑定、单调物理时钟、技能局部启动时钟、READY撤销、等待后的重新检查及显式授权。READY事件含完整实测入口状态与契约版本；等待后刷新状态会发布新事件。READY快照复制并冻结门禁值，防止调用方复用字典改变已审计状态。`abstain`不隐含安全保持动作；模块没有执行器权限。
- `BoundedReference`从上一条实际下发目标及其速度接续，限制参考速度/加速度；数学测试覆盖阶跃、反向、非有限值及承重目标保留。这不保证物理稳定、力矩或碰撞安全，不得直接当安全控制器。
- 静态核对发现v212启动渐变使用全回合`episode_length_buf`，NAV已运行1s后会跳过局部启动渐变；另有接近前腿输出归零的默认角目标覆盖。局部时钟补丁已通过CPU张量检查：原reset入口逐值不变，任务第600步激活后第600/625/650步对应0/0.5/1s。补丁仅存候选产物，未修改v212冻结源；承重腿目标接续仍待物理验证。
- 旧NAV Isaac参考资产配置的`enabled_self_collisions=False`，v212共同物理域为True并显式限制臂力矩。因此旧NAV成绩不能自动覆盖新域；本轮始终保留v212原安全项，没有关闭自碰或放宽力矩终止。

远端/本地产物根均沿用本页的`sim2sim-current-20261008-a`，目录`transition-nav-entry-v217`至`v224`。229项v212源码哈希均已核对。seed3701、1环境、名义起点(-0.25,0,0.33)；八组实测初始基座/关节/目标/力矩/足受力逐值一致，中途物理reset为0。这里只覆盖启动、NAV接管及停靠前置诊断，没有完整推箱或整链成功统计，也不是未用种子验收。

| 诊断 | 实际结果 | 首步臂目标最大变化 | 含初始化臂力矩/限值峰值（物理子步） |
| --- | --- | --- | --- |
| v217：原生18轴NAV直接接入 | 0.02s臂力矩失败 | 0.522495rad | 1.0 |
| v218：仅限制NAV臂参考速度/加速度 | 0.22s臂力矩失败 | 0.000400rad | 1.0 |
| v219：先保持原关节姿态并补偿臂重力 | 0.30s臂力矩失败，尚未交给NAV | 0.028641rad | 0.987372 |
| v220：同初态原v212控制器对照 | 完成2s诊断窗口，无安全终止；未启用NAV | 0.029107rad | 0.966801 |
| v221：前2s原启动，再完整NAV接管 | 到达停靠位置，18s无安全失败；未满足持续停稳，超时 | 0.029107rad | 0.966801 |
| v222：NAV到位后有界保留承重目标 | 11.4s开始保持，12.6s机身/箱接触失败，尚未开始臂准备 | 0.029107rad | 0.966801 |
| v223：加入机身位置/速度反馈 | 24s无安全失败，机身停稳；一个后足约6.2N未达8N，超时 | 0.029107rad | 0.966801 |
| v224：再加入四足载荷分配 | 17.42s入口条件连续通过0.5s；无安全失败，停在PUSH首动作之前 | 0.029107rad | 0.966801 |

`transition-nav-entry-v217/paired-audit-v217-v224.json`保存配对核验、报告/逐步轨迹哈希和全部安全摘要；各目录的`plan.json`、`launch.json`、`seed3701-native-entry/{report.json,control.jsonl,startup-physics.json}`保存完整命令与证据。50Hz轨迹含目标、关节位置/速度/力矩、足受力、净空、门禁；报告另记三足支撑不足、腾空、竖直速度与接触合力峰。v219起还保存实际PD、限值和全身接触力。该对照表明仅缩小初次目标跳变不够，初始化控制和后续接管须分别验证；不能把前两次失败归因为已经发生了PUSH切换。

v221前2s基座、关节、目标和力矩与v220逐值一致；NAV接管首步腿目标差0、臂目标差最大0.003679rad。这里的`joint_pos_target`是已下发的PD位置请求，不等于各执行器延迟队列消费后的目标；切换未清空队列，不能把首目标连续误称为每个物理子步力矩连续。v222表明仅冻结当前命令不能维持该NAV末态的静态平衡，已拒绝此候选。

v224的主动承重使用CLIMB已有足端运动学与力分配函数：保持足端锚点，机身位置/速度反馈0.5/0.08、笛卡尔修正上限5cm；用1.5s五次曲线从原承重偏置过渡到重力/支撑力补偿。实际USD足端几何误差0.235微米。11.4s开始承重过渡，13.38s承重停稳后才准备机械臂，17.42s达到入口：四足竖直力约72.13/71.13/35.27/35.31N，基座速度约0.00247m/s，当前关节力矩/限值0.6151。全程最小臂—机身净空76.55mm，含初始化力矩峰0.966801；腾空2个控制样本、少于三足支撑12个、最大竖直速度0.55235m/s、单足合力峰160.41N、足合力总矢量峰310.87N。初始腾空单列，不能写成全程四足静态支撑。

**历史v224结果：2个已完成开发起点中，seed3701入口通过、seed3702入口超时，缺失0；该版本未执行完整PUSH和返回NAV。** 固定v224筛查目录`transition-entry-screen-v224`：3702在24s内未满足主动承重接管前提，始终停留NAV阶段，无安全终止；批次按首失败停止，3703…3708尚未运行，不能计作终态缺失。runner1124425已退出，接手仍须核对`summary.json`及实际进程后操作，不重复启动。该批不是两组未用32验收，24s只是入口诊断预算。

### 用户指出的入口机械臂晃动（2026-10-13）

用户检查v224原速录像后指出切换前机械臂一直晃动。逐帧数据确认：2～11.4s NAV阶段将臂带到另一目标姿态，13.38s后又回到PUSH首路径点，主要关节约1.2～1.4rad往返；原先仅限制臂目标速度/加速度，没有消除两套姿态请求。v224录像为17.44s/50fps，仅到入口READY，不能作为完整PUSH或平稳切换交付；原文件`transition-entry-video-v224/seed3701-native-entry/entry-v224-original-speed.mp4`，SHA256 `a10170951de9deaea979f0744a7db0e7fb1241c32f2fd9af00df31d8ee6bbdf0`。

独立候选`transition-arm-entry-v225`起改为“冻结NAV腿输出 + 持续PUSH准备位臂参考”，保持真实18轴命令历史、执行器队列与原安全项。**这属于新的过渡适配器，不是原生完整18轴NAV通过证明。** v226将重力补偿后臂目标限制在原软限位内10mrad；已用3701/3702各1环境均24s入口超时、无安全终止，不能交付。相同3701的4～11.4s窗口，六臂关节累计实测运动由10.822降至3.472rad（约68%），但停车仍未通过。v228/v229对齐手端请求的尝试、v230加强停车反馈的尝试也超时；v227在控制日志生成前停滞并人工中断，2份终态缺失单列，不能计作无失败。v231在NAV过程中直接滤慢腿目标后，两起点分别姿态/机身接触终止，明确拒绝，不能用它消除晃动。

本轮证据分别在上述候选目录的`plan.json`、`candidate.patch`、`seed*/{report.json,control.jsonl}`和`paired-arm-audit.json`，候选代码不写回v212冻结源。接续重点是保留NAV步态，在低实测速度、四脚承重窗口交给主动承重控制；捕获控制域与最终READY条件分开标注。最终50mm位置、25mm/s基座速度、四足≥8N、原关节速度/净空/执行器门禁和连续0.5s停稳要求不降低。尚未通过的候选不能向其他组替换基线。

v232保留原NAV腿目标、捕获时以实测腿速度初始化新的承重参考（已下发位置与执行器队列保留，但不宣称命令速度C1连续），再尝试小幅机身居中；结果3701超时、3702于9.64s姿态失败，拒绝晋级。进一步放宽捕获持续时间的v233仅准备，因父候选安全失败未启动。v225～v232共12份完整终态：0入口READY、9超时、3安全失败；另有v227的2份缺失单列。逐轮安全指标、计划及报告SHA256汇总在`transition-arm-entry-v234/investigation-index.json`，不可用臂运动改善掩盖失败。

v234取消接管后位移并增加有界NAV停车积分，3701仍在10.54s机身接触失败；v235去掉额外笛卡尔反馈、v236仅去掉速度反馈，分别10.60/10.48s碰撞失败。三轮在9.0s接管前的451个物理样本逐值相同，因此不能继续把问题归因于某个额外反馈项。原排队runner1131162已退出，3702和预留录像未启动。

v237改为机身位置/速度与姿态/角速度闭环的质心合力、力矩控制，分配四足单向摩擦约束力，通过不变的原PD/延迟近似实现目标力矩；1.5s平滑接管完整结束后才允许READY。3701稳定保持至24s，无安全终止，但最终XY偏差53.57mm，未通过原50mm位置门槛，仍计超时。全过程含初始化力矩峰0.966801、最小净空76.55mm、腾空2/少于三足支撑6个控制样本，竖直速度峰0.55235m/s、单足合力峰195.85N、总合力峰310.87N。接管过程中仍有约20cm后摆，不能称为平稳切换完成。配对数据与哈希见`transition-arm-entry-v237/paired-stance-audit.json`。截至v237，新臂参考适配器共16份完整终态：0 READY、10超时、6安全失败；另有v227的2份缺失，v233未运行。

v238在承重接管结束后，用3s五次曲线把XY目标平移到停车中心，并加入匹配目标速度；高度/朝向、原READY门禁保留，须等居中轨迹完成。两个已用开发起点结果如下，均保存报告，无新增报告缺失：

| v238起点（各1环境） | 结果 | 关键证据 |
| --- | --- | --- |
| 3701 | 13.98s入口READY；尚未启动PUSH | 位置误差5.40mm，基座速度2.05mm/s，四足竖直力91.60/65.56/30.50/25.83N，全部原门禁连续通过0.5s；无安全终止 |
| 3702 | 4.82s最后完整控制样本，随后力分配约束异常退出 | 接管后机身速度增至0.297m/s、一个后足卸载；不是成功或无失败，保留错误栈及最后状态 |

同seed3701在4～11.4s固定窗口，臂累计运动10.822→2.535rad，减少76.6%；这不是全程指标或整链验收。v238与v237在10.5s居中启动前的526个物理样本逐值相同；3701仍保留约20cm接管后摆，不能仅因终点通过就宣称平稳。审计见`transition-arm-entry-v238/candidate-audit.json`及`paired-centering-audit.json`，计划SHA256 `f287eaee991508ac91df4175c94df17fdf54901154e91095f113a1c28e7b8d1d`；3701报告SHA256 `76fb86ade809db75be508fcb4624ec41ef1b0bff7ef042f99770ab3377c65fe1`。每个起点完整安全摘要包括初始化力矩、净空、支撑、腾空、竖直速度与足合力，不能用单一运动量替代安全检查。

v239已结束：缩短偏置混合1.5→0.3s后，3702仍在4.78s最后完整样本后触发力分配残差异常；3701与录像按首失败停止，未运行。报告SHA256 `8e2b9edfb1b0762c8cc9ecafa3cbe7a1cecb0b334e9a66f33f42783c4471a6b8`，该异常不能称为已证明物理不可行。离线按实际USD运动学重建最后两个已记录求解输入，12次迭代的最大力/力矩残差约0.168N/0.059Nm；300次迭代可收敛并满足同样的四足≥8N及摩擦锥约束。数据见`transition-arm-entry-v239/wrench-convergence-audit.json`；这是数学复算，不代表接管物理稳定。

v241保持最少12次迭代，必要时继续至128次，并逐次检查投影后约束力的残差；原残差接受门槛、碰撞/执行器/承重/停稳门禁及参考速度/加速度限制均不变。6项数学检查（含实际约束激活状态的float32/64回归）通过后，3702仍在4.82s触发约束异常。已保存精确求解输入；独立线性规划采用包含原摩擦圆锥的外包约束，仍判定目标力/力矩不可行，证实该时刻确实无法按要求保持四足载荷。原始输入与审计分别为`transition-arm-entry-v241/seed3702-native-entry/wrench-failure-input.json`、`failed-wrench-feasibility.json`；不能把数值收敛修复当作姿态稳定修复。另存v240预检失败记录：过早收敛中止未通过已有高精度数学检查，启动命令未传播检查失败，已立即中断本组进程；无物理终态报告，单列1份缺失，不计入通过。v241不复用该输出。候选只在仓库外，v212交付基线不变，完整PUSH/返回NAV尚未执行。

v242收紧接管前条件：基座速度<40mm/s、角速度<0.2rad/s、四足实际竖直力≥12N连续60ms；原NAV腿输出不滤慢，最终READY要求不放宽。3701/3702各1环境均24s超时，未触发承重接管，无原生安全终止、无报告缺失。3701最终角速度0.282rad/s，3702位置误差60.95mm且一个后足约6.31N；严格接管避免了立即失稳，但没有解决停车。完整安全指标及哈希见`transition-arm-entry-v242/candidate-audit.json`，不计作成功。

v243将NAV手端请求对齐PUSH准备位正运动学位置与规范化四元数，3701/3702均24s超时、0 READY、0安全终止、0缺失；两者都未进入承重控制。末态角速度分别0.256/0.210rad/s，仍未停稳。3701存在约0.22s周期的接管窗口，但最多仅连续40ms；3702最多20ms，因此新增60ms捕获持续门槛不可达。上述均为已用开发起点，不能推广成功率。`candidate-audit.json`保存两个完整结果；旧监督摘要将已启动但未读取的3701列作`not_run`属于记账错误，`screen-reconciliation.json`明确两起点均已完成超时，原始报告不改写，录像未运行。

v244在低速/实际四足≥12N的20ms步态窗口，额外检查当前姿态制动合力/力矩的可行性，规划预留为四足法向≥12N、摩擦比≤0.3、腿力矩<原限值75%。最终连续0.5s停稳与原速度/碰撞/执行器门禁不变。结果为两个开发起点1 READY、1运行异常、0报告缺失：

| v244起点 | 结果 | 关键证据 |
| --- | --- | --- |
| 3702 | 10.38s全部入口门禁通过；尚未启动PUSH | 5.4s接管；最终XY误差6.30mm、基座速度1.31mm/s、角速度0.00506rad/s，四足竖直力85.38/76.32/21.59/30.24N |
| 3701 | 6.7s力分配约束异常；未READY | 6.14s捕获时机身仍上升31.74mm/s、偏航角速度0.167rad/s，之后前冲/卸载；当前瞬时可分配承重力不足以保证接续稳定 |

3702全程含初始化臂力矩峰0.964617、净空最小76.55mm、腾空2/少于三足支撑4个20ms样本、最大竖直速度0.55072m/s、单足合力峰183.98N/总合力峰310.76N；不能称为全程四足静态支撑。两起点全部安全摘要与哈希见`transition-arm-entry-v244/candidate-audit.json`，3702报告SHA256 `ac7cd9970166d8b628aa9bb5fd545b2d0a8ea7b62a0f6aaf59544364d325d0c8`。v238的3701成功路径与v244的3702成功路径分别保留，不能拼成同一控制器2/2通过；本轮原速录像因另一点失败未启动。

v245在v244捕获条件上增加绝对竖直速度<25mm/s、绝对偏航角速度<0.1rad/s；原控制和最终门禁不变。首批四个开发起点为3 READY/4、1超时、0报告缺失：3701/3702/3703分别11.28/10.38/9.52s通过；3704始终未捕获，24s超时，最后一个后足仅1.20N。3705…3708在原首失败筛查中未运行，不能算终态缺失。3702与v244全部520个物理样本逐值相同，成功路径被保留；三个成功起点在接管后均无少于三足支撑样本，最大XY偏移约3.39～4.92cm，数据见`handoff-motion-audit.json`。完整含初始化安全指标与报告哈希在`transition-arm-entry-v245/candidate-audit.json`，仍不是完整PUSH或独立验收。

**v245入口原速录像已核验**：`transition-entry-video-v245/seed3701-native-entry/entry-v245-original-speed.mp4`，11.30s、50fps、565帧、1280×720；全部报告和控制行与非录像3701逐值相同，SHA256 `67d0000d287950ddbc71726283a5bbcd09aab677281c839a4dd539c4f099dee7`。本地已有副本，已做23帧抽样查看，不声称逐帧人工审查。相同3701在4～11.28s窗口内臂累计运动10.647→1.518rad，减少85.7%；原速画面已无先前的大幅往返。该片只到入口READY，**尚未开始推箱**，不能作NAV→PUSH→NAV完整视频。各项来源在`video-audit.json`与`arm-travel-comparison.json`。

3704后续诊断：v246仅将中间捕获速度改成水平/竖直分别约束，4.48s提前捕获后在5.14s力分配异常，拒绝；v247恢复v245严格捕获，在8s未接管后缩小NAV命令死区并加入速度阻尼，24s仍超时，后足仅1.96N。原碰撞/执行器/停稳要求没有放宽。v247对前三条成功轨迹的1562个NAV命令作纯函数回放，逐值相同，承重控制AST不变；这是数学/静态检查，不能代替物理回归。

v248在8s未接管后朝实测欠载足方向改变停车目标30mm，3704仍24s超时，后足约0.89N；runner1142656已按首失败停止，其余候选种子未启动。两次仅靠NAV停车调整均未解决重新承重，不能继续把问题归为位置门槛过严。

**v249已完成首失败筛查，v245八起点对照已补齐**：v249回到v245基线，仅在8s尚未接管时，对最欠载足增加缓慢向下的运动学参考，深度上限15mm、变化速率≤5mm/s，以实测12N足载荷为反馈；其他三条腿的原NAV目标逐值保留。这是新的切换承重准备适配器，不是原生完整NAV通过证明；原PD/延迟、碰撞/执行器、真实足载荷捕获与最终停稳门禁均保留。2403个已记录目标的纯运动学检查通过，最大FK误差约0.096微米、最大附加关节偏置0.0968rad，均在原软限位内；不代表动力学安全。3704已在15.50s通过全部入口门禁：承重准备下调右后足参考约5.63mm，10.52s捕获，最终四足竖直力71.70/63.62/39.10/39.07N、基座速度2.07mm/s、XY误差4.83mm；无原生安全终止或报告缺失。含初始化臂力矩峰0.970296、腾空1/少于三足支撑7个20ms样本、净空最小76.55mm，完整指标及哈希见`candidate-audit.json`，报告SHA256 `344a7bacee653fd3136c98142b2eee9aeaf24d0f3425e0f7a6c7c8975926bf2a`。v249已完成5个开发起点：4 READY、1超时、0报告缺失；3701/3702/3703分别11.28/10.38/9.52s通过，三条控制日志与v245逐字节一致；3705于24s超时，3706…3708按首失败停止、未运行。runner1143677已结束，未录v249视频；不能与v245结果拼成v249全批成功。入口为`transition-arm-entry-v249/screen-summary.json`和`candidate-audit.json`。

v245补充批也已结束：全部8个开发起点为5 READY、3超时、0缺失；3704/3705/3706超时，3707/3708分别10.54/10.48s通过。全部报告及含初始化安全指标已同步本地。3707在3.82s记录过一次全关节力矩比≥0.98（峰0.99215），尽管未触发原生安全终止，仍须单列，不能写成全关节零饱和；该起点物理子步机械臂力矩比峰0.962634。具体状态须合并`screen-summary.json`和`remaining-summary.json`，不能只读取旧首失败摘要。当前入口探针`foot_forces`顺序为FL/FR/RL/RR，`allocated_support_forces`为FR/FL/RR/RL；须按名字对齐，不能按数组索引混用。

剩余失败归因：v249的3705最终位置误差约57.73mm、角速度约0.387rad/s，足端附加下调仅0.043mm；v245的3706最终位置误差约51.73mm、角速度0.450rad/s。8s后的已记录样本中，没有“仅位置捕获条件不合格”的样本；两者仍在NAV小幅踏步，不能仅放宽位置门槛就称修复。逐条件审计在v249的`remaining-failure-diagnosis.json`。

v250仅在12s仍未捕获且距停车点<80mm时锁定零NAV速度请求，并允许80mm中间捕获；最终50mm及全部安全/速度/连续停稳条件不变。两个开发反例均未通过、0报告缺失：3705于24s超时，撤去偏航请求后朝向漂移；3706在13.08s满足原低速/四足载荷/制动裕量并捕获，但居中过程中在17.24s最后完整控制样本后触发力分配残差异常。不能把中间捕获当成功，也不能据此放宽力分配门槛。3705在12s以前601个物理/控制样本与v249逐值相同。完整审计及精确失败求解输入在v250的`candidate-audit.json`与`seed3706-native-entry/wrench-failure-input.json`；原始报告SHA256分别为`28bdaf10bce9a609ab37e4e1cef6cd1b90f7d2a416778120332a2a11d9661452`、`6127b0516a85511f1b686a1edff6a0fccaafa69b25bdfd26b99bc3c0d9a3a052`。v250已拒绝，观察器结束，其余六起点未运行。

**v251两起点已完成，1 READY/2、1超时、0缺失**：迟到停车模式保留原NAV偏航纠正，只撤去平移速度请求；该模式捕获后沿原3s五次曲线仅移动到40mm内部合格区，减少向精确原点移动的距离。只有12s仍未捕获才可进入该模式，已捕获的v249成功路径不启用此改动；最终READY仍为原50mm及全部原承重、关节速度、净空、执行器和连续0.5s停稳门禁。没有更改物理PD/延迟或绕过真实四足≥12N及制动裕量捕获检查。最终门禁AST核对通过，v212源码229项在启动前核验通过；这些静态检查不能代替物理回归。计划SHA256 `55cb8754ee2d7a3279718e52692acd934866156e7af80bf0f4bd0c3a6590c274`。

v251的3706在18.10s达到全部入口READY：最终XY误差33.87mm、基座速度1.81mm/s、角速度0.00445rad/s、四足竖直力84.94/86.79/12.42/29.37N，无原生安全终止；含初始化臂力矩峰0.961577、腾空2/少于三足支撑4个控制样本、竖直速度峰0.55023m/s、单足峰175.24N/总合力峰311.90N，最小净空76.55mm。报告SHA256 `365983b7de7ef04ad599bb7e90fc42e5899934019dc661250f57c8e36438eca4`。3705仍24s超时：最终XY约82.89mm；在12.48/12.50s已有两次除中间80mm位置范围外的低速/四足载荷条件合格窗口，尚须实时制动裕量核验。诊断见v251的`3705-position-capture-diagnosis.json`。观察器已结束，其他六起点未运行。

**v252同版八起点入口回归已完成：8 READY/8、0缺失**：仅将迟到捕获位置范围80→90mm，对应移动不超过50mm即可进入40mm内部最终合格区；控制器、NAV请求、所有低速/真实四足载荷/制动裕量和最终50mm连续停稳门禁不变。3705在12.48s通过实测制动裕量并捕获，17.46s READY；最终XY34.68mm、基座1.91mm/s、角速度0.01209rad/s、四足89.61/81.31/18.61/23.97N。含初始化臂力矩峰0.962211、腾空2/少于三足支撑6个控制样本、竖直速度峰0.54905m/s、单足峰187.77N/总合力峰310.59N，净空最小76.55mm；无原生安全终止或缺失。报告SHA256 `f102328470495554640450b19cb14f4f152483ea07b29fae5dc5894d02d73c45`，计划SHA256 `ed02bd59cd891855e95aaa0a801e5900ac0de77a28971902b3412b3f1fde9e90`。同版3706也已17.48s READY：捕获由13.12s提前到12.50s，因此全程轨迹不与v251相同；前625个样本一致，配对见`paired-success-path-audit.json`。3704也在15.50s再次READY，全部物理样本与v249逐值相同。全部已用开发起点3701…3708分别在11.28/10.38/9.52/15.50/17.46/17.48/10.54/10.48s通过。3701/3702/3703/3707/3708与v245完整物理轨迹逐值相同，见`early-success-regression-audit.json`；3707仍保留3.82s一次全关节力矩比≥0.98（峰0.99215）的记录。此处只证明入口READY，不能作PUSH整链或未用种子验收。

八起点观察器及条件录像均已结束，汇总为`transition-arm-entry-v252/screen-v2-summary.json`和`candidate-audit.json`。3705入口原速录像已核验：`transition-entry-video-v252/seed3705-native-entry/entry-v252-original-speed.mp4`，17.48s、50fps、874帧、1280×720，SHA256 `63e9a9e01892b973e7312209a27fb9b04a252635c9934010f2fe642bbedf695c`；全部报告和控制行与非录像一致。本地已同步并检查17张每秒抽样图，只到READY、不含推箱。

**实际NAV→PUSH开发筛查为2成功/3，1运行异常、0报告缺失（v253，尚无返回NAV）**：seed3701连续物理回合已完成，worker1147950已退出。进入PUSH前565个物理/控制样本与v249成功路径逐值一致，11.28s达到原READY后开始实际PUSH。候选只重置PUSH控制器逻辑，保留实际关节/基座状态、已下发目标与执行器队列，且运行时逐项断言激活前后状态/目标不变；PUSH启动渐入用局部激活时钟，原v212文件不修改，单表达式补丁与函数覆盖源存于新候选。机械臂补偿滤波参考从上一实际下发目标接续，承重腿控制保持到原合法接触门禁与原释放渐入完成，再交给独立冻结腿策略；两份actor和226/19契约不变。进入PUSH后不再要求手臂停在准备位，但原碰撞/净空/执行器/合法接触/箱体停稳终止项全部保持。

v253预算为入口24s、激活后PUSH48s、总上限72s；记录激活时刻、合法接触、腿部接管、箱位置/速度及含初始化安全指标，末端成功只以原`box_settled`且无同时失败判定，不称整链成功。28.70s触发原`box_settled`且无同时失败，实际PUSH阶段17.42s；箱体自首个激活控制样本前进0.616922m、侧移0.045245m。激活首步最大臂目标变化0.000987rad、腿目标0.000229rad；这仅是已下发目标连续性证据，不宣称执行器延迟后的力矩C1连续。原始报告SHA256 `2db0a3d1ab4e2a5677c21eb393cf5d3a2dfb0610abc2dfd70615de3c4c6a0ec1`，来源/激活/逐段审计见`activation-audit.json`和`phase-safety-audit.json`。计划SHA256 `c91c6df9ff64eff0af3a77a56765f1de0c0a4593ae87943174cdd6172121516f`。原速录像已核验：`transition-entry-video-v253/seed3701-native-entry/nav-to-push-v253-original-speed.mp4`，28.72s、50fps、1436帧、1280×720，SHA256 `125fea4d06a92f58d516d86bccf6783a358972c604d1aaa31ab2989350e224be`；全部报告及控制行与非录像逐值相同。本地副本和29张每秒抽样图已检查，未声称逐帧人工审查；录像包含连续NAV→PUSH并完成推箱，不含返回NAV。

v253全程含初始化臂力矩比峰0.966801、全关节≥0.98样本0、最小臂—机身净空48.56mm、腾空2/少于三足支撑42个控制样本、最大竖直速度0.55235m/s、单足合力峰244.77N/足合力总矢量峰362.25N。实际PUSH的承重保持与原释放渐入共766个控制样本，少于三足支撑0、腾空0；26.62s完成腿接管后的105个样本中35个少于三足、腾空0，须保留此步态统计，不能写成全程四足承重。**箱停稳时机器人仍以约0.0996m/s、0.4026rad/s运动，尚不满足NAV重新准入**；该结果只证明本开发起点接入完整PUSH并完成箱任务，不能声称整个切换已平稳或返回NAV通过。v253均为已用开发起点，无鲁棒性/正式验收结论。

v253首失败筛查已停止：3702也于28.82s完成原箱体停稳，报告SHA256 `e0856d754f5427a07c840ad8add42ca017294a0047338e4cd6417a9ed423f9b2`；3703在16.22s承重力分配异常，尚未完成PUSH。该点已在9.52s通过入口，因此不能把它记为入口失败。3704…3708未运行，不是缺失报告。汇总为`push-screen-summary.json`（旧状态字符串`stopped_entry_failure`须结合上述实际阶段解释）、`activation-audit.json`；3703报告SHA256 `2698e040ba6485fe236a8f700c1acc18d6d7958dad8cc481f32f05e023e02407`。失败输入`wrench-failure-input.json`记录后足分配已到8N下界，力矩残差0.105617Nm超过原0.1Nm；128→1024次原迭代仍未通过，不能单靠增加迭代或放宽门槛。

**v257备用分配已完成物理反例回归，未通过**：保留原解通过时的全部计算与返回值；原解不合格时，按原0.5N/0.1Nm残差尺度作约束梯度修正，法向载荷、摩擦和最终验收阈值不变。失败输入数学重放得到最大力残差0.247235N、力矩0.031349Nm，20份已通过原解逐位不变；原闭合/符号/载荷/不可行检查及float32/64检查通过。物理3703仅从原失败时刻16.22s推进到16.30s，又因力残差0.572468N超过原0.5N终止：0成功/1、0报告缺失；原始812个物理/控制样本逐值相同，报告SHA256 `34ce9b0d059e22aea4618036d410508d25a407b4b22b1f4bfe791ac82e3a87b8`。worker1153307与观察器1153977均结束，其余七起点未启动。静态单点可解不代表前伸过程可持续承重，此候选不晋级；见`rejection-audit.json`、`activation-audit.json`及新失败输入。下一步须在臂前伸前规划足载荷裕量及必要的机身后移，保持所有原最终门禁，不能继续通过增加迭代/放宽阈值掩盖支撑需求。计划SHA256 `a5cbdfee33be94185c3dab9e659a0dcadd63e3141d1474cb6a6896d600215835`。

**退出阶段仍未通过**：v254第一次初始化因Isaac管理器不接受`*args/**kwargs`签名而中止，未开始物理控制，记录1个终态报告缺失，证据`transition-arm-entry-v254/initialization-rejection.json`；不能省略此工程失败。v255修正为原显式签名，将原`box_settled`同一判据转为完成事件以继续物理，不修改任何原安全终止项。3701直到28.70s箱任务完成的1436个物理/控制样本与v253逐值相同；之后继续原PUSH未捕获合格停车窗口，36.44s触发`invalid_hand_contact`，没有收臂或进入NAV离开。报告SHA256 `54d80f08de512070f6451e29664e211d1fca8d39fefa46f544cd612ebe8faa8c`，诊断见`transition-arm-entry-v255/exit-audit.json`：0退出捕获、0报告缺失，含初始化臂力矩比峰0.966801、全关节≥0.98样本0、净空最小48.56mm、腾空2/少于三足支撑99样本、最大竖直速度0.55235m/s、单足峰244.77N/总合力峰362.25N。保持旧PUSH继续运行并不自动形成可接管停车态。

**v258主动NAV制动已拒绝：0退出成功/1、0报告缺失**。3701在28.70s箱任务完成前1436个物理/控制样本与v253逐值相同；28.76s实际新请求历史满3帧后使用冻结NAV零速度请求、1s五次混合及参考速度/加速度约束。机器人未能停稳，31.18s触发原`arm_effort_safety`。退出阶段基座速度峰0.820m/s、角速度峰4.250rad/s，末端全身接触传感器合力记录为0（不等于箱—手过滤接触矩阵）；全程含初始化臂力矩比峰1.0、≥0.98样本2、腾空2/少于三足73样本，最小净空48.56mm，最大竖直速度0.55235m/s、单足峰244.77N/总合力峰362.25N。退出另有12个已下发参考软限位不合格样本；不能把限速器当作限位或稳定性保证。该候选没有收臂/NAV离开通过结论，详见`transition-arm-entry-v258/exit-audit.json`；报告SHA256 `f7f51f3c69c22987fc7de1f6e9ac1e48e6de94ae03ab304f753a675ed0406510`。

**v259伸臂停车已1/1通过，0报告缺失；无收臂/返回NAV结论**：原箱体完成后，新增一个明确不等于READY的动态制动阶段。该阶段要求实际四足≥12N、手卸载、姿态/软限位/净空/力矩合格，及原法向12N/摩擦0.3/腿力矩75%以内的制动力可行性；速度<0.15m/s、角速度<0.6rad/s仅界定制动适用范围。进入后用已有足载荷分配和0.3s渐入保持当前位置及实测伸展臂姿态；仍须满足原低动量捕获及连续0.5s严格停车门禁，才允许后续收臂。保留原安全终止与物理状态，不切回NAV。worker1154579已结束，目录`transition-arm-entry-v259`，计划SHA256 `00c215db0a226ce88dac01f3a3bb623f695a7de9e70546f6de2af479b13ba263`；实际GPU以`launch-seed3701.json`为准。

v259的3701在28.70s箱任务完成时开始制动，30.44s达到原低动量/足载荷/制动力捕获，31.02s满足全部退出门禁连续0.5s。最终基座速度3.634mm/s、角速度0.05577rad/s，四足竖直力71.40/72.50/35.81/33.78N，未发生合法或非法手接触，按原门禁推断箱—手接触合力≤1N，且箱体仍停稳；未发生物理reset或原生安全终止。完成PUSH前1436个物理/控制样本与v253逐值相同。退出117样本中少于三足/腾空/全关节≥0.98均0，但速度峰0.18216m/s、角速度峰0.70702rad/s、竖直速度峰0.08563m/s，不称全程静态。含初始化全部安全指标与v253相同，见`transition-arm-entry-v259/exit-audit.json`。报告SHA256 `ee360aeb03f64345102f79510160ff1e54af5b6e7c24e2f9b70ab12d7e9d8c7c`；单个已用开发起点不能作退出鲁棒性验收。

**v260承重准备已完成，但完整PUSH仍失败：0成功/1、0报告缺失**：从各自真实READY姿态预测原机械臂路径41点的质心变化，以来源匹配的MuJoCo静态FK/惯量加Isaac实测质心偏差计算。预计算显示3701/3702保持原姿态即可满足原8N/摩擦0.4/残差约束；3703至少后移15mm才可支撑该路径，候选加5mm规划裕量。三点静态质心核对误差约30～45微米，结果见v253的`prospective-support-audit.json`；不是动力学成功证明。运行时重新核对总质量误差≤1g、质心及足位置误差≤0.2mm，再决定是否准备；若原姿态预测可行则不改变控制，否则保持臂准备位、用4s五次曲线向后移不超过40mm，并重新满足原50mm位置、真实承重及连续0.5s停车门禁后才启动PUSH。权重、PD/延迟、碰撞/接触/力矩/停稳终止项不变。3703在9.52s开始后移20mm，14.02s重新满足原READY并启动PUSH；旧承重分配异常未再发生，但26.66s腿部策略已接管时触发`invalid_hand_contact`。worker1154995与观察器1155328已结束，其余七起点未运行，不能称修复了完整任务。初始477个物理/控制样本与v253逐值相同，见`preparation-audit.json`和`activation-audit.json`；报告SHA256 `4d704bfdfb6e33fdfb32b1a425dfcc431df0d6ef0c444d8dba3fbddbcf7b7210`。含初始化臂力矩比峰0.962451、全关节≥0.98样本0、腾空2/少于三足3样本、净空最小50.25mm、竖直速度峰0.55066m/s、单足峰176.62N/总合力峰310.64N。目录`transition-arm-entry-v260`，计划SHA256 `402419fff1c65ed46c303a11e7fe17fb466c429aeee3346ab3aa5634605f2338`。
v262接触诊断已完成，1334个物理/控制样本与v260逐值相同，仍26.66s触发原非法手接触。真实`box_contact_hand`过滤合力为2.63963N，接触点在箱坐标z=90.12645mm；原边界为100−10+0.1=90.1mm（含原0.1mm数值容差），超出0.02645mm。接触点距手端10.985mm，小于原70mm要求；位置/力数据见`contact-diagnosis.json`。不能通过放宽上沿容差消除该失败。报告SHA256 `db886d26a986cb5ed9ad594d59e42ba895be729e61e402cfd6481cfc2d81252d`。原`contact_forces`末端总合力不能代替该过滤矩阵；v258/v259/v261的`hand_force_norm_N`只属于前者，卸载还由原合法/非法接触门禁联合约束。

**v263首失败筛查已结束：4成功/5已运行、1安全失败、0报告缺失**：仅对确实需要承重后移准备的分支，在PUSH激活前将手目标降低10mm；保留原箱体、路径、观测/动作结构、碰撞/力矩/合法接触/停稳判据，包括原上沿10mm余量和0.1mm数值容差。没有准备后移的已成功起点保持原目标。3703在14.02s激活PUSH，29.28s完成原箱体停稳，推进0.627054m、侧移−0.011716m，无原生失败或报告缺失；含初始化臂力矩比峰0.962451、全关节≥0.98样本0、净空最小50.12mm、腾空2/少于三足34样本、竖直速度峰0.55066m/s、单足峰196.05N/总合力峰337.55N，实际PUSH阶段腾空0。报告SHA256 `1e94f046fda3b54a870eefc128c0cd8a8f9fac5460afdf089fd448d9f343c042`，来源和安全指标见`activation-audit.json`。worker1156760与观察器1157424均已结束。目录`transition-arm-entry-v263`，计划SHA256 `a58ee295e26bf31a793c4e67ef591fecaa7849f208dc96e9ae1afec81a638b13`；已完成3701/3702/3703/3704，分别28.70/28.82/29.28/31.96s成功；3701/3702全部1436/1442个物理/控制样本与v253逐值相同。3705于36.78s触发原`actual_surface_clearance`，实测净空33.623mm低于35mm；未完成推箱，3706…3708按首失败停止、未运行。3705含初始化臂力矩峰0.962211、全关节≥0.98为0、腾空2/少于三足8样本、最大竖直速度0.54905m/s、单足峰197.27N/总合力峰310.59N；报告SHA256 `c045302b0ee4945e6524cc4873de47d8dff1367ab80196764a96d3a902007b39`。同版成功/失败及逐起点安全指标在`push-screen-summary.json`、`activation-audit.json`，不作完整退出或鲁棒性验收。

**v261“连续NAV→PUSH→停车→收臂→重新停稳”已1/1通过，0缺失**：3701保持v259直到31.02s的1552个物理/控制样本完全相同；31.02s沿原2点路径反向开始收臂，38.32s收臂完成且全部最终门禁连续0.5s。最终速度3.283mm/s、角速度0.02240rad/s，四足载荷45.92/64.73/42.35/60.78N；收臂366样本中少于三足、腾空及目标软限位违规均0，力矩比峰0.722510、竖直速度峰0.01090m/s、净空最小51.01mm。全程含初始化安全指标与v253相同，详见`stow-audit.json`、`exit-audit.json`。报告SHA256 `87d85237d429c52d017a22ba18673216eae28d097221c80b3d87a7379fb5594b`；尚未运行返回NAV，不作为整链或未用种子验收。原worker1155400及观察器均已结束。

v261原速录像已核验并同步本地：`transition-entry-video-v261/seed3701-native-entry/nav-push-stow-v261-original-speed.mp4`，38.34s、50fps、1917帧、1280×720，SHA256 `e7f2b4d311d2a491653a99323601462f37a29687eac7e1d3e83f4833881560d3`。报告与全部控制行逐值匹配；已查看38张每秒抽样图，画面覆盖接近、推箱、停车、收臂，未声称逐帧审查。录像不含返回NAV。

**v264实际返回NAV未通过：0整链成功/1，0报告缺失**。到38.32s收臂停稳的1917个物理/控制样本与v261完全相同；38.38s在3帧实际新命令历史后激活冻结NAV腿输出，1s五次接续，臂保持收拢位。目标沿原朝向后退250mm，原返回预算16s；实际54.32s超时，未进入到点制动，无原生安全终止。最后距目标355.32mm，机器人相对出发点移动106.87mm（方向未达目标），四足竖直载荷39.52/116.25/57.72/0N；不能把静止三足支撑当四足停稳，也不能把激活NAV当作返回成功。返回800个控制样本中少于三足2、腾空0、全关节≥0.98为0，速度峰0.18969m/s、角速度峰1.54071rad/s。全程含初始化臂力矩峰0.966801、最小净空48.56mm、腾空2/少于三足44样本、最大竖直速度0.55235m/s、单足峰244.77N/总合力峰362.25N，详见`transition-arm-entry-v264/exit-audit.json`；报告SHA256 `eeb1848c603dee6d2c1abffe1130e3e937fa4b09e511b6fde996de0f031aa980`。worker1157092已退出，条件录像观察器1157770因失败结束，未制作v264成功录像。

**v265提高后退速度请求仍未通过：0整链成功/1，0缺失**。收臂停稳前1917个物理/控制样本与v261相同；后退请求以0.10m/s²渐增至0.25m/s，真实NAV输入的3帧速度历史均已收到−0.25m/s，排除该末态命令漏传。54.32s返回预算超时，目标误差332.50mm、移动86.10mm，仍一足零载；未触发原安全终止。全程含初始化臂力矩峰0.966801、最小净空48.56mm、腾空2/少于三足44样本、最大竖直速度0.55235m/s、单足峰244.77N/总合力峰362.25N，≥0.98样本0。报告SHA256 `a0f37af06506a3b2c9d54f34804a3a3ab711d11b96853bca9fde978d6dba3c0a`，见`transition-arm-entry-v265/exit-audit.json`。冻结NAV在该末态真实210维输入上重放误差4.77e−7；当前锁臂且手目标x=0.196m，低于已核对NAV配置前向范围下界0.4m。改变手请求会改变腿/臂输出，但静态反事实不证明动力学因果，证据`nav-command-counterfactual.json`。世界模型最新交接也保留锁臂失败/恢复18轴输出成功的同场景对照；其结果不直接覆盖本PUSH版本。

**v266全身接管已产生实际后退，但仍0整链成功/1、0缺失**：到38.32s收臂停稳的1917个物理/控制样本与v261相同；返回阶段恢复冻结NAV六臂输出的控制权，经0.45rad/s、1rad/s²约束、原几何shield及软限位，手端请求为配置范围内(0.5,0,0.2m)。不是原生18轴无改动运行。54.32s返回预算超时，实际移动167.31mm，离目标91.48mm（最接近89.17mm），未达到原50mm目标/至少200mm移动条件，故没有启动到点制动。最后四足87.09/45.67/23.38/56.06N、速度12.28mm/s；NAV前向请求已降至−0.10305m/s，不能以近目标静止宣称成功。返回800样本中少于三足3、腾空0、≥0.98为0，净空最小76.55mm、竖直速度峰0.13459m/s、速度峰0.17664m/s、角速度峰0.91403rad/s。含初始化臂力矩峰0.966801、全程净空最小48.56mm、腾空2/少于三足45样本、最大竖直速度0.55235m/s、单足峰244.77N/总合力峰362.25N。报告SHA256 `b75c2e71707130e602d1bba904b653e324e3d9ee9f4ea98d61bcca532d7fec31`，详见`transition-arm-entry-v266/exit-audit.json`；worker1159298已结束，条件录像未启动。全身输出与手任务请求同时改变，不能据此声称已单独证明锁臂的因果作用。

**v267诊断复放已结束，完整1840个物理/控制样本与v263的3705逐值相同**，仍在36.78s触发原实际表面净空门禁，0成功/1、0缺失。36.72s起原几何屏蔽器已经介入，后续仍从49.52mm降到33.62mm；终点记录的屏蔽预测来自控制前状态：实测36.22mm、100ms预测14.23mm，不能误作终点后物理测量。证据`transition-arm-entry-v267/shield-failure-audit.json`，报告SHA256 `11b16f220d271b71f6e67dcce33533fab490a6f1de5808ef7655fbba74e54316`。说明“已屏蔽参考”不足以证明实际延迟系统能及时制动；不把纯线性速度外推当安全保证。

**v268在GPU1运行额外参考规划净空裕量筛查**：仅在几何参考投影内部加15mm裕量，投影返回后恢复原35mm实际门槛；原PD、执行器延迟、接触、腿部接管、参考平滑及实际安全终止不变。须先验证3705反例，再回归其余7个已用开发起点，首失败停止，不替换v212或合并其他版本成绩。监督器1160040已核对v267轨迹完全相同后启动3705，worker1160049；计划SHA256 `e3ec021a74f94298f14f70c4902c40e88c2d41f3ed3534dc84a9ddc781cbd5f3`。候选代码及摘要在`transition-arm-entry-v268/`；本次核对已完成3705、3701两个开发起点，2/2成功、0缺失，其余正在继续，不能称8/8。旧净空失败点3705于40.16s完成推箱，最小实测净空60.08mm；3701于32.42s完成，最小净空47.26mm。两者未触发原安全终止，全程含初始化≥0.98样本均0；此版本尚无返回NAV结果。

**v269已完成返回与收臂停稳，但最终位置未通过：0整链成功/1、0缺失**：保持v266全身适配器，返回位置控制加入与已用NAV入口相同的有界误差积分（增益0.4、每轴速度修正上限0.08m/s，40mm内清零）；保留0.25m/s速度上限、原渐入、250mm目标、16s返回预算、实际至少移动200mm及所有原最终承重/收臂/严格停稳门禁。避免近目标小请求长期静止，不延长时间窗或放宽目标。纯数学检查通过：同一步多次读取不重复积分、初始零请求历史窗口、有限性/上限、近目标清零；不代表物理通过。worker1160389，计划SHA256 `4d17202482bf416c04adf7d0a479f1d6b0b0dd082084b30f5323e8626b0377f6`，目录`transition-arm-entry-v269/`；条件录像观察器1160755只在完整返回并停稳后录制与逐值审计。43.68s达到实际四足制动准入；最终54.32s时后退208.24mm、距目标53.757mm，超原50mm门槛3.757mm，按原16s返回预算计超时。所有退出门禁连续通过7.00s、收臂就绪连续6.86s，但不能放宽最终目标或称整链成功。报告SHA256 `c0db492619f955d213ce89c8d0b155030c36f4f653a7b426468f0161e071b864`，见`return-stop-audit.json`；原worker1160389及条件录像观察器已结束，未录成功视频。此版尚未合并v263/v268支撑与净空修复。

**v270正在GPU0修正到点制动后的小偏移**：仅在真正四足到点制动后，沿现有3s五次承重轨迹移动到距原目标30mm的内部区域；原50mm最终位置、至少200mm实际移动、16s返回预算及全部原门禁不变。其他阶段、NAV请求与策略均保留，不写物理状态。worker1161451，计划SHA256 `4484ab91d16e0c2ae879c2766bd8c3c0249435a1227da3ca162bed827a3758ba`，目录`transition-arm-entry-v270/`，尚无结果；条件录像观察器1161785只在完整目标与停稳通过后录制并核对轨迹。

v256收臂原型仅保存在本地，未启动：从v253末姿态经原路径末点反向回准备位的两段各1001点静态臂—机身净空最小60.50mm，但不覆盖真实退出姿态、臂箱/腿碰撞、执行器或动力学。v255停车前置未通过，不运行该原型。下一步合并通过物理验证的入口/接近修复与实际NAV返回，完成同版整链回归和独立验收；分开候选的成绩不能拼成一个版本的成功率。v212对外交付基线保持不变。



## 维护者续跑与回退版本

接收组固定使用v212；下面只供维护者续跑，不能悄然替换交付内容。实时状态必须核对实际进程与报告，旧PID不是运行证明。

- 旧21点路径 `push-entry-retreat-v209` 保留，同8052权重开发32/32，但约38～44s。其评估修正版 `push-fixed-validation-v210` 在当时未用seed913701/913702两组分别31/32、32/32；A组有1次初始化力矩失败。这些成绩属于旧路径，不能记在v212名下，种子现已使用。
- `push-box-approach-audit-v213`、v214静态路径尝试已结束；v214静态门槛不通过，未进入动力学。v215新终点+单转折点通过固定姿态静态筛选，只用于后续实验。
- 2026-10-13 15:15（远端时间）核对 `push-retracted-guarded-v216`：3点路径加手高度减速的seed3701/8环境为7/8、缺失0、1次臂力矩失败，自动拒绝扩大2701/32。GPU1的已用913701/32启动回归仍在运行，worker1120410/Isaac1120427；没有启动重复任务。计划SHA256 `6872792bdd8b10c7b973aac7c5428d7492ecb24220b65e54e6af58186101c6b1`。该实验不是本次认可录像的来源。

PUSH单技能后续仍需修复短路径非法上沿接触和初始化力矩边界，保留v212及旧成功路径；当前先推进上述切换任务。候选固定后需在Isaac与MuJoCo各用两组未用32回合、每组至少30成功且无缺失，并完成安全指标及原速录像检查；不能仅因v212开发批达到30/32就宣称安全sim2sim已通过。实机仍暂停。

旧PUSH模型/aa、ac命令、迁移诊断及截至v216准备阶段的完整记录已移入[历史实验档案](../archive/EXPERIMENT_HISTORY_CN.md#push-through-v216-20261013)，不再作为跨组当前入口。当前版本信息只维护本页，实验原始文件与旧成功路径保留。


<a id="climb-sim2sim-diagnostics-20261009"></a>

## 2026-10-09 CLIMB静态与短窗口迁移诊断原记录

2026-10-14整合归档；未追加物理实验，当前迁移边界见[CLIMB交接](../CLIMB_CRAWL_STATUS_20261001_CN.md#mujoco-sim2sim迁移状态)。

## MuJoCo sim2sim迁移状态

2026-10-08开始在既有远端隔离的MuJoCo环境做来源核对与单回合诊断，产物目录`/path/to/artifacts/go2-piper/sim2sim-current-20261008-a/`。最新冻结`stand_actor304.pt`的输入为304维：旧MuJoCo `ClimbRuntime.observation()`仅253维，尚缺Isaac `crawl_observation`附加的步态状态、接触和关节参考51维。该冻结actor末层全零，故当前移植的行为关键是`StageClimbAction`/`StageGuidance`中的逐脚支撑转移、落脚重载、登台后展开和最终姿态控制；仍须核对传感状态与观测契约，不能用旧253维PIPER actor或旧台面中心终点逻辑代替本候选。

`climb-kinematics-stagebank-v1`使用匹配iy的USD、运动学源码、actor、初态bank及MuJoCo碰撞/本体配置哈希，对阶段初态和16组受关节限位约束的小幅扰动进行**静态**对照。四足位置最大误差`2.021e-16m`，足端Jacobian最大绝对元素误差`1.943e-16`；脚的位置规划几何在这些姿态上对齐。报告SHA256：`077466500529846fa993af8b3739e0869d943cb58fa7caf0d2b61a6da421a228`，脚本SHA256：`b2b032a55a58b6c5f2c8eae04e7d550b47480537a8a416c06abb01d4a62228f5`；本地副本在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/climb-kinematics-stagebank-v1/`。这项结果不包含接触、力矩、支撑转移或动作执行，不能称为CLIMB sim2sim成功；下一步以该几何基线接入逐脚支撑/落脚控制并对照动力学。

`climb-stage-init-v3`将`iy/stage-bank.json`的箱沿初态加载到MuJoCo，按保存关节目标保持1秒：四足仍在地面承重，无记录自碰；机身x由0.351m漂移至0.380m。报告SHA256：`61d74a6138bca4bbbfd5630035035852b4a22edf2eaaa08f1b37d08fbbabebe6`。`climb-actor-reset-probe-v2`额外拼接51维复位态后缀，304维输入得到18维零动作；冻结actor末层`18x128`权重和18维偏置非零元素数均为0，另16组随机输入的最大绝对输出也是0。该后缀及253维前缀尚未与Isaac逐项对照，动作**没有送入物理引擎**。报告SHA256：`d761ba078c70e2e76b1ecefc94adcc146ec6926200102ca3880d67fb3fa7f9e2`。两份报告的本地副本在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/`，均不是逐脚攀爬或原起点验收。

首次摆脚短窗口`climb-trace-window-200-260-v1`从iy完整报告的env0第200步（4.00秒）还原机身、关节和执行器目标历史，在MuJoCo重放60个20ms目标步；源报告SHA256为`3686efcd9e0938932c2a62d876e88b5394ab73104f641655b0b59b54b9ac09aa`。初始四足端位置误差最大`0.54µm`，第212步在Isaac开始起摆。60步没有记录自碰、机身触地或腿/臂力矩饱和，子步单足接触合力峰`150.42N`、机身竖直速度峰`0.0282m/s`。但起始接触力仅在1足超过2N，而Isaac记录为3足接触；第210步后MuJoCo恢复3足承重，至第259步机身位置误差已增长至`93.41mm`、关节位置最大误差`0.309rad`。初始约束求解状态和执行器延迟历史仅从轨迹重建，不能把首帧接触差直接归因为碰撞模型；持续增长的动力学偏差需要逐项比较接触力、关节力矩和延迟。该重放直接施加记录的关节目标，绕过`StageGuidance`和304维actor，**不是CLIMB sim2sim通过**。脚本入口`mujoco/replay_current_climb_trace.py`，远端/本地报告SHA256均为`66052a262ebd08837d44d79df88749dc55207f4c0f8cb3c63016d638fb2cdc9b`，本地副本在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/`。

后续`v3`在初态按冻结关节顺序注入Isaac记录的非零力矩，并逐步记录两侧足力、机身位置及关节力矩。第200步MuJoCo计算的足力由`5.7N`增至`22.1N`，仍仅1足超过2N；后续轨迹与未注入力矩时相同，第259步位置误差仍为`93.41mm`，分量为x `+55.37mm`、y `-73.34mm`、z `+16.73mm`。从第210步重新取Isaac状态开始的50步独立窗口也在第259步产生约`61.5mm`位置误差，说明偏差不限于第200步的初态。当时读出的`21.765kg`是Isaac控制器构造时的质量缓存，恰与当前MuJoCo模型总质量相近，**不是PhysX启动后的实际总质量**；实测修正见下。不能将源轨迹足力合计直接当作模型静态重量。`v3`两份窗口的报告SHA256分别为`2c49377150e05f545d478613d804375bdcaf335dc6ad3d4670fd53f92deb93ab`和`9263f3f2da4bf440dbb6b074f41d394de343bcb5d12a3c84fd0ee7d2bb99851a`，远端/本地副本已核对。v1脚本可从Git提交`5ae1767`取回。两份窗口均绕过阶段控制器，仍是诊断。

Isaac匹配资产的`DelayedPDActuator`在每次复位为每个环境/执行器组随机抽取0～4个物理步延迟，而当前MuJoCo运行时把全部腿固定为4步。对env0第200～299步记录进行静态PD对照，同步目标和记录状态拟合腿部力矩的均方根误差为`0.035N·m`，前一步目标为`0.23N·m`；这提示目标/力矩对齐关系，但不能单凭50Hz轨迹反推出PhysX子步的实际抽样延迟。把腿部延迟由4改为0的独立60步重放，末端位置误差仅从`93.410mm`变为`93.028mm`，故延迟不是该窗口主要漂移来源。报告SHA256：`94a3f9eeac669d3ec9aecb67bf5442cef120e860e561ee08596536bd30f16a05`。

原碰撞/零边距窗口中第200步仅1足超过2N；诊断性给机器人几何加2mm接触边距后，第200步四足都有接触力，但摆动FL也出现`3.1N`，与Isaac的FL约`0.05N`不符，末端位置误差扩大到`160.04mm`，FL位置偏差明显扩大。该边距配置**不能作为修复或验收参数**；原碰撞和停稳门禁未改。补充足端轨迹的零边距/2mm报告SHA256分别为`ef9000b40926bfcbd6ce2957c871cf297cd35fcb79698250dec1a56f95231837`、`b5e510ce5a825c81272e2748e131b82928ebdaf5d08f1380ab9bb06dff1601e7`。三份新报告均已在仓库外本地产物与远端逐项核对；该轮脚本SHA256为`2254be23f6b02373be4b6408c6189360b5cac3a8fd0b7b6af7930c49a6053379`。

进一步将源轨迹第200/210/220/259步的Isaac机身与关节状态逐帧装入MuJoCo作静态接触核对：FR、RL足球在MuJoCo中约高于地面`1µm`，两足静态接触力为0，而相同Isaac记录分别约`102N`、`99N`；RR略穿透，MuJoCo约`22N`，Isaac约`26N`。这暴露了接触激活/求解状态的敏感性，**尚不能判定单一碰撞几何或摩擦参数是根因**。仅加`2µm`接触边距虽把第200步FR/RL静态足力提至`83N/80N`，60步末端误差却从`93.41mm`扩大到`154.55mm`，因此微米级边距也不采纳。报告SHA256：`75abcebce353568b8b12358fa37ca324463b136f274c6a8a364858eb6f5fe8b0`。

记录力矩的开放环路对照把每个50Hz样本保持四个5ms物理步，分别用当前/下一样本力矩；两者均在第219步由手臂`link2`/`link5`自碰门禁停止，机身在第215步已偏离约`51mm`。这不能区分源子步力矩与动力学差异，因为原Isaac每个子步都有PD反馈，而该对照没有。相同源姿态的MuJoCo手臂`qfrc_bias`与Isaac记录的六轴力矩在第200步最大相差约`0.005N·m`，第220/259步最大约`0.027N·m`，不支持把手臂静态重力模型作为直接解释。两份开放环路报告SHA256分别为`c1a5a104959c3b9e620527f3729d85f33c44637257efd872268e9fe3f6989278`、`0d284ed51ec4f3fd6059ce3c7c623bd108aac7d8f77a3df01d37e171fb251bc6`，本地/远端已核对。当前诊断脚本SHA256为`dab0b89d7a4a98310db80cbec762462a4de18ae83ef9bb80b6c502a17bbbc745`；所有参数扫描仅用于定位，不改变正常MuJoCo运行时和Isaac候选。

2026-10-08补做匹配iy的Isaac物理子步探针：在独立完整训练树副本中只读采集env0第200～259控制步，每步4个5ms子步的机身/关节状态、目标、实际力矩和四足竖直力。探针报告前261步与原候选**32个环境逐字段完全一致**，seed、actor、控制源和实际物理配置也匹配；仪器化没有改变这段轨迹。第200步四足FL/FR/RL/RR力分别约`0.04/101.83/99.24/26.31N`，240个子步内FR/RL/RR均持续高于2N，FL均低于2N。每个控制步末子步状态与20ms报告下一条样本的关节位置和实际力矩完全相同；第212步单控制步内最大关节力矩跨度约`0.173N·m`，全窗口峰值约`1.087N·m`，说明50Hz恒力矩重放确实遗漏子步变化。探针`report.json`和`substeps.json`的SHA256分别为`0b102ce06d161aa8c0d034c632d3e5f0ca8a137cafbc04f2b0317fa28f5e739d`、`b0c1b506946ca84193425765d231d424894ee978420c4ce6369cc9f899dd9ca8`；退出码0、报告齐备，本地/远端一致。短窗口`0/32`是未到终态的预期结果，不是完整技能成功率。

用这240个**实际5ms力矩**按原顺序在MuJoCo开放环路重放，仍于第219步触发`link2`/`link5`自碰；第215步机身位置误差`50.94mm`，旧50Hz当前/下一样本对照分别约`51.00/50.96mm`。第200步MuJoCo仅RR有约`22.1N`静态足力，Isaac的FR/RL/RR约为`101.8/99.2/26.4N`；第201步MuJoCo三足恢复受力，但至第219步机身向上偏离约`93.5mm`。这表明补齐源端力矩时间分辨率**没有消除开放环路漂移**，仍不能将漂移单独归因于接触模型：MuJoCo状态偏离后没有源端PD闭环纠偏。新报告SHA256为`3f060c89ab394b67b213ee1943ec90938f4ce5e7d54144eece896811b5d21f79`，脚本SHA256为`143ab75d704ad910c236dae2771a452b0693f700f7d6e4a6284111017a237afd`，均与远端一致；报告和探针在仓库外`../artifacts/go2-piper/sim2sim-current-20261008-a/`。子步同姿态接触比较见下段；当前重放仍不含`StageGuidance`和304维观测。

**子步同姿态接触核对（2026-10-09）**：在匹配的Isaac探针副本仅补录每个5ms子步的机身四元数和角速度；新旧短窗口报告除评估脚本哈希、录像路径外逐字段一致，240条原子步记录的旧字段也逐项相同。把这240个机身、18关节姿态和速度分别装入来源匹配MuJoCo模型作**逐帧静态**接触计算，四足端位置最大差`1.884µm`。按FL/FR/RL/RR顺序，Isaac足力超过2N的帧数为`0/240/240/240`，MuJoCo静态计算为`0/1/1/239`；Isaac承重时FR和RL各有239帧在MuJoCo几何下为**正间距**，两脚间距中位数均约`0.7µm`。第200步首子步FR/RL的Isaac足力为`101.83/99.24N`，MuJoCo静态两脚无接触、RR约`22.09N`；编译后的MuJoCo足端和地面几何`margin`均为0。这定位了源姿态下接触激活的持续差异，但静态`mj_forward`不恢复约束求解器历史，静态足力也不能直接与动态PhysX足力等价；前述动态重放在第201步恢复三足接触，仍不能把全部漂移只归因于这组微小间距。新Isaac短窗口报告/子步文件SHA256分别为`767b35543bbb26472af6bd0121e32bdbb797b853ea0ee6433076b406b59e2f8c`、`4f191fb1874c42ec42e0d1de1868bdcbab466057817fc31301b3830a993bd041`，同姿态报告SHA256为`61763f4eb137537f26de86b809abd715f418a194e7575f1cfece1a65d6fbca82`，比较脚本SHA256为`4b4d8175c5f936b9550c926b3d4503f6702b297b0b0219239588797858169a26`；远端/仓库外本地副本一致，目录为`isaac-substep-probe-v4/`和`climb-contact-substep-static-v1/`。没有更改碰撞、接触边距或候选控制器。

同一240帧间距的**离线几何阈值**扫描进一步表明，统一增加四足接触边距不能按间距单独复现源端承重标签：约`1.985µm`可将FR/RL/RR全部纳入接触候选，却也把Isaac中未承重的FL纳入44帧；零边距则漏掉FR/RL各239帧。这只计算`gap <= margin`的候选关系，不代表44帧都会产生超过2N的动态足力，也没有改动MuJoCo模型。只读查看与`actual-physics.json`哈希匹配的选择性碰撞USD：FR足底碰撞体为半径约`0.022m`的球，和MuJoCo足端半径相符。2026-10-09进一步核对组合后的USD及实例原型：`FR_foot/collisions`是实例，普通USD遍历不进入其中；原型下确有`PhysicsCollisionAPI`球体，未显式写入`contactOffset`、`restOffset`或物理材质绑定。来源七项资产SHA256均与`actual-physics.json`匹配；只读报告SHA256为`a66bc0232d29bbcd4796e1b3d3d9da1a0de22e8b33ab8cc572689fb873a1a805`，脚本`mujoco/inspect_current_climb_usd_contacts.py`的SHA256为`0fe1c9e8a4505505eed1b4d5f5eba7e8ef969cd3bf497cbe85f7421c1c888ae3`，远端及仓库外本地报告一致。USD中未作者这些值不能推断PhysX运行时的有效偏移或与MuJoCo求解等价。须比较PhysX实际接触生成/恢复，不能把统一边距扫描当作修复。

**子步PD相位与闭环对照（2026-10-09）**：上述Isaac探针在`scene.update`后采样，记录力矩对应*前一个*5ms关节状态。用当前记录目标、前一个状态及原腿部`30*(target-q)-0.6*qvel`计算，239帧12轴RMSE仅`3.23e-7N·m`、最大误差`1.78e-6N·m`；错误地用同帧更新后的状态会得到`0.0572N·m`。本窗口目标在59个控制步边界发生变化，拟合仍成立。它确认了这段源轨迹的有效PD相位，**没有独立恢复复位时随机选择的延迟**。离线报告SHA256为`c39476438a402dcfbee897359fb1e9594890f01a0df5e16225d9795eb95ffb8e`，脚本为`mujoco/compare_current_climb_substep_actuation.py`（SHA256 `3c9065af6296dd20fd9a43e61dabe215c725bde689f3206bf3134032596bbf4f`）。

在原碰撞、零新增接触边距、原执行器门禁下，将同一源5ms目标送入MuJoCo并用**MuJoCo实时腿状态**闭环计算原PD；手臂暂沿用源记录的子步力矩。这60个20ms步完整跑到第260步，240个物理子步（不含初始化）未记录腿/臂力矩饱和，终态三足承重、无机身触地或自碰；单足力峰`151.26N`、机身竖直速度峰`0.0361m/s`。源端开放环路力矩重放第219步自碰；闭环同一步机身误差从`96.01mm`降至`11.86mm`。但闭环第259/260步误差仍达`98.05/102.42mm`，第260步关节最大误差`0.340rad`，**尚未实现动力学对齐或完整CLIMB sim2sim**。起始MuJoCo只有一足超过2N，第201步起记录的控制帧为三足；控制帧数量不证明所有物理子步均三足。闭环报告SHA256为`3c34d0a0a3d720e650fea616d59f33b77f56038b56d421b07e822099a6bb28e9`，脚本`mujoco/replay_current_climb_trace.py`的SHA256为`b10f5aba64475e007b318feb49962d7c972858862ba0baa3832070761f37da37`；远端报告`sim2sim-current-20261008-a/climb-trace-window-200-260-substep-leg-pd-v2.json`和仓库外本地副本哈希一致。该对照仍使用源记录目标与手臂力矩，未移植`StageGuidance`、304维观测或全阶段控制。

**闭环子步接触定位**：同一控制器补录240个5ms子步后，第200步首子步MuJoCo的FR/RL力为`151.3/144.9N`，Isaac为`101.8/99.2N`；该首子步腿部力矩与源记录的RMSE小于`1e-6N·m`。初态MuJoCo的FR/RL无静态接触，仅RR约`22.1N`，随后首子步产生明显承重冲量，关节最大位置误差已达`0.0296rad`。两端接触求解器的瞬态力不能逐值等同，但**力矩已对齐而首子步接触响应不同**，可排除源端PD相位错误作为这次初始偏差的解释。第260步机身姿态误差约`19.4°`，位置误差`102.42mm`；Isaac三只承重脚在本窗口几乎固定，MuJoCo的FR/RL在首控制步各移动约`5～7mm`，随后误差累积。第210步另取同一源姿态重启50步，初态仍仅RR静态承重，首子步FR/RL约`151.2/144.8N`，源端仍约`101.8/99.2N`，首子步腿部力矩RMSE `3.81e-7N·m`；第260步机身误差仍达`67.47mm`。重启改变诊断起点，两个末端误差不是同一起点成功率。补录报告SHA256分别为`6fc9277a37c21d6e812c23239fb49076a3655f4e86dab3c7b2d14316bc0688af`（200～260）和`fe891edf2a12cfc126c5045355b18d046a8e5d5572932eee5ca8df946e656ad3`（210～260），远端/仓库外本地副本一致；当前脚本SHA256为`0cada4d8188928abe3f19474d10dc3790df86dcef16ab6ca2bca82f4ef8302ab`。这仍是人工重置短窗口，未恢复PhysX约束历史或移植阶段控制。

**接触顺应性定位扫描（2026-10-09）**：保持原碰撞、零新增接触边距、源5ms目标闭环腿部PD和原执行器/碰撞门禁，只改MuJoCo全几何`solref`时间常数，从原默认值分别试`0.03/0.04/0.06s`。三次均跑完200～260步、240个子步，无记录自碰、机身触地或腿/臂力矩饱和。首子步FR/RL接触力从默认`151.3/144.9N`依次变为`129.7/124.7N`、`119.8/115.2N`、`110.3/106.3N`，更接近Isaac的`101.8/99.2N`；第260步机身位置误差依次为`27.46/37.20/83.28mm`，默认是`102.42mm`。但Isaac的FL在全部240子步均未超过2N，三个扫描版本却分别在`130/158/147`个子步超过2N，峰值`7.61/9.81/20.88N`；默认版为0。更软接触改变了支撑模式，且误差不随首帧足力单调改善，**不能把`0.03s`或其他扫描值采纳为sim2sim修复**。三份报告SHA256依次为`616ec9693454440ef1425f9679b661c0be33be7e1bc948a799673bd679c5fc84`、`6d743c3e3738119d08f07f59871115eed5a9ba3ea380dd47f862963f1c5a2e68`、`ae87ee3fe0ea6e77e944bd06a7477aaf180db6cabf6062c360ba81bd758ac242`；远端目录`sim2sim-current-20261008-a/`，仓库外本地副本同名且哈希一致。扫描脚本`mujoco/replay_current_climb_trace.py`的SHA256为`e227b2bb84facdc9a6e5092ef1618e5401b08684816ea7b2b3818835ffa64683`。下一步需核对PhysX运行时有效接触参数、约束历史与相位，并同时要求摆动脚不误承重；单一末端位置误差不足以选择参数。

**Isaac足底接触点实测（2026-10-09）**：在匹配iy的独立完整训练树，仅增加四个足底到`/World/ground/terrain/mesh`的只读接触传感器及场景属性采集；原261步env0控制轨迹和240条原子步字段分别与前次探针的哈希`4fd234ca7a7e9d5ab3751ca97a8608e3446c9085e023d973eea239d07916143f`、`bf582b23668a31a2e30ef59942749f764ebed89abb08e9b374969d171c3f9bc0`一致。FR、RL各在240/240子步有超过2N的地形接触力，其中各239步的接触点**分离距离为正**；首子步FR为`101.83N/+0.808µm`，RL为`99.24N/+0.929µm`。两足全窗口分离距离范围分别为`-0.212～+2.081µm`、`-0.641～+1.453µm`；RR持续承重，FL虽有73条接触点记录但力峰仅`0.083N`，没有超过2N。由此确认PhysX在此窗口实际给正分离距离的FR/RL接触点施加了承重力，也解释了同姿态静态零边距MuJoCo漏接触的现象；**不能仅凭分离距离反推有效接触偏移，更不能把统一边距或顺应性扫描值当作修复**。匹配场景USD的四足球半径均为22mm，接触/静止偏移均无写入值；地形API读到未写入的`-inf`哨兵值，不代表PhysX内部参数。独立探针`isaac-contact-patch-probe-v2/`退出码0、报告齐全，原始`report.json`、`substeps.json`、`contact-scene.json`的SHA256依次为`53eeb58a6e915f32ecccc7eb796660fa1d2d8241ee9c96e21216bfa22a2723e5`、`30e3c49fb07f38dbaebed9251cc9a59952e14e1975fb0a0b1894b7a9e4f87452`、`ff4524e1e9c0dbd57acb1ff5802c392a22e73c08da379d2d12b561b43b6b23a4`，远端与仓库外本地副本一致；评估探针源码SHA256为`9e796d757e43e147d36ca1b0883e33106f9a08ded46f1c46e594519b5362de54`。另外只读组合USD API报告`climb-usd-contact-schema-values-v6.json`的SHA256为`631902a78602cc946811fbfdae9b61f26b03eb08ec8813613540d65d26a75c4d`，对应仓库脚本`mujoco/inspect_current_climb_usd_contacts.py` SHA256为`8aaf1e66f58d9fac6f53fcf1b14d4fcc0f9be0e2a26374a084074b6412b8e312`。继续比较两引擎的接触生成、持久化和闭环逐步漂移，再移植完整阶段控制器。

**质量来源与隔离动力学对照（2026-10-09）**：`actual-physics.json`（SHA256 `ac97d8d7fa82f2ef5fcf134a54ab86ba0a7e708040a766c7efeab688ca6dbeb4`）同时记录构造时质量缓存与PhysX启动后实际质量；env0机身分别为`7.287001/8.701341kg`，整机分别为`21.765001/23.179340kg`。匹配iy的只读Isaac探针再次取得启动后机身质量、质心及惯量；机身惯量相对当前MuJoCo本体配置基本按质量比`1.194091`倍缩放，质心位置相同。探针退出0，第0步env0轨迹与先前探针哈希`73e21e97b51c92b503536ed9b6dcc1511822ed92100a6b86b17390128ca3313f`一致；`isaac-base-dynamics-probe-v1/base-dynamics.json` SHA256为`56ac8a45ac7f0d4ec42956ea89409359c44e50699b66e3680883201a1b0f401c`。在相同200～260步闭环短窗口中，单把地面滑动摩擦从`0.6`调到`0.8`，末端机身误差仅从`102.416`降至`101.683mm`；只匹配实际机身质量后降至`50.385mm`，再同比缩放机身惯量为`50.415mm`。但后两者均让源端全窗口未承重的FL在`42/240`子步超过2N（峰值约`4.55N`）；摩擦对照为`0/240`，三组均跑完整个窗口且无记录自碰。报告SHA256依次为`0996ee72ba5ff51ff3d7dbddd5f607d83fe41b0721ae82e1faeb6cb25311a7b7`、`79ce9c874f8a21e8721ac545f6f8c549918a9c3c58a8241cae066135f1eba82e`、`56bc4e61773a89e00f1ddf438be9cb241b2299351e996dedaec92a580bce4741`；远端及仓库外本地副本哈希一致。质量对齐揭示此前遗漏的物理参数差异，**仍不能作为最终修复或sim2sim通过**：摆动脚误承重且余下约50mm漂移；下一步定位FL首次误承重时刻、足端轨迹、接触力和目标相位。

对质量匹配报告逐子步复查：FL误承重集中在第202～211控制步（每步4个子步，共40个），即源端第212步起摆**之前**；另2个发生在第259步末尾。首次第202步首子步MuJoCo/Isaac FL力为`2.033/0.054N`，足端z为`0.023429/0.023602m`，机身z误差约`-1.21mm`；峰值出现在第207步第2子步，为`4.549N`。第259步末尾MuJoCo FL足端z约`0.213m`、源端约`0.255m`，需要结合箱顶碰撞与足端目标检查。故`42/240`不是整段持续误承重，也不能单用末端机身误差解释；优先定位第202步前的初始接触/质量响应，再分析末尾箱顶接触。

从源端第210步另行重启的质量匹配对照（50控制步/200物理子步）又显示起点敏感性：相同零边距与原门禁下，第260步机身误差为`89.85mm`，未匹配质量的同起点对照为`67.47mm`；第255～259步RR有12个子步降至≤2N，仅剩FR/RL两足超过2N，而未匹配质量对照全程至少三足超过2N。质量匹配对照无FL超过2N、无记录自碰/机身触地/力矩饱和，单足力峰`151.68N`、竖直速度峰`0.1043m/s`；报告SHA256为`88c25026026e986bdc220b5702f454717440e938142b699bc16393d14ea4bcfa`，远端与仓库外本地副本一致。该人工重启未恢复PhysX约束历史，与200步起点结果不能合并成成功率；质量匹配对支撑及误差的影响依赖起点，须保持诊断性质。

下一步继续核对PhysX接触生成/持久化与MuJoCo闭环逐步漂移；有效接触偏移仍未取得，不靠加边距或取消安全门禁掩盖漂移。再以匹配的`iy/source-payload.tar.gz`和完整训练底座为准，移植`StageClimbAction`/`StageGuidance`的支撑转移、足端落脚重载、前腿展开和停稳控制，逐项对照传感状态、参考平滑与命令。最后进行完整回合与独立种子验收。304维观测仍需核对，但在这版零残差actor下，拼出304个数本身不构成控制器移植。上述迁移不改变Isaac的iy候选和既有安全门禁。


<a id="nav-climb-chain-development-20261016"></a>

## NAV→CLIMB→NAV连续切换开发记录（2026-10-15～16）

以下按记录时点保存逐版诊断和计划哈希；其中的“当前/运行中”描述属于当时状态。接手时先读[当前CLIMB交接](../CLIMB_CRAWL_STATUS_20261001_CN.md)，再核对实际进程与报告。历史物理结果与失败记录保留，不能混用不同控制器成绩。

## NAV→CLIMB→NAV当前开发（2026-10-15）

**v040已取得1条受保护NAV→CLIMB→NAV完整开发正例；最新修复版CLIMB在同控制器3个开发起点均完成，其NAV出口的参考限位及低速停滞修复后，v047/v048同版整链2成功/1足位域失败，延长渐入仍失败，v052真实前脚补步通过且未再越界，但低速推进超时；v055/v056同版3701/3702完整成功、3703超时；v058已推进至位置域但减速过晚未停稳；v060提前减速仍未停稳；v062已完整成功、v064回归中；执行层复核发现制动臂参考速度边界突变，v066/v067继续验证。完整链鲁棒性、效率与正式验收仍未完成。** 早期入口候选`transition-nav-climb-v013`在3701～3708上8/8停车成功，0失败、0终态缺失，耗时10.06～18.10s。它不包含CLIMB激活、登台或台面NAV；已用起点回归不能代替最终两组未用种子验收。产物根为`sim2sim-current-20261008-a/`，读取各候选`plan.json`、`screen-summary.json`、`parking-audit.json`及实际进程。

v013保留iy场景与原始reset分布、NAV权重、观测/动作顺序、PD和执行器延迟。机器人从真实初态行走至台前机身x=0.35m，无stage bank加载、无中途物理状态改写。NAV腿反馈从第一条命令开始执行；臂前2s执行初始化（含0.08s重力补偿渐入），随后用4s渐入NAV臂输出。此初始化不宣称第一条目标与reset目标连续。接近阶段保留速度限幅/变化率，只将减速计算的停车偏置从4cm改为2cm，避免指令在目标5.2cm外过小而停滞；实际5cm停车范围不变。

到点后，独立承重制动在四脚各≥12N、零速度请求、台前足位、姿态/限位满足时检查摩擦0.3下的支撑合力/力矩可行性与腿力矩比<0.75。动态制动启动域为线速<0.08m/s、角速<0.4rad/s、竖直速度<0.04m/s、腿速<0.95rad/s、臂速<0.4rad/s；**这只是制动入口，不是READY**。控制器保持捕获的臂姿态及身体位置/朝向，以实际质量、COM和Jacobian分配支撑力。参考位置从最后下发目标接续，以实测关节速度初始化，腿/臂速度限制1/0.45rad/s、加速度限制4/1rad/s²；不声称原NAV参考导数连续。

最终停车门禁保持：位置误差<5cm、姿态合格、四脚各≥8N、线速<0.025m/s、角速<0.1rad/s、腿速<0.35rad/s、臂速<0.2rad/s、足端仍在台前及无安全失败，连续0.5s。原碰撞/姿态终止保留，并全程执行含初始化的臂物理子步0.98力矩门禁。八例三帧实际下发动作历史误差均为0，参考限速/限加速度及最后25个控制步停车条件已独立核验；未重置执行器队列。

| 起点 | 停车时间(s) | 最大臂/全关节子步力矩比 | 腾空/少于三足/恰好三足样本 | 最大竖直速度(m/s) | 单脚/四脚合力峰(N) |
| --- | --- | --- | --- | --- | --- |
| 3701 | 11.76 | 0.93931/0.93931 | 1/5/137 | 0.50181 | 209.20/375.12 |
| 3702 | 11.96 | 0.90295/0.90295 | 1/7/237 | 0.37105 | 144.68/286.46 |
| 3703 | 10.06 | 0.89439/0.89439 | 1/6/168 | 0.44408 | 179.33/325.43 |
| 3704 | 18.10 | 0.94650/0.94650 | 1/6/145 | 0.48964 | 211.61/346.90 |
| 3705 | 10.50 | 0.95406/0.95406 | 0/5/126 | 0.48982 | 222.38/361.76 |
| 3706 | 11.54 | 0.84629/0.84629 | 0/9/231 | 0.40113 | 133.26/313.39 |
| 3707 | 11.84 | 0.95571/0.95571 | 0/8/152 | 0.51347 | 201.63/356.39 |
| 3708 | 10.40 | 0.95737/0.95737 | 1/9/142 | 0.51250 | 202.97/342.20 |

这些足力/支撑统计包含初始化，按控制步计数；部分起点有1个无支撑控制步，不能宣称全程无腾空。身体启动下沉仍需结合原速录像检查，8/8停车通过不等于全程运动质量验收。物理子步力矩单独记录，控制步足力不能代替子步碰撞检查。

已归档的关键诊断：v010同源八例4停车/4启动臂超限，0缺失；v011单加启动预测臂力矩保护后3702在0.34s区间无解、3701停车通过；v012用原生NAV腿反馈替代启动固定腿参考，两例启动门禁均通过，但3702停在5cm外超时、3701停车通过；v013只修正减速计算后完成上述8/8回归。启动失败轨迹中机身下沉约9cm、俯仰速度约1.1rad/s，随后肘腕超限；旧候选证据保留，不把各版结果拼成同版成功率。

**v014原CLIMB臂参考转换已完成2/2开发验证。** v013八例审计通过且GPU空闲后才自动启动3702/3701两例。先通过真实停车门禁，再用6s五次曲线从最后下发臂目标转到原CLIMB软限位内默认PD参考`[0,0.157,-0.14835,0,0,0]`，保留承重控制与参考限速/限加速度；目标收敛后仍须真实停稳1s。该参考是原CLIMB的控制目标，不要求实测关节等于目标，因为承重PD存在静态偏差。未重设关节状态、不重训技能、不解除原碰撞/执行器门禁。3701/3702分别在18.74/18.94s完成转换后连续1s承重停稳，0失败、0缺失；含初始化的最大臂力矩比0.93932/0.90295。转换前588/598个控制步与v013逐项完全一致；实际动作历史和参考速度/加速度包络均核验通过。实测最终臂姿态约`[0,0.145,-0.033,0,0.100,0]`，与原CLIMB承重PD静态偏差一致。通过只意味着原臂参考承重稳定，不直接赋予CLIMB READY。

v013计划SHA256 `e551951455ec6097a58e77fba5e59a2adc9860796cdd7f9d0304869e804f43db`；v014计划SHA256 `08291889b5fba3015456040aa630a3c929094a1ceedebb56a9665b7c36ac7a52`。v014队列及评估均已结束，结果见`parking-audit.json`与`preservation-audit.json`。旧PUSH模型上的静态臂路径预览只作辅助，不能代替Isaac实测或完整自碰验证。本批尚无新录像。

[独立CLIMB完成判定](../../scripts/piper_climb_completion.py)及[6项边界检查](../../scripts/check_piper_climb_completion.py)已实现：四脚台面安全范围与各≥8N、前脚展开结束、最终调整启动且剩余≤2mm、身体跟踪<1cm、原参考保持≥3s、线速<0.025m/s、角速<0.1rad/s及命令限位满足，连续3s；缺字段/非有限值/缺帧不通过，安全失败优先锁存。四脚字段是`feet_position`，不是单脚`crawl_foot_position`。`climb-completion-gate-v002/`在原64条成功轨迹上识别64/64，完成时刻205.00～252.50s；该64/64仍是历史回放；v015起已在线接入，但连续整链尚无完成正例。

后续整链配置已准备来源适配器：`climb-source-adapter-v001/`从冻结iy评估器和jobs提取59项阶段动作设置，与原解析器/赋值块独立比较完全一致；不应用bank/reset配置，不执行物理。**v015连续接入iy阶段控制的两例已结束，均320s正常超时，0安全终止、0缺失。** 它在v014真实转换停稳后，从最后下发目标、实测足位建立控制器逻辑状态，冻结304维actor与原阶段规划，接入连续3s独立完成信号；不写入物理姿态、不清除动作历史或执行器延迟。使用320s整段延长诊断窗口（含NAV与转换），不是12s/24s验收或可接受最终效率；3701/3702已在18.76/18.96s进入CLIMB并完成实测支撑捕获；此前937/947帧与v014完全一致，首个CLIMB参考位置跳变量0，304维actor输入与实际三帧动作历史核对通过。此前已核对接管前缀；最终两例均未完成首脚重载，CLIMB完成0/2，台面NAV出口尚未实现。候选目录`transition-nav-climb-v015/`，计划SHA256 `2467c8b17b3b9fbabb594530a0f5c5b3541b70b694eabeee00e5cf9fef4b3429`，检查实际进程与`screen-summary.json`后续跑。下一步核对首脚支撑转移、真实落脚重载与完整登台终态，再接台面内NAV小目标及边缘裕量。已有两组32/32登台阶段路径继续保留，280秒仍只作诊断。

v015首脚地面落脚停滞已得到完整终态：首脚约26.7/26.9s摆动到末端后法向力持续为0，直到320s超时；末态足端约为`(0.690,0.127,0.0275)`/`(0.667,0.141,0.0445)`，其他三脚承重。末态首脚请求的关节参考限位超量为0.1338/0.3077rad，不能通过继续等待修复；原控制器保留最后可行参考，真实触地/重新承重门禁正确阻止换脚。原落脚探测仍为4mm/s、最大15mm，不扩大探测或跳过重载门禁。

v016靠近台沿候选已淘汰：真实NAV目标改为x=0.50m后，两例在7.36/9.72s触发原机身接触门禁，实际机身x约0.427/0.442m，尚未停车或激活CLIMB。不能继续靠NAV平移去取得原CLIMB足位。两例0成功、2碰撞终止、0缺失；队列已完成，没有待启动任务。v015/v016的`terminal-audit.json`记录完整终态、每类支撑样本、初始化饱和、竖直速度、足力峰与源哈希，全部实际三帧动作历史误差0。

| 候选/起点 | 最大臂/全关节子步力矩比 | 腾空/少于三足/恰好三足控制步 | 最大竖直速度(m/s) | 单脚/四脚合力峰(N) |
| --- | --- | --- | --- | --- |
| v015/3701 | 0.93931/0.93931 | 1/5/14966 | 0.50181 | 209.20/375.12 |
| v015/3702 | 0.90295/0.90295 | 1/7/15057 | 0.37105 | 144.68/286.46 |
| v016/3701 | 0.94629/0.94629 | 1/7/114 | 0.50181 | 209.20/375.12 |
| v016/3702 | 0.85734/0.85734 | 1/10/228 | 0.37105 | 144.68/286.46 |

**以下为修复前开发记录：旧统一条件准备控制器2完成/1超时，另1起点未运行（0缺失）；不得与后文v037/v039修复版3/3或v040整链单例合并统计。** v017两例均完成首次短地面步，但后续落脚仍因请求关节参考不可行而在320s超时，0缺失、0无效证据、0安全终止；完整实际动作历史误差0。3701在28.24s开始首次上台，3702在28.56s开始第二次地面步，换步前实测足力31.41/27.02N、重载比例1；末态分别首脚悬空/轻触不足，不能计登台成功。320s只作失败诊断。完整审计`transition-nav-climb-v017/terminal-audit.json`，计划SHA256 `e748cc9c6dacde0fdcb8db276873edc8f766e0a5e982aeff9377dcb1b34dc9d4`。

| v017起点 | 最大臂/全关节子步力矩比 | 腾空/少于三足/恰好三足控制步 | 最大竖直速度(m/s) | 单脚/合力峰(N) |
| --- | --- | --- | --- | --- |
| 3701 | 0.93931/0.93931 | 1/5/14776 | 0.50181 | 209.20/375.12 |
| 3702 | 0.90295/0.90295 | 1/7/14808 | 0.37105 | 144.68/286.46 |

源码定位：原通用摆动预检主要覆盖后腿、台面和前脚跟进；`reserve_front_ascent_pose`仅在已有一只前脚上台时生效，全地面入口没有同等完整路径/探测/重载预检。v018在该入口调用原`feasible_support_pose`及完整摆动预检，包含原15mm探测、加载参考、四脚转移路径、几何、力矩和限位检查；不可行时在卸载前以`entry_planning_rejected`结束诊断并保存输入。两例均有明确规划拒绝终态，0缺失、0无效证据：3701在18.98s第一次转移规划被拒绝；3702的两次短地面步均完成重载、未出现原限位停滞，37.14s准备首次上台时被拒绝。规划拒绝与物理安全终止分别记录，不计成功。v018计划SHA256 `9cc797e91a8506c3a5e37cae608a8109b0551b308a53156589e2c07d2f7955af`。

v019仅在上述规划失败时调用冻结的扩大姿态搜索，增加小幅滚转/俯仰候选，全部原路径与落脚门禁保持。3701拒绝状态的数值重规划找到可行解；3702上台前状态仍无可行解。在线物理评估中3701在38.76s将第一只前脚落到台上并重载，随后在下一前脚准备段停滞并90s超时；3702在37.14s保守拒绝，未抬起不可达的脚。两例0完整CLIMB、0缺失、0无效证据。候选仍属90s入口诊断，计划SHA256 `0596d1e8e6ee6675f533b2b8ce0e607c703fa37b6315e9dafa4afad27bd40e5a`；首脚上台不是完整CLIMB完成。

**v020/v021入口诊断均已结束，保留两版完整结果。** 在四脚仍在地面时，先让两前脚分别通过原短步、真实落脚与重载达到x≥0.58m，再恢复原前腿上台顺序。选脚仅由原时钟在初始或真实重载完成时采用，不强制换脚；不写入关节/机身状态，不重置历史或延迟。原iy箱沿初态已满足该条件，原选脚顺序继续保留。3702实测拒绝状态的数值预检证明右前脚短地面步存在满足原门禁的方案，动力学验证待定。v020计划SHA256 `8ee335603a10c570c9874fe61c71b5cff307e0bff144fc8c9e3dfcce21df9dce`。每例仅在同一GPU上对应v019进程退出、终态可核对且无安全失败后启动；检查两版`screen-summary.json`、各`launch-*.json`及真实进程，避免重复启动。90s是入口诊断窗口，不是12s/24s验收或整链完成证明。下一步先确认两脚准备及首次上台，再处理完整登台与台面NAV出口。

v020完整入口诊断：3701两前脚分别在48.64/57.32s前完成上台和重载，随后两后脚连续地面跟进，66.62/75.92/85.30s继续换脚，至90s窗口结束时仍在推进；3702两前脚在地面逐只准备并重载后，53.58s首次上台规划仍被拒绝，未出现原落脚超限。两例0完整CLIMB、0缺失、0无效证据，不计完整登台成功。与父版本逐帧核对：3701修改前1499帧完全一致；3702修改前1856帧完全一致，包含物理状态、实际命令及观测历史。后脚准备候选不覆盖此版成功前缀。

v021的差异：四脚均在地面时，依次将前脚准备到x≥0.58m、后脚到x≥0.14m，后脚目标x=0.15m且单步≤0.12m；完整路径/探测/重载预检扩展到地面后脚。原iy入口正运动学为前脚约0.600m、后脚约0.152m，因此保留其原选脚顺序；这是几何对照，没有注入bank。3702实测拒绝状态的左右后脚小步通过原数值预检；在线两起点均完成左后脚准备，随后在47.20/71.30s右后脚支撑规划被拒绝，0缺失、0无效证据。拒绝发生在卸载前，左后脚准备不等于完整上台。90s入口诊断，计划SHA256 `92f8bfc4106bdca6873c9bbcfa678411c2fef5b9cc2016fce6671b2d81a62cc0`；按相同种子/GPU等待v020对应进程结束才接续，不重复占用。读取v020/v021各自终态，不能将两版成绩合并。

### 连续完整登台正例与当前执行

**v022/3701在268.76s通过在线独立CLIMB完成门禁。** 同一物理回合从原起点NAV停车、原臂姿态承重转换，完成四脚登20cm台面、前脚分别展开4cm、最终重心调整及连续3s实测停稳；无bank注入、无中途物理reset。完成时四脚法向力约36.01/39.94/78.15/82.32N，展开计数2，所有关节请求限位超量0。全13438控制步实际动作历史核对通过，前4499帧（至89.98s）与v020逐项完全一致。1个完整终态、0缺失、0无效证据；只有这一个开发起点，不是未用种子验收。268.76s仍过慢，不作为最终效率达标；后续NAV不计入CLIMB完成定义。

| 已结束候选 | 完整结果 | 含初始化安全/运动统计 |
| --- | --- | --- |
| v022 / 3701 | CLIMB完成1/1；NAV出口未实现；268.76s | 最大臂/全关节子步力矩比0.93931；腾空1、少于三足5、恰好三足4811控制步；最大竖直速度0.50181m/s；单脚/合力峰209.20/375.12N |
| v023 / 3702 | 120s窗口超时；已完成四脚地面准备、两前脚登台及后脚跟进，终态仍在推进 | 无碰撞/执行器安全终止；最大臂/全关节子步力矩比0.90295；腾空1、少于三足7、恰好三足2667控制步；最大竖直速度0.37105m/s；单脚/合力峰144.68/286.46N |

v023前3564帧（至71.28s）与v021完全一致，0缺失、0无效证据。部分转移保持`swing_path_ready=False`，实测停稳再规划，完整抬脚条件满足后才卸载；该机制已让3702通过原右后脚准备阻塞并继续上台。不能因初始化含腾空样本而宣称全程无腾空，也不能把两版结果拼为同一候选成功率。

| 当前候选 | 验证内容 | 边界 |
| --- | --- | --- |
| v024 / 3702 | 原起点完整CLIMB已完成，296.48s，0缺失/无效证据 | 前5999帧至119.98s与v023完全一致；仍无NAV出口且效率未达标 |
| v025 / 3701 | CLIMB全段完全保留，NAV出口在269.32s被指令软限位门禁拒绝 | 首个NAV目标跳变0；出口28帧、原生18轴直通0帧；尚未开始台面目标行走 |
| video-v022 / 3701 | 原速完整录像已生成并同步，1280×720、25fps、268.76s | 13438控制帧及完整终态与v022完全一致；6719视频帧时间轴核对通过；12时刻抽帧检查完成，全片原速人工审阅待完成 |

v025从最后实际下发目标开始有限交权，保留冻结NAV观测分组、动作顺序、PD、延迟和实际历史。台面足位必须满足0.80<x<1.85m、|y|<0.50m、z>0.19m；到点后仍须原保守承重制动预检，再真实四足承重停稳1s，实际行走≥8cm。出口独立30s预算，原碰撞/执行器终止保持；这是待验证的开发控制器，不能提前赋予READY或完整整链成功。新录像只完成完整时序/轨迹审计及抽帧检查，不宣称全片原速人工审阅已完成。

| 计划 | SHA256 |
| --- | --- |
| v022完整登台 | `d75cc1814ddcbd6db7a3f8e14d1266d5df237c32dd0550ec9c121134d413d60c` |
| v023分段承重 | `8a9cc5ccca7bb4e888921928830ea58d4619e63637bb06fd431cf586880aef82` |
| v024完整登台延长 | `85efb67f3a142140493990880cf6a49688d1a2098a8d114419b74cdb8fa13d84` |
| v025台面NAV出口 | `368ad405c7a28e67a5cfcacdece26954864ad36f7c9a04c0b700de5c70a57e8c` |
| video-v022 | `bc2edbd28fc035195ff5684427bacc43197fc66e0cf9c85fe157255ac1f1f30d` |

### 出口修复与同版回归（最新）

v024完成时四脚法向力38.76/46.94/54.33/63.73N、前脚展开2、请求关节限位超量0；含初始化最大臂/全关节子步力矩比0.90295、腾空1/少于三足7/恰好三足5804控制步，最大竖直速度0.37105m/s、单脚/合力峰144.68/286.46N。它与v022不是同一个控制器版本，分别只是1个开发正例；后续需用相同控制代码覆盖多个起点。

v025全13438个CLIMB控制步与v022一致，完成后首个NAV参考跳变0。在交权约0.56s时，左后小腿的原NAV目标请求约−0.780rad，高于源软限位上界−0.932rad；上一已执行混合目标约−0.939rad仍在限内，下一请求被拒绝，未让超限目标进入物理。最终28个出口帧未达到原生18轴全权阶段。含初始化最大臂/全关节子步力矩比0.93931、腾空1/少于三足5/恰好三足4811控制步，最大竖直速度0.50181m/s、单脚/合力峰209.20/375.12N。0缺失、0无效证据；失败原因是出口指令域，不撤销已经成立的独立CLIMB完成。

v026出口修复已结束：原超限指令投影后不再因该限位退出，但在271.00s、NAV交权2.24s时触发足位x>0.80m门禁。机身位移约0.117m，方向主要后退；右后脚x约0.79995m，尚在台面物理边界0.75m内，但已越过预留安全域。此时腿已取得全部NAV权限、臂转换约60%，未开始预定前行，原生18轴直通仍为0帧。该结果支持把同时发生的臂姿态转换与腿接管分开验证，不能通过放宽足位域宣布成功。前13466帧至269.32s与v025完全一致，首个出口目标跳变0，0缺失、0无效证据。

v027同版回归在320s超时：两前脚在台上、后脚仍在地面，卡在右前脚跟进的支撑准备，实际与请求关节限位均未触发终止。已核对v024与v027所有物理控制文件逐字节相同，仅种子及调度不同，因此这版在已用3702/3701上是**1完成/1超时，0缺失**；不能把v022的3701成功替换进来。原直接上台成功路径继续保留，避免对本可上台的起点强制增加后脚绕行。

| 完整诊断 | 最大臂/全关节子步力矩比 | 腾空/少于三足/恰好三足控制步 | 最大竖直速度(m/s) | 单脚/合力峰(N) |
| --- | --- | --- | --- | --- |
| v026 / 3701 | 0.93931/0.93931 | 1/5/4811 | 0.50181 | 209.20/375.12 |
| v027 / 3701 | 0.93931/0.93931 | 1/5/2487 | 0.50181 | 209.20/375.12 |

| 上一轮候选 | 改动/验证范围 | 计划SHA256 |
| --- | --- | --- |
| v028 / 3701 | CLIMB完成后由原承重控制保持四脚，6s有界转换到首次原NAV输出的臂目标，并实测承重停稳1s；随后腿/臂1s有限交权，1.1s后才给前行请求。原软限位投影、足位/碰撞/执行器门禁均保留，出口总预算30s | `d9014813a9b5c43a27f4027f52e9e95c5fafaf26baca22d803b83905cacb1340` |
| v029 / 3702 | 默认保留可行的直接前脚上台路径；仅在首次前脚上台规划完整搜索仍失败时，且原时钟刚通过真实落脚重载后，逻辑选择后脚准备；保留原参考位置/速度和物理历史 | `7be246efe8e43cb45a63a9ca8e62747e2672c52030e05b96f5ef634f41c7e85a` |

v029改选要求前一步真实进度1、重载比例1且承重停稳≥0.2s，下一步进度/时钟均0，四脚≥8N且机身低速，全部仍在地面；不跳过落脚、不伪造换步、不重设物理状态或执行器队列。原参考不重新播种，日志单独记录条件改选事件，结束后核对它与上一真实控制帧的重载及参考一致。若这些条件不满足，仍明确拒绝，不以重置绕过问题。

### 统一控制器开发回归与最新接续

v029/3702在296.48s、v030/3701在268.76s分别通过独立CLIMB完成门禁。两版除调度脚本外的全部物理控制文件逐字节相同，故可作为同一控制器的**2/2已用开发起点完成，0失败、0缺失、0无效证据**。仅两例不足以证明鲁棒性，完成时间也尚未达标。

- 3702在53.58s确实因直接上台规划失败而选择后脚准备：上一脚重载0.22s、四脚均≥26.29N、参考差值0；之后完整14824帧物理状态、实际命令与历史与原v024成功路径完全一致。诊断字段有差异，因此不宣称整个控制日志SHA相同。
- 3701未触发额外后脚准备，完整13438帧控制日志SHA与原v022一致，保留直接上台成功路径。
- 来源核对见`climb-source-adapter-v001/same-controller-v029-v030-audit.json`；完整物理对照见`transition-nav-climb-v029/complete-physical-preservation.json`。v030计划SHA256 `88f665580cd5e5861e83368d9af636c4dad97cf4bd60a623653fd292817aa819`。

v028的承重臂转换已完成并停稳，但NAV腿接管后在276.64s触发原足位域。机身水平位移仅约8.7mm，但下沉约55mm、右后脚退至x=0.79956m；不是原软限位问题，也未取得原生18轴全权。完整CLIMB前13438帧仍与v022一致，0缺失/无效证据，原独立CLIMB成功继续成立。该结果表明需在接管前同时准备机身高度、姿态及后脚空间。

| 当前候选 | 验证范围 | 计划SHA256 |
| --- | --- | --- |
| v031 / 3701 | 使用已两例通过的统一CLIMB控制器；完成后，依据同回合原NAV停车的后脚相对位置、离地高度和姿态，先做四脚承重的机身准备，再转换臂姿态并启动NAV | `b71e44185b9e69061fdf24149c13643eb55b8bbd28d8e36cecbdb9b75529d541` |
| v032 / 3703、3704 | 物理控制文件与v029/v030相同，继续两个已用开发起点；单GPU串行，首个不完成即停止，未执行起点单列 | `b69fd85b02bb9ede97a35d1ff459cbad80995d9201d954f3ca08bec14ca8eadd` |

v031的参考站位由真实NAV停车测量推导。3701的静态几何预检目标为机身x≈1.119m、z≈0.4766m，较CLIMB完成态前移约0.173m、降低约0.0277m并恢复原NAV停车姿态；检查四脚保持原落点的完整路径，未发现几何/旧负载参考不可行。该预检不含完整动态力学，实际运行仍要用实时COM、重力补偿、21点路径与原碰撞形状检查每脚预测≥8N、关节命令余量≥0.03rad、力矩≤75%及力平衡残差。

机身准备按每段≤8cm、3s平滑参考执行，每段须实测位置/姿态跟踪和四脚承重停稳后才继续；然后再做6s臂转换及1s实测停稳。NAV前行12cm从真正NAV接管点重新计算，准备阶段的位移不计作NAV行走。原CLIMB完成时刻/姿态不改，不写入物理状态、不清空历史或延迟。v031总体340s、出口60s均为延长诊断窗口，不能作为最终效率或12s/24s验收通过。

v031/v032均已结束，结果与修复见下节；上述窗口与预检属于开发诊断，不能作为正式验收。

### 最新诊断与活动候选

v031在328.76s以出口60s超时结束：第一段机身准备完成，第二段稳定停在5.60mm位置误差，略超原5mm门禁；四脚持续承重，未进入NAV。v033只给这一稳定小误差增加有界外环积分力反馈（各轴补偿≤0.06m/s²、原总加速度限幅/关节参考平滑不变），保持目标及5mm门禁，随后确实完成三段机身准备、臂转换和1s停稳，在291.32s进入NAV。但其1.1s零请求交权期间发生后脚后退，在292.46s因足位x=0.791999m被原0.80m门禁拒绝。CLIMB与接管前准备完成，不计整链完成。

v032/3703在320s超时、3704按首失败停止规则未运行。3703两前脚上台后，右前小腿与台沿的计算净空约4.67mm，低于原5mm路径门禁，故首个后脚规划一直不可行；没有把等待当成功。与v029/v030物理控制文件一致，合计**2完成/1超时/1未运行，0终态缺失**，详见`climb-source-adapter-v001/same-controller-v029-v030-v032-audit.json`。

v034在第二前脚上台前增加12mm名义余量，43.54s因无完整方案保守拒绝。v035加入原四脚承重的分段准备，实际完成两段后46.58s仍被拒绝。进一步检查发现新增12mm检查也约束了已承重的另一前腿；v037将新增余量限定到目标落脚腿，所有腿仍须通过原5mm路径门禁。原落脚点无解时，在卸载前尝试缩短10/20mm的台面落点，保持目标x>0.80m；不在摆动中改目标。保存状态的数值搜索找到10mm缩短方案：目标腿名义净空17.73mm、全腿15.42mm、命令余量33.82mrad，物理结果待验证。

| 本轮修复候选 | 当前验证内容 | 计划SHA256 |
| --- | --- | --- |
| v036 / 3701 | 保留v033已通过的机身/臂承重准备；NAV交权开始时同步增加已有0.1m/s²限速的前行请求，取消额外1.1s零请求等待；1s权限渐入、0.08m/s上限、足位和停稳门禁不变 | `a3718d0f8071b6868c1e217cbc41e077831aef979c2a766b7b6465536f405adb` |
| v037 / 3703 | 目标前腿12mm名义余量＋全腿原5mm路径门禁；完整方案失败时可先做四脚承重准备，必要时在卸载前选择更短台面落点 | `6d53445540de55b162e3ffc7107f1d70d5efd0123a43bd7e71cb04123b1e142d` |

v036同时修正全权限端点的浮点抵消：渐入结束后直接使用原NAV目标再做保护，使“原生18轴直通”只取决于实际保护介入，而不受混合公式的舍入差异影响。v037的中间准备仍保持`swing_path_ready=False`，只有目标腿余量、全腿路径、加载参考及实测卸载/落脚门禁均通过才抬脚。两版均未改物理状态、权重、原PD或延迟。

| 已结束候选/起点 | 最大臂/全关节子步力矩比 | 腾空/少于三足/恰好三足控制步 | 最大竖直速度(m/s) | 单脚/合力峰(N) |
| --- | --- | --- | --- | --- |
| v031/3701 | 0.93931/0.93931 | 1/5/4811 | 0.50181 | 209.20/375.12 |
| v032/3703 | 0.89439/0.89439 | 1/6/1077 | 0.44408 | 179.33/325.43 |
| v033/3701 | 0.93931/0.93931 | 1/8/4827 | 0.50181 | 209.20/375.12 |
| v034/3703 | 0.89439/0.89439 | 1/6/829 | 0.44408 | 179.33/325.43 |
| v035/3703 | 0.89439/0.89439 | 1/6/829 | 0.44408 | 179.33/325.43 |

以上含初始化，五版均有完整终态与历史审计，0缺失/无效证据；未运行的3704单列。实际接续请检查v036/v037的进程、`screen-summary.json`和`terminal-audit.json`，不重启已运行任务。自动审计及本地小型产物同步已配置；原成功路径继续保留。340s/320s仍是诊断窗口，正式验收与提速尚未完成。

### 本轮接续状态

v037已跨过原3703的首后脚阻塞：45.06s在卸载前选择将第二前脚台面落点由x=0.83缩短到0.82m，完整预检全腿净空12.16mm、目标腿15.65mm、命令余量39.36mrad；53.58s完成该前脚真实落脚/重载，随后61.36、70.60、79.88、89.10、96.78s连续通过后脚换步。随后该回合在252.04s通过完整独立CLIMB完成门禁，0缺失/无效证据；这是修复版在3703的1/1开发结果，不能与旧控制器成绩合并。所有换脚仍需原真实落脚、重载比例1及停稳，目标调整发生在摆动前。

v036在292.20s触发原物理子步力矩终止：腕关节joint5达到−5.0Nm、力矩比1.0；此时线性预测保护的目标比为0.90，但未覆盖实际瞬态。此例CLIMB完成和承重准备成立，整链失败，0终态缺失/无效证据；不能用预测比或50Hz控制记录掩盖子步饱和。含初始化腾空1、少于三足6控制步，最大竖直速度0.50181m/s、单脚/合力峰209.20/375.12N。

| 当前接续 | 边界与验证内容 | 计划SHA256 |
| --- | --- | --- |
| v038 / 3701 | 保留v036准备与同步前行请求；NAV臂参考取速度≤0.45rad/s、加速度≤1rad/s²、85%原PD/40ms预测域与原软限位的交集。空交集明确拒绝，实际98%子步终止不变 | `1e739e8eb27d1cb56ee693ef1365a846e0171203adcd01320baa13fcf8fa01cf` |
| v039 / 3701、3702 | 物理控制文件与v037相同；已完成两例：257.34/289.98s；与v037共同构成修复版3/3开发完成 | `90fb965e840462bf897b6ee6a6660635e85c14e59c452a2bde3e626dff4bdbf1` |

v038参考从最后实际下发臂目标及其命令速度接续，不清空历史/延迟，不改策略权重或PD。纯数学200样本检查验证速率/加速度包络及空交集拒绝，不等于物理验证。滤波介入帧只标受保护NAV，原生18轴直通样本另计；即使未来任务完成，也不把受保护执行描述为全程原生直通。v038最终被旧任务成功终止打断，详情见下节。

v037完整审计：252.04s、前2176帧至43.52s与v035一致；含初始化最大臂/全关节子步力矩比0.89439、腾空1/少于三足6/恰好三足4971控制步，最大竖直速度0.44408m/s、单脚/合力峰179.33/325.43N。只证明该开发起点修复，不宣称效率达标。

v038/v039均已结束。修复版保留3701/3702完成能力，旧基线结果单独保存；当前接续核对v064、v066/v067及v062录像实际进程，避免重复启动。正式批量验收、效率验收和实机均未放行。

归档计划：v026 `ad1ee6b4be1dc213c946bb9d88b9cbd467cae5bfc1b8bb1379a6b3d9fd44768e`；v027 `ea7eeedc6b4a43ff75a79375a0a04ed5940419bead710e996174f8eeb5b415f3`。同版回归核对见`climb-source-adapter-v001/same-controller-v024-v027-audit.json`。

原速视频`transition-nav-climb-video-v022/seed3701/nav-climb-v022-original-speed.mp4`，SHA256 `704a95cb0013587490c2140deb52175265290910bc4cae9f844ba8094811c7bd`。抽查0/6/12/19/30/49/58/90/150/210/250/268s，机器人与台面可见、原NAV立臂与CLIMB姿态转换可辨，未见明显跌落；首个抽样帧有渲染启动暗画面，后续样本正常。该视频没有NAV出口，图像抽查不能代替碰撞审计或全片原速人工审阅。后续顺序仍为完整CLIMB及NAV出口证据→同候选开发起点回归→冻结候选及未用种子验收；保留实际落脚/重载/停稳门禁。


候选源码位于独立产物目录，未修改冻结iy源、权重、PD或碰撞门禁，也未并入交付代码。完整大控制轨迹保留原件，本地仅同步摘要、规划输入和哈希；`local-sync-manifest.json`明确哪些轨迹未同步，不能把局部前缀当完整回合。

## 最新完整链证据与接续（2026-10-15）

**首次完整链成功为v040/3701，296.26s；最新CLIMB修复版为v037/v039同控制器3/3。两者控制版本不同，不能合并宣称最新完整链3/3。** 全部为已用开发起点，340s是整链诊断窗口；约五分钟仍不满足最终效率要求。

| 候选 | 已完成的物理结果 | 限定 |
| --- | --- | --- |
| v037/v039 | 3703、3701、3702分别252.04、257.34、289.98s完成独立CLIMB；3/3、0缺失、0无效证据 | 同控制器核对见`climb-source-adapter-v001/same-controller-v037-v039-audit.json`；无NAV出口 |
| v038/3701 | 295.40s由旧`box_settled`成功条件终止；到点误差10.225mm、NAV位移114.875mm，但独立停稳仅0.12s | 非物理安全失败；不能计完整链成功 |
| v040/3701 | 296.26s完整链成功；独立CLIMB在268.76s完成，NAV出口27.50s | 1/1开发，0失败/缺失/无效；采用较早CLIMB成功路径 |
| v041/3703 | 252.04s完成修复版CLIMB，随后出口规划拒绝；前12602帧与v037一致 | 目标最小预测足力6.0599N，低于原8N门禁；未冒险开始该段 |
| v042 | 前置成功断言未通过，未启动物理 | 调度失败单列；不能计种子物理失败或终态缺失 |
| v043/3703 | CLIMB在252.04s完成；出口承重准备通过，NAV前进56.4mm后于274.32s拒绝继续 | 腕部参考接近原软下限，剩余减速距离不足；0缺失/无效，整链失败 |
| v044/3701、3702 | 前置成功条件未通过，两例均未启动物理 | 已补齐未运行审计；不是两例物理失败或缺失 |
| v045/3703 | 软限位减速修复通过物理执行；312.04s出口超时，NAV前进73.691mm，终态目标误差49.587mm | 0缺失/无效；原安全终止未触发，整链仍失败 |
| v046/3701、3702 | 前置完整成功条件未满足，两例均未运行 | 已生成未运行审计，0缺失 |
| v047/3703 | 284.24s完整成功，台面NAV前进115.352mm、目标误差14.439mm、承重停稳1s | 0缺失/无效；持续停滞补偿修复该例 |
| v048/3701、3702 | 3701于284.72s完整成功；3702于310.44s台面NAV足位越界拒绝 | 与v047同控制器合计2成功/1失败，0缺失/无效 |
| v049/3704～3708 | 前置3例完整成功条件未满足，5例均未运行 | 已生成未运行审计，未占用物理资源 |
| v050/3702 | 311.72s仍因足位域拒绝，3s渐入未修复该例 | 0缺失/无效；姿态门槛亦未满足 |
| v051/3701、3703 | 前置完整成功条件未满足，两例均未运行 | 未运行审计完成，0缺失 |
| v052/3702 | 两次补步真实重载及停稳通过；NAV未再越界，但409.98s出口超时 | 0缺失/无效；前进49.884mm，终态目标误差70.603mm |
| v053/3702 | 409.98s出口超时，已前进91.795mm，终态误差29.779mm满足位置域；未停稳 | 0缺失/无效；最小误差17.283mm，但实际请求始终未全归零 |
| v054/3701、3703 | 前置完整成功条件未满足，两例均未运行 | 0缺失，未运行审计完成 |
| v055/3702 | 348.98s完整成功；NAV前进96.323mm，终态误差29.579mm，真实承重停稳1s | 完整审计有效，0失败/缺失/无效；补步真实重载审计通过 |
| v056/3701、3703 | 3701完整成功310.96s；3703出口超时372.04s | 同v055合计2完整成功/1超时，0缺失/无效 |
| v057/3704～3708 | 前置完整成功条件未满足，5例均未运行 | 汇总2成功/1失败/5未运行，不能称8例已验收 |
| v058/3703 | 372.04s出口超时；NAV位移152.174mm，终态误差34.851mm；仍未承重制动停稳 | 0缺失/无效；实际请求归零时已偏出位置域 |
| v059/3701、3702 | 前置完整成功条件未满足，两例均未运行 | 未运行审计完成，0缺失 |
| v060/3703 | 372.04s仍超时；NAV位移155.371mm、终态误差36.910mm，未进入承重制动 | 0缺失/无效，单独提前减速意图未修复 |
| v061/3701、3702 | 前置完整成功条件未满足，两例均未运行 | 未运行审计完成，0缺失 |
| v062/3703 | 完整成功320.00s，终态误差25.007mm、NAV位移142.595mm，请求归零且真实停稳1s | 0缺失/无效；另发现制动臂参考速度交接不连续，不能据此放行平滑切换 |
| v063/3701、3702 | 调度器早于前置状态文件创建，未启动物理 | 2未运行、0缺失，原失败记录保留 |
| v064/3701、3702 | 3701已报告309.50s完整成功；3702仍运行 | 与v062物理代码相同；组审计待结束 |
| v065/3704～3708 | 为先修复制动参考连续性，已在启动物理前替代该扩展队列 | 5例均未运行，当前v064和录像继续完成 |
| v066/3703 | 待v064结束后验证制动臂参考按最后下发速度接续 | 其他控制与物理门禁不变；增加跨交接速度/加速度审计 |
| v067/3701、3702 | 等待v066完整成功且跨交接参考平滑审计通过，再回归 | 同v066物理代码 |

v040只把原`BoxSettled`成功终止改为记录事件：原谓词、计数器、保持时间不变，原失败终止与超时保留。旧成功在295.40s触发后继续原物理回合，不reset、不注入bank、不清除动作历史/执行器延迟；此前14770帧与v038完全一致。最后NAV目标误差10.105mm、从实际NAV激活位置前进117.275mm（承重准备位移不计入）、连续真实承重停稳1s，位置/姿态/足位域/安全门禁全部满足。

该出口采用明确的臂指令速度/加速度限制及预测力矩保护：163个限速执行样本、161个保护介入样本，**原生18轴直通样本为0**。首出口参考跳变0，实际三帧命令历史误差0。只能称“受保护NAV接管”，不能称全程原生直通。

| v040含初始化指标 | 数值 |
| --- | --- |
| 最大臂/全关节子步力矩比 | 0.9393118 / 0.9393118，无饱和 |
| 腾空/少于三足/恰好三足控制步 | 1 / 11 / 4856（14813步） |
| 最大竖直速度绝对值 | 0.501815m/s |
| 单脚/四脚接触合力峰 | 209.196 / 375.119N |

上述统计含初始化，不能与排除初始化的旧阶段统计直接比较；50Hz支撑统计也不等于物理子步支撑审计。证据为`transition-nav-climb-v040/terminal-audit.json`，计划SHA256 `3a9a30f95e16a1f622ebab0c8487fa9531932295ec4a905b5cd4ab2978fc87ae`。

v043只修正出口承重目标的选择：优先使用同回合NAV停车推导的原目标；原21点完整路径检查、15N规划负载余量和预期NAV足位裕量均满足时保持原目标，否则按距离搜索x后退0～40mm、y偏移0/±5/±10mm，并重新执行全部路径检查。实际8N承重、5mm跟踪、足位域及98%子步力矩门禁不变。v041保存初态的数值预检找到x−20mm/y+10mm目标，预测最小足力15.581N；**静态可行不等于物理通过**。v043计划SHA256 `008edf0e67b44f152994436db950e39dd4f3ab684b1942158a6bff1de95b970f`；v044计划SHA256 `80c9d06d0c179b780df37bc49a2318b8353dd670f4e8aa6e86ac2e8f56987fb7`。


v043已验证出口承重目标修正能够继续执行，但未完成整链：失败前NAV实际位移56.423mm、目标误差69.035mm，姿态和台面足位门禁为真，原安全终止项未触发。含初始化最大臂/全关节子步力矩比0.8943883，腾空1/少于三足10控制步；完整终态与历史审计有效。这仍是失败记录，不能只凭无安全终止称为成功。

v043失败点的数学归因为**静态软限位前的参考减速距离不足**：joint5原软下限约−1.098rad，最后参考−1.095494rad、速度−0.191796rad/s；仅余2.506mrad，按原1rad/s²减速度不能在下一步兼顾平滑和限位。此前策略曾请求低于软限位的目标，旧滤波只做当前步交集，未约束后续停止可行性。v045在原交集上追加`dt·|v_next| + v_next²/(2a) ≤ 距离原软限位`，并将期望目标投影到原软限位；原0.45rad/s、1rad/s²、85%/40ms预测力矩及98%实测子步门禁不变。

保存输入的单关节数学回放逐样本重现旧参考及其失败；新版首次改动在274.22s，回放至原失败输入不再出现空交集。另完成2500步双向越界目标/随机反转检查，真正不可行的力矩交集仍拒绝。此测试复用了旧实测状态，**仅证明参考算法修复，不代表新闭环物理成功**。证据`transition-nav-climb-v045/reference-braking-check.json`；新物理回归从原初态开始，不跳到故障状态。

首条整链原速录像：`transition-nav-climb-video-v040/seed3701/nav-climb-nav-v040-original-speed.mp4`，296.26s、50fps、1280×720、14813帧。完整控制轨迹及报告均与v040一致，SHA256 `d0d8947b2e4f6e925afbd12a4a3e7c08b91791098a33c5a904c3080a21619e82`。已抽查16帧，覆盖初始NAV、登台、展开、承重转换、立臂NAV及终态；画面正常，所抽帧未见明显跌落。**全片原速人工审阅仍待完成，抽帧不能证明动作平滑或无瞬时穿模。** 旧v022录像保留，其不包含NAV出口。

计划SHA256：v045 `7473549af4737d1e6d6f9c9a9c03f1e363fef9fd07a4ba8a6f9c9ccdc75e911a`；v046 `ff65ad460fdc70c880a813f203db0d927ff4aa126da572276198cec5cbddf6ad`。两版都有终态审计和本地小型产物同步；v046前置不满足时明确记录未运行。


v045完整物理验证已消除原274.32s软限位交集拒绝；前13567帧至271.34s与v043一致，实际三帧历史通过核验。含初始化最大子步力矩比0.8943883，腾空1/少于三足10/恰好三足5080控制步，竖直速度峰0.444084m/s、单脚/合力峰179.334/325.426N，未出现新的安全终止。但出口运行满60s仍未完成，不能计完整成功。

新的停滞证据：台面NAV最小目标误差29.028mm，虽有558帧满足35mm位置门槛，却始终未进入原25mm零请求范围，零请求帧为0；制动预检原本要求请求归零，因此未开始真实承重制动。末段前进请求约0.035～0.057m/s，机身在目标前反复摆动。v047只在实测连续2s前进不足5mm、目标仍在前方25mm外、此前前行请求为正时启用低速补偿：正向请求先取至少0.08m/s，再经过原停车距离上限和原0.08m/s最大值、0.1m/s²变化率。原25mm归零、35mm到点、12N制动捕获、真实1s停稳及臂保护不变。

保存轨迹上的触发检查：v045在277.00s满足停滞条件，v040完整成功轨迹不触发；另完成600点距离范围检查，速度与归零包络均保持。该诊断不等于新物理通过，回归仍从原初态执行。证据`transition-nav-climb-v045/seed3703/nav-progress-diagnostic.json`、`transition-nav-climb-v047/progress-request-check.json`。v047/v048已配置终态审计及本地小型产物同步。

当前计划SHA256：v047 `81fba060b9357e1b9ff9cc3aaac2be2d43b452facae8425fc7a710cd1c229f2a`；v048 `995e9c33c4d3e4ed8b3ac26170f32c8d7dea9b6d259ef3591ef1fe729620599d`。


### 2026-10-16：同版整链2/3与出口足位域修复

v047/v048除调度脚本外的控制文件哈希相同；3例独立CLIMB均完成，完整链2成功/1失败、0缺失/0无效。证据`climb-source-adapter-v001/same-controller-v047-v048-audit.json`。3701的完整成功保留，不能把这3例算成3/3整链，也不能将旧v040混入同版统计。

| 同版起点 | 完整链 | 含初始化最大子步力矩比 | 腾空/少于三足/恰好三足控制步 | 最大竖直速度(m/s) | 单脚/合力峰(N) |
| --- | --- | --- | --- | --- | --- |
| 3703 | 成功284.24s | 0.8943883 | 1/10/5136 | 0.444084 | 179.334/325.426 |
| 3701 | 成功284.72s | 0.9393118 | 1/10/4859 | 0.501815 | 209.196/375.119 |
| 3702 | 足位域拒绝310.44s | 0.9029478 | 1/10/5834 | 0.371053 | 155.851/286.460 |

3702在289.98s完成CLIMB，承重及臂转换均通过。约309.40s开始NAV控制权交接，随后机身从x≈1.1306后退至1.0587m，左后脚x降到0.79745m，越过原0.80m安全边界；原边界门禁拒绝继续。交接段腿参考峰值约19.92rad/s，末段机身后退速度约0.17m/s。相同开发控制器在3701也出现约19.79rad/s参考峰值但成功，故该值本身不能确认为唯一根因；需进行控制权交接对照。

v050只将腿部五次平滑渐入从1s延长为3s，并将制动资格的“渐入后0.1s”相应保留；臂1s渐入、策略、PD、真实历史、CLIMB完成及出口准备、速度请求与全部物理门禁不变。该改动是待验证假设，不宣称已解决；v051仅在3702完整成功且审计有效后回归3701/3703。

`transition-nav-climb-video-v047/seed3703/nav-climb-nav-v047-original-speed.mp4`已完成：284.24s、50fps、14212帧，完整控制轨迹及报告与v047严格一致；SHA256 `33f410f788dd2f9944b64fc2a6b1eba0391b5e10613a5bdc601ac205e750f937`。已同步本地并抽查16帧，覆盖NAV、CLIMB、姿态转换、台面NAV和终态，画面正常，抽样未见明显跌落；完整原速人工审阅仍待完成。原v040成片继续保留；成功录像不能代替同版失败证据或正式批量验收。

当前计划SHA256：v050 `17e71821b061eba95f1c592d1a34874002118006b0dd6711f15e82c009f00470`；v051 `423a294193c5236dee3ace56353ac3c1cf19230e3bf6fdb0e1d4865a9eaa863c`；录像 `d159ec99e47ced101d82941316585cc6f146cd9d5582c1598505dbd8207b56a5`。


### 出口站位补步诊断（2026-10-16）

v050的3s渐入对照未解决问题：311.72s仍触发原足位域，0缺失/无效；含初始化最大子步力矩比0.9029478、腾空1/少于三足38/恰好三足5828控制步，竖直速度峰0.371053m/s、单脚/合力峰144.683/286.460N。此结果不支持继续仅延长渐入时间；原1s版本的两条成功路径继续保留。

保存的3702独立CLIMB终态显示：按同回合NAV停车后脚偏移推导机身x≈1.12925m时，两前脚相对原NAV站位各短约98.42/99.04mm。该几何差异是下一项待检验因素，不能仅凭静态差值认定全部失败根因。

v052恢复已取得两条成功的1s渐入，在独立CLIMB完成事件之后增加独立`platform_front_stance_prepare`阶段。若上述前脚差距超过40mm，调用原`PlatformFrontExtension`和`StageClimbAction`，两前脚逐只补步，每步不超过原80mm上限；本例选80mm，预期落点x≈1.24086/1.25096m，仍在原台面域。原完整摆动规划、支撑转移、实际落脚/重新承重、关节参考平滑均保留；完成后另等四脚≥8N及姿态速度条件连续1s，再进入原NAV机身/臂准备。重新安排的是控制器的补步阶段，不写物理姿态、不重置实际动作历史或执行器状态。

原CLIMB完成记录保留，新增补步不能重复计为CLIMB成功。该阶段暂不重复已经完成的CLIMB最后重心前移，补步停稳后恢复原配置。全过程原碰撞、软限位、98%子步力矩和台面边界门禁保持；新增`nav-front-prepare.jsonl`记录逐脚状态，终态审计单列两次真实重载及准备完成。420s整段/120s出口是新增站位诊断预算，**不是允许的最终耗时，也不是12s/24s验收**。待物理结果明确后再决定下一版，不扩大为正式批量。

v052计划SHA256 `0022a118ba360fce69f74ff9e539928b6b0bf434174ce1ccea6f50c408941d13`；静态输入计算见`front-template-preview.json`，不代替物理通过。


### 补步已通过，继续定位低速推进（2026-10-16）

v052补步的两次真实落脚分别在300.68/311.38s完成，选中前脚竖直力34.808/39.222N、重载比例1、已承重约0.22s；两脚完成后真实停稳门禁通过，新增逐脚审计无错误。随后NAV在完整120s出口诊断内未再触发足位域，姿态与安全终止条件保持，但整链仍在409.98s超时：NAV只前进49.884mm，目标误差70.603mm。含初始化最大子步力矩比0.9029478、腾空1/少于三足7/恰好三足6307控制步、竖直速度峰0.371053m/s、单脚/合力峰144.683/286.460N。0缺失/0无效，不计完整成功。

停滞补偿在337.20s已触发，但前进请求随后长期保持0.08m/s上限，机身仍反复前后摆动。v053仅在该既有停滞条件触发后，将前进请求的上限/最低请求值提高至0.12m/s，仍先受原停车距离平方根限幅，且保持0.1m/s²请求变化率；未停滞时维持0.08m/s。原25mm归零、35mm目标、12N制动捕获、1s承重停稳、足位、软限位、碰撞及实测子步力矩门禁不变。**这是调整导航请求幅度，并非物理安全门槛放宽；是否有效仍待验证。** 2002点标量请求检查确认普通路径不变、近点归零及距离限幅有效，不代替动态验证。诊断窗口仍为420s整段/120s出口，不能作为最终效率。

当前计划SHA256：v053 `19193d5499fc337798d2e3c31365aa4b47d332d28d54a323d3af88e1fca2a068`；v054 `d832befdbe9d3ba0da16ad93524b4ccfaa7e00641cb56cd8f9c431b9679068c4`。完成后按同一版本回归，既有v047/v048的2/3结果单独保存。


### 到点请求归零诊断（2026-10-16）

v053在409.98s仍未完整成功，但已推进至原位置域：NAV位移91.795mm，终态误差29.779mm，位置、姿态、台面足位及安全条件为真。完整轨迹最小误差17.283mm，1969个NAV样本位于35mm范围，**实际速度请求全归零样本仍为0**。首次进入25mm范围在346.52s；来回跨越该范围导致目标速度反复切换，而原0.1m/s²请求变化率尚未降完便重新加速。逐项重建制动预检发现多帧只有“请求归零”这一项不满足；其他帧的足力/臂速等条件也各自保留，不能忽略。证据`transition-nav-climb-v053/seed3702/stop-entry-diagnostic.json`。

v055在原25mm范围内只锁存“请求减速到零”的意图，三轴目标请求保持为零并经过原变化率限制；不会直接切换控制器或宣布停稳。至少保持1s后，若偏离超过50mm，或请求已归零且机身平缓但仍在原35mm目标域外，则重新接近。真正开始承重制动仍须原位置/姿态、四脚≥12N、速度/关节速度/力矩可行及请求归零等条件；最终仍需原35mm位置域内真实承重停稳1s。普通接近、补步、请求幅度和其他门禁不变。

24/26mm交替误差的数学检查中，锁存后原0.08m/s请求按原变化率在0.78s降至零；静止于目标域外和大幅漂移时均能重新接近。仅验证逻辑与请求包络，不能推断物理已成功。v055/v056仍为420s整段/120s出口诊断，原始失败记录保留。

当前计划SHA256：v055 `fcd8b00ef72cd3050e684317ff4dee60363969e4ed17fdf50157ca0628bf23e5`；v056 `8fb1eb5e257142804920f47f82c13d0a33dfaf6ca5eb3d4efbea680a195ceaf3`。


### 3702完整成功及同版回归（2026-10-16）

**v055/3702已完整成功，348.98s，0失败/缺失/无效证据。** 独立CLIMB在289.98s完成，额外NAV前脚准备的两次真实重载保持300.68/311.38s；出口共59s。346.52s在目标误差24.993mm时保持减速请求，347.04s实际请求归零，347.66s满足全部原制动预检（位置误差34.708mm、力分配可行、预测腿力矩比0.42243、软限位合格）并开始承重制动，最后在原35mm位置域内真实停稳1s。最终NAV位移96.323mm、目标误差29.579mm。证据`transition-nav-climb-v055/terminal-audit.json`及`seed3702/arrival-stop-success-summary.json`；这次没有把仅位置达标当作成功。

含初始化最大子步力矩比0.9029478、腾空1/少于三足7/恰好三足6400控制步、竖直速度峰0.371053m/s、单脚/合力峰144.683/286.460N；实际三帧历史与无中途reset证据有效。NAV仍是明确的受保护执行，原生18轴直通样本0。约5.8分钟不能作为最终效率；420s窗口仍只作诊断。

v056同控制器回归已结束：3701完整成功310.96s，3703出口超时372.04s；与v055共同为2成功/1失败。v057前置条件未满足，5个已用开发起点3704～3708均未启动物理。终态已生成`transition-nav-climb-v057/same-controller-group-audit.json`，核对三份计划的物理控制文件完全相同、8个唯一已用起点和完整/失败/缺失/未运行数量。

`transition-nav-climb-video-v055/seed3702/nav-climb-nav-v055-original-speed.mp4`已核验并同步：348.98s、50fps、17449帧，完整控制轨迹及报告与v055严格一致；SHA256 `27937d33b42f2b4e62b8c8a3a6d00616eccf1fb0e3a9fc13ed4c1c25e59a7848`。抽查16帧覆盖NAV、CLIMB、额外前脚准备、姿态转换及终态，画面正常，抽样未见明显跌落；全片原速人工审阅仍待完成。旧v047成片保留，不能替代新版结果。候选尚未并入交付代码。

扩展计划SHA256 `7f8aed8dd009c66e4bdec1eb0d78082e5d75e45886edb0c36121c7c6381be536`；新版录像计划SHA256 `70a5419fa9c81edd89ce16a9b438d49b651f8c3b12f8728c3b163ba00035711c`。


### 新版同控制器仍为2/3，持续停滞的请求跟踪诊断

v056/3703的额外前脚补步与重载均通过（262.80/273.50s，重载比例1、已承重约0.22s），NAV阶段位置以外的姿态、足位域与安全门禁保持，但前进仅22.454mm、终态误差102.575mm，372.04s出口超时。含初始化最大子步力矩比0.8943883，腾空1/少于三足6/恰好三足5371控制步。完整同版汇总为2成功/1失败/0缺失/0无效/5未运行，见`transition-nav-climb-v057/same-controller-group-audit.json`。

实测0.12m/s请求下，3703长期在目标前往复摆动，净前进不足。v058仅在已有停滞补偿生效后，连续10s没有新增超过5mm的前进进展、且目标仍在前方50mm外时，追加有界速度跟踪补偿：根据实测前向速度与最多0.08m/s的期望实速之差缓慢积分；偏置≤0.08m/s、增长≤0.01m/s²、总NAV请求≤0.20m/s，并保留原0.1m/s²请求变化率。该补偿作用于NAV输入命令；实测速度已达到原距离速度上限时不叠加，靠近25mm时逐渐衰减，进入35mm内或减速锁存后减小偏置。原25mm减速锁存、35mm实际位置域、12N制动捕获、1s真实停稳及碰撞/足位/执行器门禁均保持。

保存轨迹的纯逻辑回放：3703在311.78s满足触发条件，3701/3702两条成功轨迹均不触发；偏置上限、增长率、停止时衰减和重复时间戳不重复积分已检查。**复用旧实测状态的回放不能证明新闭环成功**。v058从原起点执行，只有有效完整成功后，v059才以同控制器重新验证3701/3702。420s/120s仍只作诊断，正式鲁棒性、效率及原速人工审阅未完成。

当前计划SHA256：v058 `77c3c031aa00ab91748a73d4330f22b6e2c720bbbe5b9001f46bcfbc57f55227`；v059 `ab49b14fb807a5f48846c2189eb354633258d84eccf4ef115cde2d962908633d`。数学输入检查见`transition-nav-climb-v058/tracking-compensation-check.json`。


### 跟踪补偿后的减速时机诊断

v058已明显推进，但仍是完整失败：NAV位移152.174mm、终态误差34.851mm，372.04s出口超时。实际轨迹最小误差12.720mm，共1102帧满足35mm位置条件；实际请求归零有15帧（最长0.30s），却全部发生在位置域之外。317.68s才在23.136mm误差处锁存减速，319.04s因误差超过50mm重新接近；请求降至零时机器人已经向前越过目标附近。故不能只增加推进幅度，也不能把最终位置合格当作停稳成功。原门禁与终态记录保留，v059两例未运行。

v060仅在速度跟踪补偿已启用且NAV实际位移≥60mm时，依据朝向目标的实测速度和当前前进请求降至零所需时间，增加减速意图的提前量：`max(v²/(2×0.1), 0.5×v×请求减速时间)`；触发距离最多80mm，保持时间至少覆盖请求减速时间再加0.3s，限制在1～2.3s。这里只提前请求归零，真正承重制动仍需原35mm位置、四脚≥12N、速度/力矩/软限位等全部条件；完整成功仍需真实停稳1s。普通路径保持原25mm逻辑，原0.1m/s²请求变化率、其他控制及安全门禁不变。

2000步逻辑检查确认默认路径与上一版一致。保存的v058实测输入上，提前减速意图从317.68s前移至317.38s，当时目标误差59.925mm；该回放复用了旧状态，不能证明实际命令或物理停止结果已改善。v060仍从原起点完整执行，v061只在其完整成功且审计有效后回归3701/3702。420s/120s继续只作诊断。

当前计划SHA256：v060 `d88bb090c309bcaf9e60a3417c7b783406d503bd14d9c3d4bbf1aa568f20cc03`；v061 `53b9f271b0599aca40ee5fd71dab783726c258d4910cfc5fd56079c26beb1aaf`。检查见`transition-nav-climb-v060/anticipated-stop-check.json`。


### 承重制动交接顺序诊断

v060提前减速意图的完整回归仍在372.04s超时，NAV位移155.371mm、终态误差36.910mm，没有实际承重制动或完整停稳；0缺失/无效。v061两例未运行。已有诊断显示在目标附近存在实际接触和运动条件合格、但虚拟NAV输入请求尚未归零的时刻；等请求按原变化率降完后，机器人可能已离开原位置域。

v062明确调整的是**制动交接顺序**：只有到点减速意图已经生效，才允许在NAV输入请求仍渐降时尝试承重制动；仍必须满足原35mm实际位置、姿态/足位安全、四足各≥12N、机身与关节速度、力分配可行、预测腿力矩比<0.75及原软限位等全部实际条件。输入请求保持原变化率继续降至零，不清空命令或动作历史。`SupportedBrake`仍使用原有界参考；其他调用方默认仍要求请求先归零。

“请求归零”明确保留为最终完成门禁，并须与原实际位置、承重和停稳条件共同连续满足1s。因此接入制动不等于成功，不能将未停止、未到点或请求未归零的状态放行。静态语法比较确认实际制动预检条件保持，仅请求归零的要求按上述顺序调整；实时力分配与动态结果仍待完整物理验证。检查`transition-nav-climb-v062/brake-handoff-contract-check.json`；v064仅在有效完整成功后验证两条已有成功路径。原420s/120s仍为诊断。

当前计划SHA256：v062 `61e37672c69e281748e4807c5f5055319dff2c09d097a92cb83263b42b0a968f`；v063 `6c46ebfaa519fc1775d6be0546150de08e6fd6c9e42e6b12643cded7d498233b`。

替代调度v064计划SHA256 `892d790a973b6e22fac1d24fde9741ea82ff05a9195eab23ffb163a89b255b9a`；只修复调度状态读取竞争，不改变物理控制器，v063两例未运行审计保留。


### 任务成功与参考连续性必须分开核验

v062/3703已在320.00s完整成功：318.02s在实际误差18.503mm、原运动/接触条件通过且力分配可行时，接入承重制动；当时前进请求仍为0.070672m/s，预测腿力矩比0.43629。此后请求按原变化率归零，最终位置误差25.007mm、NAV位移142.595mm，原物理停稳条件与请求归零共同连续满足1s，完整审计有效。v064同版3701已报告309.50s完整成功，3702仍运行；尚不提前宣称3/3。

执行参考复核发现另一项未满足的平滑性问题：切入`SupportedBrake`时，臂参考位置沿用最后下发目标，但其初速度来自实测关节速度，未沿用最后下发参考的速度。v062虽通过任务与实际力矩门禁，跨该边界的臂参考加速度峰仍为11.885rad/s²（速度峰0.26232rad/s）。该任务成功记录保留，**不能因此宣称参考已满足全程1rad/s²平滑要求或可以交付稳定切换**。证据`transition-nav-climb-v062/seed3703/brake-handoff-success-summary.json`。

v066仅在台面NAV到承重制动这一边界，将臂参考初速度改为最后实际下发的`ArmReferenceGuard.velocity`，位置保持最后实际目标；腿部初始化、原速度0.45rad/s及加速度1rad/s²限制、物理状态、策略/请求/历史和全部安全/完成门禁不变。仅在原0.45边界的浮点误差范围内做数值归一化，非有限或超范围仍拒绝。保存的真实捕获状态加1000步浮点输出检查中，跨首步的参考速度峰0.450003rad/s、加速度峰1.000464rad/s²；这仍是数学检查，物理回归尚待执行。

为避免把已有连续性问题扩大成候选验收，v065五起点扩展在物理启动前结束，5例未运行；当前v064回归和v062录像正常完成。v066等待当前回归结束后使用同一GPU，另对实际完整日志加入`brake_reference_smoothness`审计；v067必须同时满足完整任务成功和跨边界臂参考速度/加速度检查后才运行两条已有成功路径。任务成功、参考平滑、鲁棒性、效率及正式验收分别记录。

新版`transition-nav-climb-video-v062/seed3703/nav-climb-nav-v062-original-speed.mp4`正在另一GPU录制，要求完整控制轨迹与报告一致后接收；未生成有效成片前继续使用已核验v055录像，不将其当作新版本证据。

当前计划SHA256：v066 `50a191df893574cafa04cd0f7a8aa48c62e135df581981c49a71992c812d9eec`；v067 `3f22a8fd47b4a83590b5adf3a43dede0ae1ce9339f67283a4a44ee3e34c83776`；v062录像 `7ac5d17624c369c653188158de78906cdde9535dc0cbfc5583eff3dd61fcbe9f`。

下一步：收齐v064与v062录像，完成v066及条件v067的跨交接参考连续性回归，验证补偿实际效果及两条成功路径保留，再决定扩展开发筛查，核对额外两脚真实重载、请求变化率、接触/力矩及完整NAV出口，按固定控制器统计完整链和独立CLIMB；若出口失败，基于实际足力/跟踪/力矩证据定位，保留v040成功路径。鲁棒性确认后再缩短冗余准备/等待及规划耗时并回归；随后冻结候选、开展两组未用32起点验收和来源匹配的MuJoCo筛查。候选暂未并入交付代码，完整大日志保留原件，本地同步小型证据与录像。

### 2026-10-16：v069地面准备角反馈对照未通过

原v068/3704在37.00s力矩终止；v069在真实地面补步后的四足准备中于35.38s触发既有角反馈平滑衰减，但37.58s仍力矩终止，v070三个条件回归起点未运行。候选与输入触发证据保留在独立产物目录，当前接续见CLIMB页。

冻结控制器原本已在首次前脚上台时逐渐衰减外层角速度反馈。v069将这个既有机制提前用于特定地面准备：必须先由原步态时钟确认至少一次真实地面补步已落脚/重载，随后在四脚仍着地、下一前脚未起摆、参考已运行≥0.2s、四足各≥8N且机身角速度>0.2rad/s时，以0.2s五次平滑衰减启用同样的外层角反馈抑制。PD、位置反馈增益、关节参考限制、步态选择、支撑/摆脚规划、实际落脚与重载门禁均保持；该处理不是修改机械臂力矩限制。

保存轨迹的条件回放在3704的35.38s触发，在3701～3703三条成功路径中均不触发；仅验证触发范围，不能代替新物理成功。v069从原起点执行完整回合，v070只有在任务成功及审计通过后才验证三个已有成功起点，并使用两张GPU缩短回归等待。大控制日志保持原件，本地同步小型审计与诊断。

v069计划SHA256 `f2a2b702718fa6407ceeae37ddda698f5aeca4d41cdd44290a50ded731ee87ae`。

v070计划SHA256 `7b876bc2a4ffe05c86c97add5cf2eef3fdf5706e4bc87894b9f5d68fc3237e3b`。

### 2026-10-16：v071一致减速对照未通过

3704在36.96s仍触发原力矩门禁；0终态缺失/无效，v072三个条件回归起点未运行。下列保存原设计和计划，实际未通过，当前工作见CLIMB交接。

v071回到v066基线，仅在原时钟确认一次地面补步完成后、四脚仍在地面且下一前脚尚未起摆时，将机身位姿插值、负载补偿插值和水平速度前馈的时间一致地从1.5s改为3s。卸载准备不早于该3s转移，原1.5s卸载渐变及全部实际释放/落脚/重载条件保持；其他阶段直接调用原方法，目标几何、规划路径、PD、位置增益、参考限制和力矩门禁不变。不叠加失败候选的角反馈改动，也不通过只延长等待掩盖动态不一致。

派生的两段方法经语法树归一化对照，除声明的时间量和等价导入路径外与冻结源码一致；该检查不代替物理验证。v071从原起点执行，只有完整成功、无缺失/无效证据且制动参考平滑审计通过后，v072才使用两张GPU回归三个已有成功起点。420s整段仍为诊断，不是效率验收。证据`transition-nav-climb-v071/transfer-timing-static-check.json`。

v071计划SHA256 `d050e02e8b49bf69e802551cd696578af789e7221cb2f46cec0c21abe8c33a5c`。

v072计划SHA256 `a8e8d4b00ea405653eaeadd991d02b757a418c75cf5e77b30a45c1833c508d50`。

### 2026-10-16：v073带载余量对照未通过

3704在36.76s仍触发原力矩门禁，0缺失/无效；v074三个条件回归起点未运行。下列保留设计与计划，不能将静态可行当物理成功。

v073仅对原本可行、余量<0.08rad的前脚地面步尝试上述备选，只有完整可行且余量改善>0.02rad才采用；其他规划或没有更好可行解时保留原结果。足端落点、原完整路径检查、PD、参考平滑、实际释放/落脚/重载、碰撞和力矩终止保持。候选从原起点运行；若完整成功并审计有效，v074将以双GPU重新验证3701～3703，不能只凭静态检查宣称保留成功路径。数值证据`climb-source-adapter-v001/ground-transfer-reserve-preview.json`。

v073计划SHA256 `127dbd79a7d6d774a0bcde4cbc580f9f101bc25f4667ca8593006db5f8e133dc`。

v074计划SHA256 `00e2ac2ae1b15716555c94ae91ae9ff6d16c518d76f80fcabba1cc178a232b3b`。

### 2026-10-16：v075/v076平移反馈隔离对照未通过

幅度0/25%分别在36.08/36.46s力矩终止，均0缺失/无效。选择器状态no_full_chain_candidate，未生成v077；以下保存原设计及规则，不代表通过。

进一步检查首脚重载到下一支撑转移的边界：原规划捕获会重置卸载修正和重载计数，臂目标未突跳，腿部参考位置保持连续，但随后腿参考速度快速往复变化。v075/v076均从v066出发，在已确认一次真实地面补步后的四足前脚准备中、实测角速度>0.2rad/s等原对照条件满足时，分别以0.2s五次平滑将**外层平移速度笛卡尔修正**衰减至0或25%。关节PD、外层位置/角速度修正、接触力分配中的速度反馈、规划、参考限幅、实际落脚重载和全部安全终止保持。这是隔离一个反馈分量的两个幅度对照，不是放宽执行器门禁。

派生方法经语法树对照确认只增加指定平移反馈修正，其他方法体与冻结源码一致；触发范围沿用已核对的三条成功路径不触发的范围。该静态检查不证明物理成功。两个完整原起点回合分别占用GPU0/1，结果各自记录。收齐终态审计后，只有完整成功、无缺失/无效且制动参考平滑通过的候选才能生成v077；如果两者都通过，按预先声明规则选保留25%反馈者，固定其全部物理文件后双GPU回归三个既有成功起点；都未通过则不启动回归。选择与来源哈希记录于`climb-source-adapter-v001/linear-feedback-selection.json`及未来v077的`selection.json`，仍全是已用开发起点，不是正式验收。

v075计划SHA256 `85e22e6bccf6f6f216fdbb66c56b468d6d6ba337c818484122fcbf2e74ae969a`。

v076计划SHA256 `aa510f1f56dcaaa43b8bff6c2d169bf9aa66b9502ea51729b0c1f212240a0667`。

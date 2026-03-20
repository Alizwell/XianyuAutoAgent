# 设计：统一LLM信息提取服务

## 问题背景

当前酒店价格查询Agent使用两种不同方式提取信息：
1. **文本信息**：使用正则表达式模式匹配提取酒店名称、日期、房型
2. **图片信息**：独立的 `ImageRecognitionService` 使用多模态LLM提取

正则表达式匹配存在以下问题：
- 准确率低，对用户输入格式要求严格
- 无法处理歧义（如 "22-23号" 缺少年月份）
- 不自然的语言表达无法识别

同时，两种提取方式分散在两个地方，架构不够简洁，不利于维护。

## 设计目标

创建一个统一的LLM信息提取服务：
1. 统一处理文本提取和图片提取
2. 利用LLM的理解能力识别歧义
3. 架构更简洁，便于维护和优化
4. 移除冗余代码
5. 增加错误处理和韧性

## 架构设计

### 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/services/llm_extraction_service.py` | 新增 | 统一LLM信息提取服务 |
| `src/services/image_recognition_service.py` | 删除 | 功能合并到新服务 |
| `src/agent/hotel_price_agent.py` | 修改 | 使用新服务，移除正则提取 |
| `src/tools/parse_image_tool.py` | 修改 | 保留但改用新服务（遵循现有tool架构） |

### 数据结构

```python
@dataclass
class ExtractedInfo:
    """LLM提取结果"""
    hotel_name: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    room_type: Optional[str] = None
    price: Optional[float] = None
    confidence: Dict[str, float] = None
    ambiguous_fields: List[str] = None
    raw_response: Optional[str] = None

    def __init__(self):
        self.confidence = {}
        self.ambiguous_fields = []
```

### 服务接口

```python
class LLMExtractionService:
    """统一LLM信息提取服务 - 处理文本和图片提取"""

    def __init__(self):
        # 从环境变量读取配置
        self.api_key = os.getenv("LLM_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.vision_model = os.getenv("VISION_MODEL", "gpt-4o")
        self.text_model = os.getenv("TEXT_MODEL", "gpt-3.5-turbo")
        self.timeout = int(os.getenv("EXTRACTION_TIMEOUT", "60"))
        self.max_retries = int(os.getenv("EXTRACTION_MAX_RETRIES", "3"))
        self.confidence_threshold = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.5"))

    async def extract(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> ExtractedInfo:
        """
        统一提取接口 - 处理文本+图片组合情况
        优先级：如果提供图片优先使用图片提取，否则使用文本提取
        """
        ...

    async def extract_from_text(self, text: str) -> ExtractedInfo:
        """从纯文本提取酒店预订信息"""
        ...

    async def extract_from_image(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> ExtractedInfo:
        """从图片（多模态）提取酒店预订信息"""
        ...
```

### 工具层适配

保留 `ParseImageTool`，但修改它使用新服务，遵循现有项目的工具架构：

```python
class ParseImageTool(BaseTool):
    """解析酒店预订图片工具"""

    name = "parse_hotel_image"
    description = "解析酒店预订界面图片，提取酒店名称、日期、房型信息"

    def __init__(self, extraction_service: Optional[LLMExtractionService] = None):
        self.extraction_service = extraction_service or LLMExtractionService()

    async def execute(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            result = await self.extraction_service.extract_from_image(
                image_url=image_url,
                image_base64=image_base64
            )
            return ToolResult.success_result(data=result.__dict__)
        except Exception as e:
            return ToolResult.error_result(f"图片解析失败: {str(e)}")
```

## Prompt 设计

### 文本提取 Prompt

```
请从用户输入中提取酒店预订信息：

用户输入: "{text}"

提取以下字段：
1. 酒店名称 (hotel_name) - 完整提取用户提到的酒店名称
2. 入住日期 (check_in_date) - 请转换为 YYYY-MM-DD 格式
3. 离店日期 (check_out_date) - 请转换为 YYYY-MM-DD 格式
4. 房型 (room_type) - 用户提到的房型，如：高级大床房、双床房等
5. 价格 (price) - 价格数字，单位元

规则：
- 如果某字段无法确定，请设置为 null
- 价格请提取为数字类型（不是字符串）
- 如果日期只有日月缺少年份月份，请设置该字段为 null，加入 ambiguous_fields
- 如果只给出一个日期范围如 "22-23号"，两个日期都缺年月，都加入 ambiguous_fields
- confidence 字段给出每个字段的置信度（0.0-1.0）
- 置信度 < 0.5 的字段请设为 null

请严格以JSON格式输出：

{
  "hotel_name": "酒店名称或null",
  "check_in_date": "YYYY-MM-DD或null",
  "check_out_date": "YYYY-MM-DD或null",
  "room_type": "房型名称或null",
  "price": 299 或 null,
  "confidence": {
    "hotel_name": 0.95,
    "check_in_date": 0.80,
    "check_out_date": 0.80,
    "room_type": 0.90,
    "price": 0.85
  },
  "ambiguous_fields": ["check_in_date", "check_out_date"]
}

如果没有歧义，ambiguous_fields 为空数组 []。
```

### 图片提取 Prompt

同样使用相同输出结构，增加图片说明：

```
请分析这张酒店预订相关的图片，提取以下信息：

1. 酒店名称 (hotel_name)
2. 入住日期 (check_in_date，格式：YYYY-MM-DD)
3. 离店日期 (check_out_date，格式：YYYY-MM-DD)
4. 房型 (room_type，如：高级大床房、双床房等)
5. 价格 (price，数字，单位元)

请以JSON格式返回结果：
{
  "hotel_name": "酒店名称",
  "check_in_date": "2024-01-01",
  "check_out_date": "2024-01-02",
  "room_type": "房型名称",
  "price": 299,
  "confidence": {
    "hotel_name": 0.95,
    "check_in_date": 0.98,
    "check_out_date": 0.98,
    "room_type": 0.90,
    "price": 0.95
  },
  "ambiguous_fields": []
}

如果某字段无法识别，请设置为null。confidence字段表示每个字段的识别置信度（0-1之间的小数）。如果日期不完整缺少年月，请放入ambiguous_fields。
```

## 错误处理与韧性

### 重试机制

使用指数退避重试LLM API调用：

```python
for attempt in range(self.max_retries):
    try:
        # LLM调用逻辑
        return result
    except Exception as e:
        if attempt == self.max_retries - 1:
            # 最后一次尝试失败，返回空结果
            logger.error(f"提取失败 after {self.max_retries} attempts: {str(e)}")
            return ExtractedInfo()
        # 指数退避等待
        await asyncio.sleep(1 + attempt * 2)
```

### JSON解析容错

1. 尝试直接解析JSON
2. 失败则从文本中提取JSON片段（找第一个{到最后一个}）
3. 仍然失败则返回空结果

### 输入验证

- 文本长度：限制最大token数（最大输入长度约4000字符）
- 图片：检查提供了url或base64，不接受空输入
- 验证必填配置（`LLM_API_KEY`必须存在）

## 处理流程

### 输入处理

```
用户消息 + 可选图片
    ↓
HotelPriceAgent.process_message
    ↓
service.extract(text=user_message, image_url=image_url, image_base64=image_base64)
    ↓
   优先级：图片 > 文本
    ↓
将提取结果填充到 QueryState
    ↓
检查 ambiguous_fields + 低置信度/null字段
    ↓
逐个向用户询问确认缺失/歧义信息
    ↓
信息收集完整后执行搜索查询
```

### 组合输入处理策略

当用户同时提供**文本**和**图片**时，优先使用图片提取：
- 图片通常包含更完整准确的预订信息（如截图）
- 如果图片提取失败，回退到文本提取

### 歧义处理

LLM返回 `ambiguous_fields` 后，Agent按顺序逐个询问用户确认：
```python
for field in extracted.ambiguous_fields:
    if field == 'check_in_date' and not state.check_in_date:
        return "请问入住日期是哪一天？请提供 YYYY-MM-DD 格式。"
    ...
```

### 日期标准化

日期标准化逻辑（`_normalize_date`）保留在Agent中，服务输出YYYY-MM-DD，Agent处理异常情况。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API密钥 | 必填 |
| `LLM_API_BASE` | API基础地址 | `https://api.openai.com/v1` |
| `VISION_MODEL` | 多模态模型名称 | `gpt-4o` |
| `TEXT_MODEL` | 文本模型名称 | `gpt-3.5-turbo` |
| `EXTRACTION_TIMEOUT` | 请求超时（秒） | `60` |
| `EXTRACTION_MAX_RETRIES` | 最大重试次数 | `3` |
| `EXTRACTION_CONFIDENCE_THRESHOLD` | 置信度阈值 | `0.5` |

## 优势对比

| 方面 | 原有设计 | 新设计 |
|------|----------|--------|
| 准确率 | 低（正则限制格式） | 高（LLM自然语言理解） |
| 歧义处理 | 不支持 | 原生支持 |
| 代码复用 | 低（两套逻辑） | 高（一套逻辑处理两种输入） |
| 可维护性 | 分散 | 集中 |
| 可扩展性 | 差 | 好（易于prompt优化） |
| 韧性 | 无重试，无容错 | 重试+JSON解析容错 |

## 风险考虑

1. **LLM调用成本**：文本提取用较小模型如gpt-3.5-turbo足够，成本可控
2. **LLM调用失败**：重试机制，失败返回空结果，由Agent提示用户重新提供信息
3. **JSON解析错误**：做多层容错处理，尝试从文本提取JSON，失败返回空结果
4. **安全**：API密钥通过环境变量传入，不硬编码，符合最佳实践
5. **输入限制**：文本长度限制避免超出LLM token限制

## 评审更新

此设计根据代码评审反馈更新：
- ✅ 添加 `price` 字段到 `ExtractedInfo`
- ✅ 添加统一 `extract()` 接口处理文本+图片组合
- ✅ 添加重试机制（指数退避）
- ✅ 添加输入验证
- ✅ 保留 `ParseImageTool` 适配新服务
- ✅ 更新环境变量配置
- ✅ prompt包含价格提取

## 下一步

下一步：生成详细实施计划。

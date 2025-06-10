以下是你 `/search` 接口的 Markdown 接口文档示例：

---

## 🔍 `/search` 接口文档

### 基本信息

* **接口路径**：`/search`
* **请求方法**：`POST`
* **请求格式**：`application/json`
* **接口功能**：基于指定的搜索引擎执行关键词查询，并返回结构化的内容结果。

---

### 请求参数

| 参数名    | 类型     | 是否必填 | 描述                       |
| ------ | ------ | ---- | ------------------------ |
| query  | string | 是    | 需要查询的关键词                 |
| engine | string | 是    | 指定搜索引擎，如 `sougou_weixin` |

#### 请求示例

```json
{
  "query": "广州大学 产研链",
  "engine": "sougou_weixin"
}
```

---

### 返回字段

| 字段名     | 类型             | 描述              |
| ------- | -------------- | --------------- |
| success | boolean        | 接口调用是否成功        |
| data    | array\[object] | 搜索结果数组          |
| error   | string/null    | 如果有错误信息，则返回错误描述 |

#### data 数组中的对象字段

| 字段名           | 类型     | 描述      |
| ------------- | ------ | ------- |
| title         | string | 文章标题    |
| organization  | string | 发布机构    |
| publish\_time | string | 发布时间    |
| location      | string | 所属地区    |
| content       | string | 正文内容    |
| md5           | string | 内容唯一标识符 |

---

### 返回示例

```json
{
  "success": true,
  "data": [
    {
      "title": "校内有高铁站、岭南诗意风格……广州高校，上新了！",
      "organization": "中国广州发布",
      "publish_time": "2023-09-14 10:59",
      "location": "广东",
      "content": "校内建有“高铁站”...\n（此处为内容缩略）",
      "md5": "643f8fc21e3cbc313d702b21a53dedd3"
    }
  ],
  "error": null
}
```

---

### 错误响应示例

```json
{
  "success": false,
  "data": [],
  "error": "Invalid engine parameter"
}
```

---

### 注意事项

* `engine` 参数值需为系统支持的引擎名称，未指定或错误将返回错误信息。
* 接口适用于获取公开文章、公众号数据等资讯内容，支持中文关键词。
* 返回结果可能包含大量文本内容，请合理处理存储或展示。

---

需要我再帮你生成 HTML 或 Swagger/OpenAPI 版本的文档吗？

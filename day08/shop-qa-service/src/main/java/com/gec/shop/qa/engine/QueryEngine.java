package com.gec.shop.qa.engine;

import org.neo4j.driver.*;
import java.util.*;
import java.util.regex.*;

/**
 * 问答引擎 — 意图识别 → 实体链接 → 模板匹配 → Cypher 执行 → 结果格式化。
 * 对应 RAG4Pro src/query_engine.py
 */
public class QueryEngine {

    private final Driver driver;
    private final IntentRecognizer intentRecognizer;
    private final EntityLinker entityLinker;
    private final List<Map<String, String>> qaRules = new ArrayList<>();

    public QueryEngine(Driver driver) {
        this.driver = driver;
        this.intentRecognizer = new IntentRecognizer();
        this.entityLinker = new EntityLinker();
    }

    public void buildIndex(Collection<String> brands, Collection<String> categories) {
        entityLinker.buildIndex(brands, categories);
    }

    public void loadQARules(List<Map<String, String>> rules) {
        qaRules.clear();
        qaRules.addAll(rules);
    }

    public Map<String, Object> answer(String query) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("question", query);

        // 1) QA规则库精确匹配
        for (Map<String, String> r : qaRules) {
            String kw = r.get("keyword");
            if (kw != null && query.contains(kw)) {
                result.put("answer", r.get("answer"));
                result.put("intent", r.getOrDefault("intent", "qa"));
                result.put("method", "rule");
                return result;
            }
        }

        // 2) 意图识别 + 实体链接
        String intent = intentRecognizer.recognize(query);
        List<Trie.EntityMatch> entities = entityLinker.link(query);
        String attrName = intentRecognizer.extractAttrName(query);
        String cypherAttr = entityLinker.getCypherAttr(attrName);

        result.put("intent", intent);
        if (!entities.isEmpty()) {
            result.put("entities", entities.stream()
                .map(e -> Map.of("name", e.name, "type", e.type)).toList());
        }

        // 3) 按意图执行图谱查询
        List<Map<String, Object>> graphResult = null;
        try {
            graphResult = executeByIntent(intent, entities, cypherAttr, query);
        } catch (Exception e) {
            result.put("answer", "查询执行出错: " + e.getMessage());
            result.put("method", "error");
            return result;
        }

        if (graphResult != null && !graphResult.isEmpty()) {
            result.put("data", graphResult);
            result.put("answer", formatGraphResult(graphResult, intent, attrName));
            result.put("method", "graph");
        } else {
            // 4) 兜底：模糊搜索商品
            Map<String, Object> product = fuzzySearchProduct(query);
            if (product != null) {
                result.put("answer", product.get("name") + " 售价 " + product.get("price"));
                result.put("intent", "product");
                result.put("product", product);
                result.put("method", "fuzzy_product");
            } else {
                result.put("answer", "抱歉，我还没学会这个问题。您可以问价格、库存、退换货、物流等相关问题~");
                result.put("method", "fallback");
            }
        }
        return result;
    }

    private List<Map<String, Object>> executeByIntent(
            String intent, List<Trie.EntityMatch> entities, String cypherAttr, String query) {

        List<CypherTemplates.Template> templates = CypherTemplates.getTemplates(intent);
        if (templates.isEmpty()) return null;

        if (!entities.isEmpty()) {
            // Category 实体 → 查类目下商品
            if ("Category".equals(entities.get(0).type)) {
                String catName = entities.get(0).name;
                String cypher = "MATCH (c:Category {name: '"+catName+"'})<-[:BELONGS_TO]-(p:Product) RETURN COLLECT(p.name) AS result, COLLECT(p.price) AS prices";
                List<Map<String, Object>> data = executeCypher(cypher);
                if (data != null && !data.isEmpty()) return data;
            }
            for (CypherTemplates.Template tmpl : templates) {
                Map<String, Object> params = new LinkedHashMap<>();
                params.put("entity", entities.get(0).name);
                if (entities.size() >= 2 && intent.equals(IntentRecognizer.INTENT_COMPARE)) {
                    params.put("entity1", entities.get(0).name);
                    params.put("entity2", entities.get(1).name);
                }
                String cypher = tmpl.template;
                if (cypherAttr != null && cypher.contains("{attr}")) {
                    cypher = CypherTemplates.formatAttr(cypher, cypherAttr);
                }
                cypher = CypherTemplates.fillTemplate(cypher, params);
                List<Map<String, Object>> data = executeCypher(cypher);
                if (data != null && !data.isEmpty()) return data;
            }
        }

        if (intent.equals(IntentRecognizer.INTENT_FILTER)) {
            double[] range = extractPriceRange(query);
            if (range != null) {
                Map<String, Object> params = Map.of("min_price", range[0], "max_price", range[1]);
                String cypher = CypherTemplates.fillTemplate(
                    "MATCH (p:Product) WHERE p.price >= {min_price} AND p.price <= {max_price} RETURN COLLECT(p.name) AS result, COLLECT(p.price) AS prices",
                    params);
                return executeCypher(cypher);
            }
        }
        return null;
    }

    private List<Map<String, Object>> executeCypher(String cypher) {
        try (Session session = driver.session()) {
            return session.run(cypher).list(record -> {
                Map<String, Object> row = new LinkedHashMap<>();
                for (String key : record.keys()) {
                    row.put(key, record.get(key).asObject());
                }
                return row;
            });
        } catch (Exception e) {
            return null;
        }
    }

    private Map<String, Object> fuzzySearchProduct(String keyword) {
        try (Session session = driver.session()) {
            // Try exact CONTAINS first
            var results = session.run(
                "MATCH (p:Product) WHERE p.name CONTAINS $kw RETURN p LIMIT 3",
                Map.of("kw", keyword)
            ).list(r -> r.get("p").asMap());
            if (!results.isEmpty()) return results.get(0);
            // Try each 2-char+ segment as fallback
            for (int i = 0; i < keyword.length(); i++) {
                for (int j = i + 2; j <= Math.min(i + 5, keyword.length()); j++) {
                    String seg = keyword.substring(i, j);
                    results = session.run(
                        "MATCH (p:Product) WHERE p.name CONTAINS $kw RETURN p LIMIT 3",
                        Map.of("kw", seg)
                    ).list(r -> r.get("p").asMap());
                    if (!results.isEmpty()) return results.get(0);
                }
            }
            return null;
        } catch (Exception e) {
            return null;
        }
    }

    private String formatGraphResult(List<Map<String, Object>> data, String intent, String attrName) {
        if (data.isEmpty()) return null;
        Map<String, Object> row = data.get(0);
        if (row.containsKey("result")) {
            Object val = row.get("result");
            if (val instanceof List<?> list && !list.isEmpty()) {
                return String.join("、", list.stream().map(Object::toString).toList());
            }
            return val != null ? val.toString() : "未找到结果";
        }
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Object> e : row.entrySet()) {
            String key = e.getKey().replace("_", " ");
            Object val = e.getValue();
            if (val instanceof List<?> list && !list.isEmpty()) {
                sb.append(key).append(": ").append(String.join(", ", list.stream().map(Object::toString).toList())).append("; ");
            } else if (val != null) {
                sb.append(val).append(" ");
            }
        }
        return sb.length() > 0 ? sb.toString() : "未找到结果";
    }

    private double[] extractPriceRange(String query) {
        java.util.regex.Matcher m1 = Pattern.compile("(\\d+)\\s*元?\\s*以[内下]").matcher(query);
        if (m1.find()) return new double[]{0, Double.parseDouble(m1.group(1))};
        java.util.regex.Matcher m2 = Pattern.compile("[大于高超过](\\d+)").matcher(query);
        if (m2.find()) return new double[]{Double.parseDouble(m2.group(1)), Double.MAX_VALUE};
        java.util.regex.Matcher m3 = Pattern.compile("(\\d+)\\s*[-~至到]\\s*(\\d+)\\s*元?").matcher(query);
        if (m3.find()) return new double[]{Double.parseDouble(m3.group(1)), Double.parseDouble(m3.group(2))};
        return null;
    }
}

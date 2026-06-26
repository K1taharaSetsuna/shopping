package com.gec.shop.qa.engine;

import java.util.*;
import java.util.regex.*;

public class IntentRecognizer {

    public static final String INTENT_QUERY_ATTR     = "query_attr";
    public static final String INTENT_QUERY_RELATION = "query_relation";
    public static final String INTENT_COMPARE         = "compare";
    public static final String INTENT_FILTER          = "filter";

    private static final Map<String, List<Pattern>> RULES = new LinkedHashMap<>();
    static {
        RULES.put(INTENT_QUERY_ATTR, List.of(
            Pattern.compile("多少"), Pattern.compile("什么"), Pattern.compile("哪些"),
            Pattern.compile("多[大便高长重贵]"), Pattern.compile("尺寸"), Pattern.compile("颜色"),
            Pattern.compile("规格"), Pattern.compile("库存"), Pattern.compile("有货")
        ));
        RULES.put(INTENT_QUERY_RELATION, List.of(
            Pattern.compile("属于"), Pattern.compile("是什么品牌"), Pattern.compile("相关"),
            Pattern.compile("同类"), Pattern.compile("类似"),
            Pattern.compile("有哪些产品"), Pattern.compile("产品有哪些"),
            Pattern.compile("有哪些系列"), Pattern.compile("有什么"), Pattern.compile("有没有"),
            Pattern.compile("属于什么"), Pattern.compile("主营"), Pattern.compile("业务"), Pattern.compile("品牌")
        ));
        RULES.put(INTENT_COMPARE, List.of(
            Pattern.compile("和.*哪个"), Pattern.compile("对比"), Pattern.compile("比较"),
            Pattern.compile("区别"), Pattern.compile("哪个好"), Pattern.compile("更好"),
            Pattern.compile("差异"), Pattern.compile("vs", Pattern.CASE_INSENSITIVE)
        ));
        RULES.put(INTENT_FILTER, List.of(
            Pattern.compile("大于"), Pattern.compile("小于"), Pattern.compile("以上"),
            Pattern.compile("以下"), Pattern.compile("超过"), Pattern.compile("低于"),
            Pattern.compile("价格.*\\d"), Pattern.compile("\\d+.*元"), Pattern.compile("以内"),
            Pattern.compile("之间"), Pattern.compile("排序"), Pattern.compile("最[大便高长重贵便宜]")
        ));
    }

    public String recognize(String query) {
        Map<String, Integer> scores = new LinkedHashMap<>();
        for (String intent : RULES.keySet()) {
            int score = 0;
            for (Pattern p : RULES.get(intent)) {
                java.util.regex.Matcher m = p.matcher(query);
                if (m.find()) score += m.group().length();
            }
            scores.put(intent, score);
        }

        String best = scores.entrySet().stream()
            .max(Map.Entry.comparingByValue()).get().getKey();

        if (scores.get(best) == 0) {
            for (String kw : List.of("品牌", "属于", "主营", "业务", "产品")) {
                if (query.contains(kw)) return INTENT_QUERY_RELATION;
            }
            return INTENT_QUERY_ATTR;
        }
        return best;
    }

    public String extractAttrName(String query) {
        Map<String, List<String>> kw = Map.of(
            "主营业务", List.of("主营业务", "主营什么", "主营"),
            "品牌发源地", List.of("发源地", "哪个国家", "产地"),
            "创立年份", List.of("创立年份", "成立时间", "哪年"),
            "产品", List.of("产品", "哪些产品", "商品"),
            "类目", List.of("类目", "品类", "分类"),
            "尺寸", List.of("尺寸", "大小", "规格"),
            "颜色", List.of("颜色", "什么颜色"),
            "价格", List.of("价格", "多少钱", "价位"),
            "库存", List.of("库存", "有货吗", "缺货")
        );
        for (Map.Entry<String, List<String>> e : kw.entrySet()) {
            for (String k : e.getValue()) {
                if (query.contains(k)) return e.getKey();
            }
        }
        return null;
    }
}

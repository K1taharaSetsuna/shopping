package com.gec.shop.qa.service;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.neo4j.driver.*;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

/**
 * 知识图谱构建器 — 从 MySQL 读取商品数据，写入 Neo4j。
 * 对应 RAG4Pro src/graph_builder.py
 */
@Service
public class GraphBuilderService {

    private final Driver neo4jDriver;
    private final ProductMapper productMapper;

    private final Set<String> brandsSeen = new LinkedHashSet<>();
    private final Set<String> categoriesSeen = new LinkedHashSet<>();

    public GraphBuilderService(Driver neo4jDriver, ProductMapper productMapper) {
        this.neo4jDriver = neo4jDriver;
        this.productMapper = productMapper;
    }

    @PostConstruct
    public void init() {
        buildGraph();
    }

    public void buildGraph() {
        List<ProductRow> products;
        try {
            products = productMapper.findAll();
        } catch (Exception e) {
            System.out.println("[GraphBuilder] MySQL 查询失败: " + e.getMessage() + "，使用种子数据");
            buildWithSeedData();
            return;
        }
        if (products.isEmpty()) {
            System.out.println("[GraphBuilder] MySQL 无商品数据，使用种子数据");
            buildWithSeedData();
            return;
        }

        try (Session session = neo4jDriver.session()) {
            session.run("MATCH (n) DETACH DELETE n");
            System.out.println("[GraphBuilder] 已清空旧图数据");

            for (ProductRow p : products) {
                session.run(
                    "MERGE (p:Product {pid: $pid}) SET p.name=$name, p.price=$price, p.category=$cat, p.image=$img",
                    Map.of("pid", p.pid, "name", p.name, "price", p.price, "cat", p.category != null ? p.category : "", "img", p.image != null ? p.image : "")
                );
                if (p.category != null && !p.category.isEmpty()) {
                    session.run("MERGE (c:Category {name: $cat})", Map.of("cat", p.category));
                    session.run(
                        "MATCH (p:Product {pid: $pid}), (c:Category {name: $cat}) MERGE (p)-[:BELONGS_TO]->(c)",
                        Map.of("pid", p.pid, "cat", p.category)
                    );
                    categoriesSeen.add(p.category);
                }
                String brand = extractBrand(p.name);
                if (brand != null) {
                    session.run("MERGE (b:Brand {name: $brand})", Map.of("brand", brand));
                    session.run(
                        "MATCH (p:Product {pid: $pid}), (b:Brand {name: $brand}) MERGE (p)-[:BELONGS_TO_BRAND]->(b)",
                        Map.of("pid", p.pid, "brand", brand)
                    );
                    brandsSeen.add(brand);
                }
            }

            System.out.printf("[GraphBuilder] 图谱构建完成: %d 商品, %d 类目, %d 品牌%n",
                products.size(), categoriesSeen.size(), brandsSeen.size());
        }
    }

    private void buildWithSeedData() {
        try (Session session = neo4jDriver.session()) {
            session.run("MATCH (n) DETACH DELETE n");

            String[][] data = {
                {"1", "小米14 Ultra",     "6999", "数码",   "xiaomi-1.png",     "小米"},
                {"2", "华为 MatePad Pro", "4999", "数码",   "huawei-1.png",     "华为"},
                {"3", "Air Max 运动跑鞋", "899",  "运动鞋", "airmax-1.png",     "Nike"},
                {"4", "纯棉圆领T恤",      "129",  "T恤",    "tshirt-1.png",     "优衣库"},
                {"5", "坚果礼盒",         "88",   "食品",   "nuts-1.png",       "三只松鼠"},
                {"6", "Maz Maz 番茄薯片", "15.9", "食品",   "mazmaz番茄-1.png", "MazMaz"},
                {"7", "Mini Lina 饼干",   "12.9", "食品",   "minilina-1.png",   "MiniLina"},
                {"8", "Maz Maz 土豆条",   "13.9", "食品",   "mazmaz土豆条-1.png","MazMaz"},
                {"9", "北欧风台灯",       "159",  "家居",   "lamp-1.png",       "宜家"},
            };
            for (String[] d : data) {
                session.run(
                    "CREATE (p:Product {pid: $pid, name: $name, price: $price, category: $cat, image: $img}) " +
                    "MERGE (c:Category {name: $cat}) MERGE (p)-[:BELONGS_TO]->(c) " +
                    "MERGE (b:Brand {name: $brand}) MERGE (p)-[:BELONGS_TO_BRAND]->(b)",
                    Map.of("pid", Long.parseLong(d[0]), "name", d[1], "price", Double.parseDouble(d[2]),
                           "cat", d[3], "img", d[4], "brand", d[5])
                );
                categoriesSeen.add(d[3]);
                brandsSeen.add(d[5]);
            }
            System.out.println("[GraphBuilder] 种子数据: 9 商品, " + categoriesSeen.size() + " 类目, " + brandsSeen.size() + " 品牌");
        }
    }

    private String extractBrand(String name) {
        if (name == null) return null;
        Map<String, String> known = Map.of(
            "小米", "小米", "华为", "华为", "AirMax", "Nike", "Nike", "Nike",
            "优衣库", "优衣库", "三只松鼠", "三只松鼠", "MazMaz", "MazMaz",
            "MiniLina", "MiniLina", "宜家", "宜家"
        );
        for (Map.Entry<String, String> e : known.entrySet()) {
            if (name.contains(e.getKey())) return e.getValue();
        }
        return name.length() >= 2 ? name.substring(0, 2) : name;
    }

    public Set<String> getBrands() { return brandsSeen; }
    public Set<String> getCategories() { return categoriesSeen; }

    @Mapper
    public interface ProductMapper extends BaseMapper<ProductRow> {
        @Select("SELECT pid, name, price, category, image FROM product")
        List<ProductRow> findAll();
    }

    public static class ProductRow {
        public Long pid;
        public String name;
        public Double price;
        public String category;
        public String image;
    }
}

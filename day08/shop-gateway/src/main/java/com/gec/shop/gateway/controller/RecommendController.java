package com.gec.shop.gateway.controller;

import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * DIN 推荐接口 — 转发到 Flask 推理服务 (:5001)
 *
 * 前端调用: POST /recommend (无需传参，从 JWT Header 取 username)
 * 返回: JSON 字符串（推荐商品列表）
 */
@RestController
public class RecommendController {

    private static final String FLASK_URL = "http://localhost:5001/recommend";

    @PostMapping("/recommend")
    public String recommend(@RequestHeader("X-Username") String username,
                            @RequestHeader(value = "X-User-Id", required = false) String userId) {
        try {
            // Build JSON request body
            String jsonBody = String.format("{\"username\": \"%s\", \"top_k\": 10}", username);

            // Call Flask
            URL url = new URL(FLASK_URL);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(30000);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonBody.getBytes(StandardCharsets.UTF_8));
            }

            int status = conn.getResponseCode();
            BufferedReader reader;
            if (status >= 200 && status < 300) {
                reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8));
            } else {
                reader = new BufferedReader(new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8));
            }

            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();
            conn.disconnect();

            return response.toString();

        } catch (Exception e) {
            return String.format("{\"error\": \"Recommendation service unavailable: %s\"}", e.getMessage());
        }
    }

    @GetMapping("/recommend")
    public String recommendGet(@RequestHeader("X-Username") String username) {
        return recommend(username, null);
    }
}

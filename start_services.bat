@echo off
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot
set JAVA=%JAVA_HOME%\bin\java
set BASE=D:\YueQian\shopping-frontend\day08
set LOG=D:\YueQian\shopping-frontend\logs

if not exist %LOG% mkdir %LOG%

echo [1/6] Starting auth-service :8101 ...
start "auth" cmd /c "%JAVA% -jar %BASE%\shop-auth\target\shop-auth-1.0-SNAPSHOT.jar > %LOG%\auth.log 2>&1"
timeout /t 15 >nul

echo [2/6] Starting user-service :8111 ...
start "user" cmd /c "%JAVA% -jar %BASE%\shop-user\target\shop-user-1.0-SNAPSHOT.jar > %LOG%\user.log 2>&1"
timeout /t 10 >nul

echo [3/6] Starting product-service :8081 ...
start "product" cmd /c "%JAVA% -jar %BASE%\shop-product-server\target\shop-product-server-1.0-SNAPSHOT.jar > %LOG%\product.log 2>&1"
timeout /t 10 >nul

echo [4/6] Starting order-service :8091 ...
start "order" cmd /c "%JAVA% -jar %BASE%\shop-order-server\target\shop-order-server-1.0-SNAPSHOT.jar > %LOG%\order.log 2>&1"
timeout /t 10 >nul

echo [5/6] Starting payment-service :8121 ...
start "payment" cmd /c "%JAVA% -jar %BASE%\shop-payment\target\shop-payment-1.0-SNAPSHOT.jar > %LOG%\payment.log 2>&1"
timeout /t 10 >nul

echo [6/6] Starting gateway :9000 ...
start "gateway" cmd /c "%JAVA% -jar %BASE%\shop-gateway\target\shop-gateway-1.0-SNAPSHOT.jar > %LOG%\gateway.log 2>&1"

echo All services started! Waiting 30s for verification...
timeout /t 30 >nul

echo === Verification ===
curl -s -o nul -w " auth: %%{http_code}" http://localhost:8101/a/current 2>nul
echo.
curl -s -o nul -w " product: %%{http_code}" http://localhost:8081/products 2>nul
echo.
curl -s -o nul -w " order: %%{http_code}" http://localhost:8091/orders/save?uid=1^&pid=1 2>nul
echo.
curl -s -o nul -w " gateway: %%{http_code}" http://localhost:9000/a/login 2>nul
echo.

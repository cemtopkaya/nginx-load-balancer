# Least Connections (En Az Bağlantı) Stratejisi

Bu strateji, gelen yeni istekleri o an en az aktif bağlantıya sahip sunucuya yönlendirir. Bu yaklaşım, sunucular arasındaki yük dengesizliğini minimize etmeye yardımcı olur ve özellikle sunucuların farklı kapasitelere sahip olduğu veya bazı isteklerin diğerlerinden daha uzun sürdüğü durumlarda etkilidir.

**Least Connections stratejisinin çalışma prensibi:**
1. Yeni bir istek geldiğinde, Nginx o an en az aktif bağlantıya sahip sunucuyu seçer.
2. Eğer birden fazla sunucu aynı sayıda en az bağlantıya sahipse, Nginx bu sunucular arasında round-robin yöntemini kullanır.
3. Ağırlıklar (weights) kullanıldığında, Nginx bağlantı sayılarını ağırlıklarla orantılı olarak değerlendirir.


**Bu stratejinin avantajları:**
- Dinamik olarak değişen yükleri daha iyi yönetir.
- Sunucular arasındaki kapasite farklılıklarını dikkate alır.
- Uzun süren isteklerin tek bir sunucuya yığılmasını engeller.

**Dezavantajları:**
- Round Robin'e göre biraz daha fazla işlem gücü gerektirir.
- Oturum devamlılığı (session persistence) sağlamaz.


```nginx
# nginx.conf

user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;

    upstream backend {
        least_conn;  # Least Connections stratejisini etkinleştirir
        server backend1.example.com:8080;
        server backend2.example.com:8080 weight=2;
        server backend3.example.com:8080;
        
        keepalive 32;  # Her bir worker için maksimum kalıcı bağlantı sayısı
    }

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}

```

Bu konfigürasyonu biraz açıklayalım:

1. `upstream backend` bloğu:
   - `least_conn;`: Least Connections stratejisini etkinleştirir. Bu, Nginx'in gelen istekleri en az aktif bağlantıya sahip sunucuya yönlendirmesini sağlar.
   - `server backend2.example.com:8080 weight=2;`: Bu sunucuya diğerlerinden iki kat daha fazla ağırlık verir. Yani, eşit sayıda bağlantıya sahip olduklarında, bu sunucu diğerlerinden iki kat daha fazla istek alır.
   - `keepalive 32;`: Her bir worker için maksimum 32 kalıcı bağlantı tutulmasını sağlar. Bu, performansı artırır ve sunucu üzerindeki yükü azaltır.

2. `server` bloğu:
   - `proxy_http_version 1.1;` ve `proxy_set_header Connection "";`: HTTP/1.1 keep-alive bağlantılarını etkinleştirir, bu da bağlantıların yeniden kullanılmasını sağlayarak performansı artırır.

3. Diğer `proxy_set_header` direktifleri: Orijinal istemci bilgilerinin backend sunuculara iletilmesini sağlar.

Bu konfigürasyon, özellikle farklı kapasitelerdeki sunucuları yönetirken veya istek işleme sürelerinin değişken olduğu durumlarda etkili olacaktır. 
Örneğin, `backend2` sunucusu diğerlerinden daha güçlüyse, bu konfigürasyon ona daha fazla iş yükü yönlendirecektir.

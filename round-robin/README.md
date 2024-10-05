# Round Robin Stratejisi

**Round Robin**, yük dengelemede kullanılan en basit ve en yaygın stratejilerden biridir. Bu stratejide, gelen istekler sırayla her sunucuya eşit şekilde dağıtılır. 

İşleyiş şu şekildedir:

1. İlk istek ilk sunucuya gönderilir.
2. İkinci istek ikinci sunucuya gönderilir.
3. Bu şekilde tüm sunucular sırayla kullanılır.
4. Son sunucuya ulaşıldığında, tekrar ilk sunucudan başlanır.

Bu strateji, sunucuların benzer kapasiteye sahip olduğu ve isteklerin benzer kaynak kullanımına neden olduğu durumlarda idealdir.

Round Robin stratejisinin avantajları:
- Basit ve anlaşılır
- Sunucular arasında eşit yük dağılımı sağlar
- Ek konfigürasyon gerektirmez

Dezavantajları:
- Sunucuların farklı kapasitelere sahip olduğu durumlarda ideal olmayabilir
- Oturum devamlılığı (session persistence) sağlamaz

Şimdi, Nginx ayar dosyasını daha ayrıntılı bir şekilde inceleyelim:

```nginx
# nginx.conf

user nginx;
worker_processes auto;  # Nginx worker sayısını otomatik ayarlar

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;  # Her worker'ın aynı anda işleyebileceği bağlantı sayısı
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    #tcp_nopush on;

    keepalive_timeout 65;

    #gzip on;

    upstream backend {
        # Round Robin, varsayılan stratejidir, açıkça belirtmeye gerek yoktur
        server backend1.example.com:8080;
        server backend2.example.com:8080;
        server backend3.example.com:8080;
    }

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}

```

Bu konfigürasyonu biraz açıklayalım:

1. `user nginx;`: Nginx'in hangi kullanıcı altında çalışacağını belirtir.

2. `worker_processes auto;`: Nginx'in kaç worker process kullanacağını belirler. `auto` seçeneği, sunucunun CPU çekirdek sayısına göre otomatik ayarlanır.

3. `events` bloğu: Nginx'in ağ olaylarını nasıl işleyeceğini belirler.
   - `worker_connections 1024;`: Her worker'ın aynı anda işleyebileceği maksimum bağlantı sayısını belirtir.

4. `http` bloğu: HTTP sunucusu ve ilgili direktifleri içerir.
   - `include /etc/nginx/mime.types;`: MIME türlerini içe aktarır.
   - `log_format` ve `access_log`: Erişim loglarının formatını ve konumunu belirler.

5. `upstream backend` bloğu: Backend sunucularını tanımlar.
   - Burada üç sunucu tanımlanmıştır. Round Robin stratejisi varsayılan olduğu için açıkça belirtilmemiştir.

6. `server` bloğu: Sanal sunucuyu tanımlar.
   - `listen 80;`: Sunucunun 80 portunu dinleyeceğini belirtir.
   - `server_name example.com;`: Bu sanal sunucunun hangi alan adına hizmet vereceğini belirtir.

7. `location /` bloğu: Kök dizine gelen isteklerin nasıl işleneceğini belirler.
   - `proxy_pass http://backend;`: İstekleri upstream bloğunda tanımlanan backend sunucularına yönlendirir.
   - `proxy_set_header` direktifleri: Proxy üzerinden geçen isteklerde orijinal istemci bilgilerinin korunmasını sağlar.

Bu konfigürasyon ile Nginx, gelen istekleri sırayla `backend1`, `backend2` ve `backend3` sunucularına dağıtacaktır. İlk istek `backend1`'e, ikinci istek `backend2`'ye, üçüncü istek `backend3`'e gidecek, dördüncü istek tekrar `backend1`'den başlayacaktır.

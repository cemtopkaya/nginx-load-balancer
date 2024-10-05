# IP Hash Yük Dengeleme Strateji

IP Hash, istemcinin IP adresini kullanarak istekleri belirli bir sunucuya yönlendiren bir yük dengeleme yöntemidir. 
Bu strateji, **oturum devamlılığı (session persistence)** gerektiren uygulamalar için özellikle faydalıdır.

Çalışma Prensibi:
1. İstemcinin IP adresi bir hash fonksiyonundan geçirilir.
2. Elde edilen hash değeri, mevcut sunucu sayısına bölünür.
3. Kalan değer, isteğin yönlendirileceği sunucuyu belirler.
4. Aynı IP adresinden gelen sonraki istekler, sunucu havuzu değişmediği sürece hep aynı sunucuya yönlendirilir.

IP Hash stratejisinin avantajları:
1. Oturum Devamlılığı: Aynı istemciden gelen istekler hep aynı sunucuya yönlendirildiği için, oturum bilgilerinin korunması kolaylaşır.
2. Basitlik: Karmaşık oturum yönetimi mekanizmalarına gerek kalmaz.
3. Yük Dağılımı: Farklı IP'lerden gelen istekler farklı sunuculara dağıtılır, böylece genel bir yük dağılımı sağlanır.

Dezavantajları:
1. Eşit Olmayan Dağılım: IP adreslerinin dağılımına bağlı olarak, bazı sunucular diğerlerinden daha fazla yük alabilir.
2. NAT Arkasındaki Kullanıcılar: Aynı NAT arkasındaki çok sayıda kullanıcı aynı IP ile görünebilir, bu da tek bir sunucuya aşırı yük binmesine neden olabilir.
3. Dinamik IP'ler: Mobil cihazlar gibi sık IP değiştiren istemciler için oturum devamlılığı sağlanamayabilir.



Şimdi, IP Hash stratejisini kullanan bir Nginx konfigürasyonu oluşturalım:

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
        ip_hash;  # IP Hash stratejisini etkinleştirir

        server backend1.example.com:8080;
        server backend2.example.com:8080;
        server backend3.example.com:8080;

        # Geçici olarak devre dışı bırakılmış bir sunucu
        server backend4.example.com:8080 down;
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

            # Oturum çerezini korur
            proxy_set_header Cookie $http_cookie;
        }
    }
}

```

Bu Nginx konfigürasyonunun detaylı açıklaması:

1. `upstream backend` bloğu:
   - `ip_hash;`: IP Hash stratejisini etkinleştirir. Bu, gelen isteklerin istemci IP adresine göre belirli bir sunucuya yönlendirilmesini sağlar.
   - Üç aktif sunucu tanımlanmıştır: `backend1`, `backend2`, ve `backend3`.
   - `server backend4.example.com:8080 down;`: Bu satır, geçici olarak devre dışı bırakılmış bir sunucuyu gösterir. Bu, sunucu bakımdayken veya sorun yaşanıyorken kullanışlıdır.

2. `server` bloğu:
   - `listen 80;`: Nginx'in 80 portunu dinleyeceğini belirtir.
   - `server_name example.com;`: Bu sanal sunucunun hangi alan adına hizmet vereceğini belirtir.

3. `location /` bloğu:
   - `proxy_pass http://backend;`: İstekleri upstream bloğunda tanımlanan backend sunucularına yönlendirir.
   - `proxy_set_header` direktifleri: Orijinal istemci bilgilerinin backend sunuculara iletilmesini sağlar.
   - `proxy_set_header Cookie $http_cookie;`: Oturum çerezlerinin korunmasını sağlar, bu IP Hash ile birlikte kullanıldığında oturum devamlılığını güçlendirir.

Dikkat Edilmesi Gereken Noktalar:
1. Sunucu Ekleme/Çıkarma: Upstream sunucu havuzuna sunucu eklemek veya çıkarmak, hash değerlerini değiştirebilir ve mevcut oturumların farklı sunuculara yönlendirilmesine neden olabilir.
2. `down` Parametresi: Geçici olarak devre dışı bırakılan sunucular için `down` parametresi kullanılmalıdır. Bu, hash hesaplamasını etkilemez ve sunucu tekrar aktif hale geldiğinde oturum devamlılığı korunur.
3. X-Forwarded-For Başlığı: Eğer uygulamanız proxy arkasındaysa, gerçek istemci IP'sini almak için X-Forwarded-For başlığını kullanmayı düşünebilirsiniz.

Bu konfigürasyon, özellikle oturum devamlılığının önemli olduğu web uygulamaları için uygundur. 
Örneğin, alışveriş sepeti uygulamaları veya kullanıcı oturumunun korunması gereken diğer senaryolarda etkili olacaktır.

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

## Örnek Proje

```yaml
# docker-compose.yml
version: '3'

services:
  web1:
    build: .
    expose:
      - "5000"
  
  web2:
    build: .
    expose:
      - "5000"
  
  web3:
    build: .
    expose:
      - "5000"

  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - web1
      - web2
      - web3

# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app.py /app
RUN pip install flask
CMD ["python", "app.py"]

# app.py
from flask import Flask, request, session
import socket
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Güvenli bir anahtar kullanın

@app.route('/')
def hello():
    hostname = socket.gethostname()
    if 'user_id' not in session:
        session['user_id'] = random.randint(1000, 9999)
    return f"Hello from {hostname}! Your session ID is {session['user_id']}"

@app.route('/ip')
def show_ip():
    client_ip = request.remote_addr
    return f"Your IP address is: {client_ip}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        ip_hash;
        server web1:5000;
        server web2:5000;
        server web3:5000;
    }

    server {
        listen 80;
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Oturum çerezlerini korur
            proxy_set_header Cookie $http_cookie;
        }
    }
}

```

Bu yapılandırmanın açıklaması:

1. `docker-compose.yml`:
   - Üç adet web servisi (`web1`, `web2`, `web3`) tanımlanmıştır. Hepsi aynı Dockerfile'ı kullanarak oluşturulur.
   - Bir Nginx servisi tanımlanmıştır. Bu servis, yerel `nginx.conf` dosyasını kullanarak yapılandırılır.
   - Nginx, 80 portunu dışa açar ve web servislerine bağımlıdır.

2. `Dockerfile`:
   - Python 3.9 tabanlı bir imaj kullanır.
   - Flask uygulamasını içerir ve 5000 portunda çalıştırır.

3. `app.py`:
   - İki route içeren basit bir Flask uygulaması:
     - `/`: Hangi container'dan yanıt verildiğini ve kullanıcının oturum ID'sini gösterir.
     - `/ip`: Kullanıcının IP adresini gösterir.
   - Oturum kullanımı, IP Hash'in etkisini göstermek için eklenmiştir.

4. `nginx.conf`:
   - `upstream backend` bloğunda IP Hash stratejisi (`ip_hash;`) kullanılmıştır.
   - Üç web servisi tanımlanmıştır.
   - Proxy ayarları, orijinal istemci bilgilerini ve çerezleri koruyacak şekilde yapılandırılmıştır.

Bu yapılandırmayı kullanmak için:

1. Tüm dosyaları aynı dizine kaydedin.
2. Terminalde, dosyaların bulunduğu dizine gidin.
3. Aşağıdaki komutu çalıştırın:

   ```
   docker-compose up --build
   ```

4. Tarayıcınızda `http://localhost` adresine giderek uygulamayı test edin.

Test etmek için:
- Farklı tarayıcılar veya gizli/özel pencereler kullanarak `http://localhost` adresine erişin. Her biri farklı bir IP adresi gibi davranacak ve muhtemelen farklı container'lara yönlendirilecektir.
- Aynı tarayıcı oturumunda tekrar tekrar sayfayı yenileyin. Aynı container'dan yanıt almalısınız ve oturum ID'niz değişmemelidir.
- `http://localhost/ip` adresine giderek IP adresinizi kontrol edin.

Bu konfigürasyon, Nginx'in IP Hash stratejisini kullanarak yük dengelemesi yapmasını sağlar. Aynı IP adresinden gelen istekler her zaman aynı container'a yönlendirilecektir, bu da oturum devamlılığını sağlar.

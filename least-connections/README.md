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

# Örnek Proje
Least Connections stratejisini kullanan bir Nginx yük dengeleyici ile birlikte çalışan bir Docker Compose konfigürasyonu kodunu aşağıda bulabilirsiniz. 

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
from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    return f"Hello from {hostname}!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        least_conn;
        server web1:5000;
        server web2:5000 weight=2;
        server web3:5000;
        keepalive 32;
    }

    server {
        listen 80;
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

Bu Docker Compose yapılandırmasını da biraz açıklayalım:

1. `docker-compose.yml`:
   - Üç adet web servisi (`web1`, `web2`, `web3`) tanımlanmıştır. Hepsi aynı Dockerfile'ı kullanarak oluşturulur.
   - Bir Nginx servisi tanımlanmıştır. Bu servis, yerel `nginx.conf` dosyasını kullanarak yapılandırılır.
   - Nginx, 80 portunu dışa açar ve web servislerine bağımlıdır.

2. `Dockerfile`:
   - Python 3.9 tabanlı bir imaj kullanır.
   - Flask uygulamasını içerir ve 5000 portunda çalıştırır.

3. `app.py`:
   - Basit bir Flask uygulaması. Hangi container'dan yanıt verildiğini gösterir.

4. `nginx.conf`:
   - `upstream backend` bloğunda Least Connections stratejisi (`least_conn;`) kullanılmıştır.
   - `web2` servisine iki kat ağırlık verilmiştir (`weight=2`). Bu, diğer servislerle aynı sayıda bağlantıya sahip olduğunda, `web2`'nin iki kat daha fazla istek alacağı anlamına gelir.
   - `keepalive 32;` ile her bir worker için maksimum 32 kalıcı bağlantı tutulur.

### Çalıştıralım
Bu yapılandırmayı kullanmak için aşağıdaki komutu ilgili dizinde çalıştırabilirsiniz:
   ```
   docker-compose up --build
   ```

Tarayıcınızda `http://localhost` adresine giderek uygulamayı test edelim.

Bu konfigürasyon, Nginx'in Least Connections stratejisini kullanarak yük dengelemesi yapmasını sağlar. `web2` servisi, diğerlerinden daha fazla istek alacaktır (eğer bağlantı sayıları eşitse). Sayfayı yeniledikçe, farklı container'lardan yanıtlar alacaksınız, ancak `web2`'den daha sık yanıt alacaksınız.


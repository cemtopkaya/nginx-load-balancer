# nginx-load-balancer
Nginx ile yük dengeleme örneği

## Nginx Yük Dengeleme Stratejileri

1. **Round Robin (Varsayılan)**: 
   - İstekleri sırayla sunuculara dağıtır.
   - Sunucuların benzer kapasiteye sahip olduğu durumlarda idealdir.
   - Örnek: `upstream backend { server backend1.example.com; server backend2.example.com; }`

2. **Least Connections**:
   - İsteği, en az aktif bağlantıya sahip sunucuya yönlendirir.
   - Sunucuların farklı işlem kapasitelerine sahip olduğu durumlarda faydalıdır.
   - Örnek: `upstream backend { least_conn; server backend1.example.com; server backend2.example.com; }`

3. **IP Hash**:
   - İstemci IP adresine göre istekleri aynı sunucuya yönlendirir.
   - Oturum devamlılığının önemli olduğu durumlarda kullanışlıdır.
   - Örnek: `upstream backend { ip_hash; server backend1.example.com; server backend2.example.com; }`

4. **Generic Hash**:
   - Belirtilen anahtar (örn. URL, argüman) üzerinden hash oluşturarak istekleri yönlendirir.
   - Belirli içeriğin her zaman aynı sunucudan sunulması gerektiğinde faydalıdır.
   - Örnek: `upstream backend { hash $request_uri consistent; server backend1.example.com; server backend2.example.com; }`

5. **Least Time (NGINX Plus)**:
   - En düşük ortalama yanıt süresine ve en az aktif bağlantıya sahip sunucuyu seçer.
   - Yanıt süresi kritik olan uygulamalar için idealdir (NGINX Plus gerektirir).
   - Örnek: `upstream backend { least_time header; server backend1.example.com; server backend2.example.com; }`

6. **Random**:
   - İstekleri rastgele sunuculara dağıtır.
   - Genel amaçlı kullanım için uygundur, özellikle çok sayıda sunucu varsa.
   - Örnek: `upstream backend { random two; server backend1.example.com; server backend2.example.com; }`

7. **Weighted Load Balancing**:
   - Sunuculara farklı ağırlıklar atayarak, istekleri bu ağırlıklara göre dağıtır.
   - Sunucuların farklı kapasitelere sahip olduğu durumlarda kullanışlıdır.
   - Örnek: `upstream backend { server backend1.example.com weight=3; server backend2.example.com weight=1; }`
  
Nginx'in Lua modülünü kullanarak özel bir çözüm geliştirebilir veya uygulama seviyesinde bu işlevi gerçekleştirebilirsiniz.

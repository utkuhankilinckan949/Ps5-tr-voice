# PS5 TR Voice

PS5 oyunlarındaki İngilizce konuşmaları Türkçeye çevirip yapay zekâ sesiyle ayrı bir ses kanalından dinlemeyi amaçlayan yardımcı uygulama.

## Hedef kullanım

- PlayStation 5 görüntüsü HDMI üzerinden Xiaomi Smart Projector L1 Pro'ya gider.
- HDMI ses ayırıcıdan alınan oyun sesi Windows laptop'a USB ses giriş aygıtı üzerinden aktarılır.
- Windows uygulaması konuşmayı algılar, İngilizce metne dönüştürür, Türkçeye çevirir ve Türkçe ses üretir.
- Orijinal oyun sesi projektörden duyulmaya devam eder; Türkçe ses ayrı kulaklık/hoparlör çıkışından verilir.
- İlerleyen aşamada Android uygulaması, Windows uygulamasını yerel ağ üzerinden kontrol eder ve çeviri metinlerini gösterir.

## Önemli ses notu

Bu tasarımda Türkçe ses başlangıçta ayrı çıkıştan verilir. Böylece orijinal ses kapatılmaz. Aynı hoparlörde karıştırma (mix) istenirse sonraki aşamada gecikme ve ses seviyesi kontrolüyle ayrıca ele alınacaktır.

## Geliştirme aşamaları

1. Windows uygulaması: ses giriş/çıkış aygıtlarını görme ve giriş seviyesini test etme.
2. İngilizce konuşma algılama ve canlı metne dönüştürme.
3. Türkçe çeviri ve TTS seslendirme.
4. Gecikme, ses seviyesi ve oyun sesiyle senkronizasyon iyileştirmeleri.
5. Android kontrol/altyazı uygulaması.
6. PS5 + projektör + laptop ile uçtan uca test.

## Donanım bağlantısı

Önerilen bağlantı: PS5 HDMI → HDMI ses ayırıcı → HDMI görüntü çıkışı projektöre; ses çıkışı ise uygun bir USB ses giriş adaptörü üzerinden laptop'a. Satın alma öncesinde seçilecek ayırıcının PS5/HDCP ve projektörün 1080p görüntü modu ile uyumu doğrulanmalıdır.

**Henüz belirli bir HDMI ayırıcı veya ses adaptörü modeli seçilmedi.** Donanım listesi, laptop üzerindeki mevcut ses girişleri öğrenildikten sonra netleştirilecek.

## Geliştirme

Windows 10/11 hedeflenir. İlk prototip Python tabanlıdır. API anahtarları kaynak koda yazılmaz; yerel ortam değişkenleri veya kullanıcı ayarlarıyla sağlanır.

Kurulum adımları ve gerçek zamanlı ses motoru henüz geliştirme aşamasındadır.

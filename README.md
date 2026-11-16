# PS5 TR Voice

PS5 oyunlarındaki İngilizce konuşmaları Türkçeye çevirip yapay zekâ sesiyle ayrı bir ses kanalından dinlemeyi amaçlayan yardımcı uygulama.

## Mevcut prototip

- Seçilen ses girişini dinler ve giriş seviyesini gösterir.
- faster-whisper ile İngilizce konuşmayı bilgisayarda çevrimdışı metne dönüştürür.
- Algılanan İngilizce metni Google Çeviri üzerinden Türkçeye aktarır.
- İngilizce metin ve Türkçe çeviri ayrı alanlarda gösterilir.
- Çeviri ayrı bir arka plan iş parçacığında çalışır; ses tanıma iş parçacığını doğrudan bekletmez.

**Bu aşamada Türkçe seslendirme (TTS) henüz eklenmemiştir.** Çeviri için internet bağlantısı gerekir. Google Çeviri hizmeti üçüncü taraf çevrimiçi bir hizmettir; çevrilen metin bu hizmete gönderilir. API anahtarı gerekmez, ancak hizmet erişimi ve kullanım sınırları değişebilir.

## Hedef kullanım

- PlayStation 5 görüntüsü HDMI üzerinden Xiaomi Smart Projector L1 Pro'ya gider.
- HDMI ses ayırıcıdan alınan oyun sesi Windows laptop'a USB ses giriş aygıtı üzerinden aktarılır.
- Windows uygulaması konuşmayı algılar, İngilizce metne dönüştürür ve Türkçeye çevirir.
- Orijinal oyun sesi projektörden duyulmaya devam eder; Türkçe ses ileride ayrı kulaklık/hoparlör çıkışından verilecektir.

## Geliştirme aşamaları

1. Windows ses giriş aygıtlarını görme ve giriş seviyesini test etme. (Tamamlandı)
2. İngilizce konuşma algılama ve canlı metne dönüştürme. (İlk prototip çalışıyor; hız/doğruluk iyileştirmeleri sürecek.)
3. Türkçe çeviri. (İlk prototip eklendi; gerçek kullanımda test edilmeli.)
4. Türkçe TTS seslendirme ve ayrı ses çıkışı.
5. Gecikme, ses seviyesi ve oyun sesiyle senkronizasyon iyileştirmeleri.
6. PS5 + projektör + laptop ile uçtan uca test.

## Donanım bağlantısı

Önerilen bağlantı: PS5 HDMI → HDMI ses ayırıcı → HDMI görüntü çıkışı projektöre; ses çıkışı ise uygun bir USB ses giriş adaptörü üzerinden laptop'a. Satın alma öncesinde seçilecek ayırıcının PS5/HDCP ve projektörün 1080p görüntü modu ile uyumu doğrulanmalıdır.

**Henüz belirli bir HDMI ayırıcı veya ses adaptörü modeli seçilmedi.** Donanım listesi, laptop üzerindeki mevcut ses girişleri öğrenildikten sonra netleştirilecek.

## Windows kurulumu

Proje klasöründe PowerShell açın:

```powershell
python -m pip install -e .
python -m ps5_tr_voice.main
```

Uygulama ses giriş aygıtlarını listeler. “Dinlemeyi ve çeviriyi başlat” düğmesi seçilen girişten sesi alır. İlk kullanımda faster-whisper'ın base.en modeli indirilir. Tanıma CPU int8 modunda çalışır. Türkçe çeviri için ayrıca internet bağlantısı gerekir.

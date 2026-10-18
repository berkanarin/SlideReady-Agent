# SlideReady hareket dili: yönetmen el kitabı

Bu dosya Yönetmen adımında okunur. Amaç, PowerPoint'in kendi efektleriyle elle yapılması çok zor, her slaytta
farklı ve bir motion-graphics stüdyosundan çıkmış gibi duran bir film kurmaktır. Hareketi süs olsun diye değil,
izleyicinin gözünü slaytın okuma sırasına taşımak için kurarsın.

## 1. Değişmezler (pazarlık yok)

1. İlk kare boştur: yalnızca slaytın arka planı. Boş açılış 0,3–0,6 sn sürer.
2. Bir kahraman koreografi sunumda bir kez kullanılır. Art arda iki slayt aynı biçimde açılmaz.
3. Son kare PowerPoint'in çizdiği slayttır. Her hareket o kareye oturarak biter.
4. Okuma payında (en az 2 sn) hiçbir şey kımıldamaz.
5. Kare kaçmaz, takılmaz. `slideready check` geçmeden teslim yoktur.

## 2. Bir slaytın anatomisi

| Evre | Süre (tempo 1.0) | Ne olur |
|---|---|---|
| Boş açılış | 0,3–0,6 sn | Yalnızca arka plan. Kamera hafifçe yaklaşabilir, içerik yok |
| Kahraman an | 0,8–1,6 sn | Slaytın tek büyük hareketi: koreografi kataloğundan biri |
| Destek | 0,4–0,7 sn/öğe | Kalan öğeler okuma sırasıyla, 60–120 ms aralıklarla, örtüşerek gelir |
| Yerleşme | 0,2–0,4 sn | Yay fiziğiyle küçük taşma ve oturma; ışık/parıltı biter |
| Okuma payı | 2–5 sn | Durağan. Metin arttıkça uzar |

Hareketin toplamı klibin yarısını geçmez. 6 sn'den uzun bir giriş izleyiciyi bekletir.

## 3. Hareket ilkeleri (uzman kontrol listesi)

- **Hiyerarşi:** önce en önemli şey (başlık ya da veri), sonra açıklama. Aynı anda iki kahraman olmaz.
- **Örtüşen hareket:** öğeler tek tek beklemez; bir öğe yerleşirken sonraki başlar (stagger 60–120 ms).
- **Yumuşatma:** giriş için hızlı başlayıp yavaş biten eğri (expo/quint-out), çıkış yoktur. Doğrusal hareket yok.
- **Hazırlık ve devam:** büyük hareketten önce küçük bir ters kıpırtı, sonunda yay ile oturma. Ölçülü: %2–4 taşma.
- **Okuma yönü:** Türkçe soldan sağa, yukarıdan aşağı. Destek öğeleri bu sırayı izler; kahraman an bilinçli olarak
  kırabilir (merkezden dışa, aşağıdan yukarı).
- **Derinlik:** arka plan, paneller ve içerik farklı hızda hareket eder (paralaks). Odak dışı → net geçişi göze yol
  gösterir.
- **Renk ve ışık:** perde, parıltı ve ışık süpürmesi slaytın kendi vurgu renginden gelir; marka rengini bozmaz.
- **Sessiz ekran yasağı:** boş açılıştan sonra 0,3 sn içinde bir şey olmaya başlar.
- **Metin okunur kalır:** metin hareket ederken bile bulanıklığı kısa sürer ve hiçbir an hareketli bir görselin
  arkasında kalmaz.
- **Aynı anda tek kahraman:** büyük bir hareket oynarken başka büyük hareket olmaz; destek öğeleri küçük ve ikincil
  kalır.
- **Hız bulanıklığı:** hızlı her harekette yön boyunca belirgin hareket bulanıklığı olur, öğe durunca sıfıra iner.
  Bulanıksız hızlı hareket ucuz görünür.
- **Kamera anlatır:** kamera izleyiciye "şimdi buraya bak" der. Yoğun slaytta bölgeleri sırayla gezer (başlık →
  kilit sayı → grafik), sonunda geri çekilip tam slaytta durur.

### Giriş çeşitliliği (referans: profesyonel lansman filmleri)

İyi bir motion-graphics filminde aynı giriş iki kez görülmez. Destek öğeleri için de bu dağarcıktan seç ve
slayttan slayta değiştir:

- yönlü bulanıklıkla uçarak gelme (farklı yönlerden, farklı gecikmelerle),
- harf harf ya da kelime kelime yazılma (daktilo, kinetik tipografi),
- bulanıktan netleşme (alan derinliği: arka katman odak dışı, ön katman net),
- maskeyle açılma (çizgi, daire, çapraz şerit),
- ölçekle süpürme (bir öğe büyüyüp sahneyi kaplar ve sonraki içeriği açar),
- şekil dönüşümü (bir öğe başka bir öğeye dönüşür),
- döşeme (bir öğe çoğalarak ızgarayı doldurur),
- ızgaraya oturma (öğeler dağınık yerlerden kendi hücrelerine akar).

## 4. Koreografi kataloğu

`plan.json`'da her canlandırılan slayta bir `hero` yazılır. Aynı `hero` sunumda bir kez kullanılır. Odometre ve
grafik büyümesi destek hareketleridir; kahraman koreografiyle birlikte oynayabilir.

| `hero` | Ne görünür | En iyi olduğu slayt | Kaçın |
|---|---|---|---|
| `parcacik` | Başlık binlerce parçacıktan toplanır, harfler soldan sağa dolar | Kapak, kısa ve büyük başlık | Uzun başlık, metin yoğun slayt |
| `dev-baslik` | Ekranı kaplayan dev başlık küçülerek yerine oturur, arkasından içerik açılır | Bölüm/ara slaytı | Çok satırlı başlık |
| `perde` | Vurgu renginde bir perde ekranı süpürür; içerik perdenin arkasından açılmış olarak kalır | Konu değişimi, cesur geçiş | Art arda iki slayt |
| `derinlik` | Kartlar derinlikten kameraya doğru uçup ızgaraya oturur | Kart/ızgara düzeni (3–8 kart) | Tek öğeli slayt |
| `domino` | Kartlar sırayla kendi ekseninde dönerek yüzünü gösterir | Süreç adımları, sıralı liste | Düzensiz yerleşim |
| `bulusma` | İki grup karşı yönlerden kayıp ortada buluşur | İki sütun, karşılaştırma, önce/sonra | Tek sütun |
| `halka` | Merkezden genişleyen dairesel maske içeriği açar | Merkez simetrik düzen, tek büyük sayı | Kenara yaslı içerik |
| `cizim` | Önce çerçeveler ve çizgiler çizilir, sonra içleri dolar | Diyagram, tablo, şema, çerçeveli kartlar | Fotoğraf ağırlıklı slayt |
| `murekkep` | Büyük görsel mürekkep yayılması gibi açılır | Görsel ağırlıklı, az metinli slayt | Küçük görseller |
| `sayac` | Kamera kilit sayıya yaklaşır; rakamlar sağdan sola gecikmeli, hızlıyken bulanık döner ve yaylanarak oturur; bağlı çubuk ya da halka aynı eğriyle dolar; başka büyük hareket yok | Tek ya da birkaç kilit sayı (KPI, ödül, sonuç) | Sayıların tabloda olduğu slayt |
| `grafik` | Seriler sırayla büyür, kenar parlar, kamera sabit; değer etiketleri seri bitince belirir | Grafik ağırlıklı slayt | Çok küçük grafik |
| `kamera-turu` | Kamera yoğun slaytın bölgelerini sırayla gezer, her durakta o bölge açılır, sonunda tam slayta çekilir | 15+ öğeli yoğun slayt, pano | Az öğeli slayt |
| `daktilo` | Ana mesaj harf harf yazılır, anahtar kelime vurgulanır, ardından destek öğeleri gelir | Tek güçlü cümle, alıntı, slogan | Uzun paragraf |
| `odak` | Katmanlar farklı derinlikte; odak arka plandan öne çekilir, öne gelen katman netleşir | Fotoğraf üstünde metin, katmanlı düzen | Düz, tek katmanlı slayt |
| `geri-cekilme` | Kamera yakından başlayıp geniş ve yavaş geri çekilir | Kapanış, teşekkür | Sunum ortası |

Slayt sayısı katalogdan fazlaysa bir koreografi ancak arada en az dört slayt varsa ve kamerası, giriş yönü ve
temposu farklıysa yeniden kullanılır. `slideready check` daha yakın bir tekrarı hata, uzak bir tekrarı uyarı
sayar; uzak tekrarı da kullanıcıya raporda açıkça söyle.

## 5. Kamera ve ritim

- Kamera hareketleri: yaklaşma, geri çekilme, yana kayma, hafif eğim, sabit. Art arda üç slayt aynı kamerayı
  kullanmaz; her üç slayttan biri sabit kameradır (göz dinlenir).
- Yoğunluk eğrisi: güçlü → orta → sakin → güçlü. Kapak ve kapanış en güçlü iki an, ama hareketleri farklıdır.
- Tempo (`tempo`) slayttan slayta 0,85–1,2 arasında değişir. Veri slaytları biraz yavaş, bölüm slaytları hızlı.

## 6. Kötü işaretler (görürsen planı değiştir)

- Her slaytta aynı "yukarı kayıp netleşme".
- Işık perdesi ya da parıltı her slaytta: süsler yalnızca kapak ve kapanışta.
- Bütün öğelerin aynı anda gelmesi ya da hepsinin eşit aralıkla, aynı yönden gelmesi.
- Kahraman anın 2 sn'yi geçmesi, okuma payının kısalması.
- Metnin bulanık ya da yarı saydam hâlde uzun süre kalması.
